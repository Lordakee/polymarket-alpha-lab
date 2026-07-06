"""Pure Phase 1 team specialist decision review load router."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_SPECIALIST_DECISION_REVIEW_LOAD_ROUTER_V2_CONFIG_VERSION = (
    "team-specialist-decision-review-load-router-v2"
)
TEAM_SPECIALIST_DECISION_REVIEW_LOAD_ROUTER_V2_STATUSES = (
    "pass",
    "watch",
    "blocked",
)

CATEGORY_ROUTE_MATCH_REASON = "category_route_match"
CATEGORY_ROUTE_MISS_REASON = "category_route_miss"
EVIDENCE_GAP_REASON = "evidence_gap"
DECISION_UNCERTAINTY_REASON = "decision_uncertainty"
CONFLICT_SEVERITY_REASON = "conflict_severity"
DEADLINE_PRESSURE_REASON = "deadline_pressure"
TEAM_LOAD_READY_REASON = "team_load_ready"
TEAM_LOAD_OVER_CAPACITY_REASON = "team_load_over_capacity"
URGENT_REVIEW_REASON = "urgent_review"
DECISION_REVIEW_PASS_REASON = "decision_review_pass"
REPORT_BLOCKED_REASON = "specialist_decision_review_router_blocked"
REPORT_WATCH_REASON = "specialist_decision_review_router_watch"
EMPTY_REVIEW_REASON = "specialist_decision_review_router_empty"

ROW_REASON_CODES = (
    CATEGORY_ROUTE_MATCH_REASON,
    CATEGORY_ROUTE_MISS_REASON,
    EVIDENCE_GAP_REASON,
    DECISION_UNCERTAINTY_REASON,
    CONFLICT_SEVERITY_REASON,
    DEADLINE_PRESSURE_REASON,
    TEAM_LOAD_READY_REASON,
    TEAM_LOAD_OVER_CAPACITY_REASON,
    URGENT_REVIEW_REASON,
    DECISION_REVIEW_PASS_REASON,
)
REPORT_REASON_CODES = (
    REPORT_BLOCKED_REASON,
    REPORT_WATCH_REASON,
    EVIDENCE_GAP_REASON,
    DECISION_UNCERTAINTY_REASON,
    CONFLICT_SEVERITY_REASON,
    DEADLINE_PRESSURE_REASON,
    TEAM_LOAD_OVER_CAPACITY_REASON,
    CATEGORY_ROUTE_MISS_REASON,
    URGENT_REVIEW_REASON,
    DECISION_REVIEW_PASS_REASON,
    EMPTY_REVIEW_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

EVIDENCE_GAP_WEIGHT = Decimal("0.30")
DECISION_UNCERTAINTY_WEIGHT = Decimal("0.25")
CONFLICT_SEVERITY_WEIGHT = Decimal("0.25")
DEADLINE_PRESSURE_WEIGHT = Decimal("0.20")
URGENT_REVIEW_BONUS = Decimal("0.250000")
DEFAULT_OVERLOAD_PENALTY_SCORE = Decimal("0.300000")

UNASSIGNED_SPECIALIST_TEAM_ID = "unassigned-specialist-review"
PRIVATE_REFERENCE_MARKER = "[redacted]"
SAFE_REFERENCE_PREFIXES = ("public:", "memory:", "source:", "lesson:")
PRIVATE_REFERENCE_FRAGMENTS = (
    "://",
    "@",
    "api_key",
    "bearer ",
    "credential",
    "private_key",
    "secret",
    "token",
    "key:",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute:
    category_id: str
    specialist_team_id: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_team_id", self.specialist_team_id)
        require_paper_only_flags("category route", self)


@dataclass(frozen=True)
class TeamSpecialistDecisionReviewLoadRouterV2Config:
    category_routes: tuple[TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute, ...]
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_DECISION_REVIEW_LOAD_ROUTER_V2_CONFIG_VERSION
    )
    evidence_gap_threshold: Decimal = Decimal("0.500000")
    decision_uncertainty_threshold: Decimal = Decimal("0.500000")
    conflict_severity_threshold: Decimal = Decimal("0.500000")
    deadline_pressure_threshold: Decimal = Decimal("0.500000")
    min_watch_priority_score: Decimal = Decimal("0.250000")
    min_block_priority_score: Decimal = Decimal("0.650000")
    overload_penalty_score: Decimal = DEFAULT_OVERLOAD_PENALTY_SCORE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "category_routes",
            _normalize_category_routes(self.category_routes),
        )
        for field_name in (
            "evidence_gap_threshold",
            "decision_uncertainty_threshold",
            "conflict_severity_threshold",
            "deadline_pressure_threshold",
            "min_watch_priority_score",
            "min_block_priority_score",
            "overload_penalty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_watch_priority_score > self.min_block_priority_score:
            raise ValueError(
                "min_watch_priority_score must be less than or equal to "
                "min_block_priority_score",
            )
        require_paper_only_flags("decision review load router config", self)


@dataclass(frozen=True)
class TeamSpecialistDecisionReviewLoadRouterV2TeamLoad:
    specialist_team_id: str
    assigned_review_count: Decimal
    capacity_review_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("specialist_team_id", self.specialist_team_id)
        object.__setattr__(
            self,
            "assigned_review_count",
            _normalize_count("assigned_review_count", self.assigned_review_count),
        )
        object.__setattr__(
            self,
            "capacity_review_count",
            _normalize_positive_count(
                "capacity_review_count",
                self.capacity_review_count,
            ),
        )
        require_paper_only_flags("decision review team load", self)


@dataclass(frozen=True)
class TeamSpecialistDecisionReviewLoadRouterV2Review:
    review_item_id: str
    category_id: str
    queued_at: datetime
    evidence_gap_score: Decimal
    decision_uncertainty_score: Decimal
    conflict_severity_score: Decimal
    deadline_pressure_score: Decimal
    urgent_review: bool
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("review_item_id", self.review_item_id)
        _require_public_string("category_id", self.category_id)
        _require_public_string("source_reference", self.source_reference)
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        for field_name in (
            "evidence_gap_score",
            "decision_uncertainty_score",
            "conflict_severity_score",
            "deadline_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.urgent_review) is not bool:
            raise ValueError("urgent_review must be a bool")
        require_paper_only_flags("decision review item", self)


@dataclass(frozen=True)
class TeamSpecialistDecisionReviewLoadRouterV2Assignment:
    review_item_id: str
    category_id: str
    specialist_team_id: str
    queued_at: datetime
    evidence_gap_score: Decimal
    decision_uncertainty_score: Decimal
    conflict_severity_score: Decimal
    deadline_pressure_score: Decimal
    urgent_review: bool
    base_priority_score: Decimal
    overload_penalty_score: Decimal
    priority_score: Decimal
    team_assigned_review_count: Decimal
    team_capacity_review_count: Decimal
    team_load_ratio: Decimal
    route_status: str
    redacted_source_reference: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("review_item_id", self.review_item_id)
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_team_id", self.specialist_team_id)
        _require_public_string("redacted_source_reference", self.redacted_source_reference)
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        for field_name in (
            "evidence_gap_score",
            "decision_uncertainty_score",
            "conflict_severity_score",
            "deadline_pressure_score",
            "base_priority_score",
            "overload_penalty_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("team_assigned_review_count", "team_capacity_review_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_load_ratio",
            _normalize_nonnegative_ratio_like("team_load_ratio", self.team_load_ratio),
        )
        if type(self.urgent_review) is not bool:
            raise ValueError("urgent_review must be a bool")
        _require_status("route_status", self.route_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_assignment(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _assignment_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _assignment_derived_validation_digest(
                self,
            ):
                raise ValueError("derived_validation_digest must match assignment fields")
        _reject_unsafe_public_payload(
            "decision review load router assignment",
            json_ready_no_floats(self),
        )
        require_paper_only_flags("decision review load router assignment", self)


@dataclass(frozen=True)
class TeamSpecialistDecisionReviewLoadRouterV2Report:
    generated_at: datetime
    config_version: str
    review_count: Decimal
    specialist_team_count: Decimal
    assignment_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    urgent_review_count: Decimal
    overloaded_team_count: Decimal
    average_priority_score: Decimal
    max_team_load_ratio: Decimal
    route_status: str
    reason_codes: tuple[str, ...]
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "review_count",
            "specialist_team_count",
            "assignment_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "urgent_review_count",
            "overloaded_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_priority_score",
            _normalize_ratio("average_priority_score", self.average_priority_score),
        )
        object.__setattr__(
            self,
            "max_team_load_ratio",
            _normalize_nonnegative_ratio_like(
                "max_team_load_ratio",
                self.max_team_load_ratio,
            ),
        )
        _require_status("route_status", self.route_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "assignments", _normalize_assignments(self.assignments))
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report fields")
        _reject_unsafe_public_payload(
            "decision review load router report",
            json_ready_no_floats(self),
        )
        require_paper_only_flags("decision review load router report", self)


def build_team_specialist_decision_review_load_router_v2_report(
    review_items: list[TeamSpecialistDecisionReviewLoadRouterV2Review]
    | tuple[TeamSpecialistDecisionReviewLoadRouterV2Review, ...],
    *,
    team_loads: list[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad]
    | tuple[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad, ...],
    config: TeamSpecialistDecisionReviewLoadRouterV2Config,
    generated_at: datetime,
) -> TeamSpecialistDecisionReviewLoadRouterV2Report:
    if type(config) is not TeamSpecialistDecisionReviewLoadRouterV2Config:
        raise ValueError(
            "config must be a TeamSpecialistDecisionReviewLoadRouterV2Config",
        )
    require_paper_only_flags("decision review load router config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_review_items(review_items)
    load_rows = _normalize_team_loads(team_loads)
    assignments = tuple(
        sorted(
            (_assignment_for_review(row, load_rows, config) for row in rows),
            key=_assignment_sort_key,
        ),
    )
    return TeamSpecialistDecisionReviewLoadRouterV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        review_count=_count(len(rows)),
        specialist_team_count=_count(
            len({row.specialist_team_id for row in assignments}),
        ),
        assignment_count=_count(len(assignments)),
        blocked_count=_status_count(assignments, "blocked"),
        watch_count=_status_count(assignments, "watch"),
        pass_count=_status_count(assignments, "pass"),
        urgent_review_count=_count(
            len(tuple(row for row in assignments if row.urgent_review)),
        ),
        overloaded_team_count=_overloaded_assignment_team_count(assignments),
        average_priority_score=_average_priority_score(assignments),
        max_team_load_ratio=_max_assignment_team_load_ratio(assignments),
        route_status=_report_status(assignments),
        reason_codes=_report_reason_codes(assignments),
        assignments=assignments,
    )


def team_specialist_decision_review_load_router_v2_payload(
    value: TeamSpecialistDecisionReviewLoadRouterV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is TeamSpecialistDecisionReviewLoadRouterV2Report:
        require_paper_only_flags("decision review load router report", value)
        _validate_report(value)
        payload = json_ready_no_floats(value)
    elif type(value) is dict:
        payload = json_ready_no_floats(value)
    else:
        raise ValueError(
            "value must be a TeamSpecialistDecisionReviewLoadRouterV2Report "
            "or JSON object",
        )
    if not isinstance(payload, dict):
        raise ValueError("decision review load router payload must be a JSON object")
    validate_team_specialist_decision_review_load_router_v2_public_payload(payload)
    return payload


def validate_team_specialist_decision_review_load_router_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_values("public payload", payload)
    _require_public_payload_flags(payload, "public payload")
    assignments = payload.get("assignments")
    if type(assignments) is not list:
        raise ValueError("assignments must be a list in public payload")
    for index, row in enumerate(assignments):
        if type(row) is not dict:
            raise ValueError("assignments must contain JSON objects")
        _require_public_payload_flags(row, f"public payload assignment {index}")
        _validate_assignment_public_payload_digest(row)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_report_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _assignment_for_review(
    row: TeamSpecialistDecisionReviewLoadRouterV2Review,
    loads: tuple[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad, ...],
    config: TeamSpecialistDecisionReviewLoadRouterV2Config,
) -> TeamSpecialistDecisionReviewLoadRouterV2Assignment:
    specialist_team_id = _specialist_team_for_category(row.category_id, config)
    team_load = _team_load_for_specialist(specialist_team_id, loads)
    assigned_count = ZERO
    capacity_count = COUNT_QUANTUM
    if team_load is not None:
        assigned_count = team_load.assigned_review_count
        capacity_count = team_load.capacity_review_count
    team_load_ratio = _load_ratio(assigned_count, capacity_count)
    overload_penalty_score = _overload_penalty(team_load_ratio, config)
    base_priority_score = _base_priority_score(row)
    priority_score = _priority_score(
        base_priority_score,
        overload_penalty_score,
        row.urgent_review,
    )
    reason_codes = _assignment_reason_codes(
        row,
        specialist_team_id,
        team_load_ratio,
        config,
    )
    return TeamSpecialistDecisionReviewLoadRouterV2Assignment(
        review_item_id=row.review_item_id,
        category_id=row.category_id,
        specialist_team_id=specialist_team_id,
        queued_at=row.queued_at,
        evidence_gap_score=row.evidence_gap_score,
        decision_uncertainty_score=row.decision_uncertainty_score,
        conflict_severity_score=row.conflict_severity_score,
        deadline_pressure_score=row.deadline_pressure_score,
        urgent_review=row.urgent_review,
        base_priority_score=base_priority_score,
        overload_penalty_score=overload_penalty_score,
        priority_score=priority_score,
        team_assigned_review_count=assigned_count,
        team_capacity_review_count=capacity_count,
        team_load_ratio=team_load_ratio,
        route_status=_assignment_status(priority_score, reason_codes, config),
        redacted_source_reference=_redact_source_reference(row.source_reference),
        reason_codes=reason_codes,
    )


def _specialist_team_for_category(
    category_id: str,
    config: TeamSpecialistDecisionReviewLoadRouterV2Config,
) -> str:
    for route in config.category_routes:
        if route.category_id == category_id:
            return route.specialist_team_id
    return UNASSIGNED_SPECIALIST_TEAM_ID


def _team_load_for_specialist(
    specialist_team_id: str,
    loads: tuple[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad, ...],
) -> TeamSpecialistDecisionReviewLoadRouterV2TeamLoad | None:
    for row in loads:
        if row.specialist_team_id == specialist_team_id:
            return row
    return None


def _assignment_reason_codes(
    row: TeamSpecialistDecisionReviewLoadRouterV2Review,
    specialist_team_id: str,
    team_load_ratio: Decimal,
    config: TeamSpecialistDecisionReviewLoadRouterV2Config,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if specialist_team_id == UNASSIGNED_SPECIALIST_TEAM_ID:
        codes.add(CATEGORY_ROUTE_MISS_REASON)
    else:
        codes.add(CATEGORY_ROUTE_MATCH_REASON)
    if row.evidence_gap_score >= config.evidence_gap_threshold:
        codes.add(EVIDENCE_GAP_REASON)
    if row.decision_uncertainty_score >= config.decision_uncertainty_threshold:
        codes.add(DECISION_UNCERTAINTY_REASON)
    if row.conflict_severity_score >= config.conflict_severity_threshold:
        codes.add(CONFLICT_SEVERITY_REASON)
    if row.deadline_pressure_score >= config.deadline_pressure_threshold:
        codes.add(DEADLINE_PRESSURE_REASON)
    if team_load_ratio > ONE_RATIO:
        codes.add(TEAM_LOAD_OVER_CAPACITY_REASON)
    else:
        codes.add(TEAM_LOAD_READY_REASON)
    if row.urgent_review:
        codes.add(URGENT_REVIEW_REASON)
    if codes == {CATEGORY_ROUTE_MATCH_REASON, TEAM_LOAD_READY_REASON}:
        codes.add(DECISION_REVIEW_PASS_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _assignment_status(
    priority_score: Decimal,
    reason_codes: tuple[str, ...],
    config: TeamSpecialistDecisionReviewLoadRouterV2Config,
) -> str:
    if CATEGORY_ROUTE_MISS_REASON in reason_codes:
        return "blocked"
    if TEAM_LOAD_OVER_CAPACITY_REASON in reason_codes:
        return "blocked"
    if priority_score >= config.min_block_priority_score:
        return "blocked"
    if URGENT_REVIEW_REASON in reason_codes:
        return "watch"
    if priority_score >= config.min_watch_priority_score:
        return "watch"
    if reason_codes != (
        CATEGORY_ROUTE_MATCH_REASON,
        TEAM_LOAD_READY_REASON,
        DECISION_REVIEW_PASS_REASON,
    ):
        return "watch"
    return "pass"


def _base_priority_score(
    row: TeamSpecialistDecisionReviewLoadRouterV2Review,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            row.evidence_gap_score * EVIDENCE_GAP_WEIGHT
            + row.decision_uncertainty_score * DECISION_UNCERTAINTY_WEIGHT
            + row.conflict_severity_score * CONFLICT_SEVERITY_WEIGHT
            + row.deadline_pressure_score * DEADLINE_PRESSURE_WEIGHT
        ).quantize(RATIO_QUANTUM)


def _priority_score(
    base_priority_score: Decimal,
    overload_penalty_score: Decimal,
    urgent_review: bool,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = base_priority_score + overload_penalty_score
        if urgent_review:
            score += URGENT_REVIEW_BONUS
        if score > ONE_RATIO:
            score = ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _overload_penalty(
    team_load_ratio: Decimal,
    config: TeamSpecialistDecisionReviewLoadRouterV2Config,
) -> Decimal:
    if team_load_ratio <= ONE_RATIO:
        return ZERO_RATIO
    return config.overload_penalty_score


def _load_ratio(assigned_count: Decimal, capacity_count: Decimal) -> Decimal:
    if capacity_count <= ZERO:
        raise ValueError("capacity_review_count must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (assigned_count / capacity_count).quantize(RATIO_QUANTUM)


def _report_status(
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...],
) -> str:
    if not assignments:
        return "blocked"
    if any(row.route_status == "blocked" for row in assignments):
        return "blocked"
    if any(row.route_status == "watch" for row in assignments):
        return "watch"
    return "pass"


def _report_reason_codes(
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...],
) -> tuple[str, ...]:
    if not assignments:
        return (EMPTY_REVIEW_REASON,)
    codes = {
        code
        for row in assignments
        for code in row.reason_codes
        if code
        not in (
            CATEGORY_ROUTE_MATCH_REASON,
            TEAM_LOAD_READY_REASON,
            DECISION_REVIEW_PASS_REASON,
        )
    }
    status = _report_status(assignments)
    if status == "blocked":
        codes.add(REPORT_BLOCKED_REASON)
    elif status == "watch":
        codes.add(REPORT_WATCH_REASON)
    if not codes:
        codes.add(DECISION_REVIEW_PASS_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _validate_assignment(
    row: TeamSpecialistDecisionReviewLoadRouterV2Assignment,
) -> None:
    expected_base_priority_score = _base_priority_score_from_values(
        row.evidence_gap_score,
        row.decision_uncertainty_score,
        row.conflict_severity_score,
        row.deadline_pressure_score,
    )
    if row.base_priority_score != expected_base_priority_score:
        raise ValueError("base_priority_score must match review pressure dimensions")
    expected_load_ratio = _load_ratio(
        row.team_assigned_review_count,
        row.team_capacity_review_count,
    )
    if row.team_load_ratio != expected_load_ratio:
        raise ValueError("team_load_ratio must match team assigned and capacity counts")
    expected_priority_score = _priority_score(
        row.base_priority_score,
        row.overload_penalty_score,
        row.urgent_review,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match review load dimensions")
    expected_status = _assignment_status(
        row.priority_score,
        row.reason_codes,
        _status_validation_config(),
    )
    if row.route_status != expected_status:
        raise ValueError("route_status must match priority and reason codes")
    if (
        row.redacted_source_reference != PRIVATE_REFERENCE_MARKER
        and _is_private_reference(row.redacted_source_reference)
    ):
        raise ValueError("redacted_source_reference must not expose private references")
    if CATEGORY_ROUTE_MATCH_REASON in row.reason_codes and CATEGORY_ROUTE_MISS_REASON in (
        row.reason_codes
    ):
        raise ValueError("reason_codes cannot include both category match and miss")
    if TEAM_LOAD_READY_REASON in row.reason_codes and TEAM_LOAD_OVER_CAPACITY_REASON in (
        row.reason_codes
    ):
        raise ValueError("reason_codes cannot include both ready and over capacity")


def _validate_report(report: TeamSpecialistDecisionReviewLoadRouterV2Report) -> None:
    if report.review_count != _count(len(report.assignments)):
        raise ValueError("review_count must match assignments")
    if report.specialist_team_count != _count(
        len({row.specialist_team_id for row in report.assignments}),
    ):
        raise ValueError("specialist_team_count must match assignments")
    if report.assignment_count != _count(len(report.assignments)):
        raise ValueError("assignment_count must match assignments")
    if report.blocked_count != _status_count(report.assignments, "blocked"):
        raise ValueError("blocked_count must match assignments")
    if report.watch_count != _status_count(report.assignments, "watch"):
        raise ValueError("watch_count must match assignments")
    if report.pass_count != _status_count(report.assignments, "pass"):
        raise ValueError("pass_count must match assignments")
    if report.urgent_review_count != _count(
        len(tuple(row for row in report.assignments if row.urgent_review)),
    ):
        raise ValueError("urgent_review_count must match assignments")
    if report.overloaded_team_count != _count(
        len(
            {
                row.specialist_team_id
                for row in report.assignments
                if row.team_load_ratio > ONE_RATIO
            },
        ),
    ):
        raise ValueError("overloaded_team_count must match assignments")
    if report.average_priority_score != _average_priority_score(report.assignments):
        raise ValueError("average_priority_score must match assignments")
    if report.max_team_load_ratio != _max_assignment_team_load_ratio(report.assignments):
        raise ValueError("max_team_load_ratio must match assignments")
    if report.route_status != _report_status(report.assignments):
        raise ValueError("route_status must match assignments")
    if report.reason_codes != _report_reason_codes(report.assignments):
        raise ValueError("reason_codes must match assignments")
    if report.assignments != tuple(sorted(report.assignments, key=_assignment_sort_key)):
        raise ValueError("assignments must use deterministic sequence")


def _base_priority_score_from_values(
    evidence_gap_score: Decimal,
    decision_uncertainty_score: Decimal,
    conflict_severity_score: Decimal,
    deadline_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            evidence_gap_score * EVIDENCE_GAP_WEIGHT
            + decision_uncertainty_score * DECISION_UNCERTAINTY_WEIGHT
            + conflict_severity_score * CONFLICT_SEVERITY_WEIGHT
            + deadline_pressure_score * DEADLINE_PRESSURE_WEIGHT
        ).quantize(RATIO_QUANTUM)


def _status_validation_config() -> TeamSpecialistDecisionReviewLoadRouterV2Config:
    return TeamSpecialistDecisionReviewLoadRouterV2Config(
        category_routes=(
            TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute(
                category_id="validation.category",
                specialist_team_id="validation-specialist",
            ),
        ),
    )


def _assignment_sort_key(
    row: TeamSpecialistDecisionReviewLoadRouterV2Assignment,
) -> tuple[int, int, Decimal, datetime, str]:
    return (
        -_status_rank(row.route_status),
        -int(row.urgent_review),
        -row.priority_score,
        row.queued_at,
        row.review_item_id,
    )


def _status_rank(status: str) -> int:
    if status == "blocked":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...],
    status: str,
) -> Decimal:
    return _count(len(tuple(row for row in assignments if row.route_status == status)))


def _average_priority_score(
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...],
) -> Decimal:
    if not assignments:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.priority_score for row in assignments), ZERO_RATIO)
            / Decimal(len(assignments))
        ).quantize(RATIO_QUANTUM)


def _max_team_load_ratio(
    loads: tuple[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad, ...],
) -> Decimal:
    if not loads:
        return ZERO_RATIO
    return max(_load_ratio(row.assigned_review_count, row.capacity_review_count) for row in loads)


def _max_assignment_team_load_ratio(
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...],
) -> Decimal:
    if not assignments:
        return ZERO_RATIO
    return max(row.team_load_ratio for row in assignments)


def _overloaded_assignment_team_count(
    assignments: tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...],
) -> Decimal:
    return _count(
        len(
            {
                row.specialist_team_id
                for row in assignments
                if row.team_load_ratio > ONE_RATIO
            },
        ),
    )


def _overloaded_team_count(
    loads: tuple[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad, ...],
) -> Decimal:
    return _count(
        len(
            tuple(
                row
                for row in loads
                if _load_ratio(row.assigned_review_count, row.capacity_review_count)
                > ONE_RATIO
            ),
        ),
    )


def _normalize_category_routes(
    value: object,
) -> tuple[TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute, ...]:
    if type(value) is not tuple:
        raise ValueError("category_routes must be a tuple")
    if not value:
        raise ValueError("category_routes must not be empty")
    seen_categories: set[str] = set()
    routes: list[TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute] = []
    for row in value:
        if type(row) is not TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute:
            raise ValueError(
                "category_routes must contain "
                "TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute values",
            )
        require_paper_only_flags("category route", row)
        if row.category_id in seen_categories:
            raise ValueError("category_routes must not contain duplicate categories")
        routes.append(row)
        seen_categories.add(row.category_id)
    return tuple(sorted(routes, key=lambda row: (row.category_id, row.specialist_team_id)))


def _normalize_review_items(
    value: object,
) -> tuple[TeamSpecialistDecisionReviewLoadRouterV2Review, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("review_items must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamSpecialistDecisionReviewLoadRouterV2Review:
            raise ValueError(
                "review_items must contain "
                "TeamSpecialistDecisionReviewLoadRouterV2Review values",
            )
        require_paper_only_flags("decision review item", row)
    return rows


def _normalize_team_loads(
    value: object,
) -> tuple[TeamSpecialistDecisionReviewLoadRouterV2TeamLoad, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_loads must be a list or tuple")
    rows = tuple(value)
    seen_teams: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistDecisionReviewLoadRouterV2TeamLoad:
            raise ValueError(
                "team_loads must contain "
                "TeamSpecialistDecisionReviewLoadRouterV2TeamLoad values",
            )
        require_paper_only_flags("decision review team load", row)
        if row.specialist_team_id in seen_teams:
            raise ValueError("team_loads must not contain duplicate specialist teams")
        seen_teams.add(row.specialist_team_id)
    return rows


def _normalize_assignments(
    value: object,
) -> tuple[TeamSpecialistDecisionReviewLoadRouterV2Assignment, ...]:
    if type(value) is not tuple:
        raise ValueError("assignments must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistDecisionReviewLoadRouterV2Assignment:
            raise ValueError(
                "assignments must contain "
                "TeamSpecialistDecisionReviewLoadRouterV2Assignment values",
            )
        _validate_assignment(row)
        require_paper_only_flags("assignment", row)
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    expected = tuple(code for code in allowed_reason_codes if code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _normalize_nonnegative_ratio_like(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if value not in TEAM_SPECIALIST_DECISION_REVIEW_LOAD_ROUTER_V2_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _redact_source_reference(value: str) -> str:
    if _is_private_reference(value):
        return PRIVATE_REFERENCE_MARKER
    return value


def _is_private_reference(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(SAFE_REFERENCE_PREFIXES):
        return False
    return any(fragment in lowered for fragment in PRIVATE_REFERENCE_FRAGMENTS)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            if any(term in key.lower() for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_public_numeric_values(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must serialize numeric values as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(label, item)


def _require_public_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in {label}")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _assignment_derived_validation_digest(
    row: TeamSpecialistDecisionReviewLoadRouterV2Assignment,
) -> str:
    return _public_digest(_assignment_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: TeamSpecialistDecisionReviewLoadRouterV2Report,
) -> str:
    return _public_digest(_report_public_payload_for_digest(report))


def _assignment_public_payload_for_digest(
    row: TeamSpecialistDecisionReviewLoadRouterV2Assignment,
) -> dict[str, Any]:
    payload = json_ready_no_floats(row)
    if not isinstance(payload, dict):
        raise ValueError("assignment digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: TeamSpecialistDecisionReviewLoadRouterV2Report,
) -> dict[str, Any]:
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _validate_assignment_public_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    if digest_value != _public_digest(digest_payload):
        raise ValueError("derived_validation_digest must match assignment public payload")


def _public_report_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _public_digest(digest_payload)


def _public_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_public_numeric_values("digest payload", payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_DECISION_REVIEW_LOAD_ROUTER_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_DECISION_REVIEW_LOAD_ROUTER_V2_STATUSES",
    "CATEGORY_ROUTE_MATCH_REASON",
    "CATEGORY_ROUTE_MISS_REASON",
    "EVIDENCE_GAP_REASON",
    "DECISION_UNCERTAINTY_REASON",
    "CONFLICT_SEVERITY_REASON",
    "DEADLINE_PRESSURE_REASON",
    "TEAM_LOAD_READY_REASON",
    "TEAM_LOAD_OVER_CAPACITY_REASON",
    "URGENT_REVIEW_REASON",
    "DECISION_REVIEW_PASS_REASON",
    "REPORT_BLOCKED_REASON",
    "REPORT_WATCH_REASON",
    "EMPTY_REVIEW_REASON",
    "TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute",
    "TeamSpecialistDecisionReviewLoadRouterV2Config",
    "TeamSpecialistDecisionReviewLoadRouterV2TeamLoad",
    "TeamSpecialistDecisionReviewLoadRouterV2Review",
    "TeamSpecialistDecisionReviewLoadRouterV2Assignment",
    "TeamSpecialistDecisionReviewLoadRouterV2Report",
    "build_team_specialist_decision_review_load_router_v2_report",
    "team_specialist_decision_review_load_router_v2_payload",
    "validate_team_specialist_decision_review_load_router_v2_public_payload",
)
