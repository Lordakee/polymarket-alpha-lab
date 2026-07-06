from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_team_specialist_handoff_ticket_v10 import (
    StrategyTeamSpecialistHandoffTicket,
    StrategyTeamSpecialistHandoffTicketInput,
    build_strategy_team_specialist_handoff_ticket,
    strategy_team_specialist_handoff_ticket_payload,
)


def _ticket_input(**overrides):
    values = {
        "market_id": "market-123",
        "from_team": "macro-research",
        "to_team": "specialist-review",
        "handoff_reason": "Need sector specialist review on unresolved catalyst evidence",
        "evidence_gap_count": Decimal("2.000000"),
        "urgency_score": Decimal("0.800000"),
        "source_quorum_status": "partial",
        "deadline_minutes": Decimal("90.000000"),
    }
    values.update(overrides)
    return StrategyTeamSpecialistHandoffTicketInput(**values)


def test_builds_expedited_handoff_ticket_for_urgent_gap_review():
    ticket = build_strategy_team_specialist_handoff_ticket(_ticket_input())

    assert isinstance(ticket, StrategyTeamSpecialistHandoffTicket)
    assert ticket.market_id == "market-123"
    assert ticket.from_team == "macro-research"
    assert ticket.to_team == "specialist-review"
    assert ticket.handoff_status == "expedited"
    assert ticket.sla_minutes == Decimal("30.000000")
    assert ticket.required_sections == (
        "market_context",
        "handoff_reason",
        "source_quorum_status",
        "sla_and_deadline",
        "evidence_gap_inventory",
        "source_quorum_remediation",
        "urgency_rationale",
        "specialist_decision_request",
    )
    assert ticket.reason_codes == (
        "team_specialist_handoff_ticket",
        "evidence_gap_present",
        "source_quorum_partial",
        "urgency_high",
        "deadline_standard",
        "handoff_status_expedited",
    )
    assert ticket.paper_only is True
    assert ticket.report_only is True
    assert ticket.readonly is True
    assert ticket.payload == strategy_team_specialist_handoff_ticket_payload(ticket)


def test_missing_source_quorum_blocks_handoff_with_short_triage_sla():
    ticket = build_strategy_team_specialist_handoff_ticket(
        _ticket_input(
            evidence_gap_count=Decimal("0.000000"),
            urgency_score=Decimal("0.200000"),
            source_quorum_status="missing",
            deadline_minutes=Decimal("45.000000"),
        ),
    )

    assert ticket.handoff_status == "blocked"
    assert ticket.sla_minutes == Decimal("15.000000")
    assert "source_quorum_remediation" in ticket.required_sections
    assert "source_quorum_missing" in ticket.reason_codes
    assert "handoff_status_blocked" in ticket.reason_codes


def test_ready_ticket_uses_deadline_capped_standard_sla():
    ticket = build_strategy_team_specialist_handoff_ticket(
        _ticket_input(
            evidence_gap_count=Decimal("0.000000"),
            urgency_score=Decimal("0.300000"),
            source_quorum_status="met",
            deadline_minutes=Decimal("180.000000"),
        ),
    )

    assert ticket.handoff_status == "ready"
    assert ticket.sla_minutes == Decimal("180.000000")
    assert ticket.required_sections == (
        "market_context",
        "handoff_reason",
        "source_quorum_status",
        "sla_and_deadline",
        "specialist_decision_request",
    )
    assert ticket.reason_codes == (
        "team_specialist_handoff_ticket",
        "evidence_gap_clear",
        "source_quorum_met",
        "urgency_standard",
        "deadline_standard",
        "handoff_status_ready",
    )


def test_research_required_ticket_tracks_nonurgent_gaps():
    ticket = build_strategy_team_specialist_handoff_ticket(
        _ticket_input(
            evidence_gap_count=Decimal("3.000000"),
            urgency_score=Decimal("0.400000"),
            source_quorum_status="met",
            deadline_minutes=Decimal("300.000000"),
        ),
    )

    assert ticket.handoff_status == "research_required"
    assert ticket.sla_minutes == Decimal("120.000000")
    assert "evidence_gap_inventory" in ticket.required_sections
    assert "handoff_status_research_required" in ticket.reason_codes


def test_input_requires_decimal_numbers_and_valid_ranges():
    with pytest.raises(ValueError, match="evidence_gap_count must be a Decimal"):
        _ticket_input(evidence_gap_count=2)

    with pytest.raises(ValueError, match="urgency_score must be a Decimal"):
        _ticket_input(urgency_score=0.8)

    with pytest.raises(ValueError, match="urgency_score must be between 0 and 1"):
        _ticket_input(urgency_score=Decimal("1.000001"))

    with pytest.raises(ValueError, match="evidence_gap_count must be a whole number"):
        _ticket_input(evidence_gap_count=Decimal("1.500000"))

    with pytest.raises(ValueError, match="deadline_minutes must be positive"):
        _ticket_input(deadline_minutes=Decimal("0.000000"))

    with pytest.raises(ValueError, match="source_quorum_status must be one of"):
        _ticket_input(source_quorum_status="unknown")

    with pytest.raises(ValueError, match="from_team and to_team must differ"):
        _ticket_input(to_team="macro-research")


def test_handoff_ticket_requires_hard_flags_and_safe_public_text():
    with pytest.raises(ValueError, match="paper_only must be True"):
        _ticket_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        _ticket_input(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _ticket_input(readonly=False)

    with pytest.raises(ValueError, match="unsafe live surface value"):
        _ticket_input(handoff_reason="Need wallet auth before specialist review")


def test_handoff_ticket_dataclasses_are_frozen():
    ticket_input = _ticket_input()
    ticket = build_strategy_team_specialist_handoff_ticket(ticket_input)

    with pytest.raises(FrozenInstanceError):
        ticket_input.market_id = "market-456"

    with pytest.raises(FrozenInstanceError):
        ticket.handoff_status = "ready"


def test_payload_is_report_only_json_ready_and_decimal_strings():
    ticket = build_strategy_team_specialist_handoff_ticket(_ticket_input())
    payload = strategy_team_specialist_handoff_ticket_payload(ticket)

    assert payload == ticket.payload
    assert payload["market_id"] == "market-123"
    assert payload["evidence_gap_count"] == "2.000000"
    assert payload["urgency_score"] == "0.800000"
    assert payload["deadline_minutes"] == "90.000000"
    assert payload["sla_minutes"] == "30.000000"
    assert payload["required_sections"] == [
        "market_context",
        "handoff_reason",
        "source_quorum_status",
        "sla_and_deadline",
        "evidence_gap_inventory",
        "source_quorum_remediation",
        "urgency_rationale",
        "specialist_decision_request",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in payload.values())

    unsafe = object.__new__(StrategyTeamSpecialistHandoffTicket)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_team_specialist_handoff_ticket_payload(unsafe)
