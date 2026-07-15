# Local Supabase Operations and Durable Persistence

Narrow purpose: define the local Supabase/Postgres operating rules for durable
project persistence on this workstation.

This document is documentation only. It does not add or authorize source code,
tests, CLI behavior, authentication, execution, wallet handling, account reads,
live trading, order signing, order submission, order cancellation, order
replacement, or exchange/order mutation.

## Scope

Durable project persistence means any stored project state that must survive a
process restart, support later audit review, feed readonly diagnostics, or serve
as team/research memory. Durable project persistence must use local
Supabase/Postgres only.

Durable project persistence includes:

- report history rows;
- paper-only and report-only readiness rows;
- specialist team assignment and routing rows;
- research packet summaries and source-quality summaries;
- team memory, research memory, and memory policy rows;
- operator review status, manual follow-up fields, and blocked-reason fields;
- audit-chain records, replay pointers, payload digests, and readonly
  diagnostic summaries;
- backup manifests, restore verification notes, and retention-review records.

Durable project persistence does not include temporary local artifacts used only
for a single run, generated human-readable reports that are not used as the
durable source of truth, test fixtures, screenshots, or transient caches. Those
non-durable files must not become the fallback store for project state.

## Local Supabase/Postgres Boundary

Local Supabase/Postgres is the only approved durable database boundary. The
database target must be a local Docker Supabase/Postgres instance, localhost or
loopback Postgres endpoint, or an explicit local Unix-socket Postgres endpoint.

Do not introduce or rely on:

- hosted Supabase, hosted Postgres, or any hosted database target;
- SQLite or SQLite fallback files;
- JSONL, CSV, Parquet, or filesystem ledgers as durable substitutes;
- DuckDB, Redis, MongoDB, or other alternate durable stores;
- SQLAlchemy-managed durable engines or generic durable-store abstractions;
- file-backed caches used as report history, strategy state, team memory,
  research memory, or audit history;
- environment-specific fallback behavior that silently switches away from local
  Supabase/Postgres.

If local Supabase/Postgres is unavailable, persistence must fail closed or run in
an explicitly non-persistent/report-generation mode. It must not write durable
state to a convenience file, embedded database, hosted database, or unvalidated
store.

## DSN Validation

Any raw database URL or DSN must pass the project local Postgres DSN validator
before a connection is opened. The validator boundary applies to application
code, scripts, one-off operators, smoke checks, and documentation examples.

DSN operating rules:

- read DSNs only from approved process environment or approved local
  configuration keys;
- accept only local Supabase/Postgres targets;
- reject hosted, malformed, missing, non-Postgres, or non-local DSNs;
- do not add command-line DSN flags unless an existing approved local pattern
  explicitly owns that surface;
- never print, persist, log, commit, or copy raw DSNs;
- redact connection material in examples, diagnostics, and review notes with
  placeholders such as `<redacted>`;
- keep `.env.example` values blank and free of sample credentials.

The validator must be treated as a hard precondition, not a warning. A failed
validation result means no database connection should be attempted and no
alternate durable backend should be selected.

## Migration Flow

Migrations are local-first and explicit. A migration may create or alter only
the approved local Supabase/Postgres tables, indexes, constraints, and readonly
metadata required for the documented paper/report surface.

Standard local migration flow:

1. Confirm the local Supabase/Postgres stack is running and `supabase-db` is
   present.
2. Confirm the migration file exists under `supabase/migrations/`.
3. Apply the migration through the local database container with
   `psql -v ON_ERROR_STOP=1`.
4. Verify the expected relations with catalog reads such as `to_regclass` or
   `information_schema`.
5. Verify expected columns, indexes, and constraints with catalog reads only.
6. Run readonly readback or smoke checks that do not mutate exchange, account,
   wallet, order, credential, or live-trading state.
7. Record the migration outcome in documentation or operator notes without raw
   DSNs, passwords, tokens, tenant values, or payload secrets.

