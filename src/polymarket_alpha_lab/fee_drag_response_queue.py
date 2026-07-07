"""Pure report reducer for fee drag response queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_FEE_DRAG_RESPONSE_QUEUE_CONFIG_VERSION = "fee-drag-response-queue-v0"
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
BOUNDARY_STATEMENT = (
    "Report-only fee drag response queue; no guidance or execution instructions."
)
SOURCE_TREND_STATUSES = ("insufficient_history", "stable", "watch")
SCOPE_TYPES = ("category", "team")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = (
    "fee_drag_pressure_response_required",
    "worsening_fee_drag_response_required",
    "improving_fee_drag_observed",
    "stale_fee_drag_review_response_required",
    "normal_fee_drag",
)
REASON_CODES = (
    "no_fee_drag_trend_rows_supplied",
    "fee_drag_pressure_response_required",
    "worsening_fee_drag_response_required",
    "improving_fee_drag_observed",
    "stale_fee_drag_review_response_required",
    "normal_fee_drag_observed",
)
ROW_REASON_CODES = REASON_CODES[1:]


@dataclass(frozen=True)
class FeeDragResponseQueueConfig:
    config_version: str = DEFAULT_FEE_DRAG_RESPONSE_QUEUE_CONFIG_VERSION
    pressure_fee_drag_bps_threshold: Decimal = Decimal("100.000000")
    worsening_fee_drag_bps_delta_threshold: Decimal = Decimal("25.000000")
    improving_fee_drag_bps_delta_threshold: Decimal = Decimal("25.000000")
    stale_review_after_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pressure_fee_drag_bps_threshold",
            "worsening_fee_drag_bps_delta_threshold",
            "improving_fee_drag_bps_delta_threshold",
            "stale_review_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("FeeDragResponseQueueConfig", self)


@dataclass(frozen=True)
class FeeDragTrendRow:
    scope_type: str
    scope_id: str
    source_trend_status: str
    latest_fee_drag_bps: Decimal
    fee_drag_bps_delta: Decimal
    latest_fee_drag_share: Decimal
    latest_review_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("scope_type", self.scope_type, SCOPE_TYPES)
        _require_canonical_string("scope_id", self.scope_id)
        _require_member(
            "source_trend_status",
            self.source_trend_status,
            SOURCE_TREND_STATUSES,
        )
        object.__setattr__(
            self,
            "latest_fee_drag_bps",
            _normalize_nonnegative_decimal("latest_fee_drag_bps", self.latest_fee_drag_bps),
        )
        object.__setattr__(
            self,
            "fee_drag_bps_delta",
            _normalize_decimal("fee_drag_bps_delta", self.fee_drag_bps_delta),
        )
        object.__setattr__(
            self,
            "latest_fee_drag_share",
            _normalize_ratio("latest_fee_drag_share", self.latest_fee_drag_share),
        )
        object.__setattr__(
            self,
            "latest_review_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_review_age_seconds",
                self.latest_review_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields("fee drag trend row", self)
        require_paper_only_flags("FeeDragTrendRow", self)


@dataclass(frozen=True)
class FeeDragResponseQueueRow:
    scope_type: str
    scope_id: str
    response_queue_status: str
    source_trend_status: str
    latest_fee_drag_bps: Decimal
    fee_drag_bps_delta: Decimal
    latest_fee_drag_share: Decimal
    latest_review_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("scope_type", self.scope_type, SCOPE_TYPES)
        _require_canonical_string("scope_id", self.scope_id)
        _require_row_status("response_queue_status", self.response_queue_status)
        _require_member(
            "source_trend_status",
            self.source_trend_status,
            SOURCE_TREND_STATUSES,
        )
        object.__setattr__(
            self,
            "latest_fee_drag_bps",
            _normalize_nonnegative_decimal("latest_fee_drag_bps", self.latest_fee_drag_bps),
        )
        object.__setattr__(
            self,
            "fee_drag_bps_delta",
            _normalize_decimal("fee_drag_bps_delta", self.fee_drag_bps_delta),
        )
        object.__setattr__(
            self,
            "latest_fee_drag_share",
            _normalize_ratio("latest_fee_drag_share", self.latest_fee_drag_share),
        )
        object.__setattr__(
            self,
            "latest_review_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_review_age_seconds",
                self.latest_review_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields("fee drag response queue row", self)
        require_paper_only_flags("FeeDragResponseQueueRow", self)
        _validate_response_row(self)


@dataclass(frozen=True)
class FeeDragResponseQueueReport:
    generated_at: datetime
    config_version: str
    response_queue_status: str
    source_row_count: Decimal
    row_count: Decimal
    fee_drag_pressure_count: Decimal
    worsening_drag_count: Decimal
    improving_drag_count: Decimal
    stale_review_count: Decimal
    normal_count: Decimal
    max_latest_fee_drag_bps: Decimal | None
    max_latest_fee_drag_share: Decimal | None
    rows: tuple[FeeDragResponseQueueRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("response_queue_status", self.response_queue_status)
        for field_name in (
            "source_row_count",
            "row_count",
            "fee_drag_pressure_count",
            "worsening_drag_count",
            "improving_drag_count",
            "stale_review_count",
            "normal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_fee_drag_bps",
            _normalize_optional_nonnegative_decimal(
                "max_latest_fee_drag_bps",
                self.max_latest_fee_drag_bps,
            ),
        )
        object.__setattr__(
            self,
            "max_latest_fee_drag_share",
            _normalize_optional_ratio(
                "max_latest_fee_drag_share",
                self.max_latest_fee_drag_share,
            ),
        )
        object.__setattr__(self, "rows", _normalize_queue_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match report-only scope")
        reject_unsafe_surface_fields("fee drag response queue report", self)
        require_paper_only_flags("FeeDragResponseQueueReport", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_fee_drag_response_queue_report(
    rows: list[FeeDragTrendRow] | tuple[FeeDragTrendRow, ...],
    *,
    config: FeeDragResponseQueueConfig,
    generated_at: datetime,
) -> FeeDragResponseQueueReport:
    if type(config) is not FeeDragResponseQueueConfig:
        raise ValueError("config must be a FeeDragResponseQueueConfig")
    require_paper_only_flags("FeeDragResponseQueueConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    queue_rows = tuple(
        sorted(
            (_queue_row(row, config) for row in source_rows),
            key=_queue_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(queue_rows, len(source_rows))

    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "response_queue_status": _report_status(reason_codes),
        "source_row_count": _count(len(source_rows)),
        "row_count": _count(len(queue_rows)),
        "fee_drag_pressure_count": _status_count(
            queue_rows,
            "fee_drag_pressure_response_required",
        ),
        "worsening_drag_count": _status_count(
            queue_rows,
            "worsening_fee_drag_response_required",
        ),
        "improving_drag_count": _status_count(queue_rows, "improving_fee_drag_observed"),
        "stale_review_count": _status_count(
            queue_rows,
            "stale_fee_drag_review_response_required",
        ),
        "normal_count": _status_count(queue_rows, "normal_fee_drag"),
        "max_latest_fee_drag_bps": _max_optional_decimal(
            tuple(row.latest_fee_drag_bps for row in queue_rows),
        ),
        "max_latest_fee_drag_share": _max_optional_decimal(
            tuple(row.latest_fee_drag_share for row in queue_rows),
        ),
        "rows": queue_rows,
        "reason_codes": reason_codes,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    return FeeDragResponseQueueReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def fee_drag_response_queue_payload(
    report: FeeDragResponseQueueReport,
) -> dict[str, Any]:
    if type(report) is not FeeDragResponseQueueReport:
        raise ValueError("report must be a FeeDragResponseQueueReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("fee drag response queue report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("fee drag response queue payload", ready)
    return ready


def _normalize_source_rows(
    value: list[FeeDragTrendRow] | tuple[FeeDragTrendRow, ...],
) -> tuple[FeeDragTrendRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not FeeDragTrendRow:
            raise ValueError("rows must contain FeeDragTrendRow values")
        require_paper_only_flags("FeeDragTrendRow", row)
        key = (row.scope_type, row.scope_id)
        if key in seen_keys:
            raise ValueError("rows must be deterministic")
        seen_keys.add(key)
    return rows


def _queue_row(
    source_row: FeeDragTrendRow,
    config: FeeDragResponseQueueConfig,
) -> FeeDragResponseQueueRow:
    status = _row_status(source_row, config)
    return FeeDragResponseQueueRow(
        scope_type=source_row.scope_type,
        scope_id=source_row.scope_id,
        response_queue_status=status,
        source_trend_status=source_row.source_trend_status,
        latest_fee_drag_bps=source_row.latest_fee_drag_bps,
        fee_drag_bps_delta=source_row.fee_drag_bps_delta,
        latest_fee_drag_share=source_row.latest_fee_drag_share,
        latest_review_age_seconds=source_row.latest_review_age_seconds,
        reason_codes=_row_reason_codes(source_row, config),
    )


def _row_status(
    source_row: FeeDragTrendRow,
    config: FeeDragResponseQueueConfig,
) -> str:
    if _has_fee_drag_pressure(source_row, config):
        return "fee_drag_pressure_response_required"
    if source_row.fee_drag_bps_delta >= config.worsening_fee_drag_bps_delta_threshold:
        return "worsening_fee_drag_response_required"
    if source_row.latest_review_age_seconds > config.stale_review_after_seconds:
        return "stale_fee_drag_review_response_required"
    if -source_row.fee_drag_bps_delta >= config.improving_fee_drag_bps_delta_threshold:
        return "improving_fee_drag_observed"
    return "normal_fee_drag"


def _row_reason_codes(
    source_row: FeeDragTrendRow,
    config: FeeDragResponseQueueConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if _has_fee_drag_pressure(source_row, config):
        codes.append("fee_drag_pressure_response_required")
    if source_row.fee_drag_bps_delta >= config.worsening_fee_drag_bps_delta_threshold:
        codes.append("worsening_fee_drag_response_required")
    if -source_row.fee_drag_bps_delta >= config.improving_fee_drag_bps_delta_threshold:
        codes.append("improving_fee_drag_observed")
    if source_row.latest_review_age_seconds > config.stale_review_after_seconds:
        codes.append("stale_fee_drag_review_response_required")
    if not codes:
        codes.append("normal_fee_drag_observed")
    return tuple(codes)


def _has_fee_drag_pressure(
    source_row: FeeDragTrendRow,
    config: FeeDragResponseQueueConfig,
) -> bool:
    return (
        source_row.source_trend_status == "watch"
        and source_row.latest_fee_drag_bps >= config.pressure_fee_drag_bps_threshold
    )


def _report_reason_codes(
    rows: tuple[FeeDragResponseQueueRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_fee_drag_trend_rows_supplied",)
    codes: list[str] = []
    for reason_code in (
        "fee_drag_pressure_response_required",
        "worsening_fee_drag_response_required",
        "improving_fee_drag_observed",
        "stale_fee_drag_review_response_required",
        "normal_fee_drag_observed",
    ):
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return tuple(codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if "fee_drag_pressure_response_required" in reason_codes:
        return "blocked"
    if (
        "worsening_fee_drag_response_required" in reason_codes
        or "stale_fee_drag_review_response_required" in reason_codes
    ):
        return "watch"
    return "pass"


def _queue_row_sort_key(row: FeeDragResponseQueueRow) -> tuple[int, Decimal, str, str]:
    status_rank = {
        "fee_drag_pressure_response_required": 0,
        "worsening_fee_drag_response_required": 1,
        "stale_fee_drag_review_response_required": 2,
        "improving_fee_drag_observed": 3,
        "normal_fee_drag": 4,
    }[row.response_queue_status]
    return (
        status_rank,
        -row.latest_fee_drag_bps,
        row.scope_type,
        row.scope_id,
    )


def _status_count(rows: tuple[FeeDragResponseQueueRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.response_queue_status == status))


def _validate_response_row(row: FeeDragResponseQueueRow) -> None:
    if row.response_queue_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("response_queue_status must match reason_codes")
    if "normal_fee_drag_observed" in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("reason_codes must match response_queue_status")
    if (
        "worsening_fee_drag_response_required" in row.reason_codes
        and "improving_fee_drag_observed" in row.reason_codes
    ):
        raise ValueError("reason_codes must not mix worsening and improving states")
    if (
        "worsening_fee_drag_response_required" in row.reason_codes
        and row.fee_drag_bps_delta <= ZERO_RATIO
    ):
        raise ValueError("reason_codes must match fee_drag_bps_delta")
    if "improving_fee_drag_observed" in row.reason_codes and row.fee_drag_bps_delta >= ZERO_RATIO:
        raise ValueError("reason_codes must match fee_drag_bps_delta")
    if (
        "fee_drag_pressure_response_required" in row.reason_codes
        and row.source_trend_status != "watch"
    ):
        raise ValueError("reason_codes must match source_trend_status")


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "fee_drag_pressure_response_required" in reason_codes:
        return "fee_drag_pressure_response_required"
    if "worsening_fee_drag_response_required" in reason_codes:
        return "worsening_fee_drag_response_required"
    if "stale_fee_drag_review_response_required" in reason_codes:
        return "stale_fee_drag_review_response_required"
    if "improving_fee_drag_observed" in reason_codes:
        return "improving_fee_drag_observed"
    return "normal_fee_drag"


def _validate_report(report: FeeDragResponseQueueReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.source_row_count != report.row_count:
        raise ValueError("source_row_count must match rows")
    if report.fee_drag_pressure_count != _status_count(
        report.rows,
        "fee_drag_pressure_response_required",
    ):
        raise ValueError("fee_drag_pressure_count must match rows")
    if report.worsening_drag_count != _status_count(
        report.rows,
        "worsening_fee_drag_response_required",
    ):
        raise ValueError("worsening_drag_count must match rows")
    if report.improving_drag_count != _status_count(report.rows, "improving_fee_drag_observed"):
        raise ValueError("improving_drag_count must match rows")
    if report.stale_review_count != _status_count(
        report.rows,
        "stale_fee_drag_review_response_required",
    ):
        raise ValueError("stale_review_count must match rows")
    if report.normal_count != _status_count(report.rows, "normal_fee_drag"):
        raise ValueError("normal_count must match rows")
    if report.max_latest_fee_drag_bps != _max_optional_decimal(
        tuple(row.latest_fee_drag_bps for row in report.rows),
    ):
        raise ValueError("max_latest_fee_drag_bps must match rows")
    if report.max_latest_fee_drag_share != _max_optional_decimal(
        tuple(row.latest_fee_drag_share for row in report.rows),
    ):
        raise ValueError("max_latest_fee_drag_share must match rows")
    if report.rows != tuple(sorted(report.rows, key=_queue_row_sort_key)):
        raise ValueError("rows must be deterministic")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.source_row_count)):
        raise ValueError("reason_codes must match rows")
    if report.response_queue_status != _report_status(report.reason_codes):
        raise ValueError("response_queue_status must match reason_codes")
    if report.source_row_count == ZERO_COUNT:
        if report.row_count != ZERO_COUNT:
            raise ValueError("row_count must be zero without source rows")
        if report.max_latest_fee_drag_bps is not None:
            raise ValueError("max_latest_fee_drag_bps must be absent without rows")
        if report.max_latest_fee_drag_share is not None:
            raise ValueError("max_latest_fee_drag_share must be absent without rows")


def _report_values_without_digest(report: FeeDragResponseQueueReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    reject_unsafe_surface_fields("fee drag response queue digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_queue_rows(
    value: tuple[FeeDragResponseQueueRow, ...],
) -> tuple[FeeDragResponseQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not FeeDragResponseQueueRow:
            raise ValueError("rows must contain FeeDragResponseQueueRow values")
        require_paper_only_flags("FeeDragResponseQueueRow", row)
        key = (row.scope_type, row.scope_id)
        if key in seen_keys:
            raise ValueError("rows must be deterministic")
        seen_keys.add(key)
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
    return reason_codes


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(value)
    if any(reason_code not in ROW_REASON_CODES for reason_code in reason_codes):
        raise ValueError("reason_codes must contain row values")
    if tuple(code for code in ROW_REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _normalize_source_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


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


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _max_optional_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return max(values)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
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
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_report_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_row_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known queue status")


def _require_validation_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")


__all__ = (
    "DEFAULT_FEE_DRAG_RESPONSE_QUEUE_CONFIG_VERSION",
    "FeeDragResponseQueueConfig",
    "FeeDragResponseQueueReport",
    "FeeDragResponseQueueRow",
    "FeeDragTrendRow",
    "build_fee_drag_response_queue_report",
    "fee_drag_response_queue_payload",
)
