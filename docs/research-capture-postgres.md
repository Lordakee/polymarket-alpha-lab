# Prospective research capture on local Supabase/Postgres

## What is delivered

PR #7 evaluates supplied research attempts and outcomes, but its timestamps are
caller assertions. This node adds a durable capture/readback path using ONLY
the approved local Supabase/Postgres database. It does not collect live outcomes,
run models automatically, fit a calibrator, or publish forecasts.

The path is:

1. Register a condition/market and a future forecast cutoff in the local DB.
2. Run the existing research pipeline explicitly, preserving successful AND
   failed/blocked `MarketTeamResearchRun` outputs.
3. Capture each attempt immediately. The DB assigns its actual insertion time.
4. Submit an independently confirmed binary result after the fixed cutoff.
5. Read the complete visible history in one DB snapshot into the existing
   first-attempt evaluator. Unsuccessful/late attempts remain in its counts.

`recorded_at` is DB insertion/receipt time, NOT the model's claimed generation
time, data `as_of`, transaction-start time, or exact commit visibility time.
Delayed imports are stamped when inserted: this API is deliberately not a
backfill interface. No caller-supplied capture timestamp can backdate a record.

## Schema and migration

Apply `supabase/migrations/20260912000000_research_evaluation_capture.sql` ONCE
through the normal local migration-owner procedure before using these APIs.
It is transactional and creates the previously absent `research_capture` schema.
It deliberately fails instead of silently accepting an existing incompatible
schema. No application call creates/migrates tables and no existing table is
changed. Do not apply this migration to a hosted/remote database.

The three tables hold preregistered markets, immutable research attempts and
immutable confirmed outcomes. Timestamp triggers overwrite supplied receipt
times using `clock_timestamp()`. An outcome's cutoff is copied from its original
market registration; neither API callers nor a later outcome can revise it.
Checks require registration before cutoff and cutoff <= resolution <= capture.
Attempts with a late capture are retained for exclusion/coverage accounting.

Records retain the full normalized research run (including evidence text and
its receipts), but not raw Gamma/candle HTTP bodies, provider secrets, or hidden
reasoning. Exact canonical JSON text is SHA256-checked by both Postgres and the
Python decoder. The existing evaluator additionally derives a hash including
receipt time and the reconstructed record. PostgreSQL's built-in SHA256 needs
no extra extension. This is content binding, NOT encryption or a signature.

UPDATE, DELETE and TRUNCATE are rejected by database triggers. PUBLIC has no
schema/table/function rights; nothing is added to Supabase's public API schema.
After migration, grant a dedicated local application role only USAGE on this
schema, SELECT/INSERT on these tables and EXECUTE on its trigger functions.
Do not grant ownership, CREATE, UPDATE, DELETE, TRUNCATE, or trigger-management
rights to that role. The migration intentionally does not create users, handle
passwords, change existing role privileges, or configure REST exposure.

A DB owner/superuser can disable constraints/triggers or alter the clock/data.
This implementation does not protect against a malicious database administrator.
Use the existing trusted local DB administration/backup/security boundary.

## APIs

Import from `polymarket_alpha_lab.research_capture_psycopg`:

```python
from polymarket_alpha_lab.research_capture_psycopg import (
    register_research_market_with_psycopg,
    capture_research_with_psycopg,
    capture_research_outcome_with_psycopg,
    load_research_evaluation_with_psycopg,
)

# local_dsn is explicitly supplied by your local application, never printed.
registration = register_research_market_with_psycopg(
    local_dsn, condition_id=condition_id, market_slug=market_slug,
    forecast_cutoff_at=predeclared_future_cutoff,
)

# run is an actual MarketTeamResearchRun from the existing generic pipeline,
# or the non-None market_run of the single-/dual-source crypto pipeline.
# Capture failures too; do not condition this call on research.status.
record = capture_research_with_psycopg(
    local_dsn, record_id=unique_record_id, model_id=actual_model_identity,
    protocol_version=actual_research_protocol, run=run,
)

# Only after independent confirmation. Unknown/void/unresolved is not False.
confirmed = capture_research_outcome_with_psycopg(
    local_dsn, condition_id=condition_id, market_slug=market_slug,
    resolved_at=confirmed_resolution_time, actual_yes=confirmed_binary_result,
    source_reference=approved_resolution_reference,
    source_content_sha256=confirmed_source_digest,
)
report = load_research_evaluation_with_psycopg(local_dsn)
public_diagnostics = report.to_dict()  # Omits evidence and model-summary text.
```

