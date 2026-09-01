from pydantic import ValidationError
from scholar_agent.models import SearchPlan
from scholar_agent.llm import complete
from httpx import AsyncClient

def plan_prompt(query: str) -> str:
    return f"""You are a research-search planner. NEVER GUESS ANYTHING. IF ANYTHING IS NOT IN THE QUERY, RETURN NULL FOR IT. Reply with JSON matching this schema:
        {{topics: [str], countries: [str], min_year: int|null, supervisor_rank: str|null, degree_level: str|null}}
        Query: {query}"""

async def plan_search(client: AsyncClient , query: str) -> SearchPlan:
    try:
        msg = await complete(client, messages=[{"role": "user", "content": plan_prompt(query)}], json_mode=True)
        return SearchPlan.model_validate_json(msg["content"])
    except ValidationError as e:
        messages=[{"role": "user", "content": plan_prompt(query) + "\nReturned JSON was invalid: " + str(e.errors())[:400] + "\nPlease return valid JSON."}]
        msg = await complete(client, messages=messages, json_mode=True)
        return SearchPlan.model_validate_json(msg["content"])
