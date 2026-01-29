"""SmartTodo テスト"""
import pytest
from main import Task, Priority, Status, create_task, get_tasks, get_task


class TestTask:
    def test_create_task(self):
        task = create_task("テストタスク")
        assert task.title == "テストタスク"
        assert task.priority == Priority.MEDIUM
        assert task.status == Status.TODO

    def test_create_task_with_priority(self):
        task = create_task("重要なタスク", priority=Priority.HIGH)
        assert task.priority == Priority.HIGH

    def test_get_tasks(self):
        # Note: テスト間で状態が共有されるため、実際のテストではフィクスチャでリセットが必要
        tasks = get_tasks()
        assert isinstance(tasks, list)

    def test_get_task_by_id(self):
        task = create_task("ID検索テスト")
        found = get_task(task.id)
        assert found is not None
        assert found.title == "ID検索テスト"

    def test_get_task_not_found(self):
        result = get_task(99999)
        assert result is None
