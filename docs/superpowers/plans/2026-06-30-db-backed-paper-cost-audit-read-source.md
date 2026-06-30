# DB-Backed Paper Cost Audit Read Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local Supabase/Postgres-backed paper-trade read source for the paper cost audit only, while preserving JSONL fallback/export/replay and avoiding live trading, auth, wallet, or order mutation surfaces.

**Architecture:** Add a pure DB-API helper that reads `PaperTradeRecord` values through the existing paper journal store, converts the store's newest-first query result back into append chronology, and delegates all Decimal and paper-record validation to `build_paper_trade_cost_audit_report`. Keep psycopg connection handling and CLI selection outside the helper so this node stays read-only and disjoint from dirty shared CLI files.

**Tech Stack:** Python 3.11+, `Decimal`, existing `PaperTradeRecord` and cost-audit dataclasses, DB-API connection objects, local Supabase/Postgres through existing DSN validation, pytest.

## Global Constraints

- Local Supabase/Postgres only.
- JSONL fallback/export/replay remains supported and unchanged.
- No new durable file storage.
- No live trading, auth, wallet, or order mutation code.
- Paper records must remain Decimal-only; no float coercion or rounded file export.
- The new helper is for paper cost audit only, not trend history, persistence, or live execution.
- Do not edit shared CLI, docs, or existing tests unless the worker owns those files or has a clean isolated handoff.

---

## File Structure

- Create: `src/polymarket_alpha_lab/paper_trade_journal_db_cost_audit_load.py`
  - Responsibility: read paper trade records from the existing journal DB store and build one `PaperTradeCostAuditReport`.
  - Must not import `psycopg`, `os`, HTTP clients, wallet/auth modules, or any writer/mutation helpers.
- Create: `tests/test_paper_trade_journal_db_cost_audit_load.py`
  - Responsibility: prove the helper delegates to the read-only store, preserves append chronology, returns paper/report/read-only audit output, rejects non-Decimal records through the audit boundary, and has no forbidden imports or mutation strings.
- Do not modify: `src/polymarket_alpha_lab/cli.py`
  - CLI read-source selection is an integration step after shared CLI ownership is clear.
- Do not modify: `src/polymarket_alpha_lab/paper_trade_journal_store.py`
  - Existing `load_paper_trade_records` is sufficient for this helper.
- Do not modify: `PaperTradeJournal.read`
  - Existing JSONL read, export, and replay behavior remains the fallback path.

## Task 1: Pure DB Cost-Audit Read Helper

**Files:**
- Create: `tests/test_paper_trade_journal_db_cost_audit_load.py`
- Create: `src/polymarket_alpha_lab/paper_trade_journal_db_cost_audit_load.py`

**Interfaces:**
- Consumes:
  - `paper_trade_journal_store.load_paper_trade_records(connection, condition_id=None, token_id=None, limit=None, table_name="paper_trade_journal_records") -> tuple[PaperTradeRecord, ...]`
  - `build_paper_trade_cost_audit_report(trade_records, *, config: PaperTradeCostAuditConfig, generated_at: datetime) -> PaperTradeCostAuditReport`
- Produces:
  - `load_paper_trade_journal_db_cost_audit_report(*, generated_at: datetime, config_version: str, connection: Any, condition_id: str | None = None, token_id: str | None = None, limit: int | None = None, table_name: str = "paper_trade_journal_records") -> PaperTradeCostAuditReport`

- [x] **Step 1: Write the failing tests**

Create `tests/test_paper_trade_journal_db_cost_audit_load.py` with this content:

