import pytest

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Tests GET / returns expected raw string."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == "Travel AI Extractor Running"


@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    """Tests GET /health returns expected JSON metadata."""
    settings = get_settings()
    response = await client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "Travel AI Extractor"
    assert "environment" in data
