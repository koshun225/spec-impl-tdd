"""API routes for TODO endpoints."""

from fastapi import APIRouter, HTTPException, Response

from app.database import create_todo, delete_todo, get_all_todos, update_todo
from app.models import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

router = APIRouter(prefix="/api")


@router.post("/todos", response_model=TodoResponse, status_code=201)
async def create(body: TodoCreate) -> TodoResponse:
    """Create a new TODO."""
    result = await create_todo(body.title)
    return TodoResponse(**result)


@router.get("/todos", response_model=TodoListResponse)
async def list_todos(status: str = "all") -> TodoListResponse:
    """List all TODOs with optional status filter."""
    todos = await get_all_todos(status)
    return TodoListResponse(
        todos=[TodoResponse(**t) for t in todos],
        total=len(todos),
    )


@router.patch("/todos/{todo_id}", response_model=TodoResponse)
async def update(todo_id: int, body: TodoUpdate) -> TodoResponse:
    """Update a TODO item."""
    result = await update_todo(todo_id, title=body.title, completed=body.completed)
    if result is None:
        raise HTTPException(status_code=404, detail="TODO not found")
    return TodoResponse(**result)


@router.delete("/todos/{todo_id}", status_code=204)
async def delete(todo_id: int) -> Response:
    """Delete a TODO item."""
    deleted = await delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="TODO not found")
    return Response(status_code=204)
