"""Pure report-only Treasury auction tail-pressure digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_AUCTION_TAIL_PRESSURE_DIGEST_CONFIG_VERSION",
    "RatesAuctionTailPressureDigestConfig",
    "RatesAuctionTailPressureObservation",
    "RatesAuctionTailPressureDigestRow",
    "RatesAuctionTailPressureReasonCodeCount",
    "RatesAuctionTailPressureDigestReport",
    "build_market_research_rates_auction_tail_pressure_digest",
    "market_research_rates_auction_tail_pressure_digest_payload",
)


DEFAULT_MARKET_RESEARCH_RATES_AUCTION_TAIL_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-rates-auction-tail-pressure-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
PRESSURE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
EMPTY_REASON_CODE = "auction_tail_pressure_digest_empty"

STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: (
        "block_report_only_market_research_rates_auction_tail_pressure_digest"
    ),
    WATCH_STATUS: (
        "watch_report_only_market_research_rates_auction_tail_pressure_digest"
    ),
    PASS_STATUS: "allow_report_only_market_research_rates_auction_tail_pressure_digest",
}

TAIL_PRESENT_REASON = "auction_tail_pressure_tail_present"
STOP_THROUGH_REASON = "auction_tail_pressure_stop_through_present"
WEAK_BID_TO_COVER_REASON = "auction_tail_pressure_weak_bid_to_cover"
DEALER_TAKE_DOWN_REASON = "auction_tail_pressure_dealer_take_down"
INDIRECT_BID_GAP_REASON = "auction_tail_pressure_indirect_bid_gap"
SOURCE_FRESH_REASON = "auction_tail_pressure_source_fresh"
SOURCE_STALE_REASON = "auction_tail_pressure_source_stale"
BLOCKED_REASON = "auction_tail_pressure_blocked"
WATCH_REASON = "auction_tail_pressure_watch"
CLEAR_REASON = "auction_tail_pressure_clear"


@dataclass(frozen=True)
class RatesAuctionTailPressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_AUCTION_TAIL_PRESSURE_DIGEST_CONFIG_VERSION
    )
    watch_tail_bps: Decimal = Decimal("1.000000")
    blocked_tail_bps: Decimal = Decimal("3.000000")
    watch_pressure_score: Decimal = Decimal("0.350000")
    blocked_pressure_score: Decimal = Decimal("0.650000")
    min_bid_to_cover_ratio: Decimal = Decimal("2.400000")
    high_primary_dealer_award_share: Decimal = Decimal("0.250000")
    min_indirect_bidder_award_share: Decimal = Decimal("0.550000")
    max_source_age_seconds: Decimal = Decimal("600.000000")
    blocked_confidence_cap: Decimal = Decimal("0.350000")
    watch_confidence_cap: Decimal = Decimal("0.650000")
    stale_confidence_cap: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesAuctionTailPressureDigestConfig:
            raise TypeError(
                "RatesAuctionTailPressureDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionTailPressureDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_AUCTION_TAIL_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_tail_bps",
            "blocked_tail_bps",
            "watch_pressure_score",
            "blocked_pressure_score",
            "min_bid_to_cover_ratio",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_primary_dealer_award_share",
            "min_indirect_bidder_award_share",
            "blocked_confidence_cap",
            "watch_confidence_cap",
            "stale_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_tail_bps > self.blocked_tail_bps:
            raise ValueError("watch_tail_bps must not exceed blocked_tail_bps")
        if self.watch_pressure_score > self.blocked_pressure_score:
            raise ValueError("watch_pressure_score must not exceed blocked_pressure_score")
        if self.high_primary_dealer_award_share == ONE:
            raise ValueError("high_primary_dealer_award_share must be below one")
        if self.min_indirect_bidder_award_share == ZERO:
            raise ValueError("min_indirect_bidder_award_share must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionTailPressureObservation:
    source_id: str
    market_slug: str
    auction_id: str
    tenor_bucket: str
    observed_at: datetime
    when_issued_yield_pct: Decimal
    stop_yield_pct: Decimal
    bid_to_cover_ratio: Decimal
    primary_dealer_award_share: Decimal
    indirect_bidder_award_share: Decimal
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesAuctionTailPressureObservation:
            raise TypeError(
                "RatesAuctionTailPressureObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionTailPressureObservation, "observation")
        for field_name in ("source_id", "market_slug", "auction_id", "tenor_bucket"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "when_issued_yield_pct",
            "stop_yield_pct",
            "bid_to_cover_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_dealer_award_share",
            "indirect_bidder_award_share",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                self.upstream_reason_codes,
                field_name="upstream_reason_codes",
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionTailPressureDigestRow:
    source_id: str
    market_slug: str
    auction_id: str
    tenor_bucket: str
    observed_at: datetime
    source_age_seconds: Decimal
    when_issued_yield_pct: Decimal
    stop_yield_pct: Decimal
    auction_tail_bps: Decimal
    stop_through_bps: Decimal
    bid_to_cover_ratio: Decimal
    bid_to_cover_shortfall: Decimal
    primary_dealer_award_share: Decimal
    primary_dealer_award_excess: Decimal
    indirect_bidder_award_share: Decimal
    indirect_bidder_award_gap: Decimal
    tail_pressure_score: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesAuctionTailPressureDigestRow:
            raise TypeError(
                "RatesAuctionTailPressureDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionTailPressureDigestRow, "row")
        for field_name in ("source_id", "market_slug", "auction_id", "tenor_bucket"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "when_issued_yield_pct",
            "stop_yield_pct",
            "stop_through_bps",
            "bid_to_cover_ratio",
            "bid_to_cover_shortfall",
            "primary_dealer_award_excess",
            "indirect_bidder_award_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "auction_tail_bps",
            _normalize_decimal("auction_tail_bps", self.auction_tail_bps),
        )
        for field_name in (
            "primary_dealer_award_share",
            "indirect_bidder_award_share",
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
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionTailPressureReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesAuctionTailPressureReasonCodeCount:
            raise TypeError(
                "RatesAuctionTailPressureReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RatesAuctionTailPressureReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesAuctionTailPressureDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_pressure_count: Decimal
    watch_pressure_count: Decimal
    pass_count: Decimal
    tail_count: Decimal
    stop_through_count: Decimal
    weak_bid_to_cover_count: Decimal
    dealer_take_down_count: Decimal
    indirect_bid_gap_count: Decimal
    stale_source_count: Decimal
    max_tail_pressure_score: Decimal
    average_tail_pressure_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesAuctionTailPressureDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RatesAuctionTailPressureReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesAuctionTailPressureDigestReport:
            raise TypeError(
                "RatesAuctionTailPressureDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesAuctionTailPressureDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_AUCTION_TAIL_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_pressure_count",
            "watch_pressure_count",
            "pass_count",
            "tail_count",
            "stop_through_count",
            "weak_bid_to_cover_count",
            "dealer_take_down_count",
            "indirect_bid_gap_count",
            "stale_source_count",
            "max_tail_pressure_score",
            "average_tail_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, PRESSURE_STATUSES)
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


def build_market_research_rates_auction_tail_pressure_digest(
    inputs: Iterable[RatesAuctionTailPressureObservation],
    *,
    config: RatesAuctionTailPressureDigestConfig | None = None,
    generated_at: datetime,
) -> RatesAuctionTailPressureDigestReport:
    if config is None:
        config = RatesAuctionTailPressureDigestConfig()
    elif type(config) is not RatesAuctionTailPressureDigestConfig:
        raise ValueError("config must be exactly RatesAuctionTailPressureDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    observations = _normalize_inputs(inputs)
    rows = _sort_rows(
        tuple(
            _row_from_observation(
                value,
                config=config,
                generated_at=generated_at,
            )
            for value in observations
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    status = _digest_status(rows)
    return RatesAuctionTailPressureDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(observations)),
        row_count=row_count,
        blocked_pressure_count=_status_count(rows, BLOCKED_STATUS),
        watch_pressure_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        tail_count=_reason_count(rows, TAIL_PRESENT_REASON),
        stop_through_count=_reason_count(rows, STOP_THROUGH_REASON),
        weak_bid_to_cover_count=_reason_count(rows, WEAK_BID_TO_COVER_REASON),
        dealer_take_down_count=_reason_count(rows, DEALER_TAKE_DOWN_REASON),
        indirect_bid_gap_count=_reason_count(rows, INDIRECT_BID_GAP_REASON),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON),
        max_tail_pressure_score=_max_row_decimal(rows, "tail_pressure_score"),
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


def market_research_rates_auction_tail_pressure_digest_payload(
    report: RatesAuctionTailPressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesAuctionTailPressureDigestReport:
        raise ValueError("report must be exactly RatesAuctionTailPressureDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: RatesAuctionTailPressureObservation,
    *,
    config: RatesAuctionTailPressureDigestConfig,
    generated_at: datetime,
) -> RatesAuctionTailPressureDigestRow:
    auction_tail_bps = _quantize_decimal(
        (value.stop_yield_pct - value.when_issued_yield_pct) * Decimal("100.000000"),
    )
    stop_through_bps = max(ZERO, -auction_tail_bps)
    bid_to_cover_shortfall = max(
        ZERO,
        _quantize_decimal(config.min_bid_to_cover_ratio - value.bid_to_cover_ratio),
    )
    primary_dealer_award_excess = max(
        ZERO,
        _quantize_decimal(
            value.primary_dealer_award_share - config.high_primary_dealer_award_share,
        ),
    )
    indirect_bidder_award_gap = max(
        ZERO,
        _quantize_decimal(
            config.min_indirect_bidder_award_share
            - value.indirect_bidder_award_share,
        ),
    )
    tail_pressure_score = _tail_pressure_score(
        auction_tail_bps=auction_tail_bps,
        bid_to_cover_shortfall=bid_to_cover_shortfall,
        primary_dealer_award_excess=primary_dealer_award_excess,
        indirect_bidder_award_gap=indirect_bidder_award_gap,
        config=config,
    )
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _pressure_status(
        auction_tail_bps=auction_tail_bps,
        tail_pressure_score=tail_pressure_score,
        config=config,
    )
    confidence_cap = _confidence_cap(status=status, source_fresh=source_fresh, config=config)
    return RatesAuctionTailPressureDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        auction_id=value.auction_id,
        tenor_bucket=value.tenor_bucket,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        when_issued_yield_pct=value.when_issued_yield_pct,
        stop_yield_pct=value.stop_yield_pct,
        auction_tail_bps=auction_tail_bps,
        stop_through_bps=stop_through_bps,
        bid_to_cover_ratio=value.bid_to_cover_ratio,
        bid_to_cover_shortfall=bid_to_cover_shortfall,
        primary_dealer_award_share=value.primary_dealer_award_share,
        primary_dealer_award_excess=primary_dealer_award_excess,
        indirect_bidder_award_share=value.indirect_bidder_award_share,
        indirect_bidder_award_gap=indirect_bidder_award_gap,
        tail_pressure_score=tail_pressure_score,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        pressure_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            auction_tail_bps=auction_tail_bps,
            bid_to_cover_shortfall=bid_to_cover_shortfall,
            primary_dealer_award_excess=primary_dealer_award_excess,
            indirect_bidder_award_gap=indirect_bidder_award_gap,
            status=status,
            source_fresh=source_fresh,
        ),
    )


def _tail_pressure_score(
    *,
    auction_tail_bps: Decimal,
    bid_to_cover_shortfall: Decimal,
    primary_dealer_award_excess: Decimal,
    indirect_bidder_award_gap: Decimal,
    config: RatesAuctionTailPressureDigestConfig,
) -> Decimal:
    tail_component = min(
        ONE,
        max(ZERO, auction_tail_bps) / config.blocked_tail_bps,
    )
    bid_to_cover_component = min(
        ONE,
        bid_to_cover_shortfall / config.min_bid_to_cover_ratio,
    )
    primary_dealer_component = min(
        ONE,
        primary_dealer_award_excess / (ONE - config.high_primary_dealer_award_share),
    )
    indirect_bidder_component = min(
        ONE,
        indirect_bidder_award_gap / config.min_indirect_bidder_award_share,
    )
    return _quantize_decimal(
        tail_component * Decimal("0.500000")
        + bid_to_cover_component * Decimal("0.200000")
        + primary_dealer_component * Decimal("0.150000")
        + indirect_bidder_component * Decimal("0.150000"),
    )


def _pressure_status(
    *,
    auction_tail_bps: Decimal,
    tail_pressure_score: Decimal,
    config: RatesAuctionTailPressureDigestConfig,
) -> str:
    if (
        auction_tail_bps >= config.blocked_tail_bps
        or tail_pressure_score >= config.blocked_pressure_score
    ):
        return BLOCKED_STATUS
    if (
        auction_tail_bps >= config.watch_tail_bps
        or tail_pressure_score >= config.watch_pressure_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: RatesAuctionTailPressureDigestConfig,
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
    auction_tail_bps: Decimal,
    bid_to_cover_shortfall: Decimal,
    primary_dealer_award_excess: Decimal,
    indirect_bidder_award_gap: Decimal,
    status: str,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if auction_tail_bps > ZERO:
        reason_codes.append(TAIL_PRESENT_REASON)
    elif auction_tail_bps < ZERO:
        reason_codes.append(STOP_THROUGH_REASON)
    if bid_to_cover_shortfall > ZERO:
        reason_codes.append(WEAK_BID_TO_COVER_REASON)
    if primary_dealer_award_excess > ZERO:
        reason_codes.append(DEALER_TAKE_DOWN_REASON)
    if indirect_bidder_award_gap > ZERO:
        reason_codes.append(INDIRECT_BID_GAP_REASON)
    reason_codes.append(SOURCE_FRESH_REASON if source_fresh else SOURCE_STALE_REASON)
    if status == BLOCKED_STATUS:
        reason_codes.append(BLOCKED_REASON)
    elif status == WATCH_STATUS:
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(CLEAR_REASON)
    return _canonical_reason_codes(tuple(reason_codes))


def _normalize_inputs(
    inputs: Iterable[RatesAuctionTailPressureObservation],
) -> tuple[RatesAuctionTailPressureObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of RatesAuctionTailPressureObservation")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of RatesAuctionTailPressureObservation",
        ) from exc
    seen_source_ids: set[str] = set()
    seen_auction_ids: set[str] = set()
    for value in normalized:
        if type(value) is not RatesAuctionTailPressureObservation:
            raise ValueError("inputs must contain RatesAuctionTailPressureObservation")
        if value.source_id in seen_source_ids:
            raise ValueError("duplicate source_id")
        if value.auction_id in seen_auction_ids:
            raise ValueError("duplicate auction_id")
        seen_source_ids.add(value.source_id)
        seen_auction_ids.add(value.auction_id)
    return normalized


def _normalize_rows(
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
) -> tuple[RatesAuctionTailPressureDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, RatesAuctionTailPressureDigestRow, "row")
    sorted_rows = _sort_rows(rows)
    if rows != sorted_rows:
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[RatesAuctionTailPressureReasonCodeCount, ...],
) -> tuple[RatesAuctionTailPressureReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for count in counts:
        _require_exact_type(
            count,
            RatesAuctionTailPressureReasonCodeCount,
            "reason_code_count",
        )
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(count.reason_code)
    sorted_counts = _sort_reason_code_counts(counts)
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return counts


def _report_reason_codes(
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return _canonical_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
) -> tuple[RatesAuctionTailPressureReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if row_count == ZERO:
        return (
            RatesAuctionTailPressureReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return _sort_reason_code_counts(
        tuple(
            RatesAuctionTailPressureReasonCodeCount(
                reason_code=reason_code,
                count=_reason_count(rows, reason_code),
                row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
            )
            for reason_code in reason_codes
        ),
    )


def _digest_status(rows: tuple[RatesAuctionTailPressureDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_status == status))


def _reason_count(
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _sort_rows(
    rows: tuple[RatesAuctionTailPressureDigestRow, ...],
) -> tuple[RatesAuctionTailPressureDigestRow, ...]:
    return tuple(
        row
        for _, row in sorted(
            (_row_sort_tuple(row), row)
            for row in rows
        )
    )


def _sort_reason_code_counts(
    counts: tuple[RatesAuctionTailPressureReasonCodeCount, ...],
) -> tuple[RatesAuctionTailPressureReasonCodeCount, ...]:
    return tuple(
        count
        for _, count in sorted(
            ((-count.count, count.reason_code), count)
            for count in counts
        )
    )


def _row_sort_tuple(row: RatesAuctionTailPressureDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.pressure_status],
        -row.tail_pressure_score,
        row.auction_id,
        row.source_id,
    )


def _validate_row(row: RatesAuctionTailPressureDigestRow) -> None:
    expected_tail_bps = _quantize_decimal(
        (row.stop_yield_pct - row.when_issued_yield_pct) * Decimal("100.000000"),
    )
    if row.auction_tail_bps != expected_tail_bps:
        raise ValueError("auction_tail_bps must match yield spread")
    if row.stop_through_bps != max(ZERO, -row.auction_tail_bps):
        raise ValueError("stop_through_bps must match auction_tail_bps")
    if row.capped_confidence > row.base_confidence:
        raise ValueError("capped_confidence must not exceed base_confidence")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")


def _validate_report(report: RatesAuctionTailPressureDigestReport) -> None:
    row_count = _count_decimal(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must equal rows length")
    if report.input_count < report.row_count:
        raise ValueError("input_count must be at least row_count")
    if report.blocked_pressure_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_pressure_count must match rows")
    if report.watch_pressure_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_pressure_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    status_total = (
        report.blocked_pressure_count + report.watch_pressure_count + report.pass_count
    )
    if status_total != report.row_count:
        raise ValueError("pressure status counts must equal row_count")
    reason_checks = (
        ("tail_count", TAIL_PRESENT_REASON),
        ("stop_through_count", STOP_THROUGH_REASON),
        ("weak_bid_to_cover_count", WEAK_BID_TO_COVER_REASON),
        ("dealer_take_down_count", DEALER_TAKE_DOWN_REASON),
        ("indirect_bid_gap_count", INDIRECT_BID_GAP_REASON),
        ("stale_source_count", SOURCE_STALE_REASON),
    )
    for field_name, reason_code in reason_checks:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_tail_pressure_score != _max_row_decimal(
        report.rows,
        "tail_pressure_score",
    ):
        raise ValueError("max_tail_pressure_score must match rows")
    if report.average_tail_pressure_score != _ratio(
        _sum_decimal(row.tail_pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_tail_pressure_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _revalidate_report_for_payload(report: RatesAuctionTailPressureDigestReport) -> None:
    _require_exact_type(report, RatesAuctionTailPressureDigestReport, "report")
    _require_payload_direct_fields(report)
    _require_hard_flags(report)
    if _normalize_rows(report.rows) != report.rows:
        raise ValueError("rows must be deterministically sorted")
    if _normalize_reason_codes(report.reason_codes) != report.reason_codes:
        raise ValueError("reason_codes must be canonical sorted unique reason codes")
    if (
        _normalize_reason_code_counts(report.reason_code_counts)
        != report.reason_code_counts
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    for count in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(count)
    _validate_report(report)


def _revalidate_row_for_payload(row: RatesAuctionTailPressureDigestRow) -> None:
    _require_exact_type(row, RatesAuctionTailPressureDigestRow, "row")
    _require_payload_direct_fields(row)
    for field_name in ("source_id", "market_slug", "auction_id", "tenor_bucket"):
        _require_canonical_string(field_name, getattr(row, field_name))
    _require_member("pressure_status", row.pressure_status, PRESSURE_STATUSES)
    if _normalize_reason_codes(row.reason_codes) != row.reason_codes:
        raise ValueError("reason_codes must be canonical sorted unique reason codes")
    _validate_row(row)
    _require_hard_flags(row)


def _revalidate_reason_code_count_for_payload(
    count: RatesAuctionTailPressureReasonCodeCount,
) -> None:
    _require_exact_type(
        count,
        RatesAuctionTailPressureReasonCodeCount,
        "reason_code_count",
    )
    _require_payload_direct_fields(count)
    _require_canonical_string("reason_code", count.reason_code)
    if count.count == ZERO:
        raise ValueError("count must be positive")
    _require_hard_flags(count)


def _require_payload_direct_fields(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if isinstance(field_value, Decimal):
            _require_six_decimal(field.name, field_value)
        elif isinstance(field_value, datetime):
            _as_utc(field.name, field_value)
        elif type(field_value) is int:
            raise ValueError(f"{field.name} must use Decimal values")
        elif isinstance(field_value, float):
            raise ValueError(f"{field.name} must not be a float")
        elif type(field_value) in (list, dict, set):
            raise ValueError(f"{field.name} must remain constructor-normalized")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize_decimal(Decimal(str((later - earlier).total_seconds())))


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    field_name: str = "reason_codes",
) -> tuple[str, ...]:
    normalized = _canonical_reason_codes(value, field_name=field_name)
    if value != normalized:
        raise ValueError(f"{field_name} must be canonical sorted unique reason codes")
    return normalized


def _canonical_reason_codes(
    value: tuple[str, ...],
    *,
    field_name: str = "reason_codes",
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
    return tuple(sorted(frozenset(value)))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_six_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")


def _payload_value(value: Any, *, field_name: str = "payload") -> Any:
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return format(value, "f")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is datetime:
        return _as_utc(field_name, value).isoformat()
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) is RatesAuctionTailPressureDigestReport:
            _revalidate_report_for_payload(value)
        elif type(value) is RatesAuctionTailPressureDigestRow:
            _revalidate_row_for_payload(value)
        elif type(value) is RatesAuctionTailPressureReasonCodeCount:
            _revalidate_reason_code_count_for_payload(value)
        else:
            raise ValueError("payload contains unsupported dataclass")
        return {
            field.name: _payload_value(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item, field_name=field_name) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    if type(value) is int:
        raise ValueError("payload must not contain raw integers")
    return value
