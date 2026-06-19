import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

import pytest

import polymarket_alpha_lab.paper_nav_liquidity_risk as nav_liquidity
from polymarket_alpha_lab.paper_nav_liquidity_risk import (
    PaperNavLiquidityRiskConfig,
    PaperNavLiquidityRiskMarketRow,
    PaperNavLiquidityRiskReport,
    build_paper_nav_liquidity_risk_report,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPositionMark


GENERATED_AT = datetime(2026, 6, 18, 15, 0, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 6, 18, 14, 55, tzinfo=UTC)
HEX = "b" * 64


class TaggedDecimal(Decimal):
    pass


def _config(**overrides):
    values = {"config_version": "paper-nav-liquidity-risk-v0"}
    values.update(overrides)
    return PaperNavLiquidityRiskConfig(**values)


def _mark(
    *,
    condition_id: str,
    token_id: str,
    market_slug: str,
    outcome_name: str = "YES",
    open_size: Decimal,
    cost_basis: Decimal,
    mark_status: str = "fully_executable",
    exit_filled_size: Decimal | None = None,
    exit_unfilled_size: Decimal | None = None,
    exit_average_price: Decimal | None = Decimal("0.5000"),
    spread: Decimal | None = Decimal("0.0200"),
    slippage_estimate: Decimal | None = Decimal("0.0100"),
) -> PaperPositionMark:
    if mark_status == "fully_executable":
        filled_size = open_size if exit_filled_size is None else exit_filled_size
        unfilled_size = Decimal("0.0000") if exit_unfilled_size is None else exit_unfilled_size
        average_price = exit_average_price
    elif mark_status == "partially_executable":
        filled_size = open_size / Decimal("2") if exit_filled_size is None else exit_filled_size
        unfilled_size = open_size - filled_size if exit_unfilled_size is None else exit_unfilled_size
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
    midpoint_price = average_price
    midpoint_value = (
        None
        if midpoint_price is None
        else (open_size * midpoint_price).quantize(Decimal("0.0001"))
    )

    return PaperPositionMark(
        condition_id=condition_id,
        token_id=token_id,
        market_slug=market_slug,
        outcome_name=outcome_name,
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=(cost_basis / open_size).quantize(Decimal("0.0001")),
        order_book_captured_at=CAPTURED_AT,
        order_book_snapshot_sha256=HEX,
        exit_filled_size=filled_size,
        exit_unfilled_size=unfilled_size,
        exit_average_price=average_price,
        exit_worst_price=average_price,
        exit_value=exit_value,
        midpoint_price=midpoint_price,
        midpoint_value=midpoint_value,
        best_bid=average_price,
        best_ask=None if average_price is None else average_price + (spread or Decimal("0")),
        spread=spread,
        slippage_estimate=slippage_estimate,
        mark_status=mark_status,
    )


def _nav(
    marked_at: datetime,
    *,
    marks: tuple[PaperPositionMark, ...] = (),
    cash_balance: Decimal = Decimal("1000.0000"),
) -> PaperNavSnapshot:
    exit_value = sum((mark.exit_value for mark in marks), Decimal("0"))
    total_cost_basis = sum((mark.cost_basis for mark in marks), Decimal("0"))
    unrealized = sum((mark.exit_value - mark.cost_basis for mark in marks), Decimal("0"))
    midpoint_nav = (
        cash_balance + sum((mark.midpoint_value for mark in marks), Decimal("0"))
        if all(mark.midpoint_value is not None for mark in marks)
        else None
    )
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=cash_balance + total_cost_basis,
        cash_balance=cash_balance,
        realized_pnl=Decimal("0"),
        exit_nav=cash_balance + exit_value,
        midpoint_nav=midpoint_nav,
        total_cost_basis=total_cost_basis,
        unrealized_exit_pnl=unrealized,
        marks=marks,
    )


