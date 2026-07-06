from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

import polymarket_alpha_lab.strategy_recommendation_manual_review_priority_rank_v2 as module
from polymarket_alpha_lab.strategy_recommendation_manual_review_priority_rank_v2 import (
    StrategyRecommendationManualReviewPriorityRankConfig,
    StrategyRecommendationManualReviewPriorityRankInput,
    build_strategy_recommendation_manual_review_priority_rank_report,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def recommendation(
    index: int,
    *,
    expected_value_after_cost: Decimal = Decimal("0.050000"),
    evidence_gap_score: Decimal = Decimal("0.000000"),
    resolution_ambiguity_score: Decimal = Decimal("0.000000"),
    market_urgency_score: Decimal = Decimal("0.000000"),
    liquidity_capacity_score: Decimal = Decimal("0.500000"),
    team_confidence_disagreement_score: Decimal = Decimal("0.000000"),
) -> StrategyRecommendationManualReviewPriorityRankInput:
    return StrategyRecommendationManualReviewPriorityRankInput(
        recommendation_id=f"recommendation-{index}",
        market_slug=f"market-{index}",
        selected_side="yes",
        expected_value_after_cost=expected_value_after_cost,
        evidence_gap_score=evidence_gap_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        market_urgency_score=market_urgency_score,
        liquidity_capacity_score=liquidity_capacity_score,
        team_confidence_disagreement_score=team_confidence_disagreement_score,
    )


def weighted_config() -> StrategyRecommendationManualReviewPriorityRankConfig:
    return StrategyRecommendationManualReviewPriorityRankConfig(
        config_version="phase1-test",
        expected_value_after_cost_weight=d("100.000000"),
        evidence_gap_weight=d("10.000000"),
        resolution_ambiguity_weight=d("10.000000"),
        market_urgency_weight=d("10.000000"),
        liquidity_capacity_weight=d("10.000000"),
        team_confidence_disagreement_weight=d("10.000000"),
        evidence_gap_reason_threshold=d("0.250000"),
        resolution_ambiguity_reason_threshold=d("0.250000"),
        market_urgency_reason_threshold=d("0.250000"),
        liquidity_capacity_reason_floor=d("0.500000"),
        team_confidence_disagreement_reason_threshold=d("0.250000"),
    )


def test_manual_review_priority_rank_uses_all_factors_and_deterministic_reasons():
    report = build_strategy_recommendation_manual_review_priority_rank_report(
        [
            recommendation(
                2,
                expected_value_after_cost=d("0.200000"),
                liquidity_capacity_score=d("0.200000"),
            ),
            recommendation(
                1,
                expected_value_after_cost=d("0.050000"),
                evidence_gap_score=d("0.800000"),
                resolution_ambiguity_score=d("0.400000"),
                market_urgency_score=d("0.900000"),
                liquidity_capacity_score=d("0.600000"),
                team_confidence_disagreement_score=d("0.300000"),
            ),
        ],
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        config=weighted_config(),
    )

    assert report.generated_at == datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    assert report.config_version == "phase1-test"
    assert report.recommendation_count == 2
    assert report.top_priority_score == d("35.000000")
    assert report.average_priority_score == d("28.500000")
    assert [row.recommendation_id for row in report.priority_ranks] == [
        "recommendation-1",
        "recommendation-2",
    ]

    top = report.priority_ranks[0]
    assert top.priority_rank == 1
    assert top.priority_score == d("35.000000")
    assert top.expected_value_after_cost == d("0.050000")
    assert top.reason_codes == (
        "positive_expected_value_after_cost",
        "evidence_gap",
        "resolution_ambiguity",
        "market_urgency",
        "liquidity_capacity_available",
        "team_confidence_disagreement",
    )

    assert report.priority_ranks[1].priority_score == d("22.000000")
    assert report.priority_ranks[1].reason_codes == (
        "positive_expected_value_after_cost",
        "liquidity_capacity_limited",
    )


def test_priority_rank_tie_breakers_are_stable_without_source_order():
    later_id = recommendation(20)
    earlier_id = replace(
        recommendation(10),
        recommendation_id="recommendation-01",
        market_slug="market-a",
    )

    forward = build_strategy_recommendation_manual_review_priority_rank_report(
        [later_id, earlier_id],
        generated_at=datetime(2026, 7, 6, tzinfo=UTC),
    )
    reverse = build_strategy_recommendation_manual_review_priority_rank_report(
        [earlier_id, later_id],
        generated_at=datetime(2026, 7, 6, tzinfo=UTC),
    )

    assert [row.recommendation_id for row in forward.priority_ranks] == [
        "recommendation-01",
        "recommendation-20",
    ]
    assert [row.recommendation_id for row in reverse.priority_ranks] == [
        "recommendation-01",
        "recommendation-20",
    ]
    assert [row.priority_rank for row in forward.priority_ranks] == [1, 2]


def test_negative_expected_value_and_low_capacity_still_rank_for_review_context():
    report = build_strategy_recommendation_manual_review_priority_rank_report(
        [
            recommendation(
                3,
                expected_value_after_cost=d("-0.010000"),
                evidence_gap_score=d("0.900000"),
                liquidity_capacity_score=d("0.100000"),
            ),
        ],
        generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        config=weighted_config(),
    )

    row = report.priority_ranks[0]
    assert row.priority_score == d("10.000000")
    assert row.reason_codes == (
        "nonpositive_expected_value_after_cost",
        "evidence_gap",
        "liquidity_capacity_limited",
    )


def test_dataclasses_are_frozen_decimal_only_and_validate_phase_flags():
    report = build_strategy_recommendation_manual_review_priority_rank_report(
        [recommendation(1)],
        generated_at=datetime(2026, 7, 6, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.priority_ranks[0].priority_rank = 99
    with pytest.raises(ValueError, match="priority_rank"):
        replace(report.priority_ranks[0], priority_rank=0)
    with pytest.raises(ValueError, match="recommendation_count"):
        replace(report, recommendation_count=0)
    with pytest.raises(ValueError, match="expected_value_after_cost"):
        recommendation(2, expected_value_after_cost=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_gap_score"):
        recommendation(2, evidence_gap_score=Decimal("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(recommendation(2), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_module_is_isolated_readonly_report_only_paper_only_surface():
    report = build_strategy_recommendation_manual_review_priority_rank_report(
        [recommendation(1)],
        generated_at=datetime(2026, 7, 6, tzinfo=UTC),
    )

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.priority_ranks[0].paper_only is True
    assert report.priority_ranks[0].report_only is True
    assert report.priority_ranks[0].readonly is True
    assert report.boundary_statement == (
        "Phase 1 paper-only manual-review priority rank for human review before "
        "paper execution; it is not an execution instruction."
    )

    tree = ast.parse(inspect.getsource(module))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {"__future__", "collections", "dataclasses", "datetime", "decimal"}
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write", "execute", "connect", "request", "post", "send"}
        for node in ast.walk(tree)
    )
