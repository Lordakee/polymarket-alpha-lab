"""Pure paper-only reducer for in-memory recommendation cycle snapshots."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable

from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
)


STATUSES = ("pass", "watch", "blocked")
QUANTUM = Decimal("0.000001")
SECONDS_PER_HOUR = Decimal("3600")
MICROSECONDS_PER_SECOND = Decimal("1000000")
REQUIRED_ARTIFACT_NAMES = (
    "strategy_cycle_blocked_counts",
    "strategy_cycle_screening_report",
)


@dataclass(frozen=True)
class PaperRecommendationCycleReviewConfig:
    config_version: str
    stale_after_hours: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_decimal_hours("stale_after_hours", self.stale_after_hours)


@dataclass(frozen=True)
class PaperRecommendationCycleReviewReasonCodeCount:
    reason_code: str
    count: int

    def __post_init__(self) -> None:
        _require_canonical_token("reason_code", self.reason_code)
        _require_positive_int("count", self.count)


@dataclass(frozen=True)
class PaperRecommendationCycleReviewReport:
    generated_at: datetime
    config_version: str
    snapshot_count: int
    latest_generated_at: datetime | None
    latest_final_status: str | None
    blocked_snapshot_count: int
    watch_snapshot_count: int
    pass_snapshot_count: int
    blocked_artifact_count: int
    watch_artifact_count: int
    missing_required_artifact_names: tuple[str, ...]
    reason_code_counts: tuple[PaperRecommendationCycleReviewReasonCodeCount, ...]
    review_status: str
    stale_history: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("snapshot_count", self.snapshot_count)
        if self.latest_generated_at is not None:
            object.__setattr__(
                self,
                "latest_generated_at",
                _as_utc("latest_generated_at", self.latest_generated_at),
            )
        _require_optional_status("latest_final_status", self.latest_final_status)
        for field_name in (
            "blocked_snapshot_count",
            "watch_snapshot_count",
            "pass_snapshot_count",
            "blocked_artifact_count",
            "watch_artifact_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "missing_required_artifact_names",
            _normalize_required_artifact_names(self.missing_required_artifact_names),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_status("review_status", self.review_status)
        if type(self.stale_history) is not bool:
            raise ValueError("stale_history must be a bool")
        _validate_report_consistency(self)
        _require_hard_flags("cycle review report", self)


def build_paper_recommendation_cycle_review_report(
    snapshots: Iterable[PaperRecommendationCycleSnapshotReport],
    *,
    config: PaperRecommendationCycleReviewConfig,
    generated_at: datetime,
) -> PaperRecommendationCycleReviewReport:
    """Summarize supplied in-memory paper recommendation cycle snapshots."""

    if type(config) is not PaperRecommendationCycleReviewConfig:
        raise ValueError("config must be PaperRecommendationCycleReviewConfig")
    review_generated_at = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    latest_snapshot = _latest_snapshot(normalized_snapshots)
    missing_required_artifact_names = _missing_required_artifact_names(latest_snapshot)
    watch_artifact_count = sum(
        snapshot.watch_artifact_count for snapshot in normalized_snapshots
    )
    stale_history = _stale_history(
        latest_snapshot=latest_snapshot,
        generated_at=review_generated_at,
        stale_after_hours=config.stale_after_hours,
    )

    return PaperRecommendationCycleReviewReport(
        generated_at=review_generated_at,
        config_version=config.config_version,
        snapshot_count=len(normalized_snapshots),
        latest_generated_at=latest_snapshot.generated_at if latest_snapshot else None,
        latest_final_status=latest_snapshot.final_status if latest_snapshot else None,
        blocked_snapshot_count=_snapshot_status_count(normalized_snapshots, "blocked"),
        watch_snapshot_count=_snapshot_status_count(normalized_snapshots, "watch"),
        pass_snapshot_count=_snapshot_status_count(normalized_snapshots, "pass"),
        blocked_artifact_count=sum(
            snapshot.blocked_artifact_count for snapshot in normalized_snapshots
        ),
        watch_artifact_count=watch_artifact_count,
        missing_required_artifact_names=missing_required_artifact_names,
        reason_code_counts=_reason_code_counts(normalized_snapshots),
        review_status=_review_status(
            snapshot_count=len(normalized_snapshots),
            latest_snapshot=latest_snapshot,
            missing_required_artifact_names=missing_required_artifact_names,
            stale_history=stale_history,
            watch_artifact_count=watch_artifact_count,
        ),
        stale_history=stale_history,
    )


def _normalize_snapshots(
    snapshots: Iterable[PaperRecommendationCycleSnapshotReport],
) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        normalized = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    for snapshot in normalized:
        if type(snapshot) is not PaperRecommendationCycleSnapshotReport:
            raise ValueError("snapshots must contain PaperRecommendationCycleSnapshotReport")
        _require_hard_flags("cycle snapshot", snapshot)
    return normalized


def _latest_snapshot(
    snapshots: tuple[PaperRecommendationCycleSnapshotReport, ...],
) -> PaperRecommendationCycleSnapshotReport | None:
    if not snapshots:
        return None
    return max(snapshots, key=lambda snapshot: snapshot.generated_at)


def _missing_required_artifact_names(
    latest_snapshot: PaperRecommendationCycleSnapshotReport | None,
) -> tuple[str, ...]:
    if latest_snapshot is None:
        present_names: frozenset[str] = frozenset()
    else:
        present_names = frozenset(
            row.artifact_name for row in latest_snapshot.artifact_index_report.rows
        )
    return tuple(
        artifact_name
        for artifact_name in REQUIRED_ARTIFACT_NAMES
        if artifact_name not in present_names
    )


def _stale_history(
    *,
    latest_snapshot: PaperRecommendationCycleSnapshotReport | None,
    generated_at: datetime,
    stale_after_hours: Decimal,
) -> bool:
    if latest_snapshot is None:
        return False
    elapsed = generated_at - latest_snapshot.generated_at
    elapsed_seconds = (
        (Decimal(elapsed.days) * Decimal("86400"))
        + Decimal(elapsed.seconds)
        + (Decimal(elapsed.microseconds) / MICROSECONDS_PER_SECOND)
    )
    elapsed_hours = elapsed_seconds / SECONDS_PER_HOUR
    return elapsed_hours > stale_after_hours


def _snapshot_status_count(
    snapshots: tuple[PaperRecommendationCycleSnapshotReport, ...],
    status: str,
) -> int:
    return sum(1 for snapshot in snapshots if snapshot.final_status == status)


def _reason_code_counts(
    snapshots: tuple[PaperRecommendationCycleSnapshotReport, ...],
) -> tuple[PaperRecommendationCycleReviewReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for snapshot in snapshots:
        counts.update(snapshot.reason_codes)
    return tuple(
        PaperRecommendationCycleReviewReasonCodeCount(reason_code=reason_code, count=count)
        for reason_code, count in sorted(counts.items())
    )


def _review_status(
    *,
    snapshot_count: int,
    latest_snapshot: PaperRecommendationCycleSnapshotReport | None,
    missing_required_artifact_names: tuple[str, ...],
    stale_history: bool,
    watch_artifact_count: int,
) -> str:
    if snapshot_count == 0:
        return "blocked"
    if latest_snapshot is None:
        return "blocked"
    if latest_snapshot.final_status == "blocked":
        return "blocked"
    if missing_required_artifact_names:
        return "blocked"
    if stale_history:
        return "watch"
    if latest_snapshot.final_status == "watch":
        return "watch"
    if watch_artifact_count > 0:
        return "watch"
    return "pass"


def _validate_report_consistency(report: PaperRecommendationCycleReviewReport) -> None:
    status_count_total = (
        report.blocked_snapshot_count
        + report.watch_snapshot_count
        + report.pass_snapshot_count
    )
    if report.snapshot_count != status_count_total:
        raise ValueError("snapshot status counts must match snapshot_count")
    if report.snapshot_count == 0:
        if report.latest_generated_at is not None:
            raise ValueError("latest_generated_at must be None without snapshots")
        if report.latest_final_status is not None:
            raise ValueError("latest_final_status must be None without snapshots")
        return
    if report.latest_generated_at is None:
        raise ValueError("latest_generated_at is required with snapshots")
    if report.latest_final_status is None:
        raise ValueError("latest_final_status is required with snapshots")


def _normalize_required_artifact_names(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("missing_required_artifact_names must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("missing_required_artifact_names must be an iterable") from exc
    for value in normalized:
        _require_canonical_token("missing_required_artifact_names", value)
    if normalized != tuple(
        artifact_name
        for artifact_name in REQUIRED_ARTIFACT_NAMES
        if artifact_name in normalized
    ):
        raise ValueError("missing_required_artifact_names must use declared order")
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[PaperRecommendationCycleReviewReasonCodeCount],
) -> tuple[PaperRecommendationCycleReviewReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    previous_reason_code: str | None = None
    for value in normalized:
        if type(value) is not PaperRecommendationCycleReviewReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PaperRecommendationCycleReviewReasonCodeCount",
            )
        if previous_reason_code is not None and value.reason_code <= previous_reason_code:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        previous_reason_code = value.reason_code
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_decimal_hours(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_optional_status(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_status(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_token(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a canonical token")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperRecommendationCycleReviewConfig",
    "PaperRecommendationCycleReviewReasonCodeCount",
    "PaperRecommendationCycleReviewReport",
    "build_paper_recommendation_cycle_review_report",
)
