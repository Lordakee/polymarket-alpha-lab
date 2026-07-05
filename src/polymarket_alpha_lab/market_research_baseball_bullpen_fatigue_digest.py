"""Pure in-memory reducer for baseball bullpen fatigue reports."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-bullpen-fatigue-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
CLEAR_STATUS = "clear"
FATIGUED_STATUS = "fatigued"
LIMITED_HISTORY_STATUS = "limited_history"

WORKLOAD_REASON = "baseball_bullpen_fatigue_workload_high"
BACK_TO_BACK_REASON = "baseball_bullpen_fatigue_back_to_back_usage"
REST_SHORTAGE_REASON = "baseball_bullpen_fatigue_rest_shortage"
LEVERAGE_REASON = "baseball_bullpen_fatigue_leverage_high"
CLEAR_REASON = "baseball_bullpen_fatigue_clear"
LIMITED_HISTORY_REASON = "baseball_bullpen_fatigue_limited_history"
PASSED_REASON = "baseball_bullpen_fatigue_passed"
EMPTY_REASON = "baseball_bullpen_fatigue_empty"

ROW_REASON_CODES = (
    WORKLOAD_REASON,
    BACK_TO_BACK_REASON,
    REST_SHORTAGE_REASON,
    LEVERAGE_REASON,
    LIMITED_HISTORY_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    WORKLOAD_REASON,
    BACK_TO_BACK_REASON,
    REST_SHORTAGE_REASON,
    LEVERAGE_REASON,
    LIMITED_HISTORY_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    BLOCKED_STATUS: "block_report_only_baseball_bullpen_fatigue_digest",
    PASS_STATUS: "continue_report_only_baseball_bullpen_fatigue_digest",
    WATCH_STATUS: "review_report_only_baseball_bullpen_fatigue_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_FATIGUE_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballBullpenFatigueDigestConfig",
    "MarketResearchBaseballBullpenFatigueDigestSnapshot",
    "MarketResearchBaseballBullpenFatigueDigestReasonCodeCount",
    "MarketResearchBaseballBullpenFatigueDigestRow",
    "MarketResearchBaseballBullpenFatigueDigestReport",
    "build_market_research_baseball_bullpen_fatigue_digest",
    "market_research_baseball_bullpen_fatigue_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBaseballBullpenFatigueDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_FATIGUE_DIGEST_CONFIG_VERSION
    )
    workload_index_watch_threshold: Decimal = Decimal("0.700000")
    back_to_back_outing_watch_threshold: Decimal = Decimal("3")
    rest_day_shortage_watch_threshold: Decimal = Decimal("2")
    high_leverage_outing_watch_threshold: Decimal = Decimal("2")
    min_snapshot_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBaseballBullpenFatigueDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "workload_index_watch_threshold",
            _normalize_ratio_decimal(
                "workload_index_watch_threshold",
                self.workload_index_watch_threshold,
            ),
        )
        for field_name in (
            "back_to_back_outing_watch_threshold",
            "rest_day_shortage_watch_threshold",
            "high_leverage_outing_watch_threshold",
            "min_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenFatigueDigestSnapshot(_NoSubclass):
    bullpen_key: str
    team_key: str
    observed_at: datetime
    recent_relief_innings: Decimal
    back_to_back_outing_count: Decimal
    rest_day_shortage_count: Decimal
    high_leverage_outing_count: Decimal
    available_reliever_count: Decimal
    source_count: Decimal
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_FATIGUE_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenFatigueDigestSnapshot,
            "snapshot",
        )
        for field_name in ("bullpen_key", "team_key", "source_config_version"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "recent_relief_innings",
            _normalize_nonnegative_decimal(
                "recent_relief_innings",
                self.recent_relief_innings,
            ),
        )
        for field_name in (
            "back_to_back_outing_count",
            "rest_day_shortage_count",
            "high_leverage_outing_count",
            "available_reliever_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    bullpen_count: Decimal
    bullpen_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenFatigueDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "bullpen_count",
            _normalize_positive_whole_decimal("bullpen_count", self.bullpen_count),
        )
        object.__setattr__(
            self,
            "bullpen_ratio",
            _normalize_ratio_decimal("bullpen_ratio", self.bullpen_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenFatigueDigestRow(_NoSubclass):
    bullpen_key: str
    team_key: str
    snapshot_count: Decimal
    source_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_recent_relief_innings: Decimal
    max_recent_relief_innings: Decimal
    latest_back_to_back_outing_count: Decimal
    max_back_to_back_outing_count: Decimal
    latest_rest_day_shortage_count: Decimal
    max_rest_day_shortage_count: Decimal
    latest_high_leverage_outing_count: Decimal
    max_high_leverage_outing_count: Decimal
    latest_available_reliever_count: Decimal
    min_available_reliever_count: Decimal
    workload_index: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBaseballBullpenFatigueDigestRow, "row")
        for field_name in ("bullpen_key", "team_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "snapshot_count",
            "source_count",
            "latest_back_to_back_outing_count",
            "max_back_to_back_outing_count",
            "latest_rest_day_shortage_count",
            "max_rest_day_shortage_count",
            "latest_high_leverage_outing_count",
            "max_high_leverage_outing_count",
            "latest_available_reliever_count",
            "min_available_reliever_count",
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
            "latest_recent_relief_innings",
            "max_recent_relief_innings",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "workload_index",
            _normalize_ratio_decimal("workload_index", self.workload_index),
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
class MarketResearchBaseballBullpenFatigueDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    bullpen_count: Decimal
    clear_bullpen_count: Decimal
    fatigued_bullpen_count: Decimal
    limited_history_bullpen_count: Decimal
    snapshot_count: Decimal
    high_workload_bullpen_count: Decimal
    back_to_back_bullpen_count: Decimal
    rest_shortage_bullpen_count: Decimal
    high_leverage_bullpen_count: Decimal
    workload_index_watch_threshold: Decimal
    back_to_back_outing_watch_threshold: Decimal
    rest_day_shortage_watch_threshold: Decimal
    high_leverage_outing_watch_threshold: Decimal
    min_snapshot_count: Decimal
    max_workload_index: Decimal | None
    max_recent_relief_innings: Decimal | None
    min_available_reliever_count: Decimal | None
    rows: tuple[MarketResearchBaseballBullpenFatigueDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBaseballBullpenFatigueDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchBaseballBullpenFatigueDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member(
            "digest_status",
            self.digest_status,
            (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS),
        )
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "bullpen_count",
            "clear_bullpen_count",
            "fatigued_bullpen_count",
            "limited_history_bullpen_count",
            "snapshot_count",
            "high_workload_bullpen_count",
            "back_to_back_bullpen_count",
            "rest_shortage_bullpen_count",
            "high_leverage_bullpen_count",
            "back_to_back_outing_watch_threshold",
            "rest_day_shortage_watch_threshold",
            "high_leverage_outing_watch_threshold",
            "min_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "workload_index_watch_threshold",
            _normalize_ratio_decimal(
                "workload_index_watch_threshold",
                self.workload_index_watch_threshold,
            ),
        )
        for field_name in (
            "max_workload_index",
            "max_recent_relief_innings",
            "min_available_reliever_count",
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


def build_market_research_baseball_bullpen_fatigue_digest(
    snapshots: list[MarketResearchBaseballBullpenFatigueDigestSnapshot]
    | tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
    *,
    config: MarketResearchBaseballBullpenFatigueDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchBaseballBullpenFatigueDigestReport:
    if config is None:
        config = MarketResearchBaseballBullpenFatigueDigestConfig()
    elif type(config) is not MarketResearchBaseballBullpenFatigueDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchBaseballBullpenFatigueDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_snapshots(snapshots)
    _reject_future_snapshots(normalized, generated_at_utc)
    rows = _rows(normalized, config)
    bullpen_count = _decimal_count(len(rows))
    fatigued_count = _decimal_count(
        sum(1 for row in rows if row.digest_status == FATIGUED_STATUS),
    )
    if not rows:
        digest_status = BLOCKED_STATUS
    elif fatigued_count > ZERO:
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                bullpen_count=ONE,
                bullpen_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = tuple((*reason_codes, PASSED_REASON))

    return MarketResearchBaseballBullpenFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        bullpen_count=bullpen_count,
        clear_bullpen_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        fatigued_bullpen_count=fatigued_count,
        limited_history_bullpen_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == LIMITED_HISTORY_STATUS),
        ),
        snapshot_count=_decimal_count(len(normalized)),
        high_workload_bullpen_count=_reason_bullpen_count(rows, WORKLOAD_REASON),
        back_to_back_bullpen_count=_reason_bullpen_count(rows, BACK_TO_BACK_REASON),
        rest_shortage_bullpen_count=_reason_bullpen_count(rows, REST_SHORTAGE_REASON),
        high_leverage_bullpen_count=_reason_bullpen_count(rows, LEVERAGE_REASON),
        workload_index_watch_threshold=config.workload_index_watch_threshold,
        back_to_back_outing_watch_threshold=config.back_to_back_outing_watch_threshold,
        rest_day_shortage_watch_threshold=config.rest_day_shortage_watch_threshold,
        high_leverage_outing_watch_threshold=config.high_leverage_outing_watch_threshold,
        min_snapshot_count=config.min_snapshot_count,
        max_workload_index=_max_or_none(row.workload_index for row in rows),
        max_recent_relief_innings=_max_or_none(
            row.max_recent_relief_innings for row in rows
        ),
        min_available_reliever_count=_min_or_none(
            row.min_available_reliever_count for row in rows
        ),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_baseball_bullpen_fatigue_digest_payload(
    report: MarketResearchBaseballBullpenFatigueDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBaseballBullpenFatigueDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchBaseballBullpenFatigueDigestReport",
        )
    _revalidate_public_dataclass_for_payload(report)
    return _payload_value(report)  # type: ignore[return-value]


def _normalize_snapshots(
    snapshots: list[MarketResearchBaseballBullpenFatigueDigestSnapshot]
    | tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
) -> tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    normalized = tuple(snapshots)
    seen: set[tuple[str, datetime]] = set()
    for snapshot in normalized:
        if type(snapshot) is not MarketResearchBaseballBullpenFatigueDigestSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchBaseballBullpenFatigueDigestSnapshot",
            )
        _require_flags("snapshot", snapshot)
        key = (snapshot.bullpen_key, snapshot.observed_at)
        if key in seen:
            raise ValueError("snapshots must not contain duplicate bullpen observations")
        seen.add(key)
    return normalized


def _reject_future_snapshots(
    snapshots: tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    snapshots: tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
    config: MarketResearchBaseballBullpenFatigueDigestConfig,
) -> tuple[MarketResearchBaseballBullpenFatigueDigestRow, ...]:
    grouped: dict[str, list[MarketResearchBaseballBullpenFatigueDigestSnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.bullpen_key, []).append(snapshot)
    rows = tuple(_row_for_bullpen(tuple(items), config) for items in grouped.values())
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_bullpen(
    snapshots: tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
    config: MarketResearchBaseballBullpenFatigueDigestConfig,
) -> MarketResearchBaseballBullpenFatigueDigestRow:
    chronological = tuple(sorted(snapshots, key=lambda item: item.observed_at))
    first = chronological[0]
    latest = chronological[-1]
    _validate_bullpen_identity(chronological)
    innings_values = tuple(item.recent_relief_innings for item in chronological)
    back_to_back_values = tuple(item.back_to_back_outing_count for item in chronological)
    rest_shortage_values = tuple(item.rest_day_shortage_count for item in chronological)
    leverage_values = tuple(item.high_leverage_outing_count for item in chronological)
    reliever_values = tuple(item.available_reliever_count for item in chronological)
    workload_index = _workload_index(latest.recent_relief_innings, reliever_values)
    reason_codes = _row_reason_codes(
        snapshot_count=_decimal_count(len(chronological)),
        workload_index=workload_index,
        back_to_back_outing_count=latest.back_to_back_outing_count,
        rest_day_shortage_count=latest.rest_day_shortage_count,
        high_leverage_outing_count=latest.high_leverage_outing_count,
        config=config,
    )
    return MarketResearchBaseballBullpenFatigueDigestRow(
        bullpen_key=first.bullpen_key,
        team_key=first.team_key,
        snapshot_count=_decimal_count(len(chronological)),
        source_count=_sum_decimal(item.source_count for item in chronological),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        latest_recent_relief_innings=latest.recent_relief_innings,
        max_recent_relief_innings=max(innings_values),
        latest_back_to_back_outing_count=latest.back_to_back_outing_count,
        max_back_to_back_outing_count=max(back_to_back_values),
        latest_rest_day_shortage_count=latest.rest_day_shortage_count,
        max_rest_day_shortage_count=max(rest_shortage_values),
        latest_high_leverage_outing_count=latest.high_leverage_outing_count,
        max_high_leverage_outing_count=max(leverage_values),
        latest_available_reliever_count=latest.available_reliever_count,
        min_available_reliever_count=min(reliever_values),
        workload_index=workload_index,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_bullpen_identity(
    snapshots: tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
) -> None:
    expected = snapshots[0]
    for snapshot in snapshots:
        if snapshot.team_key != expected.team_key:
            raise ValueError("team_key must match within bullpen_key")


def _row_reason_codes(
    *,
    snapshot_count: Decimal,
    workload_index: Decimal,
    back_to_back_outing_count: Decimal,
    rest_day_shortage_count: Decimal,
    high_leverage_outing_count: Decimal,
    config: MarketResearchBaseballBullpenFatigueDigestConfig,
) -> tuple[str, ...]:
    if snapshot_count < config.min_snapshot_count:
        return (LIMITED_HISTORY_REASON,)
    reason_codes = []
    if workload_index >= config.workload_index_watch_threshold:
        reason_codes.append(WORKLOAD_REASON)
    if back_to_back_outing_count >= config.back_to_back_outing_watch_threshold:
        reason_codes.append(BACK_TO_BACK_REASON)
    if rest_day_shortage_count >= config.rest_day_shortage_watch_threshold:
        reason_codes.append(REST_SHORTAGE_REASON)
    if high_leverage_outing_count >= config.high_leverage_outing_watch_threshold:
        reason_codes.append(LEVERAGE_REASON)
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


def _row_sort_key(
    row: MarketResearchBaseballBullpenFatigueDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        _row_status_rank(row.digest_status),
        -row.workload_index,
        row.team_key,
        row.bullpen_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballBullpenFatigueDigestRow, ...],
) -> tuple[MarketResearchBaseballBullpenFatigueDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(
            reason_code=reason_code,
            bullpen_count=_decimal_count(count),
            bullpen_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _reason_bullpen_count(
    rows: tuple[MarketResearchBaseballBullpenFatigueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    snapshots: tuple[MarketResearchBaseballBullpenFatigueDigestSnapshot, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (snapshot.bullpen_key, snapshot.source_config_version)
                for snapshot in snapshots
            }
        )
    )


def _workload_index(
    recent_relief_innings: Decimal,
    available_reliever_counts: tuple[Decimal, ...],
) -> Decimal:
    denominator = _sum_decimal(available_reliever_counts)
    if denominator == ZERO:
        return ONE
    ratio = recent_relief_innings / denominator
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


def _validate_row(row: MarketResearchBaseballBullpenFatigueDigestRow) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not exceed latest_observed_at")
    if row.max_recent_relief_innings < row.latest_recent_relief_innings:
        raise ValueError("max_recent_relief_innings must cover latest value")
    if row.max_back_to_back_outing_count < row.latest_back_to_back_outing_count:
        raise ValueError("max_back_to_back_outing_count must cover latest value")
    if row.max_rest_day_shortage_count < row.latest_rest_day_shortage_count:
        raise ValueError("max_rest_day_shortage_count must cover latest value")
    if row.max_high_leverage_outing_count < row.latest_high_leverage_outing_count:
        raise ValueError("max_high_leverage_outing_count must cover latest value")
    if row.min_available_reliever_count > row.latest_available_reliever_count:
        raise ValueError("min_available_reliever_count must cover latest value")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBaseballBullpenFatigueDigestReport) -> None:
    if report.bullpen_count != _decimal_count(len(report.rows)):
        raise ValueError("bullpen_count must match rows")
    if report.clear_bullpen_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_bullpen_count must match rows")
    if report.fatigued_bullpen_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == FATIGUED_STATUS),
    ):
        raise ValueError("fatigued_bullpen_count must match rows")
    if report.limited_history_bullpen_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == LIMITED_HISTORY_STATUS),
    ):
        raise ValueError("limited_history_bullpen_count must match rows")
    if report.snapshot_count != _sum_decimal(row.snapshot_count for row in report.rows):
        raise ValueError("snapshot_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                bullpen_count=ONE,
                bullpen_ratio=ZERO,
            ),
        )
        expected_reason_codes = (EMPTY_REASON,)
    elif report.fatigued_bullpen_count == ZERO:
        expected_reason_codes = tuple((*expected_reason_codes, PASSED_REASON))
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if not report.rows:
        expected_status = BLOCKED_STATUS
    elif report.fatigued_bullpen_count > ZERO:
        expected_status = WATCH_STATUS
    else:
        expected_status = PASS_STATUS
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.high_workload_bullpen_count != _reason_bullpen_count(
        report.rows,
        WORKLOAD_REASON,
    ):
        raise ValueError("high_workload_bullpen_count must match rows")
    if report.back_to_back_bullpen_count != _reason_bullpen_count(
        report.rows,
        BACK_TO_BACK_REASON,
    ):
        raise ValueError("back_to_back_bullpen_count must match rows")
    if report.rest_shortage_bullpen_count != _reason_bullpen_count(
        report.rows,
        REST_SHORTAGE_REASON,
    ):
        raise ValueError("rest_shortage_bullpen_count must match rows")
    if report.high_leverage_bullpen_count != _reason_bullpen_count(
        report.rows,
        LEVERAGE_REASON,
    ):
        raise ValueError("high_leverage_bullpen_count must match rows")
    if report.max_workload_index != _max_or_none(row.workload_index for row in report.rows):
        raise ValueError("max_workload_index must match rows")
    if report.max_recent_relief_innings != _max_or_none(
        row.max_recent_relief_innings for row in report.rows
    ):
        raise ValueError("max_recent_relief_innings must match rows")
    if report.min_available_reliever_count != _min_or_none(
        row.min_available_reliever_count for row in report.rows
    ):
        raise ValueError("min_available_reliever_count must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchBaseballBullpenFatigueDigestRow, ...],
) -> tuple[MarketResearchBaseballBullpenFatigueDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballBullpenFatigueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballBullpenFatigueDigestRow",
            )
        _require_flags("row", row)
        if row.bullpen_key in seen:
            raise ValueError("rows must contain unique bullpen_key values")
        seen.add(row.bullpen_key)
    canonical = tuple(sorted(rows, key=_row_sort_key))
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
        bullpen_key, config_version = item
        _require_canonical_string("source_config_versions bullpen_key", bullpen_key)
        _require_canonical_string("source_config_versions config_version", config_version)
        pair = (bullpen_key, config_version)
        if pair in seen:
            raise ValueError("source_config_versions must contain unique pairs")
        seen.add(pair)
        normalized.append(pair)
    canonical = tuple(sorted(normalized))
    if tuple(normalized) != canonical:
        raise ValueError("source_config_versions must be canonical")
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchBaseballBullpenFatigueDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBaseballBullpenFatigueDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchBaseballBullpenFatigueDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballBullpenFatigueDigestReasonCodeCount",
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
        if LIMITED_HISTORY_REASON in seen and len(seen) != 1:
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
    return tuple(normalized)


def _payload_value(value: object, field_name: str = "value") -> object:
    if _is_public_dataclass_instance(value):
        _revalidate_public_dataclass_for_payload(value)
        return {
            field.name: _payload_value(getattr(value, field.name), field.name)
            for field in fields(value)
        }
    if type(value) is datetime:
        return _as_utc(field_name, value).isoformat()
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return format(value, "f")
    if type(value) is tuple:
        return [_payload_value(item, field_name) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _revalidate_public_dataclass_for_payload(value: object) -> None:
    if type(value) is MarketResearchBaseballBullpenFatigueDigestReport:
        _require_six_decimal_payload_values(value)
        for row in value.rows:
            _revalidate_public_dataclass_for_payload(row)
        for count in value.reason_code_counts:
            _revalidate_public_dataclass_for_payload(count)
        MarketResearchBaseballBullpenFatigueDigestReport(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchBaseballBullpenFatigueDigestRow:
        _require_six_decimal_payload_values(value)
        MarketResearchBaseballBullpenFatigueDigestRow(**_dataclass_field_values(value))
        return
    if type(value) is MarketResearchBaseballBullpenFatigueDigestReasonCodeCount:
        _require_six_decimal_payload_values(value)
        MarketResearchBaseballBullpenFatigueDigestReasonCodeCount(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchBaseballBullpenFatigueDigestSnapshot:
        _require_six_decimal_payload_values(value)
        MarketResearchBaseballBullpenFatigueDigestSnapshot(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchBaseballBullpenFatigueDigestConfig:
        _require_six_decimal_payload_values(value)
        MarketResearchBaseballBullpenFatigueDigestConfig(**_dataclass_field_values(value))
        return
    raise ValueError("payload value must be a public baseball bullpen fatigue dataclass")


def _is_public_dataclass_instance(value: object) -> bool:
    return type(value) in (
        MarketResearchBaseballBullpenFatigueDigestConfig,
        MarketResearchBaseballBullpenFatigueDigestSnapshot,
        MarketResearchBaseballBullpenFatigueDigestReasonCodeCount,
        MarketResearchBaseballBullpenFatigueDigestRow,
        MarketResearchBaseballBullpenFatigueDigestReport,
    )


def _dataclass_field_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _require_six_decimal_payload_values(value: object) -> None:
    if type(value) is Decimal:
        _require_six_decimal("value", value)
        return
    if _is_public_dataclass_instance(value):
        for field in fields(value):
            _require_six_decimal_payload_field(
                field.name,
                getattr(value, field.name),
            )
        return
    if type(value) is tuple:
        for item in value:
            _require_six_decimal_payload_values(item)
        return
    if type(value) in (list, dict, set):
        raise ValueError("payload value must remain constructor-normalized")


def _require_six_decimal_payload_field(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return
    if _is_public_dataclass_instance(value):
        _require_six_decimal_payload_values(value)
        return
    if type(value) is tuple:
        for item in value:
            _require_six_decimal_payload_field(field_name, item)
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")


def _require_six_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must be six-decimal")


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
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _six(total)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
