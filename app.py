from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

import Database


app = Flask(__name__)

app.secret_key = "sixsense-admin-secret"


# =========================================================
# UPLOAD SETTINGS
# =========================================================

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# ADMIN TABLE
# =========================================================

def create_table():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

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


# =========================================================
# COMPANY DATABASE SETUP
# =========================================================

def setup_company_database():

    conn = get_db()

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(companies)"
        ).fetchall()
    ]

    new_columns = {
        "password": "TEXT",
        "phone": "TEXT",
        "industry": "TEXT",
        "description": "TEXT",
        "website": "TEXT",
        "address": "TEXT",
        "city": "TEXT",
        "state": "TEXT",
        "pincode": "TEXT",
        "recruiter_name": "TEXT",
        "designation": "TEXT",
        "recruiter_email": "TEXT",
        "recruiter_phone": "TEXT",
        "linkedin": "TEXT"
    }

    for column, datatype in new_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE companies ADD COLUMN {column} {datatype}"
            )

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("myweb.html")


# =========================================================
# STUDENT REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name") or request.form.get("fullname")

        email = request.form.get("email")

        password = request.form.get("password")

        resume = request.files.get("resume")


        if not name or not email or not password:

            return "Please fill all required fields."


        resume_filename = None


        if resume and resume.filename != "":

            resume_filename = secure_filename(
                resume.filename
            )

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


        student_id = Database.add_student(
            name=name,
            email=email,
            password=password,
            resume=resume_filename
        )


        if student_id is None:

            return "This email is already registered."


        return f"Registration successful! Welcome {name}"


    return render_template("register.html")


# =========================================================
# STUDENT LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")


        if not email or not password:

            return "Please enter email and password."


        user = Database.authenticate_student(
            email,
            password
        )


        if user:

            session["student_id"] = user["id"]

            session["student_name"] = user["name"]

            return redirect("/student/dashboard")


        return "Invalid email or password."


    return render_template("login.html")


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student/dashboard")
def student_dashboard():

    if "student_id" not in session:

        return redirect("/login")


    student_id = session["student_id"]


    student = Database.get_student(student_id)


    if not student:

        session.pop("student_id", None)

        session.pop("student_name", None)

        return redirect("/login")


    skills = Database.get_student_skills(student_id)


    internships = Database.get_matching_internships(
        student_id
    )


    if not internships:

        internships = Database.get_all_internships()


    applications = Database.get_student_applications(
        student_id
    )


    return render_template(
        "student_dashboard.html",
        student=student,
        skills=skills,
        internships=internships,
        applications=applications
    )


# =========================================================
# STUDENT PROFILE EDIT
# =========================================================

@app.route("/student/profile/edit", methods=["GET", "POST"])
def student_profile_edit():

    if "student_id" not in session:

        return redirect("/login")


    student_id = session["student_id"]


    if request.method == "POST":

        name = request.form.get("name")

        department = request.form.get("department")

        year = request.form.get("year")


        if not name:

            return "Name is required."


        conn = get_db()


        conn.execute(
            """
            UPDATE students
            SET name = ?, department = ?, year = ?
            WHERE id = ?
            """,
            (
                name,
                department,
                year if year else None,
                student_id
            )
        )


        conn.commit()

        conn.close()


        session["student_name"] = name


        return redirect("/student/dashboard")


    student = Database.get_student(student_id)


    return render_template(
        "student_profile_edit.html",
        student=student
    )


# =========================================================
# STUDENT SKILLS
# =========================================================

@app.route("/student/skills", methods=["GET", "POST"])
def student_skills():

    if "student_id" not in session:

        return redirect("/login")


    student_id = session["student_id"]


    if request.method == "POST":

        skill_name = request.form.get(
            "skill_name",
            ""
        ).strip()


        proficiency = request.form.get(
            "proficiency",
            "Beginner"
        )


        if not skill_name:

            return "Please enter a skill."


        skill_id = Database.add_skill(
            skill_name
        )


        if skill_id is None:

            return "Unable to add skill."


        success = Database.add_student_skill(
            student_id,
            skill_id,
            proficiency
        )


        if not success:

            return "This skill is already added."


        return redirect("/student/skills")


    skills = Database.get_student_skills(
        student_id
    )


    return render_template(
        "student_skills.html",
        skills=skills
    )


# =========================================================
# REMOVE STUDENT SKILL
# =========================================================

