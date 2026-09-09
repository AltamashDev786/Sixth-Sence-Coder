from flask import Flask, render_template, request
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Resume upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Database aur table create karna
def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            resume TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("myweb.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Resume lena
        resume = request.files.get("resume")

        resume_filename = None

        if resume and resume.filename != "":
            resume_filename = secure_filename(resume.filename)

            resume.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    resume_filename
                )
            )

        # Database me student save karna
        conn = get_db()

        conn.execute(
            """
            INSERT INTO students
            (name, email, password, resume)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, password, resume_filename)
        )

        conn.commit()
        conn.close()

        return f"Registration successful! Welcome {name}"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM students WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            return f"Login successful! Welcome {user['name']}"
        else:
            return "Invalid email or password"

    return render_template("login.html")


if __name__ == "__main__":
    create_table()
    app.run(debug=True)