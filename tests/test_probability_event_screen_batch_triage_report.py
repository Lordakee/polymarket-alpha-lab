from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_screen_batch_triage_report import (
    ProbabilityEventScreenBatchTriageReport,
    build_probability_event_screen_batch_triage_report,
)


MODULE_PATH = Path("src/polymarket_alpha_lab/probability_event_screen_batch_triage_report.py")
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventScreenBatchTriageReport:
    values = {
        "total_candidate_count": d("6.000000"),
        "ready_for_manual_review_count": d("6.000000"),
        "watch_count": ZERO,
        "blocked_count": ZERO,
        "highest_edge_to_threshold_probability": d("0.180000"),
        "average_source_reliability_score": d("0.820000"),
        "average_memory_context_score": d("0.760000"),
        "operator_output_safety_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_screen_batch_triage_report(**values)


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


def test_batch_ready_report_emits_decimal_string_payload_and_digest() -> None:
    triage = report()

    assert isinstance(triage, ProbabilityEventScreenBatchTriageReport)
    assert triage.batch_triage_ready is True
    assert triage.triage_band == "ready"
    assert triage.next_manual_review_count == d("6.000000")
    assert triage.ready_ratio == d("1.000000")
    assert triage.blocked_reason_codes == ()
    assert triage.attention_reason_codes == ()
    assert len(triage.digest) == 64

    payload = triage.public_payload
    assert payload["batch_triage_ready"] is True
    assert payload["triage_band"] == "ready"
    assert payload["total_candidate_count"] == "6.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["next_manual_review_count"] == "6.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == triage.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_blocked_safety_or_blocked_candidates_stop_manual_review_queue() -> None:
    triage = report(
        total_candidate_count=d("8.000000"),
        ready_for_manual_review_count=d("4.000000"),
        watch_count=d("2.000000"),
        blocked_count=d("2.000000"),
        operator_output_safety_ready=False,
    )

    assert triage.batch_triage_ready is False
    assert triage.triage_band == "blocked"
    assert triage.next_manual_review_count == ZERO
    assert triage.ready_ratio == d("0.500000")
    assert triage.blocked_reason_codes == (
        "operator_output_safety_not_ready",
        "screen_batch_contains_blocked_candidates",
    )
    assert triage.attention_reason_codes == (
        "manual_review_queue_available",
        "screen_batch_contains_watch_candidates",
    )


def test_watch_band_keeps_manual_review_queue_with_attention_reasons() -> None:
    triage = report(
        total_candidate_count=d("5.000000"),
        ready_for_manual_review_count=d("1.000000"),
        watch_count=d("4.000000"),
        blocked_count=ZERO,
        highest_edge_to_threshold_probability=d("0.010000"),
        average_source_reliability_score=d("0.590000"),
        average_memory_context_score=d("0.550000"),
    )

    assert triage.batch_triage_ready is False
    assert triage.triage_band == "watch"
    assert triage.next_manual_review_count == d("1.000000")
    assert triage.ready_ratio == d("0.200000")
    assert triage.blocked_reason_codes == ()
    assert triage.attention_reason_codes == (
        "edge_to_threshold_probability_low",
        "manual_review_queue_available",
        "memory_context_score_low",
        "screen_batch_contains_watch_candidates",
        "source_reliability_score_low",
    )


def test_empty_batch_is_reportable_but_not_ready_for_triage() -> None:
    triage = report(
        total_candidate_count=ZERO,
        ready_for_manual_review_count=ZERO,
        watch_count=ZERO,
        blocked_count=ZERO,
        highest_edge_to_threshold_probability=ZERO,
        average_source_reliability_score=ZERO,
        average_memory_context_score=ZERO,
    )

    assert triage.batch_triage_ready is False
    assert triage.triage_band == "watch"
    assert triage.next_manual_review_count == ZERO
    assert triage.ready_ratio == ZERO
    assert triage.attention_reason_codes == (
        "edge_to_threshold_probability_low",
        "memory_context_score_low",
        "screen_batch_empty",
        "source_reliability_score_low",
    )


def test_frozen_flags_decimal_validation_and_count_consistency() -> None:
    triage = report()

    assert is_dataclass(ProbabilityEventScreenBatchTriageReport)
    assert triage.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        triage.triage_band = "blocked"  # type: ignore[misc]

    for public_record in (triage,):
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if field.name.endswith("_count") or field.name.endswith("_score"):
                assert type(value) is Decimal
            if "probability" in field.name or field.name == "ready_ratio":
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(triage, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(triage, readonly=False)
    with pytest.raises(ValueError, match="total_candidate_count"):
        report(total_candidate_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="average_source_reliability_score"):
        report(average_source_reliability_score=0.82)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="highest_edge_to_threshold_probability"):
        report(highest_edge_to_threshold_probability=_DecimalSubclass("0.180000"))
    with pytest.raises(ValueError, match="candidate counts"):
        report(total_candidate_count=d("4.000000"))
    with pytest.raises(ValueError, match="operator_output_safety_ready"):
        report(operator_output_safety_ready=1)  # type: ignore[arg-type]


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
