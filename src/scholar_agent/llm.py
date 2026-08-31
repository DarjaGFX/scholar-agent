from typing import Any
LLM_BASE = "http://127.0.0.1:11434"
MODEL = "qwen2.5:14b"

async def complete(client, messages, *, json_mode=False) -> str:
    # POST {LLM_BASE}/v1/chat/completions   (LLM_BASE = "http://127.0.0.1:11434")
    # model: "qwen2.5:14b", messages passed through, stream=False
    # if json_mode: response_format={"type": "json_object"}
    # return choices[0].message.content
    payload: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = await client.post(
        f"{LLM_BASE}/v1/chat/completions",
        json=payload,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
