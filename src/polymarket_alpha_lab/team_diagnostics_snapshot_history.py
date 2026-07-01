"""Pure history reducer for team diagnostics snapshot reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotHistoryConfig:
    config_version: str = "team-diagnostics-snapshot-history-v0"
    min_snapshot_count: int = 2
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_snapshot_count", self.min_snapshot_count)
        _require_paper_flags("TeamDiagnosticsSnapshotHistoryConfig", self)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotHistoryReport:
    generated_at: datetime
    config_version: str
    snapshot_count: int
    required_snapshot_count: int
    status: str
    reason_codes: tuple[str, ...]
    latest_snapshot: object | None
    earliest_generated_at: datetime | None
    latest_generated_at: datetime | None
    span_seconds: int
    status_counts: tuple[tuple[str, int], ...]
    evidence_quality_average_delta: Decimal
    evidence_quality_delta: Decimal
    memory_eligible_delta: int
    settled_calibration_delta: int
    duplicate_latest_generated_at: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("snapshot_count", self.snapshot_count)
        _require_positive_int("required_snapshot_count", self.required_snapshot_count)
        _require_canonical_string("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.earliest_generated_at is not None:
            object.__setattr__(
                self,
                "earliest_generated_at",
                _as_utc("earliest_generated_at", self.earliest_generated_at),
            )
        if self.latest_generated_at is not None:
            object.__setattr__(
                self,
                "latest_generated_at",
                _as_utc("latest_generated_at", self.latest_generated_at),
            )
        _require_nonnegative_int("span_seconds", self.span_seconds)
        object.__setattr__(
            self,
            "status_counts",
            _normalize_status_counts(self.status_counts),
        )
        object.__setattr__(
            self,
            "evidence_quality_average_delta",
            _decimal_value("evidence_quality_average_delta", self.evidence_quality_average_delta),
        )
        object.__setattr__(
            self,
            "evidence_quality_delta",
            _decimal_value("evidence_quality_delta", self.evidence_quality_delta),
        )
        if self.evidence_quality_delta != self.evidence_quality_average_delta:
            raise ValueError("evidence_quality_delta must match evidence_quality_average_delta")
        _require_int("memory_eligible_delta", self.memory_eligible_delta)
        _require_int("settled_calibration_delta", self.settled_calibration_delta)
        if type(self.duplicate_latest_generated_at) is not bool:
            raise ValueError("duplicate_latest_generated_at must be a bool")
        _require_paper_flags("TeamDiagnosticsSnapshotHistoryReport", self)


def build_team_diagnostics_snapshot_history_report(
    snapshots: list[object] | tuple[object, ...],
    *,
    config: TeamDiagnosticsSnapshotHistoryConfig,
    generated_at: datetime,
) -> TeamDiagnosticsSnapshotHistoryReport:
    if type(config) is not TeamDiagnosticsSnapshotHistoryConfig:
        raise ValueError("config must be a TeamDiagnosticsSnapshotHistoryConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    snapshot_items = _normalize_snapshots(snapshots)
    ordered = _ordered_snapshots(snapshot_items)

    reason_codes: list[str] = []
    if len(ordered) < config.min_snapshot_count:
        reason_codes.append("insufficient_history")

    duplicate_latest_generated_at = _has_duplicate_latest_generated_at(ordered)
    if duplicate_latest_generated_at:
        reason_codes.append("duplicate_latest_generated_at")

    latest_snapshot = ordered[-1][1] if ordered else None
    earliest_generated_at = ordered[0][0] if ordered else None
    latest_generated_at = ordered[-1][0] if ordered else None
    status = reason_codes[0] if reason_codes else "observed"
    span_seconds = _span_seconds(earliest_generated_at, latest_generated_at)
    evidence_quality_average_delta = _decimal_delta(
        ordered,
        "evidence_quality_average_quality_score",
        "evidence_quality_average_quality",
        "evidence_quality_average",
    )

    return TeamDiagnosticsSnapshotHistoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        snapshot_count=len(ordered),
        required_snapshot_count=config.min_snapshot_count,
        status=status,
        reason_codes=tuple(reason_codes),
        latest_snapshot=latest_snapshot,
        earliest_generated_at=earliest_generated_at,
        latest_generated_at=latest_generated_at,
        span_seconds=span_seconds,
        status_counts=_status_counts(snapshot_items),
        evidence_quality_average_delta=evidence_quality_average_delta,
        evidence_quality_delta=evidence_quality_average_delta,
        memory_eligible_delta=_int_delta(
            ordered,
            "memory_eligible_count",
            "memory_eligible_reference_count",
        ),
        settled_calibration_delta=_int_delta(
            ordered,
            "calibration_settled_count",
            "settled_calibration_count",
        ),
        duplicate_latest_generated_at=duplicate_latest_generated_at,
    )


def _normalize_snapshots(snapshots: list[object] | tuple[object, ...]) -> tuple[object, ...]:
    if type(snapshots) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    items = tuple(snapshots)
    snapshot_type = _team_diagnostics_snapshot_report_type()
    for snapshot in items:
        if snapshot_type is not None and type(snapshot) is not snapshot_type:
            raise ValueError("snapshots must contain only TeamDiagnosticsSnapshotReport values")
        _as_utc("snapshot generated_at", _value(snapshot, "generated_at"))
        _require_paper_flags("snapshots", snapshot)
        _snapshot_status(snapshot)
        _decimal_snapshot_value(
            snapshot,
            "evidence_quality_average_quality_score",
            "evidence_quality_average_quality",
            "evidence_quality_average",
        )
        _int_snapshot_value(
            snapshot,
            "memory_eligible_reference_count",
            "memory_eligible_count",
        )
        _int_snapshot_value(
            snapshot,
            "calibration_settled_count",
            "settled_calibration_count",
        )
    return items


def _team_diagnostics_snapshot_report_type() -> type | None:
    try:
        from polymarket_alpha_lab.team_diagnostics_snapshot import (  # noqa: PLC0415
            TeamDiagnosticsSnapshotReport,
        )
    except ModuleNotFoundError as exc:
        if exc.name == "polymarket_alpha_lab.team_diagnostics_snapshot":
            return None
        raise
    except ImportError:
        return None
    return TeamDiagnosticsSnapshotReport


def _ordered_snapshots(snapshots: tuple[object, ...]) -> tuple[tuple[datetime, object], ...]:
    indexed = tuple(
        (_as_utc("snapshot generated_at", _value(snapshot, "generated_at")), index, snapshot)
        for index, snapshot in enumerate(snapshots)
    )
    return tuple((generated_at, snapshot) for generated_at, _, snapshot in sorted(indexed))


def _has_duplicate_latest_generated_at(ordered: tuple[tuple[datetime, object], ...]) -> bool:
    if not ordered:
        return False
    latest_generated_at = ordered[-1][0]
    return sum(1 for generated_at, _ in ordered if generated_at == latest_generated_at) > 1


def _span_seconds(
    earliest_generated_at: datetime | None,
    latest_generated_at: datetime | None,
) -> int:
    if earliest_generated_at is None or latest_generated_at is None:
        return 0
    span = latest_generated_at - earliest_generated_at
    return int(span.total_seconds())


def _status_counts(snapshots: tuple[object, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for snapshot in snapshots:
        status = _snapshot_status(snapshot)
        counts[status] = counts.get(status, 0) + 1
    return tuple(sorted(counts.items()))


def _snapshot_status(snapshot: object) -> str:
    status = _value(snapshot, "status", _value(snapshot, "evidence_quality_status", None))
    _require_canonical_string("snapshot status", status)
    return status


def _decimal_delta(
    ordered: tuple[tuple[datetime, object], ...],
    *names: str,
) -> Decimal:
    if not ordered:
        return Decimal("0")
    earliest = _decimal_snapshot_value(ordered[0][1], *names)
    latest = _decimal_snapshot_value(ordered[-1][1], *names)
    return latest - earliest


def _int_delta(
    ordered: tuple[tuple[datetime, object], ...],
    *names: str,
) -> int:
    if not ordered:
        return 0
    earliest = _int_snapshot_value(ordered[0][1], *names)
    latest = _int_snapshot_value(ordered[-1][1], *names)
    return latest - earliest


def _decimal_snapshot_value(snapshot: object, *names: str) -> Decimal:
    name, value = _first_present_value(snapshot, *names)
    return _decimal_value(name, value)


def _int_snapshot_value(snapshot: object, *names: str) -> int:
    name, value = _first_present_value(snapshot, *names)
    return _int_value(name, value)


def _first_present_value(snapshot: object, *names: str) -> tuple[str, object]:
    for name in names:
        value = _value(snapshot, name, None)
        if value is not None:
            return name, value
    return names[0], None


def _value(container: object, name: str, default: Any = None) -> Any:
    return getattr(container, name, default)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_value(name: str, value: object) -> Decimal:
    if type(value) is Decimal:
        return value
    raise ValueError(f"{name} must be a Decimal")


def _int_value(name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an int")
    return value


def _require_int(name: str, value: object) -> None:
    _int_value(name, value)


def _require_nonnegative_int(name: str, value: object) -> None:
    int_value = _int_value(name, value)
    if int_value < 0:
        raise ValueError(f"{name} must be nonnegative")


def _require_positive_int(name: str, value: object) -> None:
    int_value = _int_value(name, value)
    if int_value <= 0:
        raise ValueError(f"{name} must be positive")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    items = tuple(reason_codes)
    for reason_code in items:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must be unique")
    return items


def _normalize_status_counts(
    status_counts: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if type(status_counts) not in (list, tuple):
        raise ValueError("status_counts must be a list or tuple")
    normalized = tuple(status_counts)
    seen_statuses: set[str] = set()
    for item in normalized:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("status_counts entries must be status/count pairs")
        status, count = item
        _require_canonical_string("status_counts status", status)
        _require_nonnegative_int("status_counts count", count)
        if status in seen_statuses:
            raise ValueError("status_counts statuses must be unique")
        seen_statuses.add(status)
    return normalized


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_paper_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "TeamDiagnosticsSnapshotHistoryConfig",
    "TeamDiagnosticsSnapshotHistoryReport",
    "build_team_diagnostics_snapshot_history_report",
)
