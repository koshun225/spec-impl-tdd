import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { type Todo, type TodoListResponse } from "@/lib/api";

// ---------- Mock the API module ----------

jest.mock("@/lib/api", () => ({
  fetchTodos: jest.fn(),
  createTodo: jest.fn(),
  updateTodo: jest.fn(),
  deleteTodo: jest.fn(),
}));

import { fetchTodos } from "@/lib/api";

const mockedFetchTodos = fetchTodos as jest.MockedFunction<typeof fetchTodos>;

// ---------- Mock child components ----------

// Capture the latest props passed to each mock so tests can invoke callbacks.
let capturedTodoFormProps: { onCreated: (todo: Todo) => void } | null = null;
let capturedTodoFilterProps: {
  currentFilter: "all" | "active" | "completed";
  onFilterChange: (status: "all" | "active" | "completed") => void;
} | null = null;
let capturedTodoListProps: {
  todos: Todo[];
  onUpdated: (todo: Todo) => void;
  onDeleted: (id: number) => void;
} | null = null;

jest.mock("@/components/TodoForm", () => {
  const MockTodoForm = (props: { onCreated: (todo: Todo) => void }) => {
    capturedTodoFormProps = props;
    return (
      <div data-testid="todo-form">
        <button
          data-testid="trigger-create"
          onClick={() =>
            props.onCreated({
              id: 99,
              title: "New from form",
              completed: false,
              created_at: "2026-03-15T00:00:00Z",
              updated_at: "2026-03-15T00:00:00Z",
            })
          }
        >
          triggerCreate
        </button>
      </div>
    );
  };
  MockTodoForm.displayName = "MockTodoForm";
  return { __esModule: true, default: MockTodoForm };
});

jest.mock("@/components/TodoFilter", () => {
  const MockTodoFilter = (props: {
    currentFilter: "all" | "active" | "completed";
    onFilterChange: (status: "all" | "active" | "completed") => void;
  }) => {
    capturedTodoFilterProps = props;
    return (
      <div data-testid="todo-filter">
        <button
          data-testid="filter-all"
          onClick={() => props.onFilterChange("all")}
        >
          全件
        </button>
        <button
          data-testid="filter-active"
          onClick={() => props.onFilterChange("active")}
        >
          未完了
        </button>
        <button
          data-testid="filter-completed"
          onClick={() => props.onFilterChange("completed")}
        >
          完了済み
        </button>
      </div>
    );
  };
  MockTodoFilter.displayName = "MockTodoFilter";
  return { __esModule: true, default: MockTodoFilter };
});

jest.mock("@/components/TodoList", () => {
  const MockTodoList = (props: {
    todos: Todo[];
    onUpdated: (todo: Todo) => void;
    onDeleted: (id: number) => void;
  }) => {
    capturedTodoListProps = props;
    return (
      <div data-testid="todo-list">
        <span data-testid="todo-list-count">{props.todos.length}</span>
        {props.todos.map((t) => (
          <div key={t.id} data-testid={`todo-in-list-${t.id}`}>
            {t.title}
          </div>
        ))}
      </div>
    );
  };
  MockTodoList.displayName = "MockTodoList";
  return { __esModule: true, default: MockTodoList };
});

// ---------- Import the component under test AFTER mocks ----------

import Home from "@/app/page";

// ---------- Helpers ----------

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

function buildTodoListResponse(todos: Todo[]): TodoListResponse {
  return { todos, total: todos.length };
}

// ---------- Tests ----------

