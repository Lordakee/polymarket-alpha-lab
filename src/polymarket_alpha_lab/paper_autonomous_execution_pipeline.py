"""Pure paper-only autonomous execution pipeline reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_autonomous_proposal import (
    PaperAutonomousProposalConfig,
    build_paper_autonomous_proposal_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    PaperAutonomousProposalRiskGateConfig,
    build_paper_autonomous_proposal_risk_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from polymarket_alpha_lab.paper_broker import (
    PaperBrokerConfig,
    build_paper_broker_execution_record,
)
from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationConfig,
    build_paper_execution_reconciliation_report,
)
from polymarket_alpha_lab.paper_order_lifecycle import (
    PaperOrderLifecycleConfig,
    build_paper_order_lifecycle_record,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_EXECUTION_PIPELINE_CONFIG_VERSION",
    "PaperAutonomousExecutionPipelineReport",
    "build_paper_autonomous_execution_pipeline_report",
)


DEFAULT_PAPER_AUTONOMOUS_EXECUTION_PIPELINE_CONFIG_VERSION = (
    "paper-autonomous-execution-pipeline-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
SOURCE_GATE_STATUSES = ("pass", "watch", "blocked")
PROPOSAL_STATUSES = ("candidate", "blocked", "watch", "retired")
RISK_GATE_STATUSES = ("pass", "watch", "blocked")
BROKER_EXECUTION_STATUSES = ("paper_submitted", "paper_blocked", "paper_held")
LIFECYCLE_STATUSES = (
    "proposed",
    "risk_passed",
    "risk_blocked",
    "paper_submitted",
    "paper_filled",
    "paper_cancelled",
    "paper_expired",
    "human_approval_pending",
    "reviewed",
    "rejected",
)
RECONCILIATION_STATUSES = ("reconciled", "has_pending", "has_discrepancies")
NEXT_STEP_BY_PIPELINE_STATUS = {
    "advance": "track_paper_execution_reconciliation",
    "hold": "hold_paper_autonomous_execution_pipeline",
    "repair": "repair_paper_autonomous_execution_pipeline",
}


@dataclass(frozen=True)
class PaperAutonomousExecutionPipelineReport:
    generated_at: datetime
    config_version: str
    source_gate_status: str
    proposal_status: str
    proposal_count: int
    risk_gate_status: str
    broker_execution_status: str
    broker_execution_notional: Decimal
    lifecycle_status: str
    lifecycle_fill_notional: Decimal
    lifecycle_is_terminal: bool
    reconciliation_status: str
    reconciliation_total_positions: int
    reconciliation_filled_pending_count: int
    reconciliation_settled_win_count: int
    reconciliation_settled_loss_count: int
    reconciliation_expired_count: int
    reconciliation_cancelled_count: int
    reason_codes: tuple[str, ...]
    recommended_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousExecutionPipelineReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousExecutionPipelineReport:
            raise ValueError(
                "report must be exactly PaperAutonomousExecutionPipelineReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_choice(
            "source_gate_status",
            self.source_gate_status,
            SOURCE_GATE_STATUSES,
        )
        _require_choice("proposal_status", self.proposal_status, PROPOSAL_STATUSES)
        _require_nonnegative_int("proposal_count", self.proposal_count)
        _require_choice("risk_gate_status", self.risk_gate_status, RISK_GATE_STATUSES)
        _require_choice(
            "broker_execution_status",
            self.broker_execution_status,
            BROKER_EXECUTION_STATUSES,
        )
        object.__setattr__(
            self,
            "broker_execution_notional",
            _quantize_nonnegative_decimal(
                "broker_execution_notional",
                self.broker_execution_notional,
            ),
        )
        _require_choice("lifecycle_status", self.lifecycle_status, LIFECYCLE_STATUSES)
        object.__setattr__(
            self,
            "lifecycle_fill_notional",
            _quantize_nonnegative_decimal(
                "lifecycle_fill_notional",
                self.lifecycle_fill_notional,
            ),
        )
        if type(self.lifecycle_is_terminal) is not bool:
            raise ValueError("lifecycle_is_terminal must be a bool")
        _require_choice(
            "reconciliation_status",
            self.reconciliation_status,
            RECONCILIATION_STATUSES,
        )
        for field_name in (
            "reconciliation_total_positions",
            "reconciliation_filled_pending_count",
            "reconciliation_settled_win_count",
            "reconciliation_settled_loss_count",
            "reconciliation_expired_count",
            "reconciliation_cancelled_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _validate_report_consistency(self)
        _validate_hard_flags("pipeline report", self)


def build_paper_autonomous_execution_pipeline_report(
    *,
    gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    proposal_config: PaperAutonomousProposalConfig = PaperAutonomousProposalConfig(),
    risk_gate_config: PaperAutonomousProposalRiskGateConfig = (
        PaperAutonomousProposalRiskGateConfig()
    ),
    broker_config: PaperBrokerConfig = PaperBrokerConfig(),
    lifecycle_config: PaperOrderLifecycleConfig = PaperOrderLifecycleConfig(),
    reconciliation_config: PaperExecutionReconciliationConfig = (
        PaperExecutionReconciliationConfig()
    ),
    generated_at: datetime | None = None,
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_EXECUTION_PIPELINE_CONFIG_VERSION,
) -> PaperAutonomousExecutionPipelineReport:
    if type(gate_report) is not PaperAutonomousScreeningDecisionSupportGateReport:
        raise ValueError(
            "gate_report must be exactly "
            "PaperAutonomousScreeningDecisionSupportGateReport",
        )
    _validate_hard_flags("gate report", gate_report)
    _require_exact_config(
        "proposal_config",
        proposal_config,
        PaperAutonomousProposalConfig,
    )
    _require_exact_config(
        "risk_gate_config",
        risk_gate_config,
        PaperAutonomousProposalRiskGateConfig,
    )
    _require_exact_config("broker_config", broker_config, PaperBrokerConfig)
    _require_exact_config(
        "lifecycle_config",
        lifecycle_config,
        PaperOrderLifecycleConfig,
    )
    _require_exact_config(
        "reconciliation_config",
        reconciliation_config,
        PaperExecutionReconciliationConfig,
    )
    _require_canonical_string("config_version", config_version)

    generated_at_utc = _as_utc(
        "generated_at",
        gate_report.generated_at if generated_at is None else generated_at,
    )
    proposal_report = build_paper_autonomous_proposal_report(
        gate_report=gate_report,
        config=proposal_config,
        generated_at=generated_at_utc,
    )
    risk_gate_report = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal_report,
        config=risk_gate_config,
        generated_at=generated_at_utc,
    )
    broker_record = build_paper_broker_execution_record(
        risk_gate_report=risk_gate_report,
        config=broker_config,
        generated_at=generated_at_utc,
    )
    lifecycle_record = build_paper_order_lifecycle_record(
        broker_record=broker_record,
        config=lifecycle_config,
        generated_at=generated_at_utc,
    )
    reconciliation_report = build_paper_execution_reconciliation_report(
        lifecycle_records=(lifecycle_record,),
        config=reconciliation_config,
        generated_at=generated_at_utc,
    )

    return PaperAutonomousExecutionPipelineReport(
        generated_at=generated_at_utc,
        config_version=config_version,
        source_gate_status=gate_report.gate_status,
        proposal_status=proposal_report.proposal_status,
        proposal_count=proposal_report.proposal_count,
        risk_gate_status=risk_gate_report.gate_status,
        broker_execution_status=broker_record.execution_status,
        broker_execution_notional=broker_record.execution_notional,
        lifecycle_status=lifecycle_record.lifecycle_status,
        lifecycle_fill_notional=lifecycle_record.fill_notional,
        lifecycle_is_terminal=lifecycle_record.is_terminal,
        reconciliation_status=reconciliation_report.reconciliation_status,
        reconciliation_total_positions=reconciliation_report.total_positions,
        reconciliation_filled_pending_count=(
            reconciliation_report.filled_pending_count
        ),
        reconciliation_settled_win_count=reconciliation_report.settled_win_count,
        reconciliation_settled_loss_count=reconciliation_report.settled_loss_count,
        reconciliation_expired_count=reconciliation_report.expired_count,
        reconciliation_cancelled_count=reconciliation_report.cancelled_count,
        reason_codes=_merge_reason_codes(
            gate_report.reason_codes,
            proposal_report.reason_codes,
            risk_gate_report.reason_codes,
            broker_record.reason_codes,
            lifecycle_record.reason_codes,
            reconciliation_report.reason_codes,
        ),
        recommended_next_step=_recommended_next_step(
            proposal_status=proposal_report.proposal_status,
            risk_gate_status=risk_gate_report.gate_status,
            broker_execution_status=broker_record.execution_status,
            lifecycle_status=lifecycle_record.lifecycle_status,
        ),
    )


def _require_exact_config(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")
    _validate_hard_flags(field_name, value)


def _validate_hard_flags(label: str, obj: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_choice(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    quantized = Decimal(value).quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    previous: str | None = None
    for reason_code in value:
        _require_canonical_string("reason_codes entries", reason_code)
        if previous is not None and previous >= reason_code:
            raise ValueError("reason_codes must be sorted and unique")
        previous = reason_code
    return value


def _merge_reason_codes(*reason_code_sets: tuple[str, ...]) -> tuple[str, ...]:
    merged: set[str] = set()
    for reason_codes in reason_code_sets:
        _normalize_reason_codes(reason_codes)
        merged.update(reason_codes)
    return tuple(sorted(merged))


def _recommended_next_step(
    *,
    proposal_status: str,
    risk_gate_status: str,
    broker_execution_status: str,
    lifecycle_status: str,
) -> str:
    if proposal_status == "blocked" or risk_gate_status == "blocked":
        return NEXT_STEP_BY_PIPELINE_STATUS["repair"]
    if broker_execution_status == "paper_blocked" or lifecycle_status == "risk_blocked":
        return NEXT_STEP_BY_PIPELINE_STATUS["repair"]
    if proposal_status == "watch" or risk_gate_status == "watch":
        return NEXT_STEP_BY_PIPELINE_STATUS["hold"]
    if broker_execution_status == "paper_held" or lifecycle_status == "human_approval_pending":
        return NEXT_STEP_BY_PIPELINE_STATUS["hold"]
    return NEXT_STEP_BY_PIPELINE_STATUS["advance"]


def _validate_report_consistency(
    report: PaperAutonomousExecutionPipelineReport,
) -> None:
    expected_next_step = _recommended_next_step(
        proposal_status=report.proposal_status,
        risk_gate_status=report.risk_gate_status,
        broker_execution_status=report.broker_execution_status,
        lifecycle_status=report.lifecycle_status,
    )
    if report.recommended_next_step != expected_next_step:
        raise ValueError("recommended_next_step must match pipeline status")
    if report.broker_execution_status == "paper_submitted":
        if report.broker_execution_notional <= ZERO:
            raise ValueError("paper_submitted broker execution must have positive notional")
    if report.broker_execution_status in ("paper_blocked", "paper_held"):
        if report.broker_execution_notional != ZERO:
            raise ValueError("blocked/held broker execution must have zero notional")
    if report.lifecycle_status == "paper_filled":
        if report.lifecycle_fill_notional <= ZERO:
            raise ValueError("paper_filled lifecycle must have positive fill notional")
    if report.lifecycle_status in ("risk_blocked", "human_approval_pending"):
        if report.lifecycle_fill_notional != ZERO:
            raise ValueError("blocked/pending lifecycle must have zero fill notional")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
