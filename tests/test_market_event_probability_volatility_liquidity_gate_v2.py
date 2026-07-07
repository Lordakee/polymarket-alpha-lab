from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_NAME = "polymarket_alpha_lab.market_event_probability_volatility_liquidity_gate_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_event_probability_volatility_liquidity_gate_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_EVENT_PROBABILITY_VOLATILITY_LIQUIDITY_GATE_V2_CONFIG_VERSION
        ),
        "volatility_watch_threshold": d("0.080000"),
        "volatility_block_threshold": d("0.150000"),
        "short_horizon_volatility_multiplier": d("4.000000"),
        "max_pass_bid_ask_spread": d("0.030000"),
        "max_watch_bid_ask_spread": d("0.080000"),
        "min_pass_depth_usdc": d("1000.000000"),
        "min_watch_depth_usdc": d("250.000000"),
        "min_pass_volume_24h": d("5000.000000"),
        "min_watch_volume_24h": d("1000.000000"),
        "near_close_minutes": d("60.000000"),
    }
    values.update(overrides)
    return module.MarketEventProbabilityVolatilityLiquidityGateV2Config(**values)


def event(**overrides: object) -> Any:
    module = api()
    values = {
        "market_id": "market-pass",
        "event_slug": "event-pass",
        "category": "sports.basketball",
        "probability_move_24h": d("0.020000"),
        "probability_move_1h": d("0.005000"),
        "bid_ask_spread": d("0.015000"),
        "depth_usdc": d("2000.000000"),
        "volume_24h": d("10000.000000"),
        "minutes_to_close": d("240.000000"),
    }
    values.update(overrides)
    return module.MarketEventProbabilityVolatilityLiquidityGateV2EventInput(**values)


