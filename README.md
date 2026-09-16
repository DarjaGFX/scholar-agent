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

### The entity filter

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

### Retrieval quality, and three ranking strategies

Five queries with ground truth taken from the hand-labeled set
(`uv run python -m evals`):

```
mean precision@5 = 0.80     single live run; lower bound — expected sets are
mean latency     = 3.9s     non-exhaustive, so a correct researcher absent
                            from a set still counts as a miss
```

Three ranking strategies were measured against the same queries — and the
numbers chose:

| ranking key                          | mean precision@5 |
|--------------------------------------|------------------|
| `citations / works` (impact density) | 0.40 |
| `log(works) × ratio` (global hybrid) | 0.40 |
| `topic_count × log(citations)`       | **0.80** |

The first two failed for the same *structural* reason: they rank on global
lifetime metrics, while the query-specific signal — how many of an author's
works actually match the topic — was being discarded before the sort. No
arithmetic on lifetime totals can lift a low-resource NLP specialist above a
generalist with 2,665 lifetime papers. Carrying the topical signal through
nearly doubled precision.

### Model comparison (structured output)

Same five queries through the planner stage, driven by the environment
(`uv run python -m evals.models`; providers, keys and model lists come from
`LLM_PROVIDERS`, `<PROVIDER>_BASE_URL`, `<PROVIDER>_API_KEY`,
`<PROVIDER>_MODELS` — adding a provider is three lines of config, no code):

| arm | structured-output success | latency | tokens/query | notes |
|-----|---------------------------|---------|--------------|-------|
| `local` `qwen2.5:14b` | **5/5** | 11–33s | **137–142** | CPU inference, free |
| `zen` `nemotron-3.5-lightning-free` | **5/5** | 48–126s | 1162–2796 | free tier, reasoning-heavy |
| `zen` `nemotron-3-ultra-free` | 4/5 | 7–109s | 344–527 | 1 upstream server error |
| `zen` `big-pickle` | 1/5 | 4–10s | ~360 | 4/5 rate-limited (429) |

**The finding is the token column.** "Free" remote models are not free in
latency or verbosity: the local 14B produced the same valid structured plans in
**~140 tokens**, while the remote arms needed 340–2800 — 2.5× to 20× more —
and answered 4–10× slower (48–126 s/query). Success rates were comparable
(5/5 for two arms); the cost profile was not. A reasoning model that burns 20×
the tokens for identical output is a decision you can only make with numbers,
which is the entire point of owning this harness.

Every provider-access failure is documented rather than hidden, because an
evaluation that can't control its infrastructure ends up measuring the
infrastructure:

- **OpenRouter** — free tier allows **50 requests/day** (from `/api/v1/key`,
  reset 00:00 UTC); the eval consumed it in two runs.
- **agentrouter** — gateway returns `401 unauthorized client` to any client it
  hasn't allowlisted, regardless of key.
- **OpenCode Zen** — the free tier is **keyless**: it needs *no* `Authorization`
  header (an unrecognized bearer returns 401) and **requires** the relay's
  session-affinity header, `x-opencode-session`.

One bug the harness caught in the project's own code: the schema required
`countries: list[str]`, models legitimately emit `null`, and a single
`field_validator` fixed it across providers — a model-compatibility bug found by
measurement instead of by a user.





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
