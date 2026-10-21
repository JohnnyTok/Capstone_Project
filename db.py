"""
db.py — Centralised SQLite connection manager.

Replaces the scattered sqlite3.connect() calls in admin.py, setting.py, auth.py.
All modules import get_conn() from here instead of opening their own connections.
"""
import sqlite3
import threading
import logging

logger = logging.getLogger(__name__)
_local = threading.local()
_DB_PATH = "users.db"


def get_conn() -> sqlite3.Connection:
    """Return a thread-local SQLite connection, creating it if needed."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def close_conn() -> None:
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None


def migrate() -> None:
    """Run all schema migrations idempotently — safe to call on every startup."""
    conn = get_conn()
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}

    if "preferences" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN preferences TEXT DEFAULT '{}'")
        logger.info("Migration: added 'preferences' column")

    if "first_login" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN first_login BOOLEAN DEFAULT 1")
        logger.info("Migration: added 'first_login' column")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            filename      TEXT,
            source        TEXT DEFAULT 'upload',
            total_reviews INTEGER DEFAULT 0,
            positive_pct  REAL DEFAULT 0,
            negative_pct  REAL DEFAULT 0,
            neutral_pct   REAL DEFAULT 0,
            avg_score     REAL DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id)")
    conn.commit()
    logger.info("DB migration complete")
