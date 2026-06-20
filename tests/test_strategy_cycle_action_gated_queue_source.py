from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueConfig,
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.candidate_assessment import PaperCandidateAssessmentConfig
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventStrategyConfig,
    build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateConfig,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
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
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)


class ReviewConfigSubclass(PaperRecommendationCycleReviewConfig):
    pass


class ActionGateConfigSubclass(PaperRecommendationCycleActionGateConfig):
    pass


class QueueConfigSubclass(PaperActionGatedStrategyRecommendationQueueConfig):
    pass


def _build_source_report(cycle_report, **kwargs):
    from polymarket_alpha_lab.strategy_cycle_action_gated_queue_source import (
        build_strategy_cycle_action_gated_queue_source_report,
    )

    return build_strategy_cycle_action_gated_queue_source_report(
        cycle_report,
        **kwargs,
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


def _queue_config(
    *,
    config_version: str = "action-gated-strategy-recommendation-queue-v0",
) -> PaperActionGatedStrategyRecommendationQueueConfig:
    return PaperActionGatedStrategyRecommendationQueueConfig(
        config_version=config_version,
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


def _cycle_report(
    *,
    scan_market_count: int,
    considered_count: int,
    snapshot_ready_count: int,
    cost_aware_report_count: int,
    blocked_counts: tuple[tuple[str, int], ...],
    screening_report,
    cost_aware_reports=(),
) -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=GENERATED_AT,
        config_version="strategy-cycle-v0",
        scan_market_count=scan_market_count,
        considered_count=considered_count,
        snapshot_ready_count=snapshot_ready_count,
        cost_aware_report_count=cost_aware_report_count,
        blocked_counts=blocked_counts,
        screening_report=screening_report,
        cost_aware_reports=cost_aware_reports,
    )


def _ready_cycle_report() -> PaperStrategyCycleReport:
    cost_report = _cost_report()
    return _cycle_report(
        scan_market_count=3,
        considered_count=1,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(),
        screening_report=_screening_report((cost_report,)),
        cost_aware_reports=(cost_report,),
    )


def _blocked_cycle_report() -> PaperStrategyCycleReport:
    return _cycle_report(
        scan_market_count=4,
        considered_count=3,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(
            ("blocked_fetch_error", 2),
            ("blocked_non_binary_market", 1),
        ),
        screening_report=None,
    )


def _watch_cycle_report() -> PaperStrategyCycleReport:
    return _cycle_report(
        scan_market_count=0,
        considered_count=0,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(),
        screening_report=None,
    )


def _reason_counts(report):
    return {item.reason_code: item.count for item in report.reason_code_counts}


def test_source_rejects_wrong_cycle_report_type():
    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        _build_source_report(object())


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only"))
def test_source_rejects_false_cycle_report_safety_flags(flag_name):
    cycle_report = _blocked_cycle_report()
    object.__setattr__(cycle_report, flag_name, False)

    with pytest.raises(ValueError, match=f"cycle_report must be {flag_name}"):
        _build_source_report(cycle_report)


@pytest.mark.parametrize(
    ("cycle_report", "expected_action_status", "expected_next_step"),
    (
        (
            _blocked_cycle_report(),
            "blocked",
            "repair_cycle_evidence",
        ),
        (
            _watch_cycle_report(),
            "watch",
            "await_fresh_cycle_evidence",
        ),
    ),
)
def test_blocked_or_watch_cycle_produces_empty_action_gated_queue_report(
    cycle_report,
    expected_action_status,
    expected_next_step,
):
    report = _build_source_report(cycle_report)

    assert isinstance(report, PaperActionGatedStrategyRecommendationQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert report.source_config_version == "paper-recommendation-cycle-action-gate-v0"
    assert report.action_status == expected_action_status
    assert report.recommended_next_step == expected_next_step
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
    assert _reason_counts(report)[f"cycle_review_{expected_action_status}"] == 1


def test_ready_cycle_with_screening_and_cost_reports_builds_ready_queue_report():
    report = _build_source_report(_ready_cycle_report())

    assert isinstance(report, PaperActionGatedStrategyRecommendationQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert report.source_config_version == "paper-recommendation-cycle-action-gate-v0"
    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "review_candidate_research_queue"
    assert report.candidate_count == 1
    assert report.ready_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.candidate_assessment_report is not None
    assert report.bundle_report is not None
    assert report.queue_summary_report is not None
    assert report.total_ready_notional == report.queue_summary_report.total_ready_notional
    assert report.total_ready_notional > Decimal("0")
    assert report.candidate_assessment_report.config_version == "candidate-assessment-v1"
    assert report.bundle_report.config_version == "strategy-recommendation-bundle-v1"
    assert report.queue_summary_report.queue_count == 1
    assert _reason_counts(report)["cycle_review_pass"] == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_source_accepts_exact_custom_config_dataclasses_and_propagates_versions():
    report = _build_source_report(
        _ready_cycle_report(),
        review_config=PaperRecommendationCycleReviewConfig(
            config_version="custom-cycle-review-v1",
            stale_after_hours=Decimal("24"),
        ),
        action_gate_config=PaperRecommendationCycleActionGateConfig(
            config_version="custom-cycle-action-gate-v1",
        ),
        queue_config=_queue_config(config_version="custom-action-gated-queue-v1"),
    )

    assert report.config_version == "custom-action-gated-queue-v1"
    assert report.source_config_version == "custom-cycle-action-gate-v1"
    assert report.action_status == "research_ready"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        (
            {
                "review_config": ReviewConfigSubclass(
                    config_version="custom-cycle-review-v1",
                    stale_after_hours=Decimal("24"),
                ),
            },
            "PaperRecommendationCycleReviewConfig",
        ),
        (
            {
                "action_gate_config": ActionGateConfigSubclass(
                    config_version="custom-cycle-action-gate-v1",
                ),
            },
            "PaperRecommendationCycleActionGateConfig",
        ),
        (
            {
                "queue_config": QueueConfigSubclass(
                    config_version="custom-action-gated-queue-v1",
                    candidate_assessment_config=PaperCandidateAssessmentConfig(
                        config_version="candidate-assessment-v1",
                    ),
                    readiness_config_version="strategy-readiness-state-v1",
                    bundle_config=PaperStrategyRecommendationBundleConfig(
                        config_version="strategy-recommendation-bundle-v1",
                        recommendation_config=PaperStrategyCandidateRecommendationConfig(
                            config_version="strategy-candidate-recommendation-v1",
                        ),
                        selection_policy_config=PaperStrategySelectionPolicyConfig(
                            config_version="strategy-selection-policy-v1",
                            base_position_notional=Decimal("20.000000"),
                            max_position_notional=Decimal("12.000000"),
                            max_total_notional=Decimal("20.000000"),
                        ),
                    ),
                ),
            },
            "PaperActionGatedStrategyRecommendationQueueConfig",
        ),
    ),
)
def test_optional_configs_must_be_exact_expected_dataclass_types(kwargs, match):
    with pytest.raises(ValueError, match=match):
        _build_source_report(_ready_cycle_report(), **kwargs)
