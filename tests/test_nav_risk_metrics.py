from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
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


def test_nav_risk_metrics_aggregates_binary_condition_exposure_rows():
    binary_marks = (
        _mark(
            condition_id="condition-binary",
            token_id="token-binary-no",
            market_slug="market-binary",
            outcome_name="NO",
            open_size=Decimal("60.0000"),
            cost_basis=Decimal("30.0000"),
            exit_value=Decimal("36.0000"),
            mark_status="fully_executable",
        ),
        _mark(
            condition_id="condition-binary",
            token_id="token-binary-yes",
            market_slug="market-binary",
            outcome_name="YES",
            open_size=Decimal("40.0000"),
            cost_basis=Decimal("22.0000"),
            exit_value=Decimal("14.0000"),
            mark_status="partially_executable",
        ),
        _mark(
            condition_id="condition-other",
            token_id="token-other",
            market_slug="market-other",
            open_size=Decimal("30.0000"),
            cost_basis=Decimal("15.0000"),
            exit_value=Decimal("9.0000"),
            mark_status="fully_executable",
        ),
    )

    report = _build_report(
        (
            _nav(
                GENERATED_AT,
                exit_nav=Decimal("1000.0000"),
                marks=binary_marks,
            ),
        ),
    )

    assert report.pending_notional == Decimal("67.0000")
    assert report.open_position_count == 3
    assert report.fully_executable_count == 2
    assert report.partially_executable_count == 1
    assert report.no_exit_depth_count == 0
    assert tuple(row.market_slug for row in report.exposure_rows) == (
        "market-binary",
        "market-other",
    )
    binary_row = report.exposure_rows[0]
    assert binary_row.token_count == 2
    assert binary_row.open_size == Decimal("100.0000")
    assert binary_row.cost_basis == Decimal("52.0000")
    assert binary_row.exit_value == Decimal("50.0000")
    assert binary_row.share_of_exit_nav == Decimal("0.050000")
    assert report.largest_market_exposure_value == Decimal("50.0000")
    assert report.largest_market_exposure_share == Decimal("0.050000")


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


def test_nav_risk_metrics_allows_zero_nav_cumulative_return_to_be_undefined():
    report = _build_report(
        (
            _nav(
                datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
                exit_nav=Decimal("0.0000"),
                realized_pnl=Decimal("-1.0000"),
            ),
            _nav(
                datetime(2026, 6, 16, 13, 0, tzinfo=UTC),
                exit_nav=Decimal("0.0000"),
                realized_pnl=Decimal("-1.0000"),
            ),
        ),
    )

    assert report.nav_snapshot_count == 2
    assert report.latest_exit_nav == Decimal("0.0000")
    assert report.latest_starting_cash == Decimal("1.0000")
    assert report.cumulative_return is None


def test_nav_risk_metrics_rejects_nonpositive_starting_cash_for_non_empty_reports():
    report = _build_report((_nav(GENERATED_AT, exit_nav=Decimal("1000.0000")),))

    with pytest.raises(ValueError, match="latest_starting_cash"):
        replace(report, latest_starting_cash=Decimal("0.0000"))


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


def test_nav_risk_metrics_normalizes_direct_report_timestamps_to_utc():
    generated_at = datetime(
        2026,
        6,
        16,
        21,
        0,
        tzinfo=timezone(timedelta(hours=2)),
    )
    marked_at = datetime(2026, 6, 16, 16, 30)

    report = PaperNavRiskMetricsReport(
        generated_at=generated_at,
        config_version="nav-risk-metrics-v0",
        nav_snapshot_count=1,
        first_marked_at=marked_at,
        last_marked_at=marked_at,
        latest_exit_nav=Decimal("1000.0000"),
        latest_starting_cash=Decimal("1000.0000"),
        latest_cash_balance=Decimal("1000.0000"),
        latest_total_cost_basis=Decimal("0.0000"),
        latest_unrealized_exit_pnl=Decimal("0.0000"),
        peak_exit_nav=Decimal("1000.0000"),
        trough_exit_nav=Decimal("1000.0000"),
        cumulative_return=Decimal("0.000000"),
        max_drawdown=Decimal("0.0000"),
        max_drawdown_pct=Decimal("0.000000"),
        worst_nav_delta=None,
        nav_return_volatility=None,
        pending_notional=Decimal("0.0000"),
        open_position_count=0,
        fully_executable_count=0,
        partially_executable_count=0,
        no_exit_depth_count=0,
        largest_market_exposure_value=None,
        largest_market_exposure_share=None,
        exposure_rows=(),
    )

    assert report.generated_at == datetime(2026, 6, 16, 19, 0, tzinfo=UTC)
    assert report.first_marked_at == datetime(2026, 6, 16, 16, 30, tzinfo=UTC)
    assert report.last_marked_at == datetime(2026, 6, 16, 16, 30, tzinfo=UTC)


