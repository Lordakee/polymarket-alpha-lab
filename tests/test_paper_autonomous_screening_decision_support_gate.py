from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import inspect

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
    build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueuePriorityRow,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)
from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    PaperProjectScreeningRankStabilityReport,
    PaperProjectScreeningRankStabilityRow,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
    PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount,
    PaperResearchPacketOperatorFlowDbHistoryGateReport,
)


GENERATED_AT = datetime(2026, 6, 23, 19, 0, tzinfo=UTC)
QUEUE_AT = datetime(2026, 6, 23, 18, 45, tzinfo=UTC)
OPERATOR_SOURCE_AT = datetime(2026, 6, 23, 18, 30, tzinfo=UTC)
LATEST_OPERATOR_AT = datetime(2026, 6, 23, 18, 40, tzinfo=UTC)

NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}
RESEARCH_PRIORITY_BY_ACTION_STATUS = {
    "research_ready": "research_review",
    "watch": "await_fresh_context",
    "blocked": "repair_evidence",
}
ACTION_STATUS_SCORE = {
    "research_ready": Decimal("3.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("0.000000"),
}
NEXT_STEP_BY_RISK_STATUS = {
    "pass": "allocate_paper_research_queue",
    "watch": "throttle_paper_research_queue",
    "blocked": "block_paper_research_queue",
}
OPERATOR_NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_screening_decision_support",
    "watch": "throttle_paper_autonomous_screening_decision_support",
    "blocked": "block_paper_autonomous_screening_decision_support",
}
OPERATOR_REASON_BY_STATUS = {
    "pass": "paper_operator_flow_db_history_gate_passed",
    "watch": "latest_operator_flow_watch",
    "blocked": "latest_operator_flow_blocked",
}


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate",
    )


def _operator_flow_gate_report(
    *,
    gate_status: str = "pass",
    reason_codes: tuple[str, ...] | None = None,
) -> PaperResearchPacketOperatorFlowDbHistoryGateReport:
    if reason_codes is None:
        reason_codes = (OPERATOR_REASON_BY_STATUS[gate_status],)
    sorted_reasons = tuple(sorted(reason_codes))
    return PaperResearchPacketOperatorFlowDbHistoryGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-research-packet-operator-flow-db-history-gate-v0",
        source_config_version="paper-research-packet-operator-flow-db-history-v0",
        source_generated_at=OPERATOR_SOURCE_AT,
        gate_status=gate_status,
        recommended_next_step=OPERATOR_NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=tuple(
            PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in sorted_reasons
        ),
        source_report_count=3,
        latest_source_generated_at=LATEST_OPERATOR_AT,
        latest_source_age_seconds=1_200,
        source_history_status=gate_status,
        latest_flow_status=gate_status,
        latest_quality_status=gate_status,
        latest_operator_history_status=gate_status,
        duplicate_generated_at_count=0,
        consecutive_latest_pass_count=3 if gate_status == "pass" else 0,
        consecutive_latest_watch_count=1 if gate_status == "watch" else 0,
        consecutive_latest_blocked_count=1 if gate_status == "blocked" else 0,
        reason_codes=sorted_reasons,
    )


def _priority_row(
    *,
    priority_rank: int = 1,
    generated_at: datetime = QUEUE_AT,
    action_status: str = "research_ready",
    candidate_count: int = 1,
    ready_count: int = 1,
    watch_count: int = 0,
    blocked_count: int = 0,
    total_ready_notional: Decimal = Decimal("10.000000"),
    top_queue_score: Decimal = Decimal("0.400000"),
    average_ready_score: Decimal = Decimal("0.300000"),
) -> PaperActionGatedStrategyRecommendationQueuePriorityRow:
    return PaperActionGatedStrategyRecommendationQueuePriorityRow(
        priority_rank=priority_rank,
        source_generated_at=generated_at - timedelta(minutes=5),
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=NEXT_STEP_BY_ACTION_STATUS[action_status],
        research_priority=RESEARCH_PRIORITY_BY_ACTION_STATUS[action_status],
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_ready_notional=total_ready_notional,
        top_queue_score=top_queue_score,
        average_ready_score=average_ready_score,
        research_priority_score=(
            ACTION_STATUS_SCORE[action_status]
            + Decimal(ready_count)
            + top_queue_score
            + average_ready_score
        ).quantize(Decimal("0.000001")),
    )


