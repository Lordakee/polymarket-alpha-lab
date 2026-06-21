from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
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
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
    build_paper_strategy_readiness_state_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
    PaperStrategyRecommendationBundleReport,
    build_paper_strategy_recommendation_bundle_report,
)
from polymarket_alpha_lab.strategy_recommendation_queue import (
    build_paper_strategy_recommendation_queue_summary_report,
)


SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)


class SourceReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def _reason_count(reason_code: str, count: int):
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _recommendation_config() -> PaperStrategyCandidateRecommendationConfig:
    return PaperStrategyCandidateRecommendationConfig(
        config_version="strategy-candidate-recommendation-v1",
        min_recommendation_score=Decimal("0.100000"),
    )


def _selection_config() -> PaperStrategySelectionPolicyConfig:
    return PaperStrategySelectionPolicyConfig(
        config_version="strategy-selection-policy-v1",
        base_position_notional=Decimal("10.000000"),
        max_position_notional=Decimal("12.000000"),
        max_total_notional=Decimal("30.000000"),
    )


def _bundle_config() -> PaperStrategyRecommendationBundleConfig:
    return PaperStrategyRecommendationBundleConfig(
        config_version="strategy-recommendation-bundle-v1",
        recommendation_config=_recommendation_config(),
        selection_policy_config=_selection_config(),
    )


def _assessment_row(
    market_slug: str,
    *,
    assessment_status: str = "ready",
    readiness_score: Decimal = Decimal("0.500000"),
    selected_side: str = "yes",
    reason_codes: tuple[str, ...] = ("assessment_ready",),
) -> PaperCandidateAssessmentRow:
    return PaperCandidateAssessmentRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        research_bucket="blocked" if assessment_status == "blocked" else "research_ready",
        assessment_status=assessment_status,
        source_status=(
            "blocked_by_inputs"
            if assessment_status == "blocked"
            else "paper_review_ready"
        ),
        selected_side=selected_side,
        scoring_side="yes",
        screening_score=readiness_score,
        net_edge_per_share=readiness_score,
        total_cost_per_share=Decimal("0.000000"),
        confidence=Decimal("0.9000"),
        spread=Decimal("0.0100"),
        resolution_risk=Decimal("0.0200"),
        readiness_score=readiness_score,
        reason_codes=reason_codes,
    )


def _assessment_report(
    rows: tuple[PaperCandidateAssessmentRow, ...],
) -> PaperCandidateAssessmentReport:
    return PaperCandidateAssessmentReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="candidate-assessment-v1",
        candidate_count=len(rows),
        assessed_count=len(rows),
        ready_count=sum(1 for row in rows if row.assessment_status == "ready"),
        watch_count=sum(1 for row in rows if row.assessment_status == "watch"),
        blocked_count=sum(1 for row in rows if row.assessment_status == "blocked"),
        assessment_rows=rows,
    )


def _readiness_report():
    return build_paper_strategy_readiness_state_report(
        (
            PaperStrategyReadinessSignal(
                source_name="paper_gate",
                status="pass",
                reason_codes=("readiness_input_passed",),
                severity=10,
            ),
        ),
        config_version="strategy-readiness-state-v1",
        generated_at=SOURCE_GENERATED_AT,
    )


def _bundle_report(
    assessment_report: PaperCandidateAssessmentReport,
) -> PaperStrategyRecommendationBundleReport:
    return build_paper_strategy_recommendation_bundle_report(
        assessment_report,
        _readiness_report(),
        config=_bundle_config(),
        generated_at=SOURCE_GENERATED_AT,
    )


def _config(**overrides) -> PaperStrategyCandidateResearchQueueConfig:
    values = {
        "config_version": "strategy-candidate-research-queue-v0",
    }
    values.update(overrides)
    return PaperStrategyCandidateResearchQueueConfig(**values)


def _source_report(
    rows: tuple[PaperCandidateAssessmentRow, ...] = (),
    *,
    action_status: str = "research_ready",
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]
    | None = None,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    if reason_code_counts is None:
        reason_code_counts = (_reason_count(f"cycle_review_{action_status}", 1),)

    if action_status != "research_ready":
        next_step_by_status = {
            "watch": "await_fresh_cycle_evidence",
            "blocked": "repair_cycle_evidence",
        }
        return PaperActionGatedStrategyRecommendationQueueReport(
            generated_at=SOURCE_GENERATED_AT,
            config_version="action-gated-strategy-recommendation-queue-v0",
            source_config_version="paper-recommendation-cycle-action-gate-v0",
            action_status=action_status,
            recommended_next_step=next_step_by_status[action_status],
            reason_code_counts=reason_code_counts,
            candidate_count=0,
            ready_count=0,
            watch_count=0,
            blocked_count=0,
            total_ready_notional=Decimal("0.000000"),
        )

    candidate_assessment_report = _assessment_report(rows)
    bundle_report = _bundle_report(candidate_assessment_report)
    queue_summary_report = build_paper_strategy_recommendation_queue_summary_report(
        bundle_report,
    )
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        reason_code_counts=reason_code_counts,
        candidate_count=queue_summary_report.queue_count,
        ready_count=queue_summary_report.ready_count,
        watch_count=queue_summary_report.watch_count,
        blocked_count=queue_summary_report.blocked_count,
        total_ready_notional=queue_summary_report.total_ready_notional,
        candidate_assessment_report=candidate_assessment_report,
        bundle_report=bundle_report,
        queue_summary_report=queue_summary_report,
    )


