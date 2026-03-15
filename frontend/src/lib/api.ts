const BASE_URL = "http://localhost:8000/api";

export interface Todo {
  id: number;
  title: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TodoListResponse {
  todos: Todo[];
  total: number;
}

export interface TodoCreate {
  title: string;
}

export interface TodoUpdate {
  title?: string;
  completed?: boolean;
}

export async function fetchTodos(
  status: "all" | "active" | "completed" = "all"
): Promise<TodoListResponse> {
  const params = status !== "all" ? `?status=${status}` : "";
  const response = await fetch(`${BASE_URL}/todos${params}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch todos: ${response.status}`);
  }
  return response.json();
}

export async function createTodo(data: TodoCreate): Promise<Todo> {
  const response = await fetch(`${BASE_URL}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create todo: ${response.status}`);
  }
  return response.json();
}

export async function updateTodo(id: number, data: TodoUpdate): Promise<Todo> {
  const response = await fetch(`${BASE_URL}/todos/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update todo: ${response.status}`);
  }
  return response.json();
}

export async function deleteTodo(id: number): Promise<void> {
  const response = await fetch(`${BASE_URL}/todos/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete todo: ${response.status}`);
  }
}
