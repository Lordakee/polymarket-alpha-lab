from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_information_decay_alert_v10"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def alert_input(**overrides: object) -> Any:
    module = api()
    values = {
        "market_id": "fed-july-policy-path",
        "last_primary_update_minutes": d("30.000000"),
        "last_secondary_update_minutes": d("90.000000"),
        "market_price_move_bps": d("20.000000"),
        "source_reliability_score": d("0.900000"),
        "time_to_resolution_minutes": d("1440.000000"),
        "team_capacity_score": d("0.900000"),
    }
    values.update(overrides)
    return module.StrategyMarketInformationDecayAlertV10Input(**values)


def evaluate(**overrides: object) -> Any:
    module = api()
    return module.evaluate_strategy_market_information_decay_alert_v10(
        alert_input(**overrides),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_payload_has_no_runtime_numbers(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_has_no_runtime_numbers(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_has_no_runtime_numbers(child)


def test_current_information_keeps_monitor_priority_with_long_sla() -> None:
    module = api()

    result = evaluate()

    assert isinstance(result, module.StrategyMarketInformationDecayAlertV10Result)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.alert_status == "current"
    assert result.refresh_priority == "monitor"
    assert result.sla_minutes == d("480.000000")
    assert result.reason_codes == ("information_current",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_watch_alert_tracks_aging_sources_before_refresh_is_due() -> None:
    result = evaluate(
        last_primary_update_minutes=d("180.000000"),
        last_secondary_update_minutes=d("300.000000"),
        market_price_move_bps=d("75.000000"),
        source_reliability_score=d("0.800000"),
        time_to_resolution_minutes=d("720.000000"),
    )

    assert result.alert_status == "watch"
    assert result.refresh_priority == "normal"
    assert result.sla_minutes == d("240.000000")
    assert result.reason_codes == (
        "information_decay_watch",
        "market_move_watch",
        "primary_update_aging",
        "secondary_update_aging",
    )


def test_refresh_due_alert_tightens_sla_for_material_move_and_near_resolution() -> None:
    result = evaluate(
        last_primary_update_minutes=d("420.000000"),
        last_secondary_update_minutes=d("900.000000"),
        market_price_move_bps=d("180.000000"),
        source_reliability_score=d("0.550000"),
        time_to_resolution_minutes=d("180.000000"),
        team_capacity_score=d("0.450000"),
    )

    assert result.alert_status == "refresh_due"
    assert result.refresh_priority == "high"
    assert result.sla_minutes == d("60.000000")
    assert result.reason_codes == (
        "information_decay_refresh_due",
        "market_move_material",
        "primary_update_stale",
        "resolution_near",
        "secondary_update_stale",
        "source_reliability_low",
        "team_capacity_constrained",
    )


def test_critical_alert_uses_urgent_priority_and_immediate_sla() -> None:
    result = evaluate(
        last_primary_update_minutes=d("900.000000"),
        last_secondary_update_minutes=d("1800.000000"),
        market_price_move_bps=d("350.000000"),
        source_reliability_score=d("0.400000"),
        time_to_resolution_minutes=d("45.000000"),
        team_capacity_score=d("0.200000"),
    )

    assert result.alert_status == "critical"
    assert result.refresh_priority == "urgent"
    assert result.sla_minutes == d("15.000000")
    assert result.reason_codes == (
        "information_decay_critical",
        "market_move_critical",
        "primary_update_critical",
        "resolution_imminent",
        "secondary_update_critical",
        "source_reliability_low",
        "team_capacity_severely_constrained",
    )


def test_payload_serializes_decimals_as_strings_and_exposes_result_payload() -> None:
    module = api()
    result = evaluate(
        last_primary_update_minutes=d("420.000000"),
        last_secondary_update_minutes=d("900.000000"),
        market_price_move_bps=d("180.000000"),
        source_reliability_score=d("0.550000"),
        time_to_resolution_minutes=d("180.000000"),
        team_capacity_score=d("0.450000"),
    )

    payload = module.strategy_market_information_decay_alert_v10_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert result.payload == payload
    assert payload["market_id"] == "fed-july-policy-path"
    assert payload["last_primary_update_minutes"] == "420.000000"
    assert payload["market_price_move_bps"] == "180.000000"
    assert payload["source_reliability_score"] == "0.550000"
    assert payload["sla_minutes"] == "60.000000"
    assert payload["alert_status"] == "refresh_due"
    assert payload["refresh_priority"] == "high"
    assert payload["reason_codes"] == [
        "information_decay_refresh_due",
        "market_move_material",
        "primary_update_stale",
        "resolution_near",
        "secondary_update_stale",
        "source_reliability_low",
        "team_capacity_constrained",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"60.000000"' in encoded
    assert_payload_has_no_runtime_numbers(payload)


def test_validation_rejects_non_decimal_granular_nonfinite_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_id must be a nonblank trimmed string"):
        alert_input(market_id=" fed ")
    with pytest.raises(ValueError, match="last_primary_update_minutes must be a Decimal"):
        alert_input(last_primary_update_minutes=30)
    with pytest.raises(ValueError, match="source_reliability_score must be exactly Decimal"):
        alert_input(source_reliability_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="market_price_move_bps precision is too granular"):
        alert_input(market_price_move_bps=d("20.0000001"))
    with pytest.raises(ValueError, match="last_secondary_update_minutes must be finite"):
        alert_input(last_secondary_update_minutes=d("NaN"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        alert_input(time_to_resolution_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="team_capacity_score must be between zero and one"):
        alert_input(team_capacity_score=d("1.000001"))
    with pytest.raises(ValueError, match="input paper_only must be True"):
        alert_input(paper_only=False)

    with pytest.raises(ValueError, match="input_row must be a StrategyMarketInformationDecayAlertV10Input"):
        module.evaluate_strategy_market_information_decay_alert_v10(object())

    result = evaluate()
    with pytest.raises(FrozenInstanceError):
        result.alert_status = "critical"  # type: ignore[misc]
    with pytest.raises(ValueError, match="result readonly must be True"):
        module.StrategyMarketInformationDecayAlertV10Result(
            **{**result.__dict__, "readonly": False},
        )


def test_module_is_paper_report_readonly_without_io_or_execution_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_information_decay_alert_v10.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "open",
        "connect",
        "cancel",
        "replace",
        "wallet",
        "order",
        "create_order",
        "place_order",
        "submit_order",
        "trade",
        "auth",
        "login",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "trade",
        "execute",
        "database",
        "durable file",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
