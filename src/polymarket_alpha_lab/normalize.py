"""Normalization from raw Polymarket payloads into domain objects."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)


def normalize_gamma_market(
    payload: dict[str, Any], *, captured_at: datetime
) -> NormalizedMarket:
    condition_id = str(payload.get("conditionId") or "")
    outcomes = _as_list(payload.get("outcomes"))
    token_ids = _as_list(payload.get("clobTokenIds"))
    tokens = tuple(
        OutcomeToken(
            condition_id=condition_id,
            token_id=str(token_id),
            outcome_index=index,
            outcome_name=str(outcomes[index]) if index < len(outcomes) else str(index),
        )
        for index, token_id in enumerate(token_ids)
    )
    accepting_orders = bool(_parse_optional_bool(payload.get("acceptingOrders")))
    enable_order_book = _parse_optional_bool(payload.get("enableOrderBook"))
    market = MarketSnapshot(
        condition_id=condition_id,
        market_slug=str(payload.get("slug") or payload.get("marketSlug") or ""),
        question=str(payload.get("question") or ""),
        active=bool(payload.get("active")),
        closed=bool(payload.get("closed")),
        accepting_orders=accepting_orders and (enable_order_book is not False),
        end_time=_parse_datetime(payload.get("endDate")),
        volume_24h=_parse_decimal(payload.get("volume24hr")),
        liquidity=_parse_decimal(payload.get("liquidity")),
        captured_at=captured_at,
        enable_order_book=enable_order_book,
        order_min_size=_parse_decimal(payload.get("orderMinSize")),
        order_price_min_tick_size=_parse_decimal(payload.get("orderPriceMinTickSize")),
        resolution_status=_optional_string(
            payload.get("resolutionStatus") or payload.get("resolved")
        ),
    )
    return NormalizedMarket(
        market=market,
        tokens=tokens,
        rules_text=_optional_string(payload.get("description") or payload.get("rules")),
        resolution_source=_optional_string(payload.get("resolutionSource")),
    )


def normalize_order_book(
    payload: dict[str, Any], *, captured_at: datetime
) -> OrderBookSnapshot:
    token_id = str(payload.get("asset_id") or payload.get("token_id") or "")
    bids = tuple(
        sorted(
            (_book_level(level) for level in payload.get("bids", [])),
            key=lambda level: level.price,
            reverse=True,
        )
    )
    asks = tuple(
        sorted(
            (_book_level(level) for level in payload.get("asks", [])),
            key=lambda level: level.price,
        )
    )
    return OrderBookSnapshot(token_id=token_id, bids=bids, asks=asks, captured_at=captured_at)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, list) else []
    return []


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _parse_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return bool(value)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return datetime.fromisoformat(text).astimezone(UTC)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _book_level(payload: dict[str, Any]) -> OrderBookLevel:
    price = _parse_decimal(payload.get("price")) or Decimal("0")
    size = _parse_decimal(payload.get("size")) or Decimal("0")
    return OrderBookLevel(price=price, size=size)
