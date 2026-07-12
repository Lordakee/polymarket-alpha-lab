from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_operator_packet_regression_safety_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "probability_event_operator_packet_regression_safety_report.py",
)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def packet(**overrides: object) -> Any:
    module = api()
    values = {
        "packet_ref": "packet-alpha",
        "status": "watch",
        "reason_codes": ("source_quality_watch", "manual_review_required"),
        "source_quality": "watch",
        "memory_policy": "pass",
        "cost_gate": "pass",
        "manual_next_step": "paper_review_verify_source_quality",
    }
    values.update(overrides)
    return module.ProbabilityEventOperatorPacketSnapshot(**values)


def build_report(*, current: object, previous: object) -> Any:
    module = api()
    return module.build_probability_event_operator_packet_regression_safety_report(
        current_packet=current,
        previous_packet=previous,
    )


def assert_no_json_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_json_numbers(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_json_numbers(nested)
        return
    assert isinstance(value, bool) or not isinstance(value, (int, float, Decimal))


def test_passes_when_packet_retains_watch_status_reason_and_review_step() -> None:
    module = api()
    previous = packet()
    current = packet(reason_codes=("source_quality_watch", "manual_review_required"))

    report = build_report(current=current, previous=previous)
    payload = module.probability_event_operator_packet_regression_safety_report_payload(
        report,
    )

    assert report.regression_status == "pass"
    assert report.regression_reason_codes == (
        "probability_event_operator_packet_regression_safety_pass",
    )
    assert report.manual_next_step == "paper_review_continue_operator_packet_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload == {
        "regression_status": "pass",
        "regression_reason_codes": [
            "probability_event_operator_packet_regression_safety_pass",
        ],
        "manual_next_step": "paper_review_continue_operator_packet_review",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_json_numbers(payload)


@pytest.mark.parametrize("previous_status", ("blocked", "watch"))
def test_flags_silent_status_promotion_from_blocked_or_watch_to_pass(
    previous_status: str,
) -> None:
    previous = packet(
        status=previous_status,
        source_quality=previous_status,
        reason_codes=(f"source_quality_{previous_status}",),
        manual_next_step="paper_review_resolve_source_quality",
    )
    current = packet(
        status="pass",
        source_quality="pass",
        reason_codes=(f"source_quality_{previous_status}",),
        manual_next_step="paper_review_continue_operator_packet_review",
    )

    report = build_report(current=current, previous=previous)

    assert report.regression_status == "flagged"
    assert report.regression_reason_codes == (
        f"status_silent_{previous_status}_to_pass",
        "source_quality_silent_watch_to_pass"
        if previous_status == "watch"
        else "source_quality_silent_blocked_to_pass",
        "manual_next_step_changed",
        "probability_event_operator_packet_regression_safety_flagged",
    )
    assert report.manual_next_step == (
        "paper_review_investigate_operator_packet_regression_before_any_pass"
    )


def test_flags_reason_code_loss_even_when_current_status_remains_watch() -> None:
    previous = packet(
        status="watch",
        reason_codes=(
            "source_quality_watch",
            "manual_review_required",
            "cost_gate_review_required",
        ),
        cost_gate="watch",
    )
    current = packet(
        status="watch",
        reason_codes=("source_quality_watch",),
        cost_gate="watch",
    )

    report = build_report(current=current, previous=previous)

    assert report.regression_status == "flagged"
    assert report.regression_reason_codes == (
        "reason_code_lost_cost_gate_review_required",
        "reason_code_lost_manual_review_required",
        "probability_event_operator_packet_regression_safety_flagged",
    )
    assert report.manual_next_step == (
        "paper_review_restore_lost_operator_packet_reason_codes"
    )


def test_flags_gate_quality_policy_and_manual_step_regressions() -> None:
    previous = packet(
        status="blocked",
        reason_codes=(
            "memory_policy_blocked",
            "cost_gate_watch",
            "source_quality_watch",
        ),
        source_quality="watch",
        memory_policy="blocked",
        cost_gate="watch",
        manual_next_step="paper_review_resolve_memory_policy",
    )
    current = packet(
        status="blocked",
        reason_codes=(
            "memory_policy_blocked",
            "cost_gate_watch",
            "source_quality_watch",
        ),
        source_quality="pass",
        memory_policy="pass",
        cost_gate="pass",
        manual_next_step="paper_review_continue_operator_packet_review",
    )

    report = build_report(current=current, previous=previous)

    assert report.regression_status == "flagged"
    assert report.regression_reason_codes == (
        "source_quality_silent_watch_to_pass",
        "memory_policy_silent_blocked_to_pass",
        "cost_gate_silent_watch_to_pass",
        "manual_next_step_changed",
        "probability_event_operator_packet_regression_safety_flagged",
    )
    assert report.manual_next_step == (
        "paper_review_investigate_operator_packet_regression_before_any_pass"
    )


def test_dataclasses_are_frozen_strict_readonly_and_validate_inputs() -> None:
    module = api()
    previous = packet()
    current = packet()
    report = build_report(current=current, previous=previous)

    for record in (previous, report):
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen is True
        assert record.paper_only is True
        assert record.report_only is True
        assert record.readonly is True
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
        with pytest.raises(FrozenInstanceError):
            record.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadSnapshot(module.ProbabilityEventOperatorPacketSnapshot):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(previous, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        packet(status="PASS")
    with pytest.raises(ValueError, match="reason_codes"):
        packet(reason_codes=("source_quality_watch", "source_quality_watch"))
    with pytest.raises(ValueError, match="current_packet"):
        build_report(current={"status": "pass"}, previous=previous)


def test_module_exposes_no_persistence_execution_or_unsafe_surfaces() -> None:
    module = api()
    public_names = [name for name in dir(module) if not name.startswith("_")]
    forbidden_fragments = (
        "auth",
        "database",
        "dsn",
        "execute",
        "execution",
        "live",
        "order",
        "persist",
        "private",
        "sign",
        "submit",
        "token",
        "trade",
        "trading",
        "wallet",
    )
    offenders = [
        name
        for name in public_names
        if any(fragment in name.lower() for fragment in forbidden_fragments)
    ]
    assert offenders == []

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for fragment in forbidden_fragments:
        assert fragment not in lowered
