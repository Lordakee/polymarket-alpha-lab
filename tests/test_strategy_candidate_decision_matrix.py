from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_candidate_decision_matrix import (
    PaperStrategyCandidateDecisionInput,
    PaperStrategyCandidateDecisionMatrixConfig,
    PaperStrategyCandidateDecisionMatrixReport,
    PaperStrategyCandidateDecisionRow,
    build_paper_strategy_candidate_decision_matrix_report,
)


GENERATED_AT = datetime(2026, 7, 6, 16, 30, tzinfo=timezone(timedelta(hours=2)))
GENERATED_AT_UTC = datetime(2026, 7, 6, 14, 30, tzinfo=UTC)
CONFIG_VERSION = "strategy-candidate-decision-matrix-v1"


def _config(**overrides):
    values = {
        "config_version": CONFIG_VERSION,
        "min_candidate_score": Decimal("0.700000"),
        "min_research_score": Decimal("0.450000"),
        "min_net_edge_per_share": Decimal("0.030000"),
        "min_information_quality_score": Decimal("0.650000"),
        "min_liquidity_score": Decimal("0.500000"),
        "max_total_cost_per_share": Decimal("0.040000"),
        "max_resolution_risk_score": Decimal("0.350000"),
        "min_team_memory_score": Decimal("0.400000"),
        "edge_weight": Decimal("0.300000"),
        "information_quality_weight": Decimal("0.250000"),
        "cost_weight": Decimal("0.150000"),
        "liquidity_weight": Decimal("0.120000"),
        "resolution_risk_weight": Decimal("0.100000"),
        "team_memory_weight": Decimal("0.080000"),
    }
    values.update(overrides)
    return PaperStrategyCandidateDecisionMatrixConfig(**values)


def _candidate(
    market_slug: str,
    *,
    question: str | None = None,
    team_id: str = "macro_team",
    category: str = "macro",
    forecast_probability: Decimal = Decimal("0.650000"),
    market_probability: Decimal = Decimal("0.560000"),
    net_edge_per_share: Decimal = Decimal("0.090000"),
    total_cost_per_share: Decimal = Decimal("0.020000"),
    liquidity_score: Decimal = Decimal("0.800000"),
    information_quality_score: Decimal = Decimal("0.850000"),
    source_count: Decimal = Decimal("4"),
    freshness_minutes: Decimal = Decimal("20"),
    resolution_risk_score: Decimal = Decimal("0.120000"),
    team_memory_score: Decimal = Decimal("0.700000"),
    calibration_score: Decimal = Decimal("0.720000"),
    reason_codes: tuple[str, ...] = ("positive_edge",),
    evidence_gap_codes: tuple[str, ...] = (),
) -> PaperStrategyCandidateDecisionInput:
    return PaperStrategyCandidateDecisionInput(
        market_slug=market_slug,
        question=question or f"Will {market_slug} resolve Yes?",
        team_id=team_id,
        category=category,
        forecast_probability=forecast_probability,
        market_probability=market_probability,
        net_edge_per_share=net_edge_per_share,
        total_cost_per_share=total_cost_per_share,
        liquidity_score=liquidity_score,
        information_quality_score=information_quality_score,
        source_count=source_count,
        freshness_minutes=freshness_minutes,
        resolution_risk_score=resolution_risk_score,
        team_memory_score=team_memory_score,
        calibration_score=calibration_score,
        reason_codes=reason_codes,
        evidence_gap_codes=evidence_gap_codes,
    )


def _report(*rows: PaperStrategyCandidateDecisionInput):
    return build_paper_strategy_candidate_decision_matrix_report(
        rows,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_decision_matrix_ranks_candidate_actions_deterministically():
    report = _report(
        _candidate(
            "research-me",
            net_edge_per_share=Decimal("0.060000"),
            information_quality_score=Decimal("0.600000"),
            reason_codes=("good_edge",),
        ),
        _candidate(
            "alpha-candidate",
            net_edge_per_share=Decimal("0.090000"),
            information_quality_score=Decimal("0.850000"),
            team_memory_score=Decimal("0.700000"),
            reason_codes=("good_edge", "fresh_sources"),
        ),
        _candidate(
            "beta-candidate",
            net_edge_per_share=Decimal("0.090000"),
            information_quality_score=Decimal("0.850000"),
            team_memory_score=Decimal("0.700000"),
            reason_codes=("fresh_sources", "good_edge"),
        ),
        _candidate(
            "blocked-cost",
            net_edge_per_share=Decimal("0.025000"),
            total_cost_per_share=Decimal("0.050000"),
        ),
    )

    assert isinstance(report, PaperStrategyCandidateDecisionMatrixReport)
    assert isinstance(report.decision_rows[0], PaperStrategyCandidateDecisionRow)
    assert report.generated_at == GENERATED_AT_UTC
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == 4
    assert report.select_count == 2
    assert report.research_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.decision_rows) == (
        "alpha-candidate",
        "beta-candidate",
        "research-me",
        "blocked-cost",
    )
    assert tuple(row.rank for row in report.decision_rows) == (
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
        Decimal("4"),
    )
    assert tuple(row.decision_status for row in report.decision_rows) == (
        "candidate",
        "candidate",
        "research",
        "blocked",
    )
    assert report.decision_rows[0].action == "select_for_manual_review"
    assert report.decision_rows[2].action == "refresh_information"
    assert report.decision_rows[3].action == "reject"
    assert report.decision_rows[0].composite_score == Decimal("0.815000")
    assert report.decision_rows[0].cost_adjusted_edge == Decimal("0.070000")
    assert report.decision_rows[0].reason_codes == (
        "decision_candidate",
        "fresh_sources",
        "good_edge",
    )
    assert "decision_research" in report.decision_rows[2].reason_codes
    assert "information_quality_below_candidate_threshold" in report.decision_rows[2].reason_codes
    assert "cost_exceeds_limit" in report.decision_rows[3].reason_codes
    assert "edge_below_minimum" in report.decision_rows[3].reason_codes


