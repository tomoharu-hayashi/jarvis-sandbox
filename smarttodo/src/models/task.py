from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """タスクのステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    """タスクの優先度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCreate(BaseModel):
    """タスク作成リクエスト"""

    title: str = Field(..., min_length=1, max_length=200, description="タスクのタイトル")
    description: str = Field(default="", max_length=1000, description="タスクの詳細説明")
    due_date: datetime | None = Field(default=None, description="期限日時")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="ステータス")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="優先度")


class TaskResponse(BaseModel):
    """タスクレスポンス"""

    id: UUID
    title: str
    description: str
    due_date: datetime | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime

    @classmethod
    def from_task_create(cls, task: TaskCreate) -> "TaskResponse":
        return cls(
            id=uuid4(),
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            status=task.status,
            priority=task.priority,
            created_at=datetime.now(),
        )


class TaskListResponse(BaseModel):
    """タスク一覧レスポンス"""

    items: list[TaskResponse]
    total: int
    limit: int
    offset: int
