"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import type { Task } from "@/lib/types";
import { cn } from "@/lib/utils";

interface TaskItemProps {
  task: Task;
  onToggleComplete: (task: Task) => void;
  onDelete: (taskId: string) => void;
}

// 優先度に応じた色
const priorityColors: Record<Task["priority"], string> = {
  high: "border-l-red-500",
  medium: "border-l-yellow-500",
  low: "border-l-green-500",
};

export function TaskItem({ task, onToggleComplete, onDelete }: TaskItemProps) {
  const isCompleted = task.status === "completed";

  return (
    <div
      className={cn(
        "flex items-center gap-3 p-4 bg-white rounded-lg border border-l-4 shadow-sm transition-all hover:shadow-md",
        priorityColors[task.priority],
        isCompleted && "opacity-60"
      )}
    >
      <Checkbox
        checked={isCompleted}
        onCheckedChange={() => onToggleComplete(task)}
        aria-label={isCompleted ? "未完了に戻す" : "完了にする"}
      />
      <div className="flex-1 min-w-0">
        <p
          className={cn(
            "font-medium truncate",
            isCompleted && "line-through text-gray-500"
          )}
        >
          {task.title}
        </p>
        {task.description && (
          <p className="text-sm text-gray-500 truncate">{task.description}</p>
        )}
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onDelete(task.id)}
        aria-label="タスクを削除"
        className="text-gray-400 hover:text-red-500"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
