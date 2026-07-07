"""Pure read-only reducer for concentration response queues."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.position_concentration_trend_monitor import (
    PositionConcentrationTrendRow,
)
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONCENTRATION_RESPONSE_QUEUE_CONFIG_VERSION = "concentration-response-queue-v0"
BOUNDARY_STATEMENT = (
    "Report-only concentration response queue; no guidance or execution instructions."
)
REDACTED = "[REDACTED]"
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
REPORT_STATUSES = ("pass", "watch", "blocked")
SOURCE_TREND_STATUSES = ("improving", "unchanged", "declining", "new", "resolved")
SOURCE_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = (
    "persistent_concentration_pressure",
    "worsening_concentration",
    "improving_concentration",
    "stale_review",
    "normal",
)
REASON_CODES = (
    "no_concentration_trend_rows_supplied",
    "persistent_concentration_pressure_present",
    "worsening_concentration_present",
    "improving_concentration_observed",
    "stale_concentration_review_present",
    "normal_concentration_observed",
)
ROW_STATUS_WEIGHT = {
    "persistent_concentration_pressure": 0,
    "worsening_concentration": 1,
    "improving_concentration": 2,
    "stale_review": 3,
    "normal": 4,
}


@dataclass(frozen=True)
class ConcentrationResponseQueueConfig:
    config_version: str = DEFAULT_CONCENTRATION_RESPONSE_QUEUE_CONFIG_VERSION
    stale_review_seconds: Decimal = Decimal("172800.000000")
    last_reviewed_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_review_seconds",
            _normalize_positive_decimal("stale_review_seconds", self.stale_review_seconds),
        )
        object.__setattr__(
            self,
            "last_reviewed_at",
            _as_optional_utc("last_reviewed_at", self.last_reviewed_at),
        )
        require_paper_only_flags("ConcentrationResponseQueueConfig", self)


@dataclass(frozen=True)
class ConcentrationResponseQueueRow:
    group_type: str
    group_value: str
    response_queue_status: str
    source_trend_status: str
    source_status: str
    latest_position_count: Decimal
    latest_open_notional: Decimal
    latest_share_of_total_open_notional: Decimal | None
    threshold_share: Decimal | None
    share_delta: Decimal | None
    concentration_trend_rate: Decimal | None
    persistent_pressure_flag: bool
    review_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("group_type", self.group_type)
        _require_canonical_string("group_value", self.group_value)
        if self.group_value != REDACTED:
            raise ValueError("group_value must be redacted before queue payload")
        _require_member("response_queue_status", self.response_queue_status, ROW_STATUSES)
        _require_member("source_trend_status", self.source_trend_status, SOURCE_TREND_STATUSES)
        _require_member("source_status", self.source_status, SOURCE_STATUSES)
        object.__setattr__(
            self,
            "latest_position_count",
            _normalize_nonnegative_decimal("latest_position_count", self.latest_position_count),
        )
        object.__setattr__(
            self,
            "latest_open_notional",
            _normalize_nonnegative_decimal("latest_open_notional", self.latest_open_notional),
        )
        for field_name in (
            "latest_share_of_total_open_notional",
            "threshold_share",
            "share_delta",
            "concentration_trend_rate",
            "review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.persistent_pressure_flag) is not bool:
            raise ValueError("persistent_pressure_flag must be a bool")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields("concentration response queue row", self)
        require_paper_only_flags("ConcentrationResponseQueueRow", self)
        _validate_row(self)


@dataclass(frozen=True)
class ConcentrationResponseQueueReport:
    generated_at: datetime
    config_version: str
    response_queue_status: str
    source_row_count: Decimal
    row_count: Decimal
    persistent_pressure_count: Decimal
    worsening_concentration_count: Decimal
    improving_concentration_count: Decimal
    stale_review_count: Decimal
    normal_count: Decimal
    max_latest_share_of_total_open_notional: Decimal | None
    max_review_age_seconds: Decimal | None
    rows: tuple[ConcentrationResponseQueueRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("response_queue_status", self.response_queue_status, REPORT_STATUSES)
        for field_name in (
            "source_row_count",
            "row_count",
            "persistent_pressure_count",
            "worsening_concentration_count",
            "improving_concentration_count",
            "stale_review_count",
            "normal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_share_of_total_open_notional",
            _normalize_optional_decimal(
                "max_latest_share_of_total_open_notional",
                self.max_latest_share_of_total_open_notional,
            ),
        )
        object.__setattr__(
            self,
            "max_review_age_seconds",
            _normalize_optional_decimal("max_review_age_seconds", self.max_review_age_seconds),
        )
        object.__setattr__(self, "rows", _normalize_queue_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match report-only scope")
        reject_unsafe_surface_fields("concentration response queue report", self)
        require_paper_only_flags("ConcentrationResponseQueueReport", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_concentration_response_queue_report(
    rows: list[PositionConcentrationTrendRow] | tuple[PositionConcentrationTrendRow, ...],
    *,
    config: ConcentrationResponseQueueConfig,
    generated_at: datetime,
) -> ConcentrationResponseQueueReport:
    if type(config) is not ConcentrationResponseQueueConfig:
        raise ValueError("config must be a ConcentrationResponseQueueConfig")
    require_paper_only_flags("ConcentrationResponseQueueConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if config.last_reviewed_at is not None and config.last_reviewed_at > generated_at_utc:
        raise ValueError("last_reviewed_at must not be after generated_at")
    source_rows = _normalize_source_rows(rows)
    review_age = _review_age_seconds(generated_at_utc, config.last_reviewed_at)
    queue_rows = tuple(
        sorted(
            (_queue_row(source_row, review_age, config) for source_row in source_rows),
            key=_queue_row_sort_key,
        ),
    )
    source_row_count = _count(len(source_rows))
    reason_codes = _report_reason_codes(queue_rows, source_row_count)
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "response_queue_status": _report_status(reason_codes),
        "source_row_count": source_row_count,
        "row_count": _count(len(queue_rows)),
        "persistent_pressure_count": _status_count(
            queue_rows,
            "persistent_concentration_pressure",
        ),
        "worsening_concentration_count": _status_count(queue_rows, "worsening_concentration"),
        "improving_concentration_count": _status_count(queue_rows, "improving_concentration"),
        "stale_review_count": _status_count(queue_rows, "stale_review"),
        "normal_count": _status_count(queue_rows, "normal"),
        "max_latest_share_of_total_open_notional": _max_optional_decimal(
            tuple(
                row.latest_share_of_total_open_notional
                for row in queue_rows
                if row.latest_share_of_total_open_notional is not None
            ),
        ),
        "max_review_age_seconds": _max_optional_decimal(
            tuple(row.review_age_seconds for row in queue_rows if row.review_age_seconds is not None),
        ),
        "rows": queue_rows,
        "reason_codes": reason_codes,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ConcentrationResponseQueueReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def concentration_response_queue_payload(
    report: ConcentrationResponseQueueReport,
) -> dict[str, Any]:
    if type(report) is not ConcentrationResponseQueueReport:
        raise ValueError("report must be a ConcentrationResponseQueueReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("concentration response queue report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("concentration response queue payload", payload)
    return payload


def _normalize_source_rows(
    value: object,
) -> tuple[PositionConcentrationTrendRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[PositionConcentrationTrendRow] = set()
    for row in rows:
        if type(row) is not PositionConcentrationTrendRow:
            raise ValueError("rows must contain PositionConcentrationTrendRow values")
        require_paper_only_flags("PositionConcentrationTrendRow", row)
        if row.group_value != REDACTED:
            raise ValueError("group_value must be redacted before queue payload")
        if row in seen:
            raise ValueError("rows must be unique")
        seen.add(row)
    return rows


def _queue_row(
    source_row: PositionConcentrationTrendRow,
    review_age_seconds: Decimal | None,
    config: ConcentrationResponseQueueConfig,
) -> ConcentrationResponseQueueRow:
    status = _row_status(source_row, review_age_seconds, config)
    return ConcentrationResponseQueueRow(
        group_type=source_row.group_type,
        group_value=source_row.group_value,
        response_queue_status=status,
        source_trend_status=source_row.trend_status,
        source_status=source_row.status,
        latest_position_count=source_row.latest_position_count,
        latest_open_notional=source_row.latest_open_notional,
        latest_share_of_total_open_notional=source_row.latest_share_of_total_open_notional,
        threshold_share=source_row.threshold_share,
        share_delta=source_row.share_delta,
        concentration_trend_rate=source_row.concentration_trend_rate,
        persistent_pressure_flag=source_row.persistent_pressure_flag,
        review_age_seconds=review_age_seconds,
        reason_codes=_row_reason_codes(status),
    )


def _row_status(
    row: PositionConcentrationTrendRow,
    review_age_seconds: Decimal | None,
    config: ConcentrationResponseQueueConfig,
) -> str:
    if row.persistent_pressure_flag:
        return "persistent_concentration_pressure"
    if row.trend_status == "declining":
        return "worsening_concentration"
    if row.trend_status == "improving":
        return "improving_concentration"
    if (
        review_age_seconds is not None
        and review_age_seconds >= config.stale_review_seconds
        and row.latest_share_of_total_open_notional is not None
        and row.threshold_share is not None
        and row.latest_share_of_total_open_notional >= row.threshold_share
    ):
        return "stale_review"
    return "normal"


def _row_reason_codes(status: str) -> tuple[str, ...]:
    if status == "persistent_concentration_pressure":
        return ("persistent_concentration_pressure_present",)
    if status == "worsening_concentration":
        return ("worsening_concentration_present",)
    if status == "improving_concentration":
        return ("improving_concentration_observed",)
    if status == "stale_review":
        return ("stale_concentration_review_present",)
    return ("normal_concentration_observed",)


def _report_reason_codes(
    rows: tuple[ConcentrationResponseQueueRow, ...],
    source_row_count: Decimal,
) -> tuple[str, ...]:
    if source_row_count == ZERO:
        return ("no_concentration_trend_rows_supplied",)
    codes: list[str] = []
    for reason_code in (
        "persistent_concentration_pressure_present",
        "worsening_concentration_present",
        "improving_concentration_observed",
        "stale_concentration_review_present",
        "normal_concentration_observed",
    ):
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return tuple(codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "persistent_concentration_pressure_present" in reason_codes
        or "worsening_concentration_present" in reason_codes
    ):
        return "blocked"
    if (
        "improving_concentration_observed" in reason_codes
        or "stale_concentration_review_present" in reason_codes
    ):
        return "watch"
    return "pass"


def _queue_row_sort_key(
    row: ConcentrationResponseQueueRow,
) -> tuple[
    int,
    Decimal,
    Decimal,
    str,
    str,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    str,
    bool,
]:
    return (
        ROW_STATUS_WEIGHT[row.response_queue_status],
        -(row.latest_share_of_total_open_notional or ZERO),
        -abs(row.concentration_trend_rate or ZERO),
        row.group_type,
        row.group_value,
        -row.latest_open_notional,
        -row.latest_position_count,
        -(row.threshold_share or ZERO),
        -(row.share_delta or ZERO),
        -(row.review_age_seconds or ZERO),
        row.source_trend_status,
        row.source_status,
        row.persistent_pressure_flag,
    )


def _status_count(
    rows: tuple[ConcentrationResponseQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.response_queue_status == status))


def _review_age_seconds(
    generated_at: datetime,
    last_reviewed_at: datetime | None,
) -> Decimal | None:
    if last_reviewed_at is None:
        return None
    seconds = Decimal(str((generated_at - last_reviewed_at).total_seconds()))
    return _normalize_nonnegative_decimal("review_age_seconds", seconds)


def _max_optional_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return max(values)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_queue_rows(
    value: object,
) -> tuple[ConcentrationResponseQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[ConcentrationResponseQueueRow] = set()
    for row in rows:
        if type(row) is not ConcentrationResponseQueueRow:
            raise ValueError("rows must contain ConcentrationResponseQueueRow values")
        require_paper_only_flags("ConcentrationResponseQueueRow", row)
        if row in seen:
            raise ValueError("rows must be unique")
        seen.add(row)
    if rows != tuple(sorted(rows, key=_queue_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_row(row: ConcentrationResponseQueueRow) -> None:
    if row.reason_codes != _row_reason_codes(row.response_queue_status):
        raise ValueError("reason_codes must match response_queue_status")
    if row.response_queue_status == "persistent_concentration_pressure":
        if row.persistent_pressure_flag is not True:
            raise ValueError("persistent pressure status requires persistent flag")
    if row.response_queue_status == "worsening_concentration":
        if row.source_trend_status != "declining":
            raise ValueError("worsening status requires declining source trend")
    if row.response_queue_status == "improving_concentration":
        if row.source_trend_status != "improving":
            raise ValueError("improving status requires improving source trend")
    if row.review_age_seconds is not None and row.review_age_seconds < ZERO:
        raise ValueError("review_age_seconds must be nonnegative")


def _validate_report(report: ConcentrationResponseQueueReport) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.persistent_pressure_count != _status_count(
        report.rows,
        "persistent_concentration_pressure",
    ):
        raise ValueError("persistent_pressure_count must match rows")
    if report.worsening_concentration_count != _status_count(
        report.rows,
        "worsening_concentration",
    ):
        raise ValueError("worsening_concentration_count must match rows")
    if report.improving_concentration_count != _status_count(
        report.rows,
        "improving_concentration",
    ):
        raise ValueError("improving_concentration_count must match rows")
    if report.stale_review_count != _status_count(report.rows, "stale_review"):
        raise ValueError("stale_review_count must match rows")
    if report.normal_count != _status_count(report.rows, "normal"):
        raise ValueError("normal_count must match rows")
    if report.max_latest_share_of_total_open_notional != _max_optional_decimal(
        tuple(
            row.latest_share_of_total_open_notional
            for row in report.rows
            if row.latest_share_of_total_open_notional is not None
        ),
    ):
        raise ValueError("max_latest_share_of_total_open_notional must match rows")
    if report.max_review_age_seconds != _max_optional_decimal(
        tuple(row.review_age_seconds for row in report.rows if row.review_age_seconds is not None),
    ):
        raise ValueError("max_review_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.source_row_count):
        raise ValueError("reason_codes must match rows")
    if report.response_queue_status != _report_status(report.reason_codes):
        raise ValueError("response_queue_status must match reason_codes")


def _report_values_without_digest(report: ConcentrationResponseQueueReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    reject_unsafe_surface_fields("concentration response queue digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(RATIO_QUANTUM)


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
        raise ValueError(f"{field_name} must be a known value")


def _require_validation_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")


__all__ = (
    "DEFAULT_CONCENTRATION_RESPONSE_QUEUE_CONFIG_VERSION",
    "ConcentrationResponseQueueConfig",
    "ConcentrationResponseQueueReport",
    "ConcentrationResponseQueueRow",
    "build_concentration_response_queue_report",
    "concentration_response_queue_payload",
)
