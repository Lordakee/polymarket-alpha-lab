from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_manual_research_audit_log_contract_report import (
    PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION,
    ProbabilityEventScreenManualResearchAuditLogContractInput,
    ProbabilityEventScreenManualResearchAuditLogContractReport,
    build_probability_event_screen_manual_research_audit_log_contract_report,
    probability_event_screen_manual_research_audit_log_contract_report_digest,
    probability_event_screen_manual_research_audit_log_contract_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_manual_research_audit_log_contract_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def contract_input(
    **overrides: object,
) -> ProbabilityEventScreenManualResearchAuditLogContractInput:
    values = {
        "ephemeral_log_excluded": True,
        "public_safe_payload_ready": True,
        "supabase_persistence_ready": True,
        "redacted_identifiers_ready": True,
        "review_packet_index_ready": True,
        "operator_safety_ready": True,
        "no_live_execution_surface": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenManualResearchAuditLogContractInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventScreenManualResearchAuditLogContractReport:
    return build_probability_event_screen_manual_research_audit_log_contract_report(
        contract_input(**overrides),
    )


def test_complete_audit_log_contract_is_ready_with_stable_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenManualResearchAuditLogContractReport
    assert is_dataclass(first)
    assert (
        first.config_version
        == PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION
    )
    assert first.audit_log_contract_ready is True
    assert first.contract_band == "ready"
    assert first.ready_ratio == d("1.000000")
    assert first.blocked_reason_codes == ("audit_log_contract_ready",)
    assert first.attention_reason_codes == ()
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert (
        probability_event_screen_manual_research_audit_log_contract_report_digest(first)
        == first.digest
    )

    payload = probability_event_screen_manual_research_audit_log_contract_report_payload(
        first,
    )
    assert payload == first.public_payload
    assert payload["audit_log_contract_ready"] is True
    assert payload["contract_band"] == "ready"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == first.digest
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["audit_log_contract_ready"] = False


def test_supabase_and_review_packet_gaps_are_watch_attention_not_hard_blocks() -> None:
    result = report(
        supabase_persistence_ready=False,
        review_packet_index_ready=False,
    )

    assert result.audit_log_contract_ready is False
    assert result.contract_band == "watch"
    assert result.ready_ratio == d("0.714286")
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == (
        "supabase_persistence_not_ready_attention",
        "review_packet_index_not_ready_attention",
        "audit_log_contract_incomplete_attention",
    )
    assert result.public_payload["ready_ratio"] == "0.714286"


def test_safety_contract_gaps_block_audit_log_contract() -> None:
    result = report(
        ephemeral_log_excluded=False,
        public_safe_payload_ready=False,
        redacted_identifiers_ready=False,
        operator_safety_ready=False,
        no_live_execution_surface=False,
    )

    assert result.audit_log_contract_ready is False
    assert result.contract_band == "blocked"
    assert result.ready_ratio == d("0.285714")
    assert result.blocked_reason_codes == (
        "ephemeral_log_not_excluded",
        "public_safe_payload_not_ready",
        "redacted_identifiers_not_ready",
        "operator_safety_not_ready",
        "live_execution_surface_present",
    )
    assert result.attention_reason_codes == (
        "operator_safety_not_ready_attention",
        "live_execution_surface_present_attention",
        "audit_log_contract_incomplete_attention",
    )


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = contract_input()
    result = report()

    assert is_dataclass(ProbabilityEventScreenManualResearchAuditLogContractInput)
    assert is_dataclass(ProbabilityEventScreenManualResearchAuditLogContractReport)
    assert result.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        input_value.ephemeral_log_excluded = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.audit_log_contract_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenManualResearchAuditLogContractInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenManualResearchAuditLogContractReport):
            pass

    with pytest.raises(ValueError, match="ephemeral_log_excluded"):
        contract_input(ephemeral_log_excluded=1)
    with pytest.raises(ValueError, match="paper_only"):
        contract_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="contract_band"):
        replace(result, contract_band="trade")
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(result, ready_ratio=1)  # type: ignore[arg-type]

    hints = get_type_hints(ProbabilityEventScreenManualResearchAuditLogContractReport)
    for field in fields(ProbabilityEventScreenManualResearchAuditLogContractReport):
        if field.name == "ready_ratio":
            assert hints[field.name] is Decimal
            assert type(getattr(result, field.name)) is Decimal


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload["digest"]

    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_manual_research_audit_log_contract_report_payload(
            replace(report(), digest="0" * 64),
        )
    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_manual_research_audit_log_contract_report_payload(
            {**payload, "audit_log_contract_ready": False},
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
