"use client";

interface TodoFilterProps {
  current: string;
  onChange: (filter: string) => void;
}

const filters = [
  { value: "all", label: "すべて" },
  { value: "active", label: "未完了" },
  { value: "completed", label: "完了" },
];

export default function TodoFilter({ current, onChange }: TodoFilterProps) {
  return (
    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
      {filters.map((f) => (
        <button
          key={f.value}
          onClick={() => onChange(f.value)}
          style={{
            padding: "0.375rem 0.75rem",
            fontSize: "0.875rem",
            border: "1px solid #ccc",
            borderRadius: "4px",
            backgroundColor: current === f.value ? "#0070f3" : "white",
            color: current === f.value ? "white" : "#333",
            cursor: "pointer",
          }}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}