def _build_report(
    source_report,
    *,
    config=None,
    generated_at=GENERATED_AT,
):
    return build_paper_strategy_candidate_research_queue_report(
        source_report,
        config=config or _config(),
        generated_at=generated_at,
    )


def _unsafe_source_clone(
    source_report: PaperActionGatedStrategyRecommendationQueueReport,
    **overrides,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    clone = object.__new__(PaperActionGatedStrategyRecommendationQueueReport)
    for field_name, value in source_report.__dict__.items():
        object.__setattr__(clone, field_name, value)
    for field_name, value in overrides.items():
        object.__setattr__(clone, field_name, value)
    return clone


def _ready_source_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    return _source_report(
        (
            _assessment_row(
                "alpha-ready",
                readiness_score=Decimal("0.800000"),
                reason_codes=("alpha_ready",),
            ),
            _assessment_row(
                "beta-watch",
                assessment_status="watch",
                readiness_score=Decimal("0.700000"),
                selected_side="no",
                reason_codes=("beta_watch",),
            ),
            _assessment_row(
                "gamma-blocked",
                assessment_status="blocked",
                readiness_score=Decimal("0.000000"),
                selected_side="none",
                reason_codes=("gamma_blocked",),
            ),
        ),
    )


def _research_row(**overrides) -> PaperStrategyCandidateResearchQueueRow:
    values = {
        "research_rank": 1,
        "queue_rank": 1,
        "market_slug": "alpha-ready",
        "question": "Will alpha-ready resolve yes?",
        "selected_side": "yes",
        "scoring_side": "yes",
        "source_action": "recommend",
        "decision": "selected",
        "queue_status": "ready",
        "research_status": "ready",
        "research_bucket": "research_ready",
        "assessment_status": "ready",
        "source_status": "paper_review_ready",
        "readiness_status": "pass",
        "recommendation_score": Decimal("0.800000"),
        "readiness_score": Decimal("0.800000"),
        "screening_score": Decimal("0.800000"),
        "net_edge_per_share": Decimal("0.800000"),
        "total_cost_per_share": Decimal("0.000000"),
        "confidence": Decimal("0.900000"),
        "spread": Decimal("0.010000"),
        "resolution_risk": Decimal("0.020000"),
        "suggested_notional": Decimal("8.000000"),
        "selected_position_notional": Decimal("8.000000"),
        "primary_reason_code": "alpha_ready",
        "research_priority_score": Decimal("0.800000"),
        "evidence_gap_codes": (),
        "reason_codes": ("alpha_ready",),
        "explanation": "recommend yes because alpha_ready (score 0.800000)",
    }
    values.update(overrides)
    return PaperStrategyCandidateResearchQueueRow(**values)


def _research_report(**overrides) -> PaperStrategyCandidateResearchQueueReport:
    row = _research_row()
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "strategy-candidate-research-queue-v0",
        "source_config_version": "action-gated-strategy-recommendation-queue-v0",
        "action_status": "research_ready",
        "recommended_next_step": "review_candidate_research_queue",
        "source_reason_code_counts": (_reason_count("cycle_review_research_ready", 1),),
        "research_status": "ready",
        "candidate_count": 1,
        "research_ready_count": 1,
        "watch_count": 0,
        "blocked_count": 0,
        "selected_count": 1,
        "skipped_count": 0,
        "not_selected_count": 0,
        "total_ready_notional": Decimal("8.000000"),
        "total_selected_notional": Decimal("8.000000"),
        "total_suggested_notional": Decimal("8.000000"),
        "top_research_priority_score": Decimal("0.800000"),
        "average_research_ready_score": Decimal("0.800000"),
        "primary_reason_code_counts": (("alpha_ready", 1),),
        "rows": (row,),
        "reason_codes": ("candidate_research_queue_ready",),
    }
    values.update(overrides)
    return PaperStrategyCandidateResearchQueueReport(**values)


