import io

import pytest
from PIL import Image

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_extract_image_success(client):
    """Test successful image upload extraction endpoint."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}

    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("test_landmark.jpg", img_bytes, "image/jpeg")}

    res = await client.post(f"{settings.API_V1_STR}/extract/image", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "destination" in data
    assert "places" in data
    assert isinstance(data["places"], list)


@pytest.mark.asyncio
async def test_extract_image_invalid_extension(client):
    """Test image upload endpoint rejecting unsupported file extension."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    files = {"file": ("unsupported_doc.txt", b"text content", "text/plain")}

    res = await client.post(f"{settings.API_V1_STR}/extract/image", files=files, headers=headers)
    assert res.status_code == 400
    assert "Unsupported image extension" in res.json()["detail"]


@pytest.mark.asyncio
async def test_extract_image_empty_file(client):
    """Test image upload endpoint rejecting empty 0-byte file."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    files = {"file": ("empty_photo.jpg", b"", "image/jpeg")}

    res = await client.post(f"{settings.API_V1_STR}/extract/image", files=files, headers=headers)
    assert res.status_code == 400
    assert "Uploaded file is empty" in res.json()["detail"]
