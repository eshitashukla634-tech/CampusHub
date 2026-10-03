import sqlite3

connection = sqlite3.connect("campushub.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT NOT NULL UNIQUE,
    course TEXT NOT NULL,
    email TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL,
    UNIQUE(student_id, date),
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student'
)
""")

cursor.execute("""
INSERT OR IGNORE INTO users (name, email, password, role)
VALUES (?, ?, ?, ?)
""", (
    "Eshita",
    "eshita@campushub.com",
    "123456",
    "admin"
))



connection.commit()

connection.close()

print("Database created successfully!")