def _priority_report(
    *,
    generated_at: datetime = QUEUE_AT,
    action_status: str = "research_ready",
) -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    if action_status == "research_ready":
        row = _priority_row(generated_at=generated_at)
    elif action_status == "watch":
        row = _priority_row(
            generated_at=generated_at,
            action_status="watch",
            candidate_count=1,
            ready_count=0,
            watch_count=1,
            total_ready_notional=Decimal("0.000000"),
            top_queue_score=Decimal("0.000000"),
            average_ready_score=Decimal("0.000000"),
        )
    elif action_status == "blocked":
        row = _priority_row(
            generated_at=generated_at,
            action_status="blocked",
            candidate_count=1,
            ready_count=0,
            blocked_count=1,
            total_ready_notional=Decimal("0.000000"),
            top_queue_score=Decimal("0.000000"),
            average_ready_score=Decimal("0.000000"),
        )
    else:
        raise AssertionError(f"unknown test action_status {action_status}")

    rows = (row,)
    return PaperActionGatedStrategyRecommendationQueuePriorityReport(
        generated_at=generated_at,
        source_report_count=len(rows),
        research_ready_count=sum(1 for item in rows if item.action_status == "research_ready"),
        watch_count=sum(1 for item in rows if item.action_status == "watch"),
        blocked_count=sum(1 for item in rows if item.action_status == "blocked"),
        total_ready_notional=sum((item.total_ready_notional for item in rows), Decimal("0")),
        top_research_priority_score=max(
            (item.research_priority_score for item in rows),
            default=Decimal("0.000000"),
        ),
        average_research_priority_score=(
            sum((item.research_priority_score for item in rows), Decimal("0"))
            / Decimal(len(rows))
        ).quantize(Decimal("0.000001")),
        priority_rows=rows,
    )


def _risk_report(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    *,
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("queue_risk_passed",),
) -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    ready_notional = priority_report.total_ready_notional
    largest_notional = max(
        (row.total_ready_notional for row in priority_report.priority_rows),
        default=Decimal("0.000000"),
    )
    blocking_reasons = {
        "empty_queue_reports",
        "source_queue_blocked",
        "total_ready_notional_cap_exceeded",
        "single_queue_ready_notional_cap_exceeded",
        "ready_candidate_count_cap_exceeded",
        "candidate_count_cap_exceeded",
    }
    watch_reasons = {
        "source_queue_watch",
        "near_total_ready_notional_cap",
        "near_single_queue_ready_notional_cap",
        "near_ready_candidate_count_cap",
        "near_candidate_count_cap",
    }
    max_total_ready_notional = Decimal("100.000000")
    max_single_queue_ready_notional = Decimal("100.000000")
    return PaperActionGatedStrategyRecommendationQueueRiskReport(
        generated_at=priority_report.generated_at,
        config_version="action-gated-queue-risk-v0",
        source_config_versions=("action-gated-strategy-recommendation-queue-v0",),
        status=status,
        recommended_next_step=NEXT_STEP_BY_RISK_STATUS[status],
        reason_codes=reason_codes,
        source_queue_count=priority_report.source_report_count,
        research_ready_source_count=priority_report.research_ready_count,
        watch_source_count=priority_report.watch_count,
        blocked_source_count=priority_report.blocked_count,
        candidate_count=sum(row.candidate_count for row in priority_report.priority_rows),
        ready_count=sum(row.ready_count for row in priority_report.priority_rows),
        watch_count=sum(row.watch_count for row in priority_report.priority_rows),
        blocked_count=sum(row.blocked_count for row in priority_report.priority_rows),
        blocked_reason_count=sum(1 for reason in reason_codes if reason in blocking_reasons),
        watch_reason_count=sum(1 for reason in reason_codes if reason in watch_reasons),
        total_ready_notional=ready_notional,
        largest_queue_ready_notional=largest_notional,
        total_ready_notional_utilization=(
            ready_notional / max_total_ready_notional
        ).quantize(Decimal("0.000001")),
        largest_queue_ready_notional_utilization=(
            largest_notional / max_single_queue_ready_notional
        ).quantize(Decimal("0.000001")),
        max_total_ready_notional=max_total_ready_notional,
        max_single_queue_ready_notional=max_single_queue_ready_notional,
        max_ready_candidate_count=10,
        max_total_candidate_count=20,
        throttle_utilization_threshold=Decimal("0.900000"),
    )


