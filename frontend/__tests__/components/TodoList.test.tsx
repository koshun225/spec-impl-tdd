import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TodoList from "@/components/TodoList";
import { type Todo } from "@/lib/api";

// Mock TodoItem to isolate TodoList testing from TodoItem internals
jest.mock("@/components/TodoItem", () => {
  const MockTodoItem = (props: {
    todo: Todo;
    onUpdated: (todo: Todo) => void;
    onDeleted: (id: number) => void;
  }) => (
    <div data-testid={`todo-item-${props.todo.id}`}>
      <span>{props.todo.title}</span>
      <button
        data-testid={`trigger-updated-${props.todo.id}`}
        onClick={() => props.onUpdated(props.todo)}
      >
        triggerUpdated
      </button>
      <button
        data-testid={`trigger-deleted-${props.todo.id}`}
        onClick={() => props.onDeleted(props.todo.id)}
      >
        triggerDeleted
      </button>
    </div>
  );
  MockTodoItem.displayName = "MockTodoItem";
  return { __esModule: true, default: MockTodoItem };
});

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

describe("TodoList", () => {
  let onUpdated: jest.Mock;
  let onDeleted: jest.Mock;

  beforeEach(() => {
    onUpdated = jest.fn();
    onDeleted = jest.fn();
  });

  // ---------- Empty state ----------

  describe("empty state", () => {
    it("displays an empty state message when todos array is empty", () => {
      render(
        <TodoList todos={[]} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      expect(screen.getByText("TODOがありません")).toBeInTheDocument();
    });

    it("does not render any TodoItem when todos array is empty", () => {
      render(
        <TodoList todos={[]} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // No todo-item test IDs should be present
      expect(screen.queryByTestId(/^todo-item-/)).not.toBeInTheDocument();
    });
  });

  // ---------- Rendering with todos ----------

  describe("rendering with todos", () => {
    it("renders a TodoItem for each todo in the array", () => {
      const todos = [
        buildTodo({ id: 1, title: "最初のTODO" }),
        buildTodo({ id: 2, title: "二番目のTODO" }),
        buildTodo({ id: 3, title: "三番目のTODO" }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      expect(screen.getByTestId("todo-item-1")).toBeInTheDocument();
      expect(screen.getByTestId("todo-item-2")).toBeInTheDocument();
      expect(screen.getByTestId("todo-item-3")).toBeInTheDocument();
    });

    it("renders the correct number of TodoItems", () => {
      const todos = [
        buildTodo({ id: 1, title: "TODO 1" }),
        buildTodo({ id: 2, title: "TODO 2" }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      const items = screen.getAllByTestId(/^todo-item-/);
      expect(items).toHaveLength(2);
    });

    it("displays each todo title", () => {
      const todos = [
        buildTodo({ id: 1, title: "買い物に行く" }),
        buildTodo({ id: 2, title: "レポートを書く" }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      expect(screen.getByText("買い物に行く")).toBeInTheDocument();
      expect(screen.getByText("レポートを書く")).toBeInTheDocument();
    });

    it("does not show empty state message when todos exist", () => {
      const todos = [buildTodo({ id: 1, title: "何かのTODO" })];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      expect(screen.queryByText("TODOがありません")).not.toBeInTheDocument();
    });

    it("renders todos in a list element (ul)", () => {
      const todos = [
        buildTodo({ id: 1, title: "TODO A" }),
        buildTodo({ id: 2, title: "TODO B" }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      const list = screen.getByRole("list");
      expect(list).toBeInTheDocument();
    });
  });

  // ---------- Ordering ----------

  describe("ordering", () => {
    it("renders todos in the order provided", () => {
      const todos = [
        buildTodo({ id: 3, title: "三番目" }),
        buildTodo({ id: 1, title: "一番目" }),
        buildTodo({ id: 2, title: "二番目" }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      const items = screen.getAllByTestId(/^todo-item-/);
      expect(items[0]).toHaveAttribute("data-testid", "todo-item-3");
      expect(items[1]).toHaveAttribute("data-testid", "todo-item-1");
      expect(items[2]).toHaveAttribute("data-testid", "todo-item-2");
    });
  });

  // ---------- Props passing ----------

  describe("props passing", () => {
    it("passes onUpdated callback through to TodoItem", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 5, title: "コールバック確認" });

      render(
        <TodoList
          todos={[todo]}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      // Click the mock trigger button to simulate TodoItem calling onUpdated
      await user.click(screen.getByTestId("trigger-updated-5"));

      expect(onUpdated).toHaveBeenCalledTimes(1);
      expect(onUpdated).toHaveBeenCalledWith(todo);
    });

    it("passes onDeleted callback through to TodoItem", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 7, title: "削除コールバック確認" });

      render(
        <TodoList
          todos={[todo]}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      // Click the mock trigger button to simulate TodoItem calling onDeleted
      await user.click(screen.getByTestId("trigger-deleted-7"));

      expect(onDeleted).toHaveBeenCalledTimes(1);
      expect(onDeleted).toHaveBeenCalledWith(7);
    });

    it("passes the correct todo object to each TodoItem", () => {
      const todos = [
        buildTodo({ id: 1, title: "最初", completed: false }),
        buildTodo({ id: 2, title: "二番目", completed: true }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      // Each mocked TodoItem renders its todo.title
      expect(screen.getByText("最初")).toBeInTheDocument();
      expect(screen.getByText("二番目")).toBeInTheDocument();

      // Each has its own test ID matching the todo id
      expect(screen.getByTestId("todo-item-1")).toBeInTheDocument();
      expect(screen.getByTestId("todo-item-2")).toBeInTheDocument();
    });
  });

  // ---------- Single todo ----------

  describe("single todo", () => {
    it("renders correctly with a single todo item", () => {
      const todos = [buildTodo({ id: 42, title: "唯一のTODO" })];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      expect(screen.getByText("唯一のTODO")).toBeInTheDocument();
      const items = screen.getAllByTestId(/^todo-item-/);
      expect(items).toHaveLength(1);
    });
  });

  // ---------- Acceptance scenario ----------

  describe("acceptance scenarios", () => {
    it("US1-AC2: all TODOs displayed with title and status", () => {
      const todos = [
        buildTodo({ id: 1, title: "買い物に行く", completed: false }),
        buildTodo({ id: 2, title: "レポートを書く", completed: true }),
        buildTodo({ id: 3, title: "運動する", completed: false }),
      ];

      render(
        <TodoList
          todos={todos}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
        />
      );

      // All TODO titles are displayed
      expect(screen.getByText("買い物に行く")).toBeInTheDocument();
      expect(screen.getByText("レポートを書く")).toBeInTheDocument();
      expect(screen.getByText("運動する")).toBeInTheDocument();

      // All TodoItem components are rendered (one per todo)
      const items = screen.getAllByTestId(/^todo-item-/);
      expect(items).toHaveLength(3);
    });
  });

  // ---------- Edge case: FR-002 / empty list ----------

  describe("edge case: zero TODOs (FR-002)", () => {
    it("shows empty state message when displaying list with 0 TODOs", () => {
      render(
        <TodoList todos={[]} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Edge case from spec: TODO が 0 件の状態で一覧画面を表示した場合、空状態のメッセージを表示する
      const emptyMessage = screen.getByText("TODOがありません");
      expect(emptyMessage).toBeInTheDocument();
    });
  });
});
