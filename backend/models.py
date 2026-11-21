"""Data access functions for tasks."""

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


TASK_STATUSES = frozenset({"todo", "in_progress", "done"})
Task = Dict[str, Any]


def list_tasks(connection: sqlite3.Connection) -> List[Task]:
    rows = connection.execute(
        "SELECT id, title, description, status, created_at "
        "FROM tasks ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_task(connection: sqlite3.Connection, task_id: int) -> Optional[Task]:
    row = connection.execute(
        "SELECT id, title, description, status, created_at "
        "FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def create_task(
    connection: sqlite3.Connection,
    title: str,
    description: str,
    status: str,
) -> Task:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cursor = connection.execute(
        "INSERT INTO tasks (title, description, status, created_at) "
        "VALUES (?, ?, ?, ?)",
        (title, description, status, created_at),
    )
    task = get_task(connection, cursor.lastrowid)
    if task is None:
        raise sqlite3.DatabaseError("Task was not available after insertion.")
    return task


def update_task(
    connection: sqlite3.Connection,
    task_id: int,
    changes: Dict[str, str],
) -> Optional[Task]:
    if not changes:
        return get_task(connection, task_id)

    columns = ", ".join(f"{column} = ?" for column in changes)
    values = list(changes.values()) + [task_id]
    connection.execute(f"UPDATE tasks SET {columns} WHERE id = ?", values)
    return get_task(connection, task_id)


def delete_task(connection: sqlite3.Connection, task_id: int) -> bool:
    cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount > 0
