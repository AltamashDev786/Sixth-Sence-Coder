import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "database.db"


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    # Foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ---------------------------------------------------------
# CREATE ALL TABLES
# ---------------------------------------------------------

def create_tables():

    conn = get_db()

    # =========================
    # STUDENTS
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            resume TEXT,
            department TEXT,
            year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # =========================
    # COMPANIES
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            industry TEXT,
            description TEXT,
            website TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # =========================
    # SKILLS
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            category TEXT
        )
    """)


    # =========================
    # STUDENT SKILLS
    # Student <-> Skills
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS student_skills (
            student_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,

            proficiency TEXT DEFAULT 'Beginner',

            PRIMARY KEY (student_id, skill_id),

            FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE,

            FOREIGN KEY (skill_id)
                REFERENCES skills(id)
                ON DELETE CASCADE
        )
    """)


    # =========================
    # INTERNSHIPS
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company_id INTEGER NOT NULL,

            title TEXT NOT NULL,
            description TEXT,

            location TEXT,
            mode TEXT DEFAULT 'On-site',

            stipend REAL DEFAULT 0,

            duration TEXT,

            openings INTEGER DEFAULT 1,

            deadline DATE,

            status TEXT DEFAULT 'Open',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (company_id)
                REFERENCES companies(id)
                ON DELETE CASCADE
        )
    """)


    # =========================
    # INTERNSHIP REQUIRED SKILLS
    # Internship <-> Skills
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS internship_skills (
            internship_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,

            required_level TEXT DEFAULT 'Beginner',

            PRIMARY KEY (internship_id, skill_id),

            FOREIGN KEY (internship_id)
                REFERENCES internships(id)
                ON DELETE CASCADE,

            FOREIGN KEY (skill_id)
                REFERENCES skills(id)
                ON DELETE CASCADE
        )
    """)


    # =========================
    # APPLICATIONS
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,
            internship_id INTEGER NOT NULL,

            status TEXT DEFAULT 'Applied',

            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE,

            FOREIGN KEY (internship_id)
                REFERENCES internships(id)
                ON DELETE CASCADE,

            UNIQUE(student_id, internship_id)
        )
    """)


    conn.commit()
    conn.close()


# ---------------------------------------------------------
# STUDENT FUNCTIONS
# ---------------------------------------------------------

def add_student(name, email, password, resume=None,
                department=None, year=None):

    conn = get_db()

    hashed_password = generate_password_hash(password)

    try:

        cursor = conn.execute("""
            INSERT INTO students
            (name, email, password, resume, department, year)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            resume,
            department,
            year
        ))

        conn.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:

        return None

    finally:

        conn.close()


def authenticate_student(email, password):

    conn = get_db()

    student = conn.execute("""
        SELECT *
        FROM students
        WHERE email = ?
    """, (email,)).fetchone()

    conn.close()

    if student and check_password_hash(
        student["password"],
        password
    ):
        return student

    return None


def get_student(student_id):

    conn = get_db()

    student = conn.execute("""
        SELECT id, name, email, resume, department, year, created_at
        FROM students
        WHERE id = ?
    """, (student_id,)).fetchone()

    conn.close()

    return student


# ---------------------------------------------------------
# SKILL FUNCTIONS
# ---------------------------------------------------------

def add_skill(skill_name, category=None):

    conn = get_db()

    try:

        cursor = conn.execute("""
            INSERT INTO skills
            (skill_name, category)
            VALUES (?, ?)
        """, (skill_name, category))

        conn.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:

        existing = conn.execute("""
            SELECT id
            FROM skills
            WHERE skill_name = ?
        """, (skill_name,)).fetchone()

        return existing["id"] if existing else None

    finally:

        conn.close()


def add_student_skill(student_id, skill_id, proficiency="Beginner"):

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO student_skills
            (student_id, skill_id, proficiency)
            VALUES (?, ?, ?)
        """, (
            student_id,
            skill_id,
            proficiency
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


def get_student_skills(student_id):

    conn = get_db()

    skills = conn.execute("""
        SELECT
            s.id,
            s.skill_name,
            s.category,
            ss.proficiency

        FROM student_skills ss

        JOIN skills s
        ON ss.skill_id = s.id

        WHERE ss.student_id = ?

        ORDER BY s.skill_name
    """, (student_id,)).fetchall()

    conn.close()

    return skills


# ---------------------------------------------------------
# COMPANY FUNCTIONS
# ---------------------------------------------------------

def add_company(
    company_name,
    email=None,
    phone=None,
    industry=None,
    description=None,
    website=None
):

    conn = get_db()

    try:

        cursor = conn.execute("""
            INSERT INTO companies
            (
                company_name,
                email,
                phone,
                industry,
                description,
                website
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            company_name,
            email,
            phone,
            industry,
            description,
            website
        ))

        conn.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:

        return None

    finally:

        conn.close()


