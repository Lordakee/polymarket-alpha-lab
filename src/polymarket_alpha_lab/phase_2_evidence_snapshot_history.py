from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from polymarket_alpha_lab.forecast_calibration import PaperForecastCalibrationReport
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    PaperPhase2EvidenceSnapshotConfig,
    PaperPhase2EvidenceSnapshotReport,
    build_paper_phase_2_evidence_snapshot_report,
)
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentSummaryReport,
)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotHistoryConfig:
    config_version: str
    alignment_strategy: str = "max_prefix"

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.alignment_strategy != "max_prefix":
            raise ValueError("alignment_strategy must be max_prefix")


def build_paper_phase_2_evidence_snapshot_history(
    calibration_reports: list[PaperForecastCalibrationReport]
    | tuple[PaperForecastCalibrationReport, ...],
    segment_summary_reports: list[PaperStrategySegmentSummaryReport]
    | tuple[PaperStrategySegmentSummaryReport, ...],
    *,
    config: PaperPhase2EvidenceSnapshotHistoryConfig,
    snapshot_config: PaperPhase2EvidenceSnapshotConfig,
    generated_at: datetime,
) -> tuple[PaperPhase2EvidenceSnapshotReport, ...]:
    if type(config) is not PaperPhase2EvidenceSnapshotHistoryConfig:
        raise ValueError("config must be a PaperPhase2EvidenceSnapshotHistoryConfig")
    if type(snapshot_config) is not PaperPhase2EvidenceSnapshotConfig:
        raise ValueError("snapshot_config must be a PaperPhase2EvidenceSnapshotConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    calibration_items = _normalize_calibration_reports(calibration_reports)
    segment_items = _normalize_segment_summary_reports(segment_summary_reports)
    snapshot_count = max(len(calibration_items), len(segment_items))

    return tuple(
        build_paper_phase_2_evidence_snapshot_report(
            _latest_or_none(calibration_items, prefix_size),
            _latest_or_none(segment_items, prefix_size),
            config=snapshot_config,
            generated_at=generated_at,
        )
        for prefix_size in range(1, snapshot_count + 1)
    )


def _normalize_calibration_reports(
    reports: list[PaperForecastCalibrationReport]
    | tuple[PaperForecastCalibrationReport, ...],
) -> tuple[PaperForecastCalibrationReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("calibration_reports must be a list or tuple")
    items = tuple(reports)
    for report in items:
        if type(report) is not PaperForecastCalibrationReport:
            raise ValueError(
                "calibration_reports must contain only PaperForecastCalibrationReport values",
            )
        _require_report_flags("calibration_reports", report)
    return items


def _normalize_segment_summary_reports(
    reports: list[PaperStrategySegmentSummaryReport]
    | tuple[PaperStrategySegmentSummaryReport, ...],
) -> tuple[PaperStrategySegmentSummaryReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("segment_summary_reports must be a list or tuple")
    items = tuple(reports)
    for report in items:
        if type(report) is not PaperStrategySegmentSummaryReport:
            raise ValueError(
                "segment_summary_reports must contain only PaperStrategySegmentSummaryReport values",
            )
        _require_report_flags("segment_summary_reports", report)
    return items


def _latest_or_none(
    reports: tuple[PaperForecastCalibrationReport, ...]
    | tuple[PaperStrategySegmentSummaryReport, ...],
    prefix_size: int,
) -> PaperForecastCalibrationReport | PaperStrategySegmentSummaryReport | None:
    if not reports:
        return None
    prefix_end = min(prefix_size, len(reports))
    return reports[prefix_end - 1]


def _require_report_flags(name: str, report: object) -> None:
    if report.paper_only is not True:
        raise ValueError(f"{name} paper_only must be True")
    if report.report_only is not True:
        raise ValueError(f"{name} report_only must be True")
    if report.readonly is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_canonical_string(name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


__all__ = (
    "PaperPhase2EvidenceSnapshotHistoryConfig",
    "build_paper_phase_2_evidence_snapshot_history",
)
