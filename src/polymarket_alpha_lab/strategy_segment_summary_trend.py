"""Pure trend reducer for paper strategy segment summary reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.strategy_segment_summary import (
    STATUS_VALUES,
    PaperStrategySegmentSummaryReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SUMMARY_REPORT_STATUSES = STATUS_VALUES


@dataclass(frozen=True)
class PaperStrategySegmentSummaryTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperStrategySegmentSummaryTrendStatusRow:
    summary_status: str
    report_count: int
    report_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.summary_status not in SUMMARY_REPORT_STATUSES:
            raise ValueError("summary_status must be a known segment summary status")
        _require_nonnegative_int("report_count", self.report_count)
        _require_optional_probability_decimal("report_ratio", self.report_ratio)


@dataclass(frozen=True)
class PaperStrategySegmentSummaryTrendReport:
    generated_at: datetime
    config_version: str
    segment_summary_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_status: str | None
    latest_total_observation_count: int
    latest_probability_observation_count: int
    latest_return_observation_count: int
    latest_strategy_segment_count: int
    latest_risk_tag_segment_count: int
    latest_incomplete_segment_count: int
    latest_return_only_segment_count: int
    largest_observed_incomplete_segment_count: int
    largest_observed_return_only_segment_count: int
    consecutive_incomplete_segment_count: int
    consecutive_return_only_segment_count: int
    status_rows: tuple[PaperStrategySegmentSummaryTrendStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        for field_name, value in (
            ("segment_summary_report_count", self.segment_summary_report_count),
            ("latest_total_observation_count", self.latest_total_observation_count),
            (
                "latest_probability_observation_count",
                self.latest_probability_observation_count,
            ),
            ("latest_return_observation_count", self.latest_return_observation_count),
            ("latest_strategy_segment_count", self.latest_strategy_segment_count),
            ("latest_risk_tag_segment_count", self.latest_risk_tag_segment_count),
            ("latest_incomplete_segment_count", self.latest_incomplete_segment_count),
            ("latest_return_only_segment_count", self.latest_return_only_segment_count),
            (
                "largest_observed_incomplete_segment_count",
                self.largest_observed_incomplete_segment_count,
            ),
            (
                "largest_observed_return_only_segment_count",
                self.largest_observed_return_only_segment_count,
            ),
            (
                "consecutive_incomplete_segment_count",
                self.consecutive_incomplete_segment_count,
            ),
            (
                "consecutive_return_only_segment_count",
                self.consecutive_return_only_segment_count,
            ),
        ):
            _require_nonnegative_int(field_name, value)
        _require_optional_datetime(
            "first_report_generated_at",
            self.first_report_generated_at,
        )
        _require_optional_datetime(
            "latest_report_generated_at",
            self.latest_report_generated_at,
        )
        if self.latest_status is not None and (
            self.latest_status not in SUMMARY_REPORT_STATUSES
        ):
            raise ValueError("latest_status must be a known segment summary status")
        object.__setattr__(
            self,
            "status_rows",
            _normalize_status_rows(self.status_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_segment_summary_trend_report(
    reports: list[PaperStrategySegmentSummaryReport]
    | tuple[PaperStrategySegmentSummaryReport, ...],
    *,
    config: PaperStrategySegmentSummaryTrendConfig,
    generated_at: datetime,
) -> PaperStrategySegmentSummaryTrendReport:
    if type(config) is not PaperStrategySegmentSummaryTrendConfig:
        raise ValueError("config must be a PaperStrategySegmentSummaryTrendConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    summaries = _normalize_summary_reports(reports)
    report_count = len(summaries)
    latest = summaries[-1] if summaries else None
    status_counts = _status_counts(summaries)

    return PaperStrategySegmentSummaryTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        segment_summary_report_count=report_count,
        first_report_generated_at=summaries[0].generated_at if summaries else None,
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_status=_summary_status(latest) if latest is not None else None,
        latest_total_observation_count=latest.observation_count
        if latest is not None
        else 0,
        latest_probability_observation_count=_strategy_probability_observation_count(
            latest,
        )
        if latest is not None
        else 0,
        latest_return_observation_count=_strategy_return_observation_count(latest)
        if latest is not None
        else 0,
        latest_strategy_segment_count=latest.strategy_segment_count
        if latest is not None
        else 0,
        latest_risk_tag_segment_count=latest.risk_tag_segment_count
        if latest is not None
        else 0,
        latest_incomplete_segment_count=_incomplete_segment_count(latest)
        if latest is not None
        else 0,
        latest_return_only_segment_count=_return_only_segment_count(latest)
        if latest is not None
        else 0,
        largest_observed_incomplete_segment_count=max(
            (_incomplete_segment_count(summary) for summary in summaries),
            default=0,
        ),
        largest_observed_return_only_segment_count=max(
            (_return_only_segment_count(summary) for summary in summaries),
            default=0,
        ),
        consecutive_incomplete_segment_count=_consecutive_incomplete_segment_count(
            summaries,
        ),
        consecutive_return_only_segment_count=_consecutive_return_only_segment_count(
            summaries,
        ),
        status_rows=_build_status_rows(status_counts, report_count),
    )


def _normalize_summary_reports(
    reports: list[PaperStrategySegmentSummaryReport]
    | tuple[PaperStrategySegmentSummaryReport, ...],
) -> tuple[PaperStrategySegmentSummaryReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple of segment summary reports")
    normalized = tuple(reports)
    for report in normalized:
        if type(report) is not PaperStrategySegmentSummaryReport:
            raise ValueError(
                "reports must contain only PaperStrategySegmentSummaryReport values",
            )
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only segment summary reports")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only segment summary reports")
        if report.readonly is not True:
            raise ValueError("reports must contain readonly segment summary reports")
    return normalized


def _status_counts(
    reports: tuple[PaperStrategySegmentSummaryReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in SUMMARY_REPORT_STATUSES}
    for report in reports:
        counts[_summary_status(report)] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperStrategySegmentSummaryTrendStatusRow, ...]:
    return tuple(
        PaperStrategySegmentSummaryTrendStatusRow(
            summary_status=status,
            report_count=status_counts[status],
            report_ratio=_ratio(status_counts[status], total),
        )
        for status in SUMMARY_REPORT_STATUSES
    )


def _summary_status(report: PaperStrategySegmentSummaryReport) -> str:
    if report.observation_count == 0:
        return "insufficient_segment_probability_sample"
    if _incomplete_segment_count(report) > 0:
        return "insufficient_segment_probability_sample"
    if _return_only_segment_count(report) > 0:
        return "segment_return_evidence_observed"
    return "segment_evidence_observed"


def _strategy_probability_observation_count(
    report: PaperStrategySegmentSummaryReport,
) -> int:
    return sum(
        row.probability_observation_count
        for row in report.rows
        if row.segment_type == "strategy_type"
    )


def _strategy_return_observation_count(
    report: PaperStrategySegmentSummaryReport,
) -> int:
    return sum(
        row.return_observation_count
        for row in report.rows
        if row.segment_type == "strategy_type"
    )


def _incomplete_segment_count(report: PaperStrategySegmentSummaryReport) -> int:
    return sum(
        1
        for row in report.rows
        if row.status == "insufficient_segment_probability_sample"
    )


def _return_only_segment_count(report: PaperStrategySegmentSummaryReport) -> int:
    return sum(
        1 for row in report.rows if row.status == "segment_return_evidence_observed"
    )


def _consecutive_incomplete_segment_count(
    reports: tuple[PaperStrategySegmentSummaryReport, ...],
) -> int:
    count = 0
    for report in reversed(reports):
        if _incomplete_segment_count(report) == 0:
            break
        count += 1
    return count


def _consecutive_return_only_segment_count(
    reports: tuple[PaperStrategySegmentSummaryReport, ...],
) -> int:
    count = 0
    for report in reversed(reports):
        if _return_only_segment_count(report) == 0:
            break
        count += 1
    return count


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_consistency(
    report: PaperStrategySegmentSummaryTrendReport,
) -> None:
    if tuple(row.summary_status for row in report.status_rows) != (
        SUMMARY_REPORT_STATUSES
    ):
        raise ValueError("status_rows must cover segment summary statuses")
    if sum(row.report_count for row in report.status_rows) != (
        report.segment_summary_report_count
    ):
        raise ValueError("status_rows counts must sum to segment_summary_report_count")
    for row in report.status_rows:
        if not _ratio_value_matches(
            row.report_ratio,
            _ratio(row.report_count, report.segment_summary_report_count),
        ):
            raise ValueError("status_rows ratios must match report counts")

    if report.segment_summary_report_count == 0:
        _require_none("first_report_generated_at", report.first_report_generated_at)
        _require_none("latest_report_generated_at", report.latest_report_generated_at)
        if report.latest_status is not None:
            raise ValueError("latest_status must be absent without reports")
        _require_zero(
            "latest_total_observation_count",
            report.latest_total_observation_count,
        )
        _require_zero(
            "latest_probability_observation_count",
            report.latest_probability_observation_count,
        )
        _require_zero(
            "latest_return_observation_count",
            report.latest_return_observation_count,
        )
        _require_zero(
            "latest_strategy_segment_count",
            report.latest_strategy_segment_count,
        )
        _require_zero(
            "latest_risk_tag_segment_count",
            report.latest_risk_tag_segment_count,
        )
        _require_zero(
            "latest_incomplete_segment_count",
            report.latest_incomplete_segment_count,
        )
        _require_zero(
            "latest_return_only_segment_count",
            report.latest_return_only_segment_count,
        )
        _require_zero(
            "largest_observed_incomplete_segment_count",
            report.largest_observed_incomplete_segment_count,
        )
        _require_zero(
            "largest_observed_return_only_segment_count",
            report.largest_observed_return_only_segment_count,
        )
        _require_zero(
            "consecutive_incomplete_segment_count",
            report.consecutive_incomplete_segment_count,
        )
        _require_zero(
            "consecutive_return_only_segment_count",
            report.consecutive_return_only_segment_count,
        )
        return

    if report.first_report_generated_at is None:
        raise ValueError("first_report_generated_at is required with reports")
    if report.latest_report_generated_at is None:
        raise ValueError("latest_report_generated_at is required with reports")
    if report.latest_status is None:
        raise ValueError("latest_status is required with reports")
    if _status_report_count(report, report.latest_status) < 1:
        raise ValueError("latest_status must be counted in status_rows")
    if report.latest_total_observation_count == 0:
        if report.latest_status != "insufficient_segment_probability_sample":
            raise ValueError("latest_status must match latest segment observations")
        for field_name in (
            "latest_probability_observation_count",
            "latest_return_observation_count",
            "latest_strategy_segment_count",
            "latest_risk_tag_segment_count",
            "latest_incomplete_segment_count",
            "latest_return_only_segment_count",
        ):
            _require_zero(field_name, getattr(report, field_name))
        _require_zero(
            "consecutive_incomplete_segment_count",
            report.consecutive_incomplete_segment_count,
        )
        _require_zero(
            "consecutive_return_only_segment_count",
            report.consecutive_return_only_segment_count,
        )
        return
    if (
        report.latest_probability_observation_count
        > report.latest_total_observation_count
    ):
        raise ValueError("latest_probability_observation_count cannot exceed total")
    if report.latest_return_observation_count > report.latest_total_observation_count:
        raise ValueError("latest_return_observation_count cannot exceed total")
    latest_segment_count = (
        report.latest_strategy_segment_count + report.latest_risk_tag_segment_count
    )
    if report.latest_incomplete_segment_count > latest_segment_count:
        raise ValueError("latest_incomplete_segment_count cannot exceed latest segments")
    if report.latest_return_only_segment_count > latest_segment_count:
        raise ValueError("latest_return_only_segment_count cannot exceed latest segments")
    if (
        report.largest_observed_incomplete_segment_count
        < report.latest_incomplete_segment_count
    ):
        raise ValueError("largest_observed_incomplete_segment_count cannot be below latest")
    if (
        report.largest_observed_return_only_segment_count
        < report.latest_return_only_segment_count
    ):
        raise ValueError("largest_observed_return_only_segment_count cannot be below latest")
    if report.consecutive_incomplete_segment_count > report.segment_summary_report_count:
        raise ValueError("consecutive_incomplete_segment_count cannot exceed reports")
    if report.consecutive_return_only_segment_count > report.segment_summary_report_count:
        raise ValueError("consecutive_return_only_segment_count cannot exceed reports")
    if report.latest_incomplete_segment_count == 0:
        _require_zero(
            "consecutive_incomplete_segment_count",
            report.consecutive_incomplete_segment_count,
        )
    elif report.consecutive_incomplete_segment_count < 1:
        raise ValueError("incomplete latest report requires a streak")
    if report.latest_return_only_segment_count == 0:
        _require_zero(
            "consecutive_return_only_segment_count",
            report.consecutive_return_only_segment_count,
        )
    elif report.consecutive_return_only_segment_count < 1:
        raise ValueError("return-only latest report requires a streak")
    if report.latest_status == "segment_evidence_observed":
        if report.latest_incomplete_segment_count != 0:
            raise ValueError("latest_status must match latest incomplete segments")
        if report.latest_return_only_segment_count != 0:
            raise ValueError("latest_status must match latest return-only segments")
    elif report.latest_status == "segment_return_evidence_observed":
        if report.latest_incomplete_segment_count != 0:
            raise ValueError("latest_status must match latest incomplete segments")
        if report.latest_return_only_segment_count == 0:
            raise ValueError("latest_status must match latest return-only segments")
    else:
        if (
            report.latest_incomplete_segment_count == 0
            and report.latest_total_observation_count != 0
        ):
            raise ValueError("latest_status must match latest incomplete segments")


def _normalize_status_rows(
    rows: tuple[PaperStrategySegmentSummaryTrendStatusRow, ...],
) -> tuple[PaperStrategySegmentSummaryTrendStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("status_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("status_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperStrategySegmentSummaryTrendStatusRow:
            raise ValueError(
                "status_rows must contain PaperStrategySegmentSummaryTrendStatusRow values",
            )
        _require_nonnegative_int("report_count", row.report_count)
        _require_optional_probability_decimal("report_ratio", row.report_ratio)
    if tuple(row.summary_status for row in normalized) != SUMMARY_REPORT_STATUSES:
        raise ValueError("status_rows must cover segment summary statuses")
    return normalized


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


def _require_optional_datetime(field_name: str, value: object) -> None:
    if value is None:
        return
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or None")


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
    if (
        value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _ratio_value_matches(value: Decimal | None, expected: Decimal | None) -> bool:
    if value != expected:
        return False
    if expected is None:
        return value is None
    if type(value) is not Decimal:
        return False
    return (
        value == value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        and value.as_tuple().exponent == RATIO_QUANTUM.as_tuple().exponent
    )


def _status_report_count(
    report: PaperStrategySegmentSummaryTrendReport,
    summary_status: str,
) -> int:
    return sum(
        row.report_count
        for row in report.status_rows
        if row.summary_status == summary_status
    )


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no reports")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero when there are no reports")


__all__ = (
    "PaperStrategySegmentSummaryTrendConfig",
    "PaperStrategySegmentSummaryTrendStatusRow",
    "PaperStrategySegmentSummaryTrendReport",
    "build_paper_strategy_segment_summary_trend_report",
)
