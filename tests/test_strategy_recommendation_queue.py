from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
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
    PaperStrategyRecommendationQueueRow,
    PaperStrategyRecommendationQueueSummaryReport,
    build_paper_strategy_recommendation_queue_summary_report,
)


ASSESSMENT_GENERATED_AT = datetime(2026, 6, 18, 10, 30, tzinfo=UTC)
READINESS_GENERATED_AT = datetime(2026, 6, 18, 10, 45, tzinfo=UTC)
BUNDLE_GENERATED_AT = datetime(2026, 6, 18, 14, 0, tzinfo=UTC)


def _recommendation_config() -> PaperStrategyCandidateRecommendationConfig:
    return PaperStrategyCandidateRecommendationConfig(
        config_version="strategy-candidate-recommendation-v1",
        min_recommendation_score=Decimal("0.100000"),
    )


def _selection_config(
    *,
    base_position_notional: Decimal = Decimal("10.000000"),
    max_position_notional: Decimal = Decimal("12.000000"),
    max_total_notional: Decimal = Decimal("20.000000"),
) -> PaperStrategySelectionPolicyConfig:
    return PaperStrategySelectionPolicyConfig(
        config_version="strategy-selection-policy-v1",
        base_position_notional=base_position_notional,
        max_position_notional=max_position_notional,
        max_total_notional=max_total_notional,
    )


def _bundle_config(
    *,
    base_position_notional: Decimal = Decimal("10.000000"),
    max_position_notional: Decimal = Decimal("12.000000"),
    max_total_notional: Decimal = Decimal("20.000000"),
) -> PaperStrategyRecommendationBundleConfig:
    return PaperStrategyRecommendationBundleConfig(
        config_version="strategy-recommendation-bundle-v1",
        recommendation_config=_recommendation_config(),
        selection_policy_config=_selection_config(
            base_position_notional=base_position_notional,
            max_position_notional=max_position_notional,
            max_total_notional=max_total_notional,
        ),
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
        generated_at=ASSESSMENT_GENERATED_AT,
        config_version="candidate-assessment-v1",
        candidate_count=len(rows),
        assessed_count=len(rows),
        ready_count=sum(1 for row in rows if row.assessment_status == "ready"),
        watch_count=sum(1 for row in rows if row.assessment_status == "watch"),
        blocked_count=sum(1 for row in rows if row.assessment_status == "blocked"),
        assessment_rows=rows,
    )


def _empty_assessment_report() -> PaperCandidateAssessmentReport:
    return _assessment_report(())


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
        generated_at=READINESS_GENERATED_AT,
    )


def _bundle_report(
    rows: tuple[PaperCandidateAssessmentRow, ...],
    *,
    base_position_notional: Decimal = Decimal("10.000000"),
    max_position_notional: Decimal = Decimal("12.000000"),
    max_total_notional: Decimal = Decimal("20.000000"),
) -> PaperStrategyRecommendationBundleReport:
    return build_paper_strategy_recommendation_bundle_report(
        _assessment_report(rows),
        _readiness_report(),
        config=_bundle_config(
            base_position_notional=base_position_notional,
            max_position_notional=max_position_notional,
            max_total_notional=max_total_notional,
        ),
        generated_at=BUNDLE_GENERATED_AT,
    )


