from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_expected_value_sensitivity_v10.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_expected_value_sensitivity_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def row(**overrides: object):
    module = api()
    values = {
        "market_price": d("0.520000"),
        "forecast_probability": d("0.610000"),
        "fee_rate": d("0.010000"),
        "slippage_bps": d("15.000000"),
        "probability_error_bps": d("75.000000"),
        "settlement_cost_bps": d("5.000000"),
    }
    values.update(overrides)
    return module.StrategyExpectedValueSensitivityV10Input(**values)


def report(*, candidate=None):
    module = api()
    return module.evaluate_strategy_expected_value_sensitivity_v10(
        candidate if candidate is not None else row(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_calculates_base_worst_case_breakeven_and_high_conviction_tier() -> None:
    result = report()

    assert result.market_price == d("0.520000")
    assert result.forecast_probability == d("0.610000")
    assert result.fee_rate == d("0.010000")
    assert result.slippage_rate == d("0.001500")
    assert result.probability_error_rate == d("0.007500")
    assert result.settlement_cost_rate == d("0.000500")
    assert result.total_cost_drag == d("0.012000")
    assert result.base_ev == d("0.078000")
    assert result.worst_case_ev == d("0.070500")
    assert result.breakeven_probability == d("0.532000")
    assert result.sensitivity_tier == "high_conviction"
    assert result.reason_codes == (
        "sensitivity_tier_high_conviction",
        "base_ev_positive",
        "worst_case_ev_positive",
        "probability_error_buffered",
        "cost_drag_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_marks_fragile_when_base_ev_is_positive_but_probability_error_breaks_edge() -> None:
    result = report(
        candidate=row(
            market_price=d("0.500000"),
            forecast_probability=d("0.520000"),
            fee_rate=d("0.005000"),
            slippage_bps=d("50.000000"),
            probability_error_bps=d("200.000000"),
            settlement_cost_bps=ZERO,
        ),
    )

    assert result.total_cost_drag == d("0.010000")
    assert result.base_ev == d("0.010000")
    assert result.worst_case_ev == d("-0.010000")
    assert result.breakeven_probability == d("0.510000")
    assert result.sensitivity_tier == "fragile"
    assert result.reason_codes == (
        "sensitivity_tier_fragile",
        "base_ev_positive",
        "worst_case_ev_nonpositive",
        "probability_error_buffered",
        "cost_drag_present",
    )


def test_marks_negative_when_base_case_is_not_profitable() -> None:
    result = report(
        candidate=row(
            market_price=d("0.500000"),
            forecast_probability=d("0.480000"),
            fee_rate=ZERO,
            slippage_bps=ZERO,
            probability_error_bps=ZERO,
            settlement_cost_bps=ZERO,
        ),
    )

    assert result.base_ev == d("-0.020000")
    assert result.worst_case_ev == d("-0.020000")
    assert result.breakeven_probability == d("0.500000")
    assert result.sensitivity_tier == "negative"
    assert result.reason_codes == (
        "sensitivity_tier_negative",
        "base_ev_nonpositive",
        "worst_case_ev_nonpositive",
        "probability_error_none",
        "cost_drag_none",
    )


def test_payload_uses_decimal_strings_and_contains_no_floats() -> None:
    module = api()
    result = report()

    payload = module.strategy_expected_value_sensitivity_v10_payload(result)

    assert payload["market_price"] == "0.520000"
    assert payload["forecast_probability"] == "0.610000"
    assert payload["base_ev"] == "0.078000"
    assert payload["worst_case_ev"] == "0.070500"
    assert payload["breakeven_probability"] == "0.532000"
    assert payload["sensitivity_tier"] == "high_conviction"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_ranges_bps_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="row must be"):
        module.evaluate_strategy_expected_value_sensitivity_v10(object())

    with pytest.raises(ValueError, match="market_price must be a Decimal"):
        row(market_price=0.52)

    with pytest.raises(ValueError, match="forecast_probability must be finite"):
        row(forecast_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="fee_rate must be exactly Decimal"):
        row(fee_rate=_DecimalSubclass("0.010000"))

    with pytest.raises(ValueError, match="market_price must be a probability Decimal"):
        row(market_price=d("1.000001"))

    with pytest.raises(ValueError, match="slippage_bps must be nonnegative"):
        row(slippage_bps=d("-0.000001"))

    with pytest.raises(ValueError, match="probability_error_bps must not exceed 10000"):
        row(probability_error_bps=d("10000.000001"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyExpectedValueSensitivityV10Input(
            market_price=d("0.520000"),
            forecast_probability=d("0.610000"),
            fee_rate=d("0.010000"),
            slippage_bps=d("15.000000"),
            probability_error_bps=d("75.000000"),
            settlement_cost_bps=d("5.000000"),
            paper_only=False,
        )

    result = report()
    with pytest.raises(FrozenInstanceError):
        result.sensitivity_tier = "negative"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="reason_codes must include tier reason"):
        replace(result, reason_codes=("base_ev_positive",))


def test_decimal_fields_are_exact_decimal_instances() -> None:
    result = report()

    for item in fields(result):
        if item.name in {
            "sensitivity_tier",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(getattr(result, item.name)) is Decimal


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report()

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_expected_value_sensitivity_v10_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_expected_value_sensitivity_v10_payload(
            replace(result, report_only=False),
        )


def test_module_scope_has_no_live_trading_auth_wallet_or_order_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "recommend",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
