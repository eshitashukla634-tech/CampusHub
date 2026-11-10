import sqlite3

connection = sqlite3.connect("campushub.db")
cursor = connection.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON")


# 1. Students Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT NOT NULL UNIQUE,
    course TEXT NOT NULL,
    email TEXT
)
""")


# 2. Attendance Table
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


# 3. Assignments Table
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


# 4. Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    student_id INTEGER UNIQUE,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")


# 5. Migrate Existing Users Table
# Adds student_id without deleting existing user records.

cursor.execute("PRAGMA table_info(users)")
columns = [column[1] for column in cursor.fetchall()]

if "student_id" not in columns:

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN student_id INTEGER REFERENCES students(id)
    """)


# 6. Admin Account
cursor.execute("""
INSERT OR IGNORE INTO users
(name, email, password, role)
VALUES (?, ?, ?, ?)
""", (
    "Eshita",
    "eshita@campushub.com",
    "123456",
    "admin"
))


# 7. Notifications Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")


# 8. Student Performance Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    assessment_name TEXT NOT NULL,
    total_marks REAL NOT NULL,
    obtained_marks REAL NOT NULL,
    assessment_date TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")

# 9. Student Assignment Submissions Table

cursor.execute("""
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,

    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,

    description TEXT,

    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,

    status TEXT NOT NULL DEFAULT 'Submitted',

    feedback TEXT,

    FOREIGN KEY(assignment_id) REFERENCES assignments(id),
    FOREIGN KEY(student_id) REFERENCES students(id),

    UNIQUE(assignment_id, student_id)
)
""")

# 10. Assignment Submission Attempts Table

cursor.execute("""
CREATE TABLE IF NOT EXISTS submission_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    submission_id INTEGER NOT NULL,

    attempt_number INTEGER NOT NULL,

    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,

    description TEXT,

    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,

    status TEXT NOT NULL DEFAULT 'Submitted',

    feedback TEXT,

    FOREIGN KEY(submission_id)
        REFERENCES submissions(id),

    UNIQUE(submission_id, attempt_number)
)
""")

# 11. Assignment Grading Table

cursor.execute("""
CREATE TABLE IF NOT EXISTS assignment_grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    submission_id INTEGER NOT NULL UNIQUE,

    obtained_marks REAL NOT NULL,
    total_marks REAL NOT NULL,

    grade TEXT NOT NULL,

    remarks TEXT,

    graded_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(submission_id)
        REFERENCES submissions(id)
)
""")



# Save changes
connection.commit()

connection.close()

print("CampusHub database updated successfully!")
