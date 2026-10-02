#!/usr/bin/env python3
"""
MySQL SELECT performance benchmark.

Runs representative SELECT queries multiple times, records execution times,
and generates a Markdown report. Use --label before and --label after to
create separate benchmark results, then use --compare to compare them.

Example:
    python benchmark.py --label before
    python benchmark.py --label after
    python benchmark.py --compare
"""

import argparse
import os
import statistics
import time
from datetime import datetime
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"
RESULTS_FILE = REPORT_DIR / "benchmark_results.csv"
COMPARISON_FILE = REPORT_DIR / "benchmark_report.md"

QUERIES = [
    ("all_students", "SELECT id, name, course FROM students"),
    ("student_by_name", "SELECT id, name, course FROM students WHERE name = %s"),
    ("students_by_course", "SELECT id, name, course FROM students WHERE course = %s"),
    ("ordered_students", "SELECT id, name, course FROM students ORDER BY name"),
]

PARAMS = {
    "all_students": None,
    "student_by_name": ("Adiba",),
    "students_by_course": ("Database Management",),
    "ordered_students": None,
}


def load_config():
    load_dotenv(BASE_DIR / ".env")

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if os.getenv(key) is None]

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in the values."
        )

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def connect_db():
    return mysql.connector.connect(**load_config())


def benchmark_query(cursor, sql, params, iterations, warmup):
    for _ in range(warmup):
        cursor.execute(sql, params)
        cursor.fetchall()

    timings = []
    row_count = 0

    for _ in range(iterations):
        start = time.perf_counter()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start) * 1000
        timings.append(elapsed_ms)
        row_count = len(rows)

    return {
        "avg_ms": statistics.mean(timings),
        "min_ms": min(timings),
        "max_ms": max(timings),
        "row_count": row_count,
    }


def append_result(label, query_name, result):
    REPORT_DIR.mkdir(exist_ok=True)

    new_file = not RESULTS_FILE.exists()
    with RESULTS_FILE.open("a", encoding="utf-8", newline="") as file:
        if new_file:
            file.write("timestamp,label,query,avg_ms,min_ms,max_ms,row_count\n")

        timestamp = datetime.now().isoformat(timespec="seconds")
        file.write(
            f"{timestamp},{label},{query_name},"
            f"{result['avg_ms']:.4f},{result['min_ms']:.4f},"
            f"{result['max_ms']:.4f},{result['row_count']}\n"
        )


def run_benchmark(label, iterations, warmup):
    connection = None
    cursor = None

    try:
        connection = connect_db()
        cursor = connection.cursor()

        print(f"\nRunning {label.upper()} benchmark...")
        print("-" * 72)

        results = {}

        for query_name, sql in QUERIES:
            result = benchmark_query(
                cursor,
                sql,
                PARAMS[query_name],
                iterations,
                warmup,
            )
            results[query_name] = result
            append_result(label, query_name, result)

            print(
                f"{query_name:24} "
                f"avg={result['avg_ms']:9.4f} ms  "
                f"min={result['min_ms']:9.4f} ms  "
                f"max={result['max_ms']:9.4f} ms"
            )

        print("-" * 72)
        print(f"Results saved to: {RESULTS_FILE}")
        return results

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def read_results():
    if not RESULTS_FILE.exists():
        return []

    lines = RESULTS_FILE.read_text(encoding="utf-8").splitlines()
    if len(lines) <= 1:
        return []

    headers = lines[0].split(",")
    rows = []

    for line in lines[1:]:
        values = line.split(",")
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))

    return rows


def generate_comparison():
    rows = read_results()
    before = {}
    after = {}

    for row in rows:
        target = before if row["label"] == "before" else after if row["label"] == "after" else None
        if target is not None:
            target[row["query"]] = float(row["avg_ms"])

    common_queries = [name for name, _ in QUERIES if name in before and name in after]

    if not common_queries:
        raise RuntimeError(
            "No matching before/after results found. "
            "Run --label before and --label after first."
        )

    lines = [
        "# MySQL SELECT Performance Benchmark",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Before vs. After",
        "",
        "| Query | Before (ms) | After (ms) | Change |",
        "|---|---:|---:|---:|",
    ]

    for query_name in common_queries:
        before_ms = before[query_name]
        after_ms = after[query_name]

        if before_ms > 0:
            improvement = ((before_ms - after_ms) / before_ms) * 100
        else:
            improvement = 0.0

        direction = "faster" if improvement > 0 else "slower" if improvement < 0 else "no change"

        lines.append(
            f"| `{query_name}` | {before_ms:.4f} | {after_ms:.4f} | "
            f"{improvement:+.2f}% ({direction}) |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Positive percentage means the average execution time decreased after tuning.",
            "- Negative percentage means the average execution time increased after tuning.",
            "- Results can vary with cache state, system load, dataset size, and hardware.",
            "",
            "## Benchmark Method",
            "",
            "Each query is warmed up before timing and then executed repeatedly using "
            "`time.perf_counter()`.",
            "",
            "The benchmark measures client-observed query execution time; it is not a "
            "replacement for MySQL `EXPLAIN` or production monitoring.",
            "",
        ]
    )

    COMPARISON_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Comparison report saved to: {COMPARISON_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark MySQL SELECT performance before and after tuning."
    )
    parser.add_argument(
        "--label",
        choices=["before", "after"],
        help="Run a benchmark and save it as before or after.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Generate a before/after Markdown comparison report.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Timed executions per query (default: 10).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=2,
        help="Warm-up executions per query (default: 2).",
    )

    args = parser.parse_args()

    if not args.label and not args.compare:
        parser.error("Choose --label before/after or --compare.")

    if args.label:
        if args.iterations < 1 or args.warmup < 0:
            parser.error("--iterations must be >= 1 and --warmup must be >= 0.")
        run_benchmark(args.label, args.iterations, args.warmup)

    if args.compare:
        generate_comparison()


if __name__ == "__main__":
    main()
