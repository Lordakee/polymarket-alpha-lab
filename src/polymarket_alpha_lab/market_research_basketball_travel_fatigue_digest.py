"""Pure Phase 1 reducer for basketball back-to-back travel fatigue."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-travel-fatigue-digest-v0"
)
BASKETBALL_TRAVEL_FATIGUE_RESEARCH_SCOPE = (
    "basketball back-to-back travel fatigue phase 1 research digest only"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
CLEAR_STATUS = "clear"
LIMITED_HISTORY_STATUS = "limited_history"

FATIGUE_INDEX_REASON = "basketball_travel_fatigue_index_high"
BACK_TO_BACK_REASON = "basketball_travel_fatigue_back_to_back_spot"
REST_REASON = "basketball_travel_fatigue_rest_short"
TRAVEL_REASON = "basketball_travel_fatigue_travel_high"
TIMEZONE_REASON = "basketball_travel_fatigue_timezone_shift_high"
ROAD_TRIP_REASON = "basketball_travel_fatigue_road_trip_load_high"
LIMITED_HISTORY_REASON = "basketball_travel_fatigue_limited_history"
CLEAR_REASON = "basketball_travel_fatigue_clear"
PASSED_REASON = "basketball_travel_fatigue_passed"
EMPTY_REASON = "basketball_travel_fatigue_empty"

ROW_REASON_CODES = (
    FATIGUE_INDEX_REASON,
    BACK_TO_BACK_REASON,
    REST_REASON,
    TRAVEL_REASON,
    TIMEZONE_REASON,
    ROAD_TRIP_REASON,
    LIMITED_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    FATIGUE_INDEX_REASON,
    BACK_TO_BACK_REASON,
    REST_REASON,
    TRAVEL_REASON,
    TIMEZONE_REASON,
    ROAD_TRIP_REASON,
    LIMITED_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "allow_report_only_basketball_travel_fatigue_digest",
    WATCH_STATUS: "review_report_only_basketball_travel_fatigue_digest",
    BLOCKED_STATUS: "block_report_only_basketball_travel_fatigue_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*[a-z0-9]$|^[a-z0-9]$")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION",
    "BASKETBALL_TRAVEL_FATIGUE_RESEARCH_SCOPE",
    "MarketResearchBasketballTravelFatigueDigestConfig",
    "MarketResearchBasketballTravelFatigueDigestSignal",
    "MarketResearchBasketballTravelFatigueDigestReasonCodeCount",
    "MarketResearchBasketballTravelFatigueDigestRow",
    "MarketResearchBasketballTravelFatigueDigestReport",
    "build_market_research_basketball_travel_fatigue_digest",
    "market_research_basketball_travel_fatigue_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBasketballTravelFatigueDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION
    )
    fatigue_index_watch_threshold: Decimal = Decimal("0.650000")
    back_to_back_game_watch_threshold: Decimal = Decimal("1.000000")
    rest_hour_watch_threshold: Decimal = Decimal("24.000000")
    travel_mile_watch_threshold: Decimal = Decimal("750.000000")
    timezone_shift_hour_watch_threshold: Decimal = Decimal("2.000000")
    road_trip_game_watch_threshold: Decimal = Decimal("3.000000")
    min_signal_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballTravelFatigueDigestConfig:
            raise TypeError(
                "MarketResearchBasketballTravelFatigueDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballTravelFatigueDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fatigue_index_watch_threshold",
            _require_ratio_decimal(
                "fatigue_index_watch_threshold",
                self.fatigue_index_watch_threshold,
            ),
        )
        for field_name in (
            "back_to_back_game_watch_threshold",
            "road_trip_game_watch_threshold",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hour_watch_threshold",
            "travel_mile_watch_threshold",
            "timezone_shift_hour_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballTravelFatigueDigestSignal:
    team_event_key: str
    event_key: str
    team_key: str
    league_key: str
    observed_at: datetime
    back_to_back_game_count: Decimal
    rest_hours: Decimal
    travel_miles: Decimal
    timezone_shift_hours: Decimal
    road_trip_game_count: Decimal
    source_count: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballTravelFatigueDigestSignal:
            raise TypeError(
                "MarketResearchBasketballTravelFatigueDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballTravelFatigueDigestSignal,
            "signal",
        )
        for field_name in (
            "team_event_key",
            "event_key",
            "team_key",
            "league_key",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "back_to_back_game_count",
            "road_trip_game_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hours",
            "travel_miles",
            "timezone_shift_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballTravelFatigueDigestReasonCodeCount:
    reason_code: str
    team_event_count: Decimal
    team_event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballTravelFatigueDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBasketballTravelFatigueDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballTravelFatigueDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "team_event_count",
            _require_positive_whole_decimal("team_event_count", self.team_event_count),
        )
        object.__setattr__(
            self,
            "team_event_ratio",
            _require_ratio_decimal("team_event_ratio", self.team_event_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballTravelFatigueDigestRow:
    team_event_key: str
    event_key: str
    team_key: str
    league_key: str
    signal_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_back_to_back_game_count: Decimal
    max_back_to_back_game_count: Decimal
    latest_rest_hours: Decimal
    min_rest_hours: Decimal
    latest_travel_miles: Decimal
    max_travel_miles: Decimal
    latest_timezone_shift_hours: Decimal
    max_timezone_shift_hours: Decimal
    latest_road_trip_game_count: Decimal
    max_road_trip_game_count: Decimal
    fatigue_index: Decimal
    fatigue_index_watch_threshold: Decimal
    back_to_back_game_watch_threshold: Decimal
    rest_hour_watch_threshold: Decimal
    travel_mile_watch_threshold: Decimal
    timezone_shift_hour_watch_threshold: Decimal
    road_trip_game_watch_threshold: Decimal
    min_signal_count: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballTravelFatigueDigestRow:
            raise TypeError(
                "MarketResearchBasketballTravelFatigueDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBasketballTravelFatigueDigestRow, "row")
        for field_name in ("team_event_key", "event_key", "team_key", "league_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "signal_count",
            "source_count",
            "latest_back_to_back_game_count",
            "max_back_to_back_game_count",
            "latest_road_trip_game_count",
            "max_road_trip_game_count",
            "back_to_back_game_watch_threshold",
            "road_trip_game_watch_threshold",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "latest_rest_hours",
            "min_rest_hours",
            "latest_travel_miles",
            "max_travel_miles",
            "latest_timezone_shift_hours",
            "max_timezone_shift_hours",
            "fatigue_index",
            "rest_hour_watch_threshold",
            "travel_mile_watch_threshold",
            "timezone_shift_hour_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fatigue_index_watch_threshold",
            _require_ratio_decimal(
                "fatigue_index_watch_threshold",
                self.fatigue_index_watch_threshold,
            ),
        )
        _require_member(
            "digest_status",
            self.digest_status,
            (CLEAR_STATUS, WATCH_STATUS, LIMITED_HISTORY_STATUS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballTravelFatigueDigestReport:
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    team_event_count: Decimal
    clear_team_event_count: Decimal
    watch_team_event_count: Decimal
    limited_history_team_event_count: Decimal
    signal_count: Decimal
    fatigue_index_team_event_count: Decimal
    back_to_back_team_event_count: Decimal
    short_rest_team_event_count: Decimal
    travel_fatigue_team_event_count: Decimal
    timezone_shift_team_event_count: Decimal
    road_trip_team_event_count: Decimal
    fatigue_index_watch_threshold: Decimal
    back_to_back_game_watch_threshold: Decimal
    rest_hour_watch_threshold: Decimal
    travel_mile_watch_threshold: Decimal
    timezone_shift_hour_watch_threshold: Decimal
    road_trip_game_watch_threshold: Decimal
    min_signal_count: Decimal
    max_fatigue_index: Decimal | None
    max_travel_miles: Decimal | None
    min_rest_hours: Decimal | None
    max_timezone_shift_hours: Decimal | None
    max_road_trip_game_count: Decimal | None
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballTravelFatigueDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBasketballTravelFatigueDigestReport:
            raise TypeError(
                "MarketResearchBasketballTravelFatigueDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballTravelFatigueDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.research_scope != BASKETBALL_TRAVEL_FATIGUE_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball travel fatigue scope")
        _require_member(
            "digest_status",
            self.digest_status,
            (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS),
        )
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "team_event_count",
            "clear_team_event_count",
            "watch_team_event_count",
            "limited_history_team_event_count",
            "signal_count",
            "fatigue_index_team_event_count",
            "back_to_back_team_event_count",
            "short_rest_team_event_count",
            "travel_fatigue_team_event_count",
            "timezone_shift_team_event_count",
            "road_trip_team_event_count",
            "back_to_back_game_watch_threshold",
            "road_trip_game_watch_threshold",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hour_watch_threshold",
            "travel_mile_watch_threshold",
            "timezone_shift_hour_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fatigue_index_watch_threshold",
            _require_ratio_decimal(
                "fatigue_index_watch_threshold",
                self.fatigue_index_watch_threshold,
            ),
        )
        for field_name in (
            "max_fatigue_index",
            "max_travel_miles",
            "min_rest_hours",
            "max_timezone_shift_hours",
            "max_road_trip_game_count",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_nonnegative_decimal(field_name, value),
                )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
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
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_basketball_travel_fatigue_digest(
    signals: list[MarketResearchBasketballTravelFatigueDigestSignal]
    | tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
    *,
    config: MarketResearchBasketballTravelFatigueDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchBasketballTravelFatigueDigestReport:
    if config is None:
        config = MarketResearchBasketballTravelFatigueDigestConfig()
    if type(config) is not MarketResearchBasketballTravelFatigueDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballTravelFatigueDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_signals(signals)
    _reject_future_signals(normalized, generated_at_utc)
    rows = _rows(normalized, config)
    watch_count = _decimal_count(
        sum(row.digest_status == WATCH_STATUS for row in rows),
    )
    digest_status = _report_status(rows, watch_count)
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = _report_reason_codes(rows, watch_count, reason_code_counts)

    return MarketResearchBasketballTravelFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_TRAVEL_FATIGUE_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        team_event_count=_decimal_count(len(rows)),
        clear_team_event_count=_decimal_count(
            sum(row.digest_status == CLEAR_STATUS for row in rows),
        ),
        watch_team_event_count=watch_count,
        limited_history_team_event_count=_decimal_count(
            sum(row.digest_status == LIMITED_HISTORY_STATUS for row in rows),
        ),
        signal_count=_decimal_count(len(normalized)),
        fatigue_index_team_event_count=_reason_team_event_count(
            rows,
            FATIGUE_INDEX_REASON,
        ),
        back_to_back_team_event_count=_reason_team_event_count(rows, BACK_TO_BACK_REASON),
        short_rest_team_event_count=_reason_team_event_count(rows, REST_REASON),
        travel_fatigue_team_event_count=_reason_team_event_count(rows, TRAVEL_REASON),
        timezone_shift_team_event_count=_reason_team_event_count(rows, TIMEZONE_REASON),
        road_trip_team_event_count=_reason_team_event_count(rows, ROAD_TRIP_REASON),
        fatigue_index_watch_threshold=config.fatigue_index_watch_threshold,
        back_to_back_game_watch_threshold=config.back_to_back_game_watch_threshold,
        rest_hour_watch_threshold=config.rest_hour_watch_threshold,
        travel_mile_watch_threshold=config.travel_mile_watch_threshold,
        timezone_shift_hour_watch_threshold=config.timezone_shift_hour_watch_threshold,
        road_trip_game_watch_threshold=config.road_trip_game_watch_threshold,
        min_signal_count=config.min_signal_count,
        max_fatigue_index=_max_or_none(row.fatigue_index for row in rows),
        max_travel_miles=_max_or_none(row.max_travel_miles for row in rows),
        min_rest_hours=_min_or_none(row.min_rest_hours for row in rows),
        max_timezone_shift_hours=_max_or_none(
            row.max_timezone_shift_hours for row in rows
        ),
        max_road_trip_game_count=_max_or_none(
            row.max_road_trip_game_count for row in rows
        ),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_travel_fatigue_digest_payload(
    report: MarketResearchBasketballTravelFatigueDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballTravelFatigueDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBasketballTravelFatigueDigestReport",
        )
    _require_payload_report(report)
    return _payload_value(report)


def _normalize_signals(
    signals: list[MarketResearchBasketballTravelFatigueDigestSignal]
    | tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
) -> tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, datetime]] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchBasketballTravelFatigueDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchBasketballTravelFatigueDigestSignal",
            )
        _require_hard_flags("signal", signal)
        key = (signal.team_event_key, signal.observed_at)
        if key in seen:
            raise ValueError("signals must not contain duplicate team event observations")
        seen.add(key)
    return normalized


def _reject_future_signals(
    signals: tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
    generated_at: datetime,
) -> None:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    signals: tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
    config: MarketResearchBasketballTravelFatigueDigestConfig,
) -> tuple[MarketResearchBasketballTravelFatigueDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBasketballTravelFatigueDigestSignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.team_event_key, []).append(signal)
    rows = tuple(_row_for_team_event(tuple(items), config) for items in grouped.values())
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_team_event(
    signals: tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
    config: MarketResearchBasketballTravelFatigueDigestConfig,
) -> MarketResearchBasketballTravelFatigueDigestRow:
    sorted_signals = tuple(sorted(signals, key=lambda item: item.observed_at))
    first = sorted_signals[0]
    latest = sorted_signals[-1]
    _validate_team_event_identity(sorted_signals)
    back_to_back_values = tuple(item.back_to_back_game_count for item in sorted_signals)
    rest_values = tuple(item.rest_hours for item in sorted_signals)
    travel_values = tuple(item.travel_miles for item in sorted_signals)
    timezone_values = tuple(item.timezone_shift_hours for item in sorted_signals)
    road_trip_values = tuple(item.road_trip_game_count for item in sorted_signals)
    fatigue_index = _fatigue_index(
        latest.back_to_back_game_count,
        latest.rest_hours,
        latest.travel_miles,
        latest.timezone_shift_hours,
        latest.road_trip_game_count,
        config,
    )
    reason_codes = _row_reason_codes(
        signal_count=_decimal_count(len(sorted_signals)),
        fatigue_index=fatigue_index,
        back_to_back_game_count=latest.back_to_back_game_count,
        rest_hours=latest.rest_hours,
        travel_miles=latest.travel_miles,
        timezone_shift_hours=latest.timezone_shift_hours,
        road_trip_game_count=latest.road_trip_game_count,
        config=config,
    )
    return MarketResearchBasketballTravelFatigueDigestRow(
        team_event_key=first.team_event_key,
        event_key=first.event_key,
        team_key=first.team_key,
        league_key=first.league_key,
        signal_count=_decimal_count(len(sorted_signals)),
        source_count=_sum_decimal(item.source_count for item in sorted_signals),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_back_to_back_game_count=latest.back_to_back_game_count,
        max_back_to_back_game_count=max(back_to_back_values),
        latest_rest_hours=latest.rest_hours,
        min_rest_hours=min(rest_values),
        latest_travel_miles=latest.travel_miles,
        max_travel_miles=max(travel_values),
        latest_timezone_shift_hours=latest.timezone_shift_hours,
        max_timezone_shift_hours=max(timezone_values),
        latest_road_trip_game_count=latest.road_trip_game_count,
        max_road_trip_game_count=max(road_trip_values),
        fatigue_index=fatigue_index,
        fatigue_index_watch_threshold=config.fatigue_index_watch_threshold,
        back_to_back_game_watch_threshold=config.back_to_back_game_watch_threshold,
        rest_hour_watch_threshold=config.rest_hour_watch_threshold,
        travel_mile_watch_threshold=config.travel_mile_watch_threshold,
        timezone_shift_hour_watch_threshold=config.timezone_shift_hour_watch_threshold,
        road_trip_game_watch_threshold=config.road_trip_game_watch_threshold,
        min_signal_count=config.min_signal_count,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_team_event_identity(
    signals: tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
) -> None:
    expected = signals[0]
    for signal in signals:
        if signal.event_key != expected.event_key:
            raise ValueError("event_key must match within team_event_key")
        if signal.team_key != expected.team_key:
            raise ValueError("team_key must match within team_event_key")
        if signal.league_key != expected.league_key:
            raise ValueError("league_key must match within team_event_key")


def _row_reason_codes(
    *,
    signal_count: Decimal,
    fatigue_index: Decimal,
    back_to_back_game_count: Decimal,
    rest_hours: Decimal,
    travel_miles: Decimal,
    timezone_shift_hours: Decimal,
    road_trip_game_count: Decimal,
    config: MarketResearchBasketballTravelFatigueDigestConfig,
) -> tuple[str, ...]:
    if signal_count < config.min_signal_count:
        return (LIMITED_HISTORY_REASON,)
    reason_codes: list[str] = []
    if fatigue_index >= config.fatigue_index_watch_threshold:
        reason_codes.append(FATIGUE_INDEX_REASON)
    if back_to_back_game_count >= config.back_to_back_game_watch_threshold:
        reason_codes.append(BACK_TO_BACK_REASON)
    if rest_hours <= config.rest_hour_watch_threshold:
        reason_codes.append(REST_REASON)
    if travel_miles >= config.travel_mile_watch_threshold:
        reason_codes.append(TRAVEL_REASON)
    if timezone_shift_hours >= config.timezone_shift_hour_watch_threshold:
        reason_codes.append(TIMEZONE_REASON)
    if road_trip_game_count >= config.road_trip_game_watch_threshold:
        reason_codes.append(ROAD_TRIP_REASON)
    if not reason_codes:
        return (CLEAR_REASON,)
    return _sort_reason_codes(tuple(reason_codes), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    if reason_codes == (LIMITED_HISTORY_REASON,):
        return LIMITED_HISTORY_STATUS
    return WATCH_STATUS


def _row_status_rank(status: str) -> Decimal:
    if status == WATCH_STATUS:
        return Decimal("0.000000")
    if status == LIMITED_HISTORY_STATUS:
        return Decimal("1.000000")
    return Decimal("2.000000")


def _row_sort_key(
    row: MarketResearchBasketballTravelFatigueDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        _row_status_rank(row.digest_status),
        -row.fatigue_index,
        -row.max_travel_miles,
        row.event_key,
        row.team_key,
        row.team_event_key,
    )


def _report_status(
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...],
    watch_count: Decimal,
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if watch_count > ZERO:
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...],
    watch_count: Decimal,
    reason_code_counts: tuple[
        MarketResearchBasketballTravelFatigueDigestReasonCodeCount,
        ...,
    ],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if watch_count == ZERO:
        reason_codes = (*reason_codes, PASSED_REASON)
    return _sort_reason_codes(reason_codes, DIGEST_REASON_CODES)


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...],
) -> tuple[MarketResearchBasketballTravelFatigueDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchBasketballTravelFatigueDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                team_event_count=ONE,
                team_event_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBasketballTravelFatigueDigestReasonCodeCount(
            reason_code=reason_code,
            team_event_count=_decimal_count(counts[reason_code]),
            team_event_ratio=_ratio(_decimal_count(counts[reason_code]), total),
        )
        for reason_code in DIGEST_REASON_CODES
        if reason_code in counts
    )


def _reason_team_event_count(
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(reason_code in row.reason_codes for row in rows))


def _source_config_versions(
    signals: tuple[MarketResearchBasketballTravelFatigueDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (signal.team_event_key, signal.signal_config_version)
                for signal in signals
            }
        )
    )


def _fatigue_index(
    back_to_back_game_count: Decimal,
    rest_hours: Decimal,
    travel_miles: Decimal,
    timezone_shift_hours: Decimal,
    road_trip_game_count: Decimal,
    config: MarketResearchBasketballTravelFatigueDigestConfig
    | MarketResearchBasketballTravelFatigueDigestRow,
) -> Decimal:
    components = (
        _capped_ratio(back_to_back_game_count, config.back_to_back_game_watch_threshold),
        _inverse_capped_ratio(config.rest_hour_watch_threshold, rest_hours),
        _capped_ratio(travel_miles, config.travel_mile_watch_threshold),
        _capped_ratio(
            timezone_shift_hours,
            config.timezone_shift_hour_watch_threshold,
        ),
        _capped_ratio(road_trip_game_count, config.road_trip_game_watch_threshold),
    )
    return _ratio(_sum_decimal(components), FIVE)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value > ONE:
        return ONE
    return _six(value)


def _inverse_capped_ratio(threshold: Decimal, value: Decimal) -> Decimal:
    if threshold == ZERO:
        return ONE
    if value >= threshold:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        pressure = (threshold - value) / threshold
    if pressure > ONE:
        return ONE
    return _six(pressure)


def _max_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _six(max(normalized))


def _min_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _six(min(normalized))


def _validate_row(row: MarketResearchBasketballTravelFatigueDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.max_back_to_back_game_count < row.latest_back_to_back_game_count:
        raise ValueError("max_back_to_back_game_count must cover latest value")
    if row.min_rest_hours > row.latest_rest_hours:
        raise ValueError("min_rest_hours must cover latest value")
    if row.max_travel_miles < row.latest_travel_miles:
        raise ValueError("max_travel_miles must cover latest value")
    if row.max_timezone_shift_hours < row.latest_timezone_shift_hours:
        raise ValueError("max_timezone_shift_hours must cover latest value")
    if row.max_road_trip_game_count < row.latest_road_trip_game_count:
        raise ValueError("max_road_trip_game_count must cover latest value")
    if row.fatigue_index != _fatigue_index(
        row.latest_back_to_back_game_count,
        row.latest_rest_hours,
        row.latest_travel_miles,
        row.latest_timezone_shift_hours,
        row.latest_road_trip_game_count,
        row,
    ):
        raise ValueError("fatigue_index must match latest values")
    expected_reason_codes = _row_reason_codes(
        signal_count=row.signal_count,
        fatigue_index=row.fatigue_index,
        back_to_back_game_count=row.latest_back_to_back_game_count,
        rest_hours=row.latest_rest_hours,
        travel_miles=row.latest_travel_miles,
        timezone_shift_hours=row.latest_timezone_shift_hours,
        road_trip_game_count=row.latest_road_trip_game_count,
        config=row,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match latest values")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBasketballTravelFatigueDigestReport) -> None:
    if report.team_event_count != _decimal_count(len(report.rows)):
        raise ValueError("team_event_count must match rows")
    if report.clear_team_event_count != _status_count(report.rows, CLEAR_STATUS):
        raise ValueError("clear_team_event_count must match rows")
    if report.watch_team_event_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_team_event_count must match rows")
    if report.limited_history_team_event_count != _status_count(
        report.rows,
        LIMITED_HISTORY_STATUS,
    ):
        raise ValueError("limited_history_team_event_count must match rows")
    if report.signal_count != _sum_decimal(row.signal_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = _report_reason_codes(
        report.rows,
        report.watch_team_event_count,
        expected_reason_counts,
    )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = _report_status(report.rows, report.watch_team_event_count)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.fatigue_index_team_event_count != _reason_team_event_count(
        report.rows,
        FATIGUE_INDEX_REASON,
    ):
        raise ValueError("fatigue_index_team_event_count must match rows")
    if report.back_to_back_team_event_count != _reason_team_event_count(
        report.rows,
        BACK_TO_BACK_REASON,
    ):
        raise ValueError("back_to_back_team_event_count must match rows")
    if report.short_rest_team_event_count != _reason_team_event_count(
        report.rows,
        REST_REASON,
    ):
        raise ValueError("short_rest_team_event_count must match rows")
    if report.travel_fatigue_team_event_count != _reason_team_event_count(
        report.rows,
        TRAVEL_REASON,
    ):
        raise ValueError("travel_fatigue_team_event_count must match rows")
    if report.timezone_shift_team_event_count != _reason_team_event_count(
        report.rows,
        TIMEZONE_REASON,
    ):
        raise ValueError("timezone_shift_team_event_count must match rows")
    if report.road_trip_team_event_count != _reason_team_event_count(
        report.rows,
        ROAD_TRIP_REASON,
    ):
        raise ValueError("road_trip_team_event_count must match rows")
    if report.max_fatigue_index != _max_or_none(row.fatigue_index for row in report.rows):
        raise ValueError("max_fatigue_index must match rows")
    if report.max_travel_miles != _max_or_none(row.max_travel_miles for row in report.rows):
        raise ValueError("max_travel_miles must match rows")
    if report.min_rest_hours != _min_or_none(row.min_rest_hours for row in report.rows):
        raise ValueError("min_rest_hours must match rows")
    if report.max_timezone_shift_hours != _max_or_none(
        row.max_timezone_shift_hours for row in report.rows
    ):
        raise ValueError("max_timezone_shift_hours must match rows")
    if report.max_road_trip_game_count != _max_or_none(
        row.max_road_trip_game_count for row in report.rows
    ):
        raise ValueError("max_road_trip_game_count must match rows")
    for row in report.rows:
        if row.fatigue_index_watch_threshold != report.fatigue_index_watch_threshold:
            raise ValueError("row thresholds must match report thresholds")
        if row.back_to_back_game_watch_threshold != report.back_to_back_game_watch_threshold:
            raise ValueError("row thresholds must match report thresholds")
        if row.rest_hour_watch_threshold != report.rest_hour_watch_threshold:
            raise ValueError("row thresholds must match report thresholds")
        if row.travel_mile_watch_threshold != report.travel_mile_watch_threshold:
            raise ValueError("row thresholds must match report thresholds")
        if (
            row.timezone_shift_hour_watch_threshold
            != report.timezone_shift_hour_watch_threshold
        ):
            raise ValueError("row thresholds must match report thresholds")
        if row.road_trip_game_watch_threshold != report.road_trip_game_watch_threshold:
            raise ValueError("row thresholds must match report thresholds")
        if row.min_signal_count != report.min_signal_count:
            raise ValueError("row thresholds must match report thresholds")


def _normalize_rows(
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...],
) -> tuple[MarketResearchBasketballTravelFatigueDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBasketballTravelFatigueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBasketballTravelFatigueDigestRow",
            )
        _require_hard_flags("row", row)
        if row.team_event_key in seen:
            raise ValueError("rows must contain unique team_event_key values")
        seen.add(row.team_event_key)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_source_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("source_config_versions must contain key pairs")
        team_event_key, signal_config_version = value
        _require_canonical_string("team_event_key", team_event_key)
        _require_canonical_string("signal_config_version", signal_config_version)
        normalized.append((team_event_key, signal_config_version))
    sorted_values = tuple(sorted(normalized))
    if sorted_values != values:
        raise ValueError("source_config_versions must be sorted")
    if len(set(sorted_values)) != len(sorted_values):
        raise ValueError("source_config_versions must be unique")
    return values


def _normalize_reason_code_counts(
    values: tuple[MarketResearchBasketballTravelFatigueDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBasketballTravelFatigueDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not MarketResearchBasketballTravelFatigueDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballTravelFatigueDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(value.reason_code)
    sorted_values = tuple(
        sorted(values, key=lambda item: DIGEST_REASON_CODES.index(item.reason_code)),
    )
    if sorted_values != values:
        raise ValueError("reason_code_counts must be sorted")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_reason_code(field_name, value, allowed)
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    if _sort_reason_codes(values, allowed) != values:
        raise ValueError(f"{field_name} must be sorted")
    return values


def _sort_reason_codes(
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _status_count(
    rows: tuple[MarketResearchBasketballTravelFatigueDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(row.digest_status == status for row in rows))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _six(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _six(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of the supported values")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _public_dataclass_label(value: object) -> str | None:
    if type(value) is MarketResearchBasketballTravelFatigueDigestConfig:
        return "config"
    if type(value) is MarketResearchBasketballTravelFatigueDigestSignal:
        return "signal"
    if type(value) is MarketResearchBasketballTravelFatigueDigestReasonCodeCount:
        return "reason_code_count"
    if type(value) is MarketResearchBasketballTravelFatigueDigestRow:
        return "row"
    if type(value) is MarketResearchBasketballTravelFatigueDigestReport:
        return "report"
    return None


def _require_payload_report(
    report: MarketResearchBasketballTravelFatigueDigestReport,
) -> None:
    _require_payload_value("report", report)
    for row in report.rows:
        _validate_row(row)
    for reason_code_count in report.reason_code_counts:
        _validate_reason_code_count(reason_code_count)
    _validate_report(report)


def _validate_reason_code_count(
    count: MarketResearchBasketballTravelFatigueDigestReasonCodeCount,
) -> None:
    _require_reason_code("reason_code", count.reason_code, DIGEST_REASON_CODES)
    _require_positive_whole_decimal("team_event_count", count.team_event_count)
    _require_ratio_decimal("team_event_ratio", count.team_event_ratio)
    _require_hard_flags("reason_code_count", count)


def _require_payload_value(label: str, value: object) -> None:
    public_label = _public_dataclass_label(value)
    if public_label is not None:
        _require_hard_flags(public_label, value)
        for field in fields(value):
            _require_payload_value(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, Decimal):
        _require_payload_decimal(label, value)
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_value(f"{label}.{index}", item)
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{label} must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload numeric values must use Decimal")
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("payload contains unsupported dataclass")
    raise ValueError("payload contains unsupported value")


def _require_payload_decimal(label: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{label} must be a six-decimal Decimal")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        _require_payload_decimal("payload Decimal value", value)
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    public_label = _public_dataclass_label(value)
    if public_label is not None:
        _require_hard_flags(public_label, value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("payload value must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("payload contains unsupported dataclass")
    raise ValueError("payload contains a non-Decimal numeric value")
