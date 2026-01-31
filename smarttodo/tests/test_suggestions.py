from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.ai.prompts import SUGGESTION_SYSTEM_PROMPT, build_suggestion_prompt
from src.ai.suggestions import SuggestionService, TaskSuggestion
from src.main import app
from src.models.task import TaskPriority, TaskResponse, TaskStatus
from src.services.firestore import InMemoryTaskRepository, reset_repository, set_repository


@pytest.fixture
async def client():
    reset_repository()
    repo = InMemoryTaskRepository()
    set_repository(repo)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    reset_repository()


@pytest.fixture
def sample_tasks() -> list[TaskResponse]:
    """テスト用タスクリスト"""
    return [
        TaskResponse(
            id=uuid4(),
            title="週次レポート作成",
            description="先週の成果をまとめる",
            due_date=datetime(2025, 1, 31),
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            created_at=datetime.now(),
        ),
        TaskResponse(
            id=uuid4(),
            title="ミーティング準備",
            description="資料を作成する",
            due_date=None,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.now(),
        ),
    ]


# --------------------------------------------------------------------------
# プロンプトテスト
# --------------------------------------------------------------------------
class TestPrompts:
    def test_suggestion_system_prompt_exists(self):
        """システムプロンプトが存在する"""
        assert SUGGESTION_SYSTEM_PROMPT
        assert "タスク管理" in SUGGESTION_SYSTEM_PROMPT

    def test_build_suggestion_prompt_with_empty_tasks(self):
        """タスクが空の場合のプロンプト"""
        prompt = build_suggestion_prompt([], limit=3)
        assert "タスク履歴がありません" in prompt
        assert "3件" in prompt

    def test_build_suggestion_prompt_with_tasks(self, sample_tasks):
        """タスクがある場合のプロンプト"""
        prompt = build_suggestion_prompt(sample_tasks, limit=3)
        assert "週次レポート作成" in prompt
        assert "ミーティング準備" in prompt
        assert "3件" in prompt
        assert "JSON形式" in prompt


