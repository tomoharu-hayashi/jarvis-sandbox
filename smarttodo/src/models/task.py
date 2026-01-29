from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """タスク作成リクエスト"""

    title: str = Field(..., min_length=1, max_length=200, description="タスクのタイトル")
    description: str = Field(default="", max_length=1000, description="タスクの詳細説明")
    due_date: datetime | None = Field(default=None, description="期限日時")


class TaskResponse(BaseModel):
    """タスクレスポンス"""

    id: UUID
    title: str
    description: str
    due_date: datetime | None
    created_at: datetime

    @classmethod
    def from_task_create(cls, task: TaskCreate) -> "TaskResponse":
        return cls(
            id=uuid4(),
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            created_at=datetime.now(),
        )