describe("Home page (T023)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    capturedTodoFormProps = null;
    capturedTodoFilterProps = null;
    capturedTodoListProps = null;
    // Default: fetchTodos resolves with empty list
    mockedFetchTodos.mockResolvedValue(buildTodoListResponse([]));
  });

  // ---------- Page title ----------

  describe("page title", () => {
    it('renders an h1 with text "TODO App"', async () => {
      await act(async () => {
        render(<Home />);
      });

      const heading = screen.getByRole("heading", { level: 1 });
      expect(heading).toHaveTextContent("TODO App");
    });
  });

  // ---------- Renders components ----------

  describe("renders components", () => {
    it("renders TodoForm component", async () => {
      await act(async () => {
        render(<Home />);
      });

      expect(screen.getByTestId("todo-form")).toBeInTheDocument();
    });

    it("renders TodoList component", async () => {
      await act(async () => {
        render(<Home />);
      });

      expect(screen.getByTestId("todo-list")).toBeInTheDocument();
    });
  });

  // ---------- Initial load ----------

  describe("initial load", () => {
    it("calls fetchTodos on mount", async () => {
      await act(async () => {
        render(<Home />);
      });

      expect(mockedFetchTodos).toHaveBeenCalledTimes(1);
    });

    it("passes loaded todos to TodoList after fetchTodos resolves", async () => {
      const todos = [
        buildTodo({ id: 1, title: "最初のTODO" }),
        buildTodo({ id: 2, title: "二番目のTODO" }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(todos));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps).not.toBeNull();
        expect(capturedTodoListProps!.todos).toHaveLength(2);
        expect(capturedTodoListProps!.todos[0].title).toBe("最初のTODO");
        expect(capturedTodoListProps!.todos[1].title).toBe("二番目のTODO");
      });
    });

    it("initially passes empty array to TodoList before fetch completes", async () => {
      // Use a delayed promise so we can inspect state before resolution
      let resolveFetch!: (value: TodoListResponse) => void;
      const pendingFetch = new Promise<TodoListResponse>((resolve) => {
        resolveFetch = resolve;
      });
      mockedFetchTodos.mockReturnValue(pendingFetch);

      await act(async () => {
        render(<Home />);
      });

      // Before fetch resolves, TodoList should have 0 todos
      expect(capturedTodoListProps).not.toBeNull();
      expect(capturedTodoListProps!.todos).toHaveLength(0);

      // Now resolve to clean up
      await act(async () => {
        resolveFetch(buildTodoListResponse([]));
      });
    });
  });

  // ---------- Create flow ----------

  describe("create flow", () => {
    it("adds new todo to the list when TodoForm's onCreated fires", async () => {
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([]));

      await act(async () => {
        render(<Home />);
      });

      // Wait for initial fetch to complete
      await waitFor(() => {
        expect(capturedTodoListProps).not.toBeNull();
      });

      const newTodo = buildTodo({ id: 99, title: "New from form" });

      // After create, the page re-fetches todos — mock the re-fetch response
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([newTodo]));

      // Simulate TodoForm calling onCreated
      await act(async () => {
        capturedTodoFormProps!.onCreated(newTodo);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(1);
        expect(capturedTodoListProps!.todos[0]).toEqual(newTodo);
      });
    });

    it("appends new todo without removing existing ones", async () => {
      const existingTodos = [
        buildTodo({ id: 1, title: "既存のTODO" }),
      ];
      mockedFetchTodos.mockResolvedValue(
        buildTodoListResponse(existingTodos)
      );

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(1);
      });

      const newTodo = buildTodo({ id: 2, title: "追加されたTODO" });

      // After create, the page re-fetches todos — mock the re-fetch response
      mockedFetchTodos.mockResolvedValue(
        buildTodoListResponse([...existingTodos, newTodo])
      );

      await act(async () => {
        capturedTodoFormProps!.onCreated(newTodo);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(2);
        expect(capturedTodoListProps!.todos.find((t) => t.id === 1)).toBeTruthy();
        expect(capturedTodoListProps!.todos.find((t) => t.id === 2)).toBeTruthy();
      });
    });
  });

  // ---------- Update flow ----------

  describe("update flow", () => {
    it("replaces the matching todo when TodoList's onUpdated fires", async () => {
      const todos = [
        buildTodo({ id: 1, title: "元のタイトル", completed: false }),
        buildTodo({ id: 2, title: "変わらないTODO", completed: false }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(todos));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(2);
      });

      const updatedTodo = buildTodo({
        id: 1,
        title: "更新後タイトル",
        completed: true,
        updated_at: "2026-03-15T01:00:00Z",
      });

      act(() => {
        capturedTodoListProps!.onUpdated(updatedTodo);
      });

      await waitFor(() => {
        const todoInList = capturedTodoListProps!.todos.find((t) => t.id === 1);
        expect(todoInList).toBeDefined();
        expect(todoInList!.title).toBe("更新後タイトル");
        expect(todoInList!.completed).toBe(true);
      });

      // Other todo remains unchanged
      const otherTodo = capturedTodoListProps!.todos.find((t) => t.id === 2);
      expect(otherTodo).toBeDefined();
      expect(otherTodo!.title).toBe("変わらないTODO");
    });

    it("preserves total count after update", async () => {
      const todos = [
        buildTodo({ id: 1, title: "TODO A" }),
        buildTodo({ id: 2, title: "TODO B" }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(todos));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(2);
      });

      const updatedTodo = buildTodo({ id: 1, title: "TODO A (updated)" });

      act(() => {
        capturedTodoListProps!.onUpdated(updatedTodo);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(2);
      });
    });
  });

  // ---------- Delete flow ----------

  describe("delete flow", () => {
    it("removes the todo with matching id when TodoList's onDeleted fires", async () => {
      const todos = [
        buildTodo({ id: 1, title: "削除されるTODO" }),
        buildTodo({ id: 2, title: "残るTODO" }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(todos));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(2);
      });

      act(() => {
        capturedTodoListProps!.onDeleted(1);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(1);
        expect(capturedTodoListProps!.todos[0].id).toBe(2);
        expect(capturedTodoListProps!.todos[0].title).toBe("残るTODO");
      });
    });

    it("results in empty list when last todo is deleted", async () => {
      const todos = [buildTodo({ id: 1, title: "最後のTODO" })];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(todos));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(1);
      });

      act(() => {
        capturedTodoListProps!.onDeleted(1);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(0);
      });
    });
  });

  // ---------- Acceptance scenarios ----------

  describe("acceptance scenarios", () => {
    it("US1-AC1: when user creates a todo, it appears in the list", async () => {
      // Start with empty list
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([]));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(0);
      });

      // Simulate user creating a new todo via TodoForm
      const createdTodo = buildTodo({ id: 42, title: "買い物に行く" });

      // After create, the page re-fetches todos — mock the re-fetch response
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([createdTodo]));

      await act(async () => {
        capturedTodoFormProps!.onCreated(createdTodo);
      });

      // New todo should now appear in TodoList
      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(1);
        expect(capturedTodoListProps!.todos[0].id).toBe(42);
        expect(capturedTodoListProps!.todos[0].title).toBe("買い物に行く");
      });
    });

    it("US1-AC2: when user opens the page, all existing TODOs are displayed", async () => {
      const existingTodos = [
        buildTodo({ id: 1, title: "買い物に行く", completed: false }),
        buildTodo({ id: 2, title: "レポートを書く", completed: true }),
        buildTodo({ id: 3, title: "運動する", completed: false }),
      ];
      mockedFetchTodos.mockResolvedValue(
        buildTodoListResponse(existingTodos)
      );

      await act(async () => {
        render(<Home />);
      });

      // fetchTodos was called on mount
      expect(mockedFetchTodos).toHaveBeenCalledTimes(1);

      // All todos passed to TodoList
      await waitFor(() => {
        expect(capturedTodoListProps!.todos).toHaveLength(3);
        expect(capturedTodoListProps!.todos[0].title).toBe("買い物に行く");
        expect(capturedTodoListProps!.todos[1].title).toBe("レポートを書く");
        expect(capturedTodoListProps!.todos[2].title).toBe("運動する");
      });
    });
  });

  // ---------- Filter integration (T029) ----------

  describe("Filter integration (T029)", () => {
    it("renders the TodoFilter component on the page", async () => {
      await act(async () => {
        render(<Home />);
      });

      expect(screen.getByTestId("todo-filter")).toBeInTheDocument();
    });

    it('default filter is "all" — fetchTodos is called with default (no filter or "all")', async () => {
      await act(async () => {
        render(<Home />);
      });

      // fetchTodos should have been called once on mount
      expect(mockedFetchTodos).toHaveBeenCalledTimes(1);
      // Called with no arguments or "all"
      const callArgs = mockedFetchTodos.mock.calls[0];
      expect(callArgs.length === 0 || callArgs[0] === "all").toBe(true);

      // TodoFilter should receive currentFilter="all"
      expect(capturedTodoFilterProps).not.toBeNull();
      expect(capturedTodoFilterProps!.currentFilter).toBe("all");
    });

    it('clicking "未完了" filter button triggers fetchTodos with status="active"', async () => {
      const allTodos = [
        buildTodo({ id: 1, title: "TODO 1", completed: false }),
        buildTodo({ id: 2, title: "TODO 2", completed: true }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(allTodos));

      await act(async () => {
        render(<Home />);
      });

      // Wait for initial load
      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledTimes(1);
      });

      // Setup mock for filtered response
      const activeTodos = [
        buildTodo({ id: 1, title: "TODO 1", completed: false }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(activeTodos));

      // Click the "未完了" filter button
      const user = userEvent.setup();
      await user.click(screen.getByTestId("filter-active"));

      // fetchTodos should be called again with "active"
      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledWith("active");
      });

      // TodoFilter should reflect the new filter state
      await waitFor(() => {
        expect(capturedTodoFilterProps!.currentFilter).toBe("active");
      });
    });

    it('clicking "完了済み" filter button triggers fetchTodos with status="completed"', async () => {
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([]));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledTimes(1);
      });

      const completedTodos = [
        buildTodo({ id: 2, title: "完了TODO", completed: true }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(completedTodos));

      const user = userEvent.setup();
      await user.click(screen.getByTestId("filter-completed"));

      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledWith("completed");
      });

      await waitFor(() => {
        expect(capturedTodoFilterProps!.currentFilter).toBe("completed");
      });
    });

    it('clicking "全件" filter button after filtering triggers fetchTodos with default', async () => {
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([]));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledTimes(1);
      });

      // First, switch to "active" filter
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse([]));
      const user = userEvent.setup();
      await user.click(screen.getByTestId("filter-active"));

      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledWith("active");
      });

      // Now switch back to "all"
      const allTodos = [
        buildTodo({ id: 1, title: "TODO 1", completed: false }),
        buildTodo({ id: 2, title: "TODO 2", completed: true }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(allTodos));

      await user.click(screen.getByTestId("filter-all"));

      // fetchTodos should be called with "all" or no argument
      await waitFor(() => {
        const lastCall = mockedFetchTodos.mock.calls[mockedFetchTodos.mock.calls.length - 1];
        expect(lastCall[0] === "all" || lastCall[0] === undefined).toBe(true);
      });

      await waitFor(() => {
        expect(capturedTodoFilterProps!.currentFilter).toBe("all");
      });
    });

    it("after adding a new todo while filter is active, fetchTodos is re-called with current filter", async () => {
      // Start with some todos
      const initialTodos = [
        buildTodo({ id: 1, title: "既存の未完了TODO", completed: false }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(initialTodos));

      await act(async () => {
        render(<Home />);
      });

      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledTimes(1);
      });

      // Switch to "active" filter
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(initialTodos));
      const user = userEvent.setup();
      await user.click(screen.getByTestId("filter-active"));

      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledWith("active");
      });

      // Clear mock to track only new calls
      mockedFetchTodos.mockClear();

      // Setup the response for after adding a todo (re-fetch with filter)
      const updatedActiveTodos = [
        buildTodo({ id: 1, title: "既存の未完了TODO", completed: false }),
        buildTodo({ id: 99, title: "New from form", completed: false }),
      ];
      mockedFetchTodos.mockResolvedValue(buildTodoListResponse(updatedActiveTodos));

      // Simulate adding a new todo via TodoForm's onCreated callback
      await act(async () => {
        capturedTodoFormProps!.onCreated(
          buildTodo({ id: 99, title: "New from form", completed: false })
        );
      });

      // After creating a todo while a filter is active, fetchTodos should be
      // re-called with the current filter to get the correct filtered list
      await waitFor(() => {
        expect(mockedFetchTodos).toHaveBeenCalledWith("active");
      });
    });
  });
});