def _queue_snapshot(
    *,
    generated_at: datetime = QUEUE_AT,
    action_status: str = "research_ready",
    risk_status: str = "pass",
    risk_reason_codes: tuple[str, ...] = ("queue_risk_passed",),
) -> tuple[
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
]:
    priority_report = _priority_report(
        generated_at=generated_at,
        action_status=action_status,
    )
    return (
        priority_report,
        _risk_report(
            priority_report,
            status=risk_status,
            reason_codes=risk_reason_codes,
        ),
    )


def _rank_stability_row(
    *,
    stability_status: str = "stable",
    latest_research_bucket: str = "research_ready",
    latest_screening_status: str = "screening_ready",
    reason_codes: tuple[str, ...] = ("stable_research_ready",),
    scoring_side_changed: bool = False,
) -> PaperProjectScreeningRankStabilityRow:
    return PaperProjectScreeningRankStabilityRow(
        market_slug="fed-cut-june-2026",
        stability_status=stability_status,
        latest_research_bucket=latest_research_bucket,
        latest_screening_status=latest_screening_status,
        latest_source_status="paper_review_ready",
        latest_scoring_side="yes",
        present_snapshot_count=2,
        ready_snapshot_count=2 if latest_research_bucket == "research_ready" else 1,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=Decimal("0.700000"),
        latest_screening_score=Decimal("0.710000"),
        screening_score_delta=Decimal("0.010000"),
        max_screening_score_delta=Decimal("0.010000"),
        scoring_side_changed=scoring_side_changed,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=latest_research_bucket != "research_ready",
        reason_codes=reason_codes,
    )


def _rank_stability_report(
    *,
    stability_status: str = "stable",
) -> PaperProjectScreeningRankStabilityReport:
    if stability_status == "stable":
        row = _rank_stability_row()
        reason_codes = ("stable_ready_candidates_present",)
        top_stable_market_slug = "fed-cut-june-2026"
    elif stability_status == "watch":
        row = _rank_stability_row(
            stability_status="watch",
            reason_codes=("scoring_side_changed",),
            scoring_side_changed=True,
        )
        reason_codes = ("unstable_ready_candidates_present",)
        top_stable_market_slug = None
    elif stability_status == "blocked":
        row = _rank_stability_row(
            stability_status="blocked",
            latest_research_bucket="blocked",
            latest_screening_status="screening_blocked",
            reason_codes=("latest_candidate_blocked",),
        )
        reason_codes = ("blocked_stability_candidates_present",)
        top_stable_market_slug = None
    else:
        raise AssertionError(f"unknown test stability_status {stability_status}")

    rows = (row,)
    return PaperProjectScreeningRankStabilityReport(
        generated_at=QUEUE_AT,
        config_version="project-screening-rank-stability-v0",
        source_report_count=2,
        candidate_count=1,
        stability_status=stability_status,
        stable_count=1 if stability_status == "stable" else 0,
        watch_count=1 if stability_status == "watch" else 0,
        blocked_count=1 if stability_status == "blocked" else 0,
        stable_ready_count=1 if stability_status == "stable" else 0,
        unstable_ready_count=1 if stability_status == "watch" else 0,
        scoring_side_changed_count=1 if stability_status == "watch" else 0,
        source_status_changed_count=0,
        screening_status_changed_count=0,
        research_bucket_changed_count=1 if stability_status == "blocked" else 0,
        latest_generated_at=QUEUE_AT - timedelta(minutes=1),
        top_stable_market_slug=top_stable_market_slug,
        reason_codes=reason_codes,
        rows=rows,
    )


