from dataclasses import replace
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
    PaperStrategyCandidateResearchQueueRow,
    build_paper_strategy_candidate_research_queue_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
RESEARCH_GENERATED_AT = datetime(2026, 6, 20, 12, 30, tzinfo=UTC)
ZERO_DECIMAL = Decimal("0.000000")
SCORE_QUANTUM = Decimal("0.000001")


def _reason_count(reason_code: str, count: int):
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _action_gate_report() -> PaperRecommendationCycleActionGateReport:
    return PaperRecommendationCycleActionGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-cycle-action-gate-v0",
        source_config_version="paper-recommendation-cycle-review-v0",
        review_status="pass",
        latest_final_status="pass",
        action_status="research_ready",
        recommended_next_step="build_candidate_research_queue",
        missing_required_artifact_count=0,
        blocked_reason_count=0,
        watch_reason_count=0,
        reason_code_counts=(_reason_count("cycle_review_pass", 1),),
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
    return build_paper_action_gated_strategy_recommendation_queue_report(
        _action_gate_report(),
        _screening_report(cost_reports),
        cost_reports,
        config=_action_gated_config(),
        generated_at=GENERATED_AT,
    )


def _research_config() -> PaperStrategyCandidateResearchQueueConfig:
    return PaperStrategyCandidateResearchQueueConfig(
        config_version="strategy-candidate-research-queue-v0",
    )


def _build_research_report(source: PaperActionGatedStrategyRecommendationQueueReport):
    return build_paper_strategy_candidate_research_queue_report(
        source,
        config=_research_config(),
        generated_at=RESEARCH_GENERATED_AT,
    )


def _primary_reason_code_counts(rows):
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _score_average(rows):
    items = tuple(rows)
    if not items:
        return ZERO_DECIMAL
    return (sum((row.recommendation_score for row in items), Decimal("0")) / Decimal(len(items))).quantize(
        SCORE_QUANTUM,
    )


def _source_with_queue_rows(source, queue_rows):
    queue_summary_report = source.queue_summary_report
    assert queue_summary_report is not None
    ready_rows = tuple(row for row in queue_rows if row.queue_status == "ready")
    updated_queue_summary = replace(
        queue_summary_report,
        queue_count=len(queue_rows),
        ready_count=len(ready_rows),
        watch_count=sum(1 for row in queue_rows if row.queue_status == "watch"),
        blocked_count=sum(1 for row in queue_rows if row.queue_status == "blocked"),
        total_ready_notional=sum(
            (row.suggested_notional for row in ready_rows),
            Decimal("0"),
        ).quantize(SCORE_QUANTUM),
        top_score=(
            queue_rows[0].recommendation_score
            if queue_rows
            else ZERO_DECIMAL
        ),
        average_ready_score=_score_average(ready_rows),
        primary_reason_code_counts=_primary_reason_code_counts(queue_rows),
        queue_rows=queue_rows,
    )
    return replace(source, queue_summary_report=updated_queue_summary)


def _source_with_queue_row(source, **row_updates):
    queue_summary_report = source.queue_summary_report
    assert queue_summary_report is not None
    queue_rows = list(queue_summary_report.queue_rows)
    queue_rows[0] = replace(queue_rows[0], **row_updates)
    return _source_with_queue_rows(source, tuple(queue_rows))


def test_join_integrity_accepts_valid_research_ready_source_as_control():
    source = _ready_source_report()

    report = _build_research_report(source)

    assert isinstance(report, PaperStrategyCandidateResearchQueueReport)
    assert all(isinstance(row, PaperStrategyCandidateResearchQueueRow) for row in report.rows)
    assert report.action_status == "research_ready"
    assert report.research_status == "ready"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rejects_queue_summary_slug_set_that_differs_from_assessment_rows():
    source = _ready_source_report()
    assessment_report = source.candidate_assessment_report
    assert assessment_report is not None
    assessment_rows = list(assessment_report.assessment_rows)
    assessment_rows[-1] = replace(
        assessment_rows[-1],
        market_slug="orphan-assessment-slug",
    )
    source = replace(
        source,
        candidate_assessment_report=replace(
            assessment_report,
            assessment_rows=tuple(assessment_rows),
        ),
    )

    with pytest.raises(ValueError, match="market_slug|slug|assessment_rows|queue"):
        _build_research_report(source)


@pytest.mark.parametrize(
    ("row_updates", "expected_match"),
    (
        ({"selected_side": "no"}, "selected_side|queue|selection|recommendation|explanation"),
        ({"action": "watch"}, "action|queue|selection|recommendation|explanation"),
        (
            {"recommendation_score": Decimal("0.990000")},
            "recommendation_score|queue|selection|recommendation|explanation",
        ),
        (
            {"primary_reason_code": "synthetic_mismatch_reason"},
            "primary_reason_code|queue|explanation|recommendation",
        ),
    ),
)
def test_rejects_queue_row_values_that_differ_from_nested_join_rows(
    row_updates,
    expected_match,
):
    source = _source_with_queue_row(_ready_source_report(), **row_updates)

    with pytest.raises(ValueError, match=expected_match):
        _build_research_report(source)


@pytest.mark.parametrize(
    ("collection_owner", "collection_name"),
    (
        ("candidate_assessment_report", "assessment_rows"),
        ("queue_summary_report", "queue_rows"),
        ("recommendation_report", "recommendation_rows"),
        ("selection_policy_report", "selection_rows"),
        ("explanation_report", "explanation_rows"),
    ),
)
def test_rejects_duplicate_market_slug_in_underlying_row_collections(
    collection_owner,
    collection_name,
):
    source = _ready_source_report()
    bundle_report = source.bundle_report
    assert bundle_report is not None
    owner_by_name = {
        "candidate_assessment_report": source.candidate_assessment_report,
        "queue_summary_report": source.queue_summary_report,
        "recommendation_report": bundle_report.recommendation_report,
        "selection_policy_report": bundle_report.selection_policy_report,
        "explanation_report": bundle_report.explanation_report,
    }
    owner = owner_by_name[collection_owner]
    assert owner is not None
    rows = list(getattr(owner, collection_name))
    rows[-1] = replace(rows[-1], market_slug=rows[0].market_slug)
    object.__setattr__(owner, collection_name, tuple(rows))

    with pytest.raises(ValueError, match="unique|duplicate|market_slug|slug"):
        _build_research_report(source)


@pytest.mark.parametrize(
    ("target_name", "flag_name"),
    (
        ("candidate_assessment_report", "paper_only"),
        ("bundle_report", "report_only"),
        ("queue_summary_report", "readonly"),
        ("recommendation_report", "paper_only"),
        ("selection_policy_report", "report_only"),
        ("explanation_report", "readonly"),
        ("queue_row", "readonly"),
    ),
)
def test_rejects_false_hard_flags_on_nested_reports_and_rows(
    target_name,
    flag_name,
):
    source = _ready_source_report()
    bundle_report = source.bundle_report
    queue_summary_report = source.queue_summary_report
    assert bundle_report is not None
    assert queue_summary_report is not None
    target_by_name = {
        "candidate_assessment_report": source.candidate_assessment_report,
        "bundle_report": bundle_report,
        "queue_summary_report": queue_summary_report,
        "recommendation_report": bundle_report.recommendation_report,
        "selection_policy_report": bundle_report.selection_policy_report,
        "explanation_report": bundle_report.explanation_report,
        "queue_row": queue_summary_report.queue_rows[0],
    }
    target = target_by_name[target_name]
    assert target is not None
    object.__setattr__(target, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        _build_research_report(source)
