"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TaskList, TaskForm } from "@/components/tasks";
import { SuggestionsPanel } from "@/components/suggestions";
import { fetchTasks } from "@/lib/api";
import type { Task } from "@/lib/types";

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      const response = await fetchTasks({ limit: 100 });
      setTasks(response.items);
    } catch (e) {
      setError("タスクの取得に失敗しました");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <main className="container mx-auto max-w-2xl px-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-center">
              Taska
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <TaskForm onTaskCreated={loadTasks} />

            <SuggestionsPanel onTaskCreated={loadTasks} />

            {isLoading ? (
              <div className="text-center py-8 text-gray-500">読み込み中...</div>
            ) : error ? (
              <div className="text-center py-8 text-red-500">{error}</div>
            ) : (
              <TaskList initialTasks={tasks} onTasksChange={loadTasks} />
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
