"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from app.models import TodoCreate


class TestTodoCreate:
    """Tests for TodoCreate model validation."""

    def test_valid_title(self) -> None:
        todo = TodoCreate(title="Buy groceries")
        assert todo.title == "Buy groceries"

    def test_title_required(self) -> None:
        with pytest.raises(ValidationError):
            TodoCreate()  # type: ignore[call-arg]

    def test_title_max_200_chars(self) -> None:
        title = "a" * 200
        todo = TodoCreate(title=title)
        assert len(todo.title) == 200

    def test_title_exceeds_200_chars_rejected(self) -> None:
        title = "a" * 201
        with pytest.raises(ValidationError):
            TodoCreate(title=title)

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TodoCreate(title="")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TodoCreate(title="   ")

    def test_title_is_trimmed(self) -> None:
        todo = TodoCreate(title="  hello  ")
        assert todo.title == "hello"
