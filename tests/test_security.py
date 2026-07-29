import pytest
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_endpoint_missing_api_key_returns_401(client):
    """Verify requests missing X-API-Key header return 401 Unauthorized."""
    res = await client.post(
        "/extract/text",
        json={"text": "Exploring Paris and Eiffel Tower."}
    )
    assert res.status_code == 401
    assert "Invalid or missing API key" in res.json()["detail"]


@pytest.mark.asyncio
async def test_endpoint_invalid_api_key_returns_401(client):
    """Verify requests with invalid X-API-Key header return 401 Unauthorized."""
    headers = {"X-API-Key": "wrong_invalid_key_123"}
    res = await client.post(
        "/extract/text",
        headers=headers,
        json={"text": "Exploring Paris and Eiffel Tower."}
    )
    assert res.status_code == 401
    assert "Invalid or missing API key" in res.json()["detail"]


@pytest.mark.asyncio
async def test_endpoint_valid_api_key_returns_200(client):
    """Verify requests with valid X-API-Key header return 200 OK."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    res = await client.post(
        "/extract/text",
        headers=headers,
        json={"text": "Exploring Shibuya crossing in Tokyo."}
    )
    assert res.status_code == 200
    assert res.json()["destination"] == "Tokyo"


@pytest.mark.asyncio
async def test_health_check_accessible_without_api_key(client):
    """Verify GET /health remains publicly accessible for container health checks."""
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
