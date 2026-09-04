# Central Data Node B: Local Evidence Persistence and Normalization

## Goal

Persist safe, reproducible central-data acquisition events and normalized
observations in local Supabase/Postgres only. Node B consumes the frozen Node A
contracts; it does not fetch URLs, introduce source-specific Polymarket
parsing, construct team evidence bundles, or alter any forecast/trading path.

The node remains Phase 1 `paper_only=True`, `report_only=True`, and
`readonly=True`. Its durable data is internal evidence provenance, not an API,
account, wallet, order, or live-trading surface.

## Preconditions and Ownership

- Node A is frozen at commit `935877387ec8a8c815eb6e3d4b3a406fbd7f41da`.
  Node B must consume `SourceDefinition`, `RawResponse`, `EvidenceReference`,
  `NormalizedObservation`, their enums, `MAX_RESPONSE_BYTES`,
  `canonical_json_bytes`, and `sha256_hash` without modifying them.
- Local Supabase/Postgres is the sole durable target. No SQLite, JSONL/file
  storage, Redis, MongoDB, hosted DB, generic durable-store abstraction, or
  raw-payload archive is allowed.
- Node C owns registered parameterized request contracts, official Polymarket
  source adapters, source-specific normalization, and central evidence
  dispatch. Node D team lanes remain pure adapters and do not touch this node.
- Node B owns only the following implementation files and their tests:

  ```text
  supabase/migrations/<timestamp>_central_data_evidence.sql
  src/polymarket_alpha_lab/central_data_persistence_policy.py
  src/polymarket_alpha_lab/central_data_db_row.py
  src/polymarket_alpha_lab/central_data_store.py
  src/polymarket_alpha_lab/central_data_psycopg.py
  src/polymarket_alpha_lab/supabase_central_data_config.py
  src/polymarket_alpha_lab/central_data_normalization.py
  .env.example
  docs/supabase/local-supabase-operations.md
  docs/superpowers/plans/2026-07-30-central-internet-data-layer-and-team-evidence.md
  tests/test_central_data_persistence_policy.py
  tests/test_central_data_db_row.py
  tests/test_central_data_store.py
  tests/test_central_data_psycopg.py
  tests/test_supabase_central_data_config.py
  tests/test_supabase_cycle_snapshot_config.py
  tests/test_central_data_normalization.py
  tests/test_central_data_evidence_migration.py
  tests/test_central_data_supabase_smoke.py
  tests/test_supabase_durable_only_scope.py
  ```

  The exact migration timestamp is assigned at implementation time. Package
  exports and orchestration wiring remain Node E work.

  The parent plan receives two narrow clarifications during this node. First,
  raw SHA-256 remains indexed content provenance but is intentionally not
  unique; the acquisition-event id is the idempotency key because identical
  bytes fetched at different times are different events. Second, zero-weight
  team placeholder construction belongs to Node C's frozen evidence bundle
  and Node E wiring, not this persistence node. These are explicit ownership
  corrections, not production changes to frozen Node A contracts.

  The two additional test files above are included solely for the two reviewed
  full-suite false/omission failures:
  `tests/test_supabase_cycle_snapshot_config.py` and
  `tests/test_supabase_durable_only_scope.py`. This amendment authorizes only
  their Node B test ownership; any edits to either test file await direct
  Claude Code plan review and are not authorized by this plan ownership
  amendment.

## Decisions

### 1. Raw-byte integrity and sensitive-data refusal

`RawResponse.body` is retained byte-for-byte or not at all. Node B never
redacts/re-encodes a body and then claims that the pre-redaction SHA-256
identifies the retained bytes. `raw_payload_sha256` is always the SHA-256 of
the exact `bytea` stored in Postgres.

Before a raw event is encoded or written, a pure persistence-policy gate will:

1. Recheck `type(body) is bytes` and `len(body) <= MAX_RESPONSE_BYTES`.
2. Require the response media type to match the `SourceDefinition` exactly;
   when the source explicitly registers `*/*`, independently allow only the
   closed Phase 1 set `application/json`, `application/rss+xml`,
   `application/xml`, and `text/xml`. Require safe UTF-8 decoding for
   inspection. Unsupported/binary content fails closed until a separately
   reviewed media policy exists.
