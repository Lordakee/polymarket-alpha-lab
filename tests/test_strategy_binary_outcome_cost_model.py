from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_binary_outcome_cost_model import (
    StrategyBinaryOutcomeCostAssumptions,
    StrategyBinaryOutcomeCostReport,
    build_strategy_binary_outcome_cost_report,
)


class _DecimalSubclass(Decimal):
    pass


def _assumptions(
    *,
    yes_price: Decimal = Decimal("0.620000"),
    no_price: Decimal = Decimal("0.410000"),
    estimated_event_probability: Decimal = Decimal("0.690000"),
    shares: Decimal = Decimal("100"),
    spread_buffer: Decimal = Decimal("0.010000"),
    slippage_buffer: Decimal = Decimal("0.005000"),
    taker_fee_rate: Decimal = Decimal("0.020000"),
) -> StrategyBinaryOutcomeCostAssumptions:
    return StrategyBinaryOutcomeCostAssumptions(
        yes_price=yes_price,
        no_price=no_price,
        estimated_event_probability=estimated_event_probability,
        shares=shares,
        spread_buffer=spread_buffer,
        slippage_buffer=slippage_buffer,
        taker_fee_rate=taker_fee_rate,
    )


def test_binary_outcome_cost_model_uses_event_payoff_not_asset_return():
    report = build_strategy_binary_outcome_cost_report(_assumptions())

    assert isinstance(report, StrategyBinaryOutcomeCostReport)
    assert report.yes_price == Decimal("0.620000")
    assert report.no_price == Decimal("0.410000")
    assert report.estimated_event_probability == Decimal("0.690000")
    assert report.shares == Decimal("100.000000")
    assert report.spread_buffer == Decimal("0.010000")
    assert report.slippage_buffer == Decimal("0.005000")
    assert report.taker_fee_rate == Decimal("0.020000")
    assert report.yes_gross_cost == Decimal("62.000000")
    assert report.no_gross_cost == Decimal("41.000000")
    assert report.yes_taker_fee == Decimal("1.240000")
    assert report.no_taker_fee == Decimal("0.820000")
    assert report.yes_entry_cost == Decimal("63.240000")
    assert report.no_entry_cost == Decimal("41.820000")
    assert report.yes_round_trip_fee_drag == Decimal("3.240000")
    assert report.no_round_trip_fee_drag == Decimal("2.820000")
    assert report.spread_slippage_buffer_cost == Decimal("1.500000")
    assert report.yes_total_cost == Decimal("66.740000")
    assert report.no_total_cost == Decimal("45.320000")
    assert report.yes_breakeven_probability == Decimal("0.667400")
    assert report.no_breakeven_probability == Decimal("0.453200")
    assert report.yes_net_expected_value == Decimal("2.260000")
    assert report.no_net_expected_value == Decimal("-14.320000")
    assert report.event_payoff_mode == "binary_probability_payoff"
    assert report.reason_codes == ("binary_event_payoff_model",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_binary_outcome_cost_model_quantizes_all_decimal_outputs_to_six_places():
    report = build_strategy_binary_outcome_cost_report(
        _assumptions(
            yes_price=Decimal("0.3333334"),
            no_price=Decimal("0.6666664"),
            estimated_event_probability=Decimal("0.4444444"),
            shares=Decimal("3"),
            spread_buffer=Decimal("0.0011114"),
            slippage_buffer=Decimal("0.0022224"),
        ),
    )

    assert report.yes_price == Decimal("0.333333")
    assert report.no_price == Decimal("0.666666")
    assert report.estimated_event_probability == Decimal("0.444444")
    assert report.shares == Decimal("3.000000")
    assert report.spread_buffer == Decimal("0.001111")
    assert report.slippage_buffer == Decimal("0.002222")
    assert report.yes_gross_cost == Decimal("0.999999")
    assert report.no_gross_cost == Decimal("1.999998")
    assert report.yes_total_cost == Decimal("1.089998")
    assert report.no_total_cost == Decimal("2.109997")
    assert report.yes_breakeven_probability == Decimal("0.363333")
    assert report.no_breakeven_probability == Decimal("0.703332")
    assert report.yes_net_expected_value == Decimal("0.243334")
    assert report.no_net_expected_value == Decimal("-0.443329")


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("yes_price", Decimal("-0.000001")),
        ("yes_price", Decimal("1.000001")),
        ("no_price", Decimal("-0.000001")),
        ("no_price", Decimal("1.000001")),
        ("estimated_event_probability", Decimal("-0.000001")),
        ("estimated_event_probability", Decimal("1.000001")),
        ("shares", Decimal("0")),
        ("spread_buffer", Decimal("-0.000001")),
        ("slippage_buffer", Decimal("-0.000001")),
        ("taker_fee_rate", Decimal("-0.000001")),
    ),
)
def test_binary_outcome_assumptions_reject_invalid_ranges(
    field_name: str,
    field_value: Decimal,
):
    with pytest.raises(ValueError, match=field_name):
        _assumptions(**{field_name: field_value})


def test_binary_outcome_assumptions_reject_non_decimal_inputs():
    with pytest.raises(ValueError, match="yes_price"):
        _assumptions(yes_price=0.62)
    with pytest.raises(ValueError, match="no_price"):
        _assumptions(no_price=_DecimalSubclass("0.410000"))
    with pytest.raises(ValueError, match="shares"):
        _assumptions(shares="100")


def test_binary_outcome_builder_rejects_invalid_top_level_inputs():
    with pytest.raises(ValueError, match="assumptions"):
        build_strategy_binary_outcome_cost_report(object())


def test_binary_outcome_report_revalidates_derived_metric_consistency():
    report = build_strategy_binary_outcome_cost_report(_assumptions())

    with pytest.raises(ValueError, match="yes_total_cost"):
        replace(report, yes_total_cost=Decimal("66.730000"))
    with pytest.raises(ValueError, match="no_total_cost"):
        replace(report, no_total_cost=Decimal("45.310000"))
    with pytest.raises(ValueError, match="yes_breakeven_probability"):
        replace(report, yes_breakeven_probability=Decimal("0.620000"))
    with pytest.raises(ValueError, match="no_breakeven_probability"):
        replace(report, no_breakeven_probability=Decimal("0.410000"))
    with pytest.raises(ValueError, match="yes_net_expected_value"):
        replace(report, yes_net_expected_value=Decimal("2.250000"))
    with pytest.raises(ValueError, match="no_net_expected_value"):
        replace(report, no_net_expected_value=Decimal("-14.310000"))
    with pytest.raises(ValueError, match="event_payoff_mode"):
        replace(report, event_payoff_mode="asset_return")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("binary_event_payoff_model", "binary_event_payoff_model"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_binary_outcome_dataclasses_are_frozen():
    assumptions = _assumptions()
    report = build_strategy_binary_outcome_cost_report(assumptions)

    with pytest.raises(FrozenInstanceError):
        assumptions.yes_price = Decimal("0.1")
    with pytest.raises(FrozenInstanceError):
        report.yes_total_cost = Decimal("0")
