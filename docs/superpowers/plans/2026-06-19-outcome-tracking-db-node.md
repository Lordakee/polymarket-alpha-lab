# Outcome Tracking DB Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist `OutcomeTrackingReport` values to a narrow DB-first repository layer without wiring CLI, check-outcomes, or local observability paths.

**Architecture:** Copy the existing paper recommendation cycle snapshot persistence pattern into outcome-tracking-specific files. Keep serialization pure in the row codec, SQL generation in a DB-API store, and optional psycopg connection management in a wrapper with no import-time psycopg dependency.

**Tech Stack:** Python frozen dataclasses, DB-API `%s` parameter style, PostgreSQL JSONB migration, pytest.

---

## File Structure

- Create `src/polymarket_alpha_lab/outcome_tracking_db_row.py`: pure row codec for `OutcomeTrackingReport`, canonical JSON payload, sha256 primary key, Decimal/datetime string handling, float rejection, hard flag validation.
- Create `src/polymarket_alpha_lab/outcome_tracking_store.py`: DB-API repository functions `insert_outcome_tracking_report` and `load_outcome_tracking_reports`.
- Create `src/polymarket_alpha_lab/outcome_tracking_psycopg.py`: optional psycopg adapter with Jsonb param adaptation, redacted connect errors, and commit/rollback/close lifecycle.
- Create `supabase/migrations/20260619010200_outcome_tracking_reports.sql`: `public.outcome_tracking_reports` table with summary columns, JSONB payload, checks, and indexes.
- Create `tests/test_outcome_tracking_db_row.py`: codec round-trip, no-float payload, hash, hard flags, malformed payload validation.
- Create `tests/test_outcome_tracking_store.py`: parameterized SQL, table-name validation, query validation, and load row mapping.
- Create `tests/test_outcome_tracking_psycopg.py`: missing psycopg, connection redaction, Jsonb wrapping, commit/rollback/close behavior.
- Create `tests/test_outcome_tracking_schema.py`: migration text assertions and Phase 1 forbidden term guard.

## Task 1: DB Row Codec Tests

**Files:**
- Create: `tests/test_outcome_tracking_db_row.py`
- Create later: `src/polymarket_alpha_lab/outcome_tracking_db_row.py`

- [ ] **Step 1: Write failing codec tests**

```python
def test_outcome_tracking_db_row_serializes_summary_payload_and_round_trips():
    report = _resolved_report()
    row = outcome_tracking_report_to_db_row(report)
    assert type(row) is OutcomeTrackingReportDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.total_markets_checked == 1
    assert row.resolved_count == 1
    assert row.pending_count == 0
    assert row.observation_count == 1
    assert row.forecast_evidence_status == report.forecast_evidence_report.status
    assert row.payload_json["generated_at"] == "2026-06-19T19:00:00+00:00"
    assert row.payload_json["observations"][0]["predicted_probability"] == "0.6000"
    assert row.payload_json["paper_only"] is True
    assert outcome_tracking_report_from_db_row(row) == report
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_db_row.py -q`

Expected: collection fails with `ModuleNotFoundError` for `polymarket_alpha_lab.outcome_tracking_db_row`.

- [ ] **Step 3: Implement minimal codec**

Create `OutcomeTrackingReportDbRow`, `outcome_tracking_report_to_db_row`, and `outcome_tracking_report_from_db_row`. Serialize with `dataclasses.asdict`, recursively convert `Decimal` and UTC `datetime` to strings, reject floats anywhere, compute `report_sha256` from sorted compact JSON, and recover with `json_recovery.from_jsonable(OutcomeTrackingReport, payload_json)`.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_db_row.py -q`

Expected: all codec tests pass.

## Task 2: DB-API Store Tests

**Files:**
- Create: `tests/test_outcome_tracking_store.py`
- Create later: `src/polymarket_alpha_lab/outcome_tracking_store.py`

- [ ] **Step 1: Write failing store tests**

```python
def test_insert_outcome_tracking_report_uses_parameterized_insert(store_module):
    inserted = store_module.insert_outcome_tracking_report(connection, report)
    sql, params = connection.cursor_instance.calls[0]
    assert "INSERT INTO outcome_tracking_reports" in normalize_sql(sql)
    assert "%s" in sql
    assert params == (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.total_markets_checked,
        row.resolved_count,
        row.pending_count,
        row.observation_count,
        row.forecast_evidence_status,
        row.payload_json,
        True,
    )
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_store.py -q`

Expected: collection fails with `ModuleNotFoundError` for `polymarket_alpha_lab.outcome_tracking_store`.

- [ ] **Step 3: Implement minimal store**

Validate table names with `^[a-z][a-z0-9_]*[a-z0-9]$`, validate `config_version` as nonblank canonical string, validate `limit` as positive `int` excluding bool, execute parameterized SQL, close cursors in `finally`, and map dict/namedtuple/positional rows to `OutcomeTrackingReportDbRow`.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_store.py -q`

