from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_manual_order_cost_preview_v10 import (
    ManualOrderCostPreviewInput,
    ManualOrderCostPreviewResult,
    manual_order_cost_preview_payload,
    preview_manual_order_cost,
)


def _preview_input(**overrides):
    values = {
        "side": "buy",
        "outcome_price": Decimal("0.420000"),
        "intended_size": Decimal("10.000000"),
        "fee_rate": Decimal("0.020000"),
        "estimated_slippage_bps": Decimal("25.000000"),
        "settlement_cost_bps": Decimal("10.000000"),
        "gas_or_deposit_cost": Decimal("1.250000"),
        "reason_codes": ("manual_preview_requested",),
    }
    values.update(overrides)
    return ManualOrderCostPreviewInput(**values)


def test_preview_manual_buy_order_costs_before_any_order_placement():
    result = preview_manual_order_cost(_preview_input())

    assert isinstance(result, ManualOrderCostPreviewResult)
    assert result.side == "buy"
    assert result.gross_cost == Decimal("4.200000")
    assert result.fee_cost == Decimal("0.084000")
    assert result.slippage_cost == Decimal("0.010500")
    assert result.total_cost == Decimal("5.548700")
    assert result.breakeven_probability == Decimal("0.554870")
    assert result.cost_warning_tier == "watch"
    assert result.reason_codes == (
        "manual_preview_requested",
        "manual_cost_preview",
        "fixed_cost_present",
        "cost_warning_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == manual_order_cost_preview_payload(result)


def test_preview_blocks_when_total_cost_exceeds_binary_payout():
    result = preview_manual_order_cost(
        _preview_input(
            outcome_price=Decimal("0.970000"),
            gas_or_deposit_cost=Decimal("1.000000"),
        ),
    )

    assert result.gross_cost == Decimal("9.700000")
    assert result.total_cost == Decimal("10.927950")
    assert result.breakeven_probability == Decimal("1.092795")
    assert result.cost_warning_tier == "block"
    assert "breakeven_probability_above_one" in result.reason_codes
    assert "cost_warning_block" in result.reason_codes


def test_preview_accepts_sell_side_as_readonly_cost_drag_preview():
    result = preview_manual_order_cost(
        _preview_input(
            side="sell",
            outcome_price=Decimal("0.650000"),
            intended_size=Decimal("8.000000"),
            fee_rate=Decimal("0.010000"),
            estimated_slippage_bps=Decimal("50.000000"),
            settlement_cost_bps=Decimal("0.000000"),
            gas_or_deposit_cost=Decimal("0.000000"),
            reason_codes=(),
        ),
    )

    assert result.side == "sell"
    assert result.gross_cost == Decimal("5.200000")
    assert result.fee_cost == Decimal("0.052000")
    assert result.slippage_cost == Decimal("0.026000")
    assert result.total_cost == Decimal("5.278000")
    assert result.breakeven_probability == Decimal("0.659750")
    assert result.cost_warning_tier == "watch"
    assert result.reason_codes == (
        "manual_cost_preview",
        "cost_warning_watch",
    )


def test_preview_marks_low_cost_preview_ok():
    result = preview_manual_order_cost(
        _preview_input(
            outcome_price=Decimal("0.250000"),
            intended_size=Decimal("100.000000"),
            fee_rate=Decimal("0.001000"),
            estimated_slippage_bps=Decimal("1.000000"),
            settlement_cost_bps=Decimal("1.000000"),
            gas_or_deposit_cost=Decimal("0.000000"),
            reason_codes=(),
        ),
    )

    assert result.total_cost == Decimal("25.030000")
    assert result.breakeven_probability == Decimal("0.250300")
    assert result.cost_warning_tier == "ok"
    assert result.reason_codes == (
        "manual_cost_preview",
        "cost_warning_ok",
    )


def test_preview_uses_decimal_only_inputs_and_validates_ranges():
    with pytest.raises(ValueError, match="outcome_price must be a Decimal"):
        _preview_input(outcome_price=0.42)

    with pytest.raises(ValueError, match="side must be buy or sell"):
        _preview_input(side="hold")

    with pytest.raises(ValueError, match="outcome_price must be between 0 and 1"):
        _preview_input(outcome_price=Decimal("1.000001"))

    with pytest.raises(ValueError, match="intended_size must be positive"):
        _preview_input(intended_size=Decimal("0.000000"))

    with pytest.raises(ValueError, match="estimated_slippage_bps must be nonnegative"):
        _preview_input(estimated_slippage_bps=Decimal("-0.000001"))


def test_preview_requires_tuple_reason_codes_and_hard_flags():
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _preview_input(reason_codes=["manual_preview_requested"])

    with pytest.raises(ValueError, match="paper_only must be True"):
        _preview_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _preview_input(readonly=False)


def test_preview_dataclasses_are_frozen():
    preview_input = _preview_input()
    result = preview_manual_order_cost(preview_input)

    with pytest.raises(FrozenInstanceError):
        preview_input.side = "sell"

    with pytest.raises(FrozenInstanceError):
        result.cost_warning_tier = "ok"


def test_payload_is_report_only_json_ready_and_contains_no_decimal_objects():
    result = preview_manual_order_cost(_preview_input())
    payload = manual_order_cost_preview_payload(result)

    assert payload == result.payload
    assert payload["side"] == "buy"
    assert payload["gross_cost"] == "4.200000"
    assert payload["fee_cost"] == "0.084000"
    assert payload["slippage_cost"] == "0.010500"
    assert payload["total_cost"] == "5.548700"
    assert payload["breakeven_probability"] == "0.554870"
    assert payload["cost_warning_tier"] == "watch"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    unsafe = object.__new__(ManualOrderCostPreviewResult)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        manual_order_cost_preview_payload(unsafe)