# --------------------------------------------------------------------------
# SuggestionService テスト
# --------------------------------------------------------------------------
class TestSuggestionService:
    def _create_mock_client(self, response_content: str) -> AsyncMock:
        """モッククライアントを作成"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = response_content
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        return mock_client

    async def test_get_suggestions_calls_openai(self, sample_tasks):
        """OpenAI APIが呼び出される"""
        response_json = (
            '{"suggestions": [{"title": "Test", "reason": "reason", "priority": "high"}]}'
        )
        mock_client = self._create_mock_client(response_json)
        service = SuggestionService(client=mock_client)

        result = await service.get_suggestions(sample_tasks, limit=3)

        assert mock_client.chat.completions.create.called
        assert len(result.suggestions) == 1
        assert result.suggestions[0].title == "Test"
        assert result.suggestions[0].priority == TaskPriority.HIGH
        assert result.cached is False

    async def test_get_suggestions_with_empty_tasks(self):
        """タスクが空でも提案を取得"""
        response = '{"suggestions": [{"title": "Init", "reason": "Start", "priority": "medium"}]}'
        mock_client = self._create_mock_client(response)
        service = SuggestionService(client=mock_client)

        result = await service.get_suggestions([], limit=3)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].title == "Init"

    async def test_get_suggestions_cache_hit(self, sample_tasks):
        """キャッシュヒット時はAPIを呼ばない"""
        mock_client = self._create_mock_client(
            '{"suggestions": [{"title": "タスク1", "reason": "理由1", "priority": "low"}]}'
        )
        service = SuggestionService(client=mock_client)

        # 1回目
        result1 = await service.get_suggestions(sample_tasks, limit=3)
        assert result1.cached is False

        # 2回目（キャッシュヒット）
        result2 = await service.get_suggestions(sample_tasks, limit=3)
        assert result2.cached is True

        # APIは1回だけ呼ばれる
        assert mock_client.chat.completions.create.call_count == 1

    async def test_get_suggestions_different_limit_no_cache(self, sample_tasks):
        """limit が異なる場合はキャッシュを使わない"""
        mock_client = self._create_mock_client(
            '{"suggestions": [{"title": "タスク1", "reason": "理由1", "priority": "medium"}]}'
        )
        service = SuggestionService(client=mock_client)

        await service.get_suggestions(sample_tasks, limit=3)
        await service.get_suggestions(sample_tasks, limit=5)

        assert mock_client.chat.completions.create.call_count == 2

    async def test_clear_cache(self, sample_tasks):
        """キャッシュクリアが機能する"""
        mock_client = self._create_mock_client(
            '{"suggestions": [{"title": "タスク1", "reason": "理由1", "priority": "medium"}]}'
        )
        service = SuggestionService(client=mock_client)

        await service.get_suggestions(sample_tasks, limit=3)
        service.clear_cache()
        result = await service.get_suggestions(sample_tasks, limit=3)

        # キャッシュクリア後は新規取得
        assert result.cached is False
        assert mock_client.chat.completions.create.call_count == 2

    async def test_parse_response_handles_invalid_json(self, sample_tasks):
        """不正なJSONでも空リストを返す"""
        mock_client = self._create_mock_client("invalid json")
        service = SuggestionService(client=mock_client)

        result = await service.get_suggestions(sample_tasks, limit=3)

        assert result.suggestions == []

    async def test_parse_response_handles_empty_content(self, sample_tasks):
        """空のコンテンツでも空リストを返す"""
        mock_client = self._create_mock_client("")
        mock_client.chat.completions.create.return_value.choices[0].message.content = None
        service = SuggestionService(client=mock_client)

        result = await service.get_suggestions(sample_tasks, limit=3)

        assert result.suggestions == []

    async def test_parse_response_limits_suggestions(self, sample_tasks):
        """limit を超える提案は切り捨てる"""
        mock_client = self._create_mock_client(
            """{
            "suggestions": [
                {"title": "タスク1", "reason": "理由1", "priority": "high"},
                {"title": "タスク2", "reason": "理由2", "priority": "medium"},
                {"title": "タスク3", "reason": "理由3", "priority": "low"}
            ]
        }"""
        )
        service = SuggestionService(client=mock_client)

        result = await service.get_suggestions(sample_tasks, limit=2)

        assert len(result.suggestions) == 2

    async def test_parse_response_handles_invalid_priority(self, sample_tasks):
        """不正な優先度はmediumにフォールバック"""
        mock_client = self._create_mock_client(
            '{"suggestions": [{"title": "タスク1", "reason": "理由1", "priority": "invalid"}]}'
        )
        service = SuggestionService(client=mock_client)

        result = await service.get_suggestions(sample_tasks, limit=3)

        assert result.suggestions[0].priority == TaskPriority.MEDIUM


# --------------------------------------------------------------------------
# API エンドポイントテスト
# --------------------------------------------------------------------------
class TestSuggestionsAPI:
    @pytest.fixture
    def mock_service(self):
        """モックサービスを作成"""
        service = MagicMock(spec=SuggestionService)
        service.get_suggestions = AsyncMock(
            return_value=MagicMock(
                suggestions=[
                    TaskSuggestion(title="Suggestion", reason="Test", priority=TaskPriority.HIGH)
                ],
                cached=False,
            )
        )
        return service

    async def test_get_suggestions_endpoint(self, mock_service):
        """GET /api/tasks/suggestions が動作する"""
        from src.ai.suggestions import get_suggestion_service

        reset_repository()
        repo = InMemoryTaskRepository()
        set_repository(repo)
        app.dependency_overrides[get_suggestion_service] = lambda: mock_service

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/tasks/suggestions")

        app.dependency_overrides.clear()
        reset_repository()

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["title"] == "Suggestion"

    async def test_get_suggestions_with_custom_limit(self, mock_service):
        """limit パラメータが機能する"""
        from src.ai.suggestions import get_suggestion_service

        reset_repository()
        repo = InMemoryTaskRepository()
        set_repository(repo)
        app.dependency_overrides[get_suggestion_service] = lambda: mock_service

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            await ac.get("/api/tasks/suggestions", params={"limit": 5})

        app.dependency_overrides.clear()
        reset_repository()

        mock_service.get_suggestions.assert_called_once()
        call_args = mock_service.get_suggestions.call_args
        # 位置引数またはキーワード引数で limit=5 が渡されることを確認
        assert call_args[0][1] == 5 or call_args.kwargs.get("limit") == 5

    async def test_get_suggestions_limit_validation_min(self, client: AsyncClient):
        """limit の最小値バリデーション"""
        response = await client.get("/api/tasks/suggestions", params={"limit": 0})
        assert response.status_code == 422

    async def test_get_suggestions_limit_validation_max(self, client: AsyncClient):
        """limit の最大値バリデーション"""
        response = await client.get("/api/tasks/suggestions", params={"limit": 11})
        assert response.status_code == 422

    async def test_clear_cache_endpoint(self, mock_service):
        """DELETE /api/tasks/suggestions/cache が動作する"""
        from src.ai.suggestions import get_suggestion_service

        reset_repository()
        repo = InMemoryTaskRepository()
        set_repository(repo)
        app.dependency_overrides[get_suggestion_service] = lambda: mock_service

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.delete("/api/tasks/suggestions/cache")

        app.dependency_overrides.clear()
        reset_repository()

        assert response.status_code == 204
        mock_service.clear_cache.assert_called_once()
