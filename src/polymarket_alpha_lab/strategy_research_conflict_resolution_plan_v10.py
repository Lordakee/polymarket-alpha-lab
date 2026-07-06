"""Pure research conflict resolution plan v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RESEARCH_CONFLICT_RESOLUTION_PLAN_V10_VERSION = (
    "strategy-research-conflict-resolution-plan-v10"
)

COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
CAPACITY_CONSTRAINT_THRESHOLD = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_DISAGREEMENT_STATUSES = ("aligned", "minor", "material", "critical")
MODEL_DISAGREEMENT_STATUSES = ("aligned", "minor", "material", "critical")
RESOLUTION_RISK_TIERS = ("low", "medium", "high")
MISSING_DATA_TYPES = (
    "primary_source",
    "resolution_rule",
    "model_trace",
    "timestamp",
)
CONFLICT_PLAN_STATUSES = ("clear", "review", "escalate")
STEP_STATUSES = ("recorded", "planned", "escalation")
RESEARCH_ACTIONS = (
    "record_no_conflict_review",
    "capture_current_research_evidence",
    "reconcile_source_disagreement",
    "review_model_disagreement",
    "collect_missing_resolution_data",
    "escalate_to_research_lead",
)
REASON_CODES = (
    "strategy_research_conflict_resolution_plan_v10_no_conflict",
    "strategy_research_conflict_resolution_plan_v10_source_conflict",
    "strategy_research_conflict_resolution_plan_v10_model_conflict",
    "strategy_research_conflict_resolution_plan_v10_medium_resolution_risk",
    "strategy_research_conflict_resolution_plan_v10_high_resolution_risk",
    "strategy_research_conflict_resolution_plan_v10_missing_primary_source",
    "strategy_research_conflict_resolution_plan_v10_missing_resolution_rule",
    "strategy_research_conflict_resolution_plan_v10_missing_model_trace",
    "strategy_research_conflict_resolution_plan_v10_missing_timestamp",
    "strategy_research_conflict_resolution_plan_v10_capacity_constrained",
)
MISSING_DATA_REASON_CODES = {
    "primary_source": "strategy_research_conflict_resolution_plan_v10_missing_primary_source",
    "resolution_rule": "strategy_research_conflict_resolution_plan_v10_missing_resolution_rule",
    "model_trace": "strategy_research_conflict_resolution_plan_v10_missing_model_trace",
    "timestamp": "strategy_research_conflict_resolution_plan_v10_missing_timestamp",
}

__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_CONFLICT_RESOLUTION_PLAN_V10_VERSION",
    "StrategyResearchConflictResolutionPlanV10Payload",
    "StrategyResearchConflictResolutionPlanV10Request",
    "StrategyResearchConflictResolutionStepV10",
    "StrategyResearchConflictResolutionPlanV10",
    "build_strategy_research_conflict_resolution_plan_v10",
    "build_strategy_research_conflict_resolution_plan_v10_from_request",
    "strategy_research_conflict_resolution_plan_v10_payload",
)


@dataclass(frozen=True)
class StrategyResearchConflictResolutionPlanV10Request:
    market_id: str
    source_disagreement_status: str
    model_disagreement_status: str
    resolution_risk_tier: str
    missing_data_types: tuple[str, ...]
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "source_disagreement_status",
            _require_member(
                "source_disagreement_status",
                self.source_disagreement_status,
                SOURCE_DISAGREEMENT_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "model_disagreement_status",
            _require_member(
                "model_disagreement_status",
                self.model_disagreement_status,
                MODEL_DISAGREEMENT_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "resolution_risk_tier",
            _require_member(
                "resolution_risk_tier",
                self.resolution_risk_tier,
                RESOLUTION_RISK_TIERS,
            ),
        )
        object.__setattr__(
            self,
            "missing_data_types",
            _normalize_missing_data_types(self.missing_data_types),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_count(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_score("team_capacity_score", self.team_capacity_score),
        )
        require_paper_only_flags("StrategyResearchConflictResolutionPlanV10Request", self)


@dataclass(frozen=True)
class StrategyResearchConflictResolutionStepV10:
    step_rank: Decimal
    research_action: str
    deadline_minutes: Decimal
    step_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_rank", _normalize_positive_count("step_rank", self.step_rank))
        object.__setattr__(
            self,
            "research_action",
            _require_member("research_action", self.research_action, RESEARCH_ACTIONS),
        )
        object.__setattr__(
            self,
            "deadline_minutes",
            _normalize_nonnegative_count("deadline_minutes", self.deadline_minutes),
        )
        object.__setattr__(
            self,
            "step_status",
            _require_member("step_status", self.step_status, STEP_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_step(self)
        require_paper_only_flags("StrategyResearchConflictResolutionStepV10", self)


@dataclass(frozen=True)
class StrategyResearchConflictResolutionPlanV10Payload:
    market_id: str
    source_disagreement_status: str
    model_disagreement_status: str
    resolution_risk_tier: str
    missing_data_types: tuple[str, ...]
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    resolution_step_count: Decimal
    escalation_required: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "source_disagreement_status",
            _require_member(
                "source_disagreement_status",
                self.source_disagreement_status,
                SOURCE_DISAGREEMENT_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "model_disagreement_status",
            _require_member(
                "model_disagreement_status",
                self.model_disagreement_status,
                MODEL_DISAGREEMENT_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "resolution_risk_tier",
            _require_member(
                "resolution_risk_tier",
                self.resolution_risk_tier,
                RESOLUTION_RISK_TIERS,
            ),
        )
        object.__setattr__(
            self,
            "missing_data_types",
            _normalize_missing_data_types(self.missing_data_types),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_count(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_score("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "resolution_step_count",
            _normalize_nonnegative_count("resolution_step_count", self.resolution_step_count),
        )
        if type(self.escalation_required) is not bool:
            raise ValueError("escalation_required must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("StrategyResearchConflictResolutionPlanV10Payload", self)


@dataclass(frozen=True)
class StrategyResearchConflictResolutionPlanV10:
    plan_version: str
    market_id: str
    conflict_plan_status: str
    resolution_steps: tuple[StrategyResearchConflictResolutionStepV10, ...]
    escalation_required: bool
    reason_codes: tuple[str, ...]
    payload: StrategyResearchConflictResolutionPlanV10Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_version", _require_canonical_string("plan_version", self.plan_version))
        if self.plan_version != DEFAULT_STRATEGY_RESEARCH_CONFLICT_RESOLUTION_PLAN_V10_VERSION:
            raise ValueError("plan_version must be supported")
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "conflict_plan_status",
            _require_member(
                "conflict_plan_status",
                self.conflict_plan_status,
                CONFLICT_PLAN_STATUSES,
            ),
        )
        object.__setattr__(self, "resolution_steps", _normalize_steps(self.resolution_steps))
        if type(self.escalation_required) is not bool:
            raise ValueError("escalation_required must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if type(self.payload) is not StrategyResearchConflictResolutionPlanV10Payload:
            raise ValueError("payload must be a StrategyResearchConflictResolutionPlanV10Payload")
        require_paper_only_flags("payload", self.payload)
        _validate_plan(self)
        reject_unsafe_surface_fields("strategy research conflict resolution plan v10", self)
        require_paper_only_flags("StrategyResearchConflictResolutionPlanV10", self)


def build_strategy_research_conflict_resolution_plan_v10(
    *,
    market_id: str,
    source_disagreement_status: str,
    model_disagreement_status: str,
    resolution_risk_tier: str,
    missing_data_types: tuple[str, ...] | list[str],
    time_to_resolution_minutes: Decimal,
    team_capacity_score: Decimal,
) -> StrategyResearchConflictResolutionPlanV10:
    request = StrategyResearchConflictResolutionPlanV10Request(
        market_id=market_id,
        source_disagreement_status=source_disagreement_status,
        model_disagreement_status=model_disagreement_status,
        resolution_risk_tier=resolution_risk_tier,
        missing_data_types=tuple(missing_data_types),
        time_to_resolution_minutes=time_to_resolution_minutes,
        team_capacity_score=team_capacity_score,
    )
    return build_strategy_research_conflict_resolution_plan_v10_from_request(request)


def build_strategy_research_conflict_resolution_plan_v10_from_request(
    request: StrategyResearchConflictResolutionPlanV10Request,
) -> StrategyResearchConflictResolutionPlanV10:
    if type(request) is not StrategyResearchConflictResolutionPlanV10Request:
        raise ValueError("request must be a StrategyResearchConflictResolutionPlanV10Request")
    require_paper_only_flags("request", request)
    reason_codes = _plan_reason_codes(request)
    escalation_required = _escalation_required(request)
    status = _conflict_plan_status(reason_codes, escalation_required)
    steps = _resolution_steps(request, reason_codes, escalation_required)
    payload = StrategyResearchConflictResolutionPlanV10Payload(
        market_id=request.market_id,
        source_disagreement_status=request.source_disagreement_status,
        model_disagreement_status=request.model_disagreement_status,
        resolution_risk_tier=request.resolution_risk_tier,
        missing_data_types=request.missing_data_types,
        time_to_resolution_minutes=request.time_to_resolution_minutes,
        team_capacity_score=request.team_capacity_score,
        resolution_step_count=_count(len(steps)),
        escalation_required=escalation_required,
        reason_codes=reason_codes,
    )
    return StrategyResearchConflictResolutionPlanV10(
        plan_version=DEFAULT_STRATEGY_RESEARCH_CONFLICT_RESOLUTION_PLAN_V10_VERSION,
        market_id=request.market_id,
        conflict_plan_status=status,
        resolution_steps=steps,
        escalation_required=escalation_required,
        reason_codes=reason_codes,
        payload=payload,
    )


def strategy_research_conflict_resolution_plan_v10_payload(
    report: StrategyResearchConflictResolutionPlanV10,
) -> dict[str, Any]:
    if type(report) is not StrategyResearchConflictResolutionPlanV10:
        raise ValueError("report must be a StrategyResearchConflictResolutionPlanV10")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy research conflict resolution plan v10", report)
    return json_ready_no_floats(report)


def _plan_reason_codes(
    request: StrategyResearchConflictResolutionPlanV10Request,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if request.source_disagreement_status != "aligned":
        reason_codes.append("strategy_research_conflict_resolution_plan_v10_source_conflict")
    if request.model_disagreement_status != "aligned":
        reason_codes.append("strategy_research_conflict_resolution_plan_v10_model_conflict")
    if request.resolution_risk_tier == "medium":
        reason_codes.append("strategy_research_conflict_resolution_plan_v10_medium_resolution_risk")
    if request.resolution_risk_tier == "high":
        reason_codes.append("strategy_research_conflict_resolution_plan_v10_high_resolution_risk")
    reason_codes.extend(MISSING_DATA_REASON_CODES[item] for item in request.missing_data_types)
    if request.team_capacity_score < CAPACITY_CONSTRAINT_THRESHOLD:
        reason_codes.append("strategy_research_conflict_resolution_plan_v10_capacity_constrained")
    if not reason_codes:
        reason_codes.append("strategy_research_conflict_resolution_plan_v10_no_conflict")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _escalation_required(request: StrategyResearchConflictResolutionPlanV10Request) -> bool:
    return (
        request.source_disagreement_status == "critical"
        or request.model_disagreement_status in ("material", "critical")
        or request.resolution_risk_tier == "high"
        or request.team_capacity_score < CAPACITY_CONSTRAINT_THRESHOLD
    )


def _conflict_plan_status(
    reason_codes: tuple[str, ...],
    escalation_required: bool,
) -> str:
    if reason_codes == ("strategy_research_conflict_resolution_plan_v10_no_conflict",):
        return "clear"
    if escalation_required:
        return "escalate"
    return "review"


def _resolution_steps(
    request: StrategyResearchConflictResolutionPlanV10Request,
    reason_codes: tuple[str, ...],
    escalation_required: bool,
) -> tuple[StrategyResearchConflictResolutionStepV10, ...]:
    if reason_codes == ("strategy_research_conflict_resolution_plan_v10_no_conflict",):
        return (
            StrategyResearchConflictResolutionStepV10(
                step_rank=_count(1),
                research_action="record_no_conflict_review",
                deadline_minutes=request.time_to_resolution_minutes,
                step_status="recorded",
                reason_codes=reason_codes,
            ),
        )

    steps: list[StrategyResearchConflictResolutionStepV10] = [
        StrategyResearchConflictResolutionStepV10(
            step_rank=_count(1),
            research_action="capture_current_research_evidence",
            deadline_minutes=ZERO_COUNT,
            step_status="planned",
            reason_codes=reason_codes,
        ),
    ]
    if request.source_disagreement_status != "aligned":
        steps.append(
            StrategyResearchConflictResolutionStepV10(
                step_rank=_count(len(steps) + 1),
                research_action="reconcile_source_disagreement",
                deadline_minutes=_deadline(Decimal("15"), request.time_to_resolution_minutes),
                step_status="planned",
                reason_codes=(
                    "strategy_research_conflict_resolution_plan_v10_source_conflict",
                ),
            ),
        )
    if request.model_disagreement_status != "aligned":
        steps.append(
            StrategyResearchConflictResolutionStepV10(
                step_rank=_count(len(steps) + 1),
                research_action="review_model_disagreement",
                deadline_minutes=_deadline(Decimal("30"), request.time_to_resolution_minutes),
                step_status="planned",
                reason_codes=(
                    "strategy_research_conflict_resolution_plan_v10_model_conflict",
                ),
            ),
        )
    if request.missing_data_types:
        steps.append(
            StrategyResearchConflictResolutionStepV10(
                step_rank=_count(len(steps) + 1),
                research_action="collect_missing_resolution_data",
                deadline_minutes=request.time_to_resolution_minutes,
                step_status="planned",
                reason_codes=tuple(
                    MISSING_DATA_REASON_CODES[item] for item in request.missing_data_types
                ),
            ),
        )
    if escalation_required:
        steps.append(
            StrategyResearchConflictResolutionStepV10(
                step_rank=_count(len(steps) + 1),
                research_action="escalate_to_research_lead",
                deadline_minutes=request.time_to_resolution_minutes,
                step_status="escalation",
                reason_codes=tuple(
                    code
                    for code in reason_codes
                    if code
                    in (
                        "strategy_research_conflict_resolution_plan_v10_model_conflict",
                        "strategy_research_conflict_resolution_plan_v10_high_resolution_risk",
                        "strategy_research_conflict_resolution_plan_v10_capacity_constrained",
                    )
                ),
            ),
        )
    return tuple(steps)


def _deadline(base_minutes: Decimal, time_to_resolution_minutes: Decimal) -> Decimal:
    if base_minutes <= time_to_resolution_minutes:
        return base_minutes
    return time_to_resolution_minutes


def _normalize_steps(
    value: object,
) -> tuple[StrategyResearchConflictResolutionStepV10, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("resolution_steps must be a list or tuple")
    steps = tuple(value)
    if not steps:
        raise ValueError("resolution_steps must not be empty")
    expected_ranks = tuple(_count(index + 1) for index in range(len(steps)))
    if tuple(step.step_rank for step in steps) != expected_ranks:
        raise ValueError("resolution_steps must use contiguous step_rank values")
    for step in steps:
        if type(step) is not StrategyResearchConflictResolutionStepV10:
            raise ValueError("resolution_steps must contain StrategyResearchConflictResolutionStepV10 values")
        require_paper_only_flags("step", step)
    return steps


def _validate_step(step: StrategyResearchConflictResolutionStepV10) -> None:
    if step.research_action == "record_no_conflict_review" and step.step_status != "recorded":
        raise ValueError("step_status must match research_action")
    if step.research_action == "escalate_to_research_lead" and step.step_status != "escalation":
        raise ValueError("step_status must match research_action")
    if step.research_action not in (
        "record_no_conflict_review",
        "escalate_to_research_lead",
    ) and step.step_status != "planned":
        raise ValueError("step_status must match research_action")


def _validate_plan(report: StrategyResearchConflictResolutionPlanV10) -> None:
    if report.market_id != report.payload.market_id:
        raise ValueError("payload must match market_id")
    if report.escalation_required != report.payload.escalation_required:
        raise ValueError("payload must match escalation_required")
    if report.reason_codes != report.payload.reason_codes:
        raise ValueError("payload must match reason_codes")
    if report.payload.resolution_step_count != _count(len(report.resolution_steps)):
        raise ValueError("payload must match resolution_steps")
    expected_status = _conflict_plan_status(report.reason_codes, report.escalation_required)
    if report.conflict_plan_status != expected_status:
        raise ValueError("conflict_plan_status must match reason_codes")
    if report.escalation_required != any(
        step.step_status == "escalation" for step in report.resolution_steps
    ):
        raise ValueError("escalation_required must match resolution_steps")


def _normalize_missing_data_types(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("missing_data_types must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_member("missing_data_types", item, MISSING_DATA_TYPES)
    if len(set(items)) != len(items):
        raise ValueError("missing_data_types must not contain duplicates")
    ordered_items = tuple(item for item in MISSING_DATA_TYPES if item in items)
    if items != ordered_items:
        raise ValueError("missing_data_types must use stable sort")
    return ordered_items


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_member(name, reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must not contain duplicates")
    if reason_codes != tuple(code for code in REASON_CODES if code in reason_codes):
        raise ValueError(f"{name} must use stable sort")
    return reason_codes


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    return value


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be supported")
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return _quantize_count(name, decimal_value)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_count(name, decimal_value)


def _normalize_score(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_SCORE or decimal_value > ONE_SCORE:
        raise ValueError(f"{name} must be between zero and one")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(SCORE_QUANTUM)


def _quantize_count(name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{name} must be an integer Decimal")
    return quantized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)
