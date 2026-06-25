"""Pure paper-only order lifecycle state machine.

This module defines the lifecycle states for paper execution records.
It tracks the progression of a paper execution from submission through
completion, providing deterministic state transitions and diagnostics
without any I/O or exchange contact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_broker import (
    PaperBrokerExecutionRecord,
)


__all__ = (
    "DEFAULT_PAPER_ORDER_LIFECYCLE_CONFIG_VERSION",
    "PaperOrderLifecycleConfig",
    "PaperOrderLifecycleRecord",
    "build_paper_order_lifecycle_record",
)


DEFAULT_PAPER_ORDER_LIFECYCLE_CONFIG_VERSION = "paper-order-lifecycle-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
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
TERMINAL_STATUSES = frozenset({
    "risk_blocked",
    "paper_filled",
    "paper_cancelled",
    "paper_expired",
    "rejected",
})
NEXT_STEP_BY_STATUS = {
    "proposed": "route_to_risk_gate",
    "risk_passed": "route_to_paper_broker",
    "risk_blocked": "archive_proposal",
    "paper_submitted": "track_paper_fill",
    "paper_filled": "record_paper_outcome",
    "paper_cancelled": "archive_paper_order",
    "paper_expired": "archive_paper_order",
    "human_approval_pending": "await_human_decision",
    "reviewed": "route_to_live_broker",
    "rejected": "archive_proposal",
}
def _validate_hard_flags(label: str, obj: object) -> None:
    for field in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field) is not True:
            raise ValueError(f"{field} must be True for {label}")


def _require_lifecycle_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LIFECYCLE_STATUSES:
        raise ValueError(f"{field_name} must be one of {LIFECYCLE_STATUSES}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)



@dataclass(frozen=True)
class PaperOrderLifecycleConfig:
    config_version: str = DEFAULT_PAPER_ORDER_LIFECYCLE_CONFIG_VERSION
    max_fill_wait_seconds: int = 86_400  # 24 hours
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperOrderLifecycleConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperOrderLifecycleConfig:
            raise ValueError("config must be exactly PaperOrderLifecycleConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("max_fill_wait_seconds", self.max_fill_wait_seconds)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperOrderLifecycleRecord:
    generated_at: datetime
    config_version: str
    lifecycle_status: str
    recommended_next_step: str
    source_execution_status: str
    source_execution_notional: Decimal
    fill_notional: Decimal
    is_terminal: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperOrderLifecycleRecord does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperOrderLifecycleRecord:
            raise ValueError("record must be exactly PaperOrderLifecycleRecord")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_lifecycle_status("lifecycle_status", self.lifecycle_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_canonical_string("source_execution_status", self.source_execution_status)
        object.__setattr__(self, "source_execution_notional", _quantize(self.source_execution_notional))
        object.__setattr__(self, "fill_notional", _quantize(self.fill_notional))
        if type(self.is_terminal) is not bool:
            raise ValueError("is_terminal must be a bool")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_record_consistency(self)
        _validate_hard_flags("lifecycle record", self)


def build_paper_order_lifecycle_record(
    *,
    broker_record: PaperBrokerExecutionRecord,
    config: PaperOrderLifecycleConfig = PaperOrderLifecycleConfig(),
    generated_at: datetime,
) -> PaperOrderLifecycleRecord:
    """Build a lifecycle record from a paper broker execution record.

    The lifecycle state machine maps the broker's execution status to
    a deterministic lifecycle state:
    - paper_submitted -> paper_submitted (awaiting fill simulation)
    - paper_blocked -> risk_blocked
    - paper_held -> human_approval_pending

    For v0, paper_submitted immediately transitions to paper_filled
    because the paper broker simulates instant fills. In future versions,
    the lifecycle could track partial fills, cancellations, or expirations.
    """

    if type(broker_record) is not PaperBrokerExecutionRecord:
        raise ValueError("broker_record must be exactly PaperBrokerExecutionRecord")
    if type(config) is not PaperOrderLifecycleConfig:
        raise ValueError("config must be exactly PaperOrderLifecycleConfig")
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)

    source_status = broker_record.execution_status
    execution_notional = broker_record.execution_notional

    if source_status == "paper_submitted":
        # v0: instant paper fill
        lifecycle_status = "paper_filled"
        fill_notional = execution_notional
        reason_codes = ("paper_order_lifecycle_filled",)
    elif source_status == "paper_blocked":
        lifecycle_status = "risk_blocked"
        fill_notional = ZERO
        reason_codes = ("paper_order_lifecycle_blocked",)
    elif source_status == "paper_held":
        lifecycle_status = "human_approval_pending"
        fill_notional = ZERO
        reason_codes = ("paper_order_lifecycle_awaiting_approval",)
    else:
        raise ValueError(f"unknown source execution status: {source_status}")

    return PaperOrderLifecycleRecord(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        lifecycle_status=lifecycle_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[lifecycle_status],
        source_execution_status=source_status,
        source_execution_notional=execution_notional,
        fill_notional=fill_notional,
        is_terminal=lifecycle_status in TERMINAL_STATUSES,
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


def _validate_record_consistency(record: PaperOrderLifecycleRecord) -> None:
    if record.recommended_next_step != NEXT_STEP_BY_STATUS[record.lifecycle_status]:
        raise ValueError("recommended_next_step must match lifecycle_status")
    if record.is_terminal != (record.lifecycle_status in TERMINAL_STATUSES):
        raise ValueError("is_terminal must match lifecycle status terminal set")
    if record.lifecycle_status == "paper_filled" and record.fill_notional <= ZERO:
        raise ValueError("paper_filled must have positive fill notional")
    if record.lifecycle_status in ("risk_blocked", "human_approval_pending") and record.fill_notional != ZERO:
        raise ValueError("blocked/pending must have zero fill notional")

