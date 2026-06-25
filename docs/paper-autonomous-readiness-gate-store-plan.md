# Paper Autonomous Readiness Gate Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local Supabase/Postgres persistence for `PaperAutonomousReadinessGateReport` without changing the Phase 1 paper-only/report-only/readonly reducer boundary.

**Architecture:** Mirror the existing report persistence split used by `local_observability_trends_store.py`, `action_gated_strategy_recommendation_queue_store.py`, and `paper_autonomous_screening_decision_support_gate_store.py`: a DB-API store module accepts an already-open connection, a psycopg wrapper owns connection lifecycle and JSONB adaptation, and a Supabase migration creates the local Postgres table. The existing pure row codec remains the serialization authority and the reducer remains free of DB, env, CLI, network, psycopg, and Supabase imports.

**Tech Stack:** Python 3.12, frozen dataclasses, DB-API cursor connections, optional `psycopg`, local Supabase/Postgres migration SQL, pytest fake-connection unit tests.

## Global Constraints

- ALL database-related implementation must use the local Supabase/Postgres instance on this host.
- Do not use external hosted DBs, SQLite, file-backed DB substitutes, or generic alternate DB backends.
- Keep `paper_autonomous_readiness_gate.py` Phase 1 pure: no DB, env, CLI, network, Supabase, psycopg, filesystem, trading, auth, wallet, or exchange imports.
- Persistence stores and loads report rows only; it must not read accounts, construct orders, sign payloads, submit orders, cancel orders, replace orders, or mutate exchanges.
- Every persisted report and every recovered report must preserve `paper_only=True`, `report_only=True`, and `readonly=True`.
- Use DB-API `%s` placeholders for all runtime values. Only a validated table identifier may be interpolated into SQL.
- Use `ON CONFLICT (report_sha256) DO NOTHING` for idempotent writes.
- DB-API store/load functions must not call `commit()` or `rollback()`; transaction ownership stays with the caller.
- psycopg write wrappers own `connect`, `commit`, `rollback`, and `close`. Read-only wrappers must connect with `autocommit=True` and only close.

---

## Existing Code To Build On

CodeGraph inspection shows the readiness gate already has a pure row codec:

- `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_db_row.py`
- `PaperAutonomousReadinessGateDbRow`
- `paper_autonomous_readiness_gate_report_to_db_row(report)`
- `paper_autonomous_readiness_gate_report_from_db_row(row)`

The row codec already materializes:

```text
report_sha256
generated_at
config_version
readiness_status
recommended_next_step
source_statuses_json
source_config_versions_json
reason_code_counts_json
reason_codes_json
payload_json
paper_only
report_only
readonly
```

`report_sha256` is computed from canonical `payload_json`. Loading must rely on `paper_autonomous_readiness_gate_report_from_db_row(...)` so hash checks, payload/materialized-column consistency checks, JSON float rejection, and recursive hard-flag validation remain centralized in the codec.

## Table Contract

Create one local Supabase/Postgres table:

```text
public.paper_autonomous_readiness_gate_reports
```

Default store constant:

```python
DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE = (
    "paper_autonomous_readiness_gate_reports"
)
```

Columns:

```sql
report_sha256 text primary key,
generated_at timestamptz not null,
config_version text not null,
readiness_status text not null,
recommended_next_step text not null,
source_statuses_json jsonb not null,
source_config_versions_json jsonb not null,
reason_code_counts_json jsonb not null,
reason_codes_json jsonb not null,
payload_json jsonb not null,
paper_only boolean not null default true,
report_only boolean not null default true,
readonly boolean not null default true,
inserted_at timestamptz not null default now()
```

Required checks:

```sql
check (report_sha256 ~ '^[a-f0-9]{64}$'),
check (readiness_status in ('pass', 'watch', 'blocked')),
check (
    recommended_next_step = case readiness_status
        when 'pass' then 'allow_paper_autonomous_readiness_review'
        when 'watch' then 'throttle_paper_autonomous_readiness_review'
        when 'blocked' then 'block_paper_autonomous_readiness_review'
    end
),
check (jsonb_typeof(source_statuses_json) = 'array'),
check (jsonb_typeof(source_config_versions_json) = 'array'),
check (jsonb_typeof(reason_code_counts_json) = 'array'),
check (jsonb_typeof(reason_codes_json) = 'array'),
check (jsonb_typeof(payload_json) = 'object'),
check (jsonb_array_length(source_statuses_json) = 3),
check (jsonb_array_length(source_config_versions_json) = 3),
check (source_statuses_json = payload_json -> 'source_statuses'),
check (source_config_versions_json = payload_json -> 'source_config_versions'),
check (reason_code_counts_json = payload_json -> 'reason_code_counts'),
check (reason_codes_json = payload_json -> 'reason_codes'),
check (payload_json ->> 'paper_only' = 'true'),
check (payload_json ->> 'report_only' = 'true'),
check (payload_json ->> 'readonly' = 'true'),
check (paper_only is true),
check (report_only is true),
check (readonly is true)
```

Recommended indexes:

```sql
create index if not exists paper_autonomous_readiness_gate_generated_at_idx
    on public.paper_autonomous_readiness_gate_reports
    (generated_at desc);

create index if not exists paper_autonomous_readiness_gate_status_generated_at_idx
    on public.paper_autonomous_readiness_gate_reports
    (readiness_status, generated_at desc);

create index if not exists paper_autonomous_readiness_gate_config_generated_at_idx
    on public.paper_autonomous_readiness_gate_reports
    (config_version, generated_at desc);

create index if not exists paper_autonomous_readiness_gate_status_order_idx
    on public.paper_autonomous_readiness_gate_reports
    (readiness_status, generated_at desc, inserted_at desc, report_sha256 desc);
```

Do not add triggers, functions, RLS policies, or cross-table foreign keys in this slice. The table is an append/idempotent report archive keyed by content hash.

## Store Module

Create:

```text
src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py
```

Public exports:

```python
__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE",
    "PaperAutonomousReadinessGateInsertResult",
    "insert_paper_autonomous_readiness_gate_report",
    "insert_paper_autonomous_readiness_gate_report_with_result",
    "load_paper_autonomous_readiness_gate_reports",
)
```

Select/insert column order must be exactly:

```python
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "readiness_status",
    "recommended_next_step",
    "source_statuses_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
```

Use a simple lowercase table identifier validator matching the autonomous screening gate store, unless the implementing task explicitly aligns all nearby autonomous stores on optional schema prefixes. Recommended for this slice:

```python
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
```

This keeps runtime table names local and avoids interpolating schema-qualified user input. The migration still creates `public.paper_autonomous_readiness_gate_reports`; callers use the unqualified table name under the normal Supabase `public` search path.

### Insert Signatures

```python
@dataclass(frozen=True)
class PaperAutonomousReadinessGateInsertResult:
    row: PaperAutonomousReadinessGateDbRow
    inserted: bool
```

```python
def insert_paper_autonomous_readiness_gate_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> PaperAutonomousReadinessGateDbRow:
    return insert_paper_autonomous_readiness_gate_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row
```

```python
def insert_paper_autonomous_readiness_gate_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> PaperAutonomousReadinessGateInsertResult:
    ...
```

Insert behavior:

- Validate `table_name` before opening a cursor.
- Convert with `paper_autonomous_readiness_gate_report_to_db_row(report)`.
- Build columns/placeholders from `_SELECT_COLUMNS`.
- Execute one parameterized insert.
- Close the cursor in `finally`; swallow cursor-close errors only after execute has completed or raised.
- Read `cursor.rowcount`.
- Accept only `rowcount in (0, 1)`.
- Return `inserted=True` when `rowcount == 1`; `inserted=False` when the report already exists by `report_sha256`.
- Do not call `commit()` or `rollback()`.

SQL shape:

```sql
INSERT INTO paper_autonomous_readiness_gate_reports (
    report_sha256,
    generated_at,
    config_version,
    readiness_status,
    recommended_next_step,
    source_statuses_json,
    source_config_versions_json,
    reason_code_counts_json,
    reason_codes_json,
    payload_json,
    paper_only,
    report_only,
    readonly
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (report_sha256) DO NOTHING
```

