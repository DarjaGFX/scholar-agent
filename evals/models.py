from dotenv import load_dotenv
load_dotenv()

import asyncio, time, httpx
from src.scholar_agent.providers import arms
from scholar_agent.planner import plan_search
from evals.golden_queries import GOLDEN_QUERIES


async def run_arm(arm):
    headers = {"Authorization": f"Bearer {arm['api_key']}"} if arm.get("api_key") else {}
    rows = []
    async with httpx.AsyncClient(headers=headers, timeout=300) as client:
        for g in GOLDEN_QUERIES:
            usage = {}
            t0 = time.time()
            try:
                plan = await plan_search(client, g["query"], model=arm["model"],
                                         base_url=arm["base_url"], usage_out=usage)
                rows.append((g["query"], True, time.time() - t0, usage.get("total_tokens"), None))
            except Exception as e:
                rows.append((g["query"], False, time.time() - t0, usage.get("total_tokens"),
                             f"{type(e).__name__}: {str(e)[:120]}"))
    return rows

async def main():
    for arm in arms():
        rows = await run_arm(arm)
        ok = sum(1 for r in rows if r[1])
        print(f"\narm: {arm['label']}   ({ok}/{len(rows)} ok)")
        for query, success, dt, tokens, err in rows:
            print(f"  {query:<34} {'✓' if success else '✗'}  {dt:>7.1f}s  tokens={tokens}  {err or ''}")

asyncio.run(main())
