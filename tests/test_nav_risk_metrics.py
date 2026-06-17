from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.nav_risk_metrics import (
    PaperNavRiskExposureRow,
    PaperNavRiskMetricsConfig,
    PaperNavRiskMetricsReport,
    build_paper_nav_risk_metrics_report,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPositionMark


GENERATED_AT = datetime(2026, 6, 16, 19, 0, tzinfo=UTC)
HEX = "a" * 64


def _config(**overrides):
    values = {"config_version": "nav-risk-metrics-v0"}
    values.update(overrides)
    return PaperNavRiskMetricsConfig(**values)


def _mark(
    *,
    condition_id: str,
    token_id: str,
    market_slug: str,
    outcome_name: str = "YES",
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
        outcome_name=outcome_name,
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=(cost_basis / open_size).quantize(Decimal("0.0001")),
        order_book_captured_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
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


def _nav(
    marked_at: datetime,
    *,
    exit_nav: Decimal,
    marks: tuple[PaperPositionMark, ...] = (),
    realized_pnl: Decimal = Decimal("0.0000"),
) -> PaperNavSnapshot:
    mark_exit_value = sum((mark.exit_value for mark in marks), Decimal("0"))
    cash_balance = exit_nav - mark_exit_value
    total_cost_basis = sum((mark.cost_basis for mark in marks), Decimal("0"))
    unrealized = sum((mark.exit_value - mark.cost_basis for mark in marks), Decimal("0"))
    midpoint_nav = (
        cash_balance + sum((mark.midpoint_value for mark in marks), Decimal("0"))
        if all(mark.midpoint_value is not None for mark in marks)
        else None
    )
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=cash_balance + total_cost_basis - realized_pnl,
        cash_balance=cash_balance,
        realized_pnl=realized_pnl,
        exit_nav=exit_nav,
        midpoint_nav=midpoint_nav,
        total_cost_basis=total_cost_basis,
        unrealized_exit_pnl=unrealized,
        marks=marks,
    )


def _build_report(snapshots, **config_overrides):
    return build_paper_nav_risk_metrics_report(
        snapshots,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_nav_risk_metrics_empty_inputs_collapse_to_counts_and_none_metrics():
    report = _build_report(())

    assert isinstance(report, PaperNavRiskMetricsReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "nav-risk-metrics-v0"
    assert report.nav_snapshot_count == 0
    assert report.first_marked_at is None
    assert report.last_marked_at is None
    assert report.latest_exit_nav is None
    assert report.max_drawdown is None
    assert report.max_drawdown_pct is None
    assert report.nav_return_volatility is None
    assert report.exposure_rows == ()


def test_nav_risk_metrics_computes_drawdown_volatility_and_latest_exposures():
    latest_marks = (
        _mark(
            condition_id="condition-a",
            token_id="token-a",
            market_slug="market-a",
            open_size=Decimal("150.0000"),
            cost_basis=Decimal("120.0000"),
            exit_value=Decimal("100.0000"),
            mark_status="fully_executable",
        ),
        _mark(
            condition_id="condition-b",
            token_id="token-b",
            market_slug="market-b",
            open_size=Decimal("80.0000"),
            cost_basis=Decimal("50.0000"),
            exit_value=Decimal("0.0000"),
            mark_status="no_exit_depth",
        ),
    )
    snapshots = (
        _nav(datetime(2026, 6, 16, 13, 0, tzinfo=UTC), exit_nav=Decimal("10200.0000")),
        _nav(datetime(2026, 6, 16, 12, 0, tzinfo=UTC), exit_nav=Decimal("10000.0000")),
        _nav(
            datetime(2026, 6, 16, 14, 0, tzinfo=UTC),
            exit_nav=Decimal("9900.0000"),
            marks=latest_marks,
        ),
    )

    report = _build_report(snapshots)

    assert report.nav_snapshot_count == 3
    assert report.first_marked_at == datetime(2026, 6, 16, 12, 0, tzinfo=UTC)
    assert report.last_marked_at == datetime(2026, 6, 16, 14, 0, tzinfo=UTC)
    assert report.latest_exit_nav == Decimal("9900.0000")
    assert report.peak_exit_nav == Decimal("10200.0000")
    assert report.trough_exit_nav == Decimal("9900.0000")
    assert report.cumulative_return == Decimal("-0.010000")
    assert report.max_drawdown == Decimal("300.0000")
    assert report.max_drawdown_pct == Decimal("0.029412")
    assert report.worst_nav_delta == Decimal("-300.0000")
    assert report.nav_return_volatility == Decimal("0.024706")
    assert report.latest_total_cost_basis == Decimal("170.0000")
    assert report.pending_notional == Decimal("170.0000")
    assert report.open_position_count == 2
    assert report.fully_executable_count == 1
    assert report.partially_executable_count == 0
    assert report.no_exit_depth_count == 1
    assert report.largest_market_exposure_value == Decimal("100.0000")
    assert report.largest_market_exposure_share == Decimal("0.010101")

    assert tuple(row.market_slug for row in report.exposure_rows) == (
        "market-a",
        "market-b",
    )
    assert isinstance(report.exposure_rows[0], PaperNavRiskExposureRow)
    assert report.exposure_rows[0].condition_id == "condition-a"
    assert report.exposure_rows[0].token_count == 1
    assert report.exposure_rows[0].open_size == Decimal("150.0000")
    assert report.exposure_rows[0].cost_basis == Decimal("120.0000")
    assert report.exposure_rows[0].exit_value == Decimal("100.0000")
    assert report.exposure_rows[0].share_of_exit_nav == Decimal("0.010101")
    assert report.exposure_rows[1].share_of_exit_nav == Decimal("0.000000")


def test_nav_risk_metrics_can_preserve_append_order_for_trend_metrics():
    timestamp_latest_marks = (
        _mark(
            condition_id="condition-timestamp-latest",
            token_id="token-timestamp-latest",
            market_slug="market-timestamp-latest",
            open_size=Decimal("40.0000"),
            cost_basis=Decimal("30.0000"),
            exit_value=Decimal("20.0000"),
            mark_status="partially_executable",
        ),
    )
    input_latest_marks = (
        _mark(
            condition_id="condition-input-latest-a",
            token_id="token-input-latest-a",
            market_slug="market-input-latest-a",
            open_size=Decimal("200.0000"),
            cost_basis=Decimal("90.0000"),
            exit_value=Decimal("150.0000"),
            mark_status="fully_executable",
        ),
        _mark(
            condition_id="condition-input-latest-b",
            token_id="token-input-latest-b",
            market_slug="market-input-latest-b",
            open_size=Decimal("80.0000"),
            cost_basis=Decimal("70.0000"),
            mark_status="no_exit_depth",
        ),
    )
    snapshots = (
        _nav(
            datetime(2026, 6, 16, 14, 0, tzinfo=UTC),
            exit_nav=Decimal("10000.0000"),
            marks=timestamp_latest_marks,
        ),
        _nav(datetime(2026, 6, 16, 12, 0, tzinfo=UTC), exit_nav=Decimal("9000.0000")),
        _nav(
            datetime(2026, 6, 16, 13, 0, tzinfo=UTC),
            exit_nav=Decimal("9500.0000"),
            marks=input_latest_marks,
        ),
    )

    report = _build_report(snapshots, preserve_input_order=True)

    assert report.nav_snapshot_count == 3
    assert report.first_marked_at == datetime(2026, 6, 16, 14, 0, tzinfo=UTC)
    assert report.last_marked_at == datetime(2026, 6, 16, 13, 0, tzinfo=UTC)
    assert report.latest_exit_nav == Decimal("9500.0000")
    assert report.cumulative_return == Decimal("-0.050000")
    assert report.max_drawdown == Decimal("1000.0000")
    assert report.max_drawdown_pct == Decimal("0.100000")
    assert report.worst_nav_delta == Decimal("-1000.0000")
    assert report.nav_return_volatility == Decimal("0.077778")
    assert report.latest_total_cost_basis == Decimal("160.0000")
    assert report.pending_notional == Decimal("160.0000")
    assert report.open_position_count == 2
    assert report.fully_executable_count == 1
    assert report.no_exit_depth_count == 1
    assert report.largest_market_exposure_value == Decimal("150.0000")
    assert report.largest_market_exposure_share == Decimal("0.015789")
    assert tuple(row.market_slug for row in report.exposure_rows) == (
        "market-input-latest-a",
        "market-input-latest-b",
    )
    assert report.exposure_rows[0].share_of_exit_nav == Decimal("0.015789")
    assert report.exposure_rows[1].share_of_exit_nav == Decimal("0.000000")


def test_nav_risk_metrics_marks_single_snapshot_delta_metrics_as_none():
    report = _build_report((_nav(GENERATED_AT, exit_nav=Decimal("10000.0000")),))

    assert report.max_drawdown == Decimal("0.0000")
    assert report.max_drawdown_pct == Decimal("0.000000")
    assert report.worst_nav_delta is None
    assert report.nav_return_volatility is None
    assert report.cumulative_return == Decimal("0.000000")


def test_nav_risk_metrics_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="preserve_input_order"):
        _config(preserve_input_order=1)
    with pytest.raises(ValueError, match="config"):
        build_paper_nav_risk_metrics_report((), config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_nav_risk_metrics_report((), config=_config(), generated_at="now")
    with pytest.raises(ValueError, match="PaperNavSnapshot"):
        _build_report((object(),))


def test_nav_risk_metrics_allows_duplicate_marked_at_values_for_append_only_logs():
    first = _nav(GENERATED_AT, exit_nav=Decimal("10000.0000"))
    second = _nav(GENERATED_AT, exit_nav=Decimal("10100.0000"))

    report = _build_report((first, second))

    assert report.nav_snapshot_count == 2
    assert report.first_marked_at == GENERATED_AT
    assert report.last_marked_at == GENERATED_AT
    assert report.latest_exit_nav == Decimal("10100.0000")
    assert report.cumulative_return == Decimal("0.010000")


def test_nav_risk_metrics_dataclasses_are_frozen_and_revalidate_flags():
    report = _build_report(())

    with pytest.raises(FrozenInstanceError):
        report.nav_snapshot_count = 10
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