Required local command shape:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/<migration-file>.sql
```

Migration verification may inspect local catalog state and approved persisted
report rows. Verification must not create live order intent, mutate exchange
state, read hosted accounts, handle credentials, or bypass DSN validation.

## Backup and Restore

Backups protect local durable project persistence. They are not a license to
copy secrets, raw DSNs, private payloads, wallet material, account data, or live
execution state into this repository.

Backup rules:

- use local Postgres backup tooling against the local Supabase/Postgres
  database;
- include schema and durable report/history/memory/audit tables needed for
  replay and readonly diagnostics;
- store backup files outside the repository unless an approved local operations
  path says otherwise;
- name backups with a timestamp, database identifier, and purpose;
- keep backup manifests redacted and free of credentials;
- verify every backup with a restore rehearsal or catalog/readback check before
  relying on it.

Restore rules:

- restore only into a local Supabase/Postgres target;
- validate the restore target DSN before connecting;
- restore into a clean or explicitly prepared local database to avoid mixing
  incompatible schemas;
- apply migrations to the expected version before replaying dependent checks;
- run catalog verification and readonly report-memory-audit readback after the
  restore;
- document the restore result with timestamps, migration version, restored table
  set, row-count summaries, and redacted reason notes.

A restore that cannot prove local target validation, schema compatibility, and
readonly readback integrity must be treated as failed. Do not compensate by
loading durable state from JSONL, SQLite, CSV, hosted databases, or filesystem
caches.

## Data Retention

Retention is part of the durable persistence contract. Retention policy should
be explicit for every table family that stores report history, team memory,
research memory, operator review, or audit-chain data.

Retention policy must define:

- table family and owning report surface;
- minimum retention period for audit replay;
- maximum retention period for stale or superseded rows when cleanup is allowed;
- legal/safety reason to retain or delete;
- redaction and payload-minimization expectations;
- deletion or archival method;
- verification query or report proving the retention action;
- operator or automation owner responsible for the action.

Retention actions must preserve auditability. Prefer immutable source rows plus
new superseding rows, status fields, or retention markers over destructive
updates when downstream replay depends on historical state. If deletion is
approved, record a redacted retention-review row before deleting and verify that
remaining audit-chain links still explain the decision path.

Do not use retention cleanup to hide failed gates, missing evidence, blocked
research, stale memory, or operator warnings. Those states are audit evidence
and should remain queryable until their documented retention period expires.

## Research Memory Write Principles

Research memory exists to improve readonly research context and explainability.
It is not an execution signal, investment recommendation, order instruction, or
permission record.

Research memory writes must:

- target local Supabase/Postgres only;
- store public references, source labels, digests, timestamps, status fields,
  confidence/readiness scores, and redacted summaries;
- include memory policy values such as `allow`, `throttle`, or `block` when the
  surface supports them;
- preserve source-quality, freshness, and conflict reason codes;
- identify the owning specialist team or research surface when applicable;
- avoid raw private payloads, credentials, account identifiers, wallet material,
  order identifiers, raw DSNs, and hosted account details;
- remain paper-only, report-only, and readonly where those flags exist.

Blocked or throttled memory must be written as visible review evidence when a
surface supports persistence. Missing memory should not be silently treated as
`allow`, and stale memory should not be refreshed through hosted database or
filesystem fallback paths.

## Audit-Chain Write Principles

Audit-chain rows explain how a report, decision-support packet, readiness gate,
or research-memory state was produced. They should make replay possible without
persisting unsafe raw payloads.

Audit-chain writes should include:

- generated timestamp and inserted timestamp;
- config version, migration version, or schema version when available;
- stable row key, payload digest, or replay fingerprint;
- source report references and upstream row digests;
- public market or research references where safe;
- status fields, reason codes, blocked reasons, and manual follow-up fields;
- redacted summary fields sufficient for human review;
- `paper_only`, `report_only`, and `readonly` flags where the surface supports
  them.

Audit-chain writes must not include:

- raw DSNs, passwords, API keys, tokens, cookies, or credential headers;
- private keys, seed phrases, wallet material, account identifiers, or hosted
  account details;
- live order ids, signed order payloads, execution instructions, or broker
  requests;
- raw private source payloads when a digest or redacted summary is sufficient.

An audit-chain row can support manual review, diagnostics, and readonly
learning. It must not become automated trading authorization, position sizing,
or order routing.

## Operational Checks

Before treating a new durable persistence surface as compliant, verify:

- the durable target is local Supabase/Postgres only;
- raw DSNs pass the local Postgres DSN validator before connection setup;
- missing or invalid DSNs fail closed;
- no JSONL, SQLite, hosted database, or filesystem fallback is present;
- migrations are local, explicit, and verified with catalog reads;
- backups and restores target local Postgres and keep manifests redacted;
- retention rules identify table family, owner, period, action, and verification;
- research memory stores redacted evidence and policy state, not execution
  authority;
- audit-chain rows preserve replay context without unsafe payloads;
- readback and diagnostics remain readonly;
- live trading, execution, auth, wallet, account, order, and exchange mutation
  surfaces remain outside the persistence path.
