"""Paper-only capital-cost adapter for probability side-edge inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_capital_cost import (
    PaperCapitalCostConfig,
    build_paper_capital_cost_report,
)
from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeInput,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SIDES = frozenset(("yes", "no"))
GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class PaperCapitalCostSideEdgeAdapterInput:
    market_slug: str
    question: str
    side: str
    forecast_probability: Decimal
    side_price: Decimal
    annual_capital_cost_rate: Decimal
    days_locked: int | None
    requested_paper_shares: Decimal
    max_executable_shares: Decimal
    fee_cost_per_share: Decimal = ZERO
    spread_cost_per_share: Decimal = ZERO
    slippage_cost_per_share: Decimal = ZERO
    funding_cost_per_share: Decimal = ZERO
    finalization_cost_per_share: Decimal = ZERO
    time_cost_per_share: Decimal = ZERO
    risk_cost_per_share: Decimal = ZERO
    market_context_fresh: bool = True
    settlement_context_fresh: bool = True
    reason_codes: tuple[str, ...] = ("strategy_candidate",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _must_text("market_slug", self.market_slug)
        _must_text("question", self.question)
        if self.side not in SIDES:
            raise ValueError("side must be yes or no")
        for field_name in ("forecast_probability", "side_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _must_decimal_min_zero(
            "annual_capital_cost_rate",
            self.annual_capital_cost_rate,
        )
        if self.days_locked is not None:
            _must_int_min_zero("days_locked", self.days_locked)
        for field_name in (
            "requested_paper_shares",
            "max_executable_shares",
            "fee_cost_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "funding_cost_per_share",
            "finalization_cost_per_share",
            "time_cost_per_share",
            "risk_cost_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _must_bool("market_context_fresh", self.market_context_fresh)
        _must_bool("settlement_context_fresh", self.settlement_context_fresh)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _must_true("paper_only", self.paper_only)
        _must_true("report_only", self.report_only)
        _must_true("readonly", self.readonly)


def paper_capital_cost_side_edge_input(
    source: PaperCapitalCostSideEdgeAdapterInput,
) -> PaperProbabilitySideEdgeInput:
    """Return a canonical side-edge input with computed capital cost per share."""

    if type(source) is not PaperCapitalCostSideEdgeAdapterInput:
        raise ValueError("source must be a PaperCapitalCostSideEdgeAdapterInput")

    executable_shares = _executable_shares(
        source.requested_paper_shares,
        source.max_executable_shares,
    )
    reason_codes = source.reason_codes
    market_context_fresh = source.market_context_fresh
    settlement_context_fresh = source.settlement_context_fresh
    capital_cost_per_share = ZERO.quantize(QUANTUM)

    if source.days_locked is None:
        reason_codes = (*reason_codes, "missing_days_locked_for_capital_cost")
        market_context_fresh = False
        settlement_context_fresh = False
    elif executable_shares <= ZERO:
        reason_codes = (*reason_codes, "missing_paper_shares_for_capital_cost")
        market_context_fresh = False
    else:
        capital_cost_per_share = _capital_cost_per_share(
            source,
            executable_shares=executable_shares,
        )

    return PaperProbabilitySideEdgeInput(
        market_slug=source.market_slug,
        question=source.question,
        side=source.side,
        forecast_probability=source.forecast_probability,
        side_price=source.side_price,
        fee_cost_per_share=source.fee_cost_per_share,
        spread_cost_per_share=source.spread_cost_per_share,
        slippage_cost_per_share=source.slippage_cost_per_share,
        funding_cost_per_share=source.funding_cost_per_share,
        finalization_cost_per_share=source.finalization_cost_per_share,
        time_cost_per_share=source.time_cost_per_share,
        risk_cost_per_share=source.risk_cost_per_share,
        capital_cost_per_share=capital_cost_per_share,
        requested_paper_shares=source.requested_paper_shares,
        max_executable_shares=source.max_executable_shares,
        market_context_fresh=market_context_fresh,
        settlement_context_fresh=settlement_context_fresh,
        reason_codes=reason_codes,
    )


def _capital_cost_per_share(
    source: PaperCapitalCostSideEdgeAdapterInput,
    *,
    executable_shares: Decimal,
) -> Decimal:
    report = build_paper_capital_cost_report(
        (
            {
                "market_slug": source.market_slug,
                "question": source.question,
                "side": source.side,
                "paper_notional": _q(executable_shares * source.side_price),
                "paper_share_quantity": executable_shares,
                "days_locked": source.days_locked,
            },
        ),
        config=PaperCapitalCostConfig(
            config_version="paper-capital-cost-side-edge-adapter-v0",
            annual_capital_cost_rate=source.annual_capital_cost_rate,
        ),
        generated_at=GENERATED_AT,
    )
    return report.capital_cost_rows[0].capital_cost_per_share


def _executable_shares(
    requested_paper_shares: Decimal,
    max_executable_shares: Decimal,
) -> Decimal:
    if requested_paper_shares <= ZERO or max_executable_shares <= ZERO:
        return ZERO.quantize(QUANTUM)
    return min(requested_paper_shares, max_executable_shares)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _must_decimal(field_name, value)
    return _q(value)


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of strings")
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    if not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    normalized: list[str] = []
    for reason_code in sorted(reason_codes):
        _must_text("reason_codes", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _must_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _must_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _must_int_min_zero(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be at least zero")


def _must_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _must_decimal_min_zero(field_name: str, value: object) -> None:
    _must_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be at least zero")


def _must_true(field_name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


__all__ = (
    "PaperCapitalCostSideEdgeAdapterInput",
    "paper_capital_cost_side_edge_input",
)
