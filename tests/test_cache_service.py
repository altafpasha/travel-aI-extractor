import io
import pytest


@pytest.mark.asyncio
async def test_cache_hit_cycle(client):
    """Tests that subsequent extraction requests with identical content return instant cache hits."""
    payload = {
        "text": "Unique test travel text exploring Fushimi Inari in Kyoto Japan."
    }

    # First request: Cache Miss
    resp1 = await client.post("/extract/text", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Second request: Cache Hit
    resp2 = await client.post("/extract/text", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data1["destination"] == data2["destination"]
    assert len(data1["places"]) == len(data2["places"])
    assert data2["execution_time_seconds"] < 0.1  # Instant cache hit response time


@pytest.mark.asyncio
async def test_cache_stats_and_clear_endpoints(client):
    """Tests GET /cache statistics and DELETE /cache purge endpoints."""
    # Seed cache with text request
    await client.post("/extract/text", json={"text": "Visiting Tokyo Skytree in Japan."})
    await client.post("/extract/text", json={"text": "Visiting Tokyo Skytree in Japan."}) # Hit

    # GET /cache stats
    stats_resp = await client.get("/cache")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert "total_entries" in stats_data
    assert "total_hits" in stats_data
    assert stats_data["total_entries"] >= 1

    # DELETE /cache
    clear_resp = await client.delete("/cache")
    assert clear_resp.status_code == 200
    clear_data = clear_resp.json()
    assert clear_data["status"] == "ok"
    assert clear_data["deleted_count"] >= 1

    # Verify cache emptied
    stats_after = await client.get("/cache")
    assert stats_after.json()["total_entries"] == 0


@pytest.mark.asyncio
async def test_cache_prune_endpoint(client):
    """Tests DELETE /cache/prune endpoint for historical log retention pruning."""
    prune_resp = await client.delete("/cache/prune?days=30")
    assert prune_resp.status_code == 200
    data = prune_resp.json()
    assert data["status"] == "ok"
    assert "deleted_count" in data
