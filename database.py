import sqlite3

def init_db():
    conn = sqlite3.connect("calora.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth0_sub TEXT UNIQUE,
        name TEXT,
        email TEXT,
        age INTEGER,
        height REAL,
        weight REAL,
        activity TEXT,
        tdee REAL
    )
""")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()