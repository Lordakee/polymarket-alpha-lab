from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    build_paper_action_gated_strategy_recommendation_queue_priority_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskConfig,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
    build_paper_action_gated_strategy_recommendation_queue_risk_report,
)
from polymarket_alpha_lab.candidate_assessment import PaperCandidateAssessmentReport
from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
    PaperAutonomousAllocationProposalConfig,
    PaperAutonomousAllocationProposalReasonCodeCount,
    PaperAutonomousAllocationProposalReport,
    PaperAutonomousAllocationProposalSourceQueueSummary,
    build_paper_autonomous_allocation_proposal_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationConfig,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
)
from polymarket_alpha_lab.strategy_recommendation_queue import (
    PaperStrategyRecommendationQueueRow,
    PaperStrategyRecommendationQueueSummaryReport,
)


GENERATED_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 23, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class ProposalConfigSubclass(PaperAutonomousAllocationProposalConfig):
    pass


class SourceQueueReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _allocation_config(**overrides: object) -> PaperRecommendationAllocationConfig:
    values = {
        "config_version": "allocation-v0",
        "total_paper_budget": d("100.000000"),
        "max_paper_notional_per_market": d("50.000000"),
        "max_paper_notional_per_event": d("50.000000"),
        "max_paper_notional_per_theme": d("50.000000"),
        "max_paper_notional_per_correlation_group": d("50.000000"),
    }
    values.update(overrides)
    return PaperRecommendationAllocationConfig(**values)


def _proposal_config(**overrides: object) -> PaperAutonomousAllocationProposalConfig:
    values = {
        "config_version": DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
        "allocation_config": _allocation_config(),
    }
    values.update(overrides)
    return PaperAutonomousAllocationProposalConfig(**values)


def _empty_candidate_assessment_report() -> PaperCandidateAssessmentReport:
    return PaperCandidateAssessmentReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="candidate-assessment-v1",
        candidate_count=0,
        assessed_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        assessment_rows=(),
    )


def _empty_bundle_report() -> PaperStrategyRecommendationBundleReport:
    recommendation_report = PaperStrategyCandidateRecommendationReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="strategy-candidate-recommendation-v1",
        readiness_overall_status="pass",
        candidate_count=0,
        recommend_count=0,
        watch_count=0,
        reject_count=0,
        recommendation_rows=(),
    )
    selection_policy_report = PaperStrategySelectionPolicyReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="strategy-selection-policy-v1",
        row_count=0,
        selected_count=0,
        skipped_count=0,
        not_selected_count=0,
        total_selected_notional=ZERO,
        selection_rows=(),
    )
    explanation_report = PaperStrategyRecommendationExplanationReport(
        generated_at=SOURCE_GENERATED_AT,
        source_config_version=recommendation_report.config_version,
        recommendation_count=0,
        recommend_count=0,
        watch_count=0,
        reject_count=0,
        explanation_rows=(),
    )
    return PaperStrategyRecommendationBundleReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="strategy-recommendation-bundle-v1",
        candidate_count=0,
        recommend_count=0,
        selected_count=0,
        total_selected_notional=ZERO,
        recommendation_report=recommendation_report,
        selection_policy_report=selection_policy_report,
        explanation_report=explanation_report,
    )


def _queue_row(
    rank: int,
    market_slug: str,
    *,
    recommendation_score: Decimal = d("0.800000"),
    suggested_notional: Decimal = d("12.000000"),
    selected_side: str = "yes",
    action: str = "recommend",
    decision: str = "selected",
    queue_status: str = "ready",
    primary_reason_code: str = "selected_by_policy",
) -> PaperStrategyRecommendationQueueRow:
    return PaperStrategyRecommendationQueueRow(
        rank=rank,
        market_slug=market_slug,
        selected_side=selected_side,
        action=action,
        decision=decision,
        recommendation_score=recommendation_score,
        suggested_notional=suggested_notional,
        primary_reason_code=primary_reason_code,
        queue_status=queue_status,
    )


