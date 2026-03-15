"use client";

import { useState, useEffect } from "react";
import { fetchTodos, type Todo } from "../lib/api";
import TodoForm from "../components/TodoForm";
import TodoList from "../components/TodoList";
import TodoFilter, { type FilterStatus } from "../components/TodoFilter";

export default function Home() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [filter, setFilter] = useState<FilterStatus>("all");

  useEffect(() => {
    fetchTodos().then((response) => {
      setTodos(response.todos);
    });
  }, []);

  const handleFilterChange = (newFilter: FilterStatus) => {
    setFilter(newFilter);
    fetchTodos(newFilter).then((response) => {
      setTodos(response.todos);
    });
  };

  const handleCreated = (_todo: Todo) => {
    fetchTodos(filter).then((response) => {
      setTodos(response.todos);
    });
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
      <TodoFilter currentFilter={filter} onFilterChange={handleFilterChange} />
      <TodoList todos={todos} onUpdated={handleUpdated} onDeleted={handleDeleted} />
    </main>
  );
}
