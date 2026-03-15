"""Tests for TODO API routes."""

from httpx import AsyncClient


class TestCreateTodo:
    """Tests for POST /api/todos."""

    async def test_create_with_valid_title(self, client: AsyncClient) -> None:
        response = await client.post("/api/todos", json={"title": "Buy groceries"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_rejects_empty_title(self, client: AsyncClient) -> None:
        response = await client.post("/api/todos", json={"title": ""})
        assert response.status_code == 422

    async def test_create_rejects_long_title(self, client: AsyncClient) -> None:
        response = await client.post("/api/todos", json={"title": "a" * 201})
        assert response.status_code == 422


class TestListTodos:
    """Tests for GET /api/todos."""

    async def test_list_all_todos(self, client: AsyncClient) -> None:
        await client.post("/api/todos", json={"title": "Todo 1"})
        await client.post("/api/todos", json={"title": "Todo 2"})
        response = await client.get("/api/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["todos"]) == 2

    async def test_list_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["todos"] == []


class TestUpdateTodo:
    """Tests for PATCH /api/todos/{id}."""

    async def test_update_title(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/todos", json={"title": "Original"})
        todo_id = create_resp.json()["id"]
        response = await client.patch(
            f"/api/todos/{todo_id}", json={"title": "Updated"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_toggle_completed(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/todos", json={"title": "Toggle me"})
        todo_id = create_resp.json()["id"]
        # Toggle to completed
        resp = await client.patch(f"/api/todos/{todo_id}", json={"completed": True})
        assert resp.status_code == 200
        assert resp.json()["completed"] is True
        # Toggle back to active
        resp = await client.patch(f"/api/todos/{todo_id}", json={"completed": False})
        assert resp.status_code == 200
        assert resp.json()["completed"] is False

    async def test_update_nonexistent_returns_404(self, client: AsyncClient) -> None:
        response = await client.patch("/api/todos/9999", json={"title": "X"})
        assert response.status_code == 404


class TestFilterTodos:
    """Tests for GET /api/todos with status filter."""

    async def test_filter_completed(self, client: AsyncClient) -> None:
        await client.post("/api/todos", json={"title": "Active todo"})
        resp2 = await client.post("/api/todos", json={"title": "Done todo"})
        todo2_id = resp2.json()["id"]
        await client.patch(f"/api/todos/{todo2_id}", json={"completed": True})

        response = await client.get("/api/todos", params={"status": "completed"})
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Done todo"

    async def test_filter_active(self, client: AsyncClient) -> None:
        await client.post("/api/todos", json={"title": "Active todo"})
        resp2 = await client.post("/api/todos", json={"title": "Done todo"})
        todo2_id = resp2.json()["id"]
        await client.patch(f"/api/todos/{todo2_id}", json={"completed": True})

        response = await client.get("/api/todos", params={"status": "active"})
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["title"] == "Active todo"

    async def test_filter_all(self, client: AsyncClient) -> None:
        await client.post("/api/todos", json={"title": "Todo 1"})
        await client.post("/api/todos", json={"title": "Todo 2"})
        response = await client.get("/api/todos", params={"status": "all"})
        data = response.json()
        assert data["total"] == 2


class TestDeleteTodo:
    """Tests for DELETE /api/todos/{id}."""

    async def test_delete_existing(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/todos", json={"title": "To delete"})
        todo_id = create_resp.json()["id"]
        response = await client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        response = await client.delete("/api/todos/9999")
        assert response.status_code == 404
