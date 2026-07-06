"""Pure read-only team research queue router v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


QUEUE_ROUTER_V10_CONFIG_VERSION = "strategy-team-research-queue-router-v10"

QUEUE_LANES = (
    "blocked_refresh",
    "human_review",
    "expedited_research",
    "standard_research",
    "long_term_backlog",
)
EDGE_TIERS = ("low", "medium", "high", "critical")
FRESHNESS_STATUSES = ("fresh", "aging", "stale", "blocked")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_PRIORITY = Decimal("100.000000")
LOW_TRUST_THRESHOLD = Decimal("0.550000")
HIGH_URGENCY_THRESHOLD = Decimal("0.850000")
LONG_TERM_BACKLOG_PRIORITY_THRESHOLD = Decimal("25.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EDGE_TIER_BASE_PRIORITY = {
    "low": Decimal("10.000000"),
    "medium": Decimal("35.000000"),
    "high": Decimal("55.000000"),
    "critical": Decimal("75.000000"),
}
FRESHNESS_PRIORITY_ADJUSTMENT = {
    "fresh": Decimal("0.000000"),
    "aging": Decimal("10.000000"),
    "stale": Decimal("25.000000"),
    "blocked": Decimal("50.000000"),
}

LANE_SLA_MINUTES = {
    "blocked_refresh": Decimal("30"),
    "human_review": Decimal("60"),
    "expedited_research": Decimal("120"),
    "standard_research": Decimal("480"),
    "long_term_backlog": Decimal("1440"),
}


@dataclass(frozen=True)
class StrategyTeamResearchQueueRouterV10Candidate:
    category: str
    subcategory: str
    edge_tier: str
    freshness_status: str
    team_capacity: Decimal
    team_trust_score: Decimal
    resolution_urgency: Decimal
    human_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        _require_canonical_string("subcategory", self.subcategory)
        _require_member("edge_tier", self.edge_tier, EDGE_TIERS)
        _require_member("freshness_status", self.freshness_status, FRESHNESS_STATUSES)
        for field_name in (
            "team_capacity",
            "team_trust_score",
            "resolution_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_bool("human_review_required", self.human_review_required)
        require_paper_only_flags("strategy team research queue router v10 candidate", self)


@dataclass(frozen=True)
class StrategyTeamResearchQueueRouterV10Decision:
    category: str
    subcategory: str
    edge_tier: str
    freshness_status: str
    team_capacity: Decimal
    team_trust_score: Decimal
    resolution_urgency: Decimal
    human_review_required: bool
    queue_lane: str
    assigned_priority: Decimal
    sla_minutes: Decimal
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        _require_canonical_string("subcategory", self.subcategory)
        _require_member("edge_tier", self.edge_tier, EDGE_TIERS)
        _require_member("freshness_status", self.freshness_status, FRESHNESS_STATUSES)
        for field_name in (
            "team_capacity",
            "team_trust_score",
            "resolution_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_bool("human_review_required", self.human_review_required)
        _require_member("queue_lane", self.queue_lane, QUEUE_LANES)
        object.__setattr__(
            self,
            "assigned_priority",
            _normalize_priority("assigned_priority", self.assigned_priority),
        )
        object.__setattr__(
            self,
            "sla_minutes",
            _normalize_sla_minutes("sla_minutes", self.sla_minutes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload("payload", self.payload))
        _validate_decision(self)
        require_paper_only_flags("strategy team research queue router v10 decision", self)


def route_strategy_team_research_queue_router_v10(
    candidate: StrategyTeamResearchQueueRouterV10Candidate,
) -> StrategyTeamResearchQueueRouterV10Decision:
    if type(candidate) is not StrategyTeamResearchQueueRouterV10Candidate:
        raise ValueError(
            "candidate must be a StrategyTeamResearchQueueRouterV10Candidate",
    )
    require_paper_only_flags("strategy team research queue router v10 candidate", candidate)

    assigned_priority, priority_was_clamped = _assigned_priority(candidate)
    queue_lane = _queue_lane(candidate, assigned_priority)
    sla_minutes = LANE_SLA_MINUTES[queue_lane]
    reason_codes = _reason_codes(
        candidate,
        queue_lane=queue_lane,
        priority_was_clamped=priority_was_clamped,
    )
    payload = _decision_payload(
        candidate,
        queue_lane=queue_lane,
        assigned_priority=assigned_priority,
        sla_minutes=sla_minutes,
        reason_codes=reason_codes,
    )

    return StrategyTeamResearchQueueRouterV10Decision(
        category=candidate.category,
        subcategory=candidate.subcategory,
        edge_tier=candidate.edge_tier,
        freshness_status=candidate.freshness_status,
        team_capacity=candidate.team_capacity,
        team_trust_score=candidate.team_trust_score,
        resolution_urgency=candidate.resolution_urgency,
        human_review_required=candidate.human_review_required,
        queue_lane=queue_lane,
        assigned_priority=assigned_priority,
        sla_minutes=sla_minutes,
        reason_codes=reason_codes,
        payload=payload,
    )


def strategy_team_research_queue_router_v10_payload(
    decision: StrategyTeamResearchQueueRouterV10Decision,
) -> dict[str, Any]:
    if type(decision) is not StrategyTeamResearchQueueRouterV10Decision:
        raise ValueError("decision must be a StrategyTeamResearchQueueRouterV10Decision")
    require_paper_only_flags("strategy team research queue router v10 decision", decision)
    payload = json_ready_no_floats(decision.payload)
    if type(payload) is not dict:
        raise ValueError("decision payload must be a JSON object")
    require_paper_only_flags(
        "strategy team research queue router v10 payload",
        _PayloadFlags(payload),
    )
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _assigned_priority(
    value: StrategyTeamResearchQueueRouterV10Candidate | StrategyTeamResearchQueueRouterV10Decision,
) -> tuple[Decimal, bool]:
    with localcontext(DECIMAL_CONTEXT):
        raw_priority = EDGE_TIER_BASE_PRIORITY[value.edge_tier]
        raw_priority += FRESHNESS_PRIORITY_ADJUSTMENT[value.freshness_status]
        raw_priority += value.resolution_urgency * Decimal("30.000000")
        raw_priority += (ONE - value.team_capacity) * Decimal("20.000000")
        raw_priority += (ONE - value.team_trust_score) * Decimal("25.000000")
        if value.human_review_required:
            raw_priority += Decimal("3.000000")
    priority = _quantize(raw_priority)
    if priority > MAX_PRIORITY:
        return MAX_PRIORITY, True
    if priority < ZERO:
        return ZERO, True
    return priority, False


def _queue_lane(
    value: StrategyTeamResearchQueueRouterV10Candidate | StrategyTeamResearchQueueRouterV10Decision,
    assigned_priority: Decimal,
) -> str:
    if value.freshness_status == "blocked":
        return "blocked_refresh"
    if value.human_review_required or value.team_trust_score < LOW_TRUST_THRESHOLD:
        return "human_review"
    if value.edge_tier == "critical" or value.resolution_urgency >= HIGH_URGENCY_THRESHOLD:
        return "expedited_research"
    if assigned_priority < LONG_TERM_BACKLOG_PRIORITY_THRESHOLD:
        return "long_term_backlog"
    return "standard_research"


def _reason_codes(
    value: StrategyTeamResearchQueueRouterV10Candidate | StrategyTeamResearchQueueRouterV10Decision,
    *,
    queue_lane: str,
    priority_was_clamped: bool,
) -> tuple[str, ...]:
    reasons = [
        f"edge_tier_{value.edge_tier}",
        f"freshness_{value.freshness_status}",
    ]
    if value.human_review_required:
        reasons.append("human_review_required")
    if value.team_trust_score < LOW_TRUST_THRESHOLD:
        reasons.append("team_trust_low")
    if value.resolution_urgency >= HIGH_URGENCY_THRESHOLD:
        reasons.append("resolution_urgency_high")
    if priority_was_clamped:
        reasons.append("assigned_priority_clamped")
    reasons.append(f"queue_lane_{queue_lane}")
    return tuple(reasons)


def _decision_payload(
    value: StrategyTeamResearchQueueRouterV10Candidate | StrategyTeamResearchQueueRouterV10Decision,
    *,
    queue_lane: str,
    assigned_priority: Decimal,
    sla_minutes: Decimal,
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    payload = {
        "config_version": QUEUE_ROUTER_V10_CONFIG_VERSION,
        "category": value.category,
        "subcategory": value.subcategory,
        "edge_tier": value.edge_tier,
        "freshness_status": value.freshness_status,
        "team_capacity": str(value.team_capacity),
        "team_trust_score": str(value.team_trust_score),
        "resolution_urgency": str(value.resolution_urgency),
        "human_review_required": value.human_review_required,
        "queue_lane": queue_lane,
        "assigned_priority": str(assigned_priority),
        "sla_minutes": str(sla_minutes),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return payload


def _validate_decision(decision: StrategyTeamResearchQueueRouterV10Decision) -> None:
    expected_priority, priority_was_clamped = _assigned_priority(decision)
    if decision.assigned_priority != expected_priority:
        raise ValueError("assigned_priority must match routed candidate inputs")
    expected_lane = _queue_lane(decision, expected_priority)
    if decision.queue_lane != expected_lane:
        raise ValueError("queue_lane must match routed candidate inputs")
    expected_sla = LANE_SLA_MINUTES[expected_lane]
    if decision.sla_minutes != expected_sla:
        raise ValueError("sla_minutes must match queue_lane")
    expected_reasons = _reason_codes(
        decision,
        queue_lane=expected_lane,
        priority_was_clamped=priority_was_clamped,
    )
    if decision.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match routed candidate inputs")
    expected_payload = _decision_payload(
        decision,
        queue_lane=expected_lane,
        assigned_priority=expected_priority,
        sla_minutes=expected_sla,
        reason_codes=expected_reasons,
    )
    if decision.payload != expected_payload:
        raise ValueError("payload must match routed candidate inputs")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_priority(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > MAX_PRIORITY:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def _normalize_sla_minutes(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for item in items:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must contain unique values")
        seen.add(item)
    return items


def _normalize_payload(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    require_paper_only_flags(
        "strategy team research queue router v10 payload",
        _PayloadFlags(payload),
    )
    return payload


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must contain a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


__all__ = (
    "QUEUE_ROUTER_V10_CONFIG_VERSION",
    "StrategyTeamResearchQueueRouterV10Candidate",
    "StrategyTeamResearchQueueRouterV10Decision",
    "route_strategy_team_research_queue_router_v10",
    "strategy_team_research_queue_router_v10_payload",
)
