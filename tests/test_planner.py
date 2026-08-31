from scholar_agent.ranking import HEADERS
from scholar_agent.main import app
import httpx
import pytest
from scholar_agent.planner import plan_search
from scholar_agent.models import SearchPlan

@pytest.mark.vcr
async def test_planner():
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=30)
    query = "large language models"
    plan = await plan_search(app.state.client, query)
    assert isinstance(plan, SearchPlan)
    assert len(plan.topics) > 0
    assert len(plan.countries) == 0
    assert plan.min_year is None
    assert plan.supervisor_rank is None
    assert plan.degree_level is None


@pytest.mark.vcr
async def test_planner_complex_query():
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=30)
    query = "PhD position in AI, Europe, active researcher professor since 2020"
    plan = await plan_search(app.state.client, query)
    assert isinstance(plan, SearchPlan)
    assert len(plan.topics) >= 1
    assert len(plan.countries) >= 1
    assert plan.min_year >= 2020
    assert plan.supervisor_rank.lower() == "professor"
    assert plan.degree_level.lower() == "phd"

@pytest.mark.vcr
async def test_list_phrasings():
    PHRASINGS = [
        "PhD in NLP for low-resource languages, Europe preferred",
        "looking for a supervisor in Europe working on low-resource NLP",
        "European university, computational linguistics, underrepresented languages, PhD",
        "low-resource language processing research groups in Europe",
        "NLP PhD position, EU, focus on low-resource languages",
    ]
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=30)
    for query in PHRASINGS:
        plan = await plan_search(app.state.client, query)
        assert isinstance(plan, SearchPlan)
        assert plan.min_year is None
        assert len(plan.countries) >= 1
        assert plan.supervisor_rank is None

@pytest.mark.vcr
async def test_min_year():
    PHRASINGS = [
        "PhD in NLP for low-resource languages, Europe preferred, posted in recent 6 months",
        "PhD in AI, Europe preferred, posted after pandemic",
        "PhD in ML, Europe preferred, posted in the 2020s",
    ]
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=30)
    for query in PHRASINGS:
        plan = await plan_search(app.state.client, query)
        assert isinstance(plan, SearchPlan)
        assert plan.min_year is not None
