from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_portfolio_scenario_drawdown_guard_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_portfolio_scenario_drawdown_guard_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def exposure(**overrides: object):
    module = api()
    values = {
        "portfolio_id": "paper_portfolio_alpha",
        "scenario_id": "macro_rate_shock",
        "scenario_loss_ratio": d("0.030000"),
        "category_concentration_ratio": d("0.160000"),
        "correlated_event_exposure_ratio": d("0.120000"),
        "liquidity_exit_stress_ratio": d("0.100000"),
        "calibration_confidence": d("0.930000"),
    }
    values.update(overrides)
    return module.PortfolioScenarioDrawdownGuardV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_portfolio_scenario_drawdown_guard_v10(
        exposure(**overrides),
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


def test_low_scenario_exposure_passes_drawdown_guard() -> None:
    result = evaluate()

    assert is_dataclass(result)
    assert result.portfolio_id == "paper_portfolio_alpha"
    assert result.scenario_id == "macro_rate_shock"
    assert result.drawdown_guard_score == d("0.088500")
    assert result.guard_status == "pass"
    assert result.recommended_action == "allow_paper_exposure"
    assert result.scenario_loss_component == d("0.010500")
    assert result.category_concentration_component == d("0.032000")
    assert result.correlated_event_exposure_component == d("0.024000")
    assert result.liquidity_exit_stress_component == d("0.015000")
    assert result.calibration_confidence_gap_component == d("0.007000")
    assert result.reason_codes == (
        "portfolio_scenario_drawdown_guard_pass",
        "scenario_loss_low",
        "category_concentration_low",
        "correlated_event_exposure_low",
        "liquidity_exit_stress_low",
        "calibration_confidence_strong",
        "paper_exposure_action_allow",
    )


def test_stressed_scenario_blocks_paper_exposure() -> None:
    result = evaluate(
        scenario_loss_ratio=d("0.330000"),
        category_concentration_ratio=d("0.520000"),
        correlated_event_exposure_ratio=d("0.480000"),
        liquidity_exit_stress_ratio=d("0.620000"),
        calibration_confidence=d("0.450000"),
    )

    assert result.drawdown_guard_score == d("0.463500")
    assert result.guard_status == "blocked"
    assert result.recommended_action == "block_paper_exposure"
    assert result.reason_codes == (
        "portfolio_scenario_drawdown_guard_blocked",
        "scenario_loss_high",
        "category_concentration_high",
        "correlated_event_exposure_high",
        "liquidity_exit_stress_high",
        "calibration_confidence_low",
        "paper_exposure_action_block",
    )


def test_mixed_scenario_signals_reduce_paper_exposure() -> None:
    result = evaluate(
        scenario_loss_ratio=d("0.170000"),
        category_concentration_ratio=d("0.340000"),
        correlated_event_exposure_ratio=d("0.310000"),
        liquidity_exit_stress_ratio=d("0.320000"),
        calibration_confidence=d("0.690000"),
    )

    assert result.drawdown_guard_score == d("0.268500")
    assert result.guard_status == "watch"
    assert result.recommended_action == "reduce_paper_exposure"
    assert result.reason_codes == (
        "portfolio_scenario_drawdown_guard_watch",
        "scenario_loss_watch",
        "category_concentration_watch",
        "correlated_event_exposure_watch",
        "liquidity_exit_stress_watch",
        "calibration_confidence_watch",
        "paper_exposure_action_reduce",
    )


def test_inputs_config_and_reports_are_frozen_decimal_only_and_readonly() -> None:
    module = api()
    sample = exposure()
    config = module.PortfolioScenarioDrawdownGuardV10Config()
    result = evaluate()

    decimal_fields = {
        "scenario_loss_ratio",
        "category_concentration_ratio",
        "correlated_event_exposure_ratio",
        "liquidity_exit_stress_ratio",
        "calibration_confidence",
        "scenario_loss_weight",
        "category_concentration_weight",
        "correlated_event_exposure_weight",
        "liquidity_exit_stress_weight",
        "calibration_confidence_gap_weight",
        "watch_guard_score",
        "block_guard_score",
        "drawdown_guard_score",
        "scenario_loss_component",
        "category_concentration_component",
        "correlated_event_exposure_component",
        "liquidity_exit_stress_component",
        "calibration_confidence_gap_component",
    }

    for item in (sample, config, result):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_result_rejects_tampered_derived_validation_fields() -> None:
    result = evaluate()

    assert len(result.derived_validation_digest) == 64
    assert result.derived_validation_digest == result.derived_validation_digest.lower()
    assert set(result.derived_validation_digest) <= set("0123456789abcdef")

    with pytest.raises(FrozenInstanceError):
        result.guard_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="recommended_action must match guard_status"):
        replace(result, guard_status="watch")
    with pytest.raises(ValueError, match="reason_codes must match guard status"):
        replace(
            result,
            reason_codes=(
                "portfolio_scenario_drawdown_guard_watch",
                *result.reason_codes[1:],
            ),
        )


