"""Paper-only calibration gate reducer for strategy assessment pre-layers.

This module is pure report assembly over caller-supplied forecast calibration
reports. It is side-effect free and only summarizes in-memory inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.forecast_calibration import PaperForecastCalibrationReport
from polymarket_alpha_lab.forecast_calibration_trend import (
    PaperForecastCalibrationTrendReport,
)


__all__ = (
    "PaperCalibrationGateConfig",
    "PaperCalibrationGateRow",
    "PaperCalibrationGateReport",
    "build_paper_calibration_gate_report",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SOURCE_REPORT_KINDS = (
    "forecast_calibration_report",
    "forecast_calibration_trend",
)
GATE_NAMES = (
    "calibration_history",
    "observation_count",
    "brier_score",
    "calibration_error",
)
GATE_STATUSES = ("passed", "watch", "blocked")
REPORT_STATUSES = ("passed", "watch", "blocked")


@dataclass(frozen=True)
class PaperCalibrationGateConfig:
    config_version: str
    min_calibration_report_count: int = 1
    min_observation_count: int = 30
    max_brier_score: Decimal = Decimal("0.250000")
    max_calibration_error: Decimal = Decimal("0.100000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_calibration_report_count",
            self.min_calibration_report_count,
        )
        _require_nonnegative_int("min_observation_count", self.min_observation_count)
        _require_probability_decimal("max_brier_score", self.max_brier_score)
        _require_probability_decimal(
            "max_calibration_error",
            self.max_calibration_error,
        )


@dataclass(frozen=True)
class PaperCalibrationGateRow:
    gate_name: str
    status: str
    reason_code: str
    observed_value: Decimal | int | None
    threshold: Decimal | int

    def __post_init__(self) -> None:
        _require_canonical_string("gate_name", self.gate_name)
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known calibration gate")
        _require_canonical_string("status", self.status)
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known calibration gate status")
        _require_canonical_string("reason_code", self.reason_code)
        _require_gate_scalar("observed_value", self.observed_value, allow_none=True)
        _require_gate_scalar("threshold", self.threshold, allow_none=False)


@dataclass(frozen=True)
class PaperCalibrationGateReport:
    generated_at: datetime
    config_version: str
    source_report_kind: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    passed: bool
    reason_codes: tuple[str, ...]
    gate_count: int
    passed_gate_count: int
    watch_gate_count: int
    blocked_gate_count: int
    gate_rows: tuple[PaperCalibrationGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc(self.source_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_report_kind", self.source_report_kind)
        if self.source_report_kind not in SOURCE_REPORT_KINDS:
            raise ValueError("source_report_kind must be a known calibration source")
        _require_canonical_string(
            "source_config_version",
            self.source_config_version,
        )
        _require_canonical_string("gate_status", self.gate_status)
        if self.gate_status not in REPORT_STATUSES:
            raise ValueError("gate_status must be a known calibration gate status")
        if type(self.passed) is not bool:
            raise ValueError("passed must be a bool")
        for field_name in (
            "gate_count",
            "passed_gate_count",
            "watch_gate_count",
            "blocked_gate_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "gate_rows", _clone_gate_rows(self.gate_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_calibration_gate_report(
    source_report: PaperForecastCalibrationReport | PaperForecastCalibrationTrendReport,
    *,
    config: PaperCalibrationGateConfig,
    generated_at: datetime,
) -> PaperCalibrationGateReport:
    """Reduce paper calibration evidence into a report-only pre-layer gate."""

    if type(config) is not PaperCalibrationGateConfig:
        raise ValueError("config must be a PaperCalibrationGateConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    source = _source_view(source_report)
    _require_source_flags(source_report)

    gate_rows = (
        _build_calibration_history_gate(source.calibration_report_count, config),
        _build_observation_count_gate(source.latest_observation_count, config),
        _build_brier_score_gate(source.latest_brier_score, config),
        _build_calibration_error_gate(
            source.latest_expected_calibration_error,
            config,
        ),
    )
    blocked_gate_count = _count_status(gate_rows, "blocked")
    watch_gate_count = _count_status(gate_rows, "watch")
    passed_gate_count = _count_status(gate_rows, "passed")
    gate_status = _report_status(blocked_gate_count, watch_gate_count)

    return PaperCalibrationGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_kind=source.source_report_kind,
        source_config_version=source.source_config_version,
        source_generated_at=source.source_generated_at,
        gate_status=gate_status,
        passed=gate_status == "passed",
        reason_codes=tuple(row.reason_code for row in gate_rows),
        gate_count=len(gate_rows),
        passed_gate_count=passed_gate_count,
        watch_gate_count=watch_gate_count,
        blocked_gate_count=blocked_gate_count,
        gate_rows=gate_rows,
    )


@dataclass(frozen=True)
class _CalibrationSourceView:
    source_report_kind: str
    source_config_version: str
    source_generated_at: datetime
    calibration_report_count: int
    latest_observation_count: int
    latest_brier_score: Decimal | None
    latest_expected_calibration_error: Decimal | None


def _source_view(
    source_report: PaperForecastCalibrationReport | PaperForecastCalibrationTrendReport,
) -> _CalibrationSourceView:
    if type(source_report) is PaperForecastCalibrationTrendReport:
        return _CalibrationSourceView(
            source_report_kind="forecast_calibration_trend",
            source_config_version=source_report.config_version,
            source_generated_at=source_report.generated_at,
            calibration_report_count=source_report.calibration_report_count,
            latest_observation_count=source_report.latest_observation_count,
            latest_brier_score=source_report.latest_brier_score,
            latest_expected_calibration_error=(
                source_report.latest_expected_calibration_error
            ),
        )
    if type(source_report) is PaperForecastCalibrationReport:
        return _CalibrationSourceView(
            source_report_kind="forecast_calibration_report",
            source_config_version=source_report.config_version,
            source_generated_at=source_report.generated_at,
            calibration_report_count=1,
            latest_observation_count=source_report.observation_count,
            latest_brier_score=source_report.brier_score,
            latest_expected_calibration_error=source_report.expected_calibration_error,
        )
    raise ValueError(
        "source_report must be a PaperForecastCalibrationReport or "
        "PaperForecastCalibrationTrendReport",
    )


def _build_calibration_history_gate(
    calibration_report_count: int,
    config: PaperCalibrationGateConfig,
) -> PaperCalibrationGateRow:
    if calibration_report_count == 0:
        status = "watch"
        reason_code = "calibration_history_empty"
    elif calibration_report_count < config.min_calibration_report_count:
        status = "watch"
        reason_code = "calibration_history_insufficient"
    else:
        status = "passed"
        reason_code = "calibration_history_ready"
    return PaperCalibrationGateRow(
        "calibration_history",
        status,
        reason_code,
        calibration_report_count,
        config.min_calibration_report_count,
    )


def _build_observation_count_gate(
    observation_count: int,
    config: PaperCalibrationGateConfig,
) -> PaperCalibrationGateRow:
    if observation_count < config.min_observation_count:
        status = "watch"
        reason_code = "observation_count_insufficient"
    else:
        status = "passed"
        reason_code = "observation_count_ready"
    return PaperCalibrationGateRow(
        "observation_count",
        status,
        reason_code,
        observation_count,
        config.min_observation_count,
    )


def _build_brier_score_gate(
    brier_score: Decimal | None,
    config: PaperCalibrationGateConfig,
) -> PaperCalibrationGateRow:
    if brier_score is None:
        status = "watch"
        reason_code = "brier_score_unavailable"
    elif brier_score > config.max_brier_score:
        status = "blocked"
        reason_code = "brier_score_above_limit"
    else:
        status = "passed"
        reason_code = "brier_score_within_limit"
    return PaperCalibrationGateRow(
        "brier_score",
        status,
        reason_code,
        brier_score,
        config.max_brier_score,
    )


def _build_calibration_error_gate(
    calibration_error: Decimal | None,
    config: PaperCalibrationGateConfig,
) -> PaperCalibrationGateRow:
    if calibration_error is None:
        status = "watch"
        reason_code = "calibration_error_unavailable"
    elif calibration_error > config.max_calibration_error:
        status = "blocked"
        reason_code = "calibration_error_above_limit"
    else:
        status = "passed"
        reason_code = "calibration_error_within_limit"
    return PaperCalibrationGateRow(
        "calibration_error",
        status,
        reason_code,
        calibration_error,
        config.max_calibration_error,
    )


def _report_status(blocked_gate_count: int, watch_gate_count: int) -> str:
    if blocked_gate_count > 0:
        return "blocked"
    if watch_gate_count > 0:
        return "watch"
    return "passed"


def _count_status(rows: tuple[PaperCalibrationGateRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_report_consistency(report: PaperCalibrationGateReport) -> None:
    gate_rows = report.gate_rows
    if tuple(row.gate_name for row in gate_rows) != GATE_NAMES:
        raise ValueError("gate_rows must match the known calibration gates")
    if report.gate_count != len(gate_rows):
        raise ValueError("gate_count must match gate_rows")
    if report.passed_gate_count != _count_status(gate_rows, "passed"):
        raise ValueError("passed_gate_count must match gate_rows")
    if report.watch_gate_count != _count_status(gate_rows, "watch"):
        raise ValueError("watch_gate_count must match gate_rows")
    if report.blocked_gate_count != _count_status(gate_rows, "blocked"):
        raise ValueError("blocked_gate_count must match gate_rows")
    expected_status = _report_status(report.blocked_gate_count, report.watch_gate_count)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match gate_rows")
    if report.passed is not (report.gate_status == "passed"):
        raise ValueError("passed must match gate_status")
    if report.reason_codes != tuple(row.reason_code for row in gate_rows):
        raise ValueError("reason_codes must match gate_rows")


def _clone_gate_rows(
    rows: tuple[PaperCalibrationGateRow, ...],
) -> tuple[PaperCalibrationGateRow, ...]:
    return tuple(
        PaperCalibrationGateRow(
            gate_name=row.gate_name,
            status=row.status,
            reason_code=row.reason_code,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple("gate_rows", rows, PaperCalibrationGateRow)
    )


def _normalize_typed_tuple(
    field_name: str,
    value: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
    return reason_codes


def _require_source_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("source_report paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("source_report report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("source_report readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_gate_scalar(
    field_name: str,
    value: Decimal | int | None,
    *,
    allow_none: bool,
) -> None:
    if value is None:
        if allow_none:
            return
        raise ValueError(f"{field_name} must be an int or Decimal")
    if type(value) is int:
        if value < 0:
            raise ValueError(f"{field_name} must be nonnegative")
        return
    if type(value) is Decimal:
        _require_probability_decimal(field_name, value)
        return
    raise ValueError(f"{field_name} must be an int or Decimal")


def _require_probability_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if (
        value != value.quantize(RATIO_QUANTUM)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")
