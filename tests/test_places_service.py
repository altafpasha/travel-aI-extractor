import pytest

from app.services.places_service import GooglePlacesService


@pytest.mark.asyncio
async def test_mock_verify_place():
    """Tests place verification and enrichment fallback."""
    service = GooglePlacesService(api_key="mock-places-key")
    place_input = {
        "name": "Fushimi Inari Shrine",
        "city": "Kyoto",
        "country": "Japan"
    }
    result = await service.verify_and_enrich_place(place_input)
    assert result.name == "Fushimi Inari Shrine"
    assert result.city == "Kyoto"
    assert result.country == "Japan"
    assert result.confidence >= 90
    assert result.verified is True
    assert result.latitude is not None
    assert result.longitude is not None


@pytest.mark.asyncio
async def test_fallback_unverified_place():
    """Tests fallback behavior when place cannot be verified."""
    service = GooglePlacesService(api_key="mock-places-key")
    result = service._fallback_unverified_place("Nonexistent Landmark XYZ", "Unknown", "Unknown")
    assert result.name == "Nonexistent Landmark XYZ"
    assert result.verified is False
    assert result.confidence <= 75
