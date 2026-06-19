"""Pure paper-only bundle reducer for supplied recommendation cycle artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime


__all__ = (
    "PaperRecommendationCycleBundleReport",
    "build_paper_recommendation_cycle_bundle_report",
)


FINAL_STATUSES = ("pass", "watch", "blocked")
BLOCKING_STATUSES = ("blocked", "fail", "failed", "unhealthy")
WATCH_STATUSES = ("watch", "incomplete")
PASS_STATUSES = ("pass", "ready", "healthy", "complete")
STATUS_FIELDS = ("final_status", "primary_status", "health_status", "status", "readiness_status")


@dataclass(frozen=True)
class PaperRecommendationCycleBundleReport:
    generated_at: datetime
    config_version: str
    artifact_count: int
    ready_artifact_count: int
    blocked_artifact_count: int
    final_status: str
    artifact_names: tuple[str, ...]
    artifacts: tuple[object, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "artifact_count",
            "ready_artifact_count",
            "blocked_artifact_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_final_status("final_status", self.final_status)
        object.__setattr__(
            self,
            "artifact_names",
            _normalize_artifact_names(self.artifact_names),
        )
        object.__setattr__(self, "artifacts", _normalize_artifacts(self.artifacts))
        _validate_report_consistency(self)
        _require_hard_flags("cycle bundle report", self)


def build_paper_recommendation_cycle_bundle_report(
    *,
    generated_at: datetime,
    config_version: str,
    artifacts: Iterable[object],
) -> PaperRecommendationCycleBundleReport:
    """Join already-built readonly paper reports into one immutable cycle artifact."""

    generated_at = _as_utc(generated_at)
    normalized_artifacts = _normalize_artifacts(artifacts)
    artifact_names = tuple(_artifact_name(artifact) for artifact in normalized_artifacts)
    _require_unique_artifact_names(artifact_names)
    for artifact, artifact_name in zip(normalized_artifacts, artifact_names, strict=True):
        _require_artifact_generated_at(generated_at, artifact_name, artifact)

    artifact_statuses = tuple(_artifact_status(artifact) for artifact in normalized_artifacts)
    return PaperRecommendationCycleBundleReport(
        generated_at=generated_at,
        config_version=config_version,
        artifact_count=len(normalized_artifacts),
        ready_artifact_count=sum(
            1 for status in artifact_statuses if status in PASS_STATUSES
        ),
        blocked_artifact_count=sum(
            1 for status in artifact_statuses if status in BLOCKING_STATUSES
        ),
        final_status=_final_status(artifact_statuses),
        artifact_names=artifact_names,
        artifacts=normalized_artifacts,
    )


def _validate_report_consistency(report: PaperRecommendationCycleBundleReport) -> None:
    if report.artifact_count != len(report.artifacts):
        raise ValueError("artifact_count must match artifacts")
    if report.artifact_count != len(report.artifact_names):
        raise ValueError("artifact_count must match artifact_names")
    _require_unique_artifact_names(report.artifact_names)
    expected_artifact_names = tuple(_artifact_name(artifact) for artifact in report.artifacts)
    if report.artifact_names != expected_artifact_names:
        raise ValueError("artifact_names must match artifacts")
    for artifact, artifact_name in zip(report.artifacts, report.artifact_names, strict=True):
        _require_artifact_generated_at(report.generated_at, artifact_name, artifact)
    statuses = tuple(_artifact_status(artifact) for artifact in report.artifacts)
    if report.ready_artifact_count != sum(1 for status in statuses if status in PASS_STATUSES):
        raise ValueError("ready_artifact_count must match artifacts")
    if report.blocked_artifact_count != sum(
        1 for status in statuses if status in BLOCKING_STATUSES
    ):
        raise ValueError("blocked_artifact_count must match artifacts")
    if report.final_status != _final_status(statuses):
        raise ValueError("final_status must match artifacts")


def _normalize_artifacts(value: Iterable[object]) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("artifacts must be an iterable")
    try:
        artifacts = tuple(value)
    except TypeError as exc:
        raise ValueError("artifacts must be an iterable") from exc
    for artifact in artifacts:
        artifact_name = _artifact_name(artifact)
        _require_hard_flags(f"artifact {artifact_name}", artifact)
    return artifacts


def _normalize_artifact_names(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("artifact_names must be an iterable of strings")
    try:
        names = tuple(value)
    except TypeError as exc:
        raise ValueError("artifact_names must be an iterable of strings") from exc
    for name in names:
        _require_canonical_string("artifact name", name)
    _require_unique_artifact_names(names)
    return names


def _artifact_name(artifact: object) -> str:
    if hasattr(artifact, "name"):
        name = getattr(artifact, "name")
        _require_canonical_string("artifact name", name)
        return name
    name = artifact.__class__.__name__
    _require_canonical_string("artifact name", name)
    return name


def _require_unique_artifact_names(artifact_names: tuple[str, ...]) -> None:
    if len(set(artifact_names)) != len(artifact_names):
        raise ValueError("artifact names must be unique")


def _artifact_status(artifact: object) -> str:
    statuses: list[str] = []
    for field_name in STATUS_FIELDS:
        if hasattr(artifact, field_name):
            value = getattr(artifact, field_name)
            if type(value) is str:
                normalized = value.lower()
                if (
                    normalized in BLOCKING_STATUSES
                    or normalized in WATCH_STATUSES
                    or normalized in PASS_STATUSES
                ):
                    statuses.append(normalized)
    if any(status in BLOCKING_STATUSES for status in statuses):
        return "blocked"
    if any(status in WATCH_STATUSES for status in statuses):
        return "watch"
    if any(status in PASS_STATUSES for status in statuses):
        return "pass"
    return "pass"


def _final_status(statuses: tuple[str, ...]) -> str:
    if any(status in BLOCKING_STATUSES for status in statuses):
        return "blocked"
    if any(status in WATCH_STATUSES for status in statuses):
        return "watch"
    return "pass"


def _require_artifact_generated_at(
    expected_generated_at: datetime,
    artifact_name: str,
    artifact: object,
) -> None:
    if not hasattr(artifact, "generated_at"):
        return
    generated_at = _as_utc(getattr(artifact, "generated_at"))
    if generated_at != expected_generated_at:
        raise ValueError(f"artifact {artifact_name} generated_at must match bundle")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


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


def _require_final_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FINAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
