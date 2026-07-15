# Team Forecast Migration Safety

This note defines the safety policy for `supabase/migrations/20260701000000_team_forecast_tables.sql` and later Team Forecast migration work.

Polymarket is a probability event market. Phase 1 supports automatic screening, research, and paper execution only; no live trading, no investment advice, no trade instruction, no position advice, and no position sizing. Costs and fees are research factors only, including spread, slippage, liquidity, settlement timing, and paper cost evidence.

## Policy

- Applied migrations are append-only.
- Do not edit an applied migration after it has been shared, reviewed, or applied to a local Supabase/Postgres database.
- Use local Supabase/Postgres only.
- Local Supabase/Postgres is the only durable persistence target.
- Make no hosted DB assumptions.
- Include no raw DSN examples.
- Do no auth/RLS/role policy work in Phase 1.
- Keep Team Forecast persistence paper-only/report-only/readonly.
- Keep costs and fees as research factors only.
- Corrective changes must ship through new migrations.

## Current Migration Surface

The current migration establishes the local Team Forecast persistence surface:

- `supabase/migrations/20260701000000_team_forecast_tables.sql`

- `team_profiles`
- `team_market_routes`
- `team_forecasts`
- `team_forecast_evidence`
- `team_forecast_outcomes`

The append-only migration inventory continues with:

- `supabase/migrations/20260713000000_team_forecast_probability_yes_contract.sql`

This corrective migration contains column comments only, with no table rewrite, DML, or row rewrite. It records these contracts without changing stored forecasts:

- `Canonical Decimal P(YES) for the event; never P(selected_side).`
- `Paper-review side being evaluated; does not reorient forecast_probability.`

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

## Durable-Only Audit

Local Supabase/Postgres is the only durable persistence target for new migration
work. SQLite, Redis, Mongo, SQLAlchemy-managed engines, file journals, and hosted database targets remain disallowed.

Legacy Phase 1 payload/report tables that predate the Team Forecast surface must
finish with table-scoped `paper_only`, `report_only`, and `readonly` hard flags
when later corrective migrations backfill missing columns or constraints. Guard
tests should verify each required table's final schema state directly, not just
that hard-flag tokens appear somewhere in the migration corpus.

Public CLI output must not expose DSN values, table names, or payload JSON. It
also must not expose market slugs, market questions, secrets, tokens, private keys,
wallet/account identifiers, and order-like fields. Failure paths must redact those
fields before writing to stdout or stderr, and operator documentation should keep
connection values in environment injection rather than examples.

## Correction Procedure

When a schema issue is found after this migration has been applied locally:

1. Leave `supabase/migrations/20260701000000_team_forecast_tables.sql` unchanged.
2. Add a new migration with the next canonical timestamped filename.
3. Keep the new migration scoped to local Supabase/Postgres.
4. Add or update tests that describe the corrected contract.
5. Update `docs/team-forecast-supabase-runbook.md` if the operator verification steps change.

Operational apply and verification commands belong in `docs/team-forecast-supabase-runbook.md`; this safety note is policy only.
