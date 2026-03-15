import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TodoItem from "@/components/TodoItem";
import { type Todo } from "@/lib/api";

// Mock the API module - do NOT make real API calls
jest.mock("@/lib/api", () => ({
  updateTodo: jest.fn(),
  deleteTodo: jest.fn(),
}));

import { updateTodo, deleteTodo } from "@/lib/api";

const mockedUpdateTodo = updateTodo as jest.MockedFunction<typeof updateTodo>;
const mockedDeleteTodo = deleteTodo as jest.MockedFunction<typeof deleteTodo>;

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

describe("TodoItem", () => {
  let onUpdated: jest.Mock;
  let onDeleted: jest.Mock;

  beforeEach(() => {
    onUpdated = jest.fn();
    onDeleted = jest.fn();
    mockedUpdateTodo.mockReset();
    mockedDeleteTodo.mockReset();
    // Reset window.confirm mock between tests
    jest.restoreAllMocks();
  });

  // ---------- Rendering ----------

  describe("rendering", () => {
    it("displays the TODO title as text", () => {
      const todo = buildTodo({ title: "買い物に行く" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      expect(screen.getByText("買い物に行く")).toBeInTheDocument();
    });

    it("renders a delete button", () => {
      const todo = buildTodo();
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const deleteButton = screen.getByRole("button", { name: /削除|delete/i });
      expect(deleteButton).toBeInTheDocument();
    });
  });

  // ---------- Completed visual (FR-009) ----------

  describe("completed visual (FR-009)", () => {
    it("shows strikethrough style for completed TODOs", () => {
      const todo = buildTodo({ completed: true, title: "完了済みTODO" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const titleElement = screen.getByText("完了済みTODO");
      expect(titleElement).toHaveStyle({ textDecoration: "line-through" });
    });

    it("does not show strikethrough style for incomplete TODOs", () => {
      const todo = buildTodo({ completed: false, title: "未完了TODO" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const titleElement = screen.getByText("未完了TODO");
      expect(titleElement).not.toHaveStyle({ textDecoration: "line-through" });
    });
  });

  // ---------- Inline edit activation (FR-003) ----------

  describe("inline edit activation", () => {
    it("enters edit mode when title text is clicked, showing input with current title", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "編集対象TODO" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Click on the title text
      await user.click(screen.getByText("編集対象TODO"));

      // An input field should appear with the current title pre-filled
      const input = screen.getByRole("textbox");
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue("編集対象TODO");
    });

    it("does not show an input field before title is clicked", () => {
      const todo = buildTodo({ title: "クリック前" });
      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    });
  });

  // ---------- Inline edit save ----------

  describe("inline edit save", () => {
    it("saves on Enter key: calls updateTodo API then onUpdated callback", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 5, title: "元のタイトル" });
      const updatedTodo = buildTodo({
        id: 5,
        title: "新しいタイトル",
        updated_at: "2026-03-15T01:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("元のタイトル"));

      // Clear and type new title
      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "新しいタイトル");

      // Press Enter to save
      await user.keyboard("{Enter}");

      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledTimes(1);
        expect(mockedUpdateTodo).toHaveBeenCalledWith(5, {
          title: "新しいタイトル",
        });
      });

      await waitFor(() => {
        expect(onUpdated).toHaveBeenCalledTimes(1);
        expect(onUpdated).toHaveBeenCalledWith(updatedTodo);
      });
    });

    it("saves on blur (focus loss): calls updateTodo API then onUpdated callback", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 3, title: "フォーカス前" });
      const updatedTodo = buildTodo({
        id: 3,
        title: "フォーカス後",
        updated_at: "2026-03-15T01:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("フォーカス前"));

      // Clear and type new title
      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "フォーカス後");

      // Blur the input (Tab away)
      await user.tab();

      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledTimes(1);
        expect(mockedUpdateTodo).toHaveBeenCalledWith(3, {
          title: "フォーカス後",
        });
      });

      await waitFor(() => {
        expect(onUpdated).toHaveBeenCalledTimes(1);
        expect(onUpdated).toHaveBeenCalledWith(updatedTodo);
      });
    });

    it("exits edit mode after successful save", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 2, title: "保存前" });
      const updatedTodo = buildTodo({ id: 2, title: "保存後" });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("保存前"));
      expect(screen.getByRole("textbox")).toBeInTheDocument();

      // Type new title and press Enter
      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "保存後");
      await user.keyboard("{Enter}");

      // After save completes, input should disappear (back to text display)
      await waitFor(() => {
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      });
    });
  });

  // ---------- Inline edit cancel ----------

  describe("inline edit cancel", () => {
    it("reverts to original title on Escape key and does not call API", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "元のタイトル" });

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("元のタイトル"));

      // Change the title
      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "変更中のタイトル");

      // Press Escape to cancel
      await user.keyboard("{Escape}");

      // Should exit edit mode and show original title
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      expect(screen.getByText("元のタイトル")).toBeInTheDocument();

      // API should NOT have been called
      expect(mockedUpdateTodo).not.toHaveBeenCalled();
      expect(onUpdated).not.toHaveBeenCalled();
    });
  });

  // ---------- Inline edit empty/whitespace ----------

  describe("inline edit with empty or whitespace-only title", () => {
    it("reverts to original title when input is cleared to empty and Enter pressed", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "空にしない" });

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("空にしない"));

      // Clear the input completely
      const input = screen.getByRole("textbox");
      await user.clear(input);

      // Press Enter
      await user.keyboard("{Enter}");

      // Should revert to original title, no API call
      await waitFor(() => {
        expect(screen.getByText("空にしない")).toBeInTheDocument();
      });
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      expect(mockedUpdateTodo).not.toHaveBeenCalled();
      expect(onUpdated).not.toHaveBeenCalled();
    });

    it("reverts to original title when input is whitespace-only and Enter pressed", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "スペースのみ" });

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("スペースのみ"));

      // Replace with whitespace
      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "   ");

      // Press Enter
      await user.keyboard("{Enter}");

      // Should revert to original title, no API call
      await waitFor(() => {
        expect(screen.getByText("スペースのみ")).toBeInTheDocument();
      });
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      expect(mockedUpdateTodo).not.toHaveBeenCalled();
      expect(onUpdated).not.toHaveBeenCalled();
    });

    it("reverts to original title when input is empty and blur occurs", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "ブラー空" });

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("ブラー空"));

      // Clear the input
      const input = screen.getByRole("textbox");
      await user.clear(input);

      // Blur the input
      await user.tab();

      // Should revert to original title, no API call
      await waitFor(() => {
        expect(screen.getByText("ブラー空")).toBeInTheDocument();
      });
      expect(mockedUpdateTodo).not.toHaveBeenCalled();
      expect(onUpdated).not.toHaveBeenCalled();
    });
  });

  // ---------- Delete with confirmation (FR-004) ----------

  describe("delete with confirmation dialog", () => {
    it("calls deleteTodo API and onDeleted callback when user confirms", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 7 });
      jest.spyOn(window, "confirm").mockReturnValue(true);
      mockedDeleteTodo.mockResolvedValueOnce(undefined);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const deleteButton = screen.getByRole("button", { name: /削除|delete/i });
      await user.click(deleteButton);

      // window.confirm should have been called
      expect(window.confirm).toHaveBeenCalledTimes(1);

      // API should be called with the todo id
      await waitFor(() => {
        expect(mockedDeleteTodo).toHaveBeenCalledTimes(1);
        expect(mockedDeleteTodo).toHaveBeenCalledWith(7);
      });

      // onDeleted callback should be called with the todo id
      await waitFor(() => {
        expect(onDeleted).toHaveBeenCalledTimes(1);
        expect(onDeleted).toHaveBeenCalledWith(7);
      });
    });

    it("does not call API or callback when user cancels confirmation", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 9 });
      jest.spyOn(window, "confirm").mockReturnValue(false);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const deleteButton = screen.getByRole("button", { name: /削除|delete/i });
      await user.click(deleteButton);

      // window.confirm should have been called
      expect(window.confirm).toHaveBeenCalledTimes(1);

      // Neither API nor callback should be called
      expect(mockedDeleteTodo).not.toHaveBeenCalled();
      expect(onDeleted).not.toHaveBeenCalled();
    });

    it("shows a confirmation dialog (window.confirm) when delete button is clicked", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 4 });
      jest.spyOn(window, "confirm").mockReturnValue(false);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      const deleteButton = screen.getByRole("button", { name: /削除|delete/i });
      await user.click(deleteButton);

      expect(window.confirm).toHaveBeenCalled();
    });
  });

  // ---------- Acceptance scenarios ----------

  describe("acceptance scenarios", () => {
    it("US1-AC3: click title → inline edit activates → changes saved and reflected", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 10, title: "元のタスク" });
      const updatedTodo = buildTodo({
        id: 10,
        title: "編集済みタスク",
        updated_at: "2026-03-15T02:00:00Z",
      });
      mockedUpdateTodo.mockResolvedValueOnce(updatedTodo);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Step 1: Title is displayed as text
      expect(screen.getByText("元のタスク")).toBeInTheDocument();

      // Step 2: Click on the title to activate inline edit mode
      await user.click(screen.getByText("元のタスク"));

      // Step 3: Input field appears with current title
      const input = screen.getByRole("textbox");
      expect(input).toHaveValue("元のタスク");

      // Step 4: User changes the title
      await user.clear(input);
      await user.type(input, "編集済みタスク");

      // Step 5: User presses Enter to save
      await user.keyboard("{Enter}");

      // Step 6: API is called with the updated title
      await waitFor(() => {
        expect(mockedUpdateTodo).toHaveBeenCalledWith(10, {
          title: "編集済みタスク",
        });
      });

      // Step 7: onUpdated callback is invoked with the updated todo
      expect(onUpdated).toHaveBeenCalledWith(updatedTodo);
    });

    it("US1-AC4: delete button → confirmation dialog → after confirm, TODO removed", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ id: 20, title: "削除対象タスク" });
      jest.spyOn(window, "confirm").mockReturnValue(true);
      mockedDeleteTodo.mockResolvedValueOnce(undefined);

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Step 1: TODO is displayed
      expect(screen.getByText("削除対象タスク")).toBeInTheDocument();

      // Step 2: User clicks delete button
      const deleteButton = screen.getByRole("button", { name: /削除|delete/i });
      await user.click(deleteButton);

      // Step 3: Confirmation dialog appears
      expect(window.confirm).toHaveBeenCalled();

      // Step 4: After confirmation, API is called
      await waitFor(() => {
        expect(mockedDeleteTodo).toHaveBeenCalledWith(20);
      });

      // Step 5: onDeleted callback is invoked
      expect(onDeleted).toHaveBeenCalledWith(20);
    });
  });

  // ---------- Edge case: title unchanged ----------

  describe("edge case: title unchanged", () => {
    it("does not call API when title is unchanged on Enter", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "変更なし" });

      render(
        <TodoItem todo={todo} onUpdated={onUpdated} onDeleted={onDeleted} />
      );

      // Enter edit mode
      await user.click(screen.getByText("変更なし"));

      // Press Enter without changing the title
      await user.keyboard("{Enter}");

      // No API call should be made since title is unchanged
      expect(mockedUpdateTodo).not.toHaveBeenCalled();
      expect(onUpdated).not.toHaveBeenCalled();
    });
  });
});
