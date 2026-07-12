from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_screen_phase1_boundary_report as api
from polymarket_alpha_lab.probability_event_screen_phase1_boundary_report import (
    PHASE1_BOUNDARY_BANDS,
    ProbabilityEventScreenPhase1BoundaryInput,
    ProbabilityEventScreenPhase1BoundaryReport,
    build_probability_event_screen_phase1_boundary_report,
    probability_event_screen_phase1_boundary_report_digest,
    probability_event_screen_phase1_boundary_report_to_payload,
    validate_probability_event_screen_phase1_boundary_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_phase1_boundary_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def boundary_input(**overrides: object) -> ProbabilityEventScreenPhase1BoundaryInput:
    values = {
        "paper_only_enforced": True,
        "report_only_enforced": True,
        "readonly_enforced": True,
        "no_wallet_or_auth_path": True,
        "no_live_order_path": True,
        "manual_only_execution_ready": True,
        "public_payload_safety_ready": True,
        "supabase_persistence_ready": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenPhase1BoundaryInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenPhase1BoundaryReport:
    return build_probability_event_screen_phase1_boundary_report(
        boundary_input(**overrides),
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


def test_phase1_boundary_band_vocabulary_is_exact() -> None:
    assert PHASE1_BOUNDARY_BANDS == ("ready", "attention", "blocked")


def test_all_boundary_controls_ready_emits_readonly_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenPhase1BoundaryReport
    assert is_dataclass(first)
    assert first.phase1_boundary_ready is True
    assert first.boundary_band == "ready"
    assert first.blocked_reason_codes == ()
    assert first.attention_reason_codes == (
        "probability_event_screen_phase1_boundary_ready",
    )
    assert first.ready_ratio == d("1.000000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_screen_phase1_boundary_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "paper_only_enforced": True,
        "report_only_enforced": True,
        "readonly_enforced": True,
        "no_wallet_or_auth_path": True,
        "no_live_order_path": True,
        "manual_only_execution_ready": True,
        "public_payload_safety_ready": True,
        "supabase_persistence_ready": True,
        "phase1_boundary_ready": True,
        "boundary_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_phase1_boundary_ready",
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
    assert probability_event_screen_phase1_boundary_report_digest(first) == expected_digest
    assert validate_probability_event_screen_phase1_boundary_public_payload(payload) == payload
    assert_no_runtime_numbers(payload)


def test_boundary_control_gaps_block_in_deterministic_order() -> None:
    result = report(
        paper_only_enforced=False,
        report_only_enforced=False,
        readonly_enforced=False,
        no_wallet_or_auth_path=False,
        no_live_order_path=False,
        manual_only_execution_ready=False,
        public_payload_safety_ready=False,
        supabase_persistence_ready=False,
    )

    assert result.phase1_boundary_ready is False
    assert result.boundary_band == "blocked"
    assert result.ready_ratio == d("0.000000")
    assert result.blocked_reason_codes == (
        "phase1_boundary_paper_only_not_enforced",
        "phase1_boundary_report_only_not_enforced",
        "phase1_boundary_readonly_not_enforced",
        "phase1_boundary_wallet_or_auth_path_available",
        "phase1_boundary_live_order_path_available",
        "phase1_boundary_manual_only_execution_not_ready",
        "phase1_boundary_public_payload_safety_not_ready",
        "phase1_boundary_supabase_persistence_not_ready",
    )
    assert result.attention_reason_codes == ()
    assert result.public_payload["ready_ratio"] == "0.000000"


def test_outer_mode_flag_gaps_are_attention_not_blocked() -> None:
    result = report(paper_only=False, report_only=False, readonly=False)

    assert result.phase1_boundary_ready is False
    assert result.boundary_band == "attention"
    assert result.ready_ratio == d("1.000000")
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == (
        "phase1_boundary_paper_only_flag_not_set",
        "phase1_boundary_report_only_flag_not_set",
        "phase1_boundary_readonly_flag_not_set",
    )
    assert result.public_payload["paper_only"] is True
    assert result.public_payload["report_only"] is True
    assert result.public_payload["readonly"] is True


def test_dataclasses_are_frozen_flag_normalized_and_decimal_only() -> None:
    source = boundary_input()
    result = report()

    assert is_dataclass(ProbabilityEventScreenPhase1BoundaryInput)
    assert is_dataclass(ProbabilityEventScreenPhase1BoundaryReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.boundary_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenPhase1BoundaryInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenPhase1BoundaryReport):
            pass

    with pytest.raises(ValueError, match="paper_only_enforced"):
        boundary_input(paper_only_enforced=1)
    with pytest.raises(ValueError, match="supabase_persistence_ready"):
        boundary_input(supabase_persistence_ready=Decimal("1.000000"))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=_DecimalSubclass("1.000000"))

    hints = get_type_hints(ProbabilityEventScreenPhase1BoundaryReport)
    assert hints["ready_ratio"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenPhase1BoundaryReport(
            paper_only_enforced=False,
            report_only_enforced=True,
            readonly_enforced=True,
            no_wallet_or_auth_path=True,
            no_live_order_path=True,
            manual_only_execution_ready=True,
            public_payload_safety_ready=True,
            supabase_persistence_ready=True,
            phase1_boundary_ready=False,
            boundary_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="ready_ratio"):
        validate_probability_event_screen_phase1_boundary_public_payload(
            {**payload, "ready_ratio": "0.500000"},
        )
    with pytest.raises(ValueError, match="boundary_band"):
        validate_probability_event_screen_phase1_boundary_public_payload(
            {**payload, "boundary_band": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_screen_phase1_boundary_public_payload(
            {**payload, "paper_only": False},
        )

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


def test_digest_changes_when_boundary_inputs_change() -> None:
    ready = report()
    attention = report(readonly=False)
    blocked = report(no_live_order_path=False)

    assert ready.digest != attention.digest
    assert ready.digest != blocked.digest
    assert ready.public_payload != attention.public_payload
