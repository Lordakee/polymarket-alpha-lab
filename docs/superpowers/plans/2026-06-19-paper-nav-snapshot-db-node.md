# Paper NAV Snapshot DB Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a DB-first repository layer for already-generated `PaperNavSnapshot` values without wiring CLI, runner, or NAV calculation flows.

**Architecture:** Mirror the existing paper recommendation cycle snapshot DB layer with a narrow NAV-specific vertical slice: pure row codec, DB-API repository, optional psycopg adapter, and Supabase migration. The boundary only persists snapshots already produced by `positions.mark_paper_nav`; it does not fetch order books, read account state, or change portfolio NAV calculation.

**Tech Stack:** Python dataclasses, `Decimal`, `datetime`, DB-API cursor connections, optional `psycopg`, Supabase/Postgres SQL migration, pytest.

---

## Files And Responsibilities

- Create `src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py`
  - Frozen `PaperNavSnapshotDbRow` dataclass.
  - `paper_nav_snapshot_to_db_row(snapshot)` converts `PaperNavSnapshot` to summary columns plus canonical `payload_json`.
  - `paper_nav_snapshot_from_db_row(row)` recovers a validated `PaperNavSnapshot`.
  - Reject floats in JSON payloads and require `paper_only is True`; do not require `report_only` or `readonly`.
- Create `src/polymarket_alpha_lab/paper_nav_snapshot_store.py`
  - DB-API functions `insert_paper_nav_snapshot(...)` and `load_paper_nav_snapshots(...)`.
  - Validate simple lowercase table identifiers and positive integer limits.
  - Use parameterized values and `ORDER BY marked_at DESC, snapshot_sha256 DESC`.
- Create `src/polymarket_alpha_lab/paper_nav_snapshot_psycopg.py`
  - Optional wrapper functions that import psycopg only inside calls.
  - Adapt dict/list SQL params with `Jsonb`.
  - Commit on success, rollback on any exception, close in all paths, and redact DSNs from connection errors.
- Create `supabase/migrations/20260619010100_paper_nav_snapshots.sql`
  - `public.paper_nav_snapshots` table with `payload_json jsonb`, NAV summary columns, `paper_only` check, and lookup indexes.
- Create tests:
  - `tests/test_paper_nav_snapshot_db_row.py`
  - `tests/test_paper_nav_snapshot_store.py`
  - `tests/test_paper_nav_snapshot_psycopg.py`
  - `tests/test_paper_nav_snapshot_schema.py`

## Task 1: Row Codec Tests And Implementation

**Files:**
- Create: `tests/test_paper_nav_snapshot_db_row.py`
- Create: `src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py`

- [ ] **Step 1: Write failing tests**

```python
from polymarket_alpha_lab.paper_nav_snapshot_db_row import (
    PaperNavSnapshotDbRow,
    paper_nav_snapshot_from_db_row,
    paper_nav_snapshot_to_db_row,
)

def test_nav_snapshot_db_row_serializes_canonical_payload_and_round_trips():
    snapshot = _snapshot()
    row = paper_nav_snapshot_to_db_row(snapshot)
    assert row.mark_count == 1
    assert row.payload_json["marks"][0]["cost_basis"] == "4.00"
    assert paper_nav_snapshot_from_db_row(row) == snapshot
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_db_row.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.paper_nav_snapshot_db_row'`.

- [ ] **Step 3: Implement minimal codec**

```python
@dataclass(frozen=True)
class PaperNavSnapshotDbRow:
    snapshot_sha256: str
    marked_at: datetime
    starting_cash: Decimal
    cash_balance: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    unrealized_exit_pnl: Decimal
    mark_count: int
    payload_json: dict[str, Any]
    paper_only: bool = True
```

Use `dataclasses.asdict`, recursive JSON conversion, `json.dumps(..., sort_keys=True, separators=(",", ":"))`, and `json_recovery.from_jsonable(PaperNavSnapshot, payload_json)`.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_db_row.py -q`

Expected: PASS.

## Task 2: DB-API Store Tests And Implementation

**Files:**
- Create: `tests/test_paper_nav_snapshot_store.py`
- Create: `src/polymarket_alpha_lab/paper_nav_snapshot_store.py`

- [ ] **Step 1: Write failing tests**

```python
def test_insert_paper_nav_snapshot_uses_parameterized_insert(store_module):
    inserted = store_module.insert_paper_nav_snapshot(connection, snapshot)
    assert inserted.snapshot_sha256 == "a" * 64
    assert params[-2:] == (payload_json, True)
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_store.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.paper_nav_snapshot_store'`.

- [ ] **Step 3: Implement minimal store**

```python
def insert_paper_nav_snapshot(connection, snapshot, *, table_name="paper_nav_snapshots"):
    table_name = _validate_table_name(table_name)
    row = paper_nav_snapshot_to_db_row(snapshot)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row
```

`load_paper_nav_snapshots` selects the same summary columns and returns decoded snapshots.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_store.py -q`

Expected: PASS.

## Task 3: Optional Psycopg Adapter Tests And Implementation

**Files:**
- Create: `tests/test_paper_nav_snapshot_psycopg.py`
- Create: `src/polymarket_alpha_lab/paper_nav_snapshot_psycopg.py`

- [ ] **Step 1: Write failing tests**

```python
def test_insert_opens_psycopg_connection_delegates_commits_and_closes(adapter_module):
    inserted = adapter_module.insert_paper_nav_snapshot_with_psycopg(dsn, snapshot)
    assert inserted == row
    assert connection.commit_count == 1
    assert connection.close_count == 1
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_psycopg.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.paper_nav_snapshot_psycopg'`.

- [ ] **Step 3: Implement adapter**

```python
def _with_owned_connection(dsn, operation):
    jsonb_adapter = _jsonb_adapter()
    connection = _PsycopgJsonConnection(_connect(dsn), jsonb_adapter)
    try:
        result = operation(connection)
        connection.commit()
        return result
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
```

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_psycopg.py -q`

Expected: PASS.

## Task 4: Migration Tests And SQL

**Files:**
- Create: `tests/test_paper_nav_snapshot_schema.py`
- Create: `supabase/migrations/20260619010100_paper_nav_snapshots.sql`

- [ ] **Step 1: Write failing schema test**

```python
def test_migration_creates_nav_snapshot_table_with_required_columns():
    body = table_body(migration_sql())
    assert "snapshot_sha256 text primary key" in body
    assert "payload_json jsonb not null" in body
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_schema.py -q`

Expected: FAIL with missing migration file.

- [ ] **Step 3: Add migration**

```sql
create table if not exists public.paper_nav_snapshots (
  snapshot_sha256 text primary key,
  marked_at timestamptz not null,
  payload_json jsonb not null,
  paper_only boolean not null default true
);
```

Add all required NAV summary columns, checks, and indexes.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/test_paper_nav_snapshot_schema.py -q`

Expected: PASS.

## Final Verification

- [ ] Run targeted suite:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_nav_snapshot_db_row.py \
  tests/test_paper_nav_snapshot_store.py \
  tests/test_paper_nav_snapshot_psycopg.py \
  tests/test_paper_nav_snapshot_schema.py \
  -q
```

- [ ] Run whitespace check:

```bash
git diff --check
```

- [ ] Confirm no writes outside the allowed file list:

```bash
git status --short
```

No commit, stage, push, CLI wiring, runner wiring, portfolio NAV wiring, live-account access, wallet/auth/private-key code, or order book fetching is part of this plan.
