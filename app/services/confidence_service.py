import re
from typing import Optional

from app.core.logging import logger

GENERIC_LOCATION_TERMS = {
    "temple",
    "beach",
    "cafe",
    "restaurant",
    "hotel",
    "resort",
    "park",
    "waterfall",
    "bar",
    "club",
    "shop",
    "market",
    "museum",
    "church",
    "street",
    "island",
    "lake",
    "mountain",
    "bridge",
    "tower",
    "castle",
    "viewpoint",
    "monument",
    "statue",
    "palace",
    "stadium",
}


class ConfidenceService:
    """Service evaluating multi-signal confidence scores (0-100%) for extracted travel locations."""

    @staticmethod
    def calculate_confidence(
        raw_name: str,
        city: Optional[str] = None,
        country: Optional[str] = None,
        verified: bool = False,
        place_id: Optional[str] = None,
        address: Optional[str] = None,
        text_context: Optional[str] = None,
    ) -> int:
        """
        Calculates a 0-100% confidence score based on multi-signal evidence:
        1. Google Places Match (up to 55 pts)
        2. Metadata Completeness (up to 20 pts)
        3. Text/Caption Context Alignment (up to 20 pts)
        4. Landmark Specificity & Generic Term Penalty (up to 15 pts)
        """
        score = 0
        cleaned_name = raw_name.strip()
        lower_name = cleaned_name.lower()

        # 1. Google Places Match Signal (Max 55 pts)
        if verified and place_id:
            score += 55
        elif verified:
            score += 40
        elif address:
            score += 20
        else:
            score += 10

        # 2. Metadata Completeness Signal (Max 20 pts)
        if city:
            score += 10
        if country:
            score += 10
        if city and country:
            score += 10

        # 3. Context & Caption Alignment Signal (Max 20 pts)
        if text_context:
            context_lower = text_context.lower()
            if lower_name in context_lower:
                score += 20
            elif city and city.lower() in context_lower:
                score += 15
            elif country and country.lower() in context_lower:
                score += 10

        # 4. Landmark Specificity & Generic Penalty Signal (Max 15 pts)
        words = set(re.findall(r"\w+", lower_name))
        is_generic = words.issubset(GENERIC_LOCATION_TERMS) or lower_name in GENERIC_LOCATION_TERMS

        if is_generic:
            # Generic names without city get heavily penalized and capped at <=45%
            score = min(score, 45) if not city else min(score, 65)
        else:
            # Proper landmark name
            if len(cleaned_name.split()) >= 2:
                score += 15
            else:
                score += 10

        # Cap score between 0 and 100
        final_score = max(0, min(100, score))
        logger.debug(f"Confidence score for '{cleaned_name}' (City: {city}, Verified: {verified}): {final_score}%")
        return final_score
