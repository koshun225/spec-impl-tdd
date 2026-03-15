"""Pytest configuration and fixtures for TODO App tests."""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import init_db

TEST_DB_PATH = "test_todo.db"


@pytest.fixture(autouse=True)
async def test_db() -> AsyncIterator[str]:
    """Create and tear down a test database for each test."""
    os.environ["TODO_DB_PATH"] = TEST_DB_PATH
    # Patch database module to use test DB
    import app.database as db_module

    db_module.DB_PATH = TEST_DB_PATH
    await init_db(TEST_DB_PATH)
    yield TEST_DB_PATH
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    db_module.DB_PATH = "todo.db"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Async HTTP client for testing FastAPI endpoints."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
