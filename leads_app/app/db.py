import sqlite3
import os
from contextlib import contextmanager
from .config import Config


def get_db(db_path=None) -> sqlite3.Connection:
    """Return a new SQLite connection with WAL mode and dict factory."""
    path = db_path or Config.DATABASE_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_ctx(db_path=None):
    """Context manager for DB transactions."""
    db = get_db(db_path)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def query_one(sql: str, params=()) -> dict | None:
    conn = get_db()
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def query_all(sql: str, params=()) -> list[dict]:
    conn = get_db()
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def execute(sql: str, params=()) -> int:
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    rowcount = cur.rowcount
    conn.close()
    return rowcount
