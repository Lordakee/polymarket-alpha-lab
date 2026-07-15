from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_audit_summary_report import (
    PROBABILITY_EVENT_SCREEN_AUDIT_SUMMARY_REPORT_VERSION,
    ProbabilityEventScreenAuditSummaryInput,
    ProbabilityEventScreenAuditSummaryReport,
    build_probability_event_screen_audit_summary_report,
    probability_event_screen_audit_summary_report_digest,
    probability_event_screen_audit_summary_report_payload,
    validate_probability_event_screen_audit_summary_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_audit_summary_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def audit_input(**overrides: object) -> ProbabilityEventScreenAuditSummaryInput:
    values = {
        "pipeline_ready": True,
        "review_packet_index_ready": True,
        "export_manifest_ready": True,
        "operator_safety_ready": True,
        "exception_queue_ready": True,
        "go_no_go_ready": True,
        "supabase_contract_ready": True,
        "postmortem_learning_ready": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenAuditSummaryInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenAuditSummaryReport:
    return build_probability_event_screen_audit_summary_report(
        audit_input(**overrides),
    )


def test_all_screen_outputs_ready_produces_readonly_summary_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenAuditSummaryReport
    assert is_dataclass(first)
    assert first.config_version == PROBABILITY_EVENT_SCREEN_AUDIT_SUMMARY_REPORT_VERSION
    assert first.audit_summary_ready is True
    assert first.audit_band == "ready"
    assert first.ready_check_count == d("8.000000")
    assert first.blocked_check_count == d("0.000000")
    assert first.attention_check_count == d("0.000000")
    assert first.ready_ratio == d("1.000000")
    assert first.blocked_reason_codes == ("audit_summary_ready",)
    assert first.attention_reason_codes == ()
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert probability_event_screen_audit_summary_report_digest(first) == first.digest

    payload = probability_event_screen_audit_summary_report_payload(first)
    assert payload == first.public_payload
    assert payload["audit_summary_ready"] is True
    assert payload["audit_band"] == "ready"
    assert payload["ready_check_count"] == "8.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == first.digest
    assert validate_probability_event_screen_audit_summary_public_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["audit_summary_ready"] = False


def test_blocked_screen_outputs_roll_up_reason_codes_band_and_ratio() -> None:
    result = report(
        pipeline_ready=False,
        review_packet_index_ready=False,
        export_manifest_ready=False,
        operator_safety_ready=False,
        go_no_go_ready=False,
        supabase_contract_ready=False,
    )

    assert result.audit_summary_ready is False
    assert result.audit_band == "blocked"
    assert result.ready_check_count == d("2.000000")
    assert result.blocked_check_count == d("6.000000")
    assert result.attention_check_count == d("0.000000")
    assert result.ready_ratio == d("0.250000")
    assert result.blocked_reason_codes == (
        "pipeline_not_ready",
        "review_packet_index_not_ready",
        "export_manifest_not_ready",
        "operator_safety_not_ready",
        "go_no_go_not_ready",
        "supabase_contract_not_ready",
    )
    assert result.attention_reason_codes == ()
    assert result.public_payload["blocked_check_count"] == "6.000000"
    assert result.public_payload["ready_ratio"] == "0.250000"


def test_exception_queue_and_postmortem_learning_gaps_are_attention_only() -> None:
    result = report(
        exception_queue_ready=False,
        postmortem_learning_ready=False,
    )

    assert result.audit_summary_ready is True
    assert result.audit_band == "watch"
    assert result.ready_check_count == d("6.000000")
    assert result.blocked_check_count == d("0.000000")
    assert result.attention_check_count == d("2.000000")
    assert result.ready_ratio == d("0.750000")
    assert result.blocked_reason_codes == ("audit_summary_ready",)
    assert result.attention_reason_codes == (
        "exception_queue_not_ready_attention",
        "postmortem_learning_not_ready_attention",
    )


def test_mixed_blocked_and_attention_outputs_use_blocked_band() -> None:
    result = report(
        pipeline_ready=False,
        exception_queue_ready=False,
    )

    assert result.audit_summary_ready is False
    assert result.audit_band == "blocked"
    assert result.ready_ratio == d("0.750000")
    assert result.blocked_reason_codes == ("pipeline_not_ready",)
    assert result.attention_reason_codes == (
        "exception_queue_not_ready_attention",
    )


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = audit_input()
    result = report()

    with pytest.raises(FrozenInstanceError):
        input_value.pipeline_ready = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.audit_summary_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenAuditSummaryInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenAuditSummaryReport):
            pass

    with pytest.raises(ValueError, match="pipeline_ready"):
        audit_input(pipeline_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        audit_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=0)  # type: ignore[arg-type]

    numeric_fields = {
        "check_count",
        "ready_check_count",
        "blocked_check_count",
        "attention_check_count",
        "ready_ratio",
    }
    hints = get_type_hints(ProbabilityEventScreenAuditSummaryReport)
    for field in fields(ProbabilityEventScreenAuditSummaryReport):
        if field.name in numeric_fields:
            assert hints[field.name] is Decimal
    _assert_public_numeric_values_are_decimal(result)


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload["digest"]

    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_audit_summary_report_payload(
            replace(report(), digest="0" * 64),
        )
    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_screen_audit_summary_public_payload(
            {**payload, "audit_summary_ready": False},
        )
    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_screen_audit_summary_public_payload(
            {**payload, "digest": "0" * 64},
        )

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "postgres://",
        "postgresql://",
        "service_role",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
    ):
        assert forbidden not in encoded

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "live_trading",
        "place_order",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
    }
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(name in forbidden_call_names for name in call_names)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item_value in value.values():
            values.extend(_walk_payload_values(item_value))
    elif isinstance(value, (list, tuple)):
        for item_value in value:
            values.extend(_walk_payload_values(item_value))
    else:
        values.append(value)
    return tuple(values)


def _is_forbidden_number(value: object) -> bool:
    return type(value) is int or type(value) is float


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for child in value.values():
            _assert_public_numeric_values_are_decimal(child)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            _assert_public_numeric_values_are_decimal(child)