def _build_report(snapshots):
    return build_paper_nav_liquidity_risk_report(
        snapshots,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _market_row(**overrides):
    values = {
        "condition_id": "condition-a",
        "market_slug": "market-a",
        "token_count": 1,
        "open_size": Decimal("10.0000"),
        "cost_basis": Decimal("10.0000"),
        "exit_filled_size": Decimal("5.0000"),
        "exit_unfilled_size": Decimal("5.0000"),
        "exit_value": Decimal("2.5000"),
        "unfilled_open_size_share": Decimal("0.500000"),
        "unexecutable_cost_basis": Decimal("5.0000"),
        "unexecutable_cost_basis_share": Decimal("0.500000"),
        "weighted_slippage": Decimal("0.010000"),
        "widest_spread": Decimal("0.0200"),
        "fully_executable_count": 0,
        "partially_executable_count": 1,
        "no_exit_depth_count": 0,
    }
    values.update(overrides)
    return PaperNavLiquidityRiskMarketRow(**values)


def test_paper_nav_liquidity_risk_empty_history_returns_report_only_empty_status():
    report = _build_report(())

    assert isinstance(report, PaperNavLiquidityRiskReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-nav-liquidity-risk-v0"
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
    assert report.status == "empty_nav_liquidity_risk_history"
    assert report.market_rows == ()


def test_paper_nav_liquidity_risk_builder_ignores_caller_decimal_context():
    snapshot = _nav(
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-low-precision",
                token_id="token-low-precision",
                market_slug="market-low-precision",
                open_size=Decimal("3.0000"),
                cost_basis=Decimal("3.0000"),
                mark_status="partially_executable",
                exit_filled_size=Decimal("1.0000"),
            ),
        ),
    )

    with localcontext(Context(prec=2)):
        report = _build_report((snapshot,))

    assert report.latest_unfilled_open_size_share == Decimal("0.666667")
    assert report.latest_unexecutable_cost_basis_share == Decimal("0.666667")
    assert report.latest_weighted_slippage == Decimal("0.010000")
    assert report.market_rows[0].unfilled_open_size_share == Decimal("0.666667")


def test_paper_nav_liquidity_risk_builder_canonicalizes_upstream_mark_identifiers():
    snapshot = _nav(
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="  condition-risky  ",
                token_id="token-risky",
                market_slug="\tmarket-risky\n",
                open_size=Decimal("20.0000"),
                cost_basis=Decimal("10.0000"),
                mark_status="no_exit_depth",
            ),
        ),
    )

    report = _build_report((snapshot,))

    assert report.largest_unexecutable_condition_id == "condition-risky"
    assert report.largest_unexecutable_market_slug == "market-risky"
    assert report.market_rows[0].condition_id == "condition-risky"
    assert report.market_rows[0].market_slug == "market-risky"


