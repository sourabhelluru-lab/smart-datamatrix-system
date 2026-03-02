from flask import Flask, render_template, request, redirect, url_for, session
from pylibdmtx.pylibdmtx import encode
from PIL import Image
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id TEXT PRIMARY KEY,
        manufacturer TEXT,
        name TEXT,
        brand TEXT,
        mfg_date TEXT,
        expiry TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- Manufacturer Users ----------------
users = {
    "pfizer": "1234",
    "sunpharma": "abcd",
    "cipla": "cipla123",
    "drreddy": "reddy123",
    "lupin": "lupin123",
    "zydus": "zydus123"
}

# ---------------- Additional Medicine Info ----------------
additional_info = {
    "paracetamol": {
        "composition": "Paracetamol 500mg",
        "usage": "Used for fever and mild to moderate pain relief",
        "storage": "Store below 25°C in a dry place",
        "warning": "Do not exceed recommended dose",
        "mrp": "₹45 per strip"
    },
    "dolo 650": {
        "composition": "Paracetamol 650mg",
        "usage": "Used for fever and body pain",
        "storage": "Keep in cool and dry place",
        "warning": "Avoid overdose; liver damage risk",
        "mrp": "₹35 per strip"
    },
    "cetirizine": {
        "composition": "Cetirizine Hydrochloride 10mg",
        "usage": "Used for allergy symptoms",
        "storage": "Store at room temperature",
        "warning": "May cause drowsiness",
        "mrp": "₹20 per strip"
    },
    "cyclopam": {
        "composition": "Dicycloverine + Paracetamol",
        "usage": "Used for abdominal pain and cramps",
        "storage": "Store below 30°C",
        "warning": "Use under medical supervision",
        "mrp": "₹55 per strip"
    },
    "avomin": {
        "composition": "Promethazine Theoclate 25mg",
        "usage": "Prevention of motion sickness",
        "storage": "Store in dry place",
        "warning": "May cause drowsiness",
        "mrp": "₹25 per strip"
    }
}

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("generate_page"))
        else:
            return "Invalid Credentials"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# ---------------- GENERATE ----------------
@app.route("/generate", methods=["GET", "POST"])
def generate_page():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        med_id = request.form["med_id"]
        name = request.form["name"]
        brand = request.form["brand"]
        mfg_date = request.form["mfg_date"]
        expiry = request.form["expiry"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO medicines (id, manufacturer, name, brand, mfg_date, expiry, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            med_id,
            session["user"],
            name,
            brand,
            mfg_date,
            expiry,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        data = f"http://127.0.0.1:8000/verify/{med_id}"

        encoded = encode(data.encode("utf-8"))

        img = Image.frombytes(
            "RGB",
            (encoded.width, encoded.height),
            encoded.pixels
        )

        img = img.resize((300, 300), Image.NEAREST)

        os.makedirs("static/images", exist_ok=True)

        img_path = f"static/images/{med_id}.png"
        img.save(img_path)

        return render_template("result.html", img_path=img_path)

    return render_template("generate.html")

# ---------------- VERIFY ----------------
@app.route("/verify/<med_id>")
def verify(med_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT manufacturer, name, brand, mfg_date, expiry, created_at 
        FROM medicines 
        WHERE id = ?
    """, (med_id,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        return "Medicine Not Found"

    med = {
        "manufacturer": row[0],
        "name": row[1],
        "brand": row[2],
        "mfg_date": row[3],
        "expiry": row[4],
        "created_at": row[5]
    }

    # -------- Expiry Auto Validation --------
    today = datetime.today().date()
    expiry_date = datetime.strptime(med["expiry"], "%Y-%m-%d").date()

    if expiry_date < today:
        med["status"] = "expired"
    else:
        med["status"] = "valid"

    med_name_clean = med["name"].strip().lower()
    extra = additional_info.get(med_name_clean)

    return render_template("verify.html", med=med, extra=extra)

# ---------------- PROFILE DASHBOARD ----------------
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM medicines 
        WHERE manufacturer = ?
    """, (session["user"],))
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, name, brand, mfg_date, expiry, created_at
        FROM medicines
        WHERE manufacturer = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (session["user"],))
    records = cursor.fetchall()

    conn.close()

    return render_template(
        "profile.html",
        username=session["user"],
        total=total,
        records=records
    )

# ---------------- SCANNER ----------------
@app.route("/scan")
def scan():
    return render_template("scan.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)