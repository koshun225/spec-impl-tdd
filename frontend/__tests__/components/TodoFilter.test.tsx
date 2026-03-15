import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TodoFilter, { type FilterStatus } from "@/components/TodoFilter";

describe("TodoFilter", () => {
  let onFilterChange: jest.Mock;

  beforeEach(() => {
    onFilterChange = jest.fn();
  });

  // ---------- Rendering ----------

  describe("rendering", () => {
    it("renders three filter buttons: 全件, 未完了, 完了済み", () => {
      render(
        <TodoFilter currentFilter="all" onFilterChange={onFilterChange} />
      );

      expect(
        screen.getByRole("button", { name: "全件" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "未完了" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "完了済み" })
      ).toBeInTheDocument();
    });
  });

  // ---------- Click handlers ----------

  describe("click handlers", () => {
    it('clicking "全件" button calls onFilterChange with "all"', async () => {
      const user = userEvent.setup();
      render(
        <TodoFilter currentFilter="active" onFilterChange={onFilterChange} />
      );

      await user.click(screen.getByRole("button", { name: "全件" }));

      expect(onFilterChange).toHaveBeenCalledTimes(1);
      expect(onFilterChange).toHaveBeenCalledWith("all");
    });

    it('clicking "未完了" button calls onFilterChange with "active"', async () => {
      const user = userEvent.setup();
      render(
        <TodoFilter currentFilter="all" onFilterChange={onFilterChange} />
      );

      await user.click(screen.getByRole("button", { name: "未完了" }));

      expect(onFilterChange).toHaveBeenCalledTimes(1);
      expect(onFilterChange).toHaveBeenCalledWith("active");
    });

    it('clicking "完了済み" button calls onFilterChange with "completed"', async () => {
      const user = userEvent.setup();
      render(
        <TodoFilter currentFilter="all" onFilterChange={onFilterChange} />
      );

      await user.click(screen.getByRole("button", { name: "完了済み" }));

      expect(onFilterChange).toHaveBeenCalledTimes(1);
      expect(onFilterChange).toHaveBeenCalledWith("completed");
    });
  });

  // ---------- Active filter indication ----------

  describe("active filter indication", () => {
    it('when currentFilter is "all", the "全件" button is marked as current/active', () => {
      render(
        <TodoFilter currentFilter="all" onFilterChange={onFilterChange} />
      );

      const allButton = screen.getByRole("button", { name: "全件" });
      const activeButton = screen.getByRole("button", { name: "未完了" });
      const completedButton = screen.getByRole("button", { name: "完了済み" });

      expect(allButton).toHaveAttribute("aria-current", "true");
      expect(activeButton).not.toHaveAttribute("aria-current", "true");
      expect(completedButton).not.toHaveAttribute("aria-current", "true");
    });

    it('when currentFilter is "active", the "未完了" button is marked as current/active', () => {
      render(
        <TodoFilter currentFilter="active" onFilterChange={onFilterChange} />
      );

      const allButton = screen.getByRole("button", { name: "全件" });
      const activeButton = screen.getByRole("button", { name: "未完了" });
      const completedButton = screen.getByRole("button", { name: "完了済み" });

      expect(activeButton).toHaveAttribute("aria-current", "true");
      expect(allButton).not.toHaveAttribute("aria-current", "true");
      expect(completedButton).not.toHaveAttribute("aria-current", "true");
    });

    it('when currentFilter is "completed", the "完了済み" button is marked as current/active', () => {
      render(
        <TodoFilter
          currentFilter="completed"
          onFilterChange={onFilterChange}
        />
      );

      const allButton = screen.getByRole("button", { name: "全件" });
      const activeButton = screen.getByRole("button", { name: "未完了" });
      const completedButton = screen.getByRole("button", { name: "完了済み" });

      expect(completedButton).toHaveAttribute("aria-current", "true");
      expect(allButton).not.toHaveAttribute("aria-current", "true");
      expect(activeButton).not.toHaveAttribute("aria-current", "true");
    });
  });
});