3. Reject the entire body when high-confidence sensitive data is found. The
   initial detector covers credentials/auth tokens/API keys/private keys;
   cookie/authorization material; direct identifiers including email/phone;
   and wallet/account/user identifiers. It combines exact normalized
   structured-key detection with high-confidence value patterns so ordinary
   market metadata is not treated as PII. Errors return stable reason codes,
   never the matched value or a body excerpt.
4. Persist only a fixed response-header allowlist needed for provenance. Every
   retained value must be canonical, bounded, control-character-free, valid for
   its header grammar, and pass the same high-confidence sensitive detector.
   Unknown headers and credential names such as `authorization`,
   `proxy-authorization`, `cookie`, `set-cookie`, and `x-api-key` are never
   stored. The original body remains unchanged.
5. For this node, require effective request URL and final URL to equal the
   concrete registered `SourceDefinition.url_template` exactly. Query,
   fragment, userinfo, redirect, and parameterized URL forms are rejected.
   Node C must separately review a canonical parameter/fingerprint extension
   before this persistence boundary accepts parameterized acquisitions.

Frozen raw-row and event-identity dataclasses use fixed redacted reprs. Body,
header values, full URLs, matched content, and underlying driver exceptions are
never exposed by repr, error text, exception chaining, or public result
attributes. A private store-facing binding/comparison projection may read the
validated body and URL fields solely to bind/compare them, and is never returned
or logged.

Until Node C completes a fixture-level source-policy review, Data API payloads
that include wallet/account identifiers are deliberately refused as raw
evidence. A refused body results in no persisted body, payload excerpt, header
value, or fake empty-body record. It is a visible, typed safety outcome for the
caller, not a silent redaction or a coerced normalized observation. Persisting
transport failures that never produce a `RawResponse` is deliberately deferred
to Node C's future dispatch/failure contract; Node B will not manufacture an
`EvidenceReference` or `sha256(b"")` for an uncaptured response.

### 2. Event identity, provenance, and idempotency

The raw-payload hash is indexed provenance, not the event primary key. The
same bytes acquired at separate retrieval instants are separate acquisition
events.

`raw_event_id` is a lowercase SHA-256 computed from canonical JSON containing
every immutable acquisition-event field: source id/family/concrete endpoint/
official flag, UTC retrieval time, effective request URL, final URL, status
code, content type, safe header projection, failure status, raw payload hash,
and hard flags. The raw codec receives `SourceDefinition + RawResponse` rather
than guessing a source from a URL and emits both a frozen raw row and a frozen,
redacted `RawEventIdentity`. That identity is the sole bridge into
normalization; it is never reconstructed from the incomplete
`EvidenceReference` contract.

The normalized codec requires
`SourceDefinition + NormalizedObservation + RawEventIdentity`. It validates
source snapshot, retrieval time, payload hash, evidence reference, exact hard
flags, and fixed-endpoint policy before emitting a row. Each normalized row
includes `raw_event_id`, and `normalized_observation_id` includes that event id
in the deterministic canonical hash of the complete
frozen normalized-observation payload after its value is represented by a
versioned typed-value envelope. The envelope recursively tags `Decimal`,
string, bool, null, UTC datetime, object, and sequence values, so Node A's
JSON-facing Decimal string representation cannot collide with an original
string of the same characters. It retains source id, UTC observation/retrieval
time, parser version, parse/freshness/failure/value states, reason codes, hard
flags, and raw payload hash. Floats are rejected. `null`, Decimal zero, and
`unknown` remain distinct in both typed rows and JSONB, and decoding restores
the UTC-normalized frozen `NormalizedObservation` value tree. Node A has no
separate metric discriminator; Node C must carry one inside the value or an
explicit reason-code/typed payload before two metrics from one event can be
distinguished.

Writes use parameterized SQL and `ON CONFLICT (id) DO NOTHING RETURNING id`.
When a conflict returns no inserted id, the store reads the existing row and
compares every immutable field, including raw bytes or the typed value envelope
as applicable. Only byte-for-byte/field-for-field equality returns
`already_present`; any mismatch raises a fixed redacted `identity_collision`
error. A normalized insert first locks the matching unexpired raw row with
`SELECT ... FOR KEY SHARE`, validates event/source/hash/time equality, and then
inserts in the same psycopg transaction. New orphan observations are rejected,
while a later raw purge cannot cascade into the already validated normalized
row. It never accepts arbitrary SQL or table names. Its schema-qualified table
names are fixed internal constants, not environment-controlled inputs.

### 3. Schema, access, and lifecycle

