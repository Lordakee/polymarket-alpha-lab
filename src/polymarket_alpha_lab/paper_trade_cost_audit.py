"""Paper-only cost audit over persisted paper-trade records.

Pure arithmetic over already-typed ``PaperTradeRecord`` values. This module is
local/report-only: it does not fetch markets, construct API clients, authenticate,
read wallets, place orders, rank investments, recommend trades, or provide
financial advice.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.journal import PaperTradeRecord


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")


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
            _require_optional_decimal(field_name, getattr(self, field_name))
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


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

    trades = _normalize_trade_records(trade_records)
    if not trades:
        return PaperTradeCostAuditReport(
            generated_at=generated_at,
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
    edge_drags = tuple(
        trade.research_theoretical_edge - trade.research_cost_adjusted_edge
        for trade in trades
    )
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
        generated_at=generated_at,
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
    return trades


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
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
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


__all__ = (
    "PaperTradeCostAuditConfig",
    "PaperTradeCostAuditReport",
    "build_paper_trade_cost_audit_report",
)
