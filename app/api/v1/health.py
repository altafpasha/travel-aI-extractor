from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/", response_class=PlainTextResponse, summary="Root endpoint")
async def root() -> str:
    """Returns basic plain text root status string."""
    return "Travel AI Extractor Running"


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Returns application health and configuration metadata."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT
    )