def _build_gate(
    *,
    operator_flow_gate_report: PaperResearchPacketOperatorFlowDbHistoryGateReport | None = None,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport | None = None,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport | None = None,
    trend_report=None,
    rank_stability_report: PaperProjectScreeningRankStabilityReport | None = None,
    generated_at: datetime = GENERATED_AT,
):
    if priority_report is None or risk_report is None:
        priority_report, risk_report = _queue_snapshot()
    return _api().build_paper_autonomous_screening_decision_support_gate_report(
        operator_flow_gate_report=operator_flow_gate_report
        or _operator_flow_gate_report(),
        priority_report=priority_report,
        risk_report=risk_report,
        trend_report=trend_report,
        rank_stability_report=rank_stability_report,
        generated_at=generated_at,
    )


def _replace_gate_reasons(
    report,
    *,
    gate_status: str,
    reason_codes: tuple[str, ...],
):
    api = _api()
    return replace(
        report,
        gate_status=gate_status,
        recommended_next_step=api.NEXT_STEP_BY_STATUS[gate_status],
        reason_codes=reason_codes,
        reason_code_counts=tuple(
            api.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
                reason_code,
                1,
            )
            for reason_code in reason_codes
        ),
    )


def test_gate_passes_clean_operator_flow_queue_risk_and_stable_rank_inputs():
    report = _build_gate(rank_stability_report=_rank_stability_report())

    api = _api()
    assert type(report) is api.PaperAutonomousScreeningDecisionSupportGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "paper-autonomous-screening-decision-support-gate-v0"
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "advance_paper_autonomous_screening_recommendations"
    )
    assert report.reason_codes == (
        "paper_autonomous_screening_decision_support_gate_passed",
    )
    assert report.reason_code_counts == (
        api.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
            "paper_autonomous_screening_decision_support_gate_passed",
            1,
        ),
    )
    assert report.operator_flow_gate_status == "pass"
    assert report.queue_risk_status == "pass"
    assert report.queue_source_report_count == 1
    assert report.queue_research_ready_count == 1
    assert report.queue_watch_count == 0
    assert report.queue_blocked_count == 0
    assert report.queue_candidate_count == 1
    assert report.queue_ready_count == 1
    assert report.queue_total_ready_notional == Decimal("10.000000")
    assert report.queue_top_research_priority_score == Decimal("4.700000")
    assert report.queue_average_research_priority_score == Decimal("4.700000")
    assert report.trend_source_snapshot_count is None
    assert report.trend_latest_risk_status is None
    assert report.rank_stability_status == "stable"
    assert report.rank_stable_ready_count == 1
    assert report.rank_unstable_ready_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_gate_public_api_is_exported_from_package_root():
    import polymarket_alpha_lab as package

    api = _api()

    assert package.PaperAutonomousScreeningDecisionSupportGateReport is (
        api.PaperAutonomousScreeningDecisionSupportGateReport
    )
    assert package.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount is (
        api.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
    )
    assert package.build_paper_autonomous_screening_decision_support_gate_report is (
        api.build_paper_autonomous_screening_decision_support_gate_report
    )
    assert (
        "PaperAutonomousScreeningDecisionSupportGateReport" in package.__all__
    )
    assert (
        "build_paper_autonomous_screening_decision_support_gate_report"
        in package.__all__
    )


def test_gate_watches_when_optional_trend_or_rank_stability_requires_throttle():
    first = _queue_snapshot(generated_at=QUEUE_AT)
    duplicate_at_snapshot = _queue_snapshot(generated_at=QUEUE_AT)
    trend_report = (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            (first, duplicate_at_snapshot),
            generated_at=GENERATED_AT,
        )
    )

    report = _build_gate(
        trend_report=trend_report,
        rank_stability_report=_rank_stability_report(stability_status="watch"),
    )

    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_screening_recommendations"
    )
    assert report.reason_codes == (
        "project_screening_rank_stability_watch",
        "queue_decision_support_trend_duplicate_generated_at",
    )
    assert report.trend_source_snapshot_count == 2
    assert report.trend_duplicate_generated_at_count == 1
    assert report.rank_stability_status == "watch"
    assert report.rank_unstable_ready_count == 1


