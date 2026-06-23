# Paper Research Packet Operator Flow Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist `PaperResearchPacketOperatorFlowReport` values to Supabase/Postgres with the same DB row, DB-API store, psycopg, env config, migration, and test posture used by the existing paper research packet quality persistence layer.

**Architecture:** Keep the pure operator-flow reducer untouched and add only boundary modules around it. The DB row codec serializes immutable report objects into canonical JSON plus indexed scalar columns; the store owns parameterized DB-API SQL; the psycopg adapter owns connection lifecycle and JSONB adaptation; the env module owns Supabase/Postgres configuration names.

**Tech Stack:** Python frozen dataclasses, `datetime`, `hashlib`, canonical JSON, DB-API cursor contracts, lazy `psycopg`, Supabase/Postgres migration SQL, pytest, CodeGraph, local OpenCode review with `zhipuai-coding-plan/glm-5.2 --variant max`.

## Global Constraints

- Phase 1 only: paper-only, report-only, readonly where applicable.
- No live trading, auth, wallet, private-key, signing, order, cancellation, replacement, relayer, account, exchange, or network mutation surface.
- Do not add DSN/table CLI flags in this node; env config is file-based and reusable by a later CLI wiring node.
- Do not change the pure reducer contract except to fix a blocking mismatch found before persistence work begins.
- Preserve Decimal-only project posture: no `float`, `real`, or `double precision` in Python payloads or migration SQL.
- DB row codec stays pure: no DB connections, env reads, CLI imports, psycopg imports, network/client imports, commits, rollbacks, or prints.
- Store modules use parameterized DB-API SQL and must not import psycopg or read env.
- psycopg imports stay lazy so importing the adapter does not require the postgres extra.
- All persisted hard flags must be exact: `paper_only=True`, `report_only=True`, `readonly=True`.
- Error messages and test fixtures must not leak DSNs, secrets, payload JSON, questions, or report hashes in user-facing paths.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Use CodeGraph before grep/find/manual source reads while implementing.
- Run `codegraph sync` after code changes.
- OpenCode review is mandatory after tests pass; use local OpenCode with `zhipuai-coding-plan/glm-5.2`, `--variant max`, and a hard read-only prompt. Do not use fast mode.

---

## Pre-Implementation Gate

- [ ] **Step 1: Confirm the pure report node exists**

Run:

```bash
test -d .codegraph && codegraph explore "PaperResearchPacketOperatorFlowReport build_paper_research_packet_operator_flow_report persistence fields"
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow.py -q
```

Expected: CodeGraph returns the current `PaperResearchPacketOperatorFlowReport` source or points to the exact file, and the pure report tests pass. If the source module is missing or the tests fail, stop and finish the pure report node first.

- [ ] **Step 2: Confirm this node's write set is clear**

Run:

```bash
git status --short -- \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_store.py \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py \
  src/polymarket_alpha_lab/supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_db_row.py \
  tests/test_paper_research_packet_operator_flow_store.py \
  tests/test_paper_research_packet_operator_flow_psycopg.py \
  tests/test_supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_schema.py \
  supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql
```

Expected: no unrelated user edits in the planned write set. If another worker owns one of these files, coordinate before writing.

## File Structure

- Create `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py`
  - Pure row codec for `PaperResearchPacketOperatorFlowReport`.
  - Owns deterministic `report_sha256`, JSON-safe `payload_json`, `reason_codes_json`, and round-trip validation.
- Create `src/polymarket_alpha_lab/paper_research_packet_operator_flow_store.py`
  - DB-API repository mirroring `paper_research_packet_quality_store.py`.
  - Owns parameterized insert/load SQL, table-name validation, rowcount handling, and record normalization.
- Create `src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py`
  - Optional psycopg adapter mirroring `paper_research_packet_psycopg.py`.
  - Owns lazy psycopg imports, connection commit/rollback/close, and JSONB adaptation.
- Create `src/polymarket_alpha_lab/supabase_paper_research_packet_operator_flow_config.py`
  - Env boundary for optional Supabase/Postgres persistence.
  - Owns enabled/DSN/table parsing and redacted repr.
- Create `supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql`
  - Supabase/Postgres schema for operator-flow reports.
- Create tests:
  - `tests/test_paper_research_packet_operator_flow_db_row.py`
  - `tests/test_paper_research_packet_operator_flow_store.py`
  - `tests/test_paper_research_packet_operator_flow_psycopg.py`
  - `tests/test_supabase_paper_research_packet_operator_flow_config.py`
  - `tests/test_paper_research_packet_operator_flow_schema.py`

