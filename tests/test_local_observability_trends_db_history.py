from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.local_observability_trends_db_history import (
    LocalObservabilityTrendsDbHistoryConfig,
    LocalObservabilityTrendsDbHistoryReport,
    build_local_observability_trends_db_history_report,
)
from polymarket_alpha_lab.nav_risk_trend import (
    NAV_RISK_TREND_STATUSES,
    PaperNavRiskTrendReport,
    PaperNavRiskTrendStatusRow,
)
from polymarket_alpha_lab.outcome_freshness import (
    OUTCOME_FRESHNESS_STATUSES,
    OutcomeFreshnessReport,
    OutcomeFreshnessStatusRow,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    COST_TREND_STATUSES,
    PaperTradeCostTrendReport,
    PaperTradeCostTrendStatusRow,
)
from polymarket_alpha_lab.strategy_evidence import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendGapRow,
    PaperStrategyEvidenceTrendReport,
    PaperStrategyEvidenceTrendStatusRow,
)


GENERATED_AT = datetime(2026, 6, 20, 19, 0, tzinfo=UTC)
RATIO_ONE = Decimal("1.000000")
RATIO_ZERO = Decimal("0.000000")


def _config() -> LocalObservabilityTrendsDbHistoryConfig:
    return LocalObservabilityTrendsDbHistoryConfig(
        config_version="local-observability-trends-db-history-v0",
    )


