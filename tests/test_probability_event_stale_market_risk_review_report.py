from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.probability_event_stale_market_risk_review_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_stale_market_risk_review_report.py"
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing stale market risk review report module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "last_trade_stale_after_hours": d("12.000000"),
        "last_orderbook_stale_after_minutes": d("30.000000"),
        "price_move_watch_threshold": d("0.050000"),
        "price_move_block_threshold": d("0.120000"),
        "source_refresh_stale_after_hours": d("8.000000"),
        "market_close_urgent_hours": d("24.000000"),
    }
    values.update(overrides)
    return module.ProbabilityEventStaleMarketRiskReviewConfig(**values)


def event_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "last_trade_age_hours": d("2.000000"),
        "last_orderbook_age_minutes": d("5.000000"),
        "price_move_since_forecast": d("0.010000"),
        "source_refresh_age_hours": d("1.000000"),
        "market_close_hours": d("72.000000"),
    }
    values.update(overrides)
    return module.ProbabilityEventStaleMarketRiskReviewInput(**values)


def report(item: object | None = None, *, cfg: object | None = None) -> Any:
    module = api()
    return module.build_probability_event_stale_market_risk_review_report(
        event_input() if item is None else item,
        config=config() if cfg is None else cfg,
    )


def assert_no_public_numbers(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)
    else:
        assert value is None or isinstance(value, (str, bool))


def assert_no_execution_surface(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for fragment in (
        "auth",
        "wallet",
        "private_key",
        "place_order",
        "create_order",
        "submit_order",
        "cancel_order",
        "execute",
        "execution",
        "replace",
        "broker",
        "live",
        "database",
        "db",
        "position",
    ):
        assert fragment not in rendered


def test_ready_stale_market_risk_report_is_readonly_filter_output() -> None:
    module = api()
    result = report()

    assert is_dataclass(result)
    assert result.config_version == "probability-event-stale-market-risk-review-v0"
    assert result.last_trade_age_hours == d("2.000000")
    assert result.last_orderbook_age_minutes == d("5.000000")
    assert result.price_move_since_forecast == d("0.010000")
    assert result.source_refresh_age_hours == d("1.000000")
    assert result.market_close_hours == d("72.000000")
    assert result.stale_risk_status == "pass"
    assert result.reason_codes == ("stale_market_risk_clear",)
    assert result.manual_next_step == "allow_report_only_stale_market_risk_screen"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.probability_event_stale_market_risk_review_report_payload(result)
    assert payload == result.payload
    assert payload["last_trade_age_hours"] == "2.000000"
    assert payload["last_orderbook_age_minutes"] == "5.000000"
    assert payload["price_move_since_forecast"] == "0.010000"
    assert payload["stale_risk_status"] == "pass"
    assert payload["reason_codes"] == ["stale_market_risk_clear"]
    assert payload["manual_next_step"] == "allow_report_only_stale_market_risk_screen"
    assert_no_public_numbers(payload)
    assert_no_execution_surface(payload)


def test_watch_and_block_reasons_prioritize_stale_market_review() -> None:
    watch = report(
        event_input(
            last_trade_age_hours=d("12.000001"),
            last_orderbook_age_minutes=d("30.000001"),
            price_move_since_forecast=d("0.050001"),
            source_refresh_age_hours=d("8.000001"),
        ),
    )

    assert watch.stale_risk_status == "watch"
    assert watch.reason_codes == (
        "last_trade_stale_watch",
        "orderbook_stale_watch",
        "price_move_since_forecast_watch",
        "source_refresh_stale_watch",
    )
    assert watch.manual_next_step == "manual_review_stale_market_risk_before_shortlist"

    blocked = report(
        event_input(
            last_trade_age_hours=d("12.000001"),
            price_move_since_forecast=d("0.120001"),
            source_refresh_age_hours=d("8.000001"),
            market_close_hours=d("6.000000"),
        ),
    )

    assert blocked.stale_risk_status == "blocked"
    assert blocked.reason_codes == (
        "urgent_market_close_stale_block",
        "last_trade_stale_watch",
        "price_move_since_forecast_block",
        "source_refresh_stale_watch",
    )
    assert blocked.manual_next_step == "exclude_report_only_until_market_freshness_reviewed"


def test_market_close_without_stale_signals_does_not_block() -> None:
    near_close = report(event_input(market_close_hours=d("1.000000")))

    assert near_close.stale_risk_status == "pass"
    assert near_close.reason_codes == ("stale_market_risk_clear",)
    assert near_close.manual_next_step == "allow_report_only_stale_market_risk_screen"


def test_decimal_only_validation_and_frozen_paper_flags() -> None:
    module = api()
    item = event_input()
    result = report(item)

    assert tuple(module.__all__) == (
        "DEFAULT_PROBABILITY_EVENT_STALE_MARKET_RISK_REVIEW_CONFIG_VERSION",
        "ProbabilityEventStaleMarketRiskReviewConfig",
        "ProbabilityEventStaleMarketRiskReviewInput",
        "ProbabilityEventStaleMarketRiskReviewReport",
        "build_probability_event_stale_market_risk_review_report",
        "probability_event_stale_market_risk_review_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    for instance in (config(), item, result):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "payload",
                "config_version",
                "stale_risk_status",
                "reason_codes",
                "manual_next_step",
            }:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(FrozenInstanceError):
        item.last_trade_age_hours = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedInput", (module.ProbabilityEventStaleMarketRiskReviewInput,), {})
    with pytest.raises(ValueError, match="last_trade_age_hours must be a Decimal"):
        event_input(last_trade_age_hours=2)
    with pytest.raises(ValueError, match="last_orderbook_age_minutes must be a Decimal"):
        event_input(last_orderbook_age_minutes=5.0)
    with pytest.raises(ValueError, match="exact Decimal"):
        event_input(price_move_since_forecast=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="price_move_since_forecast must be between 0 and 1"):
        event_input(price_move_since_forecast=d("1.000001"))
    with pytest.raises(ValueError, match="market_close_hours must be nonnegative"):
        event_input(market_close_hours=d("-0.000001"))


def test_report_consistency_rejects_tampered_outputs() -> None:
    module = api()
    result = report(
        event_input(
            last_trade_age_hours=d("13.000000"),
            price_move_since_forecast=d("0.060000"),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes must match input fields"):
        replace(result, reason_codes=("stale_market_risk_clear",))
    with pytest.raises(ValueError, match="stale_risk_status must match reason_codes"):
        replace(result, stale_risk_status="pass")
    with pytest.raises(ValueError, match="manual_next_step must match stale_risk_status"):
        replace(
            result,
            manual_next_step="allow_report_only_stale_market_risk_screen",
        )
    with pytest.raises(ValueError, match="report must be"):
        module.probability_event_stale_market_risk_review_report_payload(
            {"stale_risk_status": "pass"},
        )


def test_module_does_not_import_persistence_live_auth_wallet_or_order_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "requests",
        "urllib",
        "websocket",
        "wallet",
        "auth",
        "order",
        "position",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    source = MODULE_PATH.read_text().lower()
    for forbidden in (
        "private_key",
        "wallet",
        "place_order",
        "create_order",
        "submit_order",
        "cancel_order",
        "position",
        "live",
    ):
        assert forbidden not in source
