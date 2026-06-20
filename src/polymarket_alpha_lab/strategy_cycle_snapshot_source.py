"""Pure paper snapshot source for strategy-cycle reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)
from polymarket_alpha_lab.strategy_cycle_recommendation_artifact_source import (
    build_strategy_cycle_recommendation_artifacts,
)


SAFETY_FLAGS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class _StrategyCycleSnapshotArtifact:
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


def build_strategy_cycle_snapshot_source_report(
    cycle_report: object,
    iteration_started_at: datetime | None = None,
) -> PaperRecommendationCycleSnapshotReport:
    _require_cycle_report(cycle_report)
    _require_optional_datetime("iteration_started_at", iteration_started_at)

    generated_at = _as_utc(getattr(cycle_report, "generated_at"))
    config_version = getattr(cycle_report, "config_version")
    scan_market_count = _require_nonnegative_int(
        "scan_market_count",
        getattr(cycle_report, "scan_market_count"),
    )
    considered_count = _require_nonnegative_int(
        "considered_count",
        getattr(cycle_report, "considered_count"),
    )
    snapshot_ready_count = _require_nonnegative_int(
        "snapshot_ready_count",
        getattr(cycle_report, "snapshot_ready_count"),
    )
    _require_nonnegative_int(
        "cost_aware_report_count",
        getattr(cycle_report, "cost_aware_report_count"),
    )
    blocked_counts = _normalize_blocked_counts(getattr(cycle_report, "blocked_counts"))
    screening_report = getattr(cycle_report, "screening_report")
    _require_screening_report(screening_report)

    pipeline_report = build_paper_recommendation_pipeline_report(
        generated_at=generated_at,
        config_version=config_version,
        stages=_build_pipeline_stages(
            scan_market_count=scan_market_count,
            considered_count=considered_count,
            snapshot_ready_count=snapshot_ready_count,
            screening_report=screening_report,
        ),
    )
    artifact_index_report = build_paper_recommendation_artifact_index_report(
        generated_at=generated_at,
        config_version=config_version,
        artifacts=_build_artifacts(
            cycle_report=cycle_report,
            generated_at=generated_at,
            config_version=config_version,
            blocked_counts=blocked_counts,
            considered_count=considered_count,
            screening_report=screening_report,
        ),
    )
    return build_paper_recommendation_cycle_snapshot_report(
        generated_at=generated_at,
        config_version=config_version,
        pipeline_report=pipeline_report,
        artifact_index_report=artifact_index_report,
    )


def _build_pipeline_stages(
    *,
    scan_market_count: int,
    considered_count: int,
    snapshot_ready_count: int,
    screening_report: object | None,
) -> tuple[PaperRecommendationPipelineStage, ...]:
    screening_ready_count = _screening_ready_count(screening_report)
    return (
        PaperRecommendationPipelineStage(
            stage_name="market_scan",
            status=_scan_status(scan_market_count),
            message=f"{scan_market_count} markets scanned",
            input_count=0,
            output_count=scan_market_count,
        ),
        PaperRecommendationPipelineStage(
            stage_name="market_consideration",
            status=_consideration_status(scan_market_count, considered_count),
            message=f"{considered_count} markets considered",
            input_count=scan_market_count,
            output_count=considered_count,
        ),
        PaperRecommendationPipelineStage(
            stage_name="cost_aware_snapshot",
            status=_snapshot_status(considered_count, snapshot_ready_count),
            message=_snapshot_message(snapshot_ready_count, considered_count),
            input_count=considered_count,
            output_count=snapshot_ready_count,
        ),
        PaperRecommendationPipelineStage(
            stage_name="project_screening",
            status=_screening_status(screening_report, considered_count),
            message=_screening_message(screening_report, screening_ready_count),
            input_count=snapshot_ready_count,
            output_count=screening_ready_count,
        ),
    )


def _build_artifacts(
    *,
    cycle_report: object,
    generated_at: datetime,
    config_version: str,
    blocked_counts: tuple[tuple[str, int], ...],
    considered_count: int,
    screening_report: object | None,
) -> tuple[object, ...]:
    cost_aware_reports = getattr(cycle_report, "cost_aware_reports", ())
    if cost_aware_reports:
        return build_strategy_cycle_recommendation_artifacts(
            cycle_report,
            generated_at=generated_at,
        )

    artifacts = [
        _StrategyCycleSnapshotArtifact(
            artifact_name="strategy_cycle_blocked_counts",
            config_version=config_version,
            generated_at=generated_at,
            status=_blocked_counts_status(blocked_counts),
            item_count=sum(count for _status, count in blocked_counts),
            reason_codes=tuple(sorted(status for status, _count in blocked_counts)),
        ),
        _StrategyCycleSnapshotArtifact(
            artifact_name="strategy_cycle_screening_report",
            config_version=config_version,
            generated_at=generated_at,
            status=_screening_artifact_status(screening_report, considered_count),
            item_count=_screening_ready_count(screening_report),
            reason_codes=_screening_artifact_reason_codes(screening_report, considered_count),
        ),
    ]
    return tuple(artifacts)


def _screening_artifact_status(screening_report: object | None, considered_count: int) -> str:
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


def _scan_status(scan_market_count: int) -> str:
    return "pass" if scan_market_count > 0 else "watch"


def _consideration_status(scan_market_count: int, considered_count: int) -> str:
    if considered_count > 0:
        return "pass"
    return "watch" if scan_market_count == 0 else "watch"


def _snapshot_status(considered_count: int, snapshot_ready_count: int) -> str:
    if snapshot_ready_count > 0:
        return "pass"
    if considered_count > 0:
        return "blocked"
    return "watch"


def _snapshot_message(snapshot_ready_count: int, considered_count: int) -> str:
    if snapshot_ready_count > 0:
        return f"{snapshot_ready_count} snapshots ready"
    if considered_count > 0:
        return "cost-aware snapshot blocked"
    return "no markets considered"


def _screening_status(screening_report: object | None, considered_count: int) -> str:
    if screening_report is None:
        return "blocked" if considered_count > 0 else "watch"
    ready_count = _screening_ready_count(screening_report)
    if ready_count > 0:
        return "pass"
    if _screening_count(screening_report, "blocked_count") > 0:
        return "blocked"
    return "watch"


def _screening_message(screening_report: object | None, ready_count: int) -> str:
    if screening_report is None:
        return "screening report missing"
    if ready_count > 0:
        return f"{ready_count} screening candidates ready"
    if _screening_count(screening_report, "blocked_count") > 0:
        return "screening blocked"
    if _screening_count(screening_report, "watch_count") > 0:
        return "screening watch"
    if _screening_count(screening_report, "defer_count") > 0:
        return "screening defer"
    return "screening empty"


def _blocked_counts_status(blocked_counts: tuple[tuple[str, int], ...]) -> str:
    return "blocked" if sum(count for _status, count in blocked_counts) > 0 else "pass"


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
        _require_canonical_string("blocked_counts status", status)
        normalized.append((status, _require_nonnegative_int("blocked_counts count", count)))
    return tuple(sorted(normalized))


def _require_cycle_report(value: object) -> None:
    if type(value).__name__ != "PaperStrategyCycleReport":
        raise ValueError("cycle_report must be a PaperStrategyCycleReport")
    if type(value).__module__ != "polymarket_alpha_lab.strategy_cycle":
        raise ValueError("cycle_report must be a PaperStrategyCycleReport")
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("cycle_report must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("cycle_report must be report_only")


def _require_screening_report(value: object | None) -> None:
    if value is None:
        return
    if type(value).__name__ != "PaperProjectScreeningReport":
        raise ValueError("screening_report must be a PaperProjectScreeningReport or None")
    if type(value).__module__ != "polymarket_alpha_lab.project_screening":
        raise ValueError("screening_report must be a PaperProjectScreeningReport or None")
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("screening_report must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("screening_report must be report_only")


def _require_optional_datetime(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime or None")


def _require_nonnegative_int(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = ("build_strategy_cycle_snapshot_source_report",)
