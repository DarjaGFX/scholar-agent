from pydantic import BaseModel

class Scholar(BaseModel):
    name: str
    works_count: int = 0
    cited_by_count: int = 0
    h_index: int = 0
    citations_per_work: float = 0.0

class SearchResponse(BaseModel):
    query: str
    count: int
    scholars: list[Scholar]
