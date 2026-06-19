from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
    PaperStrategyCandidateRecommendationReport,
    PaperStrategyCandidateRecommendationRow,
    build_paper_strategy_candidate_recommendation_report,
)
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
    build_paper_strategy_readiness_state_report,
)


ASSESSMENT_GENERATED_AT = datetime(2026, 6, 18, 10, 30, tzinfo=UTC)
READINESS_GENERATED_AT = datetime(2026, 6, 18, 10, 45, tzinfo=UTC)
RECOMMENDATION_GENERATED_AT = datetime(
    2026,
    6,
    18,
    14,
    0,
    tzinfo=timezone(timedelta(hours=2)),
)
CONFIG_VERSION = "strategy-candidate-recommendation-v1"


def _config(**overrides):
    values = {
        "config_version": CONFIG_VERSION,
        "min_recommendation_score": Decimal("0.100000"),
    }
    values.update(overrides)
    return PaperStrategyCandidateRecommendationConfig(**values)


def _assessment_row(
    market_slug: str,
    *,
    assessment_status: str = "ready",
    readiness_score: Decimal = Decimal("0.250000"),
    reason_codes: tuple[str, ...] = ("assessment_ready",),
) -> PaperCandidateAssessmentRow:
    return PaperCandidateAssessmentRow(
        market_slug=market_slug,
        question=f"Question for {market_slug}?",
        research_bucket="blocked" if assessment_status == "blocked" else "research_ready",
        assessment_status=assessment_status,
        source_status=(
            "blocked_by_inputs"
            if assessment_status == "blocked"
            else "paper_review_ready"
        ),
        selected_side="none" if assessment_status == "blocked" else "yes",
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
    *rows: PaperCandidateAssessmentRow,
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


def _readiness_report(overall_status: str):
    return build_paper_strategy_readiness_state_report(
        (
            PaperStrategyReadinessSignal(
                source_name=f"{overall_status}_gate",
                status=overall_status,
                reason_codes=(f"{overall_status}_readiness_input",),
                severity=10,
            ),
        ),
        config_version="strategy-readiness-state-v1",
        generated_at=READINESS_GENERATED_AT,
    )


def _build_report(
    assessment_report: PaperCandidateAssessmentReport,
    overall_status: str,
):
    return build_paper_strategy_candidate_recommendation_report(
        assessment_report,
        _readiness_report(overall_status),
        config=_config(),
        generated_at=RECOMMENDATION_GENERATED_AT,
    )


def test_strategy_candidate_recommendation_recommends_ready_candidate_when_readiness_passes():
    assessment_report = _assessment_report(
        _assessment_row(
            "ready-candidate",
            readiness_score=Decimal("0.1234567"),
            reason_codes=("assessment_ready", "high_edge"),
        ),
    )

    report = _build_report(assessment_report, "pass")

    assert isinstance(report, PaperStrategyCandidateRecommendationReport)
    assert isinstance(report.recommendation_rows[0], PaperStrategyCandidateRecommendationRow)
    assert report.generated_at == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    assert report.config_version == CONFIG_VERSION
    assert report.readiness_overall_status == "pass"
    assert report.candidate_count == 1
    assert report.recommend_count == 1
    assert report.watch_count == 0
    assert report.reject_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.recommendation_rows[0]
    assert row.market_slug == "ready-candidate"
    assert row.question == "Question for ready-candidate?"
    assert row.action == "recommend"
    assert row.assessment_status == "ready"
    assert row.readiness_status == "pass"
    assert row.selected_side == "yes"
    assert row.scoring_side == "yes"
    assert row.recommendation_score == Decimal("0.123457")
    assert row.reason_codes == (
        "assessment_ready",
        "high_edge",
        "readiness_passed",
        "candidate_ready",
    )


def test_strategy_candidate_recommendation_readiness_watch_downgrades_ready_candidate():
    report = _build_report(
        _assessment_report(
            _assessment_row("ready-but-gated", readiness_score=Decimal("0.400000")),
        ),
        "watch",
    )

    row = report.recommendation_rows[0]
    assert report.recommend_count == 0
    assert report.watch_count == 1
    assert report.reject_count == 0
    assert row.action == "watch"
    assert "readiness_watch" in row.reason_codes
    assert "candidate_ready" in row.reason_codes


def test_strategy_candidate_recommendation_recommends_candidate_at_exact_threshold():
    report = build_paper_strategy_candidate_recommendation_report(
        _assessment_report(
            _assessment_row(
                "threshold-candidate",
                readiness_score=Decimal("0.100000"),
            ),
        ),
        _readiness_report("pass"),
        config=_config(min_recommendation_score=Decimal("0.100000")),
        generated_at=RECOMMENDATION_GENERATED_AT,
    )

    row = report.recommendation_rows[0]
    assert row.action == "recommend"
    assert row.recommendation_score == Decimal("0.100000")
    assert "below_recommendation_threshold" not in row.reason_codes


def test_strategy_candidate_recommendation_readiness_blocked_prevents_recommendations():
    report = _build_report(
        _assessment_report(
            _assessment_row("ready-candidate", readiness_score=Decimal("0.900000")),
            _assessment_row(
                "watch-candidate",
                assessment_status="watch",
                readiness_score=Decimal("0.800000"),
                reason_codes=("positive_edge_watch",),
            ),
        ),
        "blocked",
    )

    assert report.recommend_count == 0
    assert report.watch_count == 2
    assert report.reject_count == 0
    assert tuple(row.action for row in report.recommendation_rows) == ("watch", "watch")
    assert all("readiness_blocked" in row.reason_codes for row in report.recommendation_rows)


def test_strategy_candidate_recommendation_rejects_blocked_candidate():
    report = _build_report(
        _assessment_report(
            _assessment_row(
                "blocked-candidate",
                assessment_status="blocked",
                readiness_score=Decimal("0.000000"),
                reason_codes=("missing_cost_report",),
            ),
        ),
        "pass",
    )

    row = report.recommendation_rows[0]
    assert report.recommend_count == 0
    assert report.watch_count == 0
    assert report.reject_count == 1
    assert row.action == "reject"
    assert row.recommendation_score == Decimal("0.000000")
    assert "candidate_blocked" in row.reason_codes
    assert "below_recommendation_threshold" in row.reason_codes


def test_strategy_candidate_recommendation_uses_deterministic_action_score_slug_order():
    report = _build_report(
        _assessment_report(
            _assessment_row(
                "watch-high-score",
                assessment_status="watch",
                readiness_score=Decimal("0.900000"),
                reason_codes=("positive_edge_watch",),
            ),
            _assessment_row(
                "reject-low-score",
                assessment_status="blocked",
                readiness_score=Decimal("0.000000"),
                reason_codes=("missing_cost_report",),
            ),
            _assessment_row("beta-recommend", readiness_score=Decimal("0.400000")),
            _assessment_row("alpha-recommend", readiness_score=Decimal("0.400000")),
            _assessment_row("top-recommend", readiness_score=Decimal("0.800000")),
        ),
        "pass",
    )

    assert tuple(row.market_slug for row in report.recommendation_rows) == (
        "top-recommend",
        "alpha-recommend",
        "beta-recommend",
        "watch-high-score",
        "reject-low-score",
    )
    assert tuple(row.action for row in report.recommendation_rows) == (
        "recommend",
        "recommend",
        "recommend",
        "watch",
        "reject",
    )


def test_strategy_candidate_recommendation_validates_constructors_counts_types_and_flags():
    report = _build_report(
        _assessment_report(
            _assessment_row("alpha-recommend", readiness_score=Decimal("0.400000")),
            _assessment_row("beta-recommend", readiness_score=Decimal("0.300000")),
        ),
        "pass",
    )
    row = report.recommendation_rows[0]

    with pytest.raises(FrozenInstanceError):
        report.recommend_count = 99
    with pytest.raises(FrozenInstanceError):
        row.action = "watch"
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=3)
    with pytest.raises(ValueError, match="recommend_count"):
        replace(report, recommend_count=1)
    with pytest.raises(ValueError, match="deterministic ordering"):
        replace(report, recommendation_rows=tuple(reversed(report.recommendation_rows)))
    with pytest.raises(ValueError, match="PaperStrategyCandidateRecommendationRow"):
        replace(report, recommendation_rows=(object(),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="action"):
        replace(row, action="hold")
    with pytest.raises(ValueError, match="selected side"):
        replace(row, selected_side="none")
    with pytest.raises(ValueError, match="assessment ready"):
        replace(row, assessment_status="watch")
    with pytest.raises(ValueError, match="passing readiness"):
        replace(row, readiness_status="watch")
    with pytest.raises(ValueError, match="blocked assessment"):
        replace(row, assessment_status="blocked")
    with pytest.raises(ValueError, match="recommendation_score"):
        replace(row, recommendation_score=0.1)
    with pytest.raises(ValueError, match="min_recommendation_score"):
        _config(min_recommendation_score=0.1)


@pytest.mark.parametrize(
    ("source_name", "flag_name"),
    (
        ("assessment_report", "paper_only"),
        ("assessment_report", "report_only"),
        ("assessment_report", "readonly"),
        ("readiness_report", "paper_only"),
        ("readiness_report", "report_only"),
        ("readiness_report", "readonly"),
    ),
)
def test_strategy_candidate_recommendation_rejects_false_source_hard_flags(
    source_name,
    flag_name,
):
    assessment_report = _assessment_report(_assessment_row("ready-candidate"))
    readiness_report = _readiness_report("pass")
    source_report = (
        assessment_report if source_name == "assessment_report" else readiness_report
    )
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=f"{source_name} must be {flag_name}"):
        build_paper_strategy_candidate_recommendation_report(
            assessment_report,
            readiness_report,
            config=_config(),
            generated_at=RECOMMENDATION_GENERATED_AT,
        )


