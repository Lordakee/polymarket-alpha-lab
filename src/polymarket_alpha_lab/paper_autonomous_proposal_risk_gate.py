"""Pure paper-only proposal risk gate reducer.

This module consumes a PaperAutonomousProposalReport and evaluates
whether its proposals remain eligible for the next controlled
pipeline stage. A 'pass' verdict does not mean 'submit now'—it
means 'this proposal remains eligible for the next controlled
execution stage under paper-only conditions.'
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context

from polymarket_alpha_lab.paper_autonomous_proposal import (
    PROPOSAL_STATUSES,
    PaperAutonomousProposalReport,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_CONFIG_VERSION",
    "PaperAutonomousProposalRiskGateConfig",
    "PaperAutonomousProposalRiskGateReport",
    "build_paper_autonomous_proposal_risk_gate_report",
)


DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_CONFIG_VERSION = (
    "paper-autonomous-proposal-risk-gate-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
GATE_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_proposal_to_paper_broker",
    "watch": "hold_paper_proposal_for_risk_review",
    "blocked": "block_paper_proposal_pending_risk_repair",
}
PASS_REASON_CODE = "paper_autonomous_proposal_risk_gate_passed"
def _validate_hard_flags(label: str, obj: object) -> None:
    for field in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field) is not True:
            raise ValueError(f"{field} must be True for {label}")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
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


def _require_nonnegative_quantized_decimal(field_name: str, value: object) -> Decimal:
    _require_quantized_decimal(field_name, value)
    assert isinstance(value, Decimal)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)



@dataclass(frozen=True)
class PaperAutonomousProposalRiskGateConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_CONFIG_VERSION
    max_proposal_notional: Decimal = Decimal("100.000000")
    max_proposal_count: int = 25
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperAutonomousProposalRiskGateConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousProposalRiskGateConfig:
            raise ValueError("config must be exactly PaperAutonomousProposalRiskGateConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_quantized_decimal("max_proposal_notional", self.max_proposal_notional)
        _require_positive_int("max_proposal_count", self.max_proposal_count)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousProposalRiskGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    source_proposal_status: str
    source_proposal_count: int
    source_proposal_total_notional: Decimal
    blocked_reason_codes: tuple[str, ...]
    watch_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperAutonomousProposalRiskGateReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousProposalRiskGateReport:
            raise ValueError("report must be exactly PaperAutonomousProposalRiskGateReport")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        if self.source_proposal_status not in PROPOSAL_STATUSES:
            raise ValueError("source_proposal_status must be a known proposal status")
        _require_nonnegative_int("source_proposal_count", self.source_proposal_count)
        object.__setattr__(
            self,
            "source_proposal_total_notional",
            _require_nonnegative_quantized_decimal(
                "source_proposal_total_notional",
                self.source_proposal_total_notional,
            ),
        )
        object.__setattr__(self, "blocked_reason_codes", _normalize_reason_codes(self.blocked_reason_codes))
        object.__setattr__(self, "watch_reason_codes", _normalize_reason_codes(self.watch_reason_codes))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _validate_hard_flags("risk gate report", self)


def build_paper_autonomous_proposal_risk_gate_report(
    *,
    proposal_report: PaperAutonomousProposalReport,
    config: PaperAutonomousProposalRiskGateConfig = PaperAutonomousProposalRiskGateConfig(),
    generated_at: datetime,
) -> PaperAutonomousProposalRiskGateReport:
    """Evaluate a proposal report through the risk gate.

    The risk gate checks:
    - source proposal status (blocked/watch/candidate)
    - proposal count against max
    - total notional against max
    Emits deterministic pass/watch/blocked verdict with reason codes.
    """

    if type(proposal_report) is not PaperAutonomousProposalReport:
        raise ValueError("proposal_report must be exactly PaperAutonomousProposalReport")
    if type(config) is not PaperAutonomousProposalRiskGateConfig:
        raise ValueError("config must be exactly PaperAutonomousProposalRiskGateConfig")
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)

    with localcontext(DECIMAL_CONTEXT):
        blocked_reasons: list[str] = []
        watch_reasons: list[str] = []

        # Source proposal status checks
        if proposal_report.proposal_status == "blocked":
            blocked_reasons.append("source_proposal_blocked")
        elif proposal_report.proposal_status == "watch":
            watch_reasons.append("source_proposal_watch")

        # Proposal count check
        if proposal_report.proposal_count > config.max_proposal_count:
            blocked_reasons.append("proposal_count_exceeded")
        elif proposal_report.proposal_count == config.max_proposal_count:
            watch_reasons.append("proposal_count_at_limit")

        # Total notional check
        total_notional = ZERO
        for row in proposal_report.proposals:
            total_notional += row.allocated_notional
        if total_notional > config.max_proposal_notional:
            blocked_reasons.append("proposal_notional_exceeded")
        elif total_notional == config.max_proposal_notional:
            watch_reasons.append("proposal_notional_at_limit")

    # Determine gate status
    if blocked_reasons:
        gate_status = "blocked"
        reason_codes = tuple(sorted(blocked_reasons))
    elif watch_reasons:
        gate_status = "watch"
        reason_codes = tuple(sorted(watch_reasons))
    else:
        gate_status = "pass"
        reason_codes = (PASS_REASON_CODE,)

    return PaperAutonomousProposalRiskGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        source_proposal_status=proposal_report.proposal_status,
        source_proposal_count=proposal_report.proposal_count,
        source_proposal_total_notional=total_notional,
        blocked_reason_codes=tuple(sorted(blocked_reasons)),
        watch_reason_codes=tuple(sorted(watch_reasons)),
        reason_codes=reason_codes,
    )


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


def _validate_report_consistency(report: PaperAutonomousProposalRiskGateReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if report.gate_status == "blocked" and not report.blocked_reason_codes:
        raise ValueError("blocked gate must have blocked reason codes")
    if report.gate_status == "pass" and report.blocked_reason_codes:
        raise ValueError("pass gate must not have blocked reason codes")
    if report.gate_status == "pass" and report.watch_reason_codes:
        raise ValueError("pass gate must not have watch reason codes")
    if report.gate_status == "watch" and report.blocked_reason_codes:
        raise ValueError("watch gate must not have blocked reason codes")
