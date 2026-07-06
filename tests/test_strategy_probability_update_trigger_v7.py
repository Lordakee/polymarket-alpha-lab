from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_probability_update_trigger_v7.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_probability_update_trigger_v7",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-probability-update-trigger-v7",
        "watch_price_change": d("0.030000"),
        "refresh_price_change": d("0.080000"),
        "watch_source_update_age_minutes": d("60.000000"),
        "refresh_source_update_age_minutes": d("10.000000"),
        "watch_forecast_age_minutes": d("30.000000"),
        "refresh_forecast_age_minutes": d("120.000000"),
        "watch_resolution_deadline_minutes": d("240.000000"),
        "refresh_resolution_deadline_minutes": d("60.000000"),
        "watch_volatility": d("0.250000"),
        "refresh_volatility": d("0.600000"),
        "watch_source_conflict": d("0.300000"),
        "refresh_source_conflict": d("0.650000"),
        "watch_next_update_minutes": d("15.000000"),
        "default_next_update_minutes": d("60.000000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityUpdateTriggerV7Config(**values)


def trigger_input(**overrides: object):
    module = api()
    values = {
        "prior_market_probability": d("0.410000"),
        "current_market_probability": d("0.420000"),
        "source_update_age_minutes": d("90.000000"),
        "forecast_age_minutes": d("10.000000"),
        "minutes_to_resolution": d("600.000000"),
        "volatility": d("0.100000"),
        "source_conflict": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityUpdateTriggerV7Input(**values)


def report(input_value=None, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_probability_update_trigger_v7_report(
        input_value if input_value is not None else trigger_input(),
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_trigger_v7_refreshes_immediately_for_material_update_signals() -> None:
    result = report(
        trigger_input(
            prior_market_probability=d("0.410000"),
            current_market_probability=d("0.500000"),
            source_update_age_minutes=d("5.000000"),
            forecast_age_minutes=d("45.000000"),
            minutes_to_resolution=d("30.000000"),
            volatility=d("0.650000"),
            source_conflict=d("0.700000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-probability-update-trigger-v7"
    assert result.price_change == d("0.090000")
    assert result.trigger_status == "refresh"
    assert result.next_update_minutes == ZERO
    assert result.reason_codes == (
        "price_change_refresh",
        "source_update_refresh",
        "resolution_deadline_refresh",
        "volatility_refresh",
        "source_conflict_refresh",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_trigger_v7_watches_positive_but_sub_refresh_signals() -> None:
    result = report(
        trigger_input(
            prior_market_probability=d("0.410000"),
            current_market_probability=d("0.450000"),
            source_update_age_minutes=d("30.000000"),
            forecast_age_minutes=d("45.000000"),
            minutes_to_resolution=d("180.000000"),
            volatility=d("0.300000"),
            source_conflict=d("0.400000"),
        ),
    )

    assert result.price_change == d("0.040000")
    assert result.trigger_status == "watch"
    assert result.next_update_minutes == d("15.000000")
    assert result.reason_codes == (
        "price_change_watch",
        "source_update_watch",
        "forecast_age_watch",
        "resolution_deadline_watch",
        "volatility_watch",
        "source_conflict_watch",
    )


def test_trigger_v7_defers_until_next_forecast_age_boundary_when_inputs_are_stable() -> None:
    result = report(
        trigger_input(
            prior_market_probability=d("0.410000"),
            current_market_probability=d("0.420000"),
            source_update_age_minutes=d("90.000000"),
            forecast_age_minutes=d("10.000000"),
            minutes_to_resolution=d("600.000000"),
            volatility=d("0.100000"),
            source_conflict=d("0.100000"),
        ),
    )

    assert result.price_change == d("0.010000")
    assert result.trigger_status == "defer"
    assert result.next_update_minutes == d("20.000000")
    assert result.reason_codes == ("probability_update_trigger_v7_defer",)


def test_payload_uses_decimal_strings_utc_timestamps_and_no_public_numbers() -> None:
    module = api()
    result = report(
        trigger_input(
            prior_market_probability=d("0.410000"),
            current_market_probability=d("0.450000"),
            forecast_age_minutes=d("45.000000"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_probability_update_trigger_v7_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["prior_market_probability"] == "0.410000"
    assert payload["current_market_probability"] == "0.450000"
    assert payload["price_change"] == "0.040000"
    assert payload["next_update_minutes"] == "15.000000"
    assert payload["trigger_status"] == "watch"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report()

    for klass in (
        module.StrategyProbabilityUpdateTriggerV7Config,
        module.StrategyProbabilityUpdateTriggerV7Input,
        module.StrategyProbabilityUpdateTriggerV7Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.trigger_status = "refresh"  # type: ignore[misc]

    decimal_result_fields = {
        "prior_market_probability",
        "current_market_probability",
        "price_change",
        "source_update_age_minutes",
        "forecast_age_minutes",
        "minutes_to_resolution",
        "volatility",
        "source_conflict",
        "next_update_minutes",
    }
    for field in fields(result):
        if field.name in decimal_result_fields:
            assert type(getattr(result, field.name)) is Decimal

    with pytest.raises(ValueError, match="prior_market_probability"):
        trigger_input(prior_market_probability=0.41)
    with pytest.raises(ValueError, match="current_market_probability"):
        trigger_input(current_market_probability=1)
    with pytest.raises(ValueError, match="volatility"):
        trigger_input(volatility=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))


def test_validation_rejects_bounds_threshold_sequences_flags_and_types() -> None:
    module = api()
    valid_input = trigger_input()

    with pytest.raises(ValueError, match="input_value"):
        module.build_strategy_probability_update_trigger_v7_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_probability_update_trigger_v7_report(
            valid_input,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        trigger_input(current_market_probability=d("1.000001"))
    with pytest.raises(ValueError, match="forecast_age_minutes"):
        trigger_input(forecast_age_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="refresh_price_change"):
        config(refresh_price_change=d("0.020000"))
    with pytest.raises(ValueError, match="refresh_source_update_age_minutes"):
        config(refresh_source_update_age_minutes=d("90.000000"))
    with pytest.raises(ValueError, match="refresh_resolution_deadline_minutes"):
        config(refresh_resolution_deadline_minutes=d("300.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_input, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_probability_update_trigger_v7_payload(
            replace(report(), readonly=False),
        )
    with pytest.raises(ValueError, match="report"):
        module.strategy_probability_update_trigger_v7_payload(object())


def test_report_revalidates_derived_fields_status_and_reason_codes() -> None:
    result = report()

    with pytest.raises(ValueError, match="price_change"):
        replace(result, price_change=d("0.020000"))
    with pytest.raises(ValueError, match="trigger_status"):
        replace(result, trigger_status="refresh")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("price_change_refresh", "price_change_refresh"))
    with pytest.raises(ValueError, match="next_update_minutes"):
        replace(result, next_update_minutes=d("-1.000000"))


def test_module_scope_has_no_external_io_db_or_live_action_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_roots = {
        "asyncio",
        "csv",
        "http",
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
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
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
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

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
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert module_name.split(".")[0] not in forbidden_import_roots
