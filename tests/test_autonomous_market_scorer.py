"""Tests for autonomous market scorer module."""

from __future__ import annotations

from decimal import Decimal

from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab.autonomous_market_scorer import (
    AutonomousMarketScorerConfig,
    AutonomousMarketScorerReport,
    AutonomousMarketScoreRow,
    build_autonomous_market_scorer_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


def _pass_gate_report() -> PaperAutonomousScreeningDecisionSupportGateReport:
    return _gate_report(
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        gate_status="pass",
    )


def _blocked_gate_report() -> PaperAutonomousScreeningDecisionSupportGateReport:
    return _gate_report(
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        gate_status="blocked",
    )


def _watch_gate_report() -> PaperAutonomousScreeningDecisionSupportGateReport:
    return _gate_report(
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        gate_status="watch",
    )


def _market_data_entry(
    *,
    condition_id: str,
    market_slug: str,
    question: str,
    side: str,
    confidence_score: Decimal,
    liquidity_score: Decimal,
    spread_score: Decimal,
    edge_score: Decimal,
    cost_score: Decimal,
    risk_score: Decimal,
    recommended_notional: Decimal | None = None,
    selection_status: str | None = None,
    reason_codes: tuple[str, ...] = (),
    use_side_field: bool = False,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "condition_id": condition_id,
        "market_slug": market_slug,
        "question": question,
        "confidence_score": confidence_score,
        "liquidity_score": liquidity_score,
        "spread_score": spread_score,
        "edge_score": edge_score,
        "cost_score": cost_score,
        "risk_score": risk_score,
        "reason_codes": reason_codes,
    }
    if use_side_field:
        entry["side"] = side
    else:
        entry["scoring_side"] = side
    if recommended_notional is not None:
        entry["recommended_notional"] = recommended_notional
    if selection_status is not None:
        entry["selection_status"] = selection_status
    return entry


def test_scorer_blocked_gate_returns_blocked_report() -> None:
    gate = _blocked_gate_report()
    report = build_autonomous_market_scorer_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(report, AutonomousMarketScorerReport)
    assert report.gate_status == "blocked"
    assert report.markets_scored == 0
    assert report.markets_blocked == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_scorer_watch_gate_returns_watch_report() -> None:
    gate = _watch_gate_report()
    report = build_autonomous_market_scorer_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.gate_status == "watch"
    assert report.markets_skipped == 1


def test_scorer_pass_gate_returns_pass_report() -> None:
    gate = _pass_gate_report()
    report = build_autonomous_market_scorer_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(report, AutonomousMarketScorerReport)
    assert report.gate_status in ("pass", "watch")
    assert report.generated_at.tzinfo is not None
    assert report.paper_only is True


def test_scorer_pass_gate_scores_market_candidates_in_deterministic_order() -> None:
    gate = _pass_gate_report()
    report = build_autonomous_market_scorer_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        market_data=(
            _market_data_entry(
                condition_id="condition-alpha",
                market_slug="alpha-market",
                question="Will alpha resolve?",
                side="yes",
                confidence_score=Decimal("0.900000"),
                liquidity_score=Decimal("0.800000"),
                spread_score=Decimal("0.700000"),
                edge_score=Decimal("0.600000"),
                cost_score=Decimal("0.100000"),
                risk_score=Decimal("0.200000"),
                recommended_notional=Decimal("12.000000"),
                selection_status="ready",
                reason_codes=("alpha_reason",),
            ),
            _market_data_entry(
                condition_id="condition-beta",
                market_slug="beta-market",
                question="Will beta resolve?",
                side="no",
                confidence_score=Decimal("0.900000"),
                liquidity_score=Decimal("0.800000"),
                spread_score=Decimal("0.700000"),
                edge_score=Decimal("0.600000"),
                cost_score=Decimal("0.100000"),
                risk_score=Decimal("0.200000"),
                recommended_notional=Decimal("12.000000"),
                selection_status="recommend",
                reason_codes=("beta_reason",),
            ),
            _market_data_entry(
                condition_id="condition-delta",
                market_slug="delta-market",
                question="Will delta resolve?",
                side="yes",
                confidence_score=Decimal("0.900000"),
                liquidity_score=Decimal("0.800000"),
                spread_score=Decimal("0.700000"),
                edge_score=Decimal("0.600000"),
                cost_score=Decimal("0.100000"),
                risk_score=Decimal("0.200000"),
                selection_status="watch",
                reason_codes=("delta_reason",),
            ),
            _market_data_entry(
                condition_id="condition-gamma",
                market_slug="gamma-market",
                question="Will gamma resolve?",
                side="no",
                confidence_score=Decimal("0.900000"),
                liquidity_score=Decimal("0.800000"),
                spread_score=Decimal("0.700000"),
                edge_score=Decimal("0.600000"),
                cost_score=Decimal("0.100000"),
                risk_score=Decimal("0.200000"),
                selection_status="reject",
                reason_codes=("gamma_reason",),
            ),
        ),
    )

    assert report.gate_status == "pass"
    assert report.markets_scored == 2
    assert report.markets_skipped == 1
    assert report.markets_blocked == 1
    assert [row.market_slug for row in report.score_rows] == [
        "alpha-market",
        "beta-market",
        "delta-market",
        "gamma-market",
    ]
    assert [row.score_status for row in report.score_rows] == [
        "scored",
        "scored",
        "skipped",
        "blocked",
    ]
    assert report.score_rows[0].total_score == Decimal("0.785000")
    assert report.score_rows[1].total_score == Decimal("0.785000")
    assert report.score_rows[2].total_score == Decimal("0.000000")
    assert report.score_rows[3].total_score == Decimal("0.000000")
    assert report.score_rows[0].scoring_side == "yes"
    assert report.score_rows[1].scoring_side == "no"
    assert report.score_rows[2].scoring_side == "yes"
    assert report.score_rows[3].scoring_side == "no"
    assert report.reason_codes == (
        "alpha_reason",
        "beta_reason",
        "delta_reason",
        "gamma_reason",
    )


