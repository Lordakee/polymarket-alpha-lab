"""Paper-only book-imbalance forecast provider reports.

This is an additional paper-only / report-only forecast primitive whose
``fair_probability_yes`` is derived from YES order-book depth imbalance. It
produces a non-zero, explainable edge where the naive baseline (``yes_ask``)
produces exactly zero. It does NOT fetch data, authenticate, handle wallets or
credentials, place orders, rank investments, recommend trades, or give
financial advice. ``no_book`` is accepted for signature parity with the naive
provider but is unused by the v0 nudge math (flagged for future cross-side
sanity checks).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.domain import NormalizedMarket, OrderBookSnapshot


__all__ = (
    "PaperBookImbalanceForecastConfig",
    "PaperBookImbalanceForecast",
    "PaperBookImbalanceForecastLog",
    "build_paper_book_imbalance_forecast",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NEG_ONE = Decimal("-1")
COST_QUANTUM = Decimal("0.000001")

BASIS_VALUES = ("book_imbalance_v0",)


@dataclass(frozen=True)
class PaperBookImbalanceForecastConfig:
    """Configuration for the book-imbalance forecast model."""

    config_version: str
    imbalance_strength: Decimal = Decimal("0.0200")
    max_nudge: Decimal = Decimal("0.0500")
    min_book_depth: Decimal = Decimal("1.0000")
    low_confidence_value: Decimal = Decimal("0.5000")
    high_confidence_value: Decimal = Decimal("0.7500")
    max_spread_for_high_confidence: Decimal = Decimal("0.0300")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_decimal("imbalance_strength", self.imbalance_strength)
        _require_positive_decimal("max_nudge", self.max_nudge)
        _require_positive_decimal("min_book_depth", self.min_book_depth)
        _require_probability_decimal("low_confidence_value", self.low_confidence_value)
        _require_probability_decimal("high_confidence_value", self.high_confidence_value)
        _require_nonnegative_decimal(
            "max_spread_for_high_confidence",
            self.max_spread_for_high_confidence,
        )


@dataclass(frozen=True)
class PaperBookImbalanceForecast:
    """A paper-only / report-only book-imbalance forecast for one market."""

    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal
    confidence: Decimal
    basis: str
    yes_best_ask: Decimal | None
    yes_bid_size: Decimal | None
    yes_ask_size: Decimal | None
    imbalance: Decimal | None
    nudge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_finite_decimal("fair_probability_yes", self.fair_probability_yes)
        object.__setattr__(
            self,
            "fair_probability_yes",
            _quantize(self.fair_probability_yes),
        )
        _require_probability_decimal("fair_probability_yes", self.fair_probability_yes)
        _require_finite_decimal("confidence", self.confidence)
        object.__setattr__(self, "confidence", _quantize(self.confidence))
        _require_probability_decimal("confidence", self.confidence)
        _require_canonical_string("basis", self.basis)
        if self.basis not in BASIS_VALUES:
            raise ValueError("basis must be a known paper forecast basis")
        _require_optional_price_decimal("yes_best_ask", self.yes_best_ask)
        _require_optional_nonnegative_decimal("yes_bid_size", self.yes_bid_size)
        _require_optional_nonnegative_decimal("yes_ask_size", self.yes_ask_size)
        _require_optional_imbalance_decimal("imbalance", self.imbalance)
        _require_signed_finite_decimal("nudge", self.nudge)
        object.__setattr__(self, "nudge", _quantize(self.nudge))
        if self.imbalance is not None:
            object.__setattr__(self, "imbalance", _quantize(self.imbalance))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


@dataclass(frozen=True)
class PaperBookImbalanceForecastLog:
    """Append-only JSONL log for book-imbalance forecast reports."""

    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, forecast: PaperBookImbalanceForecast) -> None:
        if not isinstance(forecast, PaperBookImbalanceForecast):
            raise ValueError("forecast must be a PaperBookImbalanceForecast")
        _validate_report_tree(forecast)
        line = (
            json.dumps(_json_ready(asdict(forecast)), allow_nan=False, sort_keys=True)
            + "\n"
        )
        path = _normalize_log_path(self.path)
        _validate_log_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_book_imbalance_forecast(
    market: NormalizedMarket,
    yes_book: OrderBookSnapshot,
    no_book: OrderBookSnapshot,
    *,
    config: PaperBookImbalanceForecastConfig,
    generated_at: datetime,
) -> PaperBookImbalanceForecast:
    """Build a paper-only book-imbalance forecast from caller-supplied books.

    ``no_book`` is accepted for signature parity with the naive provider and for
    future cross-side sanity checks; it is NOT used by the v0 nudge math.
    """
    if not isinstance(market, NormalizedMarket):
        raise ValueError("market must be a NormalizedMarket")
    if not isinstance(yes_book, OrderBookSnapshot):
        raise ValueError("yes_book must be an OrderBookSnapshot")
    if not isinstance(no_book, OrderBookSnapshot):
        raise ValueError("no_book must be an OrderBookSnapshot")
    if not isinstance(config, PaperBookImbalanceForecastConfig):
        raise ValueError("config must be a PaperBookImbalanceForecastConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    yes_best_ask = yes_book.asks[0].price if yes_book.asks else None
    yes_best_bid = yes_book.bids[0].price if yes_book.bids else None
    yes_bid_size = yes_book.bids[0].size if yes_book.bids else None
    yes_ask_size = yes_book.asks[0].size if yes_book.asks else None

    bid_size = yes_bid_size if yes_bid_size is not None else ZERO
    ask_size = yes_ask_size if yes_ask_size is not None else ZERO

    total = bid_size + ask_size
    # I2 (audit reproducibility): quantize imbalance FIRST, then derive the
    # nudge from the quantized value so the whole chain is reconstructable from
    # the stored audit fields.
    imbalance = _quantize((bid_size - ask_size) / total) if total > 0 else None

    reason_codes: list[str] = []
    if yes_best_ask is None or imbalance is None:
        fair_probability_yes = config.low_confidence_value
        nudge = ZERO
        reason_codes.append("missing_yes_ask_or_depth")
    else:
        raw_nudge = imbalance * config.imbalance_strength
        nudge = _clamp_signed(raw_nudge, -config.max_nudge, config.max_nudge)
        fair_probability_yes = _clamp(yes_best_ask + nudge, ZERO, ONE)
        reason_codes.append("book_imbalance_nudge")

    spread = (
        yes_best_ask - yes_best_bid
        if yes_best_ask is not None and yes_best_bid is not None
        else None
    )
    deep_and_tight = (
        ask_size >= config.min_book_depth
        and bid_size >= config.min_book_depth
        and spread is not None
        and spread <= config.max_spread_for_high_confidence
    )
    confidence = (
        config.high_confidence_value if deep_and_tight else config.low_confidence_value
    )
    reason_codes.append(
        "high_confidence_book" if deep_and_tight else "low_confidence_book",
    )

    return PaperBookImbalanceForecast(
        generated_at=generated_at,
        config_version=config.config_version,
        market_slug=market.market.market_slug,
        question=market.market.question,
        fair_probability_yes=fair_probability_yes,
        confidence=confidence,
        basis="book_imbalance_v0",
        yes_best_ask=yes_best_ask,
        yes_bid_size=yes_bid_size,
        yes_ask_size=yes_ask_size,
        imbalance=imbalance,
        nudge=nudge,
        reason_codes=tuple(reason_codes),
        paper_only=True,
        report_only=True,
    )


def _clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    _require_finite_decimal("clamp", value)
    clamped = low if value < low else high if value > high else value
    return clamped.quantize(COST_QUANTUM)


def _clamp_signed(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    _require_finite_decimal("clamp_signed", value)
    clamped = low if value < low else high if value > high else value
    return clamped.quantize(COST_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    _require_finite_decimal("quantize", value)
    return value.quantize(COST_QUANTUM)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_price_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_optional_imbalance_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)
        if value < NEG_ONE or value > ONE:
            raise ValueError(f"{field_name} must be between -1 and 1")


def _require_signed_finite_decimal(field_name: str, value: Decimal) -> None:
    """Validate a signed (possibly negative) finite Decimal.

    ``nudge`` is signed: a bid-heavy book nudges fair value up (positive) and an
    ask-heavy book nudges it down (negative). A nonnegative check would wrongly
    reject legitimate negative nudges, so this uses a plain finite check.
    """
    _require_finite_decimal(field_name, value)


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _validate_report_tree(forecast: PaperBookImbalanceForecast) -> None:
    PaperBookImbalanceForecast(
        generated_at=forecast.generated_at,
        config_version=forecast.config_version,
        market_slug=forecast.market_slug,
        question=forecast.question,
        fair_probability_yes=forecast.fair_probability_yes,
        confidence=forecast.confidence,
        basis=forecast.basis,
        yes_best_ask=forecast.yes_best_ask,
        yes_bid_size=forecast.yes_bid_size,
        yes_ask_size=forecast.yes_ask_size,
        imbalance=forecast.imbalance,
        nudge=forecast.nudge,
        reason_codes=forecast.reason_codes,
        paper_only=forecast.paper_only,
        report_only=forecast.report_only,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
