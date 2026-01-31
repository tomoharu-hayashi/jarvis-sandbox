"use client";

import { useState, useCallback, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, RefreshCw, Loader2, Plus } from "lucide-react";
import { fetchSuggestions, createTask } from "@/lib/api";
import type { TaskSuggestion, TaskPriority } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SuggestionsPanelProps {
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

export function SuggestionsPanel({ onTaskCreated }: SuggestionsPanelProps) {
  const [suggestions, setSuggestions] = useState<TaskSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [isCreating, startTransition] = useTransition();
  const [creatingIndex, setCreatingIndex] = useState<number | null>(null);

  // 提案を取得
  const loadSuggestions = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetchSuggestions(3);
      setSuggestions(response.suggestions);
      setHasLoaded(true);
    } catch {
      setError("提案の取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 提案からタスクを作成
  const handleCreateTask = (suggestion: TaskSuggestion, index: number) => {
    setCreatingIndex(index);
    startTransition(async () => {
      try {
        await createTask({
          title: suggestion.title,
          priority: suggestion.priority,
        });
        // 作成したタスクを提案リストから削除
        setSuggestions((prev) => prev.filter((_, i) => i !== index));
        onTaskCreated?.();
      } catch {
        setError("タスクの作成に失敗しました");
      } finally {
        setCreatingIndex(null);
      }
    });
  };

  // 初期状態: 提案を取得するボタンを表示
  if (!hasLoaded && !isLoading) {
    return (
      <div className="border rounded-lg p-4 bg-gradient-to-r from-purple-50 to-blue-50 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-600">
            <Lightbulb className="h-5 w-5 text-amber-500" />
            <span className="font-medium">AIが次にやるべきタスクを提案</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadSuggestions}
            disabled={isLoading}
          >
            <Lightbulb className="h-4 w-4 mr-1" />
            提案を見る
          </Button>
        </div>
        {error && (
          <div className="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-md">
            {error}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-gradient-to-r from-purple-50 to-blue-50 space-y-3">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-700">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          <span className="font-medium">AIからの提案</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={loadSuggestions}
          disabled={isLoading || isCreating}
          className="text-gray-500 hover:text-gray-700"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-md">
          {error}
        </div>
      )}

      {/* ローディング */}
      {isLoading && (
        <div className="flex items-center justify-center py-6 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          分析中...
        </div>
      )}

      {/* 提案リスト */}
      {!isLoading && suggestions.length > 0 && (
        <div className="space-y-2">
          {suggestions.map((suggestion, index) => (
            <SuggestionItem
              key={`${suggestion.title}-${index}`}
              suggestion={suggestion}
              onAdd={() => handleCreateTask(suggestion, index)}
              isAdding={isCreating && creatingIndex === index}
              disabled={isCreating}
            />
          ))}
        </div>
      )}

      {/* 提案がない場合 */}
      {!isLoading && hasLoaded && suggestions.length === 0 && (
        <div className="text-center py-4 text-gray-500 text-sm">
          現在のタスクに基づく提案はありません
        </div>
      )}
    </div>
  );
}

interface SuggestionItemProps {
  suggestion: TaskSuggestion;
  onAdd: () => void;
  isAdding: boolean;
  disabled: boolean;
}

function SuggestionItem({
  suggestion,
  onAdd,
  isAdding,
  disabled,
}: SuggestionItemProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 bg-white rounded-lg border shadow-sm",
        "transition-all hover:shadow-md hover:border-purple-200"
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="font-medium text-gray-800 truncate">
            {suggestion.title}
          </p>
          <Badge variant={priorityConfig[suggestion.priority].variant}>
            {priorityConfig[suggestion.priority].label}
          </Badge>
        </div>
        <p className="text-sm text-gray-500 line-clamp-2">{suggestion.reason}</p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={onAdd}
        disabled={disabled}
        className="text-purple-500 hover:text-purple-700 hover:bg-purple-50 shrink-0"
        aria-label="このタスクを追加"
      >
        {isAdding ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Plus className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}
