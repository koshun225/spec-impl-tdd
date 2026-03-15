"use client";

export type FilterStatus = "all" | "active" | "completed";

export interface TodoFilterProps {
  currentFilter: FilterStatus;
  onFilterChange: (status: FilterStatus) => void;
}

const FILTER_OPTIONS: { label: string; value: FilterStatus }[] = [
  { label: "全件", value: "all" },
  { label: "未完了", value: "active" },
  { label: "完了済み", value: "completed" },
];

export default function TodoFilter({ currentFilter, onFilterChange }: TodoFilterProps) {
  return (
    <nav>
      {FILTER_OPTIONS.map(({ label, value }) => (
        <button
          key={value}
          onClick={() => onFilterChange(value)}
          aria-current={currentFilter === value ? "true" : undefined}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}