The APIs return the existing evaluator record/outcome/report types, so callers
need not invent a second scoring or serialization system. The new closed codec
accepts only the known exact dataclass fields, canonical UTC timestamps and
Decimal probability strings. Unknown versions/fields, duplicate JSON keys,
incorrect types/flags, scope mismatches or changed evidence receipts fail closed.
There is no pickle, payload-selected class import, arbitrary SQL/table name,
generic DB abstraction, or alternate storage backend.

Exact retries return the ORIGINAL capture and timestamp. A conflicting record
ID, outcome, market identity or cutoff is rejected; there is no upsert/update.
One task cannot be re-labeled as another independent attempt within the same
team/model/protocol. Writers take a per-condition transaction lock before
checking existing content and inserting. Connection/statement/lock timeouts
are bounded; there are no automatic retries. A retry after an uncertain commit
must reuse the same ID AND unchanged content, not mint a fresh record ID.

Each API validates inputs before driver/connection activity, validates its raw
DSN with `validate_local_postgres_dsn`, imports psycopg lazily, and owns a short
transaction. Errors roll back, connections close, and success is not returned
before commit. DB exceptions become a fixed redacted error; conflict reasons
are fixed codes. No adapter reads credentials or DSNs from disk/environment.
Install the repository's existing locked `postgres` extra for real DB use.

## Consistent and bounded readback

Readback uses REPEATABLE READ / READ ONLY and all visible attempts, never just
successful or recent ones. A historical `generated_at` is allowed but a future
report time is rejected against the DB clock. Database snapshot visibility
still applies: uncommitted records are not visible, even if stamped earlier.
Retain the report's input digest when comparing independently produced reports.

Default limits are 10,000 attempts and 10,000 outcomes (individually) and 32 MiB
of stored payload text per evaluation. Each capture is at most 2 MiB. Counts
and bytes are checked in the same snapshot BEFORE retrieving bodies. An excess
raises `research_capture_history_limit`; no truncated score is returned. A
bounded historical query still includes ALL earlier visible attempts. Paging
and cohorts beyond these limits are not implemented in this release.

The reports retain PR #7's first-recorded-attempt selection, late exclusions,
failure/pending counts, Brier/log-loss/reliability diagnostics, and insufficient
sample warnings. A registered market with NO captured attempt is not yet a
model attempt and is not included in evaluator coverage counts. Pre-market
source failures whose pipeline returns `market_run=None` remain outside this
record type. Source/settlement truth, complete task history and honest model/
protocol identity remain caller responsibilities.

## Verification

Offline tests exercise all ten teams and successful/failed/blocked run codecs,
invalid storage payloads, row tampering, DSN preflight, idempotency/conflicts,
commit/rollback/close behavior, history limits and as-of readback contracts.
The connector inventory adds exactly the new local psycopg module; the shared
DSN guards and existing assertions are NOT disabled or relaxed.

`tests/test_research_capture_disposable.py` is opt-in. It requires BOTH:

- `POLYMARKET_ALPHA_LAB_RUN_RESEARCH_CAPTURE_DISPOSABLE_DB=1`;
- `POLYMARKET_ALPHA_LAB_RESEARCH_CAPTURE_DB_DSN` identifying a local database
  whose actual name is exactly `polymarket_research_capture_test`.

The test refuses a pre-existing capture schema BEFORE migration. It creates
only this node's schema/tables and synthetic records in that dedicated DB.
It never creates/drops a database or touches the regular `postgres` database.
Provision and destroy the disposable database through your authorized local
Supabase/Postgres test lifecycle. Run only on a disposable target; do not point
it at ordinary project data. It proves actual timestamp/constraint behavior,
eight concurrent retries, rollback, immutable data, first-failure retention,
late exclusion and historical evaluation. Default full offline CI skips it.
Actual full-suite and isolated Postgres results belong in the PR, not inferred
from fake cursor tests. A local PostgreSQL engine proof is not full acceptance
of a user's installed Supabase stack, role setup, backups, or connection config.

No live model, real outcome dataset or user database is needed for these tests.
Self-review/merge without external-review or CodeGraph gates is owner-authorized.
Phase 1 paper/report/readonly flags mean paper evidence storage, NOT that these
explicit capture functions are SQL read-only. They cannot trade, access exchange
accounts or promote a research estimate into an approved forecast.

Primary behavior references:
https://www.postgresql.org/docs/16/functions-datetime.html
https://www.postgresql.org/docs/16/functions-binarystring.html
https://www.psycopg.org/psycopg3/docs/basic/transactions.html
