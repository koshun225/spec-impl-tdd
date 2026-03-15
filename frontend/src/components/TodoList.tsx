"use client";

import { Todo } from "../lib/api";
import TodoItem from "./TodoItem";

interface TodoListProps {
  todos: Todo[];
  onUpdated: (todo: Todo) => void;
  onDeleted: (id: number) => void;
}

export default function TodoList({ todos, onUpdated, onDeleted }: TodoListProps) {
  if (todos.length === 0) {
    return <p>TODOがありません</p>;
  }

  return (
    <ul>
      {todos.map((todo) => (
        <TodoItem key={todo.id} todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      ))}
    </ul>
  );
}
