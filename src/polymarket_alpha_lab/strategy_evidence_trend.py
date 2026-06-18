"""Paper-only Strategy Evidence Snapshot trend summaries.

This module is pure report assembly over caller-supplied
PaperStrategyEvidenceSnapshotReport values. It performs no file IO, network
access, client construction, authentication, wallet handling, order handling,
ranking, recommendation, trade instruction, execution, or financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.strategy_evidence import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
    PaperStrategyEvidenceSnapshotReport,
)


__all__ = (
    "PaperStrategyEvidenceTrendConfig",
    "PaperStrategyEvidenceTrendGapRow",
    "PaperStrategyEvidenceTrendReport",
    "PaperStrategyEvidenceTrendStatusRow",
    "build_paper_strategy_evidence_trend_report",
)


RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class PaperStrategyEvidenceTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperStrategyEvidenceTrendStatusRow:
    snapshot_status: str
    snapshot_count: int
    snapshot_ratio: Decimal | None

    def __post_init__(self) -> None:
        if (
            type(self.snapshot_status) is not str
            or self.snapshot_status not in SNAPSHOT_STATUSES
        ):
            raise ValueError("snapshot_status must be a known evidence snapshot status")
        _require_nonnegative_int("snapshot_count", self.snapshot_count)
        _require_optional_probability_decimal("snapshot_ratio", self.snapshot_ratio)


@dataclass(frozen=True)
class PaperStrategyEvidenceTrendGapRow:
    evidence_gap_name: str
    gap_count: int
    gap_ratio: Decimal | None

    def __post_init__(self) -> None:
        if (
            type(self.evidence_gap_name) is not str
            or self.evidence_gap_name not in EVIDENCE_GAP_NAMES
        ):
            raise ValueError("evidence_gap_name must be a known evidence gap")
        _require_nonnegative_int("gap_count", self.gap_count)
        _require_optional_probability_decimal("gap_ratio", self.gap_ratio)


@dataclass(frozen=True)
class PaperStrategyEvidenceTrendReport:
    generated_at: datetime
    config_version: str
    snapshot_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_status: str | None
    latest_evidence_gap_names: tuple[str, ...]
    consecutive_local_risk_flags_count: int
    consecutive_non_observed_count: int
    status_rows: tuple[PaperStrategyEvidenceTrendStatusRow, ...]
    gap_rows: tuple[PaperStrategyEvidenceTrendGapRow, ...]
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
        if self.latest_status is not None:
            if (
                type(self.latest_status) is not str
                or self.latest_status not in SNAPSHOT_STATUSES
            ):
                raise ValueError(
                    "latest_status must be a known evidence snapshot status",
                )
        object.__setattr__(
            self,
            "latest_evidence_gap_names",
            _normalize_latest_evidence_gap_names(self.latest_evidence_gap_names),
        )
        _require_nonnegative_int(
            "consecutive_local_risk_flags_count",
            self.consecutive_local_risk_flags_count,
        )
        _require_nonnegative_int(
            "consecutive_non_observed_count",
            self.consecutive_non_observed_count,
        )
        object.__setattr__(
            self,
            "status_rows",
            _clone_status_rows(self.status_rows),
        )
        object.__setattr__(
            self,
            "gap_rows",
            _clone_gap_rows(self.gap_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")

    @property
    def snapshot_count(self) -> int:
        return self.snapshot_report_count

    @property
    def latest_snapshot_status(self) -> str | None:
        return self.latest_status

    @property
    def first_snapshot_generated_at(self) -> datetime | None:
        return self.first_report_generated_at

    @property
    def latest_snapshot_generated_at(self) -> datetime | None:
        return self.latest_report_generated_at

    @property
    def latest_gap_names(self) -> tuple[str, ...]:
        return self.latest_evidence_gap_names


def build_paper_strategy_evidence_trend_report(
    snapshots: list[PaperStrategyEvidenceSnapshotReport]
    | tuple[PaperStrategyEvidenceSnapshotReport, ...],
    *,
    config: PaperStrategyEvidenceTrendConfig,
    generated_at: datetime,
) -> PaperStrategyEvidenceTrendReport:
    if type(config) is not PaperStrategyEvidenceTrendConfig:
        raise ValueError("config must be a PaperStrategyEvidenceTrendConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    reports = _normalize_snapshots(snapshots)
    snapshot_report_count = len(reports)
    status_counts = _status_counts(reports)
    gap_counts = _gap_counts(reports)
    latest = reports[-1] if reports else None

    return PaperStrategyEvidenceTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_report_count=snapshot_report_count,
        first_report_generated_at=reports[0].generated_at if reports else None,
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_status=latest.status if latest is not None else None,
        latest_evidence_gap_names=latest.evidence_gap_names if latest is not None else (),
        consecutive_local_risk_flags_count=_consecutive_local_risk_flags_count(
            reports,
        ),
        consecutive_non_observed_count=_consecutive_non_observed_count(reports),
        status_rows=_build_status_rows(status_counts, snapshot_report_count),
        gap_rows=_build_gap_rows(gap_counts, snapshot_report_count),
    )


def _normalize_snapshots(
    snapshots: list[PaperStrategyEvidenceSnapshotReport]
    | tuple[PaperStrategyEvidenceSnapshotReport, ...],
) -> tuple[PaperStrategyEvidenceSnapshotReport, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    return tuple(_clone_snapshot(snapshot) for snapshot in snapshots)


def _clone_snapshot(
    snapshot: PaperStrategyEvidenceSnapshotReport,
) -> PaperStrategyEvidenceSnapshotReport:
    if type(snapshot) is not PaperStrategyEvidenceSnapshotReport:
        raise ValueError(
            "snapshots must contain PaperStrategyEvidenceSnapshotReport values",
        )
    return PaperStrategyEvidenceSnapshotReport(
        generated_at=snapshot.generated_at,
        config_version=snapshot.config_version,
        status=snapshot.status,
        cycle_count=snapshot.cycle_count,
        paper_trade_count=snapshot.paper_trade_count,
        nav_snapshot_count=snapshot.nav_snapshot_count,
        outcome_checked_count=snapshot.outcome_checked_count,
        outcome_pending_count=snapshot.outcome_pending_count,
        outcome_resolved_count=snapshot.outcome_resolved_count,
        outcome_unresolved_count=snapshot.outcome_unresolved_count,
        audit_report_count=snapshot.audit_report_count,
        latest_audit_status=snapshot.latest_audit_status,
        negative_cost_adjusted_edge_count=snapshot.negative_cost_adjusted_edge_count,
        unexecutable_open_position_count=snapshot.unexecutable_open_position_count,
        evidence_gap_names=snapshot.evidence_gap_names,
        paper_only=snapshot.paper_only,
        report_only=snapshot.report_only,
    )


def _status_counts(
    snapshots: tuple[PaperStrategyEvidenceSnapshotReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in SNAPSHOT_STATUSES}
    for snapshot in snapshots:
        counts[snapshot.status] += 1
    return counts


def _gap_counts(
    snapshots: tuple[PaperStrategyEvidenceSnapshotReport, ...],
) -> dict[str, int]:
    counts = {gap_name: 0 for gap_name in EVIDENCE_GAP_NAMES}
    for snapshot in snapshots:
        for gap_name in snapshot.evidence_gap_names:
            counts[gap_name] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperStrategyEvidenceTrendStatusRow, ...]:
    return tuple(
        PaperStrategyEvidenceTrendStatusRow(
            snapshot_status=status,
            snapshot_count=status_counts[status],
            snapshot_ratio=_ratio(status_counts[status], total),
        )
        for status in SNAPSHOT_STATUSES
    )


def _build_gap_rows(
    gap_counts: dict[str, int],
    total: int,
) -> tuple[PaperStrategyEvidenceTrendGapRow, ...]:
    return tuple(
        PaperStrategyEvidenceTrendGapRow(
            evidence_gap_name=gap_name,
            gap_count=gap_counts[gap_name],
            gap_ratio=_ratio(gap_counts[gap_name], total),
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )


def _consecutive_local_risk_flags_count(
    snapshots: tuple[PaperStrategyEvidenceSnapshotReport, ...],
) -> int:
    count = 0
    for snapshot in reversed(snapshots):
        if snapshot.status != "local_risk_flags":
            break
        count += 1
    return count


def _consecutive_non_observed_count(
    snapshots: tuple[PaperStrategyEvidenceSnapshotReport, ...],
) -> int:
    count = 0
    for snapshot in reversed(snapshots):
        if snapshot.status == "local_evidence_observed":
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


def _validate_report_consistency(report: PaperStrategyEvidenceTrendReport) -> None:
    if report.snapshot_report_count == 0:
        if report.latest_status is not None:
            raise ValueError("latest_status must be absent without snapshots")
        if (
            report.first_report_generated_at is not None
            or report.latest_report_generated_at is not None
        ):
            raise ValueError("snapshot timestamp bounds must be absent without snapshots")
        if report.consecutive_local_risk_flags_count != 0:
            raise ValueError("risk flag streak must be zero without snapshots")
        if report.consecutive_non_observed_count != 0:
            raise ValueError("consecutive count must be zero without snapshots")
        if report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must be absent without snapshots")
    else:
        if report.latest_status is None:
            raise ValueError("latest_status is required with snapshots")
        if (
            report.first_report_generated_at is None
            or report.latest_report_generated_at is None
        ):
            raise ValueError("snapshot timestamp bounds are required with snapshots")
        if report.consecutive_local_risk_flags_count > report.snapshot_report_count:
            raise ValueError("risk flag streak must not exceed snapshot_report_count")
        if report.consecutive_non_observed_count > report.snapshot_report_count:
            raise ValueError("consecutive count must not exceed snapshot_count")
        if report.latest_status == "local_evidence_observed":
            if report.consecutive_local_risk_flags_count != 0:
                raise ValueError("observed latest snapshot must reset risk flag streak")
            if report.consecutive_non_observed_count != 0:
                raise ValueError("observed latest snapshot must reset the streak")
            if report.latest_evidence_gap_names:
                raise ValueError("observed latest snapshot must not expose gaps")
        elif report.latest_status == "local_evidence_gaps":
            if not report.latest_evidence_gap_names:
                raise ValueError("latest_evidence_gap_names must match latest_status")
            if any(_is_risk_gap_name(name) for name in report.latest_evidence_gap_names):
                raise ValueError("latest_evidence_gap_names must match latest_status")
        elif report.latest_status == "local_risk_flags":
            if not any(
                _is_risk_gap_name(name) for name in report.latest_evidence_gap_names
            ):
                raise ValueError("latest_evidence_gap_names must match latest_status")
        elif report.consecutive_non_observed_count < 1:
            raise ValueError("non-observed latest snapshot requires a streak")
        if report.latest_status == "local_risk_flags":
            if report.consecutive_local_risk_flags_count < 1:
                raise ValueError("risk latest snapshot requires a risk flag streak")
        elif report.consecutive_local_risk_flags_count != 0:
            raise ValueError("non-risk latest snapshot must reset risk flag streak")
    status_row_keys = tuple(row.snapshot_status for row in report.status_rows)
    if status_row_keys != SNAPSHOT_STATUSES:
        raise ValueError("status_rows must cover evidence snapshot statuses")
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
    gap_row_keys = tuple(row.evidence_gap_name for row in report.gap_rows)
    if gap_row_keys != EVIDENCE_GAP_NAMES:
        raise ValueError("gap_rows must cover evidence gap names")
    for row in report.gap_rows:
        if row.gap_count > report.snapshot_report_count:
            raise ValueError("gap_rows counts must not exceed snapshot_report_count")
        if not _ratio_value_matches(
            row.gap_ratio,
            _ratio(row.gap_count, report.snapshot_report_count),
        ):
            raise ValueError("gap_rows ratios must match snapshot counts")
    _validate_latest_gap_state(report)


def _validate_latest_gap_state(report: PaperStrategyEvidenceTrendReport) -> None:
    if report.latest_status == "local_evidence_gaps":
        if not report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        if any(
            gap_name in ("negative_cost_adjusted_edges", "unexecutable_open_positions")
            for gap_name in report.latest_evidence_gap_names
        ):
            raise ValueError("latest_evidence_gap_names must match latest_status")
    elif report.latest_status == "local_risk_flags":
        if not report.latest_evidence_gap_names:
            raise ValueError("latest_evidence_gap_names must match latest_status")
        if not any(
            gap_name in ("negative_cost_adjusted_edges", "unexecutable_open_positions")
            for gap_name in report.latest_evidence_gap_names
        ):
            raise ValueError("latest_evidence_gap_names must match latest_status")
    elif report.latest_evidence_gap_names:
        raise ValueError("latest_evidence_gap_names must match latest_status")

    gap_counts = {row.evidence_gap_name: row.gap_count for row in report.gap_rows}
    for gap_name in report.latest_evidence_gap_names:
        if gap_counts[gap_name] == 0:
            raise ValueError("latest_evidence_gap_names must be counted in gap_rows")


def _clone_status_rows(
    rows: tuple[PaperStrategyEvidenceTrendStatusRow, ...],
) -> tuple[PaperStrategyEvidenceTrendStatusRow, ...]:
    return tuple(
        PaperStrategyEvidenceTrendStatusRow(
            snapshot_status=row.snapshot_status,
            snapshot_count=row.snapshot_count,
            snapshot_ratio=row.snapshot_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            rows,
            PaperStrategyEvidenceTrendStatusRow,
        )
    )


def _clone_gap_rows(
    rows: tuple[PaperStrategyEvidenceTrendGapRow, ...],
) -> tuple[PaperStrategyEvidenceTrendGapRow, ...]:
    return tuple(
        PaperStrategyEvidenceTrendGapRow(
            evidence_gap_name=row.evidence_gap_name,
            gap_count=row.gap_count,
            gap_ratio=row.gap_ratio,
        )
        for row in _normalize_typed_tuple(
            "gap_rows",
            rows,
            PaperStrategyEvidenceTrendGapRow,
        )
    )


def _normalize_typed_tuple(
    field_name: str,
    values: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
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


def _normalize_latest_evidence_gap_names(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("latest_evidence_gap_names must be an iterable")
    try:
        gap_names = tuple(values)
    except TypeError as exc:
        raise ValueError("latest_evidence_gap_names must be an iterable") from exc
    if len(set(gap_names)) != len(gap_names):
        raise ValueError("latest_evidence_gap_names must not contain duplicates")
    for gap_name in gap_names:
        if type(gap_name) is not str or gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("latest_evidence_gap_names must contain known gap names")
    expected_order = tuple(
        gap_name for gap_name in EVIDENCE_GAP_NAMES if gap_name in gap_names
    )
    if gap_names != expected_order:
        raise ValueError("latest_evidence_gap_names must use deterministic ordering")
    return gap_names


def _is_risk_gap_name(gap_name: str) -> bool:
    return gap_name in (
        "negative_cost_adjusted_edges",
        "unexecutable_open_positions",
    )


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
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
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between zero and one")
    if (
        value != value.quantize(RATIO_QUANTUM)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _ratio_value_matches(value: Decimal | None, expected: Decimal | None) -> bool:
    if value != expected:
        return False
    if expected is None:
        return value is None
    if type(value) is not Decimal:
        return False
    return (
        value == value.quantize(RATIO_QUANTUM)
        and value.as_tuple().exponent == RATIO_QUANTUM.as_tuple().exponent
    )
