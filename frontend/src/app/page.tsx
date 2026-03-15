"use client";

import { useState, useEffect } from "react";
import { fetchTodos, type Todo } from "../lib/api";
import TodoForm from "../components/TodoForm";
import TodoList from "../components/TodoList";

export default function Home() {
  const [todos, setTodos] = useState<Todo[]>([]);

  useEffect(() => {
    fetchTodos().then((response) => {
      setTodos(response.todos);
    });
  }, []);

  const handleCreated = (todo: Todo) => {
    setTodos((prev) => [...prev, todo]);
  };

  const handleUpdated = (updatedTodo: Todo) => {
    setTodos((prev) =>
      prev.map((t) => (t.id === updatedTodo.id ? updatedTodo : t))
    );
  };

  const handleDeleted = (id: number) => {
    setTodos((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <main>
      <h1>TODO App</h1>
      <TodoForm onCreated={handleCreated} />
      <TodoList todos={todos} onUpdated={handleUpdated} onDeleted={handleDeleted} />
    </main>
  );
}