def test_public_payload_serializes_decimal_strings_and_rejects_unsafe_values() -> None:
    module = api()
    result = evaluate()

    payload = module.portfolio_scenario_drawdown_guard_v10_payload(result)

    assert result.payload == payload
    assert payload["drawdown_guard_score"] == "0.088500"
    assert payload["scenario_loss_component"] == "0.010500"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_portfolio_scenario_drawdown_guard_v10_public_payload(
            {"result": payload, "wallet_address": "0xunsafe"},
        )
    with pytest.raises(
        ValueError,
        match="payload Decimal values must be rendered as strings",
    ):
        module.validate_portfolio_scenario_drawdown_guard_v10_public_payload(
            {"drawdown_guard_score": d("0.100000")},
        )
    with pytest.raises(ValueError, match="payload float values are not supported"):
        module.validate_portfolio_scenario_drawdown_guard_v10_public_payload(
            {"drawdown_guard_score": 0.1},
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("scenario_loss_ratio", 0.08, "scenario_loss_ratio must be exactly Decimal"),
        (
            "category_concentration_ratio",
            _DecimalSubclass("0.200000"),
            "category_concentration_ratio must be exactly Decimal",
        ),
        (
            "correlated_event_exposure_ratio",
            d("1.000001"),
            "correlated_event_exposure_ratio must be <= 1.000000",
        ),
        (
            "liquidity_exit_stress_ratio",
            d("-0.000001"),
            "liquidity_exit_stress_ratio must be >= 0.000000",
        ),
        (
            "calibration_confidence",
            Decimal("NaN"),
            "calibration_confidence must be finite",
        ),
    ),
)
def test_validation_rejects_non_decimal_and_out_of_range_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        exposure(**{field_name: bad_value})


def test_validation_rejects_blank_strings_disabled_flags_and_wrong_input_type() -> None:
    module = api()

    with pytest.raises(ValueError, match="portfolio_id must be a non-empty string"):
        exposure(portfolio_id=" ")
    with pytest.raises(ValueError, match="scenario_id must be a non-empty string"):
        exposure(scenario_id="")
    with pytest.raises(ValueError, match="paper_only must be True"):
        exposure(paper_only=False)
    with pytest.raises(
        ValueError,
        match="exposure must be a PortfolioScenarioDrawdownGuardV10Input",
    ):
        module.evaluate_portfolio_scenario_drawdown_guard_v10(object())


def test_config_rejects_non_decimal_weights_threshold_order_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="scenario_loss_weight must be exactly Decimal"):
        module.PortfolioScenarioDrawdownGuardV10Config(scenario_loss_weight=0)
    with pytest.raises(
        ValueError,
        match="drawdown guard weights must sum to 1.000000",
    ):
        module.PortfolioScenarioDrawdownGuardV10Config(
            scenario_loss_weight=d("0.300000"),
        )
    with pytest.raises(
        ValueError,
        match="watch_guard_score must not exceed block_guard_score",
    ):
        module.PortfolioScenarioDrawdownGuardV10Config(
            watch_guard_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        module.PortfolioScenarioDrawdownGuardV10Config(readonly=False)


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
