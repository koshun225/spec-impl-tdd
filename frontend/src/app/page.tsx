"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Todo,
  fetchTodos,
  createTodo,
  updateTodo,
  deleteTodo,
} from "@/lib/api";
import TodoFilter from "@/components/TodoFilter";
import TodoForm from "@/components/TodoForm";
import TodoList from "@/components/TodoList";

export default function Home() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [filter, setFilter] = useState("all");

  const loadTodos = useCallback(async () => {
    const data = await fetchTodos(filter);
    setTodos(data.todos);
  }, [filter]);

  useEffect(() => {
    loadTodos();
  }, [loadTodos]);

  const handleAdd = async (title: string) => {
    await createTodo(title);
    await loadTodos();
  };

  const handleToggle = async (id: number, completed: boolean) => {
    await updateTodo(id, { completed });
    await loadTodos();
  };

  const handleUpdate = async (id: number, title: string) => {
    await updateTodo(id, { title });
    await loadTodos();
  };

  const handleDelete = async (id: number) => {
    await deleteTodo(id);
    await loadTodos();
  };

  return (
    <main
      style={{
        maxWidth: "600px",
        margin: "0 auto",
        padding: "2rem 1rem",
      }}
    >
      <h1 style={{ marginBottom: "1.5rem" }}>TODO App</h1>
      <TodoForm onAdd={handleAdd} />
      <TodoFilter current={filter} onChange={setFilter} />
      <TodoList
        todos={todos}
        onToggle={handleToggle}
        onUpdate={handleUpdate}
        onDelete={handleDelete}
      />
    </main>
  );
}
