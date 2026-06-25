"""Pure paper-only autonomous proposal reducer for internal pipeline use.

This module defines the internal proposal boundary between research/scoring
and any future execution mode. A proposal is not an order: it describes
what the system would consider doing under controlled conditions, never
what it should submit to an exchange.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_CONFIG_VERSION",
    "PaperAutonomousProposalConfig",
    "PaperAutonomousProposalRow",
    "PaperAutonomousProposalReport",
    "build_paper_autonomous_proposal_report",
)


DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_CONFIG_VERSION = "paper-autonomous-proposal-v0"
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
PROPOSAL_STATUSES = ("candidate", "blocked", "watch", "retired")
SIDES = ("yes", "no", "none")
PROPOSAL_NEXT_STEP_BY_STATUS = {
    "candidate": "route_to_paper_proposal_risk_gate",
    "watch": "hold_paper_proposal_for_fresh_evidence",
    "blocked": "block_paper_proposal_pending_repair",
    "retired": "archive_paper_proposal",
}
PASS_REASON_CODE = "paper_autonomous_proposal_candidate_passed"
def _validate_hard_flags(label: str, obj: object) -> None:
    for field in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field) is not True:
            raise ValueError(f"{field} must be True for {label}")


def _require_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be one of {PROPOSAL_STATUSES}")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("pass", "watch", "blocked"):
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _require_quantized_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if value != Decimal(value).quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)




@dataclass(frozen=True)
class PaperAutonomousProposalConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_CONFIG_VERSION
    min_queue_ready_notional: Decimal = Decimal("1.000000")
    min_research_priority_score: Decimal = Decimal("1.000000")
    max_proposal_count: int = 25
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperAutonomousProposalConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousProposalConfig:
            raise ValueError("config must be exactly PaperAutonomousProposalConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_quantized_decimal("min_queue_ready_notional", self.min_queue_ready_notional)
        _require_quantized_decimal("min_research_priority_score", self.min_research_priority_score)
        _require_positive_int("max_proposal_count", self.max_proposal_count)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousProposalRow:
    proposal_rank: int
    market_slug: str
    side: str
    research_priority_score: Decimal
    allocated_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperAutonomousProposalRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousProposalRow:
            raise ValueError("row must be exactly PaperAutonomousProposalRow")
        _require_positive_int("proposal_rank", self.proposal_rank)
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in SIDES:
            raise ValueError("side must be yes, no, or none")
        object.__setattr__(self, "research_priority_score", _quantize(self.research_priority_score))
        object.__setattr__(self, "allocated_notional", _quantize(self.allocated_notional))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_hard_flags("proposal row", self)


@dataclass(frozen=True)
class PaperAutonomousProposalReport:
    generated_at: datetime
    config_version: str
    proposal_status: str
    recommended_next_step: str
    source_gate_status: str
    source_gate_config_version: str
    source_queue_ready_count: int
    source_queue_total_ready_notional: Decimal
    source_queue_top_research_priority_score: Decimal
    proposal_count: int
    proposals: tuple[PaperAutonomousProposalRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperAutonomousProposalReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousProposalReport:
            raise ValueError("report must be exactly PaperAutonomousProposalReport")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_proposal_status("proposal_status", self.proposal_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_gate_status("source_gate_status", self.source_gate_status)
        _require_canonical_string("source_gate_config_version", self.source_gate_config_version)
        _require_nonnegative_int("source_queue_ready_count", self.source_queue_ready_count)
        object.__setattr__(self, "source_queue_total_ready_notional", _quantize(self.source_queue_total_ready_notional))
        object.__setattr__(self, "source_queue_top_research_priority_score", _quantize(self.source_queue_top_research_priority_score))
        _require_nonnegative_int("proposal_count", self.proposal_count)
        object.__setattr__(self, "proposals", _normalize_proposals(self.proposals))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _validate_hard_flags("proposal report", self)


def build_paper_autonomous_proposal_report(
    *,
    gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    config: PaperAutonomousProposalConfig = PaperAutonomousProposalConfig(),
    generated_at: datetime,
) -> PaperAutonomousProposalReport:
    """Build a pure paper-only proposal report from a screening gate report.

    The gate report must already contain queue priority/risk data.
    This reducer extracts candidate proposals from the gate's ready rows
    and emits deterministic proposal diagnostics without any I/O.
    """

    if type(gate_report) is not PaperAutonomousScreeningDecisionSupportGateReport:
        raise ValueError("gate_report must be exactly PaperAutonomousScreeningDecisionSupportGateReport")
    if type(config) is not PaperAutonomousProposalConfig:
        raise ValueError("config must be exactly PaperAutonomousProposalConfig")
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)

    with localcontext(DECIMAL_CONTEXT):
        gate_status = gate_report.gate_status
        if gate_status == "blocked":
            proposal_status = "blocked"
            reason_codes = ("paper_autonomous_proposal_gate_blocked",)
            proposals: tuple[PaperAutonomousProposalRow, ...] = ()
        elif gate_status == "watch":
            proposal_status = "watch"
            reason_codes = ("paper_autonomous_proposal_gate_watch",)
            proposals = ()
        else:
            if gate_report.queue_ready_count == 0:
                proposal_status = "blocked"
                reason_codes = ("paper_autonomous_proposal_no_ready_candidates",)
                proposals = ()
            elif gate_report.queue_total_ready_notional < config.min_queue_ready_notional:
                proposal_status = "watch"
                reason_codes = ("paper_autonomous_proposal_insufficient_ready_notional",)
                proposals = ()
            else:
                proposal_status = "candidate"
                reason_codes = (PASS_REASON_CODE,)
                proposals = _build_candidate_proposals(
                    gate_report=gate_report,
                    config=config,
                )

    return PaperAutonomousProposalReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        proposal_status=proposal_status,
        recommended_next_step=PROPOSAL_NEXT_STEP_BY_STATUS[proposal_status],
        source_gate_status=gate_report.gate_status,
        source_gate_config_version=gate_report.config_version,
        source_queue_ready_count=gate_report.queue_ready_count,
        source_queue_total_ready_notional=gate_report.queue_total_ready_notional,
        source_queue_top_research_priority_score=gate_report.queue_top_research_priority_score,
        proposal_count=len(proposals),
        proposals=proposals,
        reason_codes=reason_codes,
    )


def _build_candidate_proposals(
    *,
    gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    config: PaperAutonomousProposalConfig,
) -> tuple[PaperAutonomousProposalRow, ...]:
    """Build a placeholder proposal row from gate-level aggregates.

    In v0, the gate report does not expose per-market allocation rows directly.
    We emit a single representative candidate row from the gate's queue
    aggregates so the proposal boundary can exist without depending on
    source-queue row readback. This is intentional: the next node
    (proposal risk gate) will refine per-market proposals from source queues.
    """

    notional = gate_report.queue_total_ready_notional
    score = gate_report.queue_top_research_priority_score
    return (
        PaperAutonomousProposalRow(
            proposal_rank=1,
            market_slug="__aggregate_queue_ready__",
            side="none",
            research_priority_score=score,
            allocated_notional=notional,
            reason_codes=(PASS_REASON_CODE,),
        ),
    )


def _normalize_proposals(value: object) -> tuple[PaperAutonomousProposalRow, ...]:
    if type(value) is not tuple:
        raise ValueError("proposals must be a tuple")
    for row in value:
        if type(row) is not PaperAutonomousProposalRow:
            raise ValueError("proposals must contain exact PaperAutonomousProposalRow values")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    previous: str | None = None
    for code in value:
        if not isinstance(code, str) or not code or code.strip() != code:
            raise ValueError("reason_codes entries must be canonical nonblank strings")
        if previous is not None and previous >= code:
            raise ValueError("reason_codes must be sorted and unique")
        previous = code
    return value


def _validate_report_consistency(report: PaperAutonomousProposalReport) -> None:
    if report.recommended_next_step != PROPOSAL_NEXT_STEP_BY_STATUS[report.proposal_status]:
        raise ValueError("recommended_next_step must match proposal_status")
    if report.proposal_count != len(report.proposals):
        raise ValueError("proposal_count must match proposals")
    if report.proposal_status == "candidate" and report.proposal_count == 0:
        raise ValueError("candidate proposals must have at least one row")
    if report.proposal_status in ("blocked", "watch") and report.proposal_count != 0:
        raise ValueError("blocked/watch proposals must have zero rows")


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)
