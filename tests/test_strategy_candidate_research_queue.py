from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueConfig,
    PaperActionGatedStrategyRecommendationQueueReport,
    build_paper_action_gated_strategy_recommendation_queue_report,
)
from polymarket_alpha_lab.candidate_assessment import PaperCandidateAssessmentConfig
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventStrategyConfig,
    build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
    PaperRecommendationCycleActionGateReport,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningConfig,
    build_paper_project_screening_report,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueConfig,
    PaperStrategyCandidateResearchQueueReport,
    build_paper_strategy_candidate_research_queue_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
RESEARCH_GENERATED_AT = datetime(2026, 6, 20, 12, 30, tzinfo=UTC)


def _reason_count(reason_code: str, count: int):
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _action_gate_report(
    *,
    review_status: str = "pass",
    latest_final_status: str | None = "pass",
    action_status: str = "research_ready",
    recommended_next_step: str = "build_candidate_research_queue",
    missing_required_artifact_count: int = 0,
    blocked_reason_count: int = 0,
    watch_reason_count: int = 0,
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]
    | None = None,
) -> PaperRecommendationCycleActionGateReport:
    if reason_code_counts is None:
        reason_code_counts = (_reason_count(f"cycle_review_{review_status}", 1),)
    return PaperRecommendationCycleActionGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-cycle-action-gate-v0",
        source_config_version="paper-recommendation-cycle-review-v0",
        review_status=review_status,
        latest_final_status=latest_final_status,
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        missing_required_artifact_count=missing_required_artifact_count,
        blocked_reason_count=blocked_reason_count,
        watch_reason_count=watch_reason_count,
        reason_code_counts=reason_code_counts,
    )


