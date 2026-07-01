# Team Research Assignment DB-Source Gap

Status: Task 3 is not feasible as a DB-source or CLI node yet.

## What Still Works

The pure team research assignment reducer remains usable when callers inject all
three source reports:

- `PaperStrategyCandidateResearchQueueReport`
- `TeamMarketRouteReport`
- `TeamMemoryReadinessDigestReport`

That path is still Phase 1 report composition. It does not require durable
route readback because the route report is already supplied by the caller.

## Covered Inputs

Two of the three required DB-source inputs already have local read paths:

- Queue input: `strategy_candidate_research_queue_psycopg_read.py` can read
  persisted `PaperStrategyCandidateResearchQueueReport` rows through the local
  Supabase/Postgres queue configuration.
- Memory readiness input: `team_memory_readiness_digest_db_source.py` can
  compose `TeamMemoryReadinessDigestReport` values from existing readonly
  diagnostics gate readback.

These cover the queue and memory-readiness sides of the reducer join.

## Missing Input

The missing input is local Supabase/Postgres route readback for
`team_market_routes`.

The repository already has the route persistence foundation:

- `TeamMarketRouteDbRow` and the `team_route_from_db_row` /
  `team_route_to_db_row` codec in `team_forecast_db_row.py`
- route insertion through `team_forecast_store.py`
- psycopg route insertion through `team_forecast_psycopg.py`
- route table configuration in `supabase_team_forecast_config.py`
- the `team_market_routes` table documented in
  `docs/team-forecast-supabase-runbook.md`

What does not exist yet is a readonly loader that reads rows from
`team_market_routes` and materializes `TeamMarketRouteReport` values through
`TeamMarketRouteDbRow` and `team_route_from_db_row`. There is also no durable
readback path for specialist route metadata that would let this assignment node
reconstruct corrected team routing from the database boundary.

## Required Future Node

Before enabling a team-research-assignment DB-source composer or CLI path, a
future node should add env-scoped local Supabase/Postgres route readback for
`team_market_routes`.

That route node should:

- read only from local Supabase/Postgres using the existing team forecast DB
  config surface;
- hydrate `TeamMarketRouteDbRow` records from database rows;
- recover `TeamMarketRouteReport` values with `team_route_from_db_row`;
- preserve route payload metadata, including corrected team routing when
  present;
- stay readonly and avoid connection, table, or DSN flags on the assignment
  CLI surface.

Once queue, route, and memory readiness loaders all exist, the assignment
DB-source composer can be a pure injectable join over those loaders and the
existing reducer.

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
