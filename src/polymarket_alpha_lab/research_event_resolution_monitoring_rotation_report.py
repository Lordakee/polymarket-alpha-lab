from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchEventResolutionMonitoringRotationConfig",
    "ResearchEventResolutionMonitoringRotationInput",
    "ResearchEventResolutionMonitoringRotationReasonCodeCount",
    "ResearchEventResolutionMonitoringRotationReport",
    "ResearchEventResolutionMonitoringRotationRow",
    "build_research_event_resolution_monitoring_rotation_report",
    "research_event_resolution_monitoring_rotation_report_payload",
)


DEFAULT_CONFIG_VERSION = "resolution-monitoring-rotation-report-v0"
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_WATCH_ROTATION_PRESSURE = Decimal("0.450000")
DEFAULT_BLOCK_ROTATION_PRESSURE = Decimal("0.700000")


@dataclass(frozen=True)
class ResearchEventResolutionMonitoringRotationConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_evidence_age_seconds: Decimal = Decimal("1800")
    stale_evidence_age_seconds: Decimal = Decimal("21600")
    deadline_window_seconds: Decimal = Decimal("86400")
    oracle_lag_limit_seconds: Decimal = Decimal("3600")
    watch_rotation_pressure: Decimal = DEFAULT_WATCH_ROTATION_PRESSURE
    block_rotation_pressure: Decimal = DEFAULT_BLOCK_ROTATION_PRESSURE
    evidence_age_weight: Decimal = Decimal("0.250000")
    deadline_weight: Decimal = Decimal("0.250000")
    source_reliability_weight: Decimal = Decimal("0.200000")
    oracle_lag_weight: Decimal = Decimal("0.150000")
    capacity_weight: Decimal = Decimal("0.150000")
    pass_monitoring_interval_seconds: Decimal = Decimal("3600")
    watch_monitoring_interval_seconds: Decimal = Decimal("900")
    block_monitoring_interval_seconds: Decimal = Decimal("300")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionMonitoringRotationConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "fresh_evidence_age_seconds",
            "stale_evidence_age_seconds",
            "deadline_window_seconds",
            "oracle_lag_limit_seconds",
            "pass_monitoring_interval_seconds",
            "watch_monitoring_interval_seconds",
            "block_monitoring_interval_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_evidence_age_seconds <= self.fresh_evidence_age_seconds:
            raise ValueError(
                "stale_evidence_age_seconds must exceed fresh_evidence_age_seconds",
            )
        for field_name in (
            "watch_rotation_pressure",
            "block_rotation_pressure",
            "evidence_age_weight",
            "deadline_weight",
            "source_reliability_weight",
            "oracle_lag_weight",
            "capacity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_rotation_pressure <= self.watch_rotation_pressure:
            raise ValueError("block_rotation_pressure must exceed watch_rotation_pressure")
        weight_total = _quantize(
            self.evidence_age_weight
            + self.deadline_weight
            + self.source_reliability_weight
            + self.oracle_lag_weight
            + self.capacity_weight,
        )
        if weight_total != ONE:
            raise ValueError("rotation pressure weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionMonitoringRotationInput:
    rotation_bucket: str
    aggregate_evidence_age_seconds: Decimal
    deadline_proximity_seconds: Decimal
    source_reliability_score: Decimal
    oracle_lag_seconds: Decimal
    open_resolution_items: Decimal
    monitoring_capacity_units: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionMonitoringRotationInput, "input")
        _require_public_bucket("rotation_bucket", self.rotation_bucket)
        for field_name in (
            "aggregate_evidence_age_seconds",
            "deadline_proximity_seconds",
            "oracle_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_reliability_score",
            _require_probability_decimal(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "open_resolution_items",
            _require_nonnegative_whole_decimal(
                "open_resolution_items",
                self.open_resolution_items,
            ),
        )
        object.__setattr__(
            self,
            "monitoring_capacity_units",
            _require_positive_whole_decimal(
                "monitoring_capacity_units",
                self.monitoring_capacity_units,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionMonitoringRotationRow:
    rotation_bucket: str
    rotation_priority: Decimal
    aggregate_evidence_age_seconds: Decimal
    deadline_proximity_seconds: Decimal
    source_reliability_score: Decimal
    oracle_lag_seconds: Decimal
    open_resolution_items: Decimal
    monitoring_capacity_units: Decimal
    evidence_age_pressure: Decimal
    deadline_pressure: Decimal
    source_reliability_pressure: Decimal
    oracle_lag_pressure: Decimal
    capacity_pressure: Decimal
    rotation_pressure: Decimal
    monitoring_interval_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionMonitoringRotationRow, "row")
        _require_public_bucket("rotation_bucket", self.rotation_bucket)
        object.__setattr__(
            self,
            "rotation_priority",
            _require_positive_whole_decimal("rotation_priority", self.rotation_priority),
        )
        for field_name in (
            "aggregate_evidence_age_seconds",
            "deadline_proximity_seconds",
            "oracle_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_reliability_score",
            _require_probability_decimal(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "open_resolution_items",
            _require_nonnegative_whole_decimal(
                "open_resolution_items",
                self.open_resolution_items,
            ),
        )
        object.__setattr__(
            self,
            "monitoring_capacity_units",
            _require_positive_whole_decimal(
                "monitoring_capacity_units",
                self.monitoring_capacity_units,
            ),
        )
        for field_name in (
            "evidence_age_pressure",
            "deadline_pressure",
            "source_reliability_pressure",
            "oracle_lag_pressure",
            "capacity_pressure",
            "rotation_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "monitoring_interval_seconds",
            _require_positive_whole_decimal(
                "monitoring_interval_seconds",
                self.monitoring_interval_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventResolutionMonitoringRotationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionMonitoringRotationReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventResolutionMonitoringRotationReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_rotation_pressure: Decimal | None
    max_rotation_pressure: Decimal | None
    near_deadline_count: Decimal
    stale_evidence_count: Decimal
    oracle_lag_count: Decimal
    constrained_capacity_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventResolutionMonitoringRotationReasonCodeCount, ...]
    derived_validation_digest: str
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionMonitoringRotationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "near_deadline_count",
            "stale_evidence_count",
            "oracle_lag_count",
            "constrained_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_rotation_pressure",
            _require_optional_probability_decimal(
                "average_rotation_pressure",
                self.average_rotation_pressure,
            ),
        )
        object.__setattr__(
            self,
            "max_rotation_pressure",
            _require_optional_probability_decimal(
                "max_rotation_pressure",
                self.max_rotation_pressure,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_validation_digest("derived_validation_digest", self.derived_validation_digest)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_event_resolution_monitoring_rotation_report(
    inputs: Iterable[ResearchEventResolutionMonitoringRotationInput],
    *,
    config: ResearchEventResolutionMonitoringRotationConfig,
    generated_at: datetime,
) -> ResearchEventResolutionMonitoringRotationReport:
    if type(config) is not ResearchEventResolutionMonitoringRotationConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionMonitoringRotationConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    row_values = tuple(
        sorted(
            (_row_values(item, config=config) for item in normalized_inputs),
            key=lambda item: (-item["rotation_pressure"], item["rotation_bucket"]),
        ),
    )
    rows = tuple(
        ResearchEventResolutionMonitoringRotationRow(
            rotation_priority=_decimal_count(index),
            **values,
        )
        for index, values in enumerate(row_values, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized_inputs)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "average_rotation_pressure": _average_rotation_pressure(rows),
        "max_rotation_pressure": _max_rotation_pressure(rows),
        "near_deadline_count": _reason_count(rows, "resolution_deadline_near"),
        "stale_evidence_count": _reason_count(rows, "evidence_stale"),
        "oracle_lag_count": _reason_count(rows, "oracle_lag_elevated"),
        "constrained_capacity_count": _reason_count(rows, "capacity_constrained"),
        "status": status,
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionMonitoringRotationReport(
        **report_values,
        derived_validation_digest=_derived_validation_digest(report_values),
    )


def research_event_resolution_monitoring_rotation_report_payload(
    report: ResearchEventResolutionMonitoringRotationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionMonitoringRotationReport:
        raise ValueError("report must be a ResearchEventResolutionMonitoringRotationReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload_text(payload)
    return payload


def _row_values(
    item: ResearchEventResolutionMonitoringRotationInput,
    *,
    config: ResearchEventResolutionMonitoringRotationConfig,
) -> dict[str, Any]:
    evidence_age_pressure = _evidence_age_pressure(item, config)
    deadline_pressure = _deadline_pressure(item, config)
    source_reliability_pressure = _quantize(ONE - item.source_reliability_score)
    oracle_lag_pressure = _bounded_ratio(
        item.oracle_lag_seconds,
        config.oracle_lag_limit_seconds,
    )
    capacity_pressure = _bounded_ratio(
        item.open_resolution_items,
        item.monitoring_capacity_units,
    )
    rotation_pressure = _quantize(
        (evidence_age_pressure * config.evidence_age_weight)
        + (deadline_pressure * config.deadline_weight)
        + (source_reliability_pressure * config.source_reliability_weight)
        + (oracle_lag_pressure * config.oracle_lag_weight)
        + (capacity_pressure * config.capacity_weight),
    )
    status = _row_status(rotation_pressure, config)
    return {
        "rotation_bucket": item.rotation_bucket,
        "aggregate_evidence_age_seconds": item.aggregate_evidence_age_seconds,
        "deadline_proximity_seconds": item.deadline_proximity_seconds,
        "source_reliability_score": item.source_reliability_score,
        "oracle_lag_seconds": item.oracle_lag_seconds,
        "open_resolution_items": item.open_resolution_items,
        "monitoring_capacity_units": item.monitoring_capacity_units,
        "evidence_age_pressure": evidence_age_pressure,
        "deadline_pressure": deadline_pressure,
        "source_reliability_pressure": source_reliability_pressure,
        "oracle_lag_pressure": oracle_lag_pressure,
        "capacity_pressure": capacity_pressure,
        "rotation_pressure": rotation_pressure,
        "monitoring_interval_seconds": _monitoring_interval(status, config),
        "status": status,
        "reason_codes": _row_reason_codes(
            item.reason_codes,
            evidence_age_pressure=evidence_age_pressure,
            deadline_pressure=deadline_pressure,
            source_reliability_pressure=source_reliability_pressure,
            oracle_lag_pressure=oracle_lag_pressure,
            capacity_pressure=capacity_pressure,
            status=status,
        ),
    }


def _evidence_age_pressure(
    item: ResearchEventResolutionMonitoringRotationInput,
    config: ResearchEventResolutionMonitoringRotationConfig,
) -> Decimal:
    if item.aggregate_evidence_age_seconds <= config.fresh_evidence_age_seconds:
        return ZERO.quantize(RATIO_QUANTUM)
    return _bounded_ratio(
        item.aggregate_evidence_age_seconds,
        config.stale_evidence_age_seconds,
    )


def _deadline_pressure(
    item: ResearchEventResolutionMonitoringRotationInput,
    config: ResearchEventResolutionMonitoringRotationConfig,
) -> Decimal:
    if item.deadline_proximity_seconds >= config.deadline_window_seconds:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(
        ONE - _bounded_ratio(
            item.deadline_proximity_seconds,
            config.deadline_window_seconds,
        ),
    )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _quantize(max(ZERO, min(ONE, numerator / denominator)))


def _row_status(
    rotation_pressure: Decimal,
    config: ResearchEventResolutionMonitoringRotationConfig,
) -> str:
    if rotation_pressure >= config.block_rotation_pressure:
        return BLOCK_STATUS
    if rotation_pressure >= config.watch_rotation_pressure:
        return WATCH_STATUS
    return PASS_STATUS


def _monitoring_interval(
    status: str,
    config: ResearchEventResolutionMonitoringRotationConfig,
) -> Decimal:
    if status == BLOCK_STATUS:
        return config.block_monitoring_interval_seconds
    if status == WATCH_STATUS:
        return config.watch_monitoring_interval_seconds
    return config.pass_monitoring_interval_seconds


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    evidence_age_pressure: Decimal,
    deadline_pressure: Decimal,
    source_reliability_pressure: Decimal,
    oracle_lag_pressure: Decimal,
    capacity_pressure: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes = {
        f"rotation_{status}",
        "evidence_stale" if evidence_age_pressure >= ONE else "evidence_fresh",
        (
            "resolution_deadline_near"
            if deadline_pressure > ZERO
            else "resolution_deadline_not_near"
        ),
        (
            "source_reliability_low"
            if source_reliability_pressure >= Decimal("0.500000")
            else "source_reliability_high"
        ),
        "oracle_lag_elevated" if oracle_lag_pressure > ZERO else "oracle_lag_clear",
        (
            "capacity_constrained"
            if capacity_pressure >= Decimal("0.750000")
            else "capacity_available"
        ),
    }
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_inputs(
    inputs: Iterable[ResearchEventResolutionMonitoringRotationInput],
) -> tuple[ResearchEventResolutionMonitoringRotationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventResolutionMonitoringRotationInput:
            raise ValueError(
                "inputs must contain ResearchEventResolutionMonitoringRotationInput values",
            )
        _require_hard_flags("input", value)
    return values


def _normalize_rows(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
) -> tuple[ResearchEventResolutionMonitoringRotationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionMonitoringRotationRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionMonitoringRotationRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (row.rotation_priority, row.rotation_bucket)),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by rotation_priority")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventResolutionMonitoringRotationReasonCodeCount, ...],
) -> tuple[ResearchEventResolutionMonitoringRotationReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventResolutionMonitoringRotationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionMonitoringRotationReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchEventResolutionMonitoringRotationRow) -> None:
    expected_reason_code = f"rotation_{row.status}"
    if expected_reason_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.rotation_pressure >= DEFAULT_WATCH_ROTATION_PRESSURE:
        raise ValueError("rotation_pressure must support status")
    if row.status == WATCH_STATUS and (
        row.rotation_pressure < DEFAULT_WATCH_ROTATION_PRESSURE
        or row.rotation_pressure >= DEFAULT_BLOCK_ROTATION_PRESSURE
    ):
        raise ValueError("rotation_pressure must support status")
    if row.status == BLOCK_STATUS and row.rotation_pressure < DEFAULT_BLOCK_ROTATION_PRESSURE:
        raise ValueError("rotation_pressure must support status")


def _validate_report(report: ResearchEventResolutionMonitoringRotationReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.average_rotation_pressure != _average_rotation_pressure(report.rows):
        raise ValueError("average_rotation_pressure must match rows")
    if report.max_rotation_pressure != _max_rotation_pressure(report.rows):
        raise ValueError("max_rotation_pressure must match rows")
    if report.near_deadline_count != _reason_count(report.rows, "resolution_deadline_near"):
        raise ValueError("near_deadline_count must match rows")
    if report.stale_evidence_count != _reason_count(report.rows, "evidence_stale"):
        raise ValueError("stale_evidence_count must match rows")
    if report.oracle_lag_count != _reason_count(report.rows, "oracle_lag_elevated"):
        raise ValueError("oracle_lag_count must match rows")
    if report.constrained_capacity_count != _reason_count(
        report.rows,
        "capacity_constrained",
    ):
        raise ValueError("constrained_capacity_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _derived_validation_digest(
        _report_values_for_digest(report),
    ):
        raise ValueError("derived_validation_digest must match report")


def _status_count(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_rotation_pressure(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.rotation_pressure for row in rows), ZERO) / Decimal(len(rows)))


def _max_rotation_pressure(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.rotation_pressure for row in rows)


def _report_status(rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_monitoring_aggregates",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionMonitoringRotationRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionMonitoringRotationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionMonitoringRotationReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventResolutionMonitoringRotationReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _report_values_for_digest(
    report: ResearchEventResolutionMonitoringRotationReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "input_count": report.input_count,
        "row_count": report.row_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_rotation_pressure": report.average_rotation_pressure,
        "max_rotation_pressure": report.max_rotation_pressure,
        "near_deadline_count": report.near_deadline_count,
        "stale_evidence_count": report.stale_evidence_count,
        "oracle_lag_count": report.oracle_lag_count,
        "constrained_capacity_count": report.constrained_capacity_count,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "reason_code_counts": tuple(asdict(item) for item in report.reason_code_counts),
        "rows": tuple(asdict(row) for row in report.rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _derived_validation_digest(value: dict[str, Any]) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_bucket(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    unsafe_fragments = (
        "raw-",
        "event-",
        "evt-",
        "market-",
        "mkt-",
        "source-",
        "src-",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} must be an aggregate public bucket")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_validation_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if not all(character in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"payload {flag_name} must be True")


def _reject_unsafe_public_payload_text(value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(
            fragment in lowered
            for fragment in ("raw-", "event-", "evt-", "market-", "mkt-", "source-", "src-")
        ):
            raise ValueError("payload contains unsafe public text")
    elif isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_payload_text(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload_text(item)
