"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { updateTodo, deleteTodo, Todo } from "../lib/api";

interface TodoItemProps {
  todo: Todo;
  onUpdated: (todo: Todo) => void;
  onDeleted: (id: number) => void;
}

export default function TodoItem({ todo, onUpdated, onDeleted }: TodoItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = async () => {
    const trimmed = editTitle.trim();

    // Empty/whitespace-only: revert, no API call
    if (trimmed === "") {
      setEditTitle(todo.title);
      setIsEditing(false);
      return;
    }

    // Title unchanged: no API call, just exit edit mode
    if (trimmed === todo.title) {
      setEditTitle(todo.title);
      setIsEditing(false);
      return;
    }

    // Title changed: call API
    const updated = await updateTodo(todo.id, { title: trimmed });
    onUpdated(updated);
    setIsEditing(false);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      setEditTitle(todo.title);
      setIsEditing(false);
    }
  };

  const handleTitleClick = () => {
    setEditTitle(todo.title);
    setIsEditing(true);
  };

  const handleDelete = async () => {
    const confirmed = window.confirm("本当に削除しますか？");
    if (!confirmed) {
      return;
    }
    await deleteTodo(todo.id);
    onDeleted(todo.id);
  };

  return (
    <li>
      {isEditing ? (
        <input
          ref={inputRef}
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
        />
      ) : (
        <span
          onClick={handleTitleClick}
          style={todo.completed ? { textDecoration: "line-through" } : undefined}
        >
          {todo.title}
        </span>
      )}
      <button onClick={handleDelete}>削除</button>
    </li>
  );
}
