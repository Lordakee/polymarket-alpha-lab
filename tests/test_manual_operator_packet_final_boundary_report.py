from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.manual_operator_packet_final_boundary_report import (
    MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION,
    ManualOperatorPacketFinalBoundaryInput,
    ManualOperatorPacketFinalBoundaryReport,
    build_manual_operator_packet_final_boundary_report,
    manual_operator_packet_final_boundary_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/manual_operator_packet_final_boundary_report.py",
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


def test_build_report_aggregates_final_manual_packet_boundary() -> None:
    report = build_manual_operator_packet_final_boundary_report(
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="macro_rates",
            source_quality_status="pass",
            memory_policy_status="pass",
            forecast_vs_price_edge_status="watch",
            costs_status="pass",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="yes",
            reason_codes=(
                "forecast_edge_requires_manual_review",
                "source_quality_confirmed",
                "liquidity_capacity_confirmed",
            ),
            manual_next_step="paper_review_check_forecast_edge",
        ),
    )
    payload = manual_operator_packet_final_boundary_report_payload(report)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert type(report) is ManualOperatorPacketFinalBoundaryReport
    assert report.config_version == MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION
    assert report.team_owner == "macro_rates"
    assert report.final_status == "watch"
    assert report.paper_review_only is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.boundary_check_count == d("7")
    assert report.pass_check_count == d("6")
    assert report.watch_check_count == d("1")
    assert report.blocked_check_count == d("0")
    assert report.ready_ratio == d("0.857143")
    assert report.reason_codes == (
        "forecast_edge_requires_manual_review",
        "source_quality_confirmed",
        "liquidity_capacity_confirmed",
        "manual_operator_packet_final_boundary_watch",
    )
    assert len(report.derived_validation_digest) == 64
    assert payload == {
        "config_version": MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION,
        "team_owner": "macro_rates",
        "source_quality_status": "pass",
        "memory_policy_status": "pass",
        "forecast_vs_price_edge_status": "watch",
        "costs_status": "pass",
        "liquidity_status": "pass",
        "resolution_risk_status": "pass",
        "selected_side": "yes",
        "final_status": "watch",
        "reason_codes": [
            "forecast_edge_requires_manual_review",
            "source_quality_confirmed",
            "liquidity_capacity_confirmed",
            "manual_operator_packet_final_boundary_watch",
        ],
        "manual_next_step": "paper_review_check_forecast_edge",
        "boundary_check_count": "7",
        "pass_check_count": "6",
        "watch_check_count": "1",
        "blocked_check_count": "0",
        "ready_ratio": "0.857143",
        "paper_review_only": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "derived_validation_digest": report.derived_validation_digest,
    }
    assert not any(isinstance(value, float) for value in walk_values(payload))


def test_blocked_status_wins_and_requires_paper_review_next_step() -> None:
    report = build_manual_operator_packet_final_boundary_report(
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="equity_indices",
            source_quality_status="pass",
            memory_policy_status="blocked",
            forecast_vs_price_edge_status="pass",
            costs_status="watch",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="no",
            reason_codes=("memory_policy_conflict", "cost_assumption_review"),
            manual_next_step="paper_review_resolve_memory_policy",
        ),
    )

    assert report.final_status == "blocked"
    assert report.manual_next_step == "paper_review_resolve_memory_policy"
    assert report.pass_check_count == d("5")
    assert report.watch_check_count == d("1")
    assert report.blocked_check_count == d("1")
    assert report.ready_ratio == d("0.714286")
    assert report.reason_codes == (
        "memory_policy_conflict",
        "cost_assumption_review",
        "manual_operator_packet_final_boundary_blocked",
    )

    with pytest.raises(ValueError, match="manual_next_step"):
        replace(report, manual_next_step="review_resolve_memory_policy")


def test_manual_next_step_must_match_final_status() -> None:
    blocked_report = build_manual_operator_packet_final_boundary_report(
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="equity_indices",
            source_quality_status="pass",
            memory_policy_status="blocked",
            forecast_vs_price_edge_status="pass",
            costs_status="pass",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="no",
            reason_codes=("memory_policy_conflict",),
            manual_next_step="paper_review_read_final_boundary_report",
        ),
    )
    pass_report = build_manual_operator_packet_final_boundary_report(
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="crypto_btc",
            source_quality_status="pass",
            memory_policy_status="pass",
            forecast_vs_price_edge_status="pass",
            costs_status="pass",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="abstain",
            reason_codes=("all_boundary_checks_pass",),
            manual_next_step="paper_review_resolve_memory_policy",
        ),
    )

    assert blocked_report.manual_next_step == "paper_review_resolve_memory_policy"
    assert pass_report.manual_next_step == "paper_review_read_final_boundary_report"
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(blocked_report, manual_next_step="paper_review_read_final_boundary_report")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(pass_report, manual_next_step="paper_review_resolve_memory_policy")


def test_report_contract_is_frozen_strict_and_readonly_public() -> None:
    report = build_manual_operator_packet_final_boundary_report(
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="crypto_btc",
            source_quality_status="pass",
            memory_policy_status="pass",
            forecast_vs_price_edge_status="pass",
            costs_status="pass",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="abstain",
            reason_codes=("all_boundary_checks_pass",),
            manual_next_step="paper_review_read_final_boundary_report",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.final_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="team_owner"):
        replace(report, team_owner=_StringSubclass("crypto_btc"))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_review_only"):
        replace(report, paper_review_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    payload = manual_operator_packet_final_boundary_report_payload(report)
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["final_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        manual_operator_packet_final_boundary_report_payload(
            {
                **payload,
                "ready_ratio": "0.500000",
            },
        )


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "account_review",
        "wallet_review",
        "key_review",
        "order_review",
        "live_review",
        "execution_review",
        "paper_review_wallet",
        "paper_review_order",
    ),
)
def test_report_rejects_account_wallet_key_order_live_execution_text(
    unsafe_text: str,
) -> None:
    with pytest.raises(ValueError, match="unsupported live surface term"):
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="macro_rates",
            source_quality_status="pass",
            memory_policy_status="pass",
            forecast_vs_price_edge_status="pass",
            costs_status="pass",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="yes",
            reason_codes=(unsafe_text,),
            manual_next_step="paper_review_read_final_boundary_report",
        )


def test_owned_module_has_no_account_wallet_key_order_live_execution_surface() -> None:
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
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "account",
        "wallet",
        "private_key",
        "secret_key",
        "api_key",
        "order",
        "live",
        "execution",
        "broker",
        "requests",
        "socket",
        "subprocess",
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
