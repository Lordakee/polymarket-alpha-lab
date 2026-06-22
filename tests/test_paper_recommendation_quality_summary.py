from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 22, 11, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class ReasonCountShape:
    reason_code: str
    count: int


@dataclass(frozen=True)
class TrendRowShape:
    reason_code: str
    source_status: str = "recommend"
    count: int = 1
    first_seen_at: datetime = SOURCE_AT
    latest_seen_at: datetime = SOURCE_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class HealthReportShape:
    health_status: str = "pass"
    reason_code_counts: tuple[ReasonCountShape, ...] = (
        ReasonCountShape("positive_net_edge", 2),
        ReasonCountShape("wide_spread", 1),
    )
    row_count: int = 3
    generated_at: datetime = SOURCE_AT
    config_version: str = "paper-recommendation-health-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class ConsistencyReportShape:
    consistency_status: str = "pass"
    reason_codes: tuple[str, ...] = ("recommendation_consistency_passed",)
    group_count: int = 2
    generated_at: datetime = SOURCE_AT
    config_version: str = "paper-recommendation-consistency-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class RiskBudgetReportShape:
    status: str = "pass"
    reason_codes: tuple[str, ...] = ("risk_budget_passed",)
    selected_count: int = 2
    generated_at: datetime = SOURCE_AT
    config_version: str = "paper-recommendation-risk-budget-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class ReasonTrendReportShape:
    source_report_count: int = 2
    reason_trend_rows: tuple[TrendRowShape, ...] = (
        TrendRowShape("positive_net_edge", count=2),
        TrendRowShape("wide_spread", source_status="watch", count=1),
    )
    transition_trend_rows: tuple[object, ...] = ()
    generated_at: datetime = SOURCE_AT
    config_version: str = "paper-recommendation-reason-trend-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class RankStabilityReportShape:
    stability_status: str = "stable"
    reason_codes: tuple[str, ...] = ("stable_ready_candidates_present",)
    candidate_count: int = 1
    generated_at: datetime = SOURCE_AT
    config_version: str = "paper-strategy-recommendation-rank-stability-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _api():
    return import_module("polymarket_alpha_lab.paper_recommendation_quality_summary")


def _build(
    *,
    health_report: object | None = HealthReportShape(),
    consistency_report: object | None = ConsistencyReportShape(),
    risk_budget_report: object | None = RiskBudgetReportShape(),
    reason_trend_report: object | None = ReasonTrendReportShape(),
    rank_stability_report: object | None = RankStabilityReportShape(),
    generated_at: datetime = GENERATED_AT,
    config_version: str = "paper-recommendation-quality-summary-v0",
):
    return _api().build_paper_recommendation_quality_summary_report(
        health_report=health_report,
        consistency_report=consistency_report,
        risk_budget_report=risk_budget_report,
        reason_trend_report=reason_trend_report,
        rank_stability_report=rank_stability_report,
        generated_at=generated_at,
        config_version=config_version,
    )