def test_queue_summary_orders_rows_and_aggregates_operator_counts():
    bundle = _bundle_report(
        (
            _assessment_row(
                "zeta-ready-lower-score",
                readiness_score=Decimal("0.400000"),
                selected_side="yes",
                reason_codes=("ready_lower",),
            ),
            _assessment_row(
                "alpha-ready-higher-score",
                readiness_score=Decimal("0.800000"),
                selected_side="no",
                reason_codes=("ready_higher",),
            ),
            _assessment_row(
                "beta-skipped-cap",
                readiness_score=Decimal("0.700000"),
                selected_side="yes",
                reason_codes=("ready_skipped",),
            ),
            _assessment_row(
                "gamma-watch",
                assessment_status="watch",
                readiness_score=Decimal("0.950000"),
                selected_side="no",
                reason_codes=("watch_candidate",),
            ),
            _assessment_row(
                "delta-blocked",
                assessment_status="blocked",
                readiness_score=Decimal("0.000000"),
                selected_side="none",
                reason_codes=("missing_inputs",),
            ),
        ),
        base_position_notional=Decimal("10.000000"),
        max_position_notional=Decimal("10.000000"),
        max_total_notional=Decimal("13.000000"),
    )

    summary = build_paper_strategy_recommendation_queue_summary_report(bundle)

    assert isinstance(summary, PaperStrategyRecommendationQueueSummaryReport)
    assert summary.generated_at == BUNDLE_GENERATED_AT
    assert summary.source_config_version == "strategy-recommendation-bundle-v1"
    assert summary.queue_count == 5
    assert summary.ready_count == 1
    assert summary.watch_count == 3
    assert summary.blocked_count == 1
    assert summary.total_ready_notional == Decimal("8.000000")
    assert summary.top_score == Decimal("0.800000")
    assert summary.average_ready_score == Decimal("0.800000")
    assert summary.primary_reason_code_counts == (
        ("missing_inputs", 1),
        ("ready_higher", 1),
        ("ready_lower", 1),
        ("ready_skipped", 1),
        ("watch_candidate", 1),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.market_slug for row in summary.queue_rows) == (
        "alpha-ready-higher-score",
        "gamma-watch",
        "beta-skipped-cap",
        "zeta-ready-lower-score",
        "delta-blocked",
    )
    assert tuple(row.rank for row in summary.queue_rows) == (1, 2, 3, 4, 5)
    assert tuple(row.queue_status for row in summary.queue_rows) == (
        "ready",
        "watch",
        "watch",
        "watch",
        "blocked",
    )
    assert tuple(row.action for row in summary.queue_rows) == (
        "recommend",
        "watch",
        "recommend",
        "recommend",
        "reject",
    )
    assert tuple(row.decision for row in summary.queue_rows) == (
        "selected",
        "not_selected",
        "skipped",
        "skipped",
        "not_selected",
    )
    assert summary.queue_rows[0].selected_side == "no"
    assert summary.queue_rows[0].suggested_notional == Decimal("8.000000")
    assert summary.queue_rows[1].suggested_notional == Decimal("0.000000")
    assert summary.queue_rows[2].suggested_notional == Decimal("7.000000")
    assert summary.queue_rows[3].suggested_notional == Decimal("4.000000")
    assert summary.queue_rows[4].suggested_notional == Decimal("0.000000")


def test_queue_summary_uses_notional_and_slug_as_deterministic_tie_breakers():
    bundle = _bundle_report(
        (
            _assessment_row(
                "gamma-equal-score",
                readiness_score=Decimal("0.500000"),
                reason_codes=("same_reason",),
            ),
            _assessment_row(
                "alpha-equal-score",
                readiness_score=Decimal("0.500000"),
                reason_codes=("same_reason",),
            ),
            _assessment_row(
                "beta-equal-score",
                readiness_score=Decimal("0.500000"),
                reason_codes=("same_reason",),
            ),
        ),
        max_total_notional=Decimal("30.000000"),
    )
    selection_rows = list(bundle.selection_policy_report.selection_rows)
    selection_rows[0] = replace(
        selection_rows[0],
        suggested_position_notional=Decimal("9.000000"),
        selected_position_notional=Decimal("9.000000"),
    )
    selection_rows[1] = replace(
        selection_rows[1],
        suggested_position_notional=Decimal("9.000000"),
        selected_position_notional=Decimal("9.000000"),
    )
    selection_rows[2] = replace(
        selection_rows[2],
        suggested_position_notional=Decimal("5.000000"),
        selected_position_notional=Decimal("5.000000"),
    )
    selection_policy_report = replace(
        bundle.selection_policy_report,
        selection_rows=tuple(selection_rows),
        total_selected_notional=Decimal("23.000000"),
        total_suggested_notional=Decimal("23.000000"),
        remaining_total_notional=None,
        total_notional_utilization=None,
    )
    bundle = replace(
        bundle,
        selection_policy_report=selection_policy_report,
        total_selected_notional=Decimal("23.000000"),
        total_suggested_notional=Decimal("23.000000"),
        remaining_total_notional=None,
    )

    summary = build_paper_strategy_recommendation_queue_summary_report(bundle)

    assert tuple(row.market_slug for row in summary.queue_rows) == (
        "alpha-equal-score",
        "beta-equal-score",
        "gamma-equal-score",
    )
    assert tuple(row.suggested_notional for row in summary.queue_rows) == (
        Decimal("9.000000"),
        Decimal("9.000000"),
        Decimal("5.000000"),
    )


