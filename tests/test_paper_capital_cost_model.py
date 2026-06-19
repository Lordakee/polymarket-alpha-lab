from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_capital_cost_model import (
    PaperCapitalCostAssumptions,
    PaperCapitalCostModelConfig,
    PaperCapitalCostReport,
    build_paper_capital_cost_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
CONFIG = PaperCapitalCostModelConfig(
    config_version="paper-capital-cost-model-v0",
    watch_cost_per_trade=Decimal("2.000000"),
    max_cost_per_trade=Decimal("3.000000"),
    watch_cost_per_notional=Decimal("0.020000"),
    max_cost_per_notional=Decimal("0.030000"),
)


class _DecimalSubclass(Decimal):
    pass


def _assumptions(
    *,
    deposit_cost: Decimal = Decimal("5"),
    withdrawal_cost: Decimal = Decimal("3"),
    bridge_cost: Decimal = Decimal("2"),
    onchain_cost: Decimal = Decimal("1"),
    finalization_cost: Decimal = Decimal("4"),
    funding_cost: Decimal = Decimal("10"),
    expected_trade_count: int = 10,
    expected_total_notional: Decimal = Decimal("1000"),
    holding_period_days: Decimal | None = Decimal("7"),
) -> PaperCapitalCostAssumptions:
    return PaperCapitalCostAssumptions(
        deposit_cost=deposit_cost,
        withdrawal_cost=withdrawal_cost,
        bridge_cost=bridge_cost,
        onchain_cost=onchain_cost,
        finalization_cost=finalization_cost,
        funding_cost=funding_cost,
        expected_trade_count=expected_trade_count,
        expected_total_notional=expected_total_notional,
        holding_period_days=holding_period_days,
    )


def _non_empty_report_kwargs() -> dict[str, object]:
    return {
        "generated_at": GENERATED_AT,
        "config_version": "paper-capital-cost-model-v0",
        "deposit_cost": Decimal("5.000000"),
        "withdrawal_cost": Decimal("3.000000"),
        "bridge_cost": Decimal("2.000000"),
        "onchain_cost": Decimal("1.000000"),
        "finalization_cost": Decimal("4.000000"),
        "funding_cost": Decimal("10.000000"),
        "expected_trade_count": 10,
        "expected_total_notional": Decimal("1000.000000"),
        "holding_period_days": Decimal("7.000000"),
        "total_fixed_cost": Decimal("15.000000"),
        "total_variable_cost": Decimal("10.000000"),
        "total_cost": Decimal("25.000000"),
        "cost_per_trade": Decimal("2.500000"),
        "cost_per_notional": Decimal("0.025000"),
        "status": "watch",
        "reason_codes": ("cost_per_trade_above_watch", "cost_per_notional_above_watch"),
    }


def test_capital_cost_model_amortizes_fixed_and_variable_costs():
    report = build_paper_capital_cost_report(
        _assumptions(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperCapitalCostReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-capital-cost-model-v0"
    assert report.deposit_cost == Decimal("5.000000")
    assert report.withdrawal_cost == Decimal("3.000000")
    assert report.bridge_cost == Decimal("2.000000")
    assert report.onchain_cost == Decimal("1.000000")
    assert report.finalization_cost == Decimal("4.000000")
    assert report.funding_cost == Decimal("10.000000")
    assert report.expected_trade_count == 10
    assert report.expected_total_notional == Decimal("1000.000000")
    assert report.holding_period_days == Decimal("7.000000")
    assert report.total_fixed_cost == Decimal("15.000000")
    assert report.total_variable_cost == Decimal("10.000000")
    assert report.total_cost == Decimal("25.000000")
    assert report.cost_per_trade == Decimal("2.500000")
    assert report.cost_per_notional == Decimal("0.025000")
    assert report.status == "watch"
    assert report.reason_codes == (
        "cost_per_trade_above_watch",
        "cost_per_notional_above_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_capital_cost_model_reports_ready_below_configured_thresholds():
    report = build_paper_capital_cost_report(
        _assumptions(
            deposit_cost=Decimal("1"),
            withdrawal_cost=Decimal("1"),
            bridge_cost=Decimal("0"),
            onchain_cost=Decimal("0"),
            finalization_cost=Decimal("0"),
            funding_cost=Decimal("1"),
            expected_trade_count=10,
            expected_total_notional=Decimal("1000"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.total_cost == Decimal("3.000000")
    assert report.cost_per_trade == Decimal("0.300000")
    assert report.cost_per_notional == Decimal("0.003000")
    assert report.status == "ready"
    assert report.reason_codes == ("capital_cost_ready",)


def test_capital_cost_model_zero_costs_allow_missing_denominators():
    report = build_paper_capital_cost_report(
        _assumptions(
            deposit_cost=Decimal("0"),
            withdrawal_cost=Decimal("0"),
            bridge_cost=Decimal("0"),
            onchain_cost=Decimal("0"),
            finalization_cost=Decimal("0"),
            funding_cost=Decimal("0"),
            expected_trade_count=0,
            expected_total_notional=Decimal("0"),
            holding_period_days=None,
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.total_fixed_cost == Decimal("0.000000")
    assert report.total_variable_cost == Decimal("0.000000")
    assert report.total_cost == Decimal("0.000000")
    assert report.cost_per_trade is None
    assert report.cost_per_notional is None
    assert report.holding_period_days is None
    assert report.status == "ready"
    assert report.reason_codes == ("zero_capital_cost_assumption",)


def test_capital_cost_model_blocks_positive_costs_without_amortization_denominators():
    report = build_paper_capital_cost_report(
        _assumptions(
            deposit_cost=Decimal("1"),
            withdrawal_cost=Decimal("0"),
            bridge_cost=Decimal("0"),
            onchain_cost=Decimal("0"),
            finalization_cost=Decimal("0"),
            funding_cost=Decimal("0"),
            expected_trade_count=0,
            expected_total_notional=Decimal("0"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.cost_per_trade is None
    assert report.cost_per_notional is None
    assert report.status == "blocked"
    assert report.reason_codes == (
        "missing_expected_trade_count_for_positive_cost",
        "missing_expected_total_notional_for_positive_cost",
    )


def test_capital_cost_model_blocks_when_costs_exceed_configured_maxima():
    report = build_paper_capital_cost_report(
        _assumptions(
            deposit_cost=Decimal("10"),
            withdrawal_cost=Decimal("10"),
            bridge_cost=Decimal("10"),
            onchain_cost=Decimal("10"),
            finalization_cost=Decimal("10"),
            funding_cost=Decimal("10"),
            expected_trade_count=10,
            expected_total_notional=Decimal("1000"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.total_cost == Decimal("60.000000")
    assert report.cost_per_trade == Decimal("6.000000")
    assert report.cost_per_notional == Decimal("0.060000")
    assert report.status == "blocked"
    assert report.reason_codes == (
        "cost_per_trade_above_max",
        "cost_per_notional_above_max",
    )


def test_capital_cost_model_quantizes_all_decimal_outputs_to_six_places():
    report = build_paper_capital_cost_report(
        _assumptions(
            deposit_cost=Decimal("1.1111114"),
            withdrawal_cost=Decimal("2.2222224"),
            bridge_cost=Decimal("3.3333334"),
            onchain_cost=Decimal("4.4444444"),
            finalization_cost=Decimal("5.5555554"),
            funding_cost=Decimal("6.6666664"),
            expected_trade_count=3,
            expected_total_notional=Decimal("9"),
            holding_period_days=Decimal("1.2345674"),
        ),
        config=PaperCapitalCostModelConfig(
            config_version="paper-capital-cost-model-v0",
            max_cost_per_trade=Decimal("10"),
            max_cost_per_notional=Decimal("10"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.deposit_cost == Decimal("1.111111")
    assert report.withdrawal_cost == Decimal("2.222222")
    assert report.bridge_cost == Decimal("3.333333")
    assert report.onchain_cost == Decimal("4.444444")
    assert report.finalization_cost == Decimal("5.555555")
    assert report.funding_cost == Decimal("6.666666")
    assert report.holding_period_days == Decimal("1.234567")
    assert report.total_fixed_cost == Decimal("16.666665")
    assert report.total_variable_cost == Decimal("6.666666")
    assert report.total_cost == Decimal("23.333331")
    assert report.cost_per_trade == Decimal("7.777777")
    assert report.cost_per_notional == Decimal("2.592592")


@pytest.mark.parametrize(
    ("generated_at", "expected_generated_at"),
    (
        (datetime(2026, 6, 19, 12, 0), GENERATED_AT),
        (
            datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
            GENERATED_AT,
        ),
    ),
)
def test_capital_cost_model_normalizes_generated_at_to_utc(
    generated_at: datetime,
    expected_generated_at: datetime,
):
    report = build_paper_capital_cost_report(
        _assumptions(),
        config=CONFIG,
        generated_at=generated_at,
    )

    assert report.generated_at == expected_generated_at
    assert report.generated_at.tzinfo is UTC


def test_capital_cost_assumptions_reject_non_decimal_cost_inputs():
    with pytest.raises(ValueError, match="deposit_cost"):
        _assumptions(deposit_cost=1.0)
    with pytest.raises(ValueError, match="deposit_cost"):
        _assumptions(deposit_cost=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="holding_period_days"):
        _assumptions(holding_period_days=7)
    with pytest.raises(ValueError, match="expected_total_notional"):
        _assumptions(expected_total_notional="100")


def test_capital_cost_assumptions_reject_negative_or_inconsistent_values():
    with pytest.raises(ValueError, match="deposit_cost"):
        _assumptions(deposit_cost=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="expected_trade_count"):
        _assumptions(expected_trade_count=-1)
    with pytest.raises(ValueError, match="expected_trade_count"):
        _assumptions(expected_trade_count=True)
    with pytest.raises(ValueError, match="expected_total_notional"):
        _assumptions(expected_total_notional=Decimal("-1"))
    with pytest.raises(ValueError, match="holding_period_days"):
        _assumptions(holding_period_days=Decimal("-1"))


def test_capital_cost_config_rejects_invalid_thresholds():
    with pytest.raises(ValueError, match="config_version"):
        PaperCapitalCostModelConfig(config_version="")
    with pytest.raises(ValueError, match="max_cost_per_trade"):
        PaperCapitalCostModelConfig(
            config_version="paper-capital-cost-model-v0",
            max_cost_per_trade=1.5,
        )
    with pytest.raises(ValueError, match="watch_cost_per_notional"):
        PaperCapitalCostModelConfig(
            config_version="paper-capital-cost-model-v0",
            watch_cost_per_notional=Decimal("-0.000001"),
        )
    with pytest.raises(ValueError, match="watch_cost_per_trade"):
        PaperCapitalCostModelConfig(
            config_version="paper-capital-cost-model-v0",
            watch_cost_per_trade=Decimal("5"),
            max_cost_per_trade=Decimal("4"),
        )
    with pytest.raises(ValueError, match="watch_cost_per_notional"):
        PaperCapitalCostModelConfig(
            config_version="paper-capital-cost-model-v0",
            watch_cost_per_notional=Decimal("0.050000"),
            max_cost_per_notional=Decimal("0.040000"),
        )


def test_capital_cost_builder_rejects_invalid_top_level_inputs():
    with pytest.raises(ValueError, match="assumptions"):
        build_paper_capital_cost_report(
            object(),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_capital_cost_report(
            _assumptions(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_capital_cost_report(
            _assumptions(),
            config=CONFIG,
            generated_at="now",
        )


def test_capital_cost_report_revalidates_derived_metric_consistency():
    report = build_paper_capital_cost_report(
        _assumptions(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="total_fixed_cost"):
        replace(report, total_fixed_cost=Decimal("14.000000"))
    with pytest.raises(ValueError, match="total_variable_cost"):
        replace(report, total_variable_cost=Decimal("9.000000"))
    with pytest.raises(ValueError, match="total_cost"):
        replace(report, total_cost=Decimal("24.000000"))
    with pytest.raises(ValueError, match="cost_per_trade"):
        replace(report, cost_per_trade=Decimal("2.400000"))
    with pytest.raises(ValueError, match="cost_per_notional"):
        replace(report, cost_per_notional=Decimal("0.024000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="unknown")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("capital_cost_ready", "capital_cost_ready"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_capital_cost_report_requires_missing_ratios_only_when_denominator_is_zero():
    report = build_paper_capital_cost_report(
        _assumptions(
            expected_trade_count=0,
            expected_total_notional=Decimal("0"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="cost_per_trade"):
        replace(report, cost_per_trade=Decimal("0.000000"))
    with pytest.raises(ValueError, match="cost_per_notional"):
        replace(report, cost_per_notional=Decimal("0.000000"))

    non_empty = build_paper_capital_cost_report(
        _assumptions(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="cost_per_trade"):
        replace(non_empty, cost_per_trade=None)
    with pytest.raises(ValueError, match="cost_per_notional"):
        replace(non_empty, cost_per_notional=None)


def test_capital_cost_dataclasses_are_frozen():
    assumptions = _assumptions()
    config = CONFIG
    report = build_paper_capital_cost_report(
        assumptions,
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        assumptions.deposit_cost = Decimal("0")
    with pytest.raises(FrozenInstanceError):
        config.max_cost_per_trade = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        report.total_cost = Decimal("0")
