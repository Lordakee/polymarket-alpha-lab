import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyConfig,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyLog,
    PaperCostAwareEventStrategyReport,
    build_paper_cost_aware_event_strategy_report,
)


GENERATED_AT = datetime(2026, 6, 16, 12, 0, tzinfo=UTC)


def base_snapshot(**overrides):
    values = {
        "market_slug": "fed-june-cut-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.6200"),
        "confidence": Decimal("0.9000"),
        "yes_bid": Decimal("0.5400"),
        "yes_ask": Decimal("0.5500"),
        "yes_ask_size": Decimal("250.0000"),
        "no_bid": Decimal("0.4400"),
        "no_ask": Decimal("0.5000"),
        "no_ask_size": Decimal("200.0000"),
        "spread": Decimal("0.0100"),
        "resolution_risk": Decimal("0.0500"),
    }
    values.update(overrides)
    return PaperCostAwareEventMarketSnapshot(**values)


def cost_assumptions(**overrides):
    values = {
        "taker_fee_rate": Decimal("0.0200"),
        "slippage_cost_per_share": Decimal("0.0000"),
        "funding_cost_per_share": Decimal("0.0000"),
        "finalization_cost_per_share": Decimal("0.0000"),
        "time_cost_per_share": Decimal("0.0000"),
        "risk_cost_per_share": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperCostAwareEventCostAssumptions(**values)


def strategy_config(**overrides):
    values = {
        "config_version": "cost-aware-event-v1",
        "min_confidence": Decimal("0.7000"),
        "max_spread": Decimal("0.0500"),
        "max_resolution_risk": Decimal("0.2000"),
        "min_ask_size": Decimal("10.0000"),
        "min_net_edge": Decimal("0.0100"),
    }
    values.update(overrides)
    return PaperCostAwareEventStrategyConfig(**values)


def build_report(snapshot=None, assumptions=None, config=None):
    return build_paper_cost_aware_event_strategy_report(
        snapshot or base_snapshot(),
        cost_assumptions=assumptions or cost_assumptions(),
        config=config or strategy_config(),
        generated_at=GENERATED_AT,
    )


def gate_statuses(report):
    return {gate.gate_name: gate.status for gate in report.gate_results}


def gate_reason_codes(report):
    return {gate.gate_name: gate.reason_code for gate in report.gate_results}


def test_cost_aware_event_strategy_computes_yes_edge_from_yes_probability_and_yes_ask():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.6200"),
            yes_ask=Decimal("0.5500"),
            no_ask=Decimal("0.5000"),
        ),
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0200"),
            slippage_cost_per_share=Decimal("0.0010"),
            funding_cost_per_share=Decimal("0.0020"),
            finalization_cost_per_share=Decimal("0.0005"),
            time_cost_per_share=Decimal("0.0005"),
            risk_cost_per_share=Decimal("0.0010"),
        ),
    )

    assert isinstance(report, PaperCostAwareEventStrategyReport)
    assert isinstance(report.yes_result, PaperCostAwareEventSideResult)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.generated_at == GENERATED_AT
    assert report.yes_result.side == "yes"
    assert report.yes_result.fair_probability == Decimal("0.6200")
    assert report.yes_bid == Decimal("0.5400")
    assert report.no_bid == Decimal("0.4400")
    assert report.yes_result.executable_price == Decimal("0.5500")
    assert report.yes_result.gross_edge_per_share == Decimal("0.0700")
    assert report.yes_result.fee_cost_per_share == Decimal("0.004950")
    assert report.yes_result.total_cost_per_share == Decimal("0.009950")
    assert report.yes_result.net_edge_per_share == Decimal("0.060050")
    assert report.selected_side == "yes"
    assert report.status == "paper_review_ready"


def test_cost_aware_event_strategy_preserves_bids_for_audit_without_using_them_for_entry_edge():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.6200"),
            yes_bid=Decimal("0.1000"),
            yes_ask=Decimal("0.5500"),
            no_bid=Decimal("0.0500"),
            no_ask=Decimal("0.7000"),
        ),
        assumptions=cost_assumptions(taker_fee_rate=Decimal("0.0000")),
    )

    assert report.yes_bid == Decimal("0.1000")
    assert report.no_bid == Decimal("0.0500")
    assert report.yes_result.executable_price == Decimal("0.5500")
    assert report.yes_result.gross_edge_per_share == Decimal("0.0700")
    assert report.yes_result.gross_edge_per_share != Decimal("0.5200")


