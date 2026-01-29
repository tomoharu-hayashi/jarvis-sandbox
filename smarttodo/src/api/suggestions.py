from fastapi import APIRouter, Depends, Query

from src.ai.suggestions import SuggestionResponse, SuggestionService, get_suggestion_service
from src.api.tasks import _tasks

router = APIRouter(prefix="/tasks/suggestions", tags=["suggestions"])


@router.get("", response_model=SuggestionResponse)
async def get_suggestions(
    limit: int = Query(default=3, ge=1, le=10, description="提案数（1-10）"),
    service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestionResponse:
    """過去のタスクを分析して、次にやるべきタスクを提案する"""
    return await service.get_suggestions(_tasks, limit)


@router.delete("/cache", status_code=204)
async def clear_cache(
    service: SuggestionService = Depends(get_suggestion_service),
) -> None:
    """提案キャッシュをクリアする"""
    service.clear_cache()
