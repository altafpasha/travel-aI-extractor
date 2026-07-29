import pytest
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_enqueue_async_job_and_poll_status(client):
    """Test POST /extract/async job enqueue and GET /jobs/{job_id} status polling."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {
        "source_type": "text",
        "content": "Exploring Kyoto Fushimi Inari Shrine",
        "context": "Async Test"
    }

    # Enqueue
    res_enqueue = await client.post("/extract/async", json=payload, headers=headers)
    assert res_enqueue.status_code == 202
    data = res_enqueue.json()
    assert "job_id" in data
    assert data["status"] in ("queued", "completed")
    job_id = data["job_id"]

    # Poll
    res_poll = await client.get(f"/jobs/{job_id}", headers=headers)
    assert res_poll.status_code == 200
    poll_data = res_poll.json()
    assert poll_data["job_id"] == job_id
    assert poll_data["status"] in ("queued", "completed")


@pytest.mark.asyncio
async def test_get_nonexistent_job_status_returns_404(client):
    """Test polling nonexistent job_id returns 404 Not Found."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    res = await client.get("/jobs/nonexistent_job_999999", headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
