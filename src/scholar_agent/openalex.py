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


async def get_author(client, author_id) -> dict:
    r = await client.get(f"{OPENALEX}/authors/{author_id}")
    r.raise_for_status()
    return r.json()