def test_paper_nav_liquidity_risk_public_decimals_accept_and_normalize_subclasses():
    row = _market_row(
        open_size=TaggedDecimal("10.0000"),
        cost_basis=TaggedDecimal("10.0000"),
        exit_filled_size=TaggedDecimal("5.0000"),
        exit_unfilled_size=TaggedDecimal("5.0000"),
        exit_value=TaggedDecimal("2.5000"),
        unfilled_open_size_share=TaggedDecimal("0.500000"),
        unexecutable_cost_basis=TaggedDecimal("5.0000"),
        unexecutable_cost_basis_share=TaggedDecimal("0.500000"),
        weighted_slippage=TaggedDecimal("0.010000"),
        widest_spread=TaggedDecimal("0.0200"),
    )

    assert type(row.open_size) is Decimal
    assert type(row.unfilled_open_size_share) is Decimal
    assert type(row.weighted_slippage) is Decimal

    report = PaperNavLiquidityRiskReport(
        generated_at=GENERATED_AT,
        config_version="paper-nav-liquidity-risk-v0",
        nav_snapshot_count=1,
        first_marked_at=CAPTURED_AT,
        last_marked_at=CAPTURED_AT,
        latest_open_position_count=1,
        latest_fully_executable_count=0,
        latest_partially_executable_count=1,
        latest_no_exit_depth_count=0,
        latest_total_open_size=TaggedDecimal("10.0000"),
        latest_total_cost_basis=TaggedDecimal("10.0000"),
        latest_unfilled_size=TaggedDecimal("5.0000"),
        latest_unfilled_open_size_share=TaggedDecimal("0.500000"),
        latest_unexecutable_cost_basis=TaggedDecimal("5.0000"),
        latest_unexecutable_cost_basis_share=TaggedDecimal("0.500000"),
        latest_weighted_slippage=TaggedDecimal("0.010000"),
        latest_widest_spread=TaggedDecimal("0.0200"),
        largest_unexecutable_condition_id="condition-a",
        largest_unexecutable_market_slug="market-a",
        largest_unexecutable_cost_basis=TaggedDecimal("5.0000"),
        consecutive_unexecutable_snapshot_count=1,
        worst_observed_unexecutable_cost_basis_share=TaggedDecimal("0.500000"),
        status="latest_nav_has_unexecutable_liquidity",
        market_rows=(row,),
    )

    assert type(report.latest_total_open_size) is Decimal
    assert type(report.latest_unfilled_open_size_share) is Decimal
    assert type(report.worst_observed_unexecutable_cost_basis_share) is Decimal


def test_paper_nav_liquidity_risk_empty_report_rejects_latest_aggregates_and_worst_share():
    report = _build_report(())

    with pytest.raises(ValueError, match="empty report"):
        replace(report, latest_open_position_count=1)
    with pytest.raises(ValueError, match="empty report"):
        replace(report, latest_total_open_size=Decimal("1.0000"))
    with pytest.raises(ValueError, match="empty report"):
        replace(report, latest_unfilled_open_size_share=Decimal("0.000000"))
    with pytest.raises(ValueError, match="empty report"):
        replace(
            report,
            largest_unexecutable_condition_id="condition-a",
            largest_unexecutable_market_slug="market-a",
            largest_unexecutable_cost_basis=Decimal("0.0000"),
        )
    with pytest.raises(ValueError, match="empty report"):
        replace(report, worst_observed_unexecutable_cost_basis_share=Decimal("0.000001"))


def test_paper_nav_liquidity_risk_market_row_rejects_ratio_drift():
    with pytest.raises(ValueError, match="unfilled_open_size_share"):
        _market_row(unfilled_open_size_share=Decimal("0.400000"))


