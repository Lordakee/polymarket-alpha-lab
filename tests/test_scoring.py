from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)
from polymarket_alpha_lab.scoring import score_market


def test_score_market_rewards_activity_liquidity_and_tight_spread():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    market = NormalizedMarket(
        market=MarketSnapshot(
            condition_id="0xabc",
            market_slug="example",
            question="Will this happen?",
            active=True,
            closed=False,
            accepting_orders=True,
            end_time=None,
            volume_24h=Decimal("10000"),
            liquidity=Decimal("20000"),
            captured_at=captured_at,
        ),
        tokens=(
            OutcomeToken("0xabc", "111", 0, "Yes"),
            OutcomeToken("0xabc", "222", 1, "No"),
        ),
        rules_text="Clear rule text",
        resolution_source="https://example.com",
    )
    books = {
        "111": OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.49"), Decimal("500")),),
            asks=(OrderBookLevel(Decimal("0.51"), Decimal("500")),),
            captured_at=captured_at,
        )
    }

    scores = score_market(market, books)

    assert len(scores) == 2
    assert scores[0].token_id == "111"
    assert scores[0].activity > Decimal("0")
    assert scores[0].liquidity > Decimal("0")
    assert scores[0].spread_quality > Decimal("0")
    assert scores[0].total > Decimal("50")
    assert scores[1].token_id == "222"
    assert scores[1].spread_quality == Decimal("0")
    assert scores[1].total > Decimal("0")


def test_score_market_does_not_reward_books_without_executable_ask():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    market = NormalizedMarket(
        market=MarketSnapshot(
            condition_id="0xabc",
            market_slug="example",
            question="Will this happen?",
            active=True,
            closed=False,
            accepting_orders=True,
            end_time=None,
            volume_24h=Decimal("10000"),
            liquidity=Decimal("20000"),
            captured_at=captured_at,
        ),
        tokens=(OutcomeToken("0xabc", "111", 0, "Yes"),),
        rules_text="Clear rule text",
        resolution_source="https://example.com",
    )
    books = {
        "111": OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.40"), Decimal("10")),),
            asks=(OrderBookLevel(Decimal("0"), Decimal("5")),),
            captured_at=captured_at,
        )
    }

    scores = score_market(market, books)

    assert scores[0].spread_quality == Decimal("0")


def test_score_market_does_not_reward_crossed_books_as_tight_spreads():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    market = NormalizedMarket(
        market=MarketSnapshot(
            condition_id="0xabc",
            market_slug="example",
            question="Will this happen?",
            active=True,
            closed=False,
            accepting_orders=True,
            end_time=None,
            volume_24h=Decimal("10000"),
            liquidity=Decimal("20000"),
            captured_at=captured_at,
        ),
        tokens=(OutcomeToken("0xabc", "111", 0, "Yes"),),
        rules_text="Clear rule text",
        resolution_source="https://example.com",
    )
    books = {
        "111": OrderBookSnapshot(
            token_id="111",
            bids=(OrderBookLevel(Decimal("0.60"), Decimal("10")),),
            asks=(OrderBookLevel(Decimal("0.55"), Decimal("10")),),
            captured_at=captured_at,
        )
    }

    scores = score_market(market, books)

    assert scores[0].spread_quality == Decimal("0")
