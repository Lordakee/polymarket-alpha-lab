"""Core domain objects for the research system.

These types deliberately avoid network, wallet, and execution concerns. They
capture the shared vocabulary used by the planning documents and later modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True)
class OutcomeToken:
    """A tradable outcome token inside a Polymarket market."""

    condition_id: str
    token_id: str
    outcome_index: int
    outcome_name: str


@dataclass(frozen=True)
class MarketSnapshot:
    """Normalized market metadata at one point in time."""

    condition_id: str
    market_slug: str
    question: str
    active: bool
    closed: bool
    accepting_orders: bool
    end_time: datetime | None
    volume_24h: Decimal | None
    liquidity: Decimal | None
    captured_at: datetime
    enable_order_book: bool | None = None
    order_min_size: Decimal | None = None
    order_price_min_tick_size: Decimal | None = None
    resolution_status: str | None = None

    @property
    def is_tradeable(self) -> bool:
        """Return whether this market belongs in the active research universe."""

        return self.active and not self.closed and self.accepting_orders

    @classmethod
    def now(
        cls,
        *,
        condition_id: str,
        market_slug: str,
        question: str,
        active: bool,
        closed: bool,
        accepting_orders: bool,
        end_time: datetime | None = None,
        volume_24h: Decimal | None = None,
        liquidity: Decimal | None = None,
    ) -> "MarketSnapshot":
        return cls(
            condition_id=condition_id,
            market_slug=market_slug,
            question=question,
            active=active,
            closed=closed,
            accepting_orders=accepting_orders,
            end_time=end_time,
            volume_24h=volume_24h,
            liquidity=liquidity,
            captured_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class NormalizedMarket:
    """Market metadata plus its tradable outcome tokens."""

    market: MarketSnapshot
    tokens: tuple[OutcomeToken, ...]
    rules_text: str | None
    resolution_source: str | None


@dataclass(frozen=True)
class OrderBookLevel:
    """One price level in an order book."""

    price: Decimal
    size: Decimal


@dataclass(frozen=True)
class OrderBookSnapshot:
    """A normalized order book snapshot for one outcome token."""

    token_id: str
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    captured_at: datetime

    @property
    def best_bid(self) -> Decimal | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Decimal | None:
        return self.asks[0].price if self.asks else None

    @property
    def spread(self) -> Decimal | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

    @property
    def midpoint(self) -> Decimal | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / Decimal("2")


@dataclass(frozen=True)
class MarketScore:
    """Market screening scores normalized to a 0-100 scale."""

    condition_id: str
    token_id: str
    activity: Decimal
    liquidity: Decimal
    spread_quality: Decimal
    time_structure: Decimal
    information_structure: Decimal
    price_behavior: Decimal
    duplicate_penalty: Decimal

    @property
    def total(self) -> Decimal:
        """Weighted screening score from the initial project design."""

        book_quality = (self.liquidity + self.spread_quality) / Decimal("2")
        return (
            self.activity * Decimal("0.25")
            + book_quality * Decimal("0.30")
            + self.time_structure * Decimal("0.10")
            + self.information_structure * Decimal("0.15")
            + self.price_behavior * Decimal("0.15")
            - self.duplicate_penalty * Decimal("0.05")
        )
