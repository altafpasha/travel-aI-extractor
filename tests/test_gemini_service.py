import pytest

from app.core.exceptions import AIServiceException
from app.services.gemini_service import GeminiService


@pytest.mark.asyncio
async def test_parse_json_response_valid():
    """Tests cleaning and parsing valid JSON text from Gemini."""
    service = GeminiService()
    raw_response = """
    ```json
    {
      "destination": "Kyoto",
      "places": [
        {
          "name": "Fushimi Inari Shrine",
          "city": "Kyoto",
          "country": "Japan",
          "category": "Landmark"
        }
      ]
    }
    ```
    """
    result = service._parse_json_response(raw_response)
    assert result["destination"] == "Kyoto"
    assert len(result["places"]) == 1
    assert result["places"][0]["name"] == "Fushimi Inari Shrine"


@pytest.mark.asyncio
async def test_parse_json_response_invalid_throws_exception():
    """Tests that unparseable text throws AIServiceException."""
    service = GeminiService()
    invalid_response = "Sorry, I could not extract places."
    with pytest.raises(AIServiceException):
        service._parse_json_response(invalid_response)


@pytest.mark.asyncio
async def test_mock_fallback_extraction():
    """Tests mock response when Gemini API key is not configured."""
    service = GeminiService(api_key="your-gemini-api-key-here")
    result = await service.extract_places_from_image(b"fake_image_data")
    assert result["destination"] == "Kyoto"
    assert len(result["places"]) == 1
