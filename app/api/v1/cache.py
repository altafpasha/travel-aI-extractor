from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repository import ExtractionRepository
from app.services.cache_service import CacheService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cache", tags=["Cache"])


class CacheStatsResponse(BaseModel):
    """Response schema for cache performance metrics."""
    total_entries: int = Field(..., description="Total unique items cached")
    total_hits: int = Field(..., description="Total cache hits served")


class CacheClearResponse(BaseModel):
    """Response schema for cache purge operation."""
    status: str = Field(default="ok")
    deleted_count: int = Field(..., description="Number of deleted cache records")


@router.get(
    "",
    response_model=CacheStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get smart cache statistics"
)
async def get_cache_stats(db: AsyncSession = Depends(get_db)) -> CacheStatsResponse:
    """Returns smart cache utilization metrics and hit counts."""
    service = CacheService(db)
    stats = await service.repository.get_stats()
    return CacheStatsResponse(**stats)


@router.delete(
    "",
    response_model=CacheClearResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear all smart cache entries"
)
async def clear_cache(db: AsyncSession = Depends(get_db)) -> CacheClearResponse:
    """Purges all cached extractions from database."""
    service = CacheService(db)
    deleted_count = await service.clear_all_cache()
    return CacheClearResponse(status="ok", deleted_count=deleted_count)


@router.delete(
    "/prune",
    response_model=CacheClearResponse,
    status_code=status.HTTP_200_OK,
    summary="Purge historical extraction logs older than N days"
)
async def prune_old_logs(
    days: int = Query(30, ge=1, le=365, description="Number of days to keep"),
    db: AsyncSession = Depends(get_db)
) -> CacheClearResponse:
    """Prunes old historical database extraction logs to keep storage size lightweight."""
    repo = ExtractionRepository(db)
    deleted_count = await repo.purge_old_records(days_to_keep=days)
    return CacheClearResponse(status="ok", deleted_count=deleted_count)
