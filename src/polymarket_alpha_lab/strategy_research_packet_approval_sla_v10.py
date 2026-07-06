"""Pure paper-only research packet approval SLA evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_APPROVAL_SLA_V10_CONFIG_VERSION = (
    "research-packet-approval-sla-v10"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")

BRIEF_STATUSES = (
    "draft",
    "researching",
    "ready",
    "in_review",
    "approved",
    "blocked",
    "archived",
)
REVIEWABLE_BRIEF_STATUSES = ("ready", "in_review", "approved")
BLOCKED_BRIEF_STATUSES = ("blocked", "archived")
APPROVAL_SLA_STATUSES = (
    "not_required",
    "within_sla",
    "watch",
    "breached",
    "blocked",
)
APPROVAL_PRIORITIES = ("none", "normal", "high", "urgent", "blocked")
REASON_CODES = (
    "review_required",
    "review_not_required",
    "brief_ready",
    "brief_in_progress",
    "brief_approved",
    "brief_blocked_status",
    "decision_ready",
    "decision_not_ready",
    "capacity_available",
    "capacity_constrained",
    "no_blocking_reasons",
    "blocking_reasons_present",
    "sla_not_required",
    "sla_within",
    "sla_watch",
    "sla_breached",
    "sla_blocked",
    "resolution_window_immediate",
    "resolution_window_near",
    "resolution_window_normal",
    "approval_priority_none",
    "approval_priority_normal",
    "approval_priority_high",
    "approval_priority_urgent",
    "approval_priority_blocked",
)


@dataclass(frozen=True)
class ResearchPacketApprovalSlaV10Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_APPROVAL_SLA_V10_CONFIG_VERSION
    approval_sla_minutes: Decimal = Decimal("120.000000")
    watch_queue_age_minutes: Decimal = Decimal("90.000000")
    immediate_resolution_minutes: Decimal = Decimal("60.000000")
    near_resolution_minutes: Decimal = Decimal("600.000000")
    minimum_decision_readiness: Decimal = Decimal("0.700000")
    minimum_capacity_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchPacketApprovalSlaV10Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "approval_sla_minutes",
            "immediate_resolution_minutes",
            "near_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "watch_queue_age_minutes",
            _normalize_nonnegative_decimal(
                "watch_queue_age_minutes",
                self.watch_queue_age_minutes,
            ),
        )
        for field_name in (
            "minimum_decision_readiness",
            "minimum_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_queue_age_minutes >= self.approval_sla_minutes:
            raise ValueError("watch_queue_age_minutes must be below approval_sla_minutes")
        if self.immediate_resolution_minutes >= self.near_resolution_minutes:
            raise ValueError(
                "immediate_resolution_minutes must be below near_resolution_minutes",
            )
        reject_unsafe_surface_fields("ResearchPacketApprovalSlaV10Config", self)
        require_paper_only_flags("ResearchPacketApprovalSlaV10Config", self)


@dataclass(frozen=True)
class ResearchPacketApprovalSlaV10Input:
    market_id: str
    brief_status: str
    review_required: bool
    review_queue_age_minutes: Decimal
    time_to_resolution_minutes: Decimal
    decision_readiness: Decimal
    team_capacity_score: Decimal
    blocking_reason_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("packet", self, ResearchPacketApprovalSlaV10Input)
        _require_canonical_string("market_id", self.market_id)
        _require_choice("brief_status", self.brief_status, BRIEF_STATUSES)
        _require_bool("review_required", self.review_required)
        for field_name in (
            "review_queue_age_minutes",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("decision_readiness", "team_capacity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocking_reason_count",
            _normalize_whole_decimal("blocking_reason_count", self.blocking_reason_count),
        )
        reject_unsafe_surface_fields("ResearchPacketApprovalSlaV10Input", self)
        require_paper_only_flags("ResearchPacketApprovalSlaV10Input", self)


@dataclass(frozen=True)
class ResearchPacketApprovalSlaV10Report:
    config_version: str
    market_id: str
    brief_status: str
    review_required: bool
    review_queue_age_minutes: Decimal
    time_to_resolution_minutes: Decimal
    decision_readiness: Decimal
    team_capacity_score: Decimal
    blocking_reason_count: Decimal
    approval_sla_status: str
    approval_priority: str
    escalation_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketApprovalSlaV10Report)
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_id", self.market_id)
        _require_choice("brief_status", self.brief_status, BRIEF_STATUSES)
        _require_bool("review_required", self.review_required)
        for field_name in (
            "review_queue_age_minutes",
            "time_to_resolution_minutes",
            "escalation_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("decision_readiness", "team_capacity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocking_reason_count",
            _normalize_whole_decimal("blocking_reason_count", self.blocking_reason_count),
        )
        _require_choice(
            "approval_sla_status",
            self.approval_sla_status,
            APPROVAL_SLA_STATUSES,
        )
        _require_choice("approval_priority", self.approval_priority, APPROVAL_PRIORITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_surface(self)
        reject_unsafe_surface_fields("ResearchPacketApprovalSlaV10Report", self)
        require_paper_only_flags("ResearchPacketApprovalSlaV10Report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_approval_sla_v10_payload(self)


def evaluate_research_packet_approval_sla_v10(
    packet: ResearchPacketApprovalSlaV10Input,
    *,
    config: ResearchPacketApprovalSlaV10Config | None = None,
) -> ResearchPacketApprovalSlaV10Report:
    if type(packet) is not ResearchPacketApprovalSlaV10Input:
        raise ValueError("packet must be a ResearchPacketApprovalSlaV10Input")
    require_paper_only_flags("packet", packet)
    active_config = config or ResearchPacketApprovalSlaV10Config()
    if type(active_config) is not ResearchPacketApprovalSlaV10Config:
        raise ValueError("config must be a ResearchPacketApprovalSlaV10Config")
    require_paper_only_flags("config", active_config)

    approval_sla_status = _approval_sla_status(packet, active_config)
    approval_priority = _approval_priority(packet, approval_sla_status, active_config)
    escalation_minutes = _escalation_minutes(packet, approval_sla_status, active_config)

    return ResearchPacketApprovalSlaV10Report(
        config_version=active_config.config_version,
        market_id=packet.market_id,
        brief_status=packet.brief_status,
        review_required=packet.review_required,
        review_queue_age_minutes=packet.review_queue_age_minutes,
        time_to_resolution_minutes=packet.time_to_resolution_minutes,
        decision_readiness=packet.decision_readiness,
        team_capacity_score=packet.team_capacity_score,
        blocking_reason_count=packet.blocking_reason_count,
        approval_sla_status=approval_sla_status,
        approval_priority=approval_priority,
        escalation_minutes=escalation_minutes,
        reason_codes=_reason_codes(
            packet=packet,
            approval_sla_status=approval_sla_status,
            approval_priority=approval_priority,
            config=active_config,
        ),
    )


def research_packet_approval_sla_v10_payload(
    report: ResearchPacketApprovalSlaV10Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketApprovalSlaV10Report:
        raise ValueError("report must be a ResearchPacketApprovalSlaV10Report")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("research packet approval sla v10", report)
    payload = {
        "config_version": report.config_version,
        "market_id": report.market_id,
        "brief_status": report.brief_status,
        "review_required": report.review_required,
        "review_queue_age_minutes": report.review_queue_age_minutes,
        "time_to_resolution_minutes": report.time_to_resolution_minutes,
        "decision_readiness": report.decision_readiness,
        "team_capacity_score": report.team_capacity_score,
        "blocking_reason_count": report.blocking_reason_count,
        "approval_sla_status": report.approval_sla_status,
        "approval_priority": report.approval_priority,
        "escalation_minutes": report.escalation_minutes,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields("research packet approval sla v10 payload", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _approval_sla_status(
    packet: ResearchPacketApprovalSlaV10Input,
    config: ResearchPacketApprovalSlaV10Config,
) -> str:
    if not packet.review_required:
        return "not_required"
    if _is_blocked(packet, config):
        return "blocked"
    if packet.review_queue_age_minutes >= config.approval_sla_minutes:
        return "breached"
    if packet.review_queue_age_minutes >= config.watch_queue_age_minutes:
        return "watch"
    return "within_sla"


def _approval_priority(
    packet: ResearchPacketApprovalSlaV10Input,
    approval_sla_status: str,
    config: ResearchPacketApprovalSlaV10Config,
) -> str:
    if approval_sla_status == "not_required":
        return "none"
    if approval_sla_status == "blocked":
        return "blocked"
    if (
        approval_sla_status == "breached"
        or packet.time_to_resolution_minutes <= config.immediate_resolution_minutes
    ):
        return "urgent"
    if (
        approval_sla_status == "watch"
        or packet.time_to_resolution_minutes <= config.near_resolution_minutes
    ):
        return "high"
    return "normal"


def _escalation_minutes(
    packet: ResearchPacketApprovalSlaV10Input,
    approval_sla_status: str,
    config: ResearchPacketApprovalSlaV10Config,
) -> Decimal:
    if approval_sla_status in ("not_required", "blocked", "breached"):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        remaining = config.approval_sla_minutes - packet.review_queue_age_minutes
    if remaining <= ZERO:
        return ZERO
    return _quantize(remaining)


def _is_blocked(
    packet: ResearchPacketApprovalSlaV10Input,
    config: ResearchPacketApprovalSlaV10Config,
) -> bool:
    return (
        packet.brief_status not in REVIEWABLE_BRIEF_STATUSES
        or packet.brief_status in BLOCKED_BRIEF_STATUSES
        or packet.decision_readiness < config.minimum_decision_readiness
        or packet.blocking_reason_count > ZERO_COUNT
    )


def _reason_codes(
    *,
    packet: ResearchPacketApprovalSlaV10Input,
    approval_sla_status: str,
    approval_priority: str,
    config: ResearchPacketApprovalSlaV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if packet.review_required:
        codes.append("review_required")
    else:
        codes.append("review_not_required")
    codes.append(_brief_reason_code(packet.brief_status))
    if packet.decision_readiness >= config.minimum_decision_readiness:
        codes.append("decision_ready")
    else:
        codes.append("decision_not_ready")
    if packet.team_capacity_score >= config.minimum_capacity_score:
        codes.append("capacity_available")
    else:
        codes.append("capacity_constrained")
    if packet.blocking_reason_count == ZERO_COUNT:
        codes.append("no_blocking_reasons")
    else:
        codes.append("blocking_reasons_present")
    codes.append(_sla_reason_code(approval_sla_status))
    codes.append(_resolution_window_reason_code(packet.time_to_resolution_minutes, config))
    codes.append(f"approval_priority_{approval_priority}")
    return _normalize_reason_codes(tuple(codes))


def _brief_reason_code(brief_status: str) -> str:
    if brief_status in ("ready", "in_review"):
        return "brief_ready"
    if brief_status == "approved":
        return "brief_approved"
    if brief_status in BLOCKED_BRIEF_STATUSES:
        return "brief_blocked_status"
    return "brief_in_progress"


def _resolution_window_reason_code(
    time_to_resolution_minutes: Decimal,
    config: ResearchPacketApprovalSlaV10Config,
) -> str:
    if time_to_resolution_minutes <= config.immediate_resolution_minutes:
        return "resolution_window_immediate"
    if time_to_resolution_minutes <= config.near_resolution_minutes:
        return "resolution_window_near"
    return "resolution_window_normal"


def _sla_reason_code(approval_sla_status: str) -> str:
    if approval_sla_status == "within_sla":
        return "sla_within"
    return f"sla_{approval_sla_status}"


def _validate_report_surface(report: ResearchPacketApprovalSlaV10Report) -> None:
    if _sla_reason_code(report.approval_sla_status) not in report.reason_codes:
        raise ValueError("reason_codes must include approval_sla_status")
    if f"approval_priority_{report.approval_priority}" not in report.reason_codes:
        raise ValueError("reason_codes must include approval_priority")
    if report.approval_sla_status == "not_required" and report.review_required:
        raise ValueError("not_required status requires review_required false")
    if report.approval_priority == "none" and report.approval_sla_status != "not_required":
        raise ValueError("none priority requires not_required status")
    if report.approval_priority == "blocked" and report.approval_sla_status != "blocked":
        raise ValueError("blocked priority requires blocked status")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    quantized = _quantize(normalized)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return quantized


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal = _require_decimal(field_name, value)
    quantized = decimal.quantize(COUNT_QUANTUM)
    if decimal != quantized:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_choice(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "APPROVAL_PRIORITIES",
    "APPROVAL_SLA_STATUSES",
    "BRIEF_STATUSES",
    "DEFAULT_RESEARCH_PACKET_APPROVAL_SLA_V10_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchPacketApprovalSlaV10Config",
    "ResearchPacketApprovalSlaV10Input",
    "ResearchPacketApprovalSlaV10Report",
    "evaluate_research_packet_approval_sla_v10",
    "research_packet_approval_sla_v10_payload",
)
