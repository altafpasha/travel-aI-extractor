from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.database.connection import get_db
from app.services.cache_service import CacheService

router = APIRouter(prefix="/cache", tags=["Cache Management"], dependencies=[Depends(verify_api_key)])


@router.get(
    "", status_code=status.HTTP_200_OK, summary="Retrieve overall smart extraction cache performance statistics"
)
async def get_cache_statistics(db: AsyncSession = Depends(get_db)):
    """
    Returns total cached extraction entries, cumulative cache hit counts, and performance metrics.
    """
    cache_service = CacheService(db_session=db)
    return await cache_service.get_stats()


@router.delete("", status_code=status.HTTP_200_OK, summary="Purge all smart cache entries from database")
async def clear_cache_entries(db: AsyncSession = Depends(get_db)):
    """
    Clears all stored smart cache entries.
    """
    cache_service = CacheService(db_session=db)
    return await cache_service.clear_cache()


@router.delete("/prune", status_code=status.HTTP_200_OK, summary="Purge historical extraction logs older than N days")
async def prune_historical_logs(
    days: int = Query(30, ge=1, le=365, description="Retention threshold in days"), db: AsyncSession = Depends(get_db)
):
    """
    Deletes historical extraction logs older than the specified retention window (default 30 days).
    """
    cache_service = CacheService(db_session=db)
    return await cache_service.prune_old_logs(days_to_keep=days)
