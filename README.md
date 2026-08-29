# Scholar Agent

A service that takes a plain-language research interest and returns a ranked
shortlist of **real academic researchers**, each with the citation metrics
that justify the match.

Built against [OpenAlex](https://openalex.org) — the open scholarly index
(~250M works, no API key required).

## The problem

Ranking authors by raw publication count returns garbage. The top authors for
"retrieval augmented generation" included:

| rank | author | works | citations |
|------|--------|-------|-----------|
| 1 | Daniel Rosehill | 7,869 | 12 |
| 2 | Chatterbox TTS | 7,780 | 12 |
| 3 | Gemini 3.1 (Flash) | 4,440 | 0 |
| 4 | Philip S. Yu | 144 | 140,132 |
| 5 | Ji-Rong Wen | 142 | 26,838 |

A text-to-speech model and a chatbot outranked two of the most cited
researchers in computer science. Anyone can call an API; the engineering is
deciding who is real.

## The solution

An entity filter and a citation-weighted ranking:

- **Citations-per-work ratio** — junk entities sit at 0.00, established
  researchers at 10–54. Threshold: 1.0.
- **h-index** — junk scores 0–1; threshold 2, established researchers 30+.
- **Impossible-shape guard** — thousands of "works" with near-zero citations
  is an aggregator artifact, not a person.
- **Institution type is NOT a filter** — industrial researchers (e.g. Adobe
  Research) are real people with h-indexes in the 30s.

The filter drops junk entirely — it returns nothing rather than a
plausible-looking entity. Every match in the response is backed by a real
OpenAlex record with real numbers.

## Measured results

A hand-labeled golden set of 43 authors across 3 topics (human / not):

```
precision = 100.00%   nothing non-human gets through
recall    = 97.37%    one thin-record human is missed, deliberately
F1        = 98.67%
```

The single miss — a real researcher with an unusual publication/citation
profile — was accepted on purpose. In this product a false positive (a fake
"professor" in the results) destroys trust, while a false negative costs
nothing visible.

## Architecture

```
plain-language query
        │
        ▼
  OpenAlex works, grouped by author       ← top candidates
        │  hydrate: full author records
        ▼
  entity filter  (is_real_researcher)
        │
        ▼
  citation-weighted ranking  (cites / works)
        │
        ▼
  ranked scholars + metrics   (FastAPI /search)
```

Tests use `pytest-recording` (VCR): real HTTP responses are recorded to
cassettes once, then replayed forever — deterministic, offline, CI-safe.

## Stack

| layer | tool |
|---|---|
| API | FastAPI + Uvicorn |
| HTTP | httpx (async, connection-pooled) |
| validation | Pydantic v2 |
| packaging | uv + pyproject.toml (hatchling) |
| tests | pytest, pytest-asyncio, pytest-recording |
| data | OpenAlex (free, no key) |

## Run it

```bash
uv sync
uv run uvicorn scholar_agent.main:app --reload
curl "localhost:8000/search?q=large%20language%20models"
```

```bash
uv run pytest -v        # offline — replays recorded cassettes
```

## Roadmap

- Query planner: plain text → structured search plan (LLM)
- Multi-tool agent: activity check, research-fit assessment
- Eval harness: precision@5 + latency across models
- Guardrail: explicit refusal when no grounded match exists
