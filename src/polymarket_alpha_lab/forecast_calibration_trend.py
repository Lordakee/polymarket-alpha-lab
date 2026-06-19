"""Paper-only forecast calibration trend summaries.

Pure aggregation over already-built ``PaperForecastCalibrationReport`` values.
This module is local/report-only and only describes caller-supplied report
history. It has no external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationReport,
    REPORT_STATUSES,
)


RATIO_QUANTUM = Decimal("0.000001")
RATIO_MICRO_UNITS = 1_000_000
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperForecastCalibrationTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperForecastCalibrationTrendStatusRow:
    calibration_status: str
    report_count: int
    report_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.calibration_status not in REPORT_STATUSES:
            raise ValueError("calibration_status must be a known calibration status")
        _require_nonnegative_int("report_count", self.report_count)
        _require_optional_probability_decimal("report_ratio", self.report_ratio)


@dataclass(frozen=True)
class PaperForecastCalibrationTrendReport:
    generated_at: datetime
    config_version: str
    calibration_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_status: str | None
    latest_observation_count: int
    latest_brier_score: Decimal | None
    latest_mean_absolute_error: Decimal | None
    latest_expected_calibration_error: Decimal | None
    latest_max_bucket_error: Decimal | None
    latest_bucket_count: int
    worst_observed_brier_score: Decimal | None
    worst_observed_expected_calibration_error: Decimal | None
    worst_observed_max_bucket_error: Decimal | None
    consecutive_insufficient_sample_count: int
    consecutive_quality_flag_count: int
    status_rows: tuple[PaperForecastCalibrationTrendStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(self.first_report_generated_at),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(self.latest_report_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "calibration_report_count",
            "latest_observation_count",
            "latest_bucket_count",
            "consecutive_insufficient_sample_count",
            "consecutive_quality_flag_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.latest_status is not None and self.latest_status not in REPORT_STATUSES:
            raise ValueError("latest_status must be a known calibration status")
        for field_name in (
            "latest_brier_score",
            "latest_mean_absolute_error",
            "latest_expected_calibration_error",
            "latest_max_bucket_error",
            "worst_observed_brier_score",
            "worst_observed_expected_calibration_error",
            "worst_observed_max_bucket_error",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "status_rows",
            _clone_status_rows(self.status_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_forecast_calibration_trend_report(
    reports: list[PaperForecastCalibrationReport]
    | tuple[PaperForecastCalibrationReport, ...],
    *,
    config: PaperForecastCalibrationTrendConfig,
    generated_at: datetime,
) -> PaperForecastCalibrationTrendReport:
    """Aggregate local paper forecast calibration reports into a trend snapshot."""

    if type(config) is not PaperForecastCalibrationTrendConfig:
        raise ValueError("config must be a PaperForecastCalibrationTrendConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    generated_at = _as_utc(generated_at)

    calibration_reports = _normalize_reports(reports)
    for report in calibration_reports[:-1]:
        if report.generated_at > generated_at:
            raise ValueError("source report generated_at must not be after generated_at")
    report_count = len(calibration_reports)
    status_counts = _status_counts(calibration_reports)
    latest = calibration_reports[-1] if calibration_reports else None

    return PaperForecastCalibrationTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        calibration_report_count=report_count,
        first_report_generated_at=(
            calibration_reports[0].generated_at if calibration_reports else None
        ),
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_status=latest.status if latest is not None else None,
        latest_observation_count=latest.observation_count if latest is not None else 0,
        latest_brier_score=latest.brier_score if latest is not None else None,
        latest_mean_absolute_error=(
            latest.mean_absolute_error if latest is not None else None
        ),
        latest_expected_calibration_error=(
            latest.expected_calibration_error if latest is not None else None
        ),
        latest_max_bucket_error=latest.max_bucket_error if latest is not None else None,
        latest_bucket_count=latest.bucket_count if latest is not None else 0,
        worst_observed_brier_score=_max_observed(
            report.brier_score for report in calibration_reports
        ),
        worst_observed_expected_calibration_error=_max_observed(
            report.expected_calibration_error for report in calibration_reports
        ),
        worst_observed_max_bucket_error=_max_observed(
            report.max_bucket_error for report in calibration_reports
        ),
        consecutive_insufficient_sample_count=_consecutive_status_count(
            calibration_reports,
            "insufficient_calibration_sample",
        ),
        consecutive_quality_flag_count=_consecutive_status_count(
            calibration_reports,
            "calibration_quality_flags",
        ),
        status_rows=_build_status_rows(status_counts, report_count),
    )


def _normalize_reports(
    reports: list[PaperForecastCalibrationReport]
    | tuple[PaperForecastCalibrationReport, ...],
) -> tuple[PaperForecastCalibrationReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    normalized = tuple(reports)
    for report in normalized:
        if type(report) is not PaperForecastCalibrationReport:
            raise ValueError(
                "reports must contain PaperForecastCalibrationReport values",
            )
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only calibration reports")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only calibration reports")
        if report.readonly is not True:
            raise ValueError("reports must contain readonly calibration reports")
    return normalized


def _status_counts(
    reports: tuple[PaperForecastCalibrationReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in REPORT_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperForecastCalibrationTrendStatusRow, ...]:
    ratios = _ratios_from_counts(
        tuple(status_counts[status] for status in REPORT_STATUSES),
        total,
    )
    return tuple(
        PaperForecastCalibrationTrendStatusRow(
            calibration_status=status,
            report_count=status_counts[status],
            report_ratio=ratio,
        )
        for status, ratio in zip(REPORT_STATUSES, ratios, strict=True)
    )


def _max_observed(values: Any) -> Decimal | None:
    observed = tuple(value for value in values if value is not None)
    return max(observed) if observed else None


def _consecutive_status_count(
    reports: tuple[PaperForecastCalibrationReport, ...],
    status: str,
) -> int:
    count = 0
    for report in reversed(reports):
        if report.status != status:
            break
        count += 1
    return count


def _ratios_from_counts(
    counts: tuple[int, ...],
    total: int,
) -> tuple[Decimal | None, ...]:
    if total == 0:
        return tuple(None for _ in counts)

    base_units: list[int] = []
    remainders: list[tuple[int, int]] = []
    for index, count in enumerate(counts):
        numerator = count * RATIO_MICRO_UNITS
        units, remainder = divmod(numerator, total)
        base_units.append(units)
        remainders.append((remainder, index))

    units_to_allocate = RATIO_MICRO_UNITS - sum(base_units)
    for _, index in sorted(remainders, key=lambda item: (-item[0], item[1]))[
        :units_to_allocate
    ]:
        base_units[index] += 1

    return tuple(
        (Decimal(units) / Decimal(RATIO_MICRO_UNITS)).quantize(RATIO_QUANTUM)
        for units in base_units
    )


def _validate_report_consistency(
    report: PaperForecastCalibrationTrendReport,
) -> None:
    if report.calibration_report_count == 0:
        if report.first_report_generated_at is not None:
            raise ValueError("first_report_generated_at must be absent without reports")
        if report.latest_report_generated_at is not None:
            raise ValueError("latest_report_generated_at must be absent without reports")
        if report.latest_status is not None:
            raise ValueError("latest_status must be absent without reports")
        _require_zero(
            "latest_observation_count",
            report.latest_observation_count,
        )
        _require_zero("latest_bucket_count", report.latest_bucket_count)
        for field_name in (
            "latest_brier_score",
            "latest_mean_absolute_error",
            "latest_expected_calibration_error",
            "latest_max_bucket_error",
            "worst_observed_brier_score",
            "worst_observed_expected_calibration_error",
            "worst_observed_max_bucket_error",
        ):
            _require_none(field_name, getattr(report, field_name))
        _require_zero(
            "consecutive_insufficient_sample_count",
            report.consecutive_insufficient_sample_count,
        )
        _require_zero(
            "consecutive_quality_flag_count",
            report.consecutive_quality_flag_count,
        )
    else:
        if report.first_report_generated_at is None:
            raise ValueError("first_report_generated_at is required with reports")
        if report.latest_report_generated_at is None:
            raise ValueError("latest_report_generated_at is required with reports")
        if report.latest_status is None:
            raise ValueError("latest_status is required with reports")
        if report.latest_report_generated_at is not None and (
            report.latest_report_generated_at > report.generated_at
        ):
            raise ValueError("latest_report_generated_at must not be after generated_at")
        if report.first_report_generated_at is not None and (
            report.first_report_generated_at > report.generated_at
        ):
            raise ValueError("first_report_generated_at must not be after generated_at")
        _validate_latest_status_metrics(report)
        _validate_latest_status_row_membership(report)
        if report.consecutive_insufficient_sample_count > report.calibration_report_count:
            raise ValueError("insufficient sample streak must not exceed report count")
        if report.consecutive_quality_flag_count > report.calibration_report_count:
            raise ValueError("quality flag streak must not exceed report count")
        status_counts = _counts_from_status_rows(report.status_rows)
        if (
            report.consecutive_insufficient_sample_count
            > status_counts["insufficient_calibration_sample"]
        ):
            raise ValueError("insufficient sample streak must not exceed status rows")
        if (
            report.consecutive_quality_flag_count
            > status_counts["calibration_quality_flags"]
        ):
            raise ValueError("quality flag streak must not exceed status rows")
        if report.latest_status == "insufficient_calibration_sample":
            if report.consecutive_insufficient_sample_count < 1:
                raise ValueError("insufficient sample latest report requires a streak")
            if report.consecutive_quality_flag_count != 0:
                raise ValueError("insufficient sample latest report resets quality flag streak")
        elif report.latest_status == "calibration_quality_flags":
            if report.consecutive_quality_flag_count < 1:
                raise ValueError("quality flag latest report requires a quality flag streak")
            if report.consecutive_insufficient_sample_count != 0:
                raise ValueError("quality flag latest report resets insufficient sample streak")
        else:
            if report.consecutive_insufficient_sample_count != 0:
                raise ValueError("observed latest report resets insufficient sample streak")
            if report.consecutive_quality_flag_count != 0:
                raise ValueError("observed latest report resets quality flag streak")
        _validate_worst_not_below_latest(
            "worst_observed_brier_score",
            report.worst_observed_brier_score,
            report.latest_brier_score,
        )
        _validate_worst_not_below_latest(
            "worst_observed_expected_calibration_error",
            report.worst_observed_expected_calibration_error,
            report.latest_expected_calibration_error,
        )
        _validate_worst_not_below_latest(
            "worst_observed_max_bucket_error",
            report.worst_observed_max_bucket_error,
            report.latest_max_bucket_error,
        )

    _validate_status_rows(report)


def _validate_status_rows(report: PaperForecastCalibrationTrendReport) -> None:
    if tuple(row.calibration_status for row in report.status_rows) != REPORT_STATUSES:
        raise ValueError("status_rows must cover calibration statuses")
    if (
        sum(row.report_count for row in report.status_rows)
        != report.calibration_report_count
    ):
        raise ValueError("status_rows counts must sum to calibration_report_count")
    expected_ratios = _ratios_from_counts(
        tuple(row.report_count for row in report.status_rows),
        report.calibration_report_count,
    )
    for row, expected_ratio in zip(report.status_rows, expected_ratios, strict=True):
        if row.report_ratio != expected_ratio:
            raise ValueError("status_rows ratios must match report counts")


def _counts_from_status_rows(
    rows: tuple[PaperForecastCalibrationTrendStatusRow, ...],
) -> dict[str, int]:
    return {row.calibration_status: row.report_count for row in rows}


def _validate_latest_status_row_membership(
    report: PaperForecastCalibrationTrendReport,
) -> None:
    counts = _counts_from_status_rows(report.status_rows)
    if report.latest_status is None:
        return
    if counts[report.latest_status] < 1:
        raise ValueError("latest_status must be counted in status_rows")


def _validate_latest_status_metrics(report: PaperForecastCalibrationTrendReport) -> None:
    if report.latest_status == "empty_calibration_history":
        if report.latest_observation_count != 0:
            raise ValueError("latest_observation_count must be zero for empty status")
        if report.latest_bucket_count != 0:
            raise ValueError("latest_bucket_count must be zero for empty status")
        for field_name in (
            "latest_brier_score",
            "latest_mean_absolute_error",
            "latest_expected_calibration_error",
            "latest_max_bucket_error",
        ):
            if getattr(report, field_name) is not None:
                raise ValueError(f"{field_name} must be absent for empty status")
        return
    if report.latest_observation_count == 0:
        raise ValueError("latest_observation_count is required for latest_status")
    if report.latest_bucket_count == 0:
        raise ValueError("latest_bucket_count is required for latest_status")
    for field_name in (
        "latest_brier_score",
        "latest_mean_absolute_error",
        "latest_expected_calibration_error",
        "latest_max_bucket_error",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required for latest_status")


def _validate_worst_not_below_latest(
    field_name: str,
    worst: Decimal | None,
    latest: Decimal | None,
) -> None:
    if latest is None:
        return
    if worst is None:
        raise ValueError(f"{field_name} is required when latest metric is observed")
    if worst < latest:
        raise ValueError(f"{field_name} cannot be below latest metric")


def _clone_status_rows(
    rows: tuple[PaperForecastCalibrationTrendStatusRow, ...],
) -> tuple[PaperForecastCalibrationTrendStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("status_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("status_rows must be an iterable") from exc
    for row in items:
        _require_status_row(row)
    return tuple(
        (
            PaperForecastCalibrationTrendStatusRow(
                calibration_status=row.calibration_status,
                report_count=row.report_count,
                report_ratio=row.report_ratio,
            )
        )
        for row in items
    )


def _require_status_row(row: Any) -> None:
    if type(row) is not PaperForecastCalibrationTrendStatusRow:
        raise ValueError(
            "status_rows must contain PaperForecastCalibrationTrendStatusRow values",
        )


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_none(field_name: str, value: Any) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no reports")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero when there are no reports")


__all__ = (
    "PaperForecastCalibrationTrendConfig",
    "PaperForecastCalibrationTrendStatusRow",
    "PaperForecastCalibrationTrendReport",
    "build_paper_forecast_calibration_trend_report",
)
