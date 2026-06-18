"""Paper-only strategy recommendation history summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable

from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
)


__all__ = (
    "PaperStrategyRecommendationHistoryReport",
    "PaperStrategyRecommendationHistorySourceSummary",
    "build_paper_strategy_recommendation_history_report",
)


@dataclass(frozen=True)
class PaperStrategyRecommendationHistorySourceSummary:
    generated_at: datetime
    config_version: str
    candidate_count: int
    recommend_count: int
    watch_count: int
    reject_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "recommend_count",
            "watch_count",
            "reject_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if (
            self.recommend_count + self.watch_count + self.reject_count
            != self.candidate_count
        ):
            raise ValueError("action counts must sum to candidate_count")


@dataclass(frozen=True)
class PaperStrategyRecommendationHistoryReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    total_candidate_count: int
    total_recommend_count: int
    total_watch_count: int
    total_reject_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_config_version: str | None
    latest_candidate_count: int
    latest_recommend_count: int
    latest_watch_count: int
    latest_reject_count: int
    source_summaries: tuple[PaperStrategyRecommendationHistorySourceSummary, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc(self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc(self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.latest_config_version is not None:
            _require_canonical_string("latest_config_version", self.latest_config_version)
        for field_name in (
            "source_report_count",
            "total_candidate_count",
            "total_recommend_count",
            "total_watch_count",
            "total_reject_count",
            "latest_candidate_count",
            "latest_recommend_count",
            "latest_watch_count",
            "latest_reject_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_source_summaries(self.source_summaries),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_recommendation_history_report(
    recommendation_reports: Iterable[PaperStrategyCandidateRecommendationReport],
    *,
    config_version: str,
    generated_at: datetime,
) -> PaperStrategyRecommendationHistoryReport:
    """Reduce paper-only recommendation reports into a small readonly history."""

    _require_canonical_string("config_version", config_version)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    reports = _normalize_recommendation_reports(recommendation_reports)
    ordered_reports = tuple(
        sorted(
            reports,
            key=lambda report: (report.generated_at, report.config_version),
        ),
    )
    source_summaries = tuple(_summary_from_report(report) for report in ordered_reports)
    latest = source_summaries[-1] if source_summaries else None

    return PaperStrategyRecommendationHistoryReport(
        generated_at=generated_at,
        config_version=config_version,
        source_report_count=len(source_summaries),
        total_candidate_count=sum(
            summary.candidate_count for summary in source_summaries
        ),
        total_recommend_count=sum(
            summary.recommend_count for summary in source_summaries
        ),
        total_watch_count=sum(summary.watch_count for summary in source_summaries),
        total_reject_count=sum(summary.reject_count for summary in source_summaries),
        first_generated_at=source_summaries[0].generated_at
        if source_summaries
        else None,
        latest_generated_at=latest.generated_at if latest is not None else None,
        latest_config_version=latest.config_version if latest is not None else None,
        latest_candidate_count=latest.candidate_count if latest is not None else 0,
        latest_recommend_count=latest.recommend_count if latest is not None else 0,
        latest_watch_count=latest.watch_count if latest is not None else 0,
        latest_reject_count=latest.reject_count if latest is not None else 0,
        source_summaries=source_summaries,
    )


def _normalize_recommendation_reports(
    recommendation_reports: Iterable[PaperStrategyCandidateRecommendationReport],
) -> tuple[PaperStrategyCandidateRecommendationReport, ...]:
    if isinstance(recommendation_reports, (str, bytes)):
        raise ValueError(
            "recommendation_reports must be an iterable of "
            "PaperStrategyCandidateRecommendationReport values",
        )
    try:
        reports = tuple(recommendation_reports)
    except TypeError as exc:
        raise ValueError(
            "recommendation_reports must be an iterable of "
            "PaperStrategyCandidateRecommendationReport values",
        ) from exc
    for report in reports:
        if type(report) is not PaperStrategyCandidateRecommendationReport:
            raise ValueError(
                "recommendation_reports must contain "
                "PaperStrategyCandidateRecommendationReport values",
            )
        if report.paper_only is not True:
            raise ValueError("recommendation_reports must contain paper_only reports")
        if report.report_only is not True:
            raise ValueError("recommendation_reports must contain report_only reports")
        if report.readonly is not True:
            raise ValueError("recommendation_reports must contain readonly reports")
    return reports


def _summary_from_report(
    report: PaperStrategyCandidateRecommendationReport,
) -> PaperStrategyRecommendationHistorySourceSummary:
    return PaperStrategyRecommendationHistorySourceSummary(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        recommend_count=report.recommend_count,
        watch_count=report.watch_count,
        reject_count=report.reject_count,
    )


def _validate_report_consistency(
    report: PaperStrategyRecommendationHistoryReport,
) -> None:
    if report.source_report_count != len(report.source_summaries):
        raise ValueError("source_report_count must match source_summaries")
    if (
        report.total_recommend_count
        + report.total_watch_count
        + report.total_reject_count
        != report.total_candidate_count
    ):
        raise ValueError("total action counts must sum to total_candidate_count")
    if report.total_candidate_count != sum(
        summary.candidate_count for summary in report.source_summaries
    ):
        raise ValueError("total_candidate_count must match source_summaries")
    if report.total_recommend_count != sum(
        summary.recommend_count for summary in report.source_summaries
    ):
        raise ValueError("total_recommend_count must match source_summaries")
    if report.total_watch_count != sum(
        summary.watch_count for summary in report.source_summaries
    ):
        raise ValueError("total_watch_count must match source_summaries")
    if report.total_reject_count != sum(
        summary.reject_count for summary in report.source_summaries
    ):
        raise ValueError("total_reject_count must match source_summaries")
    if report.source_summaries != _order_source_summaries(report.source_summaries):
        raise ValueError("source_summaries must be ordered by generated_at")
    if report.source_report_count == 0:
        _validate_empty_report(report)
    else:
        _validate_nonempty_report(report)


def _validate_empty_report(report: PaperStrategyRecommendationHistoryReport) -> None:
    if report.total_candidate_count != 0:
        raise ValueError("total_candidate_count must be zero without reports")
    if report.first_generated_at is not None or report.latest_generated_at is not None:
        raise ValueError("generated_at bounds must be absent without reports")
    if report.latest_config_version is not None:
        raise ValueError("latest_config_version must be absent without reports")
    if (
        report.latest_candidate_count != 0
        or report.latest_recommend_count != 0
        or report.latest_watch_count != 0
        or report.latest_reject_count != 0
    ):
        raise ValueError("latest counts must be zero without reports")


def _validate_nonempty_report(report: PaperStrategyRecommendationHistoryReport) -> None:
    first = report.source_summaries[0]
    latest = report.source_summaries[-1]
    if report.first_generated_at != first.generated_at:
        raise ValueError("first_generated_at must match source_summaries")
    if report.latest_generated_at != latest.generated_at:
        raise ValueError("latest_generated_at must match source_summaries")
    if report.latest_config_version != latest.config_version:
        raise ValueError("latest_config_version must match source_summaries")
    if report.latest_candidate_count != latest.candidate_count:
        raise ValueError("latest_candidate_count must match source_summaries")
    if report.latest_recommend_count != latest.recommend_count:
        raise ValueError("latest_recommend_count must match source_summaries")
    if report.latest_watch_count != latest.watch_count:
        raise ValueError("latest_watch_count must match source_summaries")
    if report.latest_reject_count != latest.reject_count:
        raise ValueError("latest_reject_count must match source_summaries")


def _normalize_source_summaries(
    source_summaries: tuple[PaperStrategyRecommendationHistorySourceSummary, ...],
) -> tuple[PaperStrategyRecommendationHistorySourceSummary, ...]:
    if isinstance(source_summaries, (str, bytes)):
        raise ValueError("source_summaries must be an iterable")
    try:
        summaries = tuple(source_summaries)
    except TypeError as exc:
        raise ValueError("source_summaries must be an iterable") from exc
    for summary in summaries:
        if type(summary) is not PaperStrategyRecommendationHistorySourceSummary:
            raise ValueError(
                "source_summaries must contain "
                "PaperStrategyRecommendationHistorySourceSummary values",
            )
    return summaries


def _order_source_summaries(
    source_summaries: tuple[PaperStrategyRecommendationHistorySourceSummary, ...],
) -> tuple[PaperStrategyRecommendationHistorySourceSummary, ...]:
    return tuple(
        sorted(
            source_summaries,
            key=lambda summary: (summary.generated_at, summary.config_version),
        ),
    )


def _as_utc(value: Any) -> datetime:
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
