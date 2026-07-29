import asyncio
import pytest


@pytest.mark.asyncio
async def test_enqueue_async_job_and_poll_status(client):
    """Tests POST /extract/async job enqueueing and subsequent status polling via GET /jobs/{job_id}."""
    payload = {
        "source_type": "text",
        "content": "Exploring Fushimi Inari Shrine in Kyoto Japan.",
        "context": "Kyoto trip"
    }

    # Enqueue async job
    enqueue_res = await client.post("/extract/async", json=payload)
    assert enqueue_res.status_code == 202, f"Enqueue failed: {enqueue_res.text}"

    data = enqueue_res.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert "check_status_url" in data
    job_id = data["job_id"]

    # Poll status until completed or timeout
    for _ in range(10):
        await asyncio.sleep(0.1)
        status_res = await client.get(f"/jobs/{job_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()

        if status_data["status"] == "completed":
            assert status_data["result"] is not None
            assert status_data["result"]["destination"] == "Kyoto"
            assert len(status_data["result"]["places"]) > 0
            break


@pytest.mark.asyncio
async def test_get_nonexistent_job_status_returns_404(client):
    """Tests that querying status for a non-existent job ID returns 404 Not Found."""
    res = await client.get("/jobs/non_existent_job_999")
    assert res.status_code == 404
