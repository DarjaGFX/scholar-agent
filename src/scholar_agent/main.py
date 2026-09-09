from scholar_agent.models import Scholar
from scholar_agent.models import SearchResponse
from fastapi import HTTPException
from scholar_agent.ranking import search_scholars
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from scholar_agent.client import HEADERS
import httpx
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(headers=HEADERS, timeout=30)
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

def get_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.client

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/search")
async def search(
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
    q: str = Query(min_length=1)
) -> SearchResponse:
    try:
        scholars = await search_scholars(q, client)
        for scholar in scholars:
            works = scholar.get("works_count") or 0
            cites = scholar.get("cited_by_count") or 0
            scholar["citations_per_work"]=cites / works if works else 0.0
        return SearchResponse(
            query=q,
            count=len(scholars),
            scholars=[
                Scholar(
                    name=scholar.get('display_name'),
                    works_count=scholar.get('works_count'),
                    cited_by_count=scholar.get('cited_by_count'),
                    h_index=(scholar.get('summary_stats') or {}).get('h_index'),
                    citations_per_work=scholar.get('citations_per_work')
                )
                for scholar in scholars
            ]
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="upstream unavailable")