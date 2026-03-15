"""Pydantic request/response models for the Todo API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class TodoCreate(BaseModel):
    """Request body for creating a new todo item."""

    title: str

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str:
        if not isinstance(v, str):
            msg = "Title must be a string"
            raise ValueError(msg)
        trimmed = v.strip()
        if len(trimmed) == 0:
            msg = "Title must not be empty"
            raise ValueError(msg)
        if len(trimmed) > 200:
            msg = "Title must be 200 characters or fewer"
            raise ValueError(msg)
        return trimmed


class TodoUpdate(BaseModel):
    """Request body for updating an existing todo item."""

    title: str | None = None
    completed: bool | None = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str | None:
        if v is None:
            return v
        if not isinstance(v, str):
            msg = "Title must be a string"
            raise ValueError(msg)
        trimmed = v.strip()
        if len(trimmed) == 0:
            msg = "Title must not be empty"
            raise ValueError(msg)
        if len(trimmed) > 200:
            msg = "Title must be 200 characters or fewer"
            raise ValueError(msg)
        return trimmed


class TodoResponse(BaseModel):
    """Response model for a single todo item."""

    id: int
    title: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class TodoListResponse(BaseModel):
    """Response model for a list of todo items."""

    todos: list[TodoResponse]
    total: int