Parameter tuple:

```python
params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
```

No report values, config versions, statuses, JSON payloads, or limits may be interpolated into SQL.

### Load Signature

```python
def load_paper_autonomous_readiness_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    readiness_status: str | None = None,
    screening_config_version: str | None = None,
    allocation_config_version: str | None = None,
    investment_ledger_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> tuple[PaperAutonomousReadinessGateReport, ...]:
    ...
```

Filters:

- `config_version`: canonical nonblank string, applied as `config_version = %s`.
- `readiness_status`: exactly `pass`, `watch`, or `blocked`, applied as `readiness_status = %s`.
- `screening_config_version`: canonical nonblank string, applied with JSONB containment against `source_config_versions_json`.
- `allocation_config_version`: canonical nonblank string, applied with JSONB containment against `source_config_versions_json`.
- `investment_ledger_config_version`: canonical nonblank string, applied with JSONB containment against `source_config_versions_json`.
- `limit`: positive `int`, rejecting `bool`, applied as `LIMIT %s`.

The source config filters must remain parameterized. Use JSONB array containment
parameters and rely on the psycopg wrapper to adapt lists/dicts to `Jsonb`.
The exact conditions are:

```python
conditions.append("source_config_versions_json @> %s")
params.append([[SCREENING_SOURCE_NAME, screening_config_version]])
```

```python
conditions.append("source_config_versions_json @> %s")
params.append([[ALLOCATION_SOURCE_NAME, allocation_config_version]])
```

```python
conditions.append("source_config_versions_json @> %s")
params.append([[INVESTMENT_LEDGER_SOURCE_NAME, investment_ledger_config_version]])
```

Ordering:

```sql
ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
```

Load behavior:

- Validate all query inputs before opening a cursor.
- Execute a parameterized `SELECT`.
- Close the cursor in `finally`.
- Accept DB records as `PaperAutonomousReadinessGateDbRow`, dict, namedtuple-like objects with `_asdict()`, or positional rows.
- Rebuild each row with `_db_row_from_record(record)`.
- Return recovered reports via `paper_autonomous_readiness_gate_report_from_db_row(row)`.
- Do not call `commit()` or `rollback()`.

## psycopg Adapter

Create:

```text
src/polymarket_alpha_lab/paper_autonomous_readiness_gate_psycopg.py
```

Public exports:

```python
__all__ = (
    "insert_paper_autonomous_readiness_gate_report_with_psycopg",
    "load_paper_autonomous_readiness_gate_reports_with_psycopg",
)
```

Write signature:

```python
def insert_paper_autonomous_readiness_gate_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> PaperAutonomousReadinessGateInsertResult:
    ...
```

Load signature:

```python
def load_paper_autonomous_readiness_gate_reports_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    readiness_status: str | None = None,
    screening_config_version: str | None = None,
    allocation_config_version: str | None = None,
    investment_ledger_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> tuple[PaperAutonomousReadinessGateReport, ...]:
    ...
```

Connection lifecycle:

- Import `psycopg` lazily inside `_connect`.
- Import `Jsonb` lazily inside `_jsonb_adapter`.
- Never import psycopg at module import time.
- For write operations, use `psycopg.connect(dsn)` with normal transaction behavior.
- For write success, call `commit()` once, then `close()` once.
- For store failure or commit failure, call `rollback()` once, then `close()` once, and re-raise the original failure.
- For connect failure, raise a redacted `RuntimeError("failed to connect to the paper autonomous readiness gate database")` from `None`.
- Do not include the DSN, host, username, password, or connection exception string in errors.
- Wrap every dict/list parameter in `Jsonb` before cursor execution.

Read autocommit:

- The read wrapper can share the same JSONB connection wrapper, but it should connect with `psycopg.connect(dsn, autocommit=True)` and should not call `commit()` or `rollback()`.
- If keeping one `_with_owned_connection` helper for both read and write would blur ownership, create two helpers:

