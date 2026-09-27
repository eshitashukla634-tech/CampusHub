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

connection.commit()

connection.close()

print("Database created successfully!")