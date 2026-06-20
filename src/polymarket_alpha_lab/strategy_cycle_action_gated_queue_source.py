"""Pure action-gated queue source for strategy-cycle reports."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueConfig,
    PaperActionGatedStrategyRecommendationQueueReport,
    build_paper_action_gated_strategy_recommendation_queue_report,
)
from polymarket_alpha_lab.candidate_assessment import PaperCandidateAssessmentConfig
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateConfig,
    build_paper_recommendation_cycle_action_gate_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
    build_paper_recommendation_cycle_review_report,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
)
from polymarket_alpha_lab.strategy_cycle_snapshot_source import (
    build_strategy_cycle_snapshot_source_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
)


def build_strategy_cycle_action_gated_queue_source_report(
    cycle_report: object,
    iteration_started_at: datetime | None = None,
    *,
    review_config: PaperRecommendationCycleReviewConfig | None = None,
    action_gate_config: PaperRecommendationCycleActionGateConfig | None = None,
    queue_config: PaperActionGatedStrategyRecommendationQueueConfig | None = None,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    resolved_review_config = _review_config(review_config)
    resolved_action_gate_config = _action_gate_config(action_gate_config)
    resolved_queue_config = _queue_config(queue_config)

    snapshot_report = build_strategy_cycle_snapshot_source_report(
        cycle_report,
        iteration_started_at,
    )
    generated_at = snapshot_report.generated_at
    review_report = build_paper_recommendation_cycle_review_report(
        (snapshot_report,),
        config=resolved_review_config,
        generated_at=generated_at,
    )
    action_gate_report = build_paper_recommendation_cycle_action_gate_report(
        review_report,
        config=resolved_action_gate_config,
        generated_at=generated_at,
    )
    return build_paper_action_gated_strategy_recommendation_queue_report(
        action_gate_report,
        getattr(cycle_report, "screening_report"),
        getattr(cycle_report, "cost_aware_reports"),
        config=resolved_queue_config,
        generated_at=generated_at,
    )


def _review_config(
    value: PaperRecommendationCycleReviewConfig | None,
) -> PaperRecommendationCycleReviewConfig:
    if value is None:
        return PaperRecommendationCycleReviewConfig(
            config_version="paper-recommendation-cycle-review-v0",
            stale_after_hours=Decimal("24"),
        )
    if type(value) is not PaperRecommendationCycleReviewConfig:
        raise ValueError("review_config must be a PaperRecommendationCycleReviewConfig")
    return value


def _action_gate_config(
    value: PaperRecommendationCycleActionGateConfig | None,
) -> PaperRecommendationCycleActionGateConfig:
    if value is None:
        return PaperRecommendationCycleActionGateConfig(
            config_version="paper-recommendation-cycle-action-gate-v0",
        )
    if type(value) is not PaperRecommendationCycleActionGateConfig:
        raise ValueError(
            "action_gate_config must be a PaperRecommendationCycleActionGateConfig",
        )
    return value


def _queue_config(
    value: PaperActionGatedStrategyRecommendationQueueConfig | None,
) -> PaperActionGatedStrategyRecommendationQueueConfig:
    if value is None:
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
    if type(value) is not PaperActionGatedStrategyRecommendationQueueConfig:
        raise ValueError(
            "queue_config must be a "
            "PaperActionGatedStrategyRecommendationQueueConfig",
        )
    return value


__all__ = ("build_strategy_cycle_action_gated_queue_source_report",)
