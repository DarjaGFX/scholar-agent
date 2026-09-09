#!/usr/bin/env python3
"""eval_golden.py — measure the filter against the hand-labeled golden set.

Usage:  uv run python scripts/eval_golden.py

Re-hydrates every author in tests/data/golden_authors.csv, applies
is_real_researcher(), and prints the confusion matrix + precision/recall/F1
plus every disagreement (filter verdict vs human label).
"""
import asyncio
import csv
from pathlib import Path

import httpx

from scholar_agent.client import HEADERS
from scholar_agent.openalex import get_author
from scholar_agent.ranking import is_real_researcher

CSV_PATH = Path(__file__).resolve().parent.parent / "tests" / "data" / "golden_authors.csv"
TIMEOUT = 60.0


async def main():
    rows = list(csv.DictReader(CSV_PATH.open()))
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        tp = fp = fn = tn = 0
        disagreements = []
        for r in rows:
            rec = await get_author(client, r["author_id"])
            verdict = is_real_researcher(rec)  # True = KEEP
            label = r["label"]
            if label == "human" and verdict:
                tp += 1
            elif label == "not" and verdict:
                fp += 1
                disagreements.append((r["name"], "not→KEEP"))
            elif label == "human" and not verdict:
                fn += 1
                disagreements.append((r["name"], "human→DROP"))
            elif label == "not" and not verdict:
                tn += 1

        n = tp + fp + fn + tn
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        print(f"golden set: {n} labeled  (human: {tp + fn}, not: {fp + tn})")
        print(f"TP={tp}  FP={fp}  FN={fn}  TN={tn}")
        print(f"precision = {precision:.2%}   recall = {recall:.2%}   F1 = {f1:.2%}")
        if disagreements:
            print("\ndisagreements (filter vs human label):")
            for name, d in disagreements:
                print(f"  ✗ {name} — {d}")


if __name__ == "__main__":
    asyncio.run(main())
