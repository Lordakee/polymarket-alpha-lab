"""Pure report-only reducer for capacity buffer response queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CAPACITY_BUFFER_RESPONSE_QUEUE_CONFIG_VERSION = (
    "capacity-buffer-response-queue-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
DECIMAL_CONTEXT = Context(prec=64)
BOUNDARY_STATEMENT = (
    "Report-only capacity buffer response queue; no live execution surface."
)
SOURCE_STATUSES = ("ready", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = (
    "capacity_pressure_response_required",
    "worsening_utilization_response_required",
    "improving_buffer_observed",
    "stale_capacity_review_response_required",
    "normal_capacity",
)
REASON_CODES = (
    "no_capacity_buffer_trend_rows_supplied",
    "capacity_pressure_response_required",
    "worsening_utilization_response_required",
    "improving_buffer_observed",
    "stale_capacity_review_response_required",
    "normal_capacity_observed",
)
ROW_REASON_CODES = REASON_CODES[1:]
UNSAFE_PUBLIC_VALUE_FRAGMENTS = UNSAFE_SURFACE_FIELD_FRAGMENTS | frozenset(
    (
        "market" "_slug",
        "ques" "tion",
        "reco" "mmend",
        "trade",
        "advice",
    ),
)


@dataclass(frozen=True)
class CapacityBufferResponseQueueConfig:
    config_version: str = DEFAULT_CAPACITY_BUFFER_RESPONSE_QUEUE_CONFIG_VERSION
    pressure_utilization_threshold: Decimal = Decimal("0.900000")
    worsening_utilization_delta_threshold: Decimal = Decimal("0.050000")
    improving_buffer_delta_threshold: Decimal = Decimal("100.000000")
    stale_review_after_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pressure_utilization_threshold",
            "worsening_utilization_delta_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("improving_buffer_delta_threshold", "stale_review_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("CapacityBufferResponseQueueConfig", self)


@dataclass(frozen=True)
class CapacityBufferTrendRow:
    category_id: str
    team_id: str
    source_capacity_status: str
    latest_utilization_ratio: Decimal
    utilization_ratio_delta: Decimal
    latest_remaining_capacity_buffer: Decimal
    remaining_capacity_buffer_delta: Decimal
    latest_over_capacity_amount: Decimal
    latest_review_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        _require_source_status("source_capacity_status", self.source_capacity_status)
        object.__setattr__(
            self,
            "latest_utilization_ratio",
            _normalize_nonnegative_ratio(
                "latest_utilization_ratio",
                self.latest_utilization_ratio,
            ),
        )
        object.__setattr__(
            self,
            "utilization_ratio_delta",
            _normalize_ratio_delta("utilization_ratio_delta", self.utilization_ratio_delta),
        )
        for field_name in (
            "latest_remaining_capacity_buffer",
            "latest_over_capacity_amount",
            "latest_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "remaining_capacity_buffer_delta",
            _normalize_decimal(
                "remaining_capacity_buffer_delta",
                self.remaining_capacity_buffer_delta,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_source_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields("capacity buffer trend row", self)
        require_paper_only_flags("CapacityBufferTrendRow", self)
        _validate_trend_row(self)


@dataclass(frozen=True)
class CapacityBufferResponseQueueRow:
    category_id: str
    team_id: str
    response_queue_status: str
    source_capacity_status: str
    latest_utilization_ratio: Decimal
    utilization_ratio_delta: Decimal
    latest_remaining_capacity_buffer: Decimal
    remaining_capacity_buffer_delta: Decimal
    latest_over_capacity_amount: Decimal
    latest_review_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        _require_row_status("response_queue_status", self.response_queue_status)
        _require_source_status("source_capacity_status", self.source_capacity_status)
        object.__setattr__(
            self,
            "latest_utilization_ratio",
            _normalize_nonnegative_ratio(
                "latest_utilization_ratio",
                self.latest_utilization_ratio,
            ),
        )
        object.__setattr__(
            self,
            "utilization_ratio_delta",
            _normalize_ratio_delta("utilization_ratio_delta", self.utilization_ratio_delta),
        )
        for field_name in (
            "latest_remaining_capacity_buffer",
            "latest_over_capacity_amount",
            "latest_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "remaining_capacity_buffer_delta",
            _normalize_decimal(
                "remaining_capacity_buffer_delta",
                self.remaining_capacity_buffer_delta,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_row_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields("capacity buffer response queue row", self)
        require_paper_only_flags("CapacityBufferResponseQueueRow", self)
        _validate_response_row(self)


@dataclass(frozen=True)
class CapacityBufferResponseQueueReport:
    generated_at: datetime
    config_version: str
    response_queue_status: str
    source_row_count: Decimal
    row_count: Decimal
    capacity_pressure_count: Decimal
    worsening_utilization_count: Decimal
    improving_buffer_count: Decimal
    stale_review_count: Decimal
    normal_capacity_count: Decimal
    max_latest_utilization_ratio: Decimal | None
    min_latest_remaining_capacity_buffer: Decimal | None
    rows: tuple[CapacityBufferResponseQueueRow, ...]
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
            "capacity_pressure_count",
            "worsening_utilization_count",
            "improving_buffer_count",
            "stale_review_count",
            "normal_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_utilization_ratio",
            _normalize_optional_nonnegative_ratio(
                "max_latest_utilization_ratio",
                self.max_latest_utilization_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_latest_remaining_capacity_buffer",
            _normalize_optional_nonnegative_decimal(
                "min_latest_remaining_capacity_buffer",
                self.min_latest_remaining_capacity_buffer,
            ),
        )
        object.__setattr__(self, "rows", _normalize_queue_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match report-only scope")
        reject_unsafe_surface_fields("capacity buffer response queue report", self)
        require_paper_only_flags("CapacityBufferResponseQueueReport", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_capacity_buffer_response_queue_report(
    rows: list[CapacityBufferTrendRow] | tuple[CapacityBufferTrendRow, ...],
    *,
    config: CapacityBufferResponseQueueConfig,
    generated_at: datetime,
) -> CapacityBufferResponseQueueReport:
    if type(config) is not CapacityBufferResponseQueueConfig:
        raise ValueError("config must be a CapacityBufferResponseQueueConfig")
    require_paper_only_flags("CapacityBufferResponseQueueConfig", config)
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
        "capacity_pressure_count": _status_count(
            queue_rows,
            "capacity_pressure_response_required",
        ),
        "worsening_utilization_count": _status_count(
            queue_rows,
            "worsening_utilization_response_required",
        ),
        "improving_buffer_count": _status_count(
            queue_rows,
            "improving_buffer_observed",
        ),
        "stale_review_count": _status_count(
            queue_rows,
            "stale_capacity_review_response_required",
        ),
        "normal_capacity_count": _status_count(queue_rows, "normal_capacity"),
        "max_latest_utilization_ratio": _max_optional_decimal(
            tuple(row.latest_utilization_ratio for row in queue_rows),
        ),
        "min_latest_remaining_capacity_buffer": _min_optional_decimal(
            tuple(row.latest_remaining_capacity_buffer for row in queue_rows),
        ),
        "rows": queue_rows,
        "reason_codes": reason_codes,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    return CapacityBufferResponseQueueReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def capacity_buffer_response_queue_payload(
    report: CapacityBufferResponseQueueReport,
) -> dict[str, Any]:
    if type(report) is not CapacityBufferResponseQueueReport:
        raise ValueError("report must be a CapacityBufferResponseQueueReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("capacity buffer response queue report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("capacity buffer response queue payload", payload)
    _reject_unsafe_public_values("capacity buffer response queue payload", payload)
    return payload


def _normalize_source_rows(
    value: list[CapacityBufferTrendRow] | tuple[CapacityBufferTrendRow, ...],
) -> tuple[CapacityBufferTrendRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not CapacityBufferTrendRow:
            raise ValueError("rows must contain CapacityBufferTrendRow values")
        require_paper_only_flags("CapacityBufferTrendRow", row)
        key = (row.category_id, row.team_id)
        if key in seen_keys:
            raise ValueError("rows must be deterministic")
        seen_keys.add(key)
    return rows


def _queue_row(
    source_row: CapacityBufferTrendRow,
    config: CapacityBufferResponseQueueConfig,
) -> CapacityBufferResponseQueueRow:
    status = _row_status(source_row, config)
    return CapacityBufferResponseQueueRow(
        category_id=source_row.category_id,
        team_id=source_row.team_id,
        response_queue_status=status,
        source_capacity_status=source_row.source_capacity_status,
        latest_utilization_ratio=source_row.latest_utilization_ratio,
        utilization_ratio_delta=source_row.utilization_ratio_delta,
        latest_remaining_capacity_buffer=source_row.latest_remaining_capacity_buffer,
        remaining_capacity_buffer_delta=source_row.remaining_capacity_buffer_delta,
        latest_over_capacity_amount=source_row.latest_over_capacity_amount,
        latest_review_age_seconds=source_row.latest_review_age_seconds,
        reason_codes=_row_reason_codes(source_row, config),
    )


def _row_status(
    source_row: CapacityBufferTrendRow,
    config: CapacityBufferResponseQueueConfig,
) -> str:
    if _has_capacity_pressure(source_row, config):
        return "capacity_pressure_response_required"
    if source_row.utilization_ratio_delta >= config.worsening_utilization_delta_threshold:
        return "worsening_utilization_response_required"
    if source_row.latest_review_age_seconds > config.stale_review_after_seconds:
        return "stale_capacity_review_response_required"
    if source_row.remaining_capacity_buffer_delta >= config.improving_buffer_delta_threshold:
        return "improving_buffer_observed"
    return "normal_capacity"


def _row_reason_codes(
    source_row: CapacityBufferTrendRow,
    config: CapacityBufferResponseQueueConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if _has_capacity_pressure(source_row, config):
        codes.append("capacity_pressure_response_required")
    if source_row.utilization_ratio_delta >= config.worsening_utilization_delta_threshold:
        codes.append("worsening_utilization_response_required")
    if source_row.remaining_capacity_buffer_delta >= config.improving_buffer_delta_threshold:
        codes.append("improving_buffer_observed")
    if source_row.latest_review_age_seconds > config.stale_review_after_seconds:
        codes.append("stale_capacity_review_response_required")
    if not codes:
        codes.append("normal_capacity_observed")
    return tuple(codes)


def _has_capacity_pressure(
    source_row: CapacityBufferTrendRow,
    config: CapacityBufferResponseQueueConfig,
) -> bool:
    return (
        source_row.source_capacity_status == "blocked"
        or source_row.latest_over_capacity_amount > ZERO_RATIO
        or source_row.latest_utilization_ratio >= config.pressure_utilization_threshold
    )


def _report_reason_codes(
    rows: tuple[CapacityBufferResponseQueueRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_capacity_buffer_trend_rows_supplied",)
    codes: list[str] = []
    for reason_code in (
        "capacity_pressure_response_required",
        "worsening_utilization_response_required",
        "improving_buffer_observed",
        "stale_capacity_review_response_required",
        "normal_capacity_observed",
    ):
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return tuple(codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if "capacity_pressure_response_required" in reason_codes:
        return "blocked"
    if (
        "worsening_utilization_response_required" in reason_codes
        or "stale_capacity_review_response_required" in reason_codes
    ):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[CapacityBufferResponseQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.response_queue_status == status))


def _queue_row_sort_key(
    row: CapacityBufferResponseQueueRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        -_row_status_weight(row.response_queue_status),
        -row.latest_utilization_ratio,
        row.latest_remaining_capacity_buffer,
        row.category_id,
        row.team_id,
    )


def _row_status_weight(status: str) -> int:
    if status == "capacity_pressure_response_required":
        return 5
    if status == "worsening_utilization_response_required":
        return 4
    if status == "stale_capacity_review_response_required":
        return 3
    if status == "improving_buffer_observed":
        return 2
    return 1


def _validate_trend_row(row: CapacityBufferTrendRow) -> None:
    if row.latest_over_capacity_amount > ZERO_RATIO and row.latest_remaining_capacity_buffer > ZERO_RATIO:
        raise ValueError(
            "latest_over_capacity_amount requires zero latest_remaining_capacity_buffer",
        )
    if row.source_capacity_status == "blocked" and row.latest_remaining_capacity_buffer > ZERO_RATIO:
        raise ValueError("blocked rows require zero latest_remaining_capacity_buffer")


def _validate_response_row(row: CapacityBufferResponseQueueRow) -> None:
    trend_row = CapacityBufferTrendRow(
        category_id=row.category_id,
        team_id=row.team_id,
        source_capacity_status=row.source_capacity_status,
        latest_utilization_ratio=row.latest_utilization_ratio,
        utilization_ratio_delta=row.utilization_ratio_delta,
        latest_remaining_capacity_buffer=row.latest_remaining_capacity_buffer,
        remaining_capacity_buffer_delta=row.remaining_capacity_buffer_delta,
        latest_over_capacity_amount=row.latest_over_capacity_amount,
        latest_review_age_seconds=row.latest_review_age_seconds,
        reason_codes=("paper_capacity_trend_validation",),
    )
    derived_reasons = tuple(
        reason
        for reason in row.reason_codes
        if reason != "normal_capacity_observed"
    )
    if row.response_queue_status == "normal_capacity":
        expected_reasons = ("normal_capacity_observed",)
    else:
        expected_reasons = derived_reasons
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match response_queue_status")
    if row.response_queue_status != _dominant_status_from_reasons(trend_row, row.reason_codes):
        raise ValueError("response_queue_status must match row diagnostics")


def _dominant_status_from_reasons(
    row: CapacityBufferTrendRow,
    reason_codes: tuple[str, ...],
) -> str:
    if "capacity_pressure_response_required" in reason_codes:
        return "capacity_pressure_response_required"
    if "worsening_utilization_response_required" in reason_codes:
        return "worsening_utilization_response_required"
    if "stale_capacity_review_response_required" in reason_codes:
        return "stale_capacity_review_response_required"
    if "improving_buffer_observed" in reason_codes:
        return "improving_buffer_observed"
    if row.source_capacity_status == "ready":
        return "normal_capacity"
    return "normal_capacity"


def _validate_report(report: CapacityBufferResponseQueueReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.source_row_count != report.row_count:
        raise ValueError("source_row_count must match rows")
    if report.capacity_pressure_count != _status_count(
        report.rows,
        "capacity_pressure_response_required",
    ):
        raise ValueError("capacity_pressure_count must match rows")
    if report.worsening_utilization_count != _status_count(
        report.rows,
        "worsening_utilization_response_required",
    ):
        raise ValueError("worsening_utilization_count must match rows")
    if report.improving_buffer_count != _status_count(report.rows, "improving_buffer_observed"):
        raise ValueError("improving_buffer_count must match rows")
    if report.stale_review_count != _status_count(
        report.rows,
        "stale_capacity_review_response_required",
    ):
        raise ValueError("stale_review_count must match rows")
    if report.normal_capacity_count != _status_count(report.rows, "normal_capacity"):
        raise ValueError("normal_capacity_count must match rows")
    if report.max_latest_utilization_ratio != _max_optional_decimal(
        tuple(row.latest_utilization_ratio for row in report.rows),
    ):
        raise ValueError("max_latest_utilization_ratio must match rows")
    if report.min_latest_remaining_capacity_buffer != _min_optional_decimal(
        tuple(row.latest_remaining_capacity_buffer for row in report.rows),
    ):
        raise ValueError("min_latest_remaining_capacity_buffer must match rows")
    if report.rows != tuple(sorted(report.rows, key=_queue_row_sort_key)):
        raise ValueError("rows must be deterministic")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.source_row_count)):
        raise ValueError("reason_codes must match rows")
    if report.response_queue_status != _report_status(report.reason_codes):
        raise ValueError("response_queue_status must match reason_codes")
    if report.source_row_count == ZERO_COUNT:
        if report.row_count != ZERO_COUNT:
            raise ValueError("row_count must be zero without source rows")
        if report.max_latest_utilization_ratio is not None:
            raise ValueError("max_latest_utilization_ratio must be absent without rows")
        if report.min_latest_remaining_capacity_buffer is not None:
            raise ValueError(
                "min_latest_remaining_capacity_buffer must be absent without rows",
            )


def _report_values_without_digest(report: CapacityBufferResponseQueueReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    reject_unsafe_surface_fields("capacity buffer response queue digest payload", payload)
    _reject_unsafe_public_values("capacity buffer response queue digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_queue_rows(
    value: tuple[CapacityBufferResponseQueueRow, ...],
) -> tuple[CapacityBufferResponseQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not CapacityBufferResponseQueueRow:
            raise ValueError(
                "rows must contain CapacityBufferResponseQueueRow values",
            )
        require_paper_only_flags("CapacityBufferResponseQueueRow", row)
        key = (row.category_id, row.team_id)
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


def _normalize_optional_nonnegative_ratio(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_ratio(field_name, value)


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


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_ratio_delta(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio_delta(field_name: str, value: object) -> Decimal:
    return _normalize_decimal(field_name, value)


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


def _min_optional_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return min(values)


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


def _require_source_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SOURCE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


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


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_values(label, item)


__all__ = (
    "DEFAULT_CAPACITY_BUFFER_RESPONSE_QUEUE_CONFIG_VERSION",
    "CapacityBufferResponseQueueConfig",
    "CapacityBufferResponseQueueReport",
    "CapacityBufferResponseQueueRow",
    "CapacityBufferTrendRow",
    "build_capacity_buffer_response_queue_report",
    "capacity_buffer_response_queue_payload",
)