The migration creates a new, dedicated non-public `central_data_internal`
schema and three table families:

```text
central_data_internal.central_data_raw_response_events
central_data_internal.central_data_normalized_observations
central_data_internal.central_data_raw_retention_audit
```

Raw-event rows contain a deterministic event id, immutable source snapshot
(source id/family/concrete endpoint/official flag), request/final URLs,
retrieval time, HTTP metadata, safe headers JSONB, raw `bytea`, body length,
raw hash, expiration timestamp, and hard flags. Constraints enforce SHA-256
format and byte/hash equality with PostgreSQL's built-in immutable
`pg_catalog.sha256(bytea)` plus `pg_catalog.encode`, HTTP/status enums, JSONB
shape, byte cap and body-length equality, UTC-capable timestamps,
`retrieval_time <= inserted_at`, exact hard flags, and a maximum expiry period.
The raw-hash index is non-unique; event id is the unique
primary key. This keeps identical bytes at different retrieval times as
distinct acquisition events without prematurely introducing a
content-deduplication lifecycle.

Normalized rows hold their deterministic observation id, supplied and validated raw event id,
source and safe endpoint snapshot, observation/retrieval times, raw payload
hash, parser version, states, reason
codes JSONB, versioned typed-value JSONB, hard flags, and audit insertion time.
They have no foreign key to raw rows and no cascade. The typed codec validates
the hash/source/time reference before insert, while the schema intentionally
lets normalized provenance survive physical raw-payload deletion.

The redacted retention-audit table supports immutable `purge_run` and
`raw_delete` records. A deletion record contains a deterministic action id,
safe source id/family/official snapshot, raw event id/hash, original body
length, expiry/deletion time, reason code, and hard flags. A run record contains
only job name, cutoff, start/completion time, deleted count, backlog/status, and
hard flags. Each run record has a deterministic run id derived from job name,
cutoff, start time, completion time, status, and deleted count, so repeated
explicit-cutoff runs cannot collide. It never stores bytes, URL, headers, source payload text, or
sensitive-detector details. Before the purge function deletes a raw row, it
writes its deletion audit in the same transaction; every invocation also writes
a run audit, including zero-delete runs. Normalized evidence and both audit
forms remain explainable after raw deletion. Neither normalized nor audit rows
has a foreign key to the raw table, and neither has a cascading lifecycle.
Normalized and retention-audit rows are long-lived Phase 1 provenance with no
deletion permission in Node B; their future retention maximum requires a
separate reviewed node.

All three tables live outside the public REST schema, have RLS enabled without
`FORCE ROW LEVEL SECURITY`, and have no policy. Node B deliberately treats the
local `postgres` owner/superuser as its trusted operational boundary; ordinary
RLS does not constrain that owner. The migration and cron job run as
`postgres`, and runtime central persistence requires an explicit local
`postgres` DSN in addition to `validate_local_postgres_dsn`.

The migration sets the schema, tables, indexes, and purge function owner to
`postgres`; revokes schema/table/function/default privileges from `PUBLIC`,
`anon`, `authenticated`, and `service_role`; and grants only the necessary
schema usage and purge execute rights back to `postgres`. The purge function is
`SECURITY INVOKER`, uses a fixed `pg_catalog` search path, fully qualifies every
central table, and has public execute revoked. There are no sequences, public
views, RPCs, or REST policies. Catalog acceptance checks inspect owners, ACLs,
`pg_policies`, `has_schema_privilege`, `has_table_privilege`, and
`has_function_privilege`; SQL text matching alone is not sufficient.

Raw bodies are physically retained for less than thirty days, not merely hidden
by a read filter. A read-only local preflight on 2026-07-31 confirmed PostgreSQL
17 built-in `sha256(bytea)`, database/user `postgres`,
`cron.database_name=postgres`, and available `pg_cron` 1.6.4. The extension is
not currently installed. The migration must run as superuser `postgres` in the
`postgres` database, verify that it matches `cron.database_name`, install
`pg_cron`, and fail atomically if any prerequisite is false.

The exact job contract is:

```text
job name: central_data_raw_retention_15m
schedule: */15 * * * *
database: postgres
username: postgres
command: select central_data_internal.purge_expired_central_data_raw_response_events();
```

