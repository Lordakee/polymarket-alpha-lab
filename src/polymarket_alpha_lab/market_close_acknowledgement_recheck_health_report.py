"""Pure in-memory health report for market close acknowledgement rechecks."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any


DEFAULT_CONFIG_VERSION = "market_close_acknowledgement_recheck_health.v1"

HEALTH_STATUSES = ("empty", "healthy", "watch", "breach")
ROW_HEALTH_STATUSES = ("healthy", "watch", "breach")
REASON_CODES = (
    "empty_input",
    "close_time_lag_breach",
    "missing_ack_pressure_breach",
    "stale_recheck_age_breach",
    "recheck_missing",
    "close_time_lag_watch",
    "missing_ack_pressure_watch",
    "stale_recheck_age_watch",
)

_ZERO = Decimal("0")
_ONE = Decimal("1")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUS_SEVERITY = {"healthy": 0, "watch": 1, "breach": 2}
_ROW_SORT_SEVERITY = {"breach": 0, "watch": 1, "healthy": 2}
_UNSAFE_FIELD_NAME_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "mnemonic",
    "password",
    "private_key",
    "secret",
    "token",
    "wallet",
)
_SECRET_VALUE_MARKERS = (
    "api-key=",
    "api_key=",
    "apikey=",
    "authorization:",
    "bearer ",
    "credential=",
    "password=",
    "private-key=",
    "private_key=",
    "secret=",
    "token=",
    "wallet=",
    "-----begin ",
)
_SECRET_VALUE_PREFIXES = ("AKIA", "ASIA", "gho_", "ghp_", "github_pat_", "sk-", "xox")


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckHealthConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    close_lag_watch_seconds: Decimal = Decimal("900")
    close_lag_breach_seconds: Decimal = Decimal("3600")
    missing_ack_watch_count: Decimal = Decimal("1")
    missing_ack_breach_count: Decimal = Decimal("3")
    stale_recheck_watch_seconds: Decimal = Decimal("1800")
    stale_recheck_breach_seconds: Decimal = Decimal("7200")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "close_lag_watch_seconds",
            self.close_lag_watch_seconds,
        )
        _require_nonnegative_decimal(
            "close_lag_breach_seconds",
            self.close_lag_breach_seconds,
        )
        _require_nonnegative_count_decimal(
            "missing_ack_watch_count",
            self.missing_ack_watch_count,
        )
        _require_nonnegative_count_decimal(
            "missing_ack_breach_count",
            self.missing_ack_breach_count,
        )
        _require_nonnegative_decimal(
            "stale_recheck_watch_seconds",
            self.stale_recheck_watch_seconds,
        )
        _require_nonnegative_decimal(
            "stale_recheck_breach_seconds",
            self.stale_recheck_breach_seconds,
        )
        if self.close_lag_watch_seconds > self.close_lag_breach_seconds:
            raise ValueError("close_lag_watch_seconds must be <= close_lag_breach_seconds")
        if self.missing_ack_watch_count > self.missing_ack_breach_count:
            raise ValueError("missing_ack_watch_count must be <= missing_ack_breach_count")
        if self.stale_recheck_watch_seconds > self.stale_recheck_breach_seconds:
            raise ValueError(
                "stale_recheck_watch_seconds must be <= stale_recheck_breach_seconds",
            )
        _reject_unsafe_surface_fields("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckInputRow:
    market_slug: str
    closed_at: datetime
    acknowledged_at: datetime | None
    last_rechecked_at: datetime | None
    expected_ack_count: Decimal
    acknowledged_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        _require_nonnegative_count_decimal("expected_ack_count", self.expected_ack_count)
        _require_nonnegative_count_decimal("acknowledged_count", self.acknowledged_count)
        if self.acknowledged_count > self.expected_ack_count:
            raise ValueError("acknowledged_count must be <= expected_ack_count")
        if self.acknowledged_at is not None and self.acknowledged_at < self.closed_at:
            raise ValueError("acknowledged_at must not be before closed_at")
        _reject_unsafe_surface_fields("input row", self)
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckHealthRow:
    market_slug: str
    closed_at: datetime
    acknowledged_at: datetime | None
    last_rechecked_at: datetime | None
    expected_ack_count: Decimal
    acknowledged_count: Decimal
    missing_ack_count: Decimal
    missing_ack_ratio: Decimal | None
    close_time_lag_seconds: Decimal
    recheck_age_seconds: Decimal
    close_time_lag_status: str
    missing_ack_status: str
    stale_recheck_status: str
    health_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        for field_name in (
            "expected_ack_count",
            "acknowledged_count",
            "missing_ack_count",
        ):
            _require_nonnegative_count_decimal(field_name, getattr(self, field_name))
        _require_optional_ratio_decimal("missing_ack_ratio", self.missing_ack_ratio)
        _require_nonnegative_decimal(
            "close_time_lag_seconds",
            self.close_time_lag_seconds,
        )
        _require_nonnegative_decimal("recheck_age_seconds", self.recheck_age_seconds)
        _require_row_status("close_time_lag_status", self.close_time_lag_status)
        _require_row_status("missing_ack_status", self.missing_ack_status)
        _require_row_status("stale_recheck_status", self.stale_recheck_status)
        _require_row_status("health_status", self.health_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_health_row_consistency(self)
        _reject_unsafe_surface_fields("health row", self)
        _require_hard_flags("health row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    total_expected_ack_count: Decimal
    total_acknowledged_count: Decimal
    total_missing_ack_count: Decimal
    missing_ack_ratio: Decimal | None
    max_close_time_lag_seconds: Decimal | None
    max_recheck_age_seconds: Decimal | None
    rows: tuple[MarketCloseAcknowledgementRecheckHealthRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("status", self.status)
        for field_name in (
            "row_count",
            "total_expected_ack_count",
            "total_acknowledged_count",
            "total_missing_ack_count",
        ):
            _require_nonnegative_count_decimal(field_name, getattr(self, field_name))
        _require_optional_ratio_decimal("missing_ack_ratio", self.missing_ack_ratio)
        _require_optional_nonnegative_decimal(
            "max_close_time_lag_seconds",
            self.max_close_time_lag_seconds,
        )
        _require_optional_nonnegative_decimal(
            "max_recheck_age_seconds",
            self.max_recheck_age_seconds,
        )
        object.__setattr__(self, "rows", _normalize_health_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _reject_unsafe_surface_fields("report", self)
        _require_hard_flags("report", self)


def build_market_close_acknowledgement_recheck_health_report(
    rows: list[MarketCloseAcknowledgementRecheckInputRow]
    | tuple[MarketCloseAcknowledgementRecheckInputRow, ...],
    *,
    config: MarketCloseAcknowledgementRecheckHealthConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckHealthReport:
    if type(config) is not MarketCloseAcknowledgementRecheckHealthConfig:
        raise ValueError("config must be a MarketCloseAcknowledgementRecheckHealthConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    health_rows = tuple(
        _build_health_row(row, config=config, generated_at=generated_at_utc)
        for row in input_rows
    )
    ordered_rows = tuple(
        sorted(
            health_rows,
            key=lambda row: (_ROW_SORT_SEVERITY[row.health_status], row.market_slug),
        ),
    )
    total_expected_ack_count = sum(
        (row.expected_ack_count for row in ordered_rows),
        _ZERO,
    )
    total_acknowledged_count = sum(
        (row.acknowledged_count for row in ordered_rows),
        _ZERO,
    )
    total_missing_ack_count = sum(
        (row.missing_ack_count for row in ordered_rows),
        _ZERO,
    )
    reason_codes = _report_reason_codes(ordered_rows)
    status = _report_status(ordered_rows)

    return MarketCloseAcknowledgementRecheckHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        row_count=Decimal(len(ordered_rows)),
        total_expected_ack_count=total_expected_ack_count,
        total_acknowledged_count=total_acknowledged_count,
        total_missing_ack_count=total_missing_ack_count,
        missing_ack_ratio=_ratio(total_missing_ack_count, total_expected_ack_count),
        max_close_time_lag_seconds=_max_decimal(
            row.close_time_lag_seconds for row in ordered_rows
        ),
        max_recheck_age_seconds=_max_decimal(
            row.recheck_age_seconds for row in ordered_rows
        ),
        rows=ordered_rows,
        reason_codes=reason_codes,
    )


def market_close_acknowledgement_recheck_health_report_to_payload(
    report: MarketCloseAcknowledgementRecheckHealthReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckHealthReport:
        raise ValueError("report must be a MarketCloseAcknowledgementRecheckHealthReport")
    _require_hard_flags("report", report)
    return _json_ready(report)


def _build_health_row(
    row: MarketCloseAcknowledgementRecheckInputRow,
    *,
    config: MarketCloseAcknowledgementRecheckHealthConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckHealthRow:
    _require_not_after_generated_at("closed_at", row.closed_at, generated_at)
    _require_optional_not_after_generated_at(
        "acknowledged_at",
        row.acknowledged_at,
        generated_at,
    )
    _require_optional_not_after_generated_at(
        "last_rechecked_at",
        row.last_rechecked_at,
        generated_at,
    )
    close_lag_until = row.acknowledged_at or generated_at
    close_time_lag_seconds = _duration_seconds(
        "close_time_lag_seconds",
        close_lag_until - row.closed_at,
    )
    recheck_age_seconds = _duration_seconds(
        "recheck_age_seconds",
        generated_at - (row.last_rechecked_at or row.closed_at),
    )
    missing_ack_count = row.expected_ack_count - row.acknowledged_count
    close_time_lag_status = _threshold_status(
        close_time_lag_seconds,
        watch_threshold=config.close_lag_watch_seconds,
        breach_threshold=config.close_lag_breach_seconds,
    )
    missing_ack_status = _threshold_status(
        missing_ack_count,
        watch_threshold=config.missing_ack_watch_count,
        breach_threshold=config.missing_ack_breach_count,
    )
    stale_recheck_status = _threshold_status(
        recheck_age_seconds,
        watch_threshold=config.stale_recheck_watch_seconds,
        breach_threshold=config.stale_recheck_breach_seconds,
    )
    health_status = _max_status(
        close_time_lag_status,
        missing_ack_status,
        stale_recheck_status,
    )

    return MarketCloseAcknowledgementRecheckHealthRow(
        market_slug=row.market_slug,
        closed_at=row.closed_at,
        acknowledged_at=row.acknowledged_at,
        last_rechecked_at=row.last_rechecked_at,
        expected_ack_count=row.expected_ack_count,
        acknowledged_count=row.acknowledged_count,
        missing_ack_count=missing_ack_count,
        missing_ack_ratio=_ratio(missing_ack_count, row.expected_ack_count),
        close_time_lag_seconds=close_time_lag_seconds,
        recheck_age_seconds=recheck_age_seconds,
        close_time_lag_status=close_time_lag_status,
        missing_ack_status=missing_ack_status,
        stale_recheck_status=stale_recheck_status,
        health_status=health_status,
        reason_codes=_row_reason_codes(
            close_time_lag_status=close_time_lag_status,
            missing_ack_status=missing_ack_status,
            stale_recheck_status=stale_recheck_status,
            recheck_missing=row.last_rechecked_at is None,
        ),
    )


def _normalize_input_rows(
    rows: list[MarketCloseAcknowledgementRecheckInputRow]
    | tuple[MarketCloseAcknowledgementRecheckInputRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_market_slugs: set[str] = set()
    for row in normalized:
        if type(row) is not MarketCloseAcknowledgementRecheckInputRow:
            raise ValueError(
                "rows must contain MarketCloseAcknowledgementRecheckInputRow values",
            )
        _require_hard_flags("input row", row)
        if row.market_slug in seen_market_slugs:
            raise ValueError("rows must not contain duplicate market_slug values")
        seen_market_slugs.add(row.market_slug)
    return normalized


def _normalize_health_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckHealthRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckHealthRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketCloseAcknowledgementRecheckHealthRow:
            raise ValueError(
                "rows must contain MarketCloseAcknowledgementRecheckHealthRow values",
            )
        _require_hard_flags("health row", row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (_ROW_SORT_SEVERITY[row.health_status], row.market_slug),
        ),
    )


def _row_reason_codes(
    *,
    close_time_lag_status: str,
    missing_ack_status: str,
    stale_recheck_status: str,
    recheck_missing: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if close_time_lag_status == "breach":
        reason_codes.append("close_time_lag_breach")
    if missing_ack_status == "breach":
        reason_codes.append("missing_ack_pressure_breach")
    if stale_recheck_status == "breach":
        reason_codes.append("stale_recheck_age_breach")
    if recheck_missing:
        reason_codes.append("recheck_missing")
    if close_time_lag_status == "watch":
        reason_codes.append("close_time_lag_watch")
    if missing_ack_status == "watch":
        reason_codes.append("missing_ack_pressure_watch")
    if stale_recheck_status == "watch":
        reason_codes.append("stale_recheck_age_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _report_status(rows: tuple[MarketCloseAcknowledgementRecheckHealthRow, ...]) -> str:
    if not rows:
        return "empty"
    return _max_status(*(row.health_status for row in rows))


def _threshold_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    breach_threshold: Decimal,
) -> str:
    if value >= breach_threshold:
        return "breach"
    if value >= watch_threshold:
        return "watch"
    return "healthy"


def _max_status(*statuses: str) -> str:
    if not statuses:
        return "healthy"
    return max(statuses, key=lambda status: _STATUS_SEVERITY[status])


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == _ZERO:
        return None
    return numerator / denominator


def _max_decimal(values: Any) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return max(normalized)


def _duration_seconds(field_name: str, delta: timedelta) -> Decimal:
    value = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_not_after_generated_at(
    field_name: str,
    value: datetime,
    generated_at: datetime,
) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_optional_not_after_generated_at(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None:
        _require_not_after_generated_at(field_name, value, generated_at)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_report_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be a known health status")


def _require_row_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be a known row health status")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")


def _require_optional_ratio_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must be <= 1")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must contain unique reason codes")
    expected_order = tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)
    if normalized != expected_order:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _reject_unsafe_surface_fields(context: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_surface_field(context, field.name, getattr(value, field.name))


def _reject_unsafe_surface_field(context: str, field_name: str, value: object) -> None:
    normalized_field_name = field_name.lower()
    if any(part in normalized_field_name for part in _UNSAFE_FIELD_NAME_PARTS):
        raise ValueError(f"{context} must not expose unsafe field names")
    if value is None or isinstance(value, bool | Decimal | datetime):
        return
    if isinstance(value, str):
        normalized_value = value.lower()
        if any(marker in normalized_value for marker in _SECRET_VALUE_MARKERS):
            raise ValueError(f"{field_name} must not contain secret-like material")
        if value.startswith(_SECRET_VALUE_PREFIXES):
            raise ValueError(f"{field_name} must not contain secret-like material")
        return
    if isinstance(value, tuple | list):
        for item in value:
            _reject_unsafe_surface_field(context, field_name, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_surface_fields(context, value)


def _validate_health_row_consistency(
    row: MarketCloseAcknowledgementRecheckHealthRow,
) -> None:
    if row.acknowledged_count > row.expected_ack_count:
        raise ValueError("acknowledged_count must be <= expected_ack_count")
    if row.expected_ack_count - row.acknowledged_count != row.missing_ack_count:
        raise ValueError("missing_ack_count must equal expected minus acknowledged")
    if _ratio(row.missing_ack_count, row.expected_ack_count) != row.missing_ack_ratio:
        raise ValueError("missing_ack_ratio must match missing_ack_count")
    expected_health_status = _max_status(
        row.close_time_lag_status,
        row.missing_ack_status,
        row.stale_recheck_status,
    )
    if row.health_status != expected_health_status:
        raise ValueError("health_status must match row status severity")
    if row.reason_codes != _row_reason_codes(
        close_time_lag_status=row.close_time_lag_status,
        missing_ack_status=row.missing_ack_status,
        stale_recheck_status=row.stale_recheck_status,
        recheck_missing=row.last_rechecked_at is None,
    ):
        raise ValueError("reason_codes must match row status fields")


def _validate_report_consistency(
    report: MarketCloseAcknowledgementRecheckHealthReport,
) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must equal rows length")
    if report.total_expected_ack_count != sum(
        (row.expected_ack_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("total_expected_ack_count must equal rows total")
    if report.total_acknowledged_count != sum(
        (row.acknowledged_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("total_acknowledged_count must equal rows total")
    if report.total_missing_ack_count != sum(
        (row.missing_ack_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("total_missing_ack_count must equal rows total")
    expected_ratio = _ratio(report.total_missing_ack_count, report.total_expected_ack_count)
    if report.missing_ack_ratio != expected_ratio:
        raise ValueError("missing_ack_ratio must match missing ack totals")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match row severities")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.rows:
        if report.max_close_time_lag_seconds != max(
            row.close_time_lag_seconds for row in report.rows
        ):
            raise ValueError("max_close_time_lag_seconds must match rows")
        if report.max_recheck_age_seconds != max(
            row.recheck_age_seconds for row in report.rows
        ):
            raise ValueError("max_recheck_age_seconds must match rows")
    else:
        if report.max_close_time_lag_seconds is not None:
            raise ValueError("max_close_time_lag_seconds must be absent without rows")
        if report.max_recheck_age_seconds is not None:
            raise ValueError("max_recheck_age_seconds must be absent without rows")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "HEALTH_STATUSES",
    "REASON_CODES",
    "ROW_HEALTH_STATUSES",
    "MarketCloseAcknowledgementRecheckHealthConfig",
    "MarketCloseAcknowledgementRecheckHealthReport",
    "MarketCloseAcknowledgementRecheckHealthRow",
    "MarketCloseAcknowledgementRecheckInputRow",
    "build_market_close_acknowledgement_recheck_health_report",
    "market_close_acknowledgement_recheck_health_report_to_payload",
)
