from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_system_health_report import (
    PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION,
    ProbabilityEventScreenSystemHealthInput,
    ProbabilityEventScreenSystemHealthReport,
    build_probability_event_screen_system_health_report,
    probability_event_screen_system_health_report_digest,
    probability_event_screen_system_health_report_payload,
    validate_probability_event_screen_system_health_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_system_health_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def health_input(**overrides: object) -> ProbabilityEventScreenSystemHealthInput:
    values = {
        "acquisition_ready": True,
        "screening_pipeline_ready": True,
        "specialist_operating_cycle_ready": True,
        "operator_runbook_ready": True,
        "release_gate_ready": True,
        "learning_dashboard_ready": True,
        "supabase_persistence_ready": True,
        "public_payload_safety_ready": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenSystemHealthInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenSystemHealthReport:
    return build_probability_event_screen_system_health_report(
        health_input(**overrides),
    )


def test_all_subsystems_ready_produces_readonly_public_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenSystemHealthReport
    assert is_dataclass(first)
    assert first.config_version == PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION
    assert first.system_health_ready is True
    assert first.health_band == "ready"
    assert first.check_count == d("8.000000")
    assert first.ready_check_count == d("8.000000")
    assert first.blocked_check_count == d("0.000000")
    assert first.attention_check_count == d("0.000000")
    assert first.ready_ratio == d("1.000000")
    assert first.blocked_reason_codes == ("system_health_ready",)
    assert first.attention_reason_codes == ()
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert probability_event_screen_system_health_report_digest(first) == first.digest

    payload = probability_event_screen_system_health_report_payload(first)
    assert payload == first.public_payload
    assert payload["system_health_ready"] is True
    assert payload["health_band"] == "ready"
    assert payload["ready_check_count"] == "8.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == first.digest
    assert validate_probability_event_screen_system_health_public_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["system_health_ready"] = False


def test_blocking_subsystem_gaps_roll_up_reason_codes_band_and_ratio() -> None:
    result = report(
        acquisition_ready=False,
        release_gate_ready=False,
        public_payload_safety_ready=False,
    )

    assert result.system_health_ready is False
    assert result.health_band == "blocked"
    assert result.ready_check_count == d("5.000000")
    assert result.blocked_check_count == d("3.000000")
    assert result.attention_check_count == d("0.000000")
    assert result.ready_ratio == d("0.625000")
    assert result.blocked_reason_codes == (
        "acquisition_not_ready",
        "release_gate_not_ready",
        "public_payload_safety_not_ready",
    )
    assert result.attention_reason_codes == ()
    assert result.public_payload["blocked_check_count"] == "3.000000"
    assert result.public_payload["ready_ratio"] == "0.625000"


def test_learning_dashboard_gap_is_attention_only_watch_band() -> None:
    result = report(learning_dashboard_ready=False)

    assert result.system_health_ready is True
    assert result.health_band == "watch"
    assert result.ready_check_count == d("7.000000")
    assert result.blocked_check_count == d("0.000000")
    assert result.attention_check_count == d("1.000000")
    assert result.ready_ratio == d("0.875000")
    assert result.blocked_reason_codes == ("system_health_ready",)
    assert result.attention_reason_codes == (
        "learning_dashboard_not_ready_attention",
    )


def test_mixed_blocked_and_attention_gaps_use_blocked_band() -> None:
    result = report(
        screening_pipeline_ready=False,
        learning_dashboard_ready=False,
    )

    assert result.system_health_ready is False
    assert result.health_band == "blocked"
    assert result.ready_ratio == d("0.750000")
    assert result.blocked_reason_codes == ("screening_pipeline_not_ready",)
    assert result.attention_reason_codes == (
        "learning_dashboard_not_ready_attention",
    )


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = health_input()
    result = report()

    with pytest.raises(FrozenInstanceError):
        input_value.acquisition_ready = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.system_health_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenSystemHealthInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenSystemHealthReport):
            pass

    with pytest.raises(ValueError, match="acquisition_ready"):
        health_input(acquisition_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        health_input(paper_only=False)
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
    hints = get_type_hints(ProbabilityEventScreenSystemHealthReport)
    for field in fields(ProbabilityEventScreenSystemHealthReport):
        if field.name in numeric_fields:
            assert hints[field.name] is Decimal
    _assert_public_numeric_values_are_decimal(result)


def test_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload["digest"]

    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_system_health_report_payload(
            replace(report(), digest="0" * 64),
        )
    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_screen_system_health_public_payload(
            {**payload, "system_health_ready": False},
        )
    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_screen_system_health_public_payload(
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


def test_public_api_exports_are_explicit() -> None:
    import polymarket_alpha_lab.probability_event_screen_system_health_report as module

    assert module.__all__ == (
        "PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION",
        "ProbabilityEventScreenSystemHealthInput",
        "ProbabilityEventScreenSystemHealthPublicPayload",
        "ProbabilityEventScreenSystemHealthReport",
        "build_probability_event_screen_system_health_report",
        "probability_event_screen_system_health_report_digest",
        "probability_event_screen_system_health_report_payload",
        "validate_probability_event_screen_system_health_public_payload",
    )
    for exported_name in module.__all__:
        assert getattr(module, exported_name)


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
