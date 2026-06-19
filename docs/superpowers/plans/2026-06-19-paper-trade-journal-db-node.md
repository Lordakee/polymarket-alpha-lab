# Paper Trade Journal DB Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the DB-first repository layer for paper trade journal records without wiring it into the CLI, runner, or strategy cycle.

**Architecture:** Mirror the existing paper recommendation cycle snapshot DB slice with a narrow row codec, a DB-API store, an optional psycopg adapter, and one Supabase migration. The slice persists only `PaperTradeRecord` payloads and summary columns; it never submits orders, reads accounts, handles wallet credentials, or changes trading flow.

**Tech Stack:** Python dataclasses, DB-API cursors, optional psycopg `Jsonb`, PostgreSQL/Supabase SQL migration, pytest.

---

### Task 1: Row Codec Tests

**Files:**
- Create: `tests/test_paper_trade_journal_db_row.py`
- Create: `src/polymarket_alpha_lab/paper_trade_journal_db_row.py`

- [ ] **Step 1: Write the failing codec tests**

Add tests that build a real `PaperTradeRecord`, call `paper_trade_record_to_db_row(record)`, and assert:

```python
assert type(row) is PaperTradeJournalDbRow
assert len(row.record_sha256) == 64
assert row.packet_id == record.packet_id
assert row.fill_average_price == Decimal("0.514")
assert row.payload_json["model_probability"] == "0.56"
assert row.payload_json["decision_timestamp_utc"] == "2026-06-13T12:31:00+00:00"
assert paper_trade_record_from_db_row(row) == record
```

Also add negative tests for wrong record type/subclass, `paper_only=False`, payload float rejection, corrupted record float rejection, malformed payload recovery, and hash mismatch.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_db_row.py -q
```

Expected: fail because `polymarket_alpha_lab.paper_trade_journal_db_row` does not exist yet.

- [ ] **Step 3: Implement the row codec**

Create `PaperTradeJournalDbRow` as a frozen dataclass with:

```python
record_sha256: str
packet_id: str
decision_timestamp_utc: datetime
condition_id: str
token_id: str
market_slug: str
outcome_name: str
order_side: str
fill_status: str
fill_filled_size: Decimal
fill_average_price: Decimal
account_equity_before_trade: Decimal
payload_json: dict[str, Any]
paper_only: bool = True
```

Implement `paper_trade_record_to_db_row(record)` and `paper_trade_record_from_db_row(row)` using canonical JSON payload hashing:

```python
encoded = json.dumps(payload_json, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
record_sha256 = hashlib.sha256(encoded).hexdigest()
```

Use `_json_ready()` to convert `Decimal` and `datetime` values to strings and reject all floats.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_db_row.py -q
```

Expected: all codec tests pass.

### Task 2: DB-API Store Tests

**Files:**
- Create: `tests/test_paper_trade_journal_store.py`
- Create: `src/polymarket_alpha_lab/paper_trade_journal_store.py`

- [ ] **Step 1: Write the failing store tests**

Add fake cursor/connection tests that assert:

```python
insert_paper_trade_record(connection, record)
load_paper_trade_records(connection, condition_id="0xabc", token_id="111", limit=25)
```

use parameterized SQL, close cursors, do not commit, validate table names with the same simple lowercase identifier pattern as the snapshot store, reject invalid limits, map DB rows back through `paper_trade_record_from_db_row`, and sort loads by:

```sql
ORDER BY decision_timestamp_utc DESC, record_sha256 DESC
```

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_store.py -q
```

Expected: fail because `polymarket_alpha_lab.paper_trade_journal_store` does not exist yet.

- [ ] **Step 3: Implement the store**

Create:

```python
insert_paper_trade_record(connection, record, *, table_name="paper_trade_journal_records")
load_paper_trade_records(connection, *, condition_id=None, token_id=None, limit=None, table_name="paper_trade_journal_records")
```

Use `INSERT ... ON CONFLICT (record_sha256) DO NOTHING`, `%s` parameters, a validated table identifier, optional `WHERE condition_id = %s` / `token_id = %s`, and `LIMIT %s`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_store.py -q
```

Expected: all store tests pass.

### Task 3: Optional psycopg Adapter Tests

**Files:**
- Create: `tests/test_paper_trade_journal_psycopg.py`
- Create: `src/polymarket_alpha_lab/paper_trade_journal_psycopg.py`

- [ ] **Step 1: Write the failing psycopg tests**

Add tests for:

```python
insert_paper_trade_record_with_psycopg(dsn, record, table_name="paper_trade_archive")
load_paper_trade_records_with_psycopg(dsn, condition_id="0xabc", token_id="111", limit=10)
```

Cover import-time optional dependency, missing dependency error, connect redaction, commit/rollback/close behavior, and `Jsonb` wrapping for dict/list params only.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_psycopg.py -q
```

Expected: fail because `polymarket_alpha_lab.paper_trade_journal_psycopg` does not exist yet.

- [ ] **Step 3: Implement the adapter**

Mirror `paper_recommendation_cycle_snapshot_psycopg.py` with paper trade journal names and redacted errors:

```python
def _adapt_json_params(params, jsonb_adapter):
    return tuple(jsonb_adapter(param) if isinstance(param, (dict, list)) else param for param in params)
```

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_psycopg.py -q
```

Expected: all adapter tests pass.

### Task 4: Supabase Migration Tests

**Files:**
- Create: `tests/test_paper_trade_journal_schema.py`
- Create: `supabase/migrations/20260619010000_paper_trade_journal_records.sql`

- [ ] **Step 1: Write the failing schema tests**

Assert the migration creates `public.paper_trade_journal_records` with the required summary columns, JSONB payload, `paper_only` invariant, primary key hash, and useful lookup indexes.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_schema.py -q
```

Expected: fail because the migration file does not exist yet.

- [ ] **Step 3: Implement the migration**

Create the table and indexes:

```sql
create table if not exists public.paper_trade_journal_records (...);
create index if not exists idx_ptjr_decision_timestamp on public.paper_trade_journal_records (decision_timestamp_utc desc);
create index if not exists idx_ptjr_condition_decision on public.paper_trade_journal_records (condition_id, decision_timestamp_utc desc);
create index if not exists idx_ptjr_token_decision on public.paper_trade_journal_records (token_id, decision_timestamp_utc desc);
create index if not exists idx_ptjr_payload_json_gin on public.paper_trade_journal_records using gin (payload_json jsonb_path_ops);
```

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_schema.py -q
```

Expected: schema tests pass.

### Task 5: Final Verification

**Files:**
- Verify only the allowed files changed.

- [ ] **Step 1: Run the targeted test suite**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_journal_db_row.py tests/test_paper_trade_journal_store.py tests/test_paper_trade_journal_psycopg.py tests/test_paper_trade_journal_schema.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 3: Review scope**

Run:

```bash
git status --short
```

Expected: only the new plan, modules, tests, and migration from this plan are listed. Do not stage, commit, or push.
