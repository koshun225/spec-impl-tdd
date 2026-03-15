"""Database connection manager and TODO table initialization."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import Any

import aiosqlite

# Module-level connection reference
_connection: aiosqlite.Connection | None = None

# Default database path: todo.db in the backend directory
_DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "todo.db")


async def init_db(db_path: str | None = None) -> None:
    """Initialise the database: create the todos table and indexes.

    This function is idempotent — calling it multiple times is safe.

    Args:
        db_path: Optional path to the SQLite database file.
                 Defaults to ``todo.db`` in the backend directory.
    """
    global _connection  # noqa: PLW0603

    if db_path is None:
        db_path = _DEFAULT_DB_PATH

    _connection = await aiosqlite.connect(db_path)

    # Enable WAL mode for better concurrent read performance
    await _connection.execute("PRAGMA journal_mode=WAL")

    # Create the todos table if it does not exist
    await _connection.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """
    )

    # Create index on completed column for filtering
    await _connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_todos_completed ON todos (completed)
        """
    )

    await _connection.commit()


async def get_connection() -> aiosqlite.Connection:
    """Return the current database connection.

    Returns:
        The active ``aiosqlite.Connection``.

    Raises:
        RuntimeError: If ``init_db`` has not been called yet.
    """
    if _connection is None:
        msg = "Database not initialised. Call init_db() first."
        raise RuntimeError(msg)
    return _connection


async def close_db() -> None:
    """Close the database connection if one is open.

    Safe to call even when no connection exists.
    """
    global _connection  # noqa: PLW0603

    if _connection is not None:
        await _connection.close()
        _connection = None


async def create_todo(title: str) -> dict[str, Any]:
    """Insert a new todo into the database and return it as a dict."""
    from datetime import datetime

    now = datetime.now(UTC).isoformat()
    conn = await get_connection()
    sql = (
        "INSERT INTO todos (title, completed, created_at, updated_at)"
        " VALUES (?, ?, ?, ?)"
    )
    cursor = await conn.execute(sql, (title, False, now, now))
    await conn.commit()
    todo_id = cursor.lastrowid
    return {
        "id": todo_id,
        "title": title,
        "completed": False,
        "created_at": now,
        "updated_at": now,
    }


async def get_all_todos(status: str = "all") -> list[dict[str, Any]]:
    """Select todos from the database with optional status filter."""
    conn = await get_connection()
    cols = "id, title, completed, created_at, updated_at"
    if status == "active":
        cursor = await conn.execute(f"SELECT {cols} FROM todos WHERE completed = 0")
    elif status == "completed":
        cursor = await conn.execute(f"SELECT {cols} FROM todos WHERE completed = 1")
    else:
        cursor = await conn.execute(f"SELECT {cols} FROM todos")
    rows = await cursor.fetchall()
    return [
        {
            "id": row[0],
            "title": row[1],
            "completed": bool(row[2]),
            "created_at": row[3],
            "updated_at": row[4],
        }
        for row in rows
    ]


async def get_todo_by_id(todo_id: int) -> dict[str, Any] | None:
    """Select a single todo by ID, returning None if not found."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT id, title, completed, created_at, updated_at FROM todos WHERE id = ?",
        (todo_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "title": row[1],
        "completed": bool(row[2]),
        "created_at": row[3],
        "updated_at": row[4],
    }


async def update_todo(
    todo_id: int, title: str | None, completed: bool | None
) -> dict[str, Any] | None:
    """Update a todo's fields and return the updated row, or None if not found."""
    from datetime import datetime

    existing = await get_todo_by_id(todo_id)
    if existing is None:
        return None

    new_title = title if title is not None else existing["title"]
    new_completed = completed if completed is not None else existing["completed"]
    now = datetime.now(UTC).isoformat()

    conn = await get_connection()
    await conn.execute(
        "UPDATE todos SET title = ?, completed = ?, updated_at = ? WHERE id = ?",
        (new_title, new_completed, now, todo_id),
    )
    await conn.commit()

    return {
        "id": todo_id,
        "title": new_title,
        "completed": new_completed,
        "created_at": existing["created_at"],
        "updated_at": now,
    }


async def delete_todo(todo_id: int) -> bool:
    """Delete a todo by ID. Return True if a row was deleted, False otherwise."""
    conn = await get_connection()
    cursor = await conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    await conn.commit()
    return cursor.rowcount > 0
