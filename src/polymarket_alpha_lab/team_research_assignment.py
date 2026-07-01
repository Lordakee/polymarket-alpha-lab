"""Pure paper-only team research assignment reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)
from polymarket_alpha_lab.team_market_router import (
    TeamMarketRouteReport,
    TeamMarketRouteRow,
)
from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReport,
    TeamMemoryReadinessDigestSourceStatus,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_TEAM_RESEARCH_ASSIGNMENT_CONFIG_VERSION = "team-research-assignment-v0"
CONFIDENCE_QUANT = Decimal("0.000001")
ZERO_CONFIDENCE = Decimal("0.000000")

NEXT_STEPS = {
    "ready": "assign_team_research_work",
    "watch": "review_team_research_assignments",
    "blocked": "block_team_research_assignment",
}
MEMORY_POLICY_BY_STATUS = {
    "pass": "allow",
    "watch": "throttle",
    "blocked": "block",
}

ASSIGNMENT_STATUSES = ("assigned", "watch", "blocked")
REPORT_STATUSES = tuple(NEXT_STEPS)
MEMORY_STATUSES = ("pass", "watch", "blocked", "missing")
MEMORY_POLICIES = ("allow", "throttle", "block")
QUEUE_RESEARCH_STATUSES = ("ready", "watch", "blocked")

ASSIGNED_REASON_CODE = "team_research_assignment_assigned"
QUEUE_WATCH_REASON_CODE = "source_queue_research_status_watch"
QUEUE_BLOCKED_REASON_CODE = "source_queue_research_status_blocked"
MISSING_ROUTE_REASON_CODE = "missing_team_market_route"
MISSING_MEMORY_REASON_CODE = "missing_team_memory_readiness"
MEMORY_WATCH_REASON_CODE = "team_memory_readiness_watch"
MEMORY_BLOCKED_REASON_CODE = "team_memory_readiness_blocked"
EMPTY_QUEUE_REASON_CODE = "team_research_assignment_empty_queue"
READY_REPORT_REASON_CODE = "team_research_assignment_ready"
WATCH_REPORT_REASON_CODE = "team_research_assignment_watch"
BLOCKED_REPORT_REASON_CODE = "team_research_assignment_blocked"

UNASSIGNED_TEAM_ID = "unassigned"
UNROUTED_CATEGORY_ID = "unrouted"


@dataclass(frozen=True)
class TeamResearchAssignmentConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_ASSIGNMENT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamResearchAssignmentConfig", self)


@dataclass(frozen=True)
class TeamResearchAssignmentRow:
    research_rank: int
    market_slug: str
    question: str
    selected_side: str
    scoring_side: str
    team_id: str
    category_id: str
    routing_confidence: Decimal
    secondary_team_ids: tuple[str, ...]
    queue_research_status: str
    queue_research_bucket: str
    queue_readiness_status: str
    memory_readiness_status: str
    memory_use_policy: str
    assignment_status: str
    assignment_reason_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("research_rank", self.research_rank)
        for field_name in (
            "market_slug",
            "question",
            "selected_side",
            "scoring_side",
            "team_id",
            "category_id",
            "queue_research_bucket",
            "queue_readiness_status",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "routing_confidence",
            _quantize_confidence(self.routing_confidence),
        )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_string_tuple(
                "secondary_team_ids",
                self.secondary_team_ids,
                allow_empty=True,
            ),
        )
        _require_member(
            "queue_research_status",
            self.queue_research_status,
            QUEUE_RESEARCH_STATUSES,
        )
        _require_member(
            "memory_readiness_status",
            self.memory_readiness_status,
            MEMORY_STATUSES,
        )
        _require_member("memory_use_policy", self.memory_use_policy, MEMORY_POLICIES)
        _require_member("assignment_status", self.assignment_status, ASSIGNMENT_STATUSES)
        object.__setattr__(
            self,
            "assignment_reason_codes",
            _normalize_string_tuple(
                "assignment_reason_codes",
                self.assignment_reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_string_tuple(
                "evidence_gap_codes",
                self.evidence_gap_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_string_tuple(
                "source_reason_codes",
                self.source_reason_codes,
                allow_empty=True,
            ),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("TeamResearchAssignmentRow", self)


@dataclass(frozen=True)
class TeamResearchAssignmentTeamSummary:
    team_id: str
    assignment_count: int
    assigned_count: int
    watch_count: int
    blocked_count: int
    memory_readiness_status: str
    memory_use_policy: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        for field_name in (
            "assignment_count",
            "assigned_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_member(
            "memory_readiness_status",
            self.memory_readiness_status,
            MEMORY_STATUSES,
        )
        _require_member("memory_use_policy", self.memory_use_policy, MEMORY_POLICIES)
        if (
            self.assigned_count + self.watch_count + self.blocked_count
            != self.assignment_count
        ):
            raise ValueError("team summary counts must match assignment_count")
        require_paper_only_flags("TeamResearchAssignmentTeamSummary", self)


@dataclass(frozen=True)
class TeamResearchAssignmentReport:
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_route_config_version: str
    source_memory_config_version: str
    assignment_status: str
    recommended_next_step: str
    assignment_count: int
    assigned_count: int
    watch_count: int
    blocked_count: int
    team_summaries: tuple[TeamResearchAssignmentTeamSummary, ...]
    rows: tuple[TeamResearchAssignmentRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "config_version",
            "source_queue_config_version",
            "source_route_config_version",
            "source_memory_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("assignment_status", self.assignment_status, REPORT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "assignment_count",
            "assigned_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "team_summaries",
            _normalize_team_summaries(self.team_summaries),
        )
        object.__setattr__(self, "rows", _normalize_assignment_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("TeamResearchAssignmentReport", self)


def build_team_research_assignment_report(
    queue_report: PaperStrategyCandidateResearchQueueReport,
    route_report: TeamMarketRouteReport,
    memory_readiness_report: TeamMemoryReadinessDigestReport,
    *,
    config: TeamResearchAssignmentConfig,
    generated_at: datetime,
) -> TeamResearchAssignmentReport:
    if type(queue_report) is not PaperStrategyCandidateResearchQueueReport:
        raise ValueError("queue_report must be a PaperStrategyCandidateResearchQueueReport")
    if type(route_report) is not TeamMarketRouteReport:
        raise ValueError("route_report must be a TeamMarketRouteReport")
    if type(memory_readiness_report) is not TeamMemoryReadinessDigestReport:
        raise ValueError(
            "memory_readiness_report must be a TeamMemoryReadinessDigestReport",
        )
    if type(config) is not TeamResearchAssignmentConfig:
        raise ValueError("config must be a TeamResearchAssignmentConfig")
    require_paper_only_flags("queue_report", queue_report)
    require_paper_only_flags("route_report", route_report)
    require_paper_only_flags("memory_readiness_report", memory_readiness_report)
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)

    queue_rows = _normalize_queue_rows(queue_report.rows)
    route_rows_by_slug = _route_rows_by_market_slug(route_report.rows)
    memory_statuses_by_team_id = _memory_statuses_by_team_id(
        memory_readiness_report.source_statuses,
    )
    rows = tuple(
        _assignment_row(
            queue_row,
            route_row=route_rows_by_slug.get(queue_row.market_slug),
            memory_statuses_by_team_id=memory_statuses_by_team_id,
        )
        for queue_row in queue_rows
    )
    assignment_status = _report_assignment_status(rows)

    return TeamResearchAssignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_queue_config_version=queue_report.config_version,
        source_route_config_version=route_report.config_version,
        source_memory_config_version=memory_readiness_report.config_version,
        assignment_status=assignment_status,
        recommended_next_step=NEXT_STEPS[assignment_status],
        assignment_count=len(rows),
        assigned_count=_assignment_status_count(rows, "assigned"),
        watch_count=_assignment_status_count(rows, "watch"),
        blocked_count=_assignment_status_count(rows, "blocked"),
        team_summaries=_team_summaries(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows, assignment_status),
    )


def _assignment_row(
    queue_row: PaperStrategyCandidateResearchQueueRow,
    *,
    route_row: TeamMarketRouteRow | None,
    memory_statuses_by_team_id: dict[str, TeamMemoryReadinessDigestSourceStatus],
) -> TeamResearchAssignmentRow:
    if route_row is None:
        memory_readiness_status = "missing"
        memory_use_policy = "block"
        assignment_status = "blocked"
        assignment_reason_codes = _unique_string_tuple(
            (
                MISSING_ROUTE_REASON_CODE,
                *_queue_status_reason_codes(queue_row.research_status),
            ),
        )
        return TeamResearchAssignmentRow(
            research_rank=queue_row.research_rank,
            market_slug=queue_row.market_slug,
            question=queue_row.question,
            selected_side=queue_row.selected_side,
            scoring_side=queue_row.scoring_side,
            team_id=UNASSIGNED_TEAM_ID,
            category_id=UNROUTED_CATEGORY_ID,
            routing_confidence=ZERO_CONFIDENCE,
            secondary_team_ids=(),
            queue_research_status=queue_row.research_status,
            queue_research_bucket=queue_row.research_bucket,
            queue_readiness_status=queue_row.readiness_status,
            memory_readiness_status=memory_readiness_status,
            memory_use_policy=memory_use_policy,
            assignment_status=assignment_status,
            assignment_reason_codes=assignment_reason_codes,
            evidence_gap_codes=queue_row.evidence_gap_codes,
            source_reason_codes=queue_row.reason_codes,
        )

    team_id = route_row.routing_corrected_team_id or route_row.primary_team_id
    memory_status = memory_statuses_by_team_id.get(team_id)
    memory_readiness_status = memory_status.gate_status if memory_status else "missing"
    memory_use_policy = (
        MEMORY_POLICY_BY_STATUS[memory_readiness_status]
        if memory_status is not None
        else "block"
    )
    assignment_status, assignment_reason_codes = _assignment_status_and_reasons(
        queue_research_status=queue_row.research_status,
        memory_readiness_status=memory_readiness_status,
    )

    return TeamResearchAssignmentRow(
        research_rank=queue_row.research_rank,
        market_slug=queue_row.market_slug,
        question=queue_row.question,
        selected_side=queue_row.selected_side,
        scoring_side=queue_row.scoring_side,
        team_id=team_id,
        category_id=route_row.category_id,
        routing_confidence=route_row.routing_confidence,
        secondary_team_ids=route_row.secondary_team_ids,
        queue_research_status=queue_row.research_status,
        queue_research_bucket=queue_row.research_bucket,
        queue_readiness_status=queue_row.readiness_status,
        memory_readiness_status=memory_readiness_status,
        memory_use_policy=memory_use_policy,
        assignment_status=assignment_status,
        assignment_reason_codes=assignment_reason_codes,
        evidence_gap_codes=queue_row.evidence_gap_codes,
        source_reason_codes=queue_row.reason_codes,
    )


def _assignment_status_and_reasons(
    *,
    queue_research_status: str,
    memory_readiness_status: str,
) -> tuple[str, tuple[str, ...]]:
    reason_codes: list[str] = []
    reason_codes.extend(_queue_status_reason_codes(queue_research_status))
    if memory_readiness_status == "missing":
        reason_codes.append(MISSING_MEMORY_REASON_CODE)
    elif memory_readiness_status == "blocked":
        reason_codes.append(MEMORY_BLOCKED_REASON_CODE)
    elif memory_readiness_status == "watch":
        reason_codes.append(MEMORY_WATCH_REASON_CODE)

    if queue_research_status == "blocked":
        return "blocked", _unique_string_tuple(reason_codes)
    if memory_readiness_status in ("missing", "blocked"):
        return "blocked", _unique_string_tuple(reason_codes)
    if queue_research_status == "watch" or memory_readiness_status == "watch":
        return "watch", _unique_string_tuple(reason_codes)
    return "assigned", (ASSIGNED_REASON_CODE,)


def _queue_status_reason_codes(queue_research_status: str) -> tuple[str, ...]:
    if queue_research_status == "watch":
        return (QUEUE_WATCH_REASON_CODE,)
    if queue_research_status == "blocked":
        return (QUEUE_BLOCKED_REASON_CODE,)
    return ()


def _team_summaries(
    rows: tuple[TeamResearchAssignmentRow, ...],
) -> tuple[TeamResearchAssignmentTeamSummary, ...]:
    team_ids = tuple(sorted({row.team_id for row in rows}))
    summaries: list[TeamResearchAssignmentTeamSummary] = []
    for team_id in team_ids:
        team_rows = tuple(row for row in rows if row.team_id == team_id)
        memory_statuses = tuple(row.memory_readiness_status for row in team_rows)
        memory_policies = tuple(row.memory_use_policy for row in team_rows)
        summaries.append(
            TeamResearchAssignmentTeamSummary(
                team_id=team_id,
                assignment_count=len(team_rows),
                assigned_count=_assignment_status_count(team_rows, "assigned"),
                watch_count=_assignment_status_count(team_rows, "watch"),
                blocked_count=_assignment_status_count(team_rows, "blocked"),
                memory_readiness_status=_summary_memory_status(memory_statuses),
                memory_use_policy=_summary_memory_policy(memory_policies),
            ),
        )
    return tuple(summaries)


def _summary_memory_status(memory_statuses: tuple[str, ...]) -> str:
    if any(status in ("missing", "blocked") for status in memory_statuses):
        return "blocked" if "blocked" in memory_statuses else "missing"
    if "watch" in memory_statuses:
        return "watch"
    return "pass"


def _summary_memory_policy(memory_policies: tuple[str, ...]) -> str:
    if "block" in memory_policies:
        return "block"
    if "throttle" in memory_policies:
        return "throttle"
    return "allow"


def _report_assignment_status(rows: tuple[TeamResearchAssignmentRow, ...]) -> str:
    if any(row.assignment_status == "blocked" for row in rows):
        return "blocked"
    if any(row.assignment_status == "watch" for row in rows):
        return "watch"
    if any(row.assignment_status == "assigned" for row in rows):
        return "ready"
    return "blocked"


def _report_reason_codes(
    rows: tuple[TeamResearchAssignmentRow, ...],
    assignment_status: str,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_QUEUE_REASON_CODE,)
    if assignment_status == "blocked":
        return (BLOCKED_REPORT_REASON_CODE,)
    if assignment_status == "watch":
        return (WATCH_REPORT_REASON_CODE,)
    return (READY_REPORT_REASON_CODE,)


def _normalize_queue_rows(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> tuple[PaperStrategyCandidateResearchQueueRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("queue rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_market_slugs: set[str] = set()
    for row in normalized_rows:
        if type(row) is not PaperStrategyCandidateResearchQueueRow:
            raise ValueError("queue rows must contain PaperStrategyCandidateResearchQueueRow")
        require_paper_only_flags("queue row", row)
        if row.market_slug in seen_market_slugs:
            raise ValueError("queue rows must have unique market_slug values")
        seen_market_slugs.add(row.market_slug)
    return normalized_rows


def _route_rows_by_market_slug(
    rows: tuple[TeamMarketRouteRow, ...],
) -> dict[str, TeamMarketRouteRow]:
    if type(rows) not in (list, tuple):
        raise ValueError("route rows must be a list or tuple")
    rows_by_slug: dict[str, TeamMarketRouteRow] = {}
    for row in rows:
        if type(row) is not TeamMarketRouteRow:
            raise ValueError("route rows must contain TeamMarketRouteRow")
        require_paper_only_flags("route row", row)
        if row.market_slug in rows_by_slug:
            raise ValueError("route rows must have unique market_slug values")
        rows_by_slug[row.market_slug] = row
    return rows_by_slug


def _memory_statuses_by_team_id(
    statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...],
) -> dict[str, TeamMemoryReadinessDigestSourceStatus]:
    if type(statuses) not in (list, tuple):
        raise ValueError("memory source_statuses must be a list or tuple")
    statuses_by_team_id: dict[str, TeamMemoryReadinessDigestSourceStatus] = {}
    for status in statuses:
        if type(status) is not TeamMemoryReadinessDigestSourceStatus:
            raise ValueError(
                "memory source_statuses must contain TeamMemoryReadinessDigestSourceStatus",
            )
        require_paper_only_flags("memory source status", status)
        if status.team_id in statuses_by_team_id:
            raise ValueError("memory source_statuses must have unique team_id values")
        statuses_by_team_id[status.team_id] = status
    return statuses_by_team_id


def _normalize_assignment_rows(
    rows: tuple[TeamResearchAssignmentRow, ...],
) -> tuple[TeamResearchAssignmentRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    for row in normalized_rows:
        if type(row) is not TeamResearchAssignmentRow:
            raise ValueError("rows must contain TeamResearchAssignmentRow")
        require_paper_only_flags("assignment row", row)
    return normalized_rows


def _normalize_team_summaries(
    team_summaries: tuple[TeamResearchAssignmentTeamSummary, ...],
) -> tuple[TeamResearchAssignmentTeamSummary, ...]:
    if type(team_summaries) not in (list, tuple):
        raise ValueError("team_summaries must be a list or tuple")
    summaries = tuple(team_summaries)
    team_ids = tuple(summary.team_id for summary in summaries)
    if team_ids != tuple(sorted(team_ids)):
        raise ValueError("team_summaries must be sorted by team_id")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("team_summaries must have unique team_id values")
    for summary in summaries:
        if type(summary) is not TeamResearchAssignmentTeamSummary:
            raise ValueError(
                "team_summaries must contain TeamResearchAssignmentTeamSummary",
            )
        require_paper_only_flags("team summary", summary)
    return summaries


def _validate_row_consistency(row: TeamResearchAssignmentRow) -> None:
    expected_assignment_status, _ = _assignment_status_and_reasons(
        queue_research_status=row.queue_research_status,
        memory_readiness_status=row.memory_readiness_status,
    )
    if row.assignment_status != expected_assignment_status:
        raise ValueError("assignment_status must match queue and memory status")
    if row.team_id == UNASSIGNED_TEAM_ID and row.assignment_status != "blocked":
        raise ValueError("unassigned rows must be blocked")
    if row.assignment_status == "assigned":
        if row.memory_use_policy != "allow":
            raise ValueError("assigned rows must allow memory use")
        if row.memory_readiness_status != "pass":
            raise ValueError("assigned rows must have pass memory readiness")
    if row.memory_readiness_status == "missing" and row.memory_use_policy != "block":
        raise ValueError("missing memory readiness must block memory use")
    if row.memory_readiness_status in MEMORY_POLICY_BY_STATUS:
        expected_policy = MEMORY_POLICY_BY_STATUS[row.memory_readiness_status]
        if row.memory_use_policy != expected_policy:
            raise ValueError("memory_use_policy must match memory_readiness_status")
    if row.queue_research_status == "blocked" and row.assignment_status != "blocked":
        raise ValueError("blocked queue rows must block assignment")
    if row.memory_readiness_status == "blocked" and row.assignment_status != "blocked":
        raise ValueError("blocked memory readiness must block assignment")
    if row.memory_readiness_status == "watch" and row.assignment_status == "assigned":
        raise ValueError("watch memory readiness cannot be assigned")


def _validate_report_consistency(report: TeamResearchAssignmentReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.assignment_status]:
        raise ValueError("recommended_next_step must match assignment_status")
    if report.assignment_count != len(report.rows):
        raise ValueError("assignment_count must match rows")
    if report.assigned_count != _assignment_status_count(report.rows, "assigned"):
        raise ValueError("assigned_count must match rows")
    if report.watch_count != _assignment_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _assignment_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    expected_status = _report_assignment_status(report.rows)
    if report.assignment_status != expected_status:
        raise ValueError("assignment_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.assignment_status):
        raise ValueError("reason_codes must match assignment_status")
    expected_team_summaries = _team_summaries(report.rows)
    if report.team_summaries != expected_team_summaries:
        raise ValueError("team_summaries must match rows")


def _assignment_status_count(
    rows: tuple[TeamResearchAssignmentRow, ...],
    assignment_status: str,
) -> int:
    return sum(1 for row in rows if row.assignment_status == assignment_status)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_confidence(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("routing_confidence must be a Decimal")
    if not value.is_finite():
        raise ValueError("routing_confidence must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError("routing_confidence must be between 0 and 1")
    return value.quantize(CONFIDENCE_QUANT)


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of canonical strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _unique_string_tuple(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return _normalize_string_tuple("reason_codes", values, allow_empty=False)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "DEFAULT_TEAM_RESEARCH_ASSIGNMENT_CONFIG_VERSION",
    "TeamResearchAssignmentConfig",
    "TeamResearchAssignmentReport",
    "TeamResearchAssignmentRow",
    "TeamResearchAssignmentTeamSummary",
    "build_team_research_assignment_report",
)