The migration uses `cron.schedule_in_database` and idempotently updates the
single named job when re-applied, then asserts exactly one active row with that
schedule/database/user/command. A mismatch aborts deployment. It invokes the
purge once during migration to seed a successful zero-or-more-delete run audit.
The idempotency guarantee is pinned to the verified local `pg_cron` 1.6.4
`schedule_in_database` named-job update behavior; the migration smoke test
applies the job registration twice and asserts exactly one equivalent final row.

Raw row `expires_at` is fixed at retrieval time plus 29 days, leaving a one-day
failure-response buffer before the 30-day ceiling. The explicit, idempotent
`central_data_internal.purge_expired_central_data_raw_response_events` accepts
owner-only parameters `cutoff timestamptz default statement_timestamp()` and a
bounded positive batch limit. It selects deterministically by
`expires_at, raw_event_id`, locks with `FOR UPDATE SKIP LOCKED`, writes deletion
audits, deletes the selected raw rows, detects any remaining expired backlog,
and writes the run audit in one transaction. The cron call uses server defaults;
the explicit cutoff is the deterministic live-test seam. The store/psycopg
maintenance operation is a write transaction and owns commit/rollback, never a
read-autocommit path.

Before every new raw insert, the store requires the exact active `cron.job` row
and a successful, backlog-free purge-run audit no older than one hour. Missing,
inactive, mismatched, consecutively failing, stale, or backlogged retention
state raises a fixed `central_data_retention_not_ready` error before raw bytes
are bound. The runbook requires immediate operator purge and job repair; raw
writes remain blocked until a fresh successful audit exists. Raw reads always
use `expires_at > statement_timestamp()` server-side, regardless of client
clock. The Python codec computes expiry from retrieval time and rejects an
already expired or future-dated raw response before a DB cursor is opened; the
database independently constrains
`expires_at - retrieval_time = interval '29 days'` and
`expires_at - retrieval_time <= interval '30 days'`; timestamp subtraction is
immutable and avoids a timezone-dependent CHECK expression. Replaying an
existing event cannot extend expiry.

Migration tests verify the function, exact job row, runtime health gate,
deterministic concurrency-safe purge, audit-before-delete order, explicit
future cutoff seam, 29-day policy, and absence of a cascading raw-to-normalized
relationship. A deployment whose Postgres does not support the pinned cron
contract is blocked rather than downgraded. Every DDL, privilege, extension,
function, and named-job operation is idempotent on re-application; a migration
rerun leaves exactly one equivalent job and does not duplicate audit metadata.
The migration is SQL-only, uses one unique canonical timestamp filename, and
adds no runtime migration-execution command or credential path. The operations
runbook identifies the local
Supabase operator as retention owner and gives exact health, audit, backlog,
privilege, and repair queries.

### 4. Modules and boundaries

`central_data_persistence_policy.py`

- Defines the closed, pure policy gate for accepted media, safe response
  headers, high-confidence sensitive-data detection, stable rejection codes,
  and `MAX_RESPONSE_BYTES` enforcement.
- Has no environment, database, network, file, credential, or logging-body
  dependency. It must not expose raw content in errors or result reprs.

`central_data_db_row.py`

- Defines frozen raw-event, redacted `RawEventIdentity`, and
  normalized-observation row dataclasses plus one-way/to-contract codecs.
- Requires `SourceDefinition + RawResponse` for raw rows and emits the identity
  only after the full safety gate succeeds. Requires
  `SourceDefinition + NormalizedObservation + RawEventIdentity` for normalized
  rows. It validates source/hash/URL/timestamp/evidence-reference/event
  consistency before any SQL; it never guesses the identity from an
  `EvidenceReference`.
- Produces the closed envelope version `central_typed_value_v1`: every scalar
  is represented by an object with an explicit `type` tag; Decimal, UTC
  datetime, and string carry canonical string values, bool carries a JSON
  boolean, null has no value, object uses the outer shape
  `{"type":"object","items":[{"key":...,"value":...}]}` with sorted
  user keys, and sequence carries an ordered envelope array. User dictionaries
  therefore cannot collide with the envelope's own `type` tag; unknown or
  tampered tags are rejected. It uses this recursive envelope
  before computing a normalized observation id or binding JSONB and
  reconstructs the same frozen contracts from database records without
  introducing float values, collapsing Decimal/string distinctions, or losing
  tri-state semantics.

`central_data_normalization.py`

