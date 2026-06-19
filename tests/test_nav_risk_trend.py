import ast
import inspect
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
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    PaperNavRiskTrendReport,
    PaperNavRiskTrendStatusRow,
    build_paper_nav_risk_trend_report,
)
import polymarket_alpha_lab.nav_risk_trend as nav_risk_trend


GENERATED_AT = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)
STATUS_ORDER = (
    "empty_nav_risk_history",
    "latest_nav_risk_observed",
    "latest_nav_has_unexecutable_positions",
)


def _config(**overrides):
    values = {"config_version": "nav-risk-trend-v0"}
    values.update(overrides)
    return PaperNavRiskTrendConfig(**values)


def _risk_metrics_report(
    generated_at: datetime,
    *,
    latest_exit_nav: Decimal | None = Decimal("10000.0000"),
    cumulative_return: Decimal | None = Decimal("0.000000"),
    max_drawdown: Decimal | None = Decimal("0.0000"),
    max_drawdown_pct: Decimal | None,
    nav_return_volatility: Decimal | None = Decimal("0.000000"),
    open_position_count: int,
    fully_executable_count: int | None = None,
    partially_executable_count: int = 0,
    no_exit_depth_count: int,
    largest_market_exposure_value: Decimal | None = None,
    largest_market_exposure_share: Decimal | None = None,
    paper_only: bool = True,
    report_only: bool = True,
) -> PaperNavRiskMetricsReport:
    if fully_executable_count is None:
        fully_executable_count = open_position_count - no_exit_depth_count
    exposure_values = ()
    if open_position_count > 0:
        first_exposure_value = largest_market_exposure_value or Decimal("100.0000")
        exposure_values = (
            first_exposure_value,
            *(Decimal("100.0000") for _ in range(open_position_count - 1)),
        )
    exposure_rows = tuple(
        PaperNavRiskExposureRow(
            condition_id=f"condition-{index}",
            market_slug=f"market-{index}",
            token_count=1,
            open_size=exit_value,
            cost_basis=exit_value,
            exit_value=exit_value,
            share_of_exit_nav=(
                None
                if latest_exit_nav is None or latest_exit_nav <= Decimal("0")
                else (exit_value / latest_exit_nav).quantize(Decimal("0.000001"))
            ),
        )
        for index, exit_value in enumerate(exposure_values)
    )
    latest_total_cost_basis = sum(exposure_values, Decimal("0"))
    total_exit_value = sum(exposure_values, Decimal("0"))
    latest_cash_balance = (
        None if latest_exit_nav is None else latest_exit_nav - total_exit_value
    )
    latest_unrealized_exit_pnl = Decimal("0.0000")
    if open_position_count == 0:
        latest_total_cost_basis = Decimal("0")
        largest_market_exposure_value = None
        largest_market_exposure_share = None
    elif largest_market_exposure_value is None:
        largest_market_exposure_value = max(exposure_values)
    if open_position_count > 0 and largest_market_exposure_share is None:
        largest_market_exposure_share = (
            None
            if latest_exit_nav is None or latest_exit_nav <= Decimal("0")
            else (largest_market_exposure_value / latest_exit_nav).quantize(
                Decimal("0.000001"),
            )
        )
    return PaperNavRiskMetricsReport(
        generated_at=generated_at,
        config_version="nav-risk-metrics-v0",
        nav_snapshot_count=3,
        first_marked_at=generated_at,
        last_marked_at=generated_at,
        latest_exit_nav=latest_exit_nav,
        latest_starting_cash=Decimal("10000.0000"),
        latest_cash_balance=latest_cash_balance,
        latest_total_cost_basis=latest_total_cost_basis,
        latest_unrealized_exit_pnl=latest_unrealized_exit_pnl,
        peak_exit_nav=Decimal("10000.0000"),
        trough_exit_nav=Decimal("9900.0000"),
        cumulative_return=cumulative_return,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        worst_nav_delta=Decimal("0.0000"),
        nav_return_volatility=nav_return_volatility,
        pending_notional=latest_total_cost_basis,
        open_position_count=open_position_count,
        fully_executable_count=fully_executable_count,
        partially_executable_count=partially_executable_count,
        no_exit_depth_count=no_exit_depth_count,
        largest_market_exposure_value=largest_market_exposure_value,
        largest_market_exposure_share=largest_market_exposure_share,
        exposure_rows=exposure_rows,
        paper_only=paper_only,
        report_only=report_only,
    )


