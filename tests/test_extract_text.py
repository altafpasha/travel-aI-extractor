import pytest

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_extract_text_success(client):
    """Test successful text extraction endpoint."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {"text": "Exploring Shibuya crossing in Tokyo Japan."}

    res = await client.post(f"{settings.API_V1_STR}/extract/text", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["destination"] == "Tokyo"
    assert len(data["places"]) >= 1
    assert data["places"][0]["name"] == "Shibuya Crossing"


@pytest.mark.asyncio
async def test_extract_text_with_context(client):
    """Test text extraction endpoint with optional context location hint."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {"text": "Visiting Fushimi Inari Shrine", "context": "Kyoto, Japan Trip"}

    res = await client.post(f"{settings.API_V1_STR}/extract/text", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["destination"] == "Kyoto"


@pytest.mark.asyncio
async def test_extract_text_validation_empty(client):
    """Test text extraction validation rejecting empty text."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {"text": "   "}

    res = await client.post(f"{settings.API_V1_STR}/extract/text", json=payload, headers=headers)
    assert res.status_code == 422
