"""Paper-only adapter into canonical probability side-edge reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeConfig,
    PaperProbabilitySideEdgeInput,
    PaperProbabilitySideEdgeReport,
    build_paper_probability_side_edge_report,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)


@dataclass(frozen=True)
class PaperSideEdgeAdapterInput:
    market_slug: str
    question: str
    side: str
    forecast_probability: Decimal
    side_price: Decimal
    fee_cost_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal
    capital_cost_per_share: Decimal
    requested_paper_shares: Decimal
    max_executable_shares: Decimal
    market_context_fresh: bool
    settlement_context_fresh: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "side_price",
            _normalize_probability("side_price", self.side_price),
        )
        for field_name in (
            "fee_cost_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "funding_cost_per_share",
            "finalization_cost_per_share",
            "time_cost_per_share",
            "risk_cost_per_share",
            "capital_cost_per_share",
            "requested_paper_shares",
            "max_executable_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("market_context_fresh", self.market_context_fresh)
        _require_bool("settlement_context_fresh", self.settlement_context_fresh)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags(self)


PaperSideEdgeStrategyRow = PaperSideEdgeAdapterInput


@dataclass(frozen=True)
class PaperSideEdgeAdapterConfig:
    config_version: str
    min_net_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_net_probability_edge",
            _normalize_probability(
                "min_net_probability_edge",
                self.min_net_probability_edge,
            ),
        )
        _require_safety_flags(self)


def paper_side_edge_inputs_from_strategy_rows(
    rows: Iterable[PaperSideEdgeAdapterInput],
) -> tuple[PaperProbabilitySideEdgeInput, ...]:
    normalized_rows = _normalize_rows(rows)
    return tuple(_paper_probability_input_from_row(row) for row in normalized_rows)


def paper_side_edge_inputs_from_adapter_inputs(
    rows: Iterable[PaperSideEdgeAdapterInput],
) -> tuple[PaperProbabilitySideEdgeInput, ...]:
    return paper_side_edge_inputs_from_strategy_rows(rows)


def build_paper_side_edge_report_from_strategy_rows(
    rows: Iterable[PaperSideEdgeAdapterInput],
    *,
    config: PaperSideEdgeAdapterConfig,
    generated_at: datetime,
) -> PaperProbabilitySideEdgeReport:
    if type(config) is not PaperSideEdgeAdapterConfig:
        raise ValueError("config must be a PaperSideEdgeAdapterConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_safety_flags(config)

    return build_paper_probability_side_edge_report(
        paper_side_edge_inputs_from_strategy_rows(rows),
        config=PaperProbabilitySideEdgeConfig(
            config_version=config.config_version,
            min_net_probability_edge=config.min_net_probability_edge,
        ),
        generated_at=generated_at,
    )


def build_paper_side_edge_report_from_adapter_inputs(
    rows: Iterable[PaperSideEdgeAdapterInput],
    *,
    config: PaperSideEdgeAdapterConfig,
    generated_at: datetime,
) -> PaperProbabilitySideEdgeReport:
    return build_paper_side_edge_report_from_strategy_rows(
        rows,
        config=config,
        generated_at=generated_at,
    )


def build_paper_side_edge_report(
    rows: Iterable[PaperSideEdgeAdapterInput],
    *,
    config: PaperSideEdgeAdapterConfig,
    generated_at: datetime,
) -> PaperProbabilitySideEdgeReport:
    return build_paper_side_edge_report_from_strategy_rows(
        rows,
        config=config,
        generated_at=generated_at,
    )


def _paper_probability_input_from_row(
    row: PaperSideEdgeAdapterInput,
) -> PaperProbabilitySideEdgeInput:
    return PaperProbabilitySideEdgeInput(
        market_slug=row.market_slug,
        question=row.question,
        side=row.side,
        forecast_probability=row.forecast_probability,
        side_price=row.side_price,
        fee_cost_per_share=row.fee_cost_per_share,
        spread_cost_per_share=row.spread_cost_per_share,
        slippage_cost_per_share=row.slippage_cost_per_share,
        funding_cost_per_share=row.funding_cost_per_share,
        finalization_cost_per_share=row.finalization_cost_per_share,
        time_cost_per_share=row.time_cost_per_share,
        risk_cost_per_share=row.risk_cost_per_share,
        capital_cost_per_share=row.capital_cost_per_share,
        requested_paper_shares=row.requested_paper_shares,
        max_executable_shares=row.max_executable_shares,
        market_context_fresh=row.market_context_fresh,
        settlement_context_fresh=row.settlement_context_fresh,
        reason_codes=row.reason_codes,
    )


def _normalize_rows(
    rows: Iterable[PaperSideEdgeAdapterInput],
) -> tuple[PaperSideEdgeAdapterInput, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of PaperSideEdgeAdapterInput values")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must be an iterable of PaperSideEdgeAdapterInput values",
        ) from exc
    for row in normalized:
        if type(row) is not PaperSideEdgeAdapterInput:
            raise ValueError("rows must contain only PaperSideEdgeAdapterInput values")
        _require_safety_flags(row)
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "PaperSideEdgeAdapterInput",
    "PaperSideEdgeStrategyRow",
    "PaperSideEdgeAdapterConfig",
    "paper_side_edge_inputs_from_strategy_rows",
    "paper_side_edge_inputs_from_adapter_inputs",
    "build_paper_side_edge_report_from_strategy_rows",
    "build_paper_side_edge_report_from_adapter_inputs",
    "build_paper_side_edge_report",
)