Expected: all store tests pass.

## Task 3: psycopg Adapter Tests

**Files:**
- Create: `tests/test_outcome_tracking_psycopg.py`
- Create later: `src/polymarket_alpha_lab/outcome_tracking_psycopg.py`

- [ ] **Step 1: Write failing psycopg tests**

```python
def test_insert_adapts_json_values_for_psycopg_without_wrapping_scalars(monkeypatch, adapter_module):
    def fake_insert(connection_arg, report_arg, *, table_name):
        cursor = connection_arg.cursor()
        cursor.execute("insert", ({"payload": {"paper_only": True}}, ["tag"], "scalar"))
        cursor.close()
        return FakeRow(report_sha256="a" * 64)
    monkeypatch.setattr(adapter_module, "insert_outcome_tracking_report", fake_insert)
    adapter_module.insert_outcome_tracking_report_with_psycopg(SECRET_DSN, FakeReport("v1"))
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert isinstance(params[1], FakeJsonb)
    assert params[2] == "scalar"
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_psycopg.py -q`

Expected: collection fails with `ModuleNotFoundError` for `polymarket_alpha_lab.outcome_tracking_psycopg`.

- [ ] **Step 3: Implement minimal adapter**

Mirror the cycle snapshot psycopg adapter, but call outcome tracking store functions. Import `psycopg` and `Jsonb` only inside helper functions. Wrap dict/list params in `Jsonb`. On connect errors raise `RuntimeError("failed to connect to the outcome tracking database")` without chaining or echoing DSN.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_psycopg.py -q`

Expected: all psycopg tests pass.

## Task 4: Migration Schema Tests

**Files:**
- Create: `tests/test_outcome_tracking_schema.py`
- Create later: `supabase/migrations/20260619010200_outcome_tracking_reports.sql`

- [ ] **Step 1: Write failing schema tests**

```python
def test_migration_creates_outcome_tracking_table_with_required_columns():
    body = table_body(migration_sql())
    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "total_markets_checked integer not null",
        "resolved_count integer not null",
        "pending_count integer not null",
        "observation_count integer not null",
        "forecast_evidence_status text",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_schema.py -q`

Expected: failure says the migration file is missing.

- [ ] **Step 3: Implement migration**

Create `public.outcome_tracking_reports` with JSONB payload, sha256 check, nonnegative count checks, `resolved_count + pending_count = total_markets_checked`, `observation_count = resolved_count`, JSON object check, `paper_only is true`, and indexes for generated time, config version with generated time, forecast evidence status with generated time, and payload GIN.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_schema.py -q`

Expected: schema tests pass.

## Task 5: Final Verification

**Files:**
- Verify all created files listed above.

- [ ] **Step 1: Run targeted tests**

Run: `.venv/bin/python -m pytest tests/test_outcome_tracking_db_row.py tests/test_outcome_tracking_store.py tests/test_outcome_tracking_psycopg.py tests/test_outcome_tracking_schema.py -q`

Expected: all targeted tests pass.

- [ ] **Step 2: Run whitespace check**

Run: `git diff --check`

Expected: no output and exit code 0.

- [ ] **Step 3: Scope audit**

Run: `git diff --name-only`

Expected: only these files appear:

```text
docs/superpowers/plans/2026-06-19-outcome-tracking-db-node.md
src/polymarket_alpha_lab/outcome_tracking_db_row.py
src/polymarket_alpha_lab/outcome_tracking_psycopg.py
src/polymarket_alpha_lab/outcome_tracking_store.py
supabase/migrations/20260619010200_outcome_tracking_reports.sql
tests/test_outcome_tracking_db_row.py
tests/test_outcome_tracking_psycopg.py
tests/test_outcome_tracking_schema.py
tests/test_outcome_tracking_store.py
```

## Self-Review

- Spec coverage: The plan covers codec round-trip and float rejection, DB-API store validation and SQL, optional psycopg lifecycle and Jsonb adaptation, PostgreSQL schema, tests, and final verification.
- Boundary check: No task edits CLI, runner, outcome tracker, local observability, package exports, existing cycle snapshot files, environment files, `.omo`, or AGENTS.md.
- Phase 1 check: No task adds Gamma fetching, outcome parsing, settlement, actions, orders, wallet, auth, or private key handling.
