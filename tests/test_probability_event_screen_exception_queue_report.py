from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_screen_exception_queue_report import (
    ProbabilityEventScreenExceptionQueueReport,
    build_probability_event_screen_exception_queue_report,
    probability_event_screen_exception_queue_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_exception_queue_report.py",
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventScreenExceptionQueueReport:
    values = {
        "total_exception_count": d("10.000000"),
        "unsafe_payload_count": ZERO,
        "missing_digest_count": ZERO,
        "stale_source_count": ZERO,
        "conflicting_evidence_count": ZERO,
        "liquidity_blocked_count": ZERO,
        "manual_review_capacity_ready": True,
        "operator_safety_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_screen_exception_queue_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in ("wallet", "auth", "order", "database", "network"):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_ready_exception_queue_emits_decimal_string_payload_and_digest() -> None:
    queue = report()

    assert isinstance(queue, ProbabilityEventScreenExceptionQueueReport)
    assert queue.exception_queue_ready is True
    assert queue.exception_severity_band == "ready"
    assert queue.ready_ratio == d("1.000000")
    assert queue.blocked_reason_codes == ()
    assert queue.attention_reason_codes == ()
    assert len(queue.digest) == 64

    payload = queue.public_payload
    assert payload == probability_event_screen_exception_queue_report_payload(queue)
    assert payload["exception_queue_ready"] is True
    assert payload["exception_severity_band"] == "ready"
    assert payload["total_exception_count"] == "10.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == queue.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_blocked_readiness_flags_and_unsafe_payloads_stop_queue() -> None:
    queue = report(
        total_exception_count=d("7.000000"),
        unsafe_payload_count=d("2.000000"),
        missing_digest_count=d("1.000000"),
        stale_source_count=d("1.000000"),
        conflicting_evidence_count=d("1.000000"),
        liquidity_blocked_count=d("2.000000"),
        manual_review_capacity_ready=False,
        operator_safety_ready=False,
    )

    assert queue.exception_queue_ready is False
    assert queue.exception_severity_band == "blocked"
    assert queue.ready_ratio == ZERO
    assert queue.blocked_reason_codes == (
        "manual_review_capacity_not_ready",
        "operator_safety_not_ready",
        "unsafe_payload_present",
    )
    assert queue.attention_reason_codes == (
        "conflicting_evidence_present",
        "liquidity_blocked_present",
        "missing_digest_present",
        "stale_source_present",
    )


def test_attention_band_keeps_queue_reportable_for_non_blocking_exceptions() -> None:
    queue = report(
        total_exception_count=d("6.000000"),
        unsafe_payload_count=ZERO,
        missing_digest_count=d("1.000000"),
        stale_source_count=d("2.000000"),
        conflicting_evidence_count=d("1.000000"),
        liquidity_blocked_count=d("2.000000"),
    )

    assert queue.exception_queue_ready is False
    assert queue.exception_severity_band == "attention"
    assert queue.ready_ratio == ZERO
    assert queue.blocked_reason_codes == ()
    assert queue.attention_reason_codes == (
        "conflicting_evidence_present",
        "liquidity_blocked_present",
        "missing_digest_present",
        "stale_source_present",
    )


def test_empty_exception_queue_is_ready_and_has_zero_ready_ratio() -> None:
    queue = report(total_exception_count=ZERO)

    assert queue.exception_queue_ready is True
    assert queue.exception_severity_band == "ready"
    assert queue.ready_ratio == ZERO
    assert queue.blocked_reason_codes == ()
    assert queue.attention_reason_codes == ()


def test_frozen_flags_decimal_validation_and_count_consistency() -> None:
    queue = report()

    assert is_dataclass(ProbabilityEventScreenExceptionQueueReport)
    assert queue.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        queue.exception_severity_band = "blocked"  # type: ignore[misc]

    for field in fields(queue):
        value = getattr(queue, field.name)
        if field.name.endswith("_count") or field.name == "ready_ratio":
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(queue, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(queue, readonly=False)
    with pytest.raises(ValueError, match="total_exception_count"):
        report(total_exception_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsafe_payload_count"):
        report(unsafe_payload_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing_digest_count"):
        report(missing_digest_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="exception counts"):
        report(total_exception_count=d("3.000000"), stale_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="manual_review_capacity_ready"):
        report(manual_review_capacity_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="operator_safety_ready"):
        report(operator_safety_ready=1)  # type: ignore[arg-type]


def test_pure_readonly_report_only_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
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
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
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
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
