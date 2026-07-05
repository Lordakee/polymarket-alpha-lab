"""Pure Phase 1 tennis travel time-zone fatigue digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_TENNIS_TIMEZONE_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-timezone-fatigue-digest-v0"
)

FATIGUE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "tennis_timezone_fatigue_large_timezone_shift",
    "tennis_timezone_fatigue_short_recovery_window",
    "tennis_timezone_fatigue_circadian_recovery_gap",
    "tennis_timezone_fatigue_long_travel",
    "tennis_timezone_fatigue_late_arrival",
    "tennis_timezone_fatigue_recent_match_load",
    "tennis_timezone_fatigue_blocked",
    "tennis_timezone_fatigue_watch",
    "tennis_timezone_fatigue_clear",
)
REPORT_REASON_CODES = (
    "tennis_timezone_fatigue_blocked_present",
    "tennis_timezone_fatigue_watch_present",
    "tennis_timezone_fatigue_timezone_shift_present",
    "tennis_timezone_fatigue_short_recovery_present",
    "tennis_timezone_fatigue_circadian_gap_present",
    "tennis_timezone_fatigue_long_travel_present",
    "tennis_timezone_fatigue_late_arrival_present",
    "tennis_timezone_fatigue_recent_match_load_present",
    "tennis_timezone_fatigue_digest_clear",
    "tennis_timezone_fatigue_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_DENOMINATOR = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_TIMEZONE_FATIGUE_DIGEST_CONFIG_VERSION",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "MarketResearchTennisTimezoneFatigueDigestConfig",
    "MarketResearchTennisTimezoneFatigueObservation",
    "MarketResearchTennisTimezoneFatigueDigestRow",
    "MarketResearchTennisTimezoneFatigueReasonCodeCount",
    "MarketResearchTennisTimezoneFatigueDigestReport",
    "build_market_research_tennis_timezone_fatigue_digest",
    "market_research_tennis_timezone_fatigue_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchTennisTimezoneFatigueDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_TIMEZONE_FATIGUE_DIGEST_CONFIG_VERSION
    )
    large_timezone_shift_hours: Decimal = Decimal("4.000000")
    min_recovery_hours: Decimal = Decimal("36.000000")
    recovery_hours_per_timezone: Decimal = Decimal("12.000000")
    long_travel_distance_km: Decimal = Decimal("3000.000000")
    late_arrival_days: Decimal = Decimal("2.000000")
    heavy_recent_match_minutes_7d: Decimal = Decimal("300.000000")
    watch_fatigue_signal_count: Decimal = Decimal("3.000000")
    blocked_fatigue_signal_count: Decimal = Decimal("5.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTennisTimezoneFatigueDigestConfig:
            raise TypeError(
                "MarketResearchTennisTimezoneFatigueDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchTennisTimezoneFatigueDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_TIMEZONE_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "large_timezone_shift_hours",
            "min_recovery_hours",
            "recovery_hours_per_timezone",
            "long_travel_distance_km",
            "late_arrival_days",
            "heavy_recent_match_minutes_7d",
            "watch_fatigue_signal_count",
            "blocked_fatigue_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_fatigue_signal_count > self.blocked_fatigue_signal_count:
            raise ValueError(
                "watch_fatigue_signal_count must not exceed "
                "blocked_fatigue_signal_count",
            )
        if self.blocked_fatigue_signal_count > SIGNAL_DENOMINATOR:
            raise ValueError("blocked_fatigue_signal_count must not exceed signal count")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchTennisTimezoneFatigueObservation:
    source_id: str
    match_id: str
    market_slug: str
    player_id: str
    tournament_key: str
    origin_location_key: str
    destination_location_key: str
    travel_distance_km: Decimal
    timezone_shift_hours: Decimal
    hours_since_arrival: Decimal
    days_since_arrival: Decimal
    recent_match_minutes_7d: Decimal
    observed_at: datetime
    scheduled_start_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTennisTimezoneFatigueObservation:
            raise TypeError(
                "MarketResearchTennisTimezoneFatigueObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchTennisTimezoneFatigueObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "match_id",
            "market_slug",
            "player_id",
            "tournament_key",
            "origin_location_key",
            "destination_location_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "travel_distance_km",
            "timezone_shift_hours",
            "hours_since_arrival",
            "days_since_arrival",
            "recent_match_minutes_7d",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        if self.scheduled_start_at < self.observed_at:
            raise ValueError("scheduled_start_at must not be before observed_at")
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchTennisTimezoneFatigueDigestRow:
    source_id: str
    match_id: str
    market_slug: str
    player_id: str
    tournament_key: str
    origin_location_key: str
    destination_location_key: str
    travel_distance_km: Decimal
    timezone_shift_hours: Decimal
    hours_since_arrival: Decimal
    days_since_arrival: Decimal
    recent_match_minutes_7d: Decimal
    circadian_recovery_hours_required: Decimal
    circadian_recovery_gap_hours: Decimal
    fatigue_signal_count: Decimal
    timezone_fatigue_score: Decimal
    observed_at: datetime
    scheduled_start_at: datetime
    fatigue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTennisTimezoneFatigueDigestRow:
            raise TypeError(
                "MarketResearchTennisTimezoneFatigueDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchTennisTimezoneFatigueDigestRow, "row")
        for field_name in (
            "source_id",
            "match_id",
            "market_slug",
            "player_id",
            "tournament_key",
            "origin_location_key",
            "destination_location_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "travel_distance_km",
            "timezone_shift_hours",
            "hours_since_arrival",
            "days_since_arrival",
            "recent_match_minutes_7d",
            "circadian_recovery_hours_required",
            "circadian_recovery_gap_hours",
            "fatigue_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "timezone_fatigue_score",
            _require_ratio("timezone_fatigue_score", self.timezone_fatigue_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        if self.scheduled_start_at < self.observed_at:
            raise ValueError("scheduled_start_at must not be before observed_at")
        _require_member("fatigue_status", self.fatigue_status, FATIGUE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
                require_nonempty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchTennisTimezoneFatigueReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTennisTimezoneFatigueReasonCodeCount:
            raise TypeError(
                "MarketResearchTennisTimezoneFatigueReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchTennisTimezoneFatigueReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchTennisTimezoneFatigueDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    timezone_shift_count: Decimal
    short_recovery_count: Decimal
    circadian_recovery_gap_count: Decimal
    long_travel_count: Decimal
    late_arrival_count: Decimal
    recent_match_load_count: Decimal
    max_timezone_fatigue_score: Decimal
    average_timezone_fatigue_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...]
    reason_code_counts: tuple[MarketResearchTennisTimezoneFatigueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTennisTimezoneFatigueDigestReport:
            raise TypeError(
                "MarketResearchTennisTimezoneFatigueDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchTennisTimezoneFatigueDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_TIMEZONE_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "timezone_shift_count",
            "short_recovery_count",
            "circadian_recovery_gap_count",
            "long_travel_count",
            "late_arrival_count",
            "recent_match_load_count",
            "max_timezone_fatigue_score",
            "average_timezone_fatigue_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("max_timezone_fatigue_score", self.max_timezone_fatigue_score)
        _require_ratio(
            "average_timezone_fatigue_score",
            self.average_timezone_fatigue_score,
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                require_nonempty=True,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_tennis_timezone_fatigue_digest(
    observations: Iterable[MarketResearchTennisTimezoneFatigueObservation],
    *,
    config: MarketResearchTennisTimezoneFatigueDigestConfig,
    generated_at: datetime,
) -> MarketResearchTennisTimezoneFatigueDigestReport:
    if type(config) is not MarketResearchTennisTimezoneFatigueDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchTennisTimezoneFatigueDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return MarketResearchTennisTimezoneFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        timezone_shift_count=_reason_count(
            rows,
            "tennis_timezone_fatigue_large_timezone_shift",
        ),
        short_recovery_count=_reason_count(
            rows,
            "tennis_timezone_fatigue_short_recovery_window",
        ),
        circadian_recovery_gap_count=_reason_count(
            rows,
            "tennis_timezone_fatigue_circadian_recovery_gap",
        ),
        long_travel_count=_reason_count(rows, "tennis_timezone_fatigue_long_travel"),
        late_arrival_count=_reason_count(rows, "tennis_timezone_fatigue_late_arrival"),
        recent_match_load_count=_reason_count(
            rows,
            "tennis_timezone_fatigue_recent_match_load",
        ),
        max_timezone_fatigue_score=_max_row_decimal(rows, "timezone_fatigue_score"),
        average_timezone_fatigue_score=_ratio(
            _sum_decimal(row.timezone_fatigue_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_tennis_timezone_fatigue_digest_payload(
    report: MarketResearchTennisTimezoneFatigueDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchTennisTimezoneFatigueDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchTennisTimezoneFatigueDigestReport",
        )
    _validate_payload_report(report)
    return _payload_value(report)


def _row_from_observation(
    observation: MarketResearchTennisTimezoneFatigueObservation,
    *,
    config: MarketResearchTennisTimezoneFatigueDigestConfig,
) -> MarketResearchTennisTimezoneFatigueDigestRow:
    circadian_required = _multiply_decimal(
        observation.timezone_shift_hours,
        config.recovery_hours_per_timezone,
    )
    circadian_gap = _max_decimal(
        _subtract_decimal(circadian_required, observation.hours_since_arrival),
        ZERO,
    )
    signal_reason_codes = _signal_reason_codes(
        observation,
        config=config,
        circadian_gap=circadian_gap,
    )
    signal_count = _count_decimal(len(signal_reason_codes))
    fatigue_status = _fatigue_status(signal_count, config=config)
    return MarketResearchTennisTimezoneFatigueDigestRow(
        source_id=observation.source_id,
        match_id=observation.match_id,
        market_slug=observation.market_slug,
        player_id=observation.player_id,
        tournament_key=observation.tournament_key,
        origin_location_key=observation.origin_location_key,
        destination_location_key=observation.destination_location_key,
        travel_distance_km=observation.travel_distance_km,
        timezone_shift_hours=observation.timezone_shift_hours,
        hours_since_arrival=observation.hours_since_arrival,
        days_since_arrival=observation.days_since_arrival,
        recent_match_minutes_7d=observation.recent_match_minutes_7d,
        circadian_recovery_hours_required=circadian_required,
        circadian_recovery_gap_hours=circadian_gap,
        fatigue_signal_count=signal_count,
        timezone_fatigue_score=_ratio(signal_count, SIGNAL_DENOMINATOR),
        observed_at=observation.observed_at,
        scheduled_start_at=observation.scheduled_start_at,
        fatigue_status=fatigue_status,
        reason_codes=_row_reason_codes(signal_reason_codes, fatigue_status),
    )


def _signal_reason_codes(
    observation: MarketResearchTennisTimezoneFatigueObservation,
    *,
    config: MarketResearchTennisTimezoneFatigueDigestConfig,
    circadian_gap: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.timezone_shift_hours >= config.large_timezone_shift_hours:
        reason_codes.append("tennis_timezone_fatigue_large_timezone_shift")
    if observation.hours_since_arrival < config.min_recovery_hours:
        reason_codes.append("tennis_timezone_fatigue_short_recovery_window")
    if circadian_gap > ZERO:
        reason_codes.append("tennis_timezone_fatigue_circadian_recovery_gap")
    if observation.travel_distance_km >= config.long_travel_distance_km:
        reason_codes.append("tennis_timezone_fatigue_long_travel")
    if observation.days_since_arrival <= config.late_arrival_days:
        reason_codes.append("tennis_timezone_fatigue_late_arrival")
    if observation.recent_match_minutes_7d >= config.heavy_recent_match_minutes_7d:
        reason_codes.append("tennis_timezone_fatigue_recent_match_load")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODES,
        require_nonempty=False,
    )


def _row_reason_codes(
    signal_reason_codes: tuple[str, ...],
    fatigue_status: str,
) -> tuple[str, ...]:
    reason_codes = list(signal_reason_codes)
    if fatigue_status == "blocked":
        reason_codes.append("tennis_timezone_fatigue_blocked")
    elif fatigue_status == "watch":
        reason_codes.append("tennis_timezone_fatigue_watch")
    else:
        reason_codes.append("tennis_timezone_fatigue_clear")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODES,
        require_nonempty=True,
    )


def _fatigue_status(
    signal_count: Decimal,
    *,
    config: MarketResearchTennisTimezoneFatigueDigestConfig,
) -> str:
    if signal_count >= config.blocked_fatigue_signal_count:
        return "blocked"
    if signal_count >= config.watch_fatigue_signal_count:
        return "watch"
    return "pass"


def _digest_status(rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.fatigue_status == "blocked" for row in rows):
        return "blocked"
    if any(row.fatigue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_tennis_timezone_fatigue_screening"
    if status == "watch":
        return "monitor_report_only_tennis_timezone_fatigue_screening"
    return "block_report_only_tennis_timezone_fatigue_screening"


def _report_reason_codes(
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("tennis_timezone_fatigue_digest_empty",)
    reason_codes: list[str] = []
    if any(row.fatigue_status == "blocked" for row in rows):
        reason_codes.append("tennis_timezone_fatigue_blocked_present")
    if not any(row.fatigue_status == "blocked" for row in rows) and any(
        row.fatigue_status == "watch" for row in rows
    ):
        reason_codes.append("tennis_timezone_fatigue_watch_present")
    if _reason_count(rows, "tennis_timezone_fatigue_large_timezone_shift") > ZERO:
        reason_codes.append("tennis_timezone_fatigue_timezone_shift_present")
    if _reason_count(rows, "tennis_timezone_fatigue_short_recovery_window") > ZERO:
        reason_codes.append("tennis_timezone_fatigue_short_recovery_present")
    if _reason_count(rows, "tennis_timezone_fatigue_circadian_recovery_gap") > ZERO:
        reason_codes.append("tennis_timezone_fatigue_circadian_gap_present")
    if _reason_count(rows, "tennis_timezone_fatigue_long_travel") > ZERO:
        reason_codes.append("tennis_timezone_fatigue_long_travel_present")
    if _reason_count(rows, "tennis_timezone_fatigue_late_arrival") > ZERO:
        reason_codes.append("tennis_timezone_fatigue_late_arrival_present")
    if _reason_count(rows, "tennis_timezone_fatigue_recent_match_load") > ZERO:
        reason_codes.append("tennis_timezone_fatigue_recent_match_load_present")
    if not reason_codes:
        reason_codes.append("tennis_timezone_fatigue_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
) -> tuple[MarketResearchTennisTimezoneFatigueReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("tennis_timezone_fatigue_digest_empty",):
        return (
            MarketResearchTennisTimezoneFatigueReasonCodeCount(
                reason_code="tennis_timezone_fatigue_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchTennisTimezoneFatigueReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "tennis_timezone_fatigue_blocked_present": (
            "tennis_timezone_fatigue_blocked"
        ),
        "tennis_timezone_fatigue_watch_present": "tennis_timezone_fatigue_watch",
        "tennis_timezone_fatigue_timezone_shift_present": (
            "tennis_timezone_fatigue_large_timezone_shift"
        ),
        "tennis_timezone_fatigue_short_recovery_present": (
            "tennis_timezone_fatigue_short_recovery_window"
        ),
        "tennis_timezone_fatigue_circadian_gap_present": (
            "tennis_timezone_fatigue_circadian_recovery_gap"
        ),
        "tennis_timezone_fatigue_long_travel_present": (
            "tennis_timezone_fatigue_long_travel"
        ),
        "tennis_timezone_fatigue_late_arrival_present": (
            "tennis_timezone_fatigue_late_arrival"
        ),
        "tennis_timezone_fatigue_recent_match_load_present": (
            "tennis_timezone_fatigue_recent_match_load"
        ),
        "tennis_timezone_fatigue_digest_clear": "tennis_timezone_fatigue_clear",
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _validate_row(row: MarketResearchTennisTimezoneFatigueDigestRow) -> None:
    expected_gap = _max_decimal(
        _subtract_decimal(
            row.circadian_recovery_hours_required,
            row.hours_since_arrival,
        ),
        ZERO,
    )
    if row.circadian_recovery_gap_hours != expected_gap:
        raise ValueError("circadian_recovery_gap_hours must match recovery fields")
    if row.fatigue_status == "pass":
        if "tennis_timezone_fatigue_clear" not in row.reason_codes:
            raise ValueError("reason_codes must match fatigue_status")
        if (
            "tennis_timezone_fatigue_watch" in row.reason_codes
            or "tennis_timezone_fatigue_blocked" in row.reason_codes
        ):
            raise ValueError("reason_codes must match fatigue_status")
    if row.fatigue_status == "watch":
        if "tennis_timezone_fatigue_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match fatigue_status")
        if (
            "tennis_timezone_fatigue_clear" in row.reason_codes
            or "tennis_timezone_fatigue_blocked" in row.reason_codes
        ):
            raise ValueError("reason_codes must match fatigue_status")
    if row.fatigue_status == "blocked":
        if "tennis_timezone_fatigue_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match fatigue_status")
        if (
            "tennis_timezone_fatigue_clear" in row.reason_codes
            or "tennis_timezone_fatigue_watch" in row.reason_codes
        ):
            raise ValueError("reason_codes must match fatigue_status")
    signal_count = _count_decimal(
        sum(1 for reason_code in ROW_REASON_CODES[:6] if reason_code in row.reason_codes),
    )
    if row.fatigue_signal_count != signal_count:
        raise ValueError("fatigue_signal_count must match reason_codes")
    if row.timezone_fatigue_score != _ratio(
        row.fatigue_signal_count,
        SIGNAL_DENOMINATOR,
    ):
        raise ValueError("timezone_fatigue_score must match fatigue_signal_count")


def _validate_report(report: MarketResearchTennisTimezoneFatigueDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    reason_count_pairs = (
        ("timezone_shift_count", "tennis_timezone_fatigue_large_timezone_shift"),
        ("short_recovery_count", "tennis_timezone_fatigue_short_recovery_window"),
        (
            "circadian_recovery_gap_count",
            "tennis_timezone_fatigue_circadian_recovery_gap",
        ),
        ("long_travel_count", "tennis_timezone_fatigue_long_travel"),
        ("late_arrival_count", "tennis_timezone_fatigue_late_arrival"),
        ("recent_match_load_count", "tennis_timezone_fatigue_recent_match_load"),
    )
    for field_name, reason_code in reason_count_pairs:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_timezone_fatigue_score != _max_row_decimal(
        report.rows,
        "timezone_fatigue_score",
    ):
        raise ValueError("max_timezone_fatigue_score must match rows")
    if report.average_timezone_fatigue_score != _ratio(
        _sum_decimal(row.timezone_fatigue_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_timezone_fatigue_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[MarketResearchTennisTimezoneFatigueObservation],
) -> tuple[MarketResearchTennisTimezoneFatigueObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain MarketResearchTennisTimezoneFatigueObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchTennisTimezoneFatigueObservation:
            raise ValueError(
                "observations must contain MarketResearchTennisTimezoneFatigueObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
) -> tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchTennisTimezoneFatigueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchTennisTimezoneFatigueDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    values: tuple[MarketResearchTennisTimezoneFatigueReasonCodeCount, ...],
) -> tuple[MarketResearchTennisTimezoneFatigueReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for value in values:
        if type(value) is not MarketResearchTennisTimezoneFatigueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchTennisTimezoneFatigueReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(value.reason_code)
    expected = tuple(
        sorted(values, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )
    if values != expected:
        raise ValueError("reason_code_counts must be sorted")
    return values


def _normalize_open_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen_reason_codes: set[str] = set()
    for value in values:
        _require_canonical_string("reason_code", value)
        if value in seen_reason_codes:
            raise ValueError(f"{field_name} must be unique")
        seen_reason_codes.add(value)
    expected = tuple(sorted(values))
    if values != expected:
        raise ValueError(f"{field_name} must be sorted")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if require_nonempty and not values:
        raise ValueError(f"{field_name} must not be empty")
    seen_reason_codes: set[str] = set()
    for value in values:
        _require_member("reason_code", value, allowed)
        if value in seen_reason_codes:
            raise ValueError(f"{field_name} must be unique")
        seen_reason_codes.add(value)
    expected = tuple(sorted(values, key=lambda value: allowed.index(value)))
    if values != expected:
        raise ValueError(f"{field_name} must be in canonical order")
    return values


def _row_sort_key(
    row: MarketResearchTennisTimezoneFatigueDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.fatigue_status],
        -row.timezone_fatigue_score,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.fatigue_status == status))


def _reason_count(
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchTennisTimezoneFatigueDigestRow, ...],
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
        total = _add_decimal(total, value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left * right)


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    field_name: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _validate_payload_report(
    report: MarketResearchTennisTimezoneFatigueDigestReport,
) -> None:
    _require_exact_type(
        report,
        MarketResearchTennisTimezoneFatigueDigestReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_TENNIS_TIMEZONE_FATIGUE_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "input_count",
        "row_count",
        "blocked_count",
        "watch_count",
        "pass_count",
        "timezone_shift_count",
        "short_recovery_count",
        "circadian_recovery_gap_count",
        "long_travel_count",
        "late_arrival_count",
        "recent_match_load_count",
        "max_timezone_fatigue_score",
        "average_timezone_fatigue_score",
    ):
        _require_six_decimal(field_name, getattr(report, field_name))
        _require_nonnegative_decimal(field_name, getattr(report, field_name))
    _require_ratio("max_timezone_fatigue_score", report.max_timezone_fatigue_score)
    _require_ratio(
        "average_timezone_fatigue_score",
        report.average_timezone_fatigue_score,
    )
    _require_member("digest_status", report.digest_status, FATIGUE_STATUSES)
    _require_canonical_string("recommended_next_step", report.recommended_next_step)
    for row in report.rows:
        _validate_payload_row(row)
    _normalize_rows(report.rows)
    for reason_code_count in report.reason_code_counts:
        _validate_payload_reason_code_count(reason_code_count)
    _normalize_reason_code_counts(report.reason_code_counts)
    _normalize_reason_codes(
        "reason_codes",
        report.reason_codes,
        REPORT_REASON_CODES,
        require_nonempty=True,
    )
    _validate_report(report)


def _validate_payload_row(row: MarketResearchTennisTimezoneFatigueDigestRow) -> None:
    _require_exact_type(row, MarketResearchTennisTimezoneFatigueDigestRow, "row")
    _require_hard_flags("row", row)
    for field_name in (
        "source_id",
        "match_id",
        "market_slug",
        "player_id",
        "tournament_key",
        "origin_location_key",
        "destination_location_key",
    ):
        _require_canonical_string(field_name, getattr(row, field_name))
    for field_name in (
        "travel_distance_km",
        "timezone_shift_hours",
        "hours_since_arrival",
        "days_since_arrival",
        "recent_match_minutes_7d",
        "circadian_recovery_hours_required",
        "circadian_recovery_gap_hours",
        "fatigue_signal_count",
    ):
        _require_six_decimal(field_name, getattr(row, field_name))
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    _require_six_decimal("timezone_fatigue_score", row.timezone_fatigue_score)
    _require_ratio("timezone_fatigue_score", row.timezone_fatigue_score)
    _require_utc_datetime("observed_at", row.observed_at)
    _require_utc_datetime("scheduled_start_at", row.scheduled_start_at)
    if row.scheduled_start_at < row.observed_at:
        raise ValueError("scheduled_start_at must not be before observed_at")
    _require_member("fatigue_status", row.fatigue_status, FATIGUE_STATUSES)
    _normalize_reason_codes(
        "reason_codes",
        row.reason_codes,
        ROW_REASON_CODES,
        require_nonempty=True,
    )
    _validate_row(row)


def _validate_payload_reason_code_count(
    reason_code_count: MarketResearchTennisTimezoneFatigueReasonCodeCount,
) -> None:
    _require_exact_type(
        reason_code_count,
        MarketResearchTennisTimezoneFatigueReasonCodeCount,
        "reason code count",
    )
    _require_hard_flags("reason code count", reason_code_count)
    _require_member("reason_code", reason_code_count.reason_code, REPORT_REASON_CODES)
    _require_six_decimal("count", reason_code_count.count)
    _require_positive_decimal("count", reason_code_count.count)
    _require_six_decimal("row_ratio", reason_code_count.row_ratio)
    _require_ratio("row_ratio", reason_code_count.row_ratio)


def _require_six_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must be six-decimal")
    return value


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(_require_six_decimal("payload decimal", value), "f")
    if isinstance(value, Decimal):
        raise ValueError("payload decimal must be exactly Decimal")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload datetime must be exactly datetime")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("payload value must remain constructor-normalized")
    if type(value) is int:
        raise ValueError("payload numeric values must use Decimal")
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload value must be safe for serialization")
