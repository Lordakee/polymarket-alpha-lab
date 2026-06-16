"""Paper-only cost-aware snapshot builder reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.domain import NormalizedMarket, OrderBookSnapshot
from polymarket_alpha_lab.forecast_provider import PaperForecast
from polymarket_alpha_lab.cost_aware_event_strategy import PaperCostAwareEventMarketSnapshot


__all__ = (
    "PaperCostAwareSnapshotConfig",
    "PaperCostAwareSnapshotAttempt",
    "PaperCostAwareSnapshotLog",
    "build_paper_cost_aware_event_market_snapshot",
)


ZERO = Decimal("0")
COST_QUANTUM = Decimal("0.000001")

YES_NAMES = {"yes", "true", "long"}
NO_NAMES = {"no", "false", "short"}
SNAPSHOT_STATUSES = (
    "snapshot_ready",
    "blocked_missing_yes_book",
    "blocked_missing_no_book",
    "blocked_non_binary_market",
    "blocked_unresolvable_outcome_pair",
    "blocked_book_token_mismatch",
    "blocked_missing_forecast",
)


@dataclass(frozen=True)
class PaperCostAwareSnapshotConfig:
    config_version: str
    default_resolution_risk: Decimal = Decimal("0.1000")
    missing_rules_resolution_risk: Decimal = Decimal("0.3000")
    imminent_resolution_risk_cap: Decimal = Decimal("0.0500")
    imminent_resolution_horizon_hours: int = 24

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("default_resolution_risk", self.default_resolution_risk)
        _require_nonnegative_decimal(
            "missing_rules_resolution_risk",
            self.missing_rules_resolution_risk,
        )
        _require_nonnegative_decimal(
            "imminent_resolution_risk_cap",
            self.imminent_resolution_risk_cap,
        )
        _require_positive_int(
            "imminent_resolution_horizon_hours",
            self.imminent_resolution_horizon_hours,
        )


@dataclass(frozen=True)
class PaperCostAwareSnapshotAttempt:
    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    status: str
    snapshot: PaperCostAwareEventMarketSnapshot | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.status not in SNAPSHOT_STATUSES:
            raise ValueError("status must be a known cost-aware snapshot status")
        if self.status == "snapshot_ready":
            if not isinstance(self.snapshot, PaperCostAwareEventMarketSnapshot):
                raise ValueError("snapshot must be a PaperCostAwareEventMarketSnapshot")
        elif self.snapshot is not None:
            raise ValueError("snapshot must be None unless status is snapshot_ready")
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
class PaperCostAwareSnapshotLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, attempt: PaperCostAwareSnapshotAttempt) -> None:
        if not isinstance(attempt, PaperCostAwareSnapshotAttempt):
            raise ValueError("attempt must be a PaperCostAwareSnapshotAttempt")
        _validate_report_tree(attempt)
        line = json.dumps(_json_ready(asdict(attempt)), allow_nan=False, sort_keys=True) + "\n"
        path = _normalize_log_path(self.path)
        _validate_log_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_cost_aware_event_market_snapshot(
    market: NormalizedMarket,
    yes_book: OrderBookSnapshot,
    no_book: OrderBookSnapshot,
    forecast: PaperForecast,
    *,
    config: PaperCostAwareSnapshotConfig,
    generated_at: datetime,
) -> PaperCostAwareSnapshotAttempt:
    if not isinstance(market, NormalizedMarket):
        raise ValueError("market must be a NormalizedMarket")
    if not isinstance(yes_book, OrderBookSnapshot):
        raise ValueError("yes_book must be an OrderBookSnapshot")
    if not isinstance(no_book, OrderBookSnapshot):
        raise ValueError("no_book must be an OrderBookSnapshot")
    if not isinstance(forecast, PaperForecast):
        raise ValueError("forecast must be a PaperForecast")
    if not isinstance(config, PaperCostAwareSnapshotConfig):
        raise ValueError("config must be a PaperCostAwareSnapshotConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    if len(market.tokens) != 2:
        return _blocked_attempt(
            market,
            config,
            generated_at,
            status="blocked_non_binary_market",
            reason_codes=("non_binary_market",),
        )

    yes_token = next(
        (
            token
            for token in market.tokens
            if token.outcome_name.strip().lower() in YES_NAMES
        ),
        None,
    )
    no_token = next(
        (
            token
            for token in market.tokens
            if token.outcome_name.strip().lower() in NO_NAMES
        ),
        None,
    )
    if yes_token is None or no_token is None:
        indexed_tokens = {token.outcome_index: token for token in market.tokens}
        yes_token = yes_token or indexed_tokens.get(0)
        no_token = no_token or indexed_tokens.get(1)
    if yes_token is None or no_token is None or yes_token.token_id == no_token.token_id:
        return _blocked_attempt(
            market,
            config,
            generated_at,
            status="blocked_unresolvable_outcome_pair",
            reason_codes=("unresolvable_outcome_pair",),
        )

    if yes_book.token_id != yes_token.token_id or no_book.token_id != no_token.token_id:
        return _blocked_attempt(
            market,
            config,
            generated_at,
            status="blocked_book_token_mismatch",
            reason_codes=("book_token_mismatch",),
        )

    yes_ask = yes_book.asks[0] if yes_book.asks else None
    yes_bid = yes_book.bids[0] if yes_book.bids else None
    no_ask = no_book.asks[0] if no_book.asks else None
    no_bid = no_book.bids[0] if no_book.bids else None

    yes_ask_price = yes_ask.price if yes_ask else None
    yes_ask_size = yes_ask.size if yes_ask else None
    yes_bid_price = yes_bid.price if yes_bid else None
    no_ask_price = no_ask.price if no_ask else None
    no_ask_size = no_ask.size if no_ask else None
    no_bid_price = no_bid.price if no_bid else None

    spread = _spread(
        yes_ask_price=yes_ask_price,
        yes_bid_price=yes_bid_price,
        no_ask_price=no_ask_price,
        no_bid_price=no_bid_price,
    )
    resolution_risk = _resolution_risk(market, config, generated_at)

    snapshot = PaperCostAwareEventMarketSnapshot(
        market_slug=market.market.market_slug,
        question=market.market.question,
        fair_probability_yes=forecast.fair_probability_yes,
        confidence=forecast.confidence,
        yes_bid=yes_bid_price,
        yes_ask=yes_ask_price,
        yes_ask_size=yes_ask_size,
        no_bid=no_bid_price,
        no_ask=no_ask_price,
        no_ask_size=no_ask_size,
        spread=spread,
        resolution_risk=resolution_risk,
    )
    return PaperCostAwareSnapshotAttempt(
        generated_at=generated_at,
        config_version=config.config_version,
        market_slug=market.market.market_slug,
        question=market.market.question,
        status="snapshot_ready",
        snapshot=snapshot,
        reason_codes=("snapshot_built",),
    )


def _blocked_attempt(
    market: NormalizedMarket,
    config: PaperCostAwareSnapshotConfig,
    generated_at: datetime,
    *,
    status: str,
    reason_codes: tuple[str, ...],
) -> PaperCostAwareSnapshotAttempt:
    return PaperCostAwareSnapshotAttempt(
        generated_at=generated_at,
        config_version=config.config_version,
        market_slug=market.market.market_slug,
        question=market.market.question,
        status=status,
        snapshot=None,
        reason_codes=reason_codes,
    )


def _spread(
    *,
    yes_ask_price: Decimal | None,
    yes_bid_price: Decimal | None,
    no_ask_price: Decimal | None,
    no_bid_price: Decimal | None,
) -> Decimal:
    if yes_ask_price is not None and yes_bid_price is not None:
        return _quantize_cost(yes_ask_price - yes_bid_price)
    if no_ask_price is not None and no_bid_price is not None:
        return _quantize_cost(no_ask_price - no_bid_price)
    return _quantize_cost(ZERO)


def _resolution_risk(
    market: NormalizedMarket,
    config: PaperCostAwareSnapshotConfig,
    generated_at: datetime,
) -> Decimal:
    base = config.default_resolution_risk
    if market.rules_text is None or market.resolution_source is None:
        base = max(base, config.missing_rules_resolution_risk)
    if market.market.end_time is not None:
        # timedelta compare, not total_seconds()/3600 — project is NEVER float.
        time_to_resolution = market.market.end_time - _as_utc(generated_at)
        imminent_horizon = timedelta(hours=config.imminent_resolution_horizon_hours)
        if time_to_resolution <= imminent_horizon:
            base = min(config.imminent_resolution_risk_cap, base)
    return _quantize_cost(base)


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


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


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


def _validate_report_tree(attempt: PaperCostAwareSnapshotAttempt) -> None:
    snapshot = None
    if attempt.snapshot is not None:
        snapshot = PaperCostAwareEventMarketSnapshot(
            market_slug=attempt.snapshot.market_slug,
            question=attempt.snapshot.question,
            fair_probability_yes=attempt.snapshot.fair_probability_yes,
            confidence=attempt.snapshot.confidence,
            yes_bid=attempt.snapshot.yes_bid,
            yes_ask=attempt.snapshot.yes_ask,
            yes_ask_size=attempt.snapshot.yes_ask_size,
            no_bid=attempt.snapshot.no_bid,
            no_ask=attempt.snapshot.no_ask,
            no_ask_size=attempt.snapshot.no_ask_size,
            spread=attempt.snapshot.spread,
            resolution_risk=attempt.snapshot.resolution_risk,
        )
    PaperCostAwareSnapshotAttempt(
        generated_at=attempt.generated_at,
        config_version=attempt.config_version,
        market_slug=attempt.market_slug,
        question=attempt.question,
        status=attempt.status,
        snapshot=snapshot,
        reason_codes=attempt.reason_codes,
        paper_only=attempt.paper_only,
        report_only=attempt.report_only,
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
