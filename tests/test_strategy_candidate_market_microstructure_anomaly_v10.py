from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    strategy_candidate_market_microstructure_anomaly_v10 as anomaly_module,
)
from polymarket_alpha_lab.strategy_candidate_market_microstructure_anomaly_v10 import (
    StrategyCandidateMarketMicrostructureAnomalyConfig,
    StrategyCandidateMarketMicrostructureAnomalyInput,
    StrategyCandidateMarketMicrostructureAnomalyScore,
    score_strategy_candidate_market_microstructure_anomaly_v10,
    strategy_candidate_market_microstructure_anomaly_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateMarketMicrostructureAnomalyConfig:
    values = {
        "config_version": "strategy-candidate-market-microstructure-anomaly-test-v10",
        "minimum_anomaly_score": d("0.700000"),
        "minimum_watch_score": d("0.450000"),
        "maximum_spread_shock": d("0.050000"),
        "maximum_depth_imbalance": d("0.650000"),
        "maximum_sudden_price_jump": d("0.100000"),
        "maximum_volume_concentration": d("0.750000"),
        "spread_shock_weight": d("0.200000"),
        "depth_imbalance_weight": d("0.200000"),
        "price_jump_weight": d("0.200000"),
        "book_thinness_weight": d("0.200000"),
        "volume_concentration_weight": d("0.200000"),
    }
    values.update(overrides)
    return StrategyCandidateMarketMicrostructureAnomalyConfig(**values)


def candidate(**overrides: object) -> StrategyCandidateMarketMicrostructureAnomalyInput:
    values = {
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "best_bid_price": d("0.500000"),
        "best_ask_price": d("0.515000"),
        "reference_bid_ask_spread": d("0.010000"),
        "previous_mid_price": d("0.500000"),
        "current_mid_price": d("0.510000"),
        "bid_depth_notional": d("1200.000000"),
        "ask_depth_notional": d("1000.000000"),
        "target_depth_notional": d("2000.000000"),
        "recent_volume_notional": d("2000.000000"),
        "largest_fill_notional": d("200.000000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyCandidateMarketMicrostructureAnomalyInput(**values)


def score(
    candidate_state: StrategyCandidateMarketMicrostructureAnomalyInput
    | object
    | None = None,
    strategy_config: StrategyCandidateMarketMicrostructureAnomalyConfig | object | None = None,
) -> StrategyCandidateMarketMicrostructureAnomalyScore:
    return score_strategy_candidate_market_microstructure_anomaly_v10(
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


def test_normal_candidate_scores_microstructure_anomaly_components() -> None:
    result = score()

    assert result.config_version == (
        "strategy-candidate-market-microstructure-anomaly-test-v10"
    )
    assert result.candidate_id == "candidate-001"
    assert result.market_slug == "fed-cuts-by-september"
    assert result.outcome_name == "Yes"
    assert result.anomaly_status == "normal"
    assert result.bid_ask_spread == d("0.015000")
    assert result.spread_shock == d("0.005000")
    assert result.spread_shock_score == d("0.100000")
    assert result.depth_imbalance_ratio == d("0.090909")
    assert result.depth_imbalance_score == d("0.090909")
    assert result.sudden_price_jump == d("0.010000")
    assert result.price_jump_score == d("0.100000")
    assert result.book_depth_notional == d("2200.000000")
    assert result.book_depth_coverage_ratio == d("1.000000")
    assert result.book_thinness_score == d("0.000000")
    assert result.volume_concentration_ratio == d("0.100000")
    assert result.volume_concentration_score == d("0.100000")
    assert result.market_microstructure_anomaly_score == d("0.078182")
    assert result.reason_codes == (
        "strategy_candidate_market_microstructure_anomaly_normal",
        "candidate_screened",
        "market_microstructure_within_limits",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_anomalous_candidate_reports_each_microstructure_blocker() -> None:
    result = score(
        candidate(
            best_bid_price=d("0.480000"),
            best_ask_price=d("0.560000"),
            previous_mid_price=d("0.500000"),
            current_mid_price=d("0.620000"),
            bid_depth_notional=d("100.000000"),
            ask_depth_notional=d("700.000000"),
            recent_volume_notional=d("1000.000000"),
            largest_fill_notional=d("900.000000"),
        ),
    )

    assert result.anomaly_status == "anomalous"
    assert result.bid_ask_spread == d("0.080000")
    assert result.spread_shock == d("0.070000")
    assert result.spread_shock_score == d("1.000000")
    assert result.depth_imbalance_ratio == d("0.750000")
    assert result.price_jump_score == d("1.000000")
    assert result.book_depth_coverage_ratio == d("0.400000")
    assert result.book_thinness_score == d("0.600000")
    assert result.volume_concentration_ratio == d("0.900000")
    assert result.market_microstructure_anomaly_score == d("0.850000")
    assert result.reason_codes == (
        "strategy_candidate_market_microstructure_anomaly_anomalous",
        "candidate_screened",
        "spread_shock_above_limit",
        "depth_imbalance_above_limit",
        "sudden_price_jump_above_limit",
        "book_depth_below_target",
        "recent_volume_concentration_above_limit",
    )


def test_watch_candidate_when_composite_is_mid_quality() -> None:
    result = score(
        candidate(
            best_bid_price=d("0.470000"),
            best_ask_price=d("0.530000"),
            previous_mid_price=d("0.500000"),
            current_mid_price=d("0.580000"),
            bid_depth_notional=d("1000.000000"),
            ask_depth_notional=d("1000.000000"),
            recent_volume_notional=d("1000.000000"),
            largest_fill_notional=d("500.000000"),
        ),
    )

    assert result.anomaly_status == "watch"
    assert result.market_microstructure_anomaly_score == d("0.460000")
    assert result.reason_codes == (
        "strategy_candidate_market_microstructure_anomaly_watch",
        "candidate_screened",
        "spread_shock_above_limit",
    )


def test_outputs_are_frozen_typed_decimal_quantized_tuple_only_and_readonly() -> None:
    candidate_state = candidate(best_ask_price=d("0.5150001"))
    result = score(candidate_state)

    assert candidate_state.best_ask_price == d("0.515000")
    assert type(result.market_microstructure_anomaly_score) is Decimal
    assert type(result.reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        result.anomaly_status = "anomalous"  # type: ignore[misc]
    with pytest.raises(ValueError, match="current_mid_price must be a Decimal"):
        replace(candidate_state, current_mid_price=0.51)
    with pytest.raises(ValueError, match="target_depth_notional must be positive"):
        replace(candidate_state, target_depth_notional=d("0.000000"))
    with pytest.raises(ValueError, match="best_ask_price must be greater than or equal"):
        replace(candidate_state, best_ask_price=d("0.499999"))
    with pytest.raises(ValueError, match="largest_fill_notional must be less than or equal"):
        replace(candidate_state, largest_fill_notional=d("2000.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(candidate_state, reason_codes=["candidate_screened"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(candidate_state, reason_codes=("candidate_screened", "candidate_screened"))
    with pytest.raises(ValueError, match="anomaly_status"):
        replace(result, anomaly_status="ready")
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_rejects_wrong_public_types_subclasses_and_bad_config() -> None:
    with pytest.raises(TypeError, match="must not be subclassed"):

        class CandidateSubclass(StrategyCandidateMarketMicrostructureAnomalyInput):
            pass

    with pytest.raises(ValueError, match="candidate_state"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(strategy_config=object())
    with pytest.raises(ValueError, match="minimum_watch_score"):
        config(minimum_watch_score=d("0.710000"))
    with pytest.raises(ValueError, match="maximum_spread_shock must be positive"):
        config(maximum_spread_shock=d("0.000000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(volume_concentration_weight=d("0.100000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)


def test_payload_uses_decimal_strings_flags_and_no_floats() -> None:
    result = score()

    payload = strategy_candidate_market_microstructure_anomaly_v10_payload(result)

    assert payload["validation_digest"] == result.validation_digest
    assert len(result.validation_digest) == 64
    assert payload == {
        "config_version": "strategy-candidate-market-microstructure-anomaly-test-v10",
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "anomaly_status": "normal",
        "best_bid_price": "0.500000",
        "best_ask_price": "0.515000",
        "reference_bid_ask_spread": "0.010000",
        "bid_ask_spread": "0.015000",
        "spread_shock": "0.005000",
        "spread_shock_score": "0.100000",
        "previous_mid_price": "0.500000",
        "current_mid_price": "0.510000",
        "sudden_price_jump": "0.010000",
        "price_jump_score": "0.100000",
        "bid_depth_notional": "1200.000000",
        "ask_depth_notional": "1000.000000",
        "book_depth_notional": "2200.000000",
        "target_depth_notional": "2000.000000",
        "depth_imbalance_ratio": "0.090909",
        "depth_imbalance_score": "0.090909",
        "book_depth_coverage_ratio": "1.000000",
        "book_thinness_score": "0.000000",
        "recent_volume_notional": "2000.000000",
        "largest_fill_notional": "200.000000",
        "volume_concentration_ratio": "0.100000",
        "volume_concentration_score": "0.100000",
        "market_microstructure_anomaly_score": "0.078182",
        "validation_digest": result.validation_digest,
        "reason_codes": [
            "strategy_candidate_market_microstructure_anomaly_normal",
            "candidate_screened",
            "market_microstructure_within_limits",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="score_result must be"):
        strategy_candidate_market_microstructure_anomaly_v10_payload(object())


def test_result_rejects_tampered_derived_fields_and_digest() -> None:
    result = score()

    with pytest.raises(ValueError, match="bid_ask_spread must match prices"):
        replace(result, bid_ask_spread=d("0.020000"))
    with pytest.raises(ValueError, match="spread_shock must match spread inputs"):
        replace(result, spread_shock=d("0.006000"))
    with pytest.raises(ValueError, match="sudden_price_jump must match mid prices"):
        replace(result, sudden_price_jump=d("0.020000"))
    with pytest.raises(ValueError, match="book_depth_notional must match depths"):
        replace(result, book_depth_notional=d("2100.000000"))
    with pytest.raises(ValueError, match="depth_imbalance_score must match"):
        replace(result, depth_imbalance_score=d("0.100000"))
    with pytest.raises(ValueError, match="book_thinness_score must match"):
        replace(result, book_thinness_score=d("0.100000"))
    with pytest.raises(ValueError, match="volume_concentration_score must match"):
        replace(result, volume_concentration_score=d("0.200000"))
    with pytest.raises(ValueError, match="validation_digest must match score_result"):
        replace(result, validation_digest="0" * 64)


def test_dataclasses_reject_subclasses_and_unsafe_payload_surfaces() -> None:
    for name in anomaly_module.__all__:
        exported = getattr(anomaly_module, name)
        if is_dataclass(exported):
            assert exported.__dataclass_params__.frozen is True
            with pytest.raises(TypeError, match="must not be subclassed"):

                class Derived(exported):  # type: ignore[misc, valid-type]
                    pass

    with pytest.raises(ValueError, match="unsafe payload surface"):
        anomaly_module._reject_unsafe_payload_surface(
            "market microstructure anomaly payload",
            {"order_id": "abc123"},
        )


def test_module_is_pure_and_has_no_network_db_execution_or_live_market_surface() -> None:
    source = inspect.getsource(anomaly_module)
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
