import pytest
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_extract_video_success(client):
    """Test successful video upload extraction endpoint."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    dummy_video_bytes = b"ftypisom" + b"\x00" * 200

    files = {"file": ("travel_reel.mp4", dummy_video_bytes, "video/mp4")}

    res = await client.post("/extract/video", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "destination" in data
    assert "places" in data
    assert isinstance(data["places"], list)


@pytest.mark.asyncio
async def test_extract_video_invalid_extension(client):
    """Test video upload endpoint rejecting unsupported file extension."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    files = {"file": ("document.pdf", b"pdf content", "application/pdf")}

    res = await client.post("/extract/video", files=files, headers=headers)
    assert res.status_code == 400
    assert "Unsupported video file format" in res.json()["detail"]


@pytest.mark.asyncio
async def test_extract_video_empty_file(client):
    """Test video upload endpoint rejecting empty 0-byte file."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    files = {"file": ("empty_reel.mp4", b"", "video/mp4")}

    res = await client.post("/extract/video", files=files, headers=headers)
    assert res.status_code == 400
    assert "Uploaded video file is empty" in res.json()["detail"]
