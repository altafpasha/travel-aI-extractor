from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.logging import logger
from app.database.connection import Base


class ExtractionLog(Base):
    """DB Model for recording historical extraction logs."""
    __tablename__ = "extraction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    destination: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    places_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    execution_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CacheEntry(Base):
    """DB Model for storing smart cache entries keyed by content SHA256 hash."""
    __tablename__ = "cache_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    destination: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cached_response: Mapped[str] = mapped_column(Text, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class ExtractionJob(Base):
    """DB Model for tracking asynchronous extraction background queue jobs."""
    __tablename__ = "extraction_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)  # queued, processing, completed, failed
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ExtractionRepository:
    """Repository managing extraction history database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_extraction(
        self,
        file_name: str,
        destination: Optional[str],
        places_count: int,
        raw_response: Dict[str, Any],
        execution_time_seconds: float,
        file_hash: Optional[str] = None
    ) -> ExtractionLog:
        """Saves an extraction audit record to database."""
        try:
            log_entry = ExtractionLog(
                file_name=file_name,
                file_hash=file_hash,
                destination=destination,
                places_count=places_count,
                raw_response=json.dumps(raw_response),
                execution_time_seconds=execution_time_seconds
            )
            self.session.add(log_entry)
            await self.session.flush()
            logger.info(f"Extraction log saved for file '{file_name}' (ID: {log_entry.id})")
            return log_entry
        except Exception as e:
            logger.error(f"Failed to log extraction into database: {str(e)}")
            raise

    async def create_job(self, job_id: str) -> ExtractionJob:
        """Creates a new queued job record."""
        job = ExtractionJob(job_id=job_id, status="queued")
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job(self, job_id: str) -> Optional[ExtractionJob]:
        """Retrieves job record by job_id."""
        stmt = select(ExtractionJob).where(ExtractionJob.job_id == job_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        result_dict: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[ExtractionJob]:
        """Updates job status, result, and completion timestamp."""
        job = await self.get_job(job_id)
        if job:
            job.status = status
            if result_dict:
                job.result_json = json.dumps(result_dict)
            if error_message:
                job.error_message = error_message
            if status in ("completed", "failed"):
                job.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
        return job

    async def purge_old_records(self, days_to_keep: int = 30) -> int:
        """Deletes historical logs older than days_to_keep days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        stmt = delete(ExtractionLog).where(ExtractionLog.created_at < cutoff)
        result = await self.session.execute(stmt)
        await self.session.flush()
        logger.info(f"Purged {result.rowcount} historical extraction log records older than {days_to_keep} days.")
        return result.rowcount


class CacheRepository:
    """Repository managing smart cache operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Looks up cached extraction by file SHA256 hash and increments hit count."""
        try:
            stmt = select(CacheEntry).where(CacheEntry.file_hash == file_hash)
            result = await self.session.execute(stmt)
            entry = result.scalar_one_or_none()

            if entry:
                entry.hit_count += 1
                await self.session.flush()
                logger.info(f"Cache HIT for hash '{file_hash[:10]}...' (Hit count: {entry.hit_count})")
                return json.loads(entry.cached_response)

            logger.info(f"Cache MISS for hash '{file_hash[:10]}...'")
            return None
        except Exception as e:
            logger.error(f"Failed to query cache by hash: {str(e)}")
            return None

    async def save_cache(
        self,
        file_hash: str,
        destination: Optional[str],
        response_dict: Dict[str, Any]
    ) -> CacheEntry:
        """Stores or updates a cached extraction entry."""
        try:
            stmt = select(CacheEntry).where(CacheEntry.file_hash == file_hash)
            result = await self.session.execute(stmt)
            entry = result.scalar_one_or_none()

            if entry:
                entry.destination = destination
                entry.cached_response = json.dumps(response_dict)
            else:
                entry = CacheEntry(
                    file_hash=file_hash,
                    destination=destination,
                    cached_response=json.dumps(response_dict),
                    hit_count=0
                )
                self.session.add(entry)

            await self.session.flush()
            logger.info(f"Cache saved for hash '{file_hash[:10]}...'")
            return entry
        except Exception as e:
            logger.error(f"Failed to save cache entry: {str(e)}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Returns overall cache statistics."""
        try:
            total_entries_stmt = select(func.count()).select_from(CacheEntry)
            total_entries_res = await self.session.execute(total_entries_stmt)
            total_entries = total_entries_res.scalar() or 0

            total_hits_stmt = select(func.coalesce(func.sum(CacheEntry.hit_count), 0))
            total_hits_res = await self.session.execute(total_hits_stmt)
            total_hits = total_hits_res.scalar() or 0

            return {
                "total_entries": total_entries,
                "total_hits": total_hits
            }
        except Exception as e:
            logger.error(f"Failed to compute cache stats: {str(e)}")
            return {"total_entries": 0, "total_hits": 0}

    async def clear_cache(self) -> int:
        """Purges all entries from the cache table, returning count of deleted records."""
        try:
            stmt = delete(CacheEntry)
            result = await self.session.execute(stmt)
            deleted_count = result.rowcount
            await self.session.flush()
            logger.info(f"Cleared {deleted_count} entries from smart cache.")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            raise
