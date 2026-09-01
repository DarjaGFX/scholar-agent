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