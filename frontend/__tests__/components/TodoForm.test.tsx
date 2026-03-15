import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TodoForm from "@/components/TodoForm";
import { type Todo } from "@/lib/api";

// Mock the API module - do NOT make real API calls
jest.mock("@/lib/api", () => ({
  createTodo: jest.fn(),
}));

import { createTodo } from "@/lib/api";

const mockedCreateTodo = createTodo as jest.MockedFunction<typeof createTodo>;

// Helper: build a sample Todo response
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

describe("TodoForm", () => {
  let onCreated: jest.Mock;

  beforeEach(() => {
    onCreated = jest.fn();
    mockedCreateTodo.mockReset();
  });

  // ---------- Rendering ----------

  describe("rendering", () => {
    it("renders a text input field with a placeholder", () => {
      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      expect(input).toBeInTheDocument();
      // Placeholder should exist (exact text is up to implementation, but it must be present)
      expect(input).toHaveAttribute("placeholder");
    });

    it('renders a submit button labeled "追加"', () => {
      render(<TodoForm onCreated={onCreated} />);

      const button = screen.getByRole("button", { name: "追加" });
      expect(button).toBeInTheDocument();
    });
  });

  // ---------- Client-side validation ----------

  describe("client-side validation", () => {
    it("shows error message when submitting empty title", async () => {
      const user = userEvent.setup();
      render(<TodoForm onCreated={onCreated} />);

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      expect(
        screen.getByText("タイトルを入力してください")
      ).toBeInTheDocument();
      expect(mockedCreateTodo).not.toHaveBeenCalled();
      expect(onCreated).not.toHaveBeenCalled();
    });

    it("shows error message when submitting whitespace-only title", async () => {
      const user = userEvent.setup();
      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "   ");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      expect(
        screen.getByText("タイトルを入力してください")
      ).toBeInTheDocument();
      expect(mockedCreateTodo).not.toHaveBeenCalled();
      expect(onCreated).not.toHaveBeenCalled();
    });

    it("limits input to 200 characters via maxLength attribute", () => {
      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      expect(input).toHaveAttribute("maxLength", "200");
    });

    it("clears error message when user starts typing after validation error", async () => {
      const user = userEvent.setup();
      render(<TodoForm onCreated={onCreated} />);

      // Trigger empty title error
      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      expect(
        screen.getByText("タイトルを入力してください")
      ).toBeInTheDocument();

      // Start typing - error should clear
      const input = screen.getByRole("textbox");
      await user.type(input, "a");

      expect(
        screen.queryByText("タイトルを入力してください")
      ).not.toBeInTheDocument();
    });
  });

  // ---------- Successful submission ----------

  describe("successful submission", () => {
    it("calls createTodo with trimmed title on valid submit", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "新しいTODO" });
      mockedCreateTodo.mockResolvedValueOnce(todo);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "  新しいTODO  ");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      await waitFor(() => {
        expect(mockedCreateTodo).toHaveBeenCalledTimes(1);
        expect(mockedCreateTodo).toHaveBeenCalledWith({
          title: "新しいTODO",
        });
      });
    });

    it("calls onCreated callback with the created todo after successful API call", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "コールバックテスト" });
      mockedCreateTodo.mockResolvedValueOnce(todo);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "コールバックテスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      await waitFor(() => {
        expect(onCreated).toHaveBeenCalledTimes(1);
        expect(onCreated).toHaveBeenCalledWith(todo);
      });
    });

    it("clears input field after successful creation", async () => {
      const user = userEvent.setup();
      const todo = buildTodo({ title: "クリアテスト" });
      mockedCreateTodo.mockResolvedValueOnce(todo);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "クリアテスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      await waitFor(() => {
        expect(input).toHaveValue("");
      });
    });
  });

  // ---------- Submission state (loading) ----------

  describe("submission state", () => {
    it("disables the submit button while submitting", async () => {
      const user = userEvent.setup();
      // Create a promise that we can control to keep the submission pending
      let resolvePromise!: (value: Todo) => void;
      const pendingPromise = new Promise<Todo>((resolve) => {
        resolvePromise = resolve;
      });
      mockedCreateTodo.mockReturnValueOnce(pendingPromise);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "送信中テスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      // Button should be disabled while submitting
      await waitFor(() => {
        expect(button).toBeDisabled();
      });

      // Resolve the promise to complete submission
      resolvePromise(buildTodo({ title: "送信中テスト" }));

      // Button should be re-enabled after submission completes
      await waitFor(() => {
        expect(button).not.toBeDisabled();
      });
    });

    it("disables the input field while submitting", async () => {
      const user = userEvent.setup();
      let resolvePromise!: (value: Todo) => void;
      const pendingPromise = new Promise<Todo>((resolve) => {
        resolvePromise = resolve;
      });
      mockedCreateTodo.mockReturnValueOnce(pendingPromise);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "入力無効テスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      // Input should be disabled while submitting
      await waitFor(() => {
        expect(input).toBeDisabled();
      });

      // Resolve the promise to complete submission
      resolvePromise(buildTodo({ title: "入力無効テスト" }));

      // Input should be re-enabled after submission completes
      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
    });
  });

  // ---------- API error handling ----------

  describe("API error handling", () => {
    it("does not call onCreated when API call fails", async () => {
      const user = userEvent.setup();
      mockedCreateTodo.mockRejectedValueOnce(
        new Error("Failed to create todo: 500")
      );

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "エラーテスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      await waitFor(() => {
        expect(mockedCreateTodo).toHaveBeenCalledTimes(1);
      });

      expect(onCreated).not.toHaveBeenCalled();
    });

    it("does not clear input when API call fails", async () => {
      const user = userEvent.setup();
      mockedCreateTodo.mockRejectedValueOnce(
        new Error("Failed to create todo: 422")
      );

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "保持テスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      await waitFor(() => {
        expect(mockedCreateTodo).toHaveBeenCalledTimes(1);
      });

      // Input should still contain the text so user can retry
      expect(input).toHaveValue("保持テスト");
    });

    it("re-enables button and input after API error", async () => {
      const user = userEvent.setup();
      mockedCreateTodo.mockRejectedValueOnce(
        new Error("Failed to create todo: 500")
      );

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, "リトライテスト");

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      // After error, both should be re-enabled
      await waitFor(() => {
        expect(button).not.toBeDisabled();
        expect(input).not.toBeDisabled();
      });
    });
  });

  // ---------- Acceptance scenario: full flow ----------

  describe("acceptance scenarios", () => {
    it("US1-AC1: user enters title, clicks add, new TODO created via API, input cleared, callback invoked", async () => {
      const user = userEvent.setup();
      const createdTodo = buildTodo({
        id: 42,
        title: "買い物に行く",
      });
      mockedCreateTodo.mockResolvedValueOnce(createdTodo);

      render(<TodoForm onCreated={onCreated} />);

      // User enters title
      const input = screen.getByRole("textbox");
      await user.type(input, "買い物に行く");

      // User clicks add button
      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      // API is called with the entered title
      await waitFor(() => {
        expect(mockedCreateTodo).toHaveBeenCalledWith({
          title: "買い物に行く",
        });
      });

      // onCreated callback is invoked with the created todo
      expect(onCreated).toHaveBeenCalledWith(createdTodo);

      // Input field is cleared
      expect(input).toHaveValue("");
    });

    it("US1-AC5: user attempts to add with empty title, error displayed, TODO not added", async () => {
      const user = userEvent.setup();
      render(<TodoForm onCreated={onCreated} />);

      // User clicks add without entering title
      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      // Error is displayed
      expect(
        screen.getByText("タイトルを入力してください")
      ).toBeInTheDocument();

      // API was NOT called
      expect(mockedCreateTodo).not.toHaveBeenCalled();

      // onCreated was NOT called
      expect(onCreated).not.toHaveBeenCalled();
    });
  });

  // ---------- Edge case: 200 char boundary ----------

  describe("boundary: title length", () => {
    it("accepts a title that is exactly 200 characters", async () => {
      const user = userEvent.setup();
      const title200 = "あ".repeat(200);
      const todo = buildTodo({ title: title200 });
      mockedCreateTodo.mockResolvedValueOnce(todo);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, title200);

      const button = screen.getByRole("button", { name: "追加" });
      await user.click(button);

      await waitFor(() => {
        expect(mockedCreateTodo).toHaveBeenCalledWith({ title: title200 });
      });

      // No error message should be shown
      expect(
        screen.queryByText("タイトルは200文字以下で入力してください")
      ).not.toBeInTheDocument();
    });

    it("truncates input at 200 characters when user types beyond limit", async () => {
      const user = userEvent.setup();
      const title201 = "あ".repeat(201);

      render(<TodoForm onCreated={onCreated} />);

      const input = screen.getByRole("textbox");
      await user.type(input, title201);

      // maxLength={200} should truncate input to 200 characters
      expect(input).toHaveValue("あ".repeat(200));
    });
  });
});
