from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
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


ASSESSMENT_GENERATED_AT = datetime(2026, 6, 18, 10, 30, tzinfo=UTC)
READINESS_GENERATED_AT = datetime(2026, 6, 18, 10, 45, tzinfo=UTC)
BUNDLE_GENERATED_AT = datetime(2026, 6, 18, 14, 0, tzinfo=UTC)


def _recommendation_config() -> PaperStrategyCandidateRecommendationConfig:
    return PaperStrategyCandidateRecommendationConfig(
        config_version="strategy-candidate-recommendation-v1",
        min_recommendation_score=Decimal("0.100000"),
    )


def _selection_config() -> PaperStrategySelectionPolicyConfig:
    return PaperStrategySelectionPolicyConfig(
        config_version="strategy-selection-policy-v1",
        base_position_notional=Decimal("20.000000"),
        max_position_notional=Decimal("12.000000"),
        max_total_notional=Decimal("20.000000"),
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


def _assessment_report() -> PaperCandidateAssessmentReport:
    rows = (
        _assessment_row("alpha-recommend", readiness_score=Decimal("0.600000")),
        _assessment_row("beta-watch", assessment_status="watch", selected_side="no"),
        _assessment_row(
            "gamma-reject",
            assessment_status="blocked",
            readiness_score=Decimal("0.000000"),
            selected_side="none",
            reason_codes=("missing_cost_report",),
        ),
    )
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
    return PaperCandidateAssessmentReport(
        generated_at=ASSESSMENT_GENERATED_AT,
        config_version="candidate-assessment-v1",
        candidate_count=0,
        assessed_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        assessment_rows=(),
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
        generated_at=READINESS_GENERATED_AT,
    )


def _bundle_report(
    *,
    generated_at: datetime = BUNDLE_GENERATED_AT,
) -> PaperStrategyRecommendationBundleReport:
    return build_paper_strategy_recommendation_bundle_report(
        _assessment_report(),
        _readiness_report(),
        config=_bundle_config(),
        generated_at=generated_at,
    )


def test_build_bundle_report_reduces_recommendations_selection_and_explanations():
    report = _bundle_report()

    assert isinstance(report, PaperStrategyRecommendationBundleReport)
    assert report.generated_at == BUNDLE_GENERATED_AT
    assert report.config_version == "strategy-recommendation-bundle-v1"
    assert report.candidate_count == 3
    assert report.recommend_count == 1
    assert report.selected_count == 1
    assert report.total_selected_notional == Decimal("12.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    recommendation_report = report.recommendation_report
    selection_policy_report = report.selection_policy_report
    explanation_report = report.explanation_report

    assert recommendation_report.generated_at == BUNDLE_GENERATED_AT
    assert recommendation_report.config_version == (
        "strategy-candidate-recommendation-v1"
    )
    assert recommendation_report.candidate_count == report.candidate_count
    assert recommendation_report.recommend_count == report.recommend_count
    assert tuple(row.action for row in recommendation_report.recommendation_rows) == (
        "recommend",
        "watch",
        "reject",
    )

    assert selection_policy_report.generated_at == BUNDLE_GENERATED_AT
    assert selection_policy_report.config_version == "strategy-selection-policy-v1"
    assert selection_policy_report.row_count == recommendation_report.candidate_count
    assert selection_policy_report.selected_count == report.selected_count
    assert selection_policy_report.total_selected_notional == (
        report.total_selected_notional
    )
    assert tuple(row.decision for row in selection_policy_report.selection_rows) == (
        "selected",
        "not_selected",
        "not_selected",
    )

    assert explanation_report.generated_at == BUNDLE_GENERATED_AT
    assert explanation_report.source_config_version == recommendation_report.config_version
    assert explanation_report.recommendation_count == (
        recommendation_report.candidate_count
    )
    assert tuple(row.market_slug for row in explanation_report.explanation_rows) == (
        "alpha-recommend",
        "beta-watch",
        "gamma-reject",
    )


def test_build_bundle_report_accepts_empty_candidate_set():
    report = build_paper_strategy_recommendation_bundle_report(
        _empty_assessment_report(),
        _readiness_report(),
        config=_bundle_config(),
        generated_at=BUNDLE_GENERATED_AT,
    )

    assert report.candidate_count == 0
    assert report.recommend_count == 0
    assert report.selected_count == 0
    assert report.total_selected_notional == Decimal("0")
    assert report.recommendation_report.recommendation_rows == ()
    assert report.selection_policy_report.selection_rows == ()
    assert report.explanation_report.explanation_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_build_bundle_report_rejects_wrong_config_type():
    with pytest.raises(ValueError, match="PaperStrategyRecommendationBundleConfig"):
        build_paper_strategy_recommendation_bundle_report(
            _assessment_report(),
            _readiness_report(),
            config=object(),
            generated_at=BUNDLE_GENERATED_AT,
        )


def test_build_bundle_report_rejects_non_readonly_source_reports_through_downstream_builders():
    assessment_report = _assessment_report()
    object.__setattr__(assessment_report, "paper_only", False)

    with pytest.raises(ValueError, match="assessment_report must be paper_only"):
        build_paper_strategy_recommendation_bundle_report(
            assessment_report,
            _readiness_report(),
            config=_bundle_config(),
            generated_at=BUNDLE_GENERATED_AT,
        )

    readiness_report = _readiness_report()
    object.__setattr__(readiness_report, "readonly", False)
    with pytest.raises(ValueError, match="readiness_report must be readonly"):
        build_paper_strategy_recommendation_bundle_report(
            _assessment_report(),
            readiness_report,
            config=_bundle_config(),
            generated_at=BUNDLE_GENERATED_AT,
        )


def test_bundle_report_direct_constructor_rejects_count_inconsistency():
    report = _bundle_report()

    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=report.candidate_count + 1)
    with pytest.raises(ValueError, match="recommend_count"):
        replace(report, recommend_count=report.recommend_count + 1)
    with pytest.raises(ValueError, match="selected_count"):
        replace(report, selected_count=report.selected_count + 1)
    with pytest.raises(ValueError, match="total_selected_notional"):
        replace(report, total_selected_notional=Decimal("0.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(FrozenInstanceError):
        report.selected_count = 0


@pytest.mark.parametrize(
    ("field_name", "row_index", "row_updates"),
    (
        ("market_slug", 0, {"market_slug": "other-market"}),
        ("question", 0, {"question": "Will other-market resolve yes?"}),
        ("source_action", 1, {"source_action": "reject"}),
        ("selected_side", 0, {"selected_side": "no"}),
        ("recommendation_score", 0, {"recommendation_score": Decimal("0.500000")}),
    ),
)
def test_bundle_report_direct_constructor_rejects_selection_row_mismatches(
    field_name,
    row_index,
    row_updates,
):
    report = _bundle_report()
    assert field_name in row_updates
    selection_rows = list(report.selection_policy_report.selection_rows)
    selection_rows[row_index] = replace(selection_rows[row_index], **row_updates)
    selection_policy_report = replace(
        report.selection_policy_report,
        selection_rows=tuple(selection_rows),
    )

    with pytest.raises(
        ValueError,
        match="selection_policy_report rows must match recommendation rows",
    ):
        replace(report, selection_policy_report=selection_policy_report)


@pytest.mark.parametrize(
    ("field_name", "row_updates_by_index"),
    (
        ("market_slug", {0: {"market_slug": "other-market"}}),
        ("action", {0: {"action": "watch"}, 1: {"action": "recommend"}}),
        ("selected_side", {0: {"selected_side": "no"}}),
        ("recommendation_score", {0: {"recommendation_score": Decimal("0.500000")}}),
        ("reason_codes", {0: {"reason_codes": ("other_reason",)}}),
    ),
)
def test_bundle_report_direct_constructor_rejects_explanation_row_mismatches(
    field_name,
    row_updates_by_index,
):
    report = _bundle_report()
    assert any(
        field_name in row_updates
        for row_updates in row_updates_by_index.values()
    )
    explanation_rows = list(report.explanation_report.explanation_rows)
    for row_index, row_updates in row_updates_by_index.items():
        explanation_rows[row_index] = _replace_explanation_row(
            explanation_rows[row_index],
            **row_updates,
        )
    explanation_report = replace(
        report.explanation_report,
        explanation_rows=tuple(explanation_rows),
    )

    with pytest.raises(
        ValueError,
        match="explanation_report rows must match recommendation rows",
    ):
        replace(report, explanation_report=explanation_report)


def _replace_explanation_row(row, **row_updates):
    action = row_updates.get("action", row.action)
    selected_side = row_updates.get("selected_side", row.selected_side)
    recommendation_score = row_updates.get(
        "recommendation_score",
        row.recommendation_score,
    )
    reason_codes = row_updates.get("reason_codes", row.reason_codes)
    primary_reason_code = reason_codes[0]
    return replace(
        row,
        **row_updates,
        primary_reason_code=primary_reason_code,
        explanation=(
            f"{action} {selected_side} because {primary_reason_code} "
            f"(score {recommendation_score})"
        ),
    )


def test_bundle_report_normalizes_generated_at_to_utc():
    generated_at = datetime(2026, 6, 18, 16, 30, tzinfo=timezone(timedelta(hours=2)))

    report = _bundle_report(generated_at=generated_at)

    assert report.generated_at == datetime(2026, 6, 18, 14, 30, tzinfo=UTC)
    assert report.recommendation_report.generated_at == report.generated_at
    assert report.selection_policy_report.generated_at == report.generated_at
    assert report.explanation_report.generated_at == report.generated_at