def test_strategy_candidate_recommendation_validates_builder_inputs_and_input_flags():
    assessment_report = _assessment_report(_assessment_row("ready-candidate"))
    readiness_report = _readiness_report("pass")

    with pytest.raises(ValueError, match="PaperCandidateAssessmentReport"):
        build_paper_strategy_candidate_recommendation_report(
            object(),
            readiness_report,
            config=_config(),
            generated_at=RECOMMENDATION_GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperStrategyReadinessStateReport"):
        build_paper_strategy_candidate_recommendation_report(
            assessment_report,
            object(),
            config=_config(),
            generated_at=RECOMMENDATION_GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperStrategyCandidateRecommendationConfig"):
        build_paper_strategy_candidate_recommendation_report(
            assessment_report,
            readiness_report,
            config=object(),
            generated_at=RECOMMENDATION_GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_candidate_recommendation_report(
            assessment_report,
            readiness_report,
            config=_config(),
            generated_at="now",
        )

    non_paper_assessment = _assessment_report(_assessment_row("non-paper-candidate"))
    object.__setattr__(non_paper_assessment, "paper_only", False)
    with pytest.raises(ValueError, match="assessment_report must be paper_only"):
        build_paper_strategy_candidate_recommendation_report(
            non_paper_assessment,
            readiness_report,
            config=_config(),
            generated_at=RECOMMENDATION_GENERATED_AT,
        )

    mutable_readiness = _readiness_report("pass")
    object.__setattr__(mutable_readiness, "readonly", False)
    with pytest.raises(ValueError, match="readiness_report must be readonly"):
        build_paper_strategy_candidate_recommendation_report(
            assessment_report,
            mutable_readiness,
            config=_config(),
            generated_at=RECOMMENDATION_GENERATED_AT,
        )