# ---------------------------------------------------------
# INTERNSHIP FUNCTIONS
# ---------------------------------------------------------

def add_internship(
    company_id,
    title,
    description=None,
    location=None,
    mode="On-site",
    stipend=0,
    duration=None,
    openings=1,
    deadline=None
):

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO internships
        (
            company_id,
            title,
            description,
            location,
            mode,
            stipend,
            duration,
            openings,
            deadline
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company_id,
        title,
        description,
        location,
        mode,
        stipend,
        duration,
        openings,
        deadline
    ))

    conn.commit()

    internship_id = cursor.lastrowid

    conn.close()

    return internship_id


def add_internship_skill(
    internship_id,
    skill_id,
    required_level="Beginner"
):

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO internship_skills
            (
                internship_id,
                skill_id,
                required_level
            )
            VALUES (?, ?, ?)
        """, (
            internship_id,
            skill_id,
            required_level
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# ---------------------------------------------------------
# INTERNSHIP LIST
# ---------------------------------------------------------

def get_all_internships():

    conn = get_db()

    internships = conn.execute("""
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

            c.company_name,
            c.industry

        FROM internships i

        JOIN companies c
        ON i.company_id = c.id

        ORDER BY i.created_at DESC
    """).fetchall()

    conn.close()

    return internships


# ---------------------------------------------------------
# SKILL MATCHING
# ---------------------------------------------------------

def get_matching_internships(student_id):

    conn = get_db()

    internships = conn.execute("""
        SELECT DISTINCT

            i.id,
            i.title,
            i.description,
            i.location,
            i.mode,
            i.stipend,
            i.duration,
            i.deadline,

            c.company_name,

            COUNT(isk.skill_id) AS matched_skills

        FROM internships i

        JOIN companies c
        ON i.company_id = c.id

        JOIN internship_skills isk
        ON i.id = isk.internship_id

        JOIN student_skills ssk
        ON isk.skill_id = ssk.skill_id

        WHERE ssk.student_id = ?

        AND i.status = 'Open'

        GROUP BY i.id

        ORDER BY matched_skills DESC
    """, (student_id,)).fetchall()

    conn.close()

    return internships


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

def apply_for_internship(student_id, internship_id):

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO applications
            (
                student_id,
                internship_id
            )
            VALUES (?, ?)
        """, (
            student_id,
            internship_id
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


def get_student_applications(student_id):

    conn = get_db()

    applications = conn.execute("""
        SELECT

            a.id,
            a.status,
            a.applied_at,

            i.title,

            c.company_name

        FROM applications a

        JOIN internships i
        ON a.internship_id = i.id

        JOIN companies c
        ON i.company_id = c.id

        WHERE a.student_id = ?

        ORDER BY a.applied_at DESC
    """, (student_id,)).fetchall()

    conn.close()

    return applications


# ---------------------------------------------------------
# DASHBOARD STATISTICS
# ---------------------------------------------------------

def get_dashboard_stats():

    conn = get_db()

    students = conn.execute(
        "SELECT COUNT(*) AS count FROM students"
    ).fetchone()["count"]

    companies = conn.execute(
        "SELECT COUNT(*) AS count FROM companies"
    ).fetchone()["count"]

    internships = conn.execute(
        "SELECT COUNT(*) AS count FROM internships"
    ).fetchone()["count"]

    applications = conn.execute(
        "SELECT COUNT(*) AS count FROM applications"
    ).fetchone()["count"]

    conn.close()

    return {
        "students": students,
        "companies": companies,
        "internships": internships,
        "applications": applications
    }


# ---------------------------------------------------------
# INITIALIZE DATABASE
# ---------------------------------------------------------

if __name__ == "__main__":

    create_tables()

    print("====================================")
    print("Database initialized successfully!")
    print("database.db created/updated.")
    print("====================================")
