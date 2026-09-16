import pytest
from scholar_agent.ranking import search_scholars

@pytest.mark.vcr
async def test_ranking_1():
    result = await search_scholars("retrieval augmented generation")

    names = [r.get("display_name", "") for r in result]

    assert names[0] == 'Philip S. Yu'
    assert {'Ji-Rong Wen', 'Tat‐Seng Chua', 'Maarten de Rijke'} <= set(names[:5])
    assert len(names) >= 5
    assert 'Chatterbox TTS' not in names
    assert 'Gemini 3.1 (Flash)' not in names
    assert 'Assignee Research' not in names
