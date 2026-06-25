"""Pure paper-only broker adapter for internal pipeline use.

This module defines the first broker boundary: a paper-only execution
mode that accepts a risk-gated proposal and emits a paper execution
record without any I/O, exchange contact, or live execution.

The paper broker does not:
- connect to exchanges
- authenticate
- handle private keys
- place, sign, submit, cancel, or replace orders
- read balances, positions, fills, or exchange user state
- mutate external state

It is purely a report reducer that transforms a risk-gated proposal
into a deterministic paper execution record.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context

from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    PaperAutonomousProposalRiskGateReport,
)


__all__ = (
    "DEFAULT_PAPER_BROKER_CONFIG_VERSION",
    "PaperBrokerConfig",
    "PaperBrokerExecutionRecord",
    "build_paper_broker_execution_record",
)


DEFAULT_PAPER_BROKER_CONFIG_VERSION = "paper-broker-v0"
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
EXECUTION_STATUSES = ("paper_submitted", "paper_blocked", "paper_held")
NEXT_STEP_BY_STATUS = {
    "paper_submitted": "route_to_paper_order_lifecycle",
    "paper_held": "hold_for_broker_review",
    "paper_blocked": "block_paper_execution_pending_repair",
}
def _validate_hard_flags(label: str, obj: object) -> None:
    for field in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field) is not True:
            raise ValueError(f"{field} must be True for {label}")


def _require_execution_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXECUTION_STATUSES:
        raise ValueError(f"{field_name} must be one of {EXECUTION_STATUSES}")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("pass", "watch", "blocked"):
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_quantized_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if value != Decimal(value).quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)



@dataclass(frozen=True)
class PaperBrokerConfig:
    config_version: str = DEFAULT_PAPER_BROKER_CONFIG_VERSION
    max_execution_notional: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperBrokerConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperBrokerConfig:
            raise ValueError("config must be exactly PaperBrokerConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_quantized_decimal("max_execution_notional", self.max_execution_notional)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperBrokerExecutionRecord:
    generated_at: datetime
    config_version: str
    execution_status: str
    recommended_next_step: str
    source_gate_status: str
    source_proposal_count: int
    source_proposal_total_notional: Decimal
    execution_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperBrokerExecutionRecord does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperBrokerExecutionRecord:
            raise ValueError("record must be exactly PaperBrokerExecutionRecord")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_execution_status("execution_status", self.execution_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_gate_status("source_gate_status", self.source_gate_status)
        _require_nonnegative_int("source_proposal_count", self.source_proposal_count)
        object.__setattr__(self, "source_proposal_total_notional", _quantize(self.source_proposal_total_notional))
        object.__setattr__(self, "execution_notional", _quantize(self.execution_notional))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_record_consistency(self)
        _validate_hard_flags("execution record", self)


def build_paper_broker_execution_record(
    *,
    risk_gate_report: PaperAutonomousProposalRiskGateReport,
    config: PaperBrokerConfig = PaperBrokerConfig(),
    generated_at: datetime,
) -> PaperBrokerExecutionRecord:
    """Build a paper execution record from a risk-gated proposal.

    The paper broker accepts a risk gate report and emits a paper
    execution record. If the risk gate passes, the broker simulates
    paper execution at the source proposal's total notional. If the
    risk gate blocks or holds, the broker blocks or holds accordingly.
    """

    if type(risk_gate_report) is not PaperAutonomousProposalRiskGateReport:
        raise ValueError("risk_gate_report must be exactly PaperAutonomousProposalRiskGateReport")
    if type(config) is not PaperBrokerConfig:
        raise ValueError("config must be exactly PaperBrokerConfig")
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)

    with localcontext(DECIMAL_CONTEXT):
        source_gate_status = risk_gate_report.gate_status
        source_proposal_total_notional = risk_gate_report.source_proposal_total_notional

        if source_gate_status == "blocked":
            execution_status = "paper_blocked"
            reason_codes = ("paper_broker_gate_blocked",)
            execution_notional = ZERO
        elif source_gate_status == "watch":
            execution_status = "paper_held"
            reason_codes = ("paper_broker_gate_held",)
            execution_notional = ZERO
        else:
            # Gate passed—check execution caps
            if source_proposal_total_notional > config.max_execution_notional:
                execution_status = "paper_blocked"
                reason_codes = ("paper_broker_execution_notional_exceeded",)
                execution_notional = ZERO
            else:
                execution_status = "paper_submitted"
                reason_codes = ("paper_broker_execution_submitted",)
                execution_notional = source_proposal_total_notional

    return PaperBrokerExecutionRecord(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        execution_status=execution_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[execution_status],
        source_gate_status=source_gate_status,
        source_proposal_count=risk_gate_report.source_proposal_count,
        source_proposal_total_notional=source_proposal_total_notional,
        execution_notional=execution_notional,
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


def _validate_record_consistency(record: PaperBrokerExecutionRecord) -> None:
    if record.recommended_next_step != NEXT_STEP_BY_STATUS[record.execution_status]:
        raise ValueError("recommended_next_step must match execution_status")
    if record.execution_status == "paper_submitted" and record.execution_notional <= ZERO:
        raise ValueError("paper_submitted execution must have positive notional")
    if record.execution_status in ("paper_blocked", "paper_held") and record.execution_notional != ZERO:
        raise ValueError("blocked/held execution must have zero notional")