def test_cost_aware_event_strategy_computes_no_edge_from_complement_probability_and_no_ask():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.3800"),
            yes_ask=Decimal("0.6500"),
            no_ask=Decimal("0.5200"),
        ),
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0200"),
            slippage_cost_per_share=Decimal("0.0010"),
            funding_cost_per_share=Decimal("0.0020"),
            finalization_cost_per_share=Decimal("0.0005"),
            time_cost_per_share=Decimal("0.0005"),
            risk_cost_per_share=Decimal("0.0010"),
        ),
    )

    assert report.no_result.side == "no"
    assert report.no_result.fair_probability == Decimal("0.6200")
    assert report.no_result.executable_price == Decimal("0.5200")
    assert report.no_result.gross_edge_per_share == Decimal("0.1000")
    assert report.no_result.fee_cost_per_share == Decimal("0.004992")
    assert report.no_result.total_cost_per_share == Decimal("0.009992")
    assert report.no_result.net_edge_per_share == Decimal("0.090008")
    assert report.selected_side == "no"
    assert report.status == "paper_review_ready"


def test_taker_fee_uses_executable_price_formula_and_is_symmetric_around_half():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.9000"),
            yes_ask=Decimal("0.4000"),
            no_ask=Decimal("0.6000"),
        ),
        assumptions=cost_assumptions(taker_fee_rate=Decimal("0.0200")),
        config=strategy_config(min_net_edge=Decimal("0.0001")),
    )

    assert report.yes_result.fee_cost_per_share == Decimal("0.004800")
    assert report.no_result.fee_cost_per_share == Decimal("0.004800")
    assert report.yes_result.fee_cost_per_share == (
        Decimal("0.0200") * Decimal("0.4000") * Decimal("0.6000")
    )
    assert report.no_result.fee_cost_per_share == (
        Decimal("0.0200") * Decimal("0.6000") * Decimal("0.4000")
    )
    assert report.yes_result.fee_cost_per_share != (
        Decimal("0.0200") * Decimal("0.9000") * Decimal("0.1000")
    )


def test_cost_aware_event_strategy_spread_gate_does_not_enter_total_cost_per_share():
    tight_spread = build_report(
        snapshot=base_snapshot(spread=Decimal("0.0100")),
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0200"),
            slippage_cost_per_share=Decimal("0.0010"),
            funding_cost_per_share=Decimal("0.0020"),
            finalization_cost_per_share=Decimal("0.0005"),
            time_cost_per_share=Decimal("0.0005"),
            risk_cost_per_share=Decimal("0.0010"),
        ),
        config=strategy_config(max_spread=Decimal("0.1000")),
    )
    wide_spread = build_report(
        snapshot=base_snapshot(spread=Decimal("0.0800")),
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0200"),
            slippage_cost_per_share=Decimal("0.0010"),
            funding_cost_per_share=Decimal("0.0020"),
            finalization_cost_per_share=Decimal("0.0005"),
            time_cost_per_share=Decimal("0.0005"),
            risk_cost_per_share=Decimal("0.0010"),
        ),
        config=strategy_config(max_spread=Decimal("0.1000")),
    )

    assert tight_spread.yes_result.executable_price == Decimal("0.5500")
    assert wide_spread.yes_result.executable_price == Decimal("0.5500")
    assert tight_spread.yes_result.total_cost_per_share == Decimal("0.009950")
    assert wide_spread.yes_result.total_cost_per_share == Decimal("0.009950")
    assert tight_spread.yes_result.net_edge_per_share == Decimal("0.060050")
    assert wide_spread.yes_result.net_edge_per_share == Decimal("0.060050")


def test_cost_aware_event_strategy_selects_side_with_highest_net_edge():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.5800"),
            yes_ask=Decimal("0.5200"),
            no_ask=Decimal("0.3500"),
        ),
        assumptions=cost_assumptions(taker_fee_rate=Decimal("0.0200")),
    )

    assert report.yes_result.net_edge_per_share == Decimal("0.055008")
    assert report.no_result.net_edge_per_share == Decimal("0.065450")
    assert report.no_result.net_edge_per_share > report.yes_result.net_edge_per_share
    assert report.selected_side == "no"
    assert report.status == "paper_review_ready"


