"""Smoke-тест: проверка что тестовая инфраструктура работает."""

from httpx import AsyncClient


async def test_health_endpoint(client: AsyncClient):
    """GET /api/health должен вернуть {"status": "ok"}."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
