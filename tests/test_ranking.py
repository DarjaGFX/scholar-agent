import pytest
from scholar_agent.ranking import search_scholars

@pytest.mark.vcr
async def test_ranking_1():
    result = await search_scholars("retrieval augmented generation")

    names = [ record.get("display_name", "") for record in result]
    assert len(names) >= 5
    assert 'Jiawei Han' == names[0]
    assert 'Tat‐Seng Chua' == names[1]
    assert 'Philip S. Yu' == names[2]
    assert 'Ji-Rong Wen' in names[:10]
    assert 'Chatterbox TTS' not in names
    assert 'Gemini 3.1 (Flash)' not in names
    assert 'Assignee Research' not in names