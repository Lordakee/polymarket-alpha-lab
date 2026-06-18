"""Pure adjacent transition reducer for Phase 2 evidence snapshots."""

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
class PaperPhase2EvidenceSnapshotTransitionConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotStatusTransitionRow:
    from_snapshot_status: str
    to_snapshot_status: str
    transition_count: int
    transition_ratio: Decimal | None

    def __post_init__(self) -> None:
        _require_canonical_string("from_snapshot_status", self.from_snapshot_status)
        _require_canonical_string("to_snapshot_status", self.to_snapshot_status)
        if self.from_snapshot_status not in SNAPSHOT_STATUSES:
            raise ValueError("from_snapshot_status must be a known phase 2 status")
        if self.to_snapshot_status not in SNAPSHOT_STATUSES:
            raise ValueError("to_snapshot_status must be a known phase 2 status")
        _require_nonnegative_int("transition_count", self.transition_count)
        _require_optional_probability_decimal("transition_ratio", self.transition_ratio)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotGapTransitionRow:
    evidence_gap_name: str
    introduced_count: int
    cleared_count: int
    persistent_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("evidence_gap_name", self.evidence_gap_name)
        if self.evidence_gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_name must be a known phase 2 gap")
        _require_nonnegative_int("introduced_count", self.introduced_count)
        _require_nonnegative_int("cleared_count", self.cleared_count)
        _require_nonnegative_int("persistent_count", self.persistent_count)


