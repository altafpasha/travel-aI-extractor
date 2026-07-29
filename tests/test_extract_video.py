import io
import pytest


@pytest.mark.asyncio
async def test_extract_video_success(client):
    """Tests successful video upload and keyframe place extraction pipeline via POST /extract/video."""
    dummy_video_bytes = b"ftypisom" + b"\x00" * 1000

    files = {
        "file": ("travel_reel.mp4", io.BytesIO(dummy_video_bytes), "video/mp4")
    }

    response = await client.post("/extract/video", files=files)
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
async def test_extract_video_invalid_extension(client):
    """Tests that uploading an unsupported video extension returns HTTP 400 error."""
    files = {
        "file": ("video.pdf", io.BytesIO(b"Fake PDF file"), "application/pdf")
    }

    response = await client.post("/extract/video", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "ImageProcessingError"
    assert "Unsupported video extension" in data["message"]


@pytest.mark.asyncio
async def test_extract_video_empty_file(client):
    """Tests that uploading an empty video file returns HTTP 400 error."""
    files = {
        "file": ("empty.mp4", io.BytesIO(b""), "video/mp4")
    }

    response = await client.post("/extract/video", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "ImageProcessingError"
    assert "Uploaded video file is empty" in data["message"]
