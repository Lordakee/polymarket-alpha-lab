from __future__ import annotations

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_nav_snapshot_db_liquidity_risk_load as db_liquidity_load
from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPositionMark


GENERATED_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
LIQUIDITY_CONFIG_VERSION = "paper-nav-liquidity-risk-db-load-v0"
HEX = "c" * 64


def _mark(
    *,
    condition_id: str,
    token_id: str,
    market_slug: str,
    open_size: Decimal = Decimal("100.0000"),
    cost_basis: Decimal = Decimal("70.0000"),
    mark_status: str = "fully_executable",
    exit_filled_size: Decimal | None = None,
    exit_average_price: Decimal = Decimal("0.5000"),
    spread: Decimal | None = Decimal("0.0200"),
    slippage_estimate: Decimal | None = Decimal("0.0100"),
) -> PaperPositionMark:
    if mark_status == "fully_executable":
        filled_size = open_size if exit_filled_size is None else exit_filled_size
        unfilled_size = Decimal("0.0000")
        average_price: Decimal | None = exit_average_price
    elif mark_status == "partially_executable":
        filled_size = open_size / Decimal("2") if exit_filled_size is None else exit_filled_size
        unfilled_size = open_size - filled_size
        average_price = exit_average_price
    else:
        filled_size = Decimal("0.0000")
        unfilled_size = open_size
        average_price = None
        spread = None
        slippage_estimate = None

    exit_value = (
        Decimal("0.0000")
        if filled_size == 0
        else (filled_size * average_price).quantize(Decimal("0.0001"))
    )
    midpoint_value = (
        None
        if average_price is None
        else (open_size * average_price).quantize(Decimal("0.0001"))
    )

    return PaperPositionMark(
        condition_id=condition_id,
        token_id=token_id,
        market_slug=market_slug,
        outcome_name="YES",
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=(cost_basis / open_size).quantize(Decimal("0.0001")),
        order_book_captured_at=datetime(2026, 6, 22, 8, 0, tzinfo=UTC),
        order_book_snapshot_sha256=HEX,
        exit_filled_size=filled_size,
        exit_unfilled_size=unfilled_size,
        exit_average_price=average_price,
        exit_worst_price=average_price,
        exit_value=exit_value,
        midpoint_price=average_price,
        midpoint_value=midpoint_value,
        best_bid=average_price,
        best_ask=None if average_price is None else average_price + (spread or Decimal("0")),
        spread=spread,
        slippage_estimate=slippage_estimate,
        mark_status=mark_status,
    )


def _snapshot(
    marked_at: datetime,
    *,
    marks: tuple[PaperPositionMark, ...] = (),
    cash_balance: Decimal = Decimal("1000.0000"),
) -> PaperNavSnapshot:
    exit_value = sum((mark.exit_value for mark in marks), Decimal("0"))
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
        exit_nav=cash_balance + exit_value,
        midpoint_nav=midpoint_nav,
        total_cost_basis=total_cost_basis,
        unrealized_exit_pnl=unrealized_exit_pnl,
        marks=marks,
    )


