from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_screening_audit_trail_readiness_report import (
    StrategyScreeningAuditTrailReadinessReport,
    build_strategy_screening_audit_trail_readiness_report,
    strategy_screening_audit_trail_readiness_digest,
    strategy_screening_audit_trail_readiness_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_screening_audit_trail_readiness_report.py"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: bool) -> StrategyScreeningAuditTrailReadinessReport:
    values = {
        "screen_contract_digest_present": True,
        "research_packet_digest_present": True,
        "cost_gate_digest_present": True,
        "team_route_digest_present": True,
        "memory_context_digest_present": True,
        "operator_safety_digest_present": True,
        "supabase_persistence_ready": True,
        "ephemeral_log_excluded": True,
    }
    values.update(overrides)
    return build_strategy_screening_audit_trail_readiness_report(**values)


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk(child))
    return (value,)


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(value) is Decimal, field.name


def test_all_required_digests_and_guards_ready_with_stable_payload_digest() -> None:
    readiness = report()

    assert is_dataclass(readiness)
    assert readiness.audit_trail_ready is True
    assert readiness.missing_digest_count == ZERO
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == (
        "strategy_screening_audit_trail_readiness_ready",
    )
    assert readiness.ready_ratio == ONE
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    payload = strategy_screening_audit_trail_readiness_payload(readiness)
    assert payload == readiness.public_payload
    assert payload["audit_trail_ready"] is True
    assert payload["missing_digest_count"] == "0.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == readiness.digest
    assert len(readiness.digest) == 64
    assert readiness.digest == strategy_screening_audit_trail_readiness_digest(readiness)
    assert not any(type(value) in (Decimal, float, int) for value in walk(payload))
    json.dumps(payload, sort_keys=True)


def test_missing_digests_block_and_operator_persistence_guards_get_attention() -> None:
    readiness = report(
        research_packet_digest_present=False,
        team_route_digest_present=False,
        supabase_persistence_ready=False,
        ephemeral_log_excluded=False,
    )

    assert readiness.audit_trail_ready is False
    assert readiness.missing_digest_count == d("2.000000")
    assert readiness.blocked_reason_codes == (
        "strategy_screening_audit_trail_research_packet_digest_missing",
        "strategy_screening_audit_trail_team_route_digest_missing",
    )
    assert readiness.attention_reason_codes == (
        "strategy_screening_audit_trail_supabase_persistence_not_ready",
        "strategy_screening_audit_trail_ephemeral_log_not_excluded",
    )
    assert readiness.ready_ratio == d("0.500000")

    same = report(
        ephemeral_log_excluded=False,
        supabase_persistence_ready=False,
        team_route_digest_present=False,
        research_packet_digest_present=False,
    )
    assert readiness == same


def test_dataclass_is_frozen_decimal_only_and_validates_bool_inputs() -> None:
    readiness = report(screen_contract_digest_present=False)

    with pytest.raises(FrozenInstanceError):
        readiness.audit_trail_ready = True  # type: ignore[misc]
    with pytest.raises(ValueError, match="screen_contract_digest_present must be a bool"):
        report(screen_contract_digest_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(readiness, paper_only=False)
    with pytest.raises(ValueError, match="missing_digest_count"):
        replace(readiness, missing_digest_count=ZERO)
    with pytest.raises(ValueError, match="digest must match public payload"):
        replace(readiness, digest="0" * 64)

    assert_public_numeric_fields_are_decimal(readiness)
    for public_type in (StrategyScreeningAuditTrailReadinessReport,):
        assert is_dataclass(public_type)
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) and field.type is not int for field in fields(public_type))


def test_module_is_read_only_report_only_paper_only_without_action_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "order",
        "trade",
        "broker",
        "position",
        "private_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "connect(",
        "execute(",
        "fetch(",
        "insert",
        "upsert",
        "delete",
        "database",
        "network",
        "live trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
        "int",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
