"""Pure paper-only event team capacity allocator."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_EVENT_TEAM_CAPACITY_ALLOCATOR_V10_CONFIG_VERSION = (
    "event-team-capacity-allocator-v10"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ALLOCATION_STATUSES = ("empty", "assigned", "partial", "blocked")
CAPACITY_WARNINGS = (
    "capacity_low_remaining",
    "capacity_fully_used",
    "capacity_constrained",
    "capacity_exhausted",
    "trust_score_below_minimum",
)
REASON_CODES = (
    "event_assigned",
    "event_unassigned",
    "events_assigned",
    "events_unassigned",
    "capacity_available",
    "capacity_low_remaining",
    "capacity_fully_used",
    "capacity_constrained",
    "capacity_exhausted",
    "priority_high",
    "priority_watch",
    "resolution_window_immediate",
    "resolution_window_near",
    "resolution_window_normal",
    "team_fit_strong",
    "team_fit_watch",
    "assignment_score_below_minimum",
    "no_candidate_events",
    "trust_score_sufficient",
    "trust_score_below_minimum",
)


@dataclass(frozen=True)
class EventTeamCapacityAllocatorV10Config:
    config_version: str = DEFAULT_EVENT_TEAM_CAPACITY_ALLOCATOR_V10_CONFIG_VERSION
    immediate_resolution_minutes: Decimal = Decimal("60")
    near_resolution_minutes: Decimal = Decimal("600")
    minimum_assignment_score: Decimal = Decimal("0.500000")
    minimum_trust_score: Decimal = Decimal("0.500000")
    capacity_warning_threshold: Decimal = Decimal("0.100000")
    high_priority_score: Decimal = Decimal("0.750000")
    strong_team_fit_score: Decimal = Decimal("0.700000")
    priority_weight: Decimal = Decimal("0.450000")
    urgency_weight: Decimal = Decimal("0.200000")
    team_fit_weight: Decimal = Decimal("0.250000")
    trust_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, EventTeamCapacityAllocatorV10Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "immediate_resolution_minutes",
            "near_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_assignment_score",
            "minimum_trust_score",
            "capacity_warning_threshold",
            "high_priority_score",
            "strong_team_fit_score",
            "priority_weight",
            "urgency_weight",
            "team_fit_weight",
            "trust_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.immediate_resolution_minutes >= self.near_resolution_minutes:
            raise ValueError(
                "immediate_resolution_minutes must be below near_resolution_minutes",
            )
        if self.minimum_assignment_score > self.high_priority_score:
            raise ValueError("minimum_assignment_score must be <= high_priority_score")
        _validate_score_weights(self)
        require_paper_only_flags("EventTeamCapacityAllocatorV10Config", self)


@dataclass(frozen=True)
class EventTeamCapacityAllocatorV10Candidate:
    market_id: str
    category: str
    priority_score: Decimal
    time_to_resolution_minutes: Decimal
    team_fit_score: Decimal
    estimated_research_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("candidate", self, EventTeamCapacityAllocatorV10Candidate)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        for field_name in ("priority_score", "team_fit_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "time_to_resolution_minutes",
            "estimated_research_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("EventTeamCapacityAllocatorV10Candidate", self)


@dataclass(frozen=True)
class EventTeamCapacityAllocatorV10Team:
    capacity_minutes: Decimal
    trust_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("team", self, EventTeamCapacityAllocatorV10Team)
        object.__setattr__(
            self,
            "capacity_minutes",
            _normalize_nonnegative_count("capacity_minutes", self.capacity_minutes),
        )
        object.__setattr__(
            self,
            "trust_score",
            _normalize_ratio("trust_score", self.trust_score),
        )
        require_paper_only_flags("EventTeamCapacityAllocatorV10Team", self)


@dataclass(frozen=True)
class EventTeamCapacityAllocatorV10AssignedRow:
    market_id: str
    category: str
    priority_score: Decimal
    time_to_resolution_minutes: Decimal
    team_fit_score: Decimal
    estimated_research_minutes: Decimal
    urgency_score: Decimal
    allocation_score: Decimal
    assigned_minutes: Decimal
    remaining_capacity_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, EventTeamCapacityAllocatorV10AssignedRow)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        for field_name in (
            "priority_score",
            "team_fit_score",
            "urgency_score",
            "allocation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "time_to_resolution_minutes",
            "estimated_research_minutes",
            "assigned_minutes",
            "remaining_capacity_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.assigned_minutes != self.estimated_research_minutes:
            raise ValueError("assigned_minutes must equal estimated_research_minutes")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("EventTeamCapacityAllocatorV10AssignedRow", self)


@dataclass(frozen=True)
class EventTeamCapacityAllocatorV10Report:
    config_version: str
    allocation_status: str
    candidate_count: Decimal
    assigned_count: Decimal
    unassigned_count: Decimal
    capacity_minutes: Decimal
    allocated_minutes: Decimal
    remaining_capacity_minutes: Decimal
    trust_score: Decimal
    assigned_rows: tuple[EventTeamCapacityAllocatorV10AssignedRow, ...]
    unassigned_market_ids: tuple[str, ...]
    capacity_warnings: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, EventTeamCapacityAllocatorV10Report)
        _require_canonical_string("config_version", self.config_version)
        _require_choice("allocation_status", self.allocation_status, ALLOCATION_STATUSES)
        for field_name in (
            "candidate_count",
            "assigned_count",
            "unassigned_count",
            "capacity_minutes",
            "allocated_minutes",
            "remaining_capacity_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "trust_score",
            _normalize_ratio("trust_score", self.trust_score),
        )
        object.__setattr__(
            self,
            "assigned_rows",
            _normalize_assigned_rows(self.assigned_rows),
        )
        object.__setattr__(
            self,
            "unassigned_market_ids",
            _normalize_market_ids(self.unassigned_market_ids),
        )
        object.__setattr__(
            self,
            "capacity_warnings",
            _normalize_capacity_warnings(self.capacity_warnings),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("EventTeamCapacityAllocatorV10Report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return event_team_capacity_allocator_v10_payload(self)


def allocate_event_team_capacity_v10(
    candidates: tuple[EventTeamCapacityAllocatorV10Candidate, ...],
    *,
    team: EventTeamCapacityAllocatorV10Team,
    config: EventTeamCapacityAllocatorV10Config | None = None,
) -> EventTeamCapacityAllocatorV10Report:
    normalized_candidates = _normalize_candidates(candidates)
    if type(team) is not EventTeamCapacityAllocatorV10Team:
        raise ValueError("team must be an EventTeamCapacityAllocatorV10Team")
    require_paper_only_flags("team", team)
    active_config = config or EventTeamCapacityAllocatorV10Config()
    if type(active_config) is not EventTeamCapacityAllocatorV10Config:
        raise ValueError("config must be an EventTeamCapacityAllocatorV10Config")
    require_paper_only_flags("config", active_config)

    if not normalized_candidates:
        return _build_report(
            config=active_config,
            allocation_status="empty",
            candidates=normalized_candidates,
            team=team,
            assigned_rows=(),
            unassigned_market_ids=(),
            capacity_warnings=(),
            reason_codes=("no_candidate_events", _trust_reason(team, active_config)),
        )

    if team.trust_score < active_config.minimum_trust_score:
        return _build_report(
            config=active_config,
            allocation_status="blocked",
            candidates=normalized_candidates,
            team=team,
            assigned_rows=(),
            unassigned_market_ids=tuple(item.market_id for item in normalized_candidates),
            capacity_warnings=("trust_score_below_minimum",),
            reason_codes=("events_unassigned", "trust_score_below_minimum"),
        )

    ranked_candidates = sorted(
        normalized_candidates,
        key=lambda item: (
            _allocation_score(item, team, active_config),
            item.priority_score,
            _urgency_score(item.time_to_resolution_minutes, active_config),
            -item.time_to_resolution_minutes,
            item.market_id,
        ),
        reverse=True,
    )
    remaining_capacity = team.capacity_minutes
    assigned_rows: list[EventTeamCapacityAllocatorV10AssignedRow] = []
    unassigned_market_ids: list[str] = []

    for item in ranked_candidates:
        urgency_score = _urgency_score(item.time_to_resolution_minutes, active_config)
        allocation_score = _allocation_score(item, team, active_config)
        if (
            allocation_score >= active_config.minimum_assignment_score
            and item.estimated_research_minutes <= remaining_capacity
        ):
            remaining_capacity -= item.estimated_research_minutes
            assigned_rows.append(
                EventTeamCapacityAllocatorV10AssignedRow(
                    market_id=item.market_id,
                    category=item.category,
                    priority_score=item.priority_score,
                    time_to_resolution_minutes=item.time_to_resolution_minutes,
                    team_fit_score=item.team_fit_score,
                    estimated_research_minutes=item.estimated_research_minutes,
                    urgency_score=urgency_score,
                    allocation_score=allocation_score,
                    assigned_minutes=item.estimated_research_minutes,
                    remaining_capacity_minutes=remaining_capacity,
                    reason_codes=_row_reason_codes(
                        candidate=item,
                        team=team,
                        config=active_config,
                        allocation_score=allocation_score,
                    ),
                ),
            )
        else:
            unassigned_market_ids.append(item.market_id)

    return _build_report(
        config=active_config,
        allocation_status=_allocation_status(
            assigned_count=len(assigned_rows),
            unassigned_count=len(unassigned_market_ids),
        ),
        candidates=normalized_candidates,
        team=team,
        assigned_rows=tuple(assigned_rows),
        unassigned_market_ids=tuple(unassigned_market_ids),
        capacity_warnings=_capacity_warnings(
            capacity_minutes=team.capacity_minutes,
            remaining_capacity_minutes=remaining_capacity,
            unassigned_count=len(unassigned_market_ids),
            config=active_config,
        ),
        reason_codes=_report_reason_codes(
            assigned_count=len(assigned_rows),
            unassigned_count=len(unassigned_market_ids),
            capacity_warnings=_capacity_warnings(
                capacity_minutes=team.capacity_minutes,
                remaining_capacity_minutes=remaining_capacity,
                unassigned_count=len(unassigned_market_ids),
                config=active_config,
            ),
            trust_reason=_trust_reason(team, active_config),
        ),
    )


def event_team_capacity_allocator_v10_payload(
    report: EventTeamCapacityAllocatorV10Report,
) -> dict[str, Any]:
    if type(report) is not EventTeamCapacityAllocatorV10Report:
        raise ValueError("report must be an EventTeamCapacityAllocatorV10Report")
    require_paper_only_flags("report", report)
    payload = {
        "config_version": report.config_version,
        "allocation_status": report.allocation_status,
        "candidate_count": report.candidate_count,
        "assigned_count": report.assigned_count,
        "unassigned_count": report.unassigned_count,
        "capacity_minutes": report.capacity_minutes,
        "allocated_minutes": report.allocated_minutes,
        "remaining_capacity_minutes": report.remaining_capacity_minutes,
        "trust_score": report.trust_score,
        "assigned_rows": report.assigned_rows,
        "unassigned_market_ids": report.unassigned_market_ids,
        "capacity_warnings": report.capacity_warnings,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _build_report(
    *,
    config: EventTeamCapacityAllocatorV10Config,
    allocation_status: str,
    candidates: tuple[EventTeamCapacityAllocatorV10Candidate, ...],
    team: EventTeamCapacityAllocatorV10Team,
    assigned_rows: tuple[EventTeamCapacityAllocatorV10AssignedRow, ...],
    unassigned_market_ids: tuple[str, ...],
    capacity_warnings: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> EventTeamCapacityAllocatorV10Report:
    allocated_minutes = sum((row.assigned_minutes for row in assigned_rows), ZERO_COUNT)
    return EventTeamCapacityAllocatorV10Report(
        config_version=config.config_version,
        allocation_status=allocation_status,
        candidate_count=_count(len(candidates)),
        assigned_count=_count(len(assigned_rows)),
        unassigned_count=_count(len(unassigned_market_ids)),
        capacity_minutes=team.capacity_minutes,
        allocated_minutes=allocated_minutes,
        remaining_capacity_minutes=team.capacity_minutes - allocated_minutes,
        trust_score=team.trust_score,
        assigned_rows=assigned_rows,
        unassigned_market_ids=unassigned_market_ids,
        capacity_warnings=capacity_warnings,
        reason_codes=reason_codes,
    )


def _allocation_score(
    candidate: EventTeamCapacityAllocatorV10Candidate,
    team: EventTeamCapacityAllocatorV10Team,
    config: EventTeamCapacityAllocatorV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            candidate.priority_score * config.priority_weight
            + _urgency_score(candidate.time_to_resolution_minutes, config)
            * config.urgency_weight
            + candidate.team_fit_score * config.team_fit_weight
            + team.trust_score * config.trust_weight,
        )


def _urgency_score(
    time_to_resolution_minutes: Decimal,
    config: EventTeamCapacityAllocatorV10Config,
) -> Decimal:
    if time_to_resolution_minutes <= config.immediate_resolution_minutes:
        return ONE_RATIO
    if time_to_resolution_minutes >= config.near_resolution_minutes:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        resolution_range = (
            config.near_resolution_minutes - config.immediate_resolution_minutes
        )
        minutes_remaining = config.near_resolution_minutes - time_to_resolution_minutes
        return _clamp_ratio(minutes_remaining / resolution_range)


def _row_reason_codes(
    *,
    candidate: EventTeamCapacityAllocatorV10Candidate,
    team: EventTeamCapacityAllocatorV10Team,
    config: EventTeamCapacityAllocatorV10Config,
    allocation_score: Decimal,
) -> tuple[str, ...]:
    codes = ["event_assigned"]
    codes.append(
        "priority_high"
        if candidate.priority_score >= config.high_priority_score
        else "priority_watch",
    )
    if candidate.time_to_resolution_minutes <= config.immediate_resolution_minutes:
        codes.append("resolution_window_immediate")
    elif candidate.time_to_resolution_minutes <= config.near_resolution_minutes:
        codes.append("resolution_window_near")
    else:
        codes.append("resolution_window_normal")
    codes.append(
        "team_fit_strong"
        if candidate.team_fit_score >= config.strong_team_fit_score
        else "team_fit_watch",
    )
    if allocation_score < config.minimum_assignment_score:
        codes.append("assignment_score_below_minimum")
    codes.append(_trust_reason(team, config))
    return _normalize_reason_codes(tuple(codes))


def _capacity_warnings(
    *,
    capacity_minutes: Decimal,
    remaining_capacity_minutes: Decimal,
    unassigned_count: int,
    config: EventTeamCapacityAllocatorV10Config,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if capacity_minutes == ZERO_COUNT:
        warnings.append("capacity_exhausted")
    elif remaining_capacity_minutes == ZERO_COUNT:
        warnings.append("capacity_fully_used")
    elif _remaining_capacity_ratio(
        capacity_minutes,
        remaining_capacity_minutes,
    ) <= config.capacity_warning_threshold:
        warnings.append("capacity_low_remaining")
    if unassigned_count:
        warnings.append("capacity_constrained")
    return _normalize_capacity_warnings(tuple(warnings))


def _report_reason_codes(
    *,
    assigned_count: int,
    unassigned_count: int,
    capacity_warnings: tuple[str, ...],
    trust_reason: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if assigned_count:
        codes.append("events_assigned")
    if unassigned_count:
        codes.append("events_unassigned")
    codes.extend(capacity_warnings)
    if trust_reason not in codes:
        codes.append(trust_reason)
    return _normalize_reason_codes(tuple(codes))


def _allocation_status(*, assigned_count: int, unassigned_count: int) -> str:
    if assigned_count and unassigned_count:
        return "partial"
    if assigned_count:
        return "assigned"
    return "blocked"


def _trust_reason(
    team: EventTeamCapacityAllocatorV10Team,
    config: EventTeamCapacityAllocatorV10Config,
) -> str:
    if team.trust_score < config.minimum_trust_score:
        return "trust_score_below_minimum"
    return "trust_score_sufficient"


def _remaining_capacity_ratio(
    capacity_minutes: Decimal,
    remaining_capacity_minutes: Decimal,
) -> Decimal:
    if capacity_minutes == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(remaining_capacity_minutes / capacity_minutes)


def _validate_report(report: EventTeamCapacityAllocatorV10Report) -> None:
    if report.assigned_count != _count(len(report.assigned_rows)):
        raise ValueError("assigned_count must equal assigned_rows count")
    if report.unassigned_count != _count(len(report.unassigned_market_ids)):
        raise ValueError("unassigned_count must equal unassigned ids count")
    if report.candidate_count != report.assigned_count + report.unassigned_count:
        raise ValueError("candidate_count must equal assigned plus unassigned count")
    allocated_minutes = sum(
        (row.assigned_minutes for row in report.assigned_rows),
        ZERO_COUNT,
    )
    if report.allocated_minutes != allocated_minutes:
        raise ValueError("allocated_minutes must equal assigned row sum")
    if report.remaining_capacity_minutes != report.capacity_minutes - allocated_minutes:
        raise ValueError("remaining_capacity_minutes must equal capacity less allocated")
    if report.remaining_capacity_minutes < ZERO_COUNT:
        raise ValueError("remaining_capacity_minutes must be nonnegative")
    if report.allocation_status != _expected_report_status(report):
        raise ValueError("allocation_status must match assignment state")
    expected_reason_codes = _expected_report_reason_codes(report)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("report reason_codes must match")


def _expected_report_status(report: EventTeamCapacityAllocatorV10Report) -> str:
    if report.candidate_count == ZERO_COUNT:
        return "empty"
    if report.assigned_count and report.unassigned_count:
        return "partial"
    if report.assigned_count:
        return "assigned"
    return "blocked"


def _expected_report_reason_codes(
    report: EventTeamCapacityAllocatorV10Report,
) -> tuple[str, ...]:
    if report.candidate_count == ZERO_COUNT:
        return _normalize_reason_codes(("no_candidate_events", _report_trust_reason(report)))
    return _report_reason_codes(
        assigned_count=int(report.assigned_count),
        unassigned_count=int(report.unassigned_count),
        capacity_warnings=report.capacity_warnings,
        trust_reason=_report_trust_reason(report),
    )


def _report_trust_reason(report: EventTeamCapacityAllocatorV10Report) -> str:
    if "trust_score_below_minimum" in report.capacity_warnings:
        return "trust_score_below_minimum"
    if "trust_score_below_minimum" in report.reason_codes:
        return "trust_score_below_minimum"
    return "trust_score_sufficient"


def _validate_score_weights(config: EventTeamCapacityAllocatorV10Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            config.priority_weight
            + config.urgency_weight
            + config.team_fit_weight
            + config.trust_weight
        ).quantize(RATIO_QUANTUM)
    if total != ONE_RATIO:
        raise ValueError("score component weights must sum to 1.000000")


def _normalize_candidates(
    candidates: tuple[EventTeamCapacityAllocatorV10Candidate, ...],
) -> tuple[EventTeamCapacityAllocatorV10Candidate, ...]:
    if type(candidates) is not tuple:
        candidates = tuple(candidates)
    for candidate in candidates:
        if type(candidate) is not EventTeamCapacityAllocatorV10Candidate:
            raise ValueError("candidates must contain EventTeamCapacityAllocatorV10Candidate")
        require_paper_only_flags("candidate", candidate)
    return candidates


def _normalize_assigned_rows(
    rows: tuple[EventTeamCapacityAllocatorV10AssignedRow, ...],
) -> tuple[EventTeamCapacityAllocatorV10AssignedRow, ...]:
    if type(rows) is not tuple:
        rows = tuple(rows)
    for row in rows:
        if type(row) is not EventTeamCapacityAllocatorV10AssignedRow:
            raise ValueError("assigned_rows must contain EventTeamCapacityAllocatorV10AssignedRow")
        require_paper_only_flags("assigned row", row)
    return rows


def _normalize_market_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        values = tuple(values)
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("market_id", value)
        if value in seen:
            raise ValueError("unassigned_market_ids contains duplicate value")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_capacity_warnings(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("capacity_warnings must be a tuple")
    seen: set[str] = set()
    for value in values:
        _require_choice("capacity_warnings", value, CAPACITY_WARNINGS)
        if value in seen:
            raise ValueError("capacity_warnings contains duplicate value")
        seen.add(value)
    return tuple(value for value in CAPACITY_WARNINGS if value in seen)


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_choice("reason_codes", value, REASON_CODES)
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_choice(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "ALLOCATION_STATUSES",
    "CAPACITY_WARNINGS",
    "DEFAULT_EVENT_TEAM_CAPACITY_ALLOCATOR_V10_CONFIG_VERSION",
    "REASON_CODES",
    "EventTeamCapacityAllocatorV10AssignedRow",
    "EventTeamCapacityAllocatorV10Candidate",
    "EventTeamCapacityAllocatorV10Config",
    "EventTeamCapacityAllocatorV10Report",
    "EventTeamCapacityAllocatorV10Team",
    "allocate_event_team_capacity_v10",
    "event_team_capacity_allocator_v10_payload",
)
