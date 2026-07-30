import pytest

from app.core.config import get_settings
from app.schemas.multisource import UniversalExtractionRequest
from app.services.multisource_service import MultiSourceEngine


@pytest.mark.asyncio
async def test_multisource_build_travel_content_text():
    """Test MultiSourceEngine building TravelContent from raw text."""
    req = UniversalExtractionRequest(
        source_type="text",
        content="Exploring Shibuya Crossing in Tokyo",
        context="Japan Trip"
    )
    content = await MultiSourceEngine.build_travel_content(req)
    assert content.source_type == "text"
    assert content.caption == "Exploring Shibuya Crossing in Tokyo"
    assert content.metadata.get("context") == "Japan Trip"


@pytest.mark.asyncio
async def test_extract_universal_endpoint(client):
    """Test POST /extract/universal endpoint."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {
        "source_type": "text",
        "content": "Visiting Fushimi Inari Shrine in Kyoto Japan.",
        "context": "Kyoto Trip"
    }

    res = await client.post("/extract/universal", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["destination"] == "Kyoto"
    assert len(data["places"]) >= 1


@pytest.mark.asyncio
async def test_extract_universal_endpoint_url(client):
    """Test POST /extract/universal endpoint with image URL."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {
        "source_type": "image_url",
        "content": "https://example.com/kyoto_photo.jpg",
        "context": "Shared Reel"
    }

    res = await client.post("/extract/universal", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "destination" in data
