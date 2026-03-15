"""Pydantic request/response models for TODO API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TodoCreate(BaseModel):
    """Request model for creating a TODO."""

    title: str = Field(..., min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            msg = "タイトルは1文字以上200文字以下で入力してください"
            raise ValueError(msg)
        return stripped


class TodoUpdate(BaseModel):
    """Request model for updating a TODO."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                msg = "タイトルは1文字以上200文字以下で入力してください"
                raise ValueError(msg)
            return stripped
        return v


class TodoResponse(BaseModel):
    """Response model for a single TODO."""

    id: int
    title: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class TodoListResponse(BaseModel):
    """Response model for a list of TODOs."""

    todos: list[TodoResponse]
    total: int
