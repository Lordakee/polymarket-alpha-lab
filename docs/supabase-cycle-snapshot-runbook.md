# Supabase Cycle Snapshot Local Migration Runbook

Narrow purpose: apply and verify the local Supabase migration for paper recommendation cycle snapshots on this workstation.

Scope constraints:

- Do not include password, DSN, token, service-role, service role, or secret values.
- Do not perform live trading, wallet, or order activity.
- Only use the local Docker Supabase stack and local migration files.
- Treat local Supabase/Postgres as the only valid durable database target. Do
  not adapt this runbook for SQLite, Redis, Mongo, SQLAlchemy-managed engines,
  hosted Postgres, or any hosted DB target.
- Do not open a connection from any application path that accepts a raw DSN
  unless the local validator has accepted that value.
- Do not document raw DSN values or authorize bypassing that validator.
- This remains Phase 1 paper-only/report-only/readonly persistence for local
  evidence history.
- Do not add authentication or private-key handling.
- Do not add account reads or live trading.
- Do not add order signing or order submission.
- Do not add order cancellation or order replacement.
- Do not add exchange/order mutation.

Local facts:

- Supabase CLI: `/home/ubuntu/supabase/node_modules/.bin/supabase`
- Migration: `supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql`
- Local database container check: `sudo -n docker ps`
- Local database psql entry point: `sudo -n docker exec supabase-db psql`

## Preconditions

Run from the repository root:

```bash
pwd
test -f supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql
sudo -n docker ps
```

Confirm `sudo -n docker ps` lists `supabase-db`. If the container is absent, start the local Supabase stack using the existing local development workflow before continuing.

## Apply

Apply the local migration file directly through the local database container:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql
```

If the command reports that objects already exist, continue to verification if
the table and indexes are present.

The Supabase CLI is available locally for projects that are configured to use
CLI migrations:

```bash
/home/ubuntu/supabase/node_modules/.bin/supabase --version
```

Do not rely on the CLI migration history table for the direct-container apply
path above.

## Verify Local Psycopg Connection Shape

For local psycopg smoke tests through Supavisor, use the tenant-qualified
database user shape `postgres.<tenant>`. The `<tenant>` value comes from the
local self-hosted Supabase environment.

Do not write the actual connection string, password, DSN, or tenant value into this repository.

## Verify Migration Effect

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select to_regclass('public.paper_recommendation_cycle_snapshots');"
```

Expected result: `paper_recommendation_cycle_snapshots`.

## Verify Snapshot Table Columns

Check the main columns without inserting data:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select column_name from information_schema.columns where table_schema = 'public' and table_name = 'paper_recommendation_cycle_snapshots';"
```

Verify the table is reachable without reading or writing non-snapshot data:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select count(*) from public.paper_recommendation_cycle_snapshots;"
```

Expected result includes `snapshot_sha256`, `generated_at`, `config_version`,
`final_status`, `stage_counts`, `artifact_counts`, `reason_codes`, `payload`,
`paper_only`, `report_only`, `readonly`, and `inserted_at`.

## Troubleshooting

If Docker access fails, rerun:

```bash
sudo -n docker ps
```

If psql access fails, rerun a minimal local query:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c "select 1;"
```

If the table is absent, rerun:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql
```
