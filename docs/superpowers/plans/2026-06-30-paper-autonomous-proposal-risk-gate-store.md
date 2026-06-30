# Paper Autonomous Proposal Risk Gate Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure local paper-only storage boundary for `PaperAutonomousProposalRiskGateReport` so autonomous investment can persist and replay proposal risk gate reports without live trading integration.

**Architecture:** Keep the existing pure reducer in `paper_autonomous_proposal_risk_gate.py` unchanged. Add a row codec that materializes query fields plus a canonical JSON payload, and a DB-API repository that inserts/loads rows through caller-owned local Postgres/Supabase connections. Do not wire this into CLI, NAV, auth, wallet, or order mutation paths.

**Tech Stack:** Python frozen dataclasses, `Decimal`, DB-API compatible local Postgres/Supabase connections, optional `psycopg` adapter.

## Global Constraints

- Pure local/report-only/paper_only True.
- Decimal-only where numeric money/probability is used.
- Frozen dataclasses.
- No live trading/auth/wallet/order mutation.
- Durable data through local Supabase/Postgres only if storage is included.
- Avoid current NAV/CLI files.
- Do not touch `src/polymarket_alpha_lab/cli.py` or `README.md` unless necessary.

---

### Task 1: DB Row Codec

**Files:**
- Create: `tests/test_paper_autonomous_proposal_risk_gate_db_row.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_proposal_risk_gate_db_row.py`

**Interfaces:**
- Consumes: `PaperAutonomousProposalRiskGateReport`
- Produces: `PaperAutonomousProposalRiskGateDbRow`, `to_db_row(report)`, `from_db_row(row)`, `paper_autonomous_proposal_risk_gate_report_to_db_row(report)`, `paper_autonomous_proposal_risk_gate_report_from_db_row(row)`

- [x] **Step 1: Write the failing codec test**

```python
def test_proposal_risk_gate_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    report = _risk_gate_report()
    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousProposalRiskGateDbRow
    assert row.gate_status == "pass"
    assert row.source_proposal_total_notional == Decimal("10.000000")
    assert row.payload_json["source_proposal_total_notional"] == "10.000000"
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert codec.from_db_row(row) == report
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_paper_autonomous_proposal_risk_gate_db_row.py -q`

Expected: FAIL with missing module `polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row`.

- [x] **Step 3: Write minimal implementation**

Create a frozen DB row dataclass with these materialized fields:

```python
report_sha256: str
generated_at: datetime
config_version: str
gate_status: str
recommended_next_step: str
source_proposal_status: str
source_proposal_count: int
source_proposal_total_notional: Decimal
blocked_reason_codes_json: list[str]
watch_reason_codes_json: list[str]
reason_codes_json: list[str]
payload_json: dict[str, Any]
paper_only: bool = True
report_only: bool = True
readonly: bool = True
```

Serialize Decimal payload values as fixed six-place strings, reject floats/raw Decimal/raw datetime inside stored JSON, hash the canonical payload, and rebuild the report with `json_recovery.from_jsonable`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_paper_autonomous_proposal_risk_gate_db_row.py -q`

Expected: PASS.

### Task 2: DB-API Store

**Files:**
- Create: `tests/test_paper_autonomous_proposal_risk_gate_store.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_proposal_risk_gate_store.py`

**Interfaces:**
- Consumes: `PaperAutonomousProposalRiskGateDbRow`
- Produces: `insert_paper_autonomous_proposal_risk_gate_report(connection, report, table_name=...)`, `insert_paper_autonomous_proposal_risk_gate_report_with_result(...)`, `load_paper_autonomous_proposal_risk_gate_reports(connection, config_version=None, gate_status=None, source_proposal_status=None, limit=None, table_name=...)`

- [x] **Step 1: Write the failing store test**

```python
def test_insert_proposal_risk_gate_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection()
    report = _risk_gate_report()
    expected_row = _db_row()

    inserted = insert_paper_autonomous_proposal_risk_gate_report(connection, report)

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    assert connection.cursor_instance.calls[0][1] == _row_values(expected_row)
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_paper_autonomous_proposal_risk_gate_store.py -q`

Expected: FAIL with missing module `polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store`.

- [x] **Step 3: Write minimal implementation**

Use the DB-API pattern from adjacent stores: validate safe local Postgres table identifiers, never interpolate values into SQL, close cursors, do not manage caller-owned transactions, and order loads by newest report.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_paper_autonomous_proposal_risk_gate_store.py -q`

Expected: PASS.

### Task 3: Optional Psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_proposal_risk_gate_psycopg.py`

**Interfaces:**
- Consumes: local Postgres/Supabase DSN string and store functions.
- Produces: `insert_paper_autonomous_proposal_risk_gate_report_with_psycopg(...)`, `load_paper_autonomous_proposal_risk_gate_reports_with_psycopg(...)`.

- [ ] **Step 1: Add adapter only after DB-API store passes**

```python
def insert_paper_autonomous_proposal_risk_gate_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE,
) -> Any:
    return _with_owned_write_connection(
        dsn,
        lambda connection: insert_paper_autonomous_proposal_risk_gate_report_with_result(
            connection,
            report,
            table_name=table_name,
        ),
    )
```

- [ ] **Step 2: Verify focused tests still pass**

Run: `pytest tests/test_paper_autonomous_proposal_risk_gate_db_row.py tests/test_paper_autonomous_proposal_risk_gate_store.py tests/test_paper_autonomous_proposal_risk_gate.py -q`

Expected: PASS.

### Integration Notes

The storage table should be created by deployment/migration tooling outside this task:

```sql
CREATE TABLE paper_autonomous_proposal_risk_gate_reports (
    report_sha256 text PRIMARY KEY,
    generated_at timestamptz NOT NULL,
    config_version text NOT NULL,
    gate_status text NOT NULL,
    recommended_next_step text NOT NULL,
    source_proposal_status text NOT NULL,
    source_proposal_count integer NOT NULL,
    source_proposal_total_notional numeric NOT NULL,
    blocked_reason_codes_json jsonb NOT NULL,
    watch_reason_codes_json jsonb NOT NULL,
    reason_codes_json jsonb NOT NULL,
    payload_json jsonb NOT NULL,
    paper_only boolean NOT NULL DEFAULT true,
    report_only boolean NOT NULL DEFAULT true,
    readonly boolean NOT NULL DEFAULT true,
    inserted_at timestamptz NOT NULL DEFAULT now()
);
```

No CLI, README, NAV, wallet, auth, or order path should import these modules until a separate integration task explicitly asks for wiring.
