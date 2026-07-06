from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_source_latency_anomaly_guard_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_source_latency_anomaly_guard_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def latency_input(**overrides: object):
    module = api()
    values = {
        "source_family": "official",
        "median_latency_minutes": d("10.000000"),
        "current_latency_minutes": d("8.000000"),
        "historical_failure_rate": d("0.050000"),
        "source_reliability": d("0.900000"),
        "market_time_sensitivity": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategySourceLatencyAnomalyGuardV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_strategy_source_latency_anomaly_guard_v10(
        latency_input(**overrides),
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


def test_critical_latency_anomaly_escalates_when_delay_compounds_with_source_risk() -> None:
    decision = evaluate(
        current_latency_minutes=d("38.000000"),
        historical_failure_rate=d("0.300000"),
        source_reliability=d("0.700000"),
        market_time_sensitivity=d("0.800000"),
    )

    assert is_dataclass(decision)
    assert decision.source_family == "official"
    assert decision.median_latency_minutes == d("10.000000")
    assert decision.current_latency_minutes == d("38.000000")
    assert decision.historical_failure_rate == d("0.300000")
    assert decision.source_reliability == d("0.700000")
    assert decision.market_time_sensitivity == d("0.800000")
    assert decision.latency_ratio == d("3.800000")
    assert decision.anomaly_status == "critical"
    assert decision.latency_penalty == d("0.676667")
    assert decision.refresh_action == "escalate_manual_review"
    assert decision.reason_codes == (
        "latency_anomaly_critical",
        "latency_above_anomaly_multiplier",
        "latency_compounded_by_source_risk",
        "historical_failure_rate_high",
        "market_time_sensitivity_high",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_watch_and_anomaly_statuses_select_refresh_actions_without_trading_surface() -> None:
    watch = evaluate(
        current_latency_minutes=d("18.000000"),
        historical_failure_rate=d("0.050000"),
        source_reliability=d("0.900000"),
        market_time_sensitivity=d("0.250000"),
    )
    anomaly = evaluate(
        current_latency_minutes=d("30.000000"),
        historical_failure_rate=d("0.050000"),
        source_reliability=d("0.900000"),
        market_time_sensitivity=d("0.250000"),
    )

    assert watch.anomaly_status == "watch"
    assert watch.latency_ratio == d("1.800000")
    assert watch.latency_penalty == d("0.150333")
    assert watch.refresh_action == "refresh_soon"
    assert watch.reason_codes == (
        "latency_anomaly_watch",
        "latency_above_watch_multiplier",
    )

    assert anomaly.anomaly_status == "anomaly"
    assert anomaly.latency_ratio == d("3.000000")
    assert anomaly.refresh_action == "refresh_now"
    assert anomaly.reason_codes == (
        "latency_anomaly_detected",
        "latency_above_anomaly_multiplier",
    )


def test_normal_latency_keeps_schedule_with_zero_penalty() -> None:
    decision = evaluate()

    assert decision.anomaly_status == "normal"
    assert decision.latency_ratio == d("0.800000")
    assert decision.latency_penalty == d("0.000000")
    assert decision.refresh_action == "keep_schedule"
    assert decision.reason_codes == ("latency_within_expected_range",)


def test_risk_amplifies_small_delay_into_watch_without_hard_blocking() -> None:
    decision = evaluate(
        current_latency_minutes=d("12.000000"),
        historical_failure_rate=d("0.300000"),
        source_reliability=d("0.550000"),
        market_time_sensitivity=d("0.800000"),
    )

    assert decision.anomaly_status == "watch"
    assert decision.latency_ratio == d("1.200000")
    assert decision.latency_penalty == d("0.050083")
    assert decision.refresh_action == "refresh_soon"
    assert decision.reason_codes == (
        "latency_anomaly_watch",
        "latency_risk_amplified_delay",
        "latency_compounded_by_source_risk",
        "historical_failure_rate_high",
        "source_reliability_low",
        "market_time_sensitivity_high",
    )


def test_payload_uses_decimal_strings_reason_lists_and_no_floats() -> None:
    module = api()
    decision = evaluate(
        source_family="market_data",
        current_latency_minutes=d("18.000000"),
    )

    payload = module.strategy_source_latency_anomaly_guard_v10_payload(decision)
    encoded = json.dumps(payload, sort_keys=True)

    assert decision.payload == payload
    assert payload["source_family"] == "market_data"
    assert payload["median_latency_minutes"] == "10.000000"
    assert payload["current_latency_minutes"] == "18.000000"
    assert payload["historical_failure_rate"] == "0.050000"
    assert payload["source_reliability"] == "0.900000"
    assert payload["market_time_sensitivity"] == "0.200000"
    assert payload["latency_ratio"] == "1.800000"
    assert payload["latency_penalty"] == "0.145333"
    assert payload["reason_codes"] == [
        "latency_anomaly_watch",
        "latency_above_watch_multiplier",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"0.145333"' in encoded
    assert_no_float_values(payload)


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "median_latency_minutes",
        "current_latency_minutes",
        "historical_failure_rate",
        "source_reliability",
        "market_time_sensitivity",
        "latency_ratio",
        "latency_penalty",
    }

    for cls in (
        module.StrategySourceLatencyAnomalyGuardV10Input,
        module.StrategySourceLatencyAnomalyGuardV10Result,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_family"):
        latency_input(source_family=_StringSubclass("official"))

    with pytest.raises(ValueError, match="median_latency_minutes must be a Decimal"):
        latency_input(median_latency_minutes=10)

    with pytest.raises(ValueError, match="current_latency_minutes must be a Decimal"):
        latency_input(current_latency_minutes=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="median_latency_minutes must be positive"):
        latency_input(median_latency_minutes=d("0.000000"))

    with pytest.raises(ValueError, match="current_latency_minutes must be nonnegative"):
        latency_input(current_latency_minutes=d("-0.000001"))

    with pytest.raises(ValueError, match="historical_failure_rate must be between 0 and 1"):
        latency_input(historical_failure_rate=d("1.000001"))

    with pytest.raises(ValueError, match="source_reliability must be finite"):
        latency_input(source_reliability=Decimal("NaN"))

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.StrategySourceLatencyAnomalyGuardV10Result(
            source_family="official",
            median_latency_minutes=d("10.000000"),
            current_latency_minutes=d("18.000000"),
            historical_failure_rate=d("0.050000"),
            source_reliability=d("0.900000"),
            market_time_sensitivity=d("0.250000"),
            latency_ratio=d("1.800000"),
            anomaly_status="watch",
            latency_penalty=d("0.150333"),
            refresh_action="refresh_soon",
            reason_codes=("latency_anomaly_watch", "latency_anomaly_watch"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(latency_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(evaluate(), readonly=False)

    with pytest.raises(FrozenInstanceError):
        decision = evaluate()
        decision.anomaly_status = "watch"  # type: ignore[misc]


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        latency_input(source_family="postgresql://user:secret@db.example.local/source")


def test_module_scope_is_paper_report_readonly_with_no_external_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "open(",
        "requests",
        "http",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
