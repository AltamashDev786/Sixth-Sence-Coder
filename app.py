from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# =========================
# FLASK SESSION
# =========================

app.secret_key = "sixsense-admin-secret"


# =========================
# RESUME UPLOAD
# =========================

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE TABLES
# =========================

def create_table():

    conn = get_db()

    # Students
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            resume TEXT
        )
    """)

    # Admins
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Default admin
    admin = conn.execute(
        "SELECT * FROM admins WHERE email = ?",
        ("admin@sixsense.com",)
    ).fetchone()

    if not admin:

        conn.execute(
            """
            INSERT INTO admins (email, password)
            VALUES (?, ?)
            """,
            ("admin@sixsense.com", "admin123")
        )

    conn.commit()
    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("myweb.html")


# =========================
# STUDENT REGISTRATION
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        resume = request.files.get("resume")

        resume_filename = None

        if resume and resume.filename != "":

            resume_filename = secure_filename(resume.filename)

            os.makedirs(
                app.config["UPLOAD_FOLDER"],
                exist_ok=True
            )

            resume.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    resume_filename
                )
            )

        conn = get_db()

        conn.execute(
            """
            INSERT INTO students
            (name, email, password, resume)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password,
                resume_filename
            )
        )

        conn.commit()
        conn.close()

        return f"Registration successful! Welcome {name}"

    return render_template("register.html")


# =========================
# STUDENT LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM students
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            return f"Login successful! Welcome {user['name']}"

        return "Invalid email or password"

    return render_template("login.html")


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        admin = conn.execute(
            """
            SELECT *
            FROM admins
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if admin:

            session["admin_id"] = admin["id"]

            return redirect("/admin/dashboard")

        return "Invalid admin email or password"

    return render_template("admin_login.html")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    conn.close()

    # Future tables
    total_companies = 0
    total_jobs = 0
    total_applications = 0

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications
    )


# =========================
# STUDENT MANAGEMENT
# SEARCH
# =========================

@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:
        return redirect("/admin/login")

    search = request.args.get("search", "").strip()

    conn = get_db()

    if search:

        students = conn.execute(
            """
            SELECT id, name, email, resume
            FROM students
            WHERE name LIKE ?
            OR email LIKE ?
            ORDER BY id DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        students = conn.execute(
            """
            SELECT id, name, email, resume
            FROM students
            ORDER BY id DESC
            """
        ).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students,
        search=search
    )


# =========================
# STUDENT DETAILS
# =========================

@app.route("/admin/student/<int:student_id>")
def student_details(student_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db()

    student = conn.execute(
        """
        SELECT *
        FROM students
        WHERE id = ?
        """,
        (student_id,)
    ).fetchone()

    conn.close()

    if not student:
        return "Student not found"

    return render_template(
        "student_details.html",
        student=student
    )


# =========================
# DELETE STUDENT
# =========================

@app.route("/admin/student/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db()

    # Student ka resume naam nikalo
    student = conn.execute(
        """
        SELECT resume
        FROM students
        WHERE id = ?
        """,
        (student_id,)
    ).fetchone()

    if student:

        # Database se student delete
        conn.execute(
            """
            DELETE FROM students
            WHERE id = ?
            """,
            (student_id,)
        )

        conn.commit()

        # Resume file bhi delete karo
        if student["resume"]:

            resume_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                student["resume"]
            )

            if os.path.exists(resume_path):
                os.remove(resume_path)

    conn.close()

    return redirect("/admin/students")


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)

    return redirect("/admin/login")


# =========================
# CREATE DATABASE
# =========================

create_table()


# =========================
# RUN FLASK
# =========================

if __name__ == "__main__":

    app.run(debug=True)