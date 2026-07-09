from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    research_market_liquidity_edge_queue_pressure_report as module,
)
from polymarket_alpha_lab.research_market_liquidity_edge_queue_pressure_report import (
    ResearchMarketLiquidityEdgeQueuePressureConfig,
    ResearchMarketLiquidityEdgeQueuePressureInput,
    build_research_market_liquidity_edge_queue_pressure_report,
    research_market_liquidity_edge_queue_pressure_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketLiquidityEdgeQueuePressureConfig:
    values = {
        "config_version": "research-market-liquidity-edge-queue-pressure-report-v0",
        "max_pass_queue_pressure": d("0.300000"),
        "max_watch_queue_pressure": d("0.600000"),
        "min_pass_liquidity_depth_ratio": d("1.500000"),
        "min_watch_liquidity_depth_ratio": d("0.750000"),
        "max_pass_bid_ask_spread": d("0.015000"),
        "max_watch_bid_ask_spread": d("0.040000"),
        "max_block_bid_ask_spread": d("0.080000"),
        "max_pass_fee_drag": d("0.010000"),
        "max_watch_fee_drag": d("0.025000"),
        "max_block_fee_drag": d("0.040000"),
        "max_pass_slippage_risk": d("0.020000"),
        "max_watch_slippage_risk": d("0.050000"),
        "max_block_slippage_risk": d("0.080000"),
        "max_pass_settlement_friction": d("0.015000"),
        "max_watch_settlement_friction": d("0.040000"),
        "max_block_settlement_friction": d("0.060000"),
        "min_pass_edge_stability": d("0.800000"),
        "min_watch_edge_stability": d("0.500000"),
        "liquidity_depth_weight": d("0.250000"),
        "spread_weight": d("0.200000"),
        "fee_drag_weight": d("0.150000"),
        "slippage_risk_weight": d("0.200000"),
        "settlement_friction_weight": d("0.100000"),
        "edge_stability_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityEdgeQueuePressureConfig(**values)


def item(**overrides: object) -> ResearchMarketLiquidityEdgeQueuePressureInput:
    values = {
        "queue_bucket": "alpha_event",
        "liquidity_depth_ratio": d("2.000000"),
        "bid_ask_spread": d("0.004000"),
        "fee_drag": d("0.003000"),
        "slippage_risk": d("0.006000"),
        "settlement_friction": d("0.004000"),
        "edge_stability": d("0.900000"),
        "reason_codes": ("sanitized_probability_event",),
    }
    values.update(overrides)
    return ResearchMarketLiquidityEdgeQueuePressureInput(**values)


def build_report(*items: object, cfg: object | None = None):
    return build_research_market_liquidity_edge_queue_pressure_report(
        items or (item(),),
        cfg or config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_float_values(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_float_values(nested)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "execution",
        "sizing",
        "recommendation",
        "auth",
        "network",
        "database",
        "persist",
        "live",
    )
    if isinstance(value, dict):
        for key, nested in value.items():
            assert_public_payload_has_no_forbidden_surface(key)
            assert_public_payload_has_no_forbidden_surface(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_public_payload_has_no_forbidden_surface(nested)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_readonly_report_contract() -> None:
    assert module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_EDGE_QUEUE_PRESSURE_CONFIG_VERSION == (
        "research-market-liquidity-edge-queue-pressure-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_EDGE_QUEUE_PRESSURE_CONFIG_VERSION",
        "ResearchMarketLiquidityEdgeQueuePressureConfig",
        "ResearchMarketLiquidityEdgeQueuePressureInput",
        "ResearchMarketLiquidityEdgeQueuePressureRow",
        "ResearchMarketLiquidityEdgeQueuePressureReport",
        "build_research_market_liquidity_edge_queue_pressure_report",
        "research_market_liquidity_edge_queue_pressure_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchMarketLiquidityEdgeQueuePressureConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_and_block_rows_from_liquidity_queue_pressure() -> None:
    report = build_report(
        item(queue_bucket="alpha_event"),
        item(
            queue_bucket="beta_event",
            liquidity_depth_ratio=d("1.000000"),
            bid_ask_spread=d("0.030000"),
            fee_drag=d("0.015000"),
            slippage_risk=d("0.035000"),
            settlement_friction=d("0.025000"),
            edge_stability=d("0.650000"),
        ),
        item(
            queue_bucket="gamma_event",
            liquidity_depth_ratio=d("0.300000"),
            bid_ask_spread=d("0.100000"),
            fee_drag=d("0.050000"),
            slippage_risk=d("0.110000"),
            settlement_friction=d("0.080000"),
            edge_stability=d("0.200000"),
        ),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_queue_pressure_score == d("0.453889")
    assert report.max_queue_pressure_score == d("0.930000")
    assert report.reason_codes == (
        "queue_pressure_report_block_rows",
        "queue_pressure_report_watch_rows",
    )

    assert tuple(row.queue_bucket for row in report.rows) == (
        "alpha_event",
        "beta_event",
        "gamma_event",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert tuple(row.queue_pressure_score for row in report.rows) == (
        d("0.052917"),
        d("0.378750"),
        d("0.930000"),
    )
    assert report.rows[0].reason_codes == (
        "sanitized_probability_event",
        "queue_pressure_pass",
    )
    assert report.rows[1].reason_codes == (
        "sanitized_probability_event",
        "liquidity_depth_pressure_watch",
        "spread_pressure_watch",
        "fee_drag_pressure_watch",
        "slippage_risk_pressure_watch",
        "settlement_friction_pressure_watch",
        "edge_stability_pressure_watch",
        "queue_pressure_watch",
    )
    assert report.rows[2].reason_codes == (
        "sanitized_probability_event",
        "liquidity_depth_pressure_block",
        "spread_pressure_block",
        "fee_drag_pressure_block",
        "slippage_risk_pressure_block",
        "settlement_friction_pressure_block",
        "edge_stability_pressure_block",
        "queue_pressure_block",
    )


def test_queue_pressure_thresholds_drive_report_statuses() -> None:
    assert build_report(item()).status == "pass"
    assert build_report(
        item(
            liquidity_depth_ratio=d("1.000000"),
            bid_ask_spread=d("0.030000"),
            fee_drag=d("0.015000"),
            slippage_risk=d("0.035000"),
            settlement_friction=d("0.025000"),
            edge_stability=d("0.650000"),
        ),
    ).status == "watch"
    assert build_report(
        item(
            liquidity_depth_ratio=d("0.300000"),
            bid_ask_spread=d("0.100000"),
            fee_drag=d("0.050000"),
            slippage_risk=d("0.110000"),
            settlement_friction=d("0.080000"),
            edge_stability=d("0.200000"),
        ),
    ).status == "block"

    custom_cfg = config(max_pass_queue_pressure=d("0.400000"))
    assert build_report(
        item(
            liquidity_depth_ratio=d("1.000000"),
            bid_ask_spread=d("0.030000"),
            fee_drag=d("0.015000"),
            slippage_risk=d("0.035000"),
            settlement_friction=d("0.025000"),
            edge_stability=d("0.650000"),
        ),
        cfg=custom_cfg,
    ).status == "pass"


def test_payload_digest_is_deterministic_decimal_stringed_and_sanitized() -> None:
    left = item(queue_bucket="alpha_event")
    right = item(
        queue_bucket="beta_event",
        liquidity_depth_ratio=d("1.000000"),
        bid_ask_spread=d("0.030000"),
        fee_drag=d("0.015000"),
        slippage_risk=d("0.035000"),
        settlement_friction=d("0.025000"),
        edge_stability=d("0.650000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = research_market_liquidity_edge_queue_pressure_report_payload(report_a)

    assert report_a.public_payload == report_b.public_payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert len(report_a.derived_validation_digest) == 64
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["queue_bucket_digest"].startswith("sha256:")
    assert payload["rows"][0]["queue_pressure_score"] == "0.052917"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert "alpha_event" not in encoded
    assert "beta_event" not in encoded


def test_public_payload_rejects_unsafe_surfaces_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="unsafe public payload"):
        item(queue_bucket="raw_market_id_123")
    with pytest.raises(ValueError, match="unsafe public payload"):
        item(reason_codes=("source_url",))
    with pytest.raises(ValueError, match="unsafe public payload"):
        item(reason_codes=("raw_text_excerpt",))
    with pytest.raises(ValueError, match="unsafe public payload"):
        item(queue_bucket="db_primary")

    report = build_report(item())
    payload = research_market_liquidity_edge_queue_pressure_report_payload(report)

    unsafe_payload = dict(payload)
    unsafe_payload["wallet_address"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_market_liquidity_edge_queue_pressure_report_payload(unsafe_payload)

    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_liquidity_edge_queue_pressure_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="public_payload"):
        replace(report, public_payload={**payload, "status": "watch"})


def test_frozen_decimal_flags_and_custom_config_validation() -> None:
    cfg = config()
    observation = item()
    report = build_report(observation)
    row = report.rows[0]

    for value in (cfg, observation, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="fee_drag must be exactly Decimal"):
        replace(observation, fee_drag=0.003)
    with pytest.raises(ValueError, match="bid_ask_spread must be exactly Decimal"):
        replace(observation, bid_ask_spread=_DecimalSubclass("0.004000"))
    with pytest.raises(ValueError, match="settlement_friction must use six decimal"):
        replace(observation, settlement_friction=d("0.0040001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation, paper_only=False)
    with pytest.raises(ValueError, match="max_pass_queue_pressure"):
        config(max_pass_queue_pressure=d("0.700000"))
    with pytest.raises(ValueError, match="min_pass_liquidity_depth_ratio"):
        config(min_pass_liquidity_depth_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(edge_stability_weight=d("0.050000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)
