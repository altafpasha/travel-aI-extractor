from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import get_settings
from app.core.logging import logger

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI security dependency validating X-API-Key header against settings.API_KEY.
    Raises HTTP 401 Unauthorized if missing or invalid.
    """
    settings = get_settings()
    expected_key = settings.API_KEY

    # If API_KEY is empty/unset in dev, allow access
    if not expected_key:
        return "unrestricted"

    if not api_key or api_key != expected_key:
        logger.warning(f"Unauthorized API request with invalid/missing X-API-Key: '{api_key}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide a valid 'X-API-Key' header.",
        )

    return api_key
