import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# 正常系テスト
class TestCreateTaskSuccess:
    async def test_create_task_with_all_fields(self, client: AsyncClient):
        """全フィールドを指定してタスク作成"""
        due_date = "2025-12-31T23:59:59Z"
        response = await client.post(
            "/api/tasks",
            json={
                "title": "テストタスク",
                "description": "これはテスト用のタスクです",
                "due_date": due_date,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "テストタスク"
        assert data["description"] == "これはテスト用のタスクです"
        assert "id" in data
        assert "created_at" in data

    async def test_create_task_with_required_fields_only(self, client: AsyncClient):
        """必須フィールドのみでタスク作成"""
        response = await client.post("/api/tasks", json={"title": "最小限のタスク"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "最小限のタスク"
        assert data["description"] == ""
        assert data["due_date"] is None

    async def test_create_task_with_empty_description(self, client: AsyncClient):
        """空の説明でタスク作成"""
        response = await client.post("/api/tasks", json={"title": "タスク", "description": ""})
        assert response.status_code == 201
        assert response.json()["description"] == ""


# 異常系テスト
class TestCreateTaskValidation:
    async def test_create_task_without_title(self, client: AsyncClient):
        """タイトルなしでエラー"""
        response = await client.post("/api/tasks", json={"description": "説明のみ"})
        assert response.status_code == 422

    async def test_create_task_with_empty_title(self, client: AsyncClient):
        """空のタイトルでエラー"""
        response = await client.post("/api/tasks", json={"title": ""})
        assert response.status_code == 422

    async def test_create_task_with_too_long_title(self, client: AsyncClient):
        """長すぎるタイトルでエラー"""
        response = await client.post("/api/tasks", json={"title": "a" * 201})
        assert response.status_code == 422

    async def test_create_task_with_too_long_description(self, client: AsyncClient):
        """長すぎる説明でエラー"""
        response = await client.post(
            "/api/tasks", json={"title": "タスク", "description": "a" * 1001}
        )
        assert response.status_code == 422

    async def test_create_task_with_invalid_due_date(self, client: AsyncClient):
        """不正な日付形式でエラー"""
        response = await client.post(
            "/api/tasks", json={"title": "タスク", "due_date": "invalid-date"}
        )
        assert response.status_code == 422

    async def test_create_task_with_invalid_body(self, client: AsyncClient):
        """不正なリクエストボディでエラー"""
        response = await client.post("/api/tasks", content="not json")
        assert response.status_code == 422
