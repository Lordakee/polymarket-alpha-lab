from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import ROUND_UP, Decimal, Inexact, Rounded, localcontext
from typing import Any, cast

import pytest

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.normalize import normalize_order_book
from polymarket_alpha_lab.paper import PaperOrder, simulate_order_book_fill


def test_simulate_buy_fill_walks_asks_and_reports_execution_costs():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(
            OrderBookLevel(Decimal("0.51"), Decimal("60")),
            OrderBookLevel(Decimal("0.52"), Decimal("60")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.token_id == "111"
    assert fill.side == "buy"
    assert fill.requested_size == Decimal("100")
    assert fill.order_book_captured_at == datetime(2026, 6, 13, tzinfo=UTC)
    assert len(fill.order_book_snapshot_sha256) == 64
    assert fill.order_book_snapshot_sha256 == fill.order_book_snapshot_sha256.lower()
    int(fill.order_book_snapshot_sha256, 16)
    assert fill.filled_size == Decimal("100")
    assert fill.unfilled_size == Decimal("0")
    assert fill.average_price == Decimal("0.514")
    assert fill.worst_price == Decimal("0.52")
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask == Decimal("0.51")
    assert fill.midpoint == Decimal("0.50")
    assert fill.spread == Decimal("0.02")
    assert fill.slippage_estimate == Decimal("0.004")
    assert fill.average_price != fill.midpoint
    assert fill.average_price > fill.best_ask
    assert fill.is_complete is True


def test_paper_order_and_fill_are_frozen():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))
    fill = simulate_order_book_fill(order, book)

    with pytest.raises(FrozenInstanceError):
        order.size = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        fill.filled_size = Decimal("1")


def test_simulate_sell_fill_walks_bids_and_reports_partial_fill():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.49"), Decimal("25")),
            OrderBookLevel(Decimal("0.48"), Decimal("25")),
        ),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("50")
    assert fill.unfilled_size == Decimal("50")
    assert fill.average_price == Decimal("0.485")
    assert fill.worst_price == Decimal("0.48")
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask == Decimal("0.51")
    assert fill.midpoint == Decimal("0.50")
    assert fill.spread == Decimal("0.02")
    assert fill.slippage_estimate == Decimal("0.005")
    assert fill.average_price != fill.midpoint
    assert fill.average_price < fill.best_bid
    assert fill.is_complete is False


def test_simulate_buy_fill_reports_partial_fill_when_asks_are_exhausted():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("100")),),
        asks=(
            OrderBookLevel(Decimal("0.51"), Decimal("25")),
            OrderBookLevel(Decimal("0.52"), Decimal("25")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("50")
    assert fill.unfilled_size == Decimal("50")
    assert fill.average_price == Decimal("0.515")
    assert fill.worst_price == Decimal("0.52")
    assert fill.slippage_estimate == Decimal("0.005")
    assert fill.is_complete is False


def test_simulate_fill_on_empty_traded_side_reports_no_execution_price():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("100")),),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("0")
    assert fill.unfilled_size == Decimal("100")
    assert fill.average_price is None
    assert fill.worst_price is None
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask is None
    assert fill.midpoint is None
    assert fill.spread is None
    assert fill.slippage_estimate is None
    assert fill.is_complete is False


def test_simulate_fill_on_empty_book_reports_no_quote_metadata():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("0")
    assert fill.unfilled_size == Decimal("100")
    assert fill.average_price is None
    assert fill.worst_price is None
    assert fill.best_bid is None
    assert fill.best_ask is None
    assert fill.midpoint is None
    assert fill.spread is None
    assert fill.slippage_estimate is None
    assert fill.is_complete is False


def test_simulate_fill_keeps_unfilled_size_exact_under_low_precision_context():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("12345.67"))

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_UP
        fill = simulate_order_book_fill(order, book)

    assert fill.requested_size == Decimal("12345.67")
    assert fill.filled_size == Decimal("0")
    assert fill.unfilled_size == Decimal("12345.67")


def test_simulate_fill_keeps_large_high_precision_size_accounting_exact():
    large_size = Decimal("1234567890123456789012345678.9")
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(OrderBookLevel(Decimal("0.51"), large_size),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=large_size)

    fill = simulate_order_book_fill(order, book)

    assert fill.requested_size == large_size
    assert fill.filled_size == large_size
    assert fill.unfilled_size == Decimal("0.0")
    assert fill.is_complete is True


