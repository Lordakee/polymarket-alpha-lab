"""Pure trend reducer for supplied liquidity capacity alert snapshots."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.liquidity_rotation_capacity_alerts import (
    ALERT_STATUSES,
    LiquidityRotationCapacityAlertsReport,
)
from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_LIQUIDITY_CAPACITY_ALERT_TREND_MONITOR_CONFIG_VERSION = (
    "liquidity-capacity-alert-trend-monitor-v0"
)
ALERT_TREND_STATUSES = ("pass", "watch", "blocked")
ALERT_SEVERITY_TRENDS = ("improving", "flat", "declining")
PRESSURE_STATUSES = ("clear", "pressured")
VALIDATION_DIGEST_ALGORITHM = "liquidity-capacity-alert-trend-monitor-v0-sha256"
HEX_DIGITS = frozenset("0123456789abcdef")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ALERT_SEVERITY_SCORE = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("2.000000"),
}
REASON_CODES = (
    "missing_liquidity_capacity_alert_snapshots",
    "latest_liquidity_capacity_alert_watch",
    "latest_liquidity_capacity_alert_blocked",
    "capacity_pressure_persistent",
    "liquidity_capacity_alert_trend_improving",
    "liquidity_capacity_alert_trend_declining",
    "liquidity_capacity_alert_trend_flat",
)


@dataclass(frozen=True)
class LiquidityCapacityAlertTrendMonitorConfig:
    config_version: str = DEFAULT_LIQUIDITY_CAPACITY_ALERT_TREND_MONITOR_CONFIG_VERSION
    persistent_pressure_window_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "persistent_pressure_window_count",
            _normalize_positive_count(
                "persistent_pressure_window_count",
                self.persistent_pressure_window_count,
            ),
        )
        require_paper_only_flags("LiquidityCapacityAlertTrendMonitorConfig", self)


@dataclass(frozen=True)
class LiquidityCapacityAlertTrendMonitorRow:
    snapshot_generated_at: datetime
    alert_status: str
    alert_severity_score: Decimal
    severity_delta_from_previous: Decimal
    pressure_status: str
    pass_alert_count: Decimal
    watch_alert_count: Decimal
    blocked_alert_count: Decimal
    source_missing_count: Decimal
    alert_row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_generated_at",
            _as_utc("snapshot_generated_at", self.snapshot_generated_at),
        )
        _require_member("alert_status", self.alert_status, ALERT_STATUSES)
        for field_name in (
            "alert_severity_score",
            "severity_delta_from_previous",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        for field_name in (
            "pass_alert_count",
            "watch_alert_count",
            "blocked_alert_count",
            "source_missing_count",
            "alert_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_row(self)
        require_paper_only_flags("LiquidityCapacityAlertTrendMonitorRow", self)


@dataclass(frozen=True)
class LiquidityCapacityAlertTrendMonitorReport:
    generated_at: datetime
    config_version: str
    source_snapshot_count: Decimal
    observed_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    first_snapshot_generated_at: datetime | None
    latest_snapshot_generated_at: datetime | None
    latest_alert_status: str | None
    first_alert_severity_score: Decimal
    latest_alert_severity_score: Decimal
    alert_severity_delta: Decimal
    alert_severity_trend: str
    persistent_capacity_pressure: bool
    latest_source_missing_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[LiquidityCapacityAlertTrendMonitorRow, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_snapshot_count",
            "observed_snapshot_count",
            "blocked_snapshot_count",
            "latest_source_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "first_snapshot_generated_at",
            "latest_snapshot_generated_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_alert_status",
            _normalize_optional_alert_status("latest_alert_status", self.latest_alert_status),
        )
        for field_name in (
            "first_alert_severity_score",
            "latest_alert_severity_score",
            "alert_severity_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("alert_severity_trend", self.alert_severity_trend, ALERT_SEVERITY_TRENDS)
        if type(self.persistent_capacity_pressure) is not bool:
            raise ValueError("persistent_capacity_pressure must be a bool")
        _require_member("status", self.status, ALERT_TREND_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("LiquidityCapacityAlertTrendMonitorReport", self)
        _reject_unsafe_public_payload(
            "liquidity capacity alert trend monitor report",
            self,
        )
        if self.validation_digest == "":
            object.__setattr__(
                self,
                "validation_digest",
                _report_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "validation_digest",
                _normalize_validation_digest(
                    "validation_digest",
                    self.validation_digest,
                ),
            )
        _validate_report_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return _payload_from_report(self)


def build_liquidity_capacity_alert_trend_monitor_report(
    snapshots: Iterable[LiquidityRotationCapacityAlertsReport],
    *,
    config: LiquidityCapacityAlertTrendMonitorConfig,
    generated_at: datetime,
) -> LiquidityCapacityAlertTrendMonitorReport:
    if type(config) is not LiquidityCapacityAlertTrendMonitorConfig:
        raise ValueError("config must be a LiquidityCapacityAlertTrendMonitorConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_snapshots = _normalize_snapshots(snapshots)
    rows = _rows_from_snapshots(source_snapshots)
    first_row = rows[0] if rows else None
    latest_row = rows[-1] if rows else None
    first_score = first_row.alert_severity_score if first_row is not None else ZERO_RATIO
    latest_score = latest_row.alert_severity_score if latest_row is not None else ZERO_RATIO
    severity_delta = _quantize_decimal(latest_score - first_score)
    severity_trend = _severity_trend(severity_delta)
    persistent_pressure = _persistent_pressure(rows, config.persistent_pressure_window_count)
    status = _status(latest_row=latest_row, missing_snapshots=not rows)

    return LiquidityCapacityAlertTrendMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_snapshot_count=_count(len(source_snapshots)),
        observed_snapshot_count=_count(len(rows)),
        blocked_snapshot_count=_count(
            sum(1 for snapshot in source_snapshots if snapshot.status == "blocked"),
        ),
        first_snapshot_generated_at=(
            first_row.snapshot_generated_at if first_row is not None else None
        ),
        latest_snapshot_generated_at=(
            latest_row.snapshot_generated_at if latest_row is not None else None
        ),
        latest_alert_status=latest_row.alert_status if latest_row is not None else None,
        first_alert_severity_score=first_score,
        latest_alert_severity_score=latest_score,
        alert_severity_delta=severity_delta,
        alert_severity_trend=severity_trend,
        persistent_capacity_pressure=persistent_pressure,
        latest_source_missing_count=(
            latest_row.source_missing_count if latest_row is not None else ZERO_COUNT
        ),
        status=status,
        reason_codes=_reason_codes(
            status=status,
            missing_snapshots=not rows,
            persistent_pressure=persistent_pressure,
            severity_trend=severity_trend,
        ),
        rows=rows,
    )


def liquidity_capacity_alert_trend_monitor_payload(
    report: LiquidityCapacityAlertTrendMonitorReport,
) -> dict[str, object]:
    if type(report) is not LiquidityCapacityAlertTrendMonitorReport:
        raise ValueError("report must be a LiquidityCapacityAlertTrendMonitorReport")
    return _payload_from_report(report)


def _rows_from_snapshots(
    snapshots: tuple[LiquidityRotationCapacityAlertsReport, ...],
) -> tuple[LiquidityCapacityAlertTrendMonitorRow, ...]:
    rows: list[LiquidityCapacityAlertTrendMonitorRow] = []
    previous_score = ZERO_RATIO
    for snapshot in sorted(snapshots, key=lambda item: item.generated_at):
        severity_score = ALERT_SEVERITY_SCORE[snapshot.status]
        rows.append(
            LiquidityCapacityAlertTrendMonitorRow(
                snapshot_generated_at=snapshot.generated_at,
                alert_status=snapshot.status,
                alert_severity_score=severity_score,
                severity_delta_from_previous=_quantize_decimal(severity_score - previous_score),
                pressure_status=(
                    "pressured"
                    if snapshot.status != "pass" or snapshot.source_missing_count > ZERO_COUNT
                    else "clear"
                ),
                pass_alert_count=snapshot.pass_alert_count,
                watch_alert_count=snapshot.watch_alert_count,
                blocked_alert_count=snapshot.blocked_alert_count,
                source_missing_count=snapshot.source_missing_count,
                alert_row_count=snapshot.alert_row_count,
            ),
        )
        previous_score = severity_score
    return tuple(rows)


def _normalize_snapshots(
    snapshots: Iterable[LiquidityRotationCapacityAlertsReport],
) -> tuple[LiquidityRotationCapacityAlertsReport, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        normalized = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    for snapshot in normalized:
        if type(snapshot) is not LiquidityRotationCapacityAlertsReport:
            raise ValueError(
                "snapshots must contain LiquidityRotationCapacityAlertsReport values",
            )
        require_paper_only_flags("snapshot", snapshot)
    return normalized


def _persistent_pressure(
    rows: tuple[LiquidityCapacityAlertTrendMonitorRow, ...],
    window_count: Decimal,
) -> bool:
    required_count = int(window_count)
    if len(rows) < required_count:
        return False
    return all(row.pressure_status == "pressured" for row in rows[-required_count:])


def _status(
    *,
    latest_row: LiquidityCapacityAlertTrendMonitorRow | None,
    missing_snapshots: bool,
) -> str:
    if missing_snapshots or latest_row is None:
        return "blocked"
    return latest_row.alert_status


def _reason_codes(
    *,
    status: str,
    missing_snapshots: bool,
    persistent_pressure: bool,
    severity_trend: str,
) -> tuple[str, ...]:
    if missing_snapshots:
        return ("missing_liquidity_capacity_alert_snapshots",)
    codes: list[str] = []
    if status == "watch":
        codes.append("latest_liquidity_capacity_alert_watch")
    elif status == "blocked":
        codes.append("latest_liquidity_capacity_alert_blocked")
    if persistent_pressure:
        codes.append("capacity_pressure_persistent")
    if severity_trend == "improving":
        codes.append("liquidity_capacity_alert_trend_improving")
    elif severity_trend == "declining":
        codes.append("liquidity_capacity_alert_trend_declining")
    if not codes:
        codes.append("liquidity_capacity_alert_trend_flat")
    return _normalize_reason_codes(tuple(codes))


def _severity_trend(value: Decimal) -> str:
    if value < ZERO_RATIO:
        return "improving"
    if value > ZERO_RATIO:
        return "declining"
    return "flat"


def _validate_row(row: LiquidityCapacityAlertTrendMonitorRow) -> None:
    if row.alert_severity_score != ALERT_SEVERITY_SCORE[row.alert_status]:
        raise ValueError("alert_severity_score must match alert_status")
    expected_pressure_status = (
        "pressured"
        if row.alert_status != "pass" or row.source_missing_count > ZERO_COUNT
        else "clear"
    )
    if row.pressure_status != expected_pressure_status:
        raise ValueError("pressure_status must match alert status and source missing count")
    if (
        row.pass_alert_count + row.watch_alert_count + row.blocked_alert_count
        != row.alert_row_count
    ):
        raise ValueError("alert counts must sum to alert_row_count")


def _validate_report(report: LiquidityCapacityAlertTrendMonitorReport) -> None:
    if report.observed_snapshot_count != _count(len(report.rows)):
        raise ValueError("observed_snapshot_count must match rows")
    if report.source_snapshot_count != report.observed_snapshot_count:
        raise ValueError("source_snapshot_count must match observed_snapshot_count")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.snapshot_generated_at)):
        raise ValueError("rows must be chronological")
    if not report.rows:
        if report.first_snapshot_generated_at is not None:
            raise ValueError("first_snapshot_generated_at must be absent without rows")
        if report.latest_snapshot_generated_at is not None:
            raise ValueError("latest_snapshot_generated_at must be absent without rows")
        if report.latest_alert_status is not None:
            raise ValueError("latest_alert_status must be absent without rows")
    else:
        if report.first_snapshot_generated_at != report.rows[0].snapshot_generated_at:
            raise ValueError("first_snapshot_generated_at must match rows")
        if report.latest_snapshot_generated_at != report.rows[-1].snapshot_generated_at:
            raise ValueError("latest_snapshot_generated_at must match rows")
        if report.latest_alert_status != report.rows[-1].alert_status:
            raise ValueError("latest_alert_status must match rows")
    if report.alert_severity_delta != _quantize_decimal(
        report.latest_alert_severity_score - report.first_alert_severity_score,
    ):
        raise ValueError("alert_severity_delta must match first and latest scores")
    if report.alert_severity_trend != _severity_trend(report.alert_severity_delta):
        raise ValueError("alert_severity_trend must match alert_severity_delta")
    if report.status != _status(
        latest_row=report.rows[-1] if report.rows else None,
        missing_snapshots=not report.rows,
    ):
        raise ValueError("status must match latest row")
    if report.reason_codes != _reason_codes(
        status=report.status,
        missing_snapshots=not report.rows,
        persistent_pressure=report.persistent_capacity_pressure,
        severity_trend=report.alert_severity_trend,
    ):
        raise ValueError("reason_codes must match report state")


def _validate_report_digest(report: LiquidityCapacityAlertTrendMonitorReport) -> None:
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest must match report")


def _payload_from_report(
    report: LiquidityCapacityAlertTrendMonitorReport,
) -> dict[str, object]:
    _validate_report(report)
    require_paper_only_flags("report", report)
    _reject_unsafe_public_payload(
        "liquidity capacity alert trend monitor report",
        report,
    )
    _validate_report_digest(report)
    payload = json_ready_no_floats(report)
    _reject_unsafe_public_payload(
        "liquidity capacity alert trend monitor payload",
        payload,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _report_validation_digest(
    report: LiquidityCapacityAlertTrendMonitorReport,
) -> str:
    return _validation_digest(_report_digest_values(report))


def _report_digest_values(
    report: LiquidityCapacityAlertTrendMonitorReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("validation_digest", None)
    return values


def _validation_digest(values: dict[str, object]) -> str:
    payload = json_ready_no_floats(
        {
            "algorithm": VALIDATION_DIGEST_ALGORITHM,
            "values": values,
        },
    )
    rendered = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _normalize_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_public_values(label, json_ready_no_floats(value))


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe payload value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_values(label, item)
        return


def _normalize_rows(
    value: Iterable[LiquidityCapacityAlertTrendMonitorRow],
) -> tuple[LiquidityCapacityAlertTrendMonitorRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not LiquidityCapacityAlertTrendMonitorRow:
            raise ValueError("rows must contain LiquidityCapacityAlertTrendMonitorRow values")
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    for code in codes:
        _require_member("reason_codes", code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_optional_alert_status(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_member(field_name, value, ALERT_STATUSES)
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_LIQUIDITY_CAPACITY_ALERT_TREND_MONITOR_CONFIG_VERSION",
    "ALERT_TREND_STATUSES",
    "ALERT_SEVERITY_TRENDS",
    "PRESSURE_STATUSES",
    "LiquidityCapacityAlertTrendMonitorConfig",
    "LiquidityCapacityAlertTrendMonitorRow",
    "LiquidityCapacityAlertTrendMonitorReport",
    "build_liquidity_capacity_alert_trend_monitor_report",
    "liquidity_capacity_alert_trend_monitor_payload",
)
