import asyncio
import json
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import ExtractionJob, ExtractionRepository
from app.schemas.extraction import ImageExtractionResponse
from app.schemas.multisource import UniversalExtractionRequest
from app.schemas.queue import AsyncExtractionResponse, JobStatusResponse
from app.services.multisource_service import MultiSourceEngine
from app.services.extraction_service import ExtractionService
from app.core.logging import logger


class QueueService:
    """Service orchestrating asynchronous background queue jobs."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.repo = ExtractionRepository(db_session)

    async def enqueue_universal_extraction(
        self,
        request: UniversalExtractionRequest
    ) -> AsyncExtractionResponse:
        """
        Creates a new queued job record and triggers background worker processing.
        Returns instant 202 Accepted status payload.
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        await self.repo.create_job(job_id)
        logger.info(f"Enqueued extraction job '{job_id}'")

        # Spawn background processing task asynchronously
        asyncio.create_task(self._process_background_job(job_id, request))

        return AsyncExtractionResponse(
            job_id=job_id,
            status="queued",
            check_status_url=f"/jobs/{job_id}"
        )

    enqueue_job = enqueue_universal_extraction

    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """Looks up job status by ID."""
        job = await self.repo.get_job(job_id)
        if not job:
            return None

        parsed_result: Optional[ImageExtractionResponse] = None
        if job.result_json:
            try:
                parsed_result = ImageExtractionResponse(**json.loads(job.result_json))
            except Exception as e:
                logger.error(f"Failed to parse stored job result JSON: {str(e)}")

        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            result=parsed_result,
            error_message=job.error_message
        )

    async def _process_background_job(
        self,
        job_id: str,
        request: UniversalExtractionRequest
    ) -> None:
        """Internal worker executing extraction logic asynchronously in background."""
        try:
            await self.repo.update_job_status(job_id, status="processing")
            content = await MultiSourceEngine.build_travel_content(request)
            
            extraction_service = ExtractionService(db_session=self.db_session)
            result = await extraction_service.process_travel_content(content)

            await self.repo.update_job_status(
                job_id,
                status="completed",
                result_dict=result.model_dump()
            )
            logger.info(f"Async extraction job '{job_id}' completed successfully.")
        except Exception as e:
            logger.error(f"Async extraction job '{job_id}' failed: {str(e)}")
            await self.repo.update_job_status(
                job_id,
                status="failed",
                error_message=str(e)
            )