def _build_report(reports):
    return build_paper_nav_risk_trend_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _report_with_flag(report: PaperNavRiskMetricsReport, flag_name: str, value: bool):
    unchecked = object.__new__(PaperNavRiskMetricsReport)
    for field_name in report.__dataclass_fields__:
        object.__setattr__(unchecked, field_name, getattr(report, field_name))
    object.__setattr__(unchecked, flag_name, value)
    return unchecked


def _status_rows(report: PaperNavRiskTrendReport):
    return {row.status: row for row in report.status_rows}


def _trend_status_rows(
    *,
    empty: int = 0,
    observed: int = 0,
    unexecutable: int = 0,
) -> tuple[PaperNavRiskTrendStatusRow, ...]:
    counts = {
        "empty_nav_risk_history": empty,
        "latest_nav_risk_observed": observed,
        "latest_nav_has_unexecutable_positions": unexecutable,
    }
    total = sum(counts.values())
    return tuple(
        PaperNavRiskTrendStatusRow(
            status,
            counts[status],
            None
            if total == 0
            else (Decimal(counts[status]) / Decimal(total)).quantize(
                Decimal("0.000001"),
            ),
        )
        for status in STATUS_ORDER
    )


def test_nav_risk_trend_empty_report_matches_full_spec_surface():
    report = _build_report([])

    assert isinstance(report, PaperNavRiskTrendReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "nav-risk-trend-v0"
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
    assert report.status == "empty_nav_risk_history"
    assert tuple(row.status for row in report.status_rows) == STATUS_ORDER
    assert tuple(row.report_count for row in report.status_rows) == (0, 0, 0)
    assert tuple(row.report_ratio for row in report.status_rows) == (None, None, None)


def test_nav_risk_trend_preserves_append_order_and_summarizes_latest_metrics():
    append_first = _risk_metrics_report(
        datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        latest_exit_nav=Decimal("10100.0000"),
        cumulative_return=Decimal("0.010000"),
        max_drawdown=Decimal("0.0000"),
        max_drawdown_pct=Decimal("0.000000"),
        nav_return_volatility=Decimal("0.010000"),
        no_exit_depth_count=0,
        open_position_count=1,
        largest_market_exposure_value=Decimal("75.0000"),
        largest_market_exposure_share=Decimal("0.007426"),
    )
    append_middle = _risk_metrics_report(
        datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        latest_exit_nav=Decimal("9900.0000"),
        cumulative_return=Decimal("-0.010000"),
        max_drawdown=Decimal("500.0000"),
        max_drawdown_pct=Decimal("0.050000"),
        nav_return_volatility=Decimal("0.020000"),
        no_exit_depth_count=1,
        open_position_count=3,
        largest_market_exposure_value=Decimal("125.0000"),
        largest_market_exposure_share=Decimal("0.012626"),
    )
    append_latest = _risk_metrics_report(
        datetime(2026, 6, 17, 11, 0, tzinfo=UTC),
        latest_exit_nav=Decimal("10050.0000"),
        cumulative_return=Decimal("0.005000"),
        max_drawdown=Decimal("250.0000"),
        max_drawdown_pct=Decimal("0.025000"),
        nav_return_volatility=Decimal("0.015000"),
        no_exit_depth_count=0,
        open_position_count=2,
        largest_market_exposure_value=Decimal("100.0000"),
        largest_market_exposure_share=Decimal("0.009950"),
    )

    report = _build_report([append_first, append_middle, append_latest])

    assert report.nav_risk_report_count == 3
    assert report.first_report_generated_at == append_first.generated_at
    assert report.latest_report_generated_at == append_latest.generated_at
    assert report.latest_exit_nav == Decimal("10050.0000")
    assert report.latest_cumulative_return == Decimal("0.005000")
    assert report.latest_max_drawdown == Decimal("250.0000")
    assert report.latest_max_drawdown_pct == Decimal("0.025000")
    assert report.latest_nav_return_volatility == Decimal("0.015000")
    assert report.latest_open_position_count == 2
    assert report.latest_fully_executable_count == 2
    assert report.latest_partially_executable_count == 0
    assert report.latest_no_exit_depth_count == 0
    assert report.latest_largest_market_exposure_value == Decimal("100.0000")
    assert report.latest_largest_market_exposure_share == Decimal("0.009950")
    assert report.worst_observed_max_drawdown_pct == Decimal("0.050000")
    assert report.consecutive_unexecutable_open_position_count == 0
    assert report.status == "latest_nav_risk_observed"


def test_nav_risk_trend_counts_unexecutable_statuses_and_consecutive_latest_reports():
    first = _risk_metrics_report(
        datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=1,
    )
    second = _risk_metrics_report(
        datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.020000"),
        no_exit_depth_count=1,
        open_position_count=4,
        fully_executable_count=2,
        partially_executable_count=1,
    )
    latest = _risk_metrics_report(
        datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.010000"),
        no_exit_depth_count=2,
        open_position_count=3,
        fully_executable_count=1,
        partially_executable_count=0,
    )

    report = _build_report([first, second, latest])
    rows = _status_rows(report)

    assert report.latest_report_generated_at == latest.generated_at
    assert report.status == "latest_nav_has_unexecutable_positions"
    assert report.consecutive_unexecutable_open_position_count == 2
    assert tuple(row.status for row in report.status_rows) == STATUS_ORDER
    assert rows["empty_nav_risk_history"].report_count == 0
    assert rows["empty_nav_risk_history"].report_ratio == Decimal("0.000000")
    assert rows["latest_nav_risk_observed"].report_count == 1
    assert rows["latest_nav_risk_observed"].report_ratio == Decimal("0.333333")
    assert rows["latest_nav_has_unexecutable_positions"].report_count == 2
    assert rows["latest_nav_has_unexecutable_positions"].report_ratio == Decimal(
        "0.666667",
    )


def test_nav_risk_trend_rejects_invalid_inputs_and_non_paper_source_flags():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="config"):
        build_paper_nav_risk_trend_report([], config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_nav_risk_trend_report([], config=_config(), generated_at="now")
    for reports in (
        "not reports",
        b"not reports",
        {"report": object()},
        (report for report in ()),
    ):
        with pytest.raises(ValueError, match="list or tuple"):
            _build_report(reports)
    with pytest.raises(ValueError, match="PaperNavRiskMetricsReport"):
        _build_report([object()])
    with pytest.raises(ValueError, match="paper_only"):
        _build_report(
            [
                _report_with_flag(
                    _risk_metrics_report(
                        GENERATED_AT,
                        max_drawdown_pct=Decimal("0.000000"),
                        no_exit_depth_count=0,
                        open_position_count=0,
                    ),
                    "paper_only",
                    False,
                ),
            ],
        )
    with pytest.raises(ValueError, match="report_only"):
        _build_report(
            [
                _report_with_flag(
                    _risk_metrics_report(
                        GENERATED_AT,
                        max_drawdown_pct=Decimal("0.000000"),
                        no_exit_depth_count=0,
                        open_position_count=0,
                    ),
                    "report_only",
                    False,
                ),
            ],
        )
    with pytest.raises(ValueError, match="readonly"):
        _build_report(
            [
                _report_with_flag(
                    _risk_metrics_report(
                        GENERATED_AT,
                        max_drawdown_pct=Decimal("0.000000"),
                        no_exit_depth_count=0,
                        open_position_count=0,
                    ),
                    "readonly",
                    False,
                ),
            ],
        )


def test_nav_risk_trend_rejects_source_reports_after_trend_timestamp():
    source = _risk_metrics_report(
        datetime(2026, 6, 17, 12, 1, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )

    with pytest.raises(ValueError, match="latest_report_generated_at"):
        _build_report([source])


def test_nav_risk_trend_rejects_any_source_report_after_trend_timestamp():
    future_middle = _risk_metrics_report(
        datetime(2026, 6, 17, 12, 1, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.010000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    latest = _risk_metrics_report(
        datetime(2026, 6, 17, 11, 59, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.020000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )

    with pytest.raises(ValueError, match="source report generated_at"):
        _build_report([latest, future_middle, latest])


def test_nav_risk_trend_normalizes_naive_generated_at_before_timestamp_checks():
    source = _risk_metrics_report(
        datetime(2026, 6, 17, 11, 59, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )

    report = build_paper_nav_risk_trend_report(
        [source],
        config=_config(),
        generated_at=datetime(2026, 6, 17, 12, 0),
    )

    assert report.generated_at == GENERATED_AT


def test_nav_risk_trend_normalizes_naive_direct_report_timestamps_to_utc():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    report = _build_report([source])

    normalized = replace(
        report,
        first_report_generated_at=datetime(2026, 6, 17, 10, 30),
        latest_report_generated_at=datetime(2026, 6, 17, 11, 0),
    )

    assert normalized.first_report_generated_at == datetime(
        2026,
        6,
        17,
        10,
        30,
        tzinfo=UTC,
    )
    assert normalized.latest_report_generated_at == datetime(
        2026,
        6,
        17,
        11,
        0,
        tzinfo=UTC,
    )


def test_nav_risk_trend_normalizes_offset_direct_report_timestamps_to_utc():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    report = _build_report([source])
    eastern = timezone(timedelta(hours=-4))

    normalized = replace(
        report,
        first_report_generated_at=datetime(2026, 6, 17, 7, 30, tzinfo=eastern),
        latest_report_generated_at=datetime(2026, 6, 17, 8, 0, tzinfo=eastern),
    )

    assert normalized.first_report_generated_at == datetime(
        2026,
        6,
        17,
        11,
        30,
        tzinfo=UTC,
    )
    assert normalized.first_report_generated_at.tzinfo is UTC
    assert normalized.latest_report_generated_at == GENERATED_AT
    assert normalized.latest_report_generated_at.tzinfo is UTC


def test_nav_risk_trend_reports_source_timestamp_errors_after_utc_normalization():
    future_middle = _risk_metrics_report(
        datetime(2026, 6, 17, 12, 1, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.010000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    latest = _risk_metrics_report(
        datetime(2026, 6, 17, 11, 59, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.020000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )

    with pytest.raises(ValueError, match="source report generated_at"):
        build_paper_nav_risk_trend_report(
            [future_middle, latest],
            config=_config(),
            generated_at=datetime(2026, 6, 17, 12, 0),
        )


def test_nav_risk_trend_rejects_empty_source_metrics_reports():
    empty_source = build_paper_nav_risk_metrics_report(
        (),
        config=PaperNavRiskMetricsConfig(config_version="nav-risk-metrics-v0"),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="source report must contain NAV snapshots"):
        _build_report([empty_source])


def test_nav_risk_trend_dataclasses_are_frozen_and_revalidate_invariants():
    report = _build_report([])

    with pytest.raises(FrozenInstanceError):
        report.nav_risk_report_count = 10
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="trade_more")
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=())
    with pytest.raises(ValueError, match="nav_risk_report_count"):
        replace(
            report,
            nav_risk_report_count=1,
            first_report_generated_at=GENERATED_AT,
            latest_report_generated_at=GENERATED_AT,
        )


def test_nav_risk_trend_rejects_non_decimal_public_metrics():
    with pytest.raises(ValueError, match="latest_exit_nav"):
        PaperNavRiskTrendReport(
            generated_at=GENERATED_AT,
            config_version="nav-risk-trend-v0",
            nav_risk_report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_exit_nav=100.0,
            latest_cumulative_return=None,
            latest_max_drawdown=None,
            latest_max_drawdown_pct=None,
            latest_nav_return_volatility=None,
            latest_open_position_count=0,
            latest_fully_executable_count=0,
            latest_partially_executable_count=0,
            latest_no_exit_depth_count=0,
            latest_largest_market_exposure_value=None,
            latest_largest_market_exposure_share=None,
            worst_observed_max_drawdown_pct=None,
            consecutive_unexecutable_open_position_count=0,
            status="empty_nav_risk_history",
            status_rows=(),
        )
    with pytest.raises(ValueError, match="report_ratio"):
        PaperNavRiskTrendStatusRow("empty_nav_risk_history", 0, 0.0)


def test_nav_risk_trend_rejects_scalar_subclasses_and_bool_counts():
    class StrSubclass(str):
        pass

    class DateTimeSubclass(datetime):
        pass

    class IntSubclass(int):
        pass

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="config_version"):
        PaperNavRiskTrendConfig(config_version=StrSubclass("nav-risk-trend-v0"))
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_nav_risk_trend_report(
            [],
            config=_config(),
            generated_at=DateTimeSubclass(2026, 6, 17, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="report_count"):
        PaperNavRiskTrendStatusRow(
            "empty_nav_risk_history",
            IntSubclass(0),
            Decimal("0.000000"),
        )
    with pytest.raises(ValueError, match="report_count"):
        PaperNavRiskTrendStatusRow("empty_nav_risk_history", True, Decimal("0.000000"))
    with pytest.raises(ValueError, match="report_ratio"):
        PaperNavRiskTrendStatusRow(
            "empty_nav_risk_history",
            0,
            DecimalSubclass("0.000000"),
        )


def test_nav_risk_trend_rejects_status_inconsistent_with_latest_counts():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=2,
    )

    with pytest.raises(ValueError, match="status"):
        PaperNavRiskTrendReport(
            generated_at=GENERATED_AT,
            config_version="nav-risk-trend-v0",
            nav_risk_report_count=1,
            first_report_generated_at=source.generated_at,
            latest_report_generated_at=source.generated_at,
            latest_exit_nav=source.latest_exit_nav,
            latest_cumulative_return=source.cumulative_return,
            latest_max_drawdown=source.max_drawdown,
            latest_max_drawdown_pct=source.max_drawdown_pct,
            latest_nav_return_volatility=source.nav_return_volatility,
            latest_open_position_count=source.open_position_count,
            latest_fully_executable_count=source.fully_executable_count,
            latest_partially_executable_count=source.partially_executable_count,
            latest_no_exit_depth_count=source.no_exit_depth_count,
            latest_largest_market_exposure_value=source.largest_market_exposure_value,
            latest_largest_market_exposure_share=source.largest_market_exposure_share,
            worst_observed_max_drawdown_pct=source.max_drawdown_pct,
            consecutive_unexecutable_open_position_count=1,
            status="latest_nav_has_unexecutable_positions",
            status_rows=(
                PaperNavRiskTrendStatusRow(
                    "empty_nav_risk_history",
                    0,
                    Decimal("0.000000"),
                ),
                PaperNavRiskTrendStatusRow(
                    "latest_nav_risk_observed",
                    0,
                    Decimal("0.000000"),
                ),
                PaperNavRiskTrendStatusRow(
                    "latest_nav_has_unexecutable_positions",
                    1,
                    Decimal("1.000000"),
                ),
            ),
        )


def test_nav_risk_trend_rejects_direct_constructor_inconsistent_timestamps():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    report = _build_report([source])

    with pytest.raises(ValueError, match="latest_report_generated_at"):
        replace(
            report,
            latest_report_generated_at=datetime(2026, 6, 17, 12, 1, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="first_report_generated_at"):
        replace(
            report,
            first_report_generated_at=datetime(2026, 6, 17, 12, 1, tzinfo=UTC),
        )


def test_nav_risk_trend_requires_direct_constructor_latest_metric_surface():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    report = _build_report([source])

    for field_name in (
        "latest_exit_nav",
        "latest_max_drawdown",
        "latest_max_drawdown_pct",
    ):
        with pytest.raises(ValueError, match=field_name):
            replace(report, **{field_name: None})


def test_nav_risk_trend_rejects_direct_constructor_impossible_latest_counts():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=1,
    )
    report = _build_report([source])

    with pytest.raises(ValueError, match="latest position counts"):
        replace(
            report,
            latest_open_position_count=1,
            latest_fully_executable_count=1,
            latest_partially_executable_count=1,
            latest_no_exit_depth_count=0,
        )
    with pytest.raises(ValueError, match="latest position counts"):
        replace(
            report,
            latest_open_position_count=1,
            latest_fully_executable_count=0,
            latest_partially_executable_count=0,
            latest_no_exit_depth_count=2,
        )


def test_nav_risk_trend_ties_direct_largest_exposure_fields_to_open_positions():
    zero_position_source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    zero_position_report = _build_report([zero_position_source])

    with pytest.raises(ValueError, match="latest_largest_market_exposure_value"):
        replace(
            zero_position_report,
            latest_largest_market_exposure_value=Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="latest_largest_market_exposure_share"):
        replace(
            zero_position_report,
            latest_largest_market_exposure_share=Decimal("0.000100"),
        )

    open_position_source = _risk_metrics_report(
        GENERATED_AT,
        latest_exit_nav=Decimal("10000.0000"),
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=1,
        largest_market_exposure_value=Decimal("100.0000"),
        largest_market_exposure_share=Decimal("0.010000"),
    )
    open_position_report = _build_report([open_position_source])

    with pytest.raises(ValueError, match="latest_largest_market_exposure_value"):
        replace(open_position_report, latest_largest_market_exposure_value=None)
    with pytest.raises(ValueError, match="latest_largest_market_exposure_share"):
        replace(open_position_report, latest_largest_market_exposure_share=None)

    zero_nav_open_position = replace(
        open_position_report,
        latest_exit_nav=Decimal("0.0000"),
        latest_largest_market_exposure_value=Decimal("0.0000"),
        latest_largest_market_exposure_share=None,
    )

    assert zero_nav_open_position.latest_largest_market_exposure_share is None


def test_nav_risk_trend_rejects_direct_constructor_inconsistent_status_rows():
    observed_source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    observed_report = _build_report([observed_source])
    unexecutable_source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=1,
        open_position_count=1,
    )
    unexecutable_report = _build_report([unexecutable_source])

    with pytest.raises(ValueError, match="status_rows"):
        replace(
            observed_report,
            status_rows=_trend_status_rows(empty=1),
        )
    with pytest.raises(ValueError, match="status_rows"):
        replace(
            unexecutable_report,
            status_rows=_trend_status_rows(observed=1),
        )


def test_nav_risk_trend_rejects_direct_constructor_impossible_unexecutable_streak():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=1,
        open_position_count=1,
    )
    report = _build_report([source])

    with pytest.raises(ValueError, match="consecutive_unexecutable"):
        replace(report, consecutive_unexecutable_open_position_count=2)


def test_nav_risk_trend_rejects_streak_longer_than_unexecutable_status_rows():
    first = _risk_metrics_report(
        datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    latest = _risk_metrics_report(
        datetime(2026, 6, 17, 11, 0, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.000000"),
        no_exit_depth_count=1,
        open_position_count=1,
    )
    report = _build_report([first, latest])

    with pytest.raises(ValueError, match="consecutive_unexecutable"):
        replace(
            report,
            consecutive_unexecutable_open_position_count=2,
            status_rows=_trend_status_rows(observed=1, unexecutable=1),
        )


def test_nav_risk_trend_rejects_direct_constructor_inconsistent_worst_drawdown():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown=Decimal("100.0000"),
        max_drawdown_pct=Decimal("0.010000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    report = _build_report([source])

    with pytest.raises(ValueError, match="worst_observed_max_drawdown_pct"):
        replace(report, worst_observed_max_drawdown_pct=None)
    with pytest.raises(ValueError, match="worst_observed_max_drawdown_pct"):
        replace(
            report,
            worst_observed_max_drawdown_pct=Decimal("0.009999"),
        )


def test_nav_risk_trend_requires_single_report_worst_drawdown_to_match_latest():
    source = _risk_metrics_report(
        GENERATED_AT,
        max_drawdown=Decimal("100.0000"),
        max_drawdown_pct=Decimal("0.010000"),
        no_exit_depth_count=0,
        open_position_count=0,
    )
    report = _build_report([source])

    with pytest.raises(ValueError, match="worst_observed_max_drawdown_pct"):
        replace(
            report,
            worst_observed_max_drawdown_pct=Decimal("0.010001"),
        )


def test_nav_risk_trend_module_stays_pure_and_leaf_only():
    source = inspect.getsource(nav_risk_trend)
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

    assert project_imports == {"polymarket_alpha_lab.nav_risk_metrics"}
    lowered = source.lower()
    for forbidden in (
        "paper_nav_log",
        ".read(",
        "open(",
        "path",
        "client",
        "network",
        "auth",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "submit_order",
        "sign_order",
        "rank",
        "recommend",
        "advice",
    ):
        assert forbidden not in lowered
