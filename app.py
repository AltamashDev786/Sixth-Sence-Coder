from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)

EXCEL_FILE = "database.xlsx"


def initialize_excel():
    if not os.path.exists(EXCEL_FILE):

        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:

            jobs_df = pd.DataFrame(columns=[
                "job_id",
                "company_id",
                "company_name",
                "title",
                "description",
                "skills",
                "stipend_salary",
                "location",
                "type",
                "deadline",
                "posted_on"
            ])

            students_df = pd.DataFrame(columns=[
                "student_id",
                "name",
                "branch",
                "skills",
                "email",
                "phone",
                "verification_status",
                "resume"
            ])

            applications_df = pd.DataFrame(columns=[
                "application_id",
                "job_id",
                "student_id",
                "company_id",
                "status",
                "applied_on"
            ])

            jobs_df.to_excel(writer, sheet_name="jobs", index=False)
            students_df.to_excel(writer, sheet_name="students", index=False)
            applications_df.to_excel(writer, sheet_name="applications", index=False)
            initialize_excel()

# ================= SESSION SECRET KEY =================

app.secret_key = "company-panel-secret-key-change-this-later"

DATABASE = "database.db"


# ================= DATABASE CONNECTION =================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ================= DATABASE SETUP =================

def init_db():

    conn = get_db()

    # Companies table create होगा अगर पहले से मौजूद नहीं है
    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cname TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            company_type TEXT,
            industry TEXT,
            website TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            description TEXT,
            recruiter_name TEXT,
            designation TEXT,
            recruiter_email TEXT,
            recruiter_phone TEXT,
            linkedin TEXT,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
# Jobs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            skills TEXT,
            salary TEXT,
            location TEXT,
            type TEXT,
            deadline TEXT,
            posted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
      
    # ================= OLD DATABASE SUPPORT =================
    # अगर database.db पहले से बनी हुई है और उसमें पुराने
    # columns हैं, तो missing columns automatically add होंगे।

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(companies)"
        ).fetchall()
    ]

    new_columns = {
        "phone": "TEXT",
        "company_type": "TEXT",
        "website": "TEXT",
        "address": "TEXT",
        "city": "TEXT",
        "state": "TEXT",
        "pincode": "TEXT",
        "description": "TEXT",
        "recruiter_name": "TEXT",
        "designation": "TEXT",
        "recruiter_email": "TEXT",
        "recruiter_phone": "TEXT",
        "linkedin": "TEXT",
        "password": "TEXT",
        "created_at": "TIMESTAMP"
    }

    for column, datatype in new_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE companies ADD COLUMN {column} {datatype}"
            )

    conn.commit()
    conn.close()


# Database initialize
init_db()


# ================= HOME =================

@app.route("/")
def home():

    return render_template(
        "myweb1.html"
    )


# ================= COMPANY REGISTRATION =================

