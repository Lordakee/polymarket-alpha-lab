from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceSnapshotReport,
)


@dataclass(frozen=True)
class PaperPhase2GapDeltaConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2GapDeltaRow:
    evidence_gap_name: str
    introduced_count: int
    cleared_count: int
    persistent_count: int

    def __post_init__(self) -> None:
        if type(self.evidence_gap_name) is not str:
            raise ValueError("evidence_gap_name must be a string")
        if self.evidence_gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_name must be a known phase 2 gap")
        _require_nonnegative_int("introduced_count", self.introduced_count)
        _require_nonnegative_int("cleared_count", self.cleared_count)
        _require_nonnegative_int("persistent_count", self.persistent_count)


@dataclass(frozen=True)
class PaperPhase2GapDeltaReport:
    generated_at: datetime
    config_version: str
    snapshot_pair_count: int
    latest_from_generated_at: datetime | None
    latest_to_generated_at: datetime | None
    latest_introduced_gap_names: tuple[str, ...]
    latest_cleared_gap_names: tuple[str, ...]
    total_introduced_gap_count: int
    total_cleared_gap_count: int
    rows: tuple[PaperPhase2GapDeltaRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "latest_from_generated_at",
            _as_optional_utc(self.latest_from_generated_at),
        )
        object.__setattr__(
            self,
            "latest_to_generated_at",
            _as_optional_utc(self.latest_to_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("snapshot_pair_count", self.snapshot_pair_count)
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
        _require_nonnegative_int(
            "total_introduced_gap_count",
            self.total_introduced_gap_count,
        )
        _require_nonnegative_int(
            "total_cleared_gap_count",
            self.total_cleared_gap_count,
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_gap_delta_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2GapDeltaConfig,
    generated_at: datetime,
) -> PaperPhase2GapDeltaReport:
    if type(config) is not PaperPhase2GapDeltaConfig:
        raise ValueError("config must be a PaperPhase2GapDeltaConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_snapshots(snapshots)
    pairs = tuple(zip(reports, reports[1:], strict=False))
    latest_pair = pairs[-1] if pairs else None
    rows = _build_rows(pairs)

    return PaperPhase2GapDeltaReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_pair_count=len(pairs),
        latest_from_generated_at=None if latest_pair is None else latest_pair[0].generated_at,
        latest_to_generated_at=None if latest_pair is None else latest_pair[1].generated_at,
        latest_introduced_gap_names=(
            () if latest_pair is None else _introduced_gap_names(*latest_pair)
        ),
        latest_cleared_gap_names=(
            () if latest_pair is None else _cleared_gap_names(*latest_pair)
        ),
        total_introduced_gap_count=sum(row.introduced_count for row in rows),
        total_cleared_gap_count=sum(row.cleared_count for row in rows),
        rows=rows,
    )


def _normalize_snapshots(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> tuple[PaperPhase2EvidenceSnapshotReport, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    reports = tuple(snapshots)
    for snapshot in reports:
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
    return reports


def _build_rows(
    pairs: tuple[
        tuple[PaperPhase2EvidenceSnapshotReport, PaperPhase2EvidenceSnapshotReport],
        ...,
    ],
) -> tuple[PaperPhase2GapDeltaRow, ...]:
    rows: list[PaperPhase2GapDeltaRow] = []
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
            PaperPhase2GapDeltaRow(
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
    previous_gap_names = set(previous_snapshot.evidence_gap_names)
    return tuple(
        gap_name
        for gap_name in EVIDENCE_GAP_NAMES
        if gap_name not in previous_gap_names
        and gap_name in next_snapshot.evidence_gap_names
    )


def _cleared_gap_names(
    previous_snapshot: PaperPhase2EvidenceSnapshotReport,
    next_snapshot: PaperPhase2EvidenceSnapshotReport,
) -> tuple[str, ...]:
    next_gap_names = set(next_snapshot.evidence_gap_names)
    return tuple(
        gap_name
        for gap_name in EVIDENCE_GAP_NAMES
        if gap_name in previous_snapshot.evidence_gap_names
        and gap_name not in next_gap_names
    )


def _validate_report_consistency(report: PaperPhase2GapDeltaReport) -> None:
    if report.snapshot_pair_count == 0:
        _require_none("latest_from_generated_at", report.latest_from_generated_at)
        _require_none("latest_to_generated_at", report.latest_to_generated_at)
        if report.latest_introduced_gap_names:
            raise ValueError(
                "latest_introduced_gap_names must be absent without pairs",
            )
        if report.latest_cleared_gap_names:
            raise ValueError("latest_cleared_gap_names must be absent without pairs")
    else:
        if report.latest_from_generated_at is None:
            raise ValueError("latest_from_generated_at is required with pairs")
        if report.latest_to_generated_at is None:
            raise ValueError("latest_to_generated_at is required with pairs")

    if set(report.latest_introduced_gap_names) & set(report.latest_cleared_gap_names):
        raise ValueError("latest gap names must not overlap")
    if report.snapshot_pair_count == 1:
        expected_latest_introduced_gap_names = tuple(
            row.evidence_gap_name for row in report.rows if row.introduced_count == 1
        )
        expected_latest_cleared_gap_names = tuple(
            row.evidence_gap_name for row in report.rows if row.cleared_count == 1
        )
        if report.latest_introduced_gap_names != expected_latest_introduced_gap_names:
            raise ValueError("latest_introduced_gap_names must match rows")
        if report.latest_cleared_gap_names != expected_latest_cleared_gap_names:
            raise ValueError("latest_cleared_gap_names must match rows")
    if sum(row.introduced_count for row in report.rows) != (
        report.total_introduced_gap_count
    ):
        raise ValueError("total_introduced_gap_count must match rows")
    if sum(row.cleared_count for row in report.rows) != (
        report.total_cleared_gap_count
    ):
        raise ValueError("total_cleared_gap_count must match rows")

    row_by_gap_name = {row.evidence_gap_name: row for row in report.rows}
    for gap_name in report.latest_introduced_gap_names:
        if row_by_gap_name[gap_name].introduced_count < 1:
            raise ValueError("latest_introduced_gap_names must be counted")
    for gap_name in report.latest_cleared_gap_names:
        if row_by_gap_name[gap_name].cleared_count < 1:
            raise ValueError("latest_cleared_gap_names must be counted")
    for row in report.rows:
        if row.introduced_count > report.snapshot_pair_count:
            raise ValueError("row counts must not exceed snapshot_pair_count")
        if row.cleared_count > report.snapshot_pair_count:
            raise ValueError("row counts must not exceed snapshot_pair_count")
        if row.persistent_count > report.snapshot_pair_count:
            raise ValueError("row counts must not exceed snapshot_pair_count")
        if (
            row.introduced_count + row.cleared_count + row.persistent_count
            > report.snapshot_pair_count
        ):
            raise ValueError("row counts must not exceed snapshot_pair_count")


def _normalize_rows(
    rows: tuple[PaperPhase2GapDeltaRow, ...],
) -> tuple[PaperPhase2GapDeltaRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperPhase2GapDeltaRow:
            raise ValueError("rows must contain PaperPhase2GapDeltaRow values")
    if tuple(row.evidence_gap_name for row in normalized) != EVIDENCE_GAP_NAMES:
        raise ValueError("rows must cover phase 2 gaps")
    return normalized


def _normalize_gap_names(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        gap_names = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(gap_names)) != len(gap_names):
        raise ValueError(f"{field_name} must not contain duplicates")
    for gap_name in gap_names:
        if type(gap_name) is not str:
            raise ValueError(f"{field_name} must contain string values")
        if gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError(f"{field_name} must contain known gap names")
    expected_gap_names = tuple(
        gap_name for gap_name in EVIDENCE_GAP_NAMES if gap_name in gap_names
    )
    if gap_names != expected_gap_names:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return gap_names


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


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be absent")


__all__ = (
    "PaperPhase2GapDeltaConfig",
    "PaperPhase2GapDeltaReport",
    "PaperPhase2GapDeltaRow",
    "build_paper_phase_2_gap_delta_report",
)