@dataclass(frozen=True)
class PaperPhase2EvidenceSnapshotTransitionReport:
    generated_at: datetime
    config_version: str
    snapshot_report_count: int
    transition_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_from_status: str | None
    latest_to_status: str | None
    latest_introduced_gap_names: tuple[str, ...]
    latest_cleared_gap_names: tuple[str, ...]
    status_transition_rows: tuple[PaperPhase2EvidenceSnapshotStatusTransitionRow, ...]
    gap_transition_rows: tuple[PaperPhase2EvidenceSnapshotGapTransitionRow, ...]
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
        _require_nonnegative_int("transition_count", self.transition_count)
        if self.latest_from_status is not None:
            _require_canonical_string("latest_from_status", self.latest_from_status)
            if self.latest_from_status not in SNAPSHOT_STATUSES:
                raise ValueError("latest_from_status must be a known phase 2 status")
        if self.latest_to_status is not None:
            _require_canonical_string("latest_to_status", self.latest_to_status)
            if self.latest_to_status not in SNAPSHOT_STATUSES:
                raise ValueError("latest_to_status must be a known phase 2 status")
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
        object.__setattr__(
            self,
            "status_transition_rows",
            _normalize_status_transition_rows(self.status_transition_rows),
        )
        object.__setattr__(
            self,
            "gap_transition_rows",
            _normalize_gap_transition_rows(self.gap_transition_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_evidence_snapshot_transition_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2EvidenceSnapshotTransitionConfig,
    generated_at: datetime,
) -> PaperPhase2EvidenceSnapshotTransitionReport:
    if type(config) is not PaperPhase2EvidenceSnapshotTransitionConfig:
        raise ValueError(
            "config must be a PaperPhase2EvidenceSnapshotTransitionConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_snapshots(snapshots)
    pairs = tuple(zip(reports, reports[1:], strict=False))
    latest_pair = pairs[-1] if pairs else None
    latest_introduced_gap_names = (
        () if latest_pair is None else _introduced_gap_names(*latest_pair)
    )
    latest_cleared_gap_names = (
        () if latest_pair is None else _cleared_gap_names(*latest_pair)
    )
    transition_count = len(pairs)

    return PaperPhase2EvidenceSnapshotTransitionReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_report_count=len(reports),
        transition_count=transition_count,
        first_report_generated_at=reports[0].generated_at if reports else None,
        latest_report_generated_at=reports[-1].generated_at if reports else None,
        latest_from_status=latest_pair[0].status if latest_pair is not None else None,
        latest_to_status=latest_pair[1].status if latest_pair is not None else None,
        latest_introduced_gap_names=latest_introduced_gap_names,
        latest_cleared_gap_names=latest_cleared_gap_names,
        status_transition_rows=_build_status_transition_rows(
            pairs,
            transition_count,
        ),
        gap_transition_rows=_build_gap_transition_rows(pairs),
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


def _build_status_transition_rows(
    pairs: tuple[
        tuple[PaperPhase2EvidenceSnapshotReport, PaperPhase2EvidenceSnapshotReport],
        ...,
    ],
    total: int,
) -> tuple[PaperPhase2EvidenceSnapshotStatusTransitionRow, ...]:
    counts = {
        (from_status, to_status): 0
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    }
    for previous_snapshot, next_snapshot in pairs:
        counts[(previous_snapshot.status, next_snapshot.status)] += 1
    return tuple(
        PaperPhase2EvidenceSnapshotStatusTransitionRow(
            from_snapshot_status=from_status,
            to_snapshot_status=to_status,
            transition_count=counts[(from_status, to_status)],
            transition_ratio=_ratio(counts[(from_status, to_status)], total),
        )
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )


def _build_gap_transition_rows(
    pairs: tuple[
        tuple[PaperPhase2EvidenceSnapshotReport, PaperPhase2EvidenceSnapshotReport],
        ...,
    ],
) -> tuple[PaperPhase2EvidenceSnapshotGapTransitionRow, ...]:
    rows: list[PaperPhase2EvidenceSnapshotGapTransitionRow] = []
    for gap_name in EVIDENCE_GAP_NAMES:
        introduced_count = 0
        cleared_count = 0
        persistent_count = 0
        for previous_snapshot, next_snapshot in pairs:
            previous_has_gap = gap_name in previous_snapshot.evidence_gap_names
            next_has_gap = gap_name in next_snapshot.evidence_gap_names
            if not previous_has_gap and next_has_gap:
                introduced_count += 1
            elif previous_has_gap and not next_has_gap:
                cleared_count += 1
            elif previous_has_gap and next_has_gap:
                persistent_count += 1
        rows.append(
            PaperPhase2EvidenceSnapshotGapTransitionRow(
                evidence_gap_name=gap_name,
                introduced_count=introduced_count,
                cleared_count=cleared_count,
                persistent_count=persistent_count,
            ),
        )
    return tuple(rows)


def _introduced_gap_names(
    previous_snapshot: PaperPhase2EvidenceSnapshotReport,
    next_snapshot: PaperPhase2EvidenceSnapshotReport,
) -> tuple[str, ...]:
    previous_gaps = set(previous_snapshot.evidence_gap_names)
    return tuple(
        gap_name
        for gap_name in EVIDENCE_GAP_NAMES
        if gap_name not in previous_gaps and gap_name in next_snapshot.evidence_gap_names
    )


def _cleared_gap_names(
    previous_snapshot: PaperPhase2EvidenceSnapshotReport,
    next_snapshot: PaperPhase2EvidenceSnapshotReport,
) -> tuple[str, ...]:
    next_gaps = set(next_snapshot.evidence_gap_names)
    return tuple(
        gap_name
        for gap_name in EVIDENCE_GAP_NAMES
        if gap_name in previous_snapshot.evidence_gap_names and gap_name not in next_gaps
    )


def _validate_report_consistency(
    report: PaperPhase2EvidenceSnapshotTransitionReport,
) -> None:
    if report.transition_count != _expected_transition_count(report.snapshot_report_count):
        raise ValueError("transition_count must match snapshot_report_count")
    _validate_status_transition_rows(report)
    _validate_gap_transition_rows(report)

    if report.snapshot_report_count == 0:
        _require_none("first_report_generated_at", report.first_report_generated_at)
        _require_none("latest_report_generated_at", report.latest_report_generated_at)
    else:
        if report.first_report_generated_at is None:
            raise ValueError("first_report_generated_at is required with snapshots")
        if report.latest_report_generated_at is None:
            raise ValueError("latest_report_generated_at is required with snapshots")

    if report.transition_count == 0:
        if report.latest_from_status is not None:
            raise ValueError("latest_from_status must be absent without transitions")
        if report.latest_to_status is not None:
            raise ValueError("latest_to_status must be absent without transitions")
        if report.latest_introduced_gap_names:
            raise ValueError(
                "latest_introduced_gap_names must be absent without transitions",
            )
        if report.latest_cleared_gap_names:
            raise ValueError(
                "latest_cleared_gap_names must be absent without transitions",
            )
        return

    if report.latest_from_status is None:
        raise ValueError("latest_from_status is required with transitions")
    if report.latest_to_status is None:
        raise ValueError("latest_to_status is required with transitions")
    if _status_transition_count(
        report,
        report.latest_from_status,
        report.latest_to_status,
    ) < 1:
        raise ValueError("latest_to_status must be counted in status_transition_rows")
    if (
        report.latest_from_status == "phase_2_evidence_observed"
        and report.latest_to_status != "phase_2_evidence_observed"
        and not report.latest_introduced_gap_names
    ):
        raise ValueError("latest_introduced_gap_names must match latest statuses")
    if (
        report.latest_from_status != "phase_2_evidence_observed"
        and report.latest_to_status == "phase_2_evidence_observed"
        and not report.latest_cleared_gap_names
    ):
        raise ValueError("latest_cleared_gap_names must match latest statuses")
    if set(report.latest_introduced_gap_names) & set(report.latest_cleared_gap_names):
        raise ValueError("latest gap changes must not overlap")

    gap_rows = {row.evidence_gap_name: row for row in report.gap_transition_rows}
    for gap_name in report.latest_introduced_gap_names:
        if gap_rows[gap_name].introduced_count < 1:
            raise ValueError("latest_introduced_gap_names must be counted")
    for gap_name in report.latest_cleared_gap_names:
        if gap_rows[gap_name].cleared_count < 1:
            raise ValueError("latest_cleared_gap_names must be counted")


def _validate_status_transition_rows(
    report: PaperPhase2EvidenceSnapshotTransitionReport,
) -> None:
    expected_keys = tuple(
        (from_status, to_status)
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )
    row_keys = tuple(
        (row.from_snapshot_status, row.to_snapshot_status)
        for row in report.status_transition_rows
    )
    if row_keys != expected_keys:
        raise ValueError("status_transition_rows must cover phase 2 status pairs")
    if sum(row.transition_count for row in report.status_transition_rows) != (
        report.transition_count
    ):
        raise ValueError(
            "status_transition_rows counts must sum to transition_count",
        )
    for row in report.status_transition_rows:
        if not _ratio_value_matches(
            row.transition_ratio,
            _ratio(row.transition_count, report.transition_count),
        ):
            raise ValueError(
                "status_transition_rows ratios must match transition counts",
            )


def _validate_gap_transition_rows(
    report: PaperPhase2EvidenceSnapshotTransitionReport,
) -> None:
    if tuple(row.evidence_gap_name for row in report.gap_transition_rows) != (
        EVIDENCE_GAP_NAMES
    ):
        raise ValueError("gap_transition_rows must cover phase 2 gaps")
    for row in report.gap_transition_rows:
        if row.introduced_count > report.transition_count:
            raise ValueError("gap_transition_rows counts cannot exceed transition_count")
        if row.cleared_count > report.transition_count:
            raise ValueError("gap_transition_rows counts cannot exceed transition_count")
        if row.persistent_count > report.transition_count:
            raise ValueError("gap_transition_rows counts cannot exceed transition_count")
        if (
            row.introduced_count + row.cleared_count + row.persistent_count
            > report.transition_count
        ):
            raise ValueError("gap_transition_rows counts cannot exceed transition_count")


def _status_transition_count(
    report: PaperPhase2EvidenceSnapshotTransitionReport,
    from_status: str,
    to_status: str,
) -> int:
    return next(
        row.transition_count
        for row in report.status_transition_rows
        if row.from_snapshot_status == from_status and row.to_snapshot_status == to_status
    )


def _normalize_status_transition_rows(
    rows: tuple[PaperPhase2EvidenceSnapshotStatusTransitionRow, ...],
) -> tuple[PaperPhase2EvidenceSnapshotStatusTransitionRow, ...]:
    normalized = _normalize_typed_tuple(
        "status_transition_rows",
        rows,
        PaperPhase2EvidenceSnapshotStatusTransitionRow,
    )
    expected_keys = tuple(
        (from_status, to_status)
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )
    row_keys = tuple(
        (row.from_snapshot_status, row.to_snapshot_status) for row in normalized
    )
    if row_keys != expected_keys:
        raise ValueError("status_transition_rows must cover phase 2 status pairs")
    return normalized


def _normalize_gap_transition_rows(
    rows: tuple[PaperPhase2EvidenceSnapshotGapTransitionRow, ...],
) -> tuple[PaperPhase2EvidenceSnapshotGapTransitionRow, ...]:
    normalized = _normalize_typed_tuple(
        "gap_transition_rows",
        rows,
        PaperPhase2EvidenceSnapshotGapTransitionRow,
    )
    if tuple(row.evidence_gap_name for row in normalized) != EVIDENCE_GAP_NAMES:
        raise ValueError("gap_transition_rows must cover phase 2 gaps")
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


def _expected_transition_count(snapshot_report_count: int) -> int:
    if snapshot_report_count == 0:
        return 0
    return snapshot_report_count - 1


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
        raise ValueError(f"{field_name} must be None without snapshots")


__all__ = (
    "PaperPhase2EvidenceSnapshotGapTransitionRow",
    "PaperPhase2EvidenceSnapshotStatusTransitionRow",
    "PaperPhase2EvidenceSnapshotTransitionConfig",
    "PaperPhase2EvidenceSnapshotTransitionReport",
    "build_paper_phase_2_evidence_snapshot_transition_report",
)
