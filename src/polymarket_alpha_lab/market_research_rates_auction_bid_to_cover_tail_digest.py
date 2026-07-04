"""Pure report-only rates auction bid-to-cover tail digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_AUCTION_BID_TO_COVER_TAIL_DIGEST_CONFIG_VERSION",
    "RatesAuctionBidToCoverTailDigestConfig",
    "RatesAuctionBidToCoverTailObservation",
    "RatesAuctionBidToCoverTailDigestRow",
    "RatesAuctionBidToCoverTailReasonCodeCount",
    "RatesAuctionBidToCoverTailDigestReport",
    "build_market_research_rates_auction_bid_to_cover_tail_digest",
    "market_research_rates_auction_bid_to_cover_tail_digest_payload",
)


DEFAULT_MARKET_RESEARCH_RATES_AUCTION_BID_TO_COVER_TAIL_DIGEST_CONFIG_VERSION = (
    "market-research-rates-auction-bid-to-cover-tail-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
TAIL_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

TAIL_SHORTFALL_DENOMINATOR = Decimal("0.200000")
TAIL_BPS_DENOMINATOR = Decimal("6.000000")

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: (
        "block_report_only_market_research_rates_auction_bid_to_cover_tail_digest"
    ),
    WATCH_STATUS: (
        "watch_report_only_market_research_rates_auction_bid_to_cover_tail_digest"
    ),
    PASS_STATUS: (
        "allow_report_only_market_research_rates_auction_bid_to_cover_tail_digest"
    ),
}


@dataclass(frozen=True)
class RatesAuctionBidToCoverTailDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_AUCTION_BID_TO_COVER_TAIL_DIGEST_CONFIG_VERSION
    )
    watch_bid_to_cover_shortfall_ratio: Decimal = Decimal("0.050000")
    blocked_bid_to_cover_shortfall_ratio: Decimal = Decimal("0.150000")
    watch_tail_bps: Decimal = Decimal("1.500000")
    blocked_tail_bps: Decimal = Decimal("4.000000")
    watch_tail_pressure_score: Decimal = Decimal("0.350000")
    blocked_tail_pressure_score: Decimal = Decimal("0.650000")
    max_source_age_seconds: Decimal = Decimal("900.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    watch_confidence_cap: Decimal = Decimal("0.600000")
    blocked_confidence_cap: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionBidToCoverTailDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_AUCTION_BID_TO_COVER_TAIL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_bid_to_cover_shortfall_ratio",
            "blocked_bid_to_cover_shortfall_ratio",
            "watch_tail_pressure_score",
            "blocked_tail_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_tail_bps",
            "blocked_tail_bps",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_confidence_cap",
            "watch_confidence_cap",
            "blocked_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.watch_bid_to_cover_shortfall_ratio
            > self.blocked_bid_to_cover_shortfall_ratio
        ):
            raise ValueError(
                "watch_bid_to_cover_shortfall_ratio must not exceed "
                "blocked_bid_to_cover_shortfall_ratio",
            )
        if self.watch_tail_bps > self.blocked_tail_bps:
            raise ValueError("watch_tail_bps must not exceed blocked_tail_bps")
        if self.watch_tail_pressure_score > self.blocked_tail_pressure_score:
            raise ValueError(
                "watch_tail_pressure_score must not exceed "
                "blocked_tail_pressure_score",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionBidToCoverTailObservation:
    source_id: str
    market_slug: str
    auction_id: str
    security_tenor: str
    reported_bid_to_cover: Decimal
    expected_bid_to_cover: Decimal
    stop_out_tail_bps: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionBidToCoverTailObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "auction_id",
            "security_tenor",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("reported_bid_to_cover", "expected_bid_to_cover"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stop_out_tail_bps",
            _normalize_nonnegative_decimal("stop_out_tail_bps", self.stop_out_tail_bps),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_confidence",
            _normalize_probability("base_confidence", self.base_confidence),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionBidToCoverTailDigestRow:
    source_id: str
    market_slug: str
    auction_id: str
    security_tenor: str
    reported_bid_to_cover: Decimal
    expected_bid_to_cover: Decimal
    bid_to_cover_gap: Decimal
    bid_to_cover_shortfall_ratio: Decimal
    stop_out_tail_bps: Decimal
    tail_pressure_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    tail_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionBidToCoverTailDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "auction_id",
            "security_tenor",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("reported_bid_to_cover", "expected_bid_to_cover"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "bid_to_cover_gap",
            _normalize_decimal("bid_to_cover_gap", self.bid_to_cover_gap),
        )
        object.__setattr__(
            self,
            "bid_to_cover_shortfall_ratio",
            _normalize_probability(
                "bid_to_cover_shortfall_ratio",
                self.bid_to_cover_shortfall_ratio,
            ),
        )
        object.__setattr__(
            self,
            "stop_out_tail_bps",
            _normalize_nonnegative_decimal("stop_out_tail_bps", self.stop_out_tail_bps),
        )
        for field_name in (
            "tail_pressure_score",
            "base_confidence",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("tail_status", self.tail_status, TAIL_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionBidToCoverTailReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RatesAuctionBidToCoverTailReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionBidToCoverTailDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_tail_count: Decimal
    watch_tail_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    weak_bid_to_cover_count: Decimal
    positive_tail_count: Decimal
    max_bid_to_cover_shortfall_ratio: Decimal
    max_tail_bps: Decimal
    average_tail_pressure_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RatesAuctionBidToCoverTailReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionBidToCoverTailDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_AUCTION_BID_TO_COVER_TAIL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_tail_count",
            "watch_tail_count",
            "pass_count",
            "stale_source_count",
            "weak_bid_to_cover_count",
            "positive_tail_count",
            "max_tail_bps",
            "average_tail_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_bid_to_cover_shortfall_ratio",
            _normalize_probability(
                "max_bid_to_cover_shortfall_ratio",
                self.max_bid_to_cover_shortfall_ratio,
            ),
        )
        _require_member("digest_status", self.digest_status, TAIL_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_rates_auction_bid_to_cover_tail_digest(
    inputs: Iterable[RatesAuctionBidToCoverTailObservation],
    *,
    config: RatesAuctionBidToCoverTailDigestConfig,
    generated_at: datetime,
) -> RatesAuctionBidToCoverTailDigestReport:
    if type(config) is not RatesAuctionBidToCoverTailDigestConfig:
        raise ValueError("config must be exactly RatesAuctionBidToCoverTailDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    status = _digest_status(rows)
    return RatesAuctionBidToCoverTailDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_tail_count=_status_count(rows, BLOCKED_STATUS),
        watch_tail_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(
            rows,
            "rates_auction_bid_to_cover_tail_source_stale",
        ),
        weak_bid_to_cover_count=_reason_count(
            rows,
            "rates_auction_bid_to_cover_tail_demand_weaker",
        ),
        positive_tail_count=_positive_tail_count(rows),
        max_bid_to_cover_shortfall_ratio=_max_row_decimal(
            rows,
            "bid_to_cover_shortfall_ratio",
        ),
        max_tail_bps=_max_row_decimal(rows, "stop_out_tail_bps"),
        average_tail_pressure_score=_ratio(
            _sum_decimal(row.tail_pressure_score for row in rows),
            row_count,
        ),
        digest_status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_rates_auction_bid_to_cover_tail_digest_payload(
    report: RatesAuctionBidToCoverTailDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesAuctionBidToCoverTailDigestReport:
        raise ValueError("report must be exactly RatesAuctionBidToCoverTailDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: RatesAuctionBidToCoverTailObservation,
    *,
    config: RatesAuctionBidToCoverTailDigestConfig,
    generated_at: datetime,
) -> RatesAuctionBidToCoverTailDigestRow:
    bid_to_cover_gap = _quantize_decimal(
        value.expected_bid_to_cover - value.reported_bid_to_cover,
    )
    bid_to_cover_shortfall_ratio = _adverse_shortfall_ratio(
        bid_to_cover_gap,
        value.expected_bid_to_cover,
    )
    tail_pressure_score = _tail_pressure_score(
        bid_to_cover_shortfall_ratio=bid_to_cover_shortfall_ratio,
        stop_out_tail_bps=value.stop_out_tail_bps,
    )
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _tail_status(
        bid_to_cover_shortfall_ratio=bid_to_cover_shortfall_ratio,
        stop_out_tail_bps=value.stop_out_tail_bps,
        tail_pressure_score=tail_pressure_score,
        config=config,
    )
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return RatesAuctionBidToCoverTailDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        auction_id=value.auction_id,
        security_tenor=value.security_tenor,
        reported_bid_to_cover=value.reported_bid_to_cover,
        expected_bid_to_cover=value.expected_bid_to_cover,
        bid_to_cover_gap=bid_to_cover_gap,
        bid_to_cover_shortfall_ratio=bid_to_cover_shortfall_ratio,
        stop_out_tail_bps=value.stop_out_tail_bps,
        tail_pressure_score=tail_pressure_score,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        tail_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            bid_to_cover_gap=bid_to_cover_gap,
            bid_to_cover_shortfall_ratio=bid_to_cover_shortfall_ratio,
            stop_out_tail_bps=value.stop_out_tail_bps,
            status=status,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _tail_pressure_score(
    *,
    bid_to_cover_shortfall_ratio: Decimal,
    stop_out_tail_bps: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        shortfall_component = min(
            ONE,
            bid_to_cover_shortfall_ratio / TAIL_SHORTFALL_DENOMINATOR,
        )
        tail_component = min(ONE, stop_out_tail_bps / TAIL_BPS_DENOMINATOR)
        return _quantize_decimal(
            shortfall_component * Decimal("0.600000")
            + tail_component * Decimal("0.400000"),
        )


def _tail_status(
    *,
    bid_to_cover_shortfall_ratio: Decimal,
    stop_out_tail_bps: Decimal,
    tail_pressure_score: Decimal,
    config: RatesAuctionBidToCoverTailDigestConfig,
) -> str:
    if (
        bid_to_cover_shortfall_ratio >= config.blocked_bid_to_cover_shortfall_ratio
        or stop_out_tail_bps >= config.blocked_tail_bps
        or tail_pressure_score >= config.blocked_tail_pressure_score
    ):
        return BLOCKED_STATUS
    if (
        bid_to_cover_shortfall_ratio >= config.watch_bid_to_cover_shortfall_ratio
        or stop_out_tail_bps >= config.watch_tail_bps
        or tail_pressure_score >= config.watch_tail_pressure_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: RatesAuctionBidToCoverTailDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == BLOCKED_STATUS:
        caps.append(config.blocked_confidence_cap)
    elif status == WATCH_STATUS:
        caps.append(config.watch_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    bid_to_cover_gap: Decimal,
    bid_to_cover_shortfall_ratio: Decimal,
    stop_out_tail_bps: Decimal,
    status: str,
    source_fresh: bool,
    config: RatesAuctionBidToCoverTailDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("rates_auction_bid_to_cover_tail_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("rates_auction_bid_to_cover_tail_watch")
    else:
        reason_codes.append("rates_auction_bid_to_cover_tail_calm")
    reason_codes.append(
        "rates_auction_bid_to_cover_tail_source_fresh"
        if source_fresh
        else "rates_auction_bid_to_cover_tail_source_stale",
    )
    if bid_to_cover_gap > ZERO:
        reason_codes.append("rates_auction_bid_to_cover_tail_demand_weaker")
    elif bid_to_cover_gap < ZERO:
        reason_codes.append("rates_auction_bid_to_cover_tail_demand_stronger")
    else:
        reason_codes.append("rates_auction_bid_to_cover_tail_demand_inline")
    if bid_to_cover_shortfall_ratio >= config.blocked_bid_to_cover_shortfall_ratio:
        reason_codes.append("rates_auction_bid_to_cover_tail_shortfall_blocked")
    elif bid_to_cover_shortfall_ratio >= config.watch_bid_to_cover_shortfall_ratio:
        reason_codes.append("rates_auction_bid_to_cover_tail_shortfall_watch")
    if stop_out_tail_bps >= config.blocked_tail_bps:
        reason_codes.append("rates_auction_stop_out_tail_blocked")
    elif stop_out_tail_bps >= config.watch_tail_bps:
        reason_codes.append("rates_auction_stop_out_tail_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("rates_auction_bid_to_cover_tail_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...],
) -> tuple[RatesAuctionBidToCoverTailReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("rates_auction_bid_to_cover_tail_digest_empty",):
        return (
            RatesAuctionBidToCoverTailReasonCodeCount(
                reason_code="rates_auction_bid_to_cover_tail_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RatesAuctionBidToCoverTailReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[RatesAuctionBidToCoverTailObservation],
) -> tuple[RatesAuctionBidToCoverTailObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not RatesAuctionBidToCoverTailObservation:
            raise ValueError("inputs must contain RatesAuctionBidToCoverTailObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[RatesAuctionBidToCoverTailDigestRow],
) -> tuple[RatesAuctionBidToCoverTailDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not RatesAuctionBidToCoverTailDigestRow:
            raise ValueError("rows must contain RatesAuctionBidToCoverTailDigestRow")
        _require_hard_flags(row)
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id")
        seen.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[RatesAuctionBidToCoverTailReasonCodeCount],
) -> tuple[RatesAuctionBidToCoverTailReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not RatesAuctionBidToCoverTailReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "RatesAuctionBidToCoverTailReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: RatesAuctionBidToCoverTailDigestRow) -> None:
    expected_gap = _quantize_decimal(
        row.expected_bid_to_cover - row.reported_bid_to_cover,
    )
    if row.bid_to_cover_gap != expected_gap:
        raise ValueError("bid_to_cover_gap must match expected minus reported")
    if row.bid_to_cover_shortfall_ratio != _adverse_shortfall_ratio(
        row.bid_to_cover_gap,
        row.expected_bid_to_cover,
    ):
        raise ValueError("bid_to_cover_shortfall_ratio must match adverse gap")
    if row.tail_pressure_score != _tail_pressure_score(
        bid_to_cover_shortfall_ratio=row.bid_to_cover_shortfall_ratio,
        stop_out_tail_bps=row.stop_out_tail_bps,
    ):
        raise ValueError("tail_pressure_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_status_code = (
        "rates_auction_bid_to_cover_tail_calm"
        if row.tail_status == PASS_STATUS
        else f"rates_auction_bid_to_cover_tail_{row.tail_status}"
    )
    if expected_status_code not in row.reason_codes:
        raise ValueError("tail_status must match reason_codes")


def _validate_report(report: RatesAuctionBidToCoverTailDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_tail_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_tail_count must match rows")
    if report.watch_tail_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_tail_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "rates_auction_bid_to_cover_tail_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.weak_bid_to_cover_count != _reason_count(
        report.rows,
        "rates_auction_bid_to_cover_tail_demand_weaker",
    ):
        raise ValueError("weak_bid_to_cover_count must match rows")
    if report.positive_tail_count != _positive_tail_count(report.rows):
        raise ValueError("positive_tail_count must match rows")
    if report.max_bid_to_cover_shortfall_ratio != _max_row_decimal(
        report.rows,
        "bid_to_cover_shortfall_ratio",
    ):
        raise ValueError("max_bid_to_cover_shortfall_ratio must match rows")
    if report.max_tail_bps != _max_row_decimal(report.rows, "stop_out_tail_bps"):
        raise ValueError("max_tail_bps must match rows")
    if report.average_tail_pressure_score != _ratio(
        _sum_decimal(row.tail_pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_tail_pressure_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")


def _digest_status(rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.tail_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.tail_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.tail_status == status))


def _reason_count(
    rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _positive_tail_count(rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...]) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "rates_auction_stop_out_tail_blocked" in row.reason_codes
            or "rates_auction_stop_out_tail_watch" in row.reason_codes
        ),
    )


def _max_row_decimal(
    rows: tuple[RatesAuctionBidToCoverTailDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _adverse_shortfall_ratio(
    bid_to_cover_gap: Decimal,
    expected_bid_to_cover: Decimal,
) -> Decimal:
    if bid_to_cover_gap <= ZERO:
        return ZERO
    return _ratio(bid_to_cover_gap, expected_bid_to_cover)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: object) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: RatesAuctionBidToCoverTailDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.tail_status],
        -row.tail_pressure_score,
        -row.bid_to_cover_shortfall_ratio,
        -row.stop_out_tail_bps,
        row.market_slug,
        row.source_id,
    )


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
