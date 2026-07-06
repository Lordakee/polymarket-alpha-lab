"""Paper/report-only liquidity and slippage guard for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import TypeAlias


DEFAULT_STRATEGY_LIQUIDITY_SLIPPAGE_GUARD_V10_CONFIG_VERSION = (
    "strategy-liquidity-slippage-guard-v10"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
DECIMAL_CONTEXT = Context(prec=64)

SIDES = ("yes", "no")
ORDER_DIRECTIONS = ("buy", "sell")
GUARD_STATUSES = ("pass", "watch", "blocked")

PASS_REASON = "liquidity_slippage_guard_v10_passed"
TARGET_MET_REASON = "target_position_already_met"
LOW_TOP_DEPTH_REASON = "below_min_top_of_book_depth_ratio"
LOW_TOTAL_DEPTH_REASON = "below_min_total_depth_ratio"
NO_DEPTH_REASON = "no_available_depth"
CLIPPED_REASON = "order_size_clipped_to_depth"
SLIPPAGE_REASON = "slippage_above_acceptable_limit"
SPREAD_REASON = "spread_above_limit"
FEE_RATE_REASON = "expected_fee_rate_above_limit"

PayloadValue: TypeAlias = str | bool | Decimal
Payload: TypeAlias = tuple[tuple[str, PayloadValue], ...]


@dataclass(frozen=True)
class StrategyLiquiditySlippageGuardV10Config:
    config_version: str = DEFAULT_STRATEGY_LIQUIDITY_SLIPPAGE_GUARD_V10_CONFIG_VERSION
    max_acceptable_slippage_per_share: Decimal = Decimal("0.008000")
    max_spread: Decimal = Decimal("0.025000")
    min_top_of_book_depth_ratio: Decimal = Decimal("0.500000")
    min_total_depth_ratio: Decimal = Decimal("1.000000")
    max_expected_fee_rate: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_acceptable_slippage_per_share",
            _probability(
                "max_acceptable_slippage_per_share",
                self.max_acceptable_slippage_per_share,
            ),
        )
        object.__setattr__(self, "max_spread", _probability("max_spread", self.max_spread))
        object.__setattr__(
            self,
            "min_top_of_book_depth_ratio",
            _nonnegative_decimal(
                "min_top_of_book_depth_ratio",
                self.min_top_of_book_depth_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_total_depth_ratio",
            _nonnegative_decimal("min_total_depth_ratio", self.min_total_depth_ratio),
        )
        object.__setattr__(
            self,
            "max_expected_fee_rate",
            _probability("max_expected_fee_rate", self.max_expected_fee_rate),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyLiquiditySlippageGuardV10Input:
    market_slug: str
    side: str
    order_direction: str
    target_position_shares: Decimal
    current_position_shares: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    top_bid_size: Decimal
    top_ask_size: Decimal
    total_bid_depth: Decimal
    total_ask_depth: Decimal
    expected_fee_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("side", self.side, SIDES)
        _require_member("order_direction", self.order_direction, ORDER_DIRECTIONS)
        for field_name in (
            "target_position_shares",
            "current_position_shares",
            "top_bid_size",
            "top_ask_size",
            "total_bid_depth",
            "total_ask_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("best_bid_price", "best_ask_price", "expected_fee_rate"):
            object.__setattr__(
                self,
                field_name,
                _probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_input_orderbook(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyLiquiditySlippageGuardV10Result:
    generated_at: datetime
    config_version: str
    market_slug: str
    side: str
    order_direction: str
    target_order_size: Decimal
    max_order_size: Decimal
    top_of_book_depth: Decimal
    available_depth: Decimal
    top_of_book_depth_ratio: Decimal
    total_depth_ratio: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    execution_price: Decimal
    mid_price: Decimal
    spread: Decimal
    slippage_per_share: Decimal
    expected_fee_rate: Decimal
    expected_fee_amount: Decimal
    guard_status: str
    reason_codes: tuple[str, ...]
    payload: Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("side", self.side, SIDES)
        _require_member("order_direction", self.order_direction, ORDER_DIRECTIONS)
        for field_name in (
            "target_order_size",
            "max_order_size",
            "top_of_book_depth",
            "available_depth",
            "top_of_book_depth_ratio",
            "total_depth_ratio",
            "expected_fee_amount",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "execution_price",
            "mid_price",
            "spread",
            "slippage_per_share",
            "expected_fee_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(field_name, getattr(self, field_name)),
            )
        _require_member("guard_status", self.guard_status, GUARD_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload(self.payload))
        _validate_result_shape(self)
        _require_hard_flags("result", self)


def build_strategy_liquidity_slippage_guard_v10(
    value: StrategyLiquiditySlippageGuardV10Input,
    *,
    config: StrategyLiquiditySlippageGuardV10Config,
    generated_at: datetime,
) -> StrategyLiquiditySlippageGuardV10Result:
    if type(value) is not StrategyLiquiditySlippageGuardV10Input:
        raise ValueError("input must be a StrategyLiquiditySlippageGuardV10Input")
    if type(config) is not StrategyLiquiditySlippageGuardV10Config:
        raise ValueError("config must be a StrategyLiquiditySlippageGuardV10Config")
    _require_hard_flags("input", value)
    _require_hard_flags("config", config)

    target_order_size = _target_order_size(value)
    top_of_book_depth, available_depth = _side_depth(value)
    max_order_size = _min_decimal(target_order_size, available_depth)
    execution_price = value.best_ask_price if value.order_direction == "buy" else value.best_bid_price
    spread = _subtract_decimal(value.best_ask_price, value.best_bid_price)
    mid_price = _divide_decimal(_add_decimal(value.best_bid_price, value.best_ask_price), TWO)
    slippage_per_share = _absolute_decimal(_subtract_decimal(execution_price, mid_price))
    top_depth_ratio = _depth_ratio(top_of_book_depth, target_order_size)
    total_depth_ratio = _depth_ratio(available_depth, target_order_size)
    expected_fee_amount = _expected_fee_amount(
        order_size=max_order_size,
        execution_price=execution_price,
        expected_fee_rate=value.expected_fee_rate,
    )
    reason_codes = _reason_codes_for(
        source_reason_codes=value.reason_codes,
        target_order_size=target_order_size,
        max_order_size=max_order_size,
        top_depth_ratio=top_depth_ratio,
        total_depth_ratio=total_depth_ratio,
        available_depth=available_depth,
        spread=spread,
        slippage_per_share=slippage_per_share,
        expected_fee_rate=value.expected_fee_rate,
        config=config,
    )
    guard_status = _guard_status(
        target_order_size=target_order_size,
        available_depth=available_depth,
        slippage_per_share=slippage_per_share,
        expected_fee_rate=value.expected_fee_rate,
        reason_codes=reason_codes,
        config=config,
    )
    payload = _payload_for(
        value=value,
        guard_status=guard_status,
        target_order_size=target_order_size,
        max_order_size=max_order_size,
        top_of_book_depth=top_of_book_depth,
        available_depth=available_depth,
        top_of_book_depth_ratio=top_depth_ratio,
        total_depth_ratio=total_depth_ratio,
        execution_price=execution_price,
        mid_price=mid_price,
        spread=spread,
        slippage_per_share=slippage_per_share,
        expected_fee_amount=expected_fee_amount,
    )

    return StrategyLiquiditySlippageGuardV10Result(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        market_slug=value.market_slug,
        side=value.side,
        order_direction=value.order_direction,
        target_order_size=target_order_size,
        max_order_size=max_order_size,
        top_of_book_depth=top_of_book_depth,
        available_depth=available_depth,
        top_of_book_depth_ratio=top_depth_ratio,
        total_depth_ratio=total_depth_ratio,
        best_bid_price=value.best_bid_price,
        best_ask_price=value.best_ask_price,
        execution_price=execution_price,
        mid_price=mid_price,
        spread=spread,
        slippage_per_share=slippage_per_share,
        expected_fee_rate=value.expected_fee_rate,
        expected_fee_amount=expected_fee_amount,
        guard_status=guard_status,
        reason_codes=reason_codes,
        payload=payload,
    )


def _target_order_size(value: StrategyLiquiditySlippageGuardV10Input) -> Decimal:
    if value.order_direction == "buy":
        raw_size = _subtract_decimal(
            value.target_position_shares,
            value.current_position_shares,
        )
    else:
        raw_size = _subtract_decimal(
            value.current_position_shares,
            value.target_position_shares,
        )
    if raw_size <= ZERO:
        return _quantize(ZERO)
    return raw_size


def _side_depth(value: StrategyLiquiditySlippageGuardV10Input) -> tuple[Decimal, Decimal]:
    if value.order_direction == "buy":
        return value.top_ask_size, value.total_ask_depth
    return value.top_bid_size, value.total_bid_depth


def _depth_ratio(depth: Decimal, target_order_size: Decimal) -> Decimal:
    if target_order_size <= ZERO:
        return _quantize(ONE)
    return _divide_decimal(depth, target_order_size)


def _expected_fee_amount(
    *,
    order_size: Decimal,
    execution_price: Decimal,
    expected_fee_rate: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(order_size * execution_price * expected_fee_rate)


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    target_order_size: Decimal,
    max_order_size: Decimal,
    top_depth_ratio: Decimal,
    total_depth_ratio: Decimal,
    available_depth: Decimal,
    spread: Decimal,
    slippage_per_share: Decimal,
    expected_fee_rate: Decimal,
    config: StrategyLiquiditySlippageGuardV10Config,
) -> tuple[str, ...]:
    if target_order_size <= ZERO:
        return _dedupe((TARGET_MET_REASON, *source_reason_codes))

    reason_codes: list[str] = []
    if top_depth_ratio < config.min_top_of_book_depth_ratio:
        reason_codes.append(LOW_TOP_DEPTH_REASON)
    if total_depth_ratio < config.min_total_depth_ratio:
        reason_codes.append(LOW_TOTAL_DEPTH_REASON)
    if available_depth <= ZERO:
        reason_codes.append(NO_DEPTH_REASON)
    if max_order_size < target_order_size:
        reason_codes.append(CLIPPED_REASON)
    if slippage_per_share > config.max_acceptable_slippage_per_share:
        reason_codes.append(SLIPPAGE_REASON)
    if spread > config.max_spread:
        reason_codes.append(SPREAD_REASON)
    if expected_fee_rate > config.max_expected_fee_rate:
        reason_codes.append(FEE_RATE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _dedupe((*reason_codes, *source_reason_codes))


def _guard_status(
    *,
    target_order_size: Decimal,
    available_depth: Decimal,
    slippage_per_share: Decimal,
    expected_fee_rate: Decimal,
    reason_codes: tuple[str, ...],
    config: StrategyLiquiditySlippageGuardV10Config,
) -> str:
    if target_order_size <= ZERO:
        return "pass"
    if available_depth <= ZERO:
        return "blocked"
    if slippage_per_share > config.max_acceptable_slippage_per_share:
        return "blocked"
    if expected_fee_rate > config.max_expected_fee_rate:
        return "blocked"
    watch_reasons = (
        LOW_TOP_DEPTH_REASON,
        LOW_TOTAL_DEPTH_REASON,
        CLIPPED_REASON,
        SPREAD_REASON,
    )
    if any(reason_code in watch_reasons for reason_code in reason_codes):
        return "watch"
    return "pass"


def _payload_for(
    *,
    value: StrategyLiquiditySlippageGuardV10Input,
    guard_status: str,
    target_order_size: Decimal,
    max_order_size: Decimal,
    top_of_book_depth: Decimal,
    available_depth: Decimal,
    top_of_book_depth_ratio: Decimal,
    total_depth_ratio: Decimal,
    execution_price: Decimal,
    mid_price: Decimal,
    spread: Decimal,
    slippage_per_share: Decimal,
    expected_fee_amount: Decimal,
) -> Payload:
    return (
        ("market_slug", value.market_slug),
        ("side", value.side),
        ("order_direction", value.order_direction),
        ("guard_status", guard_status),
        ("decision_support_only", True),
        ("target_order_size", target_order_size),
        ("max_order_size", max_order_size),
        ("top_of_book_depth", top_of_book_depth),
        ("available_depth", available_depth),
        ("top_of_book_depth_ratio", top_of_book_depth_ratio),
        ("total_depth_ratio", total_depth_ratio),
        ("best_bid_price", value.best_bid_price),
        ("best_ask_price", value.best_ask_price),
        ("execution_price", execution_price),
        ("mid_price", mid_price),
        ("spread", spread),
        ("slippage_per_share", slippage_per_share),
        ("expected_fee_rate", value.expected_fee_rate),
        ("expected_fee_amount", expected_fee_amount),
        ("paper_only", True),
        ("report_only", True),
        ("readonly", True),
    )


def _validate_input_orderbook(value: StrategyLiquiditySlippageGuardV10Input) -> None:
    if value.best_bid_price > value.best_ask_price:
        raise ValueError("best_ask_price must be greater than or equal to best_bid_price")
    if value.top_bid_size > value.total_bid_depth:
        raise ValueError("total_bid_depth must cover top_bid_size")
    if value.top_ask_size > value.total_ask_depth:
        raise ValueError("total_ask_depth must cover top_ask_size")


def _validate_result_shape(result: StrategyLiquiditySlippageGuardV10Result) -> None:
    if result.best_bid_price > result.best_ask_price:
        raise ValueError("best_ask_price must be greater than or equal to best_bid_price")
    if result.max_order_size > result.target_order_size:
        raise ValueError("max_order_size must not exceed target_order_size")
    if result.top_of_book_depth > result.available_depth:
        raise ValueError("available_depth must cover top_of_book_depth")
    if result.execution_price != (
        result.best_ask_price if result.order_direction == "buy" else result.best_bid_price
    ):
        raise ValueError("execution_price must match order_direction")
    if result.spread != _subtract_decimal(result.best_ask_price, result.best_bid_price):
        raise ValueError("spread must match bid and ask prices")
    if result.mid_price != _divide_decimal(
        _add_decimal(result.best_bid_price, result.best_ask_price),
        TWO,
    ):
        raise ValueError("mid_price must match bid and ask prices")
    if result.slippage_per_share != _absolute_decimal(
        _subtract_decimal(result.execution_price, result.mid_price),
    ):
        raise ValueError("slippage_per_share must match execution and mid prices")
    if result.top_of_book_depth_ratio != _depth_ratio(
        result.top_of_book_depth,
        result.target_order_size,
    ):
        raise ValueError("top_of_book_depth_ratio must match depth and target order size")
    if result.total_depth_ratio != _depth_ratio(
        result.available_depth,
        result.target_order_size,
    ):
        raise ValueError("total_depth_ratio must match depth and target order size")
    if result.expected_fee_amount != _expected_fee_amount(
        order_size=result.max_order_size,
        execution_price=result.execution_price,
        expected_fee_rate=result.expected_fee_rate,
    ):
        raise ValueError("expected_fee_amount must match order size, price, and fee rate")
    if result.guard_status == "pass" and any(
        reason_code
        in (
            LOW_TOP_DEPTH_REASON,
            LOW_TOTAL_DEPTH_REASON,
            NO_DEPTH_REASON,
            CLIPPED_REASON,
            SLIPPAGE_REASON,
            SPREAD_REASON,
            FEE_RATE_REASON,
        )
        for reason_code in result.reason_codes
    ):
        raise ValueError("guard_status must match reason_codes")
    payload = dict(result.payload)
    for key in (
        "decision_support_only",
        "target_order_size",
        "max_order_size",
        "expected_fee_amount",
    ):
        if key not in payload:
            raise ValueError("payload must contain guard decision fields")
    if payload["decision_support_only"] is not True:
        raise ValueError("payload must be decision-support only")


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return _quantize(left)
    return _quantize(right)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _probability(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return decimal


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return _dedupe(normalized)


def _normalize_payload(value: Payload) -> Payload:
    if type(value) not in (list, tuple):
        raise ValueError("payload must be a list or tuple")
    normalized = tuple(value)
    seen_keys: set[str] = set()
    for item in normalized:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("payload must contain key-value pairs")
        key, payload_value = item
        _require_canonical_string("payload key", key)
        if key in seen_keys:
            raise ValueError("payload keys must be unique")
        seen_keys.add(key)
        if type(payload_value) not in (str, bool, Decimal):
            raise ValueError("payload values must be strings, bools, or Decimals")
        if type(payload_value) is str:
            _require_canonical_string("payload value", payload_value)
        if type(payload_value) is Decimal:
            _decimal("payload value", payload_value)
    return normalized


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value not in seen_values:
            result.append(value)
            seen_values.add(value)
    return tuple(result)


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined_values = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of: {joined_values}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_STRATEGY_LIQUIDITY_SLIPPAGE_GUARD_V10_CONFIG_VERSION",
    "StrategyLiquiditySlippageGuardV10Config",
    "StrategyLiquiditySlippageGuardV10Input",
    "StrategyLiquiditySlippageGuardV10Result",
    "build_strategy_liquidity_slippage_guard_v10",
)
