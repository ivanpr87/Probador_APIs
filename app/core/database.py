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
                base_url   TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migración: agregar base_url a instalaciones existentes sin romper el schema
        try:
            conn.execute("ALTER TABLE saved_configs ADD COLUMN base_url TEXT")
        except Exception:
            pass  # columna ya existe — ignorar

        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                config_id  INTEGER REFERENCES saved_configs(id) ON DELETE CASCADE,
                cron       TEXT NOT NULL,
                enabled    INTEGER DEFAULT 1,
                last_run   TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
