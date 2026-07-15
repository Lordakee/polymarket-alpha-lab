from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

import polymarket_alpha_lab.manual_execution_decision_ticket_report as ticket_report_module
from polymarket_alpha_lab.manual_execution_decision_ticket_report import (
    DEFAULT_MANUAL_EXECUTION_DECISION_TICKET_REPORT_CONFIG_VERSION,
    ManualExecutionDecisionTicketInput,
    build_manual_execution_decision_ticket_report,
)


def _ticket_input(**overrides: object) -> ManualExecutionDecisionTicketInput:
    values = {
        "ticket_id": "ticket-alpha",
        "market_slug": "event-alpha-yes",
        "p_yes_forecast": Decimal("0.620000"),
        "market_probability": Decimal("0.540000"),
        "cost_adjusted_threshold": Decimal("0.580000"),
        "source_count": Decimal("4"),
        "required_source_count": Decimal("3"),
        "specialist_team": ("macro", "microstructure"),
        "proposed_position_share": Decimal("0.030000"),
        "max_position_share": Decimal("0.050000"),
        "settlement_risk_status": "clear",
    }
    values.update(overrides)
    return ManualExecutionDecisionTicketInput(**values)


def test_builds_readonly_decision_ticket_summary() -> None:
    generated_at = datetime(2026, 7, 12, 8, 30, tzinfo=UTC)

    report = build_manual_execution_decision_ticket_report(
        _ticket_input(),
        generated_at=generated_at,
    )

    assert report.generated_at == generated_at
    assert (
        report.config_version
        == DEFAULT_MANUAL_EXECUTION_DECISION_TICKET_REPORT_CONFIG_VERSION
    )
    assert report.ticket_id == "ticket-alpha"
    assert report.market_slug == "event-alpha-yes"
    assert report.p_yes_forecast == Decimal("0.620000")
    assert report.market_probability == Decimal("0.540000")
    assert report.cost_adjusted_threshold == Decimal("0.580000")
    assert report.edge_to_market_probability == Decimal("0.080000")
    assert report.edge_to_threshold == Decimal("0.040000")
    assert report.source_count == Decimal("4")
    assert report.required_source_count == Decimal("3")
    assert report.source_quorum_status == "met"
    assert report.specialist_team == ("macro", "microstructure")
    assert report.proposed_position_share == Decimal("0.030000")
    assert report.max_position_share == Decimal("0.050000")
    assert report.max_position_blocker is None
    assert report.settlement_risk_status == "clear"
    assert report.settlement_risk_blocker is None
    assert report.decision_status == "ready_for_manual_review"
    assert report.reason_codes == ("ready_readonly_manual_ticket",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload["edge_to_threshold"] == "0.040000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["decision_status"] = "changed"


def test_blockers_roll_up_source_edge_position_and_settlement_risk() -> None:
    report = build_manual_execution_decision_ticket_report(
        _ticket_input(
            p_yes_forecast=Decimal("0.560000"),
            source_count=Decimal("2"),
            proposed_position_share=Decimal("0.060000"),
            settlement_risk_status="block",
        ),
        generated_at=datetime(2026, 7, 12, 8, 30, tzinfo=UTC),
    )

    assert report.edge_to_threshold == Decimal("-0.020000")
    assert report.source_quorum_status == "missing"
    assert (
        report.max_position_blocker
        == "proposed position share exceeds max position share"
    )
    assert report.settlement_risk_blocker == "settlement risk status is block"
    assert report.decision_status == "blocked"
    assert report.reason_codes == (
        "edge_below_cost_adjusted_threshold",
        "position_exceeds_max",
        "settlement_risk_blocker",
        "source_quorum_missing",
    )


def test_inputs_and_report_are_frozen_decimal_only_and_paper_safe() -> None:
    ticket_input = _ticket_input()
    with pytest.raises(FrozenInstanceError):
        ticket_input.market_slug = "changed"  # type: ignore[misc]

    report = build_manual_execution_decision_ticket_report(
        ticket_input,
        generated_at=datetime(2026, 7, 12, 8, 30, tzinfo=UTC),
    )
    with pytest.raises(FrozenInstanceError):
        report.decision_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="p_yes_forecast must be exactly Decimal"):
        _ticket_input(p_yes_forecast=0.62)
    with pytest.raises(ValueError, match="source_count must be exactly Decimal"):
        _ticket_input(source_count=4)
    with pytest.raises(ValueError, match="paper_only must be True"):
        _ticket_input(paper_only=False)


def test_module_has_no_live_execution_hook_surface() -> None:
    source = inspect.getsource(ticket_report_module).lower()

    forbidden_terms = (
        "requests",
        "httpx",
        "web3",
        "wallet",
        "private key",
        "private_key",
        "api key",
        "api_key",
        "authentication",
        "authorization",
        "sign_order",
        "place_order",
        "submit_order",
        "live trading",
        "live_trading",
    )
    assert all(term not in source for term in forbidden_terms)
