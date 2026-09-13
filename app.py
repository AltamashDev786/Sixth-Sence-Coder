from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
import openpyxl

app = Flask(__name__)
app.secret_key = "sixsense-coders-secret-key"

UPLOAD_FOLDER = "static/uploads"
EXCEL_FILE = "users.xlsx"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- Excel ka function ---
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Students"
        ws.append(["ID", "Name", "Email", "Password", "Resume"])
        wb.save(EXCEL_FILE)

def save_to_excel(name, email, password, resume_filename):
    init_excel()
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    # duplicate email check
    for row in ws.iter_rows(min_row=2):
        if row[2].value == email:
            return False # already exists
    new_id = ws.max_row
    ws.append([new_id, name, email, password, resume_filename])
    wb.save(EXCEL_FILE)
    return True

def check_login_excel(email, password):
    if not os.path.exists(EXCEL_FILE):
        return None
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=True):
        # row = ID, Name, Email, Password, Resume
        if row[2] == email and row[3] == password:
            return {"id": row[0], "name": row[1], "email": row[2], "resume": row[4]}
    return None

# --- SQLite (backup ke liye rakha hai) ---
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            resume TEXT
        )
    """)
    conn.commit()
    conn.close()
    init_excel()

# --- Routes (Sare pages connect) ---
@app.route('/')
def home():
    return render_template('myweb.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        resume = request.files.get("resume")
        resume_filename = None
        if resume and resume.filename!= "":
            resume_filename = secure_filename(resume.filename)
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))

        # 1. Excel me save
        saved = save_to_excel(name, email, password, resume_filename)
        if not saved:
            return "Email already registered! <a href='/login'>Login karo</a>"

        # 2. DB me bhi save (optional backup)
        try:
            conn = get_db()
            conn.execute("INSERT INTO students (name, email, password, resume) VALUES (?,?,?,?)",
                         (name, email, password, resume_filename))
            conn.commit()
            conn.close()
        except:
            pass

        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Excel se match karo
        user = check_login_excel(email, password)

        if user:
            return render_template('dashboard.html', user=user)
        else:
            return "Invalid email or password! <a href='/login'>Try again</a>"

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', user={"name": "User"})

if __name__ == "__main__":
    create_table()
    app.run(debug=True)