def test_nav_risk_metrics_rejects_impossible_exposure_row_quantities():
    with pytest.raises(ValueError, match="open_size"):
        PaperNavRiskExposureRow(
            condition_id="condition-row",
            market_slug="market-row",
            token_count=1,
            open_size=Decimal("0.0000"),
            cost_basis=Decimal("0.0000"),
            exit_value=Decimal("0.0000"),
            share_of_exit_nav=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="cost_basis"):
        PaperNavRiskExposureRow(
            condition_id="condition-row",
            market_slug="market-row",
            token_count=1,
            open_size=Decimal("10.0000"),
            cost_basis=Decimal("11.0000"),
            exit_value=Decimal("5.0000"),
            share_of_exit_nav=Decimal("0.500000"),
        )

    with pytest.raises(ValueError, match="share_of_exit_nav"):
        PaperNavRiskExposureRow(
            condition_id="condition-row",
            market_slug="market-row",
            token_count=1,
            open_size=Decimal("10.0000"),
            cost_basis=Decimal("9.0000"),
            exit_value=Decimal("5.0000"),
            share_of_exit_nav=Decimal("1.000001"),
        )


def test_nav_risk_metrics_rejects_direct_report_aggregate_inconsistency():
    valid = _build_report(
        (
            _nav(
                GENERATED_AT,
                exit_nav=Decimal("1000.0000"),
                marks=(
                    _mark(
                        condition_id="condition-a",
                        token_id="token-a",
                        market_slug="market-a",
                        open_size=Decimal("80.0000"),
                        cost_basis=Decimal("50.0000"),
                        exit_value=Decimal("40.0000"),
                        mark_status="fully_executable",
                    ),
                    _mark(
                        condition_id="condition-b",
                        token_id="token-b",
                        market_slug="market-b",
                        open_size=Decimal("30.0000"),
                        cost_basis=Decimal("20.0000"),
                        exit_value=Decimal("12.0000"),
                        mark_status="partially_executable",
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="pending_notional"):
        replace(valid, pending_notional=Decimal("69.0000"))
    with pytest.raises(ValueError, match="open_position_count"):
        replace(valid, open_position_count=1)
    with pytest.raises(ValueError, match="mark status counts"):
        replace(valid, no_exit_depth_count=1)
    with pytest.raises(ValueError, match="largest_market_exposure_value"):
        replace(valid, largest_market_exposure_value=Decimal("12.0000"))
    with pytest.raises(ValueError, match="largest_market_exposure_share"):
        replace(valid, largest_market_exposure_share=Decimal("0.012000"))
    with pytest.raises(ValueError, match="latest_exit_nav"):
        replace(valid, latest_exit_nav=Decimal("999.0000"))
    with pytest.raises(ValueError, match="latest_unrealized_exit_pnl"):
        replace(valid, latest_unrealized_exit_pnl=Decimal("-17.0000"))


def test_nav_risk_metrics_rejects_zero_position_report_accounting_inconsistency():
    valid = _build_report((_nav(GENERATED_AT, exit_nav=Decimal("1000.0000")),))

    with pytest.raises(ValueError, match="latest_exit_nav"):
        replace(valid, latest_cash_balance=Decimal("999.0000"))
    with pytest.raises(ValueError, match="latest_total_cost_basis"):
        replace(valid, latest_total_cost_basis=Decimal("1.0000"))
    with pytest.raises(ValueError, match="latest_unrealized_exit_pnl"):
        replace(valid, latest_unrealized_exit_pnl=Decimal("1.0000"))


def test_nav_risk_metrics_rejects_empty_direct_report_with_populated_metrics():
    empty = _build_report(())

    with pytest.raises(ValueError, match="empty NAV risk metrics"):
        replace(empty, latest_exit_nav=Decimal("1.0000"))
    with pytest.raises(ValueError, match="empty NAV risk metrics"):
        replace(empty, open_position_count=1)
    with pytest.raises(ValueError, match="empty NAV risk metrics"):
        replace(
            empty,
            exposure_rows=(
                PaperNavRiskExposureRow(
                    condition_id="condition-row",
                    market_slug="market-row",
                    token_count=1,
                    open_size=Decimal("1.0000"),
                    cost_basis=Decimal("1.0000"),
                    exit_value=Decimal("1.0000"),
                    share_of_exit_nav=Decimal("1.000000"),
                ),
            ),
        )


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
