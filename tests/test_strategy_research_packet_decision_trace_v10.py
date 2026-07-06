from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_research_packet_decision_trace_v10 import (
    ResearchPacketDecisionTraceV10Input,
    ResearchPacketDecisionTraceV10Report,
    ResearchPacketDecisionTraceV10Step,
    strategy_research_packet_decision_trace_v10,
    strategy_research_packet_decision_trace_v10_payload,
)


def _assert_no_native_numbers(value: object) -> None:
    if type(value) is bool or value is None or type(value) is str:
        return
    if isinstance(value, (int, float)):
        raise AssertionError(f"native numeric value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_native_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_native_numbers(item)
        return
    raise AssertionError(f"unexpected payload value: {value!r}")


def _ready_input() -> ResearchPacketDecisionTraceV10Input:
    return ResearchPacketDecisionTraceV10Input(
        market_id="market-123",
        triage_status="approved",
        packet_status="ready",
        edge_status="positive",
        risk_status="cleared",
        budget_status="available",
        decision_status="recommended",
        review_status="approved",
    )


def test_decision_trace_marks_complete_recommendation_ready_path() -> None:
    report = strategy_research_packet_decision_trace_v10(_ready_input())

    assert is_dataclass(report)
    assert isinstance(report, ResearchPacketDecisionTraceV10Report)
    assert report.trace_status == "recommendation_ready"
    assert report.missing_trace_points == ()
    assert report.reason_codes == (
        "triage_approved",
        "packet_ready",
        "edge_positive",
        "risk_cleared",
        "budget_available",
        "decision_recommended",
        "review_approved",
        "trace_complete",
        "readonly_recommendation_ready",
    )
    assert tuple(step.trace_point for step in report.trace_steps) == (
        "triage",
        "packet",
        "edge",
        "risk",
        "budget",
        "decision",
        "review",
    )
    assert all(isinstance(step.sequence, Decimal) for step in report.trace_steps)
    assert all(step.step_status == "complete" for step in report.trace_steps)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_decision_trace_collects_missing_review_points() -> None:
    report = strategy_research_packet_decision_trace_v10(
        ResearchPacketDecisionTraceV10Input(
            market_id="market-review",
            triage_status="review_required",
            packet_status="review_required",
            edge_status="watch",
            risk_status="review_required",
            budget_status="constrained",
            decision_status="watchlist",
            review_status="pending",
        ),
    )

    assert report.trace_status == "review_required"
    assert report.missing_trace_points == (
        "triage_review_required",
        "packet_review_required",
        "edge_watch",
        "risk_review_required",
        "budget_constrained",
        "decision_watchlist",
        "review_pending",
    )
    assert tuple(step.step_status for step in report.trace_steps) == (
        "missing",
        "missing",
        "missing",
        "missing",
        "missing",
        "missing",
        "missing",
    )
    assert report.reason_codes[-1] == "trace_review_required"


def test_decision_trace_blocks_on_hard_stop_statuses() -> None:
    report = strategy_research_packet_decision_trace_v10(
        ResearchPacketDecisionTraceV10Input(
            market_id="market-blocked",
            triage_status="approved",
            packet_status="ready",
            edge_status="blocked",
            risk_status="cleared",
            budget_status="available",
            decision_status="recommended",
            review_status="approved",
        ),
    )

    assert report.trace_status == "blocked"
    assert report.missing_trace_points == ("edge_blocked",)
    assert report.reason_codes[-1] == "trace_blocked"
    edge_step = report.trace_steps[2]
    assert edge_step == ResearchPacketDecisionTraceV10Step(
        sequence=Decimal("3.000000"),
        trace_point="edge",
        input_status="blocked",
        step_status="blocked",
        reason_code="edge_blocked",
    )


def test_payload_is_readonly_json_ready_and_decimal_safe() -> None:
    report = strategy_research_packet_decision_trace_v10(_ready_input())

    payload = report.payload

    assert payload == strategy_research_packet_decision_trace_v10_payload(report)
    assert payload["trace_status"] == "recommendation_ready"
    assert payload["trace_steps"][0]["sequence"] == "1.000000"
    assert payload["trace_steps"][-1]["sequence"] == "7.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_native_numbers(payload)


def test_decision_trace_rejects_non_decimal_step_sequence() -> None:
    with pytest.raises(ValueError, match="sequence must be a Decimal"):
        ResearchPacketDecisionTraceV10Step(
            sequence=1,
            trace_point="triage",
            input_status="approved",
            step_status="complete",
            reason_code="triage_approved",
        )


def test_decision_trace_rejects_unapproved_status_and_flags() -> None:
    with pytest.raises(ValueError, match="edge_status must be one of"):
        ResearchPacketDecisionTraceV10Input(
            market_id="market-123",
            triage_status="approved",
            packet_status="ready",
            edge_status="excellent",
            risk_status="cleared",
            budget_status="available",
            decision_status="recommended",
            review_status="approved",
        )

    with pytest.raises(ValueError, match="input must be paper_only"):
        ResearchPacketDecisionTraceV10Input(
            market_id="market-123",
            triage_status="approved",
            packet_status="ready",
            edge_status="positive",
            risk_status="cleared",
            budget_status="available",
            decision_status="recommended",
            review_status="approved",
            paper_only=False,
        )


def test_decision_trace_dataclasses_are_frozen() -> None:
    value = _ready_input()

    with pytest.raises(FrozenInstanceError):
        value.market_id = "changed"