```python
from __future__ import annotations

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_trade_journal_db_cost_audit_load as db_cost_audit
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
)


GENERATED_AT = datetime(2026, 6, 17, 10, 0, tzinfo=UTC)
COST_AUDIT_CONFIG_VERSION = "paper-trade-cost-audit-v0"
COST_AUDIT_CONFIG = PaperTradeCostAuditConfig(
    config_version=COST_AUDIT_CONFIG_VERSION,
)
HEX = "a" * 64


def _record(
    index: int,
    *,
    requested_size: Decimal = Decimal("100"),
    filled_size: Decimal = Decimal("100"),
    unfilled_size: Decimal = Decimal("0"),
    theoretical_edge: Decimal = Decimal("0.060000"),
    cost_adjusted_edge: Decimal = Decimal("0.040000"),
    research_slippage: Decimal = Decimal("0.004000"),
    fill_slippage: Decimal | None = Decimal("0.006000"),
) -> PaperTradeRecord:
    return PaperTradeRecord(
        packet_id=f"pkt-{index}",
        packet_created_at=datetime(2026, 6, 17, 9, index, tzinfo=UTC),
        condition_id=f"0x{index:04x}",
        token_id=f"{index}",
        market_slug=f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will market {index} resolve yes?",
        outcome_name="YES",
        strategy_type="market_quality",
        source_score="80.000",
        market_raw_archive_path=f"data/raw/gamma/market-{index}.json",
        order_book_raw_archive_path=f"data/raw/clob/book-{index}.json",
        order_book_raw_payload_sha256=HEX,
        order_book_snapshot_sha256=HEX,
        risk_tags=("liquidity",),
        rule_text_hash=HEX,
        resolution_source="Official source",
        decision_timestamp_utc=datetime(2026, 6, 17, 9, index, 30, tzinfo=UTC),
        model_probability=Decimal("0.6000"),
        confidence=Decimal("0.8000"),
        research_bid=Decimal("0.5000"),
        research_ask=Decimal("0.5400"),
        research_midpoint=Decimal("0.5200"),
        research_expected_entry_price=Decimal("0.5400"),
        research_fair_value_estimate=Decimal("0.6000"),
        research_theoretical_edge=theoretical_edge,
        research_spread=Decimal("0.0400"),
        research_slippage_estimate=research_slippage,
        research_cost_adjusted_edge=cost_adjusted_edge,
        max_executable_size=Decimal("100"),
        order_side="buy",
        order_requested_size=requested_size,
        fill_filled_size=filled_size,
        fill_unfilled_size=unfilled_size,
        fill_status="complete" if unfilled_size == 0 else "partial",
        fill_average_price=Decimal("0.5400"),
        fill_worst_price=Decimal("0.5500"),
        fill_best_bid=Decimal("0.5000"),
        fill_best_ask=Decimal("0.5400"),
        fill_midpoint=Decimal("0.5200"),
        fill_spread=Decimal("0.0400"),
        fill_slippage_estimate=fill_slippage,
        order_book_captured_at=datetime(2026, 6, 17, 9, index, 20, tzinfo=UTC),
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Hold to resolution.",
        thesis="Paper test thesis.",
        invalidating_conditions="Resolution source changes.",
    )


def test_load_paper_trade_journal_db_cost_audit_filters_limits_and_builds_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    older_record = _record(1)
    newest_record = _record(
        2,
        requested_size=Decimal("100"),
        filled_size=Decimal("40"),
        unfilled_size=Decimal("60"),
        theoretical_edge=Decimal("0.030000"),
        cost_adjusted_edge=Decimal("-0.010000"),
        research_slippage=Decimal("0.002000"),
        fill_slippage=None,
    )
    calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        calls.append((connection_arg, condition_id, token_id, limit, table_name))
        return (newest_record, older_record)

    monkeypatch.setattr(
        db_cost_audit.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )

    report = db_cost_audit.load_paper_trade_journal_db_cost_audit_report(
        generated_at=GENERATED_AT,
        config_version=COST_AUDIT_CONFIG_VERSION,
        connection=connection,
        condition_id="0x0002",
        token_id="2",
        limit=25,
        table_name="paper_trade_archive",
    )

    assert calls == [(connection, "0x0002", "2", 25, "paper_trade_archive")]
    assert type(report) is PaperTradeCostAuditReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == COST_AUDIT_CONFIG_VERSION
    assert report.trade_count == 2
    assert report.total_filled_size == Decimal("140")
    assert report.total_requested_size == Decimal("200")
    assert report.fill_rate == Decimal("0.700000")
    assert report.negative_cost_adjusted_edge_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_paper_trade_journal_db_cost_audit_passes_records_in_append_chronology(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    older_record = _record(1)
    newest_record = _record(2)
    built_report = object()
    build_calls: list[
        tuple[tuple[PaperTradeRecord, ...], PaperTradeCostAuditConfig, datetime]
    ] = []

    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        return (newest_record, older_record)

    def build_audit(
        records: tuple[PaperTradeRecord, ...],
        *,
        config: PaperTradeCostAuditConfig,
        generated_at: datetime,
    ) -> object:
        build_calls.append((tuple(records), config, generated_at))
        return built_report

    monkeypatch.setattr(
        db_cost_audit.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )
    monkeypatch.setattr(
        db_cost_audit,
        "build_paper_trade_cost_audit_report",
        build_audit,
    )

    report = db_cost_audit.load_paper_trade_journal_db_cost_audit_report(
        generated_at=GENERATED_AT,
        config_version=COST_AUDIT_CONFIG_VERSION,
        connection=object(),
    )

    assert report is built_report
    assert build_calls == [
        ((older_record, newest_record), COST_AUDIT_CONFIG, GENERATED_AT),
    ]


def test_load_paper_trade_journal_db_cost_audit_allows_empty_trade_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        return ()

    monkeypatch.setattr(
        db_cost_audit.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )

    report = db_cost_audit.load_paper_trade_journal_db_cost_audit_report(
        generated_at=GENERATED_AT,
        config_version=COST_AUDIT_CONFIG_VERSION,
        connection=object(),
    )

    assert report.trade_count == 0
    assert report.total_filled_size == Decimal("0")
    assert report.total_requested_size == Decimal("0")
    assert report.fill_rate is None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_paper_trade_journal_db_cost_audit_rejects_non_decimal_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _record(1)
    object.__setattr__(record, "fill_average_price", 0.54)

    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        return (record,)

    monkeypatch.setattr(
        db_cost_audit.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )

    with pytest.raises(ValueError, match="fill_average_price|Decimal"):
        db_cost_audit.load_paper_trade_journal_db_cost_audit_report(
            generated_at=GENERATED_AT,
            config_version=COST_AUDIT_CONFIG_VERSION,
            connection=object(),
        )


def test_paper_trade_journal_db_cost_audit_load_module_has_no_mutation_or_live_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_trade_journal_db_cost_audit_load.py"
    )
    module = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "eth_account",
        "http",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "wallet",
        "websocket",
        "websockets",
    }

    source = module_path.read_text(encoding="utf-8").lower()
    for banned in (
        "api_key",
        "cancel_order",
        "insert_paper_trade_record",
        "private_key",
        "replace_order",
        "submit_order",
        "wallet",
    ):
        assert banned not in source
```

