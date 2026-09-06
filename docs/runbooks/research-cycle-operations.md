# Research-Cycle Operations Runbook

Date: 2026-09-06
Scope: M0-M4 research-cycle operations on this workstation
Status: current operator entry point

## Setup

- Python 3.11 venv with the project installed editable (`pip install -e .`),
  plus `psycopg[binary]` for database work.
- Local Supabase/Postgres runs as the self-hosted compose stack in
  `/home/ubuntu/supabase-selfhost`; the database container is `supabase-db`
  and the central-data schema lives in the `postgres` database.
- Environment variables are the only configuration surface:
  `POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_ENABLED/_DSN` for central
  evidence persistence and `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_*` for
  forecast persistence. DSNs must pass `validate_local_postgres_dsn`
  (local host only, user `postgres`) and are never printed or committed.

## Daily Cycle

```bash
PYTHONPATH=src python -m polymarket_alpha_lab btc-research-cycle \
  --market <slug-or-0x-condition-id>
```

The command fetches Gamma metadata, the CLOB book for the YES token, and
the Kraken BTC ticker, prints the deterministic operator packet followed
by redacted cycle diagnostics, and exits 0 on ready cycles and 1 on
blocked cycles with explicit reason codes. Persistence happens only when
the corresponding DSN env gates are enabled; otherwise runs are
fetch-only (discarding store).

## Offline Replay And Tests

- Default suite (no network, no DB): `python -m pytest -q`.
- Opt-in DB lifecycle acceptance: see
  `docs/roadmap/2026-09-05-m0-baseline-decisions.md` for the disposable
  loopback-forward procedure and env gates
  (`PAL_CENTRAL_DATA_DB_LIFECYCLE=1` plus the DSN env var).
- Opt-in network smoke (`PAL_CENTRAL_DATA_NETWORK_SMOKE=1`): exercises
  the registered sources and one full BTC cycle end to end.
- Failure attribution: strategy-cycle statuses distinguish
  `blocked_fetch_error`, `blocked_normalization_error`,
  `blocked_forecast_error`, `blocked_cost_snapshot_error`, and
  `blocked_report_assembly_error`; exception type names are recorded in
  the report's `market_failure_types` and paper-execution defects in
  `paper_execution_failure_types` (never messages).

## Retention And Repair

- Raw evidence retention is owned by the pg_cron job
  `central_data_raw_retention_15m` (15-minute schedule, 29-day expiry,
  audit-before-delete). If the health gate blocks writes, re-apply the
  checked-in migration as `postgres`; do not create a second job
  manually. Constraint drift cannot be repaired by reapplication
  (`CREATE TABLE IF NOT EXISTS` does not converge constraints) — with
  empty tables, drop and recreate the schema from the checked-in file;
  see the M0 stage plan's migration-drift record.
- Backups and restores follow `docs/supabase/local-supabase-operations.md`.

## Latency Baseline (this workstation)

| Metric | M0 (2026-09-05) | M4 (2026-09-06) |
| --- | --- | --- |
| Interpreter startup | 0.0264 s | 0.0293 s |
| CLI import | 1.8527 s | 0.9579 s |
| `--help` wall time | 0.9643 s | 1.0724 s |
| Commands | 77 | 78 (`btc-research-cycle` added by M3) |

Reproduce with `PYTHONPATH=src python scripts/m0_baseline_measure.py`;
the command inventory contract is
`docs/verification/2026-09-05-m0-cli-command-baseline.txt`.

## Known Boundaries

- No live trading, order submission, wallet, account, or credential
  surfaces; everything is paper-only, report-only, readonly.
- The Claude review gateway had a multi-day instability for review-sized
  sessions (M3 record); reviews fall back to shorter default-model
  sessions when the opus-5 route is unavailable.
