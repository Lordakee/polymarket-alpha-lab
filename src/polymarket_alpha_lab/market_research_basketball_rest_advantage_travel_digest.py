"""Pure report-only basketball rest-advantage travel digest reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_DOWN, ROUND_HALF_EVEN, localcontext
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_BASKETBALL_REST_ADVANTAGE_TRAVEL_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-rest-advantage-travel-digest-v0"
)
BASKETBALL_REST_ADVANTAGE_TRAVEL_RESEARCH_SCOPE = (
    "basketball rest advantage travel research digest only"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
LIMITED_HISTORY_STATUS = "limited_history"

PRESSURE_REASON = "basketball_rest_advantage_travel_pressure_high"
SHORT_REST_REASON = "basketball_rest_advantage_travel_short_rest"
REST_GAP_REASON = "basketball_rest_advantage_travel_rest_gap_high"
TRAVEL_REASON = "basketball_rest_advantage_travel_miles_high"
LIMITED_HISTORY_REASON = "basketball_rest_advantage_travel_limited_history"
CLEAR_REASON = "basketball_rest_advantage_travel_clear"
PASSED_REASON = "basketball_rest_advantage_travel_passed"
EMPTY_REASON = "basketball_rest_advantage_travel_empty"

ROW_REASON_CODES = (
    PRESSURE_REASON,
    SHORT_REST_REASON,
    REST_GAP_REASON,
    TRAVEL_REASON,
    LIMITED_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    PRESSURE_REASON,
    SHORT_REST_REASON,
    REST_GAP_REASON,
    TRAVEL_REASON,
    LIMITED_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_basketball_rest_advantage_travel_digest",
    WATCH_STATUS: "review_report_only_basketball_rest_advantage_travel_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_REST_ADVANTAGE_TRAVEL_DIGEST_CONFIG_VERSION",
    "BASKETBALL_REST_ADVANTAGE_TRAVEL_RESEARCH_SCOPE",
    "MarketResearchBasketballRestAdvantageTravelDigestConfig",
    "MarketResearchBasketballRestAdvantageTravelDigestSignal",
    "MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount",
    "MarketResearchBasketballRestAdvantageTravelDigestRow",
    "MarketResearchBasketballRestAdvantageTravelDigestReport",
    "build_market_research_basketball_rest_advantage_travel_digest",
    "market_research_basketball_rest_advantage_travel_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBasketballRestAdvantageTravelDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_REST_ADVANTAGE_TRAVEL_DIGEST_CONFIG_VERSION
    )
    short_rest_watch_threshold_hours: Decimal = Decimal("24.000000")
    rest_disadvantage_watch_threshold_hours: Decimal = Decimal("12.000000")
    travel_watch_threshold_miles: Decimal = Decimal("650.000000")
    travel_rest_pressure_index_watch_threshold: Decimal = Decimal("0.700000")
    min_signal_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRestAdvantageTravelDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "travel_rest_pressure_index_watch_threshold",
            _normalize_ratio_decimal(
                "travel_rest_pressure_index_watch_threshold",
                self.travel_rest_pressure_index_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_signal_count",
            _normalize_positive_whole_decimal("min_signal_count", self.min_signal_count),
        )
        for field_name in (
            "short_rest_watch_threshold_hours",
            "rest_disadvantage_watch_threshold_hours",
            "travel_watch_threshold_miles",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballRestAdvantageTravelDigestSignal(_NoSubclass):
    team_game_key: str
    team_key: str
    opponent_key: str
    league_key: str
    market_slug: str
    observed_at: datetime
    game_start_at: datetime
    team_rest_hours: Decimal
    opponent_rest_hours: Decimal
    travel_miles: Decimal
    source_count: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_REST_ADVANTAGE_TRAVEL_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRestAdvantageTravelDigestSignal,
            "signal",
        )
        for field_name in (
            "team_game_key",
            "team_key",
            "opponent_key",
            "league_key",
            "market_slug",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "game_start_at",
            _as_utc("game_start_at", self.game_start_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        for field_name in ("team_rest_hours", "opponent_rest_hours", "travel_miles"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    team_game_count: Decimal
    team_game_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "team_game_count",
            _normalize_nonnegative_whole_decimal("team_game_count", self.team_game_count),
        )
        object.__setattr__(
            self,
            "team_game_ratio",
            _normalize_ratio_decimal("team_game_ratio", self.team_game_ratio),
        )
        require_paper_only_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballRestAdvantageTravelDigestRow(_NoSubclass):
    team_game_key: str
    team_key: str
    opponent_key: str
    league_key: str
    market_slug: str
    game_start_at: datetime
    signal_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_team_rest_hours: Decimal
    min_team_rest_hours: Decimal
    latest_opponent_rest_hours: Decimal
    max_opponent_rest_hours: Decimal
    rest_disadvantage_hours: Decimal
    latest_travel_miles: Decimal
    max_travel_miles: Decimal
    travel_rest_pressure_index: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBasketballRestAdvantageTravelDigestRow, "row")
        for field_name in (
            "team_game_key",
            "team_key",
            "opponent_key",
            "league_key",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("game_start_at", "first_observed_at", "latest_observed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in ("signal_count", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_team_rest_hours",
            "min_team_rest_hours",
            "latest_opponent_rest_hours",
            "max_opponent_rest_hours",
            "rest_disadvantage_hours",
            "latest_travel_miles",
            "max_travel_miles",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "travel_rest_pressure_index",
            _normalize_ratio_decimal(
                "travel_rest_pressure_index",
                self.travel_rest_pressure_index,
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
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballRestAdvantageTravelDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    team_game_count: Decimal
    clear_team_game_count: Decimal
    watch_team_game_count: Decimal
    limited_history_team_game_count: Decimal
    signal_count: Decimal
    short_rest_team_game_count: Decimal
    rest_disadvantage_team_game_count: Decimal
    travel_load_team_game_count: Decimal
    travel_rest_pressure_index_team_game_count: Decimal
    short_rest_watch_threshold_hours: Decimal
    rest_disadvantage_watch_threshold_hours: Decimal
    travel_watch_threshold_miles: Decimal
    travel_rest_pressure_index_watch_threshold: Decimal
    min_signal_count: Decimal
    max_travel_rest_pressure_index: Decimal | None
    min_team_rest_hours: Decimal | None
    max_rest_disadvantage_hours: Decimal | None
    max_travel_miles: Decimal | None
    rows: tuple[MarketResearchBasketballRestAdvantageTravelDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBasketballRestAdvantageTravelDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_REST_ADVANTAGE_TRAVEL_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball rest advantage travel scope")
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "team_game_count",
            "clear_team_game_count",
            "watch_team_game_count",
            "limited_history_team_game_count",
            "signal_count",
            "short_rest_team_game_count",
            "rest_disadvantage_team_game_count",
            "travel_load_team_game_count",
            "travel_rest_pressure_index_team_game_count",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "short_rest_watch_threshold_hours",
            "rest_disadvantage_watch_threshold_hours",
            "travel_watch_threshold_miles",
            "travel_rest_pressure_index_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal(
            "travel_rest_pressure_index_watch_threshold",
            self.travel_rest_pressure_index_watch_threshold,
        )
        for field_name in (
            "min_team_rest_hours",
            "max_rest_disadvantage_hours",
            "max_travel_miles",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_nonnegative_decimal(field_name, value),
                )
        if self.max_travel_rest_pressure_index is not None:
            object.__setattr__(
                self,
                "max_travel_rest_pressure_index",
                _normalize_ratio_decimal(
                    "max_travel_rest_pressure_index",
                    self.max_travel_rest_pressure_index,
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
        require_paper_only_flags("report", self)


def build_market_research_basketball_rest_advantage_travel_digest(
    signals: list[MarketResearchBasketballRestAdvantageTravelDigestSignal]
    | tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
    *,
    config: MarketResearchBasketballRestAdvantageTravelDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballRestAdvantageTravelDigestReport:
    if type(config) is not MarketResearchBasketballRestAdvantageTravelDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBasketballRestAdvantageTravelDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_signals(signals)
    _reject_inconsistent_time_surfaces(normalized, generated_at_utc)
    rows = _rows(normalized, config)
    watch_count = _count_decimal(sum(ONE for row in rows if row.digest_status == WATCH_STATUS))
    digest_status = WATCH_STATUS if watch_count > ZERO else PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                team_game_count=ONE,
                team_game_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = tuple((*reason_codes, PASSED_REASON))

    return MarketResearchBasketballRestAdvantageTravelDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_REST_ADVANTAGE_TRAVEL_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        team_game_count=_count_decimal(len(rows)),
        clear_team_game_count=_count_decimal(
            sum(ONE for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_team_game_count=watch_count,
        limited_history_team_game_count=_count_decimal(
            sum(ONE for row in rows if row.digest_status == LIMITED_HISTORY_STATUS),
        ),
        signal_count=_count_decimal(len(normalized)),
        short_rest_team_game_count=_reason_team_game_count(rows, SHORT_REST_REASON),
        rest_disadvantage_team_game_count=_reason_team_game_count(rows, REST_GAP_REASON),
        travel_load_team_game_count=_reason_team_game_count(rows, TRAVEL_REASON),
        travel_rest_pressure_index_team_game_count=_reason_team_game_count(
            rows,
            PRESSURE_REASON,
        ),
        short_rest_watch_threshold_hours=config.short_rest_watch_threshold_hours,
        rest_disadvantage_watch_threshold_hours=(
            config.rest_disadvantage_watch_threshold_hours
        ),
        travel_watch_threshold_miles=config.travel_watch_threshold_miles,
        travel_rest_pressure_index_watch_threshold=(
            config.travel_rest_pressure_index_watch_threshold
        ),
        min_signal_count=config.min_signal_count,
        max_travel_rest_pressure_index=_max_or_none(
            row.travel_rest_pressure_index for row in rows
        ),
        min_team_rest_hours=_min_or_none(row.min_team_rest_hours for row in rows),
        max_rest_disadvantage_hours=_max_or_none(
            row.rest_disadvantage_hours for row in rows
        ),
        max_travel_miles=_max_or_none(row.max_travel_miles for row in rows),
        rows=rows,
        signal_config_versions=_signal_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_rest_advantage_travel_digest_payload(
    report: MarketResearchBasketballRestAdvantageTravelDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballRestAdvantageTravelDigestReport:
        raise ValueError(
            "report must be a MarketResearchBasketballRestAdvantageTravelDigestReport",
    )
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def _normalize_signals(
    signals: list[MarketResearchBasketballRestAdvantageTravelDigestSignal]
    | tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
) -> tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, datetime]] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchBasketballRestAdvantageTravelDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchBasketballRestAdvantageTravelDigestSignal",
            )
        require_paper_only_flags("signal", signal)
        key = (signal.team_game_key, signal.observed_at)
        if key in seen:
            raise ValueError("signals must not contain duplicate team game observations")
        seen.add(key)
    return normalized


def _reject_inconsistent_time_surfaces(
    signals: tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
    generated_at: datetime,
) -> None:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if signal.game_start_at < generated_at:
            raise ValueError("game_start_at must not be before generated_at")


def _rows(
    signals: tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
    config: MarketResearchBasketballRestAdvantageTravelDigestConfig,
) -> tuple[MarketResearchBasketballRestAdvantageTravelDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBasketballRestAdvantageTravelDigestSignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.team_game_key, []).append(signal)
    rows = tuple(_row_for_team_game(tuple(items), config) for items in grouped.values())
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_team_game(
    signals: tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
    config: MarketResearchBasketballRestAdvantageTravelDigestConfig,
) -> MarketResearchBasketballRestAdvantageTravelDigestRow:
    timeline = tuple(sorted(signals, key=lambda item: item.observed_at))
    first = timeline[0]
    latest = timeline[-1]
    _validate_team_game_identity(timeline)
    team_rest_values = tuple(item.team_rest_hours for item in timeline)
    opponent_rest_values = tuple(item.opponent_rest_hours for item in timeline)
    travel_values = tuple(item.travel_miles for item in timeline)
    rest_disadvantage_hours = _rest_disadvantage_hours(
        latest.team_rest_hours,
        latest.opponent_rest_hours,
    )
    pressure_index = _travel_rest_pressure_index(
        team_rest_hours=latest.team_rest_hours,
        rest_disadvantage_hours=rest_disadvantage_hours,
        travel_miles=latest.travel_miles,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal_count=_count_decimal(len(timeline)),
        team_rest_hours=latest.team_rest_hours,
        rest_disadvantage_hours=rest_disadvantage_hours,
        travel_miles=latest.travel_miles,
        travel_rest_pressure_index=pressure_index,
        config=config,
    )
    return MarketResearchBasketballRestAdvantageTravelDigestRow(
        team_game_key=first.team_game_key,
        team_key=first.team_key,
        opponent_key=first.opponent_key,
        league_key=first.league_key,
        market_slug=first.market_slug,
        game_start_at=first.game_start_at,
        signal_count=_count_decimal(len(timeline)),
        source_count=_sum_decimal(item.source_count for item in timeline),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_team_rest_hours=latest.team_rest_hours,
        min_team_rest_hours=min(team_rest_values),
        latest_opponent_rest_hours=latest.opponent_rest_hours,
        max_opponent_rest_hours=max(opponent_rest_values),
        rest_disadvantage_hours=rest_disadvantage_hours,
        latest_travel_miles=latest.travel_miles,
        max_travel_miles=max(travel_values),
        travel_rest_pressure_index=pressure_index,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_team_game_identity(
    signals: tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
) -> None:
    expected = signals[0]
    for signal in signals:
        if signal.team_key != expected.team_key:
            raise ValueError("team_key must match within team_game_key")
        if signal.opponent_key != expected.opponent_key:
            raise ValueError("opponent_key must match within team_game_key")
        if signal.league_key != expected.league_key:
            raise ValueError("league_key must match within team_game_key")
        if signal.market_slug != expected.market_slug:
            raise ValueError("market_slug must match within team_game_key")
        if signal.game_start_at != expected.game_start_at:
            raise ValueError("game_start_at must match within team_game_key")


def _row_reason_codes(
    *,
    signal_count: Decimal,
    team_rest_hours: Decimal,
    rest_disadvantage_hours: Decimal,
    travel_miles: Decimal,
    travel_rest_pressure_index: Decimal,
    config: MarketResearchBasketballRestAdvantageTravelDigestConfig,
) -> tuple[str, ...]:
    if signal_count < config.min_signal_count:
        return (LIMITED_HISTORY_REASON,)
    reason_codes = []
    if travel_rest_pressure_index >= config.travel_rest_pressure_index_watch_threshold:
        reason_codes.append(PRESSURE_REASON)
    if team_rest_hours <= config.short_rest_watch_threshold_hours:
        reason_codes.append(SHORT_REST_REASON)
    if rest_disadvantage_hours >= config.rest_disadvantage_watch_threshold_hours:
        reason_codes.append(REST_GAP_REASON)
    if travel_miles >= config.travel_watch_threshold_miles:
        reason_codes.append(TRAVEL_REASON)
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(sorted(reason_codes, key=ROW_REASON_CODES.index))


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


def _row_sort_key(row: MarketResearchBasketballRestAdvantageTravelDigestRow) -> tuple[object, ...]:
    return (
        _row_status_rank(row.digest_status),
        -row.travel_rest_pressure_index,
        -row.rest_disadvantage_hours,
        -row.max_travel_miles,
        row.league_key,
        row.team_key,
        row.team_game_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballRestAdvantageTravelDigestRow, ...],
) -> tuple[MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount, ...]:
    total = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount(
            reason_code=reason_code,
            team_game_count=_count_decimal(count),
            team_game_ratio=_ratio(_count_decimal(count), total),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: DIGEST_REASON_CODES.index(item[0]),
        )
    )


def _reason_team_game_count(
    rows: tuple[MarketResearchBasketballRestAdvantageTravelDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(ONE for row in rows if reason_code in row.reason_codes))


def _signal_config_versions(
    signals: tuple[MarketResearchBasketballRestAdvantageTravelDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (signal.team_game_key, signal.signal_config_version)
                for signal in signals
            },
        ),
    )


def _rest_disadvantage_hours(team_rest_hours: Decimal, opponent_rest_hours: Decimal) -> Decimal:
    rest_gap = _quantize_decimal(opponent_rest_hours - team_rest_hours)
    if rest_gap < ZERO:
        return ZERO
    return rest_gap


def _travel_rest_pressure_index(
    *,
    team_rest_hours: Decimal,
    rest_disadvantage_hours: Decimal,
    travel_miles: Decimal,
    config: MarketResearchBasketballRestAdvantageTravelDigestConfig,
) -> Decimal:
    components = (
        _short_rest_score(config.short_rest_watch_threshold_hours, team_rest_hours),
        _capped_ratio(
            rest_disadvantage_hours,
            config.rest_disadvantage_watch_threshold_hours,
        ),
        _capped_ratio(travel_miles, config.travel_watch_threshold_miles),
    )
    return _ratio(_sum_decimal(components), Decimal("3.000000"))


def _short_rest_score(threshold: Decimal, value: Decimal) -> Decimal:
    if value >= threshold:
        return ZERO
    return Decimal("0.750000")


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ONE
    ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM, rounding=ROUND_DOWN)


def _validate_row(row: MarketResearchBasketballRestAdvantageTravelDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.min_team_rest_hours > row.latest_team_rest_hours:
        raise ValueError("min_team_rest_hours must cover latest value")
    if row.max_opponent_rest_hours < row.latest_opponent_rest_hours:
        raise ValueError("max_opponent_rest_hours must cover latest value")
    if row.max_travel_miles < row.latest_travel_miles:
        raise ValueError("max_travel_miles must cover latest value")
    if row.rest_disadvantage_hours != _rest_disadvantage_hours(
        row.latest_team_rest_hours,
        row.latest_opponent_rest_hours,
    ):
        raise ValueError("rest_disadvantage_hours must match latest rest inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBasketballRestAdvantageTravelDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.team_game_count != _count_decimal(len(report.rows)):
        raise ValueError("team_game_count must match rows")
    if report.clear_team_game_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_team_game_count must match rows")
    if report.watch_team_game_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_team_game_count must match rows")
    if report.limited_history_team_game_count != _count_decimal(
        sum(ONE for row in report.rows if row.digest_status == LIMITED_HISTORY_STATUS),
    ):
        raise ValueError("limited_history_team_game_count must match rows")
    if report.signal_count != _sum_decimal(row.signal_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    if report.short_rest_team_game_count != _reason_team_game_count(
        report.rows,
        SHORT_REST_REASON,
    ):
        raise ValueError("short_rest_team_game_count must match rows")
    if report.rest_disadvantage_team_game_count != _reason_team_game_count(
        report.rows,
        REST_GAP_REASON,
    ):
        raise ValueError("rest_disadvantage_team_game_count must match rows")
    if report.travel_load_team_game_count != _reason_team_game_count(
        report.rows,
        TRAVEL_REASON,
    ):
        raise ValueError("travel_load_team_game_count must match rows")
    if report.travel_rest_pressure_index_team_game_count != _reason_team_game_count(
        report.rows,
        PRESSURE_REASON,
    ):
        raise ValueError("travel_rest_pressure_index_team_game_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                team_game_count=ONE,
                team_game_ratio=ZERO,
            ),
        )
        expected_reason_codes = (EMPTY_REASON,)
    elif report.digest_status == PASS_STATUS:
        expected_reason_codes = tuple((*expected_reason_codes, PASSED_REASON))
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.max_travel_rest_pressure_index != _max_or_none(
        row.travel_rest_pressure_index for row in report.rows
    ):
        raise ValueError("max_travel_rest_pressure_index must match rows")
    if report.min_team_rest_hours != _min_or_none(row.min_team_rest_hours for row in report.rows):
        raise ValueError("min_team_rest_hours must match rows")
    if report.max_rest_disadvantage_hours != _max_or_none(
        row.rest_disadvantage_hours for row in report.rows
    ):
        raise ValueError("max_rest_disadvantage_hours must match rows")
    if report.max_travel_miles != _max_or_none(row.max_travel_miles for row in report.rows):
        raise ValueError("max_travel_miles must match rows")
    if report.digest_status == WATCH_STATUS and report.watch_team_game_count == ZERO:
        raise ValueError("watch reports require watch rows")
    if report.digest_status == PASS_STATUS and report.watch_team_game_count != ZERO:
        raise ValueError("pass reports must not include watch rows")


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchBasketballRestAdvantageTravelDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBasketballRestAdvantageTravelDigestRow:
            raise ValueError("rows must contain MarketResearchBasketballRestAdvantageTravelDigestRow")
        require_paper_only_flags("row", row)
        if row.team_game_key in seen:
            raise ValueError("rows must not contain duplicate team_game_key")
        seen.add(row.team_game_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signal_config_versions must be a list or tuple")
    normalized = tuple(value)
    for item in normalized:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("signal_config_versions entries must be pairs")
        team_game_key, config_version = item
        _require_canonical_string("signal_config_versions team_game_key", team_game_key)
        _require_canonical_string("signal_config_versions config_version", config_version)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    if len(normalized) != len(set(normalized)):
        raise ValueError("signal_config_versions must be unique")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount",
            )
    if normalized != tuple(
        sorted(normalized, key=lambda item: DIGEST_REASON_CODES.index(item.reason_code))
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(name, reason_code, allowed)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must be unique")
    if reason_codes != tuple(sorted(reason_codes, key=allowed.index)):
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} contains invalid reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str or not CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a canonical string")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be whole")
    return normalized


def _normalize_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    _require_ratio_decimal(name, normalized)
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{name} must be at most 1")


def _count_decimal(value: object) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    return _quantize_decimal(sum(tuple(values), ZERO))  # type: ignore[arg-type]


def _max_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _quantize_decimal(max(normalized))


def _min_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _quantize_decimal(min(normalized))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
