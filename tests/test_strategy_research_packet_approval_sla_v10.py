from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_research_packet_approval_sla_v10 import (
    APPROVAL_PRIORITIES,
    APPROVAL_SLA_STATUSES,
    BRIEF_STATUSES,
    DEFAULT_RESEARCH_PACKET_APPROVAL_SLA_V10_CONFIG_VERSION,
    REASON_CODES,
    ResearchPacketApprovalSlaV10Config,
    ResearchPacketApprovalSlaV10Input,
    ResearchPacketApprovalSlaV10Report,
    evaluate_research_packet_approval_sla_v10,
    research_packet_approval_sla_v10_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _packet(**overrides: object) -> ResearchPacketApprovalSlaV10Input:
    values = {
        "market_id": "market-approval-sla",
        "brief_status": "ready",
        "review_required": True,
        "review_queue_age_minutes": d("30.000000"),
        "time_to_resolution_minutes": d("480.000000"),
        "decision_readiness": d("0.850000"),
        "team_capacity_score": d("0.750000"),
        "blocking_reason_count": d("0"),
    }
    values.update(overrides)
    return ResearchPacketApprovalSlaV10Input(**values)


def test_approval_sla_breach_returns_urgent_readonly_report_payload() -> None:
    report = evaluate_research_packet_approval_sla_v10(
        _packet(
            review_queue_age_minutes=d("130.000000"),
            time_to_resolution_minutes=d("45.000000"),
            decision_readiness=d("0.920000"),
            team_capacity_score=d("0.800000"),
        ),
    )

    assert type(report) is ResearchPacketApprovalSlaV10Report
    assert report.config_version == DEFAULT_RESEARCH_PACKET_APPROVAL_SLA_V10_CONFIG_VERSION
    assert report.market_id == "market-approval-sla"
    assert report.brief_status == "ready"
    assert report.approval_sla_status == "breached"
    assert report.approval_priority == "urgent"
    assert report.escalation_minutes == d("0.000000")
    assert report.reason_codes == (
        "review_required",
        "brief_ready",
        "decision_ready",
        "capacity_available",
        "no_blocking_reasons",
        "sla_breached",
        "resolution_window_immediate",
        "approval_priority_urgent",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload == research_packet_approval_sla_v10_payload(report)
    _assert_decimal_public_metrics(report)


def test_approval_sla_watch_prioritizes_near_resolution_and_capacity_pressure() -> None:
    report = evaluate_research_packet_approval_sla_v10(
        _packet(
            review_queue_age_minutes=d("95.000000"),
            time_to_resolution_minutes=d("240.000000"),
            decision_readiness=d("0.750000"),
            team_capacity_score=d("0.400000"),
        ),
    )

    assert report.approval_sla_status == "watch"
    assert report.approval_priority == "high"
    assert report.escalation_minutes == d("25.000000")
    assert report.reason_codes == (
        "review_required",
        "brief_ready",
        "decision_ready",
        "capacity_constrained",
        "no_blocking_reasons",
        "sla_watch",
        "resolution_window_near",
        "approval_priority_high",
    )


def test_approval_sla_blocks_unready_briefs_and_blocking_reasons() -> None:
    report = evaluate_research_packet_approval_sla_v10(
        _packet(
            brief_status="draft",
            review_queue_age_minutes=d("10.000000"),
            time_to_resolution_minutes=d("900.000000"),
            decision_readiness=d("0.400000"),
            blocking_reason_count=d("2"),
        ),
    )

    assert report.approval_sla_status == "blocked"
    assert report.approval_priority == "blocked"
    assert report.escalation_minutes == d("0.000000")
    assert report.reason_codes == (
        "review_required",
        "brief_in_progress",
        "decision_not_ready",
        "capacity_available",
        "blocking_reasons_present",
        "sla_blocked",
        "resolution_window_normal",
        "approval_priority_blocked",
    )


def test_review_not_required_is_passive_report_only_output() -> None:
    report = evaluate_research_packet_approval_sla_v10(
        _packet(
            brief_status="approved",
            review_required=False,
            review_queue_age_minutes=d("240.000000"),
            time_to_resolution_minutes=d("720.000000"),
        ),
    )

    assert report.approval_sla_status == "not_required"
    assert report.approval_priority == "none"
    assert report.escalation_minutes == d("0.000000")
    assert report.reason_codes == (
        "review_not_required",
        "brief_approved",
        "decision_ready",
        "capacity_available",
        "no_blocking_reasons",
        "sla_not_required",
        "resolution_window_normal",
        "approval_priority_none",
    )


def test_payload_is_json_ready_without_floats_and_contains_expected_strings() -> None:
    report = evaluate_research_packet_approval_sla_v10(
        _packet(
            review_queue_age_minutes=d("119.999999"),
            time_to_resolution_minutes=d("59.999999"),
        ),
    )

    payload = research_packet_approval_sla_v10_payload(report)

    assert payload == report.payload
    assert payload["review_queue_age_minutes"] == "119.999999"
    assert payload["time_to_resolution_minutes"] == "59.999999"
    assert payload["decision_readiness"] == "0.850000"
    assert payload["team_capacity_score"] == "0.750000"
    assert payload["blocking_reason_count"] == "0"
    assert payload["approval_sla_status"] == "watch"
    assert payload["approval_priority"] == "urgent"
    assert payload["escalation_minutes"] == "0.000001"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_approval_sla_validates_decimal_only_inputs_flags_and_freezing() -> None:
    packet = _packet()
    report = evaluate_research_packet_approval_sla_v10(packet)

    with pytest.raises(FrozenInstanceError):
        packet.market_id = "other"
    with pytest.raises(FrozenInstanceError):
        report.approval_priority = "none"
    with pytest.raises(ValueError, match="review_queue_age_minutes must be a Decimal"):
        _packet(review_queue_age_minutes=30)
    with pytest.raises(ValueError, match="decision_readiness must be between"):
        _packet(decision_readiness=d("1.000001"))
    with pytest.raises(ValueError, match="blocking_reason_count must be a whole Decimal"):
        _packet(blocking_reason_count=d("1.500000"))
    with pytest.raises(ValueError, match="review_required must be a bool"):
        _packet(review_required=1)
    with pytest.raises(ValueError, match="market_id must be a non-empty canonical string"):
        _packet(market_id=" market ")
    with pytest.raises(ValueError, match="brief_status must be one of"):
        _packet(brief_status="queued")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(packet, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="approval_sla_minutes must be positive"):
        ResearchPacketApprovalSlaV10Config(approval_sla_minutes=d("0.000000"))
    with pytest.raises(ValueError, match="watch_queue_age_minutes must be below"):
        ResearchPacketApprovalSlaV10Config(watch_queue_age_minutes=d("120.000000"))
    with pytest.raises(ValueError, match="minimum_capacity_score must be a Decimal"):
        ResearchPacketApprovalSlaV10Config(
            minimum_capacity_score=_DecimalSubclass("0.500000"),
        )


def test_approval_sla_exposes_only_report_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_research_packet_approval_sla_v10",
    )
    forbidden_terms = (
        "persist",
        "network",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
    )

    assert BRIEF_STATUSES == (
        "draft",
        "researching",
        "ready",
        "in_review",
        "approved",
        "blocked",
        "archived",
    )
    assert APPROVAL_SLA_STATUSES == (
        "not_required",
        "within_sla",
        "watch",
        "breached",
        "blocked",
    )
    assert APPROVAL_PRIORITIES == ("none", "normal", "high", "urgent", "blocked")
    assert "approval_priority_urgent" in REASON_CODES
    assert set(module.__all__) == {
        "APPROVAL_PRIORITIES",
        "APPROVAL_SLA_STATUSES",
        "BRIEF_STATUSES",
        "DEFAULT_RESEARCH_PACKET_APPROVAL_SLA_V10_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchPacketApprovalSlaV10Config",
        "ResearchPacketApprovalSlaV10Input",
        "ResearchPacketApprovalSlaV10Report",
        "evaluate_research_packet_approval_sla_v10",
        "research_packet_approval_sla_v10_payload",
    }
    assert not any(
        term in public_name.lower()
        for public_name in module.__all__
        for term in forbidden_terms
    )


def _assert_decimal_public_metrics(value: object) -> None:
    assert is_dataclass(value)
    for field in fields(value):
        if field.name.endswith(
            (
                "minutes",
                "readiness",
                "score",
                "count",
            ),
        ):
            assert type(getattr(value, field.name)) is Decimal


def _assert_no_floats(value: Any) -> None:
    assert not isinstance(value, float)
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)
