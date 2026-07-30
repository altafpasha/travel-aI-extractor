import pytest

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_cache_hit_cycle(client):
    """Test cache MISS on initial request followed by cache HIT on duplicate request."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    payload = {"text": "Visiting Tokyo Tower in Japan.", "context": "Test"}
    
    # First call -> fresh extraction (Cache MISS)
    res1 = await client.post("/extract/text", json=payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()

    # Second call with identical payload -> Cache HIT
    res2 = await client.post("/extract/text", json=payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()

    # Response values match and execution time is near zero on cache hit
    assert data1["destination"] == data2["destination"]
    assert data2["execution_time_seconds"] < 0.1


@pytest.mark.asyncio
async def test_cache_stats_and_clear_endpoints(client):
    """Test GET /cache and DELETE /cache endpoints."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    # Stats
    res_stats = await client.get("/cache", headers=headers)
    assert res_stats.status_code == 200
    assert "total_entries" in res_stats.json()

    # Clear
    res_clear = await client.delete("/cache", headers=headers)
    assert res_clear.status_code == 200
    assert res_clear.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_cache_prune_endpoint(client):
    """Test DELETE /cache/prune endpoint."""
    settings = get_settings()
    headers = {"X-API-Key": settings.API_KEY}
    res = await client.delete("/cache/prune?days=30", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
