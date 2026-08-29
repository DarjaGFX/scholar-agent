from httpx import AsyncClient
from httpx import ASGITransport
from scholar_agent.ranking import HEADERS
import httpx
from scholar_agent.main import app
import pytest


@pytest.mark.vcr
async def test_search_endpoint():
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=30)  # no lifespan needed in tests
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/search", params={"q": "retrieval augmented generation"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 5
    assert "Chatterbox TTS" not in [s["name"] for s in body["scholars"]]