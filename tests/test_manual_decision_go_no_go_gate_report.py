from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.manual_decision_go_no_go_gate_report import (
    MANUAL_DECISION_GO_NO_GO_GATE_REPORT_VERSION,
    ManualDecisionGoNoGoGateInput,
    ManualDecisionGoNoGoGateReport,
    build_manual_decision_go_no_go_gate_report,
    manual_decision_go_no_go_gate_report_digest,
    manual_decision_go_no_go_gate_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/manual_decision_go_no_go_gate_report.py",
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
    quality_index_ready: bool = True,
    decision_memo_ready: bool = True,
    review_packet_index_ready: bool = True,
    operator_safety_ready: bool = True,
    export_manifest_ready: bool = True,
    manual_review_capacity_ready: bool = True,
    liquidity_exit_ready: bool = True,
    resolution_rule_clarity_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ManualDecisionGoNoGoGateReport:
    return build_manual_decision_go_no_go_gate_report(
        ManualDecisionGoNoGoGateInput(
            quality_index_ready=quality_index_ready,
            decision_memo_ready=decision_memo_ready,
            review_packet_index_ready=review_packet_index_ready,
            operator_safety_ready=operator_safety_ready,
            export_manifest_ready=export_manifest_ready,
            manual_review_capacity_ready=manual_review_capacity_ready,
            liquidity_exit_ready=liquidity_exit_ready,
            resolution_rule_clarity_ready=resolution_rule_clarity_ready,
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        ),
    )


def assert_public_numbers_are_decimals(report: ManualDecisionGoNoGoGateReport) -> None:
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name in {"ready_ratio", "ready_gate_count", "blocked_gate_count"}:
            assert type(value) is Decimal
        elif field.name.endswith("_ready") or field.name in {
            "paper_only",
            "report_only",
            "readonly",
        }:
            assert type(value) is bool


def test_all_required_inputs_ready_emit_go_report_with_decimal_public_payload() -> None:
    report = build()
    payload = manual_decision_go_no_go_gate_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is ManualDecisionGoNoGoGateReport
    assert is_dataclass(report)
    assert report.config_version == MANUAL_DECISION_GO_NO_GO_GATE_REPORT_VERSION
    assert report.ready_for_manual_decision is True
    assert report.go_no_go_band == "go"
    assert report.ready_gate_count == d("8.000000")
    assert report.blocked_gate_count == ZERO
    assert report.ready_ratio == ONE
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ("manual_decision_go_no_go_gate_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_payload == payload
    assert payload["ready_ratio"] == "1.000000"
    assert payload["ready_gate_count"] == "8.000000"
    assert payload["blocked_gate_count"] == "0.000000"
    assert payload["digest"] == report.digest
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert_public_numbers_are_decimals(report)

    digest = manual_decision_go_no_go_gate_report_digest(report)
    assert "ready_for_manual_decision=true" in digest
    assert "band=go" in digest
    assert "ready_ratio=1.000000" in digest
    assert f"digest={report.digest}" in digest


def test_missing_required_gate_blocks_manual_decision_with_reason_codes() -> None:
    report = build(
        quality_index_ready=False,
        decision_memo_ready=False,
        review_packet_index_ready=False,
        operator_safety_ready=False,
        export_manifest_ready=False,
        manual_review_capacity_ready=False,
        liquidity_exit_ready=False,
        resolution_rule_clarity_ready=False,
    )

    assert report.ready_for_manual_decision is False
    assert report.go_no_go_band == "no_go"
    assert report.ready_gate_count == ZERO
    assert report.blocked_gate_count == d("8.000000")
    assert report.ready_ratio == ZERO
    assert report.blocked_reason_codes == (
        "quality_index_not_ready",
        "decision_memo_not_ready",
        "review_packet_index_not_ready",
        "operator_safety_not_ready",
        "export_manifest_not_ready",
        "manual_review_capacity_not_ready",
        "liquidity_exit_not_ready",
        "resolution_rule_clarity_not_ready",
    )
    assert report.attention_reason_codes == (
        "manual_decision_go_no_go_gate_blocked",
    )


def test_partial_gate_readiness_uses_attention_band_without_go() -> None:
    report = build(
        liquidity_exit_ready=False,
        resolution_rule_clarity_ready=False,
    )

    assert report.ready_for_manual_decision is False
    assert report.go_no_go_band == "attention"
    assert report.ready_gate_count == d("6.000000")
    assert report.blocked_gate_count == d("2.000000")
    assert report.ready_ratio == d("0.750000")
    assert report.blocked_reason_codes == (
        "liquidity_exit_not_ready",
        "resolution_rule_clarity_not_ready",
    )
    assert report.attention_reason_codes == (
        "manual_decision_go_no_go_gate_attention",
        "liquidity_exit_requires_manual_attention",
        "resolution_rule_clarity_requires_manual_attention",
    )


def test_report_contract_is_frozen_strict_readonly_and_decimal_only() -> None:
    report = build()

    with pytest.raises(FrozenInstanceError):
        report.ready_ratio = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="ready_gate_count"):
        replace(report, ready_gate_count=8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        build(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        build(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build(readonly=False)
    with pytest.raises(ValueError, match="quality_index_ready"):
        build_manual_decision_go_no_go_gate_report(
            ManualDecisionGoNoGoGateInput(
                quality_index_ready=1,  # type: ignore[arg-type]
                decision_memo_ready=True,
                review_packet_index_ready=True,
                operator_safety_ready=True,
                export_manifest_ready=True,
                manual_review_capacity_ready=True,
                liquidity_exit_ready=True,
                resolution_rule_clarity_ready=True,
            ),
        )


def test_payload_rejects_mutated_digest_and_public_numeric_values() -> None:
    report = build()
    payload = manual_decision_go_no_go_gate_report_payload(report)

    tampered = dict(payload)
    tampered["ready_ratio"] = "0.875000"
    with pytest.raises(ValueError, match="digest"):
        manual_decision_go_no_go_gate_report_payload(tampered)

    with pytest.raises(ValueError, match="public payload numerics"):
        manual_decision_go_no_go_gate_report_payload(
            {
                **payload,
                "ready_gate_count": 8,
            },
        )


def test_owned_module_has_no_live_network_storage_wallet_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

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
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
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
    }
    assert not (forbidden_import_roots & {name.split(".", 1)[0] for name in imported_modules})

    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "sign_transaction",
    }
    assert not (forbidden_call_names & set(call_names))
    assert not (
        {
            "wallet",
            "auth",
            "private_key",
            "order_execution",
            "live_trading",
        }
        & set(attribute_names)
    )