- Is a pure, generic JSON/RSS parsing boundary only. JSON integer and fractional
  tokens parse directly to finite `Decimal` through both Decimal-aware hooks;
  duplicate keys, `NaN`/infinity, and pre-existing Python float values are
  rejected. RSS/XML parsing performs a case-insensitive declaration pre-scan,
  rejects DTD/entity-bearing input, and caps body size, element count, nesting
  depth, attribute count, and aggregate text before returning a value.
- Builds generic parsed values and `NormalizedObservation` scaffolding from
  explicit caller-supplied source/observation metadata. It does not decide
  Polymarket field mappings, request parameters, evidence weights, source
  quorums, or team probability impacts; those remain Node C.
- Parse failures become explicit `ParseState`/`FailureStatus`/reason-code
  outcomes. They do not fabricate a value.

`central_data_store.py`

- Defines only concrete central evidence operations against an injected
  DB-API-like connection: insert raw event, insert normalized observation,
  deterministic filtered reads, retention-audit readback, and explicit
  expired-raw purge.
- Owns parameterized SQL, cursor scope, result conversion, fixed qualified
  `central_data_internal.*` table constants, filters, limits, deterministic
  ordering, and idempotency semantics. It does not own connections, commits,
  rollbacks, DSN handling, or psycopg imports.
- Performs the exact cron/run-audit health query before raw binding, exact-row
  conflict verification after `DO NOTHING`, and the atomic raw-row lock and
  provenance comparison before inserting a normalized row.
- Closes every cursor exactly once; if SQL execution or row conversion already
  failed, a cursor-close failure cannot replace that original exception.
- Normalized reads filter/deduplicate through fields preserved after raw purge;
  raw reads always exclude expired bodies even before the cron cleanup runs.

`central_data_psycopg.py`

- Is the optional connection boundary. Each public operation validates the
  local DSN with `validate_local_postgres_dsn` and requires the explicit
  trusted `postgres` role before importing `psycopg`, importing `Jsonb`,
  connecting, or constructing an adapter.
- Owns exactly-once connection cleanup and transaction lifecycle. Successful
  writes commit; a failed operation attempts rollback; cleanup errors never
  replace the original safe operation exception. Driver/connection errors are
  converted to fixed redacted persistence errors with exception chaining
  suppressed, so a bound body, header, DSN, or identifier cannot escape. Reads
  use autocommit connections and issue only explicit `SELECT` operations. Raw
  insert, normalized insert, and purge are write transactions; none uses the
  read-autocommit path.

`supabase_central_data_config.py`

- Reads only environment mappings. The feature is disabled by default and
  enabling it without a local DSN fails closed.
- Validates any supplied DSN even while disabled, reuses
  `validate_local_postgres_dsn`, then parses the URI/keyword form without
  retaining it and requires an explicit `user=postgres` (or URI username
  `postgres`) before any psycopg import/connect. Missing, encoded, duplicate,
  or non-postgres users fail with a fixed redacted error. It redacts the DSN in
  repr/error surfaces, exposes no table-name override, and has no database
  fallback.
- `.env.example` adds only blank central persistence enable/DSN variables; the
  runbook, not an environment flag, documents the database-owned cron job and
  its health verification.

## Test Matrix

The OpenCode handoff must implement the following focused coverage before
integration:

1. Raw policy accepts safe JSON/RSS in the 2 MiB boundary and rejects
   oversize, malformed/unsupported, credential, API-key, private-key, cookie,
   email, phone, wallet, account, and direct-user cases without echoing data.
   Inject secret samples separately into body, each retained header class, URL,
   repr, validation/driver/cursor/commit/rollback/close errors, `__cause__`, and
   public result surfaces. Query/userinfo/fragment URLs fail closed.
2. Raw and normalized codecs enforce frozen contracts, UTC coercion,
   source/hash/URL/evidence-reference/`RawEventIdentity` consistency, source
   snapshot consistency, enum/state values, exact hard flags, Decimal-only
   values, canonical round trips, and `null` vs zero vs `unknown`
   preservation. Global registry membership remains Node A/C responsibility;
   Node B does not claim an unavailable catalog input.
3. Deterministic IDs: same event replays identically; same body at a different
   retrieval time produces another raw event; raw payload hash itself is not
   unique; Decimal and same-text string values produce different observation
   identities; `raw_event_id` is included in observation identity; and any
   changed event/status/source/header/content/typed-value field changes the
   identity. Forced same-id/different-row conflicts must return a redacted
   collision rather than `already_present`.
