from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.operator_final_go_no_go_packet_readiness_report import (
    OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION,
    OperatorFinalGoNoGoPacketReadinessInput,
    OperatorFinalGoNoGoPacketReadinessReport,
    build_operator_final_go_no_go_packet_readiness_report,
    operator_final_go_no_go_packet_readiness_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_final_go_no_go_packet_readiness_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: Any) -> tuple[Any, ...]:
    values: list[Any] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def build(
    *,
    all_required_gates_passed: bool = True,
    manual_attestation_present: bool = True,
    latest_packet_digest_present: bool = True,
    cost_recheck_passed: bool = True,
    source_freshness_passed: bool = True,
    memory_policy_passed: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OperatorFinalGoNoGoPacketReadinessReport:
    return build_operator_final_go_no_go_packet_readiness_report(
        OperatorFinalGoNoGoPacketReadinessInput(
            all_required_gates_passed=all_required_gates_passed,
            manual_attestation_present=manual_attestation_present,
            latest_packet_digest_present=latest_packet_digest_present,
            cost_recheck_passed=cost_recheck_passed,
            source_freshness_passed=source_freshness_passed,
            memory_policy_passed=memory_policy_passed,
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        ),
    )


def test_all_phase_1_gates_ready_emit_human_review_go_packet() -> None:
    report = build()
    payload = operator_final_go_no_go_packet_readiness_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is OperatorFinalGoNoGoPacketReadinessReport
    assert is_dataclass(report)
    assert report.config_version == OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION
    assert report.go_no_go_status == "go"
    assert report.reason_codes == ("operator_final_go_no_go_packet_ready",)
    assert report.manual_next_step == "human_final_review_required"
    assert report.ready_gate_count == d("6.000000")
    assert report.blocked_gate_count == ZERO
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_payload == payload
    assert payload["ready_gate_count"] == "6.000000"
    assert payload["blocked_gate_count"] == "0.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["payload_digest"] == report.payload_digest
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "order" not in json.dumps(payload, sort_keys=True).lower()


def test_missing_manual_attestation_blocks_final_go_without_execution_path() -> None:
    report = build(manual_attestation_present=False)

    assert report.go_no_go_status == "no_go"
    assert report.reason_codes == ("manual_attestation_missing",)
    assert report.manual_next_step == "collect_manual_attestation_before_final_review"
    assert report.ready_gate_count == d("5.000000")
    assert report.blocked_gate_count == d("1.000000")
    assert report.ready_ratio == d("0.833333")


def test_multiple_failed_packet_readiness_checks_preserve_reason_priority() -> None:
    report = build(
        all_required_gates_passed=False,
        latest_packet_digest_present=False,
        cost_recheck_passed=False,
        source_freshness_passed=False,
        memory_policy_passed=False,
    )

    assert report.go_no_go_status == "no_go"
    assert report.reason_codes == (
        "required_gates_failed",
        "latest_packet_digest_missing",
        "cost_recheck_failed",
        "source_freshness_failed",
        "memory_policy_failed",
    )
    assert report.manual_next_step == "resolve_blockers_before_final_review"
    assert report.ready_gate_count == d("1.000000")
    assert report.blocked_gate_count == d("5.000000")
    assert report.ready_ratio == d("0.166667")


def test_contract_is_frozen_decimal_only_and_strictly_readonly() -> None:
    report = build()

    with pytest.raises(FrozenInstanceError):
        report.go_no_go_status = "no_go"  # type: ignore[misc]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="ready_gate_count"):
        replace(report, ready_gate_count=6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        build(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        build(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build(readonly=False)
    with pytest.raises(ValueError, match="all_required_gates_passed"):
        build_operator_final_go_no_go_packet_readiness_report(
            OperatorFinalGoNoGoPacketReadinessInput(
                all_required_gates_passed=1,  # type: ignore[arg-type]
                manual_attestation_present=True,
                latest_packet_digest_present=True,
                cost_recheck_passed=True,
                source_freshness_passed=True,
                memory_policy_passed=True,
            ),
        )
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name in {"ready_gate_count", "blocked_gate_count", "ready_ratio"}:
            assert type(value) is Decimal


def test_payload_rejects_mutated_digest_and_numeric_public_values() -> None:
    report = build()
    payload = operator_final_go_no_go_packet_readiness_report_payload(report)

    tampered = dict(payload)
    tampered["ready_ratio"] = "0.500000"
    with pytest.raises(ValueError, match="payload_digest"):
        operator_final_go_no_go_packet_readiness_report_payload(tampered)

    with pytest.raises(ValueError, match="public payload numerics"):
        operator_final_go_no_go_packet_readiness_report_payload(
            {
                **payload,
                "ready_gate_count": 6,
            },
        )


def test_owned_module_has_no_live_storage_auth_wallet_order_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden_text in (
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "auto",
        "execute",
        "jsonl",
        "open(",
        "write(",
        "path(",
    ):
        assert forbidden_text not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    assert not (forbidden_import_roots & {name.split(".", 1)[0] for name in imported_modules})

    forbidden_call_names = {
        "connect",
        "executemany",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "urlopen",
    }
    assert not (forbidden_call_names & set(call_names))
