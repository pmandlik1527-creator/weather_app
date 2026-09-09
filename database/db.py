"""
National Weather Big Data Analytics Platform (NWBDAP)
Database connection manager and lifecycle handlers
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
import config

_local = threading.local()

def get_connection():
    """Returns a thread-local SQLite connection with WAL enabled."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(
            str(config.DB_PATH),
            timeout=30.0,
            check_same_thread=False
        )
        _local.conn.row_factory = sqlite3.Row
        # Enable Write-Ahead Logging for high-throughput concurrent writes
        _local.conn.execute("PRAGMA journal_mode = WAL;")
        _local.conn.execute("PRAGMA synchronous = NORMAL;")
        _local.conn.execute("PRAGMA foreign_keys = ON;")
    return _local.conn

@contextmanager
def db_cursor():
    """Context manager for obtaining a database cursor with automatic commit/rollback."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

def init_db():
    """Initializes the database schema if not already present."""
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    conn.executescript(schema_sql)
    conn.commit()
    print("[DB] Database initialized successfully with WAL mode.")
