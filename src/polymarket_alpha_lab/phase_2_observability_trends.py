"""Pure Phase 2 observability trend bundle over caller-supplied reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from polymarket_alpha_lab.edge_cost_summary import PaperEdgeCostSummaryReport
from polymarket_alpha_lab.edge_cost_summary_trend import (
    PaperEdgeCostSummaryTrendConfig,
    PaperEdgeCostSummaryTrendReport,
    build_paper_edge_cost_summary_trend_report,
)
from polymarket_alpha_lab.forecast_calibration import PaperForecastCalibrationReport
from polymarket_alpha_lab.forecast_calibration_trend import (
    PaperForecastCalibrationTrendConfig,
    PaperForecastCalibrationTrendReport,
    build_paper_forecast_calibration_trend_report,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_trend import (
    PaperPhase2EvidenceSnapshotTrendConfig,
    PaperPhase2EvidenceSnapshotTrendReport,
    build_paper_phase_2_evidence_snapshot_trend_report,
)
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentSummaryReport,
)
from polymarket_alpha_lab.strategy_segment_summary_trend import (
    PaperStrategySegmentSummaryTrendConfig,
    PaperStrategySegmentSummaryTrendReport,
    build_paper_strategy_segment_summary_trend_report,
)


@dataclass(frozen=True)
class PaperPhase2ObservabilityTrendsConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2ObservabilityTrendsReport:
    generated_at: datetime
    config_version: str
    forecast_calibration_trend: PaperForecastCalibrationTrendReport
    strategy_segment_summary_trend: PaperStrategySegmentSummaryTrendReport
    phase_2_evidence_snapshot_trend: PaperPhase2EvidenceSnapshotTrendReport
    edge_cost_summary_trend: PaperEdgeCostSummaryTrendReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_exact_report(
            "forecast_calibration_trend",
            self.forecast_calibration_trend,
            PaperForecastCalibrationTrendReport,
        )
        _require_exact_report(
            "strategy_segment_summary_trend",
            self.strategy_segment_summary_trend,
            PaperStrategySegmentSummaryTrendReport,
        )
        _require_exact_report(
            "phase_2_evidence_snapshot_trend",
            self.phase_2_evidence_snapshot_trend,
            PaperPhase2EvidenceSnapshotTrendReport,
        )
        _require_exact_report(
            "edge_cost_summary_trend",
            self.edge_cost_summary_trend,
            PaperEdgeCostSummaryTrendReport,
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_observability_trends_report(
    calibration_reports: list[PaperForecastCalibrationReport]
    | tuple[PaperForecastCalibrationReport, ...],
    segment_summary_reports: list[PaperStrategySegmentSummaryReport]
    | tuple[PaperStrategySegmentSummaryReport, ...],
    evidence_snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    edge_cost_reports: list[PaperEdgeCostSummaryReport]
    | tuple[PaperEdgeCostSummaryReport, ...] = (),
    *,
    config: PaperPhase2ObservabilityTrendsConfig,
    generated_at: datetime,
) -> PaperPhase2ObservabilityTrendsReport:
    """Aggregate existing Phase 2 trend reports into a single in-memory bundle."""

    if type(config) is not PaperPhase2ObservabilityTrendsConfig:
        raise ValueError("config must be a PaperPhase2ObservabilityTrendsConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    generated_at = _as_utc(generated_at)

    return PaperPhase2ObservabilityTrendsReport(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast_calibration_trend=build_paper_forecast_calibration_trend_report(
            calibration_reports,
            config=PaperForecastCalibrationTrendConfig(
                "phase-2-forecast-calibration-trend-v0",
            ),
            generated_at=generated_at,
        ),
        strategy_segment_summary_trend=build_paper_strategy_segment_summary_trend_report(
            segment_summary_reports,
            config=PaperStrategySegmentSummaryTrendConfig(
                "phase-2-strategy-segment-summary-trend-v0",
            ),
            generated_at=generated_at,
        ),
        phase_2_evidence_snapshot_trend=build_paper_phase_2_evidence_snapshot_trend_report(
            evidence_snapshots,
            config=PaperPhase2EvidenceSnapshotTrendConfig(
                "phase-2-evidence-snapshot-trend-v0",
            ),
            generated_at=generated_at,
        ),
        edge_cost_summary_trend=build_paper_edge_cost_summary_trend_report(
            edge_cost_reports,
            config=PaperEdgeCostSummaryTrendConfig(
                "phase-2-edge-cost-summary-trend-v0",
            ),
            generated_at=generated_at,
        ),
    )


def _require_exact_report(field_name: str, value: Any, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    if value.paper_only is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if value.report_only is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if value.readonly is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "PaperPhase2ObservabilityTrendsConfig",
    "PaperPhase2ObservabilityTrendsReport",
    "build_paper_phase_2_observability_trends_report",
)
