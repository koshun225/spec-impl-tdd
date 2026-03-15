"""Shared pytest fixtures for backend tests.

Provides async test database setup and cleanup fixtures.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """Provide a temporary database file path for each test.

    Uses pytest's tmp_path to ensure isolation between tests.
    The file is automatically cleaned up after the test session.
    """
    return str(tmp_path / "test_todo.db")


@pytest.fixture(autouse=True)
async def cleanup_db(test_db_path: str):
    """Ensure the test database file is removed after each test.

    This fixture runs automatically for every test to guarantee
    a clean state.
    """
    yield
    # Cleanup: remove the test database file if it exists
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)
