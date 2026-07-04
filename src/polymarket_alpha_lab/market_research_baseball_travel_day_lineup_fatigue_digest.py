"""Pure Phase 1 baseball travel-day lineup fatigue digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASEBALL_TRAVEL_DAY_LINEUP_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-travel-day-lineup-fatigue-digest-v0"
)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
FATIGUE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)

BLOCKED_SCORE_REASON = "baseball_travel_day_lineup_fatigue_blocked_score"
INLINE_REASON = "baseball_travel_day_lineup_fatigue_inline"
LINEUP_ABSENCES_REASON = "baseball_travel_day_lineup_fatigue_lineup_absences"
LONG_TRAVEL_REASON = "baseball_travel_day_lineup_fatigue_long_travel"
SHORT_REST_REASON = "baseball_travel_day_lineup_fatigue_short_rest"
SOURCE_FRESH_REASON = "baseball_travel_day_lineup_fatigue_source_fresh"
SOURCE_STALE_REASON = "baseball_travel_day_lineup_fatigue_source_stale"
TIMEZONE_SHIFT_REASON = "baseball_travel_day_lineup_fatigue_timezone_shift"
WATCH_SCORE_REASON = "baseball_travel_day_lineup_fatigue_watch_score"

BLOCKED_SCORE_PRESENT_REASON = (
    "baseball_travel_day_lineup_fatigue_blocked_score_present"
)
WATCH_SCORE_PRESENT_REASON = "baseball_travel_day_lineup_fatigue_watch_score_present"
LONG_TRAVEL_PRESENT_REASON = "baseball_travel_day_lineup_fatigue_long_travel_present"
TIMEZONE_SHIFT_PRESENT_REASON = (
    "baseball_travel_day_lineup_fatigue_timezone_shift_present"
)
SHORT_REST_PRESENT_REASON = "baseball_travel_day_lineup_fatigue_short_rest_present"
LINEUP_ABSENCES_PRESENT_REASON = (
    "baseball_travel_day_lineup_fatigue_lineup_absences_present"
)
STALE_SOURCE_PRESENT_REASON = "baseball_travel_day_lineup_fatigue_stale_source_present"
DIGEST_CLEAR_REASON = "baseball_travel_day_lineup_fatigue_digest_clear"
DIGEST_EMPTY_REASON = "baseball_travel_day_lineup_fatigue_digest_empty"

ROW_REASON_CODES = (
    BLOCKED_SCORE_REASON,
    INLINE_REASON,
    LINEUP_ABSENCES_REASON,
    LONG_TRAVEL_REASON,
    SHORT_REST_REASON,
    SOURCE_FRESH_REASON,
    SOURCE_STALE_REASON,
    TIMEZONE_SHIFT_REASON,
    WATCH_SCORE_REASON,
)
REPORT_REASON_CODES = (
    BLOCKED_SCORE_PRESENT_REASON,
    WATCH_SCORE_PRESENT_REASON,
    LONG_TRAVEL_PRESENT_REASON,
    TIMEZONE_SHIFT_PRESENT_REASON,
    SHORT_REST_PRESENT_REASON,
    LINEUP_ABSENCES_PRESENT_REASON,
    STALE_SOURCE_PRESENT_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_FATIGUE_SCORE = Decimal("0.400000")
BLOCKED_FATIGUE_SCORE = Decimal("0.700000")
LONG_TRAVEL_DISTANCE_MILES = Decimal("750.000000")
TIMEZONE_SHIFT_HOURS = Decimal("2.000000")
SHORT_REST_HOURS = Decimal("18.000000")
LINEUP_ABSENCE_COUNT = Decimal("2.000000")
MAX_FRESH_SOURCE_AGE_SECONDS = Decimal("7200.000000")
TRAVEL_DISTANCE_CAP_MILES = Decimal("1500.000000")
TIMEZONE_SHIFT_CAP_HOURS = Decimal("3.000000")
REST_PRESSURE_CAP_HOURS = Decimal("24.000000")
LINEUP_ABSENCE_CAP = Decimal("4.000000")
TRAVEL_DISTANCE_WEIGHT = Decimal("0.300000")
TIMEZONE_SHIFT_WEIGHT = Decimal("0.200000")
REST_PRESSURE_WEIGHT = Decimal("0.250000")
LINEUP_ABSENCE_WEIGHT = Decimal("0.250000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_TRAVEL_DAY_LINEUP_FATIGUE_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballTravelDayLineupFatigueDigestConfig",
    "MarketResearchBaseballTravelDayLineupFatigueObservation",
    "MarketResearchBaseballTravelDayLineupFatigueDigestRow",
    "MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount",
    "MarketResearchBaseballTravelDayLineupFatigueDigestReport",
    "build_market_research_baseball_travel_day_lineup_fatigue_digest",
    "market_research_baseball_travel_day_lineup_fatigue_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBaseballTravelDayLineupFatigueDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_TRAVEL_DAY_LINEUP_FATIGUE_DIGEST_CONFIG_VERSION
    )
    watch_fatigue_score: Decimal = WATCH_FATIGUE_SCORE
    blocked_fatigue_score: Decimal = BLOCKED_FATIGUE_SCORE
    long_travel_distance_miles: Decimal = LONG_TRAVEL_DISTANCE_MILES
    timezone_shift_hours: Decimal = TIMEZONE_SHIFT_HOURS
    short_rest_hours: Decimal = SHORT_REST_HOURS
    lineup_absence_count: Decimal = LINEUP_ABSENCE_COUNT
    max_fresh_source_age_seconds: Decimal = MAX_FRESH_SOURCE_AGE_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballTravelDayLineupFatigueDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_TRAVEL_DAY_LINEUP_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_fatigue_score", "blocked_fatigue_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "long_travel_distance_miles",
            "timezone_shift_hours",
            "short_rest_hours",
            "max_fresh_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lineup_absence_count",
            _require_positive_whole_decimal(
                "lineup_absence_count",
                self.lineup_absence_count,
            ),
        )
        if self.blocked_fatigue_score < self.watch_fatigue_score:
            raise ValueError("blocked_fatigue_score must be at least watch_fatigue_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballTravelDayLineupFatigueObservation:
    source_id: str
    game_key: str
    team_key: str
    opponent_team_key: str
    market_slug: str
    observed_at: datetime
    scheduled_start_at: datetime
    source_age_seconds: Decimal
    travel_distance_miles: Decimal
    timezone_shift_hours: Decimal
    rest_hours_since_last_game: Decimal
    lineup_regular_absences: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballTravelDayLineupFatigueObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "game_key",
            "team_key",
            "opponent_team_key",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        for field_name in (
            "source_age_seconds",
            "travel_distance_miles",
            "timezone_shift_hours",
            "rest_hours_since_last_game",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lineup_regular_absences",
            _require_nonnegative_whole_decimal(
                "lineup_regular_absences",
                self.lineup_regular_absences,
            ),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchBaseballTravelDayLineupFatigueDigestRow:
    source_id: str
    game_key: str
    team_key: str
    opponent_team_key: str
    market_slug: str
    observed_at: datetime
    scheduled_start_at: datetime
    source_age_seconds: Decimal
    travel_distance_miles: Decimal
    timezone_shift_hours: Decimal
    rest_hours_since_last_game: Decimal
    lineup_regular_absences: Decimal
    fatigue_score: Decimal
    fatigue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballTravelDayLineupFatigueDigestRow,
            "row",
        )
        for field_name in (
            "source_id",
            "game_key",
            "team_key",
            "opponent_team_key",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        for field_name in (
            "source_age_seconds",
            "travel_distance_miles",
            "timezone_shift_hours",
            "rest_hours_since_last_game",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lineup_regular_absences",
            _require_nonnegative_whole_decimal(
                "lineup_regular_absences",
                self.lineup_regular_absences,
            ),
        )
        object.__setattr__(
            self,
            "fatigue_score",
            _require_probability("fatigue_score", self.fatigue_score),
        )
        _require_member("fatigue_status", self.fatigue_status, FATIGUE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchBaseballTravelDayLineupFatigueDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    long_travel_count: Decimal
    timezone_shift_count: Decimal
    short_rest_count: Decimal
    lineup_absence_count: Decimal
    max_fatigue_score: Decimal
    average_fatigue_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballTravelDayLineupFatigueDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_TRAVEL_DAY_LINEUP_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "long_travel_count",
            "timezone_shift_count",
            "short_rest_count",
            "lineup_absence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_fatigue_score", "average_fatigue_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, FATIGUE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_baseball_travel_day_lineup_fatigue_digest(
    observations: Iterable[MarketResearchBaseballTravelDayLineupFatigueObservation],
    *,
    config: MarketResearchBaseballTravelDayLineupFatigueDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballTravelDayLineupFatigueDigestReport:
    if type(config) is not MarketResearchBaseballTravelDayLineupFatigueDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBaseballTravelDayLineupFatigueDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    _reject_late_observations(normalized, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_observation(item, config=config) for item in normalized),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return MarketResearchBaseballTravelDayLineupFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON),
        long_travel_count=_reason_count(rows, LONG_TRAVEL_REASON),
        timezone_shift_count=_reason_count(rows, TIMEZONE_SHIFT_REASON),
        short_rest_count=_reason_count(rows, SHORT_REST_REASON),
        lineup_absence_count=_reason_count(rows, LINEUP_ABSENCES_REASON),
        max_fatigue_score=_max_row_decimal(rows, "fatigue_score"),
        average_fatigue_score=_ratio(
            _sum_decimal(row.fatigue_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_baseball_travel_day_lineup_fatigue_digest_payload(
    report: MarketResearchBaseballTravelDayLineupFatigueDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBaseballTravelDayLineupFatigueDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBaseballTravelDayLineupFatigueDigestReport",
        )
    _require_hard_flags("report", report)
    return _payload_value(report)


def _row_from_observation(
    observation: MarketResearchBaseballTravelDayLineupFatigueObservation,
    *,
    config: MarketResearchBaseballTravelDayLineupFatigueDigestConfig,
) -> MarketResearchBaseballTravelDayLineupFatigueDigestRow:
    fatigue_score = _fatigue_score(
        travel_distance_miles=observation.travel_distance_miles,
        timezone_shift_hours=observation.timezone_shift_hours,
        rest_hours_since_last_game=observation.rest_hours_since_last_game,
        lineup_regular_absences=observation.lineup_regular_absences,
    )
    fatigue_status = _fatigue_status(fatigue_score, config=config)
    return MarketResearchBaseballTravelDayLineupFatigueDigestRow(
        source_id=observation.source_id,
        game_key=observation.game_key,
        team_key=observation.team_key,
        opponent_team_key=observation.opponent_team_key,
        market_slug=observation.market_slug,
        observed_at=observation.observed_at,
        scheduled_start_at=observation.scheduled_start_at,
        source_age_seconds=observation.source_age_seconds,
        travel_distance_miles=observation.travel_distance_miles,
        timezone_shift_hours=observation.timezone_shift_hours,
        rest_hours_since_last_game=observation.rest_hours_since_last_game,
        lineup_regular_absences=observation.lineup_regular_absences,
        fatigue_score=fatigue_score,
        fatigue_status=fatigue_status,
        reason_codes=_row_reason_codes(
            observation,
            fatigue_status=fatigue_status,
            config=config,
        ),
    )


def _fatigue_score(
    *,
    travel_distance_miles: Decimal,
    timezone_shift_hours: Decimal,
    rest_hours_since_last_game: Decimal,
    lineup_regular_absences: Decimal,
) -> Decimal:
    travel_component = _component_ratio(
        travel_distance_miles,
        TRAVEL_DISTANCE_CAP_MILES,
    )
    timezone_component = _component_ratio(
        timezone_shift_hours,
        TIMEZONE_SHIFT_CAP_HOURS,
    )
    rest_component = _rest_pressure_ratio(rest_hours_since_last_game)
    lineup_component = _component_ratio(lineup_regular_absences, LINEUP_ABSENCE_CAP)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (travel_component * TRAVEL_DISTANCE_WEIGHT)
            + (timezone_component * TIMEZONE_SHIFT_WEIGHT)
            + (rest_component * REST_PRESSURE_WEIGHT)
            + (lineup_component * LINEUP_ABSENCE_WEIGHT),
        )


def _component_ratio(value: Decimal, cap: Decimal) -> Decimal:
    return min(_ratio(value, cap), ONE)


def _rest_pressure_ratio(rest_hours_since_last_game: Decimal) -> Decimal:
    if rest_hours_since_last_game >= REST_PRESSURE_CAP_HOURS:
        return ZERO
    return _component_ratio(
        REST_PRESSURE_CAP_HOURS - rest_hours_since_last_game,
        REST_PRESSURE_CAP_HOURS,
    )


def _fatigue_status(
    fatigue_score: Decimal,
    *,
    config: MarketResearchBaseballTravelDayLineupFatigueDigestConfig,
) -> str:
    if fatigue_score >= config.blocked_fatigue_score:
        return BLOCKED_STATUS
    if fatigue_score >= config.watch_fatigue_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    observation: MarketResearchBaseballTravelDayLineupFatigueObservation,
    *,
    fatigue_status: str,
    config: MarketResearchBaseballTravelDayLineupFatigueDigestConfig,
) -> tuple[str, ...]:
    reasons = [_primary_reason(fatigue_status)]
    if observation.travel_distance_miles >= config.long_travel_distance_miles:
        reasons.append(LONG_TRAVEL_REASON)
    if observation.timezone_shift_hours >= config.timezone_shift_hours:
        reasons.append(TIMEZONE_SHIFT_REASON)
    if observation.rest_hours_since_last_game <= config.short_rest_hours:
        reasons.append(SHORT_REST_REASON)
    if observation.lineup_regular_absences >= config.lineup_absence_count:
        reasons.append(LINEUP_ABSENCES_REASON)
    if observation.source_age_seconds <= config.max_fresh_source_age_seconds:
        reasons.append(SOURCE_FRESH_REASON)
    else:
        reasons.append(SOURCE_STALE_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _primary_reason(status: str) -> str:
    if status == BLOCKED_STATUS:
        return BLOCKED_SCORE_REASON
    if status == WATCH_STATUS:
        return WATCH_SCORE_REASON
    return INLINE_REASON


def _report_reason_codes(
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reasons: list[str] = []
    if _reason_count(rows, BLOCKED_SCORE_REASON) > ZERO:
        reasons.append(BLOCKED_SCORE_PRESENT_REASON)
    if _reason_count(rows, WATCH_SCORE_REASON) > ZERO:
        reasons.append(WATCH_SCORE_PRESENT_REASON)
    if _reason_count(rows, LONG_TRAVEL_REASON) > ZERO:
        reasons.append(LONG_TRAVEL_PRESENT_REASON)
    if _reason_count(rows, TIMEZONE_SHIFT_REASON) > ZERO:
        reasons.append(TIMEZONE_SHIFT_PRESENT_REASON)
    if _reason_count(rows, SHORT_REST_REASON) > ZERO:
        reasons.append(SHORT_REST_PRESENT_REASON)
    if _reason_count(rows, LINEUP_ABSENCES_REASON) > ZERO:
        reasons.append(LINEUP_ABSENCES_PRESENT_REASON)
    if _reason_count(rows, SOURCE_STALE_REASON) > ZERO:
        reasons.append(STALE_SOURCE_PRESENT_REASON)
    if not reasons:
        reasons.append(DIGEST_CLEAR_REASON)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
) -> tuple[MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        BLOCKED_SCORE_PRESENT_REASON: BLOCKED_SCORE_REASON,
        WATCH_SCORE_PRESENT_REASON: WATCH_SCORE_REASON,
        LONG_TRAVEL_PRESENT_REASON: LONG_TRAVEL_REASON,
        TIMEZONE_SHIFT_PRESENT_REASON: TIMEZONE_SHIFT_REASON,
        SHORT_REST_PRESENT_REASON: SHORT_REST_REASON,
        LINEUP_ABSENCES_PRESENT_REASON: LINEUP_ABSENCES_REASON,
        STALE_SOURCE_PRESENT_REASON: SOURCE_STALE_REASON,
        DIGEST_CLEAR_REASON: INLINE_REASON,
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.fatigue_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.fatigue_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _recommended_next_step(status: str) -> str:
    if status == PASS_STATUS:
        return "allow_report_only_baseball_travel_day_lineup_fatigue_screening"
    if status == WATCH_STATUS:
        return "monitor_report_only_baseball_travel_day_lineup_fatigue_screening"
    return "block_report_only_baseball_travel_day_lineup_fatigue_screening"


def _validate_observation(
    observation: MarketResearchBaseballTravelDayLineupFatigueObservation,
) -> None:
    if observation.scheduled_start_at < observation.observed_at:
        raise ValueError("scheduled_start_at must not precede observed_at")


def _validate_row(row: MarketResearchBaseballTravelDayLineupFatigueDigestRow) -> None:
    if row.scheduled_start_at < row.observed_at:
        raise ValueError("scheduled_start_at must not precede observed_at")
    expected_score = _fatigue_score(
        travel_distance_miles=row.travel_distance_miles,
        timezone_shift_hours=row.timezone_shift_hours,
        rest_hours_since_last_game=row.rest_hours_since_last_game,
        lineup_regular_absences=row.lineup_regular_absences,
    )
    if row.fatigue_score != expected_score:
        raise ValueError("fatigue_score must match travel day lineup burden")
    if _primary_reason(row.fatigue_status) not in row.reason_codes:
        raise ValueError("reason_codes must match fatigue_status")
    if row.fatigue_status == BLOCKED_STATUS and (
        WATCH_SCORE_REASON in row.reason_codes or INLINE_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match fatigue_status")
    if row.fatigue_status == WATCH_STATUS and (
        BLOCKED_SCORE_REASON in row.reason_codes or INLINE_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match fatigue_status")
    if row.fatigue_status == PASS_STATUS and (
        BLOCKED_SCORE_REASON in row.reason_codes
        or WATCH_SCORE_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match fatigue_status")
    source_reason_count = _count_decimal(
        sum(
            1
            for reason in row.reason_codes
            if reason in (SOURCE_FRESH_REASON, SOURCE_STALE_REASON)
        ),
    )
    if source_reason_count != ONE:
        raise ValueError("reason_codes must match source freshness")


def _validate_report(
    report: MarketResearchBaseballTravelDayLineupFatigueDigestReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.long_travel_count != _reason_count(report.rows, LONG_TRAVEL_REASON):
        raise ValueError("long_travel_count must match rows")
    if report.timezone_shift_count != _reason_count(report.rows, TIMEZONE_SHIFT_REASON):
        raise ValueError("timezone_shift_count must match rows")
    if report.short_rest_count != _reason_count(report.rows, SHORT_REST_REASON):
        raise ValueError("short_rest_count must match rows")
    if report.lineup_absence_count != _reason_count(report.rows, LINEUP_ABSENCES_REASON):
        raise ValueError("lineup_absence_count must match rows")
    if report.max_fatigue_score != _max_row_decimal(report.rows, "fatigue_score"):
        raise ValueError("max_fatigue_score must match rows")
    if report.average_fatigue_score != _ratio(
        _sum_decimal(row.fatigue_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_fatigue_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[MarketResearchBaseballTravelDayLineupFatigueObservation],
) -> tuple[MarketResearchBaseballTravelDayLineupFatigueObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain "
            "MarketResearchBaseballTravelDayLineupFatigueObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchBaseballTravelDayLineupFatigueObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchBaseballTravelDayLineupFatigueObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _reject_late_observations(
    observations: tuple[MarketResearchBaseballTravelDayLineupFatigueObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not exceed generated_at")


def _normalize_rows(
    rows: Iterable[MarketResearchBaseballTravelDayLineupFatigueDigestRow],
) -> tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError(
            "rows must contain MarketResearchBaseballTravelDayLineupFatigueDigestRow",
        )
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchBaseballTravelDayLineupFatigueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballTravelDayLineupFatigueDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount],
) -> tuple[MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: MarketResearchBaseballTravelDayLineupFatigueDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.fatigue_status],
        -row.fatigue_score,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.fatigue_status == status))


def _reason_count(
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchBaseballTravelDayLineupFatigueDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
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


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
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
