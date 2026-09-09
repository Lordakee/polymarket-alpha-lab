# Team Evidence Aggregation Supabase Local Runbook

Narrow purpose: apply and verify the local Supabase/Postgres migration for
the team-evidence aggregation attempt table (`team_evaluation_attempts`).
Node 4 is schema-only; writers, stores, and connection code are Node 5.

Scope constraints:

- Use local Supabase/Postgres only. Do not adapt this runbook for SQLite,
  Redis, Mongo, SQLAlchemy-managed engines, or any hosted database target.
- Keep this as Phase 1 paper-only/report-only/readonly persistence.
- Do not write connection strings, passwords, tenant values, or credential
  material into this repository.
- Do not bypass the local DSN validator boundary in
  `supabase_team_evidence_aggregation_config`.
- Do not add authentication, private-key handling, account reads, wallet
  operations, live trading, or any order or exchange mutation path.
- Verification queries must be catalog reads only; they must not insert,
  modify, remove, or reshape data.

This runbook is an operator contract for a later, explicitly user-authorized
task; it is not an instruction to connect, create or start services, or
apply migrations on this host. Database execution evidence is Node 5.

## Host Snapshot (Windows)

The current workstation runs plain PostgreSQL, not a Supabase toolchain:

- The Windows service `postgresql-x64-18` (PostgreSQL 18.4) listens on
  loopback only: `127.0.0.1:5432` and `[::1]:5432`.
- Every `pg_hba.conf` rule requires scram-sha-256 authentication; connecting
  needs operator-supplied credentials for a specific authorized task.
- Docker and the Supabase CLI are absent; a PostgreSQL 18 `psql` client is
  on PATH. Container-based Linux commands from older runbooks do not apply.
- Do not start, install, or create services for this runbook; see
  [docs/development/windows-local-setup.md](development/windows-local-setup.md).

## Prerequisites

- An existing local Supabase/Postgres instance the operator is already
  authorized to use. This runbook does not create or start one.
