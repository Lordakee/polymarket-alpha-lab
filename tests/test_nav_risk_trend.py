import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
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
    return PaperNavRiskMetricsReport(
        generated_at=generated_at,
        config_version="nav-risk-metrics-v0",
        nav_snapshot_count=3,
        first_marked_at=generated_at,
        last_marked_at=generated_at,
        latest_exit_nav=latest_exit_nav,
        latest_starting_cash=Decimal("10000.0000"),
        latest_cash_balance=Decimal("9900.0000"),
        latest_total_cost_basis=Decimal("100.0000"),
        latest_unrealized_exit_pnl=Decimal("0.0000"),
        peak_exit_nav=Decimal("10000.0000"),
        trough_exit_nav=Decimal("9900.0000"),
        cumulative_return=cumulative_return,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        worst_nav_delta=Decimal("0.0000"),
        nav_return_volatility=nav_return_volatility,
        pending_notional=Decimal("100.0000"),
        open_position_count=open_position_count,
        fully_executable_count=fully_executable_count,
        partially_executable_count=partially_executable_count,
        no_exit_depth_count=no_exit_depth_count,
        largest_market_exposure_value=largest_market_exposure_value,
        largest_market_exposure_share=largest_market_exposure_share,
        exposure_rows=(),
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
        max_drawdown_pct=None,
        no_exit_depth_count=0,
        open_position_count=1,
    )
    second = _risk_metrics_report(
        datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        max_drawdown_pct=Decimal("0.020000"),
        no_exit_depth_count=0,
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
