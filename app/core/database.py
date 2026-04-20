import sqlite3
from contextlib import contextmanager

from app.core.config import settings


@contextmanager
def get_connection():
    conn = sqlite3.connect(
        settings.DB_PATH,
        check_same_thread=False,
        timeout=10,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tests_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url        TEXT NOT NULL,
                method     TEXT NOT NULL,
                result     TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_configs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE,
                url        TEXT NOT NULL,
                method     TEXT NOT NULL DEFAULT 'GET',
                payload    TEXT,
                headers    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
