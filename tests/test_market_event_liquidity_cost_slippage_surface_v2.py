from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.market_event_liquidity_cost_slippage_surface_v2",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "market_event_liquidity_cost_slippage_surface_v2 module is missing: "
            f"{exc}",
        )


def d(value: str) -> Decimal:
    return Decimal(value)


def event(
    market_id: str = "market-pass",
    event_slug: str = "candidate-pass",
    category: str = "politics",
    *,
    notional_usdc: str | Decimal = "100.000000",
    orderbook_depth_usdc: str | Decimal = "1000.000000",
    bid_ask_spread: str | Decimal = "0.010000",
    taker_fee_rate: str | Decimal = "0.002000",
    volatility_score: str | Decimal = "0.020000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketEventLiquidityCostSlippageSurfaceV2Input(
        market_id=market_id,
        event_slug=event_slug,
        category=category,
        notional_usdc=notional_usdc if isinstance(notional_usdc, Decimal) else d(notional_usdc),
        orderbook_depth_usdc=(
            orderbook_depth_usdc
            if isinstance(orderbook_depth_usdc, Decimal)
            else d(orderbook_depth_usdc)
        ),
        bid_ask_spread=bid_ask_spread if isinstance(bid_ask_spread, Decimal) else d(bid_ask_spread),
        taker_fee_rate=taker_fee_rate if isinstance(taker_fee_rate, Decimal) else d(taker_fee_rate),
        volatility_score=volatility_score if isinstance(volatility_score, Decimal) else d(volatility_score),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "market-event-liquidity-cost-slippage-surface-v2",
        "depth_usage_watch_threshold": d("0.250000"),
        "depth_usage_block_threshold": d("0.600000"),
        "wide_spread_watch_threshold": d("0.030000"),
        "wide_spread_block_threshold": d("0.070000"),
        "high_cost_watch_threshold": d("0.025000"),
        "high_cost_block_threshold": d("0.080000"),
    }
    values.update(overrides)
    return module.MarketEventLiquidityCostSlippageSurfaceV2Config(**values)


