from flask import Flask, render_template, request, redirect, url_for,session
from functools import wraps
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)

app.secret_key = "campushub-development-key"

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def generate_notifications(user_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, due_date
        FROM assignments
        WHERE status = 'Pending'
    """)

    assignments = cursor.fetchall()

    today = date.today()

    for assignment in assignments:

        assignment_id = assignment[0]
        title = assignment[1]
        due_date = date.fromisoformat(assignment[2])

        remaining_days = (due_date - today).days

        if remaining_days == 1:
            message = f"Assignment '{title}' is due tomorrow."
            notification_type = "Due Tomorrow"

        elif remaining_days == 0:
            message = f"Assignment '{title}' is due today."
            notification_type = "Due Today"

        elif remaining_days < 0:
            message = f"Assignment '{title}' is overdue."
            notification_type = "Overdue"

        else:
            continue

        cursor.execute("""
            SELECT id FROM notifications
            WHERE user_id = ?
            AND message = ?
            AND notification_type = ?
        """, (user_id, message, notification_type))

        existing = cursor.fetchone()

        if existing is None:
            cursor.execute("""
                INSERT INTO notifications
                (user_id, message, notification_type)
                VALUES (?, ?, ?)
            """, (user_id, message, notification_type))

    connection.commit()
    connection.close()


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

    # Calculate assignment deadlines
    today = date.today()

    updated_assignments = []

    for assignment in assignments:

        due_date = date.fromisoformat(assignment[4])

        remaining_days = (due_date - today).days

        if assignment[5] == "Completed":
            deadline_status = "Completed"

        elif remaining_days < 0:
            deadline_status = "Overdue"

        elif remaining_days == 0:
            deadline_status = "Due Today"

        elif remaining_days == 1:
            deadline_status = "Due Tomorrow"

        else:
            deadline_status = f"{remaining_days} Days Left"

        updated_assignments.append(
            assignment + (deadline_status,)
        )

    return render_template(
        "assignments.html",
        assignments=updated_assignments,
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


    today = date.today()
    start_date = today - timedelta(days=6)

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

    #Overall attendance 
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'Present' THEN 1 END),
            COUNT(CASE WHEN status = 'Absent' THEN 1 END)
        FROM attendance
    """)
    total_present, total_absent = cursor.fetchone()

    total_records = total_present + total_absent

    if total_records > 0:
        overall_present = round((total_present / total_records) * 100)

    else:
        overall_present = 0


    #Weekly attendance
    today = date.today()
    start_date = today - timedelta(days=6)
    

    cursor.execute("""
        SELECT date,
               SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END),
               SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END)
        FROM attendance
        WHERE date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date
    """, (start_date.isoformat(), today.isoformat()))

    weekly_records = cursor.fetchall()

    weekly_data = {
        record[0]: {
            "present": record[1],
            "absent": record[2]
        }
        for record in weekly_records
    }

    weekly_labels = []
    weekly_present = []
    weekly_absent = []

    for i in range(7):

        current_date = start_date + timedelta(days=i)
        date_string = current_date.isoformat()

        weekly_labels.append(current_date.strftime("%d %b"))

        weekly_present.append(
            weekly_data.get(date_string, {}).get("present", 0)
        )

        weekly_absent.append(
            weekly_data.get(date_string, {}).get("absent", 0)
        )

    # Student-wise attendance
    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.roll_no,
            COUNT(attendance.id),
            SUM(
                CASE
                    WHEN attendance.status = 'Present'
                    THEN 1 ELSE 0
                END
            )
        FROM students
        LEFT JOIN attendance
        ON students.id = attendance.student_id
        GROUP BY students.id
        ORDER BY students.name
    """)

    student_records = cursor.fetchall()

    student_attendance = []

    for student in student_records:

        student_id = student[0]
        name = student[1]
        roll_no = student[2]
        total = student[3]
        present = student[4] or 0

        if total > 0:
            percentage = round((present / total) * 100)
        else:
            percentage = 0

        student_attendance.append({
            "id": student_id,
            "name": name,
            "roll_no": roll_no,
            "percentage": percentage,
            "total": total,
            "present": present
        })

    # Students below 75% attendance
    low_attendance = [
        student for student in student_attendance
        if student["total"] > 0
        and student["percentage"] < 75
    ]

   

        # Calculate overall attendance

    attendance_data = cursor.execute("""
        SELECT
            COUNT(CASE WHEN status = 'Present' THEN 1 END),
            COUNT(CASE WHEN status = 'Absent' THEN 1 END)
        FROM attendance
    """).fetchone()

    total_present = attendance_data[0]
    total_absent = attendance_data[1]

    total_attendance = total_present + total_absent

    if total_attendance > 0:
        overall_attendance = round(
            (total_present / total_attendance) * 100, 2
        )
    else:
        overall_attendance = 0

    connection.close()

    return render_template(
        "analytics.html",
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        total_assignments=total_assignments,
        completed_assignments=completed_assignments,
        pending_assignments=pending_assignments,
        overall_attendance=overall_attendance,
        weekly_labels=weekly_labels,
        weekly_present=weekly_present,
        weekly_absent=weekly_absent,
        student_attendance=student_attendance,
        low_attendance=low_attendance
    )


# =====================================
# STUDENT PERFORMANCE TRACKING
# =====================================

def calculate_grade(percentage):

    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    elif percentage >= 40:
        return "E"
    else:
        return "F"


# Performance Dashboard

@app.route("/performance")
@login_required
def performance():

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    # 1. Get all assessment records
    cursor.execute("""
        SELECT
            performance.id,
            students.name,
            students.roll_no,
            performance.subject,
            performance.assessment_name,
            performance.total_marks,
            performance.obtained_marks,
            performance.assessment_date
        FROM performance
        JOIN students
            ON performance.student_id = students.id
        ORDER BY performance.assessment_date DESC
    """)

    records = cursor.fetchall()
    performance_records = []

    for record in records:
        total_marks = float(record[5] or 0)
        obtained_marks = float(record[6] or 0)
        percentage = round((obtained_marks / total_marks) * 100, 2) if total_marks > 0 else 0

        performance_records.append({
            "id": record[0],
            "name": record[1],
            "roll_no": record[2],
            "subject": record[3],
            "assessment_name": record[4],
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "date": record[7],
            "percentage": percentage,
            "grade": calculate_grade(percentage)
        })

    # 2. Student-wise average performance
    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.roll_no,
            AVG(performance.obtained_marks * 100.0 / performance.total_marks)
        FROM students
        JOIN performance
            ON students.id = performance.student_id
        WHERE performance.total_marks > 0
        GROUP BY students.id, students.name, students.roll_no
        ORDER BY students.name
    """)

    student_results = cursor.fetchall()
    student_performance = []

    for student in student_results:
        average = round(float(student[3] or 0), 2)
        student_performance.append({
            "id": student[0],
            "name": student[1],
            "roll_no": student[2],
            "average": average,
            "grade": calculate_grade(average)
        })

    # 3. Top three performers
    top_performers = sorted(
        student_performance,
        key=lambda item: item["average"],
        reverse=True
    )[:3]

    # 4. Subject-wise averages
    cursor.execute("""
        SELECT
            subject,
            ROUND(AVG(obtained_marks * 100.0 / total_marks), 2)
        FROM performance
        WHERE total_marks > 0
        GROUP BY subject
        ORDER BY subject
    """)

    subject_results = cursor.fetchall()
    subject_labels = [item[0] for item in subject_results]
    subject_averages = [float(item[1] or 0) for item in subject_results]

    # 5. Grade distribution across assessment records
    grade_labels = ["A+", "A", "B", "C", "D", "E", "F"]
    grade_counts = {grade: 0 for grade in grade_labels}

    for record in performance_records:
        grade_counts[record["grade"]] += 1

    grade_values = [grade_counts[grade] for grade in grade_labels]

    # 6. Students whose average is below 40%
    low_performance = [
        student for student in student_performance
        if student["average"] < 40
    ]

    # 7. Average across all assessment records
    total_records = len(performance_records)
    if total_records:
        overall_average = round(
            sum(item["percentage"] for item in performance_records) / total_records,
            2
        )
    else:
        overall_average = 0

    # 8. Highest and lowest performing subjects
    if subject_results:
        highest_subject = max(subject_results, key=lambda item: item[1])
        lowest_subject = min(subject_results, key=lambda item: item[1])
    else:
        highest_subject = None
        lowest_subject = None

    connection.close()

    return render_template(
        "performance.html",
        performance_records=performance_records,
        student_performance=student_performance,
        low_performance=low_performance,
        top_performers=top_performers,
        subject_labels=subject_labels,
        subject_averages=subject_averages,
        grade_labels=grade_labels,
        grade_values=grade_values,
        highest_subject=highest_subject,
        lowest_subject=lowest_subject,
        total_records=total_records,
        overall_average=overall_average
    )


