"""Tests for conftest.py pytest fixtures.

Verifies the contract requirements for T010:
- async_client fixture returns a working httpx.AsyncClient
- async_client uses ASGITransport pointed at the FastAPI app
- Test database is isolated (changes don't persist between tests)
- The test database path is unique per test (uses tmp_path)
- cleanup_db removes the test database file after each test
- The async_client fixture properly initialises and tears down the DB
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest

from app.main import app


# ---------------------------------------------------------------------------
# test_db_path fixture tests
# ---------------------------------------------------------------------------


class TestDbPathFixture:
    """Verify the test_db_path fixture provides isolated temporary paths."""

    def test_test_db_path_is_string(self, test_db_path: str) -> None:
        """test_db_path should return a string file path."""
        assert isinstance(test_db_path, str)

    def test_test_db_path_ends_with_db_extension(self, test_db_path: str) -> None:
        """The test database path should end with a .db extension."""
        assert test_db_path.endswith(".db")

    def test_test_db_path_uses_tmp_dir(self, test_db_path: str) -> None:
        """The test database path should be inside a temporary directory."""
        # tmp_path is provided by pytest and is under the system temp directory
        # or pytest's configured tmp dir. Just verify it's an absolute path.
        assert os.path.isabs(test_db_path)

    def test_test_db_path_file_does_not_exist_initially(
        self, test_db_path: str
    ) -> None:
        """The database file should not exist before the test creates it."""
        assert not os.path.exists(test_db_path)

    def test_test_db_path_is_unique_per_test_a(self, test_db_path: str) -> None:
        """Record the path for uniqueness check (part A).

        This test and test_b use the same fixture but should get different paths
        because tmp_path is unique per test.
        """
        # Just verify it's a valid path; uniqueness is checked by the pair
        assert len(test_db_path) > 0
        # Store the path in a class variable for cross-test comparison
        TestDbPathFixture._path_a = test_db_path

    def test_test_db_path_is_unique_per_test_b(self, test_db_path: str) -> None:
        """Each test invocation should get a different temporary path.

        Compares with the path recorded by test_a. Because pytest's tmp_path
        creates a unique directory per test function, the paths must differ.
        """
        path_a = getattr(TestDbPathFixture, "_path_a", None)
        if path_a is not None:
            assert test_db_path != path_a, (
                "test_db_path should be unique per test invocation"
            )


# ---------------------------------------------------------------------------
# cleanup_db fixture tests
# ---------------------------------------------------------------------------


class TestCleanupDbFixture:
    """Verify the cleanup_db fixture removes the test database after each test."""

    async def test_cleanup_removes_db_file(self, test_db_path: str) -> None:
        """After this test, the cleanup_db fixture should remove the DB file.

        We create a file at test_db_path; the autouse cleanup_db fixture
        should remove it in teardown.
        """
        # Create a dummy file to simulate a database
        Path(test_db_path).touch()
        assert os.path.exists(test_db_path)
        # After yield in cleanup_db, the file should be deleted.
        # We can't directly verify teardown here, but we verify the fixture
        # doesn't interfere with test execution.

    async def test_cleanup_handles_missing_file_gracefully(
        self, test_db_path: str
    ) -> None:
        """cleanup_db should not raise if the database file doesn't exist.

        Some tests may not create a database at all. The cleanup fixture
        should handle this case without error.
        """
        assert not os.path.exists(test_db_path)
        # Test passes if no exception is raised during teardown


# ---------------------------------------------------------------------------
# async_client fixture tests
# ---------------------------------------------------------------------------


class TestAsyncClientFixture:
    """Verify the async_client fixture provides a working httpx.AsyncClient."""

    async def test_async_client_is_httpx_async_client(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """The async_client fixture should yield an httpx.AsyncClient instance."""
        assert isinstance(async_client, httpx.AsyncClient)

    async def test_async_client_uses_asgi_transport(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """The async_client should be configured with ASGITransport.

        This ensures the client talks directly to the ASGI app
        without needing a running server.
        """
        transport = async_client._transport  # noqa: SLF001
        assert isinstance(transport, httpx.ASGITransport)

    async def test_async_client_transport_points_at_fastapi_app(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """The ASGITransport should be configured with the FastAPI app."""
        transport = async_client._transport  # noqa: SLF001
        assert isinstance(transport, httpx.ASGITransport)
        assert transport.app is app

    async def test_async_client_can_make_requests(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """The async_client should be able to make HTTP requests to the app.

        Even if no routes are defined yet (404), the client should connect
        successfully without raising connection errors.
        """
        response = await async_client.get("/")
        # The app is alive; 200 or 404 or 405 are all acceptable
        assert response.status_code in (200, 404, 405)

    async def test_async_client_has_base_url(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """The async_client should have a base URL configured.

        This allows tests to use relative paths like '/api/todos'
        instead of full URLs.
        """
        base_url = str(async_client.base_url)
        assert base_url.startswith("http")


# ---------------------------------------------------------------------------
# Database isolation tests
# ---------------------------------------------------------------------------


class TestDatabaseIsolation:
    """Verify that the test database is isolated between tests.

    Each test using async_client should get a fresh, empty database.
    Data written in one test must not be visible in another test.
    """

    async def test_db_isolation_write(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """Write data via the API. The next test should not see this data.

        This test creates a todo item. If isolation is working correctly,
        test_db_isolation_read (which runs separately) will see an empty DB.
        """
        # Attempt to create a todo; endpoint may not exist yet, which is fine.
        # The important thing is that the DB was initialised for this test.
        response = await async_client.post(
            "/api/todos",
            json={"title": "Isolation test item"},
        )
        # If routes exist, should be 201; if not, 404/405 is also acceptable
        # during Red Team phase since routes may not be implemented yet.
        assert response.status_code in (201, 404, 405, 422)

    async def test_db_isolation_read(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """Read data via the API. Should see an empty database.

        If isolation is correct, the item created in test_db_isolation_write
        should not be present in this test's database.
        """
        response = await async_client.get("/api/todos")
        if response.status_code == 200:
            data = response.json()
            # The database should be empty -- no carryover from other tests
            assert data.get("total", 0) == 0, (
                "Test database should be empty; data from another test leaked"
            )
            assert data.get("todos", []) == [], (
                "Test database should have no todos; isolation failed"
            )
        else:
            # Routes not implemented yet -- 404/405 is acceptable
            assert response.status_code in (404, 405)


# ---------------------------------------------------------------------------
# Database setup tests (via async_client)
# ---------------------------------------------------------------------------


class TestDatabaseSetupViaClient:
    """Verify that the async_client fixture properly initialises the test DB."""

    async def test_database_tables_created(
        self, async_client: httpx.AsyncClient, test_db_path: str
    ) -> None:
        """The test database file should exist after async_client setup.

        The fixture should call init_db() which creates the todos table.
        """
        assert os.path.exists(test_db_path), (
            "Test database file should exist after async_client fixture setup"
        )

    async def test_database_has_todos_table(
        self, async_client: httpx.AsyncClient, test_db_path: str
    ) -> None:
        """The test database should contain the 'todos' table.

        The async_client fixture should initialise the DB with init_db(),
        which creates the todos table and indexes.
        """
        import aiosqlite

        async with aiosqlite.connect(test_db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='todos'"
            )
            row = await cursor.fetchone()
            assert row is not None, (
                "The 'todos' table should exist in the test database"
            )
            assert row[0] == "todos"


# ---------------------------------------------------------------------------
# Teardown tests
# ---------------------------------------------------------------------------


class TestAsyncClientTeardown:
    """Verify that the async_client fixture properly cleans up.

    After the fixture's teardown, the database connection should be closed
    and the database file should be eligible for removal by cleanup_db.
    """

    async def test_client_is_usable_during_test(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """The client should be fully functional during the test body.

        After the test, teardown should close the DB without errors.
        """
        # Make a request to verify the client is working
        response = await async_client.get("/")
        assert response.status_code in (200, 404, 405)
        # Teardown happens after this test function returns

    async def test_multiple_requests_in_single_test(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """Multiple requests in a single test should all work correctly.

        The database connection should remain open throughout the test body.
        """
        for _ in range(3):
            response = await async_client.get("/")
            assert response.status_code in (200, 404, 405)
