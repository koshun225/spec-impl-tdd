"use client";

import { Todo } from "@/lib/api";
import TodoItem from "./TodoItem";

interface TodoListProps {
  todos: Todo[];
  onToggle: (id: number, completed: boolean) => void;
  onUpdate: (id: number, title: string) => void;
  onDelete: (id: number) => void;
}

export default function TodoList({
  todos,
  onToggle,
  onUpdate,
  onDelete,
}: TodoListProps) {
  if (todos.length === 0) {
    return (
      <p style={{ textAlign: "center", color: "#999", padding: "2rem 0" }}>
        TODOがありません
      </p>
    );
  }

  return (
    <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={onToggle}
          onUpdate={onUpdate}
          onDelete={onDelete}
        />
      ))}
    </ul>
  );
}
