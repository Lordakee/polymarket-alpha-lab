"""Pure status transition matrix reducer for Phase 2 evidence snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    SNAPSHOT_STATUSES,
    PaperPhase2EvidenceSnapshotReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperPhase2StatusMatrixConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2StatusMatrixRow:
    from_status: str
    to_status: str
    transition_count: int
    transition_ratio: Decimal

    def __post_init__(self) -> None:
        _require_snapshot_status("from_status", self.from_status)
        _require_snapshot_status("to_status", self.to_status)
        _require_nonnegative_int("transition_count", self.transition_count)
        _require_probability_decimal("transition_ratio", self.transition_ratio)


@dataclass(frozen=True)
class PaperPhase2StatusMatrixReport:
    generated_at: datetime
    config_version: str
    snapshot_report_count: int
    transition_count: int
    latest_from_status: str | None
    latest_to_status: str | None
    rows: tuple[PaperPhase2StatusMatrixRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("snapshot_report_count", self.snapshot_report_count)
        _require_nonnegative_int("transition_count", self.transition_count)
        _require_optional_snapshot_status("latest_from_status", self.latest_from_status)
        _require_optional_snapshot_status("latest_to_status", self.latest_to_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_status_matrix_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2StatusMatrixConfig,
    generated_at: datetime,
) -> PaperPhase2StatusMatrixReport:
    if type(config) is not PaperPhase2StatusMatrixConfig:
        raise ValueError("config must be a PaperPhase2StatusMatrixConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_snapshots(snapshots)
    pairs = tuple(zip(reports, reports[1:], strict=False))
    latest_pair = pairs[-1] if pairs else None

    return PaperPhase2StatusMatrixReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_report_count=len(reports),
        transition_count=len(pairs),
        latest_from_status=None if latest_pair is None else latest_pair[0].status,
        latest_to_status=None if latest_pair is None else latest_pair[1].status,
        rows=_build_rows(pairs),
    )


def _normalize_snapshots(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> tuple[PaperPhase2EvidenceSnapshotReport, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    reports = tuple(snapshots)
    for report in reports:
        if type(report) is not PaperPhase2EvidenceSnapshotReport:
            raise ValueError(
                "snapshots must contain PaperPhase2EvidenceSnapshotReport values",
            )
        _require_snapshot_status("status", report.status)
        if report.paper_only is not True:
            raise ValueError("snapshots must contain paper_only reports")
        if report.report_only is not True:
            raise ValueError("snapshots must contain report_only reports")
        if report.readonly is not True:
            raise ValueError("snapshots must contain readonly reports")
    return reports


def _build_rows(
    pairs: tuple[
        tuple[PaperPhase2EvidenceSnapshotReport, PaperPhase2EvidenceSnapshotReport],
        ...,
    ],
) -> tuple[PaperPhase2StatusMatrixRow, ...]:
    counts = {
        (from_status, to_status): 0
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    }
    for previous, current in pairs:
        counts[(previous.status, current.status)] += 1
    total = len(pairs)
    return tuple(
        PaperPhase2StatusMatrixRow(
            from_status=from_status,
            to_status=to_status,
            transition_count=counts[(from_status, to_status)],
            transition_ratio=_ratio(counts[(from_status, to_status)], total),
        )
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )


def _validate_report_consistency(report: PaperPhase2StatusMatrixReport) -> None:
    if report.transition_count != _expected_transition_count(report.snapshot_report_count):
        raise ValueError("transition_count must match snapshot_report_count")
    if report.transition_count == 0:
        if report.latest_from_status is not None:
            raise ValueError("latest_from_status must be absent without transitions")
        if report.latest_to_status is not None:
            raise ValueError("latest_to_status must be absent without transitions")
    else:
        if report.latest_from_status is None:
            raise ValueError("latest_from_status is required with transitions")
        if report.latest_to_status is None:
            raise ValueError("latest_to_status is required with transitions")
        if _row_count(report, report.latest_from_status, report.latest_to_status) < 1:
            raise ValueError("latest_to_status must be counted in rows")
    if sum(row.transition_count for row in report.rows) != report.transition_count:
        raise ValueError("rows counts must sum to transition_count")
    for row in report.rows:
        if row.transition_count > report.transition_count:
            raise ValueError("rows counts cannot exceed transition_count")
        if row.transition_ratio != _ratio(row.transition_count, report.transition_count):
            raise ValueError("rows ratios must match transition counts")


def _normalize_rows(
    rows: tuple[PaperPhase2StatusMatrixRow, ...],
) -> tuple[PaperPhase2StatusMatrixRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperPhase2StatusMatrixRow:
            raise ValueError("rows must contain PaperPhase2StatusMatrixRow values")
    expected_keys = tuple(
        (from_status, to_status)
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )
    row_keys = tuple((row.from_status, row.to_status) for row in normalized)
    if row_keys != expected_keys:
        raise ValueError("rows must cover phase 2 status pairs")
    return normalized


def _row_count(
    report: PaperPhase2StatusMatrixReport,
    from_status: str,
    to_status: str,
) -> int:
    return next(
        row.transition_count
        for row in report.rows
        if row.from_status == from_status and row.to_status == to_status
    )


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _expected_transition_count(snapshot_report_count: int) -> int:
    return max(0, snapshot_report_count - 1)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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


def _require_snapshot_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a known phase 2 status")
    if value not in SNAPSHOT_STATUSES:
        raise ValueError(f"{field_name} must be a known phase 2 status")


def _require_optional_snapshot_status(field_name: str, value: object) -> None:
    if value is not None:
        _require_snapshot_status(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if (
        value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


__all__ = (
    "PaperPhase2StatusMatrixConfig",
    "PaperPhase2StatusMatrixReport",
    "PaperPhase2StatusMatrixRow",
    "build_paper_phase_2_status_matrix_report",
)