def report(*events: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_event_liquidity_cost_slippage_surface_v2_report(
        events,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_empty_report_status_and_zero_decimal_rollups() -> None:
    module = api()

    liquidity_report = report()

    assert isinstance(
        liquidity_report,
        module.MarketEventLiquidityCostSlippageSurfaceV2Report,
    )
    assert is_dataclass(liquidity_report)
    assert liquidity_report.__dataclass_params__.frozen
    assert liquidity_report.generated_at == GENERATED_AT
    assert liquidity_report.config_version == "market-event-liquidity-cost-slippage-surface-v2"
    assert liquidity_report.report_status == "empty"
    assert liquidity_report.market_count == d("0.000000")
    assert liquidity_report.pass_count == d("0.000000")
    assert liquidity_report.watch_count == d("0.000000")
    assert liquidity_report.block_count == d("0.000000")
    assert liquidity_report.high_depth_usage_count == d("0.000000")
    assert liquidity_report.wide_spread_count == d("0.000000")
    assert liquidity_report.high_cost_count == d("0.000000")
    assert liquidity_report.max_total_cost_rate == d("0.000000")
    assert liquidity_report.rows == ()
    assert liquidity_report.reason_codes == ()
    assert liquidity_report.reason_code_counts == ()
    assert len(liquidity_report.derived_validation_digest) == 64
    assert set(liquidity_report.derived_validation_digest) <= set("0123456789abcdef")
    assert liquidity_report.paper_only is True
    assert liquidity_report.report_only is True
    assert liquidity_report.readonly is True

    payload = module.market_event_liquidity_cost_slippage_surface_v2_payload(liquidity_report)

    assert payload["market_count"] == "0.000000"
    assert payload["max_total_cost_rate"] == "0.000000"
    assert payload["report_status"] == "empty"
    assert payload["rows"] == []
    assert payload["reason_code_counts"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert not any(type(value) in (int, float) for value in _walk_values(payload))


def test_rows_cost_surface_rollups_statuses_and_sorting_are_deterministic() -> None:
    passed = event(
        "market-pass",
        "candidate-pass",
        "politics",
        notional_usdc="100.000000",
        orderbook_depth_usdc="1000.000000",
        bid_ask_spread="0.010000",
        taker_fee_rate="0.002000",
        volatility_score="0.020000",
    )
    watched = event(
        "market-watch",
        "candidate-watch",
        "crypto",
        notional_usdc="300.000000",
        orderbook_depth_usdc="1000.000000",
        bid_ask_spread="0.030000",
        taker_fee_rate="0.002000",
        volatility_score="0.050000",
    )
    blocked = event(
        "market-block",
        "candidate-block",
        "sports",
        notional_usdc="700.000000",
        orderbook_depth_usdc="1000.000000",
        bid_ask_spread="0.080000",
        taker_fee_rate="0.005000",
        volatility_score="0.080000",
    )

    liquidity_report = report(passed, blocked, watched)
    timezone_equivalent_report = report(
        watched,
        passed,
        blocked,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert tuple(row.market_id for row in liquidity_report.rows) == (
        "market-block",
        "market-watch",
        "market-pass",
    )
    assert tuple(row.market_id for row in timezone_equivalent_report.rows) == (
        "market-block",
        "market-watch",
        "market-pass",
    )
    assert liquidity_report.derived_validation_digest == (
        timezone_equivalent_report.derived_validation_digest
    )

    blocked_row, watched_row, passed_row = liquidity_report.rows
    assert blocked_row.depth_usage_ratio == d("0.700000")
    assert blocked_row.estimated_slippage_rate == d("0.056000")
    assert blocked_row.total_cost_rate == d("0.101000")
    assert blocked_row.status == "block"
    assert blocked_row.reason_codes == (
        "liquidity_depth_usage_block",
        "liquidity_high_cost_block",
        "liquidity_wide_spread_block",
    )

    assert watched_row.depth_usage_ratio == d("0.300000")
    assert watched_row.estimated_slippage_rate == d("0.015000")
    assert watched_row.total_cost_rate == d("0.032000")
    assert watched_row.status == "watch"
    assert watched_row.reason_codes == (
        "liquidity_depth_usage_watch",
        "liquidity_high_cost_watch",
        "liquidity_wide_spread_watch",
    )

    assert passed_row.depth_usage_ratio == d("0.100000")
    assert passed_row.estimated_slippage_rate == d("0.002000")
    assert passed_row.total_cost_rate == d("0.009000")
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("liquidity_cost_slippage_pass",)

    assert liquidity_report.report_status == "block"
    assert liquidity_report.market_count == d("3.000000")
    assert liquidity_report.pass_count == d("1.000000")
    assert liquidity_report.watch_count == d("1.000000")
    assert liquidity_report.block_count == d("1.000000")
    assert liquidity_report.high_depth_usage_count == d("2.000000")
    assert liquidity_report.wide_spread_count == d("2.000000")
    assert liquidity_report.high_cost_count == d("2.000000")
    assert liquidity_report.max_total_cost_rate == d("0.101000")
    assert tuple((item.reason_code, item.count, item.row_ratio) for item in liquidity_report.reason_code_counts) == (
        ("liquidity_cost_slippage_pass", d("1.000000"), d("0.333333")),
        ("liquidity_depth_usage_block", d("1.000000"), d("0.333333")),
        ("liquidity_depth_usage_watch", d("1.000000"), d("0.333333")),
        ("liquidity_high_cost_block", d("1.000000"), d("0.333333")),
        ("liquidity_high_cost_watch", d("1.000000"), d("0.333333")),
        ("liquidity_wide_spread_block", d("1.000000"), d("0.333333")),
        ("liquidity_wide_spread_watch", d("1.000000"), d("0.333333")),
    )


def test_validation_frozen_dataclasses_digest_guard_and_safe_payload_contract() -> None:
    module = api()
    input_row = event()
    liquidity_report = report(input_row)

    for value in (
        config(),
        input_row,
        liquidity_report.rows[0],
        liquidity_report.reason_code_counts[0],
        liquidity_report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        input_row.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="notional_usdc must be a Decimal"):
        module.MarketEventLiquidityCostSlippageSurfaceV2Input(
            market_id="market-bad",
            event_slug="candidate-bad",
            category="politics",
            notional_usdc="1.000000",
            orderbook_depth_usdc=d("10.000000"),
            bid_ask_spread=d("0.010000"),
            taker_fee_rate=d("0.001000"),
            volatility_score=d("0.010000"),
        )

    with pytest.raises(ValueError, match="notional_usdc must be exactly Decimal"):
        event(notional_usdc=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="readonly must be True"):
        event(readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(liquidity_report, max_total_cost_rate=d("0.999999"))

    payload = module.market_event_liquidity_cost_slippage_surface_v2_payload(liquidity_report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["notional_usdc"] == "100.000000"
    assert payload["rows"][0]["depth_usage_ratio"] == "0.100000"
    assert payload["rows"][0]["estimated_slippage_rate"] == "0.002000"
    assert payload["rows"][0]["total_cost_rate"] == "0.009000"
    assert not any(type(value) in (int, float) for value in _walk_values(payload))

    downgraded_flags = dict(payload)
    downgraded_flags["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        module.market_event_liquidity_cost_slippage_surface_v2_payload(downgraded_flags)

    unsafe = dict(payload)
    unsafe["wallet_address"] = "0x0000000000000000000000000000000000000000"
    with pytest.raises(ValueError, match="unsafe"):
        module.market_event_liquidity_cost_slippage_surface_v2_payload(unsafe)


def test_module_imports_are_phase1_readonly_report_only_and_paper_only() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_event_liquidity_cost_slippage_surface_v2.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {
        "ccxt",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports

    forbidden_terms = (
        "api_key",
        "private_key",
        "wallet_address",
        ".execute(",
        ".post(",
        ".put(",
        ".delete(",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
    )
    assert all(term not in source for term in forbidden_terms)


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)
