from math import log
from scholar_agent.client import client_scope
import asyncio
import httpx
from scholar_agent.openalex import top_authors_by_topic, get_author


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
    topic_count = author.get("topic_count") or 0
    # works_count = author.get("works_count") or 0
    cited_by_count = author.get("cited_by_count") or 0
    return (topic_count * log(cited_by_count + 2))

async def search_scholars(topic: str, client: httpx.AsyncClient | None = None, limit: int = 25) -> list[dict]:
    """
    Search for top scholars for a given topic and return their details.
    
    The output is a list of dictionaries where each dictionary contains author information 
    from OpenAlex.
    """

    async with client_scope(client) as client:
        authors = await top_authors_by_topic(client, topic, limit=limit)
        topic_count = {a["id"]: a["count"] for a in authors}
        sem = asyncio.Semaphore(5)
        async def get_one(a):
            async with sem:
                return await get_author(client, a["id"])

        hydrated = await asyncio.gather(*(get_one(a) for a in authors))
        filtered = [r for r in hydrated if is_real_researcher(r)]
        for r in filtered:
            short = (r.get("id") or "").split("/")[-1]
            r["topic_count"] = topic_count.get(short, 0)

        return sorted(filtered, key=rank_key, reverse=True)
