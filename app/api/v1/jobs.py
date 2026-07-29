from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.schemas.multisource import UniversalExtractionRequest
from app.schemas.queue import AsyncExtractionResponse, JobStatusResponse
from app.services.queue_service import QueueService

router = APIRouter(tags=["Async Queue Jobs"])


@router.post(
    "/extract/async",
    response_model=AsyncExtractionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue an extraction task asynchronously",
    description="Submits an extraction request to the background queue and returns an instant 202 Accepted response with check_status_url."
)
async def extract_async(
    payload: UniversalExtractionRequest,
    db: AsyncSession = Depends(get_db)
) -> AsyncExtractionResponse:
    """
    Enqueues heavy extraction tasks asynchronously into the background queue.
    """
    queue_service = QueueService(db)
    return await queue_service.enqueue_universal_extraction(payload)


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check status and retrieve results of an async job",
    description="Polls background job status (queued, processing, completed, failed) and returns final extracted places JSON."
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> JobStatusResponse:
    """
    Retrieves execution status and extracted places result for a queued task.
    """
    queue_service = QueueService(db)
    job_status = await queue_service.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Async job '{job_id}' not found."
        )

    return job_status
