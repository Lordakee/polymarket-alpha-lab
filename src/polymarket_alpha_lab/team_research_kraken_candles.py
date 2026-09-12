"""Strict Kraken OHLC decoding for cross-venue research; no I/O or storage."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from types import MappingProxyType
from urllib.parse import urlencode

from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, aware, hard_flags, integer, strict_json
from polymarket_alpha_lab.team_research_crypto_candles import (
    CryptoCandleWindow, _number, _scope, _seconds,
)

# No dynamic asset lookup, provider-supplied URL, or USD/stablecoin substitution.
PAIRS = MappingProxyType({"BTC-USD": ("XBTUSD", "XXBTZUSD"), "ETH-USD": ("ETHUSD", "XETHZUSD")})
SHARED_GRANULARITIES = (60, 300, 900, 3600, 86400)
MAX_KRAKEN_BYTES = 262144
KRAKEN_REASONS = (
    "invalid_kraken_payload", "kraken_api_error", "kraken_pair_mismatch",
    "duplicate_kraken_bucket", "kraken_window_incomplete", "kraken_empty_bucket",
    "kraken_evidence_too_large",
)


def kraken_window(window: CryptoCandleWindow) -> CryptoCandleWindow:
    if type(window) is not CryptoCandleWindow:
        raise ValueError("expected exact CryptoCandleWindow")
    window = replace(window)
    if window.granularity_seconds not in SHARED_GRANULARITIES:
        raise ValueError("granularity must be supported by both venues")
    return window


def kraken_reference(window: CryptoCandleWindow) -> str:
    window = kraken_window(window)
    # Request one preceding bucket as well; never rely on since being inclusive.
    query = urlencode({"pair": PAIRS[window.product_id][0],
                       "interval": window.granularity_seconds // 60,
                       "since": max(0, _seconds(window.start) - window.granularity_seconds)})
    return "https://api.kraken.com/0/public/OHLC?" + query


@dataclass(frozen=True, slots=True)
class KrakenCandleSnapshot:
    window: CryptoCandleWindow
    fetched_at: datetime
    raw_json: bytes = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "window", kraken_window(self.window))
        aware("fetched_at", self.fetched_at)
        hard_flags(self)
        if type(self.raw_json) is not bytes or not 1 <= len(self.raw_json) <= MAX_KRAKEN_BYTES:
            raise ValueError("invalid Kraken response size or type")

    @property
    def content_sha256(self) -> str:
        return sha256(self.raw_json).hexdigest()


def kraken_source_id(window: CryptoCandleWindow, fetched_at: datetime, digest: str) -> str:
    binding = json.dumps([kraken_reference(window), fetched_at.astimezone(UTC).isoformat(), digest],
                         separators=(",", ":"), ensure_ascii=True).encode()
    return "kraken-candles-" + sha256(binding).hexdigest()


class KrakenCandleRejected(ValueError):
    """Closed, redacted content-failure code, not raw provider error text."""

    def __init__(self, reason: str) -> None:
        if reason not in KRAKEN_REASONS:
            raise ValueError("unknown Kraken rejection reason")
        super().__init__(reason)


def _decimal_string(value: object, *, zero: bool = False) -> Decimal:
    if (type(value) is not str or len(value) > 64
            or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is None):
        raise ValueError("expected bounded decimal string")
    # Share numerical bounds with Coinbase, but not its wire format or origin.
    return _number(Decimal(value), volume=zero)


def _closed_rows(snapshot: KrakenCandleSnapshot) -> tuple[tuple[tuple, ...], int]:
    payload = strict_json(
        snapshot.raw_json.decode("utf-8"))
    if type(payload) is not dict or type(payload.get("error")) is not list:
        raise ValueError("invalid Kraken envelope")
    if payload["error"]:
        raise KrakenCandleRejected("kraken_api_error")
    result = payload.get("result")
    key = PAIRS[snapshot.window.product_id][1]
    if type(result) is not dict or set(result) != {key, "last"}:
        raise KrakenCandleRejected("kraken_pair_mismatch")
    integer("last cursor", result["last"], 0, 253402300799)
    raw_rows = result[key]
    if type(raw_rows) is not list or not 1 <= len(raw_rows) <= 720:
        raise ValueError("invalid Kraken row count")
    rows, counts = [], []
    for row in raw_rows:
        if type(row) is not list or len(row) != 8:
            raise ValueError("expected eight Kraken OHLC columns")
        stamp = row[0]
        integer("bucket start", stamp, 0, 253402300799)
        if stamp % snapshot.window.granularity_seconds:
            raise ValueError("unaligned Kraken bucket")
        opening, high, low, closing = (_decimal_string(value) for value in row[1:5])
        vwap, volume = (_decimal_string(value, zero=True) for value in row[5:7])
        count = row[7]
        integer("trade count", count, 0, 1000000000000)
        if not low <= min(opening, closing) <= max(opening, closing) <= high:
            raise ValueError("inconsistent Kraken OHLC")
        if (count == 0 and volume != 0) or (count > 0 and (volume <= 0 or vwap <= 0)):
            raise ValueError("inconsistent Kraken trade activity")
        rows.append((stamp, low, high, opening, closing, volume))
        counts.append(count)
    stamps = [row[0] for row in rows]
    if len(set(stamps)) != len(stamps):
        raise KrakenCandleRejected("duplicate_kraken_bucket")
    if stamps != sorted(stamps):
        raise ValueError("Kraken rows must retain chronological ordering")
    expected = set(range(_seconds(snapshot.window.start), _seconds(snapshot.window.end),
                         snapshot.window.granularity_seconds))
    # The API's final row is always uncommitted. Drop it even if its timestamp
    # appears closed relative to capture time (boundary race / stale response).
    selected = tuple(row for row in rows[:-1] if row[0] in expected)
    if {row[0] for row in selected} != expected:
        raise KrakenCandleRejected("kraken_window_incomplete")
    if any(count == 0 for row, count in zip(rows[:-1], counts[:-1], strict=True) if row[0] in expected):
        raise KrakenCandleRejected("kraken_empty_bucket")
    return selected, len(rows) - len(selected)


def _prepare_kraken_evidence(snapshot: KrakenCandleSnapshot, *, team_id: str,
                             condition_id: str) -> tuple[ResearchEvidence, tuple[tuple, ...], int]:
    """Internal decoder. The cross-source gate owns as-of and capture checks."""
    _scope(team_id, condition_id, snapshot.window)
    try:
        rows, excluded = _closed_rows(snapshot)
    except KrakenCandleRejected:
        raise
    except (ValueError, TypeError, UnicodeError, ArithmeticError, RecursionError):
        raise KrakenCandleRejected("invalid_kraken_payload") from None
    window = snapshot.window
    body = json.dumps({
        "provider": "kraken", "product_id": window.product_id, "price_currency": "USD",
        "volume_currency": window.product_id.split("-")[0],
        "window_start": window.start.isoformat(), "window_end_exclusive": window.end.isoformat(),
        "granularity_seconds": window.granularity_seconds,
        "fetched_at": snapshot.fetched_at.astimezone(UTC).isoformat(),
        "raw_content_sha256": snapshot.content_sha256,
        "columns": ["bucket_start_unix", "low", "high", "open", "close", "volume"],
        "candles": [[row[0], *(format(value, "f") for value in row[1:])] for row in rows],
        "limitations": "Single-venue spot observations; correlated with other venues, not an independent probability or oracle.",
    }, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(body) > 12000:
        raise KrakenCandleRejected("kraken_evidence_too_large")
    evidence = ResearchEvidence(kraken_source_id(window, snapshot.fetched_at, snapshot.content_sha256),
        team_id, condition_id, f"Kraken {window.product_id} closed spot candles", body,
        kraken_reference(window), window.end)
    return evidence, rows, excluded


__all__ = ("KrakenCandleSnapshot", "SHARED_GRANULARITIES")
