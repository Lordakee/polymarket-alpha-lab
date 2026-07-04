"""Pure in-memory reducer for baseball doubleheader fatigue reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASEBALL_DOUBLEHEADER_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-doubleheader-fatigue-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
FATIGUED_STATUS = "fatigued"
LIMITED_HISTORY_STATUS = "limited_history"

BULLPEN_REASON = "baseball_doubleheader_fatigue_bullpen_load_high"
DOUBLEHEADER_REASON = "baseball_doubleheader_fatigue_doubleheader_spot"
REST_REASON = "baseball_doubleheader_fatigue_rest_short"
TRAVEL_REASON = "baseball_doubleheader_fatigue_travel_high"
CLEAR_REASON = "baseball_doubleheader_fatigue_clear"
LIMITED_HISTORY_REASON = "baseball_doubleheader_fatigue_limited_history"
PASSED_REASON = "baseball_doubleheader_fatigue_passed"
EMPTY_REASON = "baseball_doubleheader_fatigue_empty"

ROW_REASON_CODES = (
    BULLPEN_REASON,
    DOUBLEHEADER_REASON,
    REST_REASON,
    TRAVEL_REASON,
    LIMITED_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    BULLPEN_REASON,
    DOUBLEHEADER_REASON,
    REST_REASON,
    TRAVEL_REASON,
    LIMITED_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_baseball_doubleheader_fatigue_digest",
    WATCH_STATUS: "review_report_only_baseball_doubleheader_fatigue_digest",
}

ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_DOUBLEHEADER_FATIGUE_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballDoubleheaderFatigueDigestConfig",
    "MarketResearchBaseballDoubleheaderFatigueDigestSnapshot",
    "MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount",
    "MarketResearchBaseballDoubleheaderFatigueDigestRow",
    "MarketResearchBaseballDoubleheaderFatigueDigestReport",
    "build_market_research_baseball_doubleheader_fatigue_digest",
    "market_research_baseball_doubleheader_fatigue_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBaseballDoubleheaderFatigueDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_DOUBLEHEADER_FATIGUE_DIGEST_CONFIG_VERSION
    )
    fatigue_index_watch_threshold: Decimal = Decimal("0.650000")
    doubleheader_game_watch_threshold: Decimal = Decimal("1")
    rest_hour_watch_threshold: Decimal = Decimal("20")
    travel_mile_watch_threshold: Decimal = Decimal("500")
    projected_bullpen_inning_watch_threshold: Decimal = Decimal("4")
    min_snapshot_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fatigue_index_watch_threshold",
            _normalize_ratio_decimal(
                "fatigue_index_watch_threshold",
                self.fatigue_index_watch_threshold,
            ),
        )
        for field_name in (
            "doubleheader_game_watch_threshold",
            "min_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hour_watch_threshold",
            "travel_mile_watch_threshold",
            "projected_bullpen_inning_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballDoubleheaderFatigueDigestSnapshot(_NoSubclass):
    team_schedule_key: str
    team_key: str
    league_key: str
    observed_at: datetime
    doubleheader_game_count: Decimal
    rest_hours: Decimal
    travel_miles: Decimal
    projected_bullpen_innings: Decimal
    source_count: Decimal
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_DOUBLEHEADER_FATIGUE_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_schedule_key",
            "team_key",
            "league_key",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("doubleheader_game_count", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rest_hours",
            "travel_miles",
            "projected_bullpen_innings",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    team_schedule_count: Decimal
    team_schedule_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "team_schedule_count",
            _normalize_nonnegative_whole_decimal(
                "team_schedule_count",
                self.team_schedule_count,
            ),
        )
        object.__setattr__(
            self,
            "team_schedule_ratio",
            _normalize_ratio_decimal("team_schedule_ratio", self.team_schedule_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBaseballDoubleheaderFatigueDigestRow(_NoSubclass):
    team_schedule_key: str
    team_key: str
    league_key: str
    snapshot_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_doubleheader_game_count: Decimal
    max_doubleheader_game_count: Decimal
    latest_rest_hours: Decimal
    min_rest_hours: Decimal
    latest_travel_miles: Decimal
    max_travel_miles: Decimal
    latest_projected_bullpen_innings: Decimal
    max_projected_bullpen_innings: Decimal
    fatigue_index: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_schedule_key", "team_key", "league_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "snapshot_count",
            "source_count",
            "latest_doubleheader_game_count",
            "max_doubleheader_game_count",
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
            "latest_rest_hours",
            "min_rest_hours",
            "latest_travel_miles",
            "max_travel_miles",
            "latest_projected_bullpen_innings",
            "max_projected_bullpen_innings",
            "fatigue_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "digest_status",
            self.digest_status,
            (CLEAR_STATUS, FATIGUED_STATUS, LIMITED_HISTORY_STATUS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballDoubleheaderFatigueDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    team_schedule_count: Decimal
    clear_team_schedule_count: Decimal
    fatigued_team_schedule_count: Decimal
    limited_history_team_schedule_count: Decimal
    snapshot_count: Decimal
    doubleheader_team_schedule_count: Decimal
    short_rest_team_schedule_count: Decimal
    travel_fatigue_team_schedule_count: Decimal
    bullpen_load_team_schedule_count: Decimal
    fatigue_index_watch_threshold: Decimal
    doubleheader_game_watch_threshold: Decimal
    rest_hour_watch_threshold: Decimal
    travel_mile_watch_threshold: Decimal
    projected_bullpen_inning_watch_threshold: Decimal
    min_snapshot_count: Decimal
    max_fatigue_index: Decimal | None
    min_rest_hours: Decimal | None
    max_travel_miles: Decimal | None
    max_projected_bullpen_innings: Decimal | None
    rows: tuple[MarketResearchBaseballDoubleheaderFatigueDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "team_schedule_count",
            "clear_team_schedule_count",
            "fatigued_team_schedule_count",
            "limited_history_team_schedule_count",
            "snapshot_count",
            "doubleheader_team_schedule_count",
            "short_rest_team_schedule_count",
            "travel_fatigue_team_schedule_count",
            "bullpen_load_team_schedule_count",
            "doubleheader_game_watch_threshold",
            "min_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fatigue_index_watch_threshold",
            "rest_hour_watch_threshold",
            "travel_mile_watch_threshold",
            "projected_bullpen_inning_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal(
            "fatigue_index_watch_threshold",
            self.fatigue_index_watch_threshold,
        )
        for field_name in (
            "max_fatigue_index",
            "min_rest_hours",
            "max_travel_miles",
            "max_projected_bullpen_innings",
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


def build_market_research_baseball_doubleheader_fatigue_digest(
    snapshots: list[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot]
    | tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
    *,
    config: MarketResearchBaseballDoubleheaderFatigueDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballDoubleheaderFatigueDigestReport:
    if type(config) is not MarketResearchBaseballDoubleheaderFatigueDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBaseballDoubleheaderFatigueDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_snapshots(snapshots)
    _reject_future_snapshots(normalized, generated_at_utc)
    rows = _rows(normalized, config)
    team_schedule_count = _decimal_count(len(rows))
    fatigued_count = _decimal_count(
        sum(1 for row in rows if row.digest_status == FATIGUED_STATUS),
    )
    digest_status = WATCH_STATUS if fatigued_count > ZERO else PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                team_schedule_count=ONE,
                team_schedule_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = tuple((*reason_codes, PASSED_REASON))

    return MarketResearchBaseballDoubleheaderFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        team_schedule_count=team_schedule_count,
        clear_team_schedule_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        fatigued_team_schedule_count=fatigued_count,
        limited_history_team_schedule_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == LIMITED_HISTORY_STATUS),
        ),
        snapshot_count=_decimal_count(len(normalized)),
        doubleheader_team_schedule_count=_reason_team_schedule_count(
            rows,
            DOUBLEHEADER_REASON,
        ),
        short_rest_team_schedule_count=_reason_team_schedule_count(rows, REST_REASON),
        travel_fatigue_team_schedule_count=_reason_team_schedule_count(
            rows,
            TRAVEL_REASON,
        ),
        bullpen_load_team_schedule_count=_reason_team_schedule_count(
            rows,
            BULLPEN_REASON,
        ),
        fatigue_index_watch_threshold=config.fatigue_index_watch_threshold,
        doubleheader_game_watch_threshold=config.doubleheader_game_watch_threshold,
        rest_hour_watch_threshold=config.rest_hour_watch_threshold,
        travel_mile_watch_threshold=config.travel_mile_watch_threshold,
        projected_bullpen_inning_watch_threshold=(
            config.projected_bullpen_inning_watch_threshold
        ),
        min_snapshot_count=config.min_snapshot_count,
        max_fatigue_index=_max_or_none(row.fatigue_index for row in rows),
        min_rest_hours=_min_or_none(row.min_rest_hours for row in rows),
        max_travel_miles=_max_or_none(row.max_travel_miles for row in rows),
        max_projected_bullpen_innings=_max_or_none(
            row.max_projected_bullpen_innings for row in rows
        ),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_baseball_doubleheader_fatigue_digest_payload(
    report: MarketResearchBaseballDoubleheaderFatigueDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBaseballDoubleheaderFatigueDigestReport:
        raise ValueError(
            "report must be a MarketResearchBaseballDoubleheaderFatigueDigestReport",
        )
    _require_flags("report", report)
    return _payload_value(asdict(report))  # type: ignore[return-value]


def _normalize_snapshots(
    snapshots: list[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot]
    | tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
) -> tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    normalized = tuple(snapshots)
    seen: set[tuple[str, datetime]] = set()
    for snapshot in normalized:
        if type(snapshot) is not MarketResearchBaseballDoubleheaderFatigueDigestSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchBaseballDoubleheaderFatigueDigestSnapshot",
            )
        _require_flags("snapshot", snapshot)
        key = (snapshot.team_schedule_key, snapshot.observed_at)
        if key in seen:
            raise ValueError(
                "snapshots must not contain duplicate team schedule observations",
            )
        seen.add(key)
    return normalized


def _reject_future_snapshots(
    snapshots: tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    snapshots: tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
    config: MarketResearchBaseballDoubleheaderFatigueDigestConfig,
) -> tuple[MarketResearchBaseballDoubleheaderFatigueDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.team_schedule_key, []).append(snapshot)
    rows = tuple(_row_for_team_schedule(tuple(items), config) for items in grouped.values())
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_status_rank(row.digest_status),
                -row.fatigue_index,
                row.league_key,
                row.team_key,
                row.team_schedule_key,
            ),
        )
    )


def _row_for_team_schedule(
    snapshots: tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
    config: MarketResearchBaseballDoubleheaderFatigueDigestConfig,
) -> MarketResearchBaseballDoubleheaderFatigueDigestRow:
    ordered = tuple(sorted(snapshots, key=lambda item: item.observed_at))
    first = ordered[0]
    latest = ordered[-1]
    _validate_team_schedule_identity(ordered)
    doubleheader_values = tuple(item.doubleheader_game_count for item in ordered)
    rest_values = tuple(item.rest_hours for item in ordered)
    travel_values = tuple(item.travel_miles for item in ordered)
    bullpen_values = tuple(item.projected_bullpen_innings for item in ordered)
    fatigue_index = _fatigue_index(
        latest.doubleheader_game_count,
        latest.rest_hours,
        latest.travel_miles,
        latest.projected_bullpen_innings,
        config,
    )
    reason_codes = _row_reason_codes(
        snapshot_count=_decimal_count(len(ordered)),
        fatigue_index=fatigue_index,
        doubleheader_game_count=latest.doubleheader_game_count,
        rest_hours=latest.rest_hours,
        travel_miles=latest.travel_miles,
        projected_bullpen_innings=latest.projected_bullpen_innings,
        config=config,
    )
    return MarketResearchBaseballDoubleheaderFatigueDigestRow(
        team_schedule_key=first.team_schedule_key,
        team_key=first.team_key,
        league_key=first.league_key,
        snapshot_count=_decimal_count(len(ordered)),
        source_count=_sum_decimal(item.source_count for item in ordered),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_doubleheader_game_count=latest.doubleheader_game_count,
        max_doubleheader_game_count=max(doubleheader_values),
        latest_rest_hours=latest.rest_hours,
        min_rest_hours=min(rest_values),
        latest_travel_miles=latest.travel_miles,
        max_travel_miles=max(travel_values),
        latest_projected_bullpen_innings=latest.projected_bullpen_innings,
        max_projected_bullpen_innings=max(bullpen_values),
        fatigue_index=fatigue_index,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_team_schedule_identity(
    snapshots: tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
) -> None:
    expected = snapshots[0]
    for snapshot in snapshots:
        if snapshot.team_key != expected.team_key:
            raise ValueError("team_key must match within team_schedule_key")
        if snapshot.league_key != expected.league_key:
            raise ValueError("league_key must match within team_schedule_key")


def _row_reason_codes(
    *,
    snapshot_count: Decimal,
    fatigue_index: Decimal,
    doubleheader_game_count: Decimal,
    rest_hours: Decimal,
    travel_miles: Decimal,
    projected_bullpen_innings: Decimal,
    config: MarketResearchBaseballDoubleheaderFatigueDigestConfig,
) -> tuple[str, ...]:
    if snapshot_count < config.min_snapshot_count:
        return (LIMITED_HISTORY_REASON,)
    reason_codes = []
    if doubleheader_game_count >= config.doubleheader_game_watch_threshold:
        reason_codes.append(DOUBLEHEADER_REASON)
    if rest_hours <= config.rest_hour_watch_threshold:
        reason_codes.append(REST_REASON)
    if travel_miles >= config.travel_mile_watch_threshold:
        reason_codes.append(TRAVEL_REASON)
    if projected_bullpen_innings >= config.projected_bullpen_inning_watch_threshold:
        reason_codes.append(BULLPEN_REASON)
    if fatigue_index >= config.fatigue_index_watch_threshold:
        for reason_code in (
            BULLPEN_REASON,
            DOUBLEHEADER_REASON,
            REST_REASON,
            TRAVEL_REASON,
        ):
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    if reason_codes == (LIMITED_HISTORY_REASON,):
        return LIMITED_HISTORY_STATUS
    return FATIGUED_STATUS


def _row_status_rank(status: str) -> Decimal:
    if status == FATIGUED_STATUS:
        return Decimal("0")
    if status == LIMITED_HISTORY_STATUS:
        return Decimal("1")
    return Decimal("2")


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballDoubleheaderFatigueDigestRow, ...],
) -> tuple[MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount(
            reason_code=reason_code,
            team_schedule_count=_decimal_count(count),
            team_schedule_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _reason_team_schedule_count(
    rows: tuple[MarketResearchBaseballDoubleheaderFatigueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    snapshots: tuple[MarketResearchBaseballDoubleheaderFatigueDigestSnapshot, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (snapshot.team_schedule_key, snapshot.source_config_version)
                for snapshot in snapshots
            }
        )
    )


def _fatigue_index(
    doubleheader_game_count: Decimal,
    rest_hours: Decimal,
    travel_miles: Decimal,
    projected_bullpen_innings: Decimal,
    config: MarketResearchBaseballDoubleheaderFatigueDigestConfig,
) -> Decimal:
    components = (
        _capped_ratio(doubleheader_game_count, config.doubleheader_game_watch_threshold),
        _inverse_capped_ratio(config.rest_hour_watch_threshold, rest_hours),
        _capped_ratio(travel_miles, config.travel_mile_watch_threshold),
        _capped_ratio(
            projected_bullpen_innings,
            config.projected_bullpen_inning_watch_threshold,
        ),
    )
    return _ratio(_sum_decimal(components), Decimal("4"))


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


def _validate_row(row: MarketResearchBaseballDoubleheaderFatigueDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.max_doubleheader_game_count < row.latest_doubleheader_game_count:
        raise ValueError("max_doubleheader_game_count must cover latest value")
    if row.min_rest_hours > row.latest_rest_hours:
        raise ValueError("min_rest_hours must cover latest value")
    if row.max_travel_miles < row.latest_travel_miles:
        raise ValueError("max_travel_miles must cover latest value")
    if row.max_projected_bullpen_innings < row.latest_projected_bullpen_innings:
        raise ValueError("max_projected_bullpen_innings must cover latest value")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBaseballDoubleheaderFatigueDigestReport) -> None:
    if report.team_schedule_count != _decimal_count(len(report.rows)):
        raise ValueError("team_schedule_count must match rows")
    if report.clear_team_schedule_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_team_schedule_count must match rows")
    if report.fatigued_team_schedule_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == FATIGUED_STATUS),
    ):
        raise ValueError("fatigued_team_schedule_count must match rows")
    if report.limited_history_team_schedule_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == LIMITED_HISTORY_STATUS),
    ):
        raise ValueError("limited_history_team_schedule_count must match rows")
    if report.snapshot_count != _sum_decimal(row.snapshot_count for row in report.rows):
        raise ValueError("snapshot_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                team_schedule_count=ONE,
                team_schedule_ratio=ZERO,
            ),
        )
        expected_reason_codes = (EMPTY_REASON,)
    elif report.fatigued_team_schedule_count == ZERO:
        expected_reason_codes = tuple((*expected_reason_codes, PASSED_REASON))
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = WATCH_STATUS if report.fatigued_team_schedule_count > ZERO else PASS_STATUS
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.doubleheader_team_schedule_count != _reason_team_schedule_count(
        report.rows,
        DOUBLEHEADER_REASON,
    ):
        raise ValueError("doubleheader_team_schedule_count must match rows")
    if report.short_rest_team_schedule_count != _reason_team_schedule_count(
        report.rows,
        REST_REASON,
    ):
        raise ValueError("short_rest_team_schedule_count must match rows")
    if report.travel_fatigue_team_schedule_count != _reason_team_schedule_count(
        report.rows,
        TRAVEL_REASON,
    ):
        raise ValueError("travel_fatigue_team_schedule_count must match rows")
    if report.bullpen_load_team_schedule_count != _reason_team_schedule_count(
        report.rows,
        BULLPEN_REASON,
    ):
        raise ValueError("bullpen_load_team_schedule_count must match rows")
    if report.max_fatigue_index != _max_or_none(row.fatigue_index for row in report.rows):
        raise ValueError("max_fatigue_index must match rows")
    if report.min_rest_hours != _min_or_none(row.min_rest_hours for row in report.rows):
        raise ValueError("min_rest_hours must match rows")
    if report.max_travel_miles != _max_or_none(row.max_travel_miles for row in report.rows):
        raise ValueError("max_travel_miles must match rows")
    if report.max_projected_bullpen_innings != _max_or_none(
        row.max_projected_bullpen_innings for row in report.rows
    ):
        raise ValueError("max_projected_bullpen_innings must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchBaseballDoubleheaderFatigueDigestRow, ...],
) -> tuple[MarketResearchBaseballDoubleheaderFatigueDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballDoubleheaderFatigueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballDoubleheaderFatigueDigestRow",
            )
        _require_flags("row", row)
        if row.team_schedule_key in seen:
            raise ValueError("rows must contain unique team_schedule_key values")
        seen.add(row.team_schedule_key)
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
        team_schedule_key, source_config_version = value
        _require_canonical_string("team_schedule_key", team_schedule_key)
        _require_canonical_string("source_config_version", source_config_version)
        normalized.append((team_schedule_key, source_config_version))
    sorted_values = tuple(sorted(normalized))
    if sorted_values != values:
        raise ValueError("source_config_versions must be sorted")
    if len(set(sorted_values)) != len(sorted_values):
        raise ValueError("source_config_versions must be unique")
    return values


def _normalize_reason_code_counts(
    values: tuple[MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballDoubleheaderFatigueDigestReasonCodeCount",
            )
        _require_flags("reason_code_count", value)
    sorted_values = tuple(sorted(values, key=lambda item: item.reason_code))
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
    if tuple(sorted(values)) != values:
        raise ValueError(f"{field_name} must be sorted")
    return values


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
        return str(value.quantize(Decimal("1")) if value == value.to_integral_value() else value)
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(item_key): _payload_value(item_value)
            for item_key, item_value in value.items()
        }
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains a non-Decimal numeric value")
