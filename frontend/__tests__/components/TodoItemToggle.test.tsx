import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TodoItem from "@/components/TodoItem";
import { type Todo } from "@/lib/api";

// Mock the API module
jest.mock("@/lib/api", () => ({
  updateTodo: jest.fn(),
  deleteTodo: jest.fn(),
}));

import { updateTodo } from "@/lib/api";

const mockedUpdateTodo = updateTodo as jest.MockedFunction<typeof updateTodo>;

// Helper: build a sample Todo
function buildTodo(overrides: Partial<Todo> = {}): Todo {
  return {
    id: 1,
    title: "テスト TODO",
    completed: false,
    created_at: "2026-03-15T00:00:00Z",
    updated_at: "2026-03-15T00:00:00Z",
    ...overrides,
  };
}

describe("TodoItem - completion toggle (T027)", () => {
  let onUpdated: jest.Mock;
  let onDeleted: jest.Mock;

  beforeEach(() => {
    onUpdated = jest.fn();
    onDeleted = jest.fn();
    mockedUpdateTodo.mockReset();
    jest.restoreAllMocks();
  });

  // ---------- Checkbox rendering ----------

  describe("checkbox rendering", () => {
    it("renders a checkbox input element", () => {
      const todo = buildTodo();
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).toBeInTheDocument();
    });

    it("checkbox is checked when todo.completed is true", () => {
      const todo = buildTodo({ completed: true });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).toBeChecked();
    });

    it("checkbox is unchecked when todo.completed is false", () => {
      const todo = buildTodo({ completed: false });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).not.toBeChecked();
    });
  });

  // ---------- Toggle behavior ----------

  describe("toggle behavior", () => {
    it("clicking checkbox calls updateTodo with toggled completed value (false -> true)", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 1, completed: false });
      const updatedTodo = buildTodo({
        id: 1,
        completed: true,
        updated_at: "2026-03-15T01:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const checkbox = screen.getByRole("checkbox");
      await user.click(checkbox);

      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledTimes(1);
        expect(mockedUpdateTodo).toHaveBeenCalledWith(1, { completed: true });
      });
    });

    it("clicking checkbox calls updateTodo with toggled completed value (true -> false)", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 2, completed: true });
      const updatedTodo = buildTodo({
        id: 2,
        completed: false,
        updated_at: "2026-03-15T01:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const checkbox = screen.getByRole("checkbox");
      await user.click(checkbox);

      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledTimes(1);
        expect(mockedUpdateTodo).toHaveBeenCalledWith(2, { completed: false });
      });
    });

    it("after successful toggle, onUpdated callback is called with updated todo", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 3, completed: false });
      const updatedTodo = buildTodo({
        id: 3,
        completed: true,
        updated_at: "2026-03-15T01:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const checkbox = screen.getByRole("checkbox");
      await user.click(checkbox);

      await waitFor(() => {
        expect(onUpdated).toHaveBeenCalledTimes(1);
        expect(onUpdated).toHaveBeenCalledWith(updatedTodo);
      });
    });
  });

  // ---------- Visual distinction (FR-009) ----------

  describe("completed visual distinction (FR-009)", () => {
    it("completed todo title has strikethrough style (line-through text decoration)", () => {
      const todo = buildTodo({ completed: true, title: "完了タスク" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const titleElement = screen.getByText("完了タスク");
      expect(titleElement).toHaveStyle({ textDecoration: "line-through" });
    });

    it("uncompleted todo title does NOT have strikethrough", () => {
      const todo = buildTodo({ completed: false, title: "未完了タスク" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const titleElement = screen.getByText("未完了タスク");
      expect(titleElement).not.toHaveStyle({ textDecoration: "line-through" });
    });
  });

  // ---------- Acceptance scenarios (US2) ----------

  describe("acceptance scenarios", () => {
    it("US2-AC1: uncompleted TODO -> click checkbox -> becomes completed with visual distinction", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 10, completed: false, title: "未完了のTODO" });
      const updatedTodo = buildTodo({
        id: 10,
        completed: true,
        title: "未完了のTODO",
        updated_at: "2026-03-15T02:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Step 1: Checkbox is unchecked
      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).not.toBeChecked();

      // Step 2: Click checkbox
      await user.click(checkbox);

      // Step 3: API called with completed: true
      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledWith(10, { completed: true });
      });

      // Step 4: onUpdated called with the completed todo
      expect(onUpdated).toHaveBeenCalledWith(updatedTodo);
    });

    it("US2-AC2: completed TODO -> click checkbox -> becomes uncompleted", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 11, completed: true, title: "完了済みのTODO" });
      const updatedTodo = buildTodo({
        id: 11,
        completed: false,
        title: "完了済みのTODO",
        updated_at: "2026-03-15T02:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Step 1: Checkbox is checked
      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).toBeChecked();

      // Step 2: Click checkbox
      await user.click(checkbox);

      // Step 3: API called with completed: false
      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledWith(11, { completed: false });
      });

      // Step 4: onUpdated called with the uncompleted todo
      expect(onUpdated).toHaveBeenCalledWith(updatedTodo);
    });
  });
});