def _tampered_snapshot(
    snapshot: PaperNavSnapshot,
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperNavSnapshot:
    unchecked = object.__new__(PaperNavSnapshot)
    for field_name in snapshot.__dataclass_fields__:
        object.__setattr__(unchecked, field_name, getattr(snapshot, field_name))
    object.__setattr__(unchecked, "paper_only", paper_only)
    object.__setattr__(unchecked, "report_only", report_only)
    object.__setattr__(unchecked, "readonly", readonly)
    return unchecked


def test_load_paper_nav_snapshot_db_liquidity_risk_report_returns_empty_history_report(
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
        db_liquidity_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    report = db_liquidity_load.load_paper_nav_snapshot_db_liquidity_risk_report(
        generated_at=GENERATED_AT,
        config_version=LIQUIDITY_CONFIG_VERSION,
        connection=object(),
    )

    assert report.status == "empty_nav_liquidity_risk_history"
    assert report.config_version == LIQUIDITY_CONFIG_VERSION
    assert report.generated_at == GENERATED_AT
    assert report.nav_snapshot_count == 0
    assert report.first_marked_at is None
    assert report.last_marked_at is None
    assert report.latest_open_position_count == 0
    assert report.latest_fully_executable_count == 0
    assert report.latest_partially_executable_count == 0
    assert report.latest_no_exit_depth_count == 0
    assert report.latest_total_open_size is None
    assert report.latest_total_cost_basis is None
    assert report.latest_unfilled_size is None
    assert report.latest_unfilled_open_size_share is None
    assert report.latest_unexecutable_cost_basis is None
    assert report.latest_unexecutable_cost_basis_share is None
    assert report.latest_weighted_slippage is None
    assert report.latest_widest_spread is None
    assert report.largest_unexecutable_condition_id is None
    assert report.largest_unexecutable_market_slug is None
    assert report.largest_unexecutable_cost_basis is None
    assert report.consecutive_unexecutable_snapshot_count == 0
    assert report.worst_observed_unexecutable_cost_basis_share is None
    assert report.market_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_paper_nav_snapshot_db_liquidity_risk_report_reverses_store_desc_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oldest = _snapshot(
        datetime(2026, 6, 22, 7, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-ok",
                token_id="token-ok",
                market_slug="market-ok",
                open_size=Decimal("20.0000"),
                cost_basis=Decimal("10.0000"),
            ),
        ),
    )
    middle = _snapshot(
        datetime(2026, 6, 22, 8, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-middle",
                token_id="token-middle",
                market_slug="market-middle",
                open_size=Decimal("30.0000"),
                cost_basis=Decimal("30.0000"),
                mark_status="no_exit_depth",
            ),
        ),
    )
    latest = _snapshot(
        datetime(2026, 6, 22, 9, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-latest",
                token_id="token-latest",
                market_slug="market-latest",
                open_size=Decimal("40.0000"),
                cost_basis=Decimal("20.0000"),
                mark_status="partially_executable",
                exit_filled_size=Decimal("20.0000"),
            ),
        ),
    )

    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        return (latest, middle, oldest)

    monkeypatch.setattr(
        db_liquidity_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    report = db_liquidity_load.load_paper_nav_snapshot_db_liquidity_risk_report(
        generated_at=GENERATED_AT,
        config_version=LIQUIDITY_CONFIG_VERSION,
        connection=object(),
    )

    assert report.nav_snapshot_count == 3
    assert report.first_marked_at == oldest.marked_at
    assert report.last_marked_at == latest.marked_at
    assert report.status == "latest_nav_has_unexecutable_liquidity"
    assert report.latest_open_position_count == 1
    assert report.latest_partially_executable_count == 1
    assert report.latest_unexecutable_cost_basis == Decimal("10.0000")
    assert report.latest_unexecutable_cost_basis_share == Decimal("0.500000")
    assert report.consecutive_unexecutable_snapshot_count == 2
    assert report.worst_observed_unexecutable_cost_basis_share == Decimal("1.000000")
    assert tuple(row.market_slug for row in report.market_rows) == ("market-latest",)


def test_load_paper_nav_snapshot_db_liquidity_risk_report_passes_limit_and_table_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, int | None, str]] = []

    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        calls.append((connection_arg, limit, table_name))
        return ()

    monkeypatch.setattr(
        db_liquidity_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    db_liquidity_load.load_paper_nav_snapshot_db_liquidity_risk_report(
        generated_at=GENERATED_AT,
        config_version=LIQUIDITY_CONFIG_VERSION,
        connection=connection,
        limit=25,
        table_name="paper_nav_archive",
    )

    assert calls == [(connection, 25, "paper_nav_archive")]


@pytest.mark.parametrize(
    ("flag_name", "expected_message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_paper_nav_snapshot_db_liquidity_risk_report_rejects_tampered_snapshot_flags(
    flag_name: str,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {"paper_only": True, "report_only": True, "readonly": True}
    values[flag_name] = False
    unsafe = _tampered_snapshot(
        _snapshot(datetime(2026, 6, 22, 7, 0, tzinfo=UTC)),
        paper_only=values["paper_only"],
        report_only=values["report_only"],
        readonly=values["readonly"],
    )

    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        return (unsafe,)

    monkeypatch.setattr(
        db_liquidity_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match=expected_message):
        db_liquidity_load.load_paper_nav_snapshot_db_liquidity_risk_report(
            generated_at=GENERATED_AT,
            config_version=LIQUIDITY_CONFIG_VERSION,
            connection=object(),
        )


def test_load_paper_nav_snapshot_db_liquidity_risk_report_rejects_snapshot_subclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PaperNavSnapshotSubclass(PaperNavSnapshot):
        pass

    original = _snapshot(datetime(2026, 6, 22, 7, 0, tzinfo=UTC))
    subclass = PaperNavSnapshotSubclass(**{
        field_name: getattr(original, field_name)
        for field_name in original.__dataclass_fields__
    })

    def load_snapshots(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_nav_snapshots",
    ) -> tuple[PaperNavSnapshot, ...]:
        return (subclass,)

    monkeypatch.setattr(
        db_liquidity_load.paper_nav_snapshot_store,
        "load_paper_nav_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match="PaperNavSnapshot"):
        db_liquidity_load.load_paper_nav_snapshot_db_liquidity_risk_report(
            generated_at=GENERATED_AT,
            config_version=LIQUIDITY_CONFIG_VERSION,
            connection=object(),
        )


def test_paper_nav_snapshot_db_liquidity_risk_load_module_has_no_forbidden_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_nav_snapshot_db_liquidity_risk_load.py"
    )
    source = module_path.read_text()
    module = ast.parse(source)
    imported_roots: set[str] = set()
    imported_names: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
            imported_names.add(node.module)

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "click",
        "eth_account",
        "httpx",
        "motor",
        "os",
        "psycopg",
        "pymongo",
        "redis",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "sys",
        "urllib",
        "web3",
        "websocket",
        "websockets",
    }
    assert not imported_names & {
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.paper_nav_snapshot_psycopg",
    }

    forbidden_fragments = (
        "cancel",
        "dsn",
        "exchange",
        "insert_",
        "migration",
        "order",
        "private_key",
        "redis",
        "replace",
        "sign",
        "sqlite",
        "submit",
        "wallet",
    )
    lowered_source = source.lower()
    assert not any(fragment in lowered_source for fragment in forbidden_fragments)
