import type {
  Task,
  TaskCreate,
  TaskListResponse,
  TaskStatus,
  TaskPriority,
  TaskUpdate,
  ParseResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// タスク一覧を取得
export async function fetchTasks(params?: {
  limit?: number;
  offset?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
}): Promise<TaskListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.status) searchParams.set("status", params.status);
  if (params?.priority) searchParams.set("priority", params.priority);

  const query = searchParams.toString();
  const url = `${API_BASE_URL}/api/tasks${query ? `?${query}` : ""}`;

  const res = await fetch(url, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch tasks: ${res.status}`);
  }

  return res.json();
}

// タスクを作成
export async function createTask(task: TaskCreate): Promise<Task> {
  const res = await fetch(`${API_BASE_URL}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(task),
  });

  if (!res.ok) {
    throw new Error(`Failed to create task: ${res.status}`);
  }

  return res.json();
}

// タスクを更新
export async function updateTask(id: string, task: TaskUpdate): Promise<Task> {
  const res = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(task),
  });

  if (!res.ok) {
    throw new Error(`Failed to update task: ${res.status}`);
  }

  return res.json();
}

// タスクを削除
export async function deleteTask(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    throw new Error(`Failed to delete task: ${res.status}`);
  }
}

// 自然言語テキストを解析
export async function parseTaskText(text: string): Promise<ParseResponse> {
  const res = await fetch(`${API_BASE_URL}/api/tasks/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    throw new Error(`Failed to parse task: ${res.status}`);
  }

  return res.json();
}
