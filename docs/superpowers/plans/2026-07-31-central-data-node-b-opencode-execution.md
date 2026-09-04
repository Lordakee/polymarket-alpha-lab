# Node B OpenCode Execution Handoff

Date: 2026-07-31

This is the Codex-approved execution handoff after the visible Claude Code plan
review in `.superpowers/reviews/2026-07-31-central-node-b-plan-review-r4.out`.
The governing plan is
`docs/superpowers/plans/2026-07-31-central-data-node-b-persistence.md`.

## Executor

- External OpenCode process, not a Codex subagent or reviewer.
- Model: `grok/grok-4.5`.
- Variant/thinking: `high`.
- OpenCode may edit only the exclusive implementation files below. It must not
  commit, push, edit `AGENTS.md` or project plans, read secrets, use credentials,
  access accounts/wallets, call live internet endpoints, or add any live/order/
  exchange mutation path.
- OpenCode must not apply the migration or connect to Supabase/Postgres. Codex
  owns local migration smoke verification, integration, Claude result review,
  commit, and GitHub push after the implementation is returned.

## Exclusive File Scope

Production and operational files:

```text
supabase/migrations/20260731000000_central_data_evidence.sql
src/polymarket_alpha_lab/central_data_persistence_policy.py
src/polymarket_alpha_lab/central_data_db_row.py
src/polymarket_alpha_lab/central_data_store.py
src/polymarket_alpha_lab/central_data_psycopg.py
src/polymarket_alpha_lab/supabase_central_data_config.py
src/polymarket_alpha_lab/central_data_normalization.py
.env.example
docs/supabase/local-supabase-operations.md
```

Tests:

```text
tests/test_central_data_persistence_policy.py
tests/test_central_data_db_row.py
tests/test_central_data_store.py
tests/test_central_data_psycopg.py
tests/test_supabase_central_data_config.py
tests/test_central_data_normalization.py
tests/test_central_data_evidence_migration.py
tests/test_central_data_supabase_smoke.py
```

Do not edit Node A contracts/transport/registry, `api.py`, any existing team
module, `team_forecast_packet.py`, Node C/D/E files, package exports, other
migrations, project rules, or review records. If an import/export or shared
contract genuinely appears necessary, stop and report the exact missing symbol
to Codex rather than widening scope.

## Required Implementation

1. Keep all typed artifacts frozen and hard-flagged
   `paper_only=True`, `report_only=True`, `readonly=True`. Use only local
   Supabase/Postgres durable persistence. Do not add SQLite, JSONL/files,
   Redis, MongoDB, hosted databases, SQLAlchemy, or a generic store.
2. Add one idempotent SQL migration with a dedicated non-public
   `central_data_internal` schema and raw response events, normalized
   observations, and redacted retention-audit tables. Use `bytea`, a 2 MiB
   `octet_length`/body-length boundary, `pg_catalog.sha256(bytea)` plus
   `pg_catalog.encode` equality, exact enums/checks/hard flags, deterministic
   indexes, RLS without `FORCE`, no public policies, explicit ACL/default
   privilege revocations, and the trusted local `postgres` owner boundary.
   Do not use a raw-to-normalized or audit-to-raw FK/cascade.
3. Pin the database-side retention contract exactly: migration runs as
   `postgres` in database `postgres` where `cron.database_name=postgres`,
   installs `pg_cron`, registers/updates exactly one
   `central_data_raw_retention_15m` job through
   `cron.schedule_in_database` with `*/15 * * * *`, username `postgres`, and
   the fully-qualified purge command. Reapplication must leave one equivalent
   job. The purge function is `SECURITY INVOKER`, fully qualified, public
   execute revoked, owner-only, deterministic (`expires_at, raw_event_id`),
   bounded, `FOR UPDATE SKIP LOCKED`, audit-before-delete in one transaction,
   and accepts an owner-only server-time cutoff plus a test batch limit.
   Use immutable difference checks (`expires_at - retrieval_time`) rather than
   `timestamptz + interval` expressions in CHECK constraints. Seed a successful
   purge-run audit during migration. Raw inserts must check the exact active job
   and a successful backlog-free purge audit within one hour; otherwise fail
   with a fixed `central_data_retention_not_ready` error. Raw reads use the
   server-side `expires_at > statement_timestamp()` predicate.
