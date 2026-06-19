"""Pure paper-only reducer for user-supplied external cost assumptions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64)
VALID_SCOPES = ("account", "cycle", "market", "trade")
HARD_FLAGS = (
    ("paper_only", True),
    ("report_only", True),
    ("readonly", True),
)


@dataclass(frozen=True)
class PaperExternalCostAssumptionRow:
    cost_name: str
    cost_scope: str
    amount: Decimal
    amortize_over_trades: int | None
    reason: str
    flags: tuple[tuple[str, bool], ...] = HARD_FLAGS

    def __post_init__(self) -> None:
        _require_canonical_string("cost_name", self.cost_name)
        _require_cost_scope("cost_scope", self.cost_scope)
        object.__setattr__(
            self,
            "amount",
            _normalize_nonnegative_decimal("amount", self.amount),
        )
        object.__setattr__(
            self,
            "amortize_over_trades",
            _normalize_amortize_over_trades(self.amortize_over_trades),
        )
        _require_canonical_string("reason", self.reason)
        object.__setattr__(self, "flags", _normalize_flags(self.flags))


@dataclass(frozen=True)
class PaperExternalCostAssumptionsReport:
    generated_at: datetime
    config_version: str
    row_count: int
    total_account_cost: Decimal
    total_cycle_cost: Decimal
    total_market_cost: Decimal
    total_trade_cost: Decimal
    per_trade_cost_estimate: Decimal
    rows: tuple[PaperExternalCostAssumptionRow, ...]
    flags: tuple[tuple[str, bool], ...] = HARD_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("row_count", self.row_count)
        for field_name in (
            "total_account_cost",
            "total_cycle_cost",
            "total_market_cost",
            "total_trade_cost",
            "per_trade_cost_estimate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "flags", _normalize_flags(self.flags))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_external_cost_assumptions_report(
    *,
    generated_at: datetime,
    config_version: str,
    rows: Iterable[PaperExternalCostAssumptionRow],
) -> PaperExternalCostAssumptionsReport:
    """Aggregate caller-supplied external costs without external side effects."""

    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_canonical_string("config_version", config_version)

    normalized_rows = _normalize_rows(rows)
    return PaperExternalCostAssumptionsReport(
        generated_at=_as_utc(generated_at),
        config_version=config_version,
        row_count=len(normalized_rows),
        total_account_cost=_scope_total(normalized_rows, "account"),
        total_cycle_cost=_scope_total(normalized_rows, "cycle"),
        total_market_cost=_scope_total(normalized_rows, "market"),
        total_trade_cost=_scope_total(normalized_rows, "trade"),
        per_trade_cost_estimate=_per_trade_cost_estimate(normalized_rows),
        rows=normalized_rows,
        flags=HARD_FLAGS,
    )


def _normalize_rows(
    rows: Iterable[PaperExternalCostAssumptionRow],
) -> tuple[PaperExternalCostAssumptionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError(
            "rows must be an iterable of PaperExternalCostAssumptionRow values",
        )
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must be an iterable of PaperExternalCostAssumptionRow values",
        ) from exc
    for row in normalized:
        if type(row) is not PaperExternalCostAssumptionRow:
            raise ValueError(
                "rows must contain only PaperExternalCostAssumptionRow values",
            )
        _require_flags(row.flags)
    return normalized


def _validate_report_consistency(report: PaperExternalCostAssumptionsReport) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    expected_totals = {
        "total_account_cost": _scope_total(report.rows, "account"),
        "total_cycle_cost": _scope_total(report.rows, "cycle"),
        "total_market_cost": _scope_total(report.rows, "market"),
        "total_trade_cost": _scope_total(report.rows, "trade"),
        "per_trade_cost_estimate": _per_trade_cost_estimate(report.rows),
    }
    for field_name, expected_value in expected_totals.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _scope_total(
    rows: Iterable[PaperExternalCostAssumptionRow],
    cost_scope: str,
) -> Decimal:
    total = ZERO
    for row in rows:
        if row.cost_scope == cost_scope:
            total = _add_decimal(total, row.amount)
    return _quantize(total)


def _per_trade_cost_estimate(rows: Iterable[PaperExternalCostAssumptionRow]) -> Decimal:
    total = ZERO
    for row in rows:
        if row.cost_scope == "trade":
            total = _add_decimal(total, row.amount)
        elif row.amortize_over_trades is not None:
            total = _add_decimal(
                total,
                _divide_decimal(row.amount, row.amortize_over_trades),
            )
    return _quantize(total)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _divide_decimal(left: Decimal, right: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / Decimal(right))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _normalize_decimal(field_name, value)
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_amortize_over_trades(value: int | None) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise ValueError("amortize_over_trades must be an int or None")
    if value <= 0:
        raise ValueError("amortize_over_trades must be positive")
    return value


def _normalize_flags(
    flags: Iterable[tuple[str, bool]],
) -> tuple[tuple[str, bool], ...]:
    if isinstance(flags, (str, bytes)):
        raise ValueError("flags must be an iterable")
    try:
        normalized = tuple(flags)
    except TypeError as exc:
        raise ValueError("flags must be an iterable") from exc
    _require_flags(normalized)
    return normalized


def _require_flags(flags: tuple[tuple[str, bool], ...]) -> None:
    if flags != HARD_FLAGS:
        raise ValueError("flags must exactly match paper_only/report_only/readonly")
    for flag_name, flag_value in flags:
        if type(flag_name) is not str:
            raise ValueError("flags names must be strings")
        if type(flag_value) is not bool:
            raise ValueError("flags values must be bools")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_cost_scope(field_name: str, value: str) -> None:
    if type(value) is not str or value not in VALID_SCOPES:
        raise ValueError(f"{field_name} must be account, cycle, market, or trade")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperExternalCostAssumptionRow",
    "PaperExternalCostAssumptionsReport",
    "build_paper_external_cost_assumptions_report",
)
