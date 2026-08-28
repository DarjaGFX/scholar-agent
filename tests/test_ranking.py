import pytest
from scholar_agent.ranking import search_scholars

@pytest.mark.vcr
async def test_ranking_1():
    result = await search_scholars("retrieval augmented generation")

    assert len(result) >= 5
    assert 'Philip S. Yu' in result[:5]
    assert 'Ji-Rong Wen' in result[:10]
    assert 'Chatterbox TTS' not in result
    assert 'Gemini 3.1 (Flash)' not in result
    assert 'Assignee Research' not in result