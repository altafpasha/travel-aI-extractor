import pytest


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Tests GET / returns expected raw string."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == "Travel AI Extractor Running"


@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    """Tests GET /health returns expected JSON metadata."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "Travel AI Extractor"
    assert "environment" in data