def report(
    *events: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_event_probability_volatility_liquidity_gate_v2_report(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric(item)
    elif type(value) is list:
        for item in value:
            assert_no_public_numeric(item)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_gate_scores_sorts_and_rolls_up_probability_volatility_liquidity_quality() -> None:
    result = report(
        event(
            market_id="market-pass",
            event_slug="event-pass",
            category="sports.basketball",
            probability_move_24h=d("0.020000"),
            probability_move_1h=d("0.005000"),
            bid_ask_spread=d("0.015000"),
            depth_usdc=d("2000.000000"),
            volume_24h=d("10000.000000"),
            minutes_to_close=d("240.000000"),
        ),
        event(
            market_id="market-watch",
            event_slug="event-watch",
            category="crypto",
            probability_move_24h=d("0.090000"),
            probability_move_1h=d("0.010000"),
            bid_ask_spread=d("0.050000"),
            depth_usdc=d("800.000000"),
            volume_24h=d("4000.000000"),
            minutes_to_close=d("120.000000"),
        ),
        event(
            market_id="market-block",
            event_slug="event-block",
            category="macro",
            probability_move_24h=d("0.120000"),
            probability_move_1h=d("0.040000"),
            bid_ask_spread=d("0.100000"),
            depth_usdc=d("200.000000"),
            volume_24h=d("600.000000"),
            minutes_to_close=d("30.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.event_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.high_volatility_count == d("2.000000")
    assert result.low_liquidity_count == d("2.000000")
    assert result.near_close_count == d("1.000000")
    assert result.max_volatility_score == d("0.160000")
    assert result.min_liquidity_score == d("0.000000")
    assert result.report_status == "block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_id for row in result.rows) == (
        "market-block",
        "market-watch",
        "market-pass",
    )
    blocked, watched, passed = result.rows

    assert blocked.status == "block"
    assert blocked.volatility_score == d("0.160000")
    assert blocked.liquidity_score == d("0.000000")
    assert blocked.reason_codes == (
        "probability_volatility_blocked",
        "wide_bid_ask_spread_blocked",
        "thin_depth_blocked",
        "low_volume_blocked",
        "near_close_watch",
    )

    assert watched.status == "watch"
    assert watched.volatility_score == d("0.090000")
    assert watched.liquidity_score == d("0.375000")
    assert watched.reason_codes == (
        "probability_volatility_watch",
        "wide_bid_ask_spread_watch",
        "thin_depth_watch",
        "low_volume_watch",
    )

    assert passed.status == "pass"
    assert passed.volatility_score == d("0.020000")
    assert passed.liquidity_score == d("0.812500")
    assert passed.reason_codes == (
        "event_probability_volatility_liquidity_gate_passed",
    )
    assert len({row.derived_validation_digest for row in result.rows}) == 3

    assert [(item.reason_code, item.count) for item in result.reason_code_counts] == [
        ("event_probability_volatility_liquidity_gate_passed", d("1.000000")),
        ("low_volume_blocked", d("1.000000")),
        ("low_volume_watch", d("1.000000")),
        ("near_close_watch", d("1.000000")),
        ("probability_volatility_blocked", d("1.000000")),
        ("probability_volatility_watch", d("1.000000")),
        ("thin_depth_blocked", d("1.000000")),
        ("thin_depth_watch", d("1.000000")),
        ("wide_bid_ask_spread_blocked", d("1.000000")),
        ("wide_bid_ask_spread_watch", d("1.000000")),
    ]


def test_empty_input_returns_empty_status_zero_decimals_and_digest() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.MarketEventProbabilityVolatilityLiquidityGateV2Report
    assert empty.event_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.high_volatility_count == ZERO
    assert empty.low_liquidity_count == ZERO
    assert empty.near_close_count == ZERO
    assert empty.max_volatility_score == ZERO
    assert empty.min_liquidity_score == ZERO
    assert empty.report_status == "empty"
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)

    for public_value in (config(), event(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True
        assert public_value.paper_only is True
        assert public_value.report_only is True
        assert public_value.readonly is True


def test_validation_rejects_bad_decimals_thresholds_duplicates_flags_and_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="probability_move_24h"):
        event(probability_move_24h=1)
    with pytest.raises(ValueError, match="probability_move_1h"):
        event(probability_move_1h=d("0.0100001"))
    with pytest.raises(ValueError, match="bid_ask_spread"):
        event(bid_ask_spread=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="depth_usdc"):
        event(depth_usdc=d("-1.000000"))
    with pytest.raises(ValueError, match="minutes_to_close"):
        event(minutes_to_close=d("-0.000001"))
    with pytest.raises(ValueError, match="market_id"):
        event(market_id=" market-id")
    with pytest.raises(ValueError, match="paper_only"):
        event(paper_only=False)
    with pytest.raises(ValueError, match="volatility_watch_threshold"):
        config(volatility_watch_threshold=d("0.200000"))
    with pytest.raises(ValueError, match="short_horizon_volatility_multiplier"):
        config(short_horizon_volatility_multiplier=d("0.000000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="duplicate market event"):
        report(
            event(market_id="duplicate", event_slug="same"),
            event(market_id="duplicate", event_slug="same"),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_event_probability_volatility_liquidity_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    result = report(event(market_id="tamper-check", event_slug="tamper-check"))
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_count"):
        replace(result, event_count=d("2.000000"))
    with pytest.raises(ValueError, match="liquidity_score|derived_validation_digest"):
        replace(result.rows[0], liquidity_score=d("0.999999"))


def test_payload_uses_decimal_strings_validates_digest_and_rejects_unsafe_values() -> None:
    module = api()
    result = report(
        event(
            market_id="payload-market",
            event_slug="payload-event",
            probability_move_24h=d("0.090000"),
            probability_move_1h=d("0.010000"),
            bid_ask_spread=d("0.050000"),
            depth_usdc=d("800.000000"),
            volume_24h=d("4000.000000"),
            minutes_to_close=d("120.000000"),
        ),
    )

    payload = module.market_event_probability_volatility_liquidity_gate_v2_payload(result)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["watch_count"] == "1.000000"
    assert payload["report_status"] == "watch"
    assert payload["max_volatility_score"] == "0.090000"
    assert payload["min_liquidity_score"] == "0.375000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["market_id"] == "payload-market"
    assert payload["rows"][0]["volatility_score"] == "0.090000"
    assert payload["rows"][0]["liquidity_score"] == "0.375000"
    assert module.validate_market_event_probability_volatility_liquidity_gate_v2_payload(
        payload,
    )
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "event_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_market_event_probability_volatility_liquidity_gate_v2_payload(
            numeric_payload,
        )

    tampered = {**payload, "watch_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_event_probability_volatility_liquidity_gate_v2_payload(
            tampered,
        )

    unsafe_payload = {
        **payload,
        unsafe_text("wal", "let", "_address"): "redacted",
    }
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_market_event_probability_volatility_liquidity_gate_v2_payload(
            unsafe_payload,
        )


def test_exports_static_scope_and_decimal_only_public_fields() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_MARKET_EVENT_PROBABILITY_VOLATILITY_LIQUIDITY_GATE_V2_CONFIG_VERSION",
        "MarketEventProbabilityVolatilityLiquidityGateV2Config",
        "MarketEventProbabilityVolatilityLiquidityGateV2EventInput",
        "MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount",
        "MarketEventProbabilityVolatilityLiquidityGateV2Report",
        "MarketEventProbabilityVolatilityLiquidityGateV2Row",
        "build_market_event_probability_volatility_liquidity_gate_v2_report",
        "market_event_probability_volatility_liquidity_gate_v2_payload",
        "validate_market_event_probability_volatility_liquidity_gate_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    result = report(event())
    for instance in (config(), event(), result.rows[0], result, *result.reason_code_counts):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_score",
                    "_move_24h",
                    "_move_1h",
                    "_spread",
                    "_usdc",
                    "_24h",
                    "_minutes",
                    "_threshold",
                    "_multiplier",
                    "_to_close",
                ),
            ):
                assert type(value) is Decimal

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_fragments = (
        "aiohttp",
        "api_key",
        "auth_token",
        "cancel_order",
        "create_order",
        "database_url",
        "httpx",
        "live_trading",
        "network_client",
        "place_order",
        "private_key",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "submit_order",
        "supabase",
        "trade_executor",
        "urllib",
        "wallet",
        "web3",
    )
    lowered_source = source.lower()
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "executemany",
        "float",
        "open",
        "request",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names
