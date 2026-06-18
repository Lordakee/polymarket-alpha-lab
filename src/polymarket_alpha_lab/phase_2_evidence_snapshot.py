"""Pure Phase 2 evidence snapshot reducer over caller-supplied reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.forecast_calibration import PaperForecastCalibrationReport
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentRow,
    PaperStrategySegmentSummaryReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

SNAPSHOT_STATUSES = (
    "phase_2_evidence_not_observed",
    "phase_2_evidence_gaps",
    "phase_2_evidence_quality_flags",
    "phase_2_evidence_observed",
)
EVIDENCE_GAP_NAMES = (
    "missing_calibration_report",
    "thin_calibration_sample",
    "calibration_quality_flags_present",
    "missing_segment_summary",
    "thin_segment_probability_samples",
    "return_only_segments_present",
)
CALIBRATION_STATUSES = (
    "empty_calibration_history",
    "insufficient_calibration_sample",
    "calibration_quality_flags",
    "calibration_evidence_observed",
)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotConfig:
    config_version: str
    min_calibration_observations: int = 30
    min_probability_segment_observations: int = 10

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_calibration_observations",
            self.min_calibration_observations,
        )
        _require_nonnegative_int(
            "min_probability_segment_observations",
            self.min_probability_segment_observations,
        )


@dataclass(frozen=True)
class PaperPhase2EvidenceGapRow:
    evidence_gap_name: str
    gap_present: bool

    def __post_init__(self) -> None:
        if self.evidence_gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_name must be a known evidence gap")
        if type(self.gap_present) is not bool:
            raise ValueError("gap_present must be a bool")


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotReport:
    generated_at: datetime
    config_version: str
    status: str
    calibration_report_present: bool
    segment_summary_report_present: bool
    calibration_observation_count: int | None
    calibration_status: str | None
    segment_observation_count: int | None
    segment_count: int | None
    probability_segment_count: int | None
    return_only_segment_count: int | None
    thin_probability_segment_count: int | None
    probability_segment_coverage_ratio: Decimal | None
    return_only_segment_ratio: Decimal | None
    evidence_gap_count: int
    evidence_gap_names: tuple[str, ...]
    evidence_gaps: tuple[PaperPhase2EvidenceGapRow, ...]
    min_calibration_observations: int = 30
    min_probability_segment_observations: int = 10
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.status not in SNAPSHOT_STATUSES:
            raise ValueError("status must be a known phase 2 evidence snapshot status")
        _require_bool(
            "calibration_report_present",
            self.calibration_report_present,
        )
        _require_bool(
            "segment_summary_report_present",
            self.segment_summary_report_present,
        )
        _require_optional_nonnegative_int(
            "calibration_observation_count",
            self.calibration_observation_count,
        )
        if self.calibration_status is not None and (
            self.calibration_status not in CALIBRATION_STATUSES
        ):
            raise ValueError("calibration_status must be a known calibration status or None")
        for field_name in (
            "segment_observation_count",
            "segment_count",
            "probability_segment_count",
            "return_only_segment_count",
            "thin_probability_segment_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_probability_ratio(
            "probability_segment_coverage_ratio",
            self.probability_segment_coverage_ratio,
        )
        _require_optional_probability_ratio(
            "return_only_segment_ratio",
            self.return_only_segment_ratio,
        )
        _require_nonnegative_int("evidence_gap_count", self.evidence_gap_count)
        _require_nonnegative_int(
            "min_calibration_observations",
            self.min_calibration_observations,
        )
        _require_nonnegative_int(
            "min_probability_segment_observations",
            self.min_probability_segment_observations,
        )
        object.__setattr__(
            self,
            "evidence_gaps",
            _normalize_evidence_gaps(self.evidence_gaps),
        )
        object.__setattr__(
            self,
            "evidence_gap_names",
            _normalize_evidence_gap_names(self.evidence_gap_names),
        )
        _validate_report_shape(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_evidence_snapshot_report(
    calibration_report: PaperForecastCalibrationReport | None,
    segment_summary_report: PaperStrategySegmentSummaryReport | None,
    *,
    config: PaperPhase2EvidenceSnapshotConfig,
    generated_at: datetime,
) -> PaperPhase2EvidenceSnapshotReport:
    if calibration_report is not None and (
        type(calibration_report) is not PaperForecastCalibrationReport
    ):
        raise ValueError(
            "calibration_report must be a PaperForecastCalibrationReport or None",
        )
    if segment_summary_report is not None and (
        type(segment_summary_report) is not PaperStrategySegmentSummaryReport
    ):
        raise ValueError(
            "segment_summary_report must be a PaperStrategySegmentSummaryReport or None",
        )
    if type(config) is not PaperPhase2EvidenceSnapshotConfig:
        raise ValueError("config must be a PaperPhase2EvidenceSnapshotConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    if calibration_report is not None:
        _require_report_flags("calibration_report", calibration_report)
    if segment_summary_report is not None:
        _require_report_flags("segment_summary_report", segment_summary_report)

    segment_rows = (
        ()
        if segment_summary_report is None
        else tuple(segment_summary_report.rows)
    )
    segment_count = None if segment_summary_report is None else len(segment_rows)
    probability_segment_count = (
        None
        if segment_summary_report is None
        else _probability_segment_count(segment_rows)
    )
    return_only_segment_count = (
        None
        if segment_summary_report is None
        else _return_only_segment_count(segment_rows)
    )
    thin_probability_segment_count = (
        None
        if segment_summary_report is None
        else _thin_probability_segment_count(
            segment_rows,
            config.min_probability_segment_observations,
        )
    )
    evidence_gaps = _build_evidence_gaps(
        calibration_report=calibration_report,
        segment_summary_report=segment_summary_report,
        segment_count=segment_count,
        probability_segment_count=probability_segment_count,
        thin_probability_segment_count=thin_probability_segment_count,
        return_only_segment_count=return_only_segment_count,
        config=config,
    )
    evidence_gap_names = tuple(
        gap.evidence_gap_name for gap in evidence_gaps if gap.gap_present
    )
    status = _snapshot_status(
        calibration_report_present=calibration_report is not None,
        segment_summary_report_present=segment_summary_report is not None,
        evidence_gap_names=evidence_gap_names,
    )

    return PaperPhase2EvidenceSnapshotReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        calibration_report_present=calibration_report is not None,
        segment_summary_report_present=segment_summary_report is not None,
        calibration_observation_count=(
            None if calibration_report is None else calibration_report.observation_count
        ),
        calibration_status=None if calibration_report is None else calibration_report.status,
        segment_observation_count=(
            None if segment_summary_report is None else segment_summary_report.observation_count
        ),
        segment_count=segment_count,
        probability_segment_count=probability_segment_count,
        return_only_segment_count=return_only_segment_count,
        thin_probability_segment_count=thin_probability_segment_count,
        probability_segment_coverage_ratio=_ratio_or_none(
            probability_segment_count,
            segment_count,
        ),
        return_only_segment_ratio=_ratio_or_none(
            return_only_segment_count,
            segment_count,
        ),
        evidence_gap_count=len(evidence_gap_names),
        evidence_gap_names=evidence_gap_names,
        evidence_gaps=evidence_gaps,
        min_calibration_observations=config.min_calibration_observations,
        min_probability_segment_observations=(
            config.min_probability_segment_observations
        ),
    )


def _build_evidence_gaps(
    *,
    calibration_report: PaperForecastCalibrationReport | None,
    segment_summary_report: PaperStrategySegmentSummaryReport | None,
    segment_count: int | None,
    probability_segment_count: int | None,
    thin_probability_segment_count: int | None,
    return_only_segment_count: int | None,
    config: PaperPhase2EvidenceSnapshotConfig,
) -> tuple[PaperPhase2EvidenceGapRow, ...]:
    gap_present_by_name = {
        "missing_calibration_report": calibration_report is None,
        "thin_calibration_sample": (
            calibration_report is not None
            and calibration_report.observation_count < config.min_calibration_observations
        ),
        "calibration_quality_flags_present": (
            calibration_report is not None
            and calibration_report.status == "calibration_quality_flags"
        ),
        "missing_segment_summary": segment_summary_report is None,
        "thin_segment_probability_samples": (
            segment_summary_report is not None
            and (
                probability_segment_count == 0
                or thin_probability_segment_count > 0
            )
        ),
        "return_only_segments_present": (
            segment_summary_report is not None
            and segment_count is not None
            and return_only_segment_count > 0
        ),
    }
    return tuple(
        PaperPhase2EvidenceGapRow(
            evidence_gap_name=gap_name,
            gap_present=gap_present_by_name[gap_name],
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )


def _snapshot_status(
    *,
    calibration_report_present: bool,
    segment_summary_report_present: bool,
    evidence_gap_names: tuple[str, ...],
) -> str:
    if not calibration_report_present and not segment_summary_report_present:
        return "phase_2_evidence_not_observed"
    if "calibration_quality_flags_present" in evidence_gap_names:
        return "phase_2_evidence_quality_flags"
    if evidence_gap_names:
        return "phase_2_evidence_gaps"
    return "phase_2_evidence_observed"


def _probability_segment_count(rows: tuple[PaperStrategySegmentRow, ...]) -> int:
    return sum(1 for row in rows if row.probability_observation_count > 0)


def _return_only_segment_count(rows: tuple[PaperStrategySegmentRow, ...]) -> int:
    return sum(1 for row in rows if row.probability_observation_count == 0)


def _thin_probability_segment_count(
    rows: tuple[PaperStrategySegmentRow, ...],
    min_probability_segment_observations: int,
) -> int:
    return sum(
        1
        for row in rows
        if (
            row.probability_observation_count > 0
            and row.probability_observation_count < min_probability_segment_observations
        )
    )


def _ratio_or_none(numerator: int | None, denominator: int | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


def _normalize_evidence_gaps(
    values: tuple[PaperPhase2EvidenceGapRow, ...],
) -> tuple[PaperPhase2EvidenceGapRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("evidence_gaps must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("evidence_gaps must be an iterable") from exc
    if not all(type(row) is PaperPhase2EvidenceGapRow for row in rows):
        raise ValueError("evidence_gaps must contain PaperPhase2EvidenceGapRow values")
    if tuple(row.evidence_gap_name for row in rows) != EVIDENCE_GAP_NAMES:
        raise ValueError("evidence_gaps must use deterministic gap row sequence")
    return rows


def _normalize_evidence_gap_names(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("evidence_gap_names must be an iterable")
    try:
        gap_names = tuple(values)
    except TypeError as exc:
        raise ValueError("evidence_gap_names must be an iterable") from exc
    if len(set(gap_names)) != len(gap_names):
        raise ValueError("evidence_gap_names must not contain duplicates")
    for gap_name in gap_names:
        if gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_names must contain known gap names")
    expected_names = tuple(
        gap_name for gap_name in EVIDENCE_GAP_NAMES if gap_name in gap_names
    )
    if gap_names != expected_names:
        raise ValueError("evidence_gap_names must use deterministic gap name sequence")
    return gap_names


def _validate_report_shape(report: PaperPhase2EvidenceSnapshotReport) -> None:
    if not report.calibration_report_present:
        if (
            report.calibration_observation_count is not None
            or report.calibration_status is not None
        ):
            raise ValueError("calibration fields must be absent without calibration report")
    else:
        if (
            report.calibration_observation_count is None
            or report.calibration_status is None
        ):
            raise ValueError("calibration fields must be present with calibration report")

    segment_values = (
        report.segment_observation_count,
        report.segment_count,
        report.probability_segment_count,
        report.return_only_segment_count,
        report.thin_probability_segment_count,
    )
    if not report.segment_summary_report_present:
        if any(value is not None for value in segment_values):
            raise ValueError("segment fields must be absent without segment summary report")
        if (
            report.probability_segment_coverage_ratio is not None
            or report.return_only_segment_ratio is not None
        ):
            raise ValueError("segment ratios must be absent without segment summary report")
    else:
        if any(value is None for value in segment_values):
            raise ValueError("segment fields must be present with segment summary report")
        if report.segment_count == 0:
            if (
                report.probability_segment_coverage_ratio is not None
                or report.return_only_segment_ratio is not None
            ):
                raise ValueError("segment ratios must be absent without segment rows")
        elif (
            report.probability_segment_coverage_ratio is None
            or report.return_only_segment_ratio is None
        ):
            raise ValueError("segment ratios must be present with segment rows")
        if report.probability_segment_count + report.return_only_segment_count != (
            report.segment_count
        ):
            raise ValueError("segment evidence counts must sum to segment_count")
        if report.thin_probability_segment_count > report.probability_segment_count:
            raise ValueError(
                "thin_probability_segment_count cannot exceed probability_segment_count",
            )
        if report.probability_segment_coverage_ratio != _ratio_or_none(
            report.probability_segment_count,
            report.segment_count,
        ):
            raise ValueError(
                "probability_segment_coverage_ratio must match segment counts",
            )
        if report.return_only_segment_ratio != _ratio_or_none(
            report.return_only_segment_count,
            report.segment_count,
        ):
            raise ValueError("return_only_segment_ratio must match segment counts")

    expected_gaps = _expected_evidence_gaps_from_report(report)
    if report.evidence_gaps != expected_gaps:
        raise ValueError("evidence_gaps must match report fields")
    expected_gap_names = tuple(
        row.evidence_gap_name for row in report.evidence_gaps if row.gap_present
    )
    if report.evidence_gap_names != expected_gap_names:
        raise ValueError("evidence_gap_names must match evidence_gaps")
    if report.evidence_gap_count != len(report.evidence_gap_names):
        raise ValueError("evidence_gap_count must match evidence_gap_names")
    expected_status = _snapshot_status(
        calibration_report_present=report.calibration_report_present,
        segment_summary_report_present=report.segment_summary_report_present,
        evidence_gap_names=report.evidence_gap_names,
    )
    if report.status != expected_status:
        raise ValueError("status must match phase 2 evidence gaps")


def _expected_evidence_gaps_from_report(
    report: PaperPhase2EvidenceSnapshotReport,
) -> tuple[PaperPhase2EvidenceGapRow, ...]:
    gap_present_by_name = {
        "missing_calibration_report": not report.calibration_report_present,
        "thin_calibration_sample": (
            report.calibration_report_present
            and report.calibration_observation_count is not None
            and report.calibration_observation_count
            < report.min_calibration_observations
        ),
        "calibration_quality_flags_present": (
            report.calibration_report_present
            and report.calibration_status == "calibration_quality_flags"
        ),
        "missing_segment_summary": not report.segment_summary_report_present,
        "thin_segment_probability_samples": (
            report.segment_summary_report_present
            and (
                report.probability_segment_count == 0
                or (
                    report.thin_probability_segment_count is not None
                    and report.thin_probability_segment_count > 0
                )
            )
        ),
        "return_only_segments_present": (
            report.segment_summary_report_present
            and report.segment_count is not None
            and report.return_only_segment_count is not None
            and report.return_only_segment_count > 0
        ),
    }
    return tuple(
        PaperPhase2EvidenceGapRow(
            evidence_gap_name=gap_name,
            gap_present=gap_present_by_name[gap_name],
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )


def _require_report_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_probability_ratio(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)
    if value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


__all__ = (
    "PaperPhase2EvidenceSnapshotConfig",
    "PaperPhase2EvidenceGapRow",
    "PaperPhase2EvidenceSnapshotReport",
    "build_paper_phase_2_evidence_snapshot_report",
)
