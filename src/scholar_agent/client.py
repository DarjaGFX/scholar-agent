from contextlib import asynccontextmanager
import httpx


HEADERS = {"User-Agent": "scholar-agent (ali.jafari20@gmail.com)"}
TIMEOUT = 10


@asynccontextmanager
async def client_scope(client: httpx.AsyncClient | None):
    """Yield the caller's client if given; otherwise create one for this scope."""
    if client is not None:
        yield client
    else:
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as own:
            yield own