4. Migration text/schema and real catalog checks cover
   `central_data_internal` access, `bytea`, body size, built-in SHA/body-length
   equality, typed JSONB shape, status checks, hard flags, indexes, owners,
   ACL/default privileges, no public policy, no raw-to-normalized cascade,
   audit-before-delete, exact `schedule_in_database` job, and server-side time
   predicates.
5. Store tests use fakes to prove parameterization, identifier validation,
   deterministic ordering/filtering/limits, exact conflict comparison,
   retention-health-before-body-binding, unexpired raw-row lock and atomic
   normalized validation, orphan refusal, server-time expired-row exclusion,
   explicit future-cutoff purge, deterministic bounded concurrent batches,
   backlog blocking, redacted run/deletion audits, and normalized provenance
   remaining available after raw deletion.
6. Psycopg tests prove DSN validation precedes import/connect, commit on
   success, rollback on operation failure, close in every path, preservation of
   original safe errors when rollback/close fail, purge using the write path,
   and complete DSN/driver/bound-value redaction without a leaking cause.
7. Config tests prove default-disabled behavior, env-only construction,
   local-only explicit-`postgres` DSN enforcement, no-DNS/SQLite/hosted/other-
   role fallback, enabled-without-DSN failure, blank-example entries, and
   repr/error redaction.
8. Generic normalization and typed-envelope tests cover integer/fractional
   Decimal JSON, Decimal vs string, negative zero, exponent/scale, nested
   naive/non-UTC datetime normalization, deep containers, unknown/tampered
   tags, duplicate keys, float/non-finite rejection, bounded safe RSS/XML,
   declaration variants, explicit parse failures, pre-existing user
   dictionaries containing a `type` key, and no source-specific Polymarket
   mapping.
9. The real local-Supabase smoke suite applies the migration and checks catalog
   ACL/RLS/function/job state, a safe synthetic insert, identity collision,
   explicit-cutoff purge, audit retention, normalized survival, job health,
   and cleanup. The service is currently available, so this verification is
   mandatory for Node B; it may skip only when a future environment genuinely
   lacks local Supabase. SQLite never substitutes.
10. Scope tests keep pure policy/codec/normalization modules free of environment,
    psycopg, network and file persistence; keep Node A contracts unchanged; and
    verify the parent-plan idempotency/placeholder ownership clarifications.

The two reviewed full-suite false/omission regressions are verified by
`tests/test_supabase_cycle_snapshot_config.py` and
`tests/test_supabase_durable_only_scope.py`.

Regression verification after implementation:

```bash
pytest -q tests/test_central_data_persistence_policy.py \
  tests/test_central_data_db_row.py tests/test_central_data_store.py \
  tests/test_central_data_psycopg.py \
  tests/test_supabase_central_data_config.py \
  tests/test_supabase_cycle_snapshot_config.py \
  tests/test_central_data_normalization.py \
  tests/test_central_data_evidence_migration.py \
  tests/test_central_data_supabase_smoke.py \
  tests/test_supabase_durable_only_scope.py \
  tests/test_central_data_contracts.py tests/test_central_data_transport.py \
  tests/test_central_data_registry.py
python3 -m compileall -q src tests
pytest -q
codegraph sync
codegraph status
git diff --check
```

Run a targeted credential-format scan of the complete Node B ownership scope,
including `.env.example` and both runbooks, without printing potential secret
values. Do not run live network acquisition,
connect to a hosted database, or use actual credentials during verification.

## Execution and Review Gate

1. Claude Code reviews this plan read-only with `claude-opus-5`, effort `max`,
   fast mode off. The prompt must request `Proceed` or `Blocked`, plus
   Critical/Important/Minor findings focused on retention, raw-byte integrity,
   sensitive-data safety, local-only Postgres access, RLS, provenance,
   lifecycle, Node A compatibility, testability, and Node C/D ownership.
2. Codex adopts only sound findings, revises this plan, and obtains a visible
   `Proceed` before implementation.
3. Codex hands the approved exclusive file scope to OpenCode using
   `grok/grok-4.5` with thinking `high`. OpenCode may not commit, push, access
   secrets, alter Node A contracts, or expand into Nodes C/D/E.
4. Codex runs the verification matrix, performs a read-only Claude result
   review under the same model/effort rules, addresses any accepted blockers,
   commits, and pushes the reviewed Node B result to GitHub.
