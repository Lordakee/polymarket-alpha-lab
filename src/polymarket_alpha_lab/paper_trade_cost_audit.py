"""Paper-only cost audit over persisted paper-trade records.

Pure arithmetic over already-typed ``PaperTradeRecord`` values. This module is
local/report-only: it does not fetch markets, construct API clients, authenticate,
read wallets, place orders, rank investments, recommend trades, or provide
financial advice.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.journal import PaperTradeRecord


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
YES_NAMES = {"yes", "true", "long"}
NO_NAMES = {"no", "false", "short"}


@dataclass(frozen=True)
class PaperTradeCostAuditConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperTradeCostAuditReport:
    generated_at: datetime
    config_version: str
    trade_count: int
    total_filled_size: Decimal
    total_requested_size: Decimal
    fill_rate: Decimal | None
    mean_theoretical_edge: Decimal | None
    mean_cost_adjusted_edge: Decimal | None
    mean_edge_cost_drag: Decimal | None
    total_edge_cost_drag: Decimal | None
    mean_research_slippage: Decimal | None
    mean_fill_slippage: Decimal | None
    partial_fill_count: int
    negative_cost_adjusted_edge_count: int
    largest_single_trade_cost_drag: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "trade_count",
            "partial_fill_count",
            "negative_cost_adjusted_edge_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_filled_size",
            "total_requested_size",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_optional_probability_decimal("fill_rate", self.fill_rate)
        for field_name in (
            "mean_theoretical_edge",
            "mean_cost_adjusted_edge",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "mean_edge_cost_drag",
            "total_edge_cost_drag",
            "mean_research_slippage",
            "mean_fill_slippage",
            "largest_single_trade_cost_drag",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_trade_cost_audit_report(
    trade_records: Iterable[PaperTradeRecord],
    *,
    config: PaperTradeCostAuditConfig,
    generated_at: datetime,
) -> PaperTradeCostAuditReport:
    """Aggregate paper-trade costs and edge drag from local journal records."""

    if type(config) is not PaperTradeCostAuditConfig:
        raise ValueError("config must be a PaperTradeCostAuditConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    generated_at_utc = _as_utc_datetime("generated_at", generated_at)
    trades = _normalize_trade_records(trade_records)
    _reject_future_trade_evidence(trades, generated_at_utc)
    if not trades:
        return PaperTradeCostAuditReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            trade_count=0,
            total_filled_size=ZERO,
            total_requested_size=ZERO,
            fill_rate=None,
            mean_theoretical_edge=None,
            mean_cost_adjusted_edge=None,
            mean_edge_cost_drag=None,
            total_edge_cost_drag=None,
            mean_research_slippage=None,
            mean_fill_slippage=None,
            partial_fill_count=0,
            negative_cost_adjusted_edge_count=0,
            largest_single_trade_cost_drag=None,
        )

    total_filled_size = sum(
        (trade.fill_filled_size for trade in trades),
        ZERO,
    )
    total_requested_size = sum(
        (trade.order_requested_size for trade in trades),
        ZERO,
    )
    # PaperTradeRecord requires the research edge/slippage fields as Decimals;
    # only fill_slippage_estimate is optional and therefore filtered below.
    edge_drags = tuple(_edge_cost_drag(trade) for trade in trades)
    realized_edge_drags = tuple(
        drag * trade.fill_filled_size
        for drag, trade in zip(edge_drags, trades, strict=True)
    )
    fill_slippages = tuple(
        trade.fill_slippage_estimate
        for trade in trades
        if trade.fill_slippage_estimate is not None
    )

    return PaperTradeCostAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        trade_count=len(trades),
        total_filled_size=total_filled_size,
        total_requested_size=total_requested_size,
        fill_rate=_optional_ratio(total_filled_size, total_requested_size),
        mean_theoretical_edge=_mean(
            tuple(trade.research_theoretical_edge for trade in trades),
        ),
        mean_cost_adjusted_edge=_mean(
            tuple(trade.research_cost_adjusted_edge for trade in trades),
        ),
        mean_edge_cost_drag=_mean(edge_drags),
        total_edge_cost_drag=_quantize_ratio(sum(realized_edge_drags, ZERO)),
        mean_research_slippage=_mean(
            tuple(trade.research_slippage_estimate for trade in trades),
        ),
        mean_fill_slippage=_mean(fill_slippages),
        partial_fill_count=sum(1 for trade in trades if trade.fill_status == "partial"),
        negative_cost_adjusted_edge_count=sum(
            1 for trade in trades if trade.research_cost_adjusted_edge < ZERO
        ),
        largest_single_trade_cost_drag=_quantize_ratio(max(realized_edge_drags)),
    )


def _normalize_trade_records(
    trade_records: Iterable[PaperTradeRecord],
) -> tuple[PaperTradeRecord, ...]:
    if isinstance(trade_records, (str, bytes)):
        raise ValueError("trade_records must be an iterable of PaperTradeRecord values")
    try:
        trades = tuple(trade_records)
    except TypeError as exc:
        raise ValueError(
            "trade_records must be an iterable of PaperTradeRecord values",
        ) from exc
    for trade in trades:
        if type(trade) is not PaperTradeRecord:
            raise ValueError("trade_records must contain only PaperTradeRecord values")
        _validate_trade_record(trade)
    return trades


def _validate_trade_record(trade: PaperTradeRecord) -> None:
    for field_name in (
        "outcome_name",
        "fill_status",
    ):
        _require_canonical_string(field_name, getattr(trade, field_name))
    _require_binary_outcome_name(trade.outcome_name)
    if trade.order_side not in ("buy", "sell"):
        raise ValueError("order_side must be buy or sell")
    if trade.fill_status not in ("complete", "partial"):
        raise ValueError("fill_status must be complete or partial")

    for field_name in (
        "research_theoretical_edge",
        "research_cost_adjusted_edge",
    ):
        _require_decimal(field_name, getattr(trade, field_name))
    for field_name in (
        "order_requested_size",
        "fill_filled_size",
        "max_executable_size",
    ):
        _require_positive_decimal(field_name, getattr(trade, field_name))
    for field_name in (
        "fill_unfilled_size",
        "research_slippage_estimate",
    ):
        _require_nonnegative_decimal(field_name, getattr(trade, field_name))
    _require_optional_nonnegative_decimal(
        "fill_slippage_estimate",
        trade.fill_slippage_estimate,
    )
    for field_name in (
        "research_expected_entry_price",
        "research_fair_value_estimate",
        "fill_average_price",
        "fill_worst_price",
        "fill_best_bid",
        "fill_best_ask",
        "fill_midpoint",
    ):
        _require_optional_probability_decimal(field_name, getattr(trade, field_name))
    if trade.fill_filled_size + trade.fill_unfilled_size != trade.order_requested_size:
        raise ValueError("fill accounting must match requested size")
    expected_fill_status = "complete" if trade.fill_unfilled_size == ZERO else "partial"
    if trade.fill_status != expected_fill_status:
        raise ValueError("fill_status must match fill accounting")
    if trade.order_requested_size > trade.max_executable_size:
        raise ValueError("order_requested_size must not exceed max_executable_size")
    if trade.fill_filled_size > trade.order_requested_size:
        raise ValueError("fill_filled_size must not exceed order_requested_size")


def _reject_future_trade_evidence(
    trades: tuple[PaperTradeRecord, ...],
    generated_at: datetime,
) -> None:
    for trade in trades:
        field_value = _as_utc_datetime(
            "decision_timestamp_utc",
            trade.decision_timestamp_utc,
        )
        if field_value > generated_at:
            raise ValueError("decision_timestamp_utc must not be after generated_at")


def _edge_cost_drag(trade: PaperTradeRecord) -> Decimal:
    return max(trade.research_theoretical_edge - trade.research_cost_adjusted_edge, ZERO)


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize_ratio(numerator / denominator)


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / Decimal(len(values)))


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc_datetime(field_name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_binary_outcome_name(value: str) -> None:
    if value.strip().lower() not in YES_NAMES | NO_NAMES:
        raise ValueError("outcome_name must be a binary yes/no outcome alias")


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None")


def _require_present(field_name: str, value: object) -> None:
    if value is None:
        raise ValueError(f"{field_name} is required when trade_count is positive")


def _validate_report_consistency(report: PaperTradeCostAuditReport) -> None:
    if report.total_filled_size > report.total_requested_size:
        raise ValueError("total_filled_size must not exceed total_requested_size")
    if report.partial_fill_count > report.trade_count:
        raise ValueError("partial_fill_count cannot exceed trade_count")
    if report.negative_cost_adjusted_edge_count > report.trade_count:
        raise ValueError("negative_cost_adjusted_edge_count cannot exceed trade_count")
    if report.trade_count == 0:
        _require_zero_decimal("total_filled_size", report.total_filled_size)
        _require_zero_decimal("total_requested_size", report.total_requested_size)
        for field_name in (
            "fill_rate",
            "mean_theoretical_edge",
            "mean_cost_adjusted_edge",
            "mean_edge_cost_drag",
            "total_edge_cost_drag",
            "mean_research_slippage",
            "mean_fill_slippage",
            "largest_single_trade_cost_drag",
        ):
            _require_none(field_name, getattr(report, field_name))
        _require_zero("partial_fill_count", report.partial_fill_count)
        _require_zero(
            "negative_cost_adjusted_edge_count",
            report.negative_cost_adjusted_edge_count,
        )
        return
    _require_positive_decimal("total_requested_size", report.total_requested_size)
    _require_positive_decimal("total_filled_size", report.total_filled_size)
    _require_present("fill_rate", report.fill_rate)
    for field_name in (
        "mean_theoretical_edge",
        "mean_cost_adjusted_edge",
        "mean_edge_cost_drag",
        "total_edge_cost_drag",
        "mean_research_slippage",
        "largest_single_trade_cost_drag",
    ):
        _require_present(field_name, getattr(report, field_name))
    expected_fill_rate = _optional_ratio(
        report.total_filled_size,
        report.total_requested_size,
    )
    if report.fill_rate != expected_fill_rate:
        raise ValueError("fill_rate must match filled and requested size")
    if report.mean_edge_cost_drag is not None and report.mean_edge_cost_drag < ZERO:
        raise ValueError("mean_edge_cost_drag must be nonnegative")
    if report.total_edge_cost_drag is not None and report.total_edge_cost_drag < ZERO:
        raise ValueError("total_edge_cost_drag must be nonnegative")
    if (
        report.largest_single_trade_cost_drag is not None
        and report.largest_single_trade_cost_drag < ZERO
    ):
        raise ValueError("largest_single_trade_cost_drag must be nonnegative")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero")


def _require_zero_decimal(field_name: str, value: Decimal) -> None:
    if value != ZERO:
        raise ValueError(f"{field_name} must be zero")


__all__ = (
    "PaperTradeCostAuditConfig",
    "PaperTradeCostAuditReport",
    "build_paper_trade_cost_audit_report",
)
