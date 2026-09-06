# Research-Cycle Operations Runbook

Date: 2026-09-07
Scope: M0-P1 research-cycle collection and settlement operations on this workstation
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

## Daily Collection

Start with the read-only census and require both persistence gates to be enabled:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab research-inventory
```

Collect a bounded page for each operational crypto team once per day while
markets are live:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab collect-research-cycles \
  --team crypto_btc --limit 10 --offset 0
PYTHONPATH=src python -m polymarket_alpha_lab collect-research-cycles \
  --team crypto_eth --limit 10 --offset 0
```

The collector uses the documented public Gamma tags (Bitcoin `235`, Ethereum
`39`) and `closed=false` only as server-side prefilters. The frozen local rule
still requires a binary, active, not-closed market with an explicit team
keyword. Each selected slug is fetched again and its returned slug/condition
identity must match before book, spot, or forecast persistence proceeds.
Malformed metadata is counted as `invalid_metadata`; it cannot abort the rest
of the page or enter the cohort.

An `flock` on `/tmp/pal-research-collection.lock` prevents overlapping runs.
A connection interruption is recovered by re-running the same command. Raw
request identities are idempotent, while forecasts are intentionally additive
observation snapshots; settlement export selects the earliest eligible
forecast per condition/team/config cohort. Stop collection if either
persistence gate is disabled, the command reports an infrastructure failure,
or Gamma identity validation blocks a market. Blocked research outcomes with
explicit reason codes are recorded results and do not make the batch fail.

For one operator-selected market, the compatibility commands remain available:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab btc-research-cycle \
  --market <slug-or-0x-condition-id>
PYTHONPATH=src python -m polymarket_alpha_lab crypto-research-cycle \
  --team crypto_eth --market <slug-or-0x-condition-id>
```

Both fetch Gamma metadata, the YES-token CLOB book, and the matching Kraken
spot ticker. They print the deterministic operator packet and redacted cycle
diagnostics. Persistence occurs only when the corresponding local DSN gates
are enabled; otherwise they use the discarding store.

## Settlement Refresh And Export

Refresh outcomes after collection and after known market resolution windows:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab import-settled-outcomes
```

Only `closed=true` markets with an explicit YES label and final prices exactly
`1`/`0` are imported. Open, disputed, malformed, or ambiguous markets are
reported as refused and never guessed. A refresh with no qualifying outcome is
a valid zero-import result.

Export a frozen cutoff and run the existing evaluator offline:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab export-settlement-samples \
  --cutoff <ISO8601-timezone-aware-timestamp> --out /tmp/settlement-samples.json
PYTHONPATH=src python -m polymarket_alpha_lab settlement-evaluation \
  --samples /tmp/settlement-samples.json
```

The adjacent `.manifest.json` records input, included, pending, disputed, and
reason-coded exclusion counts plus the SHA-256 of the exact sample file bytes.
Re-exporting an unchanged database snapshot at the same cutoff must reproduce
both files. Preserve the samples and manifest together for replay after raw
evidence expiry.

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
| Commands | 77 | 78 (`btc-research-cycle` added by M3); current P1 inventory is 84 |

Reproduce with `PYTHONPATH=src python scripts/m0_baseline_measure.py`;
the command inventory contract is
`docs/verification/2026-09-05-m0-cli-command-baseline.txt`.

## Known Boundaries

- No live trading, order submission, wallet, account, or credential
  surfaces; everything is paper-only, report-only, readonly.
- The Claude review gateway had a multi-day instability for review-sized
  sessions (M3 record); reviews fall back to shorter default-model
  sessions when the opus-5 route is unavailable.
