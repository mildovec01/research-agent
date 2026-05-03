import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "memory" / "state.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS research_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_research(topic: str, results: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO research_cache (topic, results, created_at) VALUES (?, ?, ?)",
        (topic, json.dumps(results), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_recent_research(topic: str, hours: int = 24) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """SELECT results FROM research_cache
           WHERE topic = ?
           AND created_at > datetime('now', ?)
           ORDER BY created_at DESC LIMIT 1""",
        (topic, f"-{hours} hours"),
    )
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def log_run(run_id: str, status: str, summary: str = ""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO run_log (run_id, status, summary, created_at) VALUES (?, ?, ?, ?)",
        (run_id, status, summary, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