def test_queue_summary_accepts_empty_bundle():
    bundle = build_paper_strategy_recommendation_bundle_report(
        _empty_assessment_report(),
        _readiness_report(),
        config=_bundle_config(),
        generated_at=BUNDLE_GENERATED_AT,
    )

    summary = build_paper_strategy_recommendation_queue_summary_report(bundle)

    assert summary.queue_rows == ()
    assert summary.queue_count == 0
    assert summary.ready_count == 0
    assert summary.watch_count == 0
    assert summary.blocked_count == 0
    assert summary.total_ready_notional == Decimal("0.000000")
    assert summary.top_score == Decimal("0.000000")
    assert summary.average_ready_score == Decimal("0.000000")
    assert summary.primary_reason_code_counts == ()
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_queue_summary_validates_input_report_and_hard_flags():
    with pytest.raises(
        ValueError,
        match="PaperStrategyRecommendationBundleReport",
    ):
        build_paper_strategy_recommendation_queue_summary_report(object())

    bundle = _bundle_report(
        (
            _assessment_row("alpha-ready", readiness_score=Decimal("0.500000")),
        ),
    )
    object.__setattr__(bundle, "readonly", False)

    with pytest.raises(ValueError, match="bundle_report must be readonly"):
        build_paper_strategy_recommendation_queue_summary_report(bundle)


def test_queue_summary_dataclasses_are_frozen_and_validate_invariants():
    bundle = _bundle_report(
        (
            _assessment_row("alpha-ready", readiness_score=Decimal("0.500000")),
        ),
    )
    summary = build_paper_strategy_recommendation_queue_summary_report(bundle)

    with pytest.raises(FrozenInstanceError):
        summary.queue_count = 0
    with pytest.raises(FrozenInstanceError):
        summary.queue_rows[0].rank = 0
    with pytest.raises(ValueError, match="queue_count"):
        replace(summary, queue_count=999)
    with pytest.raises(ValueError, match="rank"):
        replace(summary.queue_rows[0], rank=0)
    with pytest.raises(ValueError, match="queue_status"):
        replace(summary.queue_rows[0], queue_status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)


def test_queue_summary_quantizes_decimal_outputs_to_six_places():
    bundle = _bundle_report(
        (
            _assessment_row(
                "alpha-ready",
                readiness_score=Decimal("0.333333"),
                reason_codes=("alpha_reason",),
            ),
            _assessment_row(
                "beta-ready",
                readiness_score=Decimal("0.333334"),
                reason_codes=("beta_reason",),
            ),
        ),
        base_position_notional=Decimal("10.000000"),
        max_total_notional=Decimal("20.000000"),
    )

    summary = build_paper_strategy_recommendation_queue_summary_report(bundle)

    assert summary.total_ready_notional == Decimal("6.666670")
    assert summary.top_score == Decimal("0.333334")
    assert summary.average_ready_score == Decimal("0.333334")
    assert tuple(row.recommendation_score for row in summary.queue_rows) == (
        Decimal("0.333334"),
        Decimal("0.333333"),
    )
    assert tuple(row.suggested_notional for row in summary.queue_rows) == (
        Decimal("3.333340"),
        Decimal("3.333330"),
    )


def test_queue_row_rejects_non_decimal_score_and_notional():
    with pytest.raises(ValueError, match="recommendation_score"):
        PaperStrategyRecommendationQueueRow(
            rank=1,
            market_slug="alpha-ready",
            selected_side="yes",
            action="recommend",
            decision="selected",
            recommendation_score="0.500000",
            suggested_notional=Decimal("5.000000"),
            primary_reason_code="assessment_ready",
            queue_status="ready",
        )
    with pytest.raises(ValueError, match="suggested_notional"):
        PaperStrategyRecommendationQueueRow(
            rank=1,
            market_slug="alpha-ready",
            selected_side="yes",
            action="recommend",
            decision="selected",
            recommendation_score=Decimal("0.500000"),
            suggested_notional="5.000000",
            primary_reason_code="assessment_ready",
            queue_status="ready",
        )
