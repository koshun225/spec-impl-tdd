"use client";

import { useState } from "react";
import { Todo } from "@/lib/api";

interface TodoItemProps {
  todo: Todo;
  onToggle: (id: number, completed: boolean) => void;
  onUpdate: (id: number, title: string) => void;
  onDelete: (id: number) => void;
}

export default function TodoItem({
  todo,
  onToggle,
  onUpdate,
  onDelete,
}: TodoItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.title);

  const handleSave = () => {
    const trimmed = editTitle.trim();
    if (trimmed && trimmed !== todo.title) {
      onUpdate(todo.id, trimmed);
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") {
      setEditTitle(todo.title);
      setIsEditing(false);
    }
  };

  const handleDelete = () => {
    if (window.confirm("このTODOを削除しますか？")) {
      onDelete(todo.id);
    }
  };

  return (
    <li
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.5rem 0",
        borderBottom: "1px solid #eee",
      }}
    >
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo.id, !todo.completed)}
        style={{ cursor: "pointer" }}
      />
      {isEditing ? (
        <input
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          autoFocus
          style={{
            flex: 1,
            padding: "0.25rem",
            fontSize: "1rem",
            border: "1px solid #0070f3",
            borderRadius: "4px",
          }}
        />
      ) : (
        <span
          onClick={() => setIsEditing(true)}
          style={{
            flex: 1,
            cursor: "pointer",
            textDecoration: todo.completed ? "line-through" : "none",
            color: todo.completed ? "#999" : "inherit",
          }}
        >
          {todo.title}
        </span>
      )}
      <button
        onClick={handleDelete}
        style={{
          padding: "0.25rem 0.5rem",
          fontSize: "0.875rem",
          backgroundColor: "#ff4444",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        削除
      </button>
    </li>
  );
}
