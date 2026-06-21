from __future__ import annotations

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_nav_snapshot_db_trend_load as db_trend_load
from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPositionMark


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
TREND_CONFIG_VERSION = "paper-nav-risk-trend-db-load-v0"
HEX = "a" * 64


def _mark(
    *,
    condition_id: str,
    token_id: str,
    market_slug: str,
    open_size: Decimal = Decimal("100.0000"),
    cost_basis: Decimal = Decimal("70.0000"),
    exit_value: Decimal = Decimal("100.0000"),
    mark_status: str = "fully_executable",
) -> PaperPositionMark:
    if mark_status == "fully_executable":
        exit_filled_size = open_size
        exit_unfilled_size = Decimal("0.0000")
        exit_average_price = (exit_value / open_size).quantize(Decimal("0.0001"))
        exit_worst_price = exit_average_price
        midpoint_price = Decimal("0.7000")
        midpoint_value = (open_size * midpoint_price).quantize(Decimal("0.0001"))
    elif mark_status == "partially_executable":
        exit_filled_size = open_size / Decimal("2")
        exit_unfilled_size = open_size - exit_filled_size
        exit_average_price = (exit_value / exit_filled_size).quantize(Decimal("0.0001"))
        exit_worst_price = exit_average_price
        midpoint_price = Decimal("0.6000")
        midpoint_value = (open_size * midpoint_price).quantize(Decimal("0.0001"))
    else:
        exit_filled_size = Decimal("0.0000")
        exit_unfilled_size = open_size
        exit_average_price = None
        exit_worst_price = None
        exit_value = Decimal("0.0000")
        midpoint_price = None
        midpoint_value = None

    return PaperPositionMark(
        condition_id=condition_id,
        token_id=token_id,
        market_slug=market_slug,
        outcome_name="YES",
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=(cost_basis / open_size).quantize(Decimal("0.0001")),
        order_book_captured_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        order_book_snapshot_sha256=HEX,
        exit_filled_size=exit_filled_size,
        exit_unfilled_size=exit_unfilled_size,
        exit_average_price=exit_average_price,
        exit_worst_price=exit_worst_price,
        exit_value=exit_value,
        midpoint_price=midpoint_price,
        midpoint_value=midpoint_value,
        best_bid=exit_average_price,
        best_ask=Decimal("0.8000") if exit_average_price is not None else None,
        spread=Decimal("0.1000") if exit_average_price is not None else None,
        slippage_estimate=Decimal("0.0000") if exit_average_price is not None else None,
        mark_status=mark_status,
    )


def _snapshot(
    marked_at: datetime,
    *,
    exit_nav: Decimal,
    marks: tuple[PaperPositionMark, ...] = (),
) -> PaperNavSnapshot:
    mark_exit_value = sum((mark.exit_value for mark in marks), Decimal("0"))
    cash_balance = exit_nav - mark_exit_value
    total_cost_basis = sum((mark.cost_basis for mark in marks), Decimal("0"))
    unrealized_exit_pnl = sum(
        (mark.exit_value - mark.cost_basis for mark in marks),
        Decimal("0"),
    )
    midpoint_nav = (
        cash_balance + sum((mark.midpoint_value for mark in marks), Decimal("0"))
        if all(mark.midpoint_value is not None for mark in marks)
        else None
    )
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=cash_balance + total_cost_basis,
        cash_balance=cash_balance,
        realized_pnl=Decimal("0.0000"),
        exit_nav=exit_nav,
        midpoint_nav=midpoint_nav,
        total_cost_basis=total_cost_basis,
        unrealized_exit_pnl=unrealized_exit_pnl,
        marks=marks,
    )


def _unsafe_snapshot(snapshot: PaperNavSnapshot, *, paper_only: bool) -> PaperNavSnapshot:
    unchecked = object.__new__(PaperNavSnapshot)
    for field_name in snapshot.__dataclass_fields__:
        object.__setattr__(unchecked, field_name, getattr(snapshot, field_name))
    object.__setattr__(unchecked, "paper_only", paper_only)
    return unchecked


