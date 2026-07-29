import pytest


@pytest.mark.asyncio
async def test_extract_text_success(client):
    """Tests successful text extraction via POST /extract/text."""
    payload = {
        "text": "Spent the weekend exploring cafes around Kyoto and visited Fushimi Inari Shrine."
    }

    response = await client.post("/extract/text", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert "destination" in data
    assert "places" in data
    assert "execution_time_seconds" in data
    assert isinstance(data["places"], list)

    if len(data["places"]) > 0:
        place = data["places"][0]
        assert "name" in place
        assert "confidence" in place
        assert "verified" in place


@pytest.mark.asyncio
async def test_extract_text_with_context(client):
    """Tests text extraction with optional location context hint."""
    payload = {
        "text": "Exploring Shibuya crossing and cafes.",
        "context": "Tokyo, Japan"
    }

    response = await client.post("/extract/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Tokyo"
    assert len(data["places"]) > 0
    assert data["places"][0]["name"] == "Shibuya Crossing"


@pytest.mark.asyncio
async def test_extract_text_validation_empty(client):
    """Tests that empty text payload returns HTTP 422 validation error."""
    payload = {
        "text": ""
    }

    response = await client.post("/extract/text", json=payload)
    assert response.status_code == 422