def test_cost_aware_event_strategy_reports_blocked_by_cost_when_cost_removes_gross_edge():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.5600"),
            yes_ask=Decimal("0.5500"),
            no_ask=Decimal("0.6000"),
        ),
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0200"),
            risk_cost_per_share=Decimal("0.0060"),
        ),
        config=strategy_config(min_net_edge=Decimal("0.0001")),
    )

    assert report.yes_result.gross_edge_per_share == Decimal("0.0100")
    assert report.yes_result.total_cost_per_share == Decimal("0.010950")
    assert report.yes_result.net_edge_per_share == Decimal("-0.000950")
    assert report.selected_side == "none"
    assert report.status == "blocked_by_cost"


def test_cost_aware_event_strategy_watches_positive_net_edge_below_threshold_without_cost_removal():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.5600"),
            yes_ask=Decimal("0.5500"),
            no_ask=Decimal("0.6000"),
        ),
        assumptions=cost_assumptions(taker_fee_rate=Decimal("0.0000")),
        config=strategy_config(min_net_edge=Decimal("0.0200")),
    )

    assert report.yes_result.gross_edge_per_share == Decimal("0.0100")
    assert report.yes_result.total_cost_per_share == Decimal("0.000000")
    assert report.yes_result.net_edge_per_share == Decimal("0.010000")
    assert report.selected_side == "none"
    assert report.status == "watch"
    assert gate_statuses(report)["edge_threshold"] == "fail"


def test_cost_aware_event_strategy_watches_valid_positive_edge_even_when_other_side_is_cost_eroded():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.5800"),
            yes_ask=Decimal("0.5500"),
            no_ask=Decimal("0.4100"),
        ),
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0000"),
            risk_cost_per_share=Decimal("0.0200"),
        ),
        config=strategy_config(min_net_edge=Decimal("0.0200")),
    )

    assert report.yes_result.net_edge_per_share == Decimal("0.010000")
    assert report.no_result.net_edge_per_share == Decimal("-0.010000")
    assert report.selected_side == "none"
    assert report.status == "watch"


def test_cost_aware_event_strategy_blocks_zero_ask_depth_from_review_ready():
    report = build_report(
        snapshot=base_snapshot(
            yes_ask_size=Decimal("0.0000"),
            no_ask_size=Decimal("0.0000"),
        ),
    )

    assert report.selected_side == "none"
    assert report.status == "blocked_by_inputs"
    assert gate_reason_codes(report)["yes_depth"] == "insufficient_yes_ask_size"
    assert gate_reason_codes(report)["no_depth"] == "insufficient_no_ask_size"


def test_cost_aware_event_strategy_watch_requires_positive_edge_side_to_have_valid_depth():
    report = build_report(
        snapshot=base_snapshot(
            fair_probability_yes=Decimal("0.5600"),
            yes_ask=Decimal("0.5500"),
            yes_ask_size=Decimal("0.0000"),
            no_ask=Decimal("0.5000"),
            no_ask_size=Decimal("200.0000"),
        ),
        assumptions=cost_assumptions(taker_fee_rate=Decimal("0.0000")),
        config=strategy_config(min_net_edge=Decimal("0.0200")),
    )

    assert report.yes_result.net_edge_per_share == Decimal("0.010000")
    assert report.no_result.net_edge_per_share == Decimal("-0.060000")
    assert gate_statuses(report)["yes_depth"] == "fail"
    assert gate_statuses(report)["no_depth"] == "pass"
    assert report.selected_side == "none"
    assert report.status == "no_paper_edge"


@pytest.mark.parametrize(
    ("snapshot_overrides", "expected_status", "failed_gates"),
    (
        (
            {"confidence": Decimal("0.6900")},
            "blocked_by_risk",
            ("confidence",),
        ),
        (
            {"spread": Decimal("0.0600")},
            "blocked_by_risk",
            ("spread",),
        ),
        (
            {"resolution_risk": Decimal("0.2500")},
            "blocked_by_risk",
            ("resolution_risk",),
        ),
        (
            {"yes_ask": None, "no_ask": None},
            "blocked_by_inputs",
            ("data_integrity",),
        ),
        (
            {
                "yes_ask_size": Decimal("5.0000"),
                "no_ask_size": Decimal("5.0000"),
            },
            "blocked_by_inputs",
            ("yes_depth", "no_depth"),
        ),
    ),
)
def test_cost_aware_event_strategy_gates_low_confidence_spread_risk_missing_ask_and_size(
    snapshot_overrides,
    expected_status,
    failed_gates,
):
    report = build_report(snapshot=base_snapshot(**snapshot_overrides))

    assert report.selected_side == "none"
    assert report.status == expected_status
    statuses = gate_statuses(report)
    assert all(isinstance(gate, PaperCostAwareEventStrategyGateResult) for gate in report.gate_results)
    for gate_name in failed_gates:
        assert statuses[gate_name] == "fail"
    if "data_integrity" in failed_gates:
        assert "missing" in gate_reason_codes(report)["data_integrity"]