```python
def _with_owned_write_connection(dsn: str, operation: Callable[[Any], _T]) -> _T: ...
def _with_owned_read_connection(dsn: str, operation: Callable[[Any], _T]) -> _T: ...
```

This makes commit ownership and autocommit behavior explicit in tests.

## Migration

Create a new Supabase migration under `supabase/migrations/` with the next timestamp available at implementation time. The file name should describe the table, for example:

```text
YYYYMMDDHHMMSS_paper_autonomous_readiness_gate_reports.sql
```

Apply and verify only against the local Supabase/Postgres stack. Do not add fallback DB engines.

Local verification commands should use the existing local container pattern:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/YYYYMMDDHHMMSS_paper_autonomous_readiness_gate_reports.sql
sudo -n docker exec supabase-db psql -U postgres -d postgres -c \
  "select to_regclass('public.paper_autonomous_readiness_gate_reports');"
```

## Tests

Create:

```text
tests/test_paper_autonomous_readiness_gate_store.py
tests/test_paper_autonomous_readiness_gate_psycopg.py
tests/test_paper_autonomous_readiness_gate_schema.py
```

Store tests should mirror the fake-connection style in local observability and autonomous screening gate tests.

Required store assertions:

- Insert uses the exact `INSERT ... VALUES (%s, ...) ON CONFLICT (report_sha256) DO NOTHING` SQL shape.
- Insert parameters equal `tuple(getattr(row, column) for column in SELECT_COLUMNS)`.
- Insert does not interpolate config versions, statuses, reason codes, source names, or JSON payload values into SQL.
- Insert validates table name before cursor creation.
- Insert closes the cursor.
- Insert does not call connection `commit()` or `rollback()`.
- Insert-result returns `inserted=True` for `rowcount == 1`.
- Insert-result returns `inserted=False` for `rowcount == 0`.
- Insert-result rejects unexpected row counts.
- Load applies filters in deterministic order: `config_version`, `readiness_status`, `screening_config_version`, `allocation_config_version`, `investment_ledger_config_version`, then `limit`.
- Load SQL orders by `generated_at DESC, inserted_at DESC, report_sha256 DESC`.
- Load uses `LIMIT %s` for limits.
- Load accepts positional rows, dict rows without mutation, namedtuple-like rows, and `PaperAutonomousReadinessGateDbRow` instances.
- Load rejects invalid `table_name`, blank config strings for any config filter, invalid statuses, `limit <= 0`, `limit=True`, and non-int limits before cursor creation.
- Public exports include the default table and store/load functions.

Required psycopg assertions:

- Importing the adapter does not import `psycopg`.
- Successful write delegates to the store, wraps the raw psycopg connection, commits once, rolls back zero times, and closes once.
- Store failure rolls back once, closes once, re-raises, and does not echo DSN details.
- Commit failure rolls back once, closes once, re-raises, and does not echo DSN details.
- Connect failure raises a redacted `RuntimeError`.
- Dict and list params are wrapped in `psycopg.types.json.Jsonb`.
- Successful read connects with `autocommit=True`, delegates to the store loader, closes once, and does not call commit/rollback.
- Read failure closes once and does not call commit/rollback.

Required schema assertions:

- The migration creates `public.paper_autonomous_readiness_gate_reports`.
- The table has the columns listed in this plan, including `inserted_at`.
- `report_sha256` is the primary key.
- JSON fields are `jsonb`.
- `paper_only`, `report_only`, and `readonly` are enforced true.
- `readiness_status` is constrained to `pass`, `watch`, or `blocked`.
- `recommended_next_step` is constrained to match `readiness_status`.
- The expected indexes exist.

Recommended test command:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_readiness_gate_db_row.py \
  tests/test_paper_autonomous_readiness_gate_db_row_scope.py \
  tests/test_paper_autonomous_readiness_gate_store.py \
  tests/test_paper_autonomous_readiness_gate_psycopg.py \
  tests/test_paper_autonomous_readiness_gate_schema.py \
  -q
```

## Phase 1 Boundary Preservation

This persistence slice remains Phase 1 paper-only/report-only/readonly because:

