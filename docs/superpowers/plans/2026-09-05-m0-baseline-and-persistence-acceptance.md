# M0 Stage Plan: Baseline And Repeatable Persistence Acceptance

Date: 2026-09-05
Stage: M0 of the [Project Delivery Plan](../../roadmap/2026-09-05-project-delivery-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Reviewer input: this document plus the files it references

## Parent-Plan Traceability

This stage implements exactly the M0 milestone of the delivery plan:

- record branch reuse decisions with dependency explanations;
- convert the earlier manual DB lifecycle verification into an opt-in,
  rerunnable test against the real local Postgres;
- exercise migration idempotency, catalog constraints, insert/readback,
  idempotent retries, conflicting identities, rollback, retention
  cleanup/audit, observation references, and sensitive-payload refusal;
- verify intended application-role permissions and sanitized errors without
  printing DSNs;
- capture CLI compatibility and latency baselines before any refactor.

Nothing in this stage adds production persistence surfaces, network
acquisition, team adapters, or orchestration. Those belong to M1-M3.

## Verified Environment Facts

- The local stack is the self-hosted Supabase compose project at
  `/home/ubuntu/supabase-selfhost`; the database container is `supabase-db`.
- The checked-in migration `supabase/migrations/20260731000000_central_data_evidence.sql`
  is already applied to the local `postgres` database: schema
  `central_data_internal` exists, `pg_cron` is installed,
  `cron.database_name=postgres`, the retention job row
  `central_data_raw_retention_15m` is active, and a successful `purge_run`
  audit was recorded at 2026-09-05 12:15 UTC.
- Current row counts in `central_data_raw_response_events` and
  `central_data_normalized_observations` are zero.
- Host port 5432 belongs to `supabase-pooler` (Supavisor). It requires a
  tenant identifier and runs in transaction pool mode, so it is unsuitable
  for a lifecycle test that needs one stable session with explicit
  transaction control. `supabase-db` itself publishes no host port.
- A disposable loopback forward (temporary `socat` sidecar publishing
  `127.0.0.1:55432 -> supabase-db:5432`, removed after the run) gives a
  validator-acceptable local endpoint. The database requires password auth;
  the credential stays in process environment and is never printed.
- Python 3.11 venv has psycopg 3.3.5.
- The CLI exposes 77 argparse subcommands (`src/polymarket_alpha_lab/cli.py`).

## Design Decisions

1. Disposal strategy: run the entire destructive scenario inside one
   connection transaction that is always rolled back in `finally`. The
   migration's hard guards (`current_user='postgres'`,
   `current_database()='postgres'`, `cron.database_name='postgres'`) make a
   separate disposable database impossible without weakening the migration,
   so rollback-based disposal is the safe equivalent: synthetic rows, audit
   rows, and any incidental deletes vanish; pre/post row counts must match.
   The purge-with-future-cutoff step can therefore never permanently remove
   real rows, and the test asserts the count is restored.
2. Gate variables: the test is skipped unless
   `PAL_CENTRAL_DATA_DB_LIFECYCLE=1`. The DSN comes only from
   `POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_DSN`, is passed through
   `validate_local_postgres_dsn` before any connection, and is never echoed.
   The test additionally asserts `current_database()='postgres'` and
   `current_user='postgres'` after connecting.
3. Migration reapplication happens inside the same rolled-back transaction
   via the checked-in SQL file. This proves idempotency against a database
   that already has the migration applied, exercises
   `cron.schedule_in_database` re-registration, and leaves no residue.
   `pg_cron` must already exist (it does); the test skips if the extension
   is missing because creating it requires server configuration outside the
   test's authority.
4. Store-level checks use `CentralDataStore` directly on the test-managed
   connection (the store is DB-API neutral). Expected-failure statements run
   inside savepoints so the outer transaction survives.
5. DB-level CHECK enforcement is proven with raw SQL inserts (the row codecs
   already reject malformed rows client-side; the lifecycle test must show
   the database also enforces the constraints independently).
6. The CLI baseline is a generated, checked-in inventory of the 77 top-level
   command names plus recorded latency numbers, produced by a small
   stdlib-only script so M4 can regenerate and diff it after any extraction.

## Work Items

### 1. `tests/test_central_data_db_lifecycle.py` (new, opt-in)

