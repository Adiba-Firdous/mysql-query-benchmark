# MySQL SELECT Query Benchmark

A Python project that benchmarks representative MySQL `SELECT` queries before and after server tuning and generates a comparison report.

## Task

The project follows these steps:

1. Define representative `SELECT` queries.
2. Measure execution time with Python's `time` module.
3. Apply new MySQL configuration settings and restart the MySQL service.
4. Run the same queries again.
5. Compare before/after results.
6. Generate a Markdown summary report.

## Project Structure

```text
mysql-query-benchmark/
├── benchmark.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── queries.sql
├── reports/
│   └── .gitkeep
└── mysql-tuning-example.ini
```

## Requirements

- Python 3.10+
- MySQL 8.0+
- A database containing a `students` table
- `mysql-connector-python`
- `python-dotenv`

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials.

Example:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=backup_restore_demo
DB_USER=root
DB_PASSWORD=your_mysql_password
```

## Verify the Test Table

The benchmark expects:

```sql
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    course VARCHAR(100)
);
```

Example data:

```sql
INSERT INTO students (name, course) VALUES
('Adiba', 'Database Management'),
('Rahul', 'Cloud Computing'),
('Sara', 'Python');
```

## Run the Before Benchmark

Run this before changing MySQL settings:

```bash
python benchmark.py --label before
```

The script performs warm-up executions and then timed executions for each query.

You can increase the number of timed executions:

```bash
python benchmark.py --label before --iterations 20
```

## Apply MySQL Tuning

`mysql-tuning-example.ini` contains example conservative settings.

On Windows, the MySQL configuration is commonly stored in:

```text
C:\ProgramData\MySQL\MySQL Server 8.0\my.ini
```

Back up the existing configuration before editing it.

Do not replace the entire `my.ini` with `mysql-tuning-example.ini`. Instead, review the example values and apply appropriate changes to your existing `[mysqld]` section.

Then restart the MySQL service from an Administrator terminal:

```cmd
net stop MySQL80
net start MySQL80
```

Confirm that MySQL starts successfully before continuing.

## Run the After Benchmark

After the configuration change and restart:

```bash
python benchmark.py --label after
```

## Generate the Report

```bash
python benchmark.py --compare
```

The report is written to:

```text
reports/benchmark_report.md
```

Raw benchmark data is stored in:

```text
reports/benchmark_results.csv
```

These generated files are ignored by Git so that local credentials and machine-specific benchmark data are not accidentally committed.

## Understanding the Result

The report compares average execution time:

```text
Improvement = ((before - after) / before) × 100
```

A positive percentage means the average query time decreased after tuning.

Benchmark results can vary because of:

- MySQL buffer/cache state
- Dataset size
- CPU and RAM
- Other processes running on the machine
- Number of benchmark iterations

Therefore, the benchmark is intended as a reproducible demonstration rather than a production performance guarantee.

## Example Output

```text
Running BEFORE benchmark...
------------------------------------------------------------------------
all_students             avg=   1.2000 ms  min=   0.9000 ms  max=   1.8000 ms
student_by_name          avg=   1.0500 ms  min=   0.8000 ms  max=   1.5000 ms
students_by_course       avg=   1.1000 ms  min=   0.9000 ms  max=   1.6000 ms
ordered_students         avg=   1.2500 ms  min=   1.0000 ms  max=   1.7000 ms
```

After tuning, run the same benchmark and generate the Markdown comparison report.

## Important Note

This project measures client-observed execution time. For deeper database analysis, use MySQL tools such as `EXPLAIN` and `EXPLAIN ANALYZE` in addition to timing benchmarks.
