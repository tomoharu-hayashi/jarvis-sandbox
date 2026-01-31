"use client";

import { useCallback, useOptimistic, useTransition } from "react";
import { TaskItem } from "./task-item";
import type { Task } from "@/lib/types";
import { updateTask, deleteTask } from "@/lib/api";

interface TaskListProps {
  initialTasks: Task[];
  onTasksChange?: () => void;
}

export function TaskList({ initialTasks, onTasksChange }: TaskListProps) {
  const [isPending, startTransition] = useTransition();
  const [optimisticTasks, setOptimisticTasks] = useOptimistic(
    initialTasks,
    (state: Task[], update: { type: "toggle" | "delete"; task: Task }) => {
      if (update.type === "toggle") {
        return state.map((t) =>
          t.id === update.task.id
            ? {
                ...t,
                status:
                  t.status === "completed"
                    ? ("pending" as const)
                    : ("completed" as const),
              }
            : t
        );
      }
      if (update.type === "delete") {
        return state.filter((t) => t.id !== update.task.id);
      }
      return state;
    }
  );

  const handleToggleComplete = useCallback(
    (task: Task) => {
      startTransition(async () => {
        setOptimisticTasks({ type: "toggle", task });
        const newStatus = task.status === "completed" ? "pending" : "completed";
        await updateTask(task.id, { status: newStatus });
        onTasksChange?.();
      });
    },
    [setOptimisticTasks, onTasksChange]
  );

  const handleDelete = useCallback(
    (taskId: string) => {
      const task = optimisticTasks.find((t) => t.id === taskId);
      if (!task) return;

      startTransition(async () => {
        setOptimisticTasks({ type: "delete", task });
        await deleteTask(taskId);
        onTasksChange?.();
      });
    },
    [optimisticTasks, setOptimisticTasks, onTasksChange]
  );

  if (optimisticTasks.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>タスクがありません</p>
        <p className="text-sm mt-1">新しいタスクを追加してください</p>
      </div>
    );
  }

  // 未完了を上に、完了を下に表示
  const sortedTasks = [...optimisticTasks].sort((a, b) => {
    if (a.status === "completed" && b.status !== "completed") return 1;
    if (a.status !== "completed" && b.status === "completed") return -1;
    return 0;
  });

  return (
    <div className={`space-y-2 ${isPending ? "opacity-70" : ""}`}>
      {sortedTasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onToggleComplete={handleToggleComplete}
          onDelete={handleDelete}
        />
      ))}
    </div>
  );
}
