"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, Clock, AlertTriangle } from "lucide-react";
import type { Task } from "@/lib/types";
import { cn } from "@/lib/utils";
import { getDueDateStatus, formatDueDate, type DueDateStatus } from "@/lib/date-utils";

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

// 期限状態に応じたスタイル
const dueDateStyles: Record<Exclude<DueDateStatus, null>, { badge: string; icon: typeof Clock }> = {
  overdue: {
    badge: "bg-red-100 text-red-700 border-red-200",
    icon: AlertTriangle,
  },
  urgent: {
    badge: "bg-yellow-100 text-yellow-700 border-yellow-200",
    icon: AlertTriangle,
  },
  upcoming: {
    badge: "bg-blue-100 text-blue-700 border-blue-200",
    icon: Clock,
  },
  normal: {
    badge: "bg-gray-100 text-gray-600 border-gray-200",
    icon: Clock,
  },
};

export function TaskItem({ task, onToggleComplete, onDelete }: TaskItemProps) {
  const isCompleted = task.status === "completed";
  const dueDateStatus = getDueDateStatus(task.due_date);
  const formattedDueDate = formatDueDate(task.due_date);

  return (
    <div
      data-testid={`task-item-${task.id}`}
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
        <div className="flex items-center gap-2 mt-1">
          {task.description && (
            <p className="text-sm text-gray-500 truncate flex-1">{task.description}</p>
          )}
          {formattedDueDate && dueDateStatus && !isCompleted && (
            <DueDateBadge status={dueDateStatus} formattedDate={formattedDueDate} />
          )}
        </div>
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

// 期限バッジコンポーネント
function DueDateBadge({
  status,
  formattedDate,
}: {
  status: Exclude<DueDateStatus, null>;
  formattedDate: string;
}) {
  const style = dueDateStyles[status];
  const Icon = style.icon;

  return (
    <Badge
      variant="outline"
      className={cn("text-xs shrink-0", style.badge)}
      aria-label={`期限: ${formattedDate}`}
    >
      <Icon className="h-3 w-3 mr-1" aria-hidden="true" />
      <span>{formattedDate}</span>
    </Badge>
  );
}
