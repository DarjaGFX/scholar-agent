import httpx
import asyncio
from scholar_agent.providers import resolve_default
from typing import Any
import os, uuid

_SESSION_ID = os.environ.get("LLM_SESSION_ID") or uuid.uuid4().hex

async def complete(client, messages, *, json_mode=False, tools=None, model=None, base_url=None, api_key=None, usage_out=None) -> dict:
    
    if base_url is None:
        d = resolve_default()
        base_url = d["base_url"]
        model = model or d["model"]
        api_key = ... or  d["api_key"]
    
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if "opencode.ai" in base_url:
        headers["x-opencode-session"] = _SESSION_ID
    
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    if tools:
        payload["tools"] = tools

    for attempt in range(3):
        try:
            response = await client.post(f"{base_url}/v1/chat/completions", json=payload, headers=headers)
        except httpx.ConnectError as e:
            if attempt == 2: raise
            await asyncio.sleep(2 ** attempt)
            continue
        if response.status_code == 429 and attempt < 2:
            await asyncio.sleep(float(response.headers.get("Retry-After", 2 ** attempt)))
            continue
        if response.status_code == 400 and json_mode and attempt < 2:
            print(f"Retrying without json mode because of: {response.text}")
            json_mode = False
            payload.pop("response_format", None)
            continue
        response.raise_for_status()
        break



    data = response.json()
    if "choices" not in data:
        raise RuntimeError(f"malformed completion response: {str(data)[:200]}")
    
    if usage_out is not None:
        for k, v in (data.get("usage") or {}).items():
            if isinstance(v, int):
                usage_out[k] = usage_out.get(k, 0) + v
    
    message = data["choices"][0]["message"]
    if message.get("content") is None:
        raise RuntimeError(f"empty completion content (model={model})")
    return message
