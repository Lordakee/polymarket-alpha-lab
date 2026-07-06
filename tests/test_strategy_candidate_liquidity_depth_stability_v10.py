from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    strategy_candidate_liquidity_depth_stability_v10 as stability_module,
)
from polymarket_alpha_lab.strategy_candidate_liquidity_depth_stability_v10 import (
    StrategyCandidateLiquidityDepthStabilityConfig,
    StrategyCandidateLiquidityDepthStabilityInput,
    StrategyCandidateLiquidityDepthStabilityScore,
    score_strategy_candidate_liquidity_depth_stability_v10,
    strategy_candidate_liquidity_depth_stability_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateLiquidityDepthStabilityConfig:
    values = {
        "config_version": "strategy-candidate-liquidity-depth-stability-test-v10",
        "minimum_stability_score": d("0.750000"),
        "minimum_watch_score": d("0.500000"),
        "maximum_bid_ask_spread": d("0.030000"),
        "maximum_recent_depth_volatility": d("0.250000"),
        "maximum_taker_fee_drag": d("0.020000"),
        "depth_weight": d("0.300000"),
        "spread_weight": d("0.200000"),
        "volatility_weight": d("0.200000"),
        "fee_drag_weight": d("0.100000"),
        "exit_capacity_weight": d("0.200000"),
    }
    values.update(overrides)
    return StrategyCandidateLiquidityDepthStabilityConfig(**values)


def candidate(**overrides: object) -> StrategyCandidateLiquidityDepthStabilityInput:
    values = {
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "target_size_notional": d("1000.000000"),
        "depth_at_target_size_notional": d("1250.000000"),
        "best_bid_price": d("0.520000"),
        "best_ask_price": d("0.525000"),
        "recent_depth_volatility": d("0.050000"),
        "taker_fee_drag": d("0.005000"),
        "exit_capacity_notional": d("1500.000000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyCandidateLiquidityDepthStabilityInput(**values)


def score(
    candidate_state: StrategyCandidateLiquidityDepthStabilityInput | object | None = None,
    strategy_config: StrategyCandidateLiquidityDepthStabilityConfig | object | None = None,
) -> StrategyCandidateLiquidityDepthStabilityScore:
    return score_strategy_candidate_liquidity_depth_stability_v10(
        candidate_state or candidate(),
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


def test_stable_candidate_scores_depth_spread_volatility_fee_and_exit_capacity() -> None:
    result = score()

    assert result.config_version == "strategy-candidate-liquidity-depth-stability-test-v10"
    assert result.candidate_id == "candidate-001"
    assert result.market_slug == "fed-cuts-by-september"
    assert result.outcome_name == "Yes"
    assert result.stability_status == "stable"
    assert result.depth_coverage_ratio == d("1.000000")
    assert result.bid_ask_spread == d("0.005000")
    assert result.spread_score == d("0.833333")
    assert result.depth_volatility_score == d("0.800000")
    assert result.fee_drag_score == d("0.750000")
    assert result.exit_capacity_ratio == d("1.000000")
    assert result.liquidity_depth_stability_score == d("0.901667")
    assert result.reason_codes == (
        "strategy_candidate_liquidity_depth_stability_stable",
        "candidate_screened",
        "liquidity_depth_stability_sufficient",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_unstable_candidate_reports_each_depth_stability_blocker() -> None:
    result = score(
        candidate(
            depth_at_target_size_notional=d("600.000000"),
            best_bid_price=d("0.500000"),
            best_ask_price=d("0.540000"),
            recent_depth_volatility=d("0.300000"),
            taker_fee_drag=d("0.025000"),
            exit_capacity_notional=d("400.000000"),
        ),
    )

    assert result.stability_status == "unstable"
    assert result.depth_coverage_ratio == d("0.600000")
    assert result.bid_ask_spread == d("0.040000")
    assert result.spread_score == d("0.000000")
    assert result.depth_volatility_score == d("0.000000")
    assert result.fee_drag_score == d("0.000000")
    assert result.exit_capacity_ratio == d("0.400000")
    assert result.liquidity_depth_stability_score == d("0.260000")
    assert result.reason_codes == (
        "strategy_candidate_liquidity_depth_stability_unstable",
        "candidate_screened",
        "depth_at_target_size_below_target",
        "bid_ask_spread_above_limit",
        "recent_depth_volatility_above_limit",
        "taker_fee_drag_above_limit",
        "exit_capacity_below_target",
    )


def test_watch_candidate_when_composite_is_mid_quality() -> None:
    result = score(
        candidate(
            depth_at_target_size_notional=d("900.000000"),
            best_bid_price=d("0.500000"),
            best_ask_price=d("0.520000"),
            recent_depth_volatility=d("0.100000"),
            exit_capacity_notional=d("900.000000"),
        ),
    )

    assert result.stability_status == "watch"
    assert result.liquidity_depth_stability_score == d("0.711667")
    assert result.reason_codes == (
        "strategy_candidate_liquidity_depth_stability_watch",
        "candidate_screened",
        "depth_at_target_size_below_target",
        "exit_capacity_below_target",
    )


def test_outputs_are_frozen_typed_decimal_quantized_tuple_only_and_readonly() -> None:
    candidate_state = candidate(best_ask_price=d("0.5250001"))
    result = score(candidate_state)

    assert candidate_state.best_ask_price == d("0.525000")
    assert type(result.liquidity_depth_stability_score) is Decimal
    assert type(result.reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        result.stability_status = "unstable"  # type: ignore[misc]
    with pytest.raises(ValueError, match="best_ask_price must be a Decimal"):
        replace(candidate_state, best_ask_price=0.525)
    with pytest.raises(ValueError, match="target_size_notional must be positive"):
        replace(candidate_state, target_size_notional=d("0.000000"))
    with pytest.raises(ValueError, match="best_ask_price must be greater than or equal"):
        replace(candidate_state, best_ask_price=d("0.519999"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(candidate_state, reason_codes=["candidate_screened"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(candidate_state, reason_codes=("candidate_screened", "candidate_screened"))
    with pytest.raises(ValueError, match="stability_status"):
        replace(result, stability_status="ready")
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_rejects_wrong_public_types_subclasses_and_bad_config() -> None:
    class CandidateSubclass(StrategyCandidateLiquidityDepthStabilityInput):
        pass

    with pytest.raises(ValueError, match="candidate_state"):
        score(object())
    with pytest.raises(ValueError, match="candidate_state"):
        score(CandidateSubclass(**candidate().__dict__))
    with pytest.raises(ValueError, match="config"):
        score(strategy_config=object())
    with pytest.raises(ValueError, match="minimum_watch_score"):
        config(minimum_watch_score=d("0.760000"))
    with pytest.raises(ValueError, match="maximum_bid_ask_spread must be positive"):
        config(maximum_bid_ask_spread=d("0.000000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(exit_capacity_weight=d("0.100000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)


def test_payload_uses_decimal_strings_flags_and_no_floats() -> None:
    result = score()

    payload = strategy_candidate_liquidity_depth_stability_v10_payload(result)

    assert payload == {
        "config_version": "strategy-candidate-liquidity-depth-stability-test-v10",
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "stability_status": "stable",
        "target_size_notional": "1000.000000",
        "depth_at_target_size_notional": "1250.000000",
        "depth_coverage_ratio": "1.000000",
        "best_bid_price": "0.520000",
        "best_ask_price": "0.525000",
        "bid_ask_spread": "0.005000",
        "spread_score": "0.833333",
        "recent_depth_volatility": "0.050000",
        "depth_volatility_score": "0.800000",
        "taker_fee_drag": "0.005000",
        "fee_drag_score": "0.750000",
        "exit_capacity_notional": "1500.000000",
        "exit_capacity_ratio": "1.000000",
        "liquidity_depth_stability_score": "0.901667",
        "reason_codes": [
            "strategy_candidate_liquidity_depth_stability_stable",
            "candidate_screened",
            "liquidity_depth_stability_sufficient",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="score_result must be"):
        strategy_candidate_liquidity_depth_stability_v10_payload(object())


def test_module_is_pure_and_has_no_network_db_execution_or_live_market_surface() -> None:
    source = inspect.getsource(stability_module)
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
