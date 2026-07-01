# Team Diagnostics Read-Only Runbook

Purpose: team diagnostics evaluate stored Team Forecast data so operators can review team behavior without touching any exchange surface. The diagnostics flow reads local rows for team routes, forecasts, evidence, and outcomes, then reports on team memory, calibration, event template performance, source reliability, and evidence quality.

This runbook is documentation for the read path only. It does not define a live strategy, an execution path, or a persistence alternative.

## Phase 1 Boundary

The diagnostics flow is read-only/report-only/paper-only.

Do not add or route any of the following through diagnostics:

- No live trading.
- No auth flow.
- No wallet access.
- No private-key handling.
- No account reads.
- No order signing.
- No order submission.
- No order cancellation.
- No order replacement.
- No exchange mutation.
- No database mutation from the baseline diagnostics read path.

The only allowed inputs are already-persisted local database rows plus command-line filters such as team id and limit. The baseline diagnostics command output is a local report or terminal summary. Snapshot persistence is allowed only for the planned internal report persistence path, and only as paper-only/report-only/readonly rows in local Supabase/Postgres.

## Data Source

Use local Supabase/Postgres only. Durable project data for this flow must stay in the local Supabase/Postgres database and must not be moved to SQLite, Redis, Mongo, SQLAlchemy-managed durable engines, file-journal storage, JSONL state files, or any other durable substitute.

Diagnostics read from these Team Forecast tables:

- `team_profiles`: team definitions and static metadata.
- `team_market_routes`: team assignment, market slug, condition id, category, event template, and routing confidence.
- `team_forecasts`: generated team forecasts, selected side, forecast probability, confidence, and forecast payload.
- `team_forecast_evidence`: source evidence used by a team forecast, including source id, evidence type, freshness, weight, and payload.
- `team_forecast_outcomes`: resolved forecast outcomes, errors, Brier score, paper PnL fields, cost-adjusted return, and dispute flags.

Diagnostics should treat rows with `paper_only`, `report_only`, and `readonly` markers as the canonical Phase 1 record shape. A diagnostics report should surface missing or unexpected markers as data-quality findings, not as a reason to repair rows in place.

## Snapshot Persistence

`team_diagnostics_snapshots` is the planned local Supabase/Postgres table for compact diagnostics snapshot history. It is internal report persistence, not a live strategy, not an exchange integration, and not a path for changing Team Forecast source rows.

The table stores one generated snapshot per `report_sha256`, with generated/filter fields (`generated_at`, `team_id`, `market_slug`, `forecast_id`), source counts, compact diagnostics fields for memory, calibration, event template performance, source reliability, evidence quality, `reason_codes_json`, the canonical `payload_json`, hard Phase 1 flags, and `inserted_at`.

The snapshot DB env surface is separate from the Team Forecast read-source env surface:

- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN`
- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE`

Default table name:

- `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE` -> `team_diagnostics_snapshots`

`POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN` must point to the same local Supabase/Postgres class of database accepted by `validate_local_postgres_dsn`. Keep the DSN in operator-managed environment injection; do not commit it and do not print it in reports or error output.

## Snapshot History Readback

Read persisted local Supabase/Postgres diagnostics snapshot history with the env-driven readback command:

```bash
polymarket-alpha-lab team-diagnostics-snapshot-history --limit 100
```

The command reads already-persisted `team_diagnostics_snapshots` rows from the local Supabase/Postgres snapshot table configured by `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED`, `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN`, and `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE`. Configuration stays in environment variables; there are no DSN/table CLI flags.

Use this readback to inspect long-term team-memory deltas from persisted diagnostics snapshots. The history report compares earliest and latest snapshot rows, then prints the observed status mix plus long-term deltas for evidence quality, memory-eligible references, and settled calibration coverage. It remains Phase 1 paper-only/report-only/readonly: no live trading, no auth, no wallet, no account access, no order path, and no mutation of Team Forecast or snapshot rows.

Sample output fields:

```text
team-diagnostics-snapshot-history: status=observed snapshot_count=12 required_snapshot_count=2 earliest_generated_at=2026-07-01T08:30:00+00:00 latest_generated_at=2026-07-01T09:45:15+00:00 span_seconds=4515 status_counts=pass:7,watch:5 evidence_quality_average_delta=0.125 memory_eligible_delta=4 settled_calibration_delta=3 duplicate_latest_generated_at=False reason_codes=none paper_only=True report_only=True readonly=True
```

## What Diagnostics Evaluate

Team memory:

- Compare recent forecasts, evidence, and outcomes for the same `team_id`, `market_slug`, `condition_id`, event template, and source ids.
- Identify repeated team behavior such as recurring overconfidence, stale evidence reuse, or repeated misses on the same market family.
- Use stored rows as memory. Do not synthesize durable memory outside local Supabase/Postgres.

Calibration:

- Compare `forecast_probability`, `confidence`, `actual_outcome`, `forecast_error`, and `brier_score`.
- Segment calibration by `team_id`, `config_version`, `selected_side`, market family, and event template.
- Treat unresolved or disputed rows as pending diagnostics inputs, not final calibration records.

