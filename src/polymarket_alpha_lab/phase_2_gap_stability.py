"""Pure gap-stability reducer for Phase 2 evidence snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceSnapshotReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperPhase2GapStabilityConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2GapStabilityRow:
    evidence_gap_name: str
    first_seen_index: int | None
    latest_seen_index: int | None
    occurrence_count: int
    occurrence_ratio: Decimal | None
    consecutive_present_count: int
    ever_cleared: bool

    def __post_init__(self) -> None:
        if type(self.evidence_gap_name) is not str:
            raise ValueError("evidence_gap_name must be a string")
        if self.evidence_gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_name must be a known phase 2 gap")
        _require_optional_nonnegative_int("first_seen_index", self.first_seen_index)
        _require_optional_nonnegative_int("latest_seen_index", self.latest_seen_index)
        _require_nonnegative_int("occurrence_count", self.occurrence_count)
        _require_optional_probability_decimal("occurrence_ratio", self.occurrence_ratio)
        _require_nonnegative_int(
            "consecutive_present_count",
            self.consecutive_present_count,
        )
        _require_bool("ever_cleared", self.ever_cleared)
        if self.occurrence_count == 0:
            if self.first_seen_index is not None:
                raise ValueError("first_seen_index must be absent without occurrences")
            if self.latest_seen_index is not None:
                raise ValueError("latest_seen_index must be absent without occurrences")
            if self.consecutive_present_count != 0:
                raise ValueError("consecutive_present_count must be zero without occurrences")
            if self.ever_cleared is not False:
                raise ValueError("ever_cleared must be False without occurrences")
        else:
            if self.first_seen_index is None:
                raise ValueError("first_seen_index is required with occurrences")
            if self.latest_seen_index is None:
                raise ValueError("latest_seen_index is required with occurrences")
            if self.latest_seen_index < self.first_seen_index:
                raise ValueError("latest_seen_index must not precede first_seen_index")


@dataclass(frozen=True)
class PaperPhase2GapStabilityReport:
    generated_at: datetime
    config_version: str
    snapshot_report_count: int
    row_count: int
    stable_gap_names: tuple[str, ...]
    cleared_gap_names: tuple[str, ...]
    rows: tuple[PaperPhase2GapStabilityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("snapshot_report_count", self.snapshot_report_count)
        _require_nonnegative_int("row_count", self.row_count)
        object.__setattr__(
            self,
            "stable_gap_names",
            _normalize_gap_names("stable_gap_names", self.stable_gap_names),
        )
        object.__setattr__(
            self,
            "cleared_gap_names",
            _normalize_gap_names("cleared_gap_names", self.cleared_gap_names),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_gap_stability_report(
    snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...],
    *,
    config: PaperPhase2GapStabilityConfig,
    generated_at: datetime,
) -> PaperPhase2GapStabilityReport:
    if type(config) is not PaperPhase2GapStabilityConfig:
        raise ValueError("config must be a PaperPhase2GapStabilityConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_snapshots(snapshots)
    rows = _build_rows(reports)
    latest_gap_names = set(reports[-1].evidence_gap_names) if reports else set()

    return PaperPhase2GapStabilityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_report_count=len(reports),
        row_count=len(rows),
        stable_gap_names=tuple(
            row.evidence_gap_name
            for row in rows
            if (
                row.consecutive_present_count > 0
                and row.occurrence_count == len(reports)
            )
        ),
        cleared_gap_names=tuple(
            row.evidence_gap_name
            for row in rows
            if row.occurrence_count > 0 and row.evidence_gap_name not in latest_gap_names
        ),
        rows=rows,
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


def _build_rows(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
) -> tuple[PaperPhase2GapStabilityRow, ...]:
    total = len(snapshots)
    rows: list[PaperPhase2GapStabilityRow] = []
    for gap_name in EVIDENCE_GAP_NAMES:
        seen_indexes = tuple(
            index
            for index, snapshot in enumerate(snapshots)
            if gap_name in snapshot.evidence_gap_names
        )
        occurrence_count = len(seen_indexes)
        rows.append(
            PaperPhase2GapStabilityRow(
                evidence_gap_name=gap_name,
                first_seen_index=seen_indexes[0] if seen_indexes else None,
                latest_seen_index=seen_indexes[-1] if seen_indexes else None,
                occurrence_count=occurrence_count,
                occurrence_ratio=_ratio(occurrence_count, total),
                consecutive_present_count=_consecutive_present_count(
                    snapshots,
                    gap_name,
                ),
                ever_cleared=_ever_cleared(snapshots, gap_name),
            ),
        )
    return tuple(rows)


def _consecutive_present_count(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
    gap_name: str,
) -> int:
    count = 0
    for snapshot in reversed(snapshots):
        if gap_name not in snapshot.evidence_gap_names:
            break
        count += 1
    return count


def _ever_cleared(
    snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...],
    gap_name: str,
) -> bool:
    previously_present = False
    for snapshot in snapshots:
        gap_present = gap_name in snapshot.evidence_gap_names
        if previously_present and not gap_present:
            return True
        if gap_present:
            previously_present = True
    return False


def _validate_report_consistency(report: PaperPhase2GapStabilityReport) -> None:
    if report.row_count != len(EVIDENCE_GAP_NAMES):
        raise ValueError("row_count must match phase 2 gap count")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")

    latest_present_names: list[str] = []
    stable_names: list[str] = []
    cleared_names: list[str] = []
    for row in report.rows:
        if row.occurrence_count > report.snapshot_report_count:
            raise ValueError("occurrence_count must not exceed snapshot_report_count")
        if row.consecutive_present_count > row.occurrence_count:
            raise ValueError("consecutive_present_count must not exceed occurrence_count")
        if row.consecutive_present_count > report.snapshot_report_count:
            raise ValueError(
                "consecutive_present_count must not exceed snapshot_report_count",
            )
        if not _ratio_value_matches(
            row.occurrence_ratio,
            _ratio(row.occurrence_count, report.snapshot_report_count),
        ):
            raise ValueError("occurrence_ratio must match occurrence_count")
        if row.occurrence_count == 0:
            if row.ever_cleared:
                raise ValueError("ever_cleared requires an occurrence")
            if row.consecutive_present_count != 0:
                raise ValueError("consecutive_present_count requires an occurrence")
        else:
            if row.first_seen_index is None:
                raise ValueError("first_seen_index is required with occurrences")
            if row.latest_seen_index is None:
                raise ValueError("latest_seen_index is required with occurrences")
            if row.first_seen_index >= report.snapshot_report_count:
                raise ValueError("first_seen_index must be within snapshot bounds")
            if row.latest_seen_index >= report.snapshot_report_count:
                raise ValueError("latest_seen_index must be within snapshot bounds")
            if row.occurrence_count == report.snapshot_report_count:
                if row.first_seen_index != 0:
                    raise ValueError("first_seen_index must match occurrence_count")
                if row.latest_seen_index != report.snapshot_report_count - 1:
                    raise ValueError("latest_seen_index must match occurrence_count")
                if row.consecutive_present_count != report.snapshot_report_count:
                    raise ValueError(
                        "consecutive_present_count must match occurrence_count",
                    )
                if row.ever_cleared:
                    raise ValueError("ever_cleared must be False for stable rows")
            if row.latest_seen_index == report.snapshot_report_count - 1:
                if row.consecutive_present_count < 1:
                    raise ValueError(
                        "consecutive_present_count must match latest_seen_index",
                    )
            elif row.consecutive_present_count != 0:
                raise ValueError(
                    "consecutive_present_count must match latest_seen_index",
                )
            if row.consecutive_present_count > 0:
                latest_present_names.append(row.evidence_gap_name)
            if (
                row.consecutive_present_count > 0
                and row.occurrence_count == report.snapshot_report_count
            ):
                stable_names.append(row.evidence_gap_name)
            if row.consecutive_present_count == 0:
                if not row.ever_cleared:
                    raise ValueError("ever_cleared must match latest absence")
                cleared_names.append(row.evidence_gap_name)
        if row.ever_cleared and row.first_seen_index == row.latest_seen_index:
            if row.consecutive_present_count > 0:
                raise ValueError("ever_cleared must match latest absence")

    if report.stable_gap_names != tuple(stable_names):
        raise ValueError("stable_gap_names must match stable rows")
    if report.cleared_gap_names != tuple(cleared_names):
        raise ValueError("cleared_gap_names must match cleared rows")
    if set(report.stable_gap_names) & set(report.cleared_gap_names):
        raise ValueError("stable_gap_names and cleared_gap_names must not overlap")


def _normalize_rows(
    rows: tuple[PaperPhase2GapStabilityRow, ...],
) -> tuple[PaperPhase2GapStabilityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperPhase2GapStabilityRow:
            raise ValueError("rows must contain PaperPhase2GapStabilityRow values")
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
            raise ValueError(f"{field_name} must contain strings")
        if gap_name not in EVIDENCE_GAP_NAMES:
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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(
    field_name: str,
    value: int | None,
) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


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


__all__ = (
    "PaperPhase2GapStabilityConfig",
    "PaperPhase2GapStabilityReport",
    "PaperPhase2GapStabilityRow",
    "build_paper_phase_2_gap_stability_report",
)