def test_paper_nav_liquidity_risk_report_rejects_latest_and_worst_ratio_drift():
    report = _build_report(
        (
            _nav(
                datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
                marks=(
                    _mark(
                        condition_id="condition-risky",
                        token_id="token-risky",
                        market_slug="market-risky",
                        open_size=Decimal("10.0000"),
                        cost_basis=Decimal("10.0000"),
                        mark_status="partially_executable",
                        exit_filled_size=Decimal("5.0000"),
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="latest_unfilled_open_size_share"):
        replace(report, latest_unfilled_open_size_share=Decimal("0.400000"))
    with pytest.raises(ValueError, match="latest_unexecutable_cost_basis_share"):
        replace(report, latest_unexecutable_cost_basis_share=Decimal("0.400000"))
    with pytest.raises(ValueError, match="worst_observed_unexecutable_cost_basis_share"):
        replace(report, worst_observed_unexecutable_cost_basis_share=Decimal("0.400000"))


def test_paper_nav_liquidity_risk_summarizes_latest_depth_and_market_rows():
    latest = _nav(
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-b",
                token_id="token-b",
                market_slug="market-b",
                open_size=Decimal("100.0000"),
                cost_basis=Decimal("80.0000"),
                mark_status="partially_executable",
                exit_filled_size=Decimal("40.0000"),
                exit_average_price=Decimal("0.5000"),
                spread=Decimal("0.0800"),
                slippage_estimate=Decimal("0.0300"),
            ),
            _mark(
                condition_id="condition-a",
                token_id="token-no-depth",
                market_slug="market-a",
                open_size=Decimal("50.0000"),
                cost_basis=Decimal("30.0000"),
                mark_status="no_exit_depth",
            ),
            _mark(
                condition_id="condition-a",
                token_id="token-full",
                market_slug="market-a",
                open_size=Decimal("20.0000"),
                cost_basis=Decimal("10.0000"),
                mark_status="fully_executable",
                exit_average_price=Decimal("0.7000"),
                spread=Decimal("0.0200"),
                slippage_estimate=Decimal("0.0100"),
            ),
        ),
    )

    report = _build_report((latest,))

    assert report.nav_snapshot_count == 1
    assert report.first_marked_at == latest.marked_at
    assert report.last_marked_at == latest.marked_at
    assert report.status == "latest_nav_has_unexecutable_liquidity"
    assert report.latest_open_position_count == 3
    assert report.latest_fully_executable_count == 1
    assert report.latest_partially_executable_count == 1
    assert report.latest_no_exit_depth_count == 1
    assert report.latest_total_open_size == Decimal("170.0000")
    assert report.latest_total_cost_basis == Decimal("120.0000")
    assert report.latest_unfilled_size == Decimal("110.0000")
    assert report.latest_unfilled_open_size_share == Decimal("0.647059")
    assert report.latest_unexecutable_cost_basis == Decimal("78.0000")
    assert report.latest_unexecutable_cost_basis_share == Decimal("0.650000")
    assert report.latest_weighted_slippage == Decimal("0.023333")
    assert report.latest_widest_spread == Decimal("0.0800")
    assert report.largest_unexecutable_condition_id == "condition-b"
    assert report.largest_unexecutable_market_slug == "market-b"
    assert report.largest_unexecutable_cost_basis == Decimal("48.0000")
    assert report.consecutive_unexecutable_snapshot_count == 1
    assert report.worst_observed_unexecutable_cost_basis_share == Decimal("0.650000")

    assert tuple(row.market_slug for row in report.market_rows) == ("market-a", "market-b")
    first, second = report.market_rows
    assert isinstance(first, PaperNavLiquidityRiskMarketRow)
    assert first.condition_id == "condition-a"
    assert first.token_count == 2
    assert first.fully_executable_count == 1
    assert first.partially_executable_count == 0
    assert first.no_exit_depth_count == 1
    assert first.open_size == Decimal("70.0000")
    assert first.cost_basis == Decimal("40.0000")
    assert first.exit_filled_size == Decimal("20.0000")
    assert first.exit_unfilled_size == Decimal("50.0000")
    assert first.unfilled_open_size_share == Decimal("0.714286")
    assert first.unexecutable_cost_basis == Decimal("30.0000")
    assert first.unexecutable_cost_basis_share == Decimal("0.250000")
    assert first.weighted_slippage == Decimal("0.010000")
    assert first.widest_spread == Decimal("0.0200")
    assert second.condition_id == "condition-b"
    assert second.token_count == 1
    assert second.exit_unfilled_size == Decimal("60.0000")
    assert second.unexecutable_cost_basis == Decimal("48.0000")
    assert second.unexecutable_cost_basis_share == Decimal("0.400000")
    assert second.weighted_slippage == Decimal("0.030000")
    assert second.widest_spread == Decimal("0.0800")


def test_paper_nav_liquidity_risk_uses_mark_time_for_history_streaks_and_worst_share():
    oldest = _nav(
        datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
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
    middle = _nav(
        datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-risky",
                token_id="token-risky",
                market_slug="market-risky",
                open_size=Decimal("30.0000"),
                cost_basis=Decimal("30.0000"),
                mark_status="no_exit_depth",
            ),
            _mark(
                condition_id="condition-ok",
                token_id="token-ok",
                market_slug="market-ok",
                open_size=Decimal("20.0000"),
                cost_basis=Decimal("10.0000"),
            ),
        ),
    )
    latest = _nav(
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
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
            _mark(
                condition_id="condition-ok",
                token_id="token-ok",
                market_slug="market-ok",
                open_size=Decimal("40.0000"),
                cost_basis=Decimal("20.0000"),
            ),
        ),
    )

    report = _build_report((latest, oldest, middle))

    assert report.first_marked_at == oldest.marked_at
    assert report.last_marked_at == latest.marked_at
    assert report.latest_unexecutable_cost_basis == Decimal("10.0000")
    assert report.latest_unexecutable_cost_basis_share == Decimal("0.250000")
    assert report.consecutive_unexecutable_snapshot_count == 2
    assert report.worst_observed_unexecutable_cost_basis_share == Decimal("0.750000")
    assert report.status == "latest_nav_has_unexecutable_liquidity"
    assert tuple(row.market_slug for row in report.market_rows) == (
        "market-latest",
        "market-ok",
    )


