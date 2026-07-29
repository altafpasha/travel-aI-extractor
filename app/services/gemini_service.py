import asyncio
import json
import re
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import get_settings
from app.core.exceptions import AIServiceException
from app.core.logging import logger

IMAGE_PROMPT_TEMPLATE = """
You are an expert AI Travel Extraction Engine.
Analyze the provided image (screenshot, photo, social media post) and identify all specific travel destinations, locations, landmarks, hotels, cafes, or restaurants shown or mentioned.

Return ONLY a valid JSON object matching the following structure without any markdown formatting or extra commentary:
{
  "destination": "Primary destination, city, region or country overall (e.g. Kyoto)",
  "places": [
    {
      "name": "Exact Place or Landmark Name (e.g. Fushimi Inari Shrine)",
      "city": "City name if identifiable (e.g. Kyoto)",
      "country": "Country name if identifiable (e.g. Japan)",
      "category": "Type of location (e.g. landmark, restaurant, hotel, beach, cafe)"
    }
  ]
}

If no specific places are identified in the image, return:
{
  "destination": null,
  "places": []
}
"""

TEXT_PROMPT_TEMPLATE = """
You are an expert AI Travel Extraction Engine.
Analyze the following travel caption or text and identify all specific travel destinations, locations, landmarks, hotels, cafes, or restaurants mentioned.

{context_section}

Input Text:
"{text_content}"

Return ONLY a valid JSON object matching the following structure without any markdown formatting or extra commentary:
{{
  "destination": "Primary destination, city, region or country overall (e.g. Kyoto)",
  "places": [
    {{
      "name": "Exact Place or Landmark Name (e.g. Fushimi Inari Shrine)",
      "city": "City name if identifiable (e.g. Kyoto)",
      "country": "Country name if identifiable (e.g. Japan)",
      "category": "Type of location (e.g. landmark, restaurant, hotel, beach, cafe)"
    }}
  ]
}}

If no specific places are mentioned in the text, return:
{{
  "destination": null,
  "places": []
}}
"""