def test_gate_blocks_when_any_required_source_is_blocked_even_with_watch_reasons():
    priority_report, risk_report = _queue_snapshot(
        action_status="blocked",
        risk_status="blocked",
        risk_reason_codes=("source_queue_blocked",),
    )

    report = _build_gate(
        operator_flow_gate_report=_operator_flow_gate_report(gate_status="watch"),
        priority_report=priority_report,
        risk_report=risk_report,
        rank_stability_report=_rank_stability_report(stability_status="watch"),
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_screening_recommendations"
    )
    assert report.reason_codes == (
        "operator_flow_db_history_gate_watch",
        "project_screening_rank_stability_watch",
        "queue_risk_blocked",
    )
    assert "paper_autonomous_screening_decision_support_gate_passed" not in report.reason_codes
    assert report.operator_flow_gate_status == "watch"
    assert report.queue_risk_status == "blocked"


def test_gate_normalizes_datetimes_and_rejects_mismatched_queue_inputs():
    generated_at = datetime(2026, 6, 23, 15, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = _build_gate(generated_at=generated_at)

    assert report.generated_at == GENERATED_AT

    priority_report, risk_report = _queue_snapshot()
    object.__setattr__(risk_report, "source_queue_count", 2)
    with pytest.raises(ValueError, match="same source snapshot"):
        _build_gate(priority_report=priority_report, risk_report=risk_report)


def test_gate_rejects_wrong_types_subclasses_false_flags_and_invalid_report_invariants():
    api = _api()
    priority_report, risk_report = _queue_snapshot()

    class OperatorGateSubclass(PaperResearchPacketOperatorFlowDbHistoryGateReport):
        pass

    class PriorityReportSubclass(PaperActionGatedStrategyRecommendationQueuePriorityReport):
        pass

    class RiskReportSubclass(PaperActionGatedStrategyRecommendationQueueRiskReport):
        pass

    with pytest.raises(ValueError, match="operator_flow_gate_report"):
        _build_gate(operator_flow_gate_report=object())
    with pytest.raises(ValueError, match="priority_report"):
        _build_gate(priority_report=object(), risk_report=risk_report)
    with pytest.raises(ValueError, match="risk_report"):
        _build_gate(priority_report=priority_report, risk_report=object())
    with pytest.raises(ValueError, match="operator_flow_gate_report"):
        _build_gate(
            operator_flow_gate_report=OperatorGateSubclass(
                **_operator_flow_gate_report().__dict__,
            ),
        )
    with pytest.raises(ValueError, match="priority_report"):
        _build_gate(
            priority_report=PriorityReportSubclass(**priority_report.__dict__),
            risk_report=risk_report,
        )
    with pytest.raises(ValueError, match="risk_report"):
        _build_gate(
            priority_report=priority_report,
            risk_report=RiskReportSubclass(**risk_report.__dict__),
        )

    object.__setattr__(priority_report, "readonly", False)
    with pytest.raises(ValueError, match="priority_report must be readonly"):
        _build_gate(priority_report=priority_report, risk_report=risk_report)

    clean_report = _build_gate()
    with pytest.raises(FrozenInstanceError):
        clean_report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(clean_report, recommended_next_step="review_live_orders")
    with pytest.raises(ValueError, match="gate_status"):
        replace(clean_report, gate_status="paused")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            clean_report,
            reason_code_counts=(
                api.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
                    "paper_autonomous_screening_decision_support_gate_passed",
                    1,
                ),
                api.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
                    "paper_autonomous_screening_decision_support_gate_passed",
                    1,
                ),
            ),
        )


@pytest.mark.parametrize(
    ("reason_code", "gate_status", "expected_message"),
    (
        (
            "operator_flow_db_history_gate_watch",
            "watch",
            "operator_flow_gate_status must match reason_codes",
        ),
        (
            "operator_flow_db_history_gate_blocked",
            "blocked",
            "operator_flow_gate_status must match reason_codes",
        ),
        (
            "queue_risk_watch",
            "watch",
            "queue_risk_status must match reason_codes",
        ),
        (
            "queue_risk_blocked",
            "blocked",
            "queue_risk_status must match reason_codes",
        ),
    ),
)
def test_direct_report_rejects_source_pass_status_with_watch_or_blocked_reason(
    reason_code: str,
    gate_status: str,
    expected_message: str,
) -> None:
    clean_report = _build_gate()

    with pytest.raises(ValueError, match=expected_message):
        _replace_gate_reasons(
            clean_report,
            gate_status=gate_status,
            reason_codes=(reason_code,),
        )


