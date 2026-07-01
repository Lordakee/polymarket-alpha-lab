from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_capital_cost_side_edge_adapter import (
    PaperCapitalCostSideEdgeAdapterInput,
    paper_capital_cost_side_edge_input,
)
from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeInput,
)


ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def adapter_input(
    *,
    market_slug: str = "will-alpha-resolve-yes",
    question: str = "Will alpha resolve yes?",
    side: str = "yes",
    forecast_probability: Decimal = d("0.640000"),
    side_price: Decimal = d("0.500000"),
    annual_capital_cost_rate: Decimal = d("0.120000"),
    days_locked: int | None = 30,
    requested_paper_shares: Decimal = d("100.000000"),
    max_executable_shares: Decimal = d("100.000000"),
    fee_cost_per_share: Decimal = ZERO,
    spread_cost_per_share: Decimal = ZERO,
    slippage_cost_per_share: Decimal = ZERO,
    funding_cost_per_share: Decimal = ZERO,
    finalization_cost_per_share: Decimal = ZERO,
    time_cost_per_share: Decimal = ZERO,
    risk_cost_per_share: Decimal = ZERO,
    market_context_fresh: bool = True,
    settlement_context_fresh: bool = True,
    reason_codes: tuple[str, ...] = ("strategy_candidate",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperCapitalCostSideEdgeAdapterInput:
    return PaperCapitalCostSideEdgeAdapterInput(
        market_slug=market_slug,
        question=question,
        side=side,
        forecast_probability=forecast_probability,
        side_price=side_price,
        annual_capital_cost_rate=annual_capital_cost_rate,
        days_locked=days_locked,
        requested_paper_shares=requested_paper_shares,
        max_executable_shares=max_executable_shares,
        fee_cost_per_share=fee_cost_per_share,
        spread_cost_per_share=spread_cost_per_share,
        slippage_cost_per_share=slippage_cost_per_share,
        funding_cost_per_share=funding_cost_per_share,
        finalization_cost_per_share=finalization_cost_per_share,
        time_cost_per_share=time_cost_per_share,
        risk_cost_per_share=risk_cost_per_share,
        market_context_fresh=market_context_fresh,
        settlement_context_fresh=settlement_context_fresh,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_adapter_calculates_capital_cost_per_share_for_side_edge_input():
    result = paper_capital_cost_side_edge_input(
        adapter_input(
            side_price=d("0.500000"),
            annual_capital_cost_rate=d("0.120000"),
            days_locked=30,
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("80.000000"),
            fee_cost_per_share=d("0.010000"),
            reason_codes=("ranked", "strategy_candidate"),
        ),
    )

    assert type(result) is PaperProbabilitySideEdgeInput
    assert result == PaperProbabilitySideEdgeInput(
        market_slug="will-alpha-resolve-yes",
        question="Will alpha resolve yes?",
        side="yes",
        forecast_probability=d("0.640000"),
        side_price=d("0.500000"),
        fee_cost_per_share=d("0.010000"),
        spread_cost_per_share=ZERO,
        slippage_cost_per_share=ZERO,
        funding_cost_per_share=ZERO,
        finalization_cost_per_share=ZERO,
        time_cost_per_share=ZERO,
        risk_cost_per_share=ZERO,
        capital_cost_per_share=d("0.004932"),
        requested_paper_shares=d("100.000000"),
        max_executable_shares=d("80.000000"),
        market_context_fresh=True,
        settlement_context_fresh=True,
        reason_codes=("ranked", "strategy_candidate"),
    )


def test_adapter_uses_max_executable_shares_for_paper_notional():
    result = paper_capital_cost_side_edge_input(
        adapter_input(
            side_price=d("0.250000"),
            annual_capital_cost_rate=d("0.100000"),
            days_locked=365,
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("40.000000"),
        ),
    )

    assert result.capital_cost_per_share == d("0.025000")


def test_adapter_missing_days_locked_fails_closed_without_optimistic_zero_cost():
    result = paper_capital_cost_side_edge_input(
        adapter_input(
            days_locked=None,
            side_price=d("0.500000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
        ),
    )

    assert result.capital_cost_per_share == ZERO
    assert result.market_context_fresh is False
    assert result.settlement_context_fresh is False
    assert "missing_days_locked_for_capital_cost" in result.reason_codes


def test_adapter_zero_executable_shares_fails_closed_without_dividing_by_zero():
    result = paper_capital_cost_side_edge_input(
        adapter_input(
            requested_paper_shares=d("100.000000"),
            max_executable_shares=ZERO,
        ),
    )

    assert result.capital_cost_per_share == ZERO
    assert result.market_context_fresh is False
    assert "missing_paper_shares_for_capital_cost" in result.reason_codes


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("side", "maybe", "side"),
        ("forecast_probability", Decimal("-0.000001"), "forecast_probability"),
        ("side_price", Decimal("1.000001"), "side_price"),
        ("annual_capital_cost_rate", Decimal("-0.000001"), "annual_capital_cost_rate"),
        ("annual_capital_cost_rate", 0.12, "annual_capital_cost_rate"),
        ("days_locked", -1, "days_locked"),
        ("days_locked", Decimal("1"), "days_locked"),
        ("requested_paper_shares", Decimal("-0.000001"), "requested_paper_shares"),
        ("max_executable_shares", Decimal("NaN"), "max_executable_shares"),
    ),
)
def test_adapter_rejects_invalid_values(field_name, bad_value, match):
    with pytest.raises(ValueError, match=match):
        replace(adapter_input(), **{field_name: bad_value})


def test_adapter_dataclass_is_frozen_and_enforces_paper_safety_flags():
    source = adapter_input()

    with pytest.raises(FrozenInstanceError):
        source.side_price = d("0.400000")
    with pytest.raises(ValueError, match="paper_only"):
        replace(source, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(source, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(source, readonly=False)


def test_adapter_module_has_no_live_boundary_terms():
    import inspect
    import polymarket_alpha_lab.paper_capital_cost_side_edge_adapter as module

    source = inspect.getsource(module).lower()

    for forbidden in (
        "auth",
        "account",
        "wallet",
        "order",
        "sign",
        "submit",
        "cancel",
        "network",
        "client",
    ):
        assert forbidden not in source
