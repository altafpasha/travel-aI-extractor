import hashlib
import os
import anyio
from fastapi import UploadFile
from typing import Tuple
from app.core.config import get_settings
from app.core.exceptions import ImageProcessingError
from app.core.logging import logger

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".m4v", ".mkv"}
ALLOWED_VIDEO_MIME_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-m4v"}
MAX_VIDEO_SIZE_MB = 50


class FileHandler:
    """Utility class to validate and process file uploads asynchronously."""

    @staticmethod
    async def validate_and_read_image(file: UploadFile) -> Tuple[bytes, str, str]:
        """
        Validates image file type and size, returning file_bytes, filename, and sha256_hash.
        """
        settings = get_settings()
        
        if not file.filename:
            raise ImageProcessingError("File must have a valid filename.")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ImageProcessingError(
                f"Unsupported image extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            )

        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise ImageProcessingError(
                f"File size {file_size_mb:.2f}MB exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if len(file_bytes) == 0:
            raise ImageProcessingError("Uploaded file is empty (0 bytes).")

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        return file_bytes, file.filename, sha256_hash

    @staticmethod
    async def validate_and_read_video(file: UploadFile) -> Tuple[bytes, str, str]:
        """
        Validates video file type and size (<50MB), returning file_bytes, filename, and sha256_hash.
        """
        if not file.filename:
            raise ImageProcessingError("File must have a valid filename.")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise ImageProcessingError(
                f"Unsupported video extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
            )

        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > MAX_VIDEO_SIZE_MB:
            raise ImageProcessingError(
                f"Video file size {file_size_mb:.2f}MB exceeds maximum limit of {MAX_VIDEO_SIZE_MB}MB."
            )

        if len(file_bytes) == 0:
            raise ImageProcessingError("Uploaded video file is empty (0 bytes).")

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        return file_bytes, file.filename, sha256_hash

    @staticmethod
    async def save_upload_file(file_bytes: bytes, filename: str) -> str:
        """Saves file bytes asynchronously to configured upload directory using anyio."""
        settings = get_settings()
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        path = anyio.Path(file_path)
        await path.write_bytes(file_bytes)

        return file_path
