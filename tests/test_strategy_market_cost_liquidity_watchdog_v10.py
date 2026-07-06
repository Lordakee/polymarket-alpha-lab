from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    strategy_market_cost_liquidity_watchdog_v10 as watchdog_module,
)
from polymarket_alpha_lab.strategy_market_cost_liquidity_watchdog_v10 import (
    StrategyMarketCostLiquidityWatchdogConfig,
    StrategyMarketCostLiquidityWatchdogInput,
    StrategyMarketCostLiquidityWatchdogReport,
    evaluate_strategy_market_cost_liquidity_watchdog_v10,
    strategy_market_cost_liquidity_watchdog_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyMarketCostLiquidityWatchdogConfig:
    values = {
        "config_version": "strategy-market-cost-liquidity-watchdog-test-v10",
        "minimum_attractive_score": d("0.750000"),
        "minimum_watch_score": d("0.500000"),
        "maximum_fee_drag": d("0.015000"),
        "maximum_bid_ask_spread": d("0.030000"),
        "maximum_expected_slippage": d("0.020000"),
        "minimum_exit_depth_ratio": d("1.000000"),
        "maximum_liquidity_volatility": d("0.250000"),
        "fee_drag_weight": d("0.200000"),
        "spread_weight": d("0.200000"),
        "slippage_weight": d("0.200000"),
        "exit_depth_weight": d("0.250000"),
        "liquidity_volatility_weight": d("0.150000"),
    }
    values.update(overrides)
    return StrategyMarketCostLiquidityWatchdogConfig(**values)


def market(**overrides: object) -> StrategyMarketCostLiquidityWatchdogInput:
    values = {
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "paper_recommendation": "paper_buy_yes",
        "target_notional": d("1000.000000"),
        "fee_drag": d("0.004000"),
        "bid_ask_spread": d("0.006000"),
        "expected_slippage": d("0.005000"),
        "exit_depth_notional": d("1400.000000"),
        "liquidity_volatility": d("0.040000"),
        "reason_codes": ("paper_candidate_screened",),
    }
    values.update(overrides)
    return StrategyMarketCostLiquidityWatchdogInput(**values)


def evaluate(
    market_state: StrategyMarketCostLiquidityWatchdogInput | object | None = None,
    strategy_config: StrategyMarketCostLiquidityWatchdogConfig | object | None = None,
) -> StrategyMarketCostLiquidityWatchdogReport:
    return evaluate_strategy_market_cost_liquidity_watchdog_v10(
        market_state or market(),
        strategy_config or config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_attractive_market_scores_cost_liquidity_components() -> None:
    report = evaluate()

    assert report.config_version == "strategy-market-cost-liquidity-watchdog-test-v10"
    assert report.market_slug == "fed-cuts-by-september"
    assert report.outcome_name == "Yes"
    assert report.paper_recommendation == "paper_buy_yes"
    assert report.watchdog_status == "attractive"
    assert report.target_notional == d("1000.000000")
    assert report.fee_drag_score == d("0.733333")
    assert report.spread_score == d("0.800000")
    assert report.slippage_score == d("0.750000")
    assert report.exit_depth_ratio == d("1.000000")
    assert report.exit_depth_score == d("1.000000")
    assert report.liquidity_volatility_score == d("0.840000")
    assert report.cost_liquidity_score == d("0.832667")
    assert report.reason_codes == (
        "strategy_market_cost_liquidity_watchdog_attractive",
        "paper_candidate_screened",
        "cost_liquidity_profile_attractive",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_unattractive_market_reports_each_cost_and_liquidity_blocker() -> None:
    report = evaluate(
        market(
            fee_drag=d("0.020000"),
            bid_ask_spread=d("0.045000"),
            expected_slippage=d("0.030000"),
            exit_depth_notional=d("400.000000"),
            liquidity_volatility=d("0.300000"),
        ),
    )

    assert report.watchdog_status == "unattractive"
    assert report.fee_drag_score == d("0.000000")
    assert report.spread_score == d("0.000000")
    assert report.slippage_score == d("0.000000")
    assert report.exit_depth_ratio == d("0.400000")
    assert report.exit_depth_score == d("0.400000")
    assert report.liquidity_volatility_score == d("0.000000")
    assert report.cost_liquidity_score == d("0.100000")
    assert report.reason_codes == (
        "strategy_market_cost_liquidity_watchdog_unattractive",
        "paper_candidate_screened",
        "fee_drag_above_limit",
        "bid_ask_spread_above_limit",
        "expected_slippage_above_limit",
        "exit_depth_below_target",
        "liquidity_volatility_above_limit",
    )


def test_watch_market_when_combined_cost_liquidity_score_is_mid_quality() -> None:
    report = evaluate(
        market(
            fee_drag=d("0.008000"),
            bid_ask_spread=d("0.018000"),
            expected_slippage=d("0.010000"),
            exit_depth_notional=d("900.000000"),
            liquidity_volatility=d("0.160000"),
        ),
    )

    assert report.watchdog_status == "watch"
    assert report.exit_depth_ratio == d("0.900000")
    assert report.cost_liquidity_score == d("0.552333")
    assert report.reason_codes == (
        "strategy_market_cost_liquidity_watchdog_watch",
        "paper_candidate_screened",
        "exit_depth_below_target",
    )


def test_outputs_are_frozen_decimal_quantized_tuple_only_and_readonly() -> None:
    market_state = market(bid_ask_spread=d("0.0060001"))
    report = evaluate(market_state)

    assert market_state.bid_ask_spread == d("0.006000")
    assert type(report.cost_liquidity_score) is Decimal
    assert type(report.reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        report.watchdog_status = "unattractive"  # type: ignore[misc]
    with pytest.raises(ValueError, match="fee_drag must be a Decimal"):
        replace(market_state, fee_drag=0.004)
    with pytest.raises(ValueError, match="target_notional must be positive"):
        replace(market_state, target_notional=d("0.000000"))
    with pytest.raises(ValueError, match="paper_recommendation"):
        replace(market_state, paper_recommendation="")
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(market_state, reason_codes=["paper_candidate_screened"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(
            market_state,
            reason_codes=("paper_candidate_screened", "paper_candidate_screened"),
        )
    with pytest.raises(ValueError, match="watchdog_status"):
        replace(report, watchdog_status="ready")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)


def test_rejects_wrong_public_types_subclasses_and_bad_config() -> None:
    class MarketSubclass(StrategyMarketCostLiquidityWatchdogInput):
        pass

    with pytest.raises(ValueError, match="market_state"):
        evaluate(object())
    with pytest.raises(ValueError, match="market_state"):
        evaluate(MarketSubclass(**market().__dict__))
    with pytest.raises(ValueError, match="config"):
        evaluate(strategy_config=object())
    with pytest.raises(ValueError, match="minimum_watch_score"):
        config(minimum_watch_score=d("0.760000"))
    with pytest.raises(ValueError, match="maximum_fee_drag must be positive"):
        config(maximum_fee_drag=d("0.000000"))
    with pytest.raises(ValueError, match="minimum_exit_depth_ratio must be positive"):
        config(minimum_exit_depth_ratio=d("0.000000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(liquidity_volatility_weight=d("0.050000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)


def test_payload_uses_decimal_strings_flags_and_no_floats() -> None:
    report = evaluate()

    payload = strategy_market_cost_liquidity_watchdog_v10_payload(report)

    assert payload == {
        "config_version": "strategy-market-cost-liquidity-watchdog-test-v10",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "paper_recommendation": "paper_buy_yes",
        "watchdog_status": "attractive",
        "target_notional": "1000.000000",
        "fee_drag": "0.004000",
        "fee_drag_score": "0.733333",
        "bid_ask_spread": "0.006000",
        "spread_score": "0.800000",
        "expected_slippage": "0.005000",
        "slippage_score": "0.750000",
        "exit_depth_notional": "1400.000000",
        "exit_depth_ratio": "1.000000",
        "exit_depth_score": "1.000000",
        "liquidity_volatility": "0.040000",
        "liquidity_volatility_score": "0.840000",
        "cost_liquidity_score": "0.832667",
        "reason_codes": [
            "strategy_market_cost_liquidity_watchdog_attractive",
            "paper_candidate_screened",
            "cost_liquidity_profile_attractive",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="report must be"):
        strategy_market_cost_liquidity_watchdog_v10_payload(object())


def test_payload_accepts_validated_dict_and_rejects_unsafe_payloads() -> None:
    payload = strategy_market_cost_liquidity_watchdog_v10_payload(evaluate())

    assert strategy_market_cost_liquidity_watchdog_v10_payload(dict(payload)) == payload

    with pytest.raises(ValueError, match="paper_only"):
        strategy_market_cost_liquidity_watchdog_v10_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="must not be a float"):
        strategy_market_cost_liquidity_watchdog_v10_payload(
            {**payload, "fee_drag": 0.004},
        )
    with pytest.raises(ValueError, match="must use Decimal-derived string values"):
        strategy_market_cost_liquidity_watchdog_v10_payload(
            {**payload, "target_notional": 1000},
        )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        strategy_market_cost_liquidity_watchdog_v10_payload(
            {**payload, "wallet_address": "0xabc"},
        )
    with pytest.raises(ValueError, match="unsafe live surface value"):
        strategy_market_cost_liquidity_watchdog_v10_payload(
            {**payload, "reason_codes": ["paper_candidate_screened", "submit_order"]},
        )


def test_report_validation_is_tamper_evident_for_derived_fields() -> None:
    report = evaluate()

    with pytest.raises(ValueError, match="exit_depth_ratio must match"):
        replace(report, exit_depth_ratio=d("0.900000"))
    with pytest.raises(ValueError, match="attractive report must include attractive"):
        replace(
            report,
            reason_codes=(
                "strategy_market_cost_liquidity_watchdog_attractive",
                "paper_candidate_screened",
                "fee_drag_above_limit",
            ),
        )
    with pytest.raises(ValueError, match="unattractive report must include blocker"):
        replace(
            evaluate(
                market(
                    fee_drag=d("0.020000"),
                    bid_ask_spread=d("0.045000"),
                    expected_slippage=d("0.030000"),
                    exit_depth_notional=d("400.000000"),
                    liquidity_volatility=d("0.300000"),
                ),
            ),
            reason_codes=(
                "strategy_market_cost_liquidity_watchdog_unattractive",
                "paper_candidate_screened",
            ),
        )


def test_module_is_pure_readonly_and_has_no_live_market_surface() -> None:
    source = inspect.getsource(watchdog_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "order",
        "trade",
    }
    forbidden_attr_fragments = (
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
