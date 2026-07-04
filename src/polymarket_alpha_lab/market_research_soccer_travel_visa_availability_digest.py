"""Pure Phase 1 reducer for soccer travel visa availability research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_VISA_AVAILABILITY_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-travel-visa-availability-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal(3600)
MICROSECONDS_PER_SECOND = Decimal(1000000)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

CONFLICTING_SOURCES_REASON = "soccer_travel_visa_availability_conflicting_sources"
RISK_BLOCKED_REASON = "soccer_travel_visa_availability_risk_score_blocked"
VISA_BLOCKED_REASON = "soccer_travel_visa_availability_visa_blocked"
TRAVEL_BLOCKED_REASON = "soccer_travel_visa_availability_travel_blocked"
PLAYER_UNAVAILABLE_REASON = "soccer_travel_visa_availability_player_unavailable"
SOURCE_COVERAGE_GAP_REASON = "soccer_travel_visa_availability_source_coverage_gap"
RISK_WATCH_REASON = "soccer_travel_visa_availability_risk_score_watch"
VISA_WATCH_REASON = "soccer_travel_visa_availability_visa_watch"
TRAVEL_WATCH_REASON = "soccer_travel_visa_availability_travel_watch"
PLAYER_WATCH_REASON = "soccer_travel_visa_availability_player_watch"
CLEAR_REASON = "soccer_travel_visa_availability_clear"
PASSED_REASON = "soccer_travel_visa_availability_passed"
EMPTY_REASON = "soccer_travel_visa_availability_empty"

ROW_REASON_CODES = (
    CONFLICTING_SOURCES_REASON,
    RISK_BLOCKED_REASON,
    VISA_BLOCKED_REASON,
    TRAVEL_BLOCKED_REASON,
    PLAYER_UNAVAILABLE_REASON,
    SOURCE_COVERAGE_GAP_REASON,
    RISK_WATCH_REASON,
    VISA_WATCH_REASON,
    TRAVEL_WATCH_REASON,
    PLAYER_WATCH_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    CONFLICTING_SOURCES_REASON,
    RISK_BLOCKED_REASON,
    VISA_BLOCKED_REASON,
    TRAVEL_BLOCKED_REASON,
    PLAYER_UNAVAILABLE_REASON,
    SOURCE_COVERAGE_GAP_REASON,
    RISK_WATCH_REASON,
    VISA_WATCH_REASON,
    TRAVEL_WATCH_REASON,
    PLAYER_WATCH_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = (*ROW_REASON_CODES, PASSED_REASON, EMPTY_REASON)
BLOCKED_ROW_REASONS = (
    CONFLICTING_SOURCES_REASON,
    RISK_BLOCKED_REASON,
    VISA_BLOCKED_REASON,
    TRAVEL_BLOCKED_REASON,
    PLAYER_UNAVAILABLE_REASON,
)

CLEARED_VISA_STATUSES = ("cleared",)
WATCH_VISA_STATUSES = ("pending", "unknown")
BLOCKED_VISA_STATUSES = ("denied", "expired", "not_issued")
VISA_STATUSES = (*CLEARED_VISA_STATUSES, *WATCH_VISA_STATUSES, *BLOCKED_VISA_STATUSES)

CLEARED_TRAVEL_STATUSES = ("cleared",)
WATCH_TRAVEL_STATUSES = ("pending", "unknown")
BLOCKED_TRAVEL_STATUSES = ("blocked", "not_arrived")
TRAVEL_STATUSES = (
    *CLEARED_TRAVEL_STATUSES,
    *WATCH_TRAVEL_STATUSES,
    *BLOCKED_TRAVEL_STATUSES,
)

AVAILABLE_PLAYER_STATUSES = ("available",)
WATCH_PLAYER_STATUSES = ("questionable", "doubtful", "unknown")
BLOCKED_PLAYER_STATUSES = ("unavailable", "suspended", "out")
PLAYER_STATUSES = (
    *AVAILABLE_PLAYER_STATUSES,
    *WATCH_PLAYER_STATUSES,
    *BLOCKED_PLAYER_STATUSES,
)

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_soccer_travel_visa_availability_monitoring",
    WATCH_STATUS: "review_report_only_soccer_travel_visa_availability_watchlist",
    BLOCKED_STATUS: "block_report_only_soccer_travel_visa_availability_review",
}

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
    "pay" "load_" "json",
    "priv" "ate_" "key",
    "ex" "change",
    "net" "work",
    "sec" "ret",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_VISA_AVAILABILITY_DIGEST_CONFIG_VERSION",
    "MarketResearchSoccerTravelVisaAvailabilityDigestConfig",
    "MarketResearchSoccerTravelVisaAvailabilityDigestSignal",
    "MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount",
    "MarketResearchSoccerTravelVisaAvailabilityDigestRow",
    "MarketResearchSoccerTravelVisaAvailabilityDigestReport",
    "build_market_research_soccer_travel_visa_availability_digest",
    "market_research_soccer_travel_visa_availability_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSoccerTravelVisaAvailabilityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_VISA_AVAILABILITY_DIGEST_CONFIG_VERSION
    )
    blocked_risk_score_threshold: Decimal = Decimal("0.800000")
    watch_risk_score_threshold: Decimal = Decimal("0.400000")
    max_input_age_hours: Decimal = Decimal("24.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_conflicting_source_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTravelVisaAvailabilityDigestConfig:
            raise TypeError(
                "MarketResearchSoccerTravelVisaAvailabilityDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTravelVisaAvailabilityDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchSoccerTravelVisaAvailabilityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "blocked_risk_score_threshold",
            "watch_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_input_age_hours",
            _normalize_nonnegative_decimal(
                "max_input_age_hours",
                self.max_input_age_hours,
            ),
        )
        for field_name in ("min_source_count", "max_conflicting_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_risk_score_threshold > self.blocked_risk_score_threshold:
            raise ValueError(
                "watch_risk_score_threshold must not exceed "
                "blocked_risk_score_threshold",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelVisaAvailabilityDigestSignal:
    condition_id: str
    market_slug: str
    competition_id: str
    match_ref: str
    team_id: str
    player_id: str
    player_role: str
    match_start_at: datetime
    observed_at: datetime
    visa_status: str
    travel_status: str
    player_availability_status: str
    risk_score: Decimal
    source_count: Decimal
    conflicting_source_count: Decimal
    signal_ref: str
    signal_config_version: str = "soccer-travel-visa-availability-feed-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTravelVisaAvailabilityDigestSignal:
            raise TypeError(
                "MarketResearchSoccerTravelVisaAvailabilityDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTravelVisaAvailabilityDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchSoccerTravelVisaAvailabilityDigestSignal",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "competition_id",
            "match_ref",
            "team_id",
            "player_id",
            "player_role",
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
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_member("visa_status", self.visa_status, VISA_STATUSES)
        _require_member("travel_status", self.travel_status, TRAVEL_STATUSES)
        _require_member(
            "player_availability_status",
            self.player_availability_status,
            PLAYER_STATUSES,
        )
        object.__setattr__(
            self,
            "risk_score",
            _normalize_probability_decimal("risk_score", self.risk_score),
        )
        for field_name in ("source_count", "conflicting_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount:
    reason_code: str
    signal_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_whole_decimal("signal_count", self.signal_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelVisaAvailabilityDigestRow:
    condition_id: str
    market_slug: str
    competition_id: str
    match_ref: str
    team_id: str
    player_id: str
    player_role: str
    match_start_at: datetime
    observed_at: datetime
    visa_status: str
    travel_status: str
    player_availability_status: str
    risk_score: Decimal
    source_count: Decimal
    conflicting_source_count: Decimal
    signal_ref: str
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTravelVisaAvailabilityDigestRow:
            raise TypeError(
                "MarketResearchSoccerTravelVisaAvailabilityDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTravelVisaAvailabilityDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchSoccerTravelVisaAvailabilityDigestRow",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "competition_id",
            "match_ref",
            "team_id",
            "player_id",
            "player_role",
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
        _require_member("visa_status", self.visa_status, VISA_STATUSES)
        _require_member("travel_status", self.travel_status, TRAVEL_STATUSES)
        _require_member(
            "player_availability_status",
            self.player_availability_status,
            PLAYER_STATUSES,
        )
        object.__setattr__(
            self,
            "risk_score",
            _normalize_probability_decimal("risk_score", self.risk_score),
        )
        for field_name in ("source_count", "conflicting_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
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
class MarketResearchSoccerTravelVisaAvailabilityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    conflict_signal_count: Decimal
    blocked_risk_signal_count: Decimal
    watch_risk_signal_count: Decimal
    visa_blocked_signal_count: Decimal
    visa_watch_signal_count: Decimal
    travel_blocked_signal_count: Decimal
    travel_watch_signal_count: Decimal
    player_unavailable_signal_count: Decimal
    player_watch_signal_count: Decimal
    source_gap_signal_count: Decimal
    blocked_risk_score_threshold: Decimal
    watch_risk_score_threshold: Decimal
    max_input_age_hours: Decimal
    min_source_count: Decimal
    max_conflicting_source_count: Decimal
    max_risk_score_observed: Decimal | None
    average_risk_score: Decimal
    rows: tuple[MarketResearchSoccerTravelVisaAvailabilityDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTravelVisaAvailabilityDigestReport:
            raise TypeError(
                "MarketResearchSoccerTravelVisaAvailabilityDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTravelVisaAvailabilityDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchSoccerTravelVisaAvailabilityDigestReport",
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
            "conflict_signal_count",
            "blocked_risk_signal_count",
            "watch_risk_signal_count",
            "visa_blocked_signal_count",
            "visa_watch_signal_count",
            "travel_blocked_signal_count",
            "travel_watch_signal_count",
            "player_unavailable_signal_count",
            "player_watch_signal_count",
            "source_gap_signal_count",
            "max_input_age_hours",
            "min_source_count",
            "max_conflicting_source_count",
            "average_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_risk_score_threshold",
            "watch_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_risk_score_observed",
            _normalize_optional_probability_decimal(
                "max_risk_score_observed",
                self.max_risk_score_observed,
            ),
        )
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


def build_market_research_soccer_travel_visa_availability_digest(
    signals: Iterable[MarketResearchSoccerTravelVisaAvailabilityDigestSignal],
    *,
    config: MarketResearchSoccerTravelVisaAvailabilityDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerTravelVisaAvailabilityDigestReport:
    if type(config) is not MarketResearchSoccerTravelVisaAvailabilityDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchSoccerTravelVisaAvailabilityDigestConfig",
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

    return MarketResearchSoccerTravelVisaAvailabilityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        signal_count=_whole(len(rows)),
        pass_signal_count=_count_rows(rows, PASS_STATUS),
        watch_signal_count=_count_rows(rows, WATCH_STATUS),
        blocked_signal_count=_count_rows(rows, BLOCKED_STATUS),
        conflict_signal_count=_count_reason(rows, CONFLICTING_SOURCES_REASON),
        blocked_risk_signal_count=_count_reason(rows, RISK_BLOCKED_REASON),
        watch_risk_signal_count=_count_reason(rows, RISK_WATCH_REASON),
        visa_blocked_signal_count=_count_reason(rows, VISA_BLOCKED_REASON),
        visa_watch_signal_count=_count_reason(rows, VISA_WATCH_REASON),
        travel_blocked_signal_count=_count_reason(rows, TRAVEL_BLOCKED_REASON),
        travel_watch_signal_count=_count_reason(rows, TRAVEL_WATCH_REASON),
        player_unavailable_signal_count=_count_reason(rows, PLAYER_UNAVAILABLE_REASON),
        player_watch_signal_count=_count_reason(rows, PLAYER_WATCH_REASON),
        source_gap_signal_count=_count_reason(rows, SOURCE_COVERAGE_GAP_REASON),
        blocked_risk_score_threshold=config.blocked_risk_score_threshold,
        watch_risk_score_threshold=config.watch_risk_score_threshold,
        max_input_age_hours=config.max_input_age_hours,
        min_source_count=config.min_source_count,
        max_conflicting_source_count=config.max_conflicting_source_count,
        max_risk_score_observed=_max_or_none(row.risk_score for row in rows),
        average_risk_score=_average(row.risk_score for row in rows),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (
                        signal.match_ref,
                        signal.player_id,
                        signal.signal_config_version,
                    )
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_travel_visa_availability_digest_payload(
    report: MarketResearchSoccerTravelVisaAvailabilityDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerTravelVisaAvailabilityDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchSoccerTravelVisaAvailabilityDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _row_for_signal(
    signal: MarketResearchSoccerTravelVisaAvailabilityDigestSignal,
    *,
    config: MarketResearchSoccerTravelVisaAvailabilityDigestConfig,
) -> MarketResearchSoccerTravelVisaAvailabilityDigestRow:
    reason_codes = []
    if signal.conflicting_source_count > config.max_conflicting_source_count:
        reason_codes.append(CONFLICTING_SOURCES_REASON)
    if signal.risk_score >= config.blocked_risk_score_threshold:
        reason_codes.append(RISK_BLOCKED_REASON)
    elif signal.risk_score >= config.watch_risk_score_threshold:
        reason_codes.append(RISK_WATCH_REASON)
    if signal.visa_status in BLOCKED_VISA_STATUSES:
        reason_codes.append(VISA_BLOCKED_REASON)
    elif signal.visa_status in WATCH_VISA_STATUSES:
        reason_codes.append(VISA_WATCH_REASON)
    if signal.travel_status in BLOCKED_TRAVEL_STATUSES:
        reason_codes.append(TRAVEL_BLOCKED_REASON)
    elif signal.travel_status in WATCH_TRAVEL_STATUSES:
        reason_codes.append(TRAVEL_WATCH_REASON)
    if signal.player_availability_status in BLOCKED_PLAYER_STATUSES:
        reason_codes.append(PLAYER_UNAVAILABLE_REASON)
    elif signal.player_availability_status in WATCH_PLAYER_STATUSES:
        reason_codes.append(PLAYER_WATCH_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(SOURCE_COVERAGE_GAP_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    sorted_reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

    return MarketResearchSoccerTravelVisaAvailabilityDigestRow(
        condition_id=signal.condition_id,
        market_slug=signal.market_slug,
        competition_id=signal.competition_id,
        match_ref=signal.match_ref,
        team_id=signal.team_id,
        player_id=signal.player_id,
        player_role=signal.player_role,
        match_start_at=signal.match_start_at,
        observed_at=signal.observed_at,
        visa_status=signal.visa_status,
        travel_status=signal.travel_status,
        player_availability_status=signal.player_availability_status,
        risk_score=signal.risk_score,
        source_count=signal.source_count,
        conflicting_source_count=signal.conflicting_source_count,
        signal_ref=signal.signal_ref,
        digest_status=_row_status(sorted_reason_codes),
        reason_codes=sorted_reason_codes,
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount(
            reason_code=reason_code,
            signal_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchSoccerTravelVisaAvailabilityDigestSignal],
) -> tuple[MarketResearchSoccerTravelVisaAvailabilityDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain soccer travel visa availability items")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must contain soccer travel visa availability items") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchSoccerTravelVisaAvailabilityDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchSoccerTravelVisaAvailabilityDigestSignal items",
            )
        _require_flags("signal", signal)
        identifier = (signal.condition_id, signal.match_ref, signal.player_id)
        if identifier in seen:
            raise ValueError("signals must not contain duplicate condition/match/player values")
        seen.add(identifier)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerTravelVisaAvailabilityDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSoccerTravelVisaAvailabilityDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchSoccerTravelVisaAvailabilityDigestRow items",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_rank)):
        raise ValueError("rows must be sorted deterministically")
    identifiers = tuple(
        (row.condition_id, row.match_ref, row.player_id)
        for row in normalized
    )
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("rows must not contain duplicate condition/match/player values")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 3:
            raise ValueError(
                "signal_config_versions entries must be match/player/version triples",
            )
        match_ref, player_id, config_version = item
        _require_canonical_string("signal_config_versions match_ref", match_ref)
        _require_canonical_string("signal_config_versions player_id", player_id)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("signal_config_versions match_ref", match_ref)
        _reject_sensitive_text("signal_config_versions player_id", player_id)
        _reject_sensitive_text(
            "signal_config_versions config_version",
            config_version,
        )
        identifier = (match_ref, player_id)
        if identifier in seen:
            raise ValueError(
                "signal_config_versions match/player values must be unique",
            )
        seen.add(identifier)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerTravelVisaAvailabilityDigestReasonCodeCount items",
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


def _validate_row(row: MarketResearchSoccerTravelVisaAvailabilityDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == PASS_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use the clear reason")
    if CLEAR_REASON in row.reason_codes and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must stand alone")
    if row.conflicting_source_count > row.source_count:
        raise ValueError("conflicting_source_count must not exceed source_count")


def _validate_report(report: MarketResearchSoccerTravelVisaAvailabilityDigestReport) -> None:
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
        (CONFLICTING_SOURCES_REASON, report.conflict_signal_count),
        (RISK_BLOCKED_REASON, report.blocked_risk_signal_count),
        (RISK_WATCH_REASON, report.watch_risk_signal_count),
        (VISA_BLOCKED_REASON, report.visa_blocked_signal_count),
        (VISA_WATCH_REASON, report.visa_watch_signal_count),
        (TRAVEL_BLOCKED_REASON, report.travel_blocked_signal_count),
        (TRAVEL_WATCH_REASON, report.travel_watch_signal_count),
        (PLAYER_UNAVAILABLE_REASON, report.player_unavailable_signal_count),
        (PLAYER_WATCH_REASON, report.player_watch_signal_count),
        (SOURCE_COVERAGE_GAP_REASON, report.source_gap_signal_count),
    )
    for reason_code, field_value in expected_reason_counts:
        if field_value != _count_reason(report.rows, reason_code):
            raise ValueError("reason count fields must match rows")
    if report.max_risk_score_observed != _max_or_none(row.risk_score for row in report.rows):
        raise ValueError("max_risk_score_observed must match rows")
    if report.average_risk_score != _average(row.risk_score for row in report.rows):
        raise ValueError("average_risk_score must match rows")
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
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in fields(value)
        }
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


def _row_sort_rank(row: MarketResearchSoccerTravelVisaAvailabilityDigestRow) -> tuple[object, ...]:
    status_rank = {
        BLOCKED_STATUS: 0,
        WATCH_STATUS: 1,
        PASS_STATUS: 2,
    }[row.digest_status]
    return (
        status_rank,
        -row.risk_score,
        row.match_start_at,
        row.condition_id,
        row.market_slug,
        row.competition_id,
        row.team_id,
        row.player_id,
        row.signal_ref,
    )


def _count_rows(
    rows: tuple[MarketResearchSoccerTravelVisaAvailabilityDigestRow, ...],
    status: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if row.digest_status == status))


def _count_reason(
    rows: tuple[MarketResearchSoccerTravelVisaAvailabilityDigestRow, ...],
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


def _normalize_optional_probability_decimal(
    name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability_decimal(name, value)


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


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(max(items))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _elapsed_seconds(start_at: datetime, end_at: datetime) -> Decimal:
    delta = end_at - start_at
    seconds = Decimal((delta.days * 86400) + delta.seconds)
    return seconds + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


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
