"""ヘルスチェックエンドポイントのテスト"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestHealthCheck:
    async def test_health_endpoint_returns_200(self, client: AsyncClient):
        """ヘルスチェックエンドポイントが200を返す"""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_endpoint_returns_status(self, client: AsyncClient):
        """ヘルスチェックエンドポイントがステータスを返す"""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
