from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.normalize import (
    normalize_gamma_market,
    normalize_order_book,
)


def test_normalize_gamma_market_parses_stringified_tokens_and_prices():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    payload = {
        "conditionId": "0xabc",
        "slug": "example-market",
        "question": "Will the example resolve yes?",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "endDate": "2026-07-01T00:00:00Z",
        "volume24hr": "123.45",
        "liquidity": "456.78",
        "orderMinSize": "5",
        "orderPriceMinTickSize": "0.01",
        "outcomes": '["Yes","No"]',
        "clobTokenIds": '["111","222"]',
        "description": "Example rules",
        "resolutionSource": "https://example.com",
    }

    normalized = normalize_gamma_market(payload, captured_at=captured_at)

    assert normalized.market.condition_id == "0xabc"
    assert normalized.market.is_tradeable is True
    assert normalized.market.volume_24h == Decimal("123.45")
    assert normalized.market.enable_order_book is True
    assert normalized.market.order_min_size == Decimal("5")
    assert normalized.market.order_price_min_tick_size == Decimal("0.01")
    assert normalized.tokens[0].token_id == "111"
    assert normalized.tokens[0].outcome_name == "Yes"
    assert normalized.tokens[1].token_id == "222"
    assert normalized.rules_text == "Example rules"
    assert normalized.resolution_source == "https://example.com"


def test_normalize_gamma_market_treats_string_false_order_book_as_not_tradeable():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    payload = {
        "conditionId": "0xabc",
        "slug": "example-market",
        "question": "Will the example resolve yes?",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": "false",
        "outcomes": ["Yes"],
        "clobTokenIds": ["111"],
    }

    normalized = normalize_gamma_market(payload, captured_at=captured_at)

    assert normalized.market.enable_order_book is False
    assert normalized.market.is_tradeable is False


def test_normalize_order_book_sorts_bids_descending_and_asks_ascending():
    captured_at = datetime(2026, 6, 13, tzinfo=UTC)
    payload = {
        "asset_id": "111",
        "bids": [{"price": "0.40", "size": "10"}, {"price": "0.45", "size": "3"}],
        "asks": [{"price": "0.60", "size": "8"}, {"price": "0.55", "size": "4"}],
    }

    book = normalize_order_book(payload, captured_at=captured_at)

    assert book.token_id == "111"
    assert [level.price for level in book.bids] == [Decimal("0.45"), Decimal("0.40")]
    assert [level.price for level in book.asks] == [Decimal("0.55"), Decimal("0.60")]
    assert book.spread == Decimal("0.10")
