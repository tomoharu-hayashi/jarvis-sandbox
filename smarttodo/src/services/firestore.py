"""Firestore サービス: タスクの永続化を担当"""

import os
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

import firebase_admin
from firebase_admin import credentials, firestore


class TaskRepository(Protocol):
    """タスクリポジトリのインターフェース"""

    async def create(self, task_data: dict) -> dict: ...
    async def get(self, task_id: UUID) -> dict | None: ...
    async def list(
        self,
        limit: int,
        offset: int,
        status: str | None,
        priority: str | None,
    ) -> tuple[list[dict], int]: ...
    async def update(self, task_id: UUID, update_data: dict) -> dict | None: ...
    async def delete(self, task_id: UUID) -> bool: ...
    async def clear(self) -> None: ...


def _get_firestore_client() -> firestore.firestore.Client:
    """Firestoreクライアントを取得（シングルトン）"""
    if not firebase_admin._apps:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # デフォルト認証情報を使用（Cloud Runなど）
            firebase_admin.initialize_app()
    return firestore.client()


class FirestoreTaskRepository:
    """FirestoreによるタスクリポジトリImpl"""

    COLLECTION = "tasks"

    def __init__(self) -> None:
        self._db = _get_firestore_client()

    def _to_firestore(self, task_data: dict) -> dict:
        """Pydanticモデル形式からFirestore形式に変換"""
        data = task_data.copy()
        # UUIDを文字列に変換
        if "id" in data and isinstance(data["id"], UUID):
            data["id"] = str(data["id"])
        # datetimeは維持（Firestoreが対応）
        return data

    def _from_firestore(self, doc_data: dict) -> dict:
        """Firestore形式からPydanticモデル形式に変換"""
        data = doc_data.copy()
        # 文字列をUUIDに変換
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])
        return data

    async def create(self, task_data: dict) -> dict:
        """タスクを作成"""
        task_id = uuid4()
        now = datetime.now()
        doc_data = {
            "id": str(task_id),
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "due_date": task_data.get("due_date"),
            "status": task_data.get("status", "pending"),
            "priority": task_data.get("priority", "medium"),
            "created_at": now,
        }
        self._db.collection(self.COLLECTION).document(str(task_id)).set(doc_data)
        return self._from_firestore(doc_data)

    async def get(self, task_id: UUID) -> dict | None:
        """タスクを取得"""
        doc = self._db.collection(self.COLLECTION).document(str(task_id)).get()
        if not doc.exists:
            return None
        return self._from_firestore(doc.to_dict())

    async def list(
        self,
        limit: int,
        offset: int,
        status: str | None,
        priority: str | None,
    ) -> tuple[list[dict], int]:
        """タスク一覧を取得"""
        # クエリ構築
        query = self._db.collection(self.COLLECTION)
        if status is not None:
            query = query.where("status", "==", status)
        if priority is not None:
            query = query.where("priority", "==", priority)

        # 全件取得してtotalを計算（Firestoreにcount集約がないため）
        all_docs = list(query.stream())
        total = len(all_docs)

        # offsetとlimitを適用
        items = []
        for doc in all_docs[offset : offset + limit]:
            items.append(self._from_firestore(doc.to_dict()))

        return items, total

    async def update(self, task_id: UUID, update_data: dict) -> dict | None:
        """タスクを更新"""
        doc_ref = self._db.collection(self.COLLECTION).document(str(task_id))
        doc = doc_ref.get()
        if not doc.exists:
            return None

        # 更新データを適用
        firestore_update = {}
        for key, value in update_data.items():
            if isinstance(value, str) and hasattr(value, "value"):
                # Enumの場合は値を取得
                firestore_update[key] = value
            else:
                firestore_update[key] = value

        doc_ref.update(firestore_update)

        # 更新後のデータを取得
        updated_doc = doc_ref.get()
        return self._from_firestore(updated_doc.to_dict())

    async def delete(self, task_id: UUID) -> bool:
        """タスクを削除"""
        doc_ref = self._db.collection(self.COLLECTION).document(str(task_id))
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.delete()
        return True

    async def clear(self) -> None:
        """全タスクを削除（テスト用）"""
        docs = self._db.collection(self.COLLECTION).stream()
        for doc in docs:
            doc.reference.delete()


class InMemoryTaskRepository:
    """インメモリによるタスクリポジトリImpl（テスト用）"""

    def __init__(self) -> None:
        self._tasks: list[dict] = []

    async def create(self, task_data: dict) -> dict:
        """タスクを作成"""
        task_id = uuid4()
        now = datetime.now()
        doc_data = {
            "id": task_id,
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "due_date": task_data.get("due_date"),
            "status": task_data.get("status", "pending"),
            "priority": task_data.get("priority", "medium"),
            "created_at": now,
        }
        self._tasks.append(doc_data)
        return doc_data

    async def get(self, task_id: UUID) -> dict | None:
        """タスクを取得"""
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    async def list(
        self,
        limit: int,
        offset: int,
        status: str | None,
        priority: str | None,
    ) -> tuple[list[dict], int]:
        """タスク一覧を取得"""
        filtered = self._tasks
        if status is not None:
            filtered = [t for t in filtered if t["status"] == status]
        if priority is not None:
            filtered = [t for t in filtered if t["priority"] == priority]

        total = len(filtered)
        items = filtered[offset : offset + limit]
        return items, total

    async def update(self, task_id: UUID, update_data: dict) -> dict | None:
        """タスクを更新"""
        for i, task in enumerate(self._tasks):
            if task["id"] == task_id:
                self._tasks[i] = {**task, **update_data}
                return self._tasks[i]
        return None

    async def delete(self, task_id: UUID) -> bool:
        """タスクを削除"""
        for i, task in enumerate(self._tasks):
            if task["id"] == task_id:
                self._tasks.pop(i)
                return True
        return False

    async def clear(self) -> None:
        """全タスクを削除"""
        self._tasks.clear()


# デフォルトリポジトリ（環境に応じて切り替え）
_repository: TaskRepository | None = None


def get_repository() -> TaskRepository:
    """タスクリポジトリを取得"""
    global _repository
    if _repository is None:
        if os.environ.get("USE_FIRESTORE", "").lower() == "true":
            _repository = FirestoreTaskRepository()
        else:
            _repository = InMemoryTaskRepository()
    return _repository


def set_repository(repo: TaskRepository) -> None:
    """タスクリポジトリを設定（テスト用）"""
    global _repository
    _repository = repo


def reset_repository() -> None:
    """リポジトリをリセット（テスト用）"""
    global _repository
    _repository = None
