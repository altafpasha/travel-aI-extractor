import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import CacheRepository, ExtractionRepository
from app.core.logging import logger


class CacheService:
    """Service providing Smart Caching and Duplicate Detection for travel extractions."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.repository = CacheRepository(db_session)
        self.extraction_repo = ExtractionRepository(db_session)

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

    async def get_stats(self) -> Dict[str, Any]:
        """Retrieves global cache hit/miss statistics."""
        return await self.repository.get_stats()

    get_cache_statistics = get_stats

    async def clear_cache(self) -> Dict[str, Any]:
        """Purges all entries from smart cache."""
        deleted_count = await self.repository.clear_cache()
        return {"status": "ok", "deleted_count": deleted_count}

    clear_all_cache = clear_cache

    async def prune_old_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Purges historical log entries older than days_to_keep days."""
        deleted_count = await self.extraction_repo.purge_old_records(days_to_keep=days_to_keep)
        return {"status": "ok", "deleted_count": deleted_count}