def test_simulate_fill_order_book_snapshot_sha256_changes_with_book_contents():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    first_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=captured_at,
    )
    second_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=captured_at,
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    first_fill = simulate_order_book_fill(order, first_book)
    repeat_fill = simulate_order_book_fill(order, first_book)
    second_fill = simulate_order_book_fill(order, second_book)

    assert first_fill.order_book_snapshot_sha256 == repeat_fill.order_book_snapshot_sha256
    assert (
        first_fill.order_book_snapshot_sha256
        == "fa44f4677b4ca5be9e06a9ab1473a391f786d835984c7184ed2de65e8487c2a5"
    )
    assert first_fill.order_book_snapshot_sha256 != second_fill.order_book_snapshot_sha256


def test_simulate_fill_order_book_snapshot_sha256_is_independent_of_order():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    buy_fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="buy", size=Decimal("25")),
        book,
    )
    sell_fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="sell", size=Decimal("10")),
        book,
    )

    assert buy_fill.order_book_snapshot_sha256 == sell_fill.order_book_snapshot_sha256


def test_simulate_fill_order_book_snapshot_sha256_canonicalizes_decimals():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    first_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=captured_at,
    )
    equivalent_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.490"), Decimal("50.0")),),
        asks=(OrderBookLevel(Decimal("0.510"), Decimal("100.00")),),
        captured_at=captured_at,
    )

    first_fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="buy", size=Decimal("25")),
        first_book,
    )
    equivalent_fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="buy", size=Decimal("25.0")),
        equivalent_book,
    )

    assert first_book == equivalent_book
    assert first_fill.order_book_snapshot_sha256 == equivalent_fill.order_book_snapshot_sha256


@pytest.mark.parametrize(
    "changed_book",
    [
        OrderBookSnapshot(
            token_id="222",
            bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
            asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
            captured_at=datetime(2026, 6, 13, tzinfo=UTC),
        ),
        OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.49"), Decimal("51")),),
            asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
            captured_at=datetime(2026, 6, 13, tzinfo=UTC),
        ),
        OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
            asks=(
                OrderBookLevel(Decimal("0.51"), Decimal("100")),
                OrderBookLevel(Decimal("0.52"), Decimal("25")),
            ),
            captured_at=datetime(2026, 6, 13, tzinfo=UTC),
        ),
        OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
            asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
            captured_at=datetime(2026, 6, 13, 0, 0, 1, tzinfo=UTC),
        ),
        OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
            asks=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
            captured_at=datetime(2026, 6, 13, tzinfo=UTC),
        ),
    ],
)
def test_simulate_fill_order_book_snapshot_sha256_changes_with_identity_fields(
    changed_book,
):
    base_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    base_fill = simulate_order_book_fill(
        PaperOrder(token_id=base_book.token_id, side="buy", size=Decimal("25")),
        base_book,
    )
    changed_fill = simulate_order_book_fill(
        PaperOrder(token_id=changed_book.token_id, side="buy", size=Decimal("25")),
        changed_book,
    )

    assert base_fill.order_book_snapshot_sha256 != changed_fill.order_book_snapshot_sha256


