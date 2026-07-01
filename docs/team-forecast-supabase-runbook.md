# Team Forecast Supabase Local Runbook

Narrow purpose: apply and verify the local Supabase/Postgres migration for Team Forecast persistence on this workstation.

Scope constraints:

- Use local Supabase/Postgres only. Do not adapt this runbook for SQLite, Redis, Mongo, SQLAlchemy-managed engines, hosted Postgres, or any hosted database target.
- Keep this as Phase 1 paper-only/report-only/readonly persistence.
- Do not write connection strings, passwords, tenant values, or credential material into this repository.
- Do not bypass the local DSN validator boundary in `supabase_team_forecast_config`.
- Do not add authentication, private-key handling, account reads, live trading, wallet operations, order signing, order submission, order cancellation, order replacement, or exchange/order mutation.
- Verification commands in this runbook must be catalog reads only. They must not insert, modify, remove, or reshape data.
- For the read-only diagnostics path over these tables, see [docs/team-diagnostics-readonly.md](team-diagnostics-readonly.md). Diagnostics are local Supabase/Postgres Phase 1 paper/report-only reads; live trading, auth, wallet, account, order, and exchange mutation surfaces remain forbidden.

Local facts:

- Supabase CLI: `/home/ubuntu/supabase/node_modules/.bin/supabase`
- Migration: `supabase/migrations/20260701000000_team_forecast_tables.sql`
- Local database container check: `sudo -n docker ps`
- Local database psql entry point: `sudo -n docker exec supabase-db psql`
- Expected tables: `team_profiles`, `team_market_routes`, `team_forecasts`, `team_forecast_evidence`, `team_forecast_outcomes`

## Preconditions

Run from the repository root:

```bash
pwd
test -f supabase/migrations/20260701000000_team_forecast_tables.sql
sudo -n docker ps
```

Confirm `sudo -n docker ps` lists `supabase-db`. If the container is absent, start the local Supabase stack using the existing local development workflow before continuing.

Confirm the local Supabase CLI is present:

```bash
/home/ubuntu/supabase/node_modules/.bin/supabase --version
```

## Apply Locally

Apply the committed migration through the local database container:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/20260701000000_team_forecast_tables.sql
```

The required local command shape is `psql -v ON_ERROR_STOP=1`; keep that flag on every direct apply so failures stop the run.

Do not rely on hosted migration state for this Phase 1 path. The direct-container apply path above is scoped to the local Docker database named `supabase-db`.

## Verify Tables

Verify the five expected relations with `to_regclass`. These commands inspect catalog state only.

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select to_regclass('public.team_profiles');"
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select to_regclass('public.team_market_routes');"
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select to_regclass('public.team_forecasts');"
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select to_regclass('public.team_forecast_evidence');"
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select to_regclass('public.team_forecast_outcomes');"
```

Expected results:

- `team_profiles`
- `team_market_routes`
- `team_forecasts`
- `team_forecast_evidence`
- `team_forecast_outcomes`

Optionally verify the same table set through `information_schema`:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select table_name from information_schema.tables where table_schema = 'public' and table_name in ('team_profiles', 'team_market_routes', 'team_forecasts', 'team_forecast_evidence', 'team_forecast_outcomes') order by table_name;"
```

Expected row set:

- `team_forecast_evidence`
- `team_forecast_outcomes`
- `team_forecasts`
- `team_market_routes`
- `team_profiles`

## Verify Columns

Use catalog reads to inspect columns without touching row data:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select table_name, column_name from information_schema.columns where table_schema = 'public' and table_name in ('team_profiles', 'team_market_routes', 'team_forecasts', 'team_forecast_evidence', 'team_forecast_outcomes') order by table_name, ordinal_position;"
```

Minimum expected column markers:

- `team_profiles`: `team_id`, `display_name`, `primary_categories`, `agent_roles`, `paper_only`, `report_only`, `readonly`, `inserted_at`
- `team_market_routes`: `payload_sha256`, `generated_at`, `team_id`, `market_slug`, `config_version`, `condition_id`, `category_id`, `event_template`, `routing_confidence`, `payload_json`, `paper_only`, `report_only`, `readonly`, `inserted_at`
- `team_forecasts`: `payload_sha256`, `generated_at`, `forecast_id`, `condition_id`, `team_id`, `market_slug`, `config_version`, `selected_side`, `forecast_probability`, `confidence`, `payload_json`, `paper_only`, `report_only`, `readonly`, `inserted_at`
- `team_forecast_evidence`: `payload_sha256`, `generated_at`, `forecast_id`, `evidence_id`, `team_id`, `market_slug`, `config_version`, `source_id`, `data_timestamp`, `data_freshness_seconds`, `evidence_type`, `weight`, `payload_json`, `paper_only`, `report_only`, `readonly`, `inserted_at`
- `team_forecast_outcomes`: `payload_sha256`, `generated_at`, `outcome_id`, `forecast_id`, `team_id`, `market_slug`, `config_version`, `resolved_at`, `actual_outcome`, `forecast_error`, `brier_score`, `paper_pnl`, `cost_adjusted_return`, `directionally_correct`, `profitable_after_cost`, `resolution_dispute_flag`, `payload_json`, `paper_only`, `report_only`, `readonly`, `inserted_at`

## Environment Surface

The Team Forecast database env surface is owned by `supabase_team_forecast_config`.

Public keys:

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

`POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN` is validated by `validate_local_postgres_dsn` before use. Treat that as the local DSN validator boundary: supplied values must resolve to localhost, loopback, or an explicit Unix socket path, and the value must not be echoed in logs or docs.

Leave the `.env.example` values blank. Do not add sample values.

## Troubleshooting

If Docker access fails, rerun:

```bash
sudo -n docker ps
```

If psql access fails, rerun a minimal local query:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select 1;"
```

If any expected table is absent, rerun the local apply command and then repeat the `to_regclass` checks:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/20260701000000_team_forecast_tables.sql
```
