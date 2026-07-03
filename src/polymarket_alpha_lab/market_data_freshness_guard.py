"""Paper-only pre-research market data quality summaries.

This module reduces caller-supplied market and book snapshot metadata into a
deterministic freshness summary. It performs no file IO, network access,
privileged secret handling, custody handling, placement actions, execution, or
investment advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from polymarket_alpha_lab.domain import MarketSnapshot


__all__ = (
    "PaperMarketDataFreshnessGuardBookRow",
    "PaperMarketDataFreshnessGuardConfig",
    "PaperMarketDataFreshnessGuardSummary",
    "build_paper_market_data_freshness_guard_summary",
)


ZERO = Decimal("0")
SEVERITY_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
ROW_STATUSES = ("pass", "watch", "blocked")
SUMMARY_STATUSES = ("pass", "watch", "blocked")


@runtime_checkable
class _BookSnapshotMetadata(Protocol):
    @property
    def token_id(self) -> str: ...

    @property
    def bids(self) -> Any: ...

    @property
    def asks(self) -> Any: ...

    @property
    def captured_at(self) -> datetime: ...


@dataclass(frozen=True)
class PaperMarketDataFreshnessGuardConfig:
    config_version: str
    max_market_snapshot_age_seconds: int
    max_book_snapshot_age_seconds: int
    min_book_count: int
    max_spread: Decimal
    min_side_depth: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int(
            "max_market_snapshot_age_seconds",
            self.max_market_snapshot_age_seconds,
        )
        _require_positive_int(
            "max_book_snapshot_age_seconds",
            self.max_book_snapshot_age_seconds,
        )
        _require_positive_int("min_book_count", self.min_book_count)
        _require_nonnegative_decimal("max_spread", self.max_spread)
        _require_nonnegative_decimal("min_side_depth", self.min_side_depth)
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperMarketDataFreshnessGuardBookRow:
    token_id: str
    captured_at: datetime
    age_seconds: Decimal
    best_bid: Decimal | None
    best_ask: Decimal | None
    spread: Decimal | None
    bid_depth: Decimal
    ask_depth: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("token_id", self.token_id)
        object.__setattr__(
            self,
            "captured_at",
            _as_utc(self.captured_at, field_name="captured_at"),
        )
        _require_nonnegative_decimal("age_seconds", self.age_seconds)
        _require_optional_nonnegative_decimal("best_bid", self.best_bid)
        _require_optional_nonnegative_decimal("best_ask", self.best_ask)
        _require_optional_nonnegative_decimal("spread", self.spread)
        _require_nonnegative_decimal("bid_depth", self.bid_depth)
        _require_nonnegative_decimal("ask_depth", self.ask_depth)
        if type(self.status) is not str or self.status not in ROW_STATUSES:
            raise ValueError("status must be a known market data freshness row status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperMarketDataFreshnessGuardSummary:
    generated_at: datetime
    config_version: str
    condition_id: str
    market_captured_at: datetime
    market_age_seconds: Decimal
    max_market_snapshot_age_seconds: int
    max_book_snapshot_age_seconds: int
    min_book_count: int
    max_spread: Decimal
    min_side_depth: Decimal
    book_count: int
    missing_book_count: int
    status: str
    reason_codes: tuple[str, ...]
    book_rows: tuple[PaperMarketDataFreshnessGuardBookRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc(self.generated_at, field_name="generated_at"),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "market_captured_at",
            _as_utc(self.market_captured_at, field_name="market_captured_at"),
        )
        _require_nonnegative_decimal("market_age_seconds", self.market_age_seconds)
        _require_positive_int(
            "max_market_snapshot_age_seconds",
            self.max_market_snapshot_age_seconds,
        )
        _require_positive_int(
            "max_book_snapshot_age_seconds",
            self.max_book_snapshot_age_seconds,
        )
        _require_positive_int("min_book_count", self.min_book_count)
        _require_nonnegative_decimal("max_spread", self.max_spread)
        _require_nonnegative_decimal("min_side_depth", self.min_side_depth)
        _require_nonnegative_int("book_count", self.book_count)
        _require_nonnegative_int("missing_book_count", self.missing_book_count)
        if type(self.status) is not str or self.status not in SUMMARY_STATUSES:
            raise ValueError("status must be a known market data freshness summary status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "book_rows", _clone_book_rows(self.book_rows))
        _validate_summary_consistency(self)
        _require_hard_flags(self)


def build_paper_market_data_freshness_guard_summary(
    market: MarketSnapshot,
    books: tuple[_BookSnapshotMetadata, ...] | list[_BookSnapshotMetadata],
    *,
    config: PaperMarketDataFreshnessGuardConfig,
    generated_at: datetime,
) -> PaperMarketDataFreshnessGuardSummary:
    if type(market) is not MarketSnapshot:
        raise ValueError("market must be a MarketSnapshot")
    if type(config) is not PaperMarketDataFreshnessGuardConfig:
        raise ValueError("config must be a PaperMarketDataFreshnessGuardConfig")
    generated_at_utc = _as_utc(generated_at, field_name="generated_at")
    market_captured_at = _as_utc(market.captured_at, field_name="market_captured_at")
    if market_captured_at > generated_at_utc:
        raise ValueError("market_captured_at must not be in the future")
    source_books = _normalize_books(books)
    book_rows = tuple(
        sorted(
            (
                _book_row_from_snapshot(
                    book,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for book in source_books
            ),
            key=lambda row: (SEVERITY_WEIGHT[row.status], row.token_id),
        ),
    )
    missing_book_count = _missing_book_count(
        book_count=len(source_books),
        min_book_count=config.min_book_count,
    )
    market_age_seconds = _age_seconds(
        market_captured_at,
        generated_at_utc,
        field_name="market_captured_at",
    )
    status = _summary_status(
        market_age_seconds=market_age_seconds,
        max_market_snapshot_age_seconds=config.max_market_snapshot_age_seconds,
        missing_book_count=missing_book_count,
        book_rows=book_rows,
    )
    return PaperMarketDataFreshnessGuardSummary(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        condition_id=market.condition_id,
        market_captured_at=market_captured_at,
        market_age_seconds=market_age_seconds,
        max_market_snapshot_age_seconds=config.max_market_snapshot_age_seconds,
        max_book_snapshot_age_seconds=config.max_book_snapshot_age_seconds,
        min_book_count=config.min_book_count,
        max_spread=config.max_spread,
        min_side_depth=config.min_side_depth,
        book_count=len(source_books),
        missing_book_count=missing_book_count,
        status=status,
        reason_codes=_summary_reason_codes(
            market_age_seconds=market_age_seconds,
            max_market_snapshot_age_seconds=config.max_market_snapshot_age_seconds,
            missing_book_count=missing_book_count,
            book_rows=book_rows,
            status=status,
        ),
        book_rows=book_rows,
    )


def _book_row_from_snapshot(
    book: _BookSnapshotMetadata,
    *,
    config: PaperMarketDataFreshnessGuardConfig,
    generated_at: datetime,
) -> PaperMarketDataFreshnessGuardBookRow:
    captured_at = _as_utc(book.captured_at, field_name="book_captured_at")
    age_seconds = _age_seconds(
        captured_at,
        generated_at,
        field_name="book_captured_at",
    )
    best_bid = _best_executable_price(book.bids, side_name="bids")
    best_ask = _best_executable_price(book.asks, side_name="asks")
    spread = _spread(best_bid=best_bid, best_ask=best_ask)
    bid_depth = _side_depth(book.bids, side_name="bids")
    ask_depth = _side_depth(book.asks, side_name="asks")
    status = _book_row_status(
        age_seconds=age_seconds,
        spread=spread,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        config=config,
    )
    return PaperMarketDataFreshnessGuardBookRow(
        token_id=book.token_id,
        captured_at=captured_at,
        age_seconds=age_seconds,
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        status=status,
        reason_codes=_book_row_reason_codes(
            age_seconds=age_seconds,
            spread=spread,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            config=config,
            status=status,
        ),
    )


def _book_row_status(
    *,
    age_seconds: Decimal,
    spread: Decimal | None,
    bid_depth: Decimal,
    ask_depth: Decimal,
    config: PaperMarketDataFreshnessGuardConfig,
) -> str:
    if age_seconds > Decimal(config.max_book_snapshot_age_seconds):
        return "blocked"
    if spread is not None and spread > config.max_spread:
        return "watch"
    if bid_depth < config.min_side_depth or ask_depth < config.min_side_depth:
        return "watch"
    return "pass"


def _book_row_reason_codes(
    *,
    age_seconds: Decimal,
    spread: Decimal | None,
    bid_depth: Decimal,
    ask_depth: Decimal,
    config: PaperMarketDataFreshnessGuardConfig,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if age_seconds > Decimal(config.max_book_snapshot_age_seconds):
        reason_codes.append("stale_book_snapshot")
    if spread is not None and spread > config.max_spread:
        reason_codes.append("wide_spread")
    if bid_depth < config.min_side_depth or ask_depth < config.min_side_depth:
        reason_codes.append("thin_depth")
    if not reason_codes and status == "pass":
        reason_codes.append("fresh_book_snapshot")
    return tuple(reason_codes)


def _summary_status(
    *,
    market_age_seconds: Decimal,
    max_market_snapshot_age_seconds: int,
    missing_book_count: int,
    book_rows: tuple[PaperMarketDataFreshnessGuardBookRow, ...],
) -> str:
    if market_age_seconds > Decimal(max_market_snapshot_age_seconds):
        return "blocked"
    if missing_book_count > 0:
        return "blocked"
    if any(row.status == "blocked" for row in book_rows):
        return "blocked"
    if any(row.status == "watch" for row in book_rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    *,
    market_age_seconds: Decimal,
    max_market_snapshot_age_seconds: int,
    missing_book_count: int,
    book_rows: tuple[PaperMarketDataFreshnessGuardBookRow, ...],
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if market_age_seconds > Decimal(max_market_snapshot_age_seconds):
        reason_codes.append("stale_market_snapshot")
    if missing_book_count > 0:
        reason_codes.append("missing_book")
    for candidate in ("stale_book_snapshot", "wide_spread", "thin_depth"):
        if any(candidate in row.reason_codes for row in book_rows):
            reason_codes.append(candidate)
    if not reason_codes and status == "pass":
        reason_codes.append("market_data_fresh")
    return tuple(reason_codes)


def _missing_book_count(*, book_count: int, min_book_count: int) -> int:
    missing = min_book_count - book_count
    if missing <= 0:
        return 0
    return missing


def _normalize_books(
    books: tuple[_BookSnapshotMetadata, ...] | list[_BookSnapshotMetadata],
) -> tuple[_BookSnapshotMetadata, ...]:
    if isinstance(books, (str, bytes)) or type(books) not in (list, tuple):
        raise ValueError("books must be a list or tuple")
    items = tuple(books)
    for item in items:
        if not isinstance(item, _BookSnapshotMetadata):
            raise ValueError("books must contain book snapshot metadata values")
        _require_canonical_string("token_id", item.token_id)
    return items


def _clone_book_rows(
    rows: tuple[PaperMarketDataFreshnessGuardBookRow, ...],
) -> tuple[PaperMarketDataFreshnessGuardBookRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("book_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("book_rows must be an iterable") from exc
    for item in items:
        if type(item) is not PaperMarketDataFreshnessGuardBookRow:
            raise ValueError(
                "book_rows must contain PaperMarketDataFreshnessGuardBookRow values",
            )
    return tuple(
        PaperMarketDataFreshnessGuardBookRow(
            token_id=row.token_id,
            captured_at=row.captured_at,
            age_seconds=row.age_seconds,
            best_bid=row.best_bid,
            best_ask=row.best_ask,
            spread=row.spread,
            bid_depth=row.bid_depth,
            ask_depth=row.ask_depth,
            status=row.status,
            reason_codes=row.reason_codes,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )
        for row in items
    )


def _validate_summary_consistency(
    summary: PaperMarketDataFreshnessGuardSummary,
) -> None:
    if summary.book_count != len(summary.book_rows):
        raise ValueError("book_count must match book_rows")
    expected_missing = _missing_book_count(
        book_count=summary.book_count,
        min_book_count=summary.min_book_count,
    )
    if summary.missing_book_count != expected_missing:
        raise ValueError("missing_book_count must match min_book_count and book_count")
    expected_market_age = _age_seconds(
        summary.market_captured_at,
        summary.generated_at,
        field_name="market_captured_at",
    )
    if summary.market_age_seconds != expected_market_age:
        raise ValueError("market_age_seconds must match market_captured_at")
    for row in summary.book_rows:
        expected_status = _book_row_status(
            age_seconds=row.age_seconds,
            spread=row.spread,
            bid_depth=row.bid_depth,
            ask_depth=row.ask_depth,
            config=PaperMarketDataFreshnessGuardConfig(
                config_version=summary.config_version,
                max_market_snapshot_age_seconds=summary.max_market_snapshot_age_seconds,
                max_book_snapshot_age_seconds=summary.max_book_snapshot_age_seconds,
                min_book_count=summary.min_book_count,
                max_spread=summary.max_spread,
                min_side_depth=summary.min_side_depth,
            ),
        )
        if row.status != expected_status:
            raise ValueError("book row status must match row metrics")
    expected_status = _summary_status(
        market_age_seconds=summary.market_age_seconds,
        max_market_snapshot_age_seconds=summary.max_market_snapshot_age_seconds,
        missing_book_count=summary.missing_book_count,
        book_rows=summary.book_rows,
    )
    if summary.status != expected_status:
        raise ValueError("status must match market data freshness state")
    expected_reason_codes = _summary_reason_codes(
        market_age_seconds=summary.market_age_seconds,
        max_market_snapshot_age_seconds=summary.max_market_snapshot_age_seconds,
        missing_book_count=summary.missing_book_count,
        book_rows=summary.book_rows,
        status=summary.status,
    )
    if summary.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match market data freshness state")
    row_keys = tuple((SEVERITY_WEIGHT[row.status], row.token_id) for row in summary.book_rows)
    if row_keys != tuple(sorted(row_keys)):
        raise ValueError("book_rows must use deterministic severity and token sorting")


def _best_executable_price(levels: Any, *, side_name: str) -> Decimal | None:
    for level in _normalize_levels(levels, side_name=side_name):
        if level.price > ZERO and level.size > ZERO:
            return level.price
    return None


def _side_depth(levels: Any, *, side_name: str) -> Decimal:
    depth = ZERO
    for level in _normalize_levels(levels, side_name=side_name):
        if level.price > ZERO and level.size > ZERO:
            depth += level.size
    return depth


def _normalize_levels(levels: Any, *, side_name: str) -> tuple[Any, ...]:
    if isinstance(levels, (str, bytes)):
        raise ValueError(f"{side_name} must be an iterable")
    try:
        items = tuple(levels)
    except TypeError as exc:
        raise ValueError(f"{side_name} must be an iterable") from exc
    for level in items:
        try:
            price = level.price
            size = level.size
        except AttributeError as exc:
            raise ValueError(f"{side_name} must contain price and size metadata") from exc
        _require_nonnegative_decimal("price", price)
        _require_nonnegative_decimal("size", size)
    return items


def _spread(*, best_bid: Decimal | None, best_ask: Decimal | None) -> Decimal | None:
    if best_bid is None or best_ask is None:
        return None
    if best_ask <= best_bid:
        return None
    return best_ask - best_bid


def _age_seconds(captured_at: datetime, generated_at: datetime, *, field_name: str) -> Decimal:
    if captured_at > generated_at:
        raise ValueError(f"{field_name} must not be in the future")
    delta = generated_at - captured_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _as_utc(value: datetime, *, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_hard_flags(value: Any) -> None:
    if value.paper_only is not True:
        raise ValueError("paper_only must be True")
    if value.report_only is not True:
        raise ValueError("report_only must be True")
    if value.readonly is not True:
        raise ValueError("readonly must be True")
