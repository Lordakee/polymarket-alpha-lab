from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_screen_commit_readiness_report as api
from polymarket_alpha_lab.probability_event_screen_commit_readiness_report import (
    COMMIT_READINESS_BANDS,
    ProbabilityEventScreenCommitReadinessInput,
    ProbabilityEventScreenCommitReadinessReport,
    build_probability_event_screen_commit_readiness_report,
    probability_event_screen_commit_readiness_report_digest,
    probability_event_screen_commit_readiness_report_to_payload,
    validate_probability_event_screen_commit_readiness_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_commit_readiness_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(**overrides: object) -> ProbabilityEventScreenCommitReadinessInput:
    values = {
        "focused_tests_ready": True,
        "compile_ready": True,
        "diff_check_ready": True,
        "codegraph_sync_ready": True,
        "claude_review_ready": True,
        "public_payload_safety_ready": True,
        "supabase_contract_ready": True,
        "no_live_execution_surface": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenCommitReadinessInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenCommitReadinessReport:
    return build_probability_event_screen_commit_readiness_report(
        readiness_input(**overrides),
    )


def test_commit_readiness_band_vocabulary_is_exact() -> None:
    assert COMMIT_READINESS_BANDS == ("ready", "attention", "blocked")


def test_all_commit_gates_ready_produces_public_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenCommitReadinessReport
    assert is_dataclass(first)
    assert first.commit_readiness_ready is True
    assert first.commit_band == "ready"
    assert first.blocked_reason_codes == ()
    assert first.attention_reason_codes == (
        "probability_event_screen_commit_readiness_ready",
    )
    assert first.ready_ratio == d("1.000000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_screen_commit_readiness_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "focused_tests_ready": True,
        "compile_ready": True,
        "diff_check_ready": True,
        "codegraph_sync_ready": True,
        "claude_review_ready": True,
        "public_payload_safety_ready": True,
        "supabase_contract_ready": True,
        "no_live_execution_surface": True,
        "commit_readiness_ready": True,
        "commit_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_commit_readiness_ready",
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
    assert probability_event_screen_commit_readiness_report_digest(first) == expected_digest
    assert validate_probability_event_screen_commit_readiness_public_payload(payload) == payload
    assert_no_runtime_numbers(payload)


def test_required_precommit_gates_block_in_deterministic_order() -> None:
    result = report(
        focused_tests_ready=False,
        compile_ready=False,
        diff_check_ready=False,
        codegraph_sync_ready=False,
        claude_review_ready=False,
        public_payload_safety_ready=False,
        supabase_contract_ready=False,
    )

    assert result.commit_readiness_ready is False
    assert result.commit_band == "blocked"
    assert result.ready_ratio == d("0.125000")
    assert result.blocked_reason_codes == (
        "commit_focused_tests_not_ready",
        "commit_compile_not_ready",
        "commit_diff_check_not_ready",
        "commit_codegraph_sync_not_ready",
        "commit_claude_review_not_ready",
        "commit_public_payload_safety_not_ready",
        "commit_supabase_contract_not_ready",
    )
    assert result.attention_reason_codes == ()
    assert result.public_payload["ready_ratio"] == "0.125000"


def test_live_execution_surface_gap_is_attention_not_blocked() -> None:
    result = report(no_live_execution_surface=False)

    assert result.commit_readiness_ready is False
    assert result.commit_band == "attention"
    assert result.ready_ratio == d("0.875000")
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == (
        "commit_live_execution_surface_detected",
    )


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = readiness_input()
    result = report()

    assert is_dataclass(ProbabilityEventScreenCommitReadinessInput)
    assert is_dataclass(ProbabilityEventScreenCommitReadinessReport)
    assert input_value.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        input_value.focused_tests_ready = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.commit_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenCommitReadinessInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenCommitReadinessReport):
            pass

    with pytest.raises(ValueError, match="focused_tests_ready"):
        readiness_input(focused_tests_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        readiness_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        readiness_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=1)  # type: ignore[arg-type]

    hints = get_type_hints(ProbabilityEventScreenCommitReadinessReport)
    assert hints["ready_ratio"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenCommitReadinessReport(
            focused_tests_ready=False,
            compile_ready=True,
            diff_check_ready=True,
            codegraph_sync_ready=True,
            claude_review_ready=True,
            public_payload_safety_ready=True,
            supabase_contract_ready=True,
            no_live_execution_surface=True,
            commit_readiness_ready=False,
            commit_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload

    with pytest.raises(ValueError, match="ready_ratio"):
        validate_probability_event_screen_commit_readiness_public_payload(
            {**payload, "ready_ratio": "0.500000"},
        )
    with pytest.raises(ValueError, match="commit_band"):
        validate_probability_event_screen_commit_readiness_public_payload(
            {**payload, "commit_band": "blocked"},
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


def test_digest_changes_when_commit_inputs_change() -> None:
    ready = report()
    attention = report(no_live_execution_surface=False)
    blocked = report(compile_ready=False)

    assert ready.digest != attention.digest
    assert ready.digest != blocked.digest
    assert ready.public_payload != attention.public_payload


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)