def test_load_paper_nav_snapshot_db_trend_report_reverses_store_desc_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, int | None, str]] = []
    append_first = _snapshot(
        datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
        exit_nav=Decimal("10000.0000"),
    )
    append_second = _snapshot(
        datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        exit_nav=Decimal("9800.0000"),
        marks=(
            _mark(
                condition_id="condition-a",
                token_id="token-a",
                market_slug="market-a",
                open_size=Decimal("120.0000"),
                cost_basis=Decimal("80.0000"),
                exit_value=Decimal("0.0000"),
                mark_status="no_exit_depth",
            ),
        ),
    )
    append_latest = _snapshot(
        datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
        exit_nav=Decimal("10100.0000"),
        marks=(
            _mark(
                condition_id="condition-b",
                token_id="token-b",
                market_slug="market-b",
                open_size=Decimal("150.0000"),
                cost_basis=Decimal("90.0000"),
                exit_value=Decimal("150.0000"),
                mark_status="fully_executable",
            ),
        ),
    )

    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        calls.append((connection_arg, limit, table_name))
        return (append_latest, append_second, append_first)

    monkeypatch.setattr(
        db_trend_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    report = db_trend_load.load_paper_nav_snapshot_db_trend_report(
        generated_at=GENERATED_AT,
        config_version=TREND_CONFIG_VERSION,
        connection=connection,
        limit=10,
        table_name="paper_nav_archive",
    )

    assert calls == [(connection, 10, "paper_nav_archive")]
    assert report.generated_at == GENERATED_AT
    assert report.config_version == TREND_CONFIG_VERSION
    assert report.nav_risk_report_count == 3
    assert report.first_report_generated_at == GENERATED_AT
    assert report.latest_report_generated_at == GENERATED_AT
    assert report.latest_exit_nav == Decimal("10100.0000")
    assert report.latest_cumulative_return == Decimal("0.010000")
    assert report.latest_max_drawdown == Decimal("200.0000")
    assert report.latest_max_drawdown_pct == Decimal("0.020000")
    assert report.latest_nav_return_volatility == Decimal("0.025306")
    assert report.latest_open_position_count == 1
    assert report.latest_fully_executable_count == 1
    assert report.latest_partially_executable_count == 0
    assert report.latest_no_exit_depth_count == 0
    assert report.latest_largest_market_exposure_value == Decimal("150.0000")
    assert report.latest_largest_market_exposure_share == Decimal("0.014851")
    assert report.worst_observed_max_drawdown_pct == Decimal("0.020000")
    assert report.consecutive_unexecutable_open_position_count == 0
    assert report.status == "latest_nav_risk_observed"


def test_load_paper_nav_snapshot_db_trend_report_returns_empty_history_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        return ()

    monkeypatch.setattr(
        db_trend_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    report = db_trend_load.load_paper_nav_snapshot_db_trend_report(
        generated_at=GENERATED_AT,
        config_version=TREND_CONFIG_VERSION,
        connection=object(),
    )

    assert report.status == "empty_nav_risk_history"
    assert report.nav_risk_report_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_exit_nav is None
    assert report.latest_cumulative_return is None
    assert report.latest_max_drawdown is None
    assert report.latest_max_drawdown_pct is None
    assert report.latest_nav_return_volatility is None
    assert report.latest_open_position_count == 0
    assert report.latest_fully_executable_count == 0
    assert report.latest_partially_executable_count == 0
    assert report.latest_no_exit_depth_count == 0
    assert report.latest_largest_market_exposure_value is None
    assert report.latest_largest_market_exposure_share is None
    assert report.worst_observed_max_drawdown_pct is None
    assert report.consecutive_unexecutable_open_position_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_paper_nav_snapshot_db_trend_report_rejects_unsafe_loaded_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unsafe = _unsafe_snapshot(
        _snapshot(
            datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
            exit_nav=Decimal("10000.0000"),
        ),
        paper_only=False,
    )

    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        return (unsafe,)

    monkeypatch.setattr(
        db_trend_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match="paper_only"):
        db_trend_load.load_paper_nav_snapshot_db_trend_report(
            generated_at=GENERATED_AT,
            config_version=TREND_CONFIG_VERSION,
            connection=object(),
        )


def test_paper_nav_snapshot_db_trend_load_module_has_no_live_driver_or_cli_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_nav_snapshot_db_trend_load.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "click",
        "eth_account",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "websocket",
        "websockets",
    }
