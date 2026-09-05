# M0 Baseline Decisions

Date: 2026-09-05
Stage: M0 of the [Project Delivery Plan](2026-09-05-project-delivery-plan.md)
Stage plan: [M0 stage plan](../superpowers/plans/2026-09-05-m0-baseline-and-persistence-acceptance.md)

## Preserved-Branch Dispositions

| Preserved work | Reference | Disposition | Trigger and dependency rationale |
| --- | --- | --- | --- |
| Reviewed Node 2C evidence aggregation | `origin/codex/node2c-reviewed-assembly` (`05b5703a`) | Evaluate at M2/M3; integrate only if the central bundle contract needs its aggregation semantics; otherwise reject | The M2 evidence bundle defines its own assembly and quorum semantics. Evaluate this branch when the bundle contract is frozen; integrate only if its reviewed aggregation adds semantics the contract lacks, to avoid a second evidence path. |
| Paper autonomous execution pipeline reducer | `origin/codex/20260629-execution-pipeline` (`f7843574`) | Evaluate at M3 against the existing strategy-cycle orchestration; do not merge if it duplicates orchestration ownership | M3 selects exactly one orchestration owner. Compare this stateless paper reducer with the existing strategy-cycle path and merge only the parts that close a demonstrated gap. |
| Node 2C governance v8 | `origin/codex/node2c-governance-v8-20260722` (`886beadb`) | Historical only; governance was deleted by user decision; do not restore it | Contains vendor-specific review/concurrency governance that the user removed. Keep purely as history; no implementation dependency. |

Preservation on a remote branch is not integration. None of these refs are
part of the current branch's history.

## CLI Interface Baseline

- Command inventory (77 top-level commands):
  [2026-09-05-m0-cli-command-baseline.txt](../verification/2026-09-05-m0-cli-command-baseline.txt).
  This file is the compatibility contract for any M4 CLI extraction:
  regenerate with the command below and diff; changes require an explicit
  compatibility decision.
- Measured latency (Python 3.11.15, this workstation, 2026-09-05):
  - interpreter startup: 0.0264 s
  - `polymarket_alpha_lab.cli` import: 1.8527 s
  - `--help` wall time: 0.9643 s
- Reproduction command:

```bash
PYTHONPATH=src python scripts/m0_baseline_measure.py
```

- Representative end-to-end cycle duration is deliberately not measured in
  M0: no offline cycle exists yet. It is measured when the M3 vertical slice
  lands and compared during M4 refactoring (delivery plan updated
  accordingly).

## Lifecycle Acceptance Procedure

The opt-in real-database acceptance lives in
`tests/test_central_data_db_lifecycle.py`. It is skipped in the default
suite with a visible reason.

Requirements:

- `pg_cron` already installed in the local `postgres` database (it is);
- `PAL_CENTRAL_DATA_DB_LIFECYCLE=1`;
- `POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_DSN` set to a DSN that
  passes `validate_local_postgres_dsn` (local host only, user `postgres`);
- a loopback endpoint that reaches `supabase-db` directly. The host's
  published 5432 is the Supavisor pooler (transaction mode, tenant
  required) and cannot serve the lifecycle session, so use a disposable
  forward:

```bash
sudo -n docker run --rm -d --name pal-m0-db-forward \
  --network supabase_default -p 127.0.0.1:55432:5432 \
  alpine/socat tcp-listen:5432,fork,reuseaddr tcp:db:5432
# export the DSN env var yourself; it is never printed by the test
PAL_CENTRAL_DATA_DB_LIFECYCLE=1 \
PYTHONPATH=src python -m pytest -q tests/test_central_data_db_lifecycle.py
sudo -n docker rm -f pal-m0-db-forward
```

Disposal model: the entire scenario (including migration reapplication and
the purge) runs in one transaction that is always rolled back, and the test
asserts baseline counts and explicit synthetic-ID absence afterwards. The
database credential stays in the process environment and is never echoed,
logged, or written to the repository.

## Recorded Results (2026-09-05)

- Default suite: the lifecycle module is skipped with its gate reason
  (`3 skipped` when the module is selected without the env gate).
- Opt-in run: `3 passed in 1.92s` against the local `postgres` database
  through the disposable loopback forward, covering the migration
  idempotency reapplication, retention health gate, insert/replay,
  integer/jsonb/bytea identity collisions, provenance mismatch and
  unavailable-raw refusals, filtered readback, six database CHECK
  negatives, sensitive-payload boundary refusal, the retention cutoff
  boundary (expired row purged, fresh row retained, audit-before-delete,
  normalized-row survival), and post-rollback absence of every synthetic
  ID in all three tables. Post-run database state: zero rows in the raw,
  normalized, and raw-delete audit tables; retention cron job still
  active and unchanged.

## M0 Finding: Migration Drift (repaired)

The first opt-in run exposed that the live `central_data_internal` schema
had been created by an older revision of the migration: its
`content_type` CHECK was only `content_type <> ''`, not the checked-in
media-type allowlist, so a `text/html` row was accepted. Because the
migration uses `CREATE TABLE IF NOT EXISTS` / `CREATE OR REPLACE`,
reapplication can never converge an already-created table's constraints.

Disposition: with both tables empty (verified immediately before), the
schema was dropped (`DROP SCHEMA central_data_internal CASCADE`) and
recreated from the checked-in migration through the documented psql flow;
constraint definitions were then verified to match the file. The lifecycle
test now fails closed on this class of drift, since its CHECK negatives
run against whatever schema is live. A later hardening node may add an
explicit schema-conformance guard (for example, asserting expected
constraint definitions before writes); that is recorded as M4 candidate
work, not M0 scope.