## Planned DB Contract

Default table:

```python
DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE = (
    "paper_research_packet_operator_flow_reports"
)
```

Env names:

```python
PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED"
)
PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN"
)
PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE"
)
```

Planned columns, derived from the current operator-flow report test contract:

```sql
report_sha256 text primary key
generated_at timestamptz not null
config_version text not null
flow_status text not null
packet_generated_at timestamptz not null
packet_config_version text not null
packet_persisted boolean not null
packet_row_count integer not null
included_count integer not null
skipped_count integer not null
quality_generated_at timestamptz not null
quality_config_version text not null
quality_status text not null
quality_persisted boolean not null
quality_check_count integer not null
quality_pass_count integer not null
quality_watch_count integer not null
quality_blocked_count integer not null
history_generated_at timestamptz not null
history_config_version text not null
history_status text not null
history_source_report_count integer not null
history_latest_quality_status text not null
reason_codes_json jsonb not null default '[]'::jsonb
reason_code_count integer not null
payload_json jsonb not null
paper_only boolean not null default true
report_only boolean not null default true
readonly boolean not null default true
inserted_at timestamptz not null default now()
```

Lookup indexes:

```sql
create index if not exists idx_prpofr_generated_at
  on public.paper_research_packet_operator_flow_reports (generated_at desc);

create index if not exists idx_prpofr_config_version_generated_at
  on public.paper_research_packet_operator_flow_reports (config_version, generated_at desc);

create index if not exists idx_prpofr_flow_status_generated_at
  on public.paper_research_packet_operator_flow_reports (flow_status, generated_at desc);

create index if not exists idx_prpofr_quality_status_generated_at
  on public.paper_research_packet_operator_flow_reports (quality_status, generated_at desc);

create index if not exists idx_prpofr_history_status_generated_at
  on public.paper_research_packet_operator_flow_reports (history_status, generated_at desc);

create index if not exists idx_prpofr_packet_generated_at
  on public.paper_research_packet_operator_flow_reports (packet_generated_at desc);

create index if not exists idx_prpofr_quality_generated_at
  on public.paper_research_packet_operator_flow_reports (quality_generated_at desc);

create index if not exists idx_prpofr_history_generated_at
  on public.paper_research_packet_operator_flow_reports (history_generated_at desc);

create index if not exists idx_prpofr_reason_codes_json
  on public.paper_research_packet_operator_flow_reports using gin (reason_codes_json jsonb_path_ops);

create index if not exists idx_prpofr_payload_json
  on public.paper_research_packet_operator_flow_reports using gin (payload_json jsonb_path_ops);
```

---

### Task 1: Operator Flow DB Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py`
- Create: `tests/test_paper_research_packet_operator_flow_db_row.py`

**Interfaces:**
- Consumes: exact `PaperResearchPacketOperatorFlowReport`.
- Produces:
  - `PaperResearchPacketOperatorFlowDbRow`
  - `paper_research_packet_operator_flow_report_to_db_row(report)`
  - `paper_research_packet_operator_flow_report_from_db_row(row)`
  - aliases `to_db_row(report)` and `from_db_row(row)`

- [ ] **Step 1: Write failing round-trip and hash tests**

Create `tests/test_paper_research_packet_operator_flow_db_row.py` using a real `PaperResearchPacketOperatorFlowReport` built by `build_paper_research_packet_operator_flow_report(...)`. Assert:
- `type(row) is PaperResearchPacketOperatorFlowDbRow`;
- `row.report_sha256` is the SHA-256 of canonical `payload_json` with `sort_keys=True`, `allow_nan=False`, and separators `(",", ":")`;
- all planned scalar columns copy report fields exactly;
- `row.reason_codes_json == list(report.reason_codes)`;
- `row.reason_code_count == len(report.reason_codes)`;
- `row.payload_json["generated_at"] == report.generated_at.isoformat()`;
- `row.payload_json["reason_codes"] == list(report.reason_codes)`;
- no floats appear anywhere in `payload_json` or `reason_codes_json`;
- `from_db_row(row) == report`;
- compatibility aliases round-trip the same row/report.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_row.py::test_operator_flow_db_row_serializes_payload_and_round_trips -q
```

Expected: FAIL because `paper_research_packet_operator_flow_db_row.py` does not exist yet.

- [ ] **Step 2: Implement minimal row dataclass and serialization**

Implement `PaperResearchPacketOperatorFlowDbRow` with the planned columns. In `__post_init__`, normalize datetimes to UTC, require SHA-256 format, require canonical strings, validate `flow_status`, `quality_status`, `history_status`, and `history_latest_quality_status` in `("pass", "watch", "blocked")`, validate all counts are nonnegative exact `int`, normalize JSON arrays/objects, validate hard flags, and validate the timeline:

```python
packet_generated_at <= quality_generated_at <= history_generated_at <= generated_at
```

Implement `paper_research_packet_operator_flow_report_to_db_row(report)` so it rejects wrong types and subclasses, rejects false hard flags, canonicalizes JSON with no floats, stores `reason_codes_json`, and computes deterministic `report_sha256`.

- [ ] **Step 3: Verify first GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_row.py::test_operator_flow_db_row_serializes_payload_and_round_trips -q
```