def _history(
    reports: list[LocalObservabilityTrendsReport]
    | tuple[LocalObservabilityTrendsReport, ...],
) -> LocalObservabilityTrendsDbHistoryReport:
    return build_local_observability_trends_db_history_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _ratio_row_count(total: int, count: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.000001"))


def _strategy_trend(
    status: str | None,
    *,
    generated_at: datetime,
) -> PaperStrategyEvidenceTrendReport:
    snapshot_count = 0 if status is None else 1
    latest_gap_names: tuple[str, ...] = ()
    local_risk_count = 0
    non_observed_count = 0
    if status == "local_evidence_gaps":
        latest_gap_names = ("missing_outcome_evidence",)
        non_observed_count = 1
    elif status == "local_risk_flags":
        latest_gap_names = ("negative_cost_adjusted_edges",)
        local_risk_count = 1
        non_observed_count = 1
    elif status == "no_local_evidence":
        non_observed_count = 1

    status_counts = {
        item: 1 if item == status else 0 for item in SNAPSHOT_STATUSES
    }
    gap_counts = {
        gap_name: 1 if gap_name in latest_gap_names else 0
        for gap_name in EVIDENCE_GAP_NAMES
    }
    return PaperStrategyEvidenceTrendReport(
        generated_at=generated_at,
        config_version="strategy-evidence-trend-v0",
        snapshot_report_count=snapshot_count,
        first_report_generated_at=generated_at if snapshot_count else None,
        latest_report_generated_at=generated_at if snapshot_count else None,
        latest_status=status,
        latest_evidence_gap_names=latest_gap_names,
        consecutive_local_risk_flags_count=local_risk_count,
        consecutive_non_observed_count=non_observed_count,
        status_rows=tuple(
            PaperStrategyEvidenceTrendStatusRow(
                snapshot_status=item,
                snapshot_count=status_counts[item],
                snapshot_ratio=_ratio_row_count(snapshot_count, status_counts[item]),
            )
            for item in SNAPSHOT_STATUSES
        ),
        gap_rows=tuple(
            PaperStrategyEvidenceTrendGapRow(
                evidence_gap_name=gap_name,
                gap_count=gap_counts[gap_name],
                gap_ratio=_ratio_row_count(snapshot_count, gap_counts[gap_name]),
            )
            for gap_name in EVIDENCE_GAP_NAMES
        ),
    )


def _outcome_freshness(
    status: str,
    *,
    generated_at: datetime,
) -> OutcomeFreshnessReport:
    report_count = 0 if status == "empty_outcome_history" else 1
    latest_total = 1 if status == "latest_outcomes_pending" else 0
    latest_pending = 1 if status == "latest_outcomes_pending" else 0
    latest_age = 7_200 if status == "latest_outcomes_stale" else 60
    status_counts = {
        item: 1 if item == status and report_count else 0
        for item in OUTCOME_FRESHNESS_STATUSES
    }
    return OutcomeFreshnessReport(
        generated_at=generated_at,
        config_version="outcome-freshness-v0",
        outcome_report_count=report_count,
        first_report_generated_at=generated_at if report_count else None,
        latest_report_generated_at=generated_at if report_count else None,
        latest_total_markets_checked=latest_total,
        latest_resolved_count=0,
        latest_pending_count=latest_pending,
        latest_resolved_ratio=RATIO_ZERO if latest_total else None,
        latest_pending_ratio=RATIO_ONE if latest_total else None,
        latest_report_age_seconds=latest_age if report_count else None,
        consecutive_pending_count=1 if latest_pending else 0,
        status=status,
        status_rows=tuple(
            OutcomeFreshnessStatusRow(
                status=item,
                outcome_report_count=status_counts[item],
                outcome_report_ratio=_ratio_row_count(
                    report_count,
                    status_counts[item],
                ),
            )
            for item in OUTCOME_FRESHNESS_STATUSES
        ),
    )


def _nav_trend(
    status: str,
    *,
    generated_at: datetime,
) -> PaperNavRiskTrendReport:
    report_count = 0 if status == "empty_nav_risk_history" else 1
    status_counts = {
        item: 1 if item == status and report_count else 0
        for item in NAV_RISK_TREND_STATUSES
    }
    has_unexecutable_positions = status == "latest_nav_has_unexecutable_positions"
    open_positions = 1 if has_unexecutable_positions else 0
    return PaperNavRiskTrendReport(
        generated_at=generated_at,
        config_version="nav-risk-trend-v0",
        nav_risk_report_count=report_count,
        first_report_generated_at=generated_at if report_count else None,
        latest_report_generated_at=generated_at if report_count else None,
        latest_exit_nav=Decimal("100.0000") if report_count else None,
        latest_cumulative_return=Decimal("0.000000") if report_count else None,
        latest_max_drawdown=Decimal("0.0000") if report_count else None,
        latest_max_drawdown_pct=Decimal("0.000000") if report_count else None,
        latest_nav_return_volatility=None,
        latest_open_position_count=open_positions,
        latest_fully_executable_count=0,
        latest_partially_executable_count=0,
        latest_no_exit_depth_count=open_positions,
        latest_largest_market_exposure_value=(
            Decimal("25.0000") if open_positions else None
        ),
        latest_largest_market_exposure_share=(
            Decimal("0.250000") if open_positions else None
        ),
        worst_observed_max_drawdown_pct=(
            Decimal("0.000000") if report_count else None
        ),
        consecutive_unexecutable_open_position_count=(
            1 if has_unexecutable_positions else 0
        ),
        status=status,
        status_rows=tuple(
            PaperNavRiskTrendStatusRow(
                status=item,
                report_count=status_counts[item],
                report_ratio=_ratio_row_count(report_count, status_counts[item]),
            )
            for item in NAV_RISK_TREND_STATUSES
        ),
    )


def _cost_trend(
    status: str,
    *,
    generated_at: datetime,
) -> PaperTradeCostTrendReport:
    report_count = 0 if status == "empty_cost_audit_history" else 1
    has_negative_edge = status == "latest_negative_cost_adjusted_edges"
    status_counts = {
        item: 1 if item == status and report_count else 0
        for item in COST_TREND_STATUSES
    }
    return PaperTradeCostTrendReport(
        generated_at=generated_at,
        config_version="paper-trade-cost-trend-v0",
        cost_audit_report_count=report_count,
        first_report_generated_at=generated_at if report_count else None,
        latest_report_generated_at=generated_at if report_count else None,
        latest_trade_count=1 if report_count else 0,
        latest_fill_rate=RATIO_ONE if report_count else None,
        latest_mean_theoretical_edge=Decimal("0.050000") if report_count else None,
        latest_mean_cost_adjusted_edge=(
            Decimal("-0.010000") if has_negative_edge else Decimal("0.040000")
        )
        if report_count
        else None,
        latest_mean_edge_cost_drag=Decimal("0.010000") if report_count else None,
        latest_total_edge_cost_drag=Decimal("0.010000") if report_count else None,
        latest_partial_fill_count=0,
        latest_negative_cost_adjusted_edge_count=1 if has_negative_edge else 0,
        worst_observed_mean_edge_cost_drag=(
            Decimal("0.010000") if report_count else None
        ),
        worst_observed_negative_cost_adjusted_edge_count=(
            1 if has_negative_edge else 0
        ),
        consecutive_negative_cost_adjusted_edge_count=(
            1 if has_negative_edge else 0
        ),
        status=status,
        status_rows=tuple(
            PaperTradeCostTrendStatusRow(
                status=item,
                status_count=status_counts[item],
                status_ratio=_ratio_row_count(report_count, status_counts[item]),
            )
            for item in COST_TREND_STATUSES
        ),
    )


def _report(
    *,
    generated_at: datetime,
    strategy_status: str | None = "local_evidence_observed",
    outcome_status: str = "latest_outcomes_fresh",
    nav_status: str = "latest_nav_risk_observed",
    cost_status: str = "latest_cost_observed",
) -> LocalObservabilityTrendsReport:
    return LocalObservabilityTrendsReport(
        generated_at=generated_at,
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=_strategy_trend(
            strategy_status,
            generated_at=generated_at,
        ),
        outcome_freshness=_outcome_freshness(
            outcome_status,
            generated_at=generated_at,
        ),
        nav_risk_trend=_nav_trend(nav_status, generated_at=generated_at),
        paper_trade_cost_trend=_cost_trend(cost_status, generated_at=generated_at),
    )


def test_local_observability_trends_db_history_empty_input_is_readonly():
    history = _history(())

    assert history.status == "empty_local_observability_trends_db_history"
    assert history.generated_at == GENERATED_AT
    assert history.config_version == "local-observability-trends-db-history-v0"
    assert history.report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.latest_strategy_evidence_status is None
    assert history.latest_outcome_status is None
    assert history.latest_nav_status is None
    assert history.latest_cost_status is None
    assert history.duplicate_generated_at_count == 0
    assert history.consecutive_outcome_stale_count == 0
    assert history.consecutive_nav_warning_or_high_risk_count == 0
    assert history.consecutive_cost_warning_or_critical_count == 0
    assert all(row.report_count == 0 for row in history.outcome_status_rows)
    assert all(row.report_ratio is None for row in history.outcome_status_rows)
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_local_observability_trends_db_history_preserves_input_order_not_time_sort():
    first = _report(
        generated_at=datetime(2026, 6, 20, 18, 0, tzinfo=UTC),
        strategy_status="local_evidence_gaps",
        outcome_status="latest_outcomes_fresh",
        nav_status="latest_nav_risk_observed",
        cost_status="latest_cost_observed",
    )
    timestamp_older_second = _report(
        generated_at=datetime(2026, 6, 20, 16, 0, tzinfo=UTC),
        strategy_status="local_risk_flags",
        outcome_status="latest_outcomes_stale",
        nav_status="latest_nav_has_unexecutable_positions",
        cost_status="latest_negative_cost_adjusted_edges",
    )

    history = _history([first, timestamp_older_second])

    assert history.status == "latest_local_observability_trends_warning"
    assert history.report_count == 2
    assert history.first_report_generated_at == first.generated_at
    assert history.latest_report_generated_at == timestamp_older_second.generated_at
    assert history.latest_strategy_evidence_status == "local_risk_flags"
    assert history.latest_outcome_status == "latest_outcomes_stale"
    assert history.latest_nav_status == "latest_nav_has_unexecutable_positions"
    assert history.latest_cost_status == "latest_negative_cost_adjusted_edges"

    outcome_rows = {row.status: row for row in history.outcome_status_rows}
    assert outcome_rows["latest_outcomes_fresh"].report_count == 1
    assert outcome_rows["latest_outcomes_fresh"].report_ratio == Decimal("0.500000")
    assert outcome_rows["latest_outcomes_stale"].report_count == 1
    assert outcome_rows["latest_outcomes_stale"].report_ratio == Decimal("0.500000")


def test_local_observability_trends_db_history_counts_duplicate_generated_at():
    timestamp = datetime(2026, 6, 20, 18, 0, tzinfo=UTC)
    reports = (
        _report(generated_at=timestamp),
        _report(generated_at=timestamp),
        _report(generated_at=timestamp),
        _report(generated_at=timestamp + timedelta(minutes=5)),
    )

    history = _history(reports)

    assert history.report_count == 4
    assert history.duplicate_generated_at_count == 2


def test_local_observability_trends_db_history_counts_consecutive_streaks():
    reports = (
        _report(generated_at=datetime(2026, 6, 20, 15, 0, tzinfo=UTC)),
        _report(
            generated_at=datetime(2026, 6, 20, 16, 0, tzinfo=UTC),
            outcome_status="latest_outcomes_stale",
            nav_status="latest_nav_has_unexecutable_positions",
            cost_status="latest_negative_cost_adjusted_edges",
        ),
        _report(
            generated_at=datetime(2026, 6, 20, 17, 0, tzinfo=UTC),
            outcome_status="latest_outcomes_stale",
            nav_status="latest_nav_has_unexecutable_positions",
            cost_status="latest_negative_cost_adjusted_edges",
        ),
    )

    history = _history(reports)

    assert history.consecutive_outcome_stale_count == 2
    assert history.consecutive_nav_warning_or_high_risk_count == 2
    assert history.consecutive_cost_warning_or_critical_count == 2


def test_local_observability_trends_db_history_rejects_latest_status_without_row_count():
    history = _history((_report(generated_at=GENERATED_AT),))

    mismatches = (
        {"latest_strategy_evidence_status": "local_evidence_gaps"},
        {
            "status": "latest_local_observability_trends_warning",
            "latest_outcome_status": "latest_outcomes_stale",
            "consecutive_outcome_stale_count": 1,
        },
        {
            "status": "latest_local_observability_trends_warning",
            "latest_nav_status": "latest_nav_has_unexecutable_positions",
            "consecutive_nav_warning_or_high_risk_count": 1,
        },
        {
            "status": "latest_local_observability_trends_warning",
            "latest_cost_status": "latest_negative_cost_adjusted_edges",
            "consecutive_cost_warning_or_critical_count": 1,
        },
    )
    expected_error = "latest status must be represented by status rows"

    for changes in mismatches:
        with pytest.raises(ValueError, match=expected_error):
            LocalObservabilityTrendsDbHistoryReport(
                **{**history.__dict__, **changes},
            )
        with pytest.raises(ValueError, match=expected_error):
            replace(history, **changes)


def test_local_observability_trends_db_history_rejects_wrong_report_type_and_subclass():
    report = _report(generated_at=GENERATED_AT)

    class ReportSubclass(LocalObservabilityTrendsReport):
        pass

    subclass = ReportSubclass(**report.__dict__)

    with pytest.raises(ValueError, match="reports must contain"):
        _history((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reports must contain"):
        _history((subclass,))


def test_local_observability_trends_db_history_rejects_non_exact_config_and_datetime():
    class ConfigSubclass(LocalObservabilityTrendsDbHistoryConfig):
        pass

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="config must be"):
        build_local_observability_trends_db_history_report(
            (),
            config=ConfigSubclass("local-observability-trends-db-history-v0"),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_local_observability_trends_db_history_report(
            (),
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 20, 19, 0, tzinfo=UTC),
        )


def test_local_observability_trends_db_history_dataclasses_are_frozen():
    history = _history(())
    status_row = history.outcome_status_rows[0]
    config = _config()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        status_row.report_count = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        history.status = "changed"  # type: ignore[misc]


def test_local_observability_trends_db_history_validates_hard_flags():
    report = _report(generated_at=GENERATED_AT)
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "readonly", False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _history((unsafe_report,))

    history = _history((report,))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(history, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(history, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(history, readonly=False)


def test_local_observability_trends_db_history_uses_decimal_ratios_not_float():
    first = _report(
        generated_at=datetime(2026, 6, 20, 16, 0, tzinfo=UTC),
        outcome_status="latest_outcomes_fresh",
        nav_status="latest_nav_risk_observed",
        cost_status="latest_cost_observed",
    )
    second = _report(
        generated_at=datetime(2026, 6, 20, 17, 0, tzinfo=UTC),
        outcome_status="latest_outcomes_stale",
        nav_status="latest_nav_has_unexecutable_positions",
        cost_status="latest_negative_cost_adjusted_edges",
    )
    third = _report(
        generated_at=datetime(2026, 6, 20, 18, 0, tzinfo=UTC),
        outcome_status="latest_outcomes_stale",
        nav_status="latest_nav_has_unexecutable_positions",
        cost_status="latest_negative_cost_adjusted_edges",
    )

    history = _history((first, second, third))

    all_rows = (
        history.strategy_evidence_status_rows
        + history.outcome_status_rows
        + history.nav_status_rows
        + history.cost_status_rows
    )
    assert all(
        row.report_ratio is None or type(row.report_ratio) is Decimal
        for row in all_rows
    )
    outcome_rows = {row.status: row for row in history.outcome_status_rows}
    assert outcome_rows["latest_outcomes_stale"].report_ratio == Decimal("0.666667")
    nav_rows = {row.status: row for row in history.nav_status_rows}
    assert (
        nav_rows["latest_nav_has_unexecutable_positions"].report_ratio
        == Decimal("0.666667")
    )
