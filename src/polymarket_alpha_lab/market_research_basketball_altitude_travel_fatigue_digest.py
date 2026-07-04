"""Pure in-memory reducer for basketball altitude travel fatigue research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-altitude-travel-fatigue-digest-v0"
)
BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_RESEARCH_SCOPE = (
    "basketball altitude travel fatigue phase 1 research digest only"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
LIMITED_HISTORY_STATUS = "limited_history"

PRESSURE_INDEX_REASON = "basketball_altitude_travel_fatigue_pressure_index_high"
HIGH_ALTITUDE_REASON = "basketball_altitude_travel_fatigue_high_altitude"
ALTITUDE_CHANGE_REASON = "basketball_altitude_travel_fatigue_altitude_change_high"
REST_REASON = "basketball_altitude_travel_fatigue_rest_days_short"
BACK_TO_BACK_REASON = "basketball_altitude_travel_fatigue_back_to_back_spot"
TRAVEL_REASON = "basketball_altitude_travel_fatigue_travel_high"
ROTATION_DEPTH_REASON = "basketball_altitude_travel_fatigue_rotation_depth_short"
LIMITED_HISTORY_REASON = "basketball_altitude_travel_fatigue_limited_history"
CLEAR_REASON = "basketball_altitude_travel_fatigue_clear"
PASSED_REASON = "basketball_altitude_travel_fatigue_passed"
EMPTY_REASON = "basketball_altitude_travel_fatigue_empty"

ROW_REASON_CODES = (
    PRESSURE_INDEX_REASON,
    HIGH_ALTITUDE_REASON,
    ALTITUDE_CHANGE_REASON,
    REST_REASON,
    BACK_TO_BACK_REASON,
    TRAVEL_REASON,
    ROTATION_DEPTH_REASON,
    LIMITED_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    PRESSURE_INDEX_REASON,
    HIGH_ALTITUDE_REASON,
    ALTITUDE_CHANGE_REASON,
    REST_REASON,
    BACK_TO_BACK_REASON,
    TRAVEL_REASON,
    ROTATION_DEPTH_REASON,
    LIMITED_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_basketball_altitude_travel_fatigue_digest",
    WATCH_STATUS: "review_report_only_basketball_altitude_travel_fatigue_digest",
}

ZERO = Decimal("0")
ONE = Decimal("1")
ROTATION_DEPTH_PRESSURE_FLOOR = Decimal("5")
QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION",
    "BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_RESEARCH_SCOPE",
    "MarketResearchBasketballAltitudeTravelFatigueDigestConfig",
    "MarketResearchBasketballAltitudeTravelFatigueDigestSignal",
    "MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount",
    "MarketResearchBasketballAltitudeTravelFatigueDigestRow",
    "MarketResearchBasketballAltitudeTravelFatigueDigestReport",
    "build_market_research_basketball_altitude_travel_fatigue_digest",
    "market_research_basketball_altitude_travel_fatigue_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBasketballAltitudeTravelFatigueDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION
    )
    fatigue_pressure_index_watch_threshold: Decimal = Decimal("0.650000")
    venue_altitude_feet_watch_threshold: Decimal = Decimal("4000")
    altitude_change_feet_watch_threshold: Decimal = Decimal("2500")
    rest_day_watch_threshold: Decimal = Decimal("1")
    back_to_back_game_watch_threshold: Decimal = Decimal("1")
    travel_mile_watch_threshold: Decimal = Decimal("750")
    rotation_depth_watch_threshold: Decimal = Decimal("8")
    min_signal_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fatigue_pressure_index_watch_threshold",
            _normalize_ratio_decimal(
                "fatigue_pressure_index_watch_threshold",
                self.fatigue_pressure_index_watch_threshold,
            ),
        )
        for field_name in (
            "back_to_back_game_watch_threshold",
            "rotation_depth_watch_threshold",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "venue_altitude_feet_watch_threshold",
            "altitude_change_feet_watch_threshold",
            "rest_day_watch_threshold",
            "travel_mile_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballAltitudeTravelFatigueDigestSignal(_NoSubclass):
    team_event_key: str
    event_key: str
    team_key: str
    league_key: str
    observed_at: datetime
    venue_altitude_feet: Decimal
    altitude_change_feet: Decimal
    rest_days: Decimal
    back_to_back_game_count: Decimal
    travel_miles: Decimal
    available_rotation_players: Decimal
    source_count: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
            "available_rotation_players",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "venue_altitude_feet",
            "altitude_change_feet",
            "rest_days",
            "travel_miles",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount(
    _NoSubclass,
):
    reason_code: str
    team_event_count: Decimal
    team_event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "team_event_count",
            _normalize_nonnegative_whole_decimal(
                "team_event_count",
                self.team_event_count,
            ),
        )
        object.__setattr__(
            self,
            "team_event_ratio",
            _normalize_ratio_decimal("team_event_ratio", self.team_event_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballAltitudeTravelFatigueDigestRow(_NoSubclass):
    team_event_key: str
    event_key: str
    team_key: str
    league_key: str
    signal_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_venue_altitude_feet: Decimal
    max_venue_altitude_feet: Decimal
    latest_altitude_change_feet: Decimal
    max_altitude_change_feet: Decimal
    latest_rest_days: Decimal
    min_rest_days: Decimal
    latest_back_to_back_game_count: Decimal
    max_back_to_back_game_count: Decimal
    latest_travel_miles: Decimal
    max_travel_miles: Decimal
    latest_available_rotation_players: Decimal
    min_available_rotation_players: Decimal
    fatigue_pressure_index: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_event_key", "event_key", "team_key", "league_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "signal_count",
            "source_count",
            "latest_back_to_back_game_count",
            "max_back_to_back_game_count",
            "latest_available_rotation_players",
            "min_available_rotation_players",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
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
            "latest_venue_altitude_feet",
            "max_venue_altitude_feet",
            "latest_altitude_change_feet",
            "max_altitude_change_feet",
            "latest_rest_days",
            "min_rest_days",
            "latest_travel_miles",
            "max_travel_miles",
            "fatigue_pressure_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal("fatigue_pressure_index", self.fatigue_pressure_index)
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
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballAltitudeTravelFatigueDigestReport(_NoSubclass):
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
    high_altitude_team_event_count: Decimal
    altitude_change_team_event_count: Decimal
    short_rest_team_event_count: Decimal
    back_to_back_team_event_count: Decimal
    travel_fatigue_team_event_count: Decimal
    rotation_depth_team_event_count: Decimal
    fatigue_pressure_index_team_event_count: Decimal
    fatigue_pressure_index_watch_threshold: Decimal
    venue_altitude_feet_watch_threshold: Decimal
    altitude_change_feet_watch_threshold: Decimal
    rest_day_watch_threshold: Decimal
    back_to_back_game_watch_threshold: Decimal
    travel_mile_watch_threshold: Decimal
    rotation_depth_watch_threshold: Decimal
    min_signal_count: Decimal
    max_fatigue_pressure_index: Decimal | None
    max_venue_altitude_feet: Decimal | None
    max_altitude_change_feet: Decimal | None
    min_rest_days: Decimal | None
    max_travel_miles: Decimal | None
    min_available_rotation_players: Decimal | None
    rows: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_RESEARCH_SCOPE:
            raise ValueError("research_scope must match altitude travel fatigue scope")
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "team_event_count",
            "clear_team_event_count",
            "watch_team_event_count",
            "limited_history_team_event_count",
            "signal_count",
            "high_altitude_team_event_count",
            "altitude_change_team_event_count",
            "short_rest_team_event_count",
            "back_to_back_team_event_count",
            "travel_fatigue_team_event_count",
            "rotation_depth_team_event_count",
            "fatigue_pressure_index_team_event_count",
            "back_to_back_game_watch_threshold",
            "rotation_depth_watch_threshold",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fatigue_pressure_index_watch_threshold",
            "venue_altitude_feet_watch_threshold",
            "altitude_change_feet_watch_threshold",
            "rest_day_watch_threshold",
            "travel_mile_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal(
            "fatigue_pressure_index_watch_threshold",
            self.fatigue_pressure_index_watch_threshold,
        )
        for field_name in (
            "max_fatigue_pressure_index",
            "max_venue_altitude_feet",
            "max_altitude_change_feet",
            "min_rest_days",
            "max_travel_miles",
            "min_available_rotation_players",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_nonnegative_decimal(field_name, value),
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
        _require_flags("report", self)


def build_market_research_basketball_altitude_travel_fatigue_digest(
    signals: list[MarketResearchBasketballAltitudeTravelFatigueDigestSignal]
    | tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
    *,
    config: MarketResearchBasketballAltitudeTravelFatigueDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballAltitudeTravelFatigueDigestReport:
    if type(config) is not MarketResearchBasketballAltitudeTravelFatigueDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBasketballAltitudeTravelFatigueDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_signals(signals)
    _reject_future_signals(normalized, generated_at_utc)
    rows = _rows(normalized, config)
    watch_count = _decimal_count(
        sum(1 for row in rows if row.digest_status == WATCH_STATUS),
    )
    digest_status = WATCH_STATUS if watch_count > ZERO else PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    if not rows:
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = _sort_reason_codes(
            (*tuple(item.reason_code for item in reason_code_counts), PASSED_REASON),
            DIGEST_REASON_CODES,
        )
    else:
        reason_codes = tuple(item.reason_code for item in reason_code_counts)

    return MarketResearchBasketballAltitudeTravelFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        team_event_count=_decimal_count(len(rows)),
        clear_team_event_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_team_event_count=watch_count,
        limited_history_team_event_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == LIMITED_HISTORY_STATUS),
        ),
        signal_count=_decimal_count(len(normalized)),
        high_altitude_team_event_count=_reason_team_event_count(rows, HIGH_ALTITUDE_REASON),
        altitude_change_team_event_count=_reason_team_event_count(
            rows,
            ALTITUDE_CHANGE_REASON,
        ),
        short_rest_team_event_count=_reason_team_event_count(rows, REST_REASON),
        back_to_back_team_event_count=_reason_team_event_count(rows, BACK_TO_BACK_REASON),
        travel_fatigue_team_event_count=_reason_team_event_count(rows, TRAVEL_REASON),
        rotation_depth_team_event_count=_reason_team_event_count(
            rows,
            ROTATION_DEPTH_REASON,
        ),
        fatigue_pressure_index_team_event_count=_reason_team_event_count(
            rows,
            PRESSURE_INDEX_REASON,
        ),
        fatigue_pressure_index_watch_threshold=(
            config.fatigue_pressure_index_watch_threshold
        ),
        venue_altitude_feet_watch_threshold=config.venue_altitude_feet_watch_threshold,
        altitude_change_feet_watch_threshold=config.altitude_change_feet_watch_threshold,
        rest_day_watch_threshold=config.rest_day_watch_threshold,
        back_to_back_game_watch_threshold=config.back_to_back_game_watch_threshold,
        travel_mile_watch_threshold=config.travel_mile_watch_threshold,
        rotation_depth_watch_threshold=config.rotation_depth_watch_threshold,
        min_signal_count=config.min_signal_count,
        max_fatigue_pressure_index=_max_or_none(row.fatigue_pressure_index for row in rows),
        max_venue_altitude_feet=_max_or_none(row.max_venue_altitude_feet for row in rows),
        max_altitude_change_feet=_max_or_none(row.max_altitude_change_feet for row in rows),
        min_rest_days=_min_or_none(row.min_rest_days for row in rows),
        max_travel_miles=_max_or_none(row.max_travel_miles for row in rows),
        min_available_rotation_players=_min_or_none(
            row.min_available_rotation_players for row in rows
        ),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_altitude_travel_fatigue_digest_payload(
    report: MarketResearchBasketballAltitudeTravelFatigueDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBasketballAltitudeTravelFatigueDigestReport:
        raise ValueError(
            "report must be a MarketResearchBasketballAltitudeTravelFatigueDigestReport",
        )
    _require_flags("report", report)
    return _payload_value(asdict(report))  # type: ignore[return-value]


def _normalize_signals(
    signals: list[MarketResearchBasketballAltitudeTravelFatigueDigestSignal]
    | tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
) -> tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, datetime]] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchBasketballAltitudeTravelFatigueDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchBasketballAltitudeTravelFatigueDigestSignal",
            )
        _require_flags("signal", signal)
        key = (signal.team_event_key, signal.observed_at)
        if key in seen:
            raise ValueError(
                "signals must not contain duplicate team event observations",
            )
        seen.add(key)
    return normalized


def _reject_future_signals(
    signals: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
    generated_at: datetime,
) -> None:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    signals: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
    config: MarketResearchBasketballAltitudeTravelFatigueDigestConfig,
) -> tuple[MarketResearchBasketballAltitudeTravelFatigueDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBasketballAltitudeTravelFatigueDigestSignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.team_event_key, []).append(signal)
    rows = tuple(_row_for_team_event(tuple(items), config) for items in grouped.values())
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_team_event(
    signals: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
    config: MarketResearchBasketballAltitudeTravelFatigueDigestConfig,
) -> MarketResearchBasketballAltitudeTravelFatigueDigestRow:
    sorted_signals = tuple(sorted(signals, key=lambda item: item.observed_at))
    first = sorted_signals[0]
    latest = sorted_signals[-1]
    _validate_team_event_identity(sorted_signals)
    venue_altitude_values = tuple(item.venue_altitude_feet for item in sorted_signals)
    altitude_change_values = tuple(item.altitude_change_feet for item in sorted_signals)
    rest_values = tuple(item.rest_days for item in sorted_signals)
    back_to_back_values = tuple(item.back_to_back_game_count for item in sorted_signals)
    travel_values = tuple(item.travel_miles for item in sorted_signals)
    rotation_values = tuple(item.available_rotation_players for item in sorted_signals)
    fatigue_pressure_index = _fatigue_pressure_index(
        latest.venue_altitude_feet,
        latest.altitude_change_feet,
        latest.rest_days,
        latest.back_to_back_game_count,
        latest.travel_miles,
        latest.available_rotation_players,
        config,
    )
    reason_codes = _row_reason_codes(
        signal_count=_decimal_count(len(sorted_signals)),
        fatigue_pressure_index=fatigue_pressure_index,
        venue_altitude_feet=latest.venue_altitude_feet,
        altitude_change_feet=latest.altitude_change_feet,
        rest_days=latest.rest_days,
        back_to_back_game_count=latest.back_to_back_game_count,
        travel_miles=latest.travel_miles,
        available_rotation_players=latest.available_rotation_players,
        config=config,
    )
    return MarketResearchBasketballAltitudeTravelFatigueDigestRow(
        team_event_key=first.team_event_key,
        event_key=first.event_key,
        team_key=first.team_key,
        league_key=first.league_key,
        signal_count=_decimal_count(len(sorted_signals)),
        source_count=_sum_decimal(item.source_count for item in sorted_signals),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_venue_altitude_feet=latest.venue_altitude_feet,
        max_venue_altitude_feet=max(venue_altitude_values),
        latest_altitude_change_feet=latest.altitude_change_feet,
        max_altitude_change_feet=max(altitude_change_values),
        latest_rest_days=latest.rest_days,
        min_rest_days=min(rest_values),
        latest_back_to_back_game_count=latest.back_to_back_game_count,
        max_back_to_back_game_count=max(back_to_back_values),
        latest_travel_miles=latest.travel_miles,
        max_travel_miles=max(travel_values),
        latest_available_rotation_players=latest.available_rotation_players,
        min_available_rotation_players=min(rotation_values),
        fatigue_pressure_index=fatigue_pressure_index,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_team_event_identity(
    signals: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
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
    fatigue_pressure_index: Decimal,
    venue_altitude_feet: Decimal,
    altitude_change_feet: Decimal,
    rest_days: Decimal,
    back_to_back_game_count: Decimal,
    travel_miles: Decimal,
    available_rotation_players: Decimal,
    config: MarketResearchBasketballAltitudeTravelFatigueDigestConfig,
) -> tuple[str, ...]:
    if signal_count < config.min_signal_count:
        return (LIMITED_HISTORY_REASON,)
    reason_codes = []
    if fatigue_pressure_index >= config.fatigue_pressure_index_watch_threshold:
        reason_codes.append(PRESSURE_INDEX_REASON)
    if venue_altitude_feet >= config.venue_altitude_feet_watch_threshold:
        reason_codes.append(HIGH_ALTITUDE_REASON)
    if altitude_change_feet >= config.altitude_change_feet_watch_threshold:
        reason_codes.append(ALTITUDE_CHANGE_REASON)
    if rest_days <= config.rest_day_watch_threshold:
        reason_codes.append(REST_REASON)
    if back_to_back_game_count >= config.back_to_back_game_watch_threshold:
        reason_codes.append(BACK_TO_BACK_REASON)
    if travel_miles >= config.travel_mile_watch_threshold:
        reason_codes.append(TRAVEL_REASON)
    if available_rotation_players <= config.rotation_depth_watch_threshold:
        reason_codes.append(ROTATION_DEPTH_REASON)
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
        return Decimal("0")
    if status == LIMITED_HISTORY_STATUS:
        return Decimal("1")
    return Decimal("2")


def _row_sort_key(
    row: MarketResearchBasketballAltitudeTravelFatigueDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        _row_status_rank(row.digest_status),
        -row.fatigue_pressure_index,
        -row.max_travel_miles,
        row.event_key,
        row.team_key,
        row.team_event_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestRow, ...],
) -> tuple[MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount(
            reason_code=reason_code,
            team_event_count=_decimal_count(counts[reason_code]),
            team_event_ratio=_ratio(_decimal_count(counts[reason_code]), total),
        )
        for reason_code in DIGEST_REASON_CODES
        if reason_code in counts
    )


def _reason_team_event_count(
    rows: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    signals: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (signal.team_event_key, signal.signal_config_version)
                for signal in signals
            }
        )
    )


def _fatigue_pressure_index(
    venue_altitude_feet: Decimal,
    altitude_change_feet: Decimal,
    rest_days: Decimal,
    back_to_back_game_count: Decimal,
    travel_miles: Decimal,
    available_rotation_players: Decimal,
    config: MarketResearchBasketballAltitudeTravelFatigueDigestConfig,
) -> Decimal:
    components = (
        _capped_ratio(venue_altitude_feet, config.venue_altitude_feet_watch_threshold),
        _capped_ratio(altitude_change_feet, config.altitude_change_feet_watch_threshold),
        _inverse_capped_ratio(config.rest_day_watch_threshold, rest_days),
        _capped_ratio(back_to_back_game_count, config.back_to_back_game_watch_threshold),
        _capped_ratio(travel_miles, config.travel_mile_watch_threshold),
        _rotation_depth_pressure(
            config.rotation_depth_watch_threshold,
            available_rotation_players,
        ),
    )
    return _ratio(_sum_decimal(components), Decimal("6"))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ONE
    ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM, rounding=ROUND_DOWN)


def _inverse_capped_ratio(threshold: Decimal, value: Decimal) -> Decimal:
    if threshold == ZERO:
        return ONE
    if value >= threshold:
        return ZERO
    ratio = (threshold - value) / threshold
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM, rounding=ROUND_DOWN)


def _rotation_depth_pressure(threshold: Decimal, value: Decimal) -> Decimal:
    if value >= threshold:
        return ZERO
    denominator = (threshold - ROTATION_DEPTH_PRESSURE_FLOOR).quantize(QUANTUM)
    if denominator <= ZERO:
        return ONE
    ratio = (threshold - value) / denominator
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM, rounding=ROUND_DOWN)


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


def _validate_row(row: MarketResearchBasketballAltitudeTravelFatigueDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.max_venue_altitude_feet < row.latest_venue_altitude_feet:
        raise ValueError("max_venue_altitude_feet must cover latest value")
    if row.max_altitude_change_feet < row.latest_altitude_change_feet:
        raise ValueError("max_altitude_change_feet must cover latest value")
    if row.min_rest_days > row.latest_rest_days:
        raise ValueError("min_rest_days must cover latest value")
    if row.max_back_to_back_game_count < row.latest_back_to_back_game_count:
        raise ValueError("max_back_to_back_game_count must cover latest value")
    if row.max_travel_miles < row.latest_travel_miles:
        raise ValueError("max_travel_miles must cover latest value")
    if row.min_available_rotation_players > row.latest_available_rotation_players:
        raise ValueError("min_available_rotation_players must cover latest value")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(
    report: MarketResearchBasketballAltitudeTravelFatigueDigestReport,
) -> None:
    if report.team_event_count != _decimal_count(len(report.rows)):
        raise ValueError("team_event_count must match rows")
    if report.clear_team_event_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_team_event_count must match rows")
    if report.watch_team_event_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_team_event_count must match rows")
    if report.limited_history_team_event_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == LIMITED_HISTORY_STATUS),
    ):
        raise ValueError("limited_history_team_event_count must match rows")
    if report.signal_count != _sum_decimal(row.signal_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_codes = (EMPTY_REASON,)
    elif report.watch_team_event_count == ZERO:
        expected_reason_codes = _sort_reason_codes(
            (*tuple(item.reason_code for item in expected_reason_counts), PASSED_REASON),
            DIGEST_REASON_CODES,
        )
    else:
        expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = WATCH_STATUS if report.watch_team_event_count > ZERO else PASS_STATUS
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.high_altitude_team_event_count != _reason_team_event_count(
        report.rows,
        HIGH_ALTITUDE_REASON,
    ):
        raise ValueError("high_altitude_team_event_count must match rows")
    if report.altitude_change_team_event_count != _reason_team_event_count(
        report.rows,
        ALTITUDE_CHANGE_REASON,
    ):
        raise ValueError("altitude_change_team_event_count must match rows")
    if report.short_rest_team_event_count != _reason_team_event_count(
        report.rows,
        REST_REASON,
    ):
        raise ValueError("short_rest_team_event_count must match rows")
    if report.back_to_back_team_event_count != _reason_team_event_count(
        report.rows,
        BACK_TO_BACK_REASON,
    ):
        raise ValueError("back_to_back_team_event_count must match rows")
    if report.travel_fatigue_team_event_count != _reason_team_event_count(
        report.rows,
        TRAVEL_REASON,
    ):
        raise ValueError("travel_fatigue_team_event_count must match rows")
    if report.rotation_depth_team_event_count != _reason_team_event_count(
        report.rows,
        ROTATION_DEPTH_REASON,
    ):
        raise ValueError("rotation_depth_team_event_count must match rows")
    if report.fatigue_pressure_index_team_event_count != _reason_team_event_count(
        report.rows,
        PRESSURE_INDEX_REASON,
    ):
        raise ValueError("fatigue_pressure_index_team_event_count must match rows")
    if report.max_fatigue_pressure_index != _max_or_none(
        row.fatigue_pressure_index for row in report.rows
    ):
        raise ValueError("max_fatigue_pressure_index must match rows")
    if report.max_venue_altitude_feet != _max_or_none(
        row.max_venue_altitude_feet for row in report.rows
    ):
        raise ValueError("max_venue_altitude_feet must match rows")
    if report.max_altitude_change_feet != _max_or_none(
        row.max_altitude_change_feet for row in report.rows
    ):
        raise ValueError("max_altitude_change_feet must match rows")
    if report.min_rest_days != _min_or_none(row.min_rest_days for row in report.rows):
        raise ValueError("min_rest_days must match rows")
    if report.max_travel_miles != _max_or_none(row.max_travel_miles for row in report.rows):
        raise ValueError("max_travel_miles must match rows")
    if report.min_available_rotation_players != _min_or_none(
        row.min_available_rotation_players for row in report.rows
    ):
        raise ValueError("min_available_rotation_players must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchBasketballAltitudeTravelFatigueDigestRow, ...],
) -> tuple[MarketResearchBasketballAltitudeTravelFatigueDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBasketballAltitudeTravelFatigueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBasketballAltitudeTravelFatigueDigestRow",
            )
        _require_flags("row", row)
        if row.team_event_key in seen:
            raise ValueError("rows must contain unique team_event_key values")
        seen.add(row.team_event_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_source_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized = []
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
    values: tuple[
        MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount",
            )
        _require_flags("reason_code_count", value)
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
    normalized = tuple(dict.fromkeys(values))
    if len(normalized) != len(values):
        raise ValueError(f"{field_name} must be unique")
    if _sort_reason_codes(values, allowed) != values:
        raise ValueError(f"{field_name} must be sorted")
    return values


def _sort_reason_codes(
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _require_reason_code(
    field_name: str,
    value: str,
    allowed: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _six(normalized)


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    _require_ratio_decimal(field_name, normalized)
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized.quantize(QUANTUM)


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal") from exc


def _six(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return _six(total)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")
    if value[0] in "._-" or value[-1] in "._-":
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(item_key): _payload_value(item_value) for item_key, item_value in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains a non-Decimal numeric value")
