from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.database.connection import get_db
from app.schemas.extraction import ExtractionErrorResponse, ImageExtractionResponse, TextExtractionRequest
from app.schemas.multisource import UniversalExtractionRequest
from app.services.extraction_service import ExtractionService
from app.services.multisource_service import MultiSourceEngine
from app.utils.file_handler import FileHandler

router = APIRouter(prefix="/extract", tags=["Extraction"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/image",
    response_model=ImageExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract places from an uploaded image or screenshot",
    responses={
        400: {"model": ExtractionErrorResponse, "description": "Invalid image file or format"},
        401: {"description": "Unauthorized - Missing or invalid X-API-Key header"},
        502: {"model": ExtractionErrorResponse, "description": "Upstream AI/Places API failure"}
    }
)
async def extract_image(
    file: UploadFile = File(..., description="Image or screenshot file (JPG, PNG, WebP)"),
    db: AsyncSession = Depends(get_db)
) -> ImageExtractionResponse:
    """
    Extracts structured travel destinations and places from an uploaded image.
    """
    file_bytes, filename, file_hash = await FileHandler.validate_and_read_image(file)

    extraction_service = ExtractionService(db_session=db)
    mime_type = file.content_type or "image/jpeg"
    response = await extraction_service.process_image_extraction(
        image_bytes=file_bytes,
        filename=filename,
        file_hash=file_hash,
        mime_type=mime_type
    )

    return response


@router.post(
    "/text",
    response_model=ImageExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract places from social media text, captions, or travel posts",
    responses={
        400: {"model": ExtractionErrorResponse, "description": "Invalid request payload"},
        401: {"description": "Unauthorized - Missing or invalid X-API-Key header"},
        502: {"model": ExtractionErrorResponse, "description": "Upstream AI/Places API failure"}
    }
)
async def extract_text(
    payload: TextExtractionRequest,
    db: AsyncSession = Depends(get_db)
) -> ImageExtractionResponse:
    """
    Extracts structured travel destinations and places from input text or social media caption.
    """
    extraction_service = ExtractionService(db_session=db)
    response = await extraction_service.process_text_extraction(
        text=payload.text,
        context=payload.context
    )

    return response


@router.post(
    "/video",
    response_model=ImageExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract places from uploaded video files (MP4, MOV, WebM)",
    responses={
        400: {"model": ExtractionErrorResponse, "description": "Invalid video file or format"},
        401: {"description": "Unauthorized - Missing or invalid X-API-Key header"},
        502: {"model": ExtractionErrorResponse, "description": "Upstream AI/Places API failure"}
    }
)
async def extract_video(
    file: UploadFile = File(..., description="Video file (MP4, MOV, WebM) under 50MB"),
    db: AsyncSession = Depends(get_db)
) -> ImageExtractionResponse:
    """
    Extracts structured travel destinations and places from a video file.
    """
    video_bytes, filename, file_hash = await FileHandler.validate_and_read_video(file)

    extraction_service = ExtractionService(db_session=db)
    response = await extraction_service.process_video_extraction(
        video_bytes=video_bytes,
        filename=filename,
        file_hash=file_hash
    )

    return response


@router.post(
    "/universal",
    response_model=ImageExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Universal multi-source travel place extraction API",
    responses={
        400: {"model": ExtractionErrorResponse, "description": "Invalid source content"},
        401: {"description": "Unauthorized - Missing or invalid X-API-Key header"},
        502: {"model": ExtractionErrorResponse, "description": "Upstream API failure"}
    }
)
async def extract_universal(
    payload: UniversalExtractionRequest,
    db: AsyncSession = Depends(get_db)
) -> ImageExtractionResponse:
    """
    Universal Public API accepting text, media URLs, or social media content:
    - Normalizes input into unified TravelContent model
    - Runs multi-modal extraction engine (Smart Cache -> OCR -> Speech -> Gemini -> Google Places -> Confidence Engine)
    - Returns standardized travel place JSON payload
    """
    content = await MultiSourceEngine.build_travel_content(payload)
    extraction_service = ExtractionService(db_session=db)
    response = await extraction_service.process_travel_content(content)
    return response
