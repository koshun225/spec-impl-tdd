"""Tests for database connection manager and TODO table initialization.

Verifies the contract specifications from data-model.md:
- TODO table schema (id, title, completed, created_at, updated_at)
- Column constraints (types, NOT NULL, defaults)
- Index on completed column for filtering
- Database connection management (async SQLite via aiosqlite)
- Table initialization is idempotent (safe to call multiple times)
"""

from __future__ import annotations

import os

import aiosqlite
import pytest

from app.database import close_db, get_connection, init_db


# ---------------------------------------------------------------------------
# Table Creation & Schema Tests
# ---------------------------------------------------------------------------


class TestInitDb:
    """Test database initialization and table creation."""

    async def test_init_db_creates_todos_table(self, test_db_path: str) -> None:
        """init_db should create the 'todos' table in the database."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='todos'"
            )
            row = await cursor.fetchone()
            assert row is not None, "todos table should exist after init_db"
            assert row[0] == "todos"

    async def test_init_db_is_idempotent(self, test_db_path: str) -> None:
        """Calling init_db multiple times should not raise errors."""
        await init_db(test_db_path)
        # Second call should succeed without error (IF NOT EXISTS)
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='todos'"
            )
            row = await cursor.fetchone()
            assert row is not None

    async def test_init_db_creates_database_file(self, test_db_path: str) -> None:
        """init_db should create the database file on disk."""
        assert not os.path.exists(test_db_path)
        await init_db(test_db_path)
        assert os.path.exists(test_db_path)


# ---------------------------------------------------------------------------
# Schema Column Tests
# ---------------------------------------------------------------------------


class TestTodosTableSchema:
    """Verify the todos table schema matches the data model contract."""

    async def _get_columns(self, db_path: str) -> dict[str, dict]:
        """Helper: return column info keyed by column name."""
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("PRAGMA table_info(todos)")
            rows = await cursor.fetchall()
            # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
            return {
                row[1]: {
                    "cid": row[0],
                    "type": row[2].upper(),
                    "notnull": bool(row[3]),
                    "default": row[4],
                    "pk": bool(row[5]),
                }
                for row in rows
            }

    async def test_table_has_all_required_columns(self, test_db_path: str) -> None:
        """The todos table must have id, title, completed, created_at, updated_at."""
        await init_db(test_db_path)
        columns = await self._get_columns(test_db_path)
        expected_columns = {"id", "title", "completed", "created_at", "updated_at"}
        assert set(columns.keys()) == expected_columns

    async def test_id_column_is_integer_primary_key(self, test_db_path: str) -> None:
        """id must be INTEGER PRIMARY KEY (auto-increment)."""
        await init_db(test_db_path)
        columns = await self._get_columns(test_db_path)
        id_col = columns["id"]
        assert id_col["type"] == "INTEGER"
        assert id_col["pk"] is True

    async def test_title_column_is_text_not_null(self, test_db_path: str) -> None:
        """title must be TEXT NOT NULL."""
        await init_db(test_db_path)
        columns = await self._get_columns(test_db_path)
        title_col = columns["title"]
        assert title_col["type"] == "TEXT"
        assert title_col["notnull"] is True

    async def test_completed_column_is_boolean_not_null_default_false(
        self, test_db_path: str
    ) -> None:
        """completed must be BOOLEAN NOT NULL DEFAULT 0 (false)."""
        await init_db(test_db_path)
        columns = await self._get_columns(test_db_path)
        completed_col = columns["completed"]
        assert completed_col["type"] == "BOOLEAN"
        assert completed_col["notnull"] is True
        assert completed_col["default"] == "0"

    async def test_created_at_column_is_timestamp_not_null(
        self, test_db_path: str
    ) -> None:
        """created_at must be TIMESTAMP NOT NULL."""
        await init_db(test_db_path)
        columns = await self._get_columns(test_db_path)
        created_at_col = columns["created_at"]
        assert created_at_col["type"] == "TIMESTAMP"
        assert created_at_col["notnull"] is True

    async def test_updated_at_column_is_timestamp_not_null(
        self, test_db_path: str
    ) -> None:
        """updated_at must be TIMESTAMP NOT NULL."""
        await init_db(test_db_path)
        columns = await self._get_columns(test_db_path)
        updated_at_col = columns["updated_at"]
        assert updated_at_col["type"] == "TIMESTAMP"
        assert updated_at_col["notnull"] is True


# ---------------------------------------------------------------------------
# Index Tests
# ---------------------------------------------------------------------------


class TestTodosTableIndexes:
    """Verify the required indexes exist on the todos table."""

    async def test_completed_index_exists(self, test_db_path: str) -> None:
        """An index on the 'completed' column must exist for filtering queries."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            cursor = await db.execute(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type='index' AND tbl_name='todos'"
            )
            indexes = await cursor.fetchall()

            # Find an index that covers the completed column
            completed_index_found = False
            for _name, sql in indexes:
                if sql and "completed" in sql.lower():
                    completed_index_found = True
                    break

            assert completed_index_found, (
                "An index on the 'completed' column should exist. "
                f"Found indexes: {[row[0] for row in indexes]}"
            )


