from flask import Flask, render_template, request, redirect, url_for,session
from functools import wraps
import sqlite3

app = Flask(__name__)

app.secret_key = "campushub-development-key"

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("campushub.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, email, role
            FROM users
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()

        connection.close()

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_role"] = user[3]

            return redirect(url_for("dashboard"))

        else:

            error = "Invalid email or password."

    return render_template(
        "login.html",
        error=error
    )



@app.route("/dashboard")
def dashboard():


    if "user_id" not in session:
       return redirect(url_for("login"))


    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    # Total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Today's present students
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = date('now')
        AND status = 'Present'
    """)
    present_today = cursor.fetchone()[0]

    # Attendance percentage
    if total_students > 0:
        attendance_percentage = round(
            (present_today / total_students) * 100
        )
    else:
        attendance_percentage = 0

    # Total assignments
    cursor.execute("SELECT COUNT(*) FROM assignments")
    total_assignments = cursor.fetchone()[0]

    # Pending assignments
    cursor.execute("""
        SELECT COUNT(*)
        FROM assignments
        WHERE status = 'Pending'
    """)
    pending_assignments = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        attendance_percentage=attendance_percentage,
        total_assignments=total_assignments,
        pending_assignments=pending_assignments
    )

@app.route("/profile")
@login_required
def profile():

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email, role
        FROM users
        WHERE id = ?
    """, (session["user_id"],))

    user = cursor.fetchone()

    connection.close()

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        user=user
    )



@app.route("/students")
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@app.route("/attendance-history/<int:student_id>")
@login_required
def attendance_history(student_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    # Get student information
    cursor.execute("""
        SELECT id, name, roll_no, course
        FROM students
        WHERE id = ?
    """, (student_id,))

    student = cursor.fetchone()

    # If student does not exist
    if student is None:
        connection.close()
        return "Student not found", 404

    # Get attendance history
    cursor.execute("""
        SELECT date, status
        FROM attendance
        WHERE student_id = ?
        ORDER BY date DESC
    """, (student_id,))

    attendance_records = cursor.fetchall()

        # Count present days
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id = ?
        AND status = 'Present'
    """, (student_id,))

    present_count = cursor.fetchone()[0]

    # Count absent days
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id = ?
        AND status = 'Absent'
    """, (student_id,))

    absent_count = cursor.fetchone()[0]

    # Calculate attendance percentage
    total_attendance = present_count + absent_count

    if total_attendance > 0:
        attendance_percentage = round(
            (present_count / total_attendance) * 100
        )
    else:
        attendance_percentage = 0


    connection.close()

    return render_template(
    "attendance_history.html",
    student=student,
    attendance_records=attendance_records,
    present_count=present_count,
    absent_count=absent_count,
    attendance_percentage=attendance_percentage
)

@app.route("/mark-attendance/<int:student_id>/<status>")
@login_required
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
@login_required
def assignments():

    search = request.args.get("search", "")

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    if search:

        cursor.execute("""
            SELECT * FROM assignments
            WHERE title LIKE ?
            OR subject LIKE ?
            ORDER BY due_date
        """, (f"%{search}%", f"%{search}%"))

    else:

        cursor.execute("""
            SELECT * FROM assignments
            ORDER BY due_date
        """)

    assignments = cursor.fetchall()

    connection.close()

    return render_template(
        "assignments.html",
        assignments=assignments,
        search=search
    )

@app.route("/add-assignment", methods=["GET", "POST"])
@login_required
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
@login_required
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
@login_required
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


@app.route("/update-assignment-status/<int:assignment_id>/<status>")
@login_required
def update_assignment_status(assignment_id, status):

    if status not in ["Pending", "Completed"]:
        return "Invalid status", 400

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE assignments
        SET status = ?
        WHERE id = ?
    """, (status, assignment_id))

    connection.commit()
    connection.close()

    return redirect(url_for("assignments"))


@app.route("/analytics")
@login_required
def analytics():

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    # Total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Today's present students
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = date('now')
        AND status = 'Present'
    """)
    present_today = cursor.fetchone()[0]

    # Today's absent students
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = date('now')
        AND status = 'Absent'
    """)
    absent_today = cursor.fetchone()[0]

    # Total assignments
    cursor.execute("SELECT COUNT(*) FROM assignments")
    total_assignments = cursor.fetchone()[0]

    # Completed assignments
    cursor.execute("""
        SELECT COUNT(*)
        FROM assignments
        WHERE status = 'Completed'
    """)
    completed_assignments = cursor.fetchone()[0]

    # Pending assignments
    cursor.execute("""
        SELECT COUNT(*)
        FROM assignments
        WHERE status = 'Pending'
    """)
    pending_assignments = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "analytics.html",
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        total_assignments=total_assignments,
        completed_assignments=completed_assignments,
        pending_assignments=pending_assignments
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)