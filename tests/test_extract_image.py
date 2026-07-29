import io
import pytest


@pytest.mark.asyncio
async def test_extract_image_success(client):
    """Tests successful image upload and place extraction pipeline via POST /extract/image."""
    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 100

    files = {
        "file": ("test_kyoto.jpg", io.BytesIO(dummy_image), "image/jpeg")
    }

    response = await client.post("/extract/image", files=files)
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert "destination" in data
    assert "places" in data
    assert "execution_time_seconds" in data
    assert isinstance(data["places"], list)

    if len(data["places"]) > 0:
        place = data["places"][0]
        assert "name" in place
        assert "confidence" in place
        assert "verified" in place


@pytest.mark.asyncio
async def test_extract_image_invalid_extension(client):
    """Tests that uploading a unsupported extension (e.g., .txt) returns HTTP 400 error."""
    files = {
        "file": ("notes.txt", io.BytesIO(b"Hello world text file"), "text/plain")
    }

    response = await client.post("/extract/image", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "ImageProcessingError"
    assert "Unsupported image extension" in data["message"]


@pytest.mark.asyncio
async def test_extract_image_empty_file(client):
    """Tests that uploading an empty 0-byte file returns HTTP 400 error."""
    files = {
        "file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")
    }

    response = await client.post("/extract/image", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "ImageProcessingError"
    assert "Uploaded file is empty" in data["message"]
