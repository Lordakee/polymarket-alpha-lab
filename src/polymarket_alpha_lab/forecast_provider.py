"""Paper-only naive forecast provider reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.domain import NormalizedMarket, OrderBookSnapshot


__all__ = (
    "PaperForecastConfig",
    "PaperForecast",
    "PaperForecastLog",
    "build_paper_naive_forecast",
)


ZERO = Decimal("0")
ONE = Decimal("1")
COST_QUANTUM = Decimal("0.000001")

BASIS_VALUES = ("yes_ask_naive_v0",)


@dataclass(frozen=True)
class PaperForecastConfig:
    config_version: str
    min_book_depth: Decimal = Decimal("1.0000")
    low_confidence_value: Decimal = Decimal("0.5000")
    high_confidence_value: Decimal = Decimal("0.7500")
    max_spread_for_high_confidence: Decimal = Decimal("0.0300")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_decimal("min_book_depth", self.min_book_depth)
        _require_probability_decimal("low_confidence_value", self.low_confidence_value)
        _require_probability_decimal("high_confidence_value", self.high_confidence_value)
        _require_nonnegative_decimal(
            "max_spread_for_high_confidence",
            self.max_spread_for_high_confidence,
        )


@dataclass(frozen=True)
class PaperForecast:
    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal
    confidence: Decimal
    basis: str
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
            _quantize_cost(self.fair_probability_yes),
        )
        _require_probability_decimal("fair_probability_yes", self.fair_probability_yes)
        _require_finite_decimal("confidence", self.confidence)
        object.__setattr__(self, "confidence", _quantize_cost(self.confidence))
        _require_probability_decimal("confidence", self.confidence)
        _require_canonical_string("basis", self.basis)
        if self.basis not in BASIS_VALUES:
            raise ValueError("basis must be a known paper forecast basis")
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
class PaperForecastLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperForecast) -> None:
        if not isinstance(report, PaperForecast):
            raise ValueError("report must be a PaperForecast")
        _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"
        path = _normalize_log_path(self.path)
        _validate_log_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_naive_forecast(
    market: NormalizedMarket,
    yes_book: OrderBookSnapshot,
    no_book: OrderBookSnapshot,
    *,
    config: PaperForecastConfig,
    generated_at: datetime,
) -> PaperForecast:
    if not isinstance(market, NormalizedMarket):
        raise ValueError("market must be a NormalizedMarket")
    if not isinstance(yes_book, OrderBookSnapshot):
        raise ValueError("yes_book must be an OrderBookSnapshot")
    if not isinstance(no_book, OrderBookSnapshot):
        raise ValueError("no_book must be an OrderBookSnapshot")
    if not isinstance(config, PaperForecastConfig):
        raise ValueError("config must be a PaperForecastConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    yes_best_ask = yes_book.asks[0].price if yes_book.asks else None
    yes_best_bid = yes_book.bids[0].price if yes_book.bids else None
    yes_ask_depth = yes_book.asks[0].size if yes_book.asks else ZERO
    spread = (
        yes_best_ask - yes_best_bid
        if yes_best_ask is not None and yes_best_bid is not None
        else None
    )
    deep_and_tight = (
        yes_ask_depth >= config.min_book_depth
        and spread is not None
        and spread <= config.max_spread_for_high_confidence
    )

    if yes_best_ask is None:
        fair_probability_yes = config.low_confidence_value
        reason_codes = ("missing_yes_ask", "low_confidence_book")
    else:
        fair_probability_yes = _clamp_probability(yes_best_ask)
        reason_codes = (
            "yes_ask_basis",
            "high_confidence_book" if deep_and_tight else "low_confidence_book",
        )
    confidence = (
        config.high_confidence_value if deep_and_tight else config.low_confidence_value
    )

    return PaperForecast(
        generated_at=generated_at,
        config_version=config.config_version,
        market_slug=market.market.market_slug,
        question=market.market.question,
        fair_probability_yes=fair_probability_yes,
        confidence=confidence,
        basis="yes_ask_naive_v0",
        reason_codes=reason_codes,
    )


def _clamp_probability(value: Decimal) -> Decimal:
    _require_finite_decimal("fair_probability_yes", value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


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


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


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


def _quantize_cost(value: Decimal) -> Decimal:
    _require_finite_decimal("cost", value)
    return value.quantize(COST_QUANTUM)


def _validate_report_tree(report: PaperForecast) -> None:
    PaperForecast(
        generated_at=report.generated_at,
        config_version=report.config_version,
        market_slug=report.market_slug,
        question=report.question,
        fair_probability_yes=report.fair_probability_yes,
        confidence=report.confidence,
        basis=report.basis,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
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
