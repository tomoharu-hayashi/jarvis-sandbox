import pytest
from httpx import ASGITransport, AsyncClient

from src.api.tasks import _tasks
from src.main import app


@pytest.fixture
async def client():
    _tasks.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# タスク作成 正常系テスト
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


# タスク一覧取得 正常系テスト
class TestListTasksSuccess:
    async def test_list_tasks_empty(self, client: AsyncClient):
        """空のタスク一覧を取得"""
        response = await client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0

    async def test_list_tasks_with_items(self, client: AsyncClient):
        """タスクがある場合の一覧取得"""
        await client.post("/api/tasks", json={"title": "タスク1"})
        await client.post("/api/tasks", json={"title": "タスク2"})

        response = await client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    async def test_list_tasks_with_pagination(self, client: AsyncClient):
        """ページネーションが動作する"""
        for i in range(5):
            await client.post("/api/tasks", json={"title": f"タスク{i}"})

        response = await client.get("/api/tasks", params={"limit": 2, "offset": 1})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 1
        assert data["items"][0]["title"] == "タスク1"
        assert data["items"][1]["title"] == "タスク2"

    async def test_list_tasks_filter_by_status(self, client: AsyncClient):
        """ステータスでフィルタリング"""
        await client.post("/api/tasks", json={"title": "タスク1", "status": "pending"})
        await client.post("/api/tasks", json={"title": "タスク2", "status": "completed"})
        await client.post("/api/tasks", json={"title": "タスク3", "status": "pending"})

        response = await client.get("/api/tasks", params={"status": "pending"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert all(item["status"] == "pending" for item in data["items"])

    async def test_list_tasks_filter_by_priority(self, client: AsyncClient):
        """優先度でフィルタリング"""
        await client.post("/api/tasks", json={"title": "タスク1", "priority": "high"})
        await client.post("/api/tasks", json={"title": "タスク2", "priority": "low"})
        await client.post("/api/tasks", json={"title": "タスク3", "priority": "high"})

        response = await client.get("/api/tasks", params={"priority": "high"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert all(item["priority"] == "high" for item in data["items"])

    async def test_list_tasks_filter_by_status_and_priority(self, client: AsyncClient):
        """ステータスと優先度の複合フィルタリング"""
        await client.post(
            "/api/tasks", json={"title": "タスク1", "status": "pending", "priority": "high"}
        )
        await client.post(
            "/api/tasks", json={"title": "タスク2", "status": "completed", "priority": "high"}
        )
        await client.post(
            "/api/tasks", json={"title": "タスク3", "status": "pending", "priority": "low"}
        )

        response = await client.get("/api/tasks", params={"status": "pending", "priority": "high"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["title"] == "タスク1"

    async def test_list_tasks_offset_beyond_total(self, client: AsyncClient):
        """offsetがtotalを超える場合は空"""
        await client.post("/api/tasks", json={"title": "タスク1"})

        response = await client.get("/api/tasks", params={"offset": 100})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 1


# タスク一覧取得 異常系テスト
class TestListTasksValidation:
    async def test_list_tasks_invalid_limit_too_small(self, client: AsyncClient):
        """limit が最小値未満でエラー"""
        response = await client.get("/api/tasks", params={"limit": 0})
        assert response.status_code == 422

    async def test_list_tasks_invalid_limit_too_large(self, client: AsyncClient):
        """limit が最大値超過でエラー"""
        response = await client.get("/api/tasks", params={"limit": 101})
        assert response.status_code == 422

    async def test_list_tasks_invalid_offset_negative(self, client: AsyncClient):
        """offset が負数でエラー"""
        response = await client.get("/api/tasks", params={"offset": -1})
        assert response.status_code == 422

    async def test_list_tasks_invalid_status(self, client: AsyncClient):
        """不正なステータスでエラー"""
        response = await client.get("/api/tasks", params={"status": "invalid"})
        assert response.status_code == 422

    async def test_list_tasks_invalid_priority(self, client: AsyncClient):
        """不正な優先度でエラー"""
        response = await client.get("/api/tasks", params={"priority": "invalid"})
        assert response.status_code == 422