@pytest.mark.parametrize(
    ("snapshot_overrides", "message"),
    (
        ({"fair_probability_yes": "0.6200"}, "fair_probability_yes"),
        ({"fair_probability_yes": Decimal("NaN")}, "fair_probability_yes|finite"),
        ({"fair_probability_yes": Decimal("1.0001")}, "fair_probability_yes"),
        ({"yes_ask": Decimal("-0.0100")}, "yes_ask"),
        ({"no_ask": Decimal("Infinity")}, "no_ask|finite"),
        ({"market_slug": " "}, "market_slug"),
        ({"question": ""}, "question"),
    ),
)
def test_market_snapshot_rejects_invalid_decimal_probability_price_and_string_inputs(
    snapshot_overrides,
    message,
):
    with pytest.raises(ValueError, match=message):
        base_snapshot(**snapshot_overrides)


@pytest.mark.parametrize(
    ("cost_overrides", "message"),
    (
        ({"taker_fee_rate": "0.0200"}, "taker_fee_rate"),
        ({"taker_fee_rate": Decimal("NaN")}, "taker_fee_rate|finite"),
        ({"slippage_cost_per_share": Decimal("-0.0001")}, "slippage_cost_per_share"),
    ),
)
def test_cost_assumptions_reject_invalid_decimal_cost_inputs(cost_overrides, message):
    with pytest.raises(ValueError, match=message):
        cost_assumptions(**cost_overrides)


def test_cost_assumptions_require_explicit_non_fee_cost_inputs():
    with pytest.raises(TypeError, match="slippage_cost_per_share"):
        PaperCostAwareEventCostAssumptions(taker_fee_rate=Decimal("0.0200"))


@pytest.mark.parametrize(
    ("config_overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_confidence": Decimal("1.0001")}, "min_confidence"),
        ({"max_spread": "0.0500"}, "max_spread"),
        ({"min_ask_size": Decimal("0.0000")}, "min_ask_size|positive"),
        ({"min_net_edge": Decimal("-0.0001")}, "min_net_edge"),
    ),
)
def test_strategy_config_rejects_invalid_decimal_probability_ratio_and_string_inputs(
    config_overrides,
    message,
):
    with pytest.raises(ValueError, match=message):
        strategy_config(**config_overrides)


def test_cost_aware_event_strategy_dataclasses_are_frozen_and_revalidate_report_flags():
    report = build_report()
    config = strategy_config()

    with pytest.raises(FrozenInstanceError):
        report.selected_side = "no"
    with pytest.raises(FrozenInstanceError):
        report.yes_result.net_edge_per_share = Decimal("0.0000")
    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_cost_aware_event_strategy_log_appends_jsonl_decimal_strings_and_preserves_existing_file(
    tmp_path,
):
    report = build_report(
        assumptions=cost_assumptions(
            taker_fee_rate=Decimal("0.0200"),
            slippage_cost_per_share=Decimal("0.0010"),
            funding_cost_per_share=Decimal("0.0020"),
            finalization_cost_per_share=Decimal("0.0005"),
            time_cost_per_share=Decimal("0.0005"),
            risk_cost_per_share=Decimal("0.0010"),
        ),
    )
    log = PaperCostAwareEventStrategyLog(
        path=tmp_path / "nested" / "cost-aware-event-strategy.jsonl",
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-06-16T12:00:00+00:00"
    assert stored["selected_side"] == "yes"
    assert stored["yes_bid"] == "0.5400"
    assert stored["no_bid"] == "0.4400"
    assert stored["yes_result"]["gross_edge_per_share"] == "0.0700"
    assert stored["yes_result"]["fee_cost_per_share"] == "0.004950"
    assert stored["yes_result"]["total_cost_per_share"] == "0.009950"
    assert stored["yes_result"]["net_edge_per_share"] == "0.060050"

    existing_log_path = tmp_path / "existing.jsonl"
    existing_log_path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PaperCostAwareEventStrategyReport"):
        PaperCostAwareEventStrategyLog(path=existing_log_path).append(object())
    assert existing_log_path.read_text(encoding="utf-8") == "existing\n"
