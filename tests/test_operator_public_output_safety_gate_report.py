from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.operator_public_output_safety_gate_report import (
    OperatorPublicOutputSafetyGateReport,
    build_operator_public_output_safety_gate_report,
    operator_public_output_safety_gate_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_public_output_safety_gate_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def test_safe_operator_output_is_display_ready_with_decimal_counts_and_digest() -> None:
    report = build_operator_public_output_safety_gate_report(
        output_surface_name="strategy_summary_panel",
        payload_field_names=("summary", "confidence_score", "readonly"),
        payload_text_tokens=("watch", "public", "summary"),
        contains_market_identifier=False,
        contains_order_language=False,
        contains_auth_or_wallet_term=False,
        contains_dsn_or_table_term=False,
        audited_by_public_payload_safety=True,
    )
    payload = operator_public_output_safety_gate_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is OperatorPublicOutputSafetyGateReport
    assert report.output_surface_name == "strategy_summary_panel"
    assert report.safe_for_operator_display is True
    assert report.blocked_field_count == d("0")
    assert report.blocked_token_count == d("0")
    assert report.attention_reason_codes == (
        "operator_public_output_safety_gate_pass",
    )
    assert report.blocker_reason_codes == ()
    assert report.ready_ratio == d("1.000000")
    assert report.public_payload_digest == report.derived_validation_digest
    assert len(report.public_payload_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["blocked_field_count"] == "0"
    assert payload["blocked_token_count"] == "0"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["safe_for_operator_display"] is True
    assert payload["public_payload_digest"] == report.public_payload_digest
    assert not any(isinstance(value, float) for value in walk_values(payload))


def test_unsafe_fields_tokens_and_missing_universal_audit_block_operator_display() -> None:
    report = build_operator_public_output_safety_gate_report(
        output_surface_name="operator_decision_ticket",
        payload_field_names=(
            "summary",
            "market_id",
            "wallet_auth_token",
            "recommendation_table",
        ),
        payload_text_tokens=(
            "buy",
            "public",
            "dsn",
            "wallet",
            "market",
        ),
        contains_market_identifier=True,
        contains_order_language=True,
        contains_auth_or_wallet_term=True,
        contains_dsn_or_table_term=True,
        audited_by_public_payload_safety=False,
    )

    assert report.safe_for_operator_display is False
    assert report.blocked_field_count == d("3")
    assert report.blocked_token_count == d("4")
    assert report.ready_ratio == d("0.000000")
    assert report.attention_reason_codes == (
        "operator_public_output_safety_gate_public_payload_audit_missing",
        "operator_public_output_safety_gate_market_identifier_present",
        "operator_public_output_safety_gate_order_language_present",
        "operator_public_output_safety_gate_auth_or_wallet_term_present",
        "operator_public_output_safety_gate_dsn_or_table_term_present",
        "operator_public_output_safety_gate_blocked_field_present",
        "operator_public_output_safety_gate_blocked_token_present",
    )
    assert report.blocker_reason_codes == (
        "operator_public_output_safety_gate_public_payload_audit_missing",
        "operator_public_output_safety_gate_market_identifier_present",
        "operator_public_output_safety_gate_order_language_present",
        "operator_public_output_safety_gate_auth_or_wallet_term_present",
        "operator_public_output_safety_gate_dsn_or_table_term_present",
        "operator_public_output_safety_gate_blocked_field_present",
        "operator_public_output_safety_gate_blocked_token_present",
    )


def test_report_contract_is_frozen_strict_and_requires_readonly_flags() -> None:
    report = OperatorPublicOutputSafetyGateReport(
        output_surface_name="manual_panel",
        payload_field_names=("summary",),
        payload_text_tokens=("public",),
        contains_market_identifier=False,
        contains_order_language=False,
        contains_auth_or_wallet_term=False,
        contains_dsn_or_table_term=False,
        audited_by_public_payload_safety=True,
        safe_for_operator_display=True,
        blocked_field_count=d("0"),
        blocked_token_count=d("0"),
        attention_reason_codes=("operator_public_output_safety_gate_pass",),
        blocker_reason_codes=(),
        ready_ratio=d("1.000000"),
        public_payload_digest=(
            "e9f67d9c6e4d2fb8384b7535e529a4db197b0fbc4b250a6f85318668a0545d23"
        ),
        derived_validation_digest=(
            "e9f67d9c6e4d2fb8384b7535e529a4db197b0fbc4b250a6f85318668a0545d23"
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.safe_for_operator_display = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="output_surface_name"):
        replace(report, output_surface_name=_StringSubclass("manual_panel"))
    with pytest.raises(ValueError, match="payload_field_names"):
        replace(report, payload_field_names=["summary"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocked_field_count"):
        replace(report, blocked_field_count=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_payload_rejects_mutated_digest_and_non_decimal_public_numbers() -> None:
    report = build_operator_public_output_safety_gate_report(
        output_surface_name="operator_panel",
        payload_field_names=("summary",),
        payload_text_tokens=("public",),
        contains_market_identifier=False,
        contains_order_language=False,
        contains_auth_or_wallet_term=False,
        contains_dsn_or_table_term=False,
        audited_by_public_payload_safety=True,
    )
    payload = operator_public_output_safety_gate_report_payload(report)

    tampered = dict(payload)
    tampered["ready_ratio"] = "0.500000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        operator_public_output_safety_gate_report_payload(tampered)

    with pytest.raises(ValueError, match="public payload numerics"):
        operator_public_output_safety_gate_report_payload(
            {
                **payload,
                "blocked_field_count": 0,
            },
        )


def test_builder_rejects_live_payload_surfaces_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="report_only"):
        build_operator_public_output_safety_gate_report(
            output_surface_name="operator_panel",
            payload_field_names=("summary",),
            payload_text_tokens=("public",),
            contains_market_identifier=False,
            contains_order_language=False,
            contains_auth_or_wallet_term=False,
            contains_dsn_or_table_term=False,
            audited_by_public_payload_safety=True,
            report_only=False,
        )
    with pytest.raises(ValueError, match="contains_order_language"):
        build_operator_public_output_safety_gate_report(
            output_surface_name="operator_panel",
            payload_field_names=("summary",),
            payload_text_tokens=("public",),
            contains_market_identifier=False,
            contains_order_language=1,  # type: ignore[arg-type]
            contains_auth_or_wallet_term=False,
            contains_dsn_or_table_term=False,
            audited_by_public_payload_safety=True,
        )
    with pytest.raises(ValueError, match="payload_field_names"):
        build_operator_public_output_safety_gate_report(
            output_surface_name="operator_panel",
            payload_field_names=("live_trading_url",),
            payload_text_tokens=("public",),
            contains_market_identifier=False,
            contains_order_language=False,
            contains_auth_or_wallet_term=False,
            contains_dsn_or_table_term=False,
            audited_by_public_payload_safety=True,
        )


def test_owned_module_has_no_live_network_storage_or_wallet_auth_surface() -> None:
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
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "broker",
        "cancel_order",
        "private_key",
        "api_key",
        "secret_key",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "network",
        "database",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
