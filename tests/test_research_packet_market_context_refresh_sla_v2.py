from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_market_context_refresh_sla_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_packet_market_context_refresh_sla_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} is not implemented")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object) -> object:
    module = api()
    values = {
        "packet_id": "packet_rates",
        "market_id": "market_fed_july",
        "price_move_at": GENERATED_AT - timedelta(minutes=5),
        "latest_source_at": GENERATED_AT - timedelta(minutes=10),
        "official_update_at": GENERATED_AT - timedelta(minutes=20),
        "liquidity_context_at": GENERATED_AT - timedelta(minutes=15),
        "market_closes_at": GENERATED_AT + timedelta(days=1),
        "contradiction_detected_at": None,
        "contradiction_follow_up_at": None,
    }
    values.update(overrides)
    return module.ResearchPacketMarketContextRefreshSlaV2Observation(**values)


def build_report(*observations: object, generated_at: datetime = GENERATED_AT) -> object:
    module = api()
    return module.build_research_packet_market_context_refresh_sla_v2_report(
        observations,
        generated_at=generated_at,
    )


def test_builds_phase1_market_context_refresh_report_with_age_metrics() -> None:
    pass_context = observation(
        market_id="market_fed_july",
        price_move_at=GENERATED_AT - timedelta(seconds=300),
        latest_source_at=GENERATED_AT - timedelta(seconds=600),
        official_update_at=GENERATED_AT - timedelta(seconds=1200),
        liquidity_context_at=GENERATED_AT - timedelta(seconds=900),
        market_closes_at=GENERATED_AT + timedelta(seconds=86400),
    )
    watch_context = observation(
        market_id="market_stale_close",
        price_move_at=GENERATED_AT - timedelta(seconds=1800),
        latest_source_at=GENERATED_AT - timedelta(seconds=2000),
        official_update_at=GENERATED_AT - timedelta(seconds=1000),
        liquidity_context_at=GENERATED_AT - timedelta(seconds=1200),
        market_closes_at=GENERATED_AT + timedelta(seconds=3600),
    )
    blocked_context = observation(
        market_id="market_conflict",
        price_move_at=GENERATED_AT - timedelta(seconds=600),
        latest_source_at=GENERATED_AT - timedelta(seconds=700),
        official_update_at=GENERATED_AT - timedelta(seconds=1000),
        liquidity_context_at=GENERATED_AT - timedelta(seconds=600),
        market_closes_at=GENERATED_AT + timedelta(seconds=7200),
        contradiction_detected_at=GENERATED_AT - timedelta(seconds=10800),
        contradiction_follow_up_at=None,
    )

    report = build_report(watch_context, blocked_context, pass_context)
    rows = {row.market_id: row for row in report.rows}

    assert tuple(row.market_id for row in report.rows) == (
        "market_conflict",
        "market_fed_july",
        "market_stale_close",
    )
    assert report.report_status == "blocked"
    assert report.market_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.price_move_stale_count == d("1.000000")
    assert report.latest_source_stale_count == d("1.000000")
    assert report.official_update_stale_count == d("0.000000")
    assert report.liquidity_context_stale_count == d("0.000000")
    assert report.contradiction_follow_up_stale_count == d("1.000000")
    assert report.close_urgent_count == d("1.000000")
    assert report.oldest_price_move_age_seconds == d("1800.000000")
    assert report.oldest_latest_source_age_seconds == d("2000.000000")
    assert report.oldest_official_update_age_seconds == d("1200.000000")
    assert report.oldest_liquidity_context_age_seconds == d("1200.000000")
    assert report.oldest_contradiction_follow_up_age_seconds == d("10800.000000")
    assert report.minimum_seconds_to_close == d("3600.000000")
    assert report.reason_codes == (
        "market_context_refresh_fresh",
        "price_move_age_stale",
        "latest_source_age_stale",
        "contradiction_follow_up_missing",
        "close_urgency_near",
        "close_urgency_urgent",
        "market_context_refresh_watch",
        "market_context_refresh_blocked",
    )

    pass_row = rows["market_fed_july"]
    assert pass_row.row_status == "pass"
    assert pass_row.price_move_age_seconds == d("300.000000")
    assert pass_row.latest_source_age_seconds == d("600.000000")
    assert pass_row.official_update_age_seconds == d("1200.000000")
    assert pass_row.liquidity_context_age_seconds == d("900.000000")
    assert pass_row.contradiction_follow_up_age_seconds == d("0.000000")
    assert pass_row.seconds_to_close == d("86400.000000")
    assert pass_row.close_urgency == "normal"
    assert pass_row.reason_codes == ("market_context_refresh_fresh",)

    watch_row = rows["market_stale_close"]
    assert watch_row.row_status == "watch"
    assert watch_row.price_move_stale is True
    assert watch_row.latest_source_stale is True
    assert watch_row.close_urgency == "urgent"
    assert watch_row.reason_codes == (
        "price_move_age_stale",
        "latest_source_age_stale",
        "close_urgency_urgent",
        "market_context_refresh_watch",
    )

    blocked_row = rows["market_conflict"]
    assert blocked_row.row_status == "blocked"
    assert blocked_row.contradiction_follow_up_stale is True
    assert blocked_row.contradiction_follow_up_age_seconds == d("10800.000000")
    assert blocked_row.close_urgency == "near"
    assert blocked_row.reason_codes == (
        "contradiction_follow_up_missing",
        "close_urgency_near",
        "market_context_refresh_blocked",
    )


def test_payload_serializes_decimals_as_strings_and_digest_is_stable() -> None:
    first = observation(market_id="market_b")
    second = observation(
        market_id="market_a",
        price_move_at=GENERATED_AT - timedelta(seconds=600),
    )

    report = build_report(first, second)
    same_report = build_report(second, first)
    payload = report.payload

    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert tuple(row.market_id for row in report.rows) == ("market_a", "market_b")
    assert json.dumps(payload, sort_keys=True)
    assert payload["market_count"] == "2.000000"
    assert payload["rows"][0]["price_move_age_seconds"] == "600.000000"
    assert payload["rows"][0]["seconds_to_close"] == "86400.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_public_numeric_values_are_decimal(report)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchPacketMarketContextRefreshSlaV2Config()
    source = observation()
    report = build_report(source)
    row = report.rows[0]

    for item in (config, source, row, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        _assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchPacketMarketContextRefreshSlaV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_validation_rejects_non_decimal_future_times_unsafe_values_and_bad_digest() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchPacketMarketContextRefreshSlaV2Config(
            price_move_max_age_seconds=900,
        )
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(
            observation(price_move_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        observation(market_id="wallet_context")

    report = build_report(observation())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="market_count"):
        replace(report, market_count=d("2.000000"))
    with pytest.raises(ValueError, match="nonnegative"):
        replace(report.rows[0], price_move_age_seconds=d("-1.000000"))


def test_module_scope_has_no_io_network_auth_wallet_order_trading_or_db_surface() -> None:
    module = api()
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
        "database",
        "db",
        "http",
        "io",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }
    unsafe_public_terms = (
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_public_terms)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if isinstance(value, (str, datetime)):
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)
