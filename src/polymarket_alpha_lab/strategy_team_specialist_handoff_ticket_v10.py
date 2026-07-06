"""Paper-only readonly team specialist handoff ticket."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HIGH_URGENCY_THRESHOLD = Decimal("0.750000")
STANDARD_URGENCY_THRESHOLD = Decimal("0.500000")
BLOCKED_SLA_MINUTES = Decimal("15.000000")
EXPEDITED_SLA_MINUTES = Decimal("30.000000")
RESEARCH_SLA_MINUTES = Decimal("120.000000")
STANDARD_SLA_MINUTES = Decimal("240.000000")
SOURCE_QUORUM_STATUSES = ("met", "partial", "missing")
HANDOFF_STATUSES = ("ready", "research_required", "expedited", "blocked")
BASE_REQUIRED_SECTIONS = (
    "market_context",
    "handoff_reason",
    "source_quorum_status",
    "sla_and_deadline",
)
FINAL_REQUIRED_SECTION = "specialist_decision_request"
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "sign",
    "exchange_mutation",
    "live trading",
    "trade execution",
    "order placement",
    "database",
    "db",
    "persist",
    "network",
    "http",
    "api key",
)


@dataclass(frozen=True)
class StrategyTeamSpecialistHandoffTicketInput:
    market_id: str
    from_team: str
    to_team: str
    handoff_reason: str
    evidence_gap_count: Decimal
    urgency_score: Decimal
    source_quorum_status: str
    deadline_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "from_team", "to_team", "handoff_reason"):
            _require_safe_canonical_string(field_name, getattr(self, field_name))
        if self.from_team == self.to_team:
            raise ValueError("from_team and to_team must differ")
        object.__setattr__(
            self,
            "evidence_gap_count",
            _normalize_whole_nonnegative_decimal(
                "evidence_gap_count",
                self.evidence_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "urgency_score",
            _normalize_ratio("urgency_score", self.urgency_score),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _normalize_source_quorum_status(self.source_quorum_status),
        )
        object.__setattr__(
            self,
            "deadline_minutes",
            _normalize_positive_decimal("deadline_minutes", self.deadline_minutes),
        )
        reject_unsafe_surface_fields("team specialist handoff ticket input", self)
        require_paper_only_flags("team specialist handoff ticket input", self)


@dataclass(frozen=True)
class StrategyTeamSpecialistHandoffTicket:
    market_id: str
    from_team: str
    to_team: str
    handoff_reason: str
    evidence_gap_count: Decimal
    urgency_score: Decimal
    source_quorum_status: str
    deadline_minutes: Decimal
    handoff_status: str
    sla_minutes: Decimal
    required_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "from_team", "to_team", "handoff_reason"):
            _require_safe_canonical_string(field_name, getattr(self, field_name))
        if self.from_team == self.to_team:
            raise ValueError("from_team and to_team must differ")
        object.__setattr__(
            self,
            "evidence_gap_count",
            _normalize_whole_nonnegative_decimal(
                "evidence_gap_count",
                self.evidence_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "urgency_score",
            _normalize_ratio("urgency_score", self.urgency_score),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _normalize_source_quorum_status(self.source_quorum_status),
        )
        object.__setattr__(
            self,
            "deadline_minutes",
            _normalize_positive_decimal("deadline_minutes", self.deadline_minutes),
        )
        object.__setattr__(
            self,
            "handoff_status",
            _normalize_handoff_status(self.handoff_status),
        )
        object.__setattr__(
            self,
            "sla_minutes",
            _normalize_positive_decimal("sla_minutes", self.sla_minutes),
        )
        object.__setattr__(
            self,
            "required_sections",
            _normalize_string_tuple("required_sections", self.required_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        if self.handoff_status != _handoff_status(
            evidence_gap_count=self.evidence_gap_count,
            urgency_score=self.urgency_score,
            source_quorum_status=self.source_quorum_status,
        ):
            raise ValueError("handoff_status must match handoff inputs")
        if self.sla_minutes != _sla_minutes(
            handoff_status=self.handoff_status,
            deadline_minutes=self.deadline_minutes,
        ):
            raise ValueError("sla_minutes must match handoff status and deadline")
        if self.required_sections != _required_sections(
            evidence_gap_count=self.evidence_gap_count,
            urgency_score=self.urgency_score,
            source_quorum_status=self.source_quorum_status,
        ):
            raise ValueError("required_sections must match handoff inputs")
        if self.reason_codes != _reason_codes(
            evidence_gap_count=self.evidence_gap_count,
            urgency_score=self.urgency_score,
            source_quorum_status=self.source_quorum_status,
            deadline_minutes=self.deadline_minutes,
            handoff_status=self.handoff_status,
        ):
            raise ValueError("reason_codes must match handoff inputs")
        reject_unsafe_surface_fields("team specialist handoff ticket", self)
        require_paper_only_flags("team specialist handoff ticket", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_team_specialist_handoff_ticket_payload(self)


def build_strategy_team_specialist_handoff_ticket(
    ticket_input: StrategyTeamSpecialistHandoffTicketInput,
) -> StrategyTeamSpecialistHandoffTicket:
    if type(ticket_input) is not StrategyTeamSpecialistHandoffTicketInput:
        raise ValueError(
            "ticket_input must be a StrategyTeamSpecialistHandoffTicketInput",
        )
    require_paper_only_flags("team specialist handoff ticket input", ticket_input)
    reject_unsafe_surface_fields("team specialist handoff ticket input", ticket_input)

    handoff_status = _handoff_status(
        evidence_gap_count=ticket_input.evidence_gap_count,
        urgency_score=ticket_input.urgency_score,
        source_quorum_status=ticket_input.source_quorum_status,
    )
    return StrategyTeamSpecialistHandoffTicket(
        market_id=ticket_input.market_id,
        from_team=ticket_input.from_team,
        to_team=ticket_input.to_team,
        handoff_reason=ticket_input.handoff_reason,
        evidence_gap_count=ticket_input.evidence_gap_count,
        urgency_score=ticket_input.urgency_score,
        source_quorum_status=ticket_input.source_quorum_status,
        deadline_minutes=ticket_input.deadline_minutes,
        handoff_status=handoff_status,
        sla_minutes=_sla_minutes(
            handoff_status=handoff_status,
            deadline_minutes=ticket_input.deadline_minutes,
        ),
        required_sections=_required_sections(
            evidence_gap_count=ticket_input.evidence_gap_count,
            urgency_score=ticket_input.urgency_score,
            source_quorum_status=ticket_input.source_quorum_status,
        ),
        reason_codes=_reason_codes(
            evidence_gap_count=ticket_input.evidence_gap_count,
            urgency_score=ticket_input.urgency_score,
            source_quorum_status=ticket_input.source_quorum_status,
            deadline_minutes=ticket_input.deadline_minutes,
            handoff_status=handoff_status,
        ),
    )


def strategy_team_specialist_handoff_ticket_payload(
    ticket: StrategyTeamSpecialistHandoffTicket,
) -> dict[str, Any]:
    if type(ticket) is not StrategyTeamSpecialistHandoffTicket:
        raise ValueError("ticket must be a StrategyTeamSpecialistHandoffTicket")
    require_paper_only_flags("team specialist handoff ticket", ticket)
    reject_unsafe_surface_fields("team specialist handoff ticket", ticket)
    return json_ready_no_floats(
        {
            "market_id": ticket.market_id,
            "from_team": ticket.from_team,
            "to_team": ticket.to_team,
            "handoff_reason": ticket.handoff_reason,
            "evidence_gap_count": ticket.evidence_gap_count,
            "urgency_score": ticket.urgency_score,
            "source_quorum_status": ticket.source_quorum_status,
            "deadline_minutes": ticket.deadline_minutes,
            "handoff_status": ticket.handoff_status,
            "sla_minutes": ticket.sla_minutes,
            "required_sections": ticket.required_sections,
            "reason_codes": ticket.reason_codes,
            "paper_only": ticket.paper_only,
            "report_only": ticket.report_only,
            "readonly": ticket.readonly,
        },
    )


def _handoff_status(
    *,
    evidence_gap_count: Decimal,
    urgency_score: Decimal,
    source_quorum_status: str,
) -> str:
    if source_quorum_status == "missing":
        return "blocked"
    if urgency_score >= HIGH_URGENCY_THRESHOLD:
        return "expedited"
    if evidence_gap_count > ZERO:
        return "research_required"
    return "ready"


def _sla_minutes(*, handoff_status: str, deadline_minutes: Decimal) -> Decimal:
    if handoff_status == "blocked":
        target = BLOCKED_SLA_MINUTES
    elif handoff_status == "expedited":
        target = EXPEDITED_SLA_MINUTES
    elif handoff_status == "research_required":
        target = RESEARCH_SLA_MINUTES
    else:
        target = STANDARD_SLA_MINUTES
    return min(target, deadline_minutes).quantize(QUANTUM)


def _required_sections(
    *,
    evidence_gap_count: Decimal,
    urgency_score: Decimal,
    source_quorum_status: str,
) -> tuple[str, ...]:
    sections = list(BASE_REQUIRED_SECTIONS)
    if evidence_gap_count > ZERO:
        sections.append("evidence_gap_inventory")
    if source_quorum_status in {"partial", "missing"}:
        sections.append("source_quorum_remediation")
    if urgency_score >= STANDARD_URGENCY_THRESHOLD:
        sections.append("urgency_rationale")
    sections.append(FINAL_REQUIRED_SECTION)
    return tuple(sections)


def _reason_codes(
    *,
    evidence_gap_count: Decimal,
    urgency_score: Decimal,
    source_quorum_status: str,
    deadline_minutes: Decimal,
    handoff_status: str,
) -> tuple[str, ...]:
    codes = [
        "team_specialist_handoff_ticket",
        "evidence_gap_present" if evidence_gap_count > ZERO else "evidence_gap_clear",
        f"source_quorum_{source_quorum_status}",
    ]
    if urgency_score >= HIGH_URGENCY_THRESHOLD:
        codes.append("urgency_high")
    elif urgency_score >= STANDARD_URGENCY_THRESHOLD:
        codes.append("urgency_elevated")
    else:
        codes.append("urgency_standard")
    if deadline_minutes < EXPEDITED_SLA_MINUTES:
        codes.append("deadline_compressed")
    else:
        codes.append("deadline_standard")
    codes.append(f"handoff_status_{handoff_status}")
    return tuple(codes)


def _normalize_source_quorum_status(value: Any) -> str:
    _require_safe_canonical_string("source_quorum_status", value)
    if value not in SOURCE_QUORUM_STATUSES:
        raise ValueError(
            "source_quorum_status must be one of met, partial, or missing",
        )
    return value


def _normalize_handoff_status(value: Any) -> str:
    _require_safe_canonical_string("handoff_status", value)
    if value not in HANDOFF_STATUSES:
        raise ValueError(
            "handoff_status must be one of ready, research_required, expedited, or blocked",
        )
    return value


def _normalize_string_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_safe_canonical_string(field_name, item)
    return value


def _normalize_whole_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_safe_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe live surface value")


__all__ = (
    "StrategyTeamSpecialistHandoffTicket",
    "StrategyTeamSpecialistHandoffTicketInput",
    "build_strategy_team_specialist_handoff_ticket",
    "strategy_team_specialist_handoff_ticket_payload",
)
