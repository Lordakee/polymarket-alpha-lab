"""Pure paper-only artifact index reducer for recommendation reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any


ARTIFACT_INDEX_STATUSES = ("pass", "watch", "blocked")
SAFETY_FLAGS = ("paper_only", "report_only", "readonly")
STATUS_ATTRS = (
    "final_status",
    "pipeline_status",
    "manifest_status",
    "health_status",
    "readiness_status",
    "consistency_status",
    "fee_schedule_status",
    "status",
)
COUNT_ATTRS = ("row_count", "stage_count", "artifact_count", "item_count")
NAME_ATTRS = ("artifact_name", "report_name", "name")

_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")
_BLOCKED_STATUS_MARKERS = (
    "blocked",
    "fail",
    "failure",
    "unhealthy",
    "invalid",
    "inconsistent",
    "error",
    "missing",
    "not_observed",
    "rejected",
    "unsafe",
)
_WATCH_STATUS_MARKERS = (
    "watch",
    "warn",
    "warning",
    "incomplete",
    "pending",
    "partial",
    "not_ready",
    "gap",
    "quality_flag",
    "thin",
    "stale",
    "unknown",
)
_PASS_STATUS_MARKERS = (
    "pass",
    "ready",
    "healthy",
    "complete",
    "observed",
    "ok",
    "valid",
    "consistent",
    "success",
)
_UNSAFE_FLAGS = {
    "auth",
    "authenticated",
    "cancel_order",
    "exchange_mutation",
    "live",
    "live_trading",
    "network",
    "network_mutation",
    "network_write",
    "order",
    "order_cancellation",
    "order_construction",
    "order_submission",
    "private_key",
    "signing",
    "submit_order",
    "trading_enabled",
    "wallet",
}
_UNSAFE_FLAG_PREFIXES = (
    "auth_",
    "exchange_",
    "live_",
    "network_",
    "order_",
    "private_key",
    "signing",
    "wallet_",
)


@dataclass(frozen=True)
class PaperRecommendationArtifactIndexRow:
    artifact_name: str
    config_version: str
    generated_at: datetime
    status: str
    item_count: int
    reason_codes: tuple[str, ...]
    flags: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_artifact_name("artifact_name", self.artifact_name)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_status("status", self.status)
        _require_nonnegative_int("item_count", self.item_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "flags", _normalize_row_flags(self.flags))


@dataclass(frozen=True)
class PaperRecommendationArtifactIndexReport:
    generated_at: datetime
    config_version: str
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    index_status: str
    rows: tuple[PaperRecommendationArtifactIndexRow, ...]
    flags: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_status("index_status", self.index_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "flags", _normalize_report_flags(self.flags))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_recommendation_artifact_index_report(
    *,
    generated_at: datetime,
    config_version: str,
    artifacts: list[object] | tuple[object, ...],
) -> PaperRecommendationArtifactIndexReport:
    """Index supplied report-like paper artifacts without side effects."""

    report_generated_at = _as_utc("generated_at", generated_at)
    _require_canonical_string("config_version", config_version)
    normalized_artifacts = _normalize_artifacts(artifacts)

    rows = tuple(
        sorted(
            (
                _build_row(
                    artifact,
                    generated_at=report_generated_at,
                    default_config_version=config_version,
                )
                for artifact in normalized_artifacts
            ),
            key=lambda row: row.artifact_name,
        ),
    )
    _reject_duplicate_artifact_names(rows)

    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")

    return PaperRecommendationArtifactIndexReport(
        generated_at=report_generated_at,
        config_version=config_version,
        row_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        index_status=_index_status(
            row_count=len(rows),
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
        rows=rows,
        flags=SAFETY_FLAGS,
    )


def _build_row(
    artifact: object,
    *,
    generated_at: datetime,
    default_config_version: str,
) -> PaperRecommendationArtifactIndexRow:
    _require_artifact_safety(artifact)
    row_generated_at = _artifact_generated_at(artifact, generated_at)
    if row_generated_at != generated_at:
        raise ValueError("artifact generated_at must match report generated_at")

    return PaperRecommendationArtifactIndexRow(
        artifact_name=_artifact_name(artifact),
        config_version=_artifact_config_version(artifact, default_config_version),
        generated_at=row_generated_at,
        status=_artifact_status(artifact),
        item_count=_artifact_item_count(artifact),
        reason_codes=_artifact_reason_codes(artifact),
        flags=_artifact_flags(artifact),
    )


def _normalize_artifacts(
    artifacts: list[object] | tuple[object, ...],
) -> tuple[object, ...]:
    if type(artifacts) not in (list, tuple):
        raise ValueError("artifacts must be a list or tuple")
    return tuple(artifacts)


def _artifact_name(artifact: object) -> str:
    for attr_name in NAME_ATTRS:
        value = getattr(artifact, attr_name, None)
        if value is not None:
            return _canonicalize_token("artifact_name", value)
    return _canonicalize_token("artifact_name", type(artifact).__name__)


def _artifact_config_version(
    artifact: object,
    default_config_version: str,
) -> str:
    value = getattr(artifact, "config_version", default_config_version)
    _require_canonical_string("config_version", value)
    return value


def _artifact_generated_at(
    artifact: object,
    default_generated_at: datetime,
) -> datetime:
    value = getattr(artifact, "generated_at", default_generated_at)
    if value is None:
        return default_generated_at
    return _as_utc("generated_at", value)


def _artifact_status(artifact: object) -> str:
    for attr_name in STATUS_ATTRS:
        value = getattr(artifact, attr_name, None)
        if value is not None:
            return _normalize_status(attr_name, value)
    return "watch"


def _artifact_item_count(artifact: object) -> int:
    for attr_name in COUNT_ATTRS:
        value = getattr(artifact, attr_name, None)
        if value is not None:
            _require_nonnegative_int(attr_name, value)
            return value
    return 0


def _artifact_reason_codes(artifact: object) -> tuple[str, ...]:
    if hasattr(artifact, "reason_codes"):
        return _normalize_reason_codes(getattr(artifact, "reason_codes"))
    if hasattr(artifact, "blocking_reason_names"):
        return _normalize_reason_codes(getattr(artifact, "blocking_reason_names"))
    return ()


def _artifact_flags(artifact: object) -> tuple[str, ...]:
    source_flags = ()
    if hasattr(artifact, "flags"):
        source_flags = _normalize_source_flags(getattr(artifact, "flags"))
    return _ordered_unique((*SAFETY_FLAGS, *source_flags))


def _normalize_status(field_name: str, value: Any) -> str:
    token = _canonicalize_token(field_name, value)
    if token in ARTIFACT_INDEX_STATUSES:
        return token
    if _contains_marker(token, _BLOCKED_STATUS_MARKERS):
        return "blocked"
    if _contains_marker(token, _WATCH_STATUS_MARKERS):
        return "watch"
    if _contains_marker(token, _PASS_STATUS_MARKERS):
        return "pass"
    return "watch"


def _contains_marker(token: str, markers: tuple[str, ...]) -> bool:
    return any(marker in token for marker in markers)


def _index_status(
    *,
    row_count: int,
    watch_count: int,
    blocked_count: int,
) -> str:
    if blocked_count > 0:
        return "blocked"
    if watch_count > 0 or row_count == 0:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[PaperRecommendationArtifactIndexRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reject_duplicate_artifact_names(
    rows: tuple[PaperRecommendationArtifactIndexRow, ...],
) -> None:
    names = tuple(row.artifact_name for row in rows)
    if len(set(names)) != len(names):
        raise ValueError("duplicate artifact_name values are not allowed")


def _validate_report_consistency(
    report: PaperRecommendationArtifactIndexReport,
) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if (
        report.pass_count
        + report.watch_count
        + report.blocked_count
        != report.row_count
    ):
        raise ValueError("counts must sum to row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.index_status != _index_status(
        row_count=report.row_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    ):
        raise ValueError("index_status must match row statuses")
    for row in report.rows:
        if row.generated_at != report.generated_at:
            raise ValueError("row generated_at must match report generated_at")


def _normalize_rows(
    rows: tuple[PaperRecommendationArtifactIndexRow, ...],
) -> tuple[PaperRecommendationArtifactIndexRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperRecommendationArtifactIndexRow:
            raise ValueError(
                "rows must contain PaperRecommendationArtifactIndexRow values",
            )
    row_names = tuple(row.artifact_name for row in normalized)
    if row_names != tuple(sorted(row_names)):
        raise ValueError("rows must be sorted by artifact_name")
    if len(set(row_names)) != len(row_names):
        raise ValueError("rows must not contain duplicate artifact_name values")
    return normalized


def _normalize_reason_codes(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    return tuple(sorted(_ordered_unique(_canonicalize_token("reason_codes", value) for value in normalized)))


def _normalize_source_flags(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise ValueError("flags must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("flags must be an iterable") from exc
    flags = tuple(_canonicalize_token("flags", value) for value in normalized)
    unsafe_flags = tuple(flag for flag in flags if _is_unsafe_flag(flag))
    if unsafe_flags:
        raise ValueError("unsafe flags are not allowed")
    return flags


def _normalize_row_flags(values: Any) -> tuple[str, ...]:
    flags = _normalize_source_flags(values)
    if flags[: len(SAFETY_FLAGS)] != SAFETY_FLAGS:
        raise ValueError("flags must start with paper safety flags")
    return _ordered_unique(flags)


def _normalize_report_flags(values: Any) -> tuple[str, ...]:
    flags = _normalize_source_flags(values)
    if flags != SAFETY_FLAGS:
        raise ValueError("flags must be paper safety flags")
    return flags


def _is_unsafe_flag(flag: str) -> bool:
    if flag in _UNSAFE_FLAGS:
        return True
    if flag.startswith("no_"):
        return False
    return any(flag.startswith(prefix) for prefix in _UNSAFE_FLAG_PREFIXES)


def _require_artifact_safety(artifact: object) -> None:
    for flag_name in SAFETY_FLAGS:
        if getattr(artifact, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a known artifact index status")
    if value not in ARTIFACT_INDEX_STATUSES:
        raise ValueError(f"{field_name} must be a known artifact index status")


def _require_canonical_artifact_name(field_name: str, value: object) -> None:
    if _canonicalize_token(field_name, value) != value:
        raise ValueError(f"{field_name} must be canonical")


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


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _canonicalize_token(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    canonical = _TOKEN_PATTERN.sub("_", value.strip().lower()).strip("_")
    if not canonical:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return canonical


def _ordered_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


__all__ = (
    "PaperRecommendationArtifactIndexReport",
    "PaperRecommendationArtifactIndexRow",
    "build_paper_recommendation_artifact_index_report",
)
