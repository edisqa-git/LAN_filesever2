import sqlite3
from pathlib import Path

from flask import current_app, g


USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

FILES_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  size INTEGER NOT NULL,
  uploaded_by INTEGER NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
"""


def _ensure_db_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE"])
        _ensure_db_parent(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(_=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.execute(USERS_SCHEMA)
    db.execute(FILES_SCHEMA)
    db.commit()


def query_one(query: str, params: tuple = ()):
    return get_db().execute(query, params).fetchone()


def query_all(query: str, params: tuple = ()):
    return get_db().execute(query, params).fetchall()


def execute(query: str, params: tuple = ()) -> int:
    cursor = get_db().execute(query, params)
    get_db().commit()
    return cursor.lastrowid