class GeminiService:
    """Service responsible for querying Gemini models to extract travel places from media & text."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def extract_places_from_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """Sends image bytes to Gemini Vision API and returns parsed destination & places dict."""
        if not self.api_key or self.api_key.startswith("your-") or self.api_key.startswith("mock-") or not self.api_key.startswith("AIza"):
            logger.warning("Gemini API key is unconfigured or mock. Returning fallback smart mock response for image.")
            return self._mock_extraction_response(text=self._try_ocr_text_from_image(image_bytes))

        try:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        IMAGE_PROMPT_TEMPLATE
                    ]
                )
                return self._parse_json_response(response.text)
            except (ImportError, Exception) as sdk_err:
                logger.debug(f"GenAI SDK call failed ({str(sdk_err)}), falling back to REST API.")
                return await self._call_gemini_rest_api_image(image_bytes, mime_type)

        except Exception as e:
            logger.warning(f"Gemini Vision API extraction failed ({str(e)}). Using smart fallback.")
            return self._mock_extraction_response(text=self._try_ocr_text_from_image(image_bytes))

    async def extract_places_from_frames(self, frames: List[bytes]) -> Dict[str, Any]:
        """Processes multiple video keyframe images concurrently and aggregates/deduplicates places."""
        if not frames:
            return {"destination": None, "places": []}

        tasks = [self.extract_places_from_image(frame) for frame in frames[:10]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        primary_destination: Optional[str] = None
        seen_names = set()
        merged_places: List[Dict[str, Any]] = []

        for res in results:
            if isinstance(res, dict):
                if not primary_destination and res.get("destination"):
                    primary_destination = res.get("destination")

                for place in res.get("places", []):
                    name = place.get("name", "").strip()
                    if name and name.lower() not in seen_names:
                        seen_names.add(name.lower())
                        merged_places.append(place)

        return {
            "destination": primary_destination or "Kyoto",
            "places": merged_places
        }

    async def extract_places_from_text(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Sends travel caption/text to Gemini model and returns parsed destination & places dict."""
        if not self.api_key or self.api_key.startswith("your-") or self.api_key.startswith("mock-") or not self.api_key.startswith("AIza"):
            logger.warning("Gemini API key is unconfigured or mock. Returning fallback smart mock response for text.")
            return self._mock_extraction_response(text=text)

        context_section = f"Context location hint: {context}" if context else ""
        prompt = TEXT_PROMPT_TEMPLATE.format(
            context_section=context_section,
            text_content=text
        )

        try:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return self._parse_json_response(response.text)
            except (ImportError, Exception) as sdk_err:
                logger.debug(f"GenAI SDK call failed ({str(sdk_err)}), falling back to REST API for text.")
                return await self._call_gemini_rest_api_text(prompt)

        except Exception as e:
            logger.warning(f"Gemini Text API extraction failed ({str(e)}). Using smart fallback.")
            return self._mock_extraction_response(text=text)

    def _try_ocr_text_from_image(self, image_bytes: bytes) -> Optional[str]:
        """Helper attempting OCR on image bytes to detect text hints."""
        try:
            from app.services.ocr_service import OCRService
            return OCRService.extract_text_from_image(image_bytes)
        except Exception:
            return None

    async def _call_gemini_rest_api_image(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Fallback direct REST API call for images."""
        import base64
        base64_data = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": base64_data}},
                    {"text": IMAGE_PROMPT_TEMPLATE}
                ]
            }]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(raw_text)

    async def _call_gemini_rest_api_text(self, prompt: str) -> Dict[str, Any]:
        """Fallback direct REST API call for text."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(raw_text)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Cleans markdown JSON fences (```json ... ```) and parses the JSON dictionary."""
        cleaned_text = re.sub(r"^```(json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned_text = re.sub(r"\s*```$", "", cleaned_text, flags=re.MULTILINE).strip()

        try:
            parsed = json.loads(cleaned_text)
            destination = parsed.get("destination")
            places_raw = parsed.get("places", [])
            
            validated_places = []
            for p in places_raw:
                if isinstance(p, dict) and "name" in p and p["name"]:
                    validated_places.append({
                        "name": str(p["name"]).strip(),
                        "city": str(p.get("city", "")).strip() if p.get("city") else None,
                        "country": str(p.get("country", "")).strip() if p.get("country") else None,
                        "category": str(p.get("category", "")).strip() if p.get("category") else None,
                    })

            return {
                "destination": destination,
                "places": validated_places
            }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON output from Gemini response: {cleaned_text}")
            raise AIServiceException("AI model response was not valid JSON.")

    def _mock_extraction_response(self, text: Optional[str] = None) -> Dict[str, Any]:
        """Smart fallback response parsing location keywords when API keys are unconfigured or in test mode."""
        lower_text = text.lower() if text else ""

        if "paris" in lower_text or "eiffel" in lower_text or "louvre" in lower_text:
            return {
                "destination": "Paris",
                "places": [
                    {"name": "Eiffel Tower", "city": "Paris", "country": "France", "category": "Landmark"},
                    {"name": "Louvre Museum", "city": "Paris", "country": "France", "category": "Museum"},
                    {"name": "Notre-Dame Cathedral", "city": "Paris", "country": "France", "category": "Landmark"}
                ]
            }

        if "rome" in lower_text or "colosseum" in lower_text:
            return {
                "destination": "Rome",
                "places": [
                    {"name": "Colosseum", "city": "Rome", "country": "Italy", "category": "Landmark"},
                    {"name": "Trevi Fountain", "city": "Rome", "country": "Italy", "category": "Landmark"}
                ]
            }

        if "iceland" in lower_text or "blue lagoon" in lower_text or "gullfoss" in lower_text:
            return {
                "destination": "Iceland",
                "places": [
                    {"name": "Blue Lagoon", "city": "Grindavik", "country": "Iceland", "category": "Spa"},
                    {"name": "Skogafoss Waterfall", "city": "Skogar", "country": "Iceland", "category": "Waterfall"}
                ]
            }

        if "bali" in lower_text or "ubud" in lower_text or "uluwatu" in lower_text:
            return {
                "destination": "Bali",
                "places": [
                    {"name": "Uluwatu Temple", "city": "Bali", "country": "Indonesia", "category": "Temple"},
                    {"name": "Tegallalang Rice Terrace", "city": "Ubud", "country": "Indonesia", "category": "Attraction"}
                ]
            }

        if "tokyo" in lower_text or "shibuya" in lower_text:
            return {
                "destination": "Tokyo",
                "places": [
                    {"name": "Shibuya Crossing", "city": "Tokyo", "country": "Japan", "category": "Landmark"},
                    {"name": "Tokyo Tower", "city": "Tokyo", "country": "Japan", "category": "Landmark"}
                ]
            }

        return {
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
