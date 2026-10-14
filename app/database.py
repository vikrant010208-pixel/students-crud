"""SQLite connection helpers. Uses the standard-library sqlite3 module."""
import os
import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    date_of_birth   TEXT    NOT NULL,          -- ISO format YYYY-MM-DD
    email           TEXT    UNIQUE,
    phone           TEXT,
    course          TEXT,
    address         TEXT,
    enrollment_date TEXT
);
"""


def db_path() -> str:
    # Read at call time so tests can point to a temporary database.
    return os.getenv("STUDENTS_DB", "students.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