Expected: PASS.

- [ ] **Step 4: Add failing validation tests**

Add tests covering:
- hash determinism for identical reports and hash change for changed `config_version`;
- frozen row mutation raises `FrozenInstanceError`;
- wrong report type and report subclass are rejected;
- wrong row type and row subclass are rejected;
- false report hard flags are rejected before write;
- corrupted payload hard flags are rejected on read;
- floats in `payload_json` are rejected;
- payload mismatch raises for each scalar field, `reason_codes_json`, `reason_code_count`, and `payload_json`;
- invalid row shape rejects bad SHA, bad statuses, negative counts, bool counts, non-list `reason_codes_json`, duplicate reason codes, empty reason codes, and false top-level hard flags;
- module purity scan rejects `psycopg`, `sql`, `network`, `client`, `auth`, `wallet`, `account`, `signing`, `submission`, `cancellation`, `replacement`, `exchange`, and `live_trading`.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_row.py -q
```

Expected: FAIL on missing validation behavior.

- [ ] **Step 5: Implement row recovery and validation**

Implement `paper_research_packet_operator_flow_report_from_db_row(row)`:
- reject non-exact row types;
- reject floats in JSON;
- recover datetime strings into UTC `datetime` values;
- recover tuples from JSON lists through the typed report constructor or `from_jsonable`;
- rebuild the expected DB row from the recovered report;
- compare every DB row field to the expected row and raise `ValueError(f"{field_name} must match payload_json")` on mismatch.

- [ ] **Step 6: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow.py tests/test_paper_research_packet_operator_flow_db_row.py -q
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py tests/test_paper_research_packet_operator_flow_db_row.py
```

Expected: all selected tests pass, compileall exits 0, and diff check is clean.

---

