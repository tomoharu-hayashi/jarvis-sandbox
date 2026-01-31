import json
import logging
from functools import lru_cache
from typing import Protocol

from cachetools import TTLCache
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from src.ai.client import get_openai_client
from src.ai.prompts import SUGGESTION_SYSTEM_PROMPT, build_suggestion_prompt
from src.models.task import TaskPriority, TaskResponse

logger = logging.getLogger(__name__)


class TaskSuggestion(BaseModel):
    """タスク提案"""

    title: str = Field(..., description="提案タスクのタイトル")
    reason: str = Field(..., description="提案理由")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="推奨優先度")


class SuggestionResponse(BaseModel):
    """提案レスポンス"""

    suggestions: list[TaskSuggestion]
    cached: bool = Field(default=False, description="キャッシュから取得したか")


class OpenAIClientProtocol(Protocol):
    """OpenAI クライアントのプロトコル（テスト用）"""

    @property
    def chat(self) -> "ChatProtocol": ...


class ChatProtocol(Protocol):
    @property
    def completions(self) -> "CompletionsProtocol": ...


class CompletionsProtocol(Protocol):
    async def create(self, **kwargs) -> "ChatCompletionProtocol": ...


class ChatCompletionProtocol(Protocol):
    @property
    def choices(self) -> list: ...


class SuggestionService:
    """タスク提案サービス"""

    def __init__(
        self,
        client: AsyncOpenAI | OpenAIClientProtocol | None = None,
        model: str = "gpt-4o-mini",
        cache_ttl: int = 300,  # 5分
        cache_maxsize: int = 100,
    ):
        self._client = client
        self._model = model
        self._cache: TTLCache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)

    @property
    def client(self) -> AsyncOpenAI | OpenAIClientProtocol:
        if self._client is None:
            self._client = get_openai_client()
        return self._client

    def _build_cache_key(self, tasks: list[TaskResponse], limit: int) -> str:
        """キャッシュキーを構築"""
        task_ids = sorted([str(t.id) for t in tasks])
        return f"{':'.join(task_ids)}:{limit}"

    async def get_suggestions(
        self, tasks: list[TaskResponse], limit: int = 3
    ) -> SuggestionResponse:
        """タスク提案を取得"""
        cache_key = self._build_cache_key(tasks, limit)

        # キャッシュチェック
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            return SuggestionResponse(suggestions=cached_result, cached=True)

        # プロンプト構築
        user_prompt = build_suggestion_prompt(tasks, limit)

        # OpenAI API呼び出し
        response = await self.client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1000,
        )

        # レスポンスをパース
        content = response.choices[0].message.content
        suggestions = self._parse_response(content, limit)

        # キャッシュに保存
        self._cache[cache_key] = suggestions

        return SuggestionResponse(suggestions=suggestions, cached=False)

    def _parse_response(self, content: str | None, limit: int) -> list[TaskSuggestion]:
        """OpenAI のレスポンスをパース"""
        if not content:
            return []

        try:
            data = json.loads(content)
            suggestions_data = data.get("suggestions", [])[:limit]

            suggestions = []
            for item in suggestions_data:
                priority_str = item.get("priority", "medium").lower()
                try:
                    priority = TaskPriority(priority_str)
                except ValueError:
                    priority = TaskPriority.MEDIUM

                suggestions.append(
                    TaskSuggestion(
                        title=item.get("title", ""),
                        reason=item.get("reason", ""),
                        priority=priority,
                    )
                )
            return suggestions
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"レスポンスのパースに失敗: {e}")
            return []

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()


@lru_cache(maxsize=1)
def get_suggestion_service() -> SuggestionService:
    """SuggestionService のシングルトンを取得"""
    return SuggestionService()
