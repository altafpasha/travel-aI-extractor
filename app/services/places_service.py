from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.schemas.extraction import PlaceLocation
from app.services.confidence_service import ConfidenceService


class GooglePlacesService:
    """Service for validating place existence and enriching location data via Google Places API."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GOOGLE_PLACES_API_KEY
        self.find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    async def verify_and_enrich_place(
        self, place_data: Dict[str, Any], text_context: Optional[str] = None
    ) -> PlaceLocation:
        """
        Verifies place against Google Places API and returns an enriched PlaceLocation with confidence score.
        """
        name = place_data.get("name", "")
        city = place_data.get("city")
        country = place_data.get("country")

        if not name:
            return PlaceLocation(name="Unknown Place", confidence=0, verified=False)

        if (
            not self.api_key
            or "your_" in self.api_key.lower()
            or "your-" in self.api_key.lower()
            or "mock" in self.api_key.lower()
            or "replace_" in self.api_key.lower()
        ):
            logger.info(f"Google Places API key is mock/unconfigured. Returning mock verified result for '{name}'.")
            return self._mock_verify_place(name, city, country, text_context=text_context)

        query = f"{name}"
        if city:
            query += f", {city}"
        if country:
            query += f", {country}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "input": query,
                    "inputtype": "textquery",
                    "fields": "place_id,name,formatted_address,geometry,rating,user_ratings_total,photos",
                    "key": self.api_key,
                }
                resp = await client.get(self.find_place_url, params=params)

                if resp.status_code != 200:
                    logger.error(f"Google Places API error status {resp.status_code}: {resp.text}")
                    return self._fallback_unverified_place(name, city, country, text_context=text_context)

                data = resp.json()
                candidates = data.get("candidates", [])

                if not candidates:
                    logger.info(f"No Google Places candidates found for query '{query}'.")
                    return self._fallback_unverified_place(name, city, country, text_context=text_context)

                best = candidates[0]
                place_id = best.get("place_id")
                formatted_address = best.get("formatted_address")
                geometry = best.get("geometry", {}).get("location", {})
                lat = geometry.get("lat")
                lng = geometry.get("lng")

                extracted_city, extracted_country = self._extract_address_components(formatted_address, city, country)
                verified_name = best.get("name", name)
                final_city = extracted_city or city
                final_country = extracted_country or country

                # Multi-signal confidence calculation
                confidence = ConfidenceService.calculate_confidence(
                    raw_name=verified_name,
                    city=final_city,
                    country=final_country,
                    verified=True,
                    place_id=place_id,
                    address=formatted_address,
                    text_context=text_context,
                )

                return PlaceLocation(
                    name=verified_name,
                    city=final_city,
                    country=final_country,
                    confidence=confidence,
                    address=formatted_address,
                    latitude=lat,
                    longitude=lng,
                    place_id=place_id,
                    verified=True,
                )

        except Exception as e:
            logger.error(f"Exception while verifying place '{name}': {str(e)}")
            return self._fallback_unverified_place(name, city, country, text_context=text_context)

    def _extract_address_components(
        self, formatted_address: Optional[str], default_city: Optional[str], default_country: Optional[str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract city and country from formatted address string if available."""
        if not formatted_address:
            return default_city, default_country

        parts = [p.strip() for p in formatted_address.split(",")]
        country = default_country or (parts[-1] if parts else None)
        city = default_city or (parts[-2] if len(parts) >= 2 else None)
        return city, country

    def _fallback_unverified_place(
        self, name: str, city: Optional[str], country: Optional[str], text_context: Optional[str] = None
    ) -> PlaceLocation:
        """Returns place location marked as unverified with calculated confidence."""
        confidence = ConfidenceService.calculate_confidence(
            raw_name=name,
            city=city,
            country=country,
            verified=False,
            place_id=None,
            address=None,
            text_context=text_context,
        )

        return PlaceLocation(
            name=name,
            city=city,
            country=country,
            confidence=confidence,
            address=None,
            latitude=None,
            longitude=None,
            place_id=None,
            verified=False,
        )

    def _mock_verify_place(
        self, name: str, city: Optional[str], country: Optional[str], text_context: Optional[str] = None
    ) -> PlaceLocation:
        """Returns mock enriched place for testing/local development."""
        mock_places_db = {
            "fushimi inari shrine": {
                "name": "Fushimi Inari Shrine",
                "city": "Kyoto",
                "country": "Japan",
                "address": "68 Fukakusa Yabunouchicho, Fushimi Ward, Kyoto, 612-0882, Japan",
                "latitude": 34.9671,
                "longitude": 135.7727,
                "place_id": "ChIJ31-1ZkQGAWARf0N5e9rW028",
                "verified": True,
            }
        }

        lower_name = name.lower()
        if lower_name in mock_places_db:
            data = mock_places_db[lower_name]
            confidence = ConfidenceService.calculate_confidence(
                raw_name=data["name"],
                city=data["city"],
                country=data["country"],
                verified=True,
                place_id=data["place_id"],
                address=data["address"],
                text_context=text_context,
            )
            return PlaceLocation(confidence=confidence, **data)

        final_city = city
        final_country = country
        confidence = ConfidenceService.calculate_confidence(
            raw_name=name,
            city=final_city,
            country=final_country,
            verified=True,
            place_id=f"mock_place_{hash(name) % 1000000}",
            address=f"{name}, {final_city}, {final_country}",
            text_context=text_context,
        )

        return PlaceLocation(
            name=name,
            city=final_city,
            country=final_country,
            confidence=confidence,
            address=f"{name}, {final_city}, {final_country}",
            latitude=34.9671,
            longitude=135.7727,
            place_id=f"mock_place_{hash(name) % 1000000}",
            verified=True,
        )
