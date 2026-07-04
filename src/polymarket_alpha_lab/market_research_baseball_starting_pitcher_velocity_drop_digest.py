"""Pure in-memory reducer for baseball starting pitcher velocity drop reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_VELOCITY_DROP_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-starting-pitcher-velocity-drop-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"

SEVERE_DROP_REASON = "baseball_starting_pitcher_velocity_drop_severe_drop"
WATCH_DROP_REASON = "baseball_starting_pitcher_velocity_drop_watch_drop"
LOW_RECENT_VELOCITY_REASON = (
    "baseball_starting_pitcher_velocity_drop_low_recent_velocity"
)
LATE_WINDOW_REASON = "baseball_starting_pitcher_velocity_drop_late_window"
THIN_SOURCES_REASON = "baseball_starting_pitcher_velocity_drop_thin_sources"
CLEAR_REASON = "baseball_starting_pitcher_velocity_drop_clear"
PASSED_REASON = "baseball_starting_pitcher_velocity_drop_passed"
EMPTY_REASON = "baseball_starting_pitcher_velocity_drop_empty"

ROW_REASON_CODES = (
    LATE_WINDOW_REASON,
    LOW_RECENT_VELOCITY_REASON,
    SEVERE_DROP_REASON,
    THIN_SOURCES_REASON,
    WATCH_DROP_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    LATE_WINDOW_REASON,
    LOW_RECENT_VELOCITY_REASON,
    SEVERE_DROP_REASON,
    THIN_SOURCES_REASON,
    WATCH_DROP_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_baseball_starting_pitcher_velocity_drop_digest",
    WATCH_STATUS: "review_report_only_baseball_starting_pitcher_velocity_drop_digest",
}

ZERO = Decimal("0")
ONE = Decimal("1")
SIXTY = Decimal("60")
MICROSECONDS_PER_SECOND = Decimal("1000000")
QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_VELOCITY_DROP_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballStartingPitcherVelocityDropDigestConfig",
    "MarketResearchBaseballStartingPitcherVelocityDropObservation",
    "MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount",
    "MarketResearchBaseballStartingPitcherVelocityDropDigestRow",
    "MarketResearchBaseballStartingPitcherVelocityDropDigestReport",
    "build_market_research_baseball_starting_pitcher_velocity_drop_digest",
    "market_research_baseball_starting_pitcher_velocity_drop_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherVelocityDropDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_VELOCITY_DROP_DIGEST_CONFIG_VERSION
    )
    velocity_drop_watch_threshold: Decimal = Decimal("1.500000")
    severe_velocity_drop_watch_threshold: Decimal = Decimal("2.500000")
    low_latest_velocity_threshold: Decimal = Decimal("91.000000")
    late_window_minutes: Decimal = Decimal("45.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "velocity_drop_watch_threshold",
            "severe_velocity_drop_watch_threshold",
            "low_latest_velocity_threshold",
            "late_window_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_whole_decimal("min_source_count", self.min_source_count),
        )
        _validate_config(self)
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherVelocityDropObservation(_NoSubclass):
    pitcher_key: str
    pitcher_name: str
    team_key: str
    game_key: str
    observed_at: datetime
    scheduled_start_at: datetime
    baseline_fastball_velocity_mph: Decimal
    latest_fastball_velocity_mph: Decimal
    source_count: Decimal
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_VELOCITY_DROP_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "pitcher_key",
            "pitcher_name",
            "team_key",
            "game_key",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        for field_name in (
            "baseline_fastball_velocity_mph",
            "latest_fastball_velocity_mph",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        _validate_observation(self)
        _require_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(_NoSubclass):
    reason_code: str
    pitcher_count: Decimal
    pitcher_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "pitcher_count",
            _normalize_nonnegative_whole_decimal("pitcher_count", self.pitcher_count),
        )
        object.__setattr__(
            self,
            "pitcher_ratio",
            _normalize_ratio_decimal("pitcher_ratio", self.pitcher_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherVelocityDropDigestRow(_NoSubclass):
    pitcher_key: str
    pitcher_name: str
    team_key: str
    game_key: str
    observed_at: datetime
    scheduled_start_at: datetime
    minutes_until_start: Decimal
    baseline_fastball_velocity_mph: Decimal
    latest_fastball_velocity_mph: Decimal
    velocity_drop_mph: Decimal
    source_count: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("pitcher_key", "pitcher_name", "team_key", "game_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        for field_name in (
            "minutes_until_start",
            "baseline_fastball_velocity_mph",
            "latest_fastball_velocity_mph",
            "velocity_drop_mph",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        _require_member("digest_status", self.digest_status, (CLEAR_STATUS, WATCH_STATUS))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherVelocityDropDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    pitcher_count: Decimal
    clear_pitcher_count: Decimal
    watch_pitcher_count: Decimal
    velocity_drop_pitcher_count: Decimal
    severe_velocity_drop_pitcher_count: Decimal
    low_recent_velocity_pitcher_count: Decimal
    late_observation_pitcher_count: Decimal
    thin_source_pitcher_count: Decimal
    velocity_drop_watch_threshold: Decimal
    severe_velocity_drop_watch_threshold: Decimal
    low_latest_velocity_threshold: Decimal
    late_window_minutes: Decimal
    min_source_count: Decimal
    max_velocity_drop_mph: Decimal | None
    rows: tuple[MarketResearchBaseballStartingPitcherVelocityDropDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount,
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
            "pitcher_count",
            "clear_pitcher_count",
            "watch_pitcher_count",
            "velocity_drop_pitcher_count",
            "severe_velocity_drop_pitcher_count",
            "low_recent_velocity_pitcher_count",
            "late_observation_pitcher_count",
            "thin_source_pitcher_count",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "velocity_drop_watch_threshold",
            "severe_velocity_drop_watch_threshold",
            "low_latest_velocity_threshold",
            "late_window_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_velocity_drop_mph is not None:
            object.__setattr__(
                self,
                "max_velocity_drop_mph",
                _normalize_nonnegative_decimal(
                    "max_velocity_drop_mph",
                    self.max_velocity_drop_mph,
                ),
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


def build_market_research_baseball_starting_pitcher_velocity_drop_digest(
    observations: list[MarketResearchBaseballStartingPitcherVelocityDropObservation]
    | tuple[MarketResearchBaseballStartingPitcherVelocityDropObservation, ...],
    *,
    config: MarketResearchBaseballStartingPitcherVelocityDropDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballStartingPitcherVelocityDropDigestReport:
    if type(config) is not MarketResearchBaseballStartingPitcherVelocityDropDigestConfig:
        raise ValueError(
            "config must be a "
            "MarketResearchBaseballStartingPitcherVelocityDropDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_future_observations(normalized, generated_at_utc)
    rows = _rows(normalized, config, generated_at_utc)
    pitcher_count = _decimal_count(len(rows))
    watch_count = _decimal_count(sum(1 for row in rows if row.digest_status == WATCH_STATUS))
    digest_status = WATCH_STATUS if watch_count > ZERO else PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
                reason_code=EMPTY_REASON,
                pitcher_count=ONE,
                pitcher_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = (PASSED_REASON,)

    return MarketResearchBaseballStartingPitcherVelocityDropDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        pitcher_count=pitcher_count,
        clear_pitcher_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_pitcher_count=watch_count,
        velocity_drop_pitcher_count=_decimal_count(
            sum(
                1
                for row in rows
                if SEVERE_DROP_REASON in row.reason_codes
                or WATCH_DROP_REASON in row.reason_codes
            ),
        ),
        severe_velocity_drop_pitcher_count=_reason_pitcher_count(
            rows,
            SEVERE_DROP_REASON,
        ),
        low_recent_velocity_pitcher_count=_reason_pitcher_count(
            rows,
            LOW_RECENT_VELOCITY_REASON,
        ),
        late_observation_pitcher_count=_reason_pitcher_count(rows, LATE_WINDOW_REASON),
        thin_source_pitcher_count=_reason_pitcher_count(rows, THIN_SOURCES_REASON),
        velocity_drop_watch_threshold=config.velocity_drop_watch_threshold,
        severe_velocity_drop_watch_threshold=config.severe_velocity_drop_watch_threshold,
        low_latest_velocity_threshold=config.low_latest_velocity_threshold,
        late_window_minutes=config.late_window_minutes,
        min_source_count=config.min_source_count,
        max_velocity_drop_mph=_max_or_none(row.velocity_drop_mph for row in rows),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_baseball_starting_pitcher_velocity_drop_digest_payload(
    report: MarketResearchBaseballStartingPitcherVelocityDropDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBaseballStartingPitcherVelocityDropDigestReport:
        raise ValueError(
            "report must be a "
            "MarketResearchBaseballStartingPitcherVelocityDropDigestReport",
        )
    _require_flags("report", report)
    return _payload_value(asdict(report))  # type: ignore[return-value]


def _normalize_observations(
    observations: list[MarketResearchBaseballStartingPitcherVelocityDropObservation]
    | tuple[MarketResearchBaseballStartingPitcherVelocityDropObservation, ...],
) -> tuple[MarketResearchBaseballStartingPitcherVelocityDropObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not MarketResearchBaseballStartingPitcherVelocityDropObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchBaseballStartingPitcherVelocityDropObservation",
            )
        _require_flags("observation", item)
        key = (item.pitcher_key, item.game_key)
        if key in seen:
            raise ValueError("observations must not contain duplicate pitcher game values")
        seen.add(key)
    return normalized


def _reject_future_observations(
    observations: tuple[MarketResearchBaseballStartingPitcherVelocityDropObservation, ...],
    generated_at: datetime,
) -> None:
    for item in observations:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    observations: tuple[MarketResearchBaseballStartingPitcherVelocityDropObservation, ...],
    config: MarketResearchBaseballStartingPitcherVelocityDropDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballStartingPitcherVelocityDropDigestRow, ...]:
    rows = tuple(_row_for_observation(item, config, generated_at) for item in observations)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_status_rank(row.digest_status),
                -row.velocity_drop_mph,
                row.pitcher_key,
                row.team_key,
                row.game_key,
            ),
        )
    )


def _row_for_observation(
    item: MarketResearchBaseballStartingPitcherVelocityDropObservation,
    config: MarketResearchBaseballStartingPitcherVelocityDropDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballStartingPitcherVelocityDropDigestRow:
    minutes_until_start = _minutes_until_start(item.scheduled_start_at, generated_at)
    velocity_drop_mph = _velocity_drop(
        item.baseline_fastball_velocity_mph,
        item.latest_fastball_velocity_mph,
    )
    reason_codes = _row_reason_codes(
        velocity_drop_mph=velocity_drop_mph,
        latest_fastball_velocity_mph=item.latest_fastball_velocity_mph,
        source_count=item.source_count,
        minutes_until_start=minutes_until_start,
        config=config,
    )
    return MarketResearchBaseballStartingPitcherVelocityDropDigestRow(
        pitcher_key=item.pitcher_key,
        pitcher_name=item.pitcher_name,
        team_key=item.team_key,
        game_key=item.game_key,
        observed_at=item.observed_at,
        scheduled_start_at=item.scheduled_start_at,
        minutes_until_start=minutes_until_start,
        baseline_fastball_velocity_mph=item.baseline_fastball_velocity_mph,
        latest_fastball_velocity_mph=item.latest_fastball_velocity_mph,
        velocity_drop_mph=velocity_drop_mph,
        source_count=item.source_count,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    velocity_drop_mph: Decimal,
    latest_fastball_velocity_mph: Decimal,
    source_count: Decimal,
    minutes_until_start: Decimal,
    config: MarketResearchBaseballStartingPitcherVelocityDropDigestConfig,
) -> tuple[str, ...]:
    reason_codes = []
    if velocity_drop_mph >= config.severe_velocity_drop_watch_threshold:
        reason_codes.append(SEVERE_DROP_REASON)
    elif velocity_drop_mph >= config.velocity_drop_watch_threshold:
        reason_codes.append(WATCH_DROP_REASON)
    if latest_fastball_velocity_mph <= config.low_latest_velocity_threshold:
        reason_codes.append(LOW_RECENT_VELOCITY_REASON)
    if minutes_until_start <= config.late_window_minutes:
        reason_codes.append(LATE_WINDOW_REASON)
    if source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    return WATCH_STATUS


def _row_status_rank(status: str) -> int:
    if status == WATCH_STATUS:
        return 0
    return 1


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballStartingPitcherVelocityDropDigestRow, ...],
) -> tuple[MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
            reason_code=reason_code,
            pitcher_count=_decimal_count(count),
            pitcher_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _reason_pitcher_count(
    rows: tuple[MarketResearchBaseballStartingPitcherVelocityDropDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    observations: tuple[MarketResearchBaseballStartingPitcherVelocityDropObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (item.pitcher_key, item.source_config_version)
                for item in observations
            }
        )
    )


def _minutes_until_start(scheduled_start_at: datetime, generated_at: datetime) -> Decimal:
    seconds = _seconds_between(generated_at, scheduled_start_at)
    if seconds <= ZERO:
        return ZERO
    return _six(seconds / SIXTY)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return _six(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )


def _velocity_drop(baseline: Decimal, latest: Decimal) -> Decimal:
    if baseline <= latest:
        return ZERO
    return _six(baseline - latest)


def _max_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _six(max(normalized))


def _validate_config(
    config: MarketResearchBaseballStartingPitcherVelocityDropDigestConfig,
) -> None:
    if config.severe_velocity_drop_watch_threshold < config.velocity_drop_watch_threshold:
        raise ValueError(
            "severe_velocity_drop_watch_threshold must be at least "
            "velocity_drop_watch_threshold",
        )


def _validate_observation(
    item: MarketResearchBaseballStartingPitcherVelocityDropObservation,
) -> None:
    if item.scheduled_start_at < item.observed_at:
        raise ValueError("scheduled_start_at must not precede observed_at")


def _validate_row(row: MarketResearchBaseballStartingPitcherVelocityDropDigestRow) -> None:
    if row.scheduled_start_at < row.observed_at:
        raise ValueError("scheduled_start_at must not precede observed_at")
    expected_velocity_drop = _velocity_drop(
        row.baseline_fastball_velocity_mph,
        row.latest_fastball_velocity_mph,
    )
    if row.velocity_drop_mph != expected_velocity_drop:
        raise ValueError("velocity_drop_mph must match velocity values")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(
    report: MarketResearchBaseballStartingPitcherVelocityDropDigestReport,
) -> None:
    if report.pitcher_count != _decimal_count(len(report.rows)):
        raise ValueError("pitcher_count must match rows")
    if report.clear_pitcher_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_pitcher_count must match rows")
    if report.watch_pitcher_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_pitcher_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount(
                reason_code=EMPTY_REASON,
                pitcher_count=ONE,
                pitcher_ratio=ZERO,
            ),
        )
        expected_reason_codes = (EMPTY_REASON,)
    elif report.watch_pitcher_count == ZERO:
        expected_reason_codes = (PASSED_REASON,)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.digest_status != (WATCH_STATUS if report.watch_pitcher_count > ZERO else PASS_STATUS):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_velocity_drop_count = _decimal_count(
        sum(
            1
            for row in report.rows
            if SEVERE_DROP_REASON in row.reason_codes
            or WATCH_DROP_REASON in row.reason_codes
        ),
    )
    if report.velocity_drop_pitcher_count != expected_velocity_drop_count:
        raise ValueError("velocity_drop_pitcher_count must match rows")
    if report.severe_velocity_drop_pitcher_count != _reason_pitcher_count(
        report.rows,
        SEVERE_DROP_REASON,
    ):
        raise ValueError("severe_velocity_drop_pitcher_count must match rows")
    if report.low_recent_velocity_pitcher_count != _reason_pitcher_count(
        report.rows,
        LOW_RECENT_VELOCITY_REASON,
    ):
        raise ValueError("low_recent_velocity_pitcher_count must match rows")
    if report.late_observation_pitcher_count != _reason_pitcher_count(
        report.rows,
        LATE_WINDOW_REASON,
    ):
        raise ValueError("late_observation_pitcher_count must match rows")
    if report.thin_source_pitcher_count != _reason_pitcher_count(
        report.rows,
        THIN_SOURCES_REASON,
    ):
        raise ValueError("thin_source_pitcher_count must match rows")
    if report.max_velocity_drop_mph != _max_or_none(
        row.velocity_drop_mph for row in report.rows
    ):
        raise ValueError("max_velocity_drop_mph must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchBaseballStartingPitcherVelocityDropDigestRow, ...],
) -> tuple[MarketResearchBaseballStartingPitcherVelocityDropDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballStartingPitcherVelocityDropDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBaseballStartingPitcherVelocityDropDigestRow",
            )
        _require_flags("row", row)
        key = (row.pitcher_key, row.game_key)
        if key in seen:
            raise ValueError("rows must contain unique pitcher game values")
        seen.add(key)
    return rows


def _normalize_source_config_versions(
    versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(versions) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized = []
    seen: set[tuple[str, str]] = set()
    for item in versions:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        pitcher_key, config_version = item
        _require_canonical_string("source_config_versions pitcher_key", pitcher_key)
        _require_canonical_string("source_config_versions config_version", config_version)
        pair = (pitcher_key, config_version)
        if pair in seen:
            raise ValueError("source_config_versions must contain unique pairs")
        seen.add(pair)
        normalized.append(pair)
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount, ...],
) -> tuple[MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballStartingPitcherVelocityDropReasonCodeCount",
            )
        _require_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(count.reason_code)
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, known_reason_codes)
        if reason_code in seen:
            raise ValueError(f"{field_name} must contain unique reason codes")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _payload_value(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value.quantize(QUANTUM, rounding=ROUND_DOWN), "f")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_reason_code(
    field_name: str,
    value: object,
    known_reason_codes: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in known_reason_codes:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = value.quantize(QUANTUM, rounding=ROUND_DOWN)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must have at most six decimal places") from exc
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return _six(normalized)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _six(value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal("value", value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _six(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM, rounding=ROUND_DOWN)
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)


def _require_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
