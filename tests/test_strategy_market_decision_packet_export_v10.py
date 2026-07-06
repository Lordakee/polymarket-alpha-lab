from __future__ import annotations

import ast
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_market_decision_packet_export_v10 import (
    StrategyMarketDecisionCostSummary,
    StrategyMarketDecisionEdgeSummary,
    StrategyMarketDecisionEvidenceSummary,
    StrategyMarketDecisionManualTicketSummary,
    StrategyMarketDecisionPacketExportV10,
    StrategyMarketDecisionRiskSummary,
    StrategyMarketDecisionTeamSummary,
    StrategyMarketDecisionTriageSummary,
    build_strategy_market_decision_packet_export_v10,
    strategy_market_decision_packet_export_v10_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def triage(**overrides: object) -> StrategyMarketDecisionTriageSummary:
    values = {
        "triage_status": "approved",
        "priority_score": d("0.820000"),
        "unresolved_issue_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionTriageSummary(**values)


def edge(**overrides: object) -> StrategyMarketDecisionEdgeSummary:
    values = {
        "probability_edge": d("0.090000"),
        "expected_value": d("0.075000"),
        "confidence_adjusted_edge": d("0.072000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionEdgeSummary(**values)


def cost(**overrides: object) -> StrategyMarketDecisionCostSummary:
    values = {
        "estimated_cost": d("0.025000"),
        "fee_drag": d("0.008000"),
        "liquidity_depth": d("250.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionCostSummary(**values)


def risk(**overrides: object) -> StrategyMarketDecisionRiskSummary:
    values = {
        "risk_score": d("0.220000"),
        "max_loss_estimate": d("0.080000"),
        "unresolved_risk_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionRiskSummary(**values)


def team(**overrides: object) -> StrategyMarketDecisionTeamSummary:
    values = {
        "team_id": "macro-research",
        "confidence_score": d("0.870000"),
        "capacity_score": d("0.760000"),
        "coverage_status": "met",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionTeamSummary(**values)


def evidence(**overrides: object) -> StrategyMarketDecisionEvidenceSummary:
    values = {
        "source_count": d("4.000000"),
        "evidence_quality_score": d("0.820000"),
        "unresolved_evidence_gaps": d("0.000000"),
        "source_quorum_status": "met",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionEvidenceSummary(**values)


def ticket(**overrides: object) -> StrategyMarketDecisionManualTicketSummary:
    values = {
        "manual_review_status": "approved",
        "ticket_status": "closed",
        "open_ticket_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return StrategyMarketDecisionManualTicketSummary(**values)


def packet(
    *,
    market_id: str = "market-alpha",
    triage_summary: StrategyMarketDecisionTriageSummary | None = None,
    edge_summary: StrategyMarketDecisionEdgeSummary | None = None,
    cost_summary: StrategyMarketDecisionCostSummary | None = None,
    risk_summary: StrategyMarketDecisionRiskSummary | None = None,
    team_summary: StrategyMarketDecisionTeamSummary | None = None,
    evidence_summary: StrategyMarketDecisionEvidenceSummary | None = None,
    manual_ticket_summary: StrategyMarketDecisionManualTicketSummary | None = None,
) -> StrategyMarketDecisionPacketExportV10:
    return build_strategy_market_decision_packet_export_v10(
        market_id=market_id,
        triage_summary=triage_summary or triage(),
        edge_summary=edge_summary or edge(),
        cost_summary=cost_summary or cost(),
        risk_summary=risk_summary or risk(),
        team_summary=team_summary or team(),
        evidence_summary=evidence_summary or evidence(),
        manual_ticket_summary=manual_ticket_summary or ticket(),
    )


def test_ready_packet_generates_readonly_decision_payload() -> None:
    report = packet()

    assert is_dataclass(report)
    assert report.packet_status == "ready"
    assert report.decision_readiness == "decision_ready"
    assert report.blocking_reasons == ()
    assert report.export_sections == (
        "market_overview",
        "triage_conclusion",
        "edge_assessment",
        "cost_liquidity_assessment",
        "risk_review",
        "team_review",
        "evidence_review",
        "manual_ticket_review",
        "final_readonly_decision",
    )
    assert report.reason_codes == (
        "triage_approved",
        "edge_above_floor",
        "costs_within_expected_value",
        "risk_within_threshold",
        "team_coverage_met",
        "evidence_quorum_met",
        "manual_ticket_clear",
        "readonly_export_ready",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = strategy_market_decision_packet_export_v10_payload(report)
    assert payload == report.payload
    assert payload["packet_status"] == "ready"
    assert payload["decision_readiness"] == "decision_ready"
    assert payload["edge_summary"]["confidence_adjusted_edge"] == "0.072000"
    assert payload["cost_summary"]["liquidity_depth"] == "250.000000"
    assert payload["blocking_reasons"] == []
    assert not _contains_float(payload)
    json.dumps(payload, sort_keys=True)


def test_review_and_blocked_paths_explain_readiness_reasons() -> None:
    review_report = packet(
        edge_summary=edge(confidence_adjusted_edge=d("0.005000")),
        risk_summary=risk(unresolved_risk_count=d("1.000000")),
        team_summary=team(coverage_status="partial"),
        evidence_summary=evidence(
            source_quorum_status="partial",
            unresolved_evidence_gaps=d("1.000000"),
        ),
        manual_ticket_summary=ticket(
            manual_review_status="pending",
            ticket_status="open",
            open_ticket_count=d("1.000000"),
        ),
    )
    blocked_report = packet(
        triage_summary=triage(triage_status="blocked"),
        edge_summary=edge(expected_value=d("-0.005000"), confidence_adjusted_edge=d("-0.006000")),
        cost_summary=cost(estimated_cost=d("0.090000"), liquidity_depth=d("25.000000")),
        risk_summary=risk(risk_score=d("0.750000")),
        team_summary=team(coverage_status="blocked", capacity_score=d("0.300000")),
        evidence_summary=evidence(
            source_count=d("1.000000"),
            evidence_quality_score=d("0.500000"),
            source_quorum_status="missing",
        ),
        manual_ticket_summary=ticket(
            manual_review_status="rejected",
            ticket_status="blocked",
            open_ticket_count=d("2.000000"),
        ),
    )

    assert review_report.packet_status == "review_required"
    assert review_report.decision_readiness == "manual_review_required"
    assert review_report.blocking_reasons == (
        "confidence_adjusted_edge_watch",
        "unresolved_risk_review",
        "team_coverage_partial",
        "source_quorum_partial",
        "evidence_gaps_present",
        "manual_review_pending",
        "manual_ticket_open",
    )
    assert review_report.reason_codes == review_report.blocking_reasons

    assert blocked_report.packet_status == "blocked"
    assert blocked_report.decision_readiness == "not_ready"
    assert blocked_report.blocking_reasons == (
        "triage_blocked",
        "nonpositive_expected_value",
        "cost_exceeds_expected_value",
        "liquidity_below_floor",
        "risk_above_threshold",
        "team_capacity_below_floor",
        "team_coverage_blocked",
        "insufficient_source_count",
        "evidence_quality_below_floor",
        "source_quorum_missing",
        "manual_review_rejected",
        "manual_ticket_blocked",
    )
    assert blocked_report.reason_codes == blocked_report.blocking_reasons
    assert blocked_report.payload["blocking_reasons"] == list(blocked_report.blocking_reasons)


def test_frozen_dataclasses_decimal_only_and_exact_types() -> None:
    report = packet()

    for value in (
        triage(),
        edge(),
        cost(),
        risk(),
        team(),
        evidence(),
        ticket(),
        report,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="priority_score"):
        triage(priority_score=_DecimalSubclass("0.820000"))
    with pytest.raises(ValueError, match="expected_value"):
        edge(expected_value=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="estimated_cost"):
        cost(estimated_cost=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="risk_score"):
        risk(risk_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_count"):
        evidence(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="open_ticket_count"):
        ticket(open_ticket_count=d("-1.000000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="payload"):
        replace(report, payload={})


def test_validation_rejects_unsafe_surface_and_payload_downgrades() -> None:
    with pytest.raises(ValueError, match="market_id"):
        packet(market_id=" market-alpha ")
    with pytest.raises(ValueError, match="triage_summary"):
        build_strategy_market_decision_packet_export_v10(
            market_id="market-alpha",
            triage_summary=object(),  # type: ignore[arg-type]
            edge_summary=edge(),
            cost_summary=cost(),
            risk_summary=risk(),
            team_summary=team(),
            evidence_summary=evidence(),
            manual_ticket_summary=ticket(),
        )
    with pytest.raises(ValueError, match="triage_status"):
        triage(triage_status="done")
    with pytest.raises(ValueError, match="paper_only"):
        team(paper_only=False)
    with pytest.raises(ValueError, match="unsafe"):
        packet(market_id="market-wallet")
    with pytest.raises(ValueError, match="unsafe"):
        packet(team_summary=team(team_id="private key unavailable"))
    with pytest.raises(ValueError, match="readonly"):
        strategy_market_decision_packet_export_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        strategy_market_decision_packet_export_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "score": 0.1},
        )
    with pytest.raises(ValueError, match="Decimal"):
        strategy_market_decision_packet_export_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "count": 1},
        )


def test_static_module_surface_is_readonly_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_market_decision_packet_export_v10.py",
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
        "psycopg",
        "supabase",
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