def test_paper_nav_liquidity_risk_observed_status_resets_unexecutable_streak():
    report = _build_report(
        (
            _nav(
                datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
                marks=(
                    _mark(
                        condition_id="condition-risky",
                        token_id="token-risky",
                        market_slug="market-risky",
                        open_size=Decimal("20.0000"),
                        cost_basis=Decimal("10.0000"),
                        mark_status="no_exit_depth",
                    ),
                ),
            ),
            _nav(
                datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
                marks=(
                    _mark(
                        condition_id="condition-ok",
                        token_id="token-ok",
                        market_slug="market-ok",
                        open_size=Decimal("20.0000"),
                        cost_basis=Decimal("10.0000"),
                    ),
                ),
            ),
        ),
    )

    assert report.status == "latest_nav_liquidity_observed"
    assert report.latest_unexecutable_cost_basis == Decimal("0")
    assert report.latest_unexecutable_cost_basis_share == Decimal("0.000000")
    assert report.consecutive_unexecutable_snapshot_count == 0
    assert report.worst_observed_unexecutable_cost_basis_share == Decimal("1.000000")


def test_paper_nav_liquidity_risk_allows_valid_crossed_book_negative_spreads():
    snapshot = _nav(
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        marks=(
            _mark(
                condition_id="condition-crossed",
                token_id="token-crossed",
                market_slug="market-crossed",
                open_size=Decimal("20.0000"),
                cost_basis=Decimal("10.0000"),
                spread=Decimal("-0.0100"),
            ),
        ),
    )

    report = _build_report((snapshot,))

    assert report.status == "latest_nav_liquidity_observed"
    assert report.latest_widest_spread == Decimal("-0.0100")
    assert report.market_rows[0].widest_spread == Decimal("-0.0100")