- [x] **Step 2: Run tests to verify the missing helper fails**

Run:

```bash
pytest tests/test_paper_trade_journal_db_cost_audit_load.py -q
```

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.paper_trade_journal_db_cost_audit_load'`.

- [x] **Step 3: Add the minimal helper implementation**

Create `src/polymarket_alpha_lab/paper_trade_journal_db_cost_audit_load.py` with this content:

```python
"""Read-only DB helper for paper-trade cost audit source records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_trade_journal_store
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)


def load_paper_trade_journal_db_cost_audit_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    condition_id: str | None = None,
    token_id: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_trade_journal_records",
) -> PaperTradeCostAuditReport:
    newest_first_records = paper_trade_journal_store.load_paper_trade_records(
        connection,
        condition_id=condition_id,
        token_id=token_id,
        limit=limit,
        table_name=table_name,
    )
    append_chronology_records = tuple(reversed(newest_first_records))
    return build_paper_trade_cost_audit_report(
        append_chronology_records,
        config=PaperTradeCostAuditConfig(config_version=config_version),
        generated_at=generated_at,
    )


__all__ = (
    "load_paper_trade_journal_db_cost_audit_report",
)
```

- [x] **Step 4: Run the focused helper tests**

Run:

```bash
pytest tests/test_paper_trade_journal_db_cost_audit_load.py -q
```

Expected: PASS with `5 passed`.

- [x] **Step 5: Run adjacent read-store and cost-audit regression tests**

Run:

```bash
pytest tests/test_paper_trade_journal_store.py tests/test_paper_trade_cost_audit.py tests/test_paper_trade_journal_db_cost_trend_load.py -q
```

Expected: PASS for all selected tests.

## Task 2: CLI Integration Handoff

**Files:**
- Deferred shared file: `src/polymarket_alpha_lab/cli.py`
- Deferred shared tests: `tests/test_cli.py`, `tests/test_cli_cost_audit_persistence.py`, `tests/test_cli_cost_audit_db_trend.py`

**Interfaces:**
- Consumes:
  - `load_paper_trade_journal_db_cost_audit_report(...) -> PaperTradeCostAuditReport`
  - Existing `PaperTradeJournal.read(path) -> tuple[PaperTradeRecord, ...]`
  - Existing local DSN validation from `SupabasePaperTradeJournalConfig` or a new read-source config with the same `validate_local_postgres_dsn` boundary.
- Produces:
  - A mutually exclusive read-source selection that uses DB records only when explicitly requested and otherwise continues reading JSONL.

- [ ] **Step 1: Confirm CLI file ownership**

Run:

```bash
git status --short src/polymarket_alpha_lab/cli.py tests/test_cli.py tests/test_cli_cost_audit_persistence.py tests/test_cli_cost_audit_db_trend.py
```