@app.route(
    "/student/skills/remove/<int:skill_id>",
    methods=["POST"]
)
def remove_student_skill(skill_id):

    if "student_id" not in session:

        return redirect("/login")


    student_id = session["student_id"]


    conn = get_db()


    conn.execute(
        """
        DELETE FROM student_skills
        WHERE student_id = ?
        AND skill_id = ?
        """,
        (
            student_id,
            skill_id
        )
    )


    conn.commit()

    conn.close()


    return redirect("/student/skills")


# =========================================================
# STUDENT APPLY INTERNSHIP
# =========================================================

@app.route(
    "/student/apply/<int:internship_id>",
    methods=["POST"]
)
def apply_internship(internship_id):

    if "student_id" not in session:

        return redirect("/login")


    student_id = session["student_id"]


    success = Database.apply_for_internship(
        student_id,
        internship_id
    )


    return redirect("/student/dashboard")


# =========================================================
# STUDENT LOGOUT
# =========================================================

@app.route("/student/logout")
def student_logout():

    session.pop("student_id", None)

    session.pop("student_name", None)

    return redirect("/login")


# =========================================================
# COMPANY REGISTER
# =========================================================

@app.route(
    "/company/register",
    methods=["GET", "POST"]
)
def company_register():

    if request.method == "POST":

        cname = request.form.get(
            "cname",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        phone = request.form.get(
            "phone",
            ""
        ).strip()


        company_type = request.form.get(
            "company_type",
            ""
        ).strip()


        industry = request.form.get(
            "industry",
            ""
        ).strip()


        website = request.form.get(
            "website",
            ""
        ).strip()


        address = request.form.get(
            "address",
            ""
        ).strip()


        city = request.form.get(
            "city",
            ""
        ).strip()


        state = request.form.get(
            "state",
            ""
        ).strip()


        pincode = request.form.get(
            "pincode",
            ""
        ).strip()


        description = request.form.get(
            "description",
            ""
        ).strip()


        recruiter_name = request.form.get(
            "recruiter_name",
            ""
        ).strip()


        designation = request.form.get(
            "designation",
            ""
        ).strip()


        recruiter_email = request.form.get(
            "recruiter_email",
            ""
        ).strip().lower()


        recruiter_phone = request.form.get(
            "recruiter_phone",
            ""
        ).strip()


        linkedin = request.form.get(
            "linkedin",
            ""
        ).strip()


        password = request.form.get(
            "password",
            ""
        )


        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if not cname or not email or not phone:

            return render_template(
                "company_registration.html",
                error="Please fill all required company fields."
            )


        if not recruiter_name or not recruiter_email:

            return render_template(
                "company_registration.html",
                error="Please enter recruiter details."
            )


        if not password:

            return render_template(
                "company_registration.html",
                error="Please create a password."
            )


        if password != confirm_password:

            return render_template(
                "company_registration.html",
                error="Password and Confirm Password do not match."
            )


        if len(password) < 6:

            return render_template(
                "company_registration.html",
                error="Password must contain at least 6 characters."
            )


        hashed_password = generate_password_hash(
            password
        )


        conn = get_db()


        try:

            conn.execute(
                """
                INSERT INTO companies
                (
                    company_name,
                    email,
                    phone,
                    industry,
                    description,
                    website,
                    password,
                    address,
                    city,
                    state,
                    pincode,
                    recruiter_name,
                    designation,
                    recruiter_email,
                    recruiter_phone,
                    linkedin
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cname,
                    email,
                    phone,
                    industry,
                    description,
                    website,
                    hashed_password,
                    address,
                    city,
                    state,
                    pincode,
                    recruiter_name,
                    designation,
                    recruiter_email,
                    recruiter_phone,
                    linkedin
                )
            )


            conn.commit()

            conn.close()


            return redirect("/company/login")


        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "company_registration.html",
                error="Company email is already registered."
            )


    return render_template(
        "company_registration.html"
    )


# =========================================================
# COMPANY LOGIN
# =========================================================

@app.route(
    "/company/login",
    methods=["GET", "POST"]
)
def company_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        conn = get_db()


        company = conn.execute(
            """
            SELECT *
            FROM companies
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


        conn.close()


        if company and company["password"]:

            if check_password_hash(
                company["password"],
                password
            ):

                session["company_id"] = company["id"]

                session["company_name"] = company["company_name"]

                session["company_email"] = company["email"]


                return redirect(
                    "/company/dashboard"
                )


        return render_template(
            "company_login.html",
            error="Invalid company email or password."
        )


    return render_template(
        "company_login.html"
    )


# =========================================================
# COMPANY DASHBOARD
# =========================================================

@app.route("/company/dashboard")
def company_dashboard():

    if "company_id" not in session:

        return redirect("/company/login")


    company_id = session["company_id"]


    conn = get_db()


    company = conn.execute(
        """
        SELECT *
        FROM companies
        WHERE id = ?
        """,
        (company_id,)
    ).fetchone()


    internships = conn.execute(
        """
        SELECT *
        FROM internships
        WHERE company_id = ?
        ORDER BY id DESC
        """,
        (company_id,)
    ).fetchall()


    applications = Database.get_company_applications(
        company_id
    )


    conn.close()


    if not company:

        session.clear()

        return redirect("/company/login")


    return render_template(
        "company_dashboard.html",
        company=company,
        internships=internships,
        applications=applications
    )


# =========================================================
# COMPANY POST JOB
# =========================================================

@app.route(
    "/company/post-job",
    methods=["POST"]
)
def company_post_job():

    if "company_id" not in session:

        return redirect("/company/login")


    company_id = session["company_id"]


    title = request.form.get(
        "title",
        ""
    ).strip()


    description = request.form.get(
        "description",
        ""
    ).strip()


    location = request.form.get(
        "location",
        ""
    ).strip()


    mode = request.form.get(
        "mode",
        "On-site"
    )


    stipend_text = request.form.get(
        "stipend",
        "0"
    ).strip()


    try:

        stipend = float(
            stipend_text
        ) if stipend_text else 0

    except ValueError:

        stipend = 0


    if not title:

        return "Internship title is required."


    Database.add_internship(
        company_id=company_id,
        title=title,
        description=description,
        location=location,
        mode=mode,
        stipend=stipend,
        duration=None,
        openings=1,
        deadline=None
    )


    return redirect(
        "/company/dashboard"
    )


# =========================================================
# COMPANY APPLICATION STATUS
# =========================================================

@app.route(
    "/company/application/<int:application_id>/status",
    methods=["POST"]
)
def company_application_status(application_id):

    if "company_id" not in session:

        return redirect("/company/login")


    company_id = session["company_id"]


    status = request.form.get(
        "status",
        "Applied"
    )


    Database.update_application_status(
        application_id,
        company_id,
        status
    )


    return redirect(
        "/company/dashboard"
    )


# =========================================================
# COMPANY LOGOUT
# =========================================================

@app.route("/company/logout")
def company_logout():

    session.clear()

    return redirect(
        "/company/login"
    )


# =========================================================
# ALL COMPANIES
# =========================================================

@app.route("/companies")
def companies_list():

    conn = get_db()


    companies = conn.execute(
        """
        SELECT *
        FROM companies
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    return render_template(
        "companies_list.html",
        companies=companies
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        conn = get_db()


        admin = conn.execute(
            """
            SELECT *
            FROM admins
            WHERE email = ?
            AND password = ?
            """,
            (
                email,
                password
            )
        ).fetchone()


        conn.close()


        if admin:

            session["admin_id"] = admin["id"]

            return redirect(
                "/admin/dashboard"
            )


        return "Invalid admin email or password."


    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:

        return redirect("/admin/login")


    stats = Database.get_dashboard_stats()


    return render_template(
        "admin_dashboard.html",
        total_students=stats.get("students", 0),
        total_companies=stats.get("companies", 0),
        total_jobs=stats.get("internships", 0),
        total_applications=stats.get("applications", 0)
    )


# =========================================================
# ADMIN STUDENTS
# =========================================================

@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:

        return redirect("/admin/login")


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = get_db()


    if search:

        students = conn.execute(
            """
            SELECT
                id,
                name,
                email,
                resume
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
            SELECT
                id,
                name,
                email,
                resume
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


# =========================================================
# ADMIN STUDENT DETAILS
# =========================================================

@app.route(
    "/admin/student/<int:student_id>"
)
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

        return "Student not found."


    return render_template(
        "student_details.html",
        student=student
    )


# =========================================================
# ADMIN DELETE STUDENT
# =========================================================

@app.route(
    "/admin/student/delete/<int:student_id>",
    methods=["POST"]
)
def delete_student(student_id):

    if "admin_id" not in session:

        return redirect("/admin/login")


    conn = get_db()


    student = conn.execute(
        """
        SELECT resume
        FROM students
        WHERE id = ?
        """,
        (student_id,)
    ).fetchone()


    if student:

        conn.execute(
            """
            DELETE FROM students
            WHERE id = ?
            """,
            (student_id,)
        )


        conn.commit()


        if student["resume"]:

            resume_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                student["resume"]
            )


            if os.path.exists(resume_path):

                os.remove(resume_path)


    conn.close()


    return redirect(
        "/admin/students"
    )


# =========================================================
# ADMIN COMPANIES
# =========================================================

@app.route("/admin/companies")
def admin_companies():

    if "admin_id" not in session:

        return redirect("/admin/login")


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = get_db()


    if search:

        companies = conn.execute(
            """
            SELECT
                c.*,
                COUNT(i.id) AS internship_count
            FROM companies c
            LEFT JOIN internships i
                ON c.id = i.company_id
            WHERE c.company_name LIKE ?
               OR c.email LIKE ?
               OR c.industry LIKE ?
            GROUP BY c.id
            ORDER BY c.id DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        companies = conn.execute(
            """
            SELECT
                c.*,
                COUNT(i.id) AS internship_count
            FROM companies c
            LEFT JOIN internships i
                ON c.id = i.company_id
            GROUP BY c.id
            ORDER BY c.id DESC
            """
        ).fetchall()


    conn.close()


    return render_template(
        "admin_companies.html",
        companies=companies,
        search=search
    )


# =========================================================
# ADMIN INTERNSHIPS
# =========================================================

@app.route("/admin/internships")
def admin_internships():

    if "admin_id" not in session:

        return redirect("/admin/login")


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = get_db()


    if search:

        internships = conn.execute(
            """
            SELECT
                i.id,
                i.title,
                i.description,
                i.location,
                i.mode,
                i.stipend,
                i.duration,
                i.openings,
                i.deadline,
                i.status,
                i.created_at,
                c.company_name,
                c.industry
            FROM internships i
            JOIN companies c
                ON i.company_id = c.id
            WHERE i.title LIKE ?
               OR c.company_name LIKE ?
               OR i.location LIKE ?
               OR i.mode LIKE ?
               OR i.status LIKE ?
            ORDER BY i.id DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        internships = conn.execute(
            """
            SELECT
                i.id,
                i.title,
                i.description,
                i.location,
                i.mode,
                i.stipend,
                i.duration,
                i.openings,
                i.deadline,
                i.status,
                i.created_at,
                c.company_name,
                c.industry
            FROM internships i
            JOIN companies c
                ON i.company_id = c.id
            ORDER BY i.id DESC
            """
        ).fetchall()


    conn.close()


    return render_template(
        "admin_internships.html",
        internships=internships,
        search=search
    )


# =========================================================
# ADMIN APPLICATIONS
# =========================================================

@app.route("/admin/applications")
def admin_applications():

    if "admin_id" not in session:

        return redirect("/admin/login")


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = get_db()


    if search:

        applications = conn.execute(
            """
            SELECT
                a.id AS application_id,
                a.status,
                a.applied_at,

                s.id AS student_id,
                s.name AS student_name,
                s.email AS student_email,
                s.department,
                s.year,

                i.id AS internship_id,
                i.title AS internship_title,

                c.company_name

            FROM applications a

            JOIN students s
                ON a.student_id = s.id

            JOIN internships i
                ON a.internship_id = i.id

            JOIN companies c
                ON i.company_id = c.id

            WHERE s.name LIKE ?
               OR s.email LIKE ?
               OR i.title LIKE ?
               OR c.company_name LIKE ?
               OR a.status LIKE ?

            ORDER BY a.applied_at DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        applications = conn.execute(
            """
            SELECT
                a.id AS application_id,
                a.status,
                a.applied_at,

                s.id AS student_id,
                s.name AS student_name,
                s.email AS student_email,
                s.department,
                s.year,

                i.id AS internship_id,
                i.title AS internship_title,

                c.company_name

            FROM applications a

            JOIN students s
                ON a.student_id = s.id

            JOIN internships i
                ON a.internship_id = i.id

            JOIN companies c
                ON i.company_id = c.id

            ORDER BY a.applied_at DESC
            """
        ).fetchall()


    conn.close()


    return render_template(
        "admin_applications.html",
        applications=applications,
        search=search
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_id",
        None
    )


    return redirect(
        "/admin/login"
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

Database.create_tables()

create_table()

setup_company_database()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )