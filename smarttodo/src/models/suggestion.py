from pydantic import BaseModel, Field

from src.models.task import TaskPriority


class TaskSuggestion(BaseModel):
    """タスク提案"""

    title: str = Field(..., description="提案タスクのタイトル")
    reason: str = Field(..., description="提案理由")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="推奨優先度")


class SuggestionResponse(BaseModel):
    """タスク提案レスポンス"""

    suggestions: list[TaskSuggestion]
    cached: bool = Field(default=False, description="キャッシュから取得したか")
