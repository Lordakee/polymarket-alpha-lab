"""Read-only market scan orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from polymarket_alpha_lab.archive import RawArchive
from polymarket_alpha_lab.domain import OrderBookSnapshot
from polymarket_alpha_lab.normalize import normalize_gamma_market, normalize_order_book
from polymarket_alpha_lab.scoring import score_market


class MarketDataClient(Protocol):
    def list_markets(self, *, active: bool, closed: bool, limit: int) -> Any:
        """Return raw public market payloads."""

    def get_order_book(self, *, token_id: str) -> Any:
        """Return raw public order book payload for one CLOB token id."""


@dataclass(frozen=True)
class MarketScanConfig:
    limit: int
    archive_root: Path
    output_path: Path
    fetch_books: bool = True


@dataclass(frozen=True)
class ScoredCandidate:
    condition_id: str
    token_id: str
    market_slug: str
    question: str
    total_score: str
    raw_archive_path: str


def run_market_scan(
    *,
    client: MarketDataClient,
    config: MarketScanConfig,
    captured_at: datetime | None = None,
) -> list[ScoredCandidate]:
    timestamp = captured_at or datetime.now(UTC)
    archive = RawArchive(config.archive_root)
    markets_payload = client.list_markets(active=True, closed=False, limit=config.limit)
    markets_archive = archive.write(
        source="gamma",
        name="markets",
        payload=markets_payload,
        captured_at=timestamp,
        endpoint="/markets",
        params={"active": True, "closed": False, "limit": config.limit},
    )

    ranked: list[tuple[Decimal, ScoredCandidate]] = []
    for raw_market in _iter_dicts(markets_payload):
        normalized_market = normalize_gamma_market(raw_market, captured_at=timestamp)
        if (
            not normalized_market.market.condition_id
            or not normalized_market.tokens
            or not normalized_market.market.is_tradeable
        ):
            continue
        books_by_token_id: dict[str, OrderBookSnapshot] = {}
        if config.fetch_books:
            books_by_token_id = _fetch_books(
                client=client,
                archive=archive,
                token_ids=[token.token_id for token in normalized_market.tokens],
                captured_at=timestamp,
            )
        for score in score_market(normalized_market, books_by_token_id):
            candidate = ScoredCandidate(
                condition_id=score.condition_id,
                token_id=score.token_id,
                market_slug=normalized_market.market.market_slug,
                question=normalized_market.market.question,
                total_score=_format_decimal(score.total),
                raw_archive_path=str(markets_archive.payload_path),
            )
            ranked.append((score.total, candidate))

    candidates = [
        candidate
        for _, candidate in sorted(
            ranked, key=lambda item: (item[0], item[1].token_id), reverse=True
        )
    ]
    _write_output(config.output_path, candidates)
    return candidates


def _fetch_books(
    *,
    client: MarketDataClient,
    archive: RawArchive,
    token_ids: list[str],
    captured_at: datetime,
) -> dict[str, OrderBookSnapshot]:
    books: dict[str, OrderBookSnapshot] = {}
    for token_id in token_ids:
        try:
            raw_book = client.get_order_book(token_id=token_id)
        except Exception:
            continue
        archive.write(
            source="clob",
            name=f"book-{token_id}",
            payload=raw_book,
            captured_at=captured_at,
            endpoint="/book",
            params={"token_id": token_id},
        )
        if isinstance(raw_book, dict):
            book = normalize_order_book(raw_book, captured_at=captured_at)
            books[book.token_id] = book
    return books


def _iter_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return [item for item in payload["data"] if isinstance(item, dict)]
    return []


def _write_output(path: Path, candidates: list[ScoredCandidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(candidate) for candidate in candidates], indent=2) + "\n",
        encoding="utf-8",
    )


def _format_decimal(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.001")))
