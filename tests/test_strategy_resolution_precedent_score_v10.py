from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path

import pytest


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_precedent_score_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def market(
    market_id: str,
    *,
    rules_text_clarity: str,
    similar_historical_event_count: str,
    historical_dispute_rate: str,
    oracle_source_type: str,
    deadline_consistency_score: str,
):
    strategy = module()
    return strategy.StrategyResolutionPrecedentScoreV10Input(
        market_id=market_id,
        rules_text_clarity=d(rules_text_clarity),
        similar_historical_event_count=d(similar_historical_event_count),
        historical_dispute_rate=d(historical_dispute_rate),
        oracle_source_type=oracle_source_type,
        deadline_consistency_score=d(deadline_consistency_score),
    )


def build(input_row):
    strategy = module()
    return strategy.build_strategy_resolution_precedent_score_v10(
        input_row,
        config=strategy.StrategyResolutionPrecedentScoreV10Config(
            config_version="strategy-resolution-precedent-score-v10-test",
            rules_text_clarity_weight=d("0.400000"),
            similar_history_weight=d("0.200000"),
            dispute_rate_weight=d("0.200000"),
            oracle_source_weight=d("0.100000"),
            deadline_consistency_weight=d("0.100000"),
            similar_history_count_cap=d("10"),
            clear_precedent_threshold=d("0.800000"),
            manual_review_score_threshold=d("0.600000"),
            high_ambiguity_penalty=d("0.400000"),
            limited_history_count=d("3"),
            high_dispute_rate=d("0.250000"),
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


def test_scores_clear_market_with_strong_resolution_precedent_payload() -> None:
    result = build(
        market(
            "market-clear",
            rules_text_clarity="0.950000",
            similar_historical_event_count="8",
            historical_dispute_rate="0.020000",
            oracle_source_type="official",
            deadline_consistency_score="0.900000",
        ),
    )

    assert is_dataclass(result)
    assert result.market_id == "market-clear"
    assert result.precedent_score == d("0.926000")
    assert result.ambiguity_penalty == d("0.034000")
    assert result.needs_manual_review is False
    assert result.reason_codes == (
        "resolution_precedent_strong",
        "rules_text_clear",
        "sufficient_resolution_history",
        "low_historical_dispute_rate",
        "official_oracle_source",
        "deadline_consistency_clear",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert result.payload == (
        ("market_id", "market-clear"),
        ("precedent_score", "0.926000"),
        ("ambiguity_penalty", "0.034000"),
        ("needs_manual_review", False),
        ("rules_text_clarity", "0.950000"),
        ("similar_historical_event_count", "8"),
        ("historical_dispute_rate", "0.020000"),
        ("oracle_source_type", "official"),
        ("deadline_consistency_score", "0.900000"),
        (
            "reason_codes",
            (
                "resolution_precedent_strong",
                "rules_text_clear",
                "sufficient_resolution_history",
                "low_historical_dispute_rate",
                "official_oracle_source",
                "deadline_consistency_clear",
            ),
        ),
    )

    payload = module().strategy_resolution_precedent_score_v10_payload(result)
    assert payload["precedent_score"] == "0.926000"
    assert payload["ambiguity_penalty"] == "0.034000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert_no_float(payload)


def test_requires_manual_review_when_resolution_precedent_is_weak() -> None:
    result = build(
        market(
            "market-manual-review",
            rules_text_clarity="0.300000",
            similar_historical_event_count="1",
            historical_dispute_rate="0.350000",
            oracle_source_type="community_resolution",
            deadline_consistency_score="0.400000",
        ),
    )

    assert result.precedent_score == d("0.355000")
    assert result.ambiguity_penalty == d("0.465000")
    assert result.needs_manual_review is True
    assert result.reason_codes == (
        "resolution_precedent_manual_review",
        "rules_text_ambiguous",
        "limited_resolution_history",
        "historical_dispute_rate_high",
        "community_resolution_source",
        "deadline_consistency_weak",
    )


def test_validation_rejects_non_decimal_values_fractional_counts_and_bad_flags() -> None:
    strategy = module()

    with pytest.raises(ValueError, match="rules_text_clarity must be a Decimal"):
        strategy.StrategyResolutionPrecedentScoreV10Input(
            market_id="float-risk",
            rules_text_clarity=0.9,  # type: ignore[arg-type]
            similar_historical_event_count=d("2"),
            historical_dispute_rate=d("0.050000"),
            oracle_source_type="official",
            deadline_consistency_score=d("0.900000"),
        )

    with pytest.raises(ValueError, match="similar_historical_event_count must be a whole"):
        market(
            "fractional-history",
            rules_text_clarity="0.900000",
            similar_historical_event_count="1.5",
            historical_dispute_rate="0.050000",
            oracle_source_type="official",
            deadline_consistency_score="0.900000",
        )

    with pytest.raises(ValueError, match="oracle_source_type"):
        market(
            "bad-oracle",
            rules_text_clarity="0.900000",
            similar_historical_event_count="2",
            historical_dispute_rate="0.050000",
            oracle_source_type="wallet_oracle",
            deadline_consistency_score="0.900000",
        )

    with pytest.raises(ValueError, match="paper_only"):
        strategy.StrategyResolutionPrecedentScoreV10Config(paper_only=False)


def test_public_contract_is_frozen_decimal_only_and_unwired() -> None:
    strategy = module()

    assert strategy.__all__ == (
        "DEFAULT_STRATEGY_RESOLUTION_PRECEDENT_SCORE_V10_CONFIG_VERSION",
        "ORACLE_SOURCE_TYPES",
        "StrategyResolutionPrecedentScoreV10Config",
        "StrategyResolutionPrecedentScoreV10Input",
        "StrategyResolutionPrecedentScoreV10Result",
        "build_strategy_resolution_precedent_score_v10",
        "strategy_resolution_precedent_score_v10_payload",
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
                        "penalty",
                        "rate",
                        "count",
                        "threshold",
                        "weight",
                        "clarity",
                        "consistency",
                    )
                ):
                    assert value.__annotations__[field.name] is Decimal

    result = build(
        market(
            "frozen-result",
            rules_text_clarity="0.950000",
            similar_historical_event_count="8",
            historical_dispute_rate="0.020000",
            oracle_source_type="official",
            deadline_consistency_score="0.900000",
        ),
    )
    with pytest.raises(FrozenInstanceError):
        result.precedent_score = d("0.100000")  # type: ignore[misc]

    source = Path(
        "src/polymarket_alpha_lab/strategy_resolution_precedent_score_v10.py",
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
    assert "strategy_resolution_precedent_score_v10" not in __import__(
        "polymarket_alpha_lab",
    ).__all__
