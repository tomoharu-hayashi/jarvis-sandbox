"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sparkles, Plus, X, Loader2 } from "lucide-react";
import { createTask, parseTaskText } from "@/lib/api";
import type { ParsedTask, TaskPriority } from "@/lib/types";

interface TaskFormProps {
  onTaskCreated?: () => void;
}

// 優先度の表示設定
const priorityConfig: Record<
  TaskPriority,
  { label: string; variant: "default" | "secondary" | "destructive" }
> = {
  high: { label: "高", variant: "destructive" },
  medium: { label: "中", variant: "default" },
  low: { label: "低", variant: "secondary" },
};

// 日付を表示用にフォーマット
function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleString("ja-JP", {
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// 日付をinput[type=datetime-local]用にフォーマット
function formatDateForInput(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function TaskForm({ onTaskCreated }: TaskFormProps) {
  const [input, setInput] = useState("");
  const [preview, setPreview] = useState<ParsedTask | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isCreating, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  // AI解析を実行
  const handleParse = async () => {
    if (!input.trim()) return;

    setError(null);
    setIsParsing(true);
    try {
      const response = await parseTaskText(input.trim());
      setPreview(response.parsed);
    } catch {
      setError("解析に失敗しました。もう一度お試しください。");
    } finally {
      setIsParsing(false);
    }
  };

  // タスク作成を実行
  const handleCreate = () => {
    if (!preview) return;

    startTransition(async () => {
      try {
        await createTask({
          title: preview.title,
          description: preview.description || undefined,
          due_date: preview.due_date,
          priority: preview.priority,
        });
        setInput("");
        setPreview(null);
        onTaskCreated?.();
      } catch {
        setError("タスクの作成に失敗しました。");
      }
    });
  };

  // プレビューをキャンセル
  const handleCancel = () => {
    setPreview(null);
    setError(null);
  };

  // プレビューのフィールドを更新
  const updatePreview = (updates: Partial<ParsedTask>) => {
    if (!preview) return;
    setPreview({ ...preview, ...updates });
  };

  // Enterキーで解析を実行
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleParse();
    }
  };

  return (
    <div className="space-y-4">
      {/* 入力フォーム */}
      <div className="flex gap-2">
        <Input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="タスクを自然言語で入力...（例: 明日までに報告書を提出）"
          disabled={isParsing || isCreating || !!preview}
          className="flex-1"
          autoFocus
        />
        {!preview && (
          <Button
            type="button"
            onClick={handleParse}
            disabled={isParsing || !input.trim()}
            variant="default"
          >
            {isParsing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 mr-1" />
            )}
            {isParsing ? "解析中..." : "AI解析"}
          </Button>
        )}
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-md">
          {error}
        </div>
      )}

      {/* プレビュー表示 */}
      {preview && (
        <div className="border rounded-lg p-4 space-y-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">
              AI解析結果（編集可能）
            </span>
            <button
              type="button"
              onClick={handleCancel}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* タイトル */}
          <div className="space-y-2">
            <Label htmlFor="title">タイトル</Label>
            <Input
              id="title"
              value={preview.title}
              onChange={(e) => updatePreview({ title: e.target.value })}
              disabled={isCreating}
            />
          </div>

          {/* 説明 */}
          <div className="space-y-2">
            <Label htmlFor="description">説明（任意）</Label>
            <Input
              id="description"
              value={preview.description}
              onChange={(e) => updatePreview({ description: e.target.value })}
              placeholder="詳細な説明を追加..."
              disabled={isCreating}
            />
          </div>

          {/* 優先度と期限 */}
          <div className="flex flex-wrap gap-4">
            {/* 優先度 */}
            <div className="space-y-2">
              <Label>優先度</Label>
              <Select
                value={preview.priority}
                onValueChange={(value: TaskPriority) =>
                  updatePreview({ priority: value })
                }
                disabled={isCreating}
              >
                <SelectTrigger className="w-[120px]">
                  <SelectValue>
                    <Badge variant={priorityConfig[preview.priority].variant}>
                      {priorityConfig[preview.priority].label}
                    </Badge>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">
                    <Badge variant="destructive">高</Badge>
                  </SelectItem>
                  <SelectItem value="medium">
                    <Badge variant="default">中</Badge>
                  </SelectItem>
                  <SelectItem value="low">
                    <Badge variant="secondary">低</Badge>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 期限 */}
            <div className="space-y-2 flex-1">
              <Label htmlFor="due_date">期限</Label>
              <Input
                id="due_date"
                type="datetime-local"
                value={formatDateForInput(preview.due_date)}
                onChange={(e) =>
                  updatePreview({
                    due_date: e.target.value
                      ? new Date(e.target.value).toISOString()
                      : null,
                  })
                }
                disabled={isCreating}
                className="w-full"
              />
              {preview.due_date && (
                <p className="text-xs text-gray-500">
                  {formatDate(preview.due_date)}
                </p>
              )}
            </div>
          </div>

          {/* アクションボタン */}
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isCreating}
            >
              キャンセル
            </Button>
            <Button
              type="button"
              onClick={handleCreate}
              disabled={isCreating || !preview.title.trim()}
            >
              {isCreating ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Plus className="h-4 w-4 mr-1" />
              )}
              タスクを作成
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
