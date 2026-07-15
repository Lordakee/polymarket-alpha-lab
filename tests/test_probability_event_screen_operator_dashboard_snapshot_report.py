from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_operator_dashboard_snapshot_report import (
    PROBABILITY_EVENT_SCREEN_OPERATOR_DASHBOARD_SNAPSHOT_REPORT_VERSION,
    ProbabilityEventScreenOperatorDashboardSnapshotInput,
    ProbabilityEventScreenOperatorDashboardSnapshotReport,
    build_probability_event_screen_operator_dashboard_snapshot_report,
    probability_event_screen_operator_dashboard_snapshot_report_digest,
    probability_event_screen_operator_dashboard_snapshot_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_operator_dashboard_snapshot_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot_input(
    **overrides: object,
) -> ProbabilityEventScreenOperatorDashboardSnapshotInput:
    values = {
        "final_review_ready": True,
        "operating_review_ready": True,
        "audit_summary_ready": True,
        "exception_queue_ready": True,
        "daily_brief_ready": True,
        "batch_triage_ready": True,
        "manual_decision_gate_ready": True,
        "learning_feedback_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenOperatorDashboardSnapshotInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventScreenOperatorDashboardSnapshotReport:
    return build_probability_event_screen_operator_dashboard_snapshot_report(
        snapshot_input(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in ("wallet", "auth", "order", "database", "network"):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, tuple):
        for item in value:
            assert_no_runtime_numbers(item)


def test_ready_dashboard_snapshot_payload_digest_and_public_schema() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenOperatorDashboardSnapshotReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert (
        first.config_version
        == PROBABILITY_EVENT_SCREEN_OPERATOR_DASHBOARD_SNAPSHOT_REPORT_VERSION
    )
    assert first.dashboard_snapshot_ready is True
    assert first.snapshot_band == "ready"
    assert first.blocked_reason_codes == ()
    assert first.attention_reason_codes == ()
    assert first.ready_signal_count == d("8.000000")
    assert first.total_signal_count == d("8.000000")
    assert first.ready_ratio == d("1.000000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert probability_event_screen_operator_dashboard_snapshot_report_digest(first) == (
        first.digest
    )

    payload = probability_event_screen_operator_dashboard_snapshot_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-screen-operator-dashboard-snapshot-v0",
        "dashboard_snapshot_ready": True,
        "snapshot_band": "ready",
        "final_review_ready": True,
        "operating_review_ready": True,
        "audit_summary_ready": True,
        "exception_queue_ready": True,
        "daily_brief_ready": True,
        "batch_triage_ready": True,
        "manual_decision_gate_ready": True,
        "learning_feedback_ready": True,
        "ready_signal_count": "8.000000",
        "total_signal_count": "8.000000",
        "blocked_reason_codes": (),
        "attention_reason_codes": (),
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": first.digest,
    }
    json.dumps(payload, sort_keys=True)
    expected_digest = sha256(
        json.dumps(
            {**payload, "digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.digest == expected_digest
    assert_no_runtime_numbers(payload)

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["snapshot_band"] = "blocked"


def test_blocked_dashboard_snapshot_lists_operator_blockers_first() -> None:
    result = report(
        final_review_ready=False,
        operating_review_ready=False,
        audit_summary_ready=False,
        exception_queue_ready=False,
        daily_brief_ready=False,
        batch_triage_ready=False,
        manual_decision_gate_ready=False,
        learning_feedback_ready=False,
    )

    assert result.dashboard_snapshot_ready is False
    assert result.snapshot_band == "blocked"
    assert result.ready_signal_count == d("0.000000")
    assert result.ready_ratio == d("0.000000")
    assert result.blocked_reason_codes == (
        "final_review_not_ready",
        "operating_review_not_ready",
        "audit_summary_not_ready",
        "exception_queue_not_ready",
        "daily_brief_not_ready",
        "batch_triage_not_ready",
        "manual_decision_gate_not_ready",
    )
    assert result.attention_reason_codes == ("learning_feedback_not_ready",)
    assert result.public_payload["blocked_reason_codes"] == result.blocked_reason_codes
    assert result.public_payload["attention_reason_codes"] == (
        result.attention_reason_codes
    )


def test_watch_snapshot_keeps_dashboard_available_for_learning_gap() -> None:
    result = report(learning_feedback_ready=False)

    assert result.dashboard_snapshot_ready is False
    assert result.snapshot_band == "watch"
    assert result.ready_signal_count == d("7.000000")
    assert result.ready_ratio == d("0.875000")
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == ("learning_feedback_not_ready",)


def test_frozen_decimal_only_exact_types_and_hard_flags() -> None:
    input_value = snapshot_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.final_review_ready = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.snapshot_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenOperatorDashboardSnapshotInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenOperatorDashboardSnapshotReport):
            pass

    with pytest.raises(ValueError, match="final_review_ready"):
        snapshot_input(final_review_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        snapshot_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(result, ready_signal_count=8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must match"):
        replace(result, ready_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_operator_dashboard_snapshot_report_payload(
            replace(result, digest="0" * 64),
        )

    hints = get_type_hints(ProbabilityEventScreenOperatorDashboardSnapshotReport)
    for field in fields(ProbabilityEventScreenOperatorDashboardSnapshotReport):
        value = getattr(result, field.name)
        if field.name.endswith("_count") or field.name == "ready_ratio":
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "live_trading",
        "order execution",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "database",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
        "submit",
        "trade",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
