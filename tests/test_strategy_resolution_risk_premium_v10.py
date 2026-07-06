import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path

import pytest


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_risk_premium_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def risk_input(
    *,
    ambiguity_score: str,
    precedent_score: str,
    rule_change_status: str,
    source_disagreement_score: str,
    time_to_resolution_minutes: str,
    dispute_history_rate: str,
):
    strategy = module()
    return strategy.StrategyResolutionRiskPremiumV10Input(
        ambiguity_score=d(ambiguity_score),
        precedent_score=d(precedent_score),
        rule_change_status=rule_change_status,
        source_disagreement_score=d(source_disagreement_score),
        time_to_resolution_minutes=d(time_to_resolution_minutes),
        dispute_history_rate=d(dispute_history_rate),
    )


def build(input_row):
    strategy = module()
    return strategy.build_strategy_resolution_risk_premium_v10(
        input_row,
        config=strategy.StrategyResolutionRiskPremiumV10Config(
            config_version="strategy-resolution-risk-premium-v10-test",
            ambiguity_weight=d("0.300000"),
            precedent_gap_weight=d("0.200000"),
            rule_change_weight=d("0.200000"),
            source_disagreement_weight=d("0.150000"),
            time_pressure_weight=d("0.100000"),
            dispute_history_weight=d("0.050000"),
            max_resolution_risk_premium_bps=d("500.000000"),
            base_required_edge_bps=d("50.000000"),
            watch_risk_premium_bps=d("100.000000"),
            high_risk_premium_bps=d("250.000000"),
            block_risk_premium_bps=d("400.000000"),
            high_ambiguity_threshold=d("0.700000"),
            strong_precedent_threshold=d("0.750000"),
            weak_precedent_threshold=d("0.400000"),
            high_source_disagreement_threshold=d("0.600000"),
            high_time_pressure_minutes=d("1440.000000"),
            time_pressure_cap_minutes=d("10080.000000"),
            high_dispute_history_rate=d("0.200000"),
        ),
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float found in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float(item)


def test_scores_low_resolution_risk_premium_payload() -> None:
    result = build(
        risk_input(
            ambiguity_score="0.100000",
            precedent_score="0.900000",
            rule_change_status="stable",
            source_disagreement_score="0.050000",
            time_to_resolution_minutes="10080.000000",
            dispute_history_rate="0.020000",
        ),
    )

    assert is_dataclass(result)
    assert result.risk_premium_bps == d("29.250000")
    assert result.adjusted_required_edge == d("79.250000")
    assert result.risk_tier == "low"
    assert result.reason_codes == (
        "resolution_risk_low",
        "ambiguity_contained",
        "precedent_strong",
        "rule_change_stable",
        "source_disagreement_contained",
        "resolution_time_pressure_contained",
        "dispute_history_contained",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert result.payload == (
        ("risk_score", "0.058500"),
        ("risk_premium_bps", "29.250000"),
        ("adjusted_required_edge", "79.250000"),
        ("risk_tier", "low"),
        ("ambiguity_score", "0.100000"),
        ("precedent_score", "0.900000"),
        ("rule_change_status", "stable"),
        ("source_disagreement_score", "0.050000"),
        ("time_to_resolution_minutes", "10080.000000"),
        ("time_pressure_score", "0.000000"),
        ("dispute_history_rate", "0.020000"),
        (
            "reason_codes",
            (
                "resolution_risk_low",
                "ambiguity_contained",
                "precedent_strong",
                "rule_change_stable",
                "source_disagreement_contained",
                "resolution_time_pressure_contained",
                "dispute_history_contained",
            ),
        ),
    )

    payload = module().strategy_resolution_risk_premium_v10_payload(result)
    assert payload["risk_premium_bps"] == "29.250000"
    assert payload["adjusted_required_edge"] == "79.250000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert_no_float(payload)


def test_scores_high_resolution_risk_premium_from_ambiguity_and_disputes() -> None:
    result = build(
        risk_input(
            ambiguity_score="0.800000",
            precedent_score="0.350000",
            rule_change_status="active",
            source_disagreement_score="0.700000",
            time_to_resolution_minutes="120.000000",
            dispute_history_rate="0.300000",
        ),
    )

    assert result.risk_premium_bps == d("369.405000")
    assert result.adjusted_required_edge == d("419.405000")
    assert result.risk_tier == "high"
    assert result.reason_codes == (
        "resolution_risk_high",
        "ambiguity_high",
        "precedent_weak",
        "rule_change_active",
        "source_disagreement_high",
        "resolution_time_pressure_high",
        "dispute_history_high",
    )


def test_validation_rejects_float_status_and_bad_thresholds() -> None:
    strategy = module()

    with pytest.raises(ValueError, match="ambiguity_score must be a Decimal"):
        strategy.StrategyResolutionRiskPremiumV10Input(
            ambiguity_score=0.8,  # type: ignore[arg-type]
            precedent_score=d("0.500000"),
            rule_change_status="stable",
            source_disagreement_score=d("0.200000"),
            time_to_resolution_minutes=d("60.000000"),
            dispute_history_rate=d("0.050000"),
        )

    with pytest.raises(ValueError, match="rule_change_status"):
        risk_input(
            ambiguity_score="0.100000",
            precedent_score="0.900000",
            rule_change_status="wallet_review",
            source_disagreement_score="0.050000",
            time_to_resolution_minutes="10080.000000",
            dispute_history_rate="0.020000",
        )

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        risk_input(
            ambiguity_score="0.100000",
            precedent_score="0.900000",
            rule_change_status="stable",
            source_disagreement_score="0.050000",
            time_to_resolution_minutes="-1.000000",
            dispute_history_rate="0.020000",
        )

    with pytest.raises(ValueError, match="risk premium thresholds"):
        strategy.StrategyResolutionRiskPremiumV10Config(
            watch_risk_premium_bps=d("300.000000"),
            high_risk_premium_bps=d("250.000000"),
        )

    with pytest.raises(ValueError, match="readonly"):
        strategy.StrategyResolutionRiskPremiumV10Config(readonly=False)


def test_public_contract_is_frozen_decimal_only_and_unwired() -> None:
    strategy = module()

    assert strategy.__all__ == (
        "DEFAULT_STRATEGY_RESOLUTION_RISK_PREMIUM_V10_CONFIG_VERSION",
        "RULE_CHANGE_STATUSES",
        "RISK_TIERS",
        "StrategyResolutionRiskPremiumV10Config",
        "StrategyResolutionRiskPremiumV10Input",
        "StrategyResolutionRiskPremiumV10Result",
        "build_strategy_resolution_risk_premium_v10",
        "strategy_resolution_risk_premium_v10_payload",
    )

    for exported_name in strategy.__all__:
        value = getattr(strategy, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True
            for field in fields(value):
                if any(
                    fragment in field.name
                    for fragment in (
                        "score",
                        "premium",
                        "edge",
                        "weight",
                        "threshold",
                        "minutes",
                        "rate",
                    )
                ):
                    assert value.__annotations__[field.name] is Decimal

    result = build(
        risk_input(
            ambiguity_score="0.100000",
            precedent_score="0.900000",
            rule_change_status="stable",
            source_disagreement_score="0.050000",
            time_to_resolution_minutes="10080.000000",
            dispute_history_rate="0.020000",
        ),
    )
    with pytest.raises(FrozenInstanceError):
        result.risk_premium_bps = d("0.000000")  # type: ignore[misc]

    source = Path(
        "src/polymarket_alpha_lab/strategy_resolution_risk_premium_v10.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports |= {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    calls |= {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imports <= {"dataclasses", "decimal", "polymarket_alpha_lab"}
    assert not {
        "open",
        "connect",
        "execute",
        "executemany",
        "request",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "buy",
        "sell",
        "place_order",
        "submit_order",
        "sign_order",
    } & calls
    assert "strategy_resolution_risk_premium_v10" not in __import__(
        "polymarket_alpha_lab",
    ).__all__
