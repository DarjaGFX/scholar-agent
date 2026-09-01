from scholar_agent.openalex import recent_works_count, get_author_topics
from scholar_agent.ranking import search_scholars


async def find_scholars(client, topic: str, limit: int = 5) -> list[dict]:
    """Ranked real researchers for a topic, with metrics AND author id
    (id matters: later tools need it to chain)."""
    # wrap search_scholars(topic, client) — records already have "id"
    records = await search_scholars(topic, client, limit)
    return [{
        "id": r.get("id"),
        "name": r.get("display_name"),
        "works_count": r.get("works_count"),
        "cited_by_count": r.get("cited_by_count"),
        "h_index": (r.get("summary_stats") or {}).get("h_index"),
    } for r in records]


FIND_SCHOLARS = {
    "type": "function",
    "function": {
        "name": "find_scholars",
        "description": "Find real academic supervisors for a research topic. Returns ranked candidates with citation metrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["topic"],
        },
    },
}


async def check_activity(client, author_id) -> dict:
    n = await recent_works_count(client, author_id)
    return {"author_id": author_id, "recent_works_since_2023": n, "active": n > 0}


CHECK_ACTIVITY = {
    "type": "function",
    "function": {
        "name": "check_activity",
        "description": "Check whether an author is still publishing actively. Returns the number of works since 2023.",
        "parameters": {
            "type": "object",
            "properties": {
                "author_id": {"type": "string", "description": "OpenAlex author id, e.g. 'https://openalex.org/A5036357902'"},
            },
            "required": ["author_id"],
        },
    },
}


async def assess_fit(client, author_id) -> dict:
    return {"author_id": author_id, "top_topics": await get_author_topics(client, author_id)}

ASSESS_FIT = {
    "type": "function",
    "function": {
        "name": "assess_fit",
        "description": "Get an author's top research topics (with relevance scores) to judge how well they fit a research interest.",
        "parameters": {
            "type": "object",
            "properties": {
                "author_id": {"type": "string"},
            },
            "required": ["author_id"],
        },
    },
}