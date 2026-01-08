import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/app.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            filename TEXT,
            filepath TEXT,
            uploaded_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT,
            answer TEXT,
            created_at TEXT
        )
        """)

        conn.commit()

def create_session(session_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions(session_id, created_at) VALUES (?, ?)",
            (session_id, datetime.utcnow().isoformat()),
        )
        conn.commit()

def log_document(session_id: str, filename: str, filepath: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO documents(session_id, filename, filepath, uploaded_at) VALUES (?, ?, ?, ?)",
            (session_id, filename, filepath, datetime.utcnow().isoformat()),
        )
        conn.commit()

def log_message(session_id: str, role: str, content: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.utcnow().isoformat()),
        )
        conn.commit()

def log_query(session_id: str, question: str, answer: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO queries(session_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (session_id, question, answer, datetime.utcnow().isoformat()),
        )
        conn.commit()

def get_recent_messages(session_id: str, limit: int = 10):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        rows = cur.fetchall()
    return list(reversed(rows))
