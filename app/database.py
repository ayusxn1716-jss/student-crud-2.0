"""SQLite connection handling and schema."""
import os
import sqlite3
from pathlib import Path
from typing import Iterator

DEFAULT_DB = Path(__file__).resolve().parent.parent / "students.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,          -- ISO date YYYY-MM-DD
    email           TEXT UNIQUE,
    phone           TEXT,
    course          TEXT,
    address         TEXT,
    enrollment_date TEXT,                   -- ISO date YYYY-MM-DD
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def db_path() -> str:
    # Read at call time so tests / users can override via environment.
    return os.getenv("STUDENTS_DB_PATH", str(DEFAULT_DB))


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
