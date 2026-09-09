#!/usr/bin/env python3
"""label_golden.py — build the golden set: hand-label authors human/not/unsure.

Usage:  uv run python scripts/label_golden.py

For each candidate author it shows the SAME signals the filter uses
(works, cites, ratio, h-index, orcid, institution) plus a link to check.
Labels are appended to tests/data/golden_authors.csv after every answer,
so Ctrl+C loses nothing and re-running resumes where you stopped.
"""
import asyncio
import csv
import sys
from pathlib import Path

import httpx

from scholar_agent.client import HEADERS, TIMEOUT
from scholar_agent.openalex import top_authors_by_topic, get_author
from scholar_agent.ranking import is_real_researcher

TOPICS = [
    "retrieval augmented generation",
    "machine translation",
    "protein structure prediction",
]
PER_TOPIC = 15
LABEL_TIMEOUT = 60.0  # OpenAlex group_by queries can take 5-10s on their side
CSV_PATH = Path(__file__).resolve().parent.parent / "tests" / "data" / "golden_authors.csv"
LABELS = {"h": "human", "n": "not", "u": "unsure"}

GUIDE = """
HOW TO JUDGE  (the decision procedure)
  n  — name is a product / model / company-as-author
       (Chatterbox TTS, Gemini 3.1, Assignee Research)
  n  — thousands of works with near-zero citations
       (aggregator/scraper artifact — no human writes 7,000 papers)
  h  — real person: sane works/cites shape, h >= 2, orcid present
  h  — industrial researcher at a research lab (Adobe Research, Google
       Research) — institution type 'company' is NOT disqualifying
  u  — genuinely uncertain. No penalty for using it.
  s  — skip this row entirely.
Hard cases: open https://openalex.org/<id> in a browser and look.

The filter's verdict is shown on each card as a SUGGESTION only.
YOUR label is the ground truth. Disagreements are the measurement —
that is exactly what precision/recall will quantify in step 1.8.
"""


def load_done():
    if not CSV_PATH.exists():
        return set()
    with CSV_PATH.open() as f:
        return {row["author_id"] for row in csv.DictReader(f)}


def show_card(i, total, name, a):
    works = a.get("works_count") or 0
    cites = a.get("cited_by_count") or 0
    ratio = cites / works if works else 0.0
    h = (a.get("summary_stats") or {}).get("h_index") or 0
    orcid = a.get("orcid")
    insts = a.get("last_known_institutions") or []
    inst = insts[0] if insts else {}
    verdict = "KEEP" if is_real_researcher(a) else "DROP"
    print(f"\n[{i}/{total}] {name}   (id: {a.get('id')})")
    print(f"  works={works}  cites={cites}  ratio={ratio:.2f}  h={h}")
    print(f"  orcid={orcid or 'NO'}   inst_type={inst.get('type') or '?'}   inst={inst.get('display_name') or '?'}")
    print(f"  filter says: {verdict}   (your label is the truth — disagree freely)")
    print(f"  check: https://openalex.org/{a.get('id')}")


async def fetch_candidates(client):
    seen = {}
    for topic in TOPICS:
        try:
            top = await top_authors_by_topic(client, topic, limit=PER_TOPIC)
        except Exception as e:
            print(f"  ! topic failed ({topic!r}): {type(e).__name__}: {e}", file=sys.stderr)
            continue
        for cand in top:
            if cand["id"] and cand["id"] not in seen:
                seen[cand["id"]] = {**cand, "topic": topic}
    return list(seen.values())


async def main():
    print(GUIDE)
    done = load_done()
    async with httpx.AsyncClient(headers=HEADERS, timeout=LABEL_TIMEOUT) as client:
        candidates = await fetch_candidates(client)
        remaining = [c for c in candidates if c["id"] not in done]
        print(f"candidates: {len(candidates)}   already labeled: {len(candidates) - len(remaining)}   to do: {len(remaining)}")
        if not remaining:
            print("all labeled — done!")
            return

        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        first_write = not CSV_PATH.exists()
        f = open(CSV_PATH, "a", newline="")
        writer = csv.DictWriter(f, fieldnames=["author_id", "name", "topic", "label", "note"])
        if first_write:
            writer.writeheader()

        for i, a in enumerate(remaining, 1):
            try:
                rec = await get_author(client, a["id"])
                rec["id"] = a["id"]
            except Exception as e:
                print(f"  ! hydrate failed ({a['name']}): {type(e).__name__}: {e}", file=sys.stderr)
                continue
            show_card(i, len(remaining), a["name"], rec)
            while True:
                try:
                    ans = input("  [h]uman / [n]ot / [u]nsure / [s]kip: ").strip().lower()
                except EOFError:
                    f.close()
                    print(f"\nstopped early — everything labeled so far is saved to {CSV_PATH}")
                    return
                if ans == "s":
                    break
                if ans in LABELS:
                    writer.writerow({
                        "author_id": a["id"],
                        "name": a["name"],
                        "topic": a["topic"],
                        "label": LABELS[ans],
                        "note": "",
                    })
                    f.flush()
                    break
                print("  ?  h / n / u / s")
        f.close()
        print(f"\nsaved to {CSV_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