Event template performance:

- Group routed markets by `event_template`, team id, and category.
- Compare route confidence, forecast error, directional correctness, and cost-adjusted paper results across templates.
- Flag templates with low sample counts separately from templates with poor resolved performance.

Source reliability:

- Aggregate evidence rows by `source_id`, `evidence_type`, freshness, and weight.
- Compare source usage against later outcome quality where resolved outcome rows exist.
- Flag missing sources, stale data, high-weight sources with poor outcomes, and sources that frequently appear in disputed resolutions.

Evidence quality:

- Inspect evidence freshness, evidence type distribution, weights, and payload completeness.
- Compare evidence quality markers against forecast confidence and outcome error.
- Report evidence gaps, stale data, low diversity, and high-confidence forecasts backed by weak evidence.

## Environment Surface

The Team Forecast database env surface is owned by `supabase_team_forecast_config`. Baseline diagnostics reads must use this same boundary and must not define a second read-source configuration surface.

For diagnostics input reads, use the Team Forecast database env surface owned by `supabase_team_forecast_config`. For optional diagnostics snapshot history, use only the snapshot env surface listed above and keep it local Supabase/Postgres.

Public env var names:

- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN`
- `POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE`
- `POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE`

Default table names:

- `POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE` -> `team_profiles`
- `POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE` -> `team_market_routes`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE` -> `team_forecasts`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE` -> `team_forecast_evidence`
- `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE` -> `team_forecast_outcomes`

`POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN` must be validated by `validate_local_postgres_dsn` through `supabase_team_forecast_config` before any diagnostics read connects. The diagnostics report must not print the DSN, password, host tenant, token, key, or any credential-like value.

Leave secret values outside docs and committed examples. Use blank local environment entries or operator-managed local environment injection.

## Intended Command Shape

Once the command is available, run diagnostics as a local read-only report command:

```bash
polymarket-alpha-lab team-diagnostics --team-id crypto_btc --limit 100
```

Expected command behavior:

- Load `supabase_team_forecast_config`.
- Reject disabled or invalid DB settings before connecting.
- Validate that the DSN is local through `validate_local_postgres_dsn`.
- Open a local Supabase/Postgres read connection.
- Read at most the requested number of stored rows for the requested team id.
- Join or correlate route, forecast, evidence, and outcome rows by stored identifiers.
- Emit a diagnostics report for team memory, calibration, event template performance, source reliability, and evidence quality.
- Exit without modifying database rows, exchange state, account state, or durable files.

## Read-Only Query Guidance

When implementing or reviewing the diagnostics command, keep the SQL surface to catalog and row reads. Suitable query shapes are `select` statements over the configured Team Forecast tables with bounded limits and deterministic ordering.

Avoid write-capable SQL and maintenance statements in diagnostics code paths. The diagnostics command should not create, alter, repair, delete, backfill, upsert, or refresh durable data.

Suggested row filters:

- `team_id` equals the requested team id.
- newest forecasts first by `generated_at`.
- evidence matched by `forecast_id`, `team_id`, and `market_slug`.
- outcomes matched by `forecast_id`, `team_id`, and `market_slug`.
- optional future filters for `config_version`, `event_template`, source id, resolved-only rows, and disputed outcomes.

## Troubleshooting

Missing DB env:

- Symptom: diagnostics exits before connecting and names `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED` or `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN`.
- Action: set the local Team Forecast env surface used by `supabase_team_forecast_config`. Keep values in the operator environment, not in docs or committed files.
- Boundary: if DB access is disabled, diagnostics should stop rather than falling back to files or another database.

Non-local DSN:

- Symptom: diagnostics rejects `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN` through `validate_local_postgres_dsn`.
- Action: point the env var at the local Supabase/Postgres instance accepted by the project validator.
- Boundary: do not weaken the validator and do not use hosted Supabase, hosted Postgres, a pooler endpoint, or a remote database for this Phase 1 flow.

No rows:

- Symptom: diagnostics succeeds but reports zero forecasts, evidence rows, routes, or outcomes for the requested team id.
- Action: verify the requested `--team-id`, `--limit`, table-name env vars, and local migration state. A zero-row report is valid and should be presented as insufficient local history.
- Boundary: do not create seed rows from the diagnostics command.

Pending outcomes:

- Symptom: forecasts and evidence exist, but few or no outcome rows exist.
- Action: report calibration, Brier score, paper PnL, and cost-adjusted performance sections as pending or low-sample. Team memory, event template coverage, source usage, and evidence quality can still be reported from route, forecast, and evidence rows.
- Boundary: do not infer final outcomes for unresolved markets and do not mutate outcome tables from diagnostics.

Unexpected table names:

- Symptom: diagnostics cannot find one of the configured Team Forecast tables.
- Action: inspect the env vars listed above and the local Supabase migration state from `docs/team-forecast-supabase-runbook.md`.
- Boundary: diagnostics should fail closed on missing required tables rather than creating tables or falling back to a file store.
