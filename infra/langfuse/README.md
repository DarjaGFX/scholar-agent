# Langfuse self-hosted (scholar-agent observability)

```bash
docker compose up -d            # 6 services: web, worker, clickhouse, postgres, redis, minio
curl localhost:3000/api/public/health
```

UI: <http://localhost:3000> · API keys are minted in the UI and live in the
project `.env` as `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` /
`LANGFUSE_BASE_URL` (never committed — `.env` is gitignored at every depth).

## Local override, and why

`docker-compose.override.yml` differs from upstream in two deliberate ways:

1. **Port hygiene** — upstream publishes Postgres on `127.0.0.1:5432` and Redis
   on `127.0.0.1:6379`. They are internal to this stack and never need a host
   port; releasing them keeps those ports free for the project's own
   Postgres+pgvector (Phase 7) and Redis (Phase 10).
2. **Exposure** — upstream publishes the web UI on `0.0.0.0:3000` and MinIO on
   `0.0.0.0:9090`, reachable from the LAN. That UI mints project API keys and
   holds trace data, so both are bound to `127.0.0.1` only.

## The trap that cost us an evening: three S3 credential families

Langfuse archives raw event blobs in MinIO under `events/`. The compose defines
**three independent S3 configs**, each defaulting its secret to `miniosecret`:

```
LANGFUSE_S3_EVENT_UPLOAD_*      # raw span/event blobs — the one that breaks ingestion
LANGFUSE_S3_MEDIA_UPLOAD_*      # uploaded media
LANGFUSE_S3_BATCH_EXPORT_*      # batch exports (disabled by default)
```

Setting only the media family (the obvious one) leaves ingestion signing with the
default `miniosecret` while MinIO's root password is something else — every
export then fails with `The request signature we calculated does not match`
(the client sees a **500 on span export** and nothing reaches the UI). `.env`
therefore sets `ACCESS_KEY_ID`/`SECRET_ACCESS_KEY` for **all three families** to
the same generated credential as `MINIO_ROOT_*`.

Symptom → cause cheat sheet:

| symptom | cause |
|---|---|
| `Failed to upload JSON to S3 ... signature does not match` | one of the three S3 families has stale/default credentials |
| `401` on span export after setting a key | the OpenCode-style "keyless" trap does not apply here — but a *wrong* key never signs correctly |
| traces missing from the UI, nothing in `traces` table | v4 runs in **events-only mode**; read the UI or `events_core` in ClickHouse, not the legacy `/api/public/traces` API (404 by design) |

## Inspecting what actually landed

The v4 read API is disabled (`/api/public/traces` → 404 in events-only mode), so
verify in the store instead:

```bash
docker compose exec -T clickhouse sh -c \
  'clickhouse-client --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" \
   --database default --query "SELECT name, type, provided_model_name, usage_details \
   FROM events_core ORDER BY start_time DESC LIMIT 5 FORMAT Vertical"'
```

Root spans have `is_app_root = true`; a generation with `provided_model_name`
and `usage_details` populated is the proof that instrumentation attached its
metadata (`update_current_generation(...)`), not just its shape.

## Regenerating secrets

`infra/langfuse/.env` is generated locally (never committed). To start clean:
delete the file, recreate it from the table above with fresh values, and
`docker compose down -v && docker compose up -d` (the `-v` drops the volumes —
ClickHouse/Postgres/MinIO data included, so the UI account is re-created).
