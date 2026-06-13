"""Paper-fill simulation utilities for normalized order book snapshots."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from hashlib import sha256
from typing import Iterator
from typing import Literal

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot

PaperSide = Literal["buy", "sell"]

PRICE_QUANTUM = Decimal("0.001")
PRICE_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class PaperOrder:
    token_id: str
    side: PaperSide
    size: Decimal


@dataclass(frozen=True)
class PaperFill:
    token_id: str
    side: PaperSide
    requested_size: Decimal
    order_book_captured_at: datetime
    order_book_snapshot_sha256: str
    filled_size: Decimal
    unfilled_size: Decimal
    average_price: Decimal | None
    worst_price: Decimal | None
    best_bid: Decimal | None
    best_ask: Decimal | None
    midpoint: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None

    @property
    def is_complete(self) -> bool:
        return self.unfilled_size == 0


def simulate_order_book_fill(order: PaperOrder, book: OrderBookSnapshot) -> PaperFill:
    """Simulate a paper fill by walking normalized best-first executable levels."""

    if order.token_id != book.token_id:
        raise ValueError("order token_id must match order book token_id")
    if order.side not in ("buy", "sell"):
        raise ValueError("order side must be buy or sell")
    if not order.size.is_finite():
        raise ValueError("order size must be finite")
    if order.size <= 0:
        raise ValueError("order size must be positive")

    best_bid = _best_executable_price(book.bids)
    best_ask = _best_executable_price(book.asks)
    spread = _spread(best_bid=best_bid, best_ask=best_ask)
    midpoint = _midpoint(best_bid=best_bid, best_ask=best_ask)
    levels = book.asks if order.side == "buy" else book.bids
    filled_size, notional, worst_price = _walk_levels(order.size, levels)
    with _exact_decimal_context(order.size, filled_size):
        unfilled_size = order.size - filled_size

    average_price: Decimal | None
    slippage_estimate: Decimal | None
    if filled_size == 0:
        average_price = None
        slippage_estimate = None
    else:
        exact_average_price = _divide_price(notional, filled_size)
        average_price = _quantize_price(exact_average_price)
        if order.side == "buy":
            slippage_estimate = (
                None
                if best_ask is None
                else _quantize_price(_positive_difference(exact_average_price, best_ask))
            )
        else:
            slippage_estimate = (
                None
                if best_bid is None
                else _quantize_price(_positive_difference(best_bid, exact_average_price))
            )

    return PaperFill(
        token_id=order.token_id,
        side=order.side,
        requested_size=order.size,
        order_book_captured_at=book.captured_at,
        order_book_snapshot_sha256=_order_book_snapshot_sha256(book),
        filled_size=filled_size,
        unfilled_size=unfilled_size,
        average_price=average_price,
        worst_price=worst_price,
        best_bid=best_bid,
        best_ask=best_ask,
        midpoint=midpoint,
        spread=spread,
        slippage_estimate=slippage_estimate,
    )


def _walk_levels(
    requested_size: Decimal,
    levels: tuple[OrderBookLevel, ...],
) -> tuple[Decimal, Decimal, Decimal | None]:
    filled_size = Decimal("0")
    notional = Decimal("0")
    worst_price: Decimal | None = None

    for level in levels:
        with _exact_decimal_context(requested_size, filled_size):
            remaining_size = requested_size - filled_size
        if remaining_size <= 0:
            break
        if not _is_executable_level(level):
            continue

        level_fill_size = min(remaining_size, level.size)
        with _exact_decimal_context(filled_size, level_fill_size):
            filled_size += level_fill_size
        with _exact_decimal_context(notional, level_fill_size, level.price):
            notional += level_fill_size * level.price
        worst_price = level.price

    return filled_size, notional, worst_price


def _best_executable_price(levels: tuple[OrderBookLevel, ...]) -> Decimal | None:
    for level in levels:
        if _is_executable_level(level):
            return level.price
    return None


def _is_executable_level(level: OrderBookLevel) -> bool:
    return (
        level.size.is_finite()
        and level.price.is_finite()
        and level.size > 0
        and level.price > 0
    )


def _order_book_snapshot_sha256(book: OrderBookSnapshot) -> str:
    payload = {
        "token_id": book.token_id,
        "captured_at": book.captured_at.isoformat(),
        "bids": _levels_for_hash(book.bids),
        "asks": _levels_for_hash(book.asks),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _levels_for_hash(levels: tuple[OrderBookLevel, ...]) -> list[dict[str, str]]:
    return [
        {
            "price": _decimal_for_hash(level.price),
            "size": _decimal_for_hash(level.size),
        }
        for level in levels
    ]


def _decimal_for_hash(value: Decimal) -> str:
    if not value.is_finite():
        return str(value)
    if value.is_zero():
        return "0"
    with _exact_decimal_context(value):
        normalized = value.normalize()
    return format(normalized, "f")


def _spread(*, best_bid: Decimal | None, best_ask: Decimal | None) -> Decimal | None:
    if best_bid is None or best_ask is None:
        return None
    with _exact_decimal_context(best_bid, best_ask, PRICE_QUANTUM):
        spread = best_ask - best_bid
    return _quantize_price(spread)


def _midpoint(*, best_bid: Decimal | None, best_ask: Decimal | None) -> Decimal | None:
    if best_bid is None or best_ask is None:
        return None
    with _exact_decimal_context(best_bid, best_ask, PRICE_QUANTUM):
        midpoint = (best_bid + best_ask) / Decimal("2")
    return _quantize_price(midpoint)


def _quantize_price(value: Decimal) -> Decimal:
    with _price_context():
        return value.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _divide_price(numerator: Decimal, denominator: Decimal) -> Decimal:
    with _exact_decimal_context(numerator, denominator, PRICE_QUANTUM):
        return numerator / denominator


def _positive_difference(left: Decimal, right: Decimal) -> Decimal:
    with _exact_decimal_context(left, right, PRICE_QUANTUM):
        return max(Decimal("0"), left - right)


@contextmanager
def _price_context() -> Iterator[None]:
    with localcontext(PRICE_CONTEXT):
        yield


@contextmanager
def _exact_decimal_context(*values: Decimal) -> Iterator[None]:
    with localcontext(Context(prec=_exact_decimal_precision(values), rounding=ROUND_HALF_EVEN)):
        yield


def _exact_decimal_precision(values: tuple[Decimal, ...]) -> int:
    finite_values = [value for value in values if value.is_finite()]
    if not finite_values:
        return 28
    required_digits = sum(
        _integer_digit_count(value) + _fractional_digit_count(value)
        for value in finite_values
    )
    return max(28, required_digits + len(finite_values) + 2)


def _integer_digit_count(value: Decimal) -> int:
    if value.is_zero():
        return 1
    return max(value.adjusted() + 1, 0)


def _fractional_digit_count(value: Decimal) -> int:
    return max(-value.as_tuple().exponent, 0)