- The reducer continues to consume already-built typed source reports and emit only an operator-facing report.
- Store/load modules persist and recover immutable report objects only.
- psycopg code is isolated at the persistence boundary and depends only on DSN/table inputs supplied by the caller.
- There is no CLI `--persist` wiring in this plan unless a later task explicitly asks for runtime wiring.
- There are no DSN CLI flags, env readers, runner hooks, account reads, wallet access, auth clients, order construction, signing, submission, cancellation, replacement, or exchange mutation.
- `paper_autonomous_readiness_gate_db_row.py` remains the hard-flag and hash validation gate before write and after load.
- Postgres checks redundantly enforce `paper_only`, `report_only`, and `readonly` on scalar columns and inside `payload_json`.

## Task Breakdown

### Task 1: Store Tests And DB-API Store

**Files:**

- Create: `tests/test_paper_autonomous_readiness_gate_store.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py`

**Interfaces:**

- Consumes: `paper_autonomous_readiness_gate_report_to_db_row(report)` and `paper_autonomous_readiness_gate_report_from_db_row(row)`
- Produces: `insert_paper_autonomous_readiness_gate_report(...)`, `insert_paper_autonomous_readiness_gate_report_with_result(...)`, `load_paper_autonomous_readiness_gate_reports(...)`

- [ ] Write failing store tests for insert SQL, insert-result rowcount behavior, no commit/rollback, cursor close, load filters, row formats, validation-before-cursor, and exports.
- [ ] Run the store tests and verify they fail because the store module does not exist.
- [ ] Implement the store module exactly to the SQL/signature contract above.
- [ ] Run the store tests and verify they pass.

### Task 2: psycopg Adapter Tests And Adapter

**Files:**

- Create: `tests/test_paper_autonomous_readiness_gate_psycopg.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_psycopg.py`

**Interfaces:**

- Consumes: Task 1 store functions
- Produces: `insert_paper_autonomous_readiness_gate_report_with_psycopg(...)` and `load_paper_autonomous_readiness_gate_reports_with_psycopg(...)`

- [ ] Write failing psycopg tests for lazy import, write commit/rollback/close, read autocommit close-only lifecycle, redacted connect failures, and JSONB adaptation.
- [ ] Run the psycopg tests and verify they fail because the adapter module does not exist.
- [ ] Implement the adapter with separate read/write lifecycle helpers.
- [ ] Run the psycopg tests and verify they pass.

### Task 3: Local Supabase/Postgres Migration And Schema Tests

**Files:**

- Create: `supabase/migrations/YYYYMMDDHHMMSS_paper_autonomous_readiness_gate_reports.sql`
- Create: `tests/test_paper_autonomous_readiness_gate_schema.py`

**Interfaces:**

- Consumes: table and column contract from this plan
- Produces: local Postgres table `public.paper_autonomous_readiness_gate_reports`

- [ ] Write schema tests that inspect the migration text and, where existing schema tests already do so, the local Supabase/Postgres catalog.
- [ ] Run the schema tests and verify they fail because the migration does not exist.
- [ ] Add the migration with the table, checks, and indexes listed above.
- [ ] Apply the migration to the local Supabase/Postgres instance.
- [ ] Run schema tests and the local `to_regclass` verification.

### Task 4: Full Persistence Verification

**Files:**

- Modify only the files created in Tasks 1-3 if fixes are required.

**Interfaces:**

- Consumes: Tasks 1-3
- Produces: verified local Supabase/Postgres persistence surface

- [ ] Run the focused pytest command listed in this plan.
- [ ] Confirm `git diff --name-only` contains only the new store, adapter, migration, and tests intended by the implementation task.
- [ ] Confirm no reducer, CLI, runner, README, AGENTS, or existing docs changed.
- [ ] Confirm no code path added auth, wallet, account, live trading, order construction, signing, submission, cancellation, replacement, or exchange mutation.

## Open Concerns For Implementers

- Existing table-name validation is not perfectly uniform. `local_observability_trends_store.py` accepts optional schema prefixes, while `paper_autonomous_screening_decision_support_gate_store.py` accepts only simple lowercase identifiers. This plan recommends the autonomous simple-identifier pattern for this slice.
