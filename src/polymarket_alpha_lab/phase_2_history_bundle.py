from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_transition import (
    PaperPhase2EvidenceSnapshotTransitionConfig,
    PaperPhase2EvidenceSnapshotTransitionReport,
    build_paper_phase_2_evidence_snapshot_transition_report,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_trend import (
    PaperPhase2EvidenceSnapshotTrendConfig,
    PaperPhase2EvidenceSnapshotTrendReport,
    build_paper_phase_2_evidence_snapshot_trend_report,
)


@dataclass(frozen=True)
class PaperPhase2HistoryBundleConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2HistoryBundleReport:
    generated_at: datetime
    config_version: str
    snapshot_history: tuple[PaperPhase2EvidenceSnapshotReport, ...]
    snapshot_trend: PaperPhase2EvidenceSnapshotTrendReport
    snapshot_transition: PaperPhase2EvidenceSnapshotTransitionReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "snapshot_history",
            _normalize_snapshot_history(self.snapshot_history),
        )
        _require_report_type(
            "snapshot_trend",
            self.snapshot_trend,
            PaperPhase2EvidenceSnapshotTrendReport,
        )
        _require_report_type(
            "snapshot_transition",
            self.snapshot_transition,
            PaperPhase2EvidenceSnapshotTransitionReport,
        )
        _require_report_flags("snapshot_trend", self.snapshot_trend)
        _require_report_flags("snapshot_transition", self.snapshot_transition)
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_history_bundle_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2HistoryBundleConfig,
    trend_config: PaperPhase2EvidenceSnapshotTrendConfig,
    transition_config: PaperPhase2EvidenceSnapshotTransitionConfig,
    generated_at: datetime,
) -> PaperPhase2HistoryBundleReport:
    if type(config) is not PaperPhase2HistoryBundleConfig:
        raise ValueError("config must be a PaperPhase2HistoryBundleConfig")
    if type(trend_config) is not PaperPhase2EvidenceSnapshotTrendConfig:
        raise ValueError(
            "trend_config must be a PaperPhase2EvidenceSnapshotTrendConfig",
        )
    if type(transition_config) is not PaperPhase2EvidenceSnapshotTransitionConfig:
        raise ValueError(
            "transition_config must be a PaperPhase2EvidenceSnapshotTransitionConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_snapshots(snapshots)
    return PaperPhase2HistoryBundleReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_history=reports,
        snapshot_trend=build_paper_phase_2_evidence_snapshot_trend_report(
            reports,
            config=trend_config,
            generated_at=generated_at,
        ),
        snapshot_transition=build_paper_phase_2_evidence_snapshot_transition_report(
            reports,
            config=transition_config,
            generated_at=generated_at,
        ),
    )


def _normalize_snapshots(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> tuple[PaperPhase2EvidenceSnapshotReport, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    normalized = tuple(snapshots)
    for snapshot in normalized:
        if type(snapshot) is not PaperPhase2EvidenceSnapshotReport:
            raise ValueError(
                "snapshots must contain PaperPhase2EvidenceSnapshotReport values",
            )
        _require_report_flags("snapshots", snapshot)
    return normalized


def _normalize_snapshot_history(
    snapshot_history: tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> tuple[PaperPhase2EvidenceSnapshotReport, ...]:
    if type(snapshot_history) is not tuple:
        raise ValueError("snapshot_history must be a tuple")
    for snapshot in snapshot_history:
        if type(snapshot) is not PaperPhase2EvidenceSnapshotReport:
            raise ValueError(
                "snapshot_history must contain PaperPhase2EvidenceSnapshotReport values",
            )
        _require_report_flags("snapshot_history", snapshot)
    return snapshot_history


def _require_report_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_report_flags(field_name: str, report: object) -> None:
    if report.paper_only is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if report.report_only is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if report.readonly is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _validate_report_consistency(report: PaperPhase2HistoryBundleReport) -> None:
    snapshot_count = len(report.snapshot_history)
    if report.snapshot_trend.snapshot_report_count != snapshot_count:
        raise ValueError("snapshot_trend must match snapshot_history")
    if report.snapshot_transition.snapshot_report_count != snapshot_count:
        raise ValueError("snapshot_transition must match snapshot_history")
    expected_trend = build_paper_phase_2_evidence_snapshot_trend_report(
        report.snapshot_history,
        config=PaperPhase2EvidenceSnapshotTrendConfig(
            config_version=report.snapshot_trend.config_version,
        ),
        generated_at=report.snapshot_trend.generated_at,
    )
    if report.snapshot_trend != expected_trend:
        raise ValueError("snapshot_trend must match snapshot_history")
    expected_transition = build_paper_phase_2_evidence_snapshot_transition_report(
        report.snapshot_history,
        config=PaperPhase2EvidenceSnapshotTransitionConfig(
            config_version=report.snapshot_transition.config_version,
        ),
        generated_at=report.snapshot_transition.generated_at,
    )
    if report.snapshot_transition != expected_transition:
        raise ValueError("snapshot_transition must match snapshot_history")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "PaperPhase2HistoryBundleConfig",
    "PaperPhase2HistoryBundleReport",
    "build_paper_phase_2_history_bundle_report",
)
