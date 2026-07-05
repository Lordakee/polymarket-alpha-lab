"""Pure in-memory reducer for baseball pitcher volatility reports."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASEBALL_PITCHER_VOLATILITY_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-pitcher-volatility-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"
INSUFFICIENT_HISTORY_STATUS = "insufficient_history"

ERA_RANGE_REASON = "baseball_pitcher_volatility_era_range_high"
WHIP_RANGE_REASON = "baseball_pitcher_volatility_whip_range_high"
PITCH_COUNT_RANGE_REASON = "baseball_pitcher_volatility_pitch_count_range_high"
VELOCITY_DROP_REASON = "baseball_pitcher_volatility_velocity_drop"
CLEAR_REASON = "baseball_pitcher_volatility_clear"
INSUFFICIENT_HISTORY_REASON = "baseball_pitcher_volatility_insufficient_history"
PASSED_REASON = "baseball_pitcher_volatility_passed"
EMPTY_REASON = "baseball_pitcher_volatility_empty"

ROW_REASON_CODES = (
    ERA_RANGE_REASON,
    PITCH_COUNT_RANGE_REASON,
    VELOCITY_DROP_REASON,
    WHIP_RANGE_REASON,
    INSUFFICIENT_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    ERA_RANGE_REASON,
    PITCH_COUNT_RANGE_REASON,
    VELOCITY_DROP_REASON,
    WHIP_RANGE_REASON,
    INSUFFICIENT_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = (*ROW_REASON_CODES, PASSED_REASON, EMPTY_REASON)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_baseball_pitcher_volatility_digest",
    WATCH_STATUS: "review_report_only_baseball_pitcher_volatility_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live " "trading",
    "wal" "let",
    "bro" "ker",
    "sign" "ing",
    "sub" "mit",
    "can" "cel",
    "or" "der",
    "re" "place",
    "ex" "change",
    "ac" "count",
    "ad" "vice",
    "au" "th",
    "pri" "vate",
    "sec" "ret",
    "to" "ken",
    "ke" "ys",
    "api" "_" "key",
    "api" "-" "key",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_PITCHER_VOLATILITY_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballPitcherVolatilityDigestConfig",
    "MarketResearchBaseballPitcherVolatilityDigestSnapshot",
    "MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount",
    "MarketResearchBaseballPitcherVolatilityDigestRow",
    "MarketResearchBaseballPitcherVolatilityDigestReport",
    "build_market_research_baseball_pitcher_volatility_digest",
    "market_research_baseball_pitcher_volatility_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBaseballPitcherVolatilityDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_PITCHER_VOLATILITY_DIGEST_CONFIG_VERSION
    )
    era_range_watch_threshold: Decimal = Decimal("0.600000")
    whip_range_watch_threshold: Decimal = Decimal("0.150000")
    pitch_count_range_watch_threshold: Decimal = Decimal("18.000000")
    velocity_drop_watch_threshold: Decimal = Decimal("1.500000")
    min_snapshot_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            MarketResearchBaseballPitcherVolatilityDigestConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "era_range_watch_threshold",
            "whip_range_watch_threshold",
            "pitch_count_range_watch_threshold",
            "velocity_drop_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_snapshot_count",
            _normalize_positive_whole_decimal(
                "min_snapshot_count",
                self.min_snapshot_count,
            ),
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballPitcherVolatilityDigestSnapshot(_NoSubclass):
    pitcher_key: str
    pitcher_name: str
    team_key: str
    observed_at: datetime
    projected_era: Decimal
    projected_whip: Decimal
    projected_pitch_count: Decimal
    fastball_velocity_mph: Decimal
    source_count: Decimal
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_PITCHER_VOLATILITY_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "snapshot",
            self,
            MarketResearchBaseballPitcherVolatilityDigestSnapshot,
        )
        for field_name in (
            "pitcher_key",
            "pitcher_name",
            "team_key",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "projected_era",
            "projected_whip",
            "projected_pitch_count",
            "fastball_velocity_mph",
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
        _require_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    pitcher_count: Decimal
    pitcher_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "pitcher_count",
            _normalize_nonnegative_whole_decimal("pitcher_count", self.pitcher_count),
        )
        if self.pitcher_count <= ZERO:
            raise ValueError("pitcher_count must be positive")
        object.__setattr__(
            self,
            "pitcher_ratio",
            _normalize_ratio_decimal("pitcher_ratio", self.pitcher_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBaseballPitcherVolatilityDigestRow(_NoSubclass):
    pitcher_key: str
    pitcher_name: str
    team_key: str
    snapshot_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_projected_era: Decimal
    latest_projected_whip: Decimal
    latest_projected_pitch_count: Decimal
    latest_fastball_velocity_mph: Decimal
    era_min: Decimal
    era_max: Decimal
    era_range: Decimal
    whip_min: Decimal
    whip_max: Decimal
    whip_range: Decimal
    pitch_count_min: Decimal
    pitch_count_max: Decimal
    pitch_count_range: Decimal
    fastball_velocity_max: Decimal
    velocity_drop: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, MarketResearchBaseballPitcherVolatilityDigestRow)
        for field_name in ("pitcher_key", "pitcher_name", "team_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "snapshot_count",
            _normalize_nonnegative_whole_decimal("snapshot_count", self.snapshot_count),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
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
            "latest_projected_era",
            "latest_projected_whip",
            "latest_projected_pitch_count",
            "latest_fastball_velocity_mph",
            "era_min",
            "era_max",
            "era_range",
            "whip_min",
            "whip_max",
            "whip_range",
            "pitch_count_min",
            "pitch_count_max",
            "pitch_count_range",
            "fastball_velocity_max",
            "velocity_drop",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "digest_status",
            self.digest_status,
            (CLEAR_STATUS, WATCH_STATUS, INSUFFICIENT_HISTORY_STATUS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballPitcherVolatilityDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    pitcher_count: Decimal
    clear_pitcher_count: Decimal
    watch_pitcher_count: Decimal
    insufficient_history_pitcher_count: Decimal
    snapshot_count: Decimal
    volatile_era_pitcher_count: Decimal
    volatile_whip_pitcher_count: Decimal
    volatile_pitch_count_pitcher_count: Decimal
    velocity_drop_pitcher_count: Decimal
    era_range_watch_threshold: Decimal
    whip_range_watch_threshold: Decimal
    pitch_count_range_watch_threshold: Decimal
    velocity_drop_watch_threshold: Decimal
    min_snapshot_count: Decimal
    max_era_range: Decimal | None
    max_whip_range: Decimal | None
    max_pitch_count_range: Decimal | None
    max_velocity_drop: Decimal | None
    rows: tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            MarketResearchBaseballPitcherVolatilityDigestReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "pitcher_count",
            "clear_pitcher_count",
            "watch_pitcher_count",
            "insufficient_history_pitcher_count",
            "snapshot_count",
            "volatile_era_pitcher_count",
            "volatile_whip_pitcher_count",
            "volatile_pitch_count_pitcher_count",
            "velocity_drop_pitcher_count",
            "min_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "era_range_watch_threshold",
            "whip_range_watch_threshold",
            "pitch_count_range_watch_threshold",
            "velocity_drop_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_era_range",
            "max_whip_range",
            "max_pitch_count_range",
            "max_velocity_drop",
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


def build_market_research_baseball_pitcher_volatility_digest(
    snapshots: list[MarketResearchBaseballPitcherVolatilityDigestSnapshot]
    | tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
    *,
    config: MarketResearchBaseballPitcherVolatilityDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballPitcherVolatilityDigestReport:
    if type(config) is not MarketResearchBaseballPitcherVolatilityDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBaseballPitcherVolatilityDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_snapshots(snapshots)
    _reject_future_snapshots(normalized, generated_at_utc)
    rows = _rows(normalized, config)
    pitcher_count = _decimal_count(len(rows))
    watch_count = _decimal_count(sum(1 for row in rows if row.digest_status == WATCH_STATUS))
    digest_status = WATCH_STATUS if watch_count > ZERO else PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                pitcher_count=ONE,
                pitcher_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = tuple((*reason_codes, PASSED_REASON))

    return MarketResearchBaseballPitcherVolatilityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        pitcher_count=pitcher_count,
        clear_pitcher_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_pitcher_count=watch_count,
        insufficient_history_pitcher_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == INSUFFICIENT_HISTORY_STATUS),
        ),
        snapshot_count=_decimal_count(len(normalized)),
        volatile_era_pitcher_count=_reason_pitcher_count(rows, ERA_RANGE_REASON),
        volatile_whip_pitcher_count=_reason_pitcher_count(rows, WHIP_RANGE_REASON),
        volatile_pitch_count_pitcher_count=_reason_pitcher_count(
            rows,
            PITCH_COUNT_RANGE_REASON,
        ),
        velocity_drop_pitcher_count=_reason_pitcher_count(rows, VELOCITY_DROP_REASON),
        era_range_watch_threshold=config.era_range_watch_threshold,
        whip_range_watch_threshold=config.whip_range_watch_threshold,
        pitch_count_range_watch_threshold=config.pitch_count_range_watch_threshold,
        velocity_drop_watch_threshold=config.velocity_drop_watch_threshold,
        min_snapshot_count=config.min_snapshot_count,
        max_era_range=_max_or_none(row.era_range for row in rows),
        max_whip_range=_max_or_none(row.whip_range for row in rows),
        max_pitch_count_range=_max_or_none(row.pitch_count_range for row in rows),
        max_velocity_drop=_max_or_none(row.velocity_drop for row in rows),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_baseball_pitcher_volatility_digest_payload(
    report: MarketResearchBaseballPitcherVolatilityDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBaseballPitcherVolatilityDigestReport:
        raise ValueError(
            "report must be a MarketResearchBaseballPitcherVolatilityDigestReport",
        )
    revalidated = _revalidate_report_for_payload(report)
    payload = _payload_value(revalidated)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_flags("payload", _DictFlags(payload))
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _revalidate_report_for_payload(
    report: MarketResearchBaseballPitcherVolatilityDigestReport,
) -> MarketResearchBaseballPitcherVolatilityDigestReport:
    _require_flags("report", report)
    _require_payload_datetime_utc("generated_at", report.generated_at)
    values = _dataclass_values(report)
    values["rows"] = _revalidate_rows_for_payload(report.rows)
    values["reason_code_counts"] = _revalidate_reason_code_counts_for_payload(
        report.reason_code_counts,
    )
    return MarketResearchBaseballPitcherVolatilityDigestReport(**values)


def _revalidate_rows_for_payload(
    rows: object,
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    revalidated = []
    for row in rows:
        if type(row) is not MarketResearchBaseballPitcherVolatilityDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballPitcherVolatilityDigestRow",
            )
        _require_payload_datetime_utc("first_observed_at", row.first_observed_at)
        _require_payload_datetime_utc("latest_observed_at", row.latest_observed_at)
        revalidated.append(
            MarketResearchBaseballPitcherVolatilityDigestRow(
                **_dataclass_values(row),
            ),
        )
    return tuple(revalidated)


def _revalidate_reason_code_counts_for_payload(
    counts: object,
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    revalidated = []
    for count in counts:
        if type(count) is not MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount",
            )
        revalidated.append(
            MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
                **_dataclass_values(count),
            ),
        )
    return tuple(revalidated)


def _dataclass_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _normalize_snapshots(
    snapshots: list[MarketResearchBaseballPitcherVolatilityDigestSnapshot]
    | tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    normalized = tuple(snapshots)
    seen: set[tuple[str, datetime]] = set()
    for snapshot in normalized:
        if type(snapshot) is not MarketResearchBaseballPitcherVolatilityDigestSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchBaseballPitcherVolatilityDigestSnapshot",
            )
        _require_flags("snapshot", snapshot)
        key = (snapshot.pitcher_key, snapshot.observed_at)
        if key in seen:
            raise ValueError("snapshots must not contain duplicate pitcher observations")
        seen.add(key)
    return normalized


def _reject_future_snapshots(
    snapshots: tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    snapshots: tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
    config: MarketResearchBaseballPitcherVolatilityDigestConfig,
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBaseballPitcherVolatilityDigestSnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.pitcher_key, []).append(snapshot)

    rows = tuple(_row_for_pitcher(tuple(items), config) for items in grouped.values())
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_status_rank(row.digest_status),
                row.pitcher_key,
                row.team_key,
            ),
        )
    )


def _row_for_pitcher(
    snapshots: tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
    config: MarketResearchBaseballPitcherVolatilityDigestConfig,
) -> MarketResearchBaseballPitcherVolatilityDigestRow:
    chronological = tuple(sorted(snapshots, key=lambda item: item.observed_at))
    first = chronological[0]
    latest = chronological[-1]
    _validate_pitcher_identity(chronological)
    era_values = tuple(item.projected_era for item in chronological)
    whip_values = tuple(item.projected_whip for item in chronological)
    pitch_count_values = tuple(item.projected_pitch_count for item in chronological)
    velocity_values = tuple(item.fastball_velocity_mph for item in chronological)
    reason_codes = _row_reason_codes(
            snapshot_count=_decimal_count(len(chronological)),
        era_range=_range(era_values),
        whip_range=_range(whip_values),
        pitch_count_range=_range(pitch_count_values),
        velocity_drop=_velocity_drop(velocity_values),
        config=config,
    )
    return MarketResearchBaseballPitcherVolatilityDigestRow(
        pitcher_key=first.pitcher_key,
        pitcher_name=first.pitcher_name,
        team_key=first.team_key,
        snapshot_count=_decimal_count(len(chronological)),
        source_count=_sum_decimal(item.source_count for item in chronological),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_projected_era=latest.projected_era,
        latest_projected_whip=latest.projected_whip,
        latest_projected_pitch_count=latest.projected_pitch_count,
        latest_fastball_velocity_mph=latest.fastball_velocity_mph,
        era_min=min(era_values),
        era_max=max(era_values),
        era_range=_range(era_values),
        whip_min=min(whip_values),
        whip_max=max(whip_values),
        whip_range=_range(whip_values),
        pitch_count_min=min(pitch_count_values),
        pitch_count_max=max(pitch_count_values),
        pitch_count_range=_range(pitch_count_values),
        fastball_velocity_max=max(velocity_values),
        velocity_drop=_velocity_drop(velocity_values),
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_pitcher_identity(
    snapshots: tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
) -> None:
    expected = snapshots[0]
    for snapshot in snapshots:
        if snapshot.pitcher_name != expected.pitcher_name:
            raise ValueError("pitcher_name must match within pitcher_key")
        if snapshot.team_key != expected.team_key:
            raise ValueError("team_key must match within pitcher_key")


def _row_reason_codes(
    *,
    snapshot_count: Decimal,
    era_range: Decimal,
    whip_range: Decimal,
    pitch_count_range: Decimal,
    velocity_drop: Decimal,
    config: MarketResearchBaseballPitcherVolatilityDigestConfig,
) -> tuple[str, ...]:
    if snapshot_count < config.min_snapshot_count:
        return (INSUFFICIENT_HISTORY_REASON,)
    reason_codes = []
    if era_range >= config.era_range_watch_threshold:
        reason_codes.append(ERA_RANGE_REASON)
    if whip_range >= config.whip_range_watch_threshold:
        reason_codes.append(WHIP_RANGE_REASON)
    if pitch_count_range >= config.pitch_count_range_watch_threshold:
        reason_codes.append(PITCH_COUNT_RANGE_REASON)
    if velocity_drop >= config.velocity_drop_watch_threshold:
        reason_codes.append(VELOCITY_DROP_REASON)
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    if reason_codes == (INSUFFICIENT_HISTORY_REASON,):
        return INSUFFICIENT_HISTORY_STATUS
    return WATCH_STATUS


def _row_status_rank(status: str) -> int:
    if status == WATCH_STATUS:
        return 0
    if status == INSUFFICIENT_HISTORY_STATUS:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...],
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
            reason_code=reason_code,
            pitcher_count=_decimal_count(count),
            pitcher_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _reason_pitcher_count(
    rows: tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    snapshots: tuple[MarketResearchBaseballPitcherVolatilityDigestSnapshot, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (snapshot.pitcher_key, snapshot.source_config_version)
                for snapshot in snapshots
            }
        )
    )


def _range(values: tuple[Decimal, ...]) -> Decimal:
    return _six(max(values) - min(values))


def _velocity_drop(values: tuple[Decimal, ...]) -> Decimal:
    latest = values[-1]
    peak = max(values)
    if peak <= latest:
        return ZERO
    return _six(peak - latest)


def _max_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _six(max(normalized))


def _validate_row(row: MarketResearchBaseballPitcherVolatilityDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.era_min > row.era_max:
        raise ValueError("era_min must not exceed era_max")
    if row.whip_min > row.whip_max:
        raise ValueError("whip_min must not exceed whip_max")
    if row.pitch_count_min > row.pitch_count_max:
        raise ValueError("pitch_count_min must not exceed pitch_count_max")
    if row.era_range != _six(row.era_max - row.era_min):
        raise ValueError("era_range must match era values")
    if row.whip_range != _six(row.whip_max - row.whip_min):
        raise ValueError("whip_range must match whip values")
    if row.pitch_count_range != _six(row.pitch_count_max - row.pitch_count_min):
        raise ValueError("pitch_count_range must match pitch count values")
    if row.fastball_velocity_max < row.latest_fastball_velocity_mph:
        raise ValueError("fastball_velocity_max must cover latest velocity")
    expected_velocity_drop = _six(
        row.fastball_velocity_max - row.latest_fastball_velocity_mph,
    )
    if row.velocity_drop != expected_velocity_drop:
        raise ValueError("velocity_drop must match velocity values")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBaseballPitcherVolatilityDigestReport) -> None:
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
    if report.insufficient_history_pitcher_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == INSUFFICIENT_HISTORY_STATUS),
    ):
        raise ValueError("insufficient_history_pitcher_count must match rows")
    if report.snapshot_count != _sum_decimal(row.snapshot_count for row in report.rows):
        raise ValueError("snapshot_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                pitcher_count=ONE,
                pitcher_ratio=ZERO,
            ),
        )
        expected_reason_codes = (EMPTY_REASON,)
    elif report.watch_pitcher_count == ZERO:
        expected_reason_codes = tuple((*expected_reason_codes, PASSED_REASON))
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.digest_status != (WATCH_STATUS if report.watch_pitcher_count > ZERO else PASS_STATUS):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.volatile_era_pitcher_count != _reason_pitcher_count(
        report.rows,
        ERA_RANGE_REASON,
    ):
        raise ValueError("volatile_era_pitcher_count must match rows")
    if report.volatile_whip_pitcher_count != _reason_pitcher_count(
        report.rows,
        WHIP_RANGE_REASON,
    ):
        raise ValueError("volatile_whip_pitcher_count must match rows")
    if report.volatile_pitch_count_pitcher_count != _reason_pitcher_count(
        report.rows,
        PITCH_COUNT_RANGE_REASON,
    ):
        raise ValueError("volatile_pitch_count_pitcher_count must match rows")
    if report.velocity_drop_pitcher_count != _reason_pitcher_count(
        report.rows,
        VELOCITY_DROP_REASON,
    ):
        raise ValueError("velocity_drop_pitcher_count must match rows")
    if report.max_era_range != _max_or_none(row.era_range for row in report.rows):
        raise ValueError("max_era_range must match rows")
    if report.max_whip_range != _max_or_none(row.whip_range for row in report.rows):
        raise ValueError("max_whip_range must match rows")
    if report.max_pitch_count_range != _max_or_none(
        row.pitch_count_range for row in report.rows
    ):
        raise ValueError("max_pitch_count_range must match rows")
    if report.max_velocity_drop != _max_or_none(
        row.velocity_drop for row in report.rows
    ):
        raise ValueError("max_velocity_drop must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...],
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballPitcherVolatilityDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballPitcherVolatilityDigestRow",
            )
        _require_flags("row", row)
        if row.pitcher_key in seen:
            raise ValueError("rows must contain unique pitcher_key values")
        seen.add(row.pitcher_key)
    canonical = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_status_rank(row.digest_status),
                row.pitcher_key,
                row.team_key,
            ),
        )
    )
    if rows != canonical:
        raise ValueError("rows must be canonical")
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
    normalized_tuple = tuple(normalized)
    canonical = tuple(sorted(normalized_tuple))
    if normalized_tuple != canonical:
        raise ValueError("source_config_versions must be canonical")
    return normalized_tuple


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount",
            )
        _require_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(count.reason_code)
    canonical = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != canonical:
        raise ValueError("reason_code_counts must be canonical")
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
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if known_reason_codes is ROW_REASON_CODES:
        if CLEAR_REASON in seen and len(seen) != 1:
            raise ValueError(f"{field_name} must match digest_status")
        if INSUFFICIENT_HISTORY_REASON in seen and len(seen) != 1:
            raise ValueError(f"{field_name} must match digest_status")
    if known_reason_codes is DIGEST_REASON_CODES:
        if EMPTY_REASON in seen and len(seen) != 1:
            raise ValueError(f"{field_name} must match digest_status")
        if PASSED_REASON in seen and len(seen) != 1:
            non_passed = seen - {PASSED_REASON}
            if not non_passed:
                raise ValueError(f"{field_name} must match digest_status")
    canonical = tuple(sorted(normalized))
    if tuple(normalized) != canonical:
        raise ValueError(f"{field_name} must be canonical")
    return canonical


def _payload_value(value: object) -> object:
    if type(value) is MarketResearchBaseballPitcherVolatilityDigestReport:
        return _payload_dataclass_values(_revalidate_report_for_payload(value))
    if type(value) is MarketResearchBaseballPitcherVolatilityDigestRow:
        return _payload_dataclass_values(
            MarketResearchBaseballPitcherVolatilityDigestRow(
                **_dataclass_values(value),
            ),
        )
    if type(value) is MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount:
        return _payload_dataclass_values(
            MarketResearchBaseballPitcherVolatilityDigestReasonCodeCount(
                **_dataclass_values(value),
            ),
        )
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return format(_six(value), "f")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (list, dict, set):
        raise ValueError("payload contains unsupported raw container")
    raise ValueError("payload contains unsupported value")


def _payload_dataclass_values(value: object) -> dict[str, object]:
    return {
        field.name: _payload_value(getattr(value, field.name))
        for field in fields(value)
    }


def _require_payload_datetime_utc(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC")


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
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public text")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _has_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


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
    if normalized != value:
        raise ValueError(f"{field_name} must have at most six decimal places")
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
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return _six(total)


def _require_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
