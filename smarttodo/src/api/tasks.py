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

router = APIRouter(prefix="/tasks", tags=["tasks"])

# インメモリでタスクを保持（後でDBに置き換え予定）
_tasks: list[TaskResponse] = []


def _find_task_index(task_id: UUID) -> int | None:
    """タスクのインデックスを検索"""
    for i, task in enumerate(_tasks):
        if task.id == task_id:
            return i
    return None


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    limit: int = Query(default=20, ge=1, le=100, description="取得件数（1-100）"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
    status: TaskStatus | None = Query(default=None, description="ステータスでフィルタ"),
    priority: TaskPriority | None = Query(default=None, description="優先度でフィルタ"),
) -> TaskListResponse:
    """タスク一覧を取得する"""
    filtered = _tasks

    if status is not None:
        filtered = [t for t in filtered if t.status == status]
    if priority is not None:
        filtered = [t for t in filtered if t.priority == priority]

    total = len(filtered)
    items = filtered[offset : offset + limit]

    return TaskListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskResponse:
    """タスクを作成する"""
    response = TaskResponse.from_task_create(task)
    _tasks.append(response)
    return response


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID) -> TaskResponse:
    """個別タスクを取得する"""
    index = _find_task_index(task_id)
    if index is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return _tasks[index]


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, task_update: TaskUpdate) -> TaskResponse:
    """タスクを更新する（部分更新対応）"""
    index = _find_task_index(task_id)
    if index is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    current = _tasks[index]
    update_data = task_update.model_dump(exclude_unset=True)

    updated = current.model_copy(update=update_data)
    _tasks[index] = updated
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID) -> None:
    """タスクを削除する"""
    index = _find_task_index(task_id)
    if index is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    _tasks.pop(index)
