from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_liquidity_exit_penalty_stress_report as api
from polymarket_alpha_lab.probability_event_liquidity_exit_penalty_stress_report import (
    ProbabilityEventLiquidityExitPenaltyStressReport,
    build_probability_event_liquidity_exit_penalty_stress_report,
    probability_event_liquidity_exit_penalty_stress_report_digest,
    probability_event_liquidity_exit_penalty_stress_report_to_payload,
    validate_probability_event_liquidity_exit_penalty_stress_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_liquidity_exit_penalty_stress_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventLiquidityExitPenaltyStressReport:
    values = {
        "entry_cost_probability": d("0.015000"),
        "exit_cost_probability": d("0.020000"),
        "exit_depth_probability": d("0.850000"),
        "time_to_resolution_hours": d("72.000000"),
        "stress_penalty_probability": d("0.010000"),
    }
    values.update(overrides)
    return build_probability_event_liquidity_exit_penalty_stress_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_clear_exit_penalty_status_payload_and_digest_are_stable() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventLiquidityExitPenaltyStressReport
    assert is_dataclass(first)
    assert first.stressed_exit_cost_probability == d("0.030000")
    assert first.exit_penalty_status == "clear"
    assert first.reason_codes == ("exit_penalty_stress_clear",)
    assert first.manual_next_step == "monitor_exit_penalty_stress"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_liquidity_exit_penalty_stress_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "entry_cost_probability": "0.015000",
        "exit_cost_probability": "0.020000",
        "exit_depth_probability": "0.850000",
        "time_to_resolution_hours": "72.000000",
        "stress_penalty_probability": "0.010000",
        "stressed_exit_cost_probability": "0.030000",
        "exit_penalty_status": "clear",
        "reason_codes": ["exit_penalty_stress_clear"],
        "manual_next_step": "monitor_exit_penalty_stress",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert (
        probability_event_liquidity_exit_penalty_stress_report_digest(first)
        == expected_digest
    )
    assert (
        validate_probability_event_liquidity_exit_penalty_stress_public_payload(
            payload,
        )
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_exit_cost_stress_statuses_reflect_depth_time_and_cost_pressure() -> None:
    watched = report(
        entry_cost_probability=d("0.020000"),
        exit_cost_probability=d("0.030000"),
        exit_depth_probability=d("0.640000"),
        time_to_resolution_hours=d("24.000000"),
        stress_penalty_probability=d("0.015000"),
    )
    blocked = report(
        entry_cost_probability=d("0.040000"),
        exit_cost_probability=d("0.075000"),
        exit_depth_probability=d("0.350000"),
        time_to_resolution_hours=d("6.000000"),
        stress_penalty_probability=d("0.050000"),
    )

    assert watched.stressed_exit_cost_probability == d("0.045000")
    assert watched.exit_penalty_status == "watch"
    assert watched.reason_codes == (
        "exit_depth_probability_watch",
        "time_to_resolution_compressed",
        "stressed_exit_cost_probability_watch",
    )
    assert watched.manual_next_step == "manual_review_exit_penalty_stress"

    assert blocked.stressed_exit_cost_probability == d("0.125000")
    assert blocked.exit_penalty_status == "blocked"
    assert blocked.reason_codes == (
        "exit_depth_probability_blocked",
        "time_to_resolution_blocked",
        "stressed_exit_cost_probability_blocked",
    )
    assert blocked.manual_next_step == "block_until_manual_exit_cost_review"


def test_dataclass_is_frozen_decimal_only_and_flags_are_hard_true() -> None:
    result = report()

    assert is_dataclass(ProbabilityEventLiquidityExitPenaltyStressReport)
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.exit_penalty_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventLiquidityExitPenaltyStressReport):
            pass

    with pytest.raises(ValueError, match="entry_cost_probability"):
        report(entry_cost_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exit_cost_probability"):
        report(exit_cost_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        build_probability_event_liquidity_exit_penalty_stress_report(
            entry_cost_probability=d("0.010000"),
            exit_cost_probability=d("0.010000"),
            exit_depth_probability=d("0.900000"),
            time_to_resolution_hours=d("48.000000"),
            stress_penalty_probability=d("0.010000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="stressed_exit_cost_probability"):
        replace(result, stressed_exit_cost_probability=1)  # type: ignore[arg-type]

    hints = get_type_hints(ProbabilityEventLiquidityExitPenaltyStressReport)
    for field_name in (
        "entry_cost_probability",
        "exit_cost_probability",
        "exit_depth_probability",
        "time_to_resolution_hours",
        "stress_penalty_probability",
        "stressed_exit_cost_probability",
    ):
        assert hints[field_name] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_probability") or field.name.endswith("_hours"):
            assert type(value) is Decimal


def test_manual_report_and_payload_tampering_must_match_derived_values() -> None:
    result = report()
    payload = dict(result.public_payload)

    with pytest.raises(ValueError, match="stressed_exit_cost_probability"):
        ProbabilityEventLiquidityExitPenaltyStressReport(
            entry_cost_probability=d("0.015000"),
            exit_cost_probability=d("0.020000"),
            exit_depth_probability=d("0.850000"),
            time_to_resolution_hours=d("72.000000"),
            stress_penalty_probability=d("0.010000"),
            stressed_exit_cost_probability=d("0.029000"),
            exit_penalty_status="clear",
            reason_codes=("exit_penalty_stress_clear",),
            manual_next_step="monitor_exit_penalty_stress",
            payload_digest=result.payload_digest,
        )

    with pytest.raises(ValueError, match="stressed_exit_cost_probability"):
        validate_probability_event_liquidity_exit_penalty_stress_public_payload(
            {**payload, "stressed_exit_cost_probability": "0.029000"},
        )
    with pytest.raises(ValueError, match="exit_penalty_status"):
        validate_probability_event_liquidity_exit_penalty_stress_public_payload(
            {**payload, "exit_penalty_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_liquidity_exit_penalty_stress_public_payload(
            {**payload, "paper_only": False},
        )


def test_module_has_no_live_io_run_or_file_persistence_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "sign",
        "execute",
        "submit",
        "jsonl",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "cursor",
            "delete",
            "executemany",
            "fetch",
            "insert",
            "open",
            "post",
            "put",
            "rollback",
            "send",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "live" not in lowered
        assert "auth" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "key" not in lowered
        assert "sign" not in lowered
        assert "execute" not in lowered
