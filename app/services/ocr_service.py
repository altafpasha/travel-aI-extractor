import io
from typing import Optional
from PIL import Image
from app.core.logging import logger


class OCRService:
    """Service utilizing local Tesseract OCR to extract visible text from images & screenshots."""

    @staticmethod
    def extract_text_from_image(image_bytes: bytes) -> Optional[str]:
        """
        Extracts raw readable text overlay or signboard text from image bytes using local OCR.
        Returns cleaned text string or None if no readable text is detected.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert palette/RGBA images to RGB for OCR compatibility
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            try:
                import pytesseract
                extracted_text = pytesseract.image_to_string(image)
                cleaned = extracted_text.strip()
                if cleaned:
                    logger.info(f"OCR successfully extracted text from image ({len(cleaned)} chars)")
                    return cleaned
            except (ImportError, Exception) as tesseract_err:
                logger.debug(f"Pytesseract OCR binary unexecutable or missing ({str(tesseract_err)}). Falling back smoothly.")

            return None
        except Exception as e:
            logger.error(f"Failed to process image bytes in OCRService: {str(e)}")
            return None
