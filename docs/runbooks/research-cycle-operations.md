# Research-Cycle Operations Runbook

Date: 2026-09-07
Scope: M0-P2 prospective research-cycle collection, lineage, settlement export, and offline evaluation
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
request identities and forecast lineage rows are idempotent, while forecasts
are intentionally additive observation snapshots; settlement export selects
the earliest eligible forecast per condition/team/config cohort. Lineage is
persisted after a ready forecast. If that final write fails, the command exits
nonzero and reports `lineage=partial_failure recovery=rerun`; the forecast is
preserved and the rerun must produce an exact lineage replay or fail closed on
identity collision. Stop collection if either persistence gate is disabled,
the command reports an infrastructure failure, or Gamma identity validation
blocks a market. Blocked research outcomes with explicit reason codes are
recorded results and do not make the batch fail.

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

## Settlement Refresh, Export, And Report

Before refreshing outcomes for a prospective cohort, create and preserve a
`p2a-settlement-checkpoint-v1` JSON checkpoint. It freezes the cohort ID,
forecast cutoff, selected forecast IDs and payload hashes, per-forecast event
IDs (including `null` for unknown lineage), aggregate event IDs/unknown count,
team/config cohorts, Gamma tags and page bounds, end/lead rules, hypothesis
`zero_impact_market_control`, independent-hypothesis status `not_implemented`,
reassessment time, generated time, and the three hard flags. It deliberately
does not contain outcome IDs or an outcome cutoff because those do not exist at
prospective freeze time.

Refresh outcomes after the checkpoint and after known market resolution windows.
For a prospective cohort, pass only condition IDs frozen in that checkpoint; a
repository-wide refresh is not a cohort selector:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab import-settled-outcomes \
  --condition-id <checkpoint-condition-id> [--condition-id <checkpoint-condition-id> ...]
```

Only `closed=true` markets with an explicit YES label and final prices exactly
`1`/`0` are imported. Open, disputed, malformed, or ambiguous markets are
reported as refused and never guessed. A refresh with no qualifying outcome is
a valid zero-import result. An exact same-time replay is idempotent; a different
outcome, source, snapshot, hash, or dispute state at the same
`(condition_id, observed_at)` is an `identity_collision` and exits nonzero.
Later observations remain additive correction rows.

Export with separate forecast and outcome cutoffs, then generate the verified
offline report:

```bash
PYTHONPATH=src python -m polymarket_alpha_lab export-settlement-samples \
  --cutoff <forecast-ISO8601-timezone-aware-timestamp> \
  --outcome-cutoff <outcome-ISO8601-timezone-aware-timestamp> \
  --checkpoint /path/to/checkpoint.json \
  --out /tmp/settlement-samples.json
PYTHONPATH=src python -m polymarket_alpha_lab evaluate-settlement-cohort \
  --samples /tmp/settlement-samples.json \
  --manifest /tmp/settlement-samples.json.manifest.json \
  --checkpoint /path/to/checkpoint.json \
  --out /tmp/settlement-report
```

For P2 exports, `--checkpoint` is required. The checkpoint must be a strict
`p2-settlement-checkpoint-v1` document: it binds the frozen cohort constants,
the exact forecast payload hashes with lineage, and the exact-byte SHA-256 of
the sibling inventory and collection artifacts, all re-verified before any
database read. Forecast rows are reconstructed through the validated
`TeamForecastDbRow` contract (payload hash and column agreement), lineage and
outcome queries are scoped to the checkpoint cohort, and any missing,
mismatched, or tampered identity fails closed without publishing files. For a
correction export, add `--prior-export-id <64-lowercase-hex-export-id>`.
The adjacent sample manifest records both cutoffs, input/included/pending/
disputed counts, every exclusion, forecast/outcome payload identities, frozen
cohorts and event lineage, plus the SHA-256 of the exact sample bytes. Outcome
rows after the outcome cutoff are counted but cannot enter the sample. Repeating
an unchanged database snapshot with the same arguments reproduces both files.

`evaluate-settlement-cohort` reads files only. It verifies exact-byte hash,
schema, cutoffs, counts, row identities and checkpoint provenance before
writing `<PREFIX>.json`, `<PREFIX>.md`, and `<PREFIX>.manifest.json`. It reports
paired Brier and clipped log loss, calibration, team/condition/event
concentration, settlement lag, coverage, and at most five deterministic
hand-check rows. With N=0, metrics are `undefined`, not zero; P2 remains open.
The compatibility `settlement-evaluation --samples FILE` command remains
available for plain-text replay without the checkpoint gate.

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
| Commands | 77 | 78 (`btc-research-cycle` added by M3); current P2a inventory is 85 |

Reproduce with `PYTHONPATH=src python scripts/m0_baseline_measure.py`;
the command inventory contract is
`docs/verification/2026-09-05-m0-cli-command-baseline.txt`.

## Known Boundaries

- No live trading, order submission, wallet, account, or credential
  surfaces; everything is paper-only, report-only, readonly.
- The Claude review gateway had a multi-day instability for review-sized
  sessions (M3 record); reviews fall back to shorter default-model
  sessions when the opus-5 route is unavailable.
