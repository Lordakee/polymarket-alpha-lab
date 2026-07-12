from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_capital_lockup_readiness_report import (
    PROBABILITY_EVENT_CAPITAL_LOCKUP_READINESS_REPORT_VERSION,
    ProbabilityEventCapitalLockupReadinessInput,
    ProbabilityEventCapitalLockupReadinessReport,
    build_probability_event_capital_lockup_readiness_report,
    probability_event_capital_lockup_readiness_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_capital_lockup_readiness_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def lockup_input(
    **overrides: object,
) -> ProbabilityEventCapitalLockupReadinessInput:
    values = {
        "event_id": "event-001",
        "market_slug": "fomc-july-2026",
        "time_to_resolution_days": d("7.000000"),
        "expected_edge": d("0.080000"),
        "capital_lockup_penalty": d("0.020000"),
        "liquidity_exit_risk": d("0.100000"),
        "settlement_risk": d("0.050000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventCapitalLockupReadinessInput(**values)


def report(**overrides: object) -> ProbabilityEventCapitalLockupReadinessReport:
    return build_probability_event_capital_lockup_readiness_report(
        lockup_input(**overrides),
    )


def test_pass_readiness_report_payload_schema_and_manual_step() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventCapitalLockupReadinessReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first.config_version == PROBABILITY_EVENT_CAPITAL_LOCKUP_READINESS_REPORT_VERSION
    assert first.readiness_status == "pass"
    assert first.reason_codes == ("capital_lockup_ready",)
    assert first.manual_next_step == "proceed_with_paper_review"
    assert first.net_edge_after_lockup == d("0.060000")
    assert first.total_lockup_risk == d("0.170000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_capital_lockup_readiness_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-capital-lockup-readiness-v0",
        "event_id": "event-001",
        "market_slug": "fomc-july-2026",
        "readiness_status": "pass",
        "time_to_resolution_days": "7.000000",
        "expected_edge": "0.080000",
        "capital_lockup_penalty": "0.020000",
        "liquidity_exit_risk": "0.100000",
        "settlement_risk": "0.050000",
        "net_edge_after_lockup": "0.060000",
        "total_lockup_risk": "0.170000",
        "reason_codes": ("capital_lockup_ready",),
        "manual_next_step": "proceed_with_paper_review",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert _float_or_int_paths(payload) == ()
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["readiness_status"] = "blocked"


def test_watch_readiness_when_lockup_or_exit_risk_needs_manual_review() -> None:
    result = report(
        time_to_resolution_days=d("21.000000"),
        capital_lockup_penalty=d("0.060000"),
        liquidity_exit_risk=d("0.350000"),
        settlement_risk=d("0.120000"),
    )

    assert result.readiness_status == "watch"
    assert result.reason_codes == (
        "extended_resolution_watch",
        "capital_lockup_penalty_watch",
        "liquidity_exit_risk_watch",
        "settlement_risk_watch",
    )
    assert result.manual_next_step == "manual_review_lockup_terms_and_exit_depth"
    assert result.net_edge_after_lockup == d("0.020000")
    assert result.total_lockup_risk == d("0.530000")


def test_blocked_readiness_prioritizes_hard_capital_lockup_risks() -> None:
    result = report(
        time_to_resolution_days=d("45.000000"),
        expected_edge=d("0.030000"),
        capital_lockup_penalty=d("0.050000"),
        liquidity_exit_risk=d("0.600000"),
        settlement_risk=d("0.500000"),
    )

    assert result.readiness_status == "blocked"
    assert result.reason_codes == (
        "extended_resolution_block",
        "negative_net_edge_after_lockup",
        "liquidity_exit_risk_block",
        "settlement_risk_block",
    )
    assert result.manual_next_step == "do_not_allocate_capital_until_blockers_clear"
    assert result.net_edge_after_lockup == d("-0.020000")
    assert result.total_lockup_risk == d("1.150000")


def test_frozen_decimal_only_exact_types_and_hard_flags_are_enforced() -> None:
    input_value = lockup_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.expected_edge = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.readiness_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventCapitalLockupReadinessInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventCapitalLockupReadinessReport):
            pass

    with pytest.raises(ValueError, match="time_to_resolution_days"):
        lockup_input(time_to_resolution_days=7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="expected_edge"):
        lockup_input(expected_edge="0.080000")
    with pytest.raises(ValueError, match="capital_lockup_penalty"):
        lockup_input(capital_lockup_penalty=d("-0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        lockup_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="readiness_status"):
        replace(result, readiness_status="ready")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(result, manual_next_step="place_order")
    with pytest.raises(ValueError, match="net_edge_after_lockup"):
        replace(result, net_edge_after_lockup=d("0.010000"))

    hints = get_type_hints(ProbabilityEventCapitalLockupReadinessReport)
    for field in fields(ProbabilityEventCapitalLockupReadinessReport):
        value = getattr(result, field.name)
        if field.name in {
            "time_to_resolution_days",
            "expected_edge",
            "capital_lockup_penalty",
            "liquidity_exit_risk",
            "settlement_risk",
            "net_edge_after_lockup",
            "total_lockup_risk",
        }:
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_live_execution_or_io_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "live_trading",
        "order execution",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "database",
        "network",
        "persist",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
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
        "write_text",
        "write_bytes",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not imported_roots.intersection(forbidden_imports)
    assert not call_names.intersection(forbidden_call_names)
    assert float_constants == []


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, (list, tuple)):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
