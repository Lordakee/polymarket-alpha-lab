import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_fee_cost_reconciliation import (
    ResearchFeeCostReconciliationConfig,
    ResearchFeeCostReconciliationInput,
    ResearchFeeCostReconciliationReport,
    build_research_fee_cost_reconciliation_report,
    research_fee_cost_reconciliation_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
CONFIG = ResearchFeeCostReconciliationConfig(
    config_version="research-fee-cost-reconciliation-v0",
    watch_total_cost_share=Decimal("0.020000"),
    block_total_cost_share=Decimal("0.050000"),
    watch_cost_per_research_unit=Decimal("2.000000"),
    block_cost_per_research_unit=Decimal("5.000000"),
)


class _DecimalSubclass(Decimal):
    pass


def _input(
    *,
    research_case_label: str = "macro-cost-bucket",
    expected_notional: Decimal = Decimal("1000"),
    expected_research_units: Decimal = Decimal("10"),
    taker_fee_rate: Decimal = Decimal("0.001"),
    spread_cost_rate: Decimal = Decimal("0.001"),
    deposit_cost: Decimal = Decimal("1"),
    settlement_cost: Decimal = Decimal("1"),
    slippage_expected_cost: Decimal = Decimal("1"),
    slippage_worst_case_cost: Decimal = Decimal("2"),
    slippage_observation_count: Decimal = Decimal("3"),
) -> ResearchFeeCostReconciliationInput:
    return ResearchFeeCostReconciliationInput(
        research_case_label=research_case_label,
        expected_notional=expected_notional,
        expected_research_units=expected_research_units,
        taker_fee_rate=taker_fee_rate,
        spread_cost_rate=spread_cost_rate,
        deposit_cost=deposit_cost,
        settlement_cost=settlement_cost,
        slippage_expected_cost=slippage_expected_cost,
        slippage_worst_case_cost=slippage_worst_case_cost,
        slippage_observation_count=slippage_observation_count,
    )


def test_fee_cost_reconciliation_passes_below_watch_thresholds():
    report = build_research_fee_cost_reconciliation_report(
        _input(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, ResearchFeeCostReconciliationReport)
    assert report.taker_fee_cost == Decimal("1.000000")
    assert report.spread_cost == Decimal("1.000000")
    assert report.deposit_settlement_cost == Decimal("2.000000")
    assert report.slippage_expected_cost == Decimal("1.000000")
    assert report.total_cost == Decimal("5.000000")
    assert report.total_cost_share == Decimal("0.005000")
    assert report.cost_per_research_unit == Decimal("0.500000")
    assert report.status == "pass"
    assert report.reason_codes == ("fee_cost_reconciliation_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.cost_explanation == (
        "taker_fee_cost=1.000000",
        "spread_cost=1.000000",
        "deposit_settlement_cost=2.000000",
        "slippage_expected_cost=1.000000",
        "total_cost_share=0.005000",
        "cost_per_research_unit=0.500000",
    )


def test_fee_cost_reconciliation_watches_between_thresholds():
    report = build_research_fee_cost_reconciliation_report(
        _input(
            slippage_expected_cost=Decimal("20"),
            slippage_worst_case_cost=Decimal("21"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.total_cost == Decimal("24.000000")
    assert report.total_cost_share == Decimal("0.024000")
    assert report.cost_per_research_unit == Decimal("2.400000")
    assert report.status == "watch"
    assert report.reason_codes == (
        "cost_per_research_unit_above_watch",
        "total_cost_share_above_watch",
    )


def test_fee_cost_reconciliation_blocks_above_thresholds():
    report = build_research_fee_cost_reconciliation_report(
        _input(
            slippage_expected_cost=Decimal("60"),
            slippage_worst_case_cost=Decimal("61"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.total_cost == Decimal("64.000000")
    assert report.total_cost_share == Decimal("0.064000")
    assert report.cost_per_research_unit == Decimal("6.400000")
    assert report.status == "block"
    assert report.reason_codes == (
        "cost_per_research_unit_above_block",
        "total_cost_share_above_block",
    )


def test_fee_cost_reconciliation_rejects_non_exact_decimal_values():
    with pytest.raises(ValueError, match="expected_notional"):
        _input(expected_notional=1000)
    with pytest.raises(ValueError, match="taker_fee_rate"):
        _input(taker_fee_rate=0.001)
    with pytest.raises(ValueError, match="deposit_cost"):
        _input(deposit_cost=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="watch_total_cost_share"):
        ResearchFeeCostReconciliationConfig(
            config_version="research-fee-cost-reconciliation-v0",
            watch_total_cost_share=1,
            block_total_cost_share=Decimal("0.050000"),
            watch_cost_per_research_unit=Decimal("2.000000"),
            block_cost_per_research_unit=Decimal("5.000000"),
        )


def test_fee_cost_reconciliation_rejects_public_payload_leaks():
    with pytest.raises(ValueError, match="research_case_label"):
        _input(research_case_label="market_slug=raw-question-source-url")

    report = build_research_fee_cost_reconciliation_report(
        _input(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="cost_explanation"):
        replace(report, cost_explanation=("buy outcome token",))

    payload = research_fee_cost_reconciliation_payload(report)
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in encoded


def test_fee_cost_reconciliation_enforces_hard_flags():
    report = build_research_fee_cost_reconciliation_report(
        _input(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="paper_only"):
        ResearchFeeCostReconciliationConfig(
            config_version="research-fee-cost-reconciliation-v0",
            watch_total_cost_share=Decimal("0.020000"),
            block_total_cost_share=Decimal("0.050000"),
            watch_cost_per_research_unit=Decimal("2.000000"),
            block_cost_per_research_unit=Decimal("5.000000"),
            paper_only=False,
        )


def test_fee_cost_reconciliation_payload_is_deterministic_and_public():
    first = build_research_fee_cost_reconciliation_report(
        _input(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    second = build_research_fee_cost_reconciliation_report(
        _input(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    first_payload = research_fee_cost_reconciliation_payload(first)
    second_payload = research_fee_cost_reconciliation_payload(second)

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["total_cost"] == "5.000000"


def test_fee_cost_reconciliation_dataclasses_are_frozen():
    report = build_research_fee_cost_reconciliation_report(
        _input(),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.total_cost = Decimal("0")
