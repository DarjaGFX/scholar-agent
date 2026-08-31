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

class SearchPlan(BaseModel):
    topics: list[str]        # research topics extracted from the query
    countries: list[str]     # preferred regions/countries ("Europe" is fine)
    min_year: int | None     # recency constraint, null if unspecified
    supervisor_rank: str | None    # seniority of the supervisor, e.g. assistant/full professor; null if unspecified
    degree_level: str | None       # level of study the USER seeks: "masters", "phd", "postdoc"; null if unspecified