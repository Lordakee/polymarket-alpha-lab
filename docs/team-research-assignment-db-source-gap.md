# Team Research Assignment DB-Source Status

Status: closed by this DB-source/CLI node. The low-level `team_market_routes`
readback prerequisite is available through store and psycopg helpers, and this
node adds the explicit team research assignment DB-source composer and
`team-research-assignment` CLI path as an env-only local Supabase/Postgres
read-only composition.

If this documentation is read before the implementation branch has landed in a
given checkout, treat "this node adds" as the planned node behavior rather than
an instruction to use alternate storage or a different CLI surface.

## What Works

The pure team research assignment reducer remains usable when callers inject all
three source reports: `PaperStrategyCandidateResearchQueueReport`,
`TeamMarketRouteReport`, and `TeamMemoryReadinessDigestReport`.

That path is still Phase 1 report composition. It does not require durable
route readback because the route report is already supplied by the caller.

This node also adds the DB-source/CLI composition that loads those same typed
inputs from existing local Supabase/Postgres read paths, merges persisted
one-row route reports into one `TeamMarketRouteReport`, and feeds the existing
assignment reducer. The composition is read-only and report-only; it does not
create assignment rows, write report history, repair source data, or refresh
upstream tables.

The DB-source requires exactly one queue report and at least one route report.
Each persisted route report must contain exactly one route row. Duplicate route
market slugs fail. Empty route readback is a fail-closed source error; it is not
converted into an empty assignment report.

## Covered Inputs

All three required DB-source inputs are covered by existing local read paths:

- Queue input: `strategy_candidate_research_queue_psycopg_read.py` can read
  persisted `PaperStrategyCandidateResearchQueueReport` rows through the local
  Supabase/Postgres queue configuration.
- Route input: the team forecast route readback helpers can read persisted
  `team_market_routes` rows and restore `TeamMarketRouteReport` values.
- Memory readiness input: `team_memory_readiness_digest_db_source.py` can
  compose `TeamMemoryReadinessDigestReport` values from existing readonly
  diagnostics gate readback over diagnostics snapshots.

The route persistence foundation is:

- `TeamMarketRouteDbRow` and the `team_route_from_db_row` /
  `team_route_to_db_row` codec in `team_forecast_db_row.py`
- route insertion through `team_forecast_store.py`
- psycopg route insertion through `team_forecast_psycopg.py`
- DB-API route readback through `load_team_market_routes` and
  `load_team_market_route_rows`
- psycopg route readback through `load_team_market_routes_with_psycopg` and
  `load_team_market_route_rows_with_psycopg`
- route table configuration in `supabase_team_forecast_config.py`
- the `team_market_routes` table documented in
  `docs/team-forecast-supabase-runbook.md`

The assignment DB-source consumes hydrated route reports from that readback
surface. It does not recompute routes in the DB-source path or treat generated
fixtures as persisted readback.

## Env-Only CLI Composition

The CLI command is:

```bash
polymarket-alpha-lab team-research-assignment \
  --team-id crypto_btc \
  --queue-limit 1 \
  --route-limit 25 \
  --memory-limit 100
```

The command reads DB configuration only from existing env config modules. It has
report selectors and limits, but no DB connection or table flags. It fails
closed before source loading if the queue DB, team forecast route DB, or
diagnostics snapshot DB is disabled or lacks a DSN. Positive CLI limits are
validated before env reads.

Queue report env family:

- `POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN`
- `POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE`

Team route env family:

- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN`
- `POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE`

The broader team forecast env config also owns team profile, forecast,
forecast-evidence, and forecast-outcome table names, but this assignment path
uses only the persisted route readback surface.

Team-memory readiness env family:

- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN`
- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE`

Allowed CLI options are report-scoped:

- `--team-id`
- `--queue-source-config-version`
- `--memory-config-version`
- `--queue-limit`
- `--route-limit`
- `--memory-limit`

The CLI defaults are queue limit `1`, route limit `500`, and memory limit
`100`. If `--team-id` is omitted, the command selects all known teams. There is
no generic assignment `--config-version`, `--market-slug`, or `--forecast-id`
option.

Forbidden CLI options remain forbidden:

- `--dsn`
- `--table`
- `--persist`
- `--live`
- `--auth`
- `--wallet`
- `--private-key`
- `--api-key`
- `--account`
- `--order`
- `--trade`
- `--execute`
- `--submit`

After the env gates pass, source/runner errors are redacted and should not
print DSNs, hostnames, table names, market slugs, market questions, raw filters,
payloads, report hashes, credentials, wallet/account/auth/key material, or
order-like details. Argparse usage errors and env-gate failures are fail-closed
validation surfaces; do not treat rejected CLI flags as a secret transport.

## Explicit Non-Substitutes

Do not fill this gap with SQLite, Redis, Mongo, SQLAlchemy, hosted database
assumptions, local files, generated fixtures, or any other durable substitute.
Do not recompute routes in the DB-source path and treat them as persisted
readback.

## Phase 1 Boundary

This remains a `paper_only=True`, `report_only=True`, `readonly=True` report
surface. It must not add live trading, authentication, wallet or account reads,
key-material handling, order signing, order submission, cancellation,
replacement, exchange mutation, investment recommendations, trade instructions,
strategy weighting, or position sizing.
