from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

import polymarket_alpha_lab.strategy_recommendation_explain as explain
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
    PaperStrategyRecommendationExplanationRow,
    build_paper_strategy_recommendation_explanation_report,
)


GENERATED_AT = datetime(2026, 6, 18, 14, 30, tzinfo=UTC)


@dataclass(frozen=True)
class _RecommendationRow:
    market_slug: str
    question: str
    action: str
    selected_side: str
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class _RecommendationReport:
    recommendation_rows: tuple[_RecommendationRow, ...]
    config_version: str = "strategy-candidate-recommendation-v1"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class _RecommendationReportSubclass(_RecommendationReport):
    pass


@pytest.fixture(autouse=True)
def _expected_recommendation_report_type(monkeypatch):
    monkeypatch.setattr(
        explain,
        "PaperStrategyCandidateRecommendationReport",
        _RecommendationReport,
    )


def _row(
    market_slug: str,
    *,
    action: str,
    selected_side: str,
    score: Decimal,
    reason_codes: tuple[str, ...],
) -> _RecommendationRow:
    return _RecommendationRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        action=action,
        selected_side=selected_side,
        recommendation_score=score,
        reason_codes=reason_codes,
    )


def _recommendation_report() -> _RecommendationReport:
    return _RecommendationReport(
        recommendation_rows=(
            _row(
                "market-recommend",
                action="recommend",
                selected_side="yes",
                score=Decimal("0.9100"),
                reason_codes=("assessment_ready", "liquidity_ok"),
            ),
            _row(
                "market-watch",
                action="watch",
                selected_side="no",
                score=Decimal("0.5200"),
                reason_codes=("low_net_edge",),
            ),
            _row(
                "market-reject",
                action="reject",
                selected_side="none",
                score=Decimal("0.0000"),
                reason_codes=(),
            ),
        ),
    )


def test_build_recommendation_explanation_report_reduces_rows_in_source_order():
    report = build_paper_strategy_recommendation_explanation_report(
        _recommendation_report(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.source_config_version == "strategy-candidate-recommendation-v1"
    assert report.recommendation_count == 3
    assert report.recommend_count == 1
    assert report.watch_count == 1
    assert report.reject_count == 1
    assert [row.market_slug for row in report.explanation_rows] == [
        "market-recommend",
        "market-watch",
        "market-reject",
    ]
    assert [row.action for row in report.explanation_rows] == [
        "recommend",
        "watch",
        "reject",
    ]
    assert [row.selected_side for row in report.explanation_rows] == [
        "yes",
        "no",
        "none",
    ]
    assert [row.recommendation_score for row in report.explanation_rows] == [
        Decimal("0.9100"),
        Decimal("0.5200"),
        Decimal("0.0000"),
    ]
    assert [row.primary_reason_code for row in report.explanation_rows] == [
        "assessment_ready",
        "low_net_edge",
        "no_reason_code",
    ]
    assert [row.reason_codes for row in report.explanation_rows] == [
        ("assessment_ready", "liquidity_ok"),
        ("low_net_edge",),
        (),
    ]
    assert [row.explanation for row in report.explanation_rows] == [
        "recommend yes because assessment_ready (score 0.9100)",
        "watch no because low_net_edge (score 0.5200)",
        "reject none because no_reason_code (score 0.0000)",
    ]


def test_explanation_row_validates_primary_reason_matches_reason_codes():
    row = PaperStrategyRecommendationExplanationRow(
        market_slug="market-1",
        action="recommend",
        selected_side="yes",
        recommendation_score=Decimal("0.7000"),
        primary_reason_code="alpha",
        reason_codes=("alpha", "beta"),
        explanation="recommend yes because alpha (score 0.7000)",
    )

    assert row.primary_reason_code == "alpha"
    assert row.reason_codes == ("alpha", "beta")

    with pytest.raises(ValueError, match="primary_reason_code"):
        replace(row, primary_reason_code="beta")

    with pytest.raises(ValueError, match="primary_reason_code"):
        replace(row, reason_codes=())

    no_reason_row = replace(
        row,
        primary_reason_code="no_reason_code",
        reason_codes=(),
        explanation="recommend yes because no_reason_code (score 0.7000)",
    )
    assert no_reason_row.primary_reason_code == "no_reason_code"


def test_explanation_report_validates_direct_constructor_counts():
    rows = build_paper_strategy_recommendation_explanation_report(
        _recommendation_report(),
        generated_at=GENERATED_AT,
    ).explanation_rows

    report = PaperStrategyRecommendationExplanationReport(
        generated_at=GENERATED_AT,
        source_config_version="strategy-candidate-recommendation-v1",
        recommendation_count=3,
        recommend_count=1,
        watch_count=1,
        reject_count=1,
        explanation_rows=rows,
    )
    assert report.recommendation_count == 3

    with pytest.raises(ValueError, match="recommendation_count"):
        replace(report, recommendation_count=2)
    with pytest.raises(ValueError, match="recommend_count"):
        replace(report, recommend_count=2)
    with pytest.raises(ValueError, match="watch_count"):
        replace(report, watch_count=2)
    with pytest.raises(ValueError, match="reject_count"):
        replace(report, reject_count=2)


def test_build_rejects_wrong_source_type_and_false_source_flags():
    with pytest.raises(ValueError, match="PaperStrategyCandidateRecommendationReport"):
        build_paper_strategy_recommendation_explanation_report(
            object(),
            generated_at=GENERATED_AT,
        )

    subclass_report = _RecommendationReportSubclass(
        recommendation_rows=_recommendation_report().recommendation_rows,
    )
    with pytest.raises(ValueError, match="PaperStrategyCandidateRecommendationReport"):
        build_paper_strategy_recommendation_explanation_report(
            subclass_report,
            generated_at=GENERATED_AT,
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        source_report = _recommendation_report()
        object.__setattr__(source_report, flag_name, False)
        with pytest.raises(ValueError, match=f"recommendation_report {flag_name}"):
            build_paper_strategy_recommendation_explanation_report(
                source_report,
                generated_at=GENERATED_AT,
            )


def test_explanation_report_flags_are_readonly_and_constructor_validated():
    report = build_paper_strategy_recommendation_explanation_report(
        _recommendation_report(),
        generated_at=GENERATED_AT,
    )

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    with pytest.raises(FrozenInstanceError):
        report.readonly = False
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
