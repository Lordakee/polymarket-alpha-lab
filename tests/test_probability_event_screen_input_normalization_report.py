from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_screen_contract import (
    ProbabilityEventScreen,
)
from polymarket_alpha_lab.probability_event_screen_input_normalization_report import (
    ProbabilityEventScreenInputNormalizationReport,
    ProbabilityEventScreenInputNormalizationRow,
    build_probability_event_screen_input_normalization_report,
    probability_event_screen_input_normalization_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_input_normalization_report.py",
)
GENERATED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def screen(**overrides: object) -> ProbabilityEventScreen:
    values = {
        "generated_at": GENERATED_AT,
        "event_ref": "event-alpha",
        "market_ref": "market-alpha-yes-no",
        "yes_executable_probability": d("0.560000"),
        "yes_executable_price": d("0.560000"),
        "no_executable_probability": d("0.440000"),
        "no_executable_price": d("0.440000"),
        "forecast_probability": d("0.630000"),
        "market_probability": d("0.560000"),
        "gross_edge_probability": d("0.070000"),
        "total_cost_probability": d("0.020000"),
        "cost_adjusted_threshold_probability": d("0.580000"),
        "edge_to_threshold_probability": d("0.050000"),
        "liquidity_probability": d("0.900000"),
        "depth_probability": d("0.820000"),
        "spread_probability": d("0.020000"),
        "resolution_risk_readiness": "ready",
        "settlement_risk_readiness": "ready",
        "source_quality_status": "ready",
        "specialist_team_route": "macro",
        "memory_policy_status": "ready",
        "manual_next_step": "manual_review",
    }
    values.update(overrides)
    return ProbabilityEventScreen(**values)


def report(
    *screens: ProbabilityEventScreen,
) -> ProbabilityEventScreenInputNormalizationReport:
    return build_probability_event_screen_input_normalization_report(screens or (screen(),))


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in ("wallet", "auth", "database", "network", "live"):
                assert forbidden not in lowered_key
            for forbidden in (
                "submit",
                "cancel",
                "replace",
                "create_order",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_ready_screen_builds_one_row_decimal_payload_and_digest() -> None:
    result = report()

    assert is_dataclass(ProbabilityEventScreenInputNormalizationReport)
    assert result.__dataclass_params__.frozen
    assert result.normalization_ready is True
    assert result.screen_count == ONE
    assert result.complete_consistent_count == ONE
    assert result.incomplete_count == ZERO
    assert result.inconsistent_count == ZERO
    assert len(result.digest) == 64

    row = result.rows[0]
    assert isinstance(row, ProbabilityEventScreenInputNormalizationRow)
    assert row.event_ref == "event-alpha"
    assert row.market_ref == "market-alpha-yes-no"
    assert row.direction == "yes"
    assert row.normalization_status == "complete_consistent"
    assert row.reason_codes == ()
    assert row.yes_executable_probability == d("0.560000")
    assert row.no_executable_probability == d("0.440000")
    assert row.forecast_probability == d("0.630000")
    assert row.market_probability == d("0.560000")
    assert row.gross_edge_probability == d("0.070000")
    assert row.total_cost_probability == d("0.020000")
    assert row.cost_adjusted_threshold_probability == d("0.580000")
    assert row.edge_to_threshold_probability == d("0.050000")
    assert row.manual_next_step == "manual_review"
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = result.public_payload
    assert payload == probability_event_screen_input_normalization_report_payload(result)
    assert payload["screen_count"] == "1.000000"
    assert payload["complete_consistent_count"] == "1.000000"
    assert payload["normalization_ready"] is True
    assert payload["rows"][0]["yes_executable_probability"] == "0.560000"
    assert payload["rows"][0]["no_executable_probability"] == "0.440000"
    assert payload["rows"][0]["manual_next_step"] == "manual_review"
    assert payload["digest"] == result.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_no_direction_keeps_forecast_market_gross_edge_and_threshold_consistent() -> None:
    result = report(
        screen(
            yes_executable_probability=d("0.650000"),
            yes_executable_price=d("0.650000"),
            no_executable_probability=d("0.350000"),
            no_executable_price=d("0.350000"),
            forecast_probability=d("0.410000"),
            market_probability=d("0.650000"),
            gross_edge_probability=d("0.240000"),
            total_cost_probability=d("0.030000"),
            cost_adjusted_threshold_probability=d("0.620000"),
            edge_to_threshold_probability=d("0.210000"),
            manual_next_step="review_no_side",
        ),
    )

    row = result.rows[0]
    assert row.direction == "no"
    assert row.yes_executable_probability == d("0.650000")
    assert row.no_executable_probability == d("0.350000")
    assert row.forecast_probability == d("0.410000")
    assert row.market_probability == d("0.650000")
    assert row.gross_edge_probability == d("0.240000")
    assert row.cost_adjusted_threshold_probability == d("0.620000")
    assert row.edge_to_threshold_probability == d("0.210000")
    assert row.manual_next_step == "review_no_side"


def test_row_validation_rejects_inconsistent_inputs_and_flags() -> None:
    row = report().rows[0]

    assert is_dataclass(ProbabilityEventScreenInputNormalizationRow)
    assert row.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        row.manual_next_step = "changed"  # type: ignore[misc]

    for field in fields(row):
        value = getattr(row, field.name)
        if "probability" in field.name:
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="yes_executable_probability"):
        replace(row, yes_executable_probability=_DecimalSubclass("0.560000"))
    with pytest.raises(ValueError, match="no_executable_probability"):
        replace(row, no_executable_probability=d("0.430000"))
    with pytest.raises(ValueError, match="market_probability"):
        replace(row, market_probability=d("0.570000"))
    with pytest.raises(ValueError, match="gross_edge_probability"):
        replace(row, gross_edge_probability=d("0.010000"))
    with pytest.raises(ValueError, match="cost_adjusted_threshold_probability"):
        replace(row, cost_adjusted_threshold_probability=d("0.600000"))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(row, manual_next_step="Manual Review")
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="screen"):
        build_probability_event_screen_input_normalization_report((object(),))  # type: ignore[arg-type]


def test_report_validation_rejects_inconsistent_rollup() -> None:
    result = report()

    with pytest.raises(FrozenInstanceError):
        result.normalization_ready = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="screen_count"):
        replace(result, screen_count=d("2.000000"))
    with pytest.raises(ValueError, match="complete_consistent_count"):
        replace(result, complete_consistent_count=ZERO)
    with pytest.raises(ValueError, match="normalization_ready"):
        replace(result, normalization_ready=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_pure_readonly_report_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "private_key",
        "api_key",
        "authentication",
        "authorization",
        "database",
        "network",
        "submit_",
        "cancel_",
        "replace_",
        "create_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
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
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    for dataclass_type in (
        ProbabilityEventScreenInputNormalizationRow,
        ProbabilityEventScreenInputNormalizationReport,
    ):
        for field in fields(dataclass_type):
            lowered_name = field.name.lower()
            for forbidden in ("wallet", "auth", "live", "order"):
                assert forbidden not in lowered_name
