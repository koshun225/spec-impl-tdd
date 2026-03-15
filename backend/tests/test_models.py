"""Tests for Pydantic request/response models.

Verifies the contract specifications from contracts/api.md and data-model.md:

- TodoCreate: title required, 1-200 chars after trim, reject empty/whitespace
- TodoUpdate: title optional, completed optional, partial update support
- TodoResponse: id, title, completed, created_at, updated_at fields
- TodoListResponse: todos list + total count
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

# ---------------------------------------------------------------------------
# TodoCreate Tests
# ---------------------------------------------------------------------------


class TestTodoCreate:
    """Test TodoCreate request model validation."""

    def test_valid_title(self) -> None:
        """A simple non-empty title should be accepted."""
        model = TodoCreate(title="Buy groceries")
        assert model.title == "Buy groceries"

    def test_title_is_required(self) -> None:
        """Omitting title should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoCreate()  # type: ignore[call-arg]

    def test_empty_string_title_rejected(self) -> None:
        """An empty string title should be rejected."""
        with pytest.raises(ValidationError):
            TodoCreate(title="")

    def test_whitespace_only_title_rejected(self) -> None:
        """A title containing only whitespace should be rejected."""
        with pytest.raises(ValidationError):
            TodoCreate(title="   ")

    def test_whitespace_only_tabs_rejected(self) -> None:
        """A title of only tab characters should be rejected."""
        with pytest.raises(ValidationError):
            TodoCreate(title="\t\t")

    def test_whitespace_only_newlines_rejected(self) -> None:
        """A title of only newline characters should be rejected."""
        with pytest.raises(ValidationError):
            TodoCreate(title="\n\n")

    def test_title_trimmed(self) -> None:
        """Leading and trailing whitespace should be trimmed from title."""
        model = TodoCreate(title="  Buy groceries  ")
        assert model.title == "Buy groceries"

    def test_title_trimmed_with_tabs(self) -> None:
        """Leading/trailing tabs should be trimmed from title."""
        model = TodoCreate(title="\tBuy groceries\t")
        assert model.title == "Buy groceries"

    def test_title_max_200_chars_accepted(self) -> None:
        """A title of exactly 200 characters should be accepted."""
        title = "a" * 200
        model = TodoCreate(title=title)
        assert len(model.title) == 200

    def test_title_over_200_chars_rejected(self) -> None:
        """A title exceeding 200 characters should be rejected."""
        title = "a" * 201
        with pytest.raises(ValidationError):
            TodoCreate(title=title)

    def test_title_trimmed_then_validated_length(self) -> None:
        """Length validation should apply after trimming.

        A title that is 200 chars of content with surrounding whitespace
        should be accepted (trimmed to 200).
        """
        title = " " + "a" * 200 + " "
        model = TodoCreate(title=title)
        assert len(model.title) == 200

    def test_title_trimmed_over_200_after_trim_rejected(self) -> None:
        """A title exceeding 200 chars even after trimming should be rejected."""
        title = " " + "a" * 201 + " "
        with pytest.raises(ValidationError):
            TodoCreate(title=title)

    def test_single_char_title_accepted(self) -> None:
        """A single non-whitespace character title should be accepted."""
        model = TodoCreate(title="a")
        assert model.title == "a"

    def test_title_with_interior_whitespace_preserved(self) -> None:
        """Interior whitespace within the title should be preserved."""
        model = TodoCreate(title="Buy some groceries")
        assert model.title == "Buy some groceries"

    def test_title_none_rejected(self) -> None:
        """Passing None for title should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoCreate(title=None)  # type: ignore[arg-type]

    def test_title_non_string_rejected(self) -> None:
        """Non-string title values should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoCreate(title=123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TodoUpdate Tests
# ---------------------------------------------------------------------------


class TestTodoUpdate:
    """Test TodoUpdate request model for partial updates."""

    def test_both_fields_optional(self) -> None:
        """Creating TodoUpdate with no fields should succeed (partial update)."""
        model = TodoUpdate()
        assert model.title is None
        assert model.completed is None

    def test_title_only(self) -> None:
        """Updating only title should be valid."""
        model = TodoUpdate(title="Updated title")
        assert model.title == "Updated title"
        assert model.completed is None

    def test_completed_only(self) -> None:
        """Updating only completed should be valid."""
        model = TodoUpdate(completed=True)
        assert model.title is None
        assert model.completed is True

    def test_both_fields_provided(self) -> None:
        """Updating both title and completed should be valid."""
        model = TodoUpdate(title="Updated", completed=False)
        assert model.title == "Updated"
        assert model.completed is False

    def test_completed_true(self) -> None:
        """Setting completed to True should be accepted."""
        model = TodoUpdate(completed=True)
        assert model.completed is True

    def test_completed_false(self) -> None:
        """Setting completed to False should be accepted."""
        model = TodoUpdate(completed=False)
        assert model.completed is False

    def test_title_empty_string_rejected(self) -> None:
        """An empty string title in update should be rejected.

        When title is provided, it must follow the same validation rules
        as TodoCreate (1-200 chars after trim).
        """
        with pytest.raises(ValidationError):
            TodoUpdate(title="")

    def test_title_whitespace_only_rejected(self) -> None:
        """A whitespace-only title in update should be rejected."""
        with pytest.raises(ValidationError):
            TodoUpdate(title="   ")

    def test_title_over_200_chars_rejected(self) -> None:
        """A title exceeding 200 characters in update should be rejected."""
        with pytest.raises(ValidationError):
            TodoUpdate(title="a" * 201)

    def test_title_trimmed_in_update(self) -> None:
        """Title should be trimmed when provided in an update."""
        model = TodoUpdate(title="  Updated title  ")
        assert model.title == "Updated title"

    def test_title_none_means_no_update(self) -> None:
        """Explicitly passing title=None means no update to title."""
        model = TodoUpdate(title=None)
        assert model.title is None

    def test_completed_none_means_no_update(self) -> None:
        """Explicitly passing completed=None means no update to completed."""
        model = TodoUpdate(completed=None)
        assert model.completed is None


# ---------------------------------------------------------------------------
# TodoResponse Tests
# ---------------------------------------------------------------------------


class TestTodoResponse:
    """Test TodoResponse model structure and serialization."""

    def _make_response(self, **overrides) -> TodoResponse:
        """Helper to create a TodoResponse with sensible defaults."""
        defaults = {
            "id": 1,
            "title": "Test todo",
            "completed": False,
            "created_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        }
        defaults.update(overrides)
        return TodoResponse(**defaults)

    def test_all_fields_present(self) -> None:
        """TodoResponse should have id, title, completed, created_at, updated_at."""
        model = self._make_response()
        assert model.id == 1
        assert model.title == "Test todo"
        assert model.completed is False
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

    def test_id_is_integer(self) -> None:
        """id field must be an integer."""
        model = self._make_response(id=42)
        assert isinstance(model.id, int)
        assert model.id == 42

    def test_completed_is_boolean(self) -> None:
        """completed field must be a boolean."""
        model = self._make_response(completed=True)
        assert isinstance(model.completed, bool)
        assert model.completed is True

    def test_created_at_is_datetime(self) -> None:
        """created_at field must be a datetime."""
        now = datetime(2026, 3, 15, 10, 30, 0, tzinfo=UTC)
        model = self._make_response(created_at=now)
        assert model.created_at == now

    def test_updated_at_is_datetime(self) -> None:
        """updated_at field must be a datetime."""
        now = datetime(2026, 3, 15, 10, 30, 0, tzinfo=UTC)
        model = self._make_response(updated_at=now)
        assert model.updated_at == now

    def test_serialization_contains_all_fields(self) -> None:
        """model_dump should include all five fields."""
        model = self._make_response()
        data = model.model_dump()
        assert set(data.keys()) == {
            "id",
            "title",
            "completed",
            "created_at",
            "updated_at",
        }

    def test_missing_id_raises_error(self) -> None:
        """Omitting id should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoResponse(
                title="Test",
                completed=False,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )  # type: ignore[call-arg]

    def test_missing_title_raises_error(self) -> None:
        """Omitting title should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoResponse(
                id=1,
                completed=False,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )  # type: ignore[call-arg]

    def test_missing_completed_raises_error(self) -> None:
        """Omitting completed should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoResponse(
                id=1,
                title="Test",
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )  # type: ignore[call-arg]

    def test_missing_created_at_raises_error(self) -> None:
        """Omitting created_at should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoResponse(
                id=1,
                title="Test",
                completed=False,
                updated_at=datetime.now(tz=UTC),
            )  # type: ignore[call-arg]

    def test_missing_updated_at_raises_error(self) -> None:
        """Omitting updated_at should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoResponse(
                id=1,
                title="Test",
                completed=False,
                created_at=datetime.now(tz=UTC),
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TodoListResponse Tests
# ---------------------------------------------------------------------------


class TestTodoListResponse:
    """Test TodoListResponse model structure."""

    def test_empty_list(self) -> None:
        """An empty todos list with total=0 should be valid."""
        model = TodoListResponse(todos=[], total=0)
        assert model.todos == []
        assert model.total == 0

    def test_list_with_items(self) -> None:
        """A list with TodoResponse items should be valid."""
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        todo = TodoResponse(
            id=1,
            title="Test",
            completed=False,
            created_at=now,
            updated_at=now,
        )
        model = TodoListResponse(todos=[todo], total=1)
        assert len(model.todos) == 1
        assert model.total == 1
        assert model.todos[0].id == 1

    def test_multiple_items(self) -> None:
        """A list with multiple TodoResponse items should be valid."""
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        todos = [
            TodoResponse(
                id=i, title=f"Todo {i}", completed=False, created_at=now, updated_at=now
            )
            for i in range(1, 4)
        ]
        model = TodoListResponse(todos=todos, total=3)
        assert len(model.todos) == 3
        assert model.total == 3

    def test_todos_field_required(self) -> None:
        """Omitting todos field should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoListResponse(total=0)  # type: ignore[call-arg]

    def test_total_field_required(self) -> None:
        """Omitting total field should raise a validation error."""
        with pytest.raises(ValidationError):
            TodoListResponse(todos=[])  # type: ignore[call-arg]

    def test_serialization_contains_all_fields(self) -> None:
        """model_dump should include todos and total fields."""
        model = TodoListResponse(todos=[], total=0)
        data = model.model_dump()
        assert "todos" in data
        assert "total" in data

    def test_todos_contains_todo_response_objects(self) -> None:
        """Items in the todos list should be TodoResponse instances."""
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        todo = TodoResponse(
            id=1,
            title="Test",
            completed=False,
            created_at=now,
            updated_at=now,
        )
        model = TodoListResponse(todos=[todo], total=1)
        assert isinstance(model.todos[0], TodoResponse)

    def test_total_is_integer(self) -> None:
        """total field must be an integer."""
        model = TodoListResponse(todos=[], total=5)
        assert isinstance(model.total, int)
        assert model.total == 5
