from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.extraction import ImageExtractionResponse


class AsyncExtractionResponse(BaseModel):
    """Response returned when an extraction task is asynchronously queued."""

    job_id: str = Field(..., json_schema_extra={"example": "job_9823f4a12"}, description="Unique async job ID")
    status: str = Field("queued", json_schema_extra={"example": "queued"}, description="Job status: queued")
    check_status_url: str = Field(
        ...,
        json_schema_extra={"example": "/jobs/job_9823f4a12"},
        description="URL to check job progress and retrieve results",
    )


JobEnqueueResponse = AsyncExtractionResponse


class JobStatusResponse(BaseModel):
    """Response model for checking async job status."""

    job_id: str = Field(..., json_schema_extra={"example": "job_9823f4a12"})
    status: str = Field(
        ..., json_schema_extra={"example": "completed"}, description="Job status: queued, processing, completed, failed"
    )
    result: Optional[ImageExtractionResponse] = Field(
        None, description="Final extracted places JSON if status == completed"
    )
    error_message: Optional[str] = Field(None, description="Error message if status == failed")