def test_simulate_fill_skips_non_positive_traded_levels():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("25")),),
        asks=(
            OrderBookLevel(Decimal("0.51"), Decimal("0")),
            OrderBookLevel(Decimal("0.52"), Decimal("-10")),
            OrderBookLevel(Decimal("0.53"), Decimal("25")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.530")
    assert fill.worst_price == Decimal("0.53")
    assert fill.best_ask == Decimal("0.53")
    assert fill.spread == Decimal("0.04")
    assert fill.midpoint == Decimal("0.510")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_fill_skips_non_positive_traded_prices():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("25")),),
        asks=(
            OrderBookLevel(Decimal("0"), Decimal("100")),
            OrderBookLevel(Decimal("-0.01"), Decimal("100")),
            OrderBookLevel(Decimal("0.53"), Decimal("25")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.530")
    assert fill.worst_price == Decimal("0.53")
    assert fill.best_ask == Decimal("0.53")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_sell_fill_skips_non_positive_traded_prices():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0"), Decimal("100")),
            OrderBookLevel(Decimal("-0.01"), Decimal("100")),
            OrderBookLevel(Decimal("0.48"), Decimal("25")),
        ),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("25")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.480")
    assert fill.worst_price == Decimal("0.48")
    assert fill.best_bid == Decimal("0.48")
    assert fill.best_ask == Decimal("0.51")
    assert fill.spread == Decimal("0.030")
    assert fill.midpoint == Decimal("0.495")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_fill_skips_non_finite_traded_levels():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("25")),),
        asks=(
            OrderBookLevel(Decimal("NaN"), Decimal("100")),
            OrderBookLevel(Decimal("Infinity"), Decimal("100")),
            OrderBookLevel(Decimal("0.52"), Decimal("Infinity")),
            OrderBookLevel(Decimal("0.53"), Decimal("NaN")),
            OrderBookLevel(Decimal("0.54"), Decimal("25")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.540")
    assert fill.worst_price == Decimal("0.54")
    assert fill.best_ask == Decimal("0.54")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_fill_skips_non_finite_quote_metadata_levels():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("NaN"), Decimal("100")),
            OrderBookLevel(Decimal("Infinity"), Decimal("100")),
            OrderBookLevel(Decimal("0.49"), Decimal("25")),
        ),
        asks=(
            OrderBookLevel(Decimal("NaN"), Decimal("100")),
            OrderBookLevel(Decimal("0.51"), Decimal("25")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask == Decimal("0.51")
    assert fill.spread == Decimal("0.02")
    assert fill.midpoint == Decimal("0.50")


def test_simulate_sell_fill_skips_non_finite_traded_levels():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("NaN"), Decimal("100")),
            OrderBookLevel(Decimal("Infinity"), Decimal("100")),
            OrderBookLevel(Decimal("0.52"), Decimal("Infinity")),
            OrderBookLevel(Decimal("0.51"), Decimal("NaN")),
            OrderBookLevel(Decimal("0.48"), Decimal("25")),
        ),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("25")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.480")
    assert fill.worst_price == Decimal("0.48")
    assert fill.best_bid == Decimal("0.48")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_sell_fill_skips_non_positive_top_bid_for_quote_metadata():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.49"), Decimal("0")),
            OrderBookLevel(Decimal("0.48"), Decimal("25")),
        ),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("25")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.480")
    assert fill.worst_price == Decimal("0.48")
    assert fill.best_bid == Decimal("0.48")
    assert fill.spread == Decimal("0.03")
    assert fill.midpoint == Decimal("0.495")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_buy_fill_executes_with_asks_only():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.510")
    assert fill.best_bid is None
    assert fill.best_ask == Decimal("0.51")
    assert fill.midpoint is None
    assert fill.spread is None
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_sell_fill_executes_with_bids_only():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("100")),),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("25")
    assert fill.average_price == Decimal("0.490")
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask is None
    assert fill.midpoint is None
    assert fill.spread is None
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.is_complete is True


def test_simulate_sell_fill_on_empty_bids_reports_no_execution_price():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("0")
    assert fill.unfilled_size == Decimal("100")
    assert fill.average_price is None
    assert fill.worst_price is None
    assert fill.best_bid is None
    assert fill.best_ask == Decimal("0.51")
    assert fill.midpoint is None
    assert fill.spread is None
    assert fill.slippage_estimate is None
    assert fill.is_complete is False


def test_simulate_fill_quantizes_with_explicit_rounding():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.514"), Decimal("1")),
            OrderBookLevel(Decimal("0.515"), Decimal("1")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("2"))

    with localcontext() as context:
        context.rounding = ROUND_UP
        fill = simulate_order_book_fill(order, book)

    assert fill.average_price == Decimal("0.514")
    assert fill.slippage_estimate == Decimal("0.000")
    assert fill.average_price.as_tuple().exponent == -3
    assert fill.slippage_estimate.as_tuple().exponent == -3
    assert fill.midpoint.as_tuple().exponent == -3
    assert fill.spread.as_tuple().exponent == -3


def test_simulate_fill_uses_half_even_rounding_for_upward_ties():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.515"), Decimal("1")),
            OrderBookLevel(Decimal("0.516"), Decimal("1")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("2"))

    with localcontext() as context:
        context.rounding = ROUND_UP
        fill = simulate_order_book_fill(order, book)

    assert fill.average_price == Decimal("0.516")


def test_simulate_fill_preserves_high_precision_average_before_quantizing():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.121"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.122"), Decimal("1")),
            OrderBookLevel(Decimal("0.123"), Decimal("1.000000000000000000000000000001")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(
        token_id="111",
        side="buy",
        size=Decimal("2.000000000000000000000000000001"),
    )

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("2.000000000000000000000000000001")
    assert fill.average_price == Decimal("0.123")
    assert fill.slippage_estimate == Decimal("0.001")


def test_simulate_fill_preserves_high_precision_spread_before_quantizing():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.1"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.1025000000000000000000000000001"), Decimal("10")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("1"))

    fill = simulate_order_book_fill(order, book)

    assert fill.spread == Decimal("0.003")


def test_simulate_fill_preserves_high_precision_midpoint_before_quantizing():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.1"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.1010000000000000000000000000002"), Decimal("10")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("1"))

    fill = simulate_order_book_fill(order, book)

    assert fill.midpoint == Decimal("0.101")


