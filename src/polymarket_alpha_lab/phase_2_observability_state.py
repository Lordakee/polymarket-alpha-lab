"""Pure Phase 2 observability state summary over an existing trend bundle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from polymarket_alpha_lab.edge_cost_summary import EDGE_COST_SUMMARY_STATUSES
from polymarket_alpha_lab.edge_cost_summary_trend import PaperEdgeCostSummaryTrendReport
from polymarket_alpha_lab.forecast_calibration import REPORT_STATUSES
from polymarket_alpha_lab.forecast_calibration_trend import (
    PaperForecastCalibrationTrendReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_trend import (
    PaperPhase2EvidenceSnapshotTrendReport,
)
from polymarket_alpha_lab.phase_2_observability_trends import (
    PaperPhase2ObservabilityTrendsReport,
)
from polymarket_alpha_lab.strategy_segment_summary import STATUS_VALUES
from polymarket_alpha_lab.strategy_segment_summary_trend import (
    PaperStrategySegmentSummaryTrendReport,
)


BLOCKING_REASON_NAMES = (
    "missing_calibration_trend",
    "missing_segment_summary_trend",
    "missing_evidence_snapshot_trend",
    "missing_edge_cost_summary_trend",
    "calibration_not_observed",
    "segment_not_observed",
    "evidence_not_observed",
    "evidence_gaps_present",
    "edge_cost_not_observed",
)
PAPER_ONLY_REQUIRED_MESSAGE = "paper_only must be True"
REPORT_ONLY_REQUIRED_MESSAGE = "report_only must be True"
READONLY_REQUIRED_MESSAGE = "readonly must be True"


@dataclass(frozen=True)
class PaperPhase2ObservabilityStateConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2ObservabilityStateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    calibration_report_count: int
    segment_summary_report_count: int
    evidence_snapshot_report_count: int
    edge_cost_report_count: int
    latest_calibration_status: str | None
    latest_segment_status: str | None
    latest_evidence_status: str | None
    latest_edge_cost_status: str | None
    evidence_gap_count: int
    latest_evidence_gap_names: tuple[str, ...]
    phase_2_ready: bool
    blocking_reason_names: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "source_config_version",
            self.source_config_version,
        )
        for field_name, field_value in (
            ("calibration_report_count", self.calibration_report_count),
            ("segment_summary_report_count", self.segment_summary_report_count),
            ("evidence_snapshot_report_count", self.evidence_snapshot_report_count),
            ("edge_cost_report_count", self.edge_cost_report_count),
            ("evidence_gap_count", self.evidence_gap_count),
        ):
            _require_nonnegative_int(field_name, field_value)
        _require_optional_member(
            "latest_calibration_status",
            self.latest_calibration_status,
            REPORT_STATUSES,
        )
        _require_optional_member(
            "latest_segment_status",
            self.latest_segment_status,
            STATUS_VALUES,
        )
        _require_optional_member(
            "latest_evidence_status",
            self.latest_evidence_status,
            SNAPSHOT_STATUSES,
        )
        _require_optional_member(
            "latest_edge_cost_status",
            self.latest_edge_cost_status,
            EDGE_COST_SUMMARY_STATUSES,
        )
        _require_latest_status_matches_count(
            "latest_calibration_status",
            self.latest_calibration_status,
            self.calibration_report_count,
        )
        _require_latest_status_matches_count(
            "latest_segment_status",
            self.latest_segment_status,
            self.segment_summary_report_count,
        )
        _require_latest_status_matches_count(
            "latest_evidence_status",
            self.latest_evidence_status,
            self.evidence_snapshot_report_count,
        )
        _require_latest_status_matches_count(
            "latest_edge_cost_status",
            self.latest_edge_cost_status,
            self.edge_cost_report_count,
        )
        object.__setattr__(
            self,
            "latest_evidence_gap_names",
            _normalize_names(
                "latest_evidence_gap_names",
                self.latest_evidence_gap_names,
                EVIDENCE_GAP_NAMES,
            ),
        )
        if self.evidence_gap_count != len(self.latest_evidence_gap_names):
            raise ValueError("evidence_gap_count must match latest_evidence_gap_names")
        if (
            self.evidence_snapshot_report_count == 0
            and self.latest_evidence_gap_names
        ):
            raise ValueError(
                "latest_evidence_gap_names must be absent without evidence snapshots",
            )
        if type(self.phase_2_ready) is not bool:
            raise ValueError("phase_2_ready must be a bool")
        object.__setattr__(
            self,
            "blocking_reason_names",
            _normalize_names(
                "blocking_reason_names",
                self.blocking_reason_names,
                BLOCKING_REASON_NAMES,
            ),
        )
        if self.phase_2_ready != (self.blocking_reason_names == ()):
            raise ValueError("phase_2_ready must match blocking_reason_names")
        expected_blocking_reason_names = _blocking_reason_names_from_report(self)
        if self.blocking_reason_names != expected_blocking_reason_names:
            raise ValueError("blocking_reason_names must match report state")
        if self.paper_only is not True:
            raise ValueError(PAPER_ONLY_REQUIRED_MESSAGE)
        if self.report_only is not True:
            raise ValueError(REPORT_ONLY_REQUIRED_MESSAGE)
        if self.readonly is not True:
            raise ValueError(READONLY_REQUIRED_MESSAGE)


def build_paper_phase_2_observability_state_report(
    observability_trends: PaperPhase2ObservabilityTrendsReport,
    *,
    config: PaperPhase2ObservabilityStateConfig,
    generated_at: datetime,
) -> PaperPhase2ObservabilityStateReport:
    """Summarize whether required Phase 2 report evidence is currently present."""

    if type(observability_trends) is not PaperPhase2ObservabilityTrendsReport:
        raise ValueError(
            "observability_trends must be a PaperPhase2ObservabilityTrendsReport",
        )
    _require_report_flags("observability_trends", observability_trends)
    if type(config) is not PaperPhase2ObservabilityStateConfig:
        raise ValueError("config must be a PaperPhase2ObservabilityStateConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    calibration_trend = observability_trends.forecast_calibration_trend
    segment_trend = observability_trends.strategy_segment_summary_trend
    evidence_trend = observability_trends.phase_2_evidence_snapshot_trend
    edge_cost_trend = observability_trends.edge_cost_summary_trend
    _require_exact_report(
        "forecast_calibration_trend",
        calibration_trend,
        PaperForecastCalibrationTrendReport,
    )
    _require_exact_report(
        "strategy_segment_summary_trend",
        segment_trend,
        PaperStrategySegmentSummaryTrendReport,
    )
    _require_exact_report(
        "phase_2_evidence_snapshot_trend",
        evidence_trend,
        PaperPhase2EvidenceSnapshotTrendReport,
    )
    _require_exact_report(
        "edge_cost_summary_trend",
        edge_cost_trend,
        PaperEdgeCostSummaryTrendReport,
    )

    blocking_reason_names = _blocking_reason_names(
        calibration_trend=calibration_trend,
        segment_trend=segment_trend,
        evidence_trend=evidence_trend,
        edge_cost_trend=edge_cost_trend,
    )

    return PaperPhase2ObservabilityStateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=observability_trends.config_version,
        calibration_report_count=calibration_trend.calibration_report_count,
        segment_summary_report_count=segment_trend.segment_summary_report_count,
        evidence_snapshot_report_count=evidence_trend.snapshot_report_count,
        edge_cost_report_count=edge_cost_trend.edge_cost_report_count,
        latest_calibration_status=calibration_trend.latest_status,
        latest_segment_status=segment_trend.latest_status,
        latest_evidence_status=evidence_trend.latest_status,
        latest_edge_cost_status=edge_cost_trend.latest_status,
        evidence_gap_count=len(evidence_trend.latest_evidence_gap_names),
        latest_evidence_gap_names=evidence_trend.latest_evidence_gap_names,
        phase_2_ready=blocking_reason_names == (),
        blocking_reason_names=blocking_reason_names,
    )


def _blocking_reason_names(
    *,
    calibration_trend: PaperForecastCalibrationTrendReport,
    segment_trend: PaperStrategySegmentSummaryTrendReport,
    evidence_trend: PaperPhase2EvidenceSnapshotTrendReport,
    edge_cost_trend: PaperEdgeCostSummaryTrendReport,
) -> tuple[str, ...]:
    names: tuple[str, ...] = ()
    if calibration_trend.calibration_report_count == 0:
        names += ("missing_calibration_trend",)
    if segment_trend.segment_summary_report_count == 0:
        names += ("missing_segment_summary_trend",)
    if evidence_trend.snapshot_report_count == 0:
        names += ("missing_evidence_snapshot_trend",)
    if edge_cost_trend.edge_cost_report_count == 0:
        names += ("missing_edge_cost_summary_trend",)
    if (
        calibration_trend.calibration_report_count > 0
        and calibration_trend.latest_status != "calibration_evidence_observed"
    ):
        names += ("calibration_not_observed",)
    if (
        segment_trend.segment_summary_report_count > 0
        and segment_trend.latest_status != "segment_evidence_observed"
    ):
        names += ("segment_not_observed",)
    if (
        evidence_trend.snapshot_report_count > 0
        and evidence_trend.latest_status != "phase_2_evidence_observed"
    ):
        names += ("evidence_not_observed",)
    if evidence_trend.latest_evidence_gap_names:
        names += ("evidence_gaps_present",)
    if (
        edge_cost_trend.edge_cost_report_count > 0
        and edge_cost_trend.latest_status != "edge_cost_evidence_observed"
    ):
        names += ("edge_cost_not_observed",)
    return names


def _blocking_reason_names_from_report(
    report: PaperPhase2ObservabilityStateReport,
) -> tuple[str, ...]:
    names: tuple[str, ...] = ()
    if report.calibration_report_count == 0:
        names += ("missing_calibration_trend",)
    if report.segment_summary_report_count == 0:
        names += ("missing_segment_summary_trend",)
    if report.evidence_snapshot_report_count == 0:
        names += ("missing_evidence_snapshot_trend",)
    if report.edge_cost_report_count == 0:
        names += ("missing_edge_cost_summary_trend",)
    if (
        report.calibration_report_count > 0
        and report.latest_calibration_status != "calibration_evidence_observed"
    ):
        names += ("calibration_not_observed",)
    if (
        report.segment_summary_report_count > 0
        and report.latest_segment_status != "segment_evidence_observed"
    ):
        names += ("segment_not_observed",)
    if (
        report.evidence_snapshot_report_count > 0
        and report.latest_evidence_status != "phase_2_evidence_observed"
    ):
        names += ("evidence_not_observed",)
    if report.latest_evidence_gap_names:
        names += ("evidence_gaps_present",)
    if (
        report.edge_cost_report_count > 0
        and report.latest_edge_cost_status != "edge_cost_evidence_observed"
    ):
        names += ("edge_cost_not_observed",)
    return names


def _require_exact_report(field_name: str, value: Any, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_report_flags(field_name, value)


def _require_report_flags(field_name: str, value: Any) -> None:
    if value.paper_only is not True:
        raise ValueError(field_name + " " + PAPER_ONLY_REQUIRED_MESSAGE)
    if value.report_only is not True:
        raise ValueError(field_name + " " + REPORT_ONLY_REQUIRED_MESSAGE)
    if value.readonly is not True:
        raise ValueError(field_name + " " + READONLY_REQUIRED_MESSAGE)


def _normalize_names(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in items:
        if item not in allowed_values:
            raise ValueError(f"{field_name} must contain known names")
    expected_items = tuple(item for item in allowed_values if item in items)
    if items != expected_items:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return items


def _require_optional_member(
    field_name: str,
    value: str | None,
    allowed_values: tuple[str, ...],
) -> None:
    if value is not None and value not in allowed_values:
        raise ValueError(f"{field_name} must contain a known status")


def _require_latest_status_matches_count(
    field_name: str,
    value: str | None,
    report_count: int,
) -> None:
    if report_count == 0 and value is not None:
        raise ValueError(f"{field_name} must be absent without reports")
    if report_count > 0 and value is None:
        raise ValueError(f"{field_name} is required with reports")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _as_utc(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperPhase2ObservabilityStateConfig",
    "PaperPhase2ObservabilityStateReport",
    "build_paper_phase_2_observability_state_report",
)
