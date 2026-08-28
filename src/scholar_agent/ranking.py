import asyncio
import httpx
from scholar_agent.openalex import top_authors_by_topic, get_author

HEADERS = {"User-Agent": "scholar-agent (ali.jafari20@gmail.com)"}
TIMEOUT = 10

MIN_CITES_PER_WORK = 1.0
MIN_H_INDEX = 2
MAX_WORKS_WITHOUT_CITES = 3_000


def is_real_researcher(author: dict) -> bool:

    works_count = author.get("works_count") or 0
    cited_by_count = author.get("cited_by_count") or 0
    h_index = (author.get("summary_stats") or {}).get("h_index") or 0

    if works_count == 0:
        return False
    if works_count > MAX_WORKS_WITHOUT_CITES and cited_by_count < MIN_CITES_PER_WORK:
        return False
    if h_index < MIN_H_INDEX:
        return False
    if cited_by_count / works_count < MIN_CITES_PER_WORK:
        return False
    return True

def rank_key(author: dict):
    if (author.get("works_count") or 0) == 0:
        return 0
    return (author.get("cited_by_count") or 0) / (author.get("works_count") or 0)

async def search_scholars(topic: str) -> list[str]:
    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=TIMEOUT,
    ) as client:
        authors = await top_authors_by_topic(client, topic, limit=25)

        filtered_authors = []
        for author in authors:
            author_data = await get_author(client, author['id'])
            if is_real_researcher(author_data):
                filtered_authors.append(author_data)
        
        filtered_authors.sort(key=rank_key, reverse=True)
        return [a["display_name"] for a in filtered_authors]