Skipped unless `PAL_CENTRAL_DATA_DB_LIFECYCLE=1`; `importorskip("psycopg")`.

Ordered scenario in one rollback transaction:

1. Connect with the validated DSN; assert database/user guards.
2. Capture baseline row counts for all three tables.
3. Re-apply the checked-in migration SQL; assert catalog objects exist
   (`to_regclass` checks for both tables, audit table, purge function).
4. `health_check_retention()` returns True.
5. Insert a synthetic `RawEventRow` (public JSON body): `inserted`;
   replay the same row: `already_present`.
6. Conflict: raw-SQL-insert a row reusing that `raw_event_id` with a
   different `status_code`, then `store.insert_raw_event(legit_row)`
   raises `identity_collision`. Repeat the conflict pattern with a
   differing `safe_headers` jsonb value and with a differing `raw_body`
   bytea value (separate savepoints) so the ON CONFLICT compare path is
   proven for integer, jsonb, and bytea round-trip representations.
7. Insert a `NormalizedObservationRow` referencing the raw event:
   `inserted`; replay: `already_present`.
8. Provenance mismatch: insert a normalized row whose `source_id` does not
   match its raw event: raises `raw_event_provenance_mismatch`.
9. Missing raw event: normalized row referencing an uninserted raw id:
   raises `raw_event_unavailable`.
10. Reads: `get_unexpired_raw(source_id=...)` and
    `get_normalized_observations(raw_event_id=...)` return the synthetic
    rows with byte-identical body, hash, and enum fields; an unrelated
    `source_id` filter returns nothing.
11. Constraint negatives via savepoint-wrapped raw SQL: bad `content_type`,
    `body_length` mismatch, `expires_at` not 29 days after retrieval,
    payload hash not matching body, `raw_body` over 2 MiB, and a normalized
    row with malformed `typed_value` envelope.
12. Boundary sanity (pre-DB, no SQL involved): constructing a
    `RawEventRow` with `authorization`/`cookie` headers or a body
    containing credential material raises `ValueError` before any
    statement runs. Full refusal coverage lives in the codec unit tests;
    this step only documents inside the lifecycle run that refused
    payloads cannot reach the database.
13. Retention cutoff boundary: raw-SQL-insert one additional synthetic
    row that is already expired (old `retrieval_time` so that
    `expires_at` lies in the past while still satisfying the exact
    29-day interval CHECK). Then `store.purge_expired_raw(now)` returns
    exactly the expired row, the fresh synthetic row (and any unexpired
    rows) survive, `raw_delete` audit rows exist for each purged id with
    `reason_code='expired_retention'`, a `purge_run` audit row exists,
    and normalized rows survive the purge.
14. Rollback in `finally`; then assert all three tables are back at the
    baseline counts AND that explicit `SELECT ... WHERE raw_event_id IN
    (synthetic ids)` (and the normalized/audit equivalents) return zero
    rows, proving the synthetic rows themselves are gone rather than only
    matching an aggregate count.

Outside the transaction, read-only catalog assertions:

- owners are `postgres`; `relrowsecurity` is enabled and
  `relforcerowsecurity` is off for all three tables;
- `has_table_privilege` is false for `PUBLIC`, `anon`, `authenticated`, and
  `service_role` on all three tables and on the purge function;
- schema `USAGE` is not granted to those roles;
- the cron job row matches the pinned contract (name, schedule, command,
  database, username, active).

### 2. `scripts/m0_baseline_measure.py` (new, stdlib only)

Measures and prints JSON: interpreter startup, `polymarket_alpha_lab.cli`
import time, `--help` wall time, and the sorted list of top-level CLI
commands parsed from the parser. No network, no database. Representative
end-to-end cycle duration is deliberately not measured here: no offline
cycle exists yet, so it is measured when the M3 vertical slice lands and
compared in M4.

### 3. `docs/verification/2026-09-05-m0-cli-command-baseline.txt` (new)

Generated inventory of the 77 command names (one per line) plus a header
recording generator, date, and Python version. This is the M4 compatibility
contract for CLI extraction.

### 4. `docs/roadmap/2026-09-05-m0-baseline-decisions.md` (new)

Records, with rationale and trigger points:

