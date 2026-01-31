// タスクのステータス
export type TaskStatus = "pending" | "in_progress" | "completed";

// タスクの優先度
export type TaskPriority = "low" | "medium" | "high";

// タスクレスポンス
export interface Task {
  id: string;
  title: string;
  description: string;
  due_date: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
}

// タスク作成リクエスト
export interface TaskCreate {
  title: string;
  description?: string;
  due_date?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
}

// タスク更新リクエスト
export interface TaskUpdate {
  title?: string;
  description?: string;
  due_date?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
}

// タスク一覧レスポンス
export interface TaskListResponse {
  items: Task[];
  total: number;
  limit: number;
  offset: number;
}
