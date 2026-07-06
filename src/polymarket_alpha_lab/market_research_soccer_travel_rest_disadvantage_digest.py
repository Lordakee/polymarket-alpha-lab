"""Pure Phase 1 soccer travel rest disadvantage digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-travel-rest-disadvantage-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
VENUE_ROLES = ("home", "away", "neutral")

SHORT_REST_REASON = "soccer_travel_rest_disadvantage_short_rest"
REST_GAP_REASON = "soccer_travel_rest_disadvantage_rest_gap"
TRAVEL_LOAD_REASON = "soccer_travel_rest_disadvantage_travel_load"
TIMEZONE_SHIFT_REASON = "soccer_travel_rest_disadvantage_timezone_shift"
AWAY_REASON = "soccer_travel_rest_disadvantage_away"
SOURCE_GAP_REASON = "soccer_travel_rest_disadvantage_source_gap"
BLOCKED_ROW_REASON = "soccer_travel_rest_disadvantage_blocked"
WATCH_ROW_REASON = "soccer_travel_rest_disadvantage_watch"
CLEAR_ROW_REASON = "soccer_travel_rest_disadvantage_clear"

BLOCKED_PRESENT_REASON = "soccer_travel_rest_disadvantage_blocked_present"
WATCH_PRESENT_REASON = "soccer_travel_rest_disadvantage_watch_present"
SHORT_REST_PRESENT_REASON = "soccer_travel_rest_disadvantage_short_rest_present"
REST_GAP_PRESENT_REASON = "soccer_travel_rest_disadvantage_rest_gap_present"
TRAVEL_LOAD_PRESENT_REASON = "soccer_travel_rest_disadvantage_travel_load_present"
TIMEZONE_SHIFT_PRESENT_REASON = (
    "soccer_travel_rest_disadvantage_timezone_shift_present"
)
AWAY_PRESENT_REASON = "soccer_travel_rest_disadvantage_away_present"
SOURCE_GAP_PRESENT_REASON = "soccer_travel_rest_disadvantage_source_gap_present"
DIGEST_CLEAR_REASON = "soccer_travel_rest_disadvantage_digest_clear"
DIGEST_EMPTY_REASON = "soccer_travel_rest_disadvantage_digest_empty"

ROW_SIGNAL_REASON_CODES = (
    SHORT_REST_REASON,
    REST_GAP_REASON,
    TRAVEL_LOAD_REASON,
    TIMEZONE_SHIFT_REASON,
    AWAY_REASON,
    SOURCE_GAP_REASON,
)
ROW_REASON_CODES = (
    *ROW_SIGNAL_REASON_CODES,
    BLOCKED_ROW_REASON,
    WATCH_ROW_REASON,
    CLEAR_ROW_REASON,
)
REPORT_REASON_CODES = (
    BLOCKED_PRESENT_REASON,
    WATCH_PRESENT_REASON,
    SHORT_REST_PRESENT_REASON,
    REST_GAP_PRESENT_REASON,
    TRAVEL_LOAD_PRESENT_REASON,
    TIMEZONE_SHIFT_PRESENT_REASON,
    AWAY_PRESENT_REASON,
    SOURCE_GAP_PRESENT_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)

REPORT_REASON_TO_ROW_REASON = {
    BLOCKED_PRESENT_REASON: BLOCKED_ROW_REASON,
    WATCH_PRESENT_REASON: WATCH_ROW_REASON,
    SHORT_REST_PRESENT_REASON: SHORT_REST_REASON,
    REST_GAP_PRESENT_REASON: REST_GAP_REASON,
    TRAVEL_LOAD_PRESENT_REASON: TRAVEL_LOAD_REASON,
    TIMEZONE_SHIFT_PRESENT_REASON: TIMEZONE_SHIFT_REASON,
    AWAY_PRESENT_REASON: AWAY_REASON,
    SOURCE_GAP_PRESENT_REASON: SOURCE_GAP_REASON,
    DIGEST_CLEAR_REASON: CLEAR_ROW_REASON,
}

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_soccer_travel_rest_disadvantage_monitoring",
    WATCH_STATUS: "review_report_only_soccer_travel_rest_disadvantage_watchlist",
    BLOCKED_STATUS: "block_report_only_soccer_travel_rest_disadvantage_review",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_DENOMINATOR = Decimal("6.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "MarketResearchSoccerTravelRestDisadvantageDigestConfig",
    "MarketResearchSoccerTravelRestDisadvantageDigestSignal",
    "MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount",
    "MarketResearchSoccerTravelRestDisadvantageDigestRow",
    "MarketResearchSoccerTravelRestDisadvantageDigestReport",
    "build_market_research_soccer_travel_rest_disadvantage_digest",
    "market_research_soccer_travel_rest_disadvantage_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchSoccerTravelRestDisadvantageDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION
    )
    short_rest_hours: Decimal = Decimal("72.000000")
    rest_disadvantage_hours: Decimal = Decimal("24.000000")
    long_travel_distance_km: Decimal = Decimal("2500.000000")
    timezone_shift_hours: Decimal = Decimal("3.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_signal_count: Decimal = Decimal("2.000000")
    blocked_signal_count: Decimal = Decimal("4.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerTravelRestDisadvantageDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "short_rest_hours",
            "rest_disadvantage_hours",
            "long_travel_distance_km",
            "timezone_shift_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_count",
            "watch_signal_count",
            "blocked_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_signal_count > self.blocked_signal_count:
            raise ValueError("watch_signal_count must not exceed blocked_signal_count")
        if self.blocked_signal_count > SIGNAL_DENOMINATOR:
            raise ValueError("blocked_signal_count must not exceed signal denominator")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelRestDisadvantageDigestSignal(_NoSubclass):
    signal_id: str
    fixture_id: str
    competition_id: str
    team_id: str
    opponent_id: str
    venue_role: str
    observed_at: datetime
    team_rest_hours: Decimal
    opponent_rest_hours: Decimal
    travel_distance_km: Decimal
    timezone_shift_hours: Decimal
    source_count: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerTravelRestDisadvantageDigestSignal,
            "signal",
        )
        for field_name in (
            "signal_id",
            "fixture_id",
            "competition_id",
            "team_id",
            "opponent_id",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "venue_role",
            _require_member("venue_role", self.venue_role, VENUE_ROLES),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "team_rest_hours",
            "opponent_rest_hours",
            "travel_distance_km",
            "timezone_shift_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_whole_decimal("source_count", self.source_count),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    signal_count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "signal_count",
            _require_positive_whole_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelRestDisadvantageDigestRow(_NoSubclass):
    signal_id: str
    fixture_id: str
    competition_id: str
    team_id: str
    opponent_id: str
    venue_role: str
    observed_at: datetime
    team_rest_hours: Decimal
    opponent_rest_hours: Decimal
    rest_disadvantage_hours: Decimal
    travel_distance_km: Decimal
    timezone_shift_hours: Decimal
    source_count: Decimal
    disadvantage_signal_count: Decimal
    disadvantage_pressure_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerTravelRestDisadvantageDigestRow,
            "row",
        )
        for field_name in (
            "signal_id",
            "fixture_id",
            "competition_id",
            "team_id",
            "opponent_id",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "venue_role",
            _require_member("venue_role", self.venue_role, VENUE_ROLES),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "team_rest_hours",
            "opponent_rest_hours",
            "rest_disadvantage_hours",
            "travel_distance_km",
            "timezone_shift_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "disadvantage_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "disadvantage_pressure_score",
            _require_ratio_decimal(
                "disadvantage_pressure_score",
                self.disadvantage_pressure_score,
            ),
        )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerTravelRestDisadvantageDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    blocked_signal_count: Decimal
    watch_signal_count: Decimal
    pass_signal_count: Decimal
    short_rest_signal_count: Decimal
    rest_gap_signal_count: Decimal
    travel_load_signal_count: Decimal
    timezone_shift_signal_count: Decimal
    away_signal_count: Decimal
    source_gap_signal_count: Decimal
    max_disadvantage_pressure_score: Decimal
    average_disadvantage_pressure_score: Decimal
    min_team_rest_hours: Decimal
    max_rest_disadvantage_hours: Decimal
    max_travel_distance_km: Decimal
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchSoccerTravelRestDisadvantageDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "blocked_signal_count",
            "watch_signal_count",
            "pass_signal_count",
            "short_rest_signal_count",
            "rest_gap_signal_count",
            "travel_load_signal_count",
            "timezone_shift_signal_count",
            "away_signal_count",
            "source_gap_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_disadvantage_pressure_score",
            "average_disadvantage_pressure_score",
            "min_team_rest_hours",
            "max_rest_disadvantage_hours",
            "max_travel_distance_km",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_disadvantage_pressure_score",
            "average_disadvantage_pressure_score",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_soccer_travel_rest_disadvantage_digest(
    signals: tuple[MarketResearchSoccerTravelRestDisadvantageDigestSignal, ...],
    *,
    config: MarketResearchSoccerTravelRestDisadvantageDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerTravelRestDisadvantageDigestReport:
    if type(config) is not MarketResearchSoccerTravelRestDisadvantageDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchSoccerTravelRestDisadvantageDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    rows = tuple(
        sorted(
            (
                _row_for_signal(signal, config=config)
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)

    return MarketResearchSoccerTravelRestDisadvantageDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(rows),
        recommended_next_step=NEXT_STEP_BY_STATUS[_digest_status(rows)],
        signal_count=_count_decimal(len(rows)),
        blocked_signal_count=_status_count(rows, BLOCKED_STATUS),
        watch_signal_count=_status_count(rows, WATCH_STATUS),
        pass_signal_count=_status_count(rows, PASS_STATUS),
        short_rest_signal_count=_reason_count(rows, SHORT_REST_REASON),
        rest_gap_signal_count=_reason_count(rows, REST_GAP_REASON),
        travel_load_signal_count=_reason_count(rows, TRAVEL_LOAD_REASON),
        timezone_shift_signal_count=_reason_count(rows, TIMEZONE_SHIFT_REASON),
        away_signal_count=_reason_count(rows, AWAY_REASON),
        source_gap_signal_count=_reason_count(rows, SOURCE_GAP_REASON),
        max_disadvantage_pressure_score=_max_row_decimal(
            rows,
            "disadvantage_pressure_score",
        ),
        average_disadvantage_pressure_score=_average_decimal(
            tuple(row.disadvantage_pressure_score for row in rows),
        ),
        min_team_rest_hours=_min_row_decimal(rows, "team_rest_hours"),
        max_rest_disadvantage_hours=_max_row_decimal(rows, "rest_disadvantage_hours"),
        max_travel_distance_km=_max_row_decimal(rows, "travel_distance_km"),
        rows=rows,
        signal_config_versions=_signal_config_versions(rows),
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_soccer_travel_rest_disadvantage_digest_payload(
    report: MarketResearchSoccerTravelRestDisadvantageDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerTravelRestDisadvantageDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchSoccerTravelRestDisadvantageDigestReport",
        )
    _revalidate_payload_dataclass(report)
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report payload must be a mapping")
    return value


def _row_for_signal(
    signal: MarketResearchSoccerTravelRestDisadvantageDigestSignal,
    *,
    config: MarketResearchSoccerTravelRestDisadvantageDigestConfig,
) -> MarketResearchSoccerTravelRestDisadvantageDigestRow:
    signal_reasons: list[str] = []
    rest_disadvantage_hours = _quantize_result(
        max(signal.opponent_rest_hours - signal.team_rest_hours, ZERO),
    )
    if signal.team_rest_hours <= config.short_rest_hours:
        signal_reasons.append(SHORT_REST_REASON)
    if rest_disadvantage_hours >= config.rest_disadvantage_hours:
        signal_reasons.append(REST_GAP_REASON)
    if signal.travel_distance_km >= config.long_travel_distance_km:
        signal_reasons.append(TRAVEL_LOAD_REASON)
    if signal.timezone_shift_hours >= config.timezone_shift_hours:
        signal_reasons.append(TIMEZONE_SHIFT_REASON)
    if signal.venue_role == "away":
        signal_reasons.append(AWAY_REASON)
    if signal.source_count < config.min_source_count:
        signal_reasons.append(SOURCE_GAP_REASON)

    disadvantage_signal_count = _count_decimal(len(signal_reasons))
    digest_status = _row_status(disadvantage_signal_count, config=config)
    return MarketResearchSoccerTravelRestDisadvantageDigestRow(
        signal_id=signal.signal_id,
        fixture_id=signal.fixture_id,
        competition_id=signal.competition_id,
        team_id=signal.team_id,
        opponent_id=signal.opponent_id,
        venue_role=signal.venue_role,
        observed_at=signal.observed_at,
        team_rest_hours=signal.team_rest_hours,
        opponent_rest_hours=signal.opponent_rest_hours,
        rest_disadvantage_hours=rest_disadvantage_hours,
        travel_distance_km=signal.travel_distance_km,
        timezone_shift_hours=signal.timezone_shift_hours,
        source_count=signal.source_count,
        disadvantage_signal_count=disadvantage_signal_count,
        disadvantage_pressure_score=_ratio(
            disadvantage_signal_count,
            SIGNAL_DENOMINATOR,
        ),
        digest_status=digest_status,
        reason_codes=_row_reason_codes(tuple(signal_reasons), digest_status),
        signal_config_version=signal.signal_config_version,
    )


def _row_status(
    signal_count: Decimal,
    *,
    config: MarketResearchSoccerTravelRestDisadvantageDigestConfig,
) -> str:
    if signal_count >= config.blocked_signal_count:
        return BLOCKED_STATUS
    if signal_count >= config.watch_signal_count:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(signal_reasons: tuple[str, ...], digest_status: str) -> tuple[str, ...]:
    reason_codes = list(signal_reasons)
    if digest_status == BLOCKED_STATUS:
        reason_codes.append(BLOCKED_ROW_REASON)
    elif digest_status == WATCH_STATUS:
        reason_codes.append(WATCH_ROW_REASON)
    else:
        reason_codes.append(CLEAR_ROW_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _digest_status(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.digest_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        reason_codes.append(BLOCKED_PRESENT_REASON)
    if any(row.digest_status == WATCH_STATUS for row in rows):
        reason_codes.append(WATCH_PRESENT_REASON)
    if _reason_count(rows, SHORT_REST_REASON) > ZERO:
        reason_codes.append(SHORT_REST_PRESENT_REASON)
    if _reason_count(rows, REST_GAP_REASON) > ZERO:
        reason_codes.append(REST_GAP_PRESENT_REASON)
    if _reason_count(rows, TRAVEL_LOAD_REASON) > ZERO:
        reason_codes.append(TRAVEL_LOAD_PRESENT_REASON)
    if _reason_count(rows, TIMEZONE_SHIFT_REASON) > ZERO:
        reason_codes.append(TIMEZONE_SHIFT_PRESENT_REASON)
    if _reason_count(rows, AWAY_REASON) > ZERO:
        reason_codes.append(AWAY_PRESENT_REASON)
    if _reason_count(rows, SOURCE_GAP_REASON) > ZERO:
        reason_codes.append(SOURCE_GAP_PRESENT_REASON)
    if not reason_codes:
        reason_codes.append(DIGEST_CLEAR_REASON)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
) -> tuple[MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount(
            reason_code=reason_code,
            signal_count=_report_reason_count(reason_code, rows),
            signal_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
) -> Decimal:
    if reason_code == DIGEST_EMPTY_REASON:
        return ONE
    row_reason = REPORT_REASON_TO_ROW_REASON[reason_code]
    return _reason_count(rows, row_reason)


def _validate_row(row: MarketResearchSoccerTravelRestDisadvantageDigestRow) -> None:
    expected_rest_gap = _quantize_result(
        max(row.opponent_rest_hours - row.team_rest_hours, ZERO),
    )
    if row.rest_disadvantage_hours != expected_rest_gap:
        raise ValueError("rest_disadvantage_hours must match rest inputs")
    signal_count = _count_decimal(
        sum(1 for reason_code in ROW_SIGNAL_REASON_CODES if reason_code in row.reason_codes),
    )
    if row.disadvantage_signal_count != signal_count:
        raise ValueError("disadvantage_signal_count must match reason_codes")
    if row.disadvantage_pressure_score != _ratio(signal_count, SIGNAL_DENOMINATOR):
        raise ValueError("disadvantage_pressure_score must match reason_codes")
    if row.digest_status == PASS_STATUS and row.reason_codes != (CLEAR_ROW_REASON,):
        raise ValueError("pass rows must use only the clear reason")
    if row.digest_status == WATCH_STATUS:
        if WATCH_ROW_REASON not in row.reason_codes:
            raise ValueError("reason_codes must match digest_status")
        if BLOCKED_ROW_REASON in row.reason_codes or CLEAR_ROW_REASON in row.reason_codes:
            raise ValueError("reason_codes must match digest_status")
    if row.digest_status == BLOCKED_STATUS:
        if BLOCKED_ROW_REASON not in row.reason_codes:
            raise ValueError("reason_codes must match digest_status")
        if WATCH_ROW_REASON in row.reason_codes or CLEAR_ROW_REASON in row.reason_codes:
            raise ValueError("reason_codes must match digest_status")


def _validate_report(report: MarketResearchSoccerTravelRestDisadvantageDigestReport) -> None:
    for row in report.rows:
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be in the future")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _count_decimal(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.blocked_signal_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_signal_count must match rows")
    if report.watch_signal_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_signal_count must match rows")
    if report.pass_signal_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_signal_count must match rows")
    if (
        report.signal_count
        != report.blocked_signal_count
        + report.watch_signal_count
        + report.pass_signal_count
    ):
        raise ValueError("status counts must reconcile")
    expected_reason_fields = (
        ("short_rest_signal_count", SHORT_REST_REASON),
        ("rest_gap_signal_count", REST_GAP_REASON),
        ("travel_load_signal_count", TRAVEL_LOAD_REASON),
        ("timezone_shift_signal_count", TIMEZONE_SHIFT_REASON),
        ("away_signal_count", AWAY_REASON),
        ("source_gap_signal_count", SOURCE_GAP_REASON),
    )
    for field_name, reason_code in expected_reason_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_disadvantage_pressure_score != _max_row_decimal(
        report.rows,
        "disadvantage_pressure_score",
    ):
        raise ValueError("max_disadvantage_pressure_score must match rows")
    if report.average_disadvantage_pressure_score != _average_decimal(
        tuple(row.disadvantage_pressure_score for row in report.rows),
    ):
        raise ValueError("average_disadvantage_pressure_score must match rows")
    if report.min_team_rest_hours != _min_row_decimal(report.rows, "team_rest_hours"):
        raise ValueError("min_team_rest_hours must match rows")
    if report.max_rest_disadvantage_hours != _max_row_decimal(
        report.rows,
        "rest_disadvantage_hours",
    ):
        raise ValueError("max_rest_disadvantage_hours must match rows")
    if report.max_travel_distance_km != _max_row_decimal(
        report.rows,
        "travel_distance_km",
    ):
        raise ValueError("max_travel_distance_km must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.signal_config_versions != _signal_config_versions(report.rows):
        raise ValueError("signal_config_versions must match rows")


def _normalize_signals(
    signals: tuple[MarketResearchSoccerTravelRestDisadvantageDigestSignal, ...],
) -> tuple[MarketResearchSoccerTravelRestDisadvantageDigestSignal, ...]:
    if type(signals) is not tuple:
        raise ValueError("signals must be a tuple")
    seen_signal_ids: set[str] = set()
    seen_fixture_teams: set[tuple[str, str]] = set()
    normalized: list[MarketResearchSoccerTravelRestDisadvantageDigestSignal] = []
    for signal in signals:
        if type(signal) is not MarketResearchSoccerTravelRestDisadvantageDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchSoccerTravelRestDisadvantageDigestSignal items",
            )
        _revalidate_payload_dataclass(signal)
        signal = MarketResearchSoccerTravelRestDisadvantageDigestSignal(
            **{field.name: getattr(signal, field.name) for field in fields(signal)},
        )
        if signal.signal_id in seen_signal_ids:
            raise ValueError("signals must not contain duplicate signal_id values")
        seen_signal_ids.add(signal.signal_id)
        fixture_team = (signal.fixture_id, signal.team_id)
        if fixture_team in seen_fixture_teams:
            raise ValueError("signals must not contain duplicate fixture/team values")
        seen_fixture_teams.add(fixture_team)
        normalized.append(signal)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchSoccerTravelRestDisadvantageDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchSoccerTravelRestDisadvantageDigestRow items",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    signal_ids = tuple(row.signal_id for row in rows)
    if len(set(signal_ids)) != len(signal_ids):
        raise ValueError("rows must not contain duplicate signal_id values")
    fixture_teams = tuple((row.fixture_id, row.team_id) for row in rows)
    if len(set(fixture_teams)) != len(fixture_teams):
        raise ValueError("rows must not contain duplicate fixture/team values")
    return rows


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("signal_config_versions must be a tuple")
    for item in value:
        if type(item) is not tuple or len(item) != 3:
            raise ValueError("signal_config_versions entries must be triples")
        fixture_id, team_id, config_version = item
        _require_canonical_string("signal_config_versions fixture_id", fixture_id)
        _require_canonical_string("signal_config_versions team_id", team_id)
        _require_canonical_string("signal_config_versions config_version", config_version)
    if value != tuple(sorted(value)):
        raise ValueError("signal_config_versions must be sorted")
    identifiers = tuple((item[0], item[1]) for item in value)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("signal_config_versions must not contain duplicate fixture/team values")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount items",
            )
        _require_hard_flags("reason_code_count", item)
    if value != tuple(sorted(value, key=lambda item: REPORT_REASON_CODES.index(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    reason_codes = tuple(item.reason_code for item in value)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts must not contain duplicates")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_member("reason_code", reason_code, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    if value != tuple(sorted(value, key=lambda item: allowed.index(item))):
        raise ValueError(f"{field_name} must be sorted by reason code rank")
    return value


def _signal_config_versions(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        sorted(
            {
                (row.fixture_id, row.team_id, row.signal_config_version)
                for row in rows
            },
        ),
    )


def _row_sort_key(
    row: MarketResearchSoccerTravelRestDisadvantageDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    status_rank = {
        BLOCKED_STATUS: Decimal("0.000000"),
        WATCH_STATUS: Decimal("1.000000"),
        PASS_STATUS: Decimal("2.000000"),
    }[row.digest_status]
    return (
        status_rank,
        -row.disadvantage_pressure_score,
        row.fixture_id,
        row.team_id,
        row.signal_id,
    )


def _status_count(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_result(max(getattr(row, field_name) for row in rows))


def _min_row_decimal(
    rows: tuple[MarketResearchSoccerTravelRestDisadvantageDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_result(min(getattr(row, field_name) for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("average inputs must be Decimals")
        total += value
    return _ratio(_quantize_result(total), _count_decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_result(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_result(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use exactly six decimal places")
    if value == ZERO and value.is_signed():
        raise ValueError(f"{field_name} must not be negative zero")
    return value


def _quantize_result(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal result must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _revalidate_payload_dataclass(value: object) -> None:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("payload value must be a dataclass instance")
    if type(value) not in (
        MarketResearchSoccerTravelRestDisadvantageDigestConfig,
        MarketResearchSoccerTravelRestDisadvantageDigestSignal,
        MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount,
        MarketResearchSoccerTravelRestDisadvantageDigestRow,
        MarketResearchSoccerTravelRestDisadvantageDigestReport,
    ):
        raise ValueError("payload dataclass type must be supported exactly")
    _require_hard_flags("payload dataclass", value)
    for field in fields(value):
        _revalidate_payload_value(field.name, getattr(value, field.name))
    value.__post_init__()


def _revalidate_payload_value(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_payload_dataclass(value)
        return
    if type(value) is Decimal:
        _require_decimal(field_name, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(field_name, value)
        return
    if type(value) is tuple:
        for item in value:
            _revalidate_payload_value(field_name, item)
        return
    if type(value) is list:
        raise ValueError(f"{field_name} must be a tuple")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("datetime", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        raise ValueError("payload values must not contain lists")
    return value
