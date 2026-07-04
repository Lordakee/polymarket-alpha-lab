"""Pure Phase 1 reducer for soccer set-piece taker availability research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_TAKER_AVAILABILITY_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-set-piece-taker-availability-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal(3600)
MICROSECONDS_PER_SECOND = Decimal(1000000)

PRIMARY_AVAILABILITY_WEIGHT = Decimal("0.350000")
SECONDARY_READINESS_WEIGHT = Decimal("0.200000")
SET_PIECE_XG_WEIGHT = Decimal("0.250000")
INJURY_SUSPENSION_WEIGHT = Decimal("0.100000")
SOURCE_DISAGREEMENT_WEIGHT = Decimal("0.100000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = DIGEST_STATUSES

SOURCE_DISAGREEMENT_REASON = (
    "soccer_set_piece_taker_availability_source_disagreement"
)
EDGE_BLOCKED_REASON = "soccer_set_piece_taker_availability_edge_score_blocked"
PRIMARY_UNAVAILABLE_REASON = (
    "soccer_set_piece_taker_availability_primary_taker_unavailable"
)
INJURY_SUSPENSION_REASON = (
    "soccer_set_piece_taker_availability_injury_suspension_pressure"
)
EDGE_WATCH_REASON = "soccer_set_piece_taker_availability_edge_score_watch"
PRIMARY_WATCH_REASON = "soccer_set_piece_taker_availability_primary_taker_watch"
SECONDARY_READINESS_REASON = (
    "soccer_set_piece_taker_availability_secondary_taker_readiness_gap"
)
LINEUP_STALE_REASON = "soccer_set_piece_taker_availability_lineup_leak_stale"
XG_DEPENDENCY_REASON = "soccer_set_piece_taker_availability_xg_dependency_high"
UPSTREAM_REASON = "soccer_set_piece_taker_availability_upstream_reason_present"
CLEAR_REASON = "soccer_set_piece_taker_availability_clear"
PASSED_REASON = "soccer_set_piece_taker_availability_passed"
EMPTY_REASON = "soccer_set_piece_taker_availability_empty"

ROW_REASON_CODES = (
    SOURCE_DISAGREEMENT_REASON,
    EDGE_BLOCKED_REASON,
    PRIMARY_UNAVAILABLE_REASON,
    INJURY_SUSPENSION_REASON,
    EDGE_WATCH_REASON,
    PRIMARY_WATCH_REASON,
    SECONDARY_READINESS_REASON,
    LINEUP_STALE_REASON,
    XG_DEPENDENCY_REASON,
    UPSTREAM_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    SOURCE_DISAGREEMENT_REASON,
    EDGE_BLOCKED_REASON,
    PRIMARY_UNAVAILABLE_REASON,
    INJURY_SUSPENSION_REASON,
    EDGE_WATCH_REASON,
    PRIMARY_WATCH_REASON,
    SECONDARY_READINESS_REASON,
    LINEUP_STALE_REASON,
    XG_DEPENDENCY_REASON,
    UPSTREAM_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = (*ROW_REASON_CODES, PASSED_REASON, EMPTY_REASON)
BLOCKED_ROW_REASONS = (
    SOURCE_DISAGREEMENT_REASON,
    EDGE_BLOCKED_REASON,
    PRIMARY_UNAVAILABLE_REASON,
    INJURY_SUSPENSION_REASON,
)

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_soccer_set_piece_taker_availability_monitoring",
    WATCH_STATUS: "review_report_only_soccer_set_piece_taker_availability_watchlist",
    BLOCKED_STATUS: "block_report_only_soccer_set_piece_taker_availability_review",
}

_SAFE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.-")
_BLOCKED_WORDS = (
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "sign" "ing",
    "sub" "mit",
    "can" "cel",
    "data" "base",
    "per" "sist",
    "priv" "ate_" "key",
    "ex" "change",
    "net" "work",
    "sec" "ret",
    "sup" "abase",
    "psy" "copg",
    "sock" "et",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_TAKER_AVAILABILITY_DIGEST_CONFIG_VERSION",
    "MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig",
    "MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal",
    "MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount",
    "MarketResearchSoccerSetPieceTakerAvailabilityDigestRow",
    "MarketResearchSoccerSetPieceTakerAvailabilityDigestReport",
    "build_market_research_soccer_set_piece_taker_availability_digest",
    "market_research_soccer_set_piece_taker_availability_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_SET_PIECE_TAKER_AVAILABILITY_DIGEST_CONFIG_VERSION
    )
    blocked_edge_score_threshold: Decimal = Decimal("0.700000")
    watch_edge_score_threshold: Decimal = Decimal("0.400000")
    primary_taker_unavailable_threshold: Decimal = Decimal("0.250000")
    primary_taker_watch_threshold: Decimal = Decimal("0.550000")
    secondary_taker_readiness_threshold: Decimal = Decimal("0.500000")
    injury_suspension_blocked_count: Decimal = Decimal("2.000000")
    max_lineup_leak_age_minutes: Decimal = Decimal("90.000000")
    high_set_piece_xg_dependency_threshold: Decimal = Decimal("0.500000")
    max_source_disagreement_count: Decimal = Decimal("0.000000")
    max_input_age_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig:
            raise TypeError(
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "blocked_edge_score_threshold",
            "watch_edge_score_threshold",
            "primary_taker_unavailable_threshold",
            "primary_taker_watch_threshold",
            "secondary_taker_readiness_threshold",
            "high_set_piece_xg_dependency_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_lineup_leak_age_minutes",
            "max_input_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "injury_suspension_blocked_count",
            "max_source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_edge_score_threshold > self.blocked_edge_score_threshold:
            raise ValueError(
                "watch_edge_score_threshold must not exceed "
                "blocked_edge_score_threshold",
            )
        if self.primary_taker_unavailable_threshold > self.primary_taker_watch_threshold:
            raise ValueError(
                "primary_taker_unavailable_threshold must not exceed "
                "primary_taker_watch_threshold",
            )
        if self.injury_suspension_blocked_count == ZERO:
            raise ValueError("injury_suspension_blocked_count must be positive")
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal:
    condition_id: str
    market_slug: str
    club: str
    opponent: str
    match_ref: str
    match_start_at: datetime
    observed_at: datetime
    primary_taker_availability_score: Decimal
    secondary_taker_readiness_score: Decimal
    injury_suspension_count: Decimal
    lineup_leak_age_minutes: Decimal
    set_piece_xg_dependency: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    signal_ref: str
    signal_config_version: str = "soccer-set-piece-taker-availability-feed-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal:
            raise TypeError(
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "club",
            "opponent",
            "match_ref",
            "signal_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "primary_taker_availability_score",
            "secondary_taker_readiness_score",
            "set_piece_xg_dependency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "injury_suspension_count",
            "lineup_leak_age_minutes",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("injury_suspension_count", "source_disagreement_count"):
            if getattr(self, field_name) != getattr(self, field_name).to_integral_value():
                raise ValueError(f"{field_name} must be a whole Decimal")
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount:
    reason_code: str
    signal_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount
        ):
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_whole_decimal("signal_count", self.signal_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceTakerAvailabilityDigestRow:
    condition_id: str
    market_slug: str
    club: str
    opponent: str
    match_ref: str
    match_start_at: datetime
    observed_at: datetime
    primary_taker_availability_score: Decimal
    secondary_taker_readiness_score: Decimal
    injury_suspension_count: Decimal
    lineup_leak_age_minutes: Decimal
    set_piece_xg_dependency: Decimal
    source_disagreement_count: Decimal
    availability_edge_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    signal_ref: str
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerSetPieceTakerAvailabilityDigestRow:
            raise TypeError(
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestRow",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "club",
            "opponent",
            "match_ref",
            "signal_ref",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "primary_taker_availability_score",
            "secondary_taker_readiness_score",
            "set_piece_xg_dependency",
            "availability_edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "injury_suspension_count",
            "lineup_leak_age_minutes",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("injury_suspension_count", "source_disagreement_count"):
            if getattr(self, field_name) != getattr(self, field_name).to_integral_value():
                raise ValueError(f"{field_name} must be a whole Decimal")
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerSetPieceTakerAvailabilityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    source_disagreement_signal_count: Decimal
    blocked_edge_score_signal_count: Decimal
    watch_edge_score_signal_count: Decimal
    primary_taker_unavailable_signal_count: Decimal
    primary_taker_watch_signal_count: Decimal
    secondary_taker_readiness_gap_signal_count: Decimal
    injury_suspension_signal_count: Decimal
    stale_lineup_leak_signal_count: Decimal
    high_set_piece_xg_dependency_signal_count: Decimal
    upstream_reason_signal_count: Decimal
    blocked_edge_score_threshold: Decimal
    watch_edge_score_threshold: Decimal
    primary_taker_unavailable_threshold: Decimal
    primary_taker_watch_threshold: Decimal
    secondary_taker_readiness_threshold: Decimal
    injury_suspension_blocked_count: Decimal
    max_lineup_leak_age_minutes: Decimal
    high_set_piece_xg_dependency_threshold: Decimal
    max_source_disagreement_count: Decimal
    max_input_age_hours: Decimal
    max_availability_edge_score: Decimal
    average_availability_edge_score: Decimal
    rows: tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerSetPieceTakerAvailabilityDigestReport:
            raise TypeError(
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "source_disagreement_signal_count",
            "blocked_edge_score_signal_count",
            "watch_edge_score_signal_count",
            "primary_taker_unavailable_signal_count",
            "primary_taker_watch_signal_count",
            "secondary_taker_readiness_gap_signal_count",
            "injury_suspension_signal_count",
            "stale_lineup_leak_signal_count",
            "high_set_piece_xg_dependency_signal_count",
            "upstream_reason_signal_count",
            "injury_suspension_blocked_count",
            "max_lineup_leak_age_minutes",
            "max_source_disagreement_count",
            "max_input_age_hours",
            "max_availability_edge_score",
            "average_availability_edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_edge_score_threshold",
            "watch_edge_score_threshold",
            "primary_taker_unavailable_threshold",
            "primary_taker_watch_threshold",
            "secondary_taker_readiness_threshold",
            "high_set_piece_xg_dependency_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "source_disagreement_signal_count",
            "blocked_edge_score_signal_count",
            "watch_edge_score_signal_count",
            "primary_taker_unavailable_signal_count",
            "primary_taker_watch_signal_count",
            "secondary_taker_readiness_gap_signal_count",
            "injury_suspension_signal_count",
            "stale_lineup_leak_signal_count",
            "high_set_piece_xg_dependency_signal_count",
            "upstream_reason_signal_count",
            "injury_suspension_blocked_count",
            "max_source_disagreement_count",
        ):
            if getattr(self, field_name) != getattr(self, field_name).to_integral_value():
                raise ValueError(f"{field_name} must be a whole Decimal")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, DIGEST_REASON_CODES),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_soccer_set_piece_taker_availability_digest(
    signals: Iterable[MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal],
    *,
    config: MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerSetPieceTakerAvailabilityDigestReport:
    if type(config) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    for signal in signal_items:
        if signal.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
        if signal.match_start_at < generated_at_utc:
            raise ValueError("match_start_at must not be in the past")
        if _elapsed_seconds(signal.observed_at, generated_at_utc) > (
            config.max_input_age_hours * SECONDS_PER_HOUR
        ):
            raise ValueError("observed_at exceeds max_input_age_hours")

    rows = tuple(
        sorted(
            (_row_for_signal(signal, config=config) for signal in signal_items),
            key=_row_sort_rank,
        ),
    )
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        digest_status = BLOCKED_STATUS
    elif any(row.digest_status == WATCH_STATUS for row in rows):
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchSoccerSetPieceTakerAvailabilityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        signal_count=_whole(len(rows)),
        pass_signal_count=_count_rows(rows, PASS_STATUS),
        watch_signal_count=_count_rows(rows, WATCH_STATUS),
        blocked_signal_count=_count_rows(rows, BLOCKED_STATUS),
        source_disagreement_signal_count=_count_reason(
            rows,
            SOURCE_DISAGREEMENT_REASON,
        ),
        blocked_edge_score_signal_count=_count_reason(rows, EDGE_BLOCKED_REASON),
        watch_edge_score_signal_count=_count_reason(rows, EDGE_WATCH_REASON),
        primary_taker_unavailable_signal_count=_count_reason(
            rows,
            PRIMARY_UNAVAILABLE_REASON,
        ),
        primary_taker_watch_signal_count=_count_reason(rows, PRIMARY_WATCH_REASON),
        secondary_taker_readiness_gap_signal_count=_count_reason(
            rows,
            SECONDARY_READINESS_REASON,
        ),
        injury_suspension_signal_count=_count_reason(rows, INJURY_SUSPENSION_REASON),
        stale_lineup_leak_signal_count=_count_reason(rows, LINEUP_STALE_REASON),
        high_set_piece_xg_dependency_signal_count=_count_reason(
            rows,
            XG_DEPENDENCY_REASON,
        ),
        upstream_reason_signal_count=_count_reason(rows, UPSTREAM_REASON),
        blocked_edge_score_threshold=config.blocked_edge_score_threshold,
        watch_edge_score_threshold=config.watch_edge_score_threshold,
        primary_taker_unavailable_threshold=config.primary_taker_unavailable_threshold,
        primary_taker_watch_threshold=config.primary_taker_watch_threshold,
        secondary_taker_readiness_threshold=config.secondary_taker_readiness_threshold,
        injury_suspension_blocked_count=config.injury_suspension_blocked_count,
        max_lineup_leak_age_minutes=config.max_lineup_leak_age_minutes,
        high_set_piece_xg_dependency_threshold=(
            config.high_set_piece_xg_dependency_threshold
        ),
        max_source_disagreement_count=config.max_source_disagreement_count,
        max_input_age_hours=config.max_input_age_hours,
        max_availability_edge_score=_max_or_zero(row.availability_edge_score for row in rows),
        average_availability_edge_score=_average(
            (row.availability_edge_score for row in rows),
        ),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (
                        signal.match_ref,
                        signal.club,
                        signal.signal_config_version,
                    )
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_set_piece_taker_availability_digest_payload(
    report: MarketResearchSoccerSetPieceTakerAvailabilityDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchSoccerSetPieceTakerAvailabilityDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _row_for_signal(
    signal: MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal,
    *,
    config: MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig,
) -> MarketResearchSoccerSetPieceTakerAvailabilityDigestRow:
    edge_score = _availability_edge_score(signal, config=config)
    reason_codes = []
    if signal.source_disagreement_count > config.max_source_disagreement_count:
        reason_codes.append(SOURCE_DISAGREEMENT_REASON)
    if edge_score >= config.blocked_edge_score_threshold:
        reason_codes.append(EDGE_BLOCKED_REASON)
    elif edge_score >= config.watch_edge_score_threshold:
        reason_codes.append(EDGE_WATCH_REASON)
    if (
        signal.primary_taker_availability_score
        <= config.primary_taker_unavailable_threshold
    ):
        reason_codes.append(PRIMARY_UNAVAILABLE_REASON)
    elif signal.primary_taker_availability_score <= config.primary_taker_watch_threshold:
        reason_codes.append(PRIMARY_WATCH_REASON)
    if signal.injury_suspension_count >= config.injury_suspension_blocked_count:
        reason_codes.append(INJURY_SUSPENSION_REASON)
    if signal.secondary_taker_readiness_score <= config.secondary_taker_readiness_threshold:
        reason_codes.append(SECONDARY_READINESS_REASON)
    if signal.lineup_leak_age_minutes > config.max_lineup_leak_age_minutes:
        reason_codes.append(LINEUP_STALE_REASON)
    if signal.set_piece_xg_dependency >= config.high_set_piece_xg_dependency_threshold:
        reason_codes.append(XG_DEPENDENCY_REASON)
    if signal.upstream_reason_codes:
        reason_codes.append(UPSTREAM_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    sorted_reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

    return MarketResearchSoccerSetPieceTakerAvailabilityDigestRow(
        condition_id=signal.condition_id,
        market_slug=signal.market_slug,
        club=signal.club,
        opponent=signal.opponent,
        match_ref=signal.match_ref,
        match_start_at=signal.match_start_at,
        observed_at=signal.observed_at,
        primary_taker_availability_score=signal.primary_taker_availability_score,
        secondary_taker_readiness_score=signal.secondary_taker_readiness_score,
        injury_suspension_count=signal.injury_suspension_count,
        lineup_leak_age_minutes=signal.lineup_leak_age_minutes,
        set_piece_xg_dependency=signal.set_piece_xg_dependency,
        source_disagreement_count=signal.source_disagreement_count,
        availability_edge_score=edge_score,
        upstream_reason_codes=signal.upstream_reason_codes,
        signal_ref=signal.signal_ref,
        digest_status=_row_status(sorted_reason_codes),
        reason_codes=sorted_reason_codes,
    )


def _availability_edge_score(
    signal: MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal,
    *,
    config: MarketResearchSoccerSetPieceTakerAvailabilityDigestConfig,
) -> Decimal:
    primary_gap = ONE - signal.primary_taker_availability_score
    secondary_gap = ONE - signal.secondary_taker_readiness_score
    injury_pressure = _capped_ratio(
        signal.injury_suspension_count,
        config.injury_suspension_blocked_count,
    )
    source_pressure = _capped_ratio(
        signal.source_disagreement_count,
        config.max_source_disagreement_count + ONE,
    )
    return _quantize(
        (primary_gap * PRIMARY_AVAILABILITY_WEIGHT)
        + (secondary_gap * SECONDARY_READINESS_WEIGHT)
        + (signal.set_piece_xg_dependency * SET_PIECE_XG_WEIGHT)
        + (injury_pressure * INJURY_SUSPENSION_WEIGHT)
        + (source_pressure * SOURCE_DISAGREEMENT_WEIGHT),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount(
            reason_code=reason_code,
            signal_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal],
) -> tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain soccer set-piece taker availability items")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError(
            "signals must contain soccer set-piece taker availability items",
        ) from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestSignal items",
            )
        _require_flags("signal", signal)
        identifier = (signal.condition_id, signal.match_ref, signal.club)
        if identifier in seen:
            raise ValueError("signals must not contain duplicate condition/match/club values")
        seen.add(identifier)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSoccerSetPieceTakerAvailabilityDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestRow items",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_rank)):
        raise ValueError("rows must be sorted deterministically")
    identifiers = tuple((row.condition_id, row.match_ref, row.club) for row in normalized)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("rows must not contain duplicate condition/match/club values")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 3:
            raise ValueError(
                "signal_config_versions entries must be match/club/version triples",
            )
        match_ref, club, config_version = item
        _require_canonical_string("signal_config_versions match_ref", match_ref)
        _require_canonical_string("signal_config_versions club", club)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("signal_config_versions match_ref", match_ref)
        _reject_sensitive_text("signal_config_versions club", club)
        _reject_sensitive_text(
            "signal_config_versions config_version",
            config_version,
        )
        identifier = (match_ref, club)
        if identifier in seen:
            raise ValueError("signal_config_versions match/club values must be unique")
        seen.add(identifier)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if (
            type(item)
            is not MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerSetPieceTakerAvailabilityDigestReasonCodeCount "
                "items",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: DIGEST_REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    codes = tuple(item.reason_code for item in normalized)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _validate_row(row: MarketResearchSoccerSetPieceTakerAvailabilityDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == PASS_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use the clear reason")
    if CLEAR_REASON in row.reason_codes and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must stand alone")


def _validate_report(
    report: MarketResearchSoccerSetPieceTakerAvailabilityDigestReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _whole(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_signal_count != _count_rows(report.rows, PASS_STATUS):
        raise ValueError("pass_signal_count must match rows")
    if report.watch_signal_count != _count_rows(report.rows, WATCH_STATUS):
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != _count_rows(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_signal_count must match rows")
    if (
        report.signal_count
        != report.pass_signal_count
        + report.watch_signal_count
        + report.blocked_signal_count
    ):
        raise ValueError("signal counts must reconcile")
    expected_reason_counts = (
        (SOURCE_DISAGREEMENT_REASON, report.source_disagreement_signal_count),
        (EDGE_BLOCKED_REASON, report.blocked_edge_score_signal_count),
        (EDGE_WATCH_REASON, report.watch_edge_score_signal_count),
        (PRIMARY_UNAVAILABLE_REASON, report.primary_taker_unavailable_signal_count),
        (PRIMARY_WATCH_REASON, report.primary_taker_watch_signal_count),
        (SECONDARY_READINESS_REASON, report.secondary_taker_readiness_gap_signal_count),
        (INJURY_SUSPENSION_REASON, report.injury_suspension_signal_count),
        (LINEUP_STALE_REASON, report.stale_lineup_leak_signal_count),
        (XG_DEPENDENCY_REASON, report.high_set_piece_xg_dependency_signal_count),
        (UPSTREAM_REASON, report.upstream_reason_signal_count),
    )
    for reason_code, field_value in expected_reason_counts:
        if field_value != _count_reason(report.rows, reason_code):
            raise ValueError("reason count fields must match rows")
    if report.max_availability_edge_score != _max_or_zero(
        row.availability_edge_score for row in report.rows
    ):
        raise ValueError("max_availability_edge_score must match rows")
    if report.average_availability_edge_score != _average(
        row.availability_edge_score for row in report.rows
    ):
        raise ValueError("average_availability_edge_score must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = (
        BLOCKED_STATUS
        if any(row.digest_status == BLOCKED_STATUS for row in report.rows)
        else WATCH_STATUS
        if any(row.digest_status == WATCH_STATUS for row in report.rows)
        else PASS_STATUS
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{name} contains invalid reason code for this field")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must not contain duplicates")
    sorted_codes = _sort_reason_codes(reason_codes, allowed)
    if reason_codes != sorted_codes:
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _normalize_upstream_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_canonical_string(name, reason_code)
        _reject_sensitive_text(name, reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{name} must be sorted")
    return reason_codes


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in reason_codes for reason_code in BLOCKED_ROW_REASONS):
        return BLOCKED_STATUS
    if reason_codes == (CLEAR_REASON,):
        return PASS_STATUS
    return WATCH_STATUS


def _row_sort_rank(
    row: MarketResearchSoccerSetPieceTakerAvailabilityDigestRow,
) -> tuple[object, ...]:
    status_rank = {
        BLOCKED_STATUS: 0,
        WATCH_STATUS: 1,
        PASS_STATUS: 2,
    }[row.digest_status]
    return (
        status_rank,
        -row.availability_edge_score,
        row.match_start_at,
        row.condition_id,
        row.market_slug,
        row.club,
        row.opponent,
        row.signal_ref,
    )


def _count_rows(
    rows: tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestRow, ...],
    status: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if row.digest_status == status))


def _count_reason(
    rows: tuple[MarketResearchSoccerSetPieceTakerAvailabilityDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must not exceed one")
    return normalized


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _whole(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize(max(items))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return _quantize(ratio)


def _elapsed_seconds(start_at: datetime, end_at: datetime) -> Decimal:
    delta = end_at - start_at
    seconds = Decimal((delta.days * 86400) + delta.seconds)
    return seconds + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if value.lower() != value or any(character not in _SAFE_CHARS for character in value):
        raise ValueError(f"{name} must be a canonical lowercase token")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(word in lowered for word in _BLOCKED_WORDS):
        raise ValueError(f"{name} contains unsafe source detail")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