def _reason_counts(
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _queue_summary(
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> PaperStrategyRecommendationQueueSummaryReport:
    ready_rows = tuple(row for row in rows if row.queue_status == "ready")
    watch_count = sum(1 for row in rows if row.queue_status == "watch")
    blocked_count = sum(1 for row in rows if row.queue_status == "blocked")
    return PaperStrategyRecommendationQueueSummaryReport(
        generated_at=SOURCE_GENERATED_AT,
        source_config_version="strategy-recommendation-bundle-v1",
        queue_count=len(rows),
        ready_count=len(ready_rows),
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_ready_notional=sum((row.suggested_notional for row in ready_rows), ZERO),
        top_score=rows[0].recommendation_score if rows else ZERO,
        average_ready_score=(
            sum((row.recommendation_score for row in ready_rows), ZERO)
            / Decimal(len(ready_rows))
            if ready_rows
            else ZERO
        ),
        primary_reason_code_counts=_reason_counts(rows),
        queue_rows=rows,
    )


def _source_queue_report(
    config_version: str = "action-gated-queue-v0",
    *,
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> PaperActionGatedStrategyRecommendationQueueReport:
    queue_summary = _queue_summary(rows)
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version=config_version,
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        reason_code_counts=(),
        candidate_count=queue_summary.queue_count,
        ready_count=queue_summary.ready_count,
        watch_count=queue_summary.watch_count,
        blocked_count=queue_summary.blocked_count,
        total_ready_notional=queue_summary.total_ready_notional,
        candidate_assessment_report=_empty_candidate_assessment_report(),
        bundle_report=_empty_bundle_report(),
        queue_summary_report=queue_summary,
    )


def _priority_report(
    source_reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    return build_paper_action_gated_strategy_recommendation_queue_priority_report(
        source_reports,
        generated_at=GENERATED_AT,
    )


def _risk_config(**overrides: object) -> PaperActionGatedStrategyRecommendationQueueRiskConfig:
    values = {
        "config_version": "action-gated-queue-risk-v0",
        "max_total_ready_notional": d("100.000000"),
        "max_single_queue_ready_notional": d("100.000000"),
        "max_ready_candidate_count": 25,
        "max_total_candidate_count": 50,
        "throttle_utilization_threshold": d("1.000000"),
    }
    values.update(overrides)
    return PaperActionGatedStrategyRecommendationQueueRiskConfig(**values)


def _risk_report(
    source_reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
    *,
    config: PaperActionGatedStrategyRecommendationQueueRiskConfig | None = None,
) -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    return build_paper_action_gated_strategy_recommendation_queue_risk_report(
        source_reports,
        config=config or _risk_config(),
        generated_at=GENERATED_AT,
    )


def _gate_reason_count(
    reason_code: str,
) -> PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
    return PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
        reason_code=reason_code,
        report_count=1,
    )


def _operator_next_step(status: str) -> str:
    return {
        "pass": "allow_paper_autonomous_screening_decision_support",
        "watch": "throttle_paper_autonomous_screening_decision_support",
        "blocked": "block_paper_autonomous_screening_decision_support",
    }[status]


def _gate_next_step(status: str) -> str:
    return {
        "pass": "advance_paper_autonomous_screening_recommendations",
        "watch": "throttle_paper_autonomous_screening_recommendations",
        "blocked": "block_paper_autonomous_screening_recommendations",
    }[status]


def _gate_report(
    *,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    gate_status: str | None = None,
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    operator_flow_gate_status = "pass"
    if risk_report.status != "pass":
        status = risk_report.status
        reason_code = f"queue_risk_{risk_report.status}"
    elif gate_status is None or gate_status == "pass":
        status = "pass"
        reason_code = "paper_autonomous_screening_decision_support_gate_passed"
    else:
        status = gate_status
        operator_flow_gate_status = gate_status
        reason_code = f"operator_flow_db_history_gate_{gate_status}"

    return PaperAutonomousScreeningDecisionSupportGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-autonomous-screening-decision-support-gate-v0",
        gate_status=status,
        recommended_next_step=_gate_next_step(status),
        reason_code_counts=(_gate_reason_count(reason_code),),
        reason_codes=(reason_code,),
        operator_flow_gate_config_version=(
            "paper-research-packet-operator-flow-db-history-gate-v0"
        ),
        operator_flow_gate_generated_at=GENERATED_AT,
        operator_flow_gate_status=operator_flow_gate_status,
        operator_flow_recommended_next_step=_operator_next_step(operator_flow_gate_status),
        queue_priority_generated_at=priority_report.generated_at,
        queue_risk_generated_at=risk_report.generated_at,
        queue_risk_config_version=risk_report.config_version,
        queue_risk_status=risk_report.status,
        queue_risk_recommended_next_step=risk_report.recommended_next_step,
        queue_source_report_count=priority_report.source_report_count,
        queue_research_ready_count=priority_report.research_ready_count,
        queue_watch_count=priority_report.watch_count,
        queue_blocked_count=priority_report.blocked_count,
        queue_candidate_count=risk_report.candidate_count,
        queue_ready_count=risk_report.ready_count,
        queue_candidate_watch_count=risk_report.watch_count,
        queue_candidate_blocked_count=risk_report.blocked_count,
        queue_total_ready_notional=risk_report.total_ready_notional,
        queue_largest_ready_notional=risk_report.largest_queue_ready_notional,
        queue_top_research_priority_score=(
            priority_report.top_research_priority_score
        ),
        queue_average_research_priority_score=(
            priority_report.average_research_priority_score
        ),
        trend_source_snapshot_count=None,
        trend_latest_risk_status=None,
        trend_consecutive_latest_watch_count=None,
        trend_consecutive_latest_blocked_count=None,
        trend_duplicate_generated_at_count=None,
        rank_stability_status=None,
        rank_stable_ready_count=None,
        rank_unstable_ready_count=None,
        rank_blocked_count=None,
    )


def _ready_inputs() -> tuple[
    PaperAutonomousScreeningDecisionSupportGateReport,
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
    tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
]:
    source = _source_queue_report(
        rows=(
            _queue_row(
                1,
                "alpha-ready",
                recommendation_score=d("0.820000"),
                suggested_notional=d("12.000000"),
            ),
        ),
    )
    sources = (source,)
    priority = _priority_report(sources)
    risk = _risk_report(sources)
    return _gate_report(priority_report=priority, risk_report=risk), priority, risk, sources


def _build_report(
    *,
    screening_gate_report: PaperAutonomousScreeningDecisionSupportGateReport | None = None,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport | None = None,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport | None = None,
    source_queue_reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...]
    | None = None,
    config: PaperAutonomousAllocationProposalConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperAutonomousAllocationProposalReport:
    gate, priority, risk, sources = _ready_inputs()
    return build_paper_autonomous_allocation_proposal_report(
        screening_gate_report=screening_gate_report or gate,
        priority_report=priority_report or priority,
        risk_report=risk_report or risk,
        source_queue_reports=source_queue_reports or sources,
        config=config or _proposal_config(),
        generated_at=generated_at,
    )


def test_pass_gate_builds_allocation_proposal_from_ready_source_queue_rows():
    gate, priority, risk, sources = _ready_inputs()

    report = build_paper_autonomous_allocation_proposal_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
        config=_proposal_config(
            config_version="paper-autonomous-allocation-proposal-v0",
            allocation_config=_allocation_config(
                config_version="allocation-v0",
                total_paper_budget=d("100.000000"),
                max_paper_notional_per_market=d("50.000000"),
                max_paper_notional_per_event=d("50.000000"),
                max_paper_notional_per_theme=d("50.000000"),
                max_paper_notional_per_correlation_group=d("50.000000"),
            ),
        ),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperAutonomousAllocationProposalReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-autonomous-allocation-proposal-v0"
    assert report.proposal_status == "pass"
    assert report.recommended_next_step == "review_paper_autonomous_allocation_proposal"
    assert report.reason_codes == ("paper_autonomous_allocation_proposal_passed",)
    assert report.reason_code_counts == (
        PaperAutonomousAllocationProposalReasonCodeCount(
            reason_code="paper_autonomous_allocation_proposal_passed",
            report_count=1,
        ),
    )
    assert report.source_queue_count == 1
    assert report.allocation_input_count == 1
    assert report.source_queue_summaries == (
        PaperAutonomousAllocationProposalSourceQueueSummary(
            source_generated_at=SOURCE_GENERATED_AT,
            config_version="action-gated-queue-v0",
            source_config_version="paper-recommendation-cycle-action-gate-v0",
            action_status="research_ready",
            queue_count=1,
            ready_count=1,
            watch_count=0,
            blocked_count=0,
            total_ready_notional=d("12.000000"),
            allocation_input_count=1,
        ),
    )

    assert report.allocation_report.paper_only is True
    assert report.allocation_report.report_only is True
    assert report.allocation_report.readonly is True
    assert report.allocation_report.allocated_count == 1
    assert report.allocation_report.config_version == "allocation-v0"

    allocation_row = report.allocation_report.rows[0]
    assert allocation_row.market_slug == "alpha-ready"
    assert allocation_row.side == "yes"
    assert allocation_row.action == "recommend"
    assert allocation_row.recommendation_score == d("0.820000")
    assert allocation_row.side_price == d("1.000000")
    assert allocation_row.executable_paper_shares == d("12.000000")
    assert allocation_row.requested_paper_notional == d("12.000000")
    assert allocation_row.allocated_paper_notional == d("12.000000")
    assert allocation_row.reason_codes == ("selected_by_policy",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("gate_status", "expected_status", "expected_reason_code"),
    (
        ("watch", "watch", "screening_gate_watch"),
        ("blocked", "blocked", "screening_gate_blocked"),
    ),
)
def test_gate_watch_and_blocked_prevent_pass_status(
    gate_status: str,
    expected_status: str,
    expected_reason_code: str,
):
    _gate, priority, risk, sources = _ready_inputs()
    gate = _gate_report(
        priority_report=priority,
        risk_report=risk,
        gate_status=gate_status,
    )

    report = _build_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
    )

    assert report.proposal_status == expected_status
    assert expected_reason_code in report.reason_codes
    assert report.allocation_report.allocated_count == 1


@pytest.mark.parametrize(
    ("risk_config", "expected_status", "expected_reason_code"),
    (
        (
            _risk_config(max_total_ready_notional=d("12.000000")),
            "watch",
            "queue_risk_watch",
        ),
        (
            _risk_config(max_total_ready_notional=d("11.000000")),
            "blocked",
            "queue_risk_blocked",
        ),
    ),
)
def test_queue_risk_watch_and_blocked_take_precedence(
    risk_config: PaperActionGatedStrategyRecommendationQueueRiskConfig,
    expected_status: str,
    expected_reason_code: str,
):
    _gate, priority, _risk, sources = _ready_inputs()
    risk = _risk_report(sources, config=risk_config)
    gate = _gate_report(priority_report=priority, risk_report=risk)

    report = _build_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
    )

    assert report.proposal_status == expected_status
    assert expected_reason_code in report.reason_codes


