import os
import sqlite3
from urllib import response
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ---------------- AUTH0 CONFIG ----------------
oauth = OAuth(app)
auth0 = oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration"
)

# ---------------- GEMINI CONFIG ----------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- DB INIT ----------------
DB_PATH = "calora.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        meal TEXT,
        calories REAL,
        protein REAL,
        carbs REAL,
        fat REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        age INTEGER,
        height REAL,
        weight REAL,
        activity TEXT,
        tdee REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    age INTEGER,
    height REAL,
    weight REAL,
    activity TEXT,
    gender TEXT,
    tdee REAL
)""")


    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return render_template("index.html")

@app.route("/login")
def login():
    return auth0.authorize_redirect(redirect_uri=url_for("callback", _external=True))

@app.route("/callback")
def callback():
    token = auth0.authorize_access_token()
    session["user"] = token["userinfo"]
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?"
        f"returnTo={os.getenv('AUTH0_BASE_URL')}&client_id={os.getenv('AUTH0_CLIENT_ID')}"
    )

@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # logs
    c.execute("SELECT meal, calories, protein, carbs, fat, id FROM logs WHERE user_id=?", (user["sub"],))
    rows = c.fetchall()


    # totals
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for _, cal, p, c_, f, _id in rows:
        totals["calories"] += cal or 0
        totals["protein"] += p or 0
        totals["carbs"] += c_ or 0
        totals["fat"] += f or 0

    # user metrics (fetch both tdee and weight)
    c.execute("SELECT tdee, weight FROM users WHERE user_id=?", (user["sub"],))
    row = c.fetchone()
    tdee, weight = (row if row else (None, None))

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        logs=rows,
        totals=totals,
        tdee=tdee,
        weight=weight
    )

import json

@app.route("/chat", methods=["POST"])
def chat():
    user = session.get("user")
    if not user:
        print("Unauthorized /chat access")
        return jsonify({"error": "Not logged in"}), 403

    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "Empty input"}), 400

        print("📨 Received message:", user_input)

        # Gemini generation
        response = model.generate_content(
            f"You are Calora. Estimate macros for: {user_input}. "
            "Return valid JSON only with keys meal, calories, protein, fat, carbs."
        )
        text = getattr(response, "text", "")
        print("🧠 Gemini raw:", text)

        import json
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Gemini did not return valid JSON.")

        data = json.loads(text[start:end+1])
        print("✅ Parsed data:", data)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO logs (user_id, meal, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?)",
            (user["sub"], data["meal"], data["calories"], data["protein"], data["carbs"], data["fat"])
        )
        conn.commit()
        conn.close()

        print("💾 Saved meal log successfully.")
        return jsonify(data)

    except Exception as e:
        print("❌ Error in /chat:", e)
        return jsonify({"error": str(e)}), 500




@app.route("/register", methods=["GET", "POST"])
def register():
    user = session.get("user")
    if not user:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        age = int(request.form["age"])
        height = float(request.form["height"])
        weight = float(request.form["weight"])
        activity = request.form["activity"]
        gender = request.form["gender"]

        # Mifflin–St Jeor formula
        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        multiplier = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very": 1.9
        }[activity]
        tdee = round(bmr * multiplier, 1)

        c.execute(
        """INSERT OR REPLACE INTO users (user_id, age, height, weight, activity, gender, tdee)
       VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user["sub"], age, height, weight, activity, gender, tdee)
)
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    # GET request → load existing metrics if present
    c.execute("SELECT age, height, weight, activity, gender FROM users WHERE user_id=?", (user["sub"],))
    row = c.fetchone()
    conn.close()

    user_data = {
    "age": row[0] if row else "",
    "height": row[1] if row else "",
    "weight": row[2] if row else "",
    "activity": row[3] if row else "",
    "gender": row[4] if row else ""
    }

    return render_template("register.html", user_data=user_data)


@app.route("/delete_log/<int:log_id>", methods=["POST"])
def delete_log(log_id):
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 403

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM logs WHERE id=? AND user_id=?", (log_id, user["sub"]))
    conn.commit()
    conn.close()

    return jsonify({"success": True})



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
