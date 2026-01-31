import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.services.firestore import InMemoryTaskRepository, reset_repository, set_repository


@pytest.fixture
async def client():
    # テスト用にインメモリリポジトリを設定
    reset_repository()
    repo = InMemoryTaskRepository()
    set_repository(repo)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    reset_repository()


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


# 個別タスク取得 正常系テスト
class TestGetTaskSuccess:
    async def test_get_task(self, client: AsyncClient):
        """タスクを個別取得"""
        create_response = await client.post("/api/tasks", json={"title": "テストタスク"})
        task_id = create_response.json()["id"]

        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "テストタスク"

    async def test_get_task_with_all_fields(self, client: AsyncClient):
        """全フィールド指定のタスクを個別取得"""
        create_response = await client.post(
            "/api/tasks",
            json={
                "title": "詳細タスク",
                "description": "説明文",
                "status": "in_progress",
                "priority": "high",
            },
        )
        task_id = create_response.json()["id"]

        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "詳細タスク"
        assert data["description"] == "説明文"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"


# 個別タスク取得 異常系テスト
class TestGetTaskError:
    async def test_get_task_not_found(self, client: AsyncClient):
        """存在しないタスクで404"""
        response = await client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert response.json()["detail"] == "タスクが見つかりません"

    async def test_get_task_invalid_id(self, client: AsyncClient):
        """不正なIDで422"""
        response = await client.get("/api/tasks/invalid-id")
        assert response.status_code == 422


# タスク更新 正常系テスト
class TestUpdateTaskSuccess:
    async def test_update_task_title(self, client: AsyncClient):
        """タイトルのみ更新"""
        create_response = await client.post("/api/tasks", json={"title": "元のタイトル"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"title": "新しいタイトル"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新しいタイトル"
        assert data["id"] == task_id

    async def test_update_task_description(self, client: AsyncClient):
        """説明のみ更新"""
        create_response = await client.post(
            "/api/tasks", json={"title": "タスク", "description": "元の説明"}
        )
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"description": "新しい説明"})
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "新しい説明"
        assert data["title"] == "タスク"

    async def test_update_task_status(self, client: AsyncClient):
        """ステータス更新"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    async def test_update_task_priority(self, client: AsyncClient):
        """優先度更新"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"priority": "high"})
        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    async def test_update_task_multiple_fields(self, client: AsyncClient):
        """複数フィールド同時更新"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"title": "更新後", "status": "in_progress", "priority": "low"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新後"
        assert data["status"] == "in_progress"
        assert data["priority"] == "low"

    async def test_update_task_empty_body(self, client: AsyncClient):
        """空のボディで更新（変更なし）"""
        create_response = await client.post(
            "/api/tasks", json={"title": "タスク", "description": "説明"}
        )
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "タスク"
        assert data["description"] == "説明"

    async def test_update_task_preserves_created_at(self, client: AsyncClient):
        """更新時にcreated_atは変わらない"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        created_at = create_response.json()["created_at"]
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"title": "更新後"})
        assert response.json()["created_at"] == created_at


# タスク更新 異常系テスト
class TestUpdateTaskError:
    async def test_update_task_not_found(self, client: AsyncClient):
        """存在しないタスクで404"""
        response = await client.put(
            "/api/tasks/00000000-0000-0000-0000-000000000000", json={"title": "更新"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "タスクが見つかりません"

    async def test_update_task_invalid_id(self, client: AsyncClient):
        """不正なIDで422"""
        response = await client.put("/api/tasks/invalid-id", json={"title": "更新"})
        assert response.status_code == 422

    async def test_update_task_empty_title(self, client: AsyncClient):
        """空のタイトルでエラー"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"title": ""})
        assert response.status_code == 422

    async def test_update_task_too_long_title(self, client: AsyncClient):
        """長すぎるタイトルでエラー"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"title": "a" * 201})
        assert response.status_code == 422

    async def test_update_task_too_long_description(self, client: AsyncClient):
        """長すぎる説明でエラー"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"description": "a" * 1001})
        assert response.status_code == 422

    async def test_update_task_invalid_status(self, client: AsyncClient):
        """不正なステータスでエラー"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"status": "invalid"})
        assert response.status_code == 422

    async def test_update_task_invalid_priority(self, client: AsyncClient):
        """不正な優先度でエラー"""
        create_response = await client.post("/api/tasks", json={"title": "タスク"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/api/tasks/{task_id}", json={"priority": "invalid"})
        assert response.status_code == 422


# タスク削除 正常系テスト
class TestDeleteTaskSuccess:
    async def test_delete_task(self, client: AsyncClient):
        """タスクを削除"""
        create_response = await client.post("/api/tasks", json={"title": "削除対象"})
        task_id = create_response.json()["id"]

        response = await client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

        # 削除後は取得できない
        get_response = await client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404

    async def test_delete_task_from_multiple(self, client: AsyncClient):
        """複数タスクから一つを削除"""
        await client.post("/api/tasks", json={"title": "タスク1"})
        create_response = await client.post("/api/tasks", json={"title": "タスク2"})
        await client.post("/api/tasks", json={"title": "タスク3"})
        task_id = create_response.json()["id"]

        await client.delete(f"/api/tasks/{task_id}")

        # 一覧から削除されている
        list_response = await client.get("/api/tasks")
        titles = [item["title"] for item in list_response.json()["items"]]
        assert "タスク2" not in titles
        assert "タスク1" in titles
        assert "タスク3" in titles
        assert list_response.json()["total"] == 2


# タスク削除 異常系テスト
class TestDeleteTaskError:
    async def test_delete_task_not_found(self, client: AsyncClient):
        """存在しないタスクで404"""
        response = await client.delete("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert response.json()["detail"] == "タスクが見つかりません"

    async def test_delete_task_invalid_id(self, client: AsyncClient):
        """不正なIDで422"""
        response = await client.delete("/api/tasks/invalid-id")
        assert response.status_code == 422

    async def test_delete_task_twice(self, client: AsyncClient):
        """同じタスクを2回削除で404"""
        create_response = await client.post("/api/tasks", json={"title": "削除対象"})
        task_id = create_response.json()["id"]

        response1 = await client.delete(f"/api/tasks/{task_id}")
        assert response1.status_code == 204

        response2 = await client.delete(f"/api/tasks/{task_id}")
        assert response2.status_code == 404
