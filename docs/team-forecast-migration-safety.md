# Team Forecast Migration Safety

This note defines the safety policy for `supabase/migrations/20260701000000_team_forecast_tables.sql` and later Team Forecast migration work.

## Policy

- Applied migrations are append-only.
- Do not edit an applied migration after it has been shared, reviewed, or applied to a local Supabase/Postgres database.
- Use local Supabase/Postgres only.
- Make no hosted DB assumptions.
- Include no raw DSN examples.
- Do no auth/RLS/role policy work in Phase 1.
- Keep Team Forecast persistence paper-only/report-only/readonly.
- Corrective changes must ship through new migrations.

## Current Migration Surface

The current migration establishes the local Team Forecast persistence surface:

- `team_profiles`
- `team_market_routes`
- `team_forecasts`
- `team_forecast_evidence`
- `team_forecast_outcomes`

These table names align with the defaults exported from `supabase_team_forecast_config`:

- `team_profiles`
- `team_market_routes`
- `team_forecasts`
- `team_forecast_evidence`
- `team_forecast_outcomes`

## Allowed Changes

Allowed future migration work:

- Add a new timestamped migration for a corrective schema change.
- Add a new timestamped migration for a catalog-compatible index or constraint adjustment.
- Add tests that compare docs, config defaults, and migration expectations.
- Add operator documentation that remains local Supabase/Postgres only and omits connection values.

## Disallowed Changes

Do not:

- Rewrite `supabase/migrations/20260701000000_team_forecast_tables.sql` to correct a later finding.
- Assume a hosted database target exists.
- Document connection strings or credential-shaped placeholders.
- Add Phase 1 auth/RLS/role policy work.
- Add application behavior that depends on account, wallet, live trading, or order permissions.
- Move Team Forecast durable data to SQLite, Redis, Mongo, SQLAlchemy-managed engines, hosted Postgres, or any hosted database target.

## Correction Procedure

When a schema issue is found after this migration has been applied locally:

1. Leave `supabase/migrations/20260701000000_team_forecast_tables.sql` unchanged.
2. Add a new migration with the next canonical timestamped filename.
3. Keep the new migration scoped to local Supabase/Postgres.
4. Add or update tests that describe the corrected contract.
5. Update `docs/team-forecast-supabase-runbook.md` if the operator verification steps change.

Operational apply and verification commands belong in `docs/team-forecast-supabase-runbook.md`; this safety note is policy only.
