"""Database connection manager and TODO table initialization."""

from __future__ import annotations

import os
from pathlib import Path

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
