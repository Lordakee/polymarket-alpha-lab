from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.supabase_research_memory_write_contract_report import (
    SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION,
    SupabaseResearchMemoryWriteContractInput,
    SupabaseResearchMemoryWriteContractReport,
    build_supabase_research_memory_write_contract_report,
    supabase_research_memory_write_contract_report_digest,
    supabase_research_memory_write_contract_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_research_memory_write_contract_report.py"
)


def contract_input(
    **overrides: object,
) -> SupabaseResearchMemoryWriteContractInput:
    values = {
        "required_tables_present": True,
        "schema_version_declared": True,
        "idempotency_key_present": True,
        "source_digest_present": True,
        "local_postgres_dsn_validator_present": True,
        "local_postgres_only_confirmed": True,
        "hosted_database_absent": True,
        "no_file_persistence_confirmed": True,
    }
    values.update(overrides)
    return SupabaseResearchMemoryWriteContractInput(**values)


def report(
    **overrides: object,
) -> SupabaseResearchMemoryWriteContractReport:
    return build_supabase_research_memory_write_contract_report(
        contract_input(**overrides),
    )


def test_complete_contract_is_ready_with_stable_public_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is SupabaseResearchMemoryWriteContractReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen
    assert (
        first.config_version
        == SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION
    )
    assert first.contract_status == "ready"
    assert first.reason_codes == ("supabase_research_memory_write_contract_ready",)
    assert first.manual_next_step == (
        "Manual reviewer may approve the planned local Supabase research memory "
        "contract for Phase 2 implementation review."
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.payload_digest == second.payload_digest
    assert supabase_research_memory_write_contract_report_digest(first) == (
        first.payload_digest
    )

    payload = supabase_research_memory_write_contract_report_payload(first)
    assert payload == first.public_payload
    assert payload["contract_status"] == "ready"
    assert payload["reason_codes"] == (
        "supabase_research_memory_write_contract_ready",
    )
    assert payload["payload_digest"] == first.payload_digest
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["contract_status"] = "blocked"


def test_missing_contract_evidence_blocks_with_deterministic_reason_codes() -> None:
    result = report(
        required_tables_present=False,
        schema_version_declared=False,
        idempotency_key_present=False,
        source_digest_present=False,
        local_postgres_dsn_validator_present=False,
        local_postgres_only_confirmed=False,
        hosted_database_absent=False,
        no_file_persistence_confirmed=False,
    )

    assert result.contract_status == "blocked"
    assert result.reason_codes == (
        "required_tables_missing",
        "schema_version_missing",
        "idempotency_key_missing",
        "source_digest_missing",
        "local_postgres_dsn_validator_missing",
        "local_postgres_only_not_confirmed",
        "hosted_database_not_confirmed_absent",
        "file_persistence_not_confirmed",
    )
    assert result.manual_next_step == (
        "Manual reviewer must document the missing local Supabase research memory "
        "contract evidence before Phase 2 implementation review."
    )
    assert result.public_payload["contract_status"] == "blocked"
    assert result.public_payload["reason_codes"] == result.reason_codes


def test_dataclasses_are_frozen_flag_guarded_and_exact_bool_contract() -> None:
    input_value = contract_input()
    result = report()

    assert is_dataclass(SupabaseResearchMemoryWriteContractInput)
    assert is_dataclass(SupabaseResearchMemoryWriteContractReport)
    assert input_value.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        input_value.required_tables_present = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.contract_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(SupabaseResearchMemoryWriteContractInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(SupabaseResearchMemoryWriteContractReport):
            pass

    with pytest.raises(ValueError, match="required_tables_present"):
        contract_input(required_tables_present=1)
    with pytest.raises(ValueError, match="local_postgres_only_confirmed"):
        contract_input(local_postgres_only_confirmed=False).__class__(
            required_tables_present=True,
            schema_version_declared=True,
            idempotency_key_present=True,
            source_digest_present=True,
            local_postgres_dsn_validator_present=True,
            local_postgres_only_confirmed=1,  # type: ignore[arg-type]
            hosted_database_absent=True,
            no_file_persistence_confirmed=True,
        )
    with pytest.raises(ValueError, match="paper_only"):
        contract_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="contract_status"):
        replace(result, contract_status="enabled")
    with pytest.raises(ValueError, match="payload_digest"):
        replace(result, payload_digest="0" * 64)

    hints = get_type_hints(SupabaseResearchMemoryWriteContractReport)
    assert "float" not in {getattr(value, "__name__", "") for value in hints.values()}
    assert "int" not in {getattr(value, "__name__", "") for value in hints.values()}


def test_public_payload_tamper_checks_and_no_database_or_file_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="payload_digest"):
        supabase_research_memory_write_contract_report_payload(
            replace(report(), payload_digest="0" * 64),
        )
    with pytest.raises(ValueError, match="contract_status"):
        supabase_research_memory_write_contract_report_payload(
            {**payload, "contract_status": "blocked"},
        )
    forged = {
        **payload,
        "local_postgres_dsn_validator_present": False,
        "local_postgres_only_confirmed": False,
        "contract_status": "ready",
        "reason_codes": ("supabase_research_memory_write_contract_ready",),
        "manual_next_step": (
            "Manual reviewer may approve the planned local Supabase research memory "
            "contract for Phase 2 implementation review."
        ),
    }
    digest_payload = dict(forged)
    digest_payload["payload_digest"] = ""
    forged["payload_digest"] = sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="contract_status"):
        supabase_research_memory_write_contract_report_payload(forged)

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "postgres://",
        "postgresql://",
        "service_role",
        "token",
        "secret",
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
        "sqlite",
        "pathlib",
        "tempfile",
        "private_key",
        "live",
        "wallet",
        "auth",
        "keys",
        "signature",
        "execute",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    forbidden_call_names = {
        "append",
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
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)


def _is_forbidden_number(value: object) -> bool:
    return isinstance(value, (int, float)) and type(value) is not bool
