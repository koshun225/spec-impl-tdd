"""API route tests for POST, GET, PATCH, DELETE /api/todos.

Tests are written against the API contract and do not embed
implementation details.
"""

from __future__ import annotations

import httpx

# -------------------------------------------------------------------
# POST /api/todos
# -------------------------------------------------------------------


class TestCreateTodo:
    """POST /api/todos"""

    async def test_create_todo_with_valid_title(
        self, async_client: httpx.AsyncClient
    ):
        """Creating a todo with a valid title returns 201."""
        response = await async_client.post(
            "/api/todos", json={"title": "Buy milk"}
        )

        assert response.status_code == 201
        data = response.json()
        assert isinstance(data["id"], int)
        assert data["title"] == "Buy milk"
        assert data["completed"] is False
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_todo_rejects_empty_title(
        self, async_client: httpx.AsyncClient
    ):
        """An empty string title must be rejected with 422."""
        response = await async_client.post(
            "/api/todos", json={"title": ""}
        )

        assert response.status_code == 422

    async def test_create_todo_rejects_whitespace_only_title(
        self, async_client: httpx.AsyncClient
    ):
        """A whitespace-only title must be rejected with 422."""
        response = await async_client.post(
            "/api/todos", json={"title": "   "}
        )

        assert response.status_code == 422

    async def test_create_todo_rejects_overlength_title(
        self, async_client: httpx.AsyncClient
    ):
        """A title exceeding 200 characters must be rejected."""
        long_title = "a" * 201
        response = await async_client.post(
            "/api/todos", json={"title": long_title}
        )

        assert response.status_code == 422

    async def test_create_todo_accepts_max_length_title(
        self, async_client: httpx.AsyncClient
    ):
        """A title of exactly 200 characters should be accepted."""
        title_200 = "a" * 200
        response = await async_client.post(
            "/api/todos", json={"title": title_200}
        )

        assert response.status_code == 201
        assert response.json()["title"] == title_200

    async def test_create_todo_trims_whitespace(
        self, async_client: httpx.AsyncClient
    ):
        """Leading/trailing whitespace is trimmed from the title."""
        response = await async_client.post(
            "/api/todos", json={"title": "  Buy eggs  "}
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Buy eggs"

    async def test_create_todo_missing_title_field(
        self, async_client: httpx.AsyncClient
    ):
        """Omitting the title field entirely must return 422."""
        response = await async_client.post("/api/todos", json={})

        assert response.status_code == 422


# -------------------------------------------------------------------
# GET /api/todos
# -------------------------------------------------------------------


class TestListTodos:
    """GET /api/todos"""

    async def test_list_todos_empty(
        self, async_client: httpx.AsyncClient
    ):
        """An empty database returns an empty list with total 0."""
        response = await async_client.get("/api/todos")

        assert response.status_code == 200
        data = response.json()
        assert data == {"todos": [], "total": 0}

    async def test_list_todos_after_creation(
        self, async_client: httpx.AsyncClient
    ):
        """After creating todos they appear in the list."""
        await async_client.post(
            "/api/todos", json={"title": "First"}
        )
        await async_client.post(
            "/api/todos", json={"title": "Second"}
        )

        response = await async_client.get("/api/todos")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["todos"]) == 2
        titles = {t["title"] for t in data["todos"]}
        assert titles == {"First", "Second"}

    async def test_list_todos_response_structure(
        self, async_client: httpx.AsyncClient
    ):
        """Each item in the list has the full TodoResponse shape."""
        await async_client.post(
            "/api/todos", json={"title": "Check structure"}
        )

        response = await async_client.get("/api/todos")

        assert response.status_code == 200
        data = response.json()
        assert "todos" in data
        assert "total" in data
        assert isinstance(data["todos"], list)
        assert isinstance(data["total"], int)

        todo = data["todos"][0]
        assert "id" in todo
        assert "title" in todo
        assert "completed" in todo
        assert "created_at" in todo
        assert "updated_at" in todo

    async def test_list_todos_filter_active(
        self, async_client: httpx.AsyncClient
    ):
        """Filtering by status=active returns only active todos."""
        await async_client.post(
            "/api/todos", json={"title": "Active todo"}
        )
        resp2 = await async_client.post(
            "/api/todos", json={"title": "Done todo"}
        )

        # Mark the second as completed
        todo_id = resp2.json()["id"]
        await async_client.patch(
            f"/api/todos/{todo_id}", json={"completed": True}
        )

        response = await async_client.get(
            "/api/todos", params={"status": "active"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Active todo"

    async def test_list_todos_filter_completed(
        self, async_client: httpx.AsyncClient
    ):
        """Filtering by status=completed returns only done todos."""
        await async_client.post(
            "/api/todos", json={"title": "Active todo"}
        )
        resp2 = await async_client.post(
            "/api/todos", json={"title": "Done todo"}
        )

        todo_id = resp2.json()["id"]
        await async_client.patch(
            f"/api/todos/{todo_id}", json={"completed": True}
        )

        response = await async_client.get(
            "/api/todos", params={"status": "completed"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Done todo"

    async def test_list_todos_filter_all(
        self, async_client: httpx.AsyncClient
    ):
        """Filtering by status=all returns all todos."""
        await async_client.post(
            "/api/todos", json={"title": "Todo A"}
        )
        await async_client.post(
            "/api/todos", json={"title": "Todo B"}
        )

        response = await async_client.get(
            "/api/todos", params={"status": "all"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


# -------------------------------------------------------------------
# PATCH /api/todos/{id}
# -------------------------------------------------------------------


class TestUpdateTodo:
    """PATCH /api/todos/{id}"""

    async def test_update_title(
        self, async_client: httpx.AsyncClient
    ):
        """Updating the title returns 200 with the new title."""
        create_resp = await async_client.post(
            "/api/todos", json={"title": "Old title"}
        )
        todo = create_resp.json()
        todo_id = todo["id"]
        original_updated_at = todo["updated_at"]

        update_resp = await async_client.patch(
            f"/api/todos/{todo_id}", json={"title": "New title"}
        )

        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["title"] == "New title"
        assert updated["id"] == todo_id
        assert updated["updated_at"] >= original_updated_at

    async def test_update_completed(
        self, async_client: httpx.AsyncClient
    ):
        """Updating completed to true returns 200."""
        create_resp = await async_client.post(
            "/api/todos", json={"title": "Mark done"}
        )
        todo_id = create_resp.json()["id"]

        update_resp = await async_client.patch(
            f"/api/todos/{todo_id}", json={"completed": True}
        )

        assert update_resp.status_code == 200
        assert update_resp.json()["completed"] is True

    async def test_update_nonexistent_todo(
        self, async_client: httpx.AsyncClient
    ):
        """Updating a non-existent todo returns 404."""
        response = await async_client.patch(
            "/api/todos/99999", json={"title": "Nope"}
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "TODO not found"}

    async def test_update_preserves_other_fields(
        self, async_client: httpx.AsyncClient
    ):
        """A partial update does not change other fields."""
        create_resp = await async_client.post(
            "/api/todos", json={"title": "Keep completed"}
        )
        todo = create_resp.json()
        todo_id = todo["id"]

        update_resp = await async_client.patch(
            f"/api/todos/{todo_id}", json={"title": "Changed"}
        )

        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["title"] == "Changed"
        assert updated["completed"] == todo["completed"]


# -------------------------------------------------------------------
# DELETE /api/todos/{id}
# -------------------------------------------------------------------


class TestDeleteTodo:
    """DELETE /api/todos/{id}"""

    async def test_delete_existing_todo(
        self, async_client: httpx.AsyncClient
    ):
        """Deleting an existing todo returns 204 No Content."""
        create_resp = await async_client.post(
            "/api/todos", json={"title": "To delete"}
        )
        todo_id = create_resp.json()["id"]

        delete_resp = await async_client.delete(
            f"/api/todos/{todo_id}"
        )

        assert delete_resp.status_code == 204

    async def test_delete_nonexistent_todo(
        self, async_client: httpx.AsyncClient
    ):
        """Deleting a non-existent todo returns 404."""
        response = await async_client.delete("/api/todos/99999")

        assert response.status_code == 404
        assert response.json() == {"detail": "TODO not found"}

    async def test_deleted_todo_not_in_list(
        self, async_client: httpx.AsyncClient
    ):
        """After deletion the todo no longer appears in the list."""
        create_resp = await async_client.post(
            "/api/todos", json={"title": "Gone soon"}
        )
        todo_id = create_resp.json()["id"]

        await async_client.delete(f"/api/todos/{todo_id}")

        list_resp = await async_client.get("/api/todos")
        data = list_resp.json()
        ids = [t["id"] for t in data["todos"]]
        assert todo_id not in ids
