from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.models.task import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from src.services.firestore import get_repository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    limit: int = Query(default=20, ge=1, le=100, description="取得件数（1-100）"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
    status: TaskStatus | None = Query(default=None, description="ステータスでフィルタ"),
    priority: TaskPriority | None = Query(default=None, description="優先度でフィルタ"),
) -> TaskListResponse:
    """タスク一覧を取得する"""
    repo = get_repository()
    status_val = status.value if status else None
    priority_val = priority.value if priority else None

    items, total = await repo.list(limit, offset, status_val, priority_val)
    task_responses = [TaskResponse(**item) for item in items]

    return TaskListResponse(items=task_responses, total=total, limit=limit, offset=offset)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskResponse:
    """タスクを作成する"""
    repo = get_repository()
    task_data = {
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date,
        "status": task.status.value,
        "priority": task.priority.value,
    }
    result = await repo.create(task_data)
    return TaskResponse(**result)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID) -> TaskResponse:
    """個別タスクを取得する"""
    repo = get_repository()
    result = await repo.get(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return TaskResponse(**result)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, task_update: TaskUpdate) -> TaskResponse:
    """タスクを更新する（部分更新対応）"""
    repo = get_repository()

    # タスク存在確認
    existing = await repo.get(task_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    # 更新データを構築
    update_data = {}
    if task_update.title is not None:
        update_data["title"] = task_update.title
    if task_update.description is not None:
        update_data["description"] = task_update.description
    if task_update.due_date is not None:
        update_data["due_date"] = task_update.due_date
    if task_update.status is not None:
        update_data["status"] = task_update.status.value
    if task_update.priority is not None:
        update_data["priority"] = task_update.priority.value

    result = await repo.update(task_id, update_data)
    return TaskResponse(**result)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID) -> None:
    """タスクを削除する"""
    repo = get_repository()
    deleted = await repo.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
