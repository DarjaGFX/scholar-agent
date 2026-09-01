from scholar_agent.ranking import HEADERS
import httpx
from scholar_agent.agent import run_agent
from scholar_agent.main import app
import pytest


@pytest.mark.vcr
async def test_tool_call():
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=120)
    trace = []
    query = "Find supervisors for low-resource NLP in Europe, check they're still active, and tell me whose research fits low-resource language processing best."
    answer = await run_agent(query, app.state.client, trace=trace)
    names = [t["name"] for t in trace]
    assert "find_scholars" in names and "check_activity" in names and "assess_fit" in names
    assert len(trace) >= 3


@pytest.mark.vcr
async def test_agent_chains_tools():
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=120)
    trace = []
    answer = await run_agent(
        "Find supervisors for protein structure prediction in Europe, check they are still active, "
        "and tell me whose research fits low-resource language processing best.",
        app.state.client, trace=trace)
    names = [t["name"] for t in trace]
    assert "find_scholars" in names
    assert "check_activity" in names
    assert "assess_fit" in names
    assert len(trace) >= 3