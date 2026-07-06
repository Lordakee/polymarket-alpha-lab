"""Paper-only candidate market screening stage gate."""

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
PASS_EDGE_THRESHOLD_BPS = Decimal("10.000000")

STAGE_NAMES = (
    "candidate_intake",
    "source_confidence",
    "edge_screen",
    "portfolio_fit",
    "research_budget",
    "human_review",
)
NEXT_STAGE_BY_STAGE = {
    "candidate_intake": "source_confidence",
    "source_confidence": "edge_screen",
    "edge_screen": "portfolio_fit",
    "portfolio_fit": "research_budget",
    "research_budget": "paper_queue",
    "human_review": "paper_queue",
}

CANDIDATE_STATUSES = ("research_ready", "watch", "blocked")
SOURCE_CONFIDENCE_LEVELS = ("high", "medium", "low")
PORTFOLIO_FIT_STATUSES = ("fit", "watch", "blocked")
RESEARCH_BUDGET_STATUSES = ("available", "limited", "exhausted")
STAGE_GATE_STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class MarketScreeningStageGateInput:
    market_id: str
    stage_name: str
    candidate_status: str
    source_confidence_level: str
    cost_adjusted_edge_bps: Decimal
    portfolio_fit_status: str
    research_budget_status: str
    human_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "stage_name",
            _require_member("stage_name", self.stage_name, STAGE_NAMES),
        )
        object.__setattr__(
            self,
            "candidate_status",
            _require_member("candidate_status", self.candidate_status, CANDIDATE_STATUSES),
        )
        object.__setattr__(
            self,
            "source_confidence_level",
            _require_member(
                "source_confidence_level",
                self.source_confidence_level,
                SOURCE_CONFIDENCE_LEVELS,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        object.__setattr__(
            self,
            "portfolio_fit_status",
            _require_member(
                "portfolio_fit_status",
                self.portfolio_fit_status,
                PORTFOLIO_FIT_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "research_budget_status",
            _require_member(
                "research_budget_status",
                self.research_budget_status,
                RESEARCH_BUDGET_STATUSES,
            ),
        )
        if type(self.human_review_required) is not bool:
            raise ValueError("human_review_required must be a bool")
        reject_unsafe_surface_fields("market screening stage gate input", self)
        require_paper_only_flags("market screening stage gate input", self)


@dataclass(frozen=True)
class MarketScreeningStageGateReport:
    market_id: str
    stage_name: str
    candidate_status: str
    source_confidence_level: str
    cost_adjusted_edge_bps: Decimal
    portfolio_fit_status: str
    research_budget_status: str
    human_review_required: bool
    stage_gate_status: str
    next_stage: str
    blocking_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "stage_name",
            _require_member("stage_name", self.stage_name, STAGE_NAMES),
        )
        object.__setattr__(
            self,
            "candidate_status",
            _require_member("candidate_status", self.candidate_status, CANDIDATE_STATUSES),
        )
        object.__setattr__(
            self,
            "source_confidence_level",
            _require_member(
                "source_confidence_level",
                self.source_confidence_level,
                SOURCE_CONFIDENCE_LEVELS,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        object.__setattr__(
            self,
            "portfolio_fit_status",
            _require_member(
                "portfolio_fit_status",
                self.portfolio_fit_status,
                PORTFOLIO_FIT_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "research_budget_status",
            _require_member(
                "research_budget_status",
                self.research_budget_status,
                RESEARCH_BUDGET_STATUSES,
            ),
        )
        if type(self.human_review_required) is not bool:
            raise ValueError("human_review_required must be a bool")
        object.__setattr__(
            self,
            "stage_gate_status",
            _require_member("stage_gate_status", self.stage_gate_status, STAGE_GATE_STATUSES),
        )
        object.__setattr__(self, "next_stage", _require_canonical_string("next_stage", self.next_stage))
        object.__setattr__(
            self,
            "blocking_reasons",
            _normalize_strings("blocking_reasons", self.blocking_reasons),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_strings("reason_codes", self.reason_codes),
        )
        if self.stage_gate_status == "blocked" and not self.blocking_reasons:
            raise ValueError("blocked stage gate requires blocking_reasons")
        if self.stage_gate_status != "blocked" and self.blocking_reasons:
            raise ValueError("blocking_reasons require blocked stage_gate_status")
        reject_unsafe_surface_fields("market screening stage gate report", self)
        require_paper_only_flags("market screening stage gate report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return market_screening_stage_gate_payload(self)


def evaluate_market_screening_stage_gate(
    gate_input: MarketScreeningStageGateInput,
) -> MarketScreeningStageGateReport:
    if type(gate_input) is not MarketScreeningStageGateInput:
        raise ValueError("gate_input must be a MarketScreeningStageGateInput")
    require_paper_only_flags("market screening stage gate input", gate_input)
    reject_unsafe_surface_fields("market screening stage gate input", gate_input)

    blocking_reasons: list[str] = []
    reason_codes: list[str] = []
    soft_reason_codes: list[str] = []

    if gate_input.candidate_status == "blocked":
        blocking_reasons.append("candidate_status=blocked")
        reason_codes.append("candidate_status_blocked")
    elif gate_input.candidate_status == "watch":
        soft_reason_codes.append("candidate_status_watch")

    if gate_input.source_confidence_level == "low":
        blocking_reasons.append("source_confidence_level=low")
        reason_codes.append("source_confidence_low")
    elif gate_input.source_confidence_level == "medium":
        soft_reason_codes.append("source_confidence_medium")

    if gate_input.cost_adjusted_edge_bps < ZERO:
        blocking_reasons.append("cost_adjusted_edge_bps_below_zero")
        reason_codes.append("cost_adjusted_edge_negative")
    elif gate_input.cost_adjusted_edge_bps < PASS_EDGE_THRESHOLD_BPS:
        soft_reason_codes.append("cost_adjusted_edge_below_pass_threshold")

    if gate_input.portfolio_fit_status == "blocked":
        blocking_reasons.append("portfolio_fit_status=blocked")
        reason_codes.append("portfolio_fit_blocked")
    elif gate_input.portfolio_fit_status == "watch":
        soft_reason_codes.append("portfolio_fit_watch")

    if gate_input.research_budget_status == "exhausted":
        blocking_reasons.append("research_budget_status=exhausted")
        reason_codes.append("research_budget_exhausted")
    elif gate_input.research_budget_status == "limited":
        soft_reason_codes.append("research_budget_limited")

    if gate_input.human_review_required:
        soft_reason_codes.append("human_review_required")

    if blocking_reasons:
        stage_gate_status = "blocked"
        next_stage = "screening_blocked"
        reason_codes = ["market_screening_stage_gate_blocked", *reason_codes]
    elif soft_reason_codes:
        stage_gate_status = "watch"
        next_stage = "human_review" if gate_input.human_review_required else "stage_review"
        reason_codes = ["market_screening_stage_gate_watch", *soft_reason_codes]
    else:
        stage_gate_status = "pass"
        next_stage = NEXT_STAGE_BY_STAGE[gate_input.stage_name]
        reason_codes = ["market_screening_stage_gate_passed"]

    return MarketScreeningStageGateReport(
        market_id=gate_input.market_id,
        stage_name=gate_input.stage_name,
        candidate_status=gate_input.candidate_status,
        source_confidence_level=gate_input.source_confidence_level,
        cost_adjusted_edge_bps=gate_input.cost_adjusted_edge_bps,
        portfolio_fit_status=gate_input.portfolio_fit_status,
        research_budget_status=gate_input.research_budget_status,
        human_review_required=gate_input.human_review_required,
        stage_gate_status=stage_gate_status,
        next_stage=next_stage,
        blocking_reasons=tuple(blocking_reasons),
        reason_codes=_dedupe(tuple(reason_codes)),
    )


def market_screening_stage_gate_payload(
    report: MarketScreeningStageGateReport,
) -> dict[str, Any]:
    if type(report) is not MarketScreeningStageGateReport:
        raise ValueError("report must be a MarketScreeningStageGateReport")
    require_paper_only_flags("market screening stage gate report", report)
    reject_unsafe_surface_fields("market screening stage gate report", report)
    return json_ready_no_floats(
        {
            "market_id": report.market_id,
            "stage_name": report.stage_name,
            "candidate_status": report.candidate_status,
            "source_confidence_level": report.source_confidence_level,
            "cost_adjusted_edge_bps": report.cost_adjusted_edge_bps,
            "portfolio_fit_status": report.portfolio_fit_status,
            "research_budget_status": report.research_budget_status,
            "human_review_required": report.human_review_required,
            "stage_gate_status": report.stage_gate_status,
            "next_stage": report.next_stage,
            "blocking_reasons": report.blocking_reasons,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)


def _normalize_strings(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(_require_canonical_string(field_name, item) for item in value)


def _require_member(field_name: str, value: Any, allowed_values: tuple[str, ...]) -> str:
    value = _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


__all__ = (
    "MarketScreeningStageGateInput",
    "MarketScreeningStageGateReport",
    "market_screening_stage_gate_payload",
    "evaluate_market_screening_stage_gate",
)
