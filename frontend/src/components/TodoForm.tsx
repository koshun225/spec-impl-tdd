"use client";

import { useState } from "react";

interface TodoFormProps {
  onAdd: (title: string) => void;
}

export default function TodoForm({ onAdd }: TodoFormProps) {
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) {
      setError("タイトルを入力してください");
      return;
    }
    if (trimmed.length > 200) {
      setError("タイトルは200文字以内で入力してください");
      return;
    }
    setError("");
    onAdd(trimmed);
    setTitle("");
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="新しいTODOを入力..."
          style={{
            flex: 1,
            padding: "0.5rem",
            fontSize: "1rem",
            border: "1px solid #ccc",
            borderRadius: "4px",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "0.5rem 1rem",
            fontSize: "1rem",
            backgroundColor: "#0070f3",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          追加
        </button>
      </div>
      {error && (
        <p style={{ color: "red", margin: "0.25rem 0 0", fontSize: "0.875rem" }}>
          {error}
        </p>
      )}
    </form>
  );
}
