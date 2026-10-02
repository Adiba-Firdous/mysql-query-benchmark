-- Representative SELECT queries used by benchmark.py

SELECT id, name, course
FROM students;

SELECT id, name, course
FROM students
WHERE name = 'Adiba';

SELECT id, name, course
FROM students
WHERE course = 'Database Management';

SELECT id, name, course
FROM students
ORDER BY name;
