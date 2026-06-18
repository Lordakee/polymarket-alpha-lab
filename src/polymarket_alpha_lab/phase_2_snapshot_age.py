"""Pure Phase 2 evidence snapshot age reducer over caller-supplied reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    PaperPhase2EvidenceSnapshotReport,
)


@dataclass(frozen=True)
class PaperPhase2SnapshotAgeConfig:
    config_version: str
    max_fresh_age_seconds: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "max_fresh_age_seconds",
            self.max_fresh_age_seconds,
        )


@dataclass(frozen=True)
class PaperPhase2SnapshotAgeReport:
    generated_at: datetime
    config_version: str
    snapshot_report_count: int
    first_snapshot_generated_at: datetime | None
    latest_snapshot_generated_at: datetime | None
    history_span_seconds: int
    latest_age_seconds: int | None
    stale_snapshot_count: int
    fresh_snapshot_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_snapshot_generated_at",
            _as_optional_utc(self.first_snapshot_generated_at),
        )
        object.__setattr__(
            self,
            "latest_snapshot_generated_at",
            _as_optional_utc(self.latest_snapshot_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "snapshot_report_count",
            self.snapshot_report_count,
        )
        _require_nonnegative_int(
            "history_span_seconds",
            self.history_span_seconds,
        )
        _require_nonnegative_int(
            "stale_snapshot_count",
            self.stale_snapshot_count,
        )
        _require_nonnegative_int(
            "fresh_snapshot_count",
            self.fresh_snapshot_count,
        )
        _require_optional_nonnegative_int("latest_age_seconds", self.latest_age_seconds)
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_snapshot_age_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2SnapshotAgeConfig,
    generated_at: datetime,
) -> PaperPhase2SnapshotAgeReport:
    """Summarize caller-supplied Phase 2 evidence snapshot freshness."""

    if type(config) is not PaperPhase2SnapshotAgeConfig:
        raise ValueError("config must be a PaperPhase2SnapshotAgeConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    report_generated_at = _as_utc(generated_at)
    reports = _normalize_snapshots(snapshots)
    latest = reports[-1] if reports else None
    ages = tuple(
        _age_seconds(report_generated_at, snapshot.generated_at)
        for snapshot in reports
    )
    stale_count = sum(
        1 for age_seconds in ages if age_seconds > config.max_fresh_age_seconds
    )

    return PaperPhase2SnapshotAgeReport(
        generated_at=report_generated_at,
        config_version=config.config_version,
        snapshot_report_count=len(reports),
        first_snapshot_generated_at=reports[0].generated_at if reports else None,
        latest_snapshot_generated_at=latest.generated_at if latest is not None else None,
        history_span_seconds=(
            0
            if latest is None
            else _age_seconds(latest.generated_at, reports[0].generated_at)
        ),
        latest_age_seconds=(
            None
            if latest is None
            else _age_seconds(report_generated_at, latest.generated_at)
        ),
        stale_snapshot_count=stale_count,
        fresh_snapshot_count=len(reports) - stale_count,
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
        if snapshot.paper_only is not True:
            raise ValueError("snapshots must contain paper_only reports")
        if snapshot.report_only is not True:
            raise ValueError("snapshots must contain report_only reports")
        if snapshot.readonly is not True:
            raise ValueError("snapshots must contain readonly reports")
    return normalized


def _validate_report_consistency(report: PaperPhase2SnapshotAgeReport) -> None:
    if report.snapshot_report_count == 0:
        if report.first_snapshot_generated_at is not None:
            raise ValueError("first_snapshot_generated_at must be absent without snapshots")
        if report.latest_snapshot_generated_at is not None:
            raise ValueError("latest_snapshot_generated_at must be absent without snapshots")
        if report.history_span_seconds != 0:
            raise ValueError("history_span_seconds must be zero without snapshots")
        if report.latest_age_seconds is not None:
            raise ValueError("latest_age_seconds must be absent without snapshots")
        if report.stale_snapshot_count != 0 or report.fresh_snapshot_count != 0:
            raise ValueError("fresh and stale counts must be zero without snapshots")
        return

    if report.first_snapshot_generated_at is None:
        raise ValueError("first_snapshot_generated_at is required with snapshots")
    if report.latest_snapshot_generated_at is None:
        raise ValueError("latest_snapshot_generated_at is required with snapshots")
    if report.latest_age_seconds is None:
        raise ValueError("latest_age_seconds is required with snapshots")
    expected_span = _age_seconds(
        report.latest_snapshot_generated_at,
        report.first_snapshot_generated_at,
    )
    if report.history_span_seconds != expected_span:
        raise ValueError("history_span_seconds must match snapshot bounds")
    expected_latest_age = _age_seconds(
        report.generated_at,
        report.latest_snapshot_generated_at,
    )
    if report.latest_age_seconds != expected_latest_age:
        raise ValueError("latest_age_seconds must match latest snapshot")
    if (
        report.fresh_snapshot_count + report.stale_snapshot_count
        != report.snapshot_report_count
    ):
        raise ValueError("fresh and stale counts must sum to snapshot_report_count")


def _age_seconds(generated_at: datetime, snapshot_generated_at: datetime) -> int:
    return int((_as_utc(generated_at) - _as_utc(snapshot_generated_at)).total_seconds())


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)


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


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


__all__ = (
    "PaperPhase2SnapshotAgeConfig",
    "PaperPhase2SnapshotAgeReport",
    "build_paper_phase_2_snapshot_age_report",
)