- preserved-branch dispositions:
  - `origin/codex/node2c-reviewed-assembly` (`05b5703a`): evaluate at M2/M3
    only if the bundle contract needs its aggregation semantics; otherwise
    reject to avoid a second evidence path;
  - `origin/codex/20260629-execution-pipeline` (`f7843574`): evaluate at M3
    against the existing strategy-cycle orchestration; do not merge if it
    duplicates orchestration ownership;
  - `origin/codex/node2c-governance-v8-20260722` (`886beadb`): historical
    only; governance was deleted by user decision; do not restore it;
- the measured latency baseline (interpreter, import, help) with the exact
  reproduction command, plus an explicit note that representative cycle
  duration is deferred to M3;
- the current 77-command inventory reference;
- how to run and re-run the lifecycle acceptance (env gates, loopback
  forward setup and teardown, expected output).

### 5. `docs/supabase/local-supabase-operations.md` (edit)

Add a subsection titled "Opt-in DB lifecycle acceptance" under
"Operational Checks", documenting the env gates, the disposable loopback
forward (start and teardown commands), the rule that the DSN must come
from the environment and pass the validator, and that the test cleans up
via rollback.

## Verification

- Default suite: full `pytest -q` on Python 3.11 (lifecycle test reports
  skipped with its reason; skip is visible, not hidden).
- Opt-in run: `PAL_CENTRAL_DATA_DB_LIFECYCLE=1` with the DSN env var set,
  executed once against the local database through the disposable forward;
  record the pass result in the decisions document.
- `python -m compileall` equivalent in-memory compile check for changed
  Python files; `git diff --check`; secret scan over changed files.
- The measurement script runs twice to confirm stable output shape.

## Acceptance Criteria (mirrors delivery-plan M0 exit)

1. A rerunnable, opt-in command exercises the real local database through
   the full central-data lifecycle and passes.
2. Fake/default tests and the real integration run are clearly separated,
   with skip reason visible in the default suite.
3. Branch reuse, defer, or reject decisions are documented with dependency
   rationale.
4. CLI compatibility inventory and latency baseline are checked in, with a
   regeneration command.
5. No production module changes (test, script, and documentation files
   only); no DSN or credential appears in any file, log, or review prompt.

## Rollback

Remove the four new files and revert the operations-doc edit. No production
behavior depends on them.

## Plan Review Response (2026-09-05)

Claude Code reviewed this plan read-only (`claude-opus-5`, effort `max`) and
returned REQUEST_CHANGES: one BLOCKER, two MAJOR, three MINOR, two NIT.
Dispositions:

1. BLOCKER "health_check_retention cannot see the uncommitted purge_run
   audit row": REJECTED as factually incorrect for PostgreSQL. A statement
   in a transaction always sees that same transaction's earlier writes,
   regardless of isolation level; isolation only hides other
   transactions' uncommitted data. The migration reapplication, the seeded
   purge_run audit, and the health check all run in one transaction on one
   connection, so the check sees both the committed real audit row and, if
   needed, the in-transaction seeded row. The reviewer's proposed fix
   (committing the migration reapplication in a separate transaction) would
   permanently write test-session audit state into the real database and
   is strictly worse than rollback disposal. The opt-in run itself is the
   empirical proof: if the premise were right, step 4 would fail.
2. MAJOR "prove the ON CONFLICT compare for jsonb and bytea fields":
   ACCEPTED; step 6 now includes differing `safe_headers` and `raw_body`
   conflict variants.
3. MAJOR "sensitive-payload refusal is client-side, not DB lifecycle":
   ACCEPTED via the reviewer's alternative; step 12 is relabeled a
   boundary sanity check and defers full coverage to codec unit tests.
4. MINOR "purge does not verify the cutoff boundary": ACCEPTED and
   strengthened beyond the reviewer's fallback; step 13 now inserts an
   already-expired row via SQL and verifies the cutoff deletes exactly it.
5. MINOR "rollback assertion should check synthetic IDs, not only counts":
   ACCEPTED; step 14 asserts explicit ID absence.
6. MINOR "cycle duration undefined": ACCEPTED; work items 2 and 4 defer
   representative cycle duration to M3, and the parent delivery plan was
   corrected accordingly.
7. NIT branch-disposition wording: ACCEPTED.
8. NIT operations-doc heading placement: ACCEPTED; the subsection is named
   and placed under "Operational Checks".
