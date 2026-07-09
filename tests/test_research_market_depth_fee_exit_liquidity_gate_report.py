from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json

import pytest


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 14, 45, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_market_depth_fee_exit_liquidity_gate_report",
    )


def cfg(**overrides: object):
    values = {
        "config_version": "research-market-depth-fee-exit-liquidity-gate-report-test-v1",
        "watch_exit_liquidity_risk_score": d("0.350000"),
        "block_exit_liquidity_risk_score": d("0.700000"),
        "minimum_depth_coverage_ratio": d("1.000000"),
        "depth_coverage_watch_threshold": d("0.750000"),
        "depth_coverage_block_threshold": d("0.350000"),
        "fee_drag_watch_threshold": d("0.015000"),
        "fee_drag_block_threshold": d("0.040000"),
        "spread_watch_threshold": d("0.030000"),
        "spread_block_threshold": d("0.070000"),
        "slippage_pressure_watch_threshold": d("0.020000"),
        "slippage_pressure_block_threshold": d("0.060000"),
        "settlement_friction_watch_threshold": d("0.250000"),
        "settlement_friction_block_threshold": d("0.700000"),
        "estimated_exit_cost_watch_threshold": d("0.040000"),
        "estimated_exit_cost_block_threshold": d("0.100000"),
        "depth_weight": d("0.300000"),
        "fee_drag_weight": d("0.150000"),
        "spread_weight": d("0.150000"),
        "slippage_pressure_weight": d("0.250000"),
        "settlement_friction_weight": d("0.150000"),
    }
    values.update(overrides)
    return api().ResearchMarketDepthFeeExitLiquidityGateConfig(**values)


def sample(
    event_reference: str,
    *,
    depth_coverage_ratio: Decimal,
    fee_drag_rate: Decimal,
    bid_ask_spread_rate: Decimal,
    slippage_pressure_rate: Decimal,
    settlement_friction_score: Decimal,
    observed_at: datetime = OBSERVED_AT,
):
    return api().ResearchMarketDepthFeeExitLiquidityGateInput(
        event_reference=event_reference,
        observed_at=observed_at,
        depth_coverage_ratio=depth_coverage_ratio,
        fee_drag_rate=fee_drag_rate,
        bid_ask_spread_rate=bid_ask_spread_rate,
        slippage_pressure_rate=slippage_pressure_rate,
        settlement_friction_score=settlement_friction_score,
    )


