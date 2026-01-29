"""自然言語タスク解析 API"""

from fastapi import APIRouter, Depends

from src.ai.parser import ParseRequest, ParseResponse, ParserService, get_parser_service

router = APIRouter(prefix="/tasks/parse", tags=["parser"])


@router.post("", response_model=ParseResponse)
async def parse_task(
    request: ParseRequest,
    service: ParserService = Depends(get_parser_service),
) -> ParseResponse:
    """自然言語テキストを解析してタスク情報をプレビュー"""
    return await service.parse(request.text)
