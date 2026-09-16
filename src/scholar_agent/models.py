from pydantic import BaseModel
from pydantic import field_validator

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
    topics: list[str]
    countries: list[str]
    min_year: int | None
    supervisor_rank: str | None
    degree_level: str | None

    @field_validator("topics", "countries", mode="before")
    @classmethod
    def _null_to_empty(cls, v):
        return v if v is not None else []
