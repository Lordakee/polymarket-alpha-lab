"""Pure paper-only cycle snapshot reducer for recommendation reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    PaperRecommendationArtifactIndexReport,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineReport,
)


STATUSES = ("pass", "watch", "blocked")
_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class PaperRecommendationCycleSnapshotReport:
    generated_at: datetime
    config_version: str
    pipeline_report: PaperRecommendationPipelineReport
    artifact_index_report: PaperRecommendationArtifactIndexReport
    final_status: str
    stage_count: int
    artifact_count: int
    blocked_artifact_count: int
    watch_artifact_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nested_report_types(self)
        _require_safety_flags("pipeline report", self.pipeline_report)
        _require_safety_flags("artifact index report", self.artifact_index_report)
        _require_safety_flags("cycle snapshot", self)
        _require_generated_at_consistency(self)
        for field_name in (
            "stage_count",
            "artifact_count",
            "blocked_artifact_count",
            "watch_artifact_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_status("final_status", self.final_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_summary_consistency(self)


def build_paper_recommendation_cycle_snapshot_report(
    *,
    generated_at: datetime,
    config_version: str,
    pipeline_report: PaperRecommendationPipelineReport,
    artifact_index_report: PaperRecommendationArtifactIndexReport,
) -> PaperRecommendationCycleSnapshotReport:
    """Build a supplied-input recommendation cycle snapshot without side effects."""

    generated_at = _as_utc("generated_at", generated_at)
    _require_canonical_string("config_version", config_version)
    if type(pipeline_report) is not PaperRecommendationPipelineReport:
        raise ValueError("pipeline_report must be PaperRecommendationPipelineReport")
    if type(artifact_index_report) is not PaperRecommendationArtifactIndexReport:
        raise ValueError(
            "artifact_index_report must be PaperRecommendationArtifactIndexReport",
        )
    _require_safety_flags("pipeline report", pipeline_report)
    _require_safety_flags("artifact index report", artifact_index_report)

    return PaperRecommendationCycleSnapshotReport(
        generated_at=generated_at,
        config_version=config_version,
        pipeline_report=pipeline_report,
        artifact_index_report=artifact_index_report,
        final_status=_final_status(
            pipeline_status=pipeline_report.final_status,
            artifact_index_status=artifact_index_report.index_status,
        ),
        stage_count=pipeline_report.stage_count,
        artifact_count=artifact_index_report.row_count,
        blocked_artifact_count=artifact_index_report.blocked_count,
        watch_artifact_count=artifact_index_report.watch_count,
        reason_codes=_snapshot_reason_codes(
            pipeline_report=pipeline_report,
            artifact_index_report=artifact_index_report,
        ),
    )


def _require_nested_report_types(report: PaperRecommendationCycleSnapshotReport) -> None:
    if type(report.pipeline_report) is not PaperRecommendationPipelineReport:
        raise ValueError("pipeline_report must be PaperRecommendationPipelineReport")
    if type(report.artifact_index_report) is not PaperRecommendationArtifactIndexReport:
        raise ValueError(
            "artifact_index_report must be PaperRecommendationArtifactIndexReport",
        )


def _require_generated_at_consistency(
    report: PaperRecommendationCycleSnapshotReport,
) -> None:
    if report.pipeline_report.generated_at != report.generated_at:
        raise ValueError("pipeline_report generated_at must match generated_at")
    if report.artifact_index_report.generated_at != report.generated_at:
        raise ValueError("artifact_index_report generated_at must match generated_at")


def _validate_summary_consistency(
    report: PaperRecommendationCycleSnapshotReport,
) -> None:
    if report.stage_count != report.pipeline_report.stage_count:
        raise ValueError("stage_count must match pipeline_report")
    if report.artifact_count != report.artifact_index_report.row_count:
        raise ValueError("artifact_count must match artifact_index_report")
    if report.blocked_artifact_count != report.artifact_index_report.blocked_count:
        raise ValueError("blocked_artifact_count must match artifact_index_report")
    if report.watch_artifact_count != report.artifact_index_report.watch_count:
        raise ValueError("watch_artifact_count must match artifact_index_report")
    if report.final_status != _final_status(
        pipeline_status=report.pipeline_report.final_status,
        artifact_index_status=report.artifact_index_report.index_status,
    ):
        raise ValueError("final_status must match nested report statuses")
    if report.reason_codes != _snapshot_reason_codes(
        pipeline_report=report.pipeline_report,
        artifact_index_report=report.artifact_index_report,
    ):
        raise ValueError("reason_codes must match nested reports")


def _final_status(*, pipeline_status: str, artifact_index_status: str) -> str:
    if pipeline_status == "blocked" or artifact_index_status == "blocked":
        return "blocked"
    if pipeline_status == "watch" or artifact_index_status == "watch":
        return "watch"
    return "pass"


def _snapshot_reason_codes(
    *,
    pipeline_report: PaperRecommendationPipelineReport,
    artifact_index_report: PaperRecommendationArtifactIndexReport,
) -> tuple[str, ...]:
    row_reason_codes = tuple(
        sorted(
            {
                reason_code
                for row in artifact_index_report.rows
                for reason_code in row.reason_codes
            },
        ),
    )
    return (
        f"pipeline_final_status_{pipeline_report.final_status}",
        f"artifact_index_{artifact_index_report.index_status}",
        *row_reason_codes,
    )


def _normalize_reason_codes(values: Any) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    return tuple(_require_reason_code(value) for value in normalized)


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if _TOKEN_PATTERN.sub("_", value.strip().lower()).strip("_") != value:
        raise ValueError("reason_codes must contain canonical tokens")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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


def _require_safety_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperRecommendationCycleSnapshotReport",
    "build_paper_recommendation_cycle_snapshot_report",
)
