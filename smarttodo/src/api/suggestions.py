from fastapi import APIRouter, Depends, Query

from src.ai.suggestions import SuggestionResponse, SuggestionService, get_suggestion_service
from src.models.task import TaskResponse
from src.services.firestore import get_repository

router = APIRouter(prefix="/tasks/suggestions", tags=["suggestions"])


@router.get("", response_model=SuggestionResponse)
async def get_suggestions(
    limit: int = Query(default=3, ge=1, le=10, description="提案数（1-10）"),
    service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestionResponse:
    """過去のタスクを分析して、次にやるべきタスクを提案する"""
    repo = get_repository()
    items, _ = await repo.list(limit=100, offset=0, status=None, priority=None)
    tasks = [TaskResponse(**item) for item in items]
    return await service.get_suggestions(tasks, limit)


@router.delete("/cache", status_code=204)
async def clear_cache(
    service: SuggestionService = Depends(get_suggestion_service),
) -> None:
    """提案キャッシュをクリアする"""
    service.clear_cache()
