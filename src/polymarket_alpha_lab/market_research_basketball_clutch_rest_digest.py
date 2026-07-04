"""Pure in-memory reducer for basketball clutch-rest research reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASKETBALL_CLUTCH_REST_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-clutch-rest-digest-v0"
)
BASKETBALL_CLUTCH_REST_RESEARCH_SCOPE = "basketball clutch rest research digest only"

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
LIMITED_HISTORY_STATUS = "limited_history"

LOAD_REASON = "basketball_clutch_rest_clutch_load_index_high"
CLUTCH_REASON = "basketball_clutch_rest_clutch_minutes_high"
REST_REASON = "basketball_clutch_rest_rest_short"
TRAVEL_REASON = "basketball_clutch_rest_travel_high"
LIMITED_HISTORY_REASON = "basketball_clutch_rest_limited_history"
CLEAR_REASON = "basketball_clutch_rest_clear"
PASSED_REASON = "basketball_clutch_rest_passed"
EMPTY_REASON = "basketball_clutch_rest_empty"

ROW_REASON_CODES = (
    LOAD_REASON,
    CLUTCH_REASON,
    REST_REASON,
    TRAVEL_REASON,
    LIMITED_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    LOAD_REASON,
    CLUTCH_REASON,
    REST_REASON,
    TRAVEL_REASON,
    LIMITED_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_basketball_clutch_rest_digest",
    WATCH_STATUS: "review_report_only_basketball_clutch_rest_digest",
}

ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_CLUTCH_REST_DIGEST_CONFIG_VERSION",
    "BASKETBALL_CLUTCH_REST_RESEARCH_SCOPE",
    "MarketResearchBasketballClutchRestDigestConfig",
    "MarketResearchBasketballClutchRestDigestSignal",
    "MarketResearchBasketballClutchRestDigestReasonCodeCount",
    "MarketResearchBasketballClutchRestDigestRow",
    "MarketResearchBasketballClutchRestDigestReport",
    "build_market_research_basketball_clutch_rest_digest",
    "market_research_basketball_clutch_rest_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBasketballClutchRestDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_CLUTCH_REST_DIGEST_CONFIG_VERSION
    )
    clutch_minutes_watch_threshold: Decimal = Decimal("5")
    rest_hours_watch_threshold: Decimal = Decimal("24")
    travel_miles_watch_threshold: Decimal = Decimal("650")
    clutch_load_index_watch_threshold: Decimal = Decimal("0.650000")
    min_signal_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "clutch_load_index_watch_threshold",
            _normalize_ratio_decimal(
                "clutch_load_index_watch_threshold",
                self.clutch_load_index_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_signal_count",
            _normalize_positive_whole_decimal("min_signal_count", self.min_signal_count),
        )
        for field_name in (
            "clutch_minutes_watch_threshold",
            "rest_hours_watch_threshold",
            "travel_miles_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballClutchRestDigestSignal(_NoSubclass):
    team_game_key: str
    team_key: str
    league_key: str
    observed_at: datetime
    clutch_minutes_last_game: Decimal
    rest_hours: Decimal
    travel_miles: Decimal
    projected_rotation_minutes: Decimal
    source_count: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_CLUTCH_REST_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_game_key",
            "team_key",
            "league_key",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        for field_name in (
            "clutch_minutes_last_game",
            "rest_hours",
            "travel_miles",
            "projected_rotation_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBasketballClutchRestDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    team_game_count: Decimal
    team_game_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballClutchRestDigestRow(_NoSubclass):
    team_game_key: str
    team_key: str
    league_key: str
    signal_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_clutch_minutes_last_game: Decimal
    max_clutch_minutes_last_game: Decimal
    latest_rest_hours: Decimal
    min_rest_hours: Decimal
    latest_travel_miles: Decimal
    max_travel_miles: Decimal
    latest_projected_rotation_minutes: Decimal
    max_projected_rotation_minutes: Decimal
    clutch_load_index: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_game_key", "team_key", "league_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("signal_count", "source_count"):
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
            "latest_clutch_minutes_last_game",
            "max_clutch_minutes_last_game",
            "latest_rest_hours",
            "min_rest_hours",
            "latest_travel_miles",
            "max_travel_miles",
            "latest_projected_rotation_minutes",
            "max_projected_rotation_minutes",
            "clutch_load_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBasketballClutchRestDigestReport(_NoSubclass):
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
    clutch_minutes_team_game_count: Decimal
    short_rest_team_game_count: Decimal
    travel_load_team_game_count: Decimal
    clutch_load_index_team_game_count: Decimal
    clutch_minutes_watch_threshold: Decimal
    rest_hours_watch_threshold: Decimal
    travel_miles_watch_threshold: Decimal
    clutch_load_index_watch_threshold: Decimal
    min_signal_count: Decimal
    max_clutch_load_index: Decimal | None
    max_clutch_minutes_last_game: Decimal | None
    min_rest_hours: Decimal | None
    max_travel_miles: Decimal | None
    rows: tuple[MarketResearchBasketballClutchRestDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballClutchRestDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_CLUTCH_REST_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball clutch rest scope")
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "team_game_count",
            "clear_team_game_count",
            "watch_team_game_count",
            "limited_history_team_game_count",
            "signal_count",
            "clutch_minutes_team_game_count",
            "short_rest_team_game_count",
            "travel_load_team_game_count",
            "clutch_load_index_team_game_count",
            "min_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "clutch_minutes_watch_threshold",
            "rest_hours_watch_threshold",
            "travel_miles_watch_threshold",
            "clutch_load_index_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal(
            "clutch_load_index_watch_threshold",
            self.clutch_load_index_watch_threshold,
        )
        for field_name in (
            "max_clutch_load_index",
            "max_clutch_minutes_last_game",
            "min_rest_hours",
            "max_travel_miles",
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
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_basketball_clutch_rest_digest(
    signals: list[MarketResearchBasketballClutchRestDigestSignal]
    | tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
    *,
    config: MarketResearchBasketballClutchRestDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballClutchRestDigestReport:
    if type(config) is not MarketResearchBasketballClutchRestDigestConfig:
        raise ValueError("config must be a MarketResearchBasketballClutchRestDigestConfig")
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
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBasketballClutchRestDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                team_game_count=ONE,
                team_game_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = tuple((*reason_codes, PASSED_REASON))

    return MarketResearchBasketballClutchRestDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_CLUTCH_REST_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        team_game_count=_decimal_count(len(rows)),
        clear_team_game_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_team_game_count=watch_count,
        limited_history_team_game_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == LIMITED_HISTORY_STATUS),
        ),
        signal_count=_decimal_count(len(normalized)),
        clutch_minutes_team_game_count=_reason_team_game_count(rows, CLUTCH_REASON),
        short_rest_team_game_count=_reason_team_game_count(rows, REST_REASON),
        travel_load_team_game_count=_reason_team_game_count(rows, TRAVEL_REASON),
        clutch_load_index_team_game_count=_reason_team_game_count(rows, LOAD_REASON),
        clutch_minutes_watch_threshold=config.clutch_minutes_watch_threshold,
        rest_hours_watch_threshold=config.rest_hours_watch_threshold,
        travel_miles_watch_threshold=config.travel_miles_watch_threshold,
        clutch_load_index_watch_threshold=config.clutch_load_index_watch_threshold,
        min_signal_count=config.min_signal_count,
        max_clutch_load_index=_max_or_none(row.clutch_load_index for row in rows),
        max_clutch_minutes_last_game=_max_or_none(
            row.max_clutch_minutes_last_game for row in rows
        ),
        min_rest_hours=_min_or_none(row.min_rest_hours for row in rows),
        max_travel_miles=_max_or_none(row.max_travel_miles for row in rows),
        rows=rows,
        signal_config_versions=_signal_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_clutch_rest_digest_payload(
    report: MarketResearchBasketballClutchRestDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBasketballClutchRestDigestReport:
        raise ValueError("report must be a MarketResearchBasketballClutchRestDigestReport")
    _require_flags("report", report)
    return _payload_value(asdict(report))  # type: ignore[return-value]


def _normalize_signals(
    signals: list[MarketResearchBasketballClutchRestDigestSignal]
    | tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
) -> tuple[MarketResearchBasketballClutchRestDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, datetime]] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchBasketballClutchRestDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchBasketballClutchRestDigestSignal",
            )
        _require_flags("signal", signal)
        key = (signal.team_game_key, signal.observed_at)
        if key in seen:
            raise ValueError("signals must not contain duplicate team game observations")
        seen.add(key)
    return normalized


def _reject_future_signals(
    signals: tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
    generated_at: datetime,
) -> None:
    for signal in signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    signals: tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
    config: MarketResearchBasketballClutchRestDigestConfig,
) -> tuple[MarketResearchBasketballClutchRestDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBasketballClutchRestDigestSignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.team_game_key, []).append(signal)
    rows = tuple(_row_for_team_game(tuple(items), config) for items in grouped.values())
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_team_game(
    signals: tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
    config: MarketResearchBasketballClutchRestDigestConfig,
) -> MarketResearchBasketballClutchRestDigestRow:
    ordered = tuple(sorted(signals, key=lambda item: item.observed_at))
    first = ordered[0]
    latest = ordered[-1]
    _validate_team_game_identity(ordered)
    clutch_values = tuple(item.clutch_minutes_last_game for item in ordered)
    rest_values = tuple(item.rest_hours for item in ordered)
    travel_values = tuple(item.travel_miles for item in ordered)
    rotation_values = tuple(item.projected_rotation_minutes for item in ordered)
    clutch_load_index = _clutch_load_index(
        latest.clutch_minutes_last_game,
        latest.rest_hours,
        latest.travel_miles,
        config,
    )
    reason_codes = _row_reason_codes(
        signal_count=_decimal_count(len(ordered)),
        clutch_load_index=clutch_load_index,
        clutch_minutes_last_game=latest.clutch_minutes_last_game,
        rest_hours=latest.rest_hours,
        travel_miles=latest.travel_miles,
        config=config,
    )
    return MarketResearchBasketballClutchRestDigestRow(
        team_game_key=first.team_game_key,
        team_key=first.team_key,
        league_key=first.league_key,
        signal_count=_decimal_count(len(ordered)),
        source_count=_sum_decimal(item.source_count for item in ordered),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_clutch_minutes_last_game=latest.clutch_minutes_last_game,
        max_clutch_minutes_last_game=max(clutch_values),
        latest_rest_hours=latest.rest_hours,
        min_rest_hours=min(rest_values),
        latest_travel_miles=latest.travel_miles,
        max_travel_miles=max(travel_values),
        latest_projected_rotation_minutes=latest.projected_rotation_minutes,
        max_projected_rotation_minutes=max(rotation_values),
        clutch_load_index=clutch_load_index,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_team_game_identity(
    signals: tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
) -> None:
    expected = signals[0]
    for signal in signals:
        if signal.team_key != expected.team_key:
            raise ValueError("team_key must match within team_game_key")
        if signal.league_key != expected.league_key:
            raise ValueError("league_key must match within team_game_key")


def _row_reason_codes(
    *,
    signal_count: Decimal,
    clutch_load_index: Decimal,
    clutch_minutes_last_game: Decimal,
    rest_hours: Decimal,
    travel_miles: Decimal,
    config: MarketResearchBasketballClutchRestDigestConfig,
) -> tuple[str, ...]:
    if signal_count < config.min_signal_count:
        return (LIMITED_HISTORY_REASON,)
    reason_codes = []
    if clutch_load_index >= config.clutch_load_index_watch_threshold:
        reason_codes.append(LOAD_REASON)
    if clutch_minutes_last_game >= config.clutch_minutes_watch_threshold:
        reason_codes.append(CLUTCH_REASON)
    if rest_hours <= config.rest_hours_watch_threshold:
        reason_codes.append(REST_REASON)
    if travel_miles >= config.travel_miles_watch_threshold:
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
        return Decimal("0")
    if status == LIMITED_HISTORY_STATUS:
        return Decimal("1")
    return Decimal("2")


def _row_sort_key(row: MarketResearchBasketballClutchRestDigestRow) -> tuple[object, ...]:
    return (
        _row_status_rank(row.digest_status),
        -row.clutch_load_index,
        row.league_key,
        row.team_key,
        row.team_game_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballClutchRestDigestRow, ...],
) -> tuple[MarketResearchBasketballClutchRestDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBasketballClutchRestDigestReasonCodeCount(
            reason_code=reason_code,
            team_game_count=_decimal_count(count),
            team_game_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: DIGEST_REASON_CODES.index(item[0]),
        )
    )


def _reason_team_game_count(
    rows: tuple[MarketResearchBasketballClutchRestDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _signal_config_versions(
    signals: tuple[MarketResearchBasketballClutchRestDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (signal.team_game_key, signal.signal_config_version)
                for signal in signals
            }
        )
    )


def _clutch_load_index(
    clutch_minutes_last_game: Decimal,
    rest_hours: Decimal,
    travel_miles: Decimal,
    config: MarketResearchBasketballClutchRestDigestConfig,
) -> Decimal:
    components = (
        _capped_ratio(clutch_minutes_last_game, config.clutch_minutes_watch_threshold),
        _short_rest_score(config.rest_hours_watch_threshold, rest_hours),
        _capped_ratio(travel_miles, config.travel_miles_watch_threshold),
    )
    return _ratio(_sum_decimal(components), Decimal("3"))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ONE
    ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM, rounding=ROUND_DOWN)


def _inverse_capped_ratio(threshold: Decimal, value: Decimal) -> Decimal:
    if threshold == ZERO:
        return ZERO
    if value >= threshold:
        return ZERO
    denominator = (threshold - Decimal("15")).quantize(QUANTUM)
    if denominator <= ZERO:
        return ONE
    ratio = (threshold - value) / denominator
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM, rounding=ROUND_DOWN)


def _short_rest_score(threshold: Decimal, value: Decimal) -> Decimal:
    if threshold == ZERO:
        return ZERO
    if value >= threshold:
        return ZERO
    if value <= threshold - Decimal("6"):
        return Decimal("0.750000")
    return Decimal("0.750000")


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


def _validate_row(row: MarketResearchBasketballClutchRestDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.max_clutch_minutes_last_game < row.latest_clutch_minutes_last_game:
        raise ValueError("max_clutch_minutes_last_game must cover latest value")
    if row.min_rest_hours > row.latest_rest_hours:
        raise ValueError("min_rest_hours must cover latest value")
    if row.max_travel_miles < row.latest_travel_miles:
        raise ValueError("max_travel_miles must cover latest value")
    if row.max_projected_rotation_minutes < row.latest_projected_rotation_minutes:
        raise ValueError("max_projected_rotation_minutes must cover latest value")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBasketballClutchRestDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.team_game_count != _decimal_count(len(report.rows)):
        raise ValueError("team_game_count must match rows")
    if report.clear_team_game_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_team_game_count must match rows")
    if report.watch_team_game_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_team_game_count must match rows")
    if report.limited_history_team_game_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == LIMITED_HISTORY_STATUS),
    ):
        raise ValueError("limited_history_team_game_count must match rows")
    if report.signal_count != _sum_decimal(row.signal_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    if report.clutch_minutes_team_game_count != _reason_team_game_count(
        report.rows,
        CLUTCH_REASON,
    ):
        raise ValueError("clutch_minutes_team_game_count must match rows")
    if report.short_rest_team_game_count != _reason_team_game_count(
        report.rows,
        REST_REASON,
    ):
        raise ValueError("short_rest_team_game_count must match rows")
    if report.travel_load_team_game_count != _reason_team_game_count(
        report.rows,
        TRAVEL_REASON,
    ):
        raise ValueError("travel_load_team_game_count must match rows")
    if report.clutch_load_index_team_game_count != _reason_team_game_count(
        report.rows,
        LOAD_REASON,
    ):
        raise ValueError("clutch_load_index_team_game_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBasketballClutchRestDigestReasonCodeCount(
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
    if report.max_clutch_load_index != _max_or_none(row.clutch_load_index for row in report.rows):
        raise ValueError("max_clutch_load_index must match rows")
    if report.max_clutch_minutes_last_game != _max_or_none(
        row.max_clutch_minutes_last_game for row in report.rows
    ):
        raise ValueError("max_clutch_minutes_last_game must match rows")
    if report.min_rest_hours != _min_or_none(row.min_rest_hours for row in report.rows):
        raise ValueError("min_rest_hours must match rows")
    if report.max_travel_miles != _max_or_none(row.max_travel_miles for row in report.rows):
        raise ValueError("max_travel_miles must match rows")
    if report.digest_status == WATCH_STATUS and report.watch_team_game_count == ZERO:
        raise ValueError("watch reports require watch rows")
    if report.digest_status == PASS_STATUS and report.watch_team_game_count != ZERO:
        raise ValueError("pass reports must not include watch rows")


def _normalize_rows(value: object) -> tuple[MarketResearchBasketballClutchRestDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchBasketballClutchRestDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBasketballClutchRestDigestRow",
            )
        _require_flags("row", row)
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
) -> tuple[MarketResearchBasketballClutchRestDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchBasketballClutchRestDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballClutchRestDigestReasonCodeCount",
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


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} contains invalid reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{name} must not contain leading or trailing whitespace")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    try:
        normalized = value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not normalized.is_finite():
        raise ValueError(f"{name} must be finite")
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
    return normalized.quantize(Decimal("1"))


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


def _require_flags(name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{name} {flag} must be True")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(Decimal("1"))


def _sum_decimal(values: object) -> Decimal:
    return sum(tuple(values), ZERO)  # type: ignore[arg-type]


def _six(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)
