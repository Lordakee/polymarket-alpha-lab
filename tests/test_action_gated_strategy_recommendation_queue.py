from dataclasses import FrozenInstanceError, dataclass, replace
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
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)


@dataclass(frozen=True)
class FakeActionGateReport:
    generated_at: datetime = GENERATED_AT
    config_version: str = "paper-recommendation-cycle-action-gate-v0"
    source_config_version: str = "paper-recommendation-cycle-review-v0"
    review_status: str = "pass"
    latest_final_status: str | None = "pass"
    action_status: str = "research_ready"
    recommended_next_step: str = "build_candidate_research_queue"
    missing_required_artifact_count: int = 0
    blocked_reason_count: int = 0
    watch_reason_count: int = 0
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class ActionGateReportSubclass(PaperRecommendationCycleActionGateReport):
    pass


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


def _screening_config(**overrides):
    values = {
        "config_version": "project-screening-v1",
        "min_screening_score": Decimal("0.010000"),
        "reference_ask_size": Decimal("100.0000"),
        "net_edge_weight": Decimal("1.0000"),
        "confidence_weight": Decimal("0.0000"),
        "depth_weight": Decimal("0.0000"),
        "spread_penalty_weight": Decimal("0.0000"),
        "resolution_risk_penalty_weight": Decimal("0.0000"),
        "cost_penalty_weight": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperProjectScreeningConfig(**values)


def _screening_report(cost_reports):
    return build_paper_project_screening_report(
        cost_reports,
        config=_screening_config(),
        generated_at=SOURCE_GENERATED_AT,
    )


def _config() -> PaperActionGatedStrategyRecommendationQueueConfig:
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


def _build_report(
    action_gate_report,
    screening_report,
    cost_reports,
    *,
    config=None,
    generated_at=GENERATED_AT,
):
    return build_paper_action_gated_strategy_recommendation_queue_report(
        action_gate_report,
        screening_report,
        cost_reports,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_ready_gate_builds_candidate_bundle_and_queue_summary():
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
    screening = _screening_report((ready, watch, blocked))
    gate = _action_gate_report()

    report = _build_report(gate, screening, (ready, watch, blocked))

    assert isinstance(report, PaperActionGatedStrategyRecommendationQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert report.source_config_version == "paper-recommendation-cycle-action-gate-v0"
    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "review_candidate_research_queue"
    assert report.reason_code_counts == gate.reason_code_counts
    assert report.candidate_assessment_report is not None
    assert report.bundle_report is not None
    assert report.queue_summary_report is not None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    queue = report.queue_summary_report
    assert report.candidate_count == queue.queue_count == 3
    assert report.ready_count == queue.ready_count == 1
    assert report.watch_count == queue.watch_count == 1
    assert report.blocked_count == queue.blocked_count == 1
    assert report.total_ready_notional == queue.total_ready_notional
    assert type(report.total_ready_notional) is Decimal

    assert report.candidate_assessment_report.candidate_count == 3
    assert report.bundle_report.candidate_count == 3
    assert tuple(row.queue_status for row in queue.queue_rows) == (
        "ready",
        "watch",
        "blocked",
    )


def test_watch_gate_returns_report_only_empty_queue_and_copies_gate_reasons():
    gate = _action_gate_report(
        review_status="watch",
        latest_final_status="watch",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        watch_reason_count=2,
        reason_code_counts=(
            _reason_count("cycle_history_stale", 1),
            _reason_count("cycle_review_watch", 1),
        ),
    )
    cost_report = _cost_report()

    report = _build_report(gate, _screening_report((cost_report,)), (cost_report,))

    assert report.action_status == "watch"
    assert report.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert report.recommended_next_step == "await_fresh_cycle_evidence"
    assert report.reason_code_counts == gate.reason_code_counts
    assert report.candidate_count == 0
    assert report.ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_ready_notional == Decimal("0.000000")
    assert report.candidate_assessment_report is None
    assert report.bundle_report is None
    assert report.queue_summary_report is None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_non_ready_gate_returns_before_validating_downstream_inputs():
    gate = _action_gate_report(
        review_status="watch",
        latest_final_status="watch",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        watch_reason_count=1,
        reason_code_counts=(_reason_count("cycle_review_watch", 1),),
    )

    report = _build_report(
        gate,
        object(),
        object(),
    )

    assert report.action_status == "watch"
    assert report.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert report.recommended_next_step == "await_fresh_cycle_evidence"
    assert report.candidate_assessment_report is None
    assert report.bundle_report is None
    assert report.queue_summary_report is None
    assert report.candidate_count == 0


def test_blocked_gate_returns_report_only_empty_queue_and_copies_gate_reasons():
    gate = _action_gate_report(
        review_status="blocked",
        latest_final_status="blocked",
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
        blocked_reason_count=2,
        reason_code_counts=(
            _reason_count("cycle_review_blocked", 1),
            _reason_count("pipeline_final_status_blocked", 1),
        ),
    )
    cost_report = _cost_report()

    report = _build_report(gate, _screening_report((cost_report,)), (cost_report,))

    assert report.action_status == "blocked"
    assert report.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert report.recommended_next_step == "repair_cycle_evidence"
    assert report.reason_code_counts == gate.reason_code_counts
    assert report.candidate_count == 0
    assert report.ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_ready_notional == Decimal("0.000000")
    assert report.candidate_assessment_report is None
    assert report.bundle_report is None
    assert report.queue_summary_report is None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reducer_rejects_wrong_public_types_subclasses_and_hard_flag_breaks():
    cost_report = _cost_report()
    screening = _screening_report((cost_report,))
    gate = _action_gate_report()

    with pytest.raises(ValueError, match="PaperRecommendationCycleActionGateReport"):
        _build_report(FakeActionGateReport(), screening, (cost_report,))
    with pytest.raises(ValueError, match="PaperRecommendationCycleActionGateReport"):
        _build_report(ActionGateReportSubclass(**gate.__dict__), screening, (cost_report,))
    with pytest.raises(ValueError, match="PaperProjectScreeningReport"):
        _build_report(gate, object(), (cost_report,))
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueConfig",
    ):
        _build_report(gate, screening, (cost_report,), config=object())
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(gate, screening, (cost_report,), generated_at="2026-06-20")

    object.__setattr__(gate, "readonly", False)
    with pytest.raises(ValueError, match="action_gate_report must be readonly"):
        _build_report(gate, screening, (cost_report,))

    gate = _action_gate_report()
    object.__setattr__(screening, "paper_only", False)
    with pytest.raises(ValueError, match="screening_report must be paper_only"):
        _build_report(gate, screening, (cost_report,))

    screening = _screening_report((cost_report,))
    object.__setattr__(screening, "readonly", False)
    with pytest.raises(ValueError, match="screening_report must be readonly"):
        _build_report(gate, screening, (cost_report,))


def test_config_and_report_are_frozen_and_validate_invariants():
    cost_report = _cost_report()
    report = _build_report(
        _action_gate_report(),
        _screening_report((cost_report,)),
        (cost_report,),
    )

    with pytest.raises(FrozenInstanceError):
        report.ready_count = 99
    with pytest.raises(FrozenInstanceError):
        _config().config_version = "other"
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=999)
    with pytest.raises(ValueError, match="config_version"):
        replace(report, config_version="")
    with pytest.raises(ValueError, match="total_ready_notional"):
        replace(report, total_ready_notional=Decimal("0.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="candidate_assessment_config"):
        replace(_config(), candidate_assessment_config=object())
    with pytest.raises(ValueError, match="readiness_config_version"):
        replace(_config(), readiness_config_version="")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