- Operator-supplied connection parameters and credentials, injected at the
  process edge for the authorized task only (libpq `PGHOST`, `PGPORT`,
  `PGDATABASE`, `PGUSER`; credential via the operator's approved channel).
  Never place credentials on the command line, in files, in logs, or in
  this repository.
- The committed migration file in the checkout:
  `supabase/migrations/20260714000000_team_evidence_aggregation_tables.sql`.

## Migration Ordering

Local apply order:

1. All earlier migrations through `20260713000000_team_forecast_probability_yes_contract.sql`
2. `supabase/migrations/20260714000000_team_evidence_aggregation_tables.sql`

`20260714000000` applies only after `20260713000000`; migrations are operator
prerequisites and must not auto-reset or auto-apply to the host database.

## Apply Procedure (Authorized Task Only)

When the user explicitly authorizes applying this migration to the local
instance, apply the committed file through psql with operator-supplied
connection parameters:

```bash
psql -X --single-transaction -v ON_ERROR_STOP=1 \
  --file=supabase/migrations/20260714000000_team_evidence_aggregation_tables.sql
```

`ON_ERROR_STOP=1` stops the run on failure and `--single-transaction` wraps
the whole file in one transaction, so any failure rolls back every statement
and leaves no partial relation. The migration adds no rows, changes no
existing relation, and contains no auth, RLS, or role-policy statement.
## Verify Table and Columns

```sql
select column_name
from information_schema.columns
where table_schema = 'public'
  and table_name = 'team_evaluation_attempts'
order by ordinal_position;
```

Minimum expected column markers:

- `tea_id`, `tfr_id`, `attempted_at`, `status`, `hard_flag`
- `scope_version`, `scope_key`, `config_version`, `config_digest`,
  `diagnostic_record_count`, `arithmetic_record_count`
- `payload_sha256`, `evaluation_scope_payload`, `created_at`
- `paper_only`, `report_only`, `readonly`

The three hard-flag columns must be boolean not null default true with
`CHECK (... IS TRUE)` constraints. The `status` domain is exactly `ready`,
`watch`, or `blocked`; `pass` is rejected.

## Verify Partial Indexes

Catalog read for index names and definitions:

```sql
select indexname, indexdef
from pg_indexes
where schemaname = 'public'
  and tablename = 'team_evaluation_attempts'
order by indexname;
```

Two partial indexes are pinned; names, key column order, and predicates
must match exactly:

```sql
CREATE INDEX team_evaluation_attempts_hard_by_run_idx
ON team_evaluation_attempts (tfr_id, attempted_at DESC, tea_id DESC)
WHERE hard_flag IS TRUE
  AND status IN ('ready', 'watch', 'blocked');

CREATE INDEX team_evaluation_attempts_hard_by_scope_idx
ON team_evaluation_attempts (scope_version, scope_key, attempted_at DESC, tea_id DESC)
WHERE hard_flag IS TRUE
  AND status IN ('ready', 'watch', 'blocked');
```

Postgres normalizes `indexdef` display; compare shape, not bytes: each index
name, each key column order, and the shared predicate selecting rows with
`hard_flag IS TRUE` and `status` in the `ready`/`watch`/`blocked` set.

## Environment Surface

The env surface is owned by `supabase_team_evidence_aggregation_config`.
Keep `.env.example` values blank; do not add sample values.

```text
POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_ENABLED=
POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN=
POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_TABLE=
```

- `POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_TABLE` defaults to
  `team_evaluation_attempts` and must be a lowercase identifier.
- Enabled without a DSN fails closed.
- The DSN must pass `validate_local_postgres_dsn` before any connection or
  persistence adapter is constructed; loopback targets only. Treat that as
  the local DSN validator boundary.
- The DSN must never be printed or logged; the config representation
  redacts it. Node 4 makes no connection attempt.

## Insert-Only Semantics

`tea_id` is the sole identity key (primary key) and attempts are immutable.
Node 5 writers insert with `ON CONFLICT DO NOTHING` against `tea_id`:
duplicate attempt ids are dropped and existing rows are never revised,
replaced, or removed. The Node 4 schema adds no update, delete, or replacement
path.

## Latest-Attempt Query Semantics

History is ordering, not linkage: within a run (`tfr_id`) or a scope
(`scope_version` plus `scope_key`), the latest attempt is the first row by
`attempted_at DESC, tea_id DESC`. The status domain is exactly `ready`,
`watch`, or `blocked`. The partial indexes serve the hard-contradiction
history path (`hard_flag IS TRUE`, same status set); there is no revision
ordinal, no supersession link, and `core_digest` never identifies a scope.

## Authorized Disposable Proof (Node 5, Windows-Native)

Node 5 proves the atomic writer only against the dedicated disposable database
`polymarket_alpha_lab_node5_disposable`, created and dropped by the operator
procedure below. The gated proof test never creates or drops a database,
refuses any other database name, deletes only its own rows by `tea_id`, and
skips by default offline; that skip is the green offline state.

Rules:

- Refuse if the dedicated database already exists; never reuse or drop an
  existing database of that name without user instruction.
- The maintenance DSN is used only for catalog inspection and
  `CREATE/DROP DATABASE`; no shared database is migrated, reset, or
  data-mutated.
- Before any migration apply, `select current_database()` on the TARGET DSN
  must equal the dedicated name; the DSN validator only checks localhost.
- Every native command is followed by an explicit `$LASTEXITCODE` check;
  `$ErrorActionPreference` alone does not trap native exit codes.
- Inject both DSNs through the operator's process-environment channel; never
  echo, log, or paste them. A failed `finally` drop throws, never silences.

```powershell
$ErrorActionPreference = "Stop"
$dbName = "polymarket_alpha_lab_node5_disposable"
$created = $false

# Inject both DSNs through the approved operator channel; never echo them.
& .venv\Scripts\python.exe -c "import os; from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn as v; v(os.environ['POLYMARKET_ALPHA_LAB_NODE5_DISPOSABLE_MAINTENANCE_DSN'], env_var_name='POLYMARKET_ALPHA_LAB_NODE5_DISPOSABLE_MAINTENANCE_DSN'); v(os.environ['POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN'], env_var_name='POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN')"
if ($LASTEXITCODE -ne 0) { throw "DSN validation failed" }

try {
  $exists = (& psql -X -qAt -v ON_ERROR_STOP=1 --dbname=$env:POLYMARKET_ALPHA_LAB_NODE5_DISPOSABLE_MAINTENANCE_DSN -c "select 1 from pg_database where datname = '$dbName'").Trim()
  if ($LASTEXITCODE -ne 0) { throw "catalog inspection failed" }
  if ($exists -eq "1") { throw "dedicated disposable database already exists; refuse to reuse or drop it" }
  & psql -X -v ON_ERROR_STOP=1 --dbname=$env:POLYMARKET_ALPHA_LAB_NODE5_DISPOSABLE_MAINTENANCE_DSN -c "create database $dbName"
  if ($LASTEXITCODE -ne 0) { throw "create database failed" }
  $created = $true
  # Name-assert the TARGET DSN before migrating anything; the validator only checks localhost.
  $target = (& psql -X -qAt -v ON_ERROR_STOP=1 --dbname=$env:POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN -c "select current_database()").Trim()
  if ($LASTEXITCODE -ne 0) { throw "target DSN probe failed" }
  if ($target -ne $dbName) { throw "target DSN points at '$target', not '$dbName'; refusing to migrate it" }
  & psql -X --single-transaction -v ON_ERROR_STOP=1 `
    --dbname=$env:POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN `
    --file=supabase/migrations/20260714000000_team_evidence_aggregation_tables.sql
  if ($LASTEXITCODE -ne 0) { throw "migration apply failed" }

  $env:POLYMARKET_ALPHA_LAB_RUN_TEAM_EVIDENCE_AGGREGATION_DISPOSABLE_DB = "1"
  & .venv\Scripts\python.exe -m pytest -q tests/test_team_evidence_aggregation_attempt_disposable.py
  if ($LASTEXITCODE -ne 0) { throw "disposable proof failed" }
}
finally {
  if ($created) {
    & psql -X -v ON_ERROR_STOP=1 --dbname=$env:POLYMARKET_ALPHA_LAB_NODE5_DISPOSABLE_MAINTENANCE_DSN -c "drop database $dbName with (force)"
    if ($LASTEXITCODE -ne 0) { throw "cleanup drop failed for $dbName; drop it manually before re-running" }
  }
}
```

Evidence records only redacted metadata, never the DSN:

```text
database_name=polymarket_alpha_lab_node5_disposable
migration_apply=pass
status_round_trip=ready,watch,blocked
retry_first_inserted=true
retry_second_inserted=false
retry_row_count_stable=true
orphan_rejected_before_connect=true
rollback_zero_rows=true
cleanup_drop=pass
dsn=redacted
```

The proof test prints its evidence block only after every proof assertion
passed; add `-s` (or `--capture=tee-sys`) to surface it, because pytest
captures stdout on passing runs. Gating is unchanged: skipped unless the flag
is `1` and the DSN passes `validate_local_postgres_dsn`; invalid or unset
DSNs skip, never fail; the proof is never wired into `scripts/verify_local.py`.

## Phase 1 Boundary and Node 5 Handoff

- This surface is paper-only/report-only/readonly local paper evidence
  storage. It is not execution authorization.
- No account authentication, wallet handling, private keys, hosted account
  reads, order signing, order submission, order cancellation, order
  replacement, or exchange mutation belongs on this path.
- Node 5 owns the store, connection path, writer, and disposable-database
  proofs. Until Node 5 lands, nothing in this repository writes these rows.

## Recovery

If a catalog check fails after an authorized apply, inspect the psql error
output; the failed transaction aborted atomically. Reapply the unchanged
committed file through the same authorized procedure and repeat the catalog
checks. Do not reset the instance or remove relations.
