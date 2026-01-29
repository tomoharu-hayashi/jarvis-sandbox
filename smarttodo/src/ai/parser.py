"""自然言語タスク解析サービス"""

import json
import logging
from datetime import datetime
from functools import lru_cache

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from src.ai.client import get_openai_client
from src.ai.suggestions import OpenAIClientProtocol
from src.models.task import TaskPriority

logger = logging.getLogger(__name__)


# 自然言語解析用プロンプト
PARSER_SYSTEM_PROMPT = """あなたはタスク解析アシスタントです。
ユーザーが入力した自然言語テキストからタスク情報を抽出してください。

抽出する情報:
- title: タスクのタイトル（簡潔に）
- description: タスクの詳細説明（推測できる場合のみ）
- due_date: 期限日時（ISO 8601形式、推測できる場合のみ）
- priority: 優先度（high/medium/low）

日本語の日時表現を解釈してください:
- 「明日」→ 現在日時の翌日
- 「明後日」→ 現在日時の2日後
- 「来週」→ 7日後
- 「今週中」→ 今週の日曜日
- 「今月中」→ 今月の最終日
- 「来月」→ 翌月の1日
- 「〇日後」→ 指定日数後
- 「〇時」「午前/午後〇時」→ 具体的な時刻

優先度の判断基準:
- high: 緊急、至急、重要、すぐに、今すぐ、ASAP、期限が近い（1-2日以内）
- medium: 通常のタスク、特に指定がない場合
- low: 余裕がある、時間があるとき、いつか、後で

必ずJSON形式で回答してください。
"""


def build_parser_prompt(text: str, current_datetime: datetime) -> str:
    """タスク解析用のプロンプトを構築"""
    return f"""現在日時: {current_datetime.isoformat()}

以下のテキストからタスク情報を抽出してください:
「{text}」

JSON形式で回答してください:
{{
  "title": "タスクのタイトル",
  "description": "詳細説明（なければ空文字）",
  "due_date": "YYYY-MM-DDTHH:MM:SS（推測できなければnull）",
  "priority": "high/medium/low"
}}"""


class ParsedTask(BaseModel):
    """解析結果のタスク"""

    title: str = Field(..., description="タスクのタイトル")
    description: str = Field(default="", description="タスクの詳細説明")
    due_date: datetime | None = Field(default=None, description="期限日時")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="優先度")


class ParseRequest(BaseModel):
    """解析リクエスト"""

    text: str = Field(..., min_length=1, max_length=500, description="解析するテキスト")


class ParseResponse(BaseModel):
    """解析レスポンス"""

    original_text: str = Field(..., description="元のテキスト")
    parsed: ParsedTask = Field(..., description="解析結果")


class ParserService:
    """自然言語タスク解析サービス"""

    def __init__(
        self,
        client: AsyncOpenAI | OpenAIClientProtocol | None = None,
        model: str = "gpt-4o-mini",
    ):
        self._client = client
        self._model = model

    @property
    def client(self) -> AsyncOpenAI | OpenAIClientProtocol:
        if self._client is None:
            self._client = get_openai_client()
        return self._client

    async def parse(self, text: str, current_datetime: datetime | None = None) -> ParseResponse:
        """自然言語テキストを解析してタスク情報を抽出"""
        if current_datetime is None:
            current_datetime = datetime.now()

        user_prompt = build_parser_prompt(text, current_datetime)

        response = await self.client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": PARSER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        parsed = self._parse_response(content, text)

        return ParseResponse(original_text=text, parsed=parsed)

    def _parse_response(self, content: str | None, original_text: str) -> ParsedTask:
        """OpenAI のレスポンスをパース"""
        if not content:
            return ParsedTask(title=original_text)

        try:
            data = json.loads(content)

            # 優先度のパース
            priority_str = data.get("priority", "medium").lower()
            try:
                priority = TaskPriority(priority_str)
            except ValueError:
                priority = TaskPriority.MEDIUM

            # 日時のパース
            due_date = None
            due_date_str = data.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.fromisoformat(due_date_str)
                except ValueError:
                    pass

            return ParsedTask(
                title=data.get("title", original_text),
                description=data.get("description", ""),
                due_date=due_date,
                priority=priority,
            )
        except json.JSONDecodeError as e:
            logger.error(f"レスポンスのパースに失敗: {e}")
            return ParsedTask(title=original_text)


@lru_cache(maxsize=1)
def get_parser_service() -> ParserService:
    """ParserService のシングルトンを取得"""
    return ParserService()
