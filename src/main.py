"""
SmartTodo - AI アシスタント機能付き Todo アプリ
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Task:
    """タスクモデル"""
    id: int
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    due_date: datetime | None = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# インメモリストレージ（仮実装）
_tasks: dict[int, Task] = {}
_next_id = 1


def create_task(title: str, description: str = "", priority: Priority = Priority.MEDIUM) -> Task:
    """タスクを作成"""
    global _next_id
    task = Task(id=_next_id, title=title, description=description, priority=priority)
    _tasks[_next_id] = task
    _next_id += 1
    return task


def get_tasks() -> list[Task]:
    """全タスクを取得"""
    return list(_tasks.values())


def get_task(task_id: int) -> Task | None:
    """IDでタスクを取得"""
    return _tasks.get(task_id)


if __name__ == "__main__":
    # サンプル実行
    task = create_task("SmartTodo の開発を始める", priority=Priority.HIGH)
    print(f"Created: {task.title} (Priority: {task.priority.value})")
