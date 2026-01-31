"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus } from "lucide-react";
import { createTask } from "@/lib/api";

interface TaskFormProps {
  onTaskCreated?: () => void;
}

export function TaskForm({ onTaskCreated }: TaskFormProps) {
  const [title, setTitle] = useState("");
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    startTransition(async () => {
      await createTask({ title: title.trim() });
      setTitle("");
      onTaskCreated?.();
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="新しいタスクを入力..."
        disabled={isPending}
        className="flex-1"
        autoFocus
      />
      <Button type="submit" disabled={isPending || !title.trim()}>
        <Plus className="h-4 w-4 mr-1" />
        追加
      </Button>
    </form>
  );
}
