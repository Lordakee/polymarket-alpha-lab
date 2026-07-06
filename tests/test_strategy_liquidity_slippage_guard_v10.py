from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_liquidity_slippage_guard_v10 import (
    DEFAULT_STRATEGY_LIQUIDITY_SLIPPAGE_GUARD_V10_CONFIG_VERSION,
    StrategyLiquiditySlippageGuardV10Config,
    StrategyLiquiditySlippageGuardV10Input,
    StrategyLiquiditySlippageGuardV10Result,
    build_strategy_liquidity_slippage_guard_v10,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def guard_input(
    *,
    market_slug: str = "event-alpha",
    side: str = "yes",
    order_direction: str = "buy",
    target_position_shares: Decimal = d("150.000000"),
    current_position_shares: Decimal = d("50.000000"),
    best_bid_price: Decimal = d("0.550000"),
    best_ask_price: Decimal = d("0.560000"),
    top_bid_size: Decimal = d("80.000000"),
    top_ask_size: Decimal = d("120.000000"),
    total_bid_depth: Decimal = d("180.000000"),
    total_ask_depth: Decimal = d("200.000000"),
    expected_fee_rate: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyLiquiditySlippageGuardV10Input:
    return StrategyLiquiditySlippageGuardV10Input(
        market_slug=market_slug,
        side=side,
        order_direction=order_direction,
        target_position_shares=target_position_shares,
        current_position_shares=current_position_shares,
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        top_bid_size=top_bid_size,
        top_ask_size=top_ask_size,
        total_bid_depth=total_bid_depth,
        total_ask_depth=total_ask_depth,
        expected_fee_rate=expected_fee_rate,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    max_acceptable_slippage_per_share: Decimal = d("0.008000"),
    max_spread: Decimal = d("0.025000"),
    min_top_of_book_depth_ratio: Decimal = d("0.500000"),
    min_total_depth_ratio: Decimal = d("1.000000"),
    max_expected_fee_rate: Decimal = d("0.010000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyLiquiditySlippageGuardV10Config:
    return StrategyLiquiditySlippageGuardV10Config(
        config_version=DEFAULT_STRATEGY_LIQUIDITY_SLIPPAGE_GUARD_V10_CONFIG_VERSION,
        max_acceptable_slippage_per_share=max_acceptable_slippage_per_share,
        max_spread=max_spread,
        min_top_of_book_depth_ratio=min_top_of_book_depth_ratio,
        min_total_depth_ratio=min_total_depth_ratio,
        max_expected_fee_rate=max_expected_fee_rate,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_result(
    value: StrategyLiquiditySlippageGuardV10Input | None = None,
    *,
    guard_config: StrategyLiquiditySlippageGuardV10Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyLiquiditySlippageGuardV10Result:
    return build_strategy_liquidity_slippage_guard_v10(
        value or guard_input(),
        config=guard_config or config(),
        generated_at=generated_at,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def payload_value(
    result: StrategyLiquiditySlippageGuardV10Result,
    key: str,
) -> str | bool | Decimal:
    return dict(result.payload)[key]


def test_guard_passes_when_spread_depth_slippage_and_fees_are_within_limits():
    result = build_result(
        guard_input(
            market_slug="event-pass",
            reason_codes=("ranked_candidate",),
        ),
    )

    assert type(result) is StrategyLiquiditySlippageGuardV10Result
    assert result.generated_at == GENERATED_AT
    assert result.config_version == DEFAULT_STRATEGY_LIQUIDITY_SLIPPAGE_GUARD_V10_CONFIG_VERSION
    assert result.market_slug == "event-pass"
    assert result.side == "yes"
    assert result.order_direction == "buy"
    assert result.target_order_size == d("100.000000")
    assert result.max_order_size == d("100.000000")
    assert result.execution_price == d("0.560000")
    assert result.mid_price == d("0.555000")
    assert result.spread == d("0.010000")
    assert result.slippage_per_share == d("0.005000")
    assert result.expected_fee_amount == d("0.280000")
    assert result.guard_status == "pass"
    assert result.reason_codes == (
        "liquidity_slippage_guard_v10_passed",
        "ranked_candidate",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert payload_value(result, "decision_support_only") is True
    assert payload_value(result, "target_order_size") == d("100.000000")
    assert payload_value(result, "max_order_size") == d("100.000000")


def test_guard_watches_and_clips_when_total_depth_cannot_cover_target_order():
    result = build_result(
        guard_input(
            market_slug="event-shallow",
            top_ask_size=d("20.000000"),
            total_ask_depth=d("60.000000"),
            reason_codes=("source_depth_partial",),
        ),
    )

    assert result.guard_status == "watch"
    assert result.max_order_size == d("60.000000")
    assert result.available_depth == d("60.000000")
    assert result.top_of_book_depth == d("20.000000")
    assert result.total_depth_ratio == d("0.600000")
    assert result.top_of_book_depth_ratio == d("0.200000")
    assert result.expected_fee_amount == d("0.168000")
    assert result.reason_codes == (
        "below_min_top_of_book_depth_ratio",
        "below_min_total_depth_ratio",
        "order_size_clipped_to_depth",
        "source_depth_partial",
    )


def test_guard_blocks_unacceptable_slippage_fee_rate_and_empty_depth():
    high_slippage = build_result(
        guard_input(
            market_slug="event-slippage",
            best_bid_price=d("0.500000"),
            best_ask_price=d("0.530000"),
            top_ask_size=d("150.000000"),
            total_ask_depth=d("200.000000"),
        ),
    )
    high_fee = build_result(
        guard_input(
            market_slug="event-fee",
            expected_fee_rate=d("0.020000"),
        ),
    )
    no_depth = build_result(
        guard_input(
            market_slug="event-no-depth",
            top_ask_size=ZERO,
            total_ask_depth=ZERO,
        ),
    )

    assert high_slippage.guard_status == "blocked"
    assert high_slippage.max_order_size == d("100.000000")
    assert high_slippage.reason_codes == (
        "slippage_above_acceptable_limit",
        "spread_above_limit",
    )

    assert high_fee.guard_status == "blocked"
    assert high_fee.reason_codes == ("expected_fee_rate_above_limit",)

    assert no_depth.guard_status == "blocked"
    assert no_depth.max_order_size == ZERO
    assert no_depth.reason_codes == (
        "below_min_top_of_book_depth_ratio",
        "below_min_total_depth_ratio",
        "no_available_depth",
        "order_size_clipped_to_depth",
    )


def test_guard_uses_bid_depth_for_sell_orders_and_passes_when_target_is_met():
    sell_result = build_result(
        guard_input(
            market_slug="event-sell",
            order_direction="sell",
            target_position_shares=d("40.000000"),
            current_position_shares=d("100.000000"),
            top_bid_size=d("70.000000"),
            total_bid_depth=d("90.000000"),
            top_ask_size=d("5.000000"),
            total_ask_depth=d("5.000000"),
        ),
    )
    target_met = build_result(
        guard_input(
            market_slug="event-target-met",
            target_position_shares=d("50.000000"),
            current_position_shares=d("50.000000"),
            top_ask_size=ZERO,
            total_ask_depth=ZERO,
        ),
    )

    assert sell_result.target_order_size == d("60.000000")
    assert sell_result.top_of_book_depth == d("70.000000")
    assert sell_result.available_depth == d("90.000000")
    assert sell_result.max_order_size == d("60.000000")
    assert sell_result.execution_price == d("0.550000")
    assert sell_result.guard_status == "pass"

    assert target_met.target_order_size == ZERO
    assert target_met.max_order_size == ZERO
    assert target_met.guard_status == "pass"
    assert target_met.reason_codes == ("target_position_already_met",)
    assert payload_value(target_met, "decision_support_only") is True


def test_guard_quantizes_decimals_and_normalizes_generated_at_to_utc():
    eastern = timezone(timedelta(hours=-4))

    result = build_strategy_liquidity_slippage_guard_v10(
        guard_input(
            target_position_shares=d("3.0000004"),
            current_position_shares=d("1.0000004"),
            best_bid_price=d("0.5200004"),
            best_ask_price=d("0.5260004"),
            top_ask_size=d("2.0000004"),
            total_ask_depth=d("3.0000004"),
            expected_fee_rate=d("0.0040004"),
        ),
        config=config(
            max_acceptable_slippage_per_share=d("0.0040004"),
            max_spread=d("0.0100004"),
            min_top_of_book_depth_ratio=d("0.5000004"),
            min_total_depth_ratio=d("1.0000004"),
            max_expected_fee_rate=d("0.0100004"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 30, tzinfo=eastern),
    )

    assert result.generated_at == GENERATED_AT
    assert result.target_order_size == d("2.000000")
    assert result.max_order_size == d("2.000000")
    assert result.mid_price == d("0.523000")
    assert result.spread == d("0.006000")
    assert result.slippage_per_share == d("0.003000")
    assert result.expected_fee_amount == d("0.004208")
    assert result.total_depth_ratio == d("1.500000")


def test_guard_rejects_non_decimal_values_inconsistent_orderbooks_and_bad_flags():
    with pytest.raises(ValueError, match="best_ask_price"):
        replace(guard_input(), best_ask_price=0.56)
    with pytest.raises(ValueError, match="expected_fee_rate"):
        replace(guard_input(), expected_fee_rate=d("1.000001"))
    with pytest.raises(ValueError, match="best_ask_price"):
        replace(guard_input(), best_bid_price=d("0.570000"), best_ask_price=d("0.560000"))
    with pytest.raises(ValueError, match="total_ask_depth"):
        replace(guard_input(), top_ask_size=d("10.000000"), total_ask_depth=d("9.999999"))
    with pytest.raises(ValueError, match="max_spread"):
        config(max_spread=0.025)
    with pytest.raises(ValueError, match="config paper_only"):
        build_result(guard_config=config(paper_only=False))
    with pytest.raises(ValueError, match="input readonly"):
        build_result(guard_input(readonly=False))


def test_guard_dataclasses_are_frozen_and_public_build_rejects_bad_types():
    value = guard_input()
    guard_config = config()
    result = build_result(value, guard_config=guard_config)
    rebuilt = StrategyLiquiditySlippageGuardV10Result(**field_values(result))

    assert rebuilt == result
    with pytest.raises(FrozenInstanceError):
        value.market_slug = "other"
    with pytest.raises(FrozenInstanceError):
        guard_config.max_spread = d("0.020000")
    with pytest.raises(FrozenInstanceError):
        result.guard_status = "blocked"
    with pytest.raises(ValueError, match="input"):
        build_strategy_liquidity_slippage_guard_v10(
            object(),
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_strategy_liquidity_slippage_guard_v10(
            value,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_strategy_liquidity_slippage_guard_v10(
            value,
            config=guard_config,
            generated_at="2026-07-06T12:30:00Z",
        )