def test_quality_summary_passes_when_required_reports_pass_and_rank_is_stable():
    report = _build()
    api = _api()

    assert isinstance(report, api.PaperRecommendationQualitySummaryReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-recommendation-quality-summary-v0"
    assert report.summary_status == "pass"
    assert report.subreport_count == 5
    assert report.pass_count == 5
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.incomplete_count == 0
    assert tuple(row.report_name for row in report.subreports) == (
        "health",
        "consistency",
        "risk_budget",
        "reason_trend",
        "rank_stability",
    )
    assert tuple(row.status for row in report.subreports) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert report.reason_code_counts == (
        api.PaperRecommendationQualityReasonCodeCount(
            reason_code="positive_net_edge",
            subreport_count=2,
        ),
        api.PaperRecommendationQualityReasonCodeCount(
            reason_code="wide_spread",
            subreport_count=2,
        ),
        api.PaperRecommendationQualityReasonCodeCount(
            reason_code="recommendation_consistency_passed",
            subreport_count=1,
        ),
        api.PaperRecommendationQualityReasonCodeCount(
            reason_code="risk_budget_passed",
            subreport_count=1,
        ),
        api.PaperRecommendationQualityReasonCodeCount(
            reason_code="stable_ready_candidates_present",
            subreport_count=1,
        ),
    )
    assert report.reason_codes == tuple(
        row.reason_code for row in report.reason_code_counts
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_quality_summary_status_precedence_and_optional_rank_watch():
    optional_rank_missing = _build(rank_stability_report=None)

    assert optional_rank_missing.summary_status == "watch"
    assert optional_rank_missing.watch_count == 1
    assert optional_rank_missing.subreports[-1].report_name == "rank_stability"
    assert optional_rank_missing.subreports[-1].status == "watch"
    assert optional_rank_missing.subreports[-1].reason_codes == (
        "optional_rank_stability_report_missing",
    )

    incomplete = _build(health_report=None, rank_stability_report=None)
    assert incomplete.summary_status == "incomplete"
    assert incomplete.incomplete_count == 1
    assert incomplete.watch_count == 1
    assert incomplete.reason_codes[0] == "health_report_missing"

    blocked = _build(
        health_report=None,
        risk_budget_report=RiskBudgetReportShape(
            status="blocked",
            reason_codes=("empty_selection",),
            selected_count=0,
        ),
    )
    assert blocked.summary_status == "blocked"
    assert blocked.blocked_count == 1
    assert blocked.incomplete_count == 1
    assert "empty_selection" in blocked.reason_codes


def test_quality_summary_maps_watch_and_blocked_report_like_statuses():
    report = _build(
        health_report=HealthReportShape(
            health_status="watch",
            reason_code_counts=(ReasonCountShape("high_average_cost", 1),),
        ),
        consistency_report=ConsistencyReportShape(
            consistency_status="blocked",
            reason_codes=("edge_spread_exceeds_consistency_cap",),
        ),
        risk_budget_report=RiskBudgetReportShape(
            status="watch",
            reason_codes=("near_total_utilization_cap",),
        ),
        reason_trend_report=ReasonTrendReportShape(
            source_report_count=0,
            reason_trend_rows=(),
        ),
        rank_stability_report=RankStabilityReportShape(
            stability_status="watch",
            reason_codes=("insufficient_history",),
        ),
    )

    assert report.summary_status == "blocked"
    assert report.pass_count == 0
    assert report.watch_count == 4
    assert report.blocked_count == 1
    assert tuple((row.report_name, row.status) for row in report.subreports) == (
        ("health", "watch"),
        ("consistency", "blocked"),
        ("risk_budget", "watch"),
        ("reason_trend", "watch"),
        ("rank_stability", "watch"),
    )
    assert report.subreports[3].reason_codes == ("reason_trend_source_reports_missing",)
    assert report.reason_codes == (
        "edge_spread_exceeds_consistency_cap",
        "high_average_cost",
        "insufficient_history",
        "near_total_utilization_cap",
        "reason_trend_source_reports_missing",
    )


def test_quality_summary_validates_hard_flags_utc_strictness_and_freezing():
    report = _build(
        generated_at=datetime(2026, 6, 22, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        report.summary_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _build(generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        _build(generated_at=_DatetimeSubclass(2026, 6, 22, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config_version"):
        _build(config_version=" paper-recommendation-quality-summary-v0")
    with pytest.raises(ValueError, match="health report must be paper_only"):
        _build(health_report=HealthReportShape(paper_only=False))
    with pytest.raises(ValueError, match="rank_stability report must be readonly"):
        _build(rank_stability_report=RankStabilityReportShape(readonly=False))


def test_quality_summary_dataclasses_reject_inconsistent_values():
    api = _api()
    valid = _build()

    with pytest.raises(ValueError, match="subreport_count"):
        replace(valid, subreport_count=4)
    with pytest.raises(ValueError, match="pass_count"):
        replace(valid, pass_count=4)
    with pytest.raises(ValueError, match="summary_status"):
        replace(valid, summary_status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid, reason_codes=("risk_budget_passed",))
    with pytest.raises(ValueError, match="subreport_count"):
        api.PaperRecommendationQualityReasonCodeCount(
            reason_code="risk_budget_passed",
            subreport_count=_IntSubclass(1),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        api.PaperRecommendationQualitySubreportSummary(
            report_name="health",
            status="pass",
            generated_at=SOURCE_AT,
            config_version="paper-recommendation-health-v0",
            row_count=1,
            reason_codes=("duplicate", "duplicate"),
        )
