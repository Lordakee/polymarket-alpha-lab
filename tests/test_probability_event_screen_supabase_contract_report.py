from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_supabase_contract_report import (
    PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION,
    ProbabilityEventScreenSupabaseContractInput,
    ProbabilityEventScreenSupabaseContractReport,
    build_probability_event_screen_supabase_contract_report,
    validate_probability_event_screen_supabase_contract_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_supabase_contract_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def contract_input(**overrides: object) -> ProbabilityEventScreenSupabaseContractInput:
    values = {
        "table_contract_ready": True,
        "required_columns_present": True,
        "jsonb_payload_ready": True,
        "redacted_payload_ready": True,
        "local_dsn_validated": True,
        "remote_host_blocked": True,
        "migration_revision_current": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenSupabaseContractInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenSupabaseContractReport:
    return build_probability_event_screen_supabase_contract_report(
        contract_input(**overrides),
    )


def test_all_contract_checks_ready_produces_readonly_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenSupabaseContractReport
    assert is_dataclass(first)
    assert first.config_version == PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION
    assert first.contract_name == "ProbabilityEventScreen"
    assert first.persistence_surface == "local_supabase_postgres"
    assert first.persistence_ready is True
    assert first.check_count == d("7.000000")
    assert first.ready_check_count == d("7.000000")
    assert first.blocked_check_count == d("0.000000")
    assert first.attention_check_count == d("0.000000")
    assert first.ready_check_ratio == d("1.000000")
    assert first.reason_codes == (
        "table_contract_ready",
        "required_columns_present",
        "jsonb_payload_ready",
        "redacted_payload_ready",
        "local_dsn_validated",
        "remote_host_blocked",
        "migration_revision_current",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest

    payload = first.public_payload
    assert payload["persistence_ready"] is True
    assert payload["check_count"] == "7.000000"
    assert payload["ready_check_ratio"] == "1.000000"
    assert payload["digest"] == first.digest
    assert validate_probability_event_screen_supabase_contract_public_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["persistence_ready"] = False


def test_blocked_and_attention_checks_roll_up_reason_codes_and_ratio() -> None:
    result = report(
        table_contract_ready=False,
        required_columns_present=False,
        redacted_payload_ready=False,
        remote_host_blocked=False,
        migration_revision_current=False,
    )

    assert result.persistence_ready is False
    assert result.check_count == d("7.000000")
    assert result.ready_check_count == d("2.000000")
    assert result.blocked_check_count == d("4.000000")
    assert result.attention_check_count == d("1.000000")
    assert result.ready_check_ratio == d("0.285714")
    assert result.reason_codes == (
        "table_contract_missing",
        "required_columns_missing",
        "jsonb_payload_ready",
        "redacted_payload_not_ready",
        "local_dsn_validated",
        "remote_host_not_blocked",
        "migration_revision_outdated",
    )
    assert result.public_payload["blocked_check_count"] == "4.000000"
    assert result.public_payload["attention_check_count"] == "1.000000"


def test_migration_revision_gap_is_attention_not_blocked() -> None:
    result = report(migration_revision_current=False)

    assert result.persistence_ready is False
    assert result.ready_check_count == d("6.000000")
    assert result.blocked_check_count == d("0.000000")
    assert result.attention_check_count == d("1.000000")
    assert result.ready_check_ratio == d("0.857143")
    assert result.reason_codes[-1] == "migration_revision_outdated"


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = contract_input()
    result = report()

    with pytest.raises(FrozenInstanceError):
        input_value.table_contract_ready = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.persistence_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenSupabaseContractInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenSupabaseContractReport):
            pass

    with pytest.raises(ValueError, match="table_contract_ready"):
        contract_input(table_contract_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        contract_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="blocked_check_count"):
        replace(result, blocked_check_count=0)  # type: ignore[arg-type]

    numeric_fields = {
        "check_count",
        "ready_check_count",
        "blocked_check_count",
        "attention_check_count",
        "ready_check_ratio",
    }
    hints = get_type_hints(ProbabilityEventScreenSupabaseContractReport)
    for field in fields(ProbabilityEventScreenSupabaseContractReport):
        if field.name in numeric_fields:
            assert hints[field.name] is Decimal
    _assert_public_numeric_values_are_decimal(result)


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload["digest"]

    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_screen_supabase_contract_public_payload(
            {**payload, "persistence_ready": False},
        )
    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_screen_supabase_contract_public_payload(
            {**payload, "digest": "0" * 64},
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
        "place_order",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
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
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
    }
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(name in forbidden_call_names for name in call_names)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item_value in value.values():
            values.extend(_walk_payload_values(item_value))
    elif isinstance(value, (list, tuple)):
        for item_value in value:
            values.extend(_walk_payload_values(item_value))
    else:
        values.append(value)
    return tuple(values)


def _is_forbidden_number(value: object) -> bool:
    return type(value) is int or type(value) is float


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for child in value.values():
            _assert_public_numeric_values_are_decimal(child)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            _assert_public_numeric_values_are_decimal(child)
