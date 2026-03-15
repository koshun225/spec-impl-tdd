"""Database connection manager and CRUD operations for TODO items."""

from typing import Any

import aiosqlite

DB_PATH = "todo.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_todos_completed ON todos (completed);
"""


async def get_connection(db_path: str = DB_PATH) -> aiosqlite.Connection:
    """Get a database connection with row_factory enabled."""
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db(db_path: str = DB_PATH) -> None:
    """Initialize the database schema."""
    conn = await get_connection(db_path)
    try:
        await conn.execute(CREATE_TABLE_SQL)
        await conn.execute(CREATE_INDEX_SQL)
        await conn.commit()
    finally:
        await conn.close()


async def create_todo(title: str) -> dict[str, Any]:
    """Create a new TODO item."""
    conn = await get_connection(DB_PATH)
    try:
        cursor = await conn.execute("INSERT INTO todos (title) VALUES (?)", (title,))
        await conn.commit()
        row = await conn.execute(
            "SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)
        )
        result = await row.fetchone()
        assert result is not None
        return dict(result)
    finally:
        await conn.close()


async def get_all_todos(status: str = "all") -> list[dict[str, Any]]:
    """Get all TODO items, optionally filtered by status."""
    conn = await get_connection(DB_PATH)
    try:
        if status == "completed":
            rows = await conn.execute(
                "SELECT * FROM todos WHERE completed = 1 ORDER BY created_at DESC"
            )
        elif status == "active":
            rows = await conn.execute(
                "SELECT * FROM todos WHERE completed = 0 ORDER BY created_at DESC"
            )
        else:
            rows = await conn.execute("SELECT * FROM todos ORDER BY created_at DESC")
        results = await rows.fetchall()
        return [dict(row) for row in results]
    finally:
        await conn.close()


async def get_todo_by_id(todo_id: int) -> dict[str, Any] | None:
    """Get a single TODO item by ID."""
    conn = await get_connection(DB_PATH)
    try:
        row = await conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        result = await row.fetchone()
        return dict(result) if result else None
    finally:
        await conn.close()


async def update_todo(
    todo_id: int, title: str | None = None, completed: bool | None = None
) -> dict[str, Any] | None:
    """Update a TODO item."""
    conn = await get_connection(DB_PATH)
    try:
        existing = await conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        if await existing.fetchone() is None:
            return None

        updates: list[str] = []
        params: list[object] = []
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if completed is not None:
            updates.append("completed = ?")
            params.append(completed)
        if updates:
            updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')")
            params.append(todo_id)
            await conn.execute(
                f"UPDATE todos SET {', '.join(updates)} WHERE id = ?",  # noqa: S608
                params,
            )
            await conn.commit()

        row = await conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        result = await row.fetchone()
        assert result is not None
        return dict(result)
    finally:
        await conn.close()


async def delete_todo(todo_id: int) -> bool:
    """Delete a TODO item. Returns True if deleted, False if not found."""
    conn = await get_connection(DB_PATH)
    try:
        existing = await conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
        if await existing.fetchone() is None:
            return False
        await conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        await conn.commit()
        return True
    finally:
        await conn.close()
