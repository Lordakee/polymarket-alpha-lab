from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.domain import (
    MarketScore,
    MarketSnapshot,
    OrderBookLevel,
    OrderBookSnapshot,
)


def test_market_snapshot_is_tradeable_only_when_active_open_and_accepting_orders():
    snapshot = MarketSnapshot.now(
        condition_id="0xabc",
        market_slug="example-market",
        question="Will the example resolve yes?",
        active=True,
        closed=False,
        accepting_orders=True,
    )

    assert snapshot.is_tradeable is True


def test_order_book_snapshot_derives_bid_ask_spread_and_midpoint():
    snapshot = OrderBookSnapshot(
        token_id="123",
        bids=(OrderBookLevel(price=Decimal("0.48"), size=Decimal("100")),),
        asks=(OrderBookLevel(price=Decimal("0.52"), size=Decimal("120")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    assert snapshot.best_bid == Decimal("0.48")
    assert snapshot.best_ask == Decimal("0.52")
    assert snapshot.spread == Decimal("0.04")
    assert snapshot.midpoint == Decimal("0.50")


def test_order_book_snapshot_ignores_non_executable_levels_for_best_prices():
    snapshot = OrderBookSnapshot(
        token_id="123",
        bids=(
            OrderBookLevel(price=Decimal("0"), size=Decimal("100")),
            OrderBookLevel(price=Decimal("0.48"), size=Decimal("100")),
        ),
        asks=(
            OrderBookLevel(price=Decimal("0"), size=Decimal("100")),
            OrderBookLevel(price=Decimal("0.52"), size=Decimal("0")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    assert snapshot.best_bid == Decimal("0.48")
    assert snapshot.best_ask is None
    assert snapshot.spread is None
    assert snapshot.midpoint is None


def test_order_book_snapshot_treats_crossed_executable_book_as_no_spread():
    snapshot = OrderBookSnapshot(
        token_id="123",
        bids=(OrderBookLevel(price=Decimal("0.60"), size=Decimal("10")),),
        asks=(OrderBookLevel(price=Decimal("0.55"), size=Decimal("10")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    assert snapshot.best_bid == Decimal("0.60")
    assert snapshot.best_ask == Decimal("0.55")
    assert snapshot.spread is None
    assert snapshot.midpoint is None


def test_market_score_applies_initial_weighting():
    score = MarketScore(
        condition_id="0xabc",
        token_id="123",
        activity=Decimal("80"),
        liquidity=Decimal("90"),
        spread_quality=Decimal("75"),
        time_structure=Decimal("60"),
        information_structure=Decimal("70"),
        price_behavior=Decimal("50"),
        duplicate_penalty=Decimal("20"),
    )

    assert score.total == Decimal("67.750")
