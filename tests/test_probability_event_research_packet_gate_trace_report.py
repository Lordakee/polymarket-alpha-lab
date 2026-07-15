from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_research_packet_gate_trace_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.probability_event_research_packet_gate_trace_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def gate(status: str = "pass", reason_codes: tuple[str, ...] = ("gate_pass",)) -> Any:
    module = api()
    return module.ProbabilityEventResearchPacketGateTraceStep(
        gate_status=status,
        reason_codes=reason_codes,
    )


def trace_input(**overrides: object) -> Any:
    module = api()
    values = {
        "event_ref": "event-alpha",
        "probability_screen": gate(
            "pass",
            ("probability_screen_edge_ready",),
        ),
        "source_quality": gate(
            "pass",
            ("source_quality_ready",),
        ),
        "memory_policy": gate(
            "pass",
            ("memory_policy_allows_research_packet",),
        ),
        "cost_gate": gate(
            "pass",
            ("cost_gate_ready",),
        ),
        "operator_packet": gate(
            "pass",
            ("operator_packet_ready",),
        ),
    }
    values.update(overrides)
    return module.ProbabilityEventResearchPacketGateTraceInput(**values)


def build_report(source_input: object) -> Any:
    return api().build_probability_event_research_packet_gate_trace_report(
        source_input,
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def assert_decimal_only(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric value {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_decimal_only(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_decimal_only(item)


def test_blocked_gate_wins_and_preserves_auditable_trace() -> None:
    module = api()
    result = build_report(
        trace_input(
            source_quality=gate(
                "blocked",
                ("source_quality_contradiction_unresolved",),
            ),
            cost_gate=gate(
                "watch",
                ("fee_drag_requires_review",),
            ),
        ),
    )
    payload = module.probability_event_research_packet_gate_trace_report_payload(
        result,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert type(result) is module.ProbabilityEventResearchPacketGateTraceReport
    assert is_dataclass(result)
    assert result.event_ref == "event-alpha"
    assert result.trace_status == "blocked"
    assert result.blocking_gate == "source_quality"
    assert result.watch_gates == ("cost_gate",)
    assert result.manual_next_step == "manual_review_blocking_gate_before_packet_use"
    assert result.gate_count == d("5")
    assert result.pass_count == d("3")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.reason_codes == (
        "research_packet_gate_trace_blocked",
        "source_quality_blocked",
        "cost_gate_watch",
        "probability_screen_edge_ready",
        "source_quality_contradiction_unresolved",
        "memory_policy_allows_research_packet",
        "fee_drag_requires_review",
        "operator_packet_ready",
    )
    assert tuple(row.gate_name for row in result.trace_rows) == (
        "probability_screen",
        "source_quality",
        "memory_policy",
        "cost_gate",
        "operator_packet",
    )
    assert result.trace_rows[1].gate_status == "blocked"
    assert result.trace_rows[1].reason_codes == (
        "source_quality_contradiction_unresolved",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert payload["trace_status"] == "blocked"
    assert payload["blocking_gate"] == "source_quality"
    assert payload["watch_gates"] == ["cost_gate"]
    assert payload["trace_rows"][1]["reason_codes"] == [
        "source_quality_contradiction_unresolved",
    ]
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert_decimal_only(result)


def test_watch_trace_lists_watch_gates_without_blocking_gate() -> None:
    result = build_report(
        trace_input(
            probability_screen=gate(
                "watch",
                ("probability_edge_needs_confirmation",),
            ),
            memory_policy=gate(
                "watch",
                ("memory_policy_requires_team_review",),
            ),
        ),
    )

    assert result.trace_status == "watch"
    assert result.blocking_gate == ""
    assert result.watch_gates == ("probability_screen", "memory_policy")
    assert result.manual_next_step == "manual_review_watch_gates_before_packet_use"
    assert result.pass_count == d("3")
    assert result.watch_count == d("2")
    assert result.blocked_count == d("0")
    assert result.reason_codes == (
        "research_packet_gate_trace_watch",
        "probability_screen_watch",
        "memory_policy_watch",
        "probability_edge_needs_confirmation",
        "source_quality_ready",
        "memory_policy_requires_team_review",
        "cost_gate_ready",
        "operator_packet_ready",
    )


def test_all_pass_trace_is_frozen_strict_and_payload_is_readonly() -> None:
    module = api()
    result = build_report(trace_input())
    repeated = build_report(trace_input())

    assert result.trace_status == "pass"
    assert result.blocking_gate == ""
    assert result.watch_gates == ()
    assert result.manual_next_step == "manual_read_research_packet_gate_trace"
    assert result.reason_codes == (
        "research_packet_gate_trace_pass",
        "probability_screen_edge_ready",
        "source_quality_ready",
        "memory_policy_allows_research_packet",
        "cost_gate_ready",
        "operator_packet_ready",
    )
    assert result.derived_validation_digest == repeated.derived_validation_digest
    assert len(result.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        result.trace_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_ref"):
        replace(result, event_ref=_StringSubclass("event-alpha"))
    with pytest.raises(ValueError, match="gate_count"):
        replace(result, gate_count=_DecimalSubclass("5"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    payload = module.probability_event_research_packet_gate_trace_report_payload(
        result,
    )
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["trace_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.probability_event_research_packet_gate_trace_report_payload(
            {
                **payload,
                "trace_status": "watch",
            },
        )


def test_inputs_are_strict_decimal_safe_and_reject_unsafe_public_text() -> None:
    module = api()

    assert module.__all__ == (
        "PROBABILITY_EVENT_RESEARCH_PACKET_GATE_TRACE_REPORT_VERSION",
        "ProbabilityEventResearchPacketGateTraceInput",
        "ProbabilityEventResearchPacketGateTraceReport",
        "ProbabilityEventResearchPacketGateTraceRow",
        "ProbabilityEventResearchPacketGateTraceStep",
        "build_probability_event_research_packet_gate_trace_report",
        "probability_event_research_packet_gate_trace_report_payload",
    )

    with pytest.raises(FrozenInstanceError):
        source_step = gate()
        source_step.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="gate_status"):
        gate("allow")
    with pytest.raises(ValueError, match="reason_codes"):
        gate("pass", ())
    with pytest.raises(ValueError, match="reason_code"):
        gate("pass", ("live_review",))
    with pytest.raises(ValueError, match="probability_screen"):
        trace_input(probability_screen=object())
    with pytest.raises(ValueError, match="event_ref"):
        trace_input(event_ref="wallet-review")

    source = inspect.getsource(module)
    forbidden_terms = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
        "submit_",
        "cancel_",
        "place_",
    )
    for term in forbidden_terms:
        assert term not in source
