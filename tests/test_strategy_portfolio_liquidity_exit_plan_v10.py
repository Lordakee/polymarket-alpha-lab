from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_portfolio_liquidity_exit_plan_v10 as exit_plan
from polymarket_alpha_lab.strategy_portfolio_liquidity_exit_plan_v10 import (
    CONFIG_VERSION,
    PortfolioLiquidityExitPlanV10Input,
    build_strategy_portfolio_liquidity_exit_plan_v10_report,
)


def _scenario(
    *,
    position_size_proxy: str = "10",
    exit_depth: str = "100",
    spread_bps: str = "10",
    expected_slippage_bps: str = "5",
    hours_to_resolution: str = "240",
    correlated_exit_pressure: str = "0.10",
) -> PortfolioLiquidityExitPlanV10Input:
    return PortfolioLiquidityExitPlanV10Input(
        position_size_proxy=Decimal(position_size_proxy),
        exit_depth=Decimal(exit_depth),
        spread_bps=Decimal(spread_bps),
        expected_slippage_bps=Decimal(expected_slippage_bps),
        hours_to_resolution=Decimal(hours_to_resolution),
        correlated_exit_pressure=Decimal(correlated_exit_pressure),
    )


def test_low_stress_position_returns_monitoring_plan() -> None:
    generated_at = datetime(2026, 7, 6, 12, tzinfo=UTC)

    report = build_strategy_portfolio_liquidity_exit_plan_v10_report(
        _scenario(),
        generated_at=generated_at,
    )

    assert report.generated_at == generated_at
    assert report.config_version == CONFIG_VERSION
    assert report.pressure_adjusted_exit_depth == Decimal("90.000000")
    assert report.pressure_adjusted_size_to_depth_ratio == Decimal("0.111111")
    assert report.estimated_exit_cost_bps == Decimal("25.00")
    assert report.liquidity_stress_score == Decimal("0.083889")
    assert report.recommended_action == "monitor"
    assert report.recommended_exit_fraction == Decimal("0.000000")
    assert report.planned_exit_size_proxy == Decimal("0.000000")
    assert report.exit_slice_count == 0
    assert report.max_slice_size_proxy == Decimal("0.000000")
    assert report.min_hours_between_slices == Decimal("0.000000")
    assert report.reason_codes == ("exit_liquidity_monitor",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_correlated_pressure_and_short_window_stage_exit_plan() -> None:
    report = build_strategy_portfolio_liquidity_exit_plan_v10_report(
        _scenario(
            position_size_proxy="120",
            exit_depth="100",
            spread_bps="35",
            expected_slippage_bps="45",
            hours_to_resolution="18",
            correlated_exit_pressure="0.25",
        ),
        generated_at=datetime(2026, 7, 6, 12, tzinfo=UTC),
    )

    assert report.pressure_adjusted_exit_depth == Decimal("75.000000")
    assert report.pressure_adjusted_size_to_depth_ratio == Decimal("1.600000")
    assert report.estimated_exit_cost_bps == Decimal("105.00")
    assert report.liquidity_stress_score == Decimal("0.692500")
    assert report.recommended_action == "stage_exit"
    assert report.recommended_exit_fraction == Decimal("0.750000")
    assert report.planned_exit_size_proxy == Decimal("90.000000")
    assert report.exit_slice_count == 6
    assert report.max_slice_size_proxy == Decimal("15.000000")
    assert report.min_hours_between_slices == Decimal("3.000000")
    assert report.reason_codes == (
        "position_exceeds_pressure_adjusted_depth",
        "exit_cost_elevated",
        "resolution_window_short",
        "correlated_exit_pressure_elevated",
    )


def test_unavailable_depth_recommends_immediate_paper_exit_plan() -> None:
    report = build_strategy_portfolio_liquidity_exit_plan_v10_report(
        _scenario(
            position_size_proxy="50",
            exit_depth="0",
            spread_bps="5",
            expected_slippage_bps="10",
            hours_to_resolution="6",
            correlated_exit_pressure="1",
        ),
        generated_at=datetime(2026, 7, 6, 12, tzinfo=UTC),
    )

    assert report.pressure_adjusted_exit_depth == Decimal("0.000000")
    assert report.pressure_adjusted_size_to_depth_ratio == Decimal("999999.000000")
    assert report.estimated_exit_cost_bps == Decimal("115.00")
    assert report.liquidity_stress_score == Decimal("0.894167")
    assert report.recommended_action == "exit_immediately"
    assert report.recommended_exit_fraction == Decimal("1.000000")
    assert report.planned_exit_size_proxy == Decimal("50.000000")
    assert report.exit_slice_count == 1
    assert report.max_slice_size_proxy == Decimal("50.000000")
    assert "exit_depth_unavailable" in report.reason_codes
    assert "correlated_exit_pressure_high" in report.reason_codes


def test_public_payload_is_json_ready_readonly_and_rejects_unsafe_values() -> None:
    report = build_strategy_portfolio_liquidity_exit_plan_v10_report(
        _scenario(
            position_size_proxy="120",
            exit_depth="100",
            spread_bps="35",
            expected_slippage_bps="45",
            hours_to_resolution="18",
            correlated_exit_pressure="0.25",
        ),
        generated_at=datetime(2026, 7, 6, 12, tzinfo=UTC),
    )

    payload = exit_plan.strategy_portfolio_liquidity_exit_plan_v10_payload(report)

    assert report.payload == payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["position_size_proxy"] == "120.000000"
    assert payload["estimated_exit_cost_bps"] == "105.00"
    assert payload["liquidity_stress_score"] == "0.692500"
    assert payload["exit_slice_count"] == "6"
    assert payload["reason_codes"] == [
        "position_exceeds_pressure_adjusted_depth",
        "exit_cost_elevated",
        "resolution_window_short",
        "correlated_exit_pressure_elevated",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_public_payload_has_no_json_numbers(payload)

    missing_flag_payload = dict(payload)
    del missing_flag_payload["paper_only"]
    with pytest.raises(ValueError, match="paper_only"):
        exit_plan.strategy_portfolio_liquidity_exit_plan_v10_payload(
            missing_flag_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        exit_plan.strategy_portfolio_liquidity_exit_plan_v10_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["public_note"] = "route a live order through wallet"
    with pytest.raises(ValueError, match="unsafe live surface value"):
        exit_plan.strategy_portfolio_liquidity_exit_plan_v10_payload(
            unsafe_value_payload,
        )


def test_report_rejects_tampered_derived_fields() -> None:
    report = build_strategy_portfolio_liquidity_exit_plan_v10_report(
        _scenario(
            position_size_proxy="120",
            exit_depth="100",
            spread_bps="35",
            expected_slippage_bps="45",
            hours_to_resolution="18",
            correlated_exit_pressure="0.25",
        ),
        generated_at=datetime(2026, 7, 6, 12, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="pressure_adjusted_exit_depth"):
        replace(report, exit_depth=Decimal("110"))

    with pytest.raises(ValueError, match="liquidity_stress_score"):
        replace(report, liquidity_stress_score=Decimal("0.500000"))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("exit_liquidity_monitor",))


def test_numeric_inputs_must_be_decimal_values() -> None:
    with pytest.raises(ValueError, match="position_size_proxy.*Decimal"):
        PortfolioLiquidityExitPlanV10Input(
            position_size_proxy=10,  # type: ignore[arg-type]
            exit_depth=Decimal("100"),
            spread_bps=Decimal("10"),
            expected_slippage_bps=Decimal("5"),
            hours_to_resolution=Decimal("24"),
            correlated_exit_pressure=Decimal("0.1"),
        )


@pytest.mark.parametrize(
    ("field_name", "field_value", "message"),
    (
        ("position_size_proxy", "-0.000001", "position_size_proxy"),
        ("exit_depth", "-1", "exit_depth"),
        ("spread_bps", "-0.01", "spread_bps"),
        ("expected_slippage_bps", "-0.01", "expected_slippage_bps"),
        ("hours_to_resolution", "-1", "hours_to_resolution"),
        ("correlated_exit_pressure", "1.000001", "correlated_exit_pressure"),
    ),
)
def test_rejects_out_of_range_inputs(
    field_name: str,
    field_value: str,
    message: str,
) -> None:
    kwargs = {
        "position_size_proxy": Decimal("10"),
        "exit_depth": Decimal("100"),
        "spread_bps": Decimal("10"),
        "expected_slippage_bps": Decimal("5"),
        "hours_to_resolution": Decimal("24"),
        "correlated_exit_pressure": Decimal("0.1"),
    }
    kwargs[field_name] = Decimal(field_value)

    with pytest.raises(ValueError, match=message):
        PortfolioLiquidityExitPlanV10Input(**kwargs)


def test_report_is_frozen_and_enforces_readonly_flags() -> None:
    report = build_strategy_portfolio_liquidity_exit_plan_v10_report(
        _scenario(),
        generated_at=datetime(2026, 7, 6, 12, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.recommended_action = "stage_exit"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def _assert_public_payload_has_no_json_numbers(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise AssertionError("public payload must not expose JSON numeric values")
    if type(value) is list:
        for item in value:
            _assert_public_payload_has_no_json_numbers(item)
        return
    if type(value) is dict:
        for item in value.values():
            _assert_public_payload_has_no_json_numbers(item)