def test_empty_source_queue_reports_are_blocked_without_allocations():
    sources: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...] = ()
    priority = _priority_report(sources)
    risk = _risk_report(sources)
    gate = _gate_report(priority_report=priority, risk_report=risk)

    report = build_paper_autonomous_allocation_proposal_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
        config=_proposal_config(),
        generated_at=GENERATED_AT,
    )

    assert report.proposal_status == "blocked"
    assert "empty_source_queue_reports" in report.reason_codes
    assert "empty_allocation_inputs" in report.reason_codes
    assert "no_allocated_or_capped_rows" in report.reason_codes
    assert report.source_queue_count == 0
    assert report.allocation_input_count == 0
    assert report.allocation_report.input_count == 0
    assert report.allocation_report.rows == ()


def test_no_ready_queue_rows_are_blocked_even_when_source_reports_exist():
    source = _source_queue_report(
        rows=(
            _queue_row(
                1,
                "alpha-watch",
                recommendation_score=d("0.650000"),
                suggested_notional=ZERO,
                action="recommend",
                decision="skipped",
                queue_status="watch",
                primary_reason_code="await_fresh_context",
            ),
        ),
    )
    sources = (source,)
    priority = _priority_report(sources)
    risk = _risk_report(sources)
    gate = _gate_report(priority_report=priority, risk_report=risk)

    report = _build_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
    )

    assert report.proposal_status == "blocked"
    assert report.source_queue_count == 1
    assert report.allocation_input_count == 0
    assert "empty_allocation_inputs" in report.reason_codes
    assert report.allocation_report.row_count == 0


