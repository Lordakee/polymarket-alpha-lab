"""Deterministic Level 0 market scoring."""

from __future__ import annotations

from decimal import Decimal

from polymarket_alpha_lab.domain import MarketScore, NormalizedMarket, OrderBookSnapshot


# Level 0 placeholders use neutral values until later nodes add time,
# price-behavior, and duplicate-market features.
def score_market(
    market: NormalizedMarket,
    books_by_token_id: dict[str, OrderBookSnapshot],
) -> list[MarketScore]:
    return [
        MarketScore(
            condition_id=market.market.condition_id,
            token_id=token.token_id,
            activity=_score_amount(market.market.volume_24h, Decimal("10000")),
            liquidity=_score_amount(market.market.liquidity, Decimal("20000")),
            spread_quality=_score_spread(books_by_token_id.get(token.token_id)),
            time_structure=Decimal("50"),
            information_structure=_score_information(market),
            price_behavior=Decimal("50"),
            duplicate_penalty=Decimal("0"),
        )
        for token in market.tokens
    ]


def _score_amount(value: Decimal | None, full_score_at: Decimal) -> Decimal:
    if value is None or value <= 0:
        return Decimal("0")
    return min(Decimal("100"), (value / full_score_at) * Decimal("100"))


def _score_spread(book: OrderBookSnapshot | None) -> Decimal:
    if book is None or book.spread is None:
        return Decimal("0")
    spread = book.spread
    if spread <= Decimal("0.01"):
        return Decimal("100")
    if spread >= Decimal("0.20"):
        return Decimal("0")
    return max(Decimal("0"), Decimal("100") - (spread * Decimal("500")))


def _score_information(market: NormalizedMarket) -> Decimal:
    score = Decimal("0")
    if market.rules_text:
        score += Decimal("50")
    if market.resolution_source:
        score += Decimal("50")
    return score
