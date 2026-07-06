from __future__ import annotations

import ast
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_investment_decision_memo_v10 import (
    StrategyInvestmentDecisionCostSummary,
    StrategyInvestmentDecisionEdgeSummary,
    StrategyInvestmentDecisionEvidenceGap,
    StrategyInvestmentDecisionForecastSummary,
    StrategyInvestmentDecisionMemoV10,
    StrategyInvestmentDecisionRiskSummary,
    StrategyInvestmentDecisionTeamAssignment,
    build_strategy_investment_decision_memo_v10,
    strategy_investment_decision_memo_v10_payload,
)


ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def assignment(**overrides: object) -> StrategyInvestmentDecisionTeamAssignment:
    values = {
        "team_id": "macro-research",
        "lead_analyst": "analyst_alpha",
        "confidence_score": d("0.850000"),
        "coverage_score": d("0.900000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyInvestmentDecisionTeamAssignment(**values)


def forecast(**overrides: object) -> StrategyInvestmentDecisionForecastSummary:
    values = {
        "forecast_probability": d("0.640000"),
        "market_probability": d("0.540000"),
        "confidence_score": d("0.780000"),
        "sample_count": d("8.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyInvestmentDecisionForecastSummary(**values)


def edge(**overrides: object) -> StrategyInvestmentDecisionEdgeSummary:
    values = {
        "probability_edge": d("0.100000"),
        "expected_value": d("0.080000"),
        "confidence_adjusted_edge": d("0.078000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyInvestmentDecisionEdgeSummary(**values)


def cost(**overrides: object) -> StrategyInvestmentDecisionCostSummary:
    values = {
        "estimated_cost": d("0.030000"),
        "fee_drag": d("0.010000"),
        "liquidity_depth": d("250.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyInvestmentDecisionCostSummary(**values)


def risk(**overrides: object) -> StrategyInvestmentDecisionRiskSummary:
    values = {
        "risk_score": d("0.180000"),
        "max_loss_estimate": d("0.070000"),
        "correlation_risk": d("0.120000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyInvestmentDecisionRiskSummary(**values)


def gap(**overrides: object) -> StrategyInvestmentDecisionEvidenceGap:
    values = {
        "gap_code": "resolution_source_missing",
        "severity": d("0.200000"),
        "description": "Need second independent resolution source.",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyInvestmentDecisionEvidenceGap(**values)


def memo(
    *,
    market_id: str = "market-alpha",
    team_assignment: StrategyInvestmentDecisionTeamAssignment | None = None,
    forecast_summary: StrategyInvestmentDecisionForecastSummary | None = None,
    edge_summary: StrategyInvestmentDecisionEdgeSummary | None = None,
    cost_summary: StrategyInvestmentDecisionCostSummary | None = None,
    risk_summary: StrategyInvestmentDecisionRiskSummary | None = None,
    evidence_gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...] = (),
    human_review_status: str = "approved",
) -> StrategyInvestmentDecisionMemoV10:
    return build_strategy_investment_decision_memo_v10(
        market_id=market_id,
        team_assignment=team_assignment or assignment(),
        forecast_summary=forecast_summary or forecast(),
        edge_summary=edge_summary or edge(),
        cost_summary=cost_summary or cost(),
        risk_summary=risk_summary or risk(),
        evidence_gaps=evidence_gaps,
        human_review_status=human_review_status,
    )


def test_approved_market_generates_ready_readonly_payload() -> None:
    report = memo()

    assert is_dataclass(report)
    assert report.memo_status == "ready"
    assert report.decision_label == "approve_for_paper_research"
    assert report.approval_blockers == ()
    assert report.reason_codes == (
        "human_review_approved",
        "positive_confidence_adjusted_edge",
        "costs_within_expected_value",
        "risk_within_threshold",
        "no_evidence_gaps",
    )
    assert report.summary_bullets == (
        "market-alpha: approve_for_paper_research for macro-research.",
        "Forecast probability 0.640000 vs market probability 0.540000.",
        "Confidence-adjusted edge 0.078000 with expected value 0.080000.",
        "Estimated cost 0.030000 and risk score 0.180000.",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = strategy_investment_decision_memo_v10_payload(report)
    assert payload == report.payload
    assert payload["memo_status"] == "ready"
    assert payload["decision_label"] == "approve_for_paper_research"
    assert payload["team_assignment"]["confidence_score"] == "0.850000"
    assert payload["forecast_summary"]["sample_count"] == "8.000000"
    assert payload["approval_blockers"] == []
    assert not _contains_float(payload)
    json.dumps(payload, sort_keys=True)


def test_review_and_blocked_paths_explain_approval_blockers() -> None:
    review_report = memo(
        edge_summary=edge(
            probability_edge=d("0.010000"),
            expected_value=d("0.005000"),
            confidence_adjusted_edge=d("0.004000"),
        ),
        cost_summary=cost(estimated_cost=d("0.002000")),
        evidence_gaps=(gap(),),
        human_review_status="pending",
    )
    blocked_report = memo(
        forecast_summary=forecast(sample_count=d("2.000000")),
        edge_summary=edge(
            probability_edge=d("-0.010000"),
            expected_value=d("-0.005000"),
            confidence_adjusted_edge=d("-0.006000"),
        ),
        cost_summary=cost(estimated_cost=d("0.090000"), liquidity_depth=d("25.000000")),
        risk_summary=risk(risk_score=d("0.750000")),
        evidence_gaps=(gap(severity=d("0.900000")),),
        human_review_status="rejected",
    )

    assert review_report.memo_status == "review_required"
    assert review_report.decision_label == "defer_pending_review"
    assert review_report.approval_blockers == (
        "human_review_pending",
        "confidence_adjusted_edge_watch",
        "evidence_gaps_present",
    )
    assert review_report.reason_codes == (
        "human_review_pending",
        "confidence_adjusted_edge_watch",
        "evidence_gaps_present",
    )

    assert blocked_report.memo_status == "blocked"
    assert blocked_report.decision_label == "do_not_approve"
    assert blocked_report.approval_blockers == (
        "human_review_rejected",
        "insufficient_forecast_sample",
        "negative_expected_value",
        "cost_exceeds_expected_value",
        "liquidity_below_floor",
        "risk_above_threshold",
        "critical_evidence_gap",
    )
    assert blocked_report.reason_codes == blocked_report.approval_blockers
    assert blocked_report.payload["approval_blockers"] == list(
        blocked_report.approval_blockers,
    )


def test_frozen_dataclasses_decimal_only_and_exact_types() -> None:
    report = memo(evidence_gaps=(gap(),), human_review_status="pending")

    for value in (
        assignment(),
        forecast(),
        edge(),
        cost(),
        risk(),
        gap(),
        report,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="confidence_score"):
        assignment(confidence_score=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="forecast_probability"):
        forecast(forecast_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="expected_value"):
        edge(expected_value=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_depth"):
        cost(liquidity_depth=d("-0.000001"))
    with pytest.raises(ValueError, match="risk_score"):
        risk(risk_score=d("1.000001"))
    with pytest.raises(ValueError, match="severity"):
        gap(severity=d("1.000001"))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="payload"):
        replace(report, payload={})


def test_validation_rejects_unsafe_surface_and_payload_downgrades() -> None:
    with pytest.raises(ValueError, match="market_id"):
        memo(market_id=" market-alpha ")
    with pytest.raises(ValueError, match="team_assignment"):
        build_strategy_investment_decision_memo_v10(
            market_id="market-alpha",
            team_assignment=object(),  # type: ignore[arg-type]
            forecast_summary=forecast(),
            edge_summary=edge(),
            cost_summary=cost(),
            risk_summary=risk(),
            evidence_gaps=(),
            human_review_status="approved",
        )
    with pytest.raises(ValueError, match="human_review_status"):
        memo(human_review_status="done")
    with pytest.raises(ValueError, match="paper_only"):
        assignment(paper_only=False)
    with pytest.raises(ValueError, match="evidence_gaps"):
        memo(evidence_gaps=(object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsafe"):
        memo(market_id="market-wallet")
    with pytest.raises(ValueError, match="unsafe"):
        gap(description="private key is unavailable")
    with pytest.raises(ValueError, match="readonly"):
        strategy_investment_decision_memo_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        strategy_investment_decision_memo_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "score": 0.1},
        )


def test_static_module_surface_is_readonly_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_investment_decision_memo_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "private_key",
        "live_trading",
        "place_order",
        "signed_payload",
        "requests.",
        "urllib",
        "sqlite",
        "open(",
    ):
        assert forbidden not in lowered
    assert not re.search(r"\b(auth|broker|signing)\b", lowered)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