def test_allocation_caps_downgrade_pass_gate_to_watch():
    gate, priority, risk, sources = _ready_inputs()

    report = _build_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
        config=_proposal_config(
            allocation_config=_allocation_config(
                total_paper_budget=d("10.000000"),
            ),
        ),
    )

    assert report.proposal_status == "watch"
    assert "allocation_capped" in report.reason_codes
    assert report.allocation_report.capped_count == 1
    assert report.allocation_report.rows[0].allocated_paper_notional == d("10.000000")


def test_ready_non_recommend_queue_row_is_preserved_as_non_recommend_allocation():
    source = _source_queue_report(
        rows=(
            _queue_row(
                1,
                "alpha-watch-action",
                recommendation_score=d("0.780000"),
                suggested_notional=d("12.000000"),
                action="watch",
            ),
        ),
    )
    sources = (source,)
    priority = _priority_report(sources)
    risk = _risk_report(sources)
    gate = _gate_report(priority_report=priority, risk_report=risk)

    report = _build_report(
        screening_gate_report=gate,
        priority_report=priority,
        risk_report=risk,
        source_queue_reports=sources,
    )

    assert report.proposal_status == "watch"
    assert "allocation_non_recommend" in report.reason_codes
    assert report.allocation_report.non_recommend_count == 1
    allocation_row = report.allocation_report.rows[0]
    assert allocation_row.action == "watch"
    assert allocation_row.cap_status == "non_recommend"
    assert allocation_row.allocated_paper_notional == d("0.000000")