def test_simulate_fill_preserves_high_precision_quote_metadata_under_hostile_context():
    spread_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.1"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.1025000000000000000000000000001"), Decimal("10")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    midpoint_book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.1"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.1010000000000000000000000000002"), Decimal("10")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_UP
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        spread_fill = simulate_order_book_fill(
            PaperOrder(token_id="111", side="buy", size=Decimal("1")),
            spread_book,
        )
        midpoint_fill = simulate_order_book_fill(
            PaperOrder(token_id="111", side="buy", size=Decimal("1")),
            midpoint_book,
        )

    assert spread_fill.spread == Decimal("0.003")
    assert midpoint_fill.midpoint == Decimal("0.101")


def test_simulate_fill_quantizes_independently_from_decimal_precision_context():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.514"), Decimal("1")),
            OrderBookLevel(Decimal("0.515"), Decimal("1")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("2"))

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_UP
        fill = simulate_order_book_fill(order, book)

    assert fill.average_price == Decimal("0.514")
    assert fill.slippage_estimate == Decimal("0.000")


def test_simulate_fill_quantizes_independently_from_decimal_traps():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("10")),),
        asks=(
            OrderBookLevel(Decimal("0.514"), Decimal("1")),
            OrderBookLevel(Decimal("0.515"), Decimal("1")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("2"))

    with localcontext() as context:
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        fill = simulate_order_book_fill(order, book)

    assert fill.average_price == Decimal("0.514")
    assert fill.slippage_estimate == Decimal("0.000")


def test_simulate_sell_fill_keeps_high_precision_size_accounting_under_hostile_context():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(
                Decimal("0.49"),
                Decimal("1.000000000000000000000000000001"),
            ),
            OrderBookLevel(Decimal("0.48"), Decimal("1.5")),
        ),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("10")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(
        token_id="111",
        side="sell",
        size=Decimal("3.000000000000000000000000000001"),
    )

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_UP
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("2.500000000000000000000000000001")
    assert fill.unfilled_size == Decimal("0.500000000000000000000000000000")
    assert fill.average_price == Decimal("0.484")
    assert fill.slippage_estimate == Decimal("0.006")
    assert fill.is_complete is False


def test_simulate_fill_ignores_later_levels_after_order_is_complete():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(
            OrderBookLevel(Decimal("0.51"), Decimal("60")),
            OrderBookLevel(Decimal("0.52"), Decimal("40")),
            OrderBookLevel(Decimal("0.90"), Decimal("100")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("100")
    assert fill.average_price == Decimal("0.514")
    assert fill.worst_price == Decimal("0.52")


def test_simulate_fill_does_not_inspect_later_levels_after_order_is_complete():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(
            OrderBookLevel(Decimal("0.51"), Decimal("100")),
            OrderBookLevel(Decimal("NaN"), Decimal("100")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("100")
    assert fill.worst_price == Decimal("0.51")


def test_simulate_fill_uses_normalized_order_book_sorting():
    book = normalize_order_book(
        {
            "asset_id": "111",
            "bids": [
                {"price": "0.40", "size": "10"},
                {"price": "0.49", "size": "10"},
            ],
            "asks": [
                {"price": "0.60", "size": "10"},
                {"price": "0.51", "size": "10"},
            ],
        },
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("15"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("15")
    assert fill.average_price == Decimal("0.540")
    assert fill.worst_price == Decimal("0.60")
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask == Decimal("0.51")
    assert fill.spread == Decimal("0.020")


def test_simulate_fill_preserves_crossed_book_spread_while_using_correct_side():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.55"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.53"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("25"))

    fill = simulate_order_book_fill(order, book)

    assert fill.average_price == Decimal("0.530")
    assert fill.best_bid == Decimal("0.55")
    assert fill.best_ask == Decimal("0.53")
    assert fill.spread == Decimal("-0.020")
    assert fill.midpoint == Decimal("0.540")


def test_simulate_fill_rejects_token_mismatch():
    book = OrderBookSnapshot(
        token_id="222",
        bids=(),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    with pytest.raises(ValueError, match="token"):
        simulate_order_book_fill(order, book)


def test_simulate_fill_rejects_non_positive_order_size():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    for size in (Decimal("0"), Decimal("-1")):
        order = PaperOrder(token_id="111", side="buy", size=size)

        with pytest.raises(ValueError, match="size"):
            simulate_order_book_fill(order, book)


def test_simulate_fill_rejects_non_finite_order_size():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    for size in (
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ):
        order = PaperOrder(token_id="111", side="buy", size=size)

        with pytest.raises(ValueError, match="finite"):
            simulate_order_book_fill(order, book)


def test_simulate_fill_rejects_invalid_side():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side=cast(Any, "hold"), size=Decimal("10"))

    with pytest.raises(ValueError, match="side"):
        simulate_order_book_fill(order, book)
