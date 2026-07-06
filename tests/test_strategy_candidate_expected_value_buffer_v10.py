from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_candidate_expected_value_buffer_v10",
    )


def buffer_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "market_id": "market-ev-buffer",
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.550000"),
        "fee_bps": d("20.000000"),
        "spread_bps": d("15.000000"),
        "slippage_bps": d("25.000000"),
        "forecast_uncertainty_bps": d("80.000000"),
        "resolution_ambiguity_bps": d("40.000000"),
        "liquidity_exit_cost_bps": d("35.000000"),
        "minimum_buffer_bps": d("100.000000"),
        "reason_codes": ("source_consensus_pass",),
    }
    values.update(overrides)
    return module.StrategyCandidateExpectedValueBufferV10Input(**values)


def estimate(subject: object | None = None):
    return api().estimate_strategy_candidate_expected_value_buffer_v10(
        buffer_input() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_screens_in_candidate_when_conservative_ev_buffer_clears_threshold() -> None:
    module = api()

    result = estimate()

    assert result == module.StrategyCandidateExpectedValueBufferV10Result(
        market_id="market-ev-buffer",
        forecast_probability=d("0.620000"),
        market_probability=d("0.550000"),
        gross_edge_bps=d("700.000000"),
        fee_bps=d("20.000000"),
        spread_bps=d("15.000000"),
        slippage_bps=d("25.000000"),
        market_friction_cost_bps=d("60.000000"),
        forecast_uncertainty_bps=d("80.000000"),
        resolution_ambiguity_bps=d("40.000000"),
        liquidity_exit_cost_bps=d("35.000000"),
        total_conservative_adjustment_bps=d("215.000000"),
        net_expected_value_buffer_bps=d("485.000000"),
        minimum_buffer_bps=d("100.000000"),
        screening_status="candidate",
        screening_decision="screen_in",
        reason_codes=(
            "source_consensus_pass",
            "strategy_candidate_expected_value_buffer",
            "buffer_candidate",
            "gross_edge_positive",
            "market_friction_applied",
            "forecast_uncertainty_applied",
            "resolution_ambiguity_applied",
            "liquidity_exit_cost_applied",
            "minimum_buffer_met",
        ),
    )
    assert type(result.net_expected_value_buffer_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == module.strategy_candidate_expected_value_buffer_v10_payload(result)
    assert payload["screening_status"] == "candidate"
    assert payload["screening_decision"] == "screen_in"
    assert payload["gross_edge_bps"] == "700.000000"
    assert payload["net_expected_value_buffer_bps"] == "485.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_watches_candidate_when_positive_buffer_is_below_minimum() -> None:
    result = estimate(
        buffer_input(
            forecast_probability=d("0.535000"),
            market_probability=d("0.500000"),
            fee_bps=d("10.000000"),
            spread_bps=d("20.000000"),
            slippage_bps=d("20.000000"),
            forecast_uncertainty_bps=d("120.000000"),
            resolution_ambiguity_bps=d("60.000000"),
            liquidity_exit_cost_bps=d("80.000000"),
            minimum_buffer_bps=d("50.000000"),
            reason_codes=(),
        ),
    )

    assert result.gross_edge_bps == d("350.000000")
    assert result.market_friction_cost_bps == d("50.000000")
    assert result.total_conservative_adjustment_bps == d("310.000000")
    assert result.net_expected_value_buffer_bps == d("40.000000")
    assert result.screening_status == "watch"
    assert result.screening_decision == "manual_review"
    assert result.reason_codes == (
        "strategy_candidate_expected_value_buffer",
        "buffer_watch",
        "gross_edge_positive",
        "market_friction_applied",
        "forecast_uncertainty_applied",
        "resolution_ambiguity_applied",
        "liquidity_exit_cost_applied",
        "minimum_buffer_not_met",
    )


def test_blocks_candidate_when_conservative_costs_exceed_edge() -> None:
    result = estimate(
        buffer_input(
            forecast_probability=d("0.510000"),
            market_probability=d("0.500000"),
            fee_bps=d("15.000000"),
            spread_bps=d("20.000000"),
            slippage_bps=d("25.000000"),
            forecast_uncertainty_bps=d("40.000000"),
            resolution_ambiguity_bps=d("35.000000"),
            liquidity_exit_cost_bps=d("30.000000"),
            minimum_buffer_bps=d("25.000000"),
            reason_codes=("thin_book_review",),
        ),
    )

    assert result.gross_edge_bps == d("100.000000")
    assert result.total_conservative_adjustment_bps == d("165.000000")
    assert result.net_expected_value_buffer_bps == d("-65.000000")
    assert result.screening_status == "blocked"
    assert result.screening_decision == "reject"
    assert result.reason_codes == (
        "thin_book_review",
        "strategy_candidate_expected_value_buffer",
        "buffer_blocked",
        "gross_edge_positive",
        "market_friction_applied",
        "forecast_uncertainty_applied",
        "resolution_ambiguity_applied",
        "liquidity_exit_cost_applied",
        "costs_exceed_edge",
    )


def test_decimal_only_validation_hard_flags_and_frozen_dataclasses() -> None:
    subject = buffer_input()
    result = estimate(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert api().StrategyCandidateExpectedValueBufferV10Input.__dataclass_params__.frozen
    assert api().StrategyCandidateExpectedValueBufferV10Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.market_id = "other-market"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.screening_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        buffer_input(forecast_probability=0.62)

    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        buffer_input(market_probability=d("1.000001"))

    with pytest.raises(ValueError, match="fee_bps must be nonnegative"):
        buffer_input(fee_bps=d("-0.000001"))

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        buffer_input(reason_codes=["source_consensus_pass"])

    with pytest.raises(ValueError, match="paper_only must be True"):
        buffer_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        buffer_input(readonly=False)

    with pytest.raises(ValueError, match="buffer_input"):
        estimate(object())


def test_payload_is_json_ready_and_module_has_no_live_io_surface() -> None:
    module = api()
    result = estimate()
    payload = module.strategy_candidate_expected_value_buffer_v10_payload(result)

    assert payload == result.payload
    assert payload["total_conservative_adjustment_bps"] == "215.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert_no_float_values(payload)

    source = inspect.getsource(module)
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "wallet",
        "private_key",
        "signing",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)
    assert "network" not in lowered
    assert "database" not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
