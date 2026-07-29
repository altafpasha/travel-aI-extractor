import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import CacheRepository
from app.core.logging import logger


class CacheService:
    """Service providing Smart Caching and Duplicate Detection for travel extractions."""

    def __init__(self, db_session: AsyncSession):
        self.repository = CacheRepository(db_session)

    async def get_cached_extraction(
        self,
        file_hash: str,
        min_confidence: int = 70
    ) -> Optional[Dict[str, Any]]:
        """
        Looks up cached extraction by content SHA256 checksum.
        If a duplicate match is found AND its places meet the high-confidence threshold (>= 70%),
        returns the cached extraction instantly without re-running AI Vision or Places API.
        """
        cached_data = await self.repository.get_by_hash(file_hash)
        if not cached_data:
            return None

        places = cached_data.get("places", [])
        # If cached data contains places, check if at least one place meets min_confidence threshold
        if places:
            max_confidence = max(p.get("confidence", 0) for p in places)
            if max_confidence < min_confidence:
                logger.info(
                    f"Duplicate cache match found for '{file_hash[:10]}...', but max confidence "
                    f"({max_confidence}%) is below threshold ({min_confidence}%). Re-running extraction."
                )
                return None

        logger.info(f"Duplicate high-confidence match found for hash '{file_hash[:10]}...'. Returning instant response.")
        return cached_data

    async def save_extraction_cache(
        self,
        file_hash: str,
        destination: Optional[str],
        response_dict: Dict[str, Any]
    ):
        """Saves a verified extraction response in the smart cache database."""
        await self.repository.save_cache(
            file_hash=file_hash,
            destination=destination,
            response_dict=response_dict
        )

    async def get_cache_statistics() -> Dict[str, Any]:
        """Retrieves global cache hit/miss statistics."""
        return await self.repository.get_stats()

    async def clear_all_cache(self) -> int:
        """Purges all entries from smart cache."""
        return await self.repository.clear_cache()
