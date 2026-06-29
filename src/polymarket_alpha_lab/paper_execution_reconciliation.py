"""Pure paper-only execution reconciliation module.

This module reconciles paper execution lifecycle records with NAV 
snapshots and outcome tracking to produce an integrated view of
portfolio performance attribution.

It answers:
- Which paper-filled positions have settled outcomes?
- What is the P&L per position and aggregate?
- Are there any unfilled/expired paper orders that need attention?
- How does paper NAV compare to paper P&L?

This module is pure/reducer: no I/O, no DB, no exchange contact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context

from polymarket_alpha_lab.paper_order_lifecycle import PaperOrderLifecycleRecord


__all__ = (
    "DEFAULT_PAPER_EXECUTION_RECONCILIATION_CONFIG_VERSION",
    "PaperExecutionReconciliationConfig",
    "PaperExecutionReconciliationPositionRow",
    "PaperExecutionReconciliationReport",
    "build_paper_execution_reconciliation_report",
)


DEFAULT_PAPER_EXECUTION_RECONCILIATION_CONFIG_VERSION = (
    "paper-execution-reconciliation-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
POSITION_STATUSES = ("filled_pending", "settled_win", "settled_loss", "expired", "cancelled")
RECONCILIATION_STATUSES = ("reconciled", "has_pending", "has_discrepancies")


def _validate_hard_flags(label: str, obj: object) -> None:
    for field in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field) is not True:
            raise ValueError(f"{field} must be True for {label}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True)
class PaperExecutionReconciliationConfig:
    config_version: str = DEFAULT_PAPER_EXECUTION_RECONCILIATION_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperExecutionReconciliationConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationConfig:
            raise ValueError("config must be exactly PaperExecutionReconciliationConfig")
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationPositionRow:
    """Reconciliation row for a single paper position."""

    condition_id: str
    market_slug: str
    question: str
    scoring_side: str
    position_status: str
    fill_notional: Decimal
    cost_basis: Decimal
    outcome_value: Decimal | None
    pnl: Decimal | None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationPositionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationPositionRow:
            raise ValueError(
                "row must be exactly PaperExecutionReconciliationPositionRow",
            )
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("scoring_side", self.scoring_side)
        if self.position_status not in POSITION_STATUSES:
            raise ValueError(
                f"position_status must be one of {POSITION_STATUSES}",
            )
        _require_nonnegative_decimal("fill_notional", self.fill_notional)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        if self.outcome_value is not None:
            _require_nonnegative_decimal("outcome_value", self.outcome_value)
        if self.pnl is not None:
            _require_decimal("pnl", self.pnl)


@dataclass(frozen=True)
class PaperExecutionReconciliationReport:
    """Aggregate reconciliation report."""

    generated_at: datetime
    config_version: str
    reconciliation_status: str
    total_positions: int
    filled_pending_count: int
    settled_win_count: int
    settled_loss_count: int
    expired_count: int
    cancelled_count: int
    total_fill_notional: Decimal
    total_cost_basis: Decimal
    total_outcome_value: Decimal | None
    total_pnl: Decimal | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    position_rows: tuple[PaperExecutionReconciliationPositionRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool
    report_only: bool
    readonly: bool

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationReport:
            raise ValueError(
                "report must be exactly PaperExecutionReconciliationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.reconciliation_status not in RECONCILIATION_STATUSES:
            raise ValueError(
                f"reconciliation_status must be one of {RECONCILIATION_STATUSES}",
            )
        _require_nonnegative_int("total_positions", self.total_positions)
        _require_nonnegative_int("filled_pending_count", self.filled_pending_count)
        _require_nonnegative_int("settled_win_count", self.settled_win_count)
        _require_nonnegative_int("settled_loss_count", self.settled_loss_count)
        _require_nonnegative_int("expired_count", self.expired_count)
        _require_nonnegative_int("cancelled_count", self.cancelled_count)
        _require_nonnegative_decimal("total_fill_notional", self.total_fill_notional)
        _require_nonnegative_decimal("total_cost_basis", self.total_cost_basis)
        if self.total_outcome_value is not None:
            _require_nonnegative_decimal("total_outcome_value", self.total_outcome_value)
        if self.total_pnl is not None:
            _require_decimal("total_pnl", self.total_pnl)
        _require_decimal("realized_pnl", self.realized_pnl)
        _require_decimal("unrealized_pnl", self.unrealized_pnl)
        if type(self.position_rows) is not tuple:
            raise ValueError("position_rows must be a tuple")
        for row in self.position_rows:
            if type(row) is not PaperExecutionReconciliationPositionRow:
                raise ValueError(
                    "position_rows entries must be PaperExecutionReconciliationPositionRow",
                )
        _normalize_reason_codes(self.reason_codes)
        _validate_hard_flags("report", self)


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


def build_paper_execution_reconciliation_report(
    *,
    lifecycle_records: tuple[object, ...],
    config: PaperExecutionReconciliationConfig = PaperExecutionReconciliationConfig(),
    generated_at: datetime,
) -> PaperExecutionReconciliationReport:
    """Build a reconciliation report from paper order lifecycle records.

    Accepts PaperOrderLifecycleRecord instances and produces an
    aggregate reconciliation view. Settled outcomes are resolved from
    the lifecycle record's fill_notional. In v0, all paper_filled records
    are treated as filled_pending until outcome tracking provides
    settlement data in a future version.
    """
    if type(config) is not PaperExecutionReconciliationConfig:
        raise ValueError("config must be exactly PaperExecutionReconciliationConfig")
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)

    with localcontext(DECIMAL_CONTEXT):
        position_rows: list[PaperExecutionReconciliationPositionRow] = []
        filled_pending = 0
        settled_win = 0
        settled_loss = 0
        expired = 0
        cancelled = 0
        total_fill = ZERO
        total_cost = ZERO
        realized_pnl = ZERO
        unrealized_pnl = ZERO

        for record in lifecycle_records:
            _validate_lifecycle_record(record)
            lifecycle_status = record.lifecycle_status
            fill_notional = record.fill_notional
            source_notional = record.source_execution_notional

            if lifecycle_status == "paper_filled":
                position_status = "filled_pending"
                filled_pending += 1
                total_fill += fill_notional
                total_cost += source_notional
                # v0: no settlement data yet, treat as unrealized
                unrealized_pnl += (fill_notional - source_notional)
            elif lifecycle_status == "risk_blocked":
                position_status = "cancelled"
                cancelled += 1
            elif lifecycle_status == "paper_expired":
                position_status = "expired"
                expired += 1
            elif lifecycle_status == "paper_cancelled":
                position_status = "cancelled"
                cancelled += 1
            elif lifecycle_status == "human_approval_pending":
                position_status = "filled_pending"
                filled_pending += 1
            else:
                continue

            position_rows.append(
                PaperExecutionReconciliationPositionRow(
                    condition_id=f"lifecycle_{lifecycle_status}",
                    market_slug="paper_order",
                    question=f"Paper {lifecycle_status}",
                    scoring_side="none",
                    position_status=position_status,
                    fill_notional=_quantize(fill_notional),
                    cost_basis=_quantize(source_notional),
                    outcome_value=None,
                    pnl=None,
                ),
            )

        total_positions = len(position_rows)
        reason_codes: list[str] = []
        if filled_pending > 0:
            reason_codes.append("paper_execution_reconciliation_has_pending")
        if settled_win > 0 or settled_loss > 0:
            reason_codes.append("paper_execution_reconciliation_has_settled")
        if total_positions == 0:
            reason_codes.append("paper_execution_reconciliation_no_positions")

        if filled_pending > 0:
            recon_status = "has_pending"
        elif settled_win > 0 or settled_loss > 0:
            recon_status = "reconciled"
        else:
            recon_status = "reconciled"

        return PaperExecutionReconciliationReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            reconciliation_status=recon_status,
            total_positions=total_positions,
            filled_pending_count=filled_pending,
            settled_win_count=settled_win,
            settled_loss_count=settled_loss,
            expired_count=expired,
            cancelled_count=cancelled,
            total_fill_notional=_quantize(total_fill),
            total_cost_basis=_quantize(total_cost),
            total_outcome_value=None,
            total_pnl=None,
            realized_pnl=_quantize(realized_pnl),
            unrealized_pnl=_quantize(unrealized_pnl),
            position_rows=tuple(position_rows),
            reason_codes=tuple(sorted(reason_codes)),
            paper_only=True,
            report_only=True,
            readonly=True,
        )


def _validate_lifecycle_record(record: object) -> None:
    if type(record) is not PaperOrderLifecycleRecord:
        raise ValueError(
            "lifecycle_records entries must be exactly PaperOrderLifecycleRecord",
        )
    _validate_hard_flags("lifecycle record", record)
