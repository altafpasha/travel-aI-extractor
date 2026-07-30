from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.database.connection import get_db
from app.schemas.multisource import UniversalExtractionRequest
from app.schemas.queue import JobEnqueueResponse, JobStatusResponse
from app.services.queue_service import QueueService

router = APIRouter(tags=["Async Queue"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/extract/async",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue heavy extraction job for asynchronous background processing"
)
async def enqueue_extraction_job(
    payload: UniversalExtractionRequest,
    db: AsyncSession = Depends(get_db)
) -> JobEnqueueResponse:
    """
    Submits extraction payload to asynchronous queue workers.
    Returns HTTP 202 Accepted instantly with a job_id for status polling.
    """
    queue_service = QueueService(db_session=db)
    response = await queue_service.enqueue_job(payload)
    return response


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check status and retrieve results for an asynchronous extraction job"
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> JobStatusResponse:
    """
    Polls the status of an enqueued job by job_id.
    """
    queue_service = QueueService(db_session=db)
    job_status = await queue_service.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Async job '{job_id}' not found."
        )

    return job_status
