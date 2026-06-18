"""Pure trend reducer for paper edge cost summary reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.edge_cost_summary import (
    EDGE_COST_SUMMARY_STATUSES,
    PaperEdgeCostSummaryReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperEdgeCostSummaryTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperEdgeCostSummaryTrendStatusRow:
    edge_cost_status: str
    report_count: int
    report_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.edge_cost_status not in EDGE_COST_SUMMARY_STATUSES:
            raise ValueError("edge_cost_status must be a known edge cost summary status")
        _require_nonnegative_int("report_count", self.report_count)
        _require_optional_probability_decimal("report_ratio", self.report_ratio)


@dataclass(frozen=True)
class PaperEdgeCostSummaryTrendReport:
    generated_at: datetime
    config_version: str
    edge_cost_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_status: str | None
    latest_edge_observation_count: int
    latest_mean_theoretical_edge_ratio: Decimal | None
    latest_mean_executable_edge_ratio: Decimal | None
    latest_mean_edge_cost_drag: Decimal | None
    latest_mean_fill_probability: Decimal | None
    latest_mean_residual_exposure_ratio: Decimal | None
    latest_mean_paper_return_ratio: Decimal | None
    latest_negative_executable_edge_count: int
    latest_negative_executable_edge_rate: Decimal | None
    latest_low_fill_probability_count: int
    latest_low_fill_probability_rate: Decimal | None
    latest_high_residual_exposure_count: int
    latest_high_residual_exposure_rate: Decimal | None
    latest_positive_paper_return_count: int
    latest_positive_paper_return_rate: Decimal | None
    largest_negative_executable_edge_count: int
    largest_low_fill_probability_count: int
    largest_high_residual_exposure_count: int
    worst_observed_mean_edge_cost_drag: Decimal | None
    worst_observed_mean_residual_exposure_ratio: Decimal | None
    consecutive_quality_flag_count: int
    consecutive_insufficient_sample_count: int
    status_rows: tuple[PaperEdgeCostSummaryTrendStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
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
            "edge_cost_report_count",
            "latest_edge_observation_count",
            "latest_negative_executable_edge_count",
            "latest_low_fill_probability_count",
            "latest_high_residual_exposure_count",
            "latest_positive_paper_return_count",
            "largest_negative_executable_edge_count",
            "largest_low_fill_probability_count",
            "largest_high_residual_exposure_count",
            "consecutive_quality_flag_count",
            "consecutive_insufficient_sample_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "latest_mean_theoretical_edge_ratio",
            "latest_mean_executable_edge_ratio",
            "latest_mean_edge_cost_drag",
            "latest_mean_fill_probability",
            "latest_mean_residual_exposure_ratio",
            "latest_mean_paper_return_ratio",
            "worst_observed_mean_edge_cost_drag",
            "worst_observed_mean_residual_exposure_ratio",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "latest_negative_executable_edge_rate",
            "latest_low_fill_probability_rate",
            "latest_high_residual_exposure_rate",
            "latest_positive_paper_return_rate",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.latest_status is not None and self.latest_status not in EDGE_COST_SUMMARY_STATUSES:
            raise ValueError("latest_status must be a known edge cost summary status")
        object.__setattr__(self, "status_rows", _normalize_status_rows(self.status_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_edge_cost_summary_trend_report(
    reports: list[PaperEdgeCostSummaryReport] | tuple[PaperEdgeCostSummaryReport, ...],
    *,
    config: PaperEdgeCostSummaryTrendConfig,
    generated_at: datetime,
) -> PaperEdgeCostSummaryTrendReport:
    """Aggregate paper edge-cost summary reports into a trend snapshot."""

    if type(config) is not PaperEdgeCostSummaryTrendConfig:
        raise ValueError("config must be a PaperEdgeCostSummaryTrendConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    edge_cost_reports = _normalize_reports(reports)
    report_count = len(edge_cost_reports)
    status_counts = _status_counts(edge_cost_reports)
    latest = edge_cost_reports[-1] if edge_cost_reports else None

    return PaperEdgeCostSummaryTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        edge_cost_report_count=report_count,
        first_report_generated_at=(
            edge_cost_reports[0].generated_at if edge_cost_reports else None
        ),
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_status=latest.status if latest is not None else None,
        latest_edge_observation_count=(
            latest.edge_observation_count if latest is not None else 0
        ),
        latest_mean_theoretical_edge_ratio=(
            latest.mean_theoretical_edge_ratio if latest is not None else None
        ),
        latest_mean_executable_edge_ratio=(
            latest.mean_executable_edge_ratio if latest is not None else None
        ),
        latest_mean_edge_cost_drag=latest.mean_edge_cost_drag if latest is not None else None,
        latest_mean_fill_probability=(
            latest.mean_fill_probability if latest is not None else None
        ),
        latest_mean_residual_exposure_ratio=(
            latest.mean_residual_exposure_ratio if latest is not None else None
        ),
        latest_mean_paper_return_ratio=(
            latest.mean_paper_return_ratio if latest is not None else None
        ),
        latest_negative_executable_edge_count=(
            latest.negative_executable_edge_count if latest is not None else 0
        ),
        latest_negative_executable_edge_rate=(
            _canonical_optional_ratio(latest.negative_executable_edge_rate)
            if latest is not None
            else None
        ),
        latest_low_fill_probability_count=(
            latest.low_fill_probability_count if latest is not None else 0
        ),
        latest_low_fill_probability_rate=(
            _canonical_optional_ratio(latest.low_fill_probability_rate)
            if latest is not None
            else None
        ),
        latest_high_residual_exposure_count=(
            latest.high_residual_exposure_count if latest is not None else 0
        ),
        latest_high_residual_exposure_rate=(
            _canonical_optional_ratio(latest.high_residual_exposure_rate)
            if latest is not None
            else None
        ),
        latest_positive_paper_return_count=(
            latest.positive_paper_return_count if latest is not None else 0
        ),
        latest_positive_paper_return_rate=(
            _canonical_optional_ratio(latest.positive_paper_return_rate)
            if latest is not None
            else None
        ),
        largest_negative_executable_edge_count=max(
            (report.negative_executable_edge_count for report in edge_cost_reports),
            default=0,
        ),
        largest_low_fill_probability_count=max(
            (report.low_fill_probability_count for report in edge_cost_reports),
            default=0,
        ),
        largest_high_residual_exposure_count=max(
            (report.high_residual_exposure_count for report in edge_cost_reports),
            default=0,
        ),
        worst_observed_mean_edge_cost_drag=_worst_observed_mean_edge_cost_drag(
            edge_cost_reports,
        ),
        worst_observed_mean_residual_exposure_ratio=_worst_observed_mean_residual_exposure_ratio(
            edge_cost_reports,
        ),
        consecutive_quality_flag_count=_consecutive_status_count(
            edge_cost_reports,
            "edge_cost_quality_flags",
        ),
        consecutive_insufficient_sample_count=_consecutive_status_count(
            edge_cost_reports,
            "insufficient_edge_cost_sample",
        ),
        status_rows=_build_status_rows(status_counts, report_count),
    )


def _normalize_reports(
    reports: list[PaperEdgeCostSummaryReport] | tuple[PaperEdgeCostSummaryReport, ...],
) -> tuple[PaperEdgeCostSummaryReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    normalized = tuple(reports)
    for report in normalized:
        if type(report) is not PaperEdgeCostSummaryReport:
            raise ValueError("reports must contain PaperEdgeCostSummaryReport values")
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only edge cost summary reports")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only edge cost summary reports")
        if report.readonly is not True:
            raise ValueError("reports must contain readonly edge cost summary reports")
    return normalized


def _status_counts(
    reports: tuple[PaperEdgeCostSummaryReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in EDGE_COST_SUMMARY_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperEdgeCostSummaryTrendStatusRow, ...]:
    return tuple(
        PaperEdgeCostSummaryTrendStatusRow(
            edge_cost_status=status,
            report_count=status_counts[status],
            report_ratio=_ratio(status_counts[status], total),
        )
        for status in EDGE_COST_SUMMARY_STATUSES
    )


def _consecutive_status_count(
    reports: tuple[PaperEdgeCostSummaryReport, ...],
    status: str,
) -> int:
    count = 0
    for report in reversed(reports):
        if report.status != status:
            break
        count += 1
    return count


def _worst_observed_mean_edge_cost_drag(
    reports: tuple[PaperEdgeCostSummaryReport, ...],
) -> Decimal | None:
    values = tuple(
        report.mean_edge_cost_drag
        for report in reports
        if report.mean_edge_cost_drag is not None
    )
    return max(values) if values else None


def _worst_observed_mean_residual_exposure_ratio(
    reports: tuple[PaperEdgeCostSummaryReport, ...],
) -> Decimal | None:
    values = tuple(
        report.mean_residual_exposure_ratio
        for report in reports
        if report.mean_residual_exposure_ratio is not None
    )
    return max(values) if values else None


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _canonical_optional_ratio(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _validate_report_consistency(report: PaperEdgeCostSummaryTrendReport) -> None:
    _validate_status_rows(report)

    if report.edge_cost_report_count == 0:
        _require_none("first_report_generated_at", report.first_report_generated_at)
        _require_none("latest_report_generated_at", report.latest_report_generated_at)
        _require_none("latest_status", report.latest_status)
        _require_zero("latest_edge_observation_count", report.latest_edge_observation_count)
        for field_name in (
            "latest_mean_theoretical_edge_ratio",
            "latest_mean_executable_edge_ratio",
            "latest_mean_edge_cost_drag",
            "latest_mean_fill_probability",
            "latest_mean_residual_exposure_ratio",
            "latest_mean_paper_return_ratio",
            "latest_negative_executable_edge_rate",
            "latest_low_fill_probability_rate",
            "latest_high_residual_exposure_rate",
            "latest_positive_paper_return_rate",
            "worst_observed_mean_edge_cost_drag",
            "worst_observed_mean_residual_exposure_ratio",
        ):
            _require_none(field_name, getattr(report, field_name))
        for field_name in (
            "latest_negative_executable_edge_count",
            "latest_low_fill_probability_count",
            "latest_high_residual_exposure_count",
            "latest_positive_paper_return_count",
            "largest_negative_executable_edge_count",
            "largest_low_fill_probability_count",
            "largest_high_residual_exposure_count",
            "consecutive_quality_flag_count",
            "consecutive_insufficient_sample_count",
        ):
            _require_zero(field_name, getattr(report, field_name))
        return

    if report.first_report_generated_at is None:
        raise ValueError("first_report_generated_at is required with reports")
    if report.latest_report_generated_at is None:
        raise ValueError("latest_report_generated_at is required with reports")
    if report.latest_status is None:
        raise ValueError("latest_status is required with reports")
    if _status_report_count(report, report.latest_status) < 1:
        raise ValueError("latest_status must be counted in status_rows")
    if report.latest_edge_observation_count == 0:
        if report.latest_status != "empty_edge_cost_history":
            raise ValueError("latest_status must match latest edge cost observations")
        for field_name in (
            "latest_mean_theoretical_edge_ratio",
            "latest_mean_executable_edge_ratio",
            "latest_mean_edge_cost_drag",
            "latest_mean_fill_probability",
            "latest_mean_residual_exposure_ratio",
            "latest_mean_paper_return_ratio",
            "latest_negative_executable_edge_rate",
            "latest_low_fill_probability_rate",
            "latest_high_residual_exposure_rate",
            "latest_positive_paper_return_rate",
        ):
            _require_none(field_name, getattr(report, field_name))
        for field_name in (
            "latest_negative_executable_edge_count",
            "latest_low_fill_probability_count",
            "latest_high_residual_exposure_count",
            "latest_positive_paper_return_count",
        ):
            _require_zero(field_name, getattr(report, field_name))
        if _nonempty_source_report_count(report) == 0:
            _require_zero(
                "largest_negative_executable_edge_count",
                report.largest_negative_executable_edge_count,
            )
            _require_zero(
                "largest_low_fill_probability_count",
                report.largest_low_fill_probability_count,
            )
            _require_zero(
                "largest_high_residual_exposure_count",
                report.largest_high_residual_exposure_count,
            )
            _require_none(
                "worst_observed_mean_edge_cost_drag",
                report.worst_observed_mean_edge_cost_drag,
            )
            _require_none(
                "worst_observed_mean_residual_exposure_ratio",
                report.worst_observed_mean_residual_exposure_ratio,
            )
        else:
            if report.worst_observed_mean_edge_cost_drag is None:
                raise ValueError("worst_observed_mean_edge_cost_drag is required")
            if report.worst_observed_mean_residual_exposure_ratio is None:
                raise ValueError(
                    "worst_observed_mean_residual_exposure_ratio is required"
                )
        _require_zero("consecutive_quality_flag_count", report.consecutive_quality_flag_count)
        _require_zero(
            "consecutive_insufficient_sample_count",
            report.consecutive_insufficient_sample_count,
        )
        return

    for field_name in (
        "latest_mean_theoretical_edge_ratio",
        "latest_mean_executable_edge_ratio",
        "latest_mean_edge_cost_drag",
        "latest_mean_fill_probability",
        "latest_mean_residual_exposure_ratio",
        "latest_mean_paper_return_ratio",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with reports")
    for field_name in (
        "latest_negative_executable_edge_rate",
        "latest_low_fill_probability_rate",
        "latest_high_residual_exposure_rate",
        "latest_positive_paper_return_rate",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with reports")
    for field_name in (
        "latest_negative_executable_edge_count",
        "latest_low_fill_probability_count",
        "latest_high_residual_exposure_count",
        "latest_positive_paper_return_count",
    ):
        if getattr(report, field_name) > report.latest_edge_observation_count:
            raise ValueError(f"{field_name} cannot exceed latest_edge_observation_count")

    expected_rates = (
        (
            "latest_negative_executable_edge_rate",
            report.latest_negative_executable_edge_count,
            report.latest_negative_executable_edge_rate,
        ),
        (
            "latest_low_fill_probability_rate",
            report.latest_low_fill_probability_count,
            report.latest_low_fill_probability_rate,
        ),
        (
            "latest_high_residual_exposure_rate",
            report.latest_high_residual_exposure_count,
            report.latest_high_residual_exposure_rate,
        ),
        (
            "latest_positive_paper_return_rate",
            report.latest_positive_paper_return_count,
            report.latest_positive_paper_return_rate,
        ),
    )
    for field_name, count, rate in expected_rates:
        if rate != _ratio(count, report.latest_edge_observation_count):
            raise ValueError(f"{field_name} must match latest_edge_observation_count")

    if report.latest_status == "empty_edge_cost_history":
        raise ValueError("latest_status must match latest edge cost observations")
    if report.latest_status == "edge_cost_evidence_observed":
        if (
            report.latest_negative_executable_edge_count != 0
            or report.latest_low_fill_probability_count != 0
            or report.latest_high_residual_exposure_count != 0
        ):
            raise ValueError("latest_status must match latest edge cost quality flags")
        if report.consecutive_quality_flag_count != 0:
            raise ValueError("observed latest report resets quality flag streak")
        if report.consecutive_insufficient_sample_count != 0:
            raise ValueError("observed latest report resets insufficient sample streak")
    elif report.latest_status == "insufficient_edge_cost_sample":
        if report.consecutive_insufficient_sample_count < 1:
            raise ValueError("insufficient sample latest report requires a streak")
        if report.consecutive_insufficient_sample_count > _status_report_count(
            report,
            "insufficient_edge_cost_sample",
        ):
            raise ValueError(
                "insufficient sample streak cannot exceed status_rows count"
            )
        if report.consecutive_quality_flag_count != 0:
            raise ValueError("insufficient sample latest report resets quality flag streak")
        if (
            report.latest_negative_executable_edge_count != 0
            or report.latest_low_fill_probability_count != 0
            or report.latest_high_residual_exposure_count != 0
        ):
            raise ValueError("insufficient sample latest report cannot carry quality flags")
    elif report.latest_status == "edge_cost_quality_flags":
        if report.consecutive_quality_flag_count < 1:
            raise ValueError("quality flag latest report requires a quality flag streak")
        if report.consecutive_quality_flag_count > _status_report_count(
            report,
            "edge_cost_quality_flags",
        ):
            raise ValueError("quality flag streak cannot exceed status_rows count")
        if report.consecutive_insufficient_sample_count != 0:
            raise ValueError("quality flag latest report resets insufficient sample streak")
        if (
            report.latest_negative_executable_edge_count == 0
            and report.latest_low_fill_probability_count == 0
            and report.latest_high_residual_exposure_count == 0
        ):
            raise ValueError("latest_status must match latest edge cost quality flags")
    else:
        raise ValueError("latest_status must match latest edge cost observations")

    if report.latest_mean_edge_cost_drag is not None:
        if report.worst_observed_mean_edge_cost_drag is None:
            raise ValueError("worst_observed_mean_edge_cost_drag is required")
    if (
        report.worst_observed_mean_edge_cost_drag is not None
        and report.latest_mean_edge_cost_drag is not None
        and report.worst_observed_mean_edge_cost_drag < report.latest_mean_edge_cost_drag
    ):
        raise ValueError("worst_observed_mean_edge_cost_drag cannot be below latest metric")
    if report.latest_mean_residual_exposure_ratio is not None:
        if report.worst_observed_mean_residual_exposure_ratio is None:
            raise ValueError("worst_observed_mean_residual_exposure_ratio is required")
    if (
        report.worst_observed_mean_residual_exposure_ratio is not None
        and report.latest_mean_residual_exposure_ratio is not None
        and report.worst_observed_mean_residual_exposure_ratio
        < report.latest_mean_residual_exposure_ratio
    ):
        raise ValueError(
            "worst_observed_mean_residual_exposure_ratio cannot be below latest metric"
        )
    if report.largest_negative_executable_edge_count < report.latest_negative_executable_edge_count:
        raise ValueError(
            "largest_negative_executable_edge_count cannot be below latest count"
        )
    if report.largest_low_fill_probability_count < report.latest_low_fill_probability_count:
        raise ValueError(
            "largest_low_fill_probability_count cannot be below latest count"
        )
    if (
        report.largest_high_residual_exposure_count
        < report.latest_high_residual_exposure_count
    ):
        raise ValueError(
            "largest_high_residual_exposure_count cannot be below latest count"
        )


def _validate_status_rows(report: PaperEdgeCostSummaryTrendReport) -> None:
    if tuple(row.edge_cost_status for row in report.status_rows) != EDGE_COST_SUMMARY_STATUSES:
        raise ValueError("status_rows must cover edge cost summary statuses")
    if sum(row.report_count for row in report.status_rows) != report.edge_cost_report_count:
        raise ValueError("status_rows counts must sum to edge_cost_report_count")
    for row in report.status_rows:
        if row.report_ratio != _ratio(row.report_count, report.edge_cost_report_count):
            raise ValueError("status_rows ratios must match report counts")


def _nonempty_source_report_count(report: PaperEdgeCostSummaryTrendReport) -> int:
    empty_count = next(
        row.report_count
        for row in report.status_rows
        if row.edge_cost_status == "empty_edge_cost_history"
    )
    return report.edge_cost_report_count - empty_count


def _status_report_count(
    report: PaperEdgeCostSummaryTrendReport,
    status: str,
) -> int:
    return next(
        row.report_count for row in report.status_rows if row.edge_cost_status == status
    )


def _clone_status_rows(
    rows: tuple[PaperEdgeCostSummaryTrendStatusRow, ...],
) -> tuple[PaperEdgeCostSummaryTrendStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("status_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("status_rows must be an iterable") from exc
    for row in items:
        if type(row) is not PaperEdgeCostSummaryTrendStatusRow:
            raise ValueError(
                "status_rows must contain PaperEdgeCostSummaryTrendStatusRow values",
            )
    return tuple(
        PaperEdgeCostSummaryTrendStatusRow(
            edge_cost_status=row.edge_cost_status,
            report_count=row.report_count,
            report_ratio=row.report_ratio,
        )
        for row in items
    )


def _normalize_status_rows(
    rows: tuple[PaperEdgeCostSummaryTrendStatusRow, ...],
) -> tuple[PaperEdgeCostSummaryTrendStatusRow, ...]:
    normalized = _clone_status_rows(rows)
    if tuple(row.edge_cost_status for row in normalized) != EDGE_COST_SUMMARY_STATUSES:
        raise ValueError("status_rows must cover edge cost summary statuses")
    return normalized


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_probability_decimal(field_name, value)
    if value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")
    if value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no reports")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero when there are no reports")


__all__ = (
    "PaperEdgeCostSummaryTrendConfig",
    "PaperEdgeCostSummaryTrendStatusRow",
    "PaperEdgeCostSummaryTrendReport",
    "build_paper_edge_cost_summary_trend_report",
)