def build_report(*inputs: object, config: object | None = None):
    return api().build_research_market_depth_fee_exit_liquidity_gate_report(
        inputs,
        config=config if config is not None else cfg(),
        generated_at=GENERATED_AT,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def test_exit_liquidity_gate_scores_cost_thresholds_and_sorts_rows() -> None:
    module = api()
    report = build_report(
        sample(
            "candidate-pass market-slug pass question https://example.invalid token=secret",
            depth_coverage_ratio=d("1.500000"),
            fee_drag_rate=d("0.005000"),
            bid_ask_spread_rate=d("0.010000"),
            slippage_pressure_rate=d("0.005000"),
            settlement_friction_score=d("0.100000"),
        ),
        sample(
            "candidate-block market-id block question dsn=postgres table=markets",
            depth_coverage_ratio=d("0.200000"),
            fee_drag_rate=d("0.050000"),
            bid_ask_spread_rate=d("0.080000"),
            slippage_pressure_rate=d("0.070000"),
            settlement_friction_score=d("0.800000"),
        ),
        sample(
            "candidate-watch market-slug watch question source text",
            depth_coverage_ratio=d("0.600000"),
            fee_drag_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.040000"),
            slippage_pressure_rate=d("0.025000"),
            settlement_friction_score=d("0.300000"),
        ),
    )

    assert type(report) is module.ResearchMarketDepthFeeExitLiquidityGateReport
    assert report.input_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.report_status == "block"
    assert report.highest_exit_liquidity_risk_score == d("0.940000")
    assert report.max_estimated_exit_cost_rate == d("0.160000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.gate_status for row in report.rows) == ("block", "watch", "pass")

    assert block_row.estimated_exit_cost_rate == d("0.160000")
    assert block_row.depth_risk_score == d("0.240000")
    assert block_row.fee_drag_risk_score == d("0.150000")
    assert block_row.spread_risk_score == d("0.150000")
    assert block_row.slippage_pressure_risk_score == d("0.250000")
    assert block_row.settlement_friction_risk_score == d("0.150000")
    assert block_row.exit_liquidity_risk_score == d("0.940000")
    assert block_row.reason_codes == (
        "depth_coverage_block",
        "estimated_exit_cost_block",
        "exit_liquidity_score_block",
        "fee_drag_block",
        "settlement_friction_block",
        "slippage_pressure_block",
        "spread_block",
    )

    assert watch_row.estimated_exit_cost_rate == d("0.065000")
    assert watch_row.exit_liquidity_risk_score == d("0.449167")
    assert watch_row.reason_codes == (
        "depth_coverage_watch",
        "estimated_exit_cost_watch",
        "exit_liquidity_score_watch",
        "fee_drag_watch",
        "settlement_friction_watch",
        "slippage_pressure_watch",
        "spread_watch",
    )

    assert pass_row.estimated_exit_cost_rate == d("0.015000")
    assert pass_row.exit_liquidity_risk_score == d("0.082441")
    assert pass_row.reason_codes == ("exit_liquidity_gate_pass",)
    assert len({row.event_digest for row in report.rows}) == 3


def test_public_payload_is_json_ready_digest_bound_and_safe() -> None:
    module = api()
    raw_reference = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid dsn=postgres table=markets token=secret "
        "wallet order trade"
    )
    report = build_report(
        sample(
            raw_reference,
            depth_coverage_ratio=d("0.200000"),
            fee_drag_rate=d("0.050000"),
            bid_ask_spread_rate=d("0.080000"),
            slippage_pressure_rate=d("0.070000"),
            settlement_friction_score=d("0.800000"),
        ),
    )
    same_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            depth_coverage_ratio=d("0.200000"),
            fee_drag_rate=d("0.050000"),
            bid_ask_spread_rate=d("0.080000"),
            slippage_pressure_rate=d("0.070000"),
            settlement_friction_score=d("0.800000"),
        ),
    )

    payload = module.research_market_depth_fee_exit_liquidity_gate_report_payload(report)
    encoded_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-08T15:00:00+00:00"
    assert payload["rows"][0]["event_digest"] == report.rows[0].event_digest
    assert payload["rows"][0]["estimated_exit_cost_rate"] == "0.160000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "candidate-alpha",
        "market-id",
        "market-slug",
        "raw question text",
        "https://",
        "dsn=",
        "table=markets",
        "token=secret",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden.lower() not in encoded_payload.lower()

    changed_report = build_report(
        sample(
            raw_reference,
            depth_coverage_ratio=d("0.210000"),
            fee_drag_rate=d("0.050000"),
            bid_ask_spread_rate=d("0.080000"),
            slippage_pressure_rate=d("0.070000"),
            settlement_friction_score=d("0.800000"),
        ),
    )
    assert changed_report.derived_validation_digest != report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_estimated_exit_cost_rate=d("0.999999"))

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "leaked-market"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_depth_fee_exit_liquidity_gate_report_payload(unsafe_payload)


def test_empty_input_blocks_for_manual_review_without_row_leakage() -> None:
    report = build_report()

    assert report.input_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.highest_exit_liquidity_risk_score == d("0.000000")
    assert report.max_estimated_exit_cost_rate == d("0.000000")
    assert report.report_status == "block"
    assert report.reason_codes == ("missing_depth_fee_exit_liquidity_inputs",)
    assert report.rows == ()


def test_custom_config_validation_and_frozen_decimal_only_contracts() -> None:
    module = api()
    custom_config = cfg(block_exit_liquidity_risk_score=d("0.440000"))
    report = build_report(
        sample(
            "candidate-watch custom thresholds",
            depth_coverage_ratio=d("0.600000"),
            fee_drag_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.040000"),
            slippage_pressure_rate=d("0.025000"),
            settlement_friction_score=d("0.300000"),
        ),
        config=custom_config,
    )

    assert report.rows[0].exit_liquidity_risk_score == d("0.449167")
    assert report.rows[0].gate_status == "block"
    assert "exit_liquidity_score_block" in report.rows[0].reason_codes

    for contract in (
        module.ResearchMarketDepthFeeExitLiquidityGateConfig,
        module.ResearchMarketDepthFeeExitLiquidityGateInput,
        module.ResearchMarketDepthFeeExitLiquidityGateReportRow,
        module.ResearchMarketDepthFeeExitLiquidityGateReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(custom_config, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample(
            "candidate-decimal-subclass",
            depth_coverage_ratio=_DecimalSubclass("1.000000"),
            fee_drag_rate=d("0.001000"),
            bid_ask_spread_rate=d("0.001000"),
            slippage_pressure_rate=d("0.001000"),
            settlement_friction_score=d("0.001000"),
        )
    with pytest.raises(ValueError, match="watch_exit_liquidity_risk_score"):
        cfg(
            watch_exit_liquidity_risk_score=d("0.800000"),
            block_exit_liquidity_risk_score=d("0.700000"),
        )
    with pytest.raises(ValueError, match="weights must sum"):
        cfg(depth_weight=d("0.310000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_source_excludes_network_database_wallet_and_action_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()

    assert "research_market_depth_fee_exit_liquidity_gate_report_payload" in module.__all__
    for banned in (
        "api_key",
        "private_key",
        "wallet",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "recommendation",
    ):
        assert banned not in source
