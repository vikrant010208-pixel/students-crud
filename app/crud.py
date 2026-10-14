"""Database operations. All SQL is parameterised (no string-built queries)."""
import sqlite3
from typing import Optional

from .database import get_conn

COLUMNS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


class DuplicateEmail(Exception):
    pass


def _to_params(data: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in data.items()}


def create_student(data: dict) -> dict:
    values = _to_params({c: data.get(c) for c in COLUMNS})
    try:
        with get_conn() as conn:
            cur = conn.execute(
                f"INSERT INTO students ({', '.join(COLUMNS)}) "
                f"VALUES ({', '.join(':' + c for c in COLUMNS)})",
                values,
            )
            row = conn.execute("SELECT * FROM students WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        raise DuplicateEmail()
    return dict(row)


def get_student(student_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def list_students(name=None, course=None, born_after=None, born_before=None,
                  limit=100, offset=0) -> list[dict]:
    sql, params = "SELECT * FROM students WHERE 1=1", []
    if name:
        sql += " AND name LIKE ?"
        params.append(f"%{name}%")
    if course:
        sql += " AND course LIKE ?"
        params.append(f"%{course}%")
    if born_after:
        sql += " AND date_of_birth > ?"
        params.append(born_after.isoformat())
    if born_before:
        sql += " AND date_of_birth < ?"
        params.append(born_before.isoformat())
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params += [limit, offset]
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def count_students() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]


def update_student(student_id: int, data: dict) -> Optional[dict]:
    values = _to_params({c: data.get(c) for c in COLUMNS})
    try:
        with get_conn() as conn:
            cur = conn.execute(
                f"UPDATE students SET {', '.join(c + ' = :' + c for c in COLUMNS)} "
                "WHERE id = :id",
                {**values, "id": student_id},
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    except sqlite3.IntegrityError:
        raise DuplicateEmail()
    return dict(row)


def delete_student(student_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        return cur.rowcount > 0
