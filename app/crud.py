"""All database access lives here. Every query is parameterised (no SQL injection)."""
import sqlite3

COLUMNS = ("name", "date_of_birth", "email", "phone",
           "course", "address", "enrollment_date")


class DuplicateEmailError(Exception):
    pass


def _norm(data: dict) -> dict:
    out = dict(data)
    if out.get("email"):
        out["email"] = out["email"].lower()
    return out


def create_student(conn: sqlite3.Connection, data: dict) -> dict:
    data = _norm(data)
    values = [data.get(c) for c in COLUMNS]
    try:
        cur = conn.execute(
            f"INSERT INTO students ({', '.join(COLUMNS)}) "
            f"VALUES ({', '.join('?' * len(COLUMNS))})", values)
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise DuplicateEmailError from exc
    return get_student(conn, cur.lastrowid)


def get_student(conn: sqlite3.Connection, student_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def _build_filters(name=None, course=None, born_after=None, born_before=None):
    where, params = [], []
    if name:
        where.append("name LIKE ?")
        params.append(f"%{name}%")
    if course:
        where.append("course LIKE ?")
        params.append(f"%{course}%")
    if born_after:
        where.append("date_of_birth > ?")
        params.append(str(born_after))
    if born_before:
        where.append("date_of_birth < ?")
        params.append(str(born_before))
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    return clause, params


def list_students(conn, *, name=None, course=None, born_after=None,
                  born_before=None, limit=100, offset=0) -> list[dict]:
    clause, params = _build_filters(name, course, born_after, born_before)
    rows = conn.execute(
        f"SELECT * FROM students {clause} ORDER BY id LIMIT ? OFFSET ?",
        [*params, limit, offset]).fetchall()
    return [dict(r) for r in rows]


def count_students(conn, **filters) -> int:
    clause, params = _build_filters(**filters)
    return conn.execute(f"SELECT COUNT(*) FROM students {clause}", params).fetchone()[0]


def distinct_courses(conn) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT course FROM students WHERE course IS NOT NULL").fetchall()
    return [r[0] for r in rows]


def update_student(conn, student_id: int, fields: dict) -> dict | None:
    """Update only whitelisted columns. Returns None if the student doesn't exist."""
    fields = _norm({k: v for k, v in fields.items() if k in COLUMNS})
    if get_student(conn, student_id) is None:
        return None
    if fields:
        assignments = ", ".join(f"{k} = ?" for k in fields)
        try:
            conn.execute(f"UPDATE students SET {assignments} WHERE id = ?",
                         [*fields.values(), student_id])
            conn.commit()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise DuplicateEmailError from exc
    return get_student(conn, student_id)


def delete_student(conn, student_id: int) -> bool:
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    return cur.rowcount > 0
