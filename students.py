import sqlite3

def add_student(name, roll_no, course, email):

    if not name.strip():
        print("⚠️ Name cannot be empty.")
        return

    if not roll_no.strip():
        print("⚠️ Roll number cannot be empty.")
        return

    if not course.strip():
        print("⚠️ Course cannot be empty.")
        return

    if "@" not in email:
        print("⚠️ Please enter a valid email.")
        return

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO students (name, roll_no, course, email)
            VALUES (?, ?, ?, ?)
        """, (name, roll_no, course, email))

        connection.commit()
        print("✅ Student added successfully!")

    except sqlite3.IntegrityError:
        print("⚠️ Roll number already exists!")

    finally:
        connection.close()


def view_students():
    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    connection.close()

    if not students:
        print("No students found.")
        return

    print("\n===== Student Records =====")

    for student in students:
        print("ID:", student[0])
        print("Name:", student[1])
        print("Roll No:", student[2])
        print("Course:", student[3])
        print("Email:", student[4])
        print("--------------------------")

def update_student(student_id, name, roll_no, course, email):

    if not name.strip():
        print("⚠️ Name cannot be empty.")
        return

    if not roll_no.strip():
        print("⚠️ Roll number cannot be empty.")
        return

    if not course.strip():
        print("⚠️ Course cannot be empty.")
        return

    if "@" not in email:
        print("⚠️ Please enter a valid email.")
        return

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE students
            SET name = ?, roll_no = ?, course = ?, email = ?
            WHERE id = ?
        """, (name, roll_no, course, email, student_id))

        connection.commit()

        if cursor.rowcount == 0:
            print("⚠️ Student not found.")
        else:
            print("✅ Student updated successfully!")

    except sqlite3.IntegrityError:
        print("⚠️ That roll number already belongs to another student.")

    finally:
        connection.close()
   
def delete_student(student_id):
    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    connection.commit()

    if cursor.rowcount == 0:
        print("Student not found.")
    else:
        print("Student deleted successfully!")

    connection.close()

def search_student(search_value):
    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM students
        WHERE name LIKE ? OR roll_no LIKE ?
    """, (f"%{search_value}%", f"%{search_value}%"))

    students = cursor.fetchall()

    connection.close()

    if not students:
        print("No student found.")
        return

    print("\n===== Search Results =====")

    for student in students:
        print("ID:", student[0])
        print("Name:", student[1])
        print("Roll No:", student[2])
        print("Course:", student[3])
        print("Email:", student[4])
        print("--------------------------")