def test_research_ready_source_builds_readonly_research_rows_from_nested_reports():
    source = _ready_source_report()

    report = _build_report(source)

    assert isinstance(report, PaperStrategyCandidateResearchQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-candidate-research-queue-v0"
    assert report.source_config_version == source.config_version
    assert report.action_status == "research_ready"
    assert report.research_status == "ready"
    assert report.candidate_count == 3
    assert report.research_ready_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.total_ready_notional == Decimal("8.000000")
    assert type(report.total_ready_notional) is Decimal
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.rows) == (
        "alpha-ready",
        "beta-watch",
        "gamma-blocked",
    )
    assert tuple(row.research_rank for row in report.rows) == (1, 2, 3)
    assert tuple(row.queue_rank for row in report.rows) == (1, 2, 3)
    assert tuple(row.question for row in report.rows) == (
        "Will alpha-ready resolve yes?",
        "Will beta-watch resolve yes?",
        "Will gamma-blocked resolve yes?",
    )
    assert tuple(row.selected_side for row in report.rows) == ("yes", "no", "none")
    assert tuple(row.source_action for row in report.rows) == (
        "recommend",
        "watch",
        "reject",
    )
    assert tuple(row.research_status for row in report.rows) == (
        "ready",
        "watch",
        "blocked",
    )
    assert tuple(row.recommendation_score for row in report.rows) == (
        Decimal("0.800000"),
        Decimal("0.700000"),
        Decimal("0.000000"),
    )
    assert tuple(row.suggested_notional for row in report.rows) == (
        Decimal("8.000000"),
        Decimal("0.000000"),
        Decimal("0.000000"),
    )
    assert tuple(row.primary_reason_code for row in report.rows) == (
        "alpha_ready",
        "beta_watch",
        "gamma_blocked",
    )
    assert all(
        isinstance(row, PaperStrategyCandidateResearchQueueRow)
        for row in report.rows
    )
    assert all(row.paper_only is True for row in report.rows)
    assert all(row.report_only is True for row in report.rows)
    assert all(row.readonly is True for row in report.rows)
    assert all(type(row.recommendation_score) is Decimal for row in report.rows)
    assert all(type(row.suggested_notional) is Decimal for row in report.rows)


@pytest.mark.parametrize("action_status", ("watch", "blocked"))
def test_watch_and_blocked_sources_emit_empty_rows_without_nested_reports(action_status):
    source = _source_report(action_status=action_status)

    report = _build_report(source)

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-candidate-research-queue-v0"
    assert report.source_config_version == source.config_version
    assert report.action_status == action_status
    assert report.research_status == action_status
    assert report.candidate_count == 0
    assert report.research_ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_ready_notional == Decimal("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reducer_accepts_only_action_gated_source_reports_and_hard_flags():
    source = _ready_source_report()

    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueReport",
    ):
        _build_report(object())
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueReport",
    ):
        _build_report(SourceReportSubclass(**source.__dict__))
    with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueConfig"):
        _build_report(source, config=object())
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(source, generated_at="2026-06-20")

    object.__setattr__(source, "readonly", False)
    with pytest.raises(ValueError, match="source_report must be readonly"):
        _build_report(source)


@pytest.mark.parametrize(
    "nested_field",
    ("candidate_assessment_report", "bundle_report", "queue_summary_report"),
)
def test_research_ready_source_requires_nested_reports_and_safe_nested_flags(
    nested_field,
):
    source = _ready_source_report()
    missing_nested = _unsafe_source_clone(source, **{nested_field: None})

    with pytest.raises(ValueError, match=nested_field):
        _build_report(missing_nested)

    source = _ready_source_report()
    nested_report = getattr(source, nested_field)
    assert nested_report is not None
    object.__setattr__(nested_report, "readonly", False)

    with pytest.raises(ValueError, match=f"{nested_field} must be readonly"):
        _build_report(source)


def test_mismatched_nested_market_slugs_are_rejected():
    source = _ready_source_report()
    assert source.queue_summary_report is not None

    summary = source.queue_summary_report
    mismatched_row = replace(summary.queue_rows[0], market_slug="omega-mismatch")
    mismatched_summary = replace(
        summary,
        queue_rows=(mismatched_row,) + summary.queue_rows[1:],
    )
    source = replace(source, queue_summary_report=mismatched_summary)

    with pytest.raises(ValueError, match="market_slug"):
        _build_report(source)


def test_config_row_and_report_are_frozen_and_validate_direct_invariants():
    row = _research_row()
    report = _research_report()

    with pytest.raises(FrozenInstanceError):
        row.research_rank = 2
    with pytest.raises(FrozenInstanceError):
        report.candidate_count = 2
    with pytest.raises(FrozenInstanceError):
        _config().config_version = "other"

    with pytest.raises(ValueError, match="config_version"):
        replace(_config(), config_version="")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)

    with pytest.raises(ValueError, match="research_rank"):
        replace(row, research_rank=0)
    with pytest.raises(ValueError, match="market_slug"):
        replace(row, market_slug="")
    with pytest.raises(ValueError, match="research_status"):
        replace(row, research_status="defer")
    with pytest.raises(ValueError, match="recommendation_score"):
        replace(row, recommendation_score="0.800000")
    with pytest.raises(ValueError, match="suggested_notional"):
        replace(row, suggested_notional="8.000000")
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=2)
    with pytest.raises(ValueError, match="research_ready_count"):
        replace(report, research_ready_count=0)
    with pytest.raises(ValueError, match="total_ready_notional"):
        replace(report, total_ready_notional=Decimal("7.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
