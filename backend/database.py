"""SQLite connection and schema management."""

import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

from flask import current_app


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo'
        CHECK (status IN ('todo', 'in_progress', 'done')),
    created_at TEXT NOT NULL
);
"""


@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    """Yield a configured connection and always close it afterward."""
    database_path = current_app.config["DATABASE"]
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: Optional[str] = None) -> None:
    """Create the database file and tasks table if they do not exist."""
    if database_path is None:
        database_path = current_app.config["DATABASE"]

    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()
