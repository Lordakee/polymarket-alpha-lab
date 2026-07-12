from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.manual_execution_safety_interlock_report as api
from polymarket_alpha_lab.manual_execution_safety_interlock_report import (
    ManualExecutionSafetyInterlockInput,
    ManualExecutionSafetyInterlockReport,
    build_manual_execution_safety_interlock_report,
    manual_execution_safety_interlock_report_digest,
    manual_execution_safety_interlock_report_to_public_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/manual_execution_safety_interlock_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def interlock_input(
    *,
    no_live_order_path: bool = True,
    no_wallet_or_auth_path: bool = True,
    paper_only_enforced: bool = True,
    operator_manual_only: bool = True,
    public_payload_safe: bool = True,
    supabase_persistence_ready: bool = True,
    decision_gate_ready: bool = True,
    review_packet_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ManualExecutionSafetyInterlockInput:
    return ManualExecutionSafetyInterlockInput(
        no_live_order_path=no_live_order_path,
        no_wallet_or_auth_path=no_wallet_or_auth_path,
        paper_only_enforced=paper_only_enforced,
        operator_manual_only=operator_manual_only,
        public_payload_safe=public_payload_safe,
        supabase_persistence_ready=supabase_persistence_ready,
        decision_gate_ready=decision_gate_ready,
        review_packet_ready=review_packet_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    value: ManualExecutionSafetyInterlockInput,
) -> ManualExecutionSafetyInterlockReport:
    return build_manual_execution_safety_interlock_report(value)


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def test_all_interlocks_ready_builds_public_payload_and_digest() -> None:
    readiness = report(interlock_input())

    assert is_dataclass(readiness)
    assert readiness.execution_interlock_ready is True
    assert readiness.interlock_band == "ready"
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == ()
    assert readiness.ready_ratio == ONE
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    payload = readiness.public_payload
    assert payload == {
        "no_live_order_path": True,
        "no_wallet_or_auth_path": True,
        "paper_only_enforced": True,
        "operator_manual_only": True,
        "public_payload_safe": True,
        "supabase_persistence_ready": True,
        "decision_gate_ready": True,
        "review_packet_ready": True,
        "execution_interlock_ready": True,
        "interlock_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": readiness.digest,
    }
    assert len(readiness.digest) == 64
    assert readiness.digest == manual_execution_safety_interlock_report_digest(readiness)
    assert_no_float_or_int_values(payload)


def test_blocked_and_attention_reasons_roll_up_in_stable_order() -> None:
    readiness = report(
        interlock_input(
            no_live_order_path=False,
            public_payload_safe=False,
            supabase_persistence_ready=False,
            decision_gate_ready=False,
        ),
    )

    assert readiness.execution_interlock_ready is False
    assert readiness.interlock_band == "blocked"
    assert readiness.blocked_reason_codes == (
        "manual_execution_interlock_live_order_path_present",
        "manual_execution_interlock_public_payload_not_safe",
        "manual_execution_interlock_decision_gate_not_ready",
    )
    assert readiness.attention_reason_codes == (
        "manual_execution_interlock_supabase_persistence_not_ready",
    )
    assert readiness.ready_ratio == Decimal("0.500000")

    payload = manual_execution_safety_interlock_report_to_public_payload(readiness)
    assert payload["execution_interlock_ready"] is False
    assert payload["interlock_band"] == "blocked"
    assert payload["ready_ratio"] == "0.500000"
    assert payload["blocked_reason_codes"] == list(readiness.blocked_reason_codes)
    assert payload["attention_reason_codes"] == list(readiness.attention_reason_codes)
    assert_no_float_or_int_values(payload)


def test_attention_only_band_blocks_ready_state_without_hard_blockers() -> None:
    readiness = report(interlock_input(supabase_persistence_ready=False))

    assert readiness.execution_interlock_ready is False
    assert readiness.interlock_band == "attention"
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == (
        "manual_execution_interlock_supabase_persistence_not_ready",
    )
    assert readiness.ready_ratio == Decimal("0.875000")


def test_dataclasses_are_frozen_bool_input_decimal_ratio_and_flags_are_enforced() -> None:
    input_value = interlock_input()
    readiness = report(input_value)

    with pytest.raises(FrozenInstanceError):
        readiness.interlock_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ManualExecutionSafetyInterlockInput):
            pass

    with pytest.raises(ValueError, match="no_live_order_path must be a bool"):
        interlock_input(no_live_order_path=Decimal("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        interlock_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)

    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(readiness, ready_ratio=1)  # type: ignore[arg-type]

    for field in fields(readiness):
        public_value = getattr(readiness, field.name)
        assert type(public_value) is not float
        assert type(public_value) is not int


def test_report_constructor_rejects_state_that_does_not_match_flags() -> None:
    readiness = report(interlock_input(no_wallet_or_auth_path=False))

    with pytest.raises(ValueError, match="interlock_band must match"):
        replace(readiness, interlock_band="ready")

    with pytest.raises(ValueError, match="blocked_reason_codes must match"):
        replace(readiness, blocked_reason_codes=())

    with pytest.raises(ValueError, match="execution_interlock_ready must match"):
        replace(readiness, execution_interlock_ready=True)


def test_public_payload_is_immutable_and_digest_bound_to_payload() -> None:
    readiness = report(interlock_input())
    payload = readiness.public_payload

    with pytest.raises(TypeError, match="public payload is immutable"):
        payload["interlock_band"] = "blocked"

    with pytest.raises(TypeError, match="public payload is immutable"):
        payload["blocked_reason_codes"].append("changed")

    payload_from_function = manual_execution_safety_interlock_report_to_public_payload(
        readiness,
    )
    assert payload_from_function["digest"] == readiness.digest


def test_module_has_no_external_side_effect_imports_or_execution_hooks() -> None:
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
    }

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(forbidden_imports)

    forbidden_public_names = (
        "connect",
        "persist",
        "send",
        "sign",
        "submit",
        "trade",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(name in lowered for name in forbidden_public_names)

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_source_terms = (
        "place_order",
        "submit_order",
        "sign_order",
        "private_key",
        "api_key",
        "secret",
    )
    assert all(term not in source for term in forbidden_source_terms)
