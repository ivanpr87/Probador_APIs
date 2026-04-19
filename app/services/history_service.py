import sqlite3
import json

DB_PATH = "sentinel.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tests_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url        TEXT,
                method     TEXT,
                result     TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_test(url: str, method: str, result: dict):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO tests_history (url, method, result) VALUES (?, ?, ?)",
            (url, method, json.dumps(result))
        )


def get_tests(limit: int = 50) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, url, method, result, created_at "
            "FROM tests_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()

    history = []
    for r in rows:
        parsed = json.loads(r["result"])
        history.append({
            "id": r["id"],
            "url": r["url"],
            "method": r["method"],
            "quality_score": parsed.get("quality_score"),
            "severity": parsed.get("severity"),
            "total_tests": parsed.get("total_tests"),
            "created_at": r["created_at"],
        })
    return history
