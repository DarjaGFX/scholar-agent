import asyncio
import httpx
from scholar_agent.openalex import top_authors_by_topic, get_author

HEADERS = {"User-Agent": "scholar-agent (ali.jafari20@gmail.com)"}
TIMEOUT = 10

MIN_CITES_PER_WORK = 1.0
MIN_H_INDEX = 2
MAX_WORKS_WITHOUT_CITES = 3_000


def is_real_researcher(author: dict) -> bool:

    works_count = author.get("works_count") or 0
    cited_by_count = author.get("cited_by_count") or 0
    h_index = (author.get("summary_stats") or {}).get("h_index") or 0

    if works_count == 0:
        return False
    if works_count > MAX_WORKS_WITHOUT_CITES and cited_by_count < MIN_CITES_PER_WORK:
        return False
    if h_index < MIN_H_INDEX:
        return False
    if cited_by_count / works_count < MIN_CITES_PER_WORK:
        return False
    return True

def rank_key(author: dict):
    if (author.get("works_count") or 0) == 0:
        return 0
    return (author.get("cited_by_count") or 0) / (author.get("works_count") or 0)

async def search_scholars(topic: str, client: httpx.AsyncClient | None = None) -> list[dict]:
    """
    Search for top scholars for a given topic and return their details.
    
    The output is a list of dictionaries where each dictionary contains author information 
    from OpenAlex.
    
    Example output structure for a single author:
    {
        'id': 'https://openalex.org/A5036357902',
        'orcid': 'https://orcid.org/0000-0002-3491-5968',
        'display_name': 'Philip S. Yu',
        'raw_author_names': ['P S Yu', 'P. S. Yu', 'Philip S. Yu', ...],
        'full_name': 'PHILIP S. YU',
        'works_count': 2665,
        'cited_by_count': 140218,
        'summary_stats': {
            '2yr_mean_citedness': 15.126948775055679,
            'h_index': 169,
            'i10_index': 1293
        },
        'ids': {
            'openalex': 'https://openalex.org/A5036357902',
            'orcid': 'https://orcid.org/0000-0002-3491-5968'
        },
        'affiliations': [
            {
                'institution': {
                    'id': 'https://openalex.org/I103635307',
                    'ror': 'https://ror.org/03nawhv43',
                    'display_name': 'University of California, Riverside',
                    'country_code': 'US',
                    'type': 'education'
                },
                'years': [2007]
            },
            ...
        ],
        'last_known_institutions': [...],
        'topics': [...],
        'topic_share': [...],
        'x_concepts': [...],
        'counts_by_year': [...],
        'works_api_url': 'https://api.openalex.org/works?filter=author.id:A5036357902',
        'updated_date': '2026-08-26T12:17:03',
        'created_date': '2016-06-24T00:00:00',
        ...
    }
    """

    async def _search_scholars(client: httpx.AsyncClient) -> list[str]:
        authors = await top_authors_by_topic(client, topic, limit=25)
        filtered_authors = []
        for author in authors:
            author_data = await get_author(client, author['id'])
            if is_real_researcher(author_data):
                filtered_authors.append(author_data)
        
        filtered_authors.sort(key=rank_key, reverse=True)
        return filtered_authors

    if client is not None:
        return await _search_scholars(client)
    else:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=TIMEOUT,
        ) as client:
            return await _search_scholars(client)
