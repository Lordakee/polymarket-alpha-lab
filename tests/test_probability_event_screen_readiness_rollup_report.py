from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_screen_readiness_rollup_report as api
from polymarket_alpha_lab.probability_event_screen_readiness_rollup_report import (
    ProbabilityEventScreenReadinessRollupInput,
    ProbabilityEventScreenReadinessRollupReport,
    READINESS_ROLLUP_BANDS,
    build_probability_event_screen_readiness_rollup_report,
    probability_event_screen_readiness_rollup_report_digest,
    probability_event_screen_readiness_rollup_report_to_payload,
    validate_probability_event_screen_readiness_rollup_public_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_readiness_rollup_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def rollup_input(
    **overrides: object,
) -> ProbabilityEventScreenReadinessRollupInput:
    values = {
        "end_to_end_ready": True,
        "system_health_ready": True,
        "validation_matrix_ready": True,
        "node_handoff_ready": True,
        "operator_dashboard_ready": True,
        "operator_runbook_ready": True,
        "release_gate_ready": True,
        "knowledge_base_index_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenReadinessRollupInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenReadinessRollupReport:
    return build_probability_event_screen_readiness_rollup_report(
        rollup_input(**overrides),
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


def test_readiness_rollup_band_vocabulary_is_exact() -> None:
    assert READINESS_ROLLUP_BANDS == ("ready", "attention", "blocked")


def test_all_readiness_inputs_ready_emits_readonly_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenReadinessRollupReport
    assert is_dataclass(first)
    assert first.readiness_rollup_ready is True
    assert first.rollup_band == "ready"
    assert first.blocked_reason_codes == ()
    assert first.attention_reason_codes == (
        "probability_event_screen_readiness_rollup_ready",
    )
    assert first.ready_ratio == ONE
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_screen_readiness_rollup_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "end_to_end_ready": True,
        "system_health_ready": True,
        "validation_matrix_ready": True,
        "node_handoff_ready": True,
        "operator_dashboard_ready": True,
        "operator_runbook_ready": True,
        "release_gate_ready": True,
        "knowledge_base_index_ready": True,
        "readiness_rollup_ready": True,
        "rollup_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_readiness_rollup_ready",
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
    assert probability_event_screen_readiness_rollup_report_digest(first) == expected_digest
    assert validate_probability_event_screen_readiness_rollup_public_payload(payload) == payload
    assert_no_runtime_numbers(payload)


def test_missing_required_readiness_inputs_block_in_deterministic_order() -> None:
    result = report(
        end_to_end_ready=False,
        system_health_ready=False,
        validation_matrix_ready=False,
        node_handoff_ready=False,
        operator_dashboard_ready=False,
        operator_runbook_ready=False,
        release_gate_ready=False,
        knowledge_base_index_ready=False,
    )

    assert result.readiness_rollup_ready is False
    assert result.rollup_band == "blocked"
    assert result.ready_ratio == ZERO
    assert result.blocked_reason_codes == (
        "rollup_end_to_end_not_ready",
        "rollup_system_health_not_ready",
        "rollup_validation_matrix_not_ready",
        "rollup_node_handoff_not_ready",
        "rollup_operator_dashboard_not_ready",
        "rollup_operator_runbook_not_ready",
        "rollup_release_gate_not_ready",
        "rollup_knowledge_base_index_not_ready",
    )
    assert result.attention_reason_codes == ()
    assert result.public_payload["ready_ratio"] == "0.000000"


def test_paper_report_readonly_flag_gaps_are_attention_not_blocked() -> None:
    result = report(paper_only=False, report_only=False, readonly=False)

    assert result.readiness_rollup_ready is False
    assert result.rollup_band == "attention"
    assert result.ready_ratio == ONE
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == (
        "rollup_paper_only_flag_not_set",
        "rollup_report_only_flag_not_set",
        "rollup_readonly_flag_not_set",
    )
    assert result.public_payload["paper_only"] is True
    assert result.public_payload["report_only"] is True
    assert result.public_payload["readonly"] is True


def test_dataclasses_are_frozen_flag_normalized_and_decimal_only() -> None:
    source = rollup_input()
    result = report()

    assert is_dataclass(ProbabilityEventScreenReadinessRollupInput)
    assert is_dataclass(ProbabilityEventScreenReadinessRollupReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.rollup_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenReadinessRollupInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenReadinessRollupReport):
            pass

    with pytest.raises(ValueError, match="end_to_end_ready"):
        rollup_input(end_to_end_ready=1)
    with pytest.raises(ValueError, match="knowledge_base_index_ready"):
        rollup_input(knowledge_base_index_ready=Decimal("1.000000"))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=_DecimalSubclass("1.000000"))

    hints = get_type_hints(ProbabilityEventScreenReadinessRollupReport)
    assert hints["ready_ratio"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenReadinessRollupReport(
            end_to_end_ready=False,
            system_health_ready=True,
            validation_matrix_ready=True,
            node_handoff_ready=True,
            operator_dashboard_ready=True,
            operator_runbook_ready=True,
            release_gate_ready=True,
            knowledge_base_index_ready=True,
            readiness_rollup_ready=False,
            rollup_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="ready_ratio"):
        validate_probability_event_screen_readiness_rollup_public_payload(
            {**payload, "ready_ratio": "0.500000"},
        )
    with pytest.raises(ValueError, match="rollup_band"):
        validate_probability_event_screen_readiness_rollup_public_payload(
            {**payload, "rollup_band": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_screen_readiness_rollup_public_payload(
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
        "replace_order",
        "create_order",
        ".open(",
        "open(",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.partition(".")[0])
    assert not {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
    } & imported_roots


def test_public_api_surface_is_narrow_and_readonly() -> None:
    assert api.__all__ == (
        "ProbabilityEventScreenReadinessRollupInput",
        "ProbabilityEventScreenReadinessRollupReport",
        "READINESS_ROLLUP_BANDS",
        "build_probability_event_screen_readiness_rollup_report",
        "probability_event_screen_readiness_rollup_report_digest",
        "probability_event_screen_readiness_rollup_report_to_payload",
        "validate_probability_event_screen_readiness_rollup_public_payload",
    )

    forbidden_fragments = (
        "auth",
        "wallet",
        "database",
        "network",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
    for cls in (
        ProbabilityEventScreenReadinessRollupInput,
        ProbabilityEventScreenReadinessRollupReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)