def test_reducer_rejects_source_queue_reports_with_mismatched_score_fields():
    original_source = _source_queue_report(
        rows=(
            _queue_row(
                1,
                "alpha-ready",
                recommendation_score=d("0.820000"),
                suggested_notional=d("12.000000"),
            ),
        ),
    )
    replacement_source = _source_queue_report(
        rows=(
            _queue_row(
                1,
                "alpha-ready",
                recommendation_score=d("0.520000"),
                suggested_notional=d("12.000000"),
            ),
        ),
    )
    priority = _priority_report((original_source,))
    risk = _risk_report((original_source,))
    gate = _gate_report(priority_report=priority, risk_report=risk)

    with pytest.raises(ValueError, match="source_queue_reports"):
        _build_report(
            screening_gate_report=gate,
            priority_report=priority,
            risk_report=risk,
            source_queue_reports=(replacement_source,),
        )


def test_reducer_rejects_priority_risk_source_mismatch_and_unsafe_inputs():
    gate, priority, risk, sources = _ready_inputs()
    mismatched_source = _source_queue_report(
        "action-gated-queue-other",
        rows=(
            _queue_row(
                1,
                "alpha-ready",
                recommendation_score=d("0.820000"),
                suggested_notional=d("12.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="source_queue_reports"):
        _build_report(
            screening_gate_report=gate,
            priority_report=priority,
            risk_report=risk,
            source_queue_reports=(mismatched_source,),
        )
    with pytest.raises(ValueError, match="PaperAutonomousScreeningDecisionSupportGateReport"):
        _build_report(screening_gate_report=object())
    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalConfig"):
        _build_report(
            config=ProposalConfigSubclass(
                config_version="paper-autonomous-allocation-proposal-v0",
                allocation_config=_allocation_config(),
            ),
        )
    with pytest.raises(ValueError, match="PaperActionGatedStrategyRecommendationQueueReport"):
        _build_report(
            source_queue_reports=(
                SourceQueueReportSubclass(**sources[0].__dict__),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(generated_at="2026-06-23")  # type: ignore[arg-type]

    unsafe_source = _source_queue_report(
        rows=(
            _queue_row(
                1,
                "unsafe-source",
                recommendation_score=d("0.700000"),
                suggested_notional=d("5.000000"),
            ),
        ),
    )
    object.__setattr__(unsafe_source, "readonly", False)
    with pytest.raises(ValueError, match="source_queue_reports.*readonly"):
        _build_report(source_queue_reports=(unsafe_source,))


def test_config_report_and_reason_code_counts_are_frozen_and_consistent():
    report = _build_report()
    config = _proposal_config()

    assert type(report.allocation_report.total_allocated_paper_notional) is Decimal
    assert report.allocation_report.total_allocated_paper_notional == d("12.000000")

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.proposal_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.source_queue_summaries = ()  # type: ignore[misc]

    with pytest.raises(ValueError, match="allocation_config"):
        replace(config, allocation_config=object())
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="proposal_status"):
        replace(report, proposal_status="watch")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="source_queue_count"):
        replace(report, source_queue_count=99)
    with pytest.raises(ValueError, match="allocation_input_count"):
        replace(report, allocation_input_count=99)

    with pytest.raises(ValueError, match="total_ready_notional"):
        PaperAutonomousAllocationProposalSourceQueueSummary(
            source_generated_at=SOURCE_GENERATED_AT,
            config_version="action-gated-queue-v0",
            source_config_version="paper-recommendation-cycle-action-gate-v0",
            action_status="research_ready",
            queue_count=1,
            ready_count=1,
            watch_count=0,
            blocked_count=0,
            total_ready_notional=12.0,  # type: ignore[arg-type]
            allocation_input_count=1,
        )
    with pytest.raises(ValueError, match="report_count"):
        PaperAutonomousAllocationProposalReasonCodeCount(
            reason_code="paper_autonomous_allocation_proposal_passed",
            report_count=0,
        )