Expected before editing: either no output for those files, or an explicit handoff from the worker who owns the dirty changes.

- [ ] **Step 2: Add tests for explicit DB source selection**

In the CLI test file owned by the implementer, add a test with this shape:

```python
def test_cost_audit_cli_db_read_source_uses_local_paper_trade_journal_without_jsonl(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://paper-journal:secret@localhost:54322/db"
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_DSN", dsn)
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_TABLE",
        "paper_trade_journal_archive",
    )
    jsonl_path = tmp_path / "paper-trades.jsonl"
    read_calls = []
    db_source_calls = []

    def forbidden_jsonl_read(path):
        read_calls.append(path)
        raise AssertionError("JSONL read must not run for explicit DB source")

    def fake_db_source(**kwargs):
        db_source_calls.append(kwargs)
        return PaperTradeCostAuditReport(
            generated_at=datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
            config_version="paper-trade-cost-audit-v0",
            trade_count=0,
            total_filled_size=Decimal("0"),
            total_requested_size=Decimal("0"),
            fill_rate=None,
            mean_theoretical_edge=None,
            mean_cost_adjusted_edge=None,
            mean_edge_cost_drag=None,
            total_edge_cost_drag=None,
            mean_research_slippage=None,
            mean_fill_slippage=None,
            partial_fill_count=0,
            negative_cost_adjusted_edge_count=0,
            largest_single_trade_cost_drag=None,
        )

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(jsonl_path),
            "--read-source",
            "db",
        ],
        paper_trade_journal_reader=forbidden_jsonl_read,
        paper_trade_cost_audit_db_read_source=fake_db_source,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert read_calls == []
    assert len(db_source_calls) == 1
    assert db_source_calls[0]["dsn"] == dsn
    assert db_source_calls[0]["table_name"] == "paper_trade_journal_archive"
    captured = capsys.readouterr()
    assert dsn not in captured.out
    assert dsn not in captured.err
```

- [ ] **Step 3: Preserve JSONL fallback with an explicit regression**

Add a companion test:

```python
def test_cost_audit_cli_keeps_jsonl_fallback_when_db_source_not_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED",
        "not-a-bool",
    )
    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")
    db_source_calls = []

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
        ],
        cost_audit_runner=lambda **kwargs: PaperTradeCostAuditReport(
            generated_at=datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
            config_version="paper-trade-cost-audit-v0",
            trade_count=0,
            total_filled_size=Decimal("0"),
            total_requested_size=Decimal("0"),
            fill_rate=None,
            mean_theoretical_edge=None,
            mean_cost_adjusted_edge=None,
            mean_edge_cost_drag=None,
            total_edge_cost_drag=None,
            mean_research_slippage=None,
            mean_fill_slippage=None,
            partial_fill_count=0,
            negative_cost_adjusted_edge_count=0,
            largest_single_trade_cost_drag=None,
        ),
        paper_trade_cost_audit_db_read_source=lambda **kwargs: db_source_calls.append(kwargs),
    )

    assert exit_code == 0
    assert db_source_calls == []
    captured = capsys.readouterr()
    assert "cost-audit:" in captured.out
```

- [ ] **Step 4: Wire CLI only after the tests fail for the expected missing option/dependency reason**

Add a `--read-source {jsonl,db}` option or equivalent explicit source selector to the cost-audit command. The JSONL branch must keep the current `PaperTradeJournal.read(trade_log)` path. The DB branch must validate the journal DB config with the local-only DSN boundary and call the new helper through a psycopg-owned connection adapter, without adding any file writes.

- [ ] **Step 5: Run CLI and scope tests**

Run:

```bash
pytest tests/test_cli.py tests/test_cli_cost_audit_persistence.py tests/test_cli_cost_audit_db_trend.py tests/test_paper_trade_journal_db_cost_audit_load.py -q
```

Expected: PASS for the owned CLI tests and the new helper tests, with no DSN leakage in stdout or stderr.

## Self-Review

- Spec coverage: Task 1 covers the pure DB read source, Decimal-only paper records, read-only behavior, and no live/auth/wallet/order mutation imports. Task 2 covers explicit integration while preserving JSONL fallback/export/replay.
- Placeholder scan: This plan names concrete files, commands, signatures, and expected test results. It avoids unspecified future work inside implemented tasks.
- Type consistency: `load_paper_trade_journal_db_cost_audit_report` uses `datetime`, `str`, `Any`, optional string filters, optional positive integer limit, and returns `PaperTradeCostAuditReport`, matching existing cost-audit and journal-store interfaces.
