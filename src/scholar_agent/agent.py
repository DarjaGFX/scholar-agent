import json
import unicodedata
import httpx

from scholar_agent.tools import (
    FIND_SCHOLARS,
    find_scholars,
    CHECK_ACTIVITY,
    check_activity,
    assess_fit,
    ASSESS_FIT
)
from scholar_agent.llm import complete

SYSTEM_PROMPT = (
    "You are a research-advisor agent. Never invent researchers or numbers; "
    "use the tools. Answer in English, concisely (under 120 words)."
)
TOOL_REGISTRY = {"find_scholars": find_scholars, "check_activity": check_activity, "assess_fit": assess_fit}
TOOL_SCHEMAS = [FIND_SCHOLARS, CHECK_ACTIVITY, ASSESS_FIT]

def mostly_latin(text: str) -> bool:
    """True if the answer is predominantly Latin-script.
    Allows names with diacritics (Ø, ü, é — all LATIN block) —
    only flags answers written mostly in another script."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    latin = sum(1 for c in letters if unicodedata.name(c, "").startswith("LATIN"))
    return latin / len(letters) >= 0.5

async def run_agent(query: str, client, max_steps: int = 5, trace: list=None) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    for _ in range(max_steps):
        for attempt in range(2):
            try:
                msg = await complete(client, messages, tools=TOOL_SCHEMAS)
                break
            except httpx.HTTPError:
                if attempt == 1:
                    raise
        
        if msg.get("content") and not mostly_latin(msg["content"]):
            messages.append({"role": "user", "content": "Your previous answer was not in English. Answer again in English only, under 120 words."})
            continue
        
        if not msg.get("tool_calls"):
            return msg.get("content") or ""
        
        for call in msg["tool_calls"]:
            fn = call["function"]
            args = json.loads(fn["arguments"] or "{}")
            if trace is not None:
                trace.append({"name": fn["name"], "args": args})
            try:
                result = await TOOL_REGISTRY[fn["name"]](client, **args)
                if trace is not None:
                    trace[-1]["ok"] = True
                content = json.dumps(result, ensure_ascii=False, default=str)
            except Exception as e:
                content = f"tool error: {type(e).__name__}: {e}"
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": content})
    
    return "Reached max steps without a final answer."