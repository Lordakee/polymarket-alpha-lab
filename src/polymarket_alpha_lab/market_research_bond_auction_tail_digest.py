"""Pure report-only reducer for bond auction tail research digests."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable


DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION = (
    "market-research-bond-auction-tail-digest-v0"
)

TAIL_STATUSES = ("pass", "watch", "blocked")
DIGEST_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "auction_tail_blocked",
    "auction_tail_passed",
    "auction_tail_watch",
    "low_indirect_bidder_share",
    "positive_auction_tail",
    "weak_bid_to_cover",
)
DIGEST_REASON_CODES = (
    "bond_auction_tail_digest_blocked",
    "bond_auction_tail_digest_no_inputs",
    "bond_auction_tail_digest_passed",
    "bond_auction_tail_digest_watch",
)
NEXT_STEP = "review_bond_auction_tail_risk"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION",
    "MarketResearchBondAuctionTailDigestAuction",
    "MarketResearchBondAuctionTailDigestConfig",
    "MarketResearchBondAuctionTailDigestReasonCodeCount",
    "MarketResearchBondAuctionTailDigestReport",
    "MarketResearchBondAuctionTailDigestRow",
    "build_market_research_bond_auction_tail_digest",
    "market_research_bond_auction_tail_digest_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketResearchBondAuctionTailDigestConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION
    watch_tail_bps: Decimal = Decimal("1.000000")
    blocked_tail_bps: Decimal = Decimal("3.000000")
    weak_bid_to_cover_ratio: Decimal = Decimal("2.100000")
    low_indirect_bidder_pct: Decimal = Decimal("55.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBondAuctionTailDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_tail_bps",
            "blocked_tail_bps",
            "weak_bid_to_cover_ratio",
            "low_indirect_bidder_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_measure_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_tail_bps < Decimal("0"):
            raise ValueError("watch_tail_bps must be nonnegative")
        if self.blocked_tail_bps < self.watch_tail_bps:
            raise ValueError("blocked_tail_bps must cover watch_tail_bps")
        if self.weak_bid_to_cover_ratio <= Decimal("0"):
            raise ValueError("weak_bid_to_cover_ratio must be positive")
        _require_percentage("low_indirect_bidder_pct", self.low_indirect_bidder_pct)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBondAuctionTailDigestAuction(_FinalPublicDataclass):
    auction_id: str
    security_term: str
    auctioned_at: datetime
    tail_bps: Decimal
    bid_to_cover_ratio: Decimal
    indirect_bidder_pct: Decimal
    high_yield_pct: Decimal
    when_issued_yield_pct: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBondAuctionTailDigestAuction, "auction")
        _normalize_auction_fields(self)
        _validate_tail_yield_link(self)
        _require_hard_flags("auction", self)


@dataclass(frozen=True)
class MarketResearchBondAuctionTailDigestRow(_FinalPublicDataclass):
    auction_id: str
    security_term: str
    auctioned_at: datetime
    tail_bps: Decimal
    bid_to_cover_ratio: Decimal
    indirect_bidder_pct: Decimal
    high_yield_pct: Decimal
    when_issued_yield_pct: Decimal
    tail_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBondAuctionTailDigestRow, "row")
        _normalize_auction_fields(self)
        _validate_tail_yield_link(self)
        _require_tail_status("tail_status", self.tail_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBondAuctionTailDigestReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBondAuctionTailDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_count_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        if self.count <= Decimal("0"):
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBondAuctionTailDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    digest_next_step: str
    auction_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    tail_event_count: Decimal
    weak_demand_count: Decimal
    low_indirect_bidder_count: Decimal
    max_tail_bps: Decimal
    average_tail_bps: Decimal
    average_bid_to_cover_ratio: Decimal
    tail_event_ratio: Decimal
    rows: tuple[MarketResearchBondAuctionTailDigestRow, ...]
    reason_code_counts: tuple[MarketResearchBondAuctionTailDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBondAuctionTailDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("digest_next_step", self.digest_next_step)
        for field_name in (
            "auction_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "tail_event_count",
            "weak_demand_count",
            "low_indirect_bidder_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_tail_bps",
            "average_tail_bps",
            "average_bid_to_cover_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_measure_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "tail_event_ratio",
            _normalize_ratio_decimal("tail_event_ratio", self.tail_event_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_digest_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchBondAuctionTailDigestConfig,
    MarketResearchBondAuctionTailDigestAuction,
    MarketResearchBondAuctionTailDigestRow,
    MarketResearchBondAuctionTailDigestReasonCodeCount,
    MarketResearchBondAuctionTailDigestReport,
)


def build_market_research_bond_auction_tail_digest(
    auctions: Iterable[MarketResearchBondAuctionTailDigestAuction],
    *,
    config: MarketResearchBondAuctionTailDigestConfig,
    generated_at: datetime,
) -> MarketResearchBondAuctionTailDigestReport:
    if type(config) is not MarketResearchBondAuctionTailDigestConfig:
        raise ValueError("config must be a MarketResearchBondAuctionTailDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_auctions = _normalize_auctions(auctions)
    rows = _sorted_rows(
        _row_from_auction(auction, config=config) for auction in normalized_auctions
    )
    reason_codes = _digest_reason_codes(rows)
    return MarketResearchBondAuctionTailDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(reason_codes),
        digest_next_step=NEXT_STEP,
        auction_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        tail_event_count=_reason_row_count(rows, "positive_auction_tail"),
        weak_demand_count=_reason_row_count(rows, "weak_bid_to_cover"),
        low_indirect_bidder_count=_reason_row_count(rows, "low_indirect_bidder_share"),
        max_tail_bps=_max_tail_bps(rows),
        average_tail_bps=_average_measure(row.tail_bps for row in rows),
        average_bid_to_cover_ratio=_average_measure(row.bid_to_cover_ratio for row in rows),
        tail_event_ratio=_tail_event_ratio(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def market_research_bond_auction_tail_digest_payload(
    report: MarketResearchBondAuctionTailDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBondAuctionTailDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchBondAuctionTailDigestReport",
        )
    _require_payload_safe_value("report", report)
    return _payload_value(report)


def _row_from_auction(
    auction: MarketResearchBondAuctionTailDigestAuction,
    *,
    config: MarketResearchBondAuctionTailDigestConfig,
) -> MarketResearchBondAuctionTailDigestRow:
    reason_codes = _row_reason_codes(auction, config=config)
    return MarketResearchBondAuctionTailDigestRow(
        auction_id=auction.auction_id,
        security_term=auction.security_term,
        auctioned_at=auction.auctioned_at,
        tail_bps=auction.tail_bps,
        bid_to_cover_ratio=auction.bid_to_cover_ratio,
        indirect_bidder_pct=auction.indirect_bidder_pct,
        high_yield_pct=auction.high_yield_pct,
        when_issued_yield_pct=auction.when_issued_yield_pct,
        tail_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    auction: MarketResearchBondAuctionTailDigestAuction,
    *,
    config: MarketResearchBondAuctionTailDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if auction.tail_bps >= config.blocked_tail_bps:
        reason_codes.append("auction_tail_blocked")
    elif auction.tail_bps >= config.watch_tail_bps:
        reason_codes.append("auction_tail_watch")
    else:
        reason_codes.append("auction_tail_passed")
    if auction.tail_bps >= config.watch_tail_bps:
        reason_codes.append("positive_auction_tail")
    if auction.bid_to_cover_ratio < config.weak_bid_to_cover_ratio:
        reason_codes.append("weak_bid_to_cover")
    if auction.indirect_bidder_pct < config.low_indirect_bidder_pct:
        reason_codes.append("low_indirect_bidder_share")
    if reason_codes == ["auction_tail_passed"]:
        return ("auction_tail_passed",)
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "auction_tail_blocked" in reason_codes:
        return "blocked"
    if reason_codes == ("auction_tail_passed",):
        return "pass"
    return "watch"


def _digest_reason_codes(
    rows: tuple[MarketResearchBondAuctionTailDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("bond_auction_tail_digest_no_inputs",)
    if any(row.tail_status == "blocked" for row in rows):
        return ("bond_auction_tail_digest_blocked",)
    if any(row.tail_status == "watch" for row in rows):
        return ("bond_auction_tail_digest_watch",)
    return ("bond_auction_tail_digest_passed",)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("bond_auction_tail_digest_passed",):
        return "pass"
    if reason_codes == ("bond_auction_tail_digest_watch",):
        return "watch"
    return "blocked"


def _sorted_rows(
    rows: Iterable[MarketResearchBondAuctionTailDigestRow],
) -> tuple[MarketResearchBondAuctionTailDigestRow, ...]:
    status_weight = {"blocked": 0, "watch": 1, "pass": 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_weight[row.tail_status],
                -row.tail_bps,
                row.auctioned_at,
                row.auction_id,
            ),
        ),
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBondAuctionTailDigestRow, ...],
) -> tuple[MarketResearchBondAuctionTailDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchBondAuctionTailDigestReasonCodeCount(
                reason_code="bond_auction_tail_digest_no_inputs",
                count=_count_decimal(1),
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
        )
        for reason_code in sorted(counter)
    )


def _status_count(
    rows: tuple[MarketResearchBondAuctionTailDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.tail_status == status))


def _reason_row_count(
    rows: tuple[MarketResearchBondAuctionTailDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_tail_bps(rows: tuple[MarketResearchBondAuctionTailDigestRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_decimal(max(row.tail_bps for row in rows))


def _average_measure(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return _quantize_decimal(
        sum(normalized_values, ZERO) / _count_decimal(len(normalized_values)),
    )


def _tail_event_ratio(
    rows: tuple[MarketResearchBondAuctionTailDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_decimal(
        _reason_row_count(rows, "positive_auction_tail") / _count_decimal(len(rows)),
    )


def _normalize_auctions(
    value: Iterable[MarketResearchBondAuctionTailDigestAuction],
) -> tuple[MarketResearchBondAuctionTailDigestAuction, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("auctions must be an iterable")
    try:
        auctions = tuple(value)
    except TypeError as exc:
        raise ValueError("auctions must be an iterable") from exc
    for auction in auctions:
        if type(auction) is not MarketResearchBondAuctionTailDigestAuction:
            raise ValueError(
                "auctions must contain MarketResearchBondAuctionTailDigestAuction values",
            )
        _require_hard_flags("auctions", auction)
    return auctions


def _normalize_rows(
    value: tuple[MarketResearchBondAuctionTailDigestRow, ...],
) -> tuple[MarketResearchBondAuctionTailDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBondAuctionTailDigestRow:
            raise ValueError("rows must contain MarketResearchBondAuctionTailDigestRow values")
        _require_hard_flags("rows", row)
        if row.auction_id in seen_ids:
            raise ValueError("rows auction_id values must be unique")
        seen_ids.add(row.auction_id)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: tuple[MarketResearchBondAuctionTailDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBondAuctionTailDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchBondAuctionTailDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchBondAuctionTailDigestReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(sorted(seen)):
        raise ValueError("reason_code_counts must use canonical sequence")
    return counts


def _normalize_auction_fields(
    value: MarketResearchBondAuctionTailDigestAuction
    | MarketResearchBondAuctionTailDigestRow,
) -> None:
    _require_canonical_string("auction_id", value.auction_id)
    _require_canonical_string("security_term", value.security_term)
    object.__setattr__(value, "auctioned_at", _as_utc("auctioned_at", value.auctioned_at))
    for field_name in (
        "tail_bps",
        "bid_to_cover_ratio",
        "indirect_bidder_pct",
        "high_yield_pct",
        "when_issued_yield_pct",
    ):
        object.__setattr__(
            value,
            field_name,
            _normalize_measure_decimal(field_name, getattr(value, field_name)),
        )
    if value.bid_to_cover_ratio <= Decimal("0"):
        raise ValueError("bid_to_cover_ratio must be positive")
    _require_percentage("indirect_bidder_pct", value.indirect_bidder_pct)
    _require_nonnegative_measure("high_yield_pct", value.high_yield_pct)
    _require_nonnegative_measure("when_issued_yield_pct", value.when_issued_yield_pct)
    if value.tail_bps != Decimal("0") and value.high_yield_pct == value.when_issued_yield_pct:
        object.__setattr__(
            value,
            "when_issued_yield_pct",
            _quantize_decimal(value.high_yield_pct - (value.tail_bps / Decimal("100"))),
        )


def _validate_tail_yield_link(
    value: MarketResearchBondAuctionTailDigestAuction
    | MarketResearchBondAuctionTailDigestRow,
) -> None:
    implied_tail_bps = (
        (value.high_yield_pct - value.when_issued_yield_pct) * Decimal("100")
    )
    implied_tail_bps = _quantize_decimal(implied_tail_bps)
    if implied_tail_bps != value.tail_bps:
        raise ValueError("tail_bps must match high_yield_pct and when_issued_yield_pct")


def _validate_report(report: MarketResearchBondAuctionTailDigestReport) -> None:
    if report.auction_count != _count_decimal(len(report.rows)):
        raise ValueError("auction_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.tail_event_count != _reason_row_count(report.rows, "positive_auction_tail"):
        raise ValueError("tail_event_count must match rows")
    if report.weak_demand_count != _reason_row_count(report.rows, "weak_bid_to_cover"):
        raise ValueError("weak_demand_count must match rows")
    if report.low_indirect_bidder_count != _reason_row_count(
        report.rows,
        "low_indirect_bidder_share",
    ):
        raise ValueError("low_indirect_bidder_count must match rows")
    if report.max_tail_bps != _max_tail_bps(report.rows):
        raise ValueError("max_tail_bps must match rows")
    if report.average_tail_bps != _average_measure(row.tail_bps for row in report.rows):
        raise ValueError("average_tail_bps must match rows")
    if report.average_bid_to_cover_ratio != _average_measure(
        row.bid_to_cover_ratio for row in report.rows
    ):
        raise ValueError("average_bid_to_cover_ratio must match rows")
    if report.tail_event_ratio != _tail_event_ratio(report.rows):
        raise ValueError("tail_event_ratio must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _digest_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.digest_next_step != NEXT_STEP:
        raise ValueError("digest_next_step must match reducer")


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_row_reason_code("reason_codes", reason_code)
    if normalized != ("auction_tail_passed",) and normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _normalize_digest_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if len(normalized) != 1:
        raise ValueError("reason_codes must contain exactly one value")
    _require_digest_reason_code("reason_codes", normalized[0])
    return normalized


def _normalize_measure_decimal(field_name: str, value: object) -> Decimal:
    return _normalize_decimal(field_name, value)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_measure(field_name: str, value: Decimal) -> None:
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")


def _require_percentage(field_name: str, value: Decimal) -> None:
    _require_nonnegative_measure(field_name, value)
    if value > Decimal("100"):
        raise ValueError(f"{field_name} must be at most one hundred")


def _require_tail_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in TAIL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_digest_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_row_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_REASON_CODES:
        raise ValueError(f"{field_name} must contain known row reason codes")


def _require_reason_count_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_REASON_CODES and value not in DIGEST_REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_digest_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_REASON_CODES:
        raise ValueError(f"{field_name} must contain known digest reason codes")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, type_: type[object], field_name: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{field_name} must be exactly {type_.__name__}")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if isinstance(value, Decimal):
        _require_decimal(field_name, value)
        if value != _quantize_decimal(value):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a known public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
