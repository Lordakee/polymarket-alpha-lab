import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab import (
    action_gated_strategy_recommendation_queue_risk as risk_module,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueConfig,
    PaperActionGatedStrategyRecommendationQueueReport,
    build_paper_action_gated_strategy_recommendation_queue_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskConfig,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
    build_paper_action_gated_strategy_recommendation_queue_risk_report,
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


class QueueReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def _reason_count(
    reason_code: str,
    count: int,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
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


def _cost_assumptions(**overrides) -> PaperCostAwareEventCostAssumptions:
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


def _cost_aware_config(**overrides) -> PaperCostAwareEventStrategyConfig:
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


def _screening_config(**overrides) -> PaperProjectScreeningConfig:
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


def _queue_report(
    cost_reports,
    *,
    action_gate_report: PaperRecommendationCycleActionGateReport | None = None,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    return build_paper_action_gated_strategy_recommendation_queue_report(
        action_gate_report or _action_gate_report(),
        _screening_report(cost_reports),
        cost_reports,
        config=_action_gated_config(),
        generated_at=GENERATED_AT,
    )


def _risk_config(
    **overrides,
) -> PaperActionGatedStrategyRecommendationQueueRiskConfig:
    values = {
        "config_version": "action-gated-queue-risk-v0",
        "max_total_ready_notional": Decimal("30.000000"),
        "max_single_queue_ready_notional": Decimal("20.000000"),
        "max_ready_candidate_count": 5,
        "max_total_candidate_count": 10,
        "throttle_utilization_threshold": Decimal("0.950000"),
    }
    values.update(overrides)
    return PaperActionGatedStrategyRecommendationQueueRiskConfig(**values)


def _build_risk_report(
    queue_reports,
    *,
    config: PaperActionGatedStrategyRecommendationQueueRiskConfig | None = None,
    generated_at=GENERATED_AT,
) -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    return build_paper_action_gated_strategy_recommendation_queue_risk_report(
        queue_reports,
        config=config or _risk_config(),
        generated_at=generated_at,
    )


def test_pass_status_summarizes_ready_notional_counts_and_utilization():
    ready_queue = _queue_report((_cost_report(),))

    report = _build_risk_report((ready_queue,))

    assert isinstance(report, PaperActionGatedStrategyRecommendationQueueRiskReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "action-gated-queue-risk-v0"
    assert report.source_config_versions == (
        "action-gated-strategy-recommendation-queue-v0",
    )
    assert report.status == "pass"
    assert report.recommended_next_step == "allocate_paper_research_queue"
    assert report.reason_codes == ("queue_risk_passed",)
    assert report.source_queue_count == 1
    assert report.research_ready_source_count == 1
    assert report.watch_source_count == 0
    assert report.blocked_source_count == 0
    assert report.candidate_count == 1
    assert report.ready_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.blocked_reason_count == 0
    assert report.watch_reason_count == 0
    assert report.total_ready_notional == Decimal("4.400000")
    assert report.largest_queue_ready_notional == Decimal("4.400000")
    assert report.total_ready_notional_utilization == Decimal("0.146667")
    assert report.largest_queue_ready_notional_utilization == Decimal("0.220000")
    assert report.max_total_ready_notional == Decimal("30.000000")
    assert report.max_single_queue_ready_notional == Decimal("20.000000")
    assert report.max_ready_candidate_count == 5
    assert report.max_total_candidate_count == 10
    assert report.throttle_utilization_threshold == Decimal("0.950000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_watch_status_recommends_throttle_when_ready_notional_nears_cap():
    ready_queue = _queue_report((_cost_report(),))

    report = _build_risk_report(
        (ready_queue,),
        config=_risk_config(
            max_total_ready_notional=Decimal("5.500000"),
            throttle_utilization_threshold=Decimal("0.800000"),
        ),
    )

    assert report.status == "watch"
    assert report.recommended_next_step == "throttle_paper_research_queue"
    assert report.reason_codes == ("near_total_ready_notional_cap",)
    assert report.blocked_reason_count == 0
    assert report.watch_reason_count == 1
    assert report.total_ready_notional_utilization == Decimal("0.800000")


def test_blocked_status_when_ready_notional_cap_is_exceeded():
    ready_queue = _queue_report((_cost_report(),))

    report = _build_risk_report(
        (ready_queue,),
        config=_risk_config(max_total_ready_notional=Decimal("4.000000")),
    )

    assert report.status == "blocked"
    assert report.recommended_next_step == "block_paper_research_queue"
    assert report.reason_codes == ("total_ready_notional_cap_exceeded",)
    assert report.blocked_reason_count == 1
    assert report.watch_reason_count == 0


def test_blocked_source_queue_blocks_allocation_even_without_ready_candidates():
    blocked_gate = _action_gate_report(
        review_status="blocked",
        latest_final_status="blocked",
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
        blocked_reason_count=1,
        reason_code_counts=(_reason_count("cycle_review_blocked", 1),),
    )
    blocked_queue = _queue_report((_cost_report(),), action_gate_report=blocked_gate)

    report = _build_risk_report((blocked_queue,))

    assert report.status == "blocked"
    assert report.reason_codes == ("source_queue_blocked",)
    assert report.blocked_source_count == 1
    assert report.candidate_count == 0
    assert report.total_ready_notional == Decimal("0.000000")


def test_empty_queue_reports_block_allocation_without_fabricating_candidates():
    report = _build_risk_report(())

    assert report.status == "blocked"
    assert report.recommended_next_step == "block_paper_research_queue"
    assert report.reason_codes == ("empty_queue_reports",)
    assert report.source_queue_count == 0
    assert report.candidate_count == 0
    assert report.ready_count == 0
    assert report.total_ready_notional == Decimal("0.000000")
    assert report.blocked_reason_count == 1
    assert report.watch_reason_count == 0


def test_reducer_rejects_wrong_types_subclasses_flags_and_bad_thresholds():
    ready_queue = _queue_report((_cost_report(),))
    report = _build_risk_report((ready_queue,))

    with pytest.raises(ValueError, match="PaperActionGatedStrategyRecommendationQueueReport"):
        _build_risk_report((object(),))
    with pytest.raises(ValueError, match="PaperActionGatedStrategyRecommendationQueueReport"):
        _build_risk_report((QueueReportSubclass(**ready_queue.__dict__),))
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueRiskConfig",
    ):
        _build_risk_report((ready_queue,), config=object())
    with pytest.raises(ValueError, match="generated_at"):
        _build_risk_report((ready_queue,), generated_at="2026-06-20")

    object.__setattr__(ready_queue, "readonly", False)
    with pytest.raises(ValueError, match="queue_report must be readonly"):
        _build_risk_report((ready_queue,))

    with pytest.raises(ValueError, match="max_total_ready_notional"):
        replace(
            _risk_config(),
            max_total_ready_notional=Decimal("-0.000001"),
        )
    with pytest.raises(ValueError, match="max_single_queue_ready_notional"):
        replace(
            _risk_config(),
            max_single_queue_ready_notional=Decimal("-0.000001"),
        )
    with pytest.raises(ValueError, match="max_ready_candidate_count"):
        replace(_risk_config(), max_ready_candidate_count=-1)
    with pytest.raises(ValueError, match="max_total_candidate_count"):
        replace(_risk_config(), max_total_candidate_count=-1)
    with pytest.raises(ValueError, match="throttle_utilization_threshold"):
        replace(
            _risk_config(),
            throttle_utilization_threshold=Decimal("1.000001"),
        )

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="within_limits")
    with pytest.raises(ValueError, match="total_ready_notional_utilization"):
        replace(report, total_ready_notional=Decimal("0.000000"))


def test_risk_module_stays_pure_and_readonly_by_import_boundary():
    source = inspect.getsource(risk_module)
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
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg",
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read",
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
        "live",
        "auth",
        "wallet",
        "private_key",
        "private-key",
        "account",
        "order_submission",
        "submit_order",
        "cancel_order",
        "signing",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)