def test_decision_matrix_blocks_stale_or_insufficient_sources_even_with_edge():
    report = _report(
        _candidate(
            "stale-high-edge",
            net_edge_per_share=Decimal("0.150000"),
            information_quality_score=Decimal("0.620000"),
            source_count=Decimal("1"),
            freshness_minutes=Decimal("240"),
            reason_codes=("headline_signal",),
            evidence_gap_codes=("missing_primary_source",),
        ),
    )

    row = report.decision_rows[0]
    assert row.decision_status == "blocked"
    assert row.action == "reject"
    assert row.composite_score == Decimal("0.702000")
    assert row.reason_codes == (
        "decision_blocked",
        "headline_signal",
        "missing_primary_source",
        "source_count_below_minimum",
        "stale_information",
    )
    assert report.reason_code_counts == (
        ("decision_blocked", Decimal("1")),
        ("headline_signal", Decimal("1")),
        ("missing_primary_source", Decimal("1")),
        ("source_count_below_minimum", Decimal("1")),
        ("stale_information", Decimal("1")),
    )


def test_decision_matrix_blocks_when_costs_erase_forecast_edge():
    report = _report(
        _candidate(
            "costly-market",
            net_edge_per_share=Decimal("0.055000"),
            total_cost_per_share=Decimal("0.060000"),
        ),
    )

    row = report.decision_rows[0]
    assert row.decision_status == "blocked"
    assert row.action == "reject"
    assert row.cost_adjusted_edge == Decimal("-0.005000")
    assert "costs_erase_edge" in row.reason_codes
    assert "cost_exceeds_limit" in row.reason_codes


def test_decision_matrix_clamps_valid_degenerate_composite_score_to_zero():
    report = _report(
        _candidate(
            "all-adverse-inputs",
            forecast_probability=Decimal("0.000000"),
            market_probability=Decimal("1.000000"),
            net_edge_per_share=Decimal("0.000000"),
            total_cost_per_share=Decimal("0.050000"),
            liquidity_score=Decimal("0.000000"),
            information_quality_score=Decimal("0.000000"),
            source_count=Decimal("1"),
            freshness_minutes=Decimal("240"),
            resolution_risk_score=Decimal("1.000000"),
            team_memory_score=Decimal("0.000000"),
            calibration_score=Decimal("0.000000"),
            reason_codes=(),
        ),
    )

    row = report.decision_rows[0]
    assert row.decision_status == "blocked"
    assert row.action == "reject"
    assert row.composite_score == Decimal("0.000000")
    assert "costs_erase_edge" in row.reason_codes
    assert "resolution_risk_above_limit" in row.reason_codes


def test_decision_matrix_resolution_risk_and_team_memory_downgrade_to_research():
    report = _report(
        _candidate(
            "messy-resolution",
            resolution_risk_score=Decimal("0.340000"),
            team_memory_score=Decimal("0.390000"),
            calibration_score=Decimal("0.350000"),
        ),
    )

    row = report.decision_rows[0]
    assert row.decision_status == "research"
    assert row.action == "escalate_specialist_review"
    assert "team_memory_below_minimum" in row.reason_codes
    assert "calibration_below_minimum" in row.reason_codes
    assert "resolution_risk_watch" in row.reason_codes


def test_decision_matrix_rejects_float_inputs_and_preserves_frozen_tuples():
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        _candidate("floaty", forecast_probability=0.55)  # type: ignore[arg-type]

    report = _report(_candidate("immutable-row"))
    row = report.decision_rows[0]

    assert isinstance(report.decision_rows, tuple)
    assert isinstance(row.reason_codes, tuple)
    with pytest.raises(FrozenInstanceError):
        row.action = "watch"  # type: ignore[misc]


def test_decision_matrix_requires_paper_only_report_boundaries():
    with pytest.raises(ValueError, match="paper_only must be True"):
        PaperStrategyCandidateDecisionMatrixReport(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            candidate_count=Decimal("0"),
            select_count=Decimal("0"),
            research_count=Decimal("0"),
            watch_count=Decimal("0"),
            blocked_count=Decimal("0"),
            decision_rows=(),
            reason_code_counts=(),
            paper_only=False,
        )