4. Preserve raw bytes exactly or refuse them before database binding. The pure
   policy gate must reject oversize, unsupported/binary, malformed, credential,
   token, cookie, API-key, private-key, email, phone, wallet/account/user and
   other high-confidence sensitive body content without echoing matches. Use a
   fixed safe response-header allowlist with bounded grammar/value scanning;
   reject query/userinfo/fragment/redirect/parameterized URLs in this node and
   require request/final URL equality to the concrete registered endpoint.
   Refused/uncaptured bodies create no fake empty hash, body, excerpt, header,
   or normalized observation. Raw and identity reprs/errors/causes are fixed
   redacted; only a private store binding projection may read bytes/URLs.
5. Implement a frozen redacted `RawEventIdentity` emitted only from
   `SourceDefinition + RawResponse` after the safety gate. Its deterministic
   SHA includes every immutable event field (source snapshot, retrieval time,
   endpoint/request/final URLs, status/content/failure/safe headers, payload
   hash, flags). The normalized codec must require
   `SourceDefinition + NormalizedObservation + RawEventIdentity`, include the
   event id in the observation id, validate all evidence/source/hash/time
   relations, and never reconstruct the id from `EvidenceReference` alone.
   The store locks an unexpired matching raw row before normalized insert in the
   same transaction; no new orphan observations are allowed.
6. Make replay idempotency explicit: `ON CONFLICT ... DO NOTHING RETURNING`,
   then compare every immutable field, including bytes or typed envelope. Return
   `already_present` only for exact equality; otherwise raise fixed redacted
   `identity_collision`.
7. Use a collision-proof `central_typed_value_v1` envelope. Every scalar has a
   type tag; object values use an outer `{"type":"object","items":[...]}`
   shape with sorted user keys, so a user dict containing `type` cannot be
   confused with an envelope. Preserve Decimal/string, null/zero/unknown,
   bool, UTC datetime, object, and sequence semantics; reject unknown tags,
   floats, non-finite numbers, tampering, and unsafe datetime forms.
8. Keep JSON/RSS normalization pure and source-agnostic. Parse JSON integers and
   fractions as finite Decimal, reject duplicate keys/NaN/infinity, and bound
   XML declaration/DTD/entity, element, depth, attribute, and text sizes. Do
   not map Polymarket fields, source parameters, quorum, team weights, or
   placeholders here; Node C/E owns those.
9. Keep `central_data_store.py` DB-API-only and transaction-neutral. It owns
   parameterized SQL, fixed qualified table constants, cursor closure and
   safe row conversion, server-time filters, health checks, raw/normalized/
   audit operations, conflict comparison, and deterministic ordering. It does
   not import psycopg, environment, network clients, or files.
10. Keep `central_data_psycopg.py` lazy and redacted. Validate local DSN and
    explicit `user=postgres` before psycopg/Jsonb import or connect. Writes and
    purge commit/rollback/close with original-safe-error precedence; reads use
    explicit autocommit SELECT only. Driver errors and `__cause__` cannot leak
    DSNs, bound data, headers, URLs, table names, or secrets.
11. Keep config env-only, disabled by default, fail closed when enabled with no
    DSN, validate nonblank DSNs even while disabled, require explicit local
    `postgres`, redact repr/errors, and expose no table override or fallback.
    Add only blank central enable/DSN entries to `.env.example`.
12. Update the local Supabase operations runbook with the retention owner,
    exact job/ACL/health/audit/backlog queries, reapplication/repair procedure,
    and the blocked-write response. Do not add a runtime migration runner.

## Focused Tests

Implement the complete matrix in the governing plan, including sensitive
metadata/error/repr redaction, same-id collision, raw-event/observation
identity, Decimal and typed-envelope edge cases, cursor/transaction cleanup,
server-time expiry, retention health and concurrency, migration source checks,
catalog ACL/RLS/job assertions, and a gated real-local-Supabase smoke test. The
smoke test must use synthetic non-sensitive bytes and clean up its rows; it must
never substitute SQLite or a hosted database.

Run only focused pure/fake tests while executing. Report the changed files and
focused test results to Codex. Do not commit or push.

## Stop Conditions

Stop and report without widening scope if implementation requires changing a
Node A contract, adding a parameterized URL contract, touching a team adapter,
using a secret/real network/database, changing project rules, or making a
decision absent from the approved plan.
