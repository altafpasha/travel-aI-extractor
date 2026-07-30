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

                collected_text_parts = []
                # Pass 1: Standard image OCR
                t1 = pytesseract.image_to_string(image).strip()
                if t1:
                    collected_text_parts.append(t1)

                # Pass 2: Header banner crop (top 40% where travel poster titles like BALI reside)
                w, h = image.size
                if h > 50:
                    top_banner = image.crop((0, 0, w, int(h * 0.4)))
                    t2 = pytesseract.image_to_string(top_banner, config="--psm 6").strip()
                    if t2:
                        collected_text_parts.append(t2)
                    t2_sparse = pytesseract.image_to_string(top_banner, config="--psm 11").strip()
                    if t2_sparse:
                        collected_text_parts.append(t2_sparse)

                # Pass 3: Grayscale & inverted threshold for white text on dark background
                gray = image.convert("L")
                bw = gray.point(lambda x: 0 if x > 140 else 255)
                t3 = pytesseract.image_to_string(bw).strip()
                if t3:
                    collected_text_parts.append(t3)

                cleaned = " ".join(collected_text_parts).strip()
                if cleaned:
                    logger.info(f"OCR successfully extracted text from image ({len(cleaned)} chars)")
                    return cleaned
            except (ImportError, Exception) as tesseract_err:
                logger.debug(
                    f"Pytesseract OCR binary unexecutable or missing ({str(tesseract_err)}). Falling back smoothly."
                )

            return None
        except Exception as e:
            logger.error(f"Failed to process image bytes in OCRService: {str(e)}")
            return None