@pytest.mark.parametrize(
    ("reason_code", "gate_status", "expected_message"),
    (
        (
            "queue_decision_support_trend_latest_risk_watch",
            "watch",
            "trend reason_codes require trend fields",
        ),
        (
            "project_screening_rank_stability_watch",
            "watch",
            "rank_stability_status must match reason_codes",
        ),
        (
            "project_screening_rank_stability_blocked",
            "blocked",
            "rank_stability_status must match reason_codes",
        ),
    ),
)
def test_direct_report_rejects_optional_source_reason_without_source_fields(
    reason_code: str,
    gate_status: str,
    expected_message: str,
) -> None:
    clean_report = _build_gate()

    with pytest.raises(ValueError, match=expected_message):
        _replace_gate_reasons(
            clean_report,
            gate_status=gate_status,
            reason_codes=(reason_code,),
        )


@pytest.mark.parametrize(
    ("field_name", "wrong_next_step", "expected_message"),
    (
        (
            "operator_flow_recommended_next_step",
            OPERATOR_NEXT_STEP_BY_STATUS["watch"],
            "operator_flow_recommended_next_step must match operator_flow_gate_status",
        ),
        (
            "queue_risk_recommended_next_step",
            NEXT_STEP_BY_RISK_STATUS["watch"],
            "queue_risk_recommended_next_step must match queue_risk_status",
        ),
    ),
)
def test_direct_report_rejects_source_next_steps_that_do_not_match_source_status(
    field_name: str,
    wrong_next_step: str,
    expected_message: str,
) -> None:
    clean_report = _build_gate()

    with pytest.raises(ValueError, match=expected_message):
        replace(clean_report, **{field_name: wrong_next_step})


def test_direct_report_reason_code_counts_are_single_report_counts() -> None:
    api = _api()
    clean_report = _build_gate()

    with pytest.raises(ValueError, match="reason_code_counts report_count must be 1"):
        replace(
            clean_report,
            reason_code_counts=(
                api.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
                    "paper_autonomous_screening_decision_support_gate_passed",
                    2,
                ),
            ),
        )


def test_direct_report_gate_status_must_match_reason_codes_independently() -> None:
    api = _api()
    clean_report = _build_gate()

    with pytest.raises(ValueError, match="gate_status must match reason_codes"):
        replace(
            clean_report,
            gate_status="watch",
            recommended_next_step=api.NEXT_STEP_BY_STATUS["watch"],
        )


def test_direct_report_rejects_partial_optional_trend_and_rank_fields() -> None:
    clean_report = _build_gate()

    with pytest.raises(
        ValueError,
        match="trend_latest_risk_status is required with trend snapshots",
    ):
        replace(clean_report, trend_source_snapshot_count=1)

    with pytest.raises(ValueError, match="trend fields must be absent without snapshots"):
        replace(
            clean_report,
            trend_source_snapshot_count=0,
            trend_latest_risk_status="pass",
        )

    with pytest.raises(ValueError, match="rank fields must be present together"):
        replace(clean_report, rank_stability_status="stable")


@pytest.mark.parametrize(
    "field_name",
    (
        "queue_total_ready_notional",
        "queue_largest_ready_notional",
        "queue_top_research_priority_score",
        "queue_average_research_priority_score",
    ),
)
def test_direct_report_rejects_raw_negative_decimal_before_quantization(
    field_name: str,
) -> None:
    clean_report = _build_gate()

    with pytest.raises(ValueError, match=f"{field_name} must be nonnegative"):
        replace(clean_report, **{field_name: Decimal("-0.0000001")})


def test_gate_module_is_pure_paper_report_only_readonly_and_uses_decimal_numbers():
    source = inspect.getsource(_api())
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    float_literals: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)

    forbidden_imports = {
        "os",
        "sqlite3",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "submit_order",
        "cancel_order",
        "sign_order",
        "place_order",
    }
    forbidden_fragments = (
        "wallet",
        "private_key",
        "private-key",
        "auth",
        "order_submission",
        "submit_order",
        "cancel_order",
        "signing",
        "exchange mutation",
        "live trading",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)
