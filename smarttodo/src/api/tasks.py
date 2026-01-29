from fastapi import APIRouter, status

from src.models.task import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskResponse:
    """タスクを作成する"""
    return TaskResponse.from_task_create(task)