def test_scorer_pass_gate_caps_market_candidates_after_sorting() -> None:
    gate = _pass_gate_report()
    report = build_autonomous_market_scorer_report(
        gate_report=gate,
        config=AutonomousMarketScorerConfig(max_markets=2),
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        market_data=(
            _market_data_entry(
                condition_id="condition-alpha",
                market_slug="alpha-market",
                question="Will alpha resolve?",
                side="yes",
                confidence_score=Decimal("0.900000"),
                liquidity_score=Decimal("0.800000"),
                spread_score=Decimal("0.700000"),
                edge_score=Decimal("0.600000"),
                cost_score=Decimal("0.100000"),
                risk_score=Decimal("0.200000"),
                reason_codes=("alpha_reason",),
            ),
            _market_data_entry(
                condition_id="condition-beta",
                market_slug="beta-market",
                question="Will beta resolve?",
                side="yes",
                confidence_score=Decimal("0.900000"),
                liquidity_score=Decimal("0.800000"),
                spread_score=Decimal("0.700000"),
                edge_score=Decimal("0.600000"),
                cost_score=Decimal("0.100000"),
                risk_score=Decimal("0.200000"),
                reason_codes=("beta_reason",),
            ),
            _market_data_entry(
                condition_id="condition-gamma",
                market_slug="gamma-market",
                question="Will gamma resolve?",
                side="yes",
                confidence_score=Decimal("0.800000"),
                liquidity_score=Decimal("0.700000"),
                spread_score=Decimal("0.600000"),
                edge_score=Decimal("0.500000"),
                cost_score=Decimal("0.200000"),
                risk_score=Decimal("0.300000"),
                reason_codes=("gamma_reason",),
            ),
        ),
    )

    assert [row.market_slug for row in report.score_rows] == [
        "alpha-market",
        "beta-market",
    ]
    assert report.markets_scored == 2
    assert report.markets_skipped == 0
    assert report.markets_blocked == 0
    assert report.reason_codes == ("alpha_reason", "beta_reason")


def test_scorer_pass_gate_rejects_float_market_data_values() -> None:
    gate = _pass_gate_report()
    with pytest.raises(ValueError, match="must be a Decimal"):
        build_autonomous_market_scorer_report(
            gate_report=gate,
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
            market_data=(
                {
                    "condition_id": "condition-alpha",
                    "market_slug": "alpha-market",
                    "question": "Will alpha resolve?",
                    "scoring_side": "yes",
                    "confidence_score": 0.9,
                    "liquidity_score": Decimal("0.800000"),
                    "spread_score": Decimal("0.700000"),
                    "edge_score": Decimal("0.600000"),
                    "cost_score": Decimal("0.100000"),
                    "risk_score": Decimal("0.200000"),
                },
            ),
        )


def test_scorer_pass_gate_rejects_unsafe_market_data_flags() -> None:
    gate = _pass_gate_report()
    entry = _market_data_entry(
        condition_id="condition-alpha",
        market_slug="alpha-market",
        question="Will alpha resolve?",
        side="yes",
        confidence_score=Decimal("0.900000"),
        liquidity_score=Decimal("0.800000"),
        spread_score=Decimal("0.700000"),
        edge_score=Decimal("0.600000"),
        cost_score=Decimal("0.100000"),
        risk_score=Decimal("0.200000"),
    )
    entry["paper_only"] = False

    with pytest.raises(ValueError, match="paper_only must be True"):
        build_autonomous_market_scorer_report(
            gate_report=gate,
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
            market_data=(entry,),
        )


def test_scorer_rejects_naive_generated_at() -> None:
    gate = _pass_gate_report()
    with pytest.raises(ValueError, match="timezone-aware"):
        build_autonomous_market_scorer_report(
            gate_report=gate,
            generated_at=datetime(2026, 6, 25),
        )


def test_scorer_rejects_wrong_gate_type() -> None:
    with pytest.raises(ValueError, match="PaperAutonomousScreeningDecisionSupportGateReport"):
        build_autonomous_market_scorer_report(
            gate_report="not_a_report",
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        )


def test_scorer_config_defaults() -> None:
    config = AutonomousMarketScorerConfig()
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert config.max_markets == 10


def test_scorer_config_rejects_subclass() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadConfig(AutonomousMarketScorerConfig):
            pass


def test_score_row_frozen() -> None:
    row = AutonomousMarketScoreRow(
        condition_id="test",
        market_slug="test-slug",
        question="Test?",
        scoring_side="yes",
        confidence_score=Decimal("0.800000"),
        liquidity_score=Decimal("0.700000"),
        spread_score=Decimal("0.600000"),
        edge_score=Decimal("0.500000"),
        cost_score=Decimal("0.900000"),
        risk_score=Decimal("0.300000"),
        total_score=Decimal("0.650000"),
        score_status="scored",
        recommended_notional=Decimal("10.000000"),
        estimated_edge=Decimal("0.050000"),
        reason_codes=("test_reason",),
    )
    assert row.score_status == "scored"
    assert row.total_score == Decimal("0.650000")
