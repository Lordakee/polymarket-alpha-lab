"""Pure trend reducer for Phase 2 evidence snapshot transition reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_transition import (
    PaperPhase2EvidenceSnapshotTransitionReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTransitionTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTransitionTrendGapRow:
    evidence_gap_name: str
    introduced_count: int
    cleared_count: int
    persistent_count: int
    transition_presence_ratio: Decimal | None

    def __post_init__(self) -> None:
        if (
            type(self.evidence_gap_name) is not str
            or self.evidence_gap_name not in EVIDENCE_GAP_NAMES
        ):
            raise ValueError("evidence_gap_name must be a known phase 2 gap")
        _require_nonnegative_int("introduced_count", self.introduced_count)
        _require_nonnegative_int("cleared_count", self.cleared_count)
        _require_nonnegative_int("persistent_count", self.persistent_count)
        _require_optional_probability_decimal(
            "transition_presence_ratio",
            self.transition_presence_ratio,
        )


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTransitionTrendReport:
    generated_at: datetime
    config_version: str
    transition_report_count: int
    total_snapshot_report_count: int
    total_transition_count: int
    first_transition_report_generated_at: datetime | None
    latest_transition_report_generated_at: datetime | None
    latest_from_status: str | None
    latest_to_status: str | None
    latest_introduced_gap_names: tuple[str, ...]
    latest_cleared_gap_names: tuple[str, ...]
    total_introduced_gap_count: int
    total_cleared_gap_count: int
    total_persistent_gap_count: int
    gap_rows: tuple[PaperPhase2EvidenceSnapshotTransitionTrendGapRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_transition_report_generated_at",
            _as_optional_utc(self.first_transition_report_generated_at),
        )
        object.__setattr__(
            self,
            "latest_transition_report_generated_at",
            _as_optional_utc(self.latest_transition_report_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "transition_report_count",
            self.transition_report_count,
        )
        _require_nonnegative_int(
            "total_snapshot_report_count",
            self.total_snapshot_report_count,
        )
        _require_nonnegative_int("total_transition_count", self.total_transition_count)
        _require_nonnegative_int(
            "total_introduced_gap_count",
            self.total_introduced_gap_count,
        )
        _require_nonnegative_int(
            "total_cleared_gap_count",
            self.total_cleared_gap_count,
        )
        _require_nonnegative_int(
            "total_persistent_gap_count",
            self.total_persistent_gap_count,
        )
        _require_optional_snapshot_status("latest_from_status", self.latest_from_status)
        _require_optional_snapshot_status("latest_to_status", self.latest_to_status)
        object.__setattr__(
            self,
            "latest_introduced_gap_names",
            _normalize_gap_names(
                "latest_introduced_gap_names",
                self.latest_introduced_gap_names,
            ),
        )
        object.__setattr__(
            self,
            "latest_cleared_gap_names",
            _normalize_gap_names(
                "latest_cleared_gap_names",
                self.latest_cleared_gap_names,
            ),
        )
        object.__setattr__(self, "gap_rows", _normalize_gap_rows(self.gap_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_evidence_snapshot_transition_trend_report(
    transition_reports: list[PaperPhase2EvidenceSnapshotTransitionReport]
    | tuple[PaperPhase2EvidenceSnapshotTransitionReport, ...],
    *,
    config: PaperPhase2EvidenceSnapshotTransitionTrendConfig,
    generated_at: datetime,
) -> PaperPhase2EvidenceSnapshotTransitionTrendReport:
    if type(config) is not PaperPhase2EvidenceSnapshotTransitionTrendConfig:
        raise ValueError(
            "config must be a PaperPhase2EvidenceSnapshotTransitionTrendConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_reports(transition_reports)
    latest = reports[-1] if reports else None
    total_transition_count = sum(report.transition_count for report in reports)
    gap_rows = _build_gap_rows(reports, total_transition_count)

    return PaperPhase2EvidenceSnapshotTransitionTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        transition_report_count=len(reports),
        total_snapshot_report_count=sum(
            report.snapshot_report_count for report in reports
        ),
        total_transition_count=total_transition_count,
        first_transition_report_generated_at=(
            None if not reports else reports[0].generated_at
        ),
        latest_transition_report_generated_at=(
            None if latest is None else latest.generated_at
        ),
        latest_from_status=None if latest is None else latest.latest_from_status,
        latest_to_status=None if latest is None else latest.latest_to_status,
        latest_introduced_gap_names=(
            () if latest is None else latest.latest_introduced_gap_names
        ),
        latest_cleared_gap_names=(
            () if latest is None else latest.latest_cleared_gap_names
        ),
        total_introduced_gap_count=sum(row.introduced_count for row in gap_rows),
        total_cleared_gap_count=sum(row.cleared_count for row in gap_rows),
        total_persistent_gap_count=sum(row.persistent_count for row in gap_rows),
        gap_rows=gap_rows,
    )


def _normalize_reports(
    transition_reports: list[PaperPhase2EvidenceSnapshotTransitionReport]
    | tuple[PaperPhase2EvidenceSnapshotTransitionReport, ...],
) -> tuple[PaperPhase2EvidenceSnapshotTransitionReport, ...]:
    if type(transition_reports) not in (list, tuple):
        raise ValueError("transition_reports must be a list or tuple")
    reports = tuple(transition_reports)
    for report in reports:
        if type(report) is not PaperPhase2EvidenceSnapshotTransitionReport:
            raise ValueError(
                "transition_reports must contain "
                "PaperPhase2EvidenceSnapshotTransitionReport values",
            )
        if report.paper_only is not True:
            raise ValueError("transition_reports must contain paper_only reports")
        if report.report_only is not True:
            raise ValueError("transition_reports must contain report_only reports")
        if report.readonly is not True:
            raise ValueError("transition_reports must contain readonly reports")
    return reports


def _build_gap_rows(
    reports: tuple[PaperPhase2EvidenceSnapshotTransitionReport, ...],
    total_transition_count: int,
) -> tuple[PaperPhase2EvidenceSnapshotTransitionTrendGapRow, ...]:
    rows: list[PaperPhase2EvidenceSnapshotTransitionTrendGapRow] = []
    for gap_name in EVIDENCE_GAP_NAMES:
        introduced_count = 0
        cleared_count = 0
        persistent_count = 0
        for report in reports:
            source_row = next(
                row
                for row in report.gap_transition_rows
                if row.evidence_gap_name == gap_name
            )
            introduced_count += source_row.introduced_count
            cleared_count += source_row.cleared_count
            persistent_count += source_row.persistent_count
        rows.append(
            PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
                evidence_gap_name=gap_name,
                introduced_count=introduced_count,
                cleared_count=cleared_count,
                persistent_count=persistent_count,
                transition_presence_ratio=_ratio(
                    introduced_count + cleared_count + persistent_count,
                    total_transition_count,
                ),
            ),
        )
    return tuple(rows)


def _validate_report_consistency(
    report: PaperPhase2EvidenceSnapshotTransitionTrendReport,
) -> None:
    if report.transition_report_count == 0:
        if report.total_snapshot_report_count != 0:
            raise ValueError(
                "total_snapshot_report_count must be zero without reports",
            )
        if report.total_transition_count != 0:
            raise ValueError("total_transition_count must be zero without reports")
        _require_none(
            "first_transition_report_generated_at",
            report.first_transition_report_generated_at,
        )
        _require_none(
            "latest_transition_report_generated_at",
            report.latest_transition_report_generated_at,
        )
        if report.latest_from_status is not None:
            raise ValueError("latest_from_status must be absent without reports")
        if report.latest_to_status is not None:
            raise ValueError("latest_to_status must be absent without reports")
        if report.latest_introduced_gap_names:
            raise ValueError(
                "latest_introduced_gap_names must be absent without reports",
            )
        if report.latest_cleared_gap_names:
            raise ValueError(
                "latest_cleared_gap_names must be absent without reports",
            )
    else:
        if report.total_snapshot_report_count < report.total_transition_count:
            raise ValueError(
                "total_snapshot_report_count must cover transitions",
            )
        if report.total_snapshot_report_count > (
            report.total_transition_count + report.transition_report_count
        ):
            raise ValueError(
                "total_snapshot_report_count cannot exceed transition span",
            )
        if report.first_transition_report_generated_at is None:
            raise ValueError(
                "first_transition_report_generated_at is required with reports",
            )
        if report.latest_transition_report_generated_at is None:
            raise ValueError(
                "latest_transition_report_generated_at is required with reports",
            )

    if set(report.latest_introduced_gap_names) & set(report.latest_cleared_gap_names):
        raise ValueError("latest gap names must not overlap")
    gap_counts = {row.evidence_gap_name: row for row in report.gap_rows}
    for gap_name in report.latest_introduced_gap_names:
        if gap_counts[gap_name].introduced_count < 1:
            raise ValueError("latest_introduced_gap_names must be counted")
    for gap_name in report.latest_cleared_gap_names:
        if gap_counts[gap_name].cleared_count < 1:
            raise ValueError("latest_cleared_gap_names must be counted")
    if report.transition_report_count == 1 and report.total_transition_count == 1:
        expected_latest_introduced_gap_names = tuple(
            row.evidence_gap_name for row in report.gap_rows if row.introduced_count == 1
        )
        expected_latest_cleared_gap_names = tuple(
            row.evidence_gap_name for row in report.gap_rows if row.cleared_count == 1
        )
        if report.latest_introduced_gap_names != expected_latest_introduced_gap_names:
            raise ValueError("latest_introduced_gap_names must match gap_rows")
        if report.latest_cleared_gap_names != expected_latest_cleared_gap_names:
            raise ValueError("latest_cleared_gap_names must match gap_rows")

    if sum(row.introduced_count for row in report.gap_rows) != (
        report.total_introduced_gap_count
    ):
        raise ValueError("total_introduced_gap_count must match gap_rows")
    if sum(row.cleared_count for row in report.gap_rows) != (
        report.total_cleared_gap_count
    ):
        raise ValueError("total_cleared_gap_count must match gap_rows")
    if sum(row.persistent_count for row in report.gap_rows) != (
        report.total_persistent_gap_count
    ):
        raise ValueError("total_persistent_gap_count must match gap_rows")

    for row in report.gap_rows:
        expected_ratio = _ratio(
            row.introduced_count + row.cleared_count + row.persistent_count,
            report.total_transition_count,
        )
        if not _ratio_value_matches(row.transition_presence_ratio, expected_ratio):
            raise ValueError("transition_presence_ratio must match gap counts")


def _normalize_gap_rows(
    rows: tuple[PaperPhase2EvidenceSnapshotTransitionTrendGapRow, ...],
) -> tuple[PaperPhase2EvidenceSnapshotTransitionTrendGapRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("gap_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("gap_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperPhase2EvidenceSnapshotTransitionTrendGapRow:
            raise ValueError(
                "gap_rows must contain "
                "PaperPhase2EvidenceSnapshotTransitionTrendGapRow values",
            )
    if tuple(row.evidence_gap_name for row in normalized) != EVIDENCE_GAP_NAMES:
        raise ValueError("gap_rows must cover phase 2 evidence gaps")
    return normalized


def _normalize_gap_names(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        gap_names = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(gap_names)) != len(gap_names):
        raise ValueError(f"{field_name} must not contain duplicates")
    for gap_name in gap_names:
        if type(gap_name) is not str or gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError(f"{field_name} must contain known gap names")
    expected_names = tuple(
        gap_name for gap_name in EVIDENCE_GAP_NAMES if gap_name in gap_names
    )
    if gap_names != expected_names:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return gap_names


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


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
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


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


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
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
        raise ValueError(f"{field_name} must be None without reports")


def _require_optional_snapshot_status(field_name: str, value: object) -> None:
    if value is not None and (type(value) is not str or value not in SNAPSHOT_STATUSES):
        raise ValueError(f"{field_name} must be a known phase 2 status")


__all__ = (
    "PaperPhase2EvidenceSnapshotTransitionTrendConfig",
    "PaperPhase2EvidenceSnapshotTransitionTrendGapRow",
    "PaperPhase2EvidenceSnapshotTransitionTrendReport",
    "build_paper_phase_2_evidence_snapshot_transition_trend_report",
)
