"use client";

import { useState, FormEvent, ChangeEvent } from "react";
import { createTodo, Todo } from "../lib/api";

interface TodoFormProps {
  onCreated: (todo: Todo) => void;
}

export default function TodoForm({ onCreated }: TodoFormProps) {
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setTitle(e.target.value);
    setError("");
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    const trimmedTitle = title.trim();

    if (trimmedTitle === "") {
      setError("タイトルを入力してください");
      return;
    }

    if (trimmedTitle.length > 200) {
      setError("タイトルは200文字以下で入力してください");
      return;
    }

    setIsSubmitting(true);

    try {
      const todo = await createTodo({ title: trimmedTitle });
      setTitle("");
      onCreated(todo);
    } catch {
      // On API error: don't call onCreated, keep input value, re-enable controls
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={title}
        onChange={handleChange}
        placeholder="新しいTODOを入力..."
        maxLength={200}
        disabled={isSubmitting}
      />
      <button type="submit" disabled={isSubmitting}>
        追加
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
