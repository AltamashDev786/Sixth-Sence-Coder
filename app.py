from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# Database banao
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password TEXT)')
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('myweb.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect('/')
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000) 