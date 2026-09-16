# evals/__main__.py
# Run with: uv run python -m evals
# Measures the retrieval pipeline (no LLM) against evals/golden_queries.py.
import asyncio
import time

from scholar_agent.client import client_scope
from scholar_agent.ranking import search_scholars
from evals.golden_queries import GOLDEN_QUERIES

DASHES = {"‐": "-", "‑": "-", "–": "-", "—": "-"}


def norm(name: str) -> str:
    """Normalize typographic dashes/whitespace so 'Tat‐Seng' == 'Tat-Seng'."""
    for k, v in DASHES.items():
        name = name.replace(k, v)
    return " ".join(name.split()).lower()


async def main():
    p5_total, lat_total = 0.0, 0.0
    async with client_scope(None) as client:
        for g in GOLDEN_QUERIES:
            t0 = time.time()
            records = await search_scholars(g["query"], client, limit=25)  # fetch 25 candidates...
            dt = time.time() - t0
            returned = [r["display_name"] for r in records[:5]]            # ...rank, then take top 5
            expected = {norm(n) for n in g["expected"]}
            hits = sorted(n for n in returned if norm(n) in expected)
            p5 = len(hits) / 5
            p5_total += p5
            lat_total += dt
            print(f"{g['query']:<32} p@5={p5:.2f}  {dt:>5.1f}s  n={len(returned)}")
            print(f"    hits     : {hits}")
            print(f"    returned : {returned}")

    n = len(GOLDEN_QUERIES)
    print(f"\nmean precision@5: {p5_total / n:.2%}   mean latency: {lat_total / n:.1f}s")
    print("(expected sets are non-exhaustive → precision@5 is a LOWER BOUND)")


asyncio.run(main())
