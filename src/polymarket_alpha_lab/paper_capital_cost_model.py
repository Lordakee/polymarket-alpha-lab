"""Paper-only capital cost model for strategy research reports.

Pure arithmetic over caller-supplied assumptions. This module is local,
paper-only, read-only, and report-only: it does not fetch data, mutate external
state, or construct exchange instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
READY = "ready"
WATCH = "watch"
BLOCKED = "blocked"
REPORT_STATUSES = {READY, WATCH, BLOCKED}


@dataclass(frozen=True)
class PaperCapitalCostAssumptions:
    deposit_cost: Decimal
    withdrawal_cost: Decimal
    bridge_cost: Decimal
    onchain_cost: Decimal
    finalization_cost: Decimal
    funding_cost: Decimal
    expected_trade_count: int
    expected_total_notional: Decimal
    holding_period_days: Decimal | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "deposit_cost",
            "withdrawal_cost",
            "bridge_cost",
            "onchain_cost",
            "finalization_cost",
            "funding_cost",
            "expected_total_notional",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_nonnegative_int("expected_trade_count", self.expected_trade_count)
        _require_optional_nonnegative_decimal(
            "holding_period_days",
            self.holding_period_days,
        )


@dataclass(frozen=True)
class PaperCapitalCostModelConfig:
    config_version: str
    watch_cost_per_trade: Decimal | None = None
    max_cost_per_trade: Decimal | None = None
    watch_cost_per_notional: Decimal | None = None
    max_cost_per_notional: Decimal | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_cost_per_trade",
            "max_cost_per_trade",
            "watch_cost_per_notional",
            "max_cost_per_notional",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        if (
            self.watch_cost_per_trade is not None
            and self.max_cost_per_trade is not None
            and self.watch_cost_per_trade > self.max_cost_per_trade
        ):
            raise ValueError("watch_cost_per_trade must not exceed max_cost_per_trade")
        if (
            self.watch_cost_per_notional is not None
            and self.max_cost_per_notional is not None
            and self.watch_cost_per_notional > self.max_cost_per_notional
        ):
            raise ValueError(
                "watch_cost_per_notional must not exceed max_cost_per_notional",
            )


@dataclass(frozen=True)
class PaperCapitalCostReport:
    generated_at: datetime
    config_version: str
    deposit_cost: Decimal
    withdrawal_cost: Decimal
    bridge_cost: Decimal
    onchain_cost: Decimal
    finalization_cost: Decimal
    funding_cost: Decimal
    expected_trade_count: int
    expected_total_notional: Decimal
    holding_period_days: Decimal | None
    total_fixed_cost: Decimal
    total_variable_cost: Decimal
    total_cost: Decimal
    cost_per_trade: Decimal | None
    cost_per_notional: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc_datetime("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "deposit_cost",
            "withdrawal_cost",
            "bridge_cost",
            "onchain_cost",
            "finalization_cost",
            "funding_cost",
            "expected_total_notional",
            "total_fixed_cost",
            "total_variable_cost",
            "total_cost",
        ):
            _require_quantized_nonnegative_decimal(
                field_name,
                getattr(self, field_name),
            )
        _require_nonnegative_int("expected_trade_count", self.expected_trade_count)
        _require_optional_quantized_nonnegative_decimal(
            "holding_period_days",
            self.holding_period_days,
        )
        _require_optional_quantized_nonnegative_decimal(
            "cost_per_trade",
            self.cost_per_trade,
        )
        _require_optional_quantized_nonnegative_decimal(
            "cost_per_notional",
            self.cost_per_notional,
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be ready, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_capital_cost_report(
    assumptions: PaperCapitalCostAssumptions,
    *,
    config: PaperCapitalCostModelConfig,
    generated_at: datetime,
) -> PaperCapitalCostReport:
    """Amortize paper capital costs into research friction metrics."""

    if type(assumptions) is not PaperCapitalCostAssumptions:
        raise ValueError("assumptions must be a PaperCapitalCostAssumptions")
    if type(config) is not PaperCapitalCostModelConfig:
        raise ValueError("config must be a PaperCapitalCostModelConfig")
    generated_at_utc = _as_utc_datetime("generated_at", generated_at)

    deposit_cost = _quantize_decimal(assumptions.deposit_cost)
    withdrawal_cost = _quantize_decimal(assumptions.withdrawal_cost)
    bridge_cost = _quantize_decimal(assumptions.bridge_cost)
    onchain_cost = _quantize_decimal(assumptions.onchain_cost)
    finalization_cost = _quantize_decimal(assumptions.finalization_cost)
    funding_cost = _quantize_decimal(assumptions.funding_cost)
    expected_total_notional = _quantize_decimal(assumptions.expected_total_notional)
    holding_period_days = _optional_quantize_decimal(assumptions.holding_period_days)

    total_fixed_cost = _quantize_decimal(
        deposit_cost
        + withdrawal_cost
        + bridge_cost
        + onchain_cost
        + finalization_cost,
    )
    total_variable_cost = funding_cost
    total_cost = _quantize_decimal(total_fixed_cost + total_variable_cost)
    cost_per_trade = _optional_ratio(
        total_cost,
        Decimal(assumptions.expected_trade_count),
    )
    cost_per_notional = _optional_ratio(total_cost, expected_total_notional)
    status, reason_codes = _status_and_reason_codes(
        total_cost=total_cost,
        expected_trade_count=assumptions.expected_trade_count,
        expected_total_notional=expected_total_notional,
        cost_per_trade=cost_per_trade,
        cost_per_notional=cost_per_notional,
        config=config,
    )

    return PaperCapitalCostReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        deposit_cost=deposit_cost,
        withdrawal_cost=withdrawal_cost,
        bridge_cost=bridge_cost,
        onchain_cost=onchain_cost,
        finalization_cost=finalization_cost,
        funding_cost=funding_cost,
        expected_trade_count=assumptions.expected_trade_count,
        expected_total_notional=expected_total_notional,
        holding_period_days=holding_period_days,
        total_fixed_cost=total_fixed_cost,
        total_variable_cost=total_variable_cost,
        total_cost=total_cost,
        cost_per_trade=cost_per_trade,
        cost_per_notional=cost_per_notional,
        status=status,
        reason_codes=reason_codes,
    )


def _status_and_reason_codes(
    *,
    total_cost: Decimal,
    expected_trade_count: int,
    expected_total_notional: Decimal,
    cost_per_trade: Decimal | None,
    cost_per_notional: Decimal | None,
    config: PaperCapitalCostModelConfig,
) -> tuple[str, tuple[str, ...]]:
    blocked_reasons: list[str] = []
    watch_reasons: list[str] = []

    if total_cost == ZERO:
        return READY, ("zero_capital_cost_assumption",)
    if expected_trade_count == 0:
        blocked_reasons.append("missing_expected_trade_count_for_positive_cost")
    if expected_total_notional == ZERO:
        blocked_reasons.append("missing_expected_total_notional_for_positive_cost")
    if (
        cost_per_trade is not None
        and config.max_cost_per_trade is not None
        and cost_per_trade > config.max_cost_per_trade
    ):
        blocked_reasons.append("cost_per_trade_above_max")
    if (
        cost_per_notional is not None
        and config.max_cost_per_notional is not None
        and cost_per_notional > config.max_cost_per_notional
    ):
        blocked_reasons.append("cost_per_notional_above_max")
    if blocked_reasons:
        return BLOCKED, tuple(blocked_reasons)

    if (
        cost_per_trade is not None
        and config.watch_cost_per_trade is not None
        and cost_per_trade > config.watch_cost_per_trade
    ):
        watch_reasons.append("cost_per_trade_above_watch")
    if (
        cost_per_notional is not None
        and config.watch_cost_per_notional is not None
        and cost_per_notional > config.watch_cost_per_notional
    ):
        watch_reasons.append("cost_per_notional_above_watch")
    if watch_reasons:
        return WATCH, tuple(watch_reasons)
    return READY, ("capital_cost_ready",)


def _validate_report_consistency(report: PaperCapitalCostReport) -> None:
    expected_fixed_cost = _quantize_decimal(
        report.deposit_cost
        + report.withdrawal_cost
        + report.bridge_cost
        + report.onchain_cost
        + report.finalization_cost,
    )
    if report.total_fixed_cost != expected_fixed_cost:
        raise ValueError("total_fixed_cost must match fixed cost components")
    if report.total_variable_cost != report.funding_cost:
        raise ValueError("total_variable_cost must match funding_cost")
    expected_total_cost = _quantize_decimal(
        report.total_fixed_cost + report.total_variable_cost,
    )
    if report.total_cost != expected_total_cost:
        raise ValueError("total_cost must match fixed and variable costs")

    expected_cost_per_trade = _optional_ratio(
        report.total_cost,
        Decimal(report.expected_trade_count),
    )
    if report.cost_per_trade != expected_cost_per_trade:
        raise ValueError("cost_per_trade must match total cost and trade count")
    expected_cost_per_notional = _optional_ratio(
        report.total_cost,
        report.expected_total_notional,
    )
    if report.cost_per_notional != expected_cost_per_notional:
        raise ValueError("cost_per_notional must match total cost and notional")


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize_decimal(numerator / denominator)


def _as_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of strings")
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    if not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_quantized_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_optional_quantized_nonnegative_decimal(
    field_name: str,
    value: object,
) -> None:
    if value is None:
        return
    _require_quantized_nonnegative_decimal(field_name, value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _optional_quantize_decimal(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _quantize_decimal(value)


__all__ = (
    "PaperCapitalCostAssumptions",
    "PaperCapitalCostModelConfig",
    "PaperCapitalCostReport",
    "build_paper_capital_cost_report",
)