@app.route("/company/register", methods=["GET", "POST"])
def company_register():

    # ================= POST REQUEST =================

    if request.method == "POST":

        # ---------- COMPANY DETAILS ----------

        cname = request.form.get(
            "cname", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        phone = request.form.get(
            "phone", ""
        ).strip()

        company_type = request.form.get(
            "company_type", ""
        ).strip()

        industry = request.form.get(
            "industry", ""
        ).strip()

        website = request.form.get(
            "website", ""
        ).strip()

        address = request.form.get(
            "address", ""
        ).strip()

        city = request.form.get(
            "city", ""
        ).strip()

        state = request.form.get(
            "state", ""
        ).strip()

        pincode = request.form.get(
            "pincode", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()


        # ---------- RECRUITER DETAILS ----------

        recruiter_name = request.form.get(
            "recruiter_name", ""
        ).strip()

        designation = request.form.get(
            "designation", ""
        ).strip()

        recruiter_email = request.form.get(
            "recruiter_email", ""
        ).strip().lower()

        recruiter_phone = request.form.get(
            "recruiter_phone", ""
        ).strip()

        linkedin = request.form.get(
            "linkedin", ""
        ).strip()


        # ---------- LOGIN DETAILS ----------

        password = request.form.get(
            "password", ""
        )

        confirm_password = request.form.get(
            "confirm_password", ""
        )


        # ================= VALIDATION =================

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


        # ================= DATABASE CONNECTION =================

        conn = get_db()


        # ================= CHECK DUPLICATE EMAIL =================

        existing_company = conn.execute(
            "SELECT id FROM companies WHERE email = ?",
            (email,)
        ).fetchone()


        if existing_company:

            conn.close()

            return render_template(
                "company_registration.html",
                error="This company email is already registered."
            )


        # ================= SECURE PASSWORD HASH =================

        hashed_password = generate_password_hash(password)


        # ================= INSERT COMPANY =================

        try:

            conn.execute("""
                INSERT INTO companies
                (
                    cname,
                    email,
                    phone,
                    company_type,
                    industry,
                    website,
                    address,
                    city,
                    state,
                    pincode,
                    description,
                    recruiter_name,
                    designation,
                    recruiter_email,
                    recruiter_phone,
                    linkedin,
                    password
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
            """,)


            conn.commit()
            conn.close()


            # ================= REGISTRATION SUCCESS =================

            return redirect(
                "/company/dashboard",
                cname=cname,
                email=email
            )


        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "company_registration.html",
                error="This company email is already registered."
            )


    # ================= GET REQUEST =================

    return render_template(
        "company_registration.html"
    )


# ================= COMPANY LOGIN =================

@app.route("/company/login", methods=["GET", "POST"])
def company_login():


    # ================= LOGIN POST =================

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )


        # ---------- DATABASE ----------

        conn = get_db()

        company = conn.execute(
            "SELECT * FROM companies WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()


        # ================= CHECK LOGIN =================

        if company and company["password"]:

            if check_password_hash(
                company["password"],
                password
            ):

                # ================= CREATE SESSION =================

                session["company_id"] = company["id"]

                session["company_name"] = company["cname"]

                session["company_email"] = company["email"]


                # ================= LOGIN SUCCESS =================

                return redirect(
                    "/company/dashboard"
                )


        # ================= LOGIN FAILED =================

        return render_template(
            "company_login.html",
            error="Invalid company email or password."
        )


    # ================= LOGIN PAGE =================

    return render_template(
        "company_login.html"
    )


# ================= COMPANY DASHBOARD =================

@app.route('/company/dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect('/company_login')
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE id=?", (session['company_id'],))
    company = cur.fetchone()
    cur.execute("SELECT * FROM jobs WHERE company_id=?", (session['company_id'],))
    jobs = cur.fetchall()
    conn.close()
    return render_template('company_dashboard.html', company=company, jobs=jobs)

@app.route('/post_job', methods=['POST'])
def post_job():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs (company_id, title, type, location, salary, skills, description) VALUES (?,?,?,?,?,?,?)",
                (session['company_id'], request.form['job_title'], request.form['job_type'], request.form['location'], request.form['salary'], request.form['skills'], request.form['description']))
    conn.commit()
    conn.close()
    return redirect('/company/dashboard')

    # ---------- DATABASE ----------

    conn = get_db()

    company = conn.execute(
        "SELECT * FROM companies WHERE id = ?",
        (session["company_id"],)
    ).fetchone()

    conn.close()


    # अगर company database में नहीं मिली
    if not company:

        session.clear()

        return redirect(
            "/company/login"
        )


    # ================= DASHBOARD =================

    return render_template(
        "company_dashboard.html",
        company=company
    )


# ================= COMPANY LOGOUT =================

@app.route("/company/logout")
def company_logout():


    # Session खत्म करें
    session.clear()


    # Login page पर वापस जाएँ
    return redirect(
        "/company/login"
    )


# ================= ALL COMPANIES =================

@app.route("/companies")
def companies_list():


    conn = get_db()

    companies = conn.execute(
        "SELECT * FROM companies"
    ).fetchall()

    conn.close()


    return render_template(
        "companies_list.html",
        companies=companies
    )


# ================= RUN APPLICATION =================

if __name__ == "__main__":

    app.run(
        debug=True
    )