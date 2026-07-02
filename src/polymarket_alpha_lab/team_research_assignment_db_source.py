"""Pure DB-source composer for team research assignment reports."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
)
from polymarket_alpha_lab.team_market_router import (
    TeamMarketRouteReport,
    TeamMarketRouteRow,
)
from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReport,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_research_assignment import (
    TeamResearchAssignmentConfig,
    TeamResearchAssignmentReport,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


__all__ = (
    "load_team_research_assignment_report",
    "merge_team_market_route_reports",
)


def load_team_research_assignment_report(
    *,
    queue_loader: Callable[..., tuple[object, ...]],
    route_loader: Callable[..., tuple[object, ...]],
    memory_loader: Callable[..., object],
    assignment_builder: Callable[..., object],
    assignment_config: object,
    generated_at: object,
    team_ids: tuple[str, ...],
    queue_source_config_version: str | None = None,
    queue_limit: int = 1,
    route_limit: int | None = None,
    memory_config_version: str | None = None,
    memory_limit: int | None = None,
) -> object:
    _require_callable("queue_loader", queue_loader)
    _require_callable("route_loader", route_loader)
    _require_callable("memory_loader", memory_loader)
    _require_callable("assignment_builder", assignment_builder)
    if type(assignment_config) is not TeamResearchAssignmentConfig:
        raise ValueError("assignment_config must be a TeamResearchAssignmentConfig")
    require_paper_only_flags("assignment_config", assignment_config)
    normalized_team_ids = _normalize_team_ids(team_ids)
    normalized_queue_source_config_version = _normalize_optional_config_version(
        "queue_source_config_version",
        queue_source_config_version,
    )
    normalized_queue_limit = _require_positive_int("queue_limit", queue_limit)
    normalized_route_limit = _normalize_optional_positive_int(
        "route_limit",
        route_limit,
    )
    normalized_memory_config_version = _normalize_optional_config_version(
        "memory_config_version",
        memory_config_version,
    )
    normalized_memory_limit = _normalize_optional_positive_int(
        "memory_limit",
        memory_limit,
    )

    queue_reports = queue_loader(
        source_config_version=normalized_queue_source_config_version,
        action_status="research_ready",
        research_status="ready",
        limit=normalized_queue_limit,
    )
    queue_report = _only_queue_report(queue_reports)

    route_reports = route_loader(limit=normalized_route_limit)
    merged_route_report = merge_team_market_route_reports(route_reports)

    memory_report = memory_loader(
        team_ids=normalized_team_ids,
        config_version=normalized_memory_config_version,
        limit=normalized_memory_limit,
    )
    if type(memory_report) is not TeamMemoryReadinessDigestReport:
        raise ValueError("memory_loader must return a TeamMemoryReadinessDigestReport")
    require_paper_only_flags("memory_report", memory_report)

    assignment_report = assignment_builder(
        queue_report,
        merged_route_report,
        memory_report,
        config=assignment_config,
        generated_at=generated_at,
    )
    if type(assignment_report) is not TeamResearchAssignmentReport:
        raise ValueError("assignment_builder must return a TeamResearchAssignmentReport")
    require_paper_only_flags("assignment_report", assignment_report)
    return assignment_report


def merge_team_market_route_reports(
    route_reports: tuple[object, ...],
) -> TeamMarketRouteReport:
    reports = _normalize_route_reports(route_reports)
    if not reports:
        raise ValueError("route_reports must contain at least one TeamMarketRouteReport")

    rows: list[TeamMarketRouteRow] = []
    seen_market_slugs: set[str] = set()
    for report in reports:
        if report.route_count != 1 or len(report.rows) != 1:
            raise ValueError(
                "route readback reports must be one-row TeamMarketRouteReport values",
            )
        row = report.rows[0]
        if row.market_slug in seen_market_slugs:
            raise ValueError("route reports must have unique market_slug values")
        seen_market_slugs.add(row.market_slug)
        rows.append(row)

    first_report = reports[0]
    return TeamMarketRouteReport(
        generated_at=first_report.generated_at,
        config_version=first_report.config_version,
        route_count=len(rows),
        rows=tuple(rows),
    )


def _require_callable(name: str, value: object) -> None:
    if not callable(value):
        raise ValueError(f"{name} must be callable")


def _require_positive_int(name: str, value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive int")
    return value


def _normalize_optional_positive_int(name: str, value: object) -> int | None:
    if value is None:
        return None
    return _require_positive_int(name, value)


def _normalize_optional_config_version(name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be None or a canonical non-empty string")
    return value


def _only_queue_report(
    queue_reports: Any,
) -> PaperStrategyCandidateResearchQueueReport:
    if type(queue_reports) not in (list, tuple):
        raise ValueError("queue_loader must return a list or tuple")
    reports = tuple(queue_reports)
    if len(reports) != 1:
        raise ValueError("queue_loader must return exactly one queue report")
    report = reports[0]
    if type(report) is not PaperStrategyCandidateResearchQueueReport:
        raise ValueError(
            "queue_loader must return PaperStrategyCandidateResearchQueueReport",
        )
    require_paper_only_flags("queue_report", report)
    return report


def _normalize_route_reports(
    route_reports: Any,
) -> tuple[TeamMarketRouteReport, ...]:
    if type(route_reports) not in (list, tuple):
        raise ValueError("route_reports must be a list or tuple")
    reports = tuple(route_reports)
    for report in reports:
        if type(report) is not TeamMarketRouteReport:
            raise ValueError("route_reports must contain TeamMarketRouteReport values")
        require_paper_only_flags("route_report", report)
    return reports


def _normalize_team_ids(team_ids: object) -> tuple[str, ...]:
    if type(team_ids) is not tuple:
        raise ValueError("team_ids must be a tuple")
    if not team_ids:
        raise ValueError("team_ids must contain at least one team")
    normalized: list[str] = []
    seen: set[str] = set()
    for team_id in team_ids:
        if type(team_id) is not str:
            raise ValueError("team_ids must contain strings")
        normalized_team_id = require_team_id("team_ids", team_id)
        if normalized_team_id in seen:
            raise ValueError("duplicate team_ids are not allowed")
        seen.add(normalized_team_id)
        normalized.append(normalized_team_id)
    return tuple(normalized)
