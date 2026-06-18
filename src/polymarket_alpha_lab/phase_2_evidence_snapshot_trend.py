"""Pure trend reducer for Phase 2 evidence snapshot reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
    PaperPhase2EvidenceSnapshotReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTrendStatusRow:
    snapshot_status: str
    snapshot_count: int
    snapshot_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.snapshot_status not in SNAPSHOT_STATUSES:
            raise ValueError("snapshot_status must be a known phase 2 status")
        _require_nonnegative_int("snapshot_count", self.snapshot_count)
        _require_optional_probability_decimal("snapshot_ratio", self.snapshot_ratio)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTrendGapRow:
    evidence_gap_name: str
    gap_count: int
    gap_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.evidence_gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_name must be a known phase 2 gap")
        _require_nonnegative_int("gap_count", self.gap_count)
        _require_optional_probability_decimal("gap_ratio", self.gap_ratio)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTrendReport:
    generated_at: datetime
    config_version: str
    snapshot_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_status: str | None
    latest_evidence_gap_names: tuple[str, ...]
    consecutive_quality_flag_count: int
    consecutive_gap_count: int
    consecutive_non_observed_count: int
    status_rows: tuple[PaperPhase2EvidenceSnapshotTrendStatusRow, ...]
    gap_rows: tuple[PaperPhase2EvidenceSnapshotTrendGapRow, ...]
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
        _require_nonnegative_int("snapshot_report_count", self.snapshot_report_count)
        if self.latest_status is not None and (
            self.latest_status not in SNAPSHOT_STATUSES
        ):
            raise ValueError("latest_status must be a known phase 2 status")
        object.__setattr__(
            self,
            "latest_evidence_gap_names",
            _normalize_gap_names(self.latest_evidence_gap_names),
        )
        for field_name in (
            "consecutive_quality_flag_count",
            "consecutive_gap_count",
            "consecutive_non_observed_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "status_rows", _normalize_status_rows(self.status_rows))
        object.__setattr__(self, "gap_rows", _normalize_gap_rows(self.gap_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_evidence_snapshot_trend_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2EvidenceSnapshotTrendConfig,
    generated_at: datetime,
) -> PaperPhase2EvidenceSnapshotTrendReport:
    """Aggregate Phase 2 evidence snapshots into a trend snapshot."""

    if type(config) is not PaperPhase2EvidenceSnapshotTrendConfig:
        raise ValueError("config must be a PaperPhase2EvidenceSnapshotTrendConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_snapshots(snapshots)
    report_count = len(reports)
    latest = reports[-1] if reports else None
    status_counts = _status_counts(reports)
    gap_counts = _gap_counts(reports)

    return PaperPhase2EvidenceSnapshotTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_report_count=report_count,
        first_report_generated_at=reports[0].generated_at if reports else None,
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_status=latest.status if latest is not None else None,
        latest_evidence_gap_names=latest.evidence_gap_names if latest is not None else (),
        consecutive_quality_flag_count=_consecutive_status_count(
            reports,
            "phase_2_evidence_quality_flags",
        ),
        consecutive_gap_count=_consecutive_status_count(
            reports,
            "phase_2_evidence_gaps",
        ),
        consecutive_non_observed_count=_consecutive_non_observed_count(reports),
        status_rows=_build_status_rows(status_counts, report_count),
        gap_rows=_build_gap_rows(gap_counts, report_count),
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


def _status_counts(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in SNAPSHOT_STATUSES}
    for snapshot in snapshots:
        counts[snapshot.status] += 1
    return counts


def _gap_counts(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> dict[str, int]:
    counts = {gap_name: 0 for gap_name in EVIDENCE_GAP_NAMES}
    for snapshot in snapshots:
        for gap_name in snapshot.evidence_gap_names:
            counts[gap_name] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperPhase2EvidenceSnapshotTrendStatusRow, ...]:
    return tuple(
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            snapshot_status=status,
            snapshot_count=status_counts[status],
            snapshot_ratio=_ratio(status_counts[status], total),
        )
        for status in SNAPSHOT_STATUSES
    )


def _build_gap_rows(
    gap_counts: dict[str, int],
    total: int,
) -> tuple[PaperPhase2EvidenceSnapshotTrendGapRow, ...]:
    return tuple(
        PaperPhase2EvidenceSnapshotTrendGapRow(
            evidence_gap_name=gap_name,
            gap_count=gap_counts[gap_name],
            gap_ratio=_ratio(gap_counts[gap_name], total),
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )


def _consecutive_status_count(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
    status: str,
) -> int:
    count = 0
    for snapshot in reversed(snapshots):
        if snapshot.status != status:
            break
        count += 1
    return count


def _consecutive_non_observed_count(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> int:
    count = 0
    for snapshot in reversed(snapshots):
        if snapshot.status == "phase_2_evidence_observed":
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
    report: PaperPhase2EvidenceSnapshotTrendReport,
) -> None:
    _validate_status_rows(report)
    _validate_gap_rows(report)

    if report.snapshot_report_count == 0:
        _require_none("first_report_generated_at", report.first_report_generated_at)
        _require_none("latest_report_generated_at", report.latest_report_generated_at)
        if report.latest_status is not None:
            raise ValueError("latest_status must be absent without snapshots")
        if report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must be absent without snapshots")
        _require_zero(
            "consecutive_quality_flag_count",
            report.consecutive_quality_flag_count,
        )
        _require_zero("consecutive_gap_count", report.consecutive_gap_count)
        _require_zero(
            "consecutive_non_observed_count",
            report.consecutive_non_observed_count,
        )
        return

    if report.first_report_generated_at is None:
        raise ValueError("first_report_generated_at is required with snapshots")
    if report.latest_report_generated_at is None:
        raise ValueError("latest_report_generated_at is required with snapshots")
    if report.latest_status is None:
        raise ValueError("latest_status is required with snapshots")
    if _status_snapshot_count(report, report.latest_status) < 1:
        raise ValueError("latest_status must be counted in status_rows")
    if report.consecutive_quality_flag_count > _status_snapshot_count(
        report,
        "phase_2_evidence_quality_flags",
    ):
        raise ValueError("quality flag streak cannot exceed status_rows count")
    if report.consecutive_gap_count > _status_snapshot_count(
        report,
        "phase_2_evidence_gaps",
    ):
        raise ValueError("gap streak cannot exceed status_rows count")
    non_observed_count = report.snapshot_report_count - _status_snapshot_count(
        report,
        "phase_2_evidence_observed",
    )
    if report.consecutive_non_observed_count > non_observed_count:
        raise ValueError("non-observed streak cannot exceed non-observed snapshots")

    if report.latest_status == "phase_2_evidence_observed":
        if report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        _require_zero(
            "consecutive_quality_flag_count",
            report.consecutive_quality_flag_count,
        )
        _require_zero("consecutive_gap_count", report.consecutive_gap_count)
        _require_zero(
            "consecutive_non_observed_count",
            report.consecutive_non_observed_count,
        )
    elif report.latest_status == "phase_2_evidence_quality_flags":
        if "calibration_quality_flags_present" not in report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        if report.consecutive_quality_flag_count < 1:
            raise ValueError("quality flag latest snapshot requires a streak")
        _require_zero("consecutive_gap_count", report.consecutive_gap_count)
        if report.consecutive_non_observed_count < 1:
            raise ValueError("non-observed latest snapshot requires a streak")
    elif report.latest_status == "phase_2_evidence_gaps":
        if not report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        if "calibration_quality_flags_present" in report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        _require_zero(
            "consecutive_quality_flag_count",
            report.consecutive_quality_flag_count,
        )
        if report.consecutive_gap_count < 1:
            raise ValueError("gap latest snapshot requires a streak")
        if report.consecutive_non_observed_count < 1:
            raise ValueError("non-observed latest snapshot requires a streak")
    elif report.latest_status == "phase_2_evidence_not_observed":
        if set(report.latest_evidence_gap_names) != {
            "missing_calibration_report",
            "missing_segment_summary",
        }:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        _require_zero(
            "consecutive_quality_flag_count",
            report.consecutive_quality_flag_count,
        )
        _require_zero("consecutive_gap_count", report.consecutive_gap_count)
        if report.consecutive_non_observed_count < 1:
            raise ValueError("non-observed latest snapshot requires a streak")

    gap_counts = {row.evidence_gap_name: row.gap_count for row in report.gap_rows}
    for gap_name in report.latest_evidence_gap_names:
        if gap_counts[gap_name] < 1:
            raise ValueError("latest_evidence_gap_names must be counted in gap_rows")


def _validate_status_rows(report: PaperPhase2EvidenceSnapshotTrendReport) -> None:
    if tuple(row.snapshot_status for row in report.status_rows) != SNAPSHOT_STATUSES:
        raise ValueError("status_rows must cover phase 2 statuses")
    if sum(row.snapshot_count for row in report.status_rows) != (
        report.snapshot_report_count
    ):
        raise ValueError("status_rows counts must sum to snapshot_report_count")
    for row in report.status_rows:
        if not _ratio_value_matches(
            row.snapshot_ratio,
            _ratio(row.snapshot_count, report.snapshot_report_count),
        ):
            raise ValueError("status_rows ratios must match snapshot counts")


def _validate_gap_rows(report: PaperPhase2EvidenceSnapshotTrendReport) -> None:
    if tuple(row.evidence_gap_name for row in report.gap_rows) != EVIDENCE_GAP_NAMES:
        raise ValueError("gap_rows must cover phase 2 evidence gaps")
    for row in report.gap_rows:
        if row.gap_count > report.snapshot_report_count:
            raise ValueError("gap_rows counts cannot exceed snapshot_report_count")
        if not _ratio_value_matches(
            row.gap_ratio,
            _ratio(row.gap_count, report.snapshot_report_count),
        ):
            raise ValueError("gap_rows ratios must match snapshot counts")


def _status_snapshot_count(
    report: PaperPhase2EvidenceSnapshotTrendReport,
    status: str,
) -> int:
    return next(
        row.snapshot_count for row in report.status_rows if row.snapshot_status == status
    )


def _normalize_status_rows(
    rows: tuple[PaperPhase2EvidenceSnapshotTrendStatusRow, ...],
) -> tuple[PaperPhase2EvidenceSnapshotTrendStatusRow, ...]:
    normalized = _normalize_typed_tuple(
        "status_rows",
        rows,
        PaperPhase2EvidenceSnapshotTrendStatusRow,
    )
    if tuple(row.snapshot_status for row in normalized) != SNAPSHOT_STATUSES:
        raise ValueError("status_rows must cover phase 2 statuses")
    return normalized


def _normalize_gap_rows(
    rows: tuple[PaperPhase2EvidenceSnapshotTrendGapRow, ...],
) -> tuple[PaperPhase2EvidenceSnapshotTrendGapRow, ...]:
    normalized = _normalize_typed_tuple(
        "gap_rows",
        rows,
        PaperPhase2EvidenceSnapshotTrendGapRow,
    )
    if tuple(row.evidence_gap_name for row in normalized) != EVIDENCE_GAP_NAMES:
        raise ValueError("gap_rows must cover phase 2 evidence gaps")
    return normalized


def _normalize_typed_tuple(
    field_name: str,
    values: tuple[object, ...],
    expected_type: type,
) -> tuple[object, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


def _normalize_gap_names(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("latest_evidence_gap_names must be an iterable")
    try:
        gap_names = tuple(values)
    except TypeError as exc:
        raise ValueError("latest_evidence_gap_names must be an iterable") from exc
    if len(set(gap_names)) != len(gap_names):
        raise ValueError("latest_evidence_gap_names must not contain duplicates")
    for gap_name in gap_names:
        if gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("latest_evidence_gap_names must contain known gap names")
    expected_names = tuple(
        gap_name for gap_name in EVIDENCE_GAP_NAMES if gap_name in gap_names
    )
    if gap_names != expected_names:
        raise ValueError("latest_evidence_gap_names must use deterministic order")
    return gap_names


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


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no snapshots")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero")


__all__ = (
    "PaperPhase2EvidenceSnapshotTrendConfig",
    "PaperPhase2EvidenceSnapshotTrendGapRow",
    "PaperPhase2EvidenceSnapshotTrendReport",
    "PaperPhase2EvidenceSnapshotTrendStatusRow",
    "build_paper_phase_2_evidence_snapshot_trend_report",
)
