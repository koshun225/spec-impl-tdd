"""API route handlers for the Todo application."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.database import create_todo, get_all_todos, get_todo_by_id, update_todo, delete_todo
from app.models import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse

router = APIRouter(prefix="/api")


@router.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo_route(body: TodoCreate) -> TodoResponse:
    """Create a new todo item."""
    todo = await create_todo(body.title)
    return TodoResponse(**todo)


@router.get("/todos", response_model=TodoListResponse)
async def list_todos_route(status: str = "all") -> TodoListResponse:
    """List todo items with optional status filter."""
    todos = await get_all_todos(status)
    return TodoListResponse(
        todos=[TodoResponse(**t) for t in todos],
        total=len(todos),
    )


@router.patch("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo_route(todo_id: int, body: TodoUpdate) -> TodoResponse:
    """Update an existing todo item."""
    updated = await update_todo(todo_id, body.title, body.completed)
    if updated is None:
        raise HTTPException(status_code=404, detail="TODO not found")
    return TodoResponse(**updated)


@router.delete("/todos/{todo_id}", status_code=204)
async def delete_todo_route(todo_id: int) -> Response:
    """Delete a todo item."""
    deleted = await delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="TODO not found")
    return Response(status_code=204)