def _cost_assumptions(**overrides):
    values = {
        "taker_fee_rate": Decimal("0.0000"),
        "slippage_cost_per_share": Decimal("0.0000"),
        "funding_cost_per_share": Decimal("0.0000"),
        "finalization_cost_per_share": Decimal("0.0000"),
        "time_cost_per_share": Decimal("0.0000"),
        "risk_cost_per_share": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperCostAwareEventCostAssumptions(**values)


def _cost_aware_config(**overrides):
    values = {
        "config_version": "cost-aware-event-v1",
        "min_confidence": Decimal("0.7000"),
        "max_spread": Decimal("0.0500"),
        "max_resolution_risk": Decimal("0.2000"),
        "min_ask_size": Decimal("10.0000"),
        "min_net_edge": Decimal("0.0100"),
    }
    values.update(overrides)
    return PaperCostAwareEventStrategyConfig(**values)


def _cost_report(**overrides):
    values = {
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.6300"),
        "confidence": Decimal("0.9000"),
        "yes_bid": Decimal("0.5400"),
        "yes_ask": Decimal("0.5500"),
        "yes_ask_size": Decimal("250.0000"),
        "no_bid": Decimal("0.4400"),
        "no_ask": Decimal("0.5000"),
        "no_ask_size": Decimal("200.0000"),
        "spread": Decimal("0.0100"),
        "resolution_risk": Decimal("0.0200"),
        "risk_cost_per_share": Decimal("0.0000"),
        "min_net_edge": Decimal("0.0100"),
        "generated_at": SOURCE_GENERATED_AT,
    }
    values.update(overrides)
    snapshot = PaperCostAwareEventMarketSnapshot(
        market_slug=values["market_slug"],
        question=values["question"],
        fair_probability_yes=values["fair_probability_yes"],
        confidence=values["confidence"],
        yes_bid=values["yes_bid"],
        yes_ask=values["yes_ask"],
        yes_ask_size=values["yes_ask_size"],
        no_bid=values["no_bid"],
        no_ask=values["no_ask"],
        no_ask_size=values["no_ask_size"],
        spread=values["spread"],
        resolution_risk=values["resolution_risk"],
    )
    return build_paper_cost_aware_event_strategy_report(
        snapshot,
        cost_assumptions=_cost_assumptions(
            risk_cost_per_share=values["risk_cost_per_share"],
        ),
        config=_cost_aware_config(min_net_edge=values["min_net_edge"]),
        generated_at=values["generated_at"],
    )


def _screening_config() -> PaperProjectScreeningConfig:
    return PaperProjectScreeningConfig(
        config_version="project-screening-v1",
        min_screening_score=Decimal("0.010000"),
        reference_ask_size=Decimal("100.0000"),
        net_edge_weight=Decimal("1.0000"),
        confidence_weight=Decimal("0.0000"),
        depth_weight=Decimal("0.0000"),
        spread_penalty_weight=Decimal("0.0000"),
        resolution_risk_penalty_weight=Decimal("0.0000"),
        cost_penalty_weight=Decimal("0.0000"),
    )


def _screening_report(cost_reports):
    return build_paper_project_screening_report(
        cost_reports,
        config=_screening_config(),
        generated_at=SOURCE_GENERATED_AT,
    )


def _action_gated_config() -> PaperActionGatedStrategyRecommendationQueueConfig:
    return PaperActionGatedStrategyRecommendationQueueConfig(
        config_version="action-gated-strategy-recommendation-queue-v0",
        candidate_assessment_config=PaperCandidateAssessmentConfig(
            config_version="candidate-assessment-v1",
            min_ready_score=Decimal("0.010000"),
            max_total_cost_per_share=Decimal("0.050000"),
        ),
        readiness_config_version="strategy-readiness-state-v1",
        bundle_config=PaperStrategyRecommendationBundleConfig(
            config_version="strategy-recommendation-bundle-v1",
            recommendation_config=PaperStrategyCandidateRecommendationConfig(
                config_version="strategy-candidate-recommendation-v1",
                min_recommendation_score=Decimal("0.100000"),
            ),
            selection_policy_config=PaperStrategySelectionPolicyConfig(
                config_version="strategy-selection-policy-v1",
                base_position_notional=Decimal("20.000000"),
                max_position_notional=Decimal("12.000000"),
                max_total_notional=Decimal("20.000000"),
            ),
        ),
    )


def _build_action_gated_report(
    action_gate_report,
    screening_report,
    cost_reports,
):
    return build_paper_action_gated_strategy_recommendation_queue_report(
        action_gate_report,
        screening_report,
        cost_reports,
        config=_action_gated_config(),
        generated_at=GENERATED_AT,
    )


def _research_config() -> PaperStrategyCandidateResearchQueueConfig:
    return PaperStrategyCandidateResearchQueueConfig(
        config_version="strategy-candidate-research-queue-v0",
    )


def _ready_source_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    ready = _cost_report(
        market_slug="alpha-ready",
        question="Will alpha resolve yes?",
        fair_probability_yes=Decimal("0.6300"),
        yes_ask=Decimal("0.5500"),
    )
    watch = _cost_report(
        market_slug="beta-watch",
        question="Will beta resolve yes?",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        min_net_edge=Decimal("0.0200"),
    )
    blocked = _cost_report(
        market_slug="gamma-blocked",
        question="Will gamma resolve yes?",
        fair_probability_yes=Decimal("0.6800"),
        yes_ask=Decimal("0.5500"),
        risk_cost_per_share=Decimal("0.0600"),
    )
    cost_reports = (ready, watch, blocked)
    return _build_action_gated_report(
        _action_gate_report(),
        _screening_report(cost_reports),
        cost_reports,
    )


def test_non_ready_source_emits_empty_research_queue_without_downstream_inputs():
    source = PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=GENERATED_AT,
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(_reason_count("cycle_review_watch", 1),),
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("0.000000"),
    )

    report = build_paper_strategy_candidate_research_queue_report(
        source,
        config=_research_config(),
        generated_at=RESEARCH_GENERATED_AT,
    )

    assert isinstance(report, PaperStrategyCandidateResearchQueueReport)
    assert report.generated_at == RESEARCH_GENERATED_AT
    assert report.config_version == "strategy-candidate-research-queue-v0"
    assert report.source_config_version == source.config_version
    assert report.action_status == "watch"
    assert report.recommended_next_step == "await_fresh_cycle_evidence"
    assert report.research_status == "watch"
    assert report.candidate_count == 0
    assert report.research_ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_ready_notional == Decimal("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("source_action_status_watch",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_ready_source_joins_nested_reports_into_ranked_research_rows():
    source = _ready_source_report()
    queue = source.queue_summary_report
    assessment = source.candidate_assessment_report
    assert queue is not None
    assert assessment is not None

    report = build_paper_strategy_candidate_research_queue_report(
        source,
        config=_research_config(),
        generated_at=RESEARCH_GENERATED_AT,
    )

    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "review_candidate_research_queue"
    assert report.research_status == "ready"
    assert report.candidate_count == source.candidate_count == 3
    assert report.research_ready_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.total_ready_notional == source.total_ready_notional
    assert report.reason_codes == ("candidate_research_queue_ready",)

    assert tuple(row.market_slug for row in report.rows) == tuple(
        row.market_slug for row in queue.queue_rows
    )
    assert tuple(row.research_rank for row in report.rows) == (1, 2, 3)
    assert tuple(row.queue_rank for row in report.rows) == (1, 2, 3)
    assert tuple(row.research_status for row in report.rows) == (
        "ready",
        "watch",
        "blocked",
    )

    ready_row = report.rows[0]
    source_queue_row = queue.queue_rows[0]
    source_assessment_row = next(
        row
        for row in assessment.assessment_rows
        if row.market_slug == ready_row.market_slug
    )
    assert ready_row.question == source_assessment_row.question
    assert ready_row.selected_side == source_queue_row.selected_side
    assert ready_row.source_action == source_queue_row.action
    assert ready_row.decision == source_queue_row.decision
    assert ready_row.queue_status == source_queue_row.queue_status
    assert ready_row.recommendation_score == source_queue_row.recommendation_score
    assert ready_row.readiness_score == source_assessment_row.readiness_score
    assert ready_row.screening_score == source_assessment_row.screening_score
    assert ready_row.net_edge_per_share == source_assessment_row.net_edge_per_share
    assert ready_row.suggested_notional == source_queue_row.suggested_notional
    assert ready_row.primary_reason_code == source_queue_row.primary_reason_code
    assert ready_row.research_priority_score == (
        (
            source_queue_row.recommendation_score
            + source_assessment_row.readiness_score
        )
        / Decimal("2")
    ).quantize(Decimal("0.000001"))
    assert ready_row.evidence_gap_codes == ()
    assert ready_row.explanation.startswith("recommend yes because")
    assert ready_row.paper_only is True
    assert ready_row.report_only is True
    assert ready_row.readonly is True

    blocked_row = report.rows[2]
    assert blocked_row.market_slug == "gamma-blocked"
    assert "high_cost" in blocked_row.evidence_gap_codes
    assert "high_cost" in blocked_row.reason_codes


def test_ready_source_requires_nested_reports_and_safe_hard_flags():
    source = _ready_source_report()

    object.__setattr__(source, "queue_summary_report", None)
    with pytest.raises(ValueError, match="queue_summary_report"):
        build_paper_strategy_candidate_research_queue_report(
            source,
            config=_research_config(),
            generated_at=RESEARCH_GENERATED_AT,
        )

    source = _ready_source_report()
    assert source.bundle_report is not None
    object.__setattr__(source.bundle_report, "readonly", False)
    with pytest.raises(ValueError, match="bundle_report must be readonly"):
        build_paper_strategy_candidate_research_queue_report(
            source,
            config=_research_config(),
            generated_at=RESEARCH_GENERATED_AT,
        )


def test_research_queue_dataclasses_are_frozen_and_validate_counts():
    source = _ready_source_report()
    report = build_paper_strategy_candidate_research_queue_report(
        source,
        config=_research_config(),
        generated_at=RESEARCH_GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.candidate_count = 0
    with pytest.raises(FrozenInstanceError):
        report.rows[0].research_rank = 99
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=999)
    with pytest.raises(ValueError, match="research_ready_count"):
        replace(report, research_ready_count=999)
    with pytest.raises(ValueError, match="research_rank"):
        replace(report.rows[0], research_rank=0)
    with pytest.raises(ValueError, match="research_status"):
        replace(report.rows[0], research_status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="config_version"):
        replace(_research_config(), config_version="")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_research_config(), paper_only=False)
