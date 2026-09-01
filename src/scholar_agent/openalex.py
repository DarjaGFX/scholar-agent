import httpx
OPENALEX = "https://api.openalex.org"


async def top_authors_by_topic(client, topic, limit=25) -> list[dict]:
    r = await client.get(
        f"{OPENALEX}/works",
        params={
            "filter": f"default.search:{topic}",
            "group_by": "authorships.author.id",
            "per-page": limit,
        },
    )
    r.raise_for_status()
    group = r.json().get("group_by", [])
    authors = []
    for author in group:
        authors.append({
            "id": (author.get("key") or "").split("/")[-1] or None,
            "name": author.get("key_display_name") or None,
            "count": author.get("count") or 0
        })
    return authors


async def get_author(client: httpx.AsyncClient, author_id: str) -> dict:
    r = await client.get(f"{OPENALEX}/authors/{author_id}")
    r.raise_for_status()
    return r.json()


async def recent_works_count(client, author_id, since="2023-01-01") -> int:
    author_id = author_id.split("/")[-1]
    r = await client.get(
        f"{OPENALEX}/works",
        params={
            "filter": f"author.id:{author_id},from_publication_date:{since}",
            "per-page": 1,
        },
    )
    r.raise_for_status()
    return r.json()["meta"]["count"]


async def get_author_topics(client, author_id) -> list[dict]:
    author_id = author_id.split("/")[-1]
    r = await client.get(
        f"{OPENALEX}/authors/{author_id}",
        params={"select": "id,display_name,topics"},
    )
    r.raise_for_status()
    topics = r.json().get("topics") or []
    return [{"topic": t.get("display_name"), "score": t.get("score")} for t in topics[:5]]