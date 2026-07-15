from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.manual_trade_preflight_readiness_report as api
from polymarket_alpha_lab.manual_trade_preflight_readiness_report import (
    ManualTradePreflightReadinessInput,
    ManualTradePreflightReadinessReport,
    build_manual_trade_preflight_readiness_report,
    manual_trade_preflight_readiness_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/manual_trade_preflight_readiness_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def preflight_input(
    *,
    decision_ticket_ready: Decimal = ONE,
    cost_gate_ready: Decimal = ONE,
    source_quorum_ready: Decimal = ONE,
    team_routing_ready: Decimal = ONE,
    settlement_risk_ready: Decimal = ONE,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ManualTradePreflightReadinessInput:
    return ManualTradePreflightReadinessInput(
        decision_ticket_ready=decision_ticket_ready,
        cost_gate_ready=cost_gate_ready,
        source_quorum_ready=source_quorum_ready,
        team_routing_ready=team_routing_ready,
        settlement_risk_ready=settlement_risk_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    readiness: ManualTradePreflightReadinessInput,
) -> ManualTradePreflightReadinessReport:
    return build_manual_trade_preflight_readiness_report(readiness)


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_all_checks_ready_can_present_manual_ticket() -> None:
    readiness = report(preflight_input())

    assert is_dataclass(readiness)
    assert readiness.can_present_manual_ticket is True
    assert readiness.blocked_check_count == ZERO
    assert readiness.attention_check_count == ZERO
    assert readiness.ready_check_ratio == ONE
    assert readiness.reason_codes == ("manual_trade_preflight_all_checks_ready",)
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    payload = manual_trade_preflight_readiness_report_to_payload(readiness)
    assert payload == {
        "can_present_manual_ticket": True,
        "blocked_check_count": "0.000000",
        "attention_check_count": "0.000000",
        "ready_check_ratio": "1.000000",
        "reason_codes": ["manual_trade_preflight_all_checks_ready"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_or_int_values(payload)


def test_blocked_and_attention_checks_explain_manual_ticket_suppression() -> None:
    readiness = report(
        preflight_input(
            decision_ticket_ready=ZERO,
            cost_gate_ready=d("0.500000"),
            source_quorum_ready=ONE,
            team_routing_ready=d("0.750000"),
            settlement_risk_ready=ZERO,
        ),
    )

    assert readiness.can_present_manual_ticket is False
    assert readiness.blocked_check_count == d("2.000000")
    assert readiness.attention_check_count == d("2.000000")
    assert readiness.ready_check_ratio == d("0.200000")
    assert readiness.reason_codes == (
        "manual_trade_preflight_decision_ticket_blocked",
        "manual_trade_preflight_settlement_risk_blocked",
        "manual_trade_preflight_cost_gate_attention",
        "manual_trade_preflight_team_routing_attention",
    )

    payload = manual_trade_preflight_readiness_report_to_payload(readiness)
    assert payload["can_present_manual_ticket"] is False
    assert payload["blocked_check_count"] == "2.000000"
    assert payload["attention_check_count"] == "2.000000"
    assert payload["ready_check_ratio"] == "0.200000"
    assert_no_float_or_int_values(payload)


def test_attention_only_preflight_remains_presentable_with_reason_codes() -> None:
    readiness = report(
        preflight_input(
            source_quorum_ready=d("0.800000"),
            team_routing_ready=d("0.250000"),
        ),
    )

    assert readiness.can_present_manual_ticket is True
    assert readiness.blocked_check_count == ZERO
    assert readiness.attention_check_count == d("2.000000")
    assert readiness.ready_check_ratio == d("0.600000")
    assert readiness.reason_codes == (
        "manual_trade_preflight_source_quorum_attention",
        "manual_trade_preflight_team_routing_attention",
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    readiness = report(preflight_input())

    with pytest.raises(FrozenInstanceError):
        readiness.can_present_manual_ticket = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ManualTradePreflightReadinessInput):
            pass

    with pytest.raises(ValueError, match="decision_ticket_ready must be a Decimal"):
        preflight_input(decision_ticket_ready=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="decision_ticket_ready must be between"):
        preflight_input(decision_ticket_ready=d("1.100000"))

    with pytest.raises(ValueError, match="paper_only"):
        preflight_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        preflight_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)


def test_public_api_excludes_live_trading_auth_wallet_and_side_effect_surfaces() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "database",
        "network",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (ManualTradePreflightReadinessInput, ManualTradePreflightReadinessReport):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
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
        },
    )
