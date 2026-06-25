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
