from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "secret"

DB_FILE = "parish_log.db"

def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = connect()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            priest_name TEXT,
            parish_name TEXT,
            mass_type TEXT,
            log_date TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sched_date TEXT,
            sched_time TEXT,
            description TEXT
        )
    """)

    # default user
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("carlo", hash_password("1234"))
        )
    except:
        pass

    conn.commit()
    conn.close()

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = connect()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------- ADD LOG ----------
@app.route("/add-log", methods=["GET", "POST"])
def add_log():
    if request.method == "POST":
        conn = connect()
        conn.execute("""
            INSERT INTO logs (priest_name, parish_name, mass_type, log_date)
            VALUES (?, ?, ?, ?)
        """, (
            request.form["priest"],
            request.form["parish"],
            request.form["mass"],
            request.form["date"]
        ))
        conn.commit()
        conn.close()
        return redirect("/records")

    return render_template("add_log.html")

# ---------- RECORDS ----------
@app.route("/records")
def records():
    conn = connect()
    logs = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("records.html", logs=logs)

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    conn = connect()
    conn.execute("DELETE FROM logs WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/records")

# ---------- CALENDAR ----------
@app.route("/calendar", methods=["GET", "POST"])
def calendar_page():
    if request.method == "POST":
        conn = connect()
        conn.execute("""
            INSERT INTO schedules (sched_date, sched_time, description)
            VALUES (?, ?, ?)
        """, (
            request.form["date"],
            request.form["time"],
            request.form["desc"]
        ))
        conn.commit()
        conn.close()

    conn = connect()
    schedules = conn.execute("SELECT * FROM schedules").fetchall()
    conn.close()

    return render_template("calendar.html", schedules=schedules)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)