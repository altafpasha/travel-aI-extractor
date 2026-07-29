import pytest
from app.schemas.multisource import UniversalExtractionRequest
from app.services.multisource_service import MultiSourceEngine


@pytest.mark.asyncio
async def test_multisource_build_travel_content_text():
    """Tests building normalized TravelContent from text source."""
    req = UniversalExtractionRequest(
        source_type="text",
        content="Exploring Shibuya in Tokyo",
        context="Japan"
    )
    content = await MultiSourceEngine.build_travel_content(req)

    assert content.source_type == "text"
    assert content.caption == "Exploring Shibuya in Tokyo"
    assert content.metadata.get("context_hint") == "Japan"


@pytest.mark.asyncio
async def test_extract_universal_endpoint(client):
    """Tests POST /extract/universal endpoint with text content."""
    payload = {
        "source_type": "text",
        "content": "Exploring Shibuya crossing in Tokyo Japan.",
        "context": "Tokyo trip"
    }

    response = await client.post("/extract/universal", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert "destination" in data
    assert "places" in data
    assert isinstance(data["places"], list)
    if len(data["places"]) > 0:
        assert data["places"][0]["name"] == "Shibuya Crossing"


@pytest.mark.asyncio
async def test_extract_universal_endpoint_url(client):
    """Tests POST /extract/universal endpoint with media URL."""
    payload = {
        "source_type": "image_url",
        "content": "https://example.com/kyoto_photo.jpg",
        "context": "Kyoto, Japan"
    }

    response = await client.post("/extract/universal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "destination" in data
    assert "places" in data
