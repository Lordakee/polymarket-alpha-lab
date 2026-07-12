from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_screen_end_to_end_readiness_report as api
from polymarket_alpha_lab.probability_event_screen_end_to_end_readiness_report import (
    END_TO_END_READINESS_BANDS,
    ProbabilityEventScreenEndToEndReadinessInput,
    ProbabilityEventScreenEndToEndReadinessReport,
    build_probability_event_screen_end_to_end_readiness_report,
    probability_event_screen_end_to_end_readiness_report_digest,
    probability_event_screen_end_to_end_readiness_report_to_payload,
    validate_probability_event_screen_end_to_end_readiness_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_end_to_end_readiness_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(
    **overrides: object,
) -> ProbabilityEventScreenEndToEndReadinessInput:
    values = {
        "acquisition_ready": True,
        "screen_contract_ready": True,
        "quality_index_ready": True,
        "manual_decision_gate_ready": True,
        "operator_runbook_ready": True,
        "release_gate_ready": True,
        "learning_feedback_ready": True,
        "supabase_persistence_ready": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenEndToEndReadinessInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenEndToEndReadinessReport:
    return build_probability_event_screen_end_to_end_readiness_report(
        readiness_input(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_end_to_end_readiness_band_vocabulary_is_exact() -> None:
    assert END_TO_END_READINESS_BANDS == ("ready", "attention", "blocked")


def test_all_components_ready_emits_readonly_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenEndToEndReadinessReport
    assert is_dataclass(first)
    assert first.end_to_end_ready is True
    assert first.readiness_band == "ready"
    assert first.blocked_reason_codes == ()
    assert first.attention_reason_codes == (
        "probability_event_screen_end_to_end_ready",
    )
    assert first.ready_ratio == d("1.000000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_screen_end_to_end_readiness_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "acquisition_ready": True,
        "screen_contract_ready": True,
        "quality_index_ready": True,
        "manual_decision_gate_ready": True,
        "operator_runbook_ready": True,
        "release_gate_ready": True,
        "learning_feedback_ready": True,
        "supabase_persistence_ready": True,
        "end_to_end_ready": True,
        "readiness_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_end_to_end_ready",
        ],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.digest == expected_digest
    assert first.digest == second.digest
    assert probability_event_screen_end_to_end_readiness_report_digest(first) == expected_digest
    assert (
        validate_probability_event_screen_end_to_end_readiness_public_payload(payload)
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_missing_required_components_block_in_deterministic_order() -> None:
    result = report(
        acquisition_ready=False,
        screen_contract_ready=False,
        quality_index_ready=False,
        manual_decision_gate_ready=False,
        operator_runbook_ready=False,
        release_gate_ready=False,
        learning_feedback_ready=False,
        supabase_persistence_ready=False,
    )

    assert result.end_to_end_ready is False
    assert result.readiness_band == "blocked"
    assert result.ready_ratio == d("0.000000")
    assert result.blocked_reason_codes == (
        "end_to_end_acquisition_not_ready",
        "end_to_end_screen_contract_not_ready",
        "end_to_end_quality_index_not_ready",
        "end_to_end_manual_decision_gate_not_ready",
        "end_to_end_operator_runbook_not_ready",
        "end_to_end_release_gate_not_ready",
        "end_to_end_learning_feedback_not_ready",
        "end_to_end_supabase_persistence_not_ready",
    )
    assert result.attention_reason_codes == ()
    assert result.public_payload["ready_ratio"] == "0.000000"


def test_paper_report_readonly_flag_gaps_are_attention_not_blocked() -> None:
    result = report(paper_only=False, report_only=False, readonly=False)

    assert result.end_to_end_ready is False
    assert result.readiness_band == "attention"
    assert result.ready_ratio == d("1.000000")
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == (
        "end_to_end_paper_only_flag_not_set",
        "end_to_end_report_only_flag_not_set",
        "end_to_end_readonly_flag_not_set",
    )
    assert result.public_payload["paper_only"] is True
    assert result.public_payload["report_only"] is True
    assert result.public_payload["readonly"] is True


def test_dataclasses_are_frozen_flag_normalized_and_decimal_only() -> None:
    source = readiness_input()
    result = report()

    assert is_dataclass(ProbabilityEventScreenEndToEndReadinessInput)
    assert is_dataclass(ProbabilityEventScreenEndToEndReadinessReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.readiness_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenEndToEndReadinessInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenEndToEndReadinessReport):
            pass

    with pytest.raises(ValueError, match="acquisition_ready"):
        readiness_input(acquisition_ready=1)
    with pytest.raises(ValueError, match="supabase_persistence_ready"):
        readiness_input(supabase_persistence_ready=Decimal("1.000000"))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=_DecimalSubclass("1.000000"))

    hints = get_type_hints(ProbabilityEventScreenEndToEndReadinessReport)
    assert hints["ready_ratio"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenEndToEndReadinessReport(
            acquisition_ready=False,
            screen_contract_ready=True,
            quality_index_ready=True,
            manual_decision_gate_ready=True,
            operator_runbook_ready=True,
            release_gate_ready=True,
            learning_feedback_ready=True,
            supabase_persistence_ready=True,
            end_to_end_ready=False,
            readiness_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="ready_ratio"):
        validate_probability_event_screen_end_to_end_readiness_public_payload(
            {**payload, "ready_ratio": "0.500000"},
        )
    with pytest.raises(ValueError, match="readiness_band"):
        validate_probability_event_screen_end_to_end_readiness_public_payload(
            {**payload, "readiness_band": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_screen_end_to_end_readiness_public_payload(
            {**payload, "paper_only": False},
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
        "submit_order",
        "cancel_order",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
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
            "send",
            "sign",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "wallet" not in lowered
        assert "auth" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered


def test_digest_changes_when_readiness_inputs_change() -> None:
    ready = report()
    attention = report(readonly=False)
    blocked = report(acquisition_ready=False)

    assert ready.digest != attention.digest
    assert ready.digest != blocked.digest
    assert ready.public_payload != attention.public_payload