### Task 2: Operator Flow DB-API Store

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_store.py`
- Create: `tests/test_paper_research_packet_operator_flow_store.py`

**Interfaces:**
- Consumes: `PaperResearchPacketOperatorFlowDbRow`, `paper_research_packet_operator_flow_report_to_db_row(...)`, `paper_research_packet_operator_flow_report_from_db_row(...)`.
- Produces:
  - `DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE`
  - `PaperResearchPacketOperatorFlowInsertResult`
  - `insert_paper_research_packet_operator_flow_report(connection, report, *, table_name=...)`
  - `insert_paper_research_packet_operator_flow_report_with_result(connection, report, *, table_name=...)`
  - `load_paper_research_packet_operator_flow_reports(connection, *, config_version=None, flow_status=None, limit=None, table_name=...)`

- [ ] **Step 1: Write failing insert tests with a fake DB row module**

Mirror `tests/test_paper_research_packet_quality_store.py`: monkeypatch `polymarket_alpha_lab.paper_research_packet_operator_flow_db_row` before importing the store. Use fake connection/cursor classes and assert the insert SQL is exactly:

```sql
INSERT INTO paper_research_packet_operator_flow_reports (
    report_sha256,
    generated_at,
    config_version,
    flow_status,
    packet_generated_at,
    packet_config_version,
    packet_persisted,
    packet_row_count,
    included_count,
    skipped_count,
    quality_generated_at,
    quality_config_version,
    quality_status,
    quality_persisted,
    quality_check_count,
    quality_pass_count,
    quality_watch_count,
    quality_blocked_count,
    history_generated_at,
    history_config_version,
    history_status,
    history_source_report_count,
    history_latest_quality_status,
    reason_codes_json,
    reason_code_count,
    payload_json,
    paper_only,
    report_only,
    readonly
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (report_sha256) DO NOTHING
```

Assert params are the row fields in the same order, the cursor closes, and the store does not commit or roll back.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_store.py::test_insert_operator_flow_report_uses_parameterized_insert -q
```

Expected: FAIL because the store module does not exist yet.

- [ ] **Step 2: Implement minimal insert store**

Implement the default table constant, `_SELECT_COLUMNS`, table-name validation copied from `paper_research_packet_quality_store.py`, insert SQL, cursor close handling, rowcount validation in `(0, 1)`, and `PaperResearchPacketOperatorFlowInsertResult(row, inserted)`.

- [ ] **Step 3: Verify insert GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_store.py::test_insert_operator_flow_report_uses_parameterized_insert -q
```

Expected: PASS.

- [ ] **Step 4: Add failing load and validation tests**

Add tests for:
- `insert_paper_research_packet_operator_flow_report_with_result(...)` returns `inserted=True` for rowcount 1 and `inserted=False` for rowcount 0;
- unexpected rowcount raises `ValueError("insert rowcount must be 0 or 1")`;
- unsafe table names reject before `connection.cursor()` is called;
- load query filters by `config_version`, `flow_status`, and `limit`;
- selected rows are ordered by `generated_at DESC, inserted_at DESC, report_sha256 DESC`;
- positional tuple, dict, namedtuple, and already-typed row records are accepted;
- empty reads return `()`;
- invalid `table_name`, blank/trimmed `config_version`, bad `flow_status`, and nonpositive/bool `limit` reject before executing SQL;
- `__all__` includes the default table, insert result, insert functions, and load function.

Expected load SQL with all filters:

```sql
SELECT
    report_sha256,
    generated_at,
    config_version,
    flow_status,
    packet_generated_at,
    packet_config_version,
    packet_persisted,
    packet_row_count,
    included_count,
    skipped_count,
    quality_generated_at,
    quality_config_version,
    quality_status,
    quality_persisted,
    quality_check_count,
    quality_pass_count,
    quality_watch_count,
    quality_blocked_count,
    history_generated_at,
    history_config_version,
    history_status,
    history_source_report_count,
    history_latest_quality_status,
    reason_codes_json,
    reason_code_count,
    payload_json,
    paper_only,
    report_only,
    readonly
FROM audit.paper_research_packet_operator_flow_reports
WHERE config_version = %s AND flow_status = %s
ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
LIMIT %s
```

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_store.py -q
```

Expected: FAIL on missing load behavior and validation.

- [ ] **Step 5: Implement load store**

Implement `load_paper_research_packet_operator_flow_reports(...)`, `_db_row_from_record(...)`, JSON object/array normalization, `flow_status` validation, positive limit validation, and no commit/rollback/connection close behavior.

- [ ] **Step 6: Verify Task 2**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_store.py -q
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/paper_research_packet_operator_flow_store.py tests/test_paper_research_packet_operator_flow_store.py
```

Expected: all selected tests pass, compileall exits 0, and diff check is clean.

---

### Task 3: Operator Flow psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py`
- Create: `tests/test_paper_research_packet_operator_flow_psycopg.py`

**Interfaces:**
- Consumes: store functions from Task 2.
- Produces:
  - `insert_paper_research_packet_operator_flow_report_with_psycopg(dsn, report, *, table_name=...)`
  - `load_paper_research_packet_operator_flow_reports_with_psycopg(dsn, *, config_version=None, flow_status=None, limit=None, table_name=...)`

- [ ] **Step 1: Write failing adapter tests**

Mirror `tests/test_paper_research_packet_psycopg.py` and assert:
- `__all__` exports only the insert and load psycopg functions;
- importing the module does not require `psycopg`;
- insert opens one psycopg connection, wraps it in a JSONB-adapting connection, delegates to the store insert function, commits once, does not rollback, and closes once;
- load delegates `config_version`, `flow_status`, `limit`, and `table_name` to the store load function and commits/closes once;
- dict/list params are adapted with `psycopg.types.json.Jsonb`, while scalars like strings, bools, ints, datetimes, and `None` are not wrapped;
- rowcount on wrapped cursors is visible to the store;
- store exceptions roll back, close, and reraise without DSN leakage;
- rollback/close failures do not mask the store exception;
- connect failure raises a clean `RuntimeError` without DSN or secret text;
- missing psycopg raises a clean `RuntimeError` without import-time dependency.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_psycopg.py -q
```

Expected: FAIL because the adapter module does not exist yet.

- [ ] **Step 2: Implement psycopg adapter**

Copy the local pattern from `paper_research_packet_psycopg.py`, changing only names and delegated store functions. Keep `_connect(...)`, `_jsonb_adapter()`, `_PsycopgJsonConnection`, `_PsycopgJsonCursor`, and `_adapt_json_params(...)` private. Error strings must say "paper research packet operator flow" and must not include the DSN.

- [ ] **Step 3: Verify Task 3**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_psycopg.py -q
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py tests/test_paper_research_packet_operator_flow_psycopg.py
```

Expected: all selected tests pass, compileall exits 0, and diff check is clean.

---

### Task 4: Supabase Env Config

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_paper_research_packet_operator_flow_config.py`
- Create: `tests/test_supabase_paper_research_packet_operator_flow_config.py`

**Interfaces:**
- Consumes: `DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE`.
- Produces:
  - `DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE`
  - `PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR`
  - `PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR`
  - `PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR`
  - `SupabasePaperResearchPacketOperatorFlowConfig`
  - `from_paper_research_packet_operator_flow_db_env(env=None)`

- [ ] **Step 1: Write failing env config tests**

Mirror `tests/test_supabase_paper_research_packet_quality_config.py` and assert:
- disabled env config uses default table and accepts absent DSN;
- enabled env config requires DSN without echoing `postgresql://` or secret fragments;
- enabled env config reads explicit DSN and `audit.paper_research_packet_operator_flow_reports`;
- enabled values accepted: `"1"`, `"true"`, `" TRUE "`;
- disabled values accepted: `""`, `"0"`, `"false"`, `" FALSE "`;
- invalid enabled values reject: `"yes"`, `"2"`, `True`;
- config is frozen and masks DSN in `repr`;
- table names accepted: `operator_flow_archive`, `paper_research_packet_operator_flow_reports`, `a`, `a1`, `audit.paper_research_packet_operator_flow_reports`;
- table names rejected: `audit..paper_research_packet_operator_flow_reports`, `audit.paper.research_packet_operator_flow_reports`, `PaperResearchPacketOperatorFlowReports`, `_paper_research_packet_operator_flow_reports`, `paper_research_packet_operator_flow_reports_`, `paper-research-packet-operator-flow-reports`, and `""`;
- direct config rejects non-bool `enabled`;
- direct config rejects non-string DSN without echoing object repr.

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_paper_research_packet_operator_flow_config.py -q
```

Expected: FAIL because the config module does not exist yet.

- [ ] **Step 2: Implement env config module**

Copy the local parsing contract from `supabase_paper_research_packet_quality_config.py`, changing only the default table and public env names. Do not import psycopg, CLI, or network/client modules.

- [ ] **Step 3: Verify Task 4**

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_paper_research_packet_operator_flow_config.py -q
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/supabase_paper_research_packet_operator_flow_config.py tests/test_supabase_paper_research_packet_operator_flow_config.py
```

Expected: all selected tests pass, compileall exits 0, and diff check is clean.

---

### Task 5: Supabase Migration

**Files:**
- Create: `supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql`
- Create: `tests/test_paper_research_packet_operator_flow_schema.py`

**Interfaces:**
- Consumes: planned DB columns from this plan and `PaperResearchPacketOperatorFlowDbRow`.
- Produces: Postgres table `public.paper_research_packet_operator_flow_reports`.

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_paper_research_packet_operator_flow_schema.py` with helpers `migration_sql()`, `compact(sql)`, `compact_expression(sql)`, and `table_body(sql)` matching `tests/test_paper_research_packet_quality_schema.py`.

Tests must assert:
- migration creates `public.paper_research_packet_operator_flow_reports`;
- every planned column exists;
- all statuses are constrained to `('pass', 'watch', 'blocked')`;
- all count columns are nonnegative;
- `jsonb_typeof(reason_codes_json) = 'array'`;
- `jsonb_typeof(payload_json) = 'object'`;
- hard flags are checked true at top level and inside `payload_json`;
- `reason_code_count = jsonb_array_length(reason_codes_json)`;
- `payload_json -> 'reason_codes'` equals `reason_codes_json`;
- payload values for generated/config/status/count/persisted fields match scalar columns;
- timeline checks enforce `packet_generated_at <= quality_generated_at`, `quality_generated_at <= history_generated_at`, and `history_generated_at <= generated_at`;
- `quality_check_count = quality_pass_count + quality_watch_count + quality_blocked_count`;
- `flow_status` matches persisted flags and quality/history status precedence:
  - `blocked` when `packet_persisted is false`, `quality_persisted is false`, `quality_status = 'blocked'`, or `history_status = 'blocked'`;
  - `watch` when no blocked condition and `quality_status = 'watch'` or `history_status = 'watch'`;
  - `pass` when no blocked/watch condition;
- no `float`, `real`, or `double precision` type appears;
- useful lookup indexes exist using the names listed in this plan;
- migration matches existing no-RLS posture: no row-level security, no policy, no alter table;
- forbidden terms do not appear: live trading, auth, order, submit, cancel, sign, wallet, private key, exchange.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_schema.py -q
```

Expected: FAIL because the migration does not exist yet.

- [ ] **Step 2: Implement migration**

Create `supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql` with `create table if not exists`, the planned columns, check constraints, and indexes. Mirror the style of `20260623000000_paper_research_packet_quality_reports.sql`: lowercase SQL, no RLS, no policy, and JSONB checks that keep scalar columns in sync with `payload_json`.

- [ ] **Step 3: Verify Task 5**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_schema.py -q
git diff --check -- supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql tests/test_paper_research_packet_operator_flow_schema.py
```

Expected: schema tests pass and diff check is clean.

---

### Task 6: Integrated Verification, Review, And Handoff

**Files:**
- Modify only files created in Tasks 1-5 if findings require fixes.

**Interfaces:**
- Consumes: complete operator-flow persistence diff.
- Produces: reviewed, tested implementation ready for a later CLI wiring node.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_research_packet_operator_flow.py \
  tests/test_paper_research_packet_operator_flow_db_row.py \
  tests/test_paper_research_packet_operator_flow_store.py \
  tests/test_paper_research_packet_operator_flow_psycopg.py \
  tests/test_supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_schema.py \
  -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Run full local verification**

Run:

```bash
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
git diff --check
git diff --check --cached
git diff -- src tests supabase | rg -n "postgresql://|private[_ -]?key|wallet|secret|api[_-]?key" || true
codegraph sync
```

Expected: compileall passes, full pytest passes, diff checks are clean, the secret scan prints no real credential leak, and CodeGraph sync completes.

- [ ] **Step 3: Run local OpenCode review**

Run from `/home/ubuntu/polymarket-alpha-lab`:

```bash
mkdir -p .superpowers/sdd
git diff -- \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_store.py \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py \
  src/polymarket_alpha_lab/supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_db_row.py \
  tests/test_paper_research_packet_operator_flow_store.py \
  tests/test_paper_research_packet_operator_flow_psycopg.py \
  tests/test_supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_schema.py \
  supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql \
  > .superpowers/sdd/review-paper-research-packet-operator-flow-persistence.diff
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "Read-only review of .superpowers/sdd/review-paper-research-packet-operator-flow-persistence.diff. Scope: PaperResearchPacketOperatorFlowReport persistence only. Requirements: mirror paper_research_packet_quality_store DB-API patterns; add pure db_row codec, store, psycopg adapter, Supabase env config, and migration; preserve Phase 1 paper-only/report-only/readonly constraints; no live trading/auth/wallet/private-key/signing/order/cancel/exchange/network mutation; no DSN/table CLI flags; lazy psycopg import; parameterized SQL; JSONB adaptation; no DSN/secret/payload/question/hash leakage. DO NOT modify/create/delete ANY file; output ONLY verdict plus Critical and Important findings."
```

Expected: OpenCode returns no Critical or Important findings. Fix any Critical or Important finding and rerun focused verification plus this review step.

- [ ] **Step 4: Final implementation handoff**

After tests and OpenCode review pass, make a focused commit for the implementation node if project policy still requires it:

```bash
git add \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_store.py \
  src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py \
  src/polymarket_alpha_lab/supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_db_row.py \
  tests/test_paper_research_packet_operator_flow_store.py \
  tests/test_paper_research_packet_operator_flow_psycopg.py \
  tests/test_supabase_paper_research_packet_operator_flow_config.py \
  tests/test_paper_research_packet_operator_flow_schema.py \
  supabase/migrations/20260623000001_paper_research_packet_operator_flow_reports.sql
git commit -m "feat: persist paper research packet operator flow reports"
```

Push only when the active user/project instruction authorizes pushing this implementation node.