def test_paper_nav_liquidity_risk_rejects_invalid_inputs_and_freezes_flags():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="config"):
        build_paper_nav_liquidity_risk_report((), config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_nav_liquidity_risk_report((), config=_config(), generated_at="now")
    with pytest.raises(ValueError, match="PaperNavSnapshot"):
        _build_report((object(),))

    report = _build_report(())

    with pytest.raises(FrozenInstanceError):
        report.nav_snapshot_count = 10
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_paper_nav_liquidity_risk_rejects_non_decimal_public_metrics():
    with pytest.raises(ValueError, match="unfilled_open_size_share"):
        PaperNavLiquidityRiskMarketRow(
            condition_id="condition-a",
            market_slug="market-a",
            token_count=1,
            open_size=Decimal("1.0000"),
            cost_basis=Decimal("1.0000"),
            exit_filled_size=Decimal("1.0000"),
            exit_unfilled_size=Decimal("0"),
            exit_value=Decimal("0.5000"),
            unfilled_open_size_share=0.0,
            unexecutable_cost_basis=Decimal("0"),
            unexecutable_cost_basis_share=Decimal("0.000000"),
            weighted_slippage=Decimal("0.000000"),
            widest_spread=Decimal("0.0100"),
            fully_executable_count=1,
            partially_executable_count=0,
            no_exit_depth_count=0,
        )


def test_paper_nav_liquidity_risk_market_row_rejects_impossible_aggregates():
    with pytest.raises(ValueError, match="cost_basis must not exceed open_size"):
        PaperNavLiquidityRiskMarketRow(
            condition_id="condition-a",
            market_slug="market-a",
            token_count=1,
            open_size=Decimal("1.0000"),
            cost_basis=Decimal("2.0000"),
            exit_filled_size=Decimal("1.0000"),
            exit_unfilled_size=Decimal("0"),
            exit_value=Decimal("0.5000"),
            unfilled_open_size_share=Decimal("0.000000"),
            unexecutable_cost_basis=Decimal("0"),
            unexecutable_cost_basis_share=Decimal("0.000000"),
            weighted_slippage=Decimal("0.000000"),
            widest_spread=Decimal("-0.0100"),
            fully_executable_count=1,
            partially_executable_count=0,
            no_exit_depth_count=0,
        )

    with pytest.raises(ValueError, match="exit_value must not exceed exit_filled_size"):
        PaperNavLiquidityRiskMarketRow(
            condition_id="condition-a",
            market_slug="market-a",
            token_count=1,
            open_size=Decimal("1.0000"),
            cost_basis=Decimal("1.0000"),
            exit_filled_size=Decimal("0.5000"),
            exit_unfilled_size=Decimal("0.5000"),
            exit_value=Decimal("0.6000"),
            unfilled_open_size_share=Decimal("0.500000"),
            unexecutable_cost_basis=Decimal("0.5000"),
            unexecutable_cost_basis_share=Decimal("0.500000"),
            weighted_slippage=Decimal("0.000000"),
            widest_spread=Decimal("-0.0100"),
            fully_executable_count=0,
            partially_executable_count=1,
            no_exit_depth_count=0,
        )


def test_paper_nav_liquidity_risk_report_rejects_market_row_aggregate_mismatches():
    report = _build_report(
        (
            _nav(
                datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
                marks=(
                    _mark(
                        condition_id="condition-risky",
                        token_id="token-risky",
                        market_slug="market-risky",
                        open_size=Decimal("20.0000"),
                        cost_basis=Decimal("10.0000"),
                        mark_status="no_exit_depth",
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="latest_total_open_size"):
        replace(report, latest_total_open_size=Decimal("21.0000"))
    with pytest.raises(ValueError, match="latest_total_cost_basis"):
        replace(report, latest_total_cost_basis=Decimal("11.0000"))
    with pytest.raises(ValueError, match="latest_unfilled_size"):
        replace(report, latest_unfilled_size=Decimal("19.0000"))
    with pytest.raises(ValueError, match="latest_unexecutable_cost_basis"):
        replace(report, latest_unexecutable_cost_basis=Decimal("9.0000"))
    with pytest.raises(ValueError, match="largest unexecutable fields"):
        replace(report, largest_unexecutable_cost_basis=Decimal("9.0000"))


def test_paper_nav_liquidity_risk_module_stays_pure_and_leaf_only():
    source = inspect.getsource(nav_liquidity)
    tree = ast.parse(source)
    project_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("polymarket_alpha_lab."):
                project_imports.add(module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("polymarket_alpha_lab."):
                    project_imports.add(alias.name)

    assert project_imports == {"polymarket_alpha_lab.positions"}
    lowered = source.lower()
    for forbidden in (
        "paper_nav_log",
        ".read(",
        "open(",
        "path",
        "logging",
        "logger",
        "client",
        "network",
        "auth",
        "wallet",
        "private_key",
        "order",
        "rank",
        "recommend",
        "advice",
    ):
        assert forbidden not in lowered
