from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/students")
def students():

    search = request.args.get("search", "")

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    if search:

        cursor.execute("""
            SELECT * FROM students
            WHERE name LIKE ?
            OR roll_no LIKE ?
        """, (f"%{search}%", f"%{search}%"))

    else:

        cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    connection.close()

    return render_template(
        "students.html",
        students=students,
        search=search
    )



@app.route("/add-student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":

        name = request.form["name"]
        roll_no = request.form["roll_no"]
        course = request.form["course"]
        email = request.form["email"]

        connection = sqlite3.connect("campushub.db")
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO students
                (name, roll_no, course, email)
                VALUES (?, ?, ?, ?)
            """, (name, roll_no, course, email))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "Roll number already exists!"

        connection.close()

        return redirect(url_for("students"))

    return render_template("add_student.html")



@app.route("/delete-student/<int:student_id>")
def delete_student(student_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("students"))


@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    if request.method == "POST":

        name = request.form["name"]
        roll_no = request.form["roll_no"]
        course = request.form["course"]
        email = request.form["email"]

        cursor.execute("""
            UPDATE students
            SET name = ?, roll_no = ?, course = ?, email = ?
            WHERE id = ?
        """, (name, roll_no, course, email, student_id))

        connection.commit()
        connection.close()

        return redirect(url_for("students"))

    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    )

    student = cursor.fetchone()

    connection.close()

    return render_template(
        "edit_student.html",
        student=student
    )


@app.route("/attendance")
def attendance():

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.roll_no,
            students.course,
            attendance.status
        FROM students
        LEFT JOIN attendance
        ON students.id = attendance.student_id
        AND attendance.date = date('now')
    """)

    students = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = date('now')
        AND status = 'Present'
    """)
    present_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = date('now')
        AND status = 'Absent'
    """)
    absent_count = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "attendance.html",
        students=students,
        total_students=total_students,
        present_count=present_count,
        absent_count=absent_count
    )
  

@app.route("/mark-attendance/<int:student_id>/<status>")
def mark_attendance(student_id, status):

    if status not in ["Present", "Absent"]:
        return "Invalid attendance status"

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO attendance
        (student_id, date, status)
        VALUES (?, date('now'), ?)
        ON CONFLICT(student_id, date)
        DO UPDATE SET status = excluded.status
    """, (student_id, status))

    connection.commit()
    connection.close()

    return redirect(url_for("attendance"))


@app.route("/assignments")
def assignments():

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM assignments
        ORDER BY due_date
    """)

    assignments = cursor.fetchall()

    connection.close()

    return render_template(
        "assignments.html",
        assignments=assignments
    ) 


@app.route("/add-assignment", methods=["GET", "POST"])
def add_assignment():

    if request.method == "POST":

        title = request.form["title"]
        subject = request.form["subject"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        connection = sqlite3.connect("campushub.db")
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO assignments
            (title, subject, description, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            subject,
            description,
            due_date,
            "Pending"
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("assignments"))

    return render_template("add_assignment.html")


@app.route("/edit-assignment/<int:assignment_id>", methods=["GET", "POST"])
def edit_assignment(assignment_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    if request.method == "POST":

        title = request.form["title"]
        subject = request.form["subject"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        cursor.execute("""
            UPDATE assignments
            SET title = ?,
                subject = ?,
                description = ?,
                due_date = ?
            WHERE id = ?
        """, (
            title,
            subject,
            description,
            due_date,
            assignment_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("assignments"))

    cursor.execute(
        "SELECT * FROM assignments WHERE id = ?",
        (assignment_id,)
    )

    assignment = cursor.fetchone()

    connection.close()

    if assignment is None:
        return "Assignment not found", 404

    return render_template(
        "edit_assignment.html",
        assignment=assignment
    )


@app.route("/delete-assignment/<int:assignment_id>")
def delete_assignment(assignment_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM assignments WHERE id = ?",
        (assignment_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("assignments"))

if __name__ == "__main__":
    app.run(debug=True)