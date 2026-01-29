"""自然言語タスク解析のテスト"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.ai.parser import (
    PARSER_SYSTEM_PROMPT,
    ParsedTask,
    ParserService,
    build_parser_prompt,
)
from src.main import app
from src.models.task import TaskPriority


# --------------------------------------------------------------------------
# プロンプトテスト
# --------------------------------------------------------------------------
class TestParserPrompts:
    def test_parser_system_prompt_exists(self):
        """システムプロンプトが存在する"""
        assert PARSER_SYSTEM_PROMPT
        assert "タスク解析" in PARSER_SYSTEM_PROMPT

    def test_parser_system_prompt_contains_date_expressions(self):
        """日本語の日時表現が含まれる"""
        assert "明日" in PARSER_SYSTEM_PROMPT
        assert "来週" in PARSER_SYSTEM_PROMPT
        assert "今週中" in PARSER_SYSTEM_PROMPT

    def test_parser_system_prompt_contains_priority_criteria(self):
        """優先度の判断基準が含まれる"""
        assert "high" in PARSER_SYSTEM_PROMPT
        assert "medium" in PARSER_SYSTEM_PROMPT
        assert "low" in PARSER_SYSTEM_PROMPT
        assert "緊急" in PARSER_SYSTEM_PROMPT

    def test_build_parser_prompt(self):
        """プロンプト構築"""
        dt = datetime(2025, 1, 15, 10, 0, 0)
        prompt = build_parser_prompt("明日の会議の準備", dt)

        assert "2025-01-15T10:00:00" in prompt
        assert "明日の会議の準備" in prompt
        assert "JSON形式" in prompt

    def test_build_parser_prompt_includes_expected_fields(self):
        """プロンプトに期待されるフィールドが含まれる"""
        dt = datetime(2025, 1, 15, 10, 0, 0)
        prompt = build_parser_prompt("テスト", dt)

        assert "title" in prompt
        assert "description" in prompt
        assert "due_date" in prompt
        assert "priority" in prompt


# --------------------------------------------------------------------------
# ParserService テスト
# --------------------------------------------------------------------------
class TestParserService:
    def _create_mock_client(self, response_content: str) -> AsyncMock:
        """モッククライアントを作成"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = response_content
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        return mock_client

    # --- 正常系テスト ---

    async def test_parse_basic_task(self):
        """基本的なタスクの解析"""
        response_json = """{
            "title": "会議の準備",
            "description": "資料を作成する",
            "due_date": "2025-01-16T09:00:00",
            "priority": "high"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        result = await service.parse("明日の会議の準備")

        assert result.original_text == "明日の会議の準備"
        assert result.parsed.title == "会議の準備"
        assert result.parsed.description == "資料を作成する"
        assert result.parsed.due_date == datetime(2025, 1, 16, 9, 0, 0)
        assert result.parsed.priority == TaskPriority.HIGH

    async def test_parse_with_custom_datetime(self):
        """カスタム日時での解析"""
        response_json = """{
            "title": "レポート提出",
            "description": "",
            "due_date": "2025-02-01T00:00:00",
            "priority": "medium"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        custom_dt = datetime(2025, 1, 25, 14, 30, 0)
        await service.parse("来週レポート提出", custom_dt)

        # プロンプトにカスタム日時が含まれることを確認
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_message = messages[1]["content"]
        assert "2025-01-25T14:30:00" in user_message

    async def test_parse_task_without_due_date(self):
        """期限なしのタスク解析"""
        response_json = """{
            "title": "ドキュメント整理",
            "description": "",
            "due_date": null,
            "priority": "low"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        result = await service.parse("いつかドキュメントを整理する")

        assert result.parsed.title == "ドキュメント整理"
        assert result.parsed.due_date is None
        assert result.parsed.priority == TaskPriority.LOW

    async def test_parse_high_priority_task(self):
        """高優先度タスクの解析"""
        response_json = """{
            "title": "緊急対応",
            "description": "バグ修正が必要",
            "due_date": "2025-01-15T17:00:00",
            "priority": "high"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        result = await service.parse("至急バグを修正")

        assert result.parsed.priority == TaskPriority.HIGH

    async def test_parse_calls_openai_correctly(self):
        """OpenAI APIが正しく呼び出される"""
        mock_client = self._create_mock_client(
            '{"title": "Test", "description": "", "due_date": null, "priority": "medium"}'
        )
        service = ParserService(client=mock_client, model="gpt-4o-mini")

        await service.parse("テストタスク")

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["response_format"] == {"type": "json_object"}
        assert call_kwargs["temperature"] == 0.3

    # --- 異常系テスト ---

    async def test_parse_invalid_json_response(self):
        """不正なJSONレスポンスでも元のテキストをタイトルとして返す"""
        mock_client = self._create_mock_client("invalid json")
        service = ParserService(client=mock_client)

        result = await service.parse("テストタスク")

        assert result.parsed.title == "テストタスク"
        assert result.parsed.priority == TaskPriority.MEDIUM

    async def test_parse_empty_content(self):
        """空のコンテンツでも元のテキストをタイトルとして返す"""
        mock_client = self._create_mock_client("")
        mock_client.chat.completions.create.return_value.choices[0].message.content = None
        service = ParserService(client=mock_client)

        result = await service.parse("テストタスク")

        assert result.parsed.title == "テストタスク"

    async def test_parse_invalid_priority_fallback(self):
        """不正な優先度はmediumにフォールバック"""
        response_json = """{
            "title": "タスク",
            "description": "",
            "due_date": null,
            "priority": "invalid"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        result = await service.parse("タスク")

        assert result.parsed.priority == TaskPriority.MEDIUM

    async def test_parse_invalid_date_format(self):
        """不正な日付形式はNoneになる"""
        response_json = """{
            "title": "タスク",
            "description": "",
            "due_date": "not-a-date",
            "priority": "medium"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        result = await service.parse("タスク")

        assert result.parsed.due_date is None

    async def test_parse_missing_title_uses_original(self):
        """titleがない場合は元のテキストを使用"""
        response_json = """{
            "description": "説明のみ",
            "due_date": null,
            "priority": "medium"
        }"""
        mock_client = self._create_mock_client(response_json)
        service = ParserService(client=mock_client)

        result = await service.parse("元のテキスト")

        assert result.parsed.title == "元のテキスト"


# --------------------------------------------------------------------------
# API エンドポイントテスト
# --------------------------------------------------------------------------
class TestParserAPI:
    @pytest.fixture
    def mock_service(self):
        """モックサービスを作成"""
        service = MagicMock(spec=ParserService)
        service.parse = AsyncMock(
            return_value=MagicMock(
                original_text="明日の会議",
                parsed=ParsedTask(
                    title="会議",
                    description="",
                    due_date=datetime(2025, 1, 16, 9, 0, 0),
                    priority=TaskPriority.MEDIUM,
                ),
            )
        )
        return service

    # --- 正常系テスト ---

    async def test_parse_endpoint_success(self, mock_service):
        """POST /api/tasks/parse が動作する"""
        from src.ai.parser import get_parser_service

        app.dependency_overrides[get_parser_service] = lambda: mock_service

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/tasks/parse", json={"text": "明日の会議"})

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["original_text"] == "明日の会議"
        assert data["parsed"]["title"] == "会議"
        assert data["parsed"]["priority"] == "medium"

    async def test_parse_endpoint_with_due_date(self, mock_service):
        """期限付きタスクの解析"""
        from src.ai.parser import get_parser_service

        mock_service.parse = AsyncMock(
            return_value=MagicMock(
                original_text="来週レポート",
                parsed=ParsedTask(
                    title="レポート作成",
                    description="",
                    due_date=datetime(2025, 1, 22, 0, 0, 0),
                    priority=TaskPriority.HIGH,
                ),
            )
        )
        app.dependency_overrides[get_parser_service] = lambda: mock_service

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/tasks/parse", json={"text": "来週レポート"})

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "due_date" in data["parsed"]
        assert data["parsed"]["priority"] == "high"

    # --- 異常系テスト ---

    async def test_parse_endpoint_empty_text(self):
        """空のテキストでバリデーションエラー"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/tasks/parse", json={"text": ""})

        assert response.status_code == 422

    async def test_parse_endpoint_missing_text(self):
        """textフィールドがないとバリデーションエラー"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/tasks/parse", json={})

        assert response.status_code == 422

    async def test_parse_endpoint_text_too_long(self):
        """テキストが長すぎるとバリデーションエラー"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/tasks/parse", json={"text": "a" * 501})

        assert response.status_code == 422

    async def test_parse_endpoint_invalid_json(self):
        """不正なJSONでバリデーションエラー"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/tasks/parse", content="not json")

        assert response.status_code == 422
