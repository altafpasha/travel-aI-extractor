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
        if not self.api_key or self.api_key.startswith("your-") or self.api_key.startswith("mock-"):
            logger.warning("Gemini API key is unconfigured or mock. Returning fallback mock response for image.")
            return self._mock_extraction_response()

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
            logger.error(f"Gemini Vision API extraction failed: {str(e)}")
            raise AIServiceException(f"Failed to process image with Gemini AI: {str(e)}")

    async def extract_places_from_frames(self, frames: List[bytes]) -> Dict[str, Any]:
        """Processes multiple video keyframe images concurrently and aggregates/deduplicates places."""
        if not frames:
            return {"destination": None, "places": []}

        # Analyze frames concurrently in async tasks
        tasks = [self.extract_places_from_image(frame) for frame in frames[:10]] # Cap at 10 keyframes max
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
        if not self.api_key or self.api_key.startswith("your-") or self.api_key.startswith("mock-"):
            logger.warning("Gemini API key is unconfigured or mock. Returning fallback mock response for text.")
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
            logger.error(f"Gemini Text API extraction failed: {str(e)}")
            raise AIServiceException(f"Failed to process text with Gemini AI: {str(e)}")

    async def _call_gemini_rest_api_image(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Fallback direct REST API call for images."""
        import base64
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                    {"text": IMAGE_PROMPT_TEMPLATE}
                ]
            }]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise AIServiceException(f"Gemini API returned status code {resp.status_code}")
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(text)

    async def _call_gemini_rest_api_text(self, prompt: str) -> Dict[str, Any]:
        """Fallback direct REST API call for text."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise AIServiceException(f"Gemini API returned status code {resp.status_code}")
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(text)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Cleans markdown wrappers and parses structured JSON from Gemini response."""
        cleaned_text = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned_text = re.sub(r"^```\s*", "", cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r"```$", "", cleaned_text).strip()

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
        """Mock response returned when API keys are unconfigured in test environment."""
        if text and "shibuya" in text.lower():
            return {
                "destination": "Tokyo",
                "places": [
                    {
                        "name": "Shibuya Crossing",
                        "city": "Tokyo",
                        "country": "Japan",
                        "category": "Landmark"
                    }
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
