from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class TravelExtractorException(Exception):
    """Base exception for Travel AI Extractor."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ImageProcessingError(TravelExtractorException):
    """Raised when an uploaded image cannot be validated or processed."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class AIServiceException(TravelExtractorException):
    """Raised when the AI model/Gemini API fails to extract places."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


class PlacesServiceException(TravelExtractorException):
    """Raised when Google Places API fails or encounters an issue."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


async def travel_extractor_exception_handler(request: Request, exc: TravelExtractorException) -> JSONResponse:
    """Global exception handler for application domain exceptions."""
    logger.error(f"Domain exception on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message
        }
    )
