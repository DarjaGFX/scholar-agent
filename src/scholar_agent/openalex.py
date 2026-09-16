from typing import Any
import httpx
import asyncio

OPENALEX = "https://api.openalex.org"


async def get_json(client, url, params=None, retries=3) -> dict[Any, Any] | Any:
    """GET with retry/backoff. 429 is expected under load; honor Retry-After."""
    for attempt in range(retries):
        r = await client.get(url, params=params)
        if r.status_code == 429 and attempt < retries - 1:
            wait = float(r.headers.get("Retry-After", 2 ** attempt))
            await asyncio.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


async def top_authors_by_topic(client, topic, limit=25) -> list[dict]:
    data = await get_json(
        client,
        f"{OPENALEX}/works",
        params={
            "filter": f"default.search:{topic}",
            "group_by": "authorships.author.id",
            "per-page": limit,
        },
    )
    group = data.get("group_by", [])
    authors = []
    for author in group:
        authors.append({
            "id": (author.get("key") or "").split("/")[-1] or None,
            "name": author.get("key_display_name") or None,
            "count": author.get("count") or 0
        })
    return authors


async def get_author(client: httpx.AsyncClient, author_id: str) -> dict:
    return await get_json(client, f"{OPENALEX}/authors/{author_id}")


async def recent_works_count(client, author_id, since="2023-01-01") -> int:
    author_id = author_id.split("/")[-1]
    data = await get_json(
        client,
        f"{OPENALEX}/works",
        params={
            "filter": f"author.id:{author_id},from_publication_date:{since}",
            "per-page": 1,
        },
    )
    return data.get("meta", {}).get("count", 0)


async def get_author_topics(client, author_id) -> list[dict]:
    author_id = author_id.split("/")[-1]
    data = await get_json(
        client,
        f"{OPENALEX}/authors/{author_id}",
        params={"select": "id,display_name,topics"},
    )
    topics = data.get("topics") or []
    return [{"topic": t.get("display_name"), "score": t.get("score")} for t in topics[:5]]