# ---------------------------------------------------------------------------
# Connection Management Tests
# ---------------------------------------------------------------------------


class TestGetConnection:
    """Test the database connection factory."""

    async def test_get_connection_returns_aiosqlite_connection(
        self, test_db_path: str
    ) -> None:
        """get_connection should return an aiosqlite Connection object."""
        await init_db(test_db_path)
        conn = await get_connection()
        try:
            assert isinstance(conn, aiosqlite.Connection)
        finally:
            await conn.close()

    async def test_connection_can_execute_queries(self, test_db_path: str) -> None:
        """A connection from get_connection should be able to query the todos table."""
        await init_db(test_db_path)
        conn = await get_connection()
        try:
            cursor = await conn.execute("SELECT count(*) FROM todos")
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0  # Empty table initially
        finally:
            await conn.close()


# ---------------------------------------------------------------------------
# Data Integrity Tests (verifying schema constraints via INSERT)
# ---------------------------------------------------------------------------


class TestSchemaConstraints:
    """Verify the schema constraints work correctly via data operations."""

    async def test_insert_todo_with_all_required_fields(
        self, test_db_path: str
    ) -> None:
        """Inserting a row with all required fields should succeed."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            await db.execute(
                "INSERT INTO todos (title, completed, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                ("Test todo", False),
            )
            await db.commit()

            cursor = await db.execute("SELECT * FROM todos")
            row = await cursor.fetchone()
            assert row is not None

    async def test_id_auto_increments(self, test_db_path: str) -> None:
        """id should auto-increment for each new row."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            await db.execute(
                "INSERT INTO todos (title, completed, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                ("First", False),
            )
            await db.execute(
                "INSERT INTO todos (title, completed, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                ("Second", False),
            )
            await db.commit()

            cursor = await db.execute("SELECT id FROM todos ORDER BY id")
            rows = await cursor.fetchall()
            assert len(rows) == 2
            assert rows[0][0] == 1
            assert rows[1][0] == 2

    async def test_completed_defaults_to_false(self, test_db_path: str) -> None:
        """completed should default to 0 (false) when not specified."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            await db.execute(
                "INSERT INTO todos (title, created_at, updated_at) "
                "VALUES (?, datetime('now'), datetime('now'))",
                ("Default completed",),
            )
            await db.commit()

            cursor = await db.execute("SELECT completed FROM todos")
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0  # False in SQLite

    async def test_title_not_null_constraint(self, test_db_path: str) -> None:
        """Inserting a row without title should fail due to NOT NULL constraint."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO todos (completed, created_at, updated_at) "
                    "VALUES (?, datetime('now'), datetime('now'))",
                    (False,),
                )
                await db.commit()
                pytest.fail("Should have raised an error for NULL title")
            except Exception:
                # Expected: NOT NULL constraint violation
                pass

    async def test_created_at_not_null_constraint(self, test_db_path: str) -> None:
        """Inserting a row without created_at should fail due to NOT NULL constraint."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO todos (title, completed, updated_at) "
                    "VALUES (?, ?, datetime('now'))",
                    ("Test", False),
                )
                await db.commit()
                pytest.fail("Should have raised an error for NULL created_at")
            except Exception:
                pass

    async def test_updated_at_not_null_constraint(self, test_db_path: str) -> None:
        """Inserting a row without updated_at should fail due to NOT NULL constraint."""
        await init_db(test_db_path)

        async with aiosqlite.connect(test_db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO todos (title, completed, created_at) "
                    "VALUES (?, ?, datetime('now'))",
                    ("Test", False),
                )
                await db.commit()
                pytest.fail("Should have raised an error for NULL updated_at")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Close DB Tests
# ---------------------------------------------------------------------------


class TestCloseDb:
    """Test database connection cleanup."""

    async def test_close_db_does_not_raise_when_no_connection(
        self, test_db_path: str
    ) -> None:
        """close_db should not raise even if no connection was opened."""
        # Should succeed without error
        await close_db()

    async def test_close_db_after_init(self, test_db_path: str) -> None:
        """close_db after init_db should succeed without error."""
        await init_db(test_db_path)
        await close_db()
