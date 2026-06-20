"""Pure strategy-cycle adapter for recommendation artifact indexing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


SAFETY_FLAGS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyCycleRecommendationArtifact:
    artifact_name: str
    config_version: str
    generated_at: datetime
    status: str
    item_count: int
    reason_codes: tuple[str, ...]
    flags: tuple[str, ...] = SAFETY_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("artifact_name", self.artifact_name)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_status("status", self.status)
        _require_nonnegative_int("item_count", self.item_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "flags",
            _normalize_string_tuple("flags", self.flags),
        )
        if self.flags != SAFETY_FLAGS:
            raise ValueError("flags must be paper safety flags")
        _require_safety_flags("artifact", self)


def build_strategy_cycle_recommendation_artifacts(
    cycle_report: object,
    *,
    generated_at: datetime | None = None,
) -> tuple[object, ...]:
    """Build report-like artifacts from a paper strategy-cycle report."""

    _require_cycle_report(cycle_report)
    report_generated_at = _generated_at(cycle_report, generated_at)
    config_version = _require_canonical_string(
        "config_version",
        getattr(cycle_report, "config_version"),
    )
    considered_count = _require_nonnegative_int(
        "considered_count",
        getattr(cycle_report, "considered_count"),
    )
    cost_aware_report_count = _require_nonnegative_int(
        "cost_aware_report_count",
        getattr(cycle_report, "cost_aware_report_count"),
    )
    blocked_counts = _normalize_blocked_counts(getattr(cycle_report, "blocked_counts"))
    screening_report = getattr(cycle_report, "screening_report")

    return tuple(
        sorted(
            (
                _blocked_counts_artifact(
                    generated_at=report_generated_at,
                    config_version=config_version,
                    blocked_counts=blocked_counts,
                ),
                _cost_aware_reports_artifact(
                    cycle_report,
                    generated_at=report_generated_at,
                    config_version=config_version,
                    expected_count=cost_aware_report_count,
                ),
                _screening_report_artifact(
                    generated_at=report_generated_at,
                    config_version=config_version,
                    considered_count=considered_count,
                    screening_report=screening_report,
                ),
            ),
            key=lambda artifact: artifact.artifact_name,
        ),
    )


def _blocked_counts_artifact(
    *,
    generated_at: datetime,
    config_version: str,
    blocked_counts: tuple[tuple[str, int], ...],
) -> StrategyCycleRecommendationArtifact:
    return StrategyCycleRecommendationArtifact(
        artifact_name="strategy_cycle_blocked_counts",
        config_version=config_version,
        generated_at=generated_at,
        status=(
            "blocked"
            if sum(count for _status, count in blocked_counts) > 0
            else "pass"
        ),
        item_count=sum(count for _status, count in blocked_counts),
        reason_codes=tuple(status for status, _count in blocked_counts),
    )


def _cost_aware_reports_artifact(
    cycle_report: object,
    *,
    generated_at: datetime,
    config_version: str,
    expected_count: int,
) -> StrategyCycleRecommendationArtifact:
    if "cost_aware_reports" not in vars(cycle_report):
        return StrategyCycleRecommendationArtifact(
            artifact_name="strategy_cycle_cost_aware_reports",
            config_version=config_version,
            generated_at=generated_at,
            status="watch",
            item_count=0,
            reason_codes=("cost_aware_reports_unavailable",),
        )

    reports = _normalize_cost_aware_reports(getattr(cycle_report, "cost_aware_reports"))
    if len(reports) != expected_count:
        return StrategyCycleRecommendationArtifact(
            artifact_name="strategy_cycle_cost_aware_reports",
            config_version=config_version,
            generated_at=generated_at,
            status="blocked",
            item_count=len(reports),
            reason_codes=("cost_aware_report_count_mismatch",),
        )

    return StrategyCycleRecommendationArtifact(
        artifact_name="strategy_cycle_cost_aware_reports",
        config_version=config_version,
        generated_at=generated_at,
        status=_cost_aware_reports_status(reports),
        item_count=len(reports),
        reason_codes=_cost_aware_reports_reason_codes(reports),
    )


def _screening_report_artifact(
    *,
    generated_at: datetime,
    config_version: str,
    considered_count: int,
    screening_report: object | None,
) -> StrategyCycleRecommendationArtifact:
    return StrategyCycleRecommendationArtifact(
        artifact_name="strategy_cycle_screening_report",
        config_version=config_version,
        generated_at=generated_at,
        status=_screening_artifact_status(screening_report, considered_count),
        item_count=_screening_ready_count(screening_report),
        reason_codes=_screening_artifact_reason_codes(screening_report, considered_count),
    )


def _screening_artifact_status(
    screening_report: object | None,
    considered_count: int,
) -> str:
    if screening_report is None:
        return "blocked" if considered_count > 0 else "watch"

    ready_count = _screening_ready_count(screening_report)
    if ready_count > 0:
        return "pass"
    if _screening_count(screening_report, "blocked_count") > 0:
        return "blocked"
    return "watch"


def _screening_artifact_reason_codes(
    screening_report: object | None,
    considered_count: int,
) -> tuple[str, ...]:
    if screening_report is None:
        return ("missing_screening_report",)

    ready_count = _screening_ready_count(screening_report)
    if ready_count > 0:
        return ("screening_ready_candidates",)
    if _screening_count(screening_report, "blocked_count") > 0:
        return ("screening_blocked_candidates",)
    if _screening_count(screening_report, "watch_count") > 0:
        return ("screening_watch_candidates",)
    if _screening_count(screening_report, "defer_count") > 0:
        return ("screening_defer_candidates",)
    if considered_count > 0:
        return ("screening_no_ready_candidates",)
    return ()


def _screening_ready_count(screening_report: object | None) -> int:
    if screening_report is None:
        return 0
    return _screening_count(screening_report, "ready_count")


def _screening_count(screening_report: object, field_name: str) -> int:
    value = getattr(screening_report, field_name)
    return _require_nonnegative_int(field_name, value)


def _cost_aware_reports_status(reports: tuple[object, ...]) -> str:
    if not reports:
        return "watch"
    statuses = tuple(_cost_aware_report_status(report) for report in reports)
    if any(status in ("blocked_by_inputs", "blocked_by_risk") for status in statuses):
        return "blocked"
    if all(status == "paper_review_ready" for status in statuses):
        return "pass"
    return "watch"


def _cost_aware_reports_reason_codes(reports: tuple[object, ...]) -> tuple[str, ...]:
    if not reports:
        return ("no_cost_aware_reports",)
    return tuple(
        sorted(
            dict.fromkeys(
                f"cost_aware_{_cost_aware_report_status(report)}" for report in reports
            ),
        ),
    )


def _normalize_cost_aware_reports(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("cost_aware_reports must be an iterable")
    try:
        reports = tuple(value)
    except TypeError as exc:
        raise ValueError("cost_aware_reports must be an iterable") from exc
    for report in reports:
        _require_safety_flags("cost_aware_reports", report)
        _require_canonical_string(
            "cost_aware_reports config_version",
            getattr(report, "config_version"),
        )
        _cost_aware_report_status(report)
    return reports


def _cost_aware_report_status(report: object) -> str:
    status = getattr(report, "status")
    _require_canonical_string("cost_aware_reports status", status)
    return status


def _normalize_blocked_counts(
    value: object,
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("blocked_counts must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("blocked_counts must be an iterable") from exc
    normalized: list[tuple[str, int]] = []
    for item in items:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("blocked_counts entries must be (status, count) pairs")
        status, count = item
        normalized.append(
            (
                _require_canonical_string("blocked_counts status", status),
                _require_nonnegative_int("blocked_counts count", count),
            ),
        )
    return tuple(sorted(normalized))


def _require_cycle_report(value: object) -> None:
    required_attrs = (
        "generated_at",
        "config_version",
        "considered_count",
        "cost_aware_report_count",
        "blocked_counts",
        "screening_report",
    )
    for attr_name in required_attrs:
        if not hasattr(value, attr_name):
            raise ValueError("cycle_report must expose strategy cycle report fields")
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("cycle_report must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("cycle_report must be report_only")


def _require_safety_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", True) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _generated_at(cycle_report: object, generated_at: datetime | None) -> datetime:
    report_generated_at = _as_utc(getattr(cycle_report, "generated_at"))
    if generated_at is None:
        return report_generated_at
    override = _as_utc(generated_at)
    if override != report_generated_at:
        raise ValueError("generated_at must match cycle_report generated_at")
    return override


def _require_status(field_name: str, value: object) -> None:
    if value not in ("pass", "watch", "blocked"):
        raise ValueError(f"{field_name} must be a known artifact status")


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    return tuple(_require_canonical_string(field_name, item) for item in items)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_nonnegative_int(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "StrategyCycleRecommendationArtifact",
    "build_strategy_cycle_recommendation_artifacts",
)
