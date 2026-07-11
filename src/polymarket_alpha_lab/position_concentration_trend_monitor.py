"""Pure paper-only position concentration trend reducer.

This module summarizes supplied paper position concentration guard reports. It is
pure/report-only: it does not read files, fetch markets, construct API clients,
authenticate, access wallets, place orders, rank investments, recommend trades,
or retain state between calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.paper_position_concentration_guard import (
    GROUP_TYPES,
    PaperPositionConcentrationGuardReport,
    PaperPositionConcentrationGuardRow,
)
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_POSITION_CONCENTRATION_TREND_MONITOR_CONFIG_VERSION = (
    "position-concentration-trend-monitor-v0"
)
REDACTED = "[REDACTED]"
COUNT_QUANTUM = Decimal("1")
RATE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATE = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
TREND_STATUSES = ("improving", "unchanged", "declining", "new", "resolved")
RISK_STATUSES = ("pass", "watch", "blocked")
REPORT_REASON_CODES = (
    "position_concentration_trend_clear",
    "watch_trend_rate_watch",
    "watch_trend_rate_blocked",
    "max_share_trend_rate_watch",
    "max_share_trend_rate_blocked",
    "initial_watch_groups_present",
    "persistent_pressure_detected",
    "declining_concentration_detected",
)
ROW_REASON_CODES = (
    "group_persistent_pressure",
    "group_concentration_declining",
    "group_concentration_improving",
    "group_concentration_new",
    "group_concentration_resolved",
    "group_concentration_trend_clear",
)
GROUP_TYPE_PRIORITY = {"market": 0, "category": 1, "team": 2, "outcome_side": 3}
TREND_STATUS_PRIORITY = {
    "declining": 0,
    "new": 1,
    "unchanged": 2,
    "resolved": 3,
    "improving": 4,
}
STATUS_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class PositionConcentrationTrendMonitorConfig:
    config_version: str = DEFAULT_POSITION_CONCENTRATION_TREND_MONITOR_CONFIG_VERSION
    persistent_pressure_periods: int = 3
    watch_trend_rate: Decimal = Decimal("0.100000")
    blocked_trend_rate: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int(
            "persistent_pressure_periods",
            self.persistent_pressure_periods,
        )
        object.__setattr__(
            self,
            "watch_trend_rate",
            _normalize_nonnegative_rate("watch_trend_rate", self.watch_trend_rate),
        )
        object.__setattr__(
            self,
            "blocked_trend_rate",
            _normalize_nonnegative_rate("blocked_trend_rate", self.blocked_trend_rate),
        )
        if self.blocked_trend_rate < self.watch_trend_rate:
            raise ValueError("blocked_trend_rate must be >= watch_trend_rate")
        require_paper_only_flags("PositionConcentrationTrendMonitorConfig", self)


@dataclass(frozen=True)
class PositionConcentrationTrendRow:
    group_type: str
    group_value: str
    latest_position_count: Decimal
    latest_open_notional: Decimal
    latest_share_of_total_open_notional: Decimal | None
    threshold_share: Decimal | None
    share_delta: Decimal | None
    concentration_trend_rate: Decimal | None
    persistent_pressure_flag: bool
    trend_status: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.group_type not in GROUP_TYPES:
            raise ValueError("group_type must be a known concentration group type")
        _require_canonical_string("group_value", self.group_value)
        for field_name in ("latest_position_count", "latest_open_notional"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_share_of_total_open_notional",
            "threshold_share",
            "share_delta",
            "concentration_trend_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_rate(field_name, getattr(self, field_name)),
            )
        if type(self.persistent_pressure_flag) is not bool:
            raise ValueError("persistent_pressure_flag must be a bool")
        _require_member("trend_status", self.trend_status, TREND_STATUSES)
        _require_member("status", self.status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("position concentration trend row", self)
        require_paper_only_flags("PositionConcentrationTrendRow", self)


@dataclass(frozen=True)
class PositionConcentrationTrendMonitorReport:
    generated_at: datetime
    config_version: str
    source_snapshot_count: Decimal
    group_count: Decimal
    first_snapshot_generated_at: datetime | None
    latest_snapshot_generated_at: datetime | None
    latest_watch_count: Decimal
    watch_count_delta: Decimal
    watch_trend_rate: Decimal | None
    latest_max_share: Decimal | None
    max_share_delta: Decimal | None
    max_share_trend_rate: Decimal | None
    persistent_pressure_count: Decimal
    improving_count: Decimal
    declining_count: Decimal
    unchanged_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PositionConcentrationTrendRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_snapshot_count",
            "group_count",
            "latest_watch_count",
            "persistent_pressure_count",
            "improving_count",
            "declining_count",
            "unchanged_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "watch_count_delta",
            _normalize_count_delta("watch_count_delta", self.watch_count_delta),
        )
        object.__setattr__(
            self,
            "first_snapshot_generated_at",
            _as_optional_utc(
                "first_snapshot_generated_at",
                self.first_snapshot_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_snapshot_generated_at",
            _as_optional_utc(
                "latest_snapshot_generated_at",
                self.latest_snapshot_generated_at,
            ),
        )
        for field_name in (
            "watch_trend_rate",
            "latest_max_share",
            "max_share_delta",
            "max_share_trend_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_rate(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("position concentration trend report", self)
        require_paper_only_flags("PositionConcentrationTrendMonitorReport", self)


@dataclass(frozen=True)
class _GroupObservation:
    position_count: Decimal
    open_notional: Decimal
    share: Decimal | None
    threshold_share: Decimal
    concentration_status: str


def build_position_concentration_trend_monitor_report(
    snapshots: list[PaperPositionConcentrationGuardReport]
    | tuple[PaperPositionConcentrationGuardReport, ...],
    *,
    config: PositionConcentrationTrendMonitorConfig,
    generated_at: datetime,
) -> PositionConcentrationTrendMonitorReport:
    if type(config) is not PositionConcentrationTrendMonitorConfig:
        raise ValueError("config must be a PositionConcentrationTrendMonitorConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_snapshots = _chronological_snapshots(_normalize_snapshots(snapshots))
    for snapshot in source_snapshots:
        if snapshot.generated_at > generated_at_utc:
            raise ValueError("source snapshot generated_at must not be after generated_at")

    first_snapshot = source_snapshots[0] if source_snapshots else None
    first_comparison = source_snapshots[0] if len(source_snapshots) > 1 else None
    latest = source_snapshots[-1] if source_snapshots else None
    rows = _trend_rows(source_snapshots, config)
    reason_codes = _report_reason_codes(rows, first_comparison, latest, config)

    return PositionConcentrationTrendMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_snapshot_count=_count(len(source_snapshots)),
        group_count=_count(len(rows)),
        first_snapshot_generated_at=first_snapshot.generated_at if first_snapshot else None,
        latest_snapshot_generated_at=latest.generated_at if latest else None,
        latest_watch_count=_watch_count(latest),
        watch_count_delta=_watch_count_delta(first_comparison, latest),
        watch_trend_rate=_trend_rate(
            _watch_count(first_comparison),
            _watch_count(latest),
        ),
        latest_max_share=_max_share(latest),
        max_share_delta=_optional_delta(_max_share(first_comparison), _max_share(latest)),
        max_share_trend_rate=_trend_rate(
            _max_share(first_comparison),
            _max_share(latest),
        ),
        persistent_pressure_count=_count(
            sum(1 for row in rows if row.persistent_pressure_flag),
        ),
        improving_count=_count(
            sum(1 for row in rows if row.trend_status == "improving"),
        ),
        declining_count=_count(
            sum(1 for row in rows if row.trend_status == "declining"),
        ),
        unchanged_count=_count(
            sum(1 for row in rows if row.trend_status == "unchanged"),
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        rows=rows,
    )


def position_concentration_trend_monitor_payload(
    report: PositionConcentrationTrendMonitorReport,
) -> dict[str, Any]:
    if type(report) is not PositionConcentrationTrendMonitorReport:
        raise ValueError("report must be a PositionConcentrationTrendMonitorReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("position concentration trend monitor report", report)
    return json_ready_no_floats(report)


def _normalize_snapshots(
    value: list[PaperPositionConcentrationGuardReport]
    | tuple[PaperPositionConcentrationGuardReport, ...],
) -> tuple[PaperPositionConcentrationGuardReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    for snapshot in snapshots:
        if type(snapshot) is not PaperPositionConcentrationGuardReport:
            raise ValueError(
                "snapshots must contain PaperPositionConcentrationGuardReport values",
            )
        require_paper_only_flags("snapshot", snapshot)
    return snapshots


def _chronological_snapshots(
    snapshots: tuple[PaperPositionConcentrationGuardReport, ...],
) -> tuple[PaperPositionConcentrationGuardReport, ...]:
    indexed = tuple(
        (snapshot.generated_at, index, snapshot)
        for index, snapshot in enumerate(snapshots)
    )
    return tuple(snapshot for _generated_at, _index, snapshot in sorted(indexed))


def _trend_rows(
    snapshots: tuple[PaperPositionConcentrationGuardReport, ...],
    config: PositionConcentrationTrendMonitorConfig,
) -> tuple[PositionConcentrationTrendRow, ...]:
    if not snapshots:
        return ()
    first_by_group = _group_observations(snapshots[0]) if len(snapshots) > 1 else {}
    latest_by_group = _group_observations(snapshots[-1])
    group_keys = tuple(sorted(set(first_by_group) | set(latest_by_group)))
    rows = tuple(
        _trend_row(
            key,
            first_by_group.get(key),
            latest_by_group.get(key),
            snapshots,
            config,
        )
        for key in group_keys
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _trend_row(
    key: tuple[str, str],
    first: _GroupObservation | None,
    latest: _GroupObservation | None,
    snapshots: tuple[PaperPositionConcentrationGuardReport, ...],
    config: PositionConcentrationTrendMonitorConfig,
) -> PositionConcentrationTrendRow:
    latest_share = _observation_share(latest)
    first_share = _observation_share(first)
    trend_status = _trend_status(first_share, latest_share)
    persistent_pressure = _persistent_pressure_flag(key, snapshots, config)
    reason_codes = _row_reason_codes(trend_status, persistent_pressure)
    return PositionConcentrationTrendRow(
        group_type=key[0],
        group_value=REDACTED,
        latest_position_count=_observation_count(latest, "position_count"),
        latest_open_notional=_observation_count(latest, "open_notional"),
        latest_share_of_total_open_notional=latest_share,
        threshold_share=latest.threshold_share if latest else None,
        share_delta=_optional_delta(first_share, latest_share),
        concentration_trend_rate=_trend_rate(first_share, latest_share),
        persistent_pressure_flag=persistent_pressure,
        trend_status=trend_status,
        status=_row_status(trend_status, persistent_pressure),
        reason_codes=reason_codes,
    )


def _group_observations(
    snapshot: PaperPositionConcentrationGuardReport,
) -> dict[tuple[str, str], _GroupObservation]:
    return {
        (row.group_type, row.group_value): _observation_from_row(row)
        for row in snapshot.rows
    }


def _observation_from_row(row: PaperPositionConcentrationGuardRow) -> _GroupObservation:
    require_paper_only_flags("snapshot row", row)
    return _GroupObservation(
        position_count=_count(row.position_count),
        open_notional=row.open_notional,
        share=row.share_of_total_open_notional,
        threshold_share=row.threshold_share,
        concentration_status=row.concentration_status,
    )


def _row_reason_codes(
    trend_status: str,
    persistent_pressure: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if persistent_pressure:
        codes.append("group_persistent_pressure")
    if trend_status == "declining":
        codes.append("group_concentration_declining")
    elif trend_status == "improving":
        codes.append("group_concentration_improving")
    elif trend_status == "new":
        codes.append("group_concentration_new")
    elif trend_status == "resolved":
        codes.append("group_concentration_resolved")
    return tuple(codes) if codes else ("group_concentration_trend_clear",)


def _report_reason_codes(
    rows: tuple[PositionConcentrationTrendRow, ...],
    first: PaperPositionConcentrationGuardReport | None,
    latest: PaperPositionConcentrationGuardReport | None,
    config: PositionConcentrationTrendMonitorConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("position_concentration_trend_clear",)
    codes: list[str] = []
    latest_watch_count = _watch_count(latest)
    if first is None and latest_watch_count > ZERO_COUNT:
        codes.append("initial_watch_groups_present")
    _append_rate_reason(
        codes,
        _trend_rate(_watch_count(first), latest_watch_count),
        "watch_trend_rate",
        config,
    )
    _append_rate_reason(
        codes,
        _trend_rate(_max_share(first), _max_share(latest)),
        "max_share_trend_rate",
        config,
    )
    if any(row.persistent_pressure_flag for row in rows):
        codes.append("persistent_pressure_detected")
    if any(row.trend_status == "declining" for row in rows):
        codes.append("declining_concentration_detected")
    return _dedupe(codes) if codes else ("position_concentration_trend_clear",)


def _append_rate_reason(
    codes: list[str],
    rate: Decimal | None,
    prefix: str,
    config: PositionConcentrationTrendMonitorConfig,
) -> None:
    if rate is None or rate <= ZERO_RATE:
        return
    if rate >= config.blocked_trend_rate:
        codes.append(f"{prefix}_blocked")
    elif rate >= config.watch_trend_rate:
        codes.append(f"{prefix}_watch")


def _persistent_pressure_flag(
    key: tuple[str, str],
    snapshots: tuple[PaperPositionConcentrationGuardReport, ...],
    config: PositionConcentrationTrendMonitorConfig,
) -> bool:
    if len(snapshots) < config.persistent_pressure_periods:
        return False
    recent = snapshots[-config.persistent_pressure_periods :]
    for snapshot in recent:
        observation = _group_observations(snapshot).get(key)
        if observation is None or observation.concentration_status != "watch":
            return False
    return True


def _row_status(trend_status: str, persistent_pressure: bool) -> str:
    if persistent_pressure or trend_status == "declining":
        return "blocked"
    if trend_status == "new":
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if (
        "persistent_pressure_detected" in reason_codes
        or "declining_concentration_detected" in reason_codes
    ):
        return "blocked"
    if reason_codes == ("position_concentration_trend_clear",):
        return "pass"
    return "watch"


def _trend_status(first: Decimal | None, latest: Decimal | None) -> str:
    if first is None and latest is None:
        return "unchanged"
    if first is None:
        return "new"
    if latest is None:
        return "resolved"
    delta = latest - first
    if delta > ZERO_RATE:
        return "declining"
    if delta < ZERO_RATE:
        return "improving"
    return "unchanged"


def _watch_count(report: PaperPositionConcentrationGuardReport | None) -> Decimal:
    if report is None:
        return ZERO_COUNT
    return _count(report.watch_count)


def _watch_count_delta(
    first: PaperPositionConcentrationGuardReport | None,
    latest: PaperPositionConcentrationGuardReport | None,
) -> Decimal:
    return _normalize_count_delta(
        "watch_count_delta",
        _watch_count(latest) - _watch_count(first),
    )


def _max_share(report: PaperPositionConcentrationGuardReport | None) -> Decimal | None:
    if report is None:
        return None
    values = tuple(
        row.share_of_total_open_notional
        for row in report.rows
        if row.share_of_total_open_notional is not None
    )
    if not values:
        return None
    return max(values)


def _observation_count(observation: _GroupObservation | None, field_name: str) -> Decimal:
    if observation is None:
        return ZERO_COUNT
    return getattr(observation, field_name)


def _observation_share(observation: _GroupObservation | None) -> Decimal | None:
    if observation is None:
        return None
    return observation.share


def _optional_delta(first: Decimal | None, latest: Decimal | None) -> Decimal | None:
    if first is None or latest is None:
        return None
    return _normalize_optional_rate("delta", latest - first)


def _trend_rate(first: Decimal | None, latest: Decimal | None) -> Decimal | None:
    if first is None or latest is None:
        return None
    if first == ZERO_COUNT:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_rate((latest - first) / first)


def _row_sort_key(
    row: PositionConcentrationTrendRow,
) -> tuple[int, int, int, Decimal, str]:
    latest_share = (
        row.latest_share_of_total_open_notional
        if row.latest_share_of_total_open_notional is not None
        else Decimal("-1.000000")
    )
    return (
        STATUS_PRIORITY[row.status],
        TREND_STATUS_PRIORITY[row.trend_status],
        GROUP_TYPE_PRIORITY[row.group_type],
        -latest_share,
        row.group_value,
    )


def _normalize_rows(
    value: object,
) -> tuple[PositionConcentrationTrendRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not PositionConcentrationTrendRow:
            raise ValueError("rows must contain PositionConcentrationTrendRow values")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _validate_row(row: PositionConcentrationTrendRow) -> None:
    expected_status = _row_status(row.trend_status, row.persistent_pressure_flag)
    if row.status != expected_status:
        raise ValueError("status must match row trend pressure")
    expected_reasons = _row_reason_codes(
        row.trend_status,
        row.persistent_pressure_flag,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row trend pressure")
    if row.latest_share_of_total_open_notional is None:
        if row.latest_open_notional != ZERO_COUNT:
            raise ValueError("latest_share_of_total_open_notional needs total notional")
    if row.trend_status in ("new", "resolved") and row.concentration_trend_rate is not None:
        raise ValueError("new or resolved rows cannot include concentration_trend_rate")


def _validate_report(report: PositionConcentrationTrendMonitorReport) -> None:
    if report.group_count != _count(len(report.rows)):
        raise ValueError("group_count must equal rows length")
    if report.persistent_pressure_count != _count(
        sum(1 for row in report.rows if row.persistent_pressure_flag),
    ):
        raise ValueError("persistent_pressure_count must equal rows")
    if report.improving_count != _count(
        sum(1 for row in report.rows if row.trend_status == "improving"),
    ):
        raise ValueError("improving_count must equal rows")
    if report.declining_count != _count(
        sum(1 for row in report.rows if row.trend_status == "declining"),
    ):
        raise ValueError("declining_count must equal rows")
    if report.unchanged_count != _count(
        sum(1 for row in report.rows if row.trend_status == "unchanged"),
    ):
        raise ValueError("unchanged_count must equal rows")
    if report.source_snapshot_count == ZERO_COUNT:
        if report.rows:
            raise ValueError("empty source history cannot include rows")
        if report.status != "pass":
            raise ValueError("empty source history status must be pass")
        if report.reason_codes != ("position_concentration_trend_clear",):
            raise ValueError("empty source history reason_codes must be clear")
        if report.first_snapshot_generated_at is not None:
            raise ValueError("first_snapshot_generated_at must be empty")
        if report.latest_snapshot_generated_at is not None:
            raise ValueError("latest_snapshot_generated_at must be empty")


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_delta(field_name: str, value: object) -> Decimal:
    return _normalize_decimal(field_name, value, COUNT_QUANTUM)


def _normalize_nonnegative_rate(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATE_QUANTUM)
    if normalized < ZERO_RATE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_rate(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value, RATE_QUANTUM)


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _quantize_rate(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATE_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in allowed_values:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _dedupe(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be known")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = (
    "DEFAULT_POSITION_CONCENTRATION_TREND_MONITOR_CONFIG_VERSION",
    "PositionConcentrationTrendMonitorConfig",
    "PositionConcentrationTrendMonitorReport",
    "PositionConcentrationTrendRow",
    "build_position_concentration_trend_monitor_report",
    "position_concentration_trend_monitor_payload",
)
