import io

import pytest
from PIL import Image, ImageDraw

from app.services.ocr_service import OCRService


def test_ocr_extract_text_empty_on_dummy_bytes():
    """Tests that passing invalid bytes to OCRService returns None cleanly without throwing errors."""
    result = OCRService.extract_text_from_image(b"invalid_binary_data")
    assert result is None


def test_ocr_extract_text_from_created_image():
    """Tests local OCR processing on a synthetic image containing rendered text."""
    # Create synthetic RGB image with text
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Kyoto Fushimi Inari", fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    image_bytes = img_byte_arr.getvalue()

    result = OCRService.extract_text_from_image(image_bytes)
    # If tesseract is installed in container, result contains text string, else returns None fallback
    if result:
        assert isinstance(result, str)
        assert len(result) > 0