# Add Performance

@app.route("/add-performance", methods=["GET", "POST"])
@login_required
def add_performance():

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("SELECT id, name, roll_no FROM students")
    students = cursor.fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]
        subject = request.form["subject"].strip()
        assessment_name = request.form["assessment_name"].strip()
        total_marks = float(request.form["total_marks"])
        obtained_marks = float(request.form["obtained_marks"])
        assessment_date = request.form["assessment_date"]

        if (
            not subject
            or not assessment_name
            or total_marks <= 0
            or obtained_marks < 0
            or obtained_marks > total_marks
        ):
            connection.close()
            return "Invalid marks or assessment details.", 400

        cursor.execute("""
            INSERT INTO performance
            (
                student_id,
                subject,
                assessment_name,
                total_marks,
                obtained_marks,
                assessment_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            subject,
            assessment_name,
            total_marks,
            obtained_marks,
            assessment_date
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("performance"))

    connection.close()

    return render_template(
        "add_performance.html",
        students=students
    )


# Edit Performance

@app.route(
    "/edit-performance/<int:performance_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_performance(performance_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    if request.method == "POST":

        subject = request.form["subject"].strip()
        assessment_name = request.form["assessment_name"].strip()
        total_marks = float(request.form["total_marks"])
        obtained_marks = float(request.form["obtained_marks"])
        assessment_date = request.form["assessment_date"]

        if (
            not subject
            or not assessment_name
            or total_marks <= 0
            or obtained_marks < 0
            or obtained_marks > total_marks
        ):
            connection.close()
            return "Invalid marks or assessment details.", 400

        cursor.execute("""
            UPDATE performance
            SET subject = ?,
                assessment_name = ?,
                total_marks = ?,
                obtained_marks = ?,
                assessment_date = ?
            WHERE id = ?
        """, (
            subject,
            assessment_name,
            total_marks,
            obtained_marks,
            assessment_date,
            performance_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("performance"))

    cursor.execute("""
        SELECT *
        FROM performance
        WHERE id = ?
    """, (performance_id,))

    record = cursor.fetchone()

    connection.close()

    if record is None:
        return "Performance record not found.", 404

    return render_template(
        "edit_performance.html",
        record=record
    )


# Delete Performance

@app.route("/delete-performance/<int:performance_id>")
@login_required
def delete_performance(performance_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM performance
        WHERE id = ?
    """, (performance_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("performance"))


# Notifications Page
@app.route("/notifications")
@login_required
def notifications():

    user_id = session["user_id"]

    # Generate new notifications
    generate_notifications(user_id)

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, message, notification_type,
               is_read, created_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    notifications = cursor.fetchall()

    connection.close()

    return render_template(
        "notifications.html",
        notifications=notifications
    )


# Global notification count
@app.context_processor
def inject_notification_count():

    if "user_id" not in session:
        return {"unread_count": 0}

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM notifications
        WHERE user_id = ?
        AND is_read = 0
    """, (session["user_id"],))

    unread_count = cursor.fetchone()[0]

    connection.close()

    return {"unread_count": unread_count}


# Mark notification as read
@app.route("/mark-notification-read/<int:notification_id>")
@login_required
def mark_notification_read(notification_id):

    connection = sqlite3.connect("campushub.db")
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE id = ? AND user_id = ?
    """, (notification_id, session["user_id"]))

    connection.commit()
    connection.close()

    return redirect(url_for("notifications"))

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)



