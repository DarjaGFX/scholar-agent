"""Reconnaissance: look at real OpenAlex author data before designing the filter.

Throwaway script. Its only job is to make the junk-entity problem visible so the
filter can be designed from evidence instead of from guesses.

The real client and filter belong in the package (Phase 1) — not here.
"""

import asyncio

import httpx

OPENALEX = "https://api.openalex.org"

# OpenAlex runs a "polite pool": requests that identify themselves with a
# reachable email get better rate limits and lower latency. Anonymous traffic
# gets throttled. Most free APIs have some version of this.
HEADERS = {"User-Agent": "scholar-agent (ali.jafari20@gmail.com)"}

TOPIC = "retrieval augmented generation"
TOP_N = 12  # deliberately >10: row 10 has a missing institution, which is the
# messy case the filter has to survive


async def candidate_authors(client: httpx.AsyncClient, topic: str, n: int) -> list[dict]:
    """Call 1 — topic to candidate authors.

    `group_by` makes OpenAlex aggregate instead of returning documents, so one
    request gives us authors ranked by how many matching works they have.
    This is the ranking that produces garbage.
    """
    r = await client.get(
        f"{OPENALEX}/works",
        params={
            "filter": f"default.search:{topic}",
            "group_by": "authorships.author.id",
            "per-page": 25,
        },
    )
    r.raise_for_status()  # turn HTTP errors into exceptions instead of silent bad data
    return r.json().get("group_by", [])[:n]


async def author_detail(client: httpx.AsyncClient, author_id: str) -> dict:
    """Call 2 — hydrate one author record by ID."""
    r = await client.get(f"{OPENALEX}/authors/{author_id}")
    r.raise_for_status()
    return r.json()


def summarise(author: dict) -> dict:
    """Pull out the candidate filter signals, defensively.

    Every `or {}` / `or []` here is a real case in the live data: OpenAlex
    returns null for missing sub-objects, so `.get('x').get('y')` crashes.
    """
    stats = author.get("summary_stats") or {}
    insts = author.get("last_known_institutions") or []
    inst = insts[0] if insts else {}

    works = author.get("works_count") or 0
    cites = author.get("cited_by_count") or 0

    return {
        "name": author.get("display_name") or "?",
        "works": works,
        "cites": cites,
        "h_index": stats.get("h_index") or 0,
        "orcid": bool(author.get("orcid")),
        # citations per work — the sharpest single discriminator so far
        "ratio": (cites / works) if works else 0.0,
        "inst": inst.get("display_name") or "NONE",
        "inst_type": inst.get("type") or "NONE",
    }


async def main() -> None:
    # ONE client for all requests: it holds a connection pool and reuses
    # TCP/TLS connections. A client per request throws that away and gets you
    # rate-limited. Headers go in the constructor, not mutated afterwards.
    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        groups = await candidate_authors(client, TOPIC, TOP_N)

        # --- Call 1 output: the naive ranking, exactly as OpenAlex returns it ---
        print(f'TOP {len(groups)} "authors" for: {TOPIC}')
        print("(ranked by matching work count — the WRONG ranking)\n")
        for n, g in enumerate(groups, 1):
            print(f"  {n:>2}. {g['count']:>4} works   {g['key_display_name']}")

        # --- Call 2 output: hydrate each one and show the discriminating fields ---
        print("\n\nHYDRATED AUTHOR RECORDS")
        print(f"{'#':<4}{'name':<27}{'works':>7}{'cites':>9}{'h':>5}"
              f"{'orcid':>7}{'ratio':>8}   institution type")
        print("-" * 86)

        for n, g in enumerate(groups, 1):
            author_id = g["key"].rsplit("/", 1)[-1]
            detail = await author_detail(client, author_id)
            s = summarise(detail)
            print(
                f"{n:<4}{s['name'][:26]:<27}{s['works']:>7}{s['cites']:>9}"
                f"{s['h_index']:>5}{'yes' if s['orcid'] else 'NO':>7}"
                f"{s['ratio']:>8.2f}   {s['inst_type']}"
            )


if __name__ == "__main__":
    asyncio.run(main())
