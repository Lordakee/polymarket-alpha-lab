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
