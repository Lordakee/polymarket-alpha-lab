from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_edge_decay_policy import (
    StrategyEdgeDecayPolicyConfig,
    StrategyEdgeDecayPolicyInput,
    StrategyEdgeDecayPolicyReport,
    build_strategy_edge_decay_policy_report,
    strategy_edge_decay_policy_report_to_payload,
)


ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    *,
    signal_id: str = "signal-alpha",
    market_slug: str = "event-alpha",
    side: str = "yes",
    edge_per_share: Decimal = d("0.100000"),
    time_to_resolution: Decimal = d("172800.000000"),
    last_forecast_age: Decimal = d("1800.000000"),
    information_velocity: Decimal = d("0.200000"),
    probability_volatility: Decimal = d("0.030000"),
    source_staleness: Decimal = d("900.000000"),
    reason_codes: tuple[str, ...] = ("seed",),
) -> StrategyEdgeDecayPolicyInput:
    return StrategyEdgeDecayPolicyInput(
        signal_id=signal_id,
        market_slug=market_slug,
        side=side,
        edge_per_share=edge_per_share,
        time_to_resolution=time_to_resolution,
        last_forecast_age=last_forecast_age,
        information_velocity=information_velocity,
        probability_volatility=probability_volatility,
        source_staleness=source_staleness,
        reason_codes=reason_codes,
    )


def config() -> StrategyEdgeDecayPolicyConfig:
    return StrategyEdgeDecayPolicyConfig()


def report(
    *signals: StrategyEdgeDecayPolicyInput,
) -> StrategyEdgeDecayPolicyReport:
    return build_strategy_edge_decay_policy_report(signals, config=config())


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_values(child)


def test_build_report_estimates_decayed_edge_statuses_and_reasons() -> None:
    result = report(
        signal(signal_id="clear", market_slug="event-clear"),
        signal(
            signal_id="watch",
            market_slug="event-watch",
            edge_per_share=d("0.090000"),
            time_to_resolution=d("43200.000000"),
            last_forecast_age=d("5400.000000"),
            information_velocity=d("0.350000"),
            probability_volatility=d("0.060000"),
            source_staleness=d("1800.000000"),
        ),
        signal(
            signal_id="blocked",
            market_slug="event-blocked",
            time_to_resolution=d("21600.000000"),
            last_forecast_age=d("10800.000000"),
            information_velocity=d("0.840000"),
            probability_volatility=d("0.180000"),
            source_staleness=d("14400.000000"),
        ),
    )

    assert [row.signal_id for row in result.rows] == ["blocked", "watch", "clear"]
    assert result.input_count == d("3.000000")
    assert result.row_count == d("3.000000")
    assert result.blocked_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.clear_count == d("1.000000")
    assert result.max_edge_decay_ratio == d("0.900000")
    assert result.average_edge_decay_ratio == d("0.577381")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked = result.rows[0]
    assert blocked.edge_decay_ratio == d("0.900000")
    assert blocked.decayed_edge_per_share == d("0.010000")
    assert blocked.edge_decay_status == "blocked"
    assert blocked.reason_codes == (
        "resolution_window_compressed",
        "last_forecast_stale",
        "information_velocity_high",
        "probability_volatility_high",
        "source_stale",
        "edge_decayed_below_floor",
        "seed",
    )

    watch = result.rows[1]
    assert watch.edge_decay_ratio == d("0.575000")
    assert watch.decayed_edge_per_share == d("0.038250")
    assert watch.edge_decay_status == "watch"
    assert watch.reason_codes == (
        "resolution_window_compressed",
        "last_forecast_stale",
        "seed",
    )

    clear = result.rows[2]
    assert clear.edge_decay_ratio == d("0.257143")
    assert clear.decayed_edge_per_share == d("0.074286")
    assert clear.edge_decay_status == "clear"
    assert clear.reason_codes == ("seed",)


def test_payload_helper_is_json_ready_and_never_emits_floats() -> None:
    payload = strategy_edge_decay_policy_report_to_payload(report(signal()))

    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)
    assert payload["input_count"] == "1.000000"
    assert payload["average_edge_decay_ratio"] == "0.257143"
    assert payload["rows"][0]["signal_id"] == "signal-alpha"
    assert payload["rows"][0]["decayed_edge_per_share"] == "0.074286"
    assert payload["rows"][0]["edge_decay_status"] == "clear"
    assert payload["rows"][0]["paper_only"] is True


def test_public_numeric_policy_fields_are_decimals() -> None:
    result = report(signal())
    row = result.rows[0]

    for field in fields(result):
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(getattr(result, field.name)) is Decimal

    for field in fields(row):
        if field.name in {
            "edge_per_share",
            "time_to_resolution",
            "last_forecast_age",
            "information_velocity",
            "probability_volatility",
            "source_staleness",
            "edge_decay_ratio",
            "decayed_edge_per_share",
        }:
            assert type(getattr(row, field.name)) is Decimal


def test_constructors_validate_decimals_consistency_and_safety_flags() -> None:
    result = report(
        signal(
            time_to_resolution=d("21600.000000"),
            last_forecast_age=d("10800.000000"),
            information_velocity=d("0.840000"),
            probability_volatility=d("0.180000"),
            source_staleness=d("14400.000000"),
        ),
    )
    blocked_row = result.rows[0]

    with pytest.raises(ValueError, match="edge_per_share"):
        replace(signal(), edge_per_share=0.10)
    with pytest.raises(ValueError, match="time_to_resolution"):
        replace(signal(), time_to_resolution=d("-1.000000"))
    with pytest.raises(ValueError, match="information_velocity"):
        replace(signal(), information_velocity=d("1.100000"))
    with pytest.raises(ValueError, match="config"):
        build_strategy_edge_decay_policy_report([signal()], config=object())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(blocked_row, reason_codes=("seed",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(FrozenInstanceError):
        blocked_row.decayed_edge_per_share = ZERO  # type: ignore[misc]


def test_policy_surface_is_paper_report_readonly_without_live_trading_fields() -> None:
    for cls in (
        StrategyEdgeDecayPolicyConfig,
        StrategyEdgeDecayPolicyInput,
        type(report(signal()).rows[0]),
        StrategyEdgeDecayPolicyReport,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"} <= field_names
        assert not any(
            forbidden in field_name
            for field_name in field_names
            for forbidden in ("live", "trading", "trade", "auth", "order")
        )
