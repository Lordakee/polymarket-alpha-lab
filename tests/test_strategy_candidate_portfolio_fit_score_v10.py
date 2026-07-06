import ast
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.strategy_candidate_portfolio_fit_score_v10 as module
from polymarket_alpha_lab.strategy_candidate_portfolio_fit_score_v10 import (
    StrategyCandidatePortfolioFitScoreV10Input,
    StrategyCandidatePortfolioFitScoreV10Penalties,
    StrategyCandidatePortfolioFitScoreV10Result,
    score_strategy_candidate_portfolio_fit_v10,
    strategy_candidate_portfolio_fit_score_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate_input(**overrides):
    values = {
        "market_id": "market-alpha",
        "category": "macro",
        "cost_adjusted_edge_bps": d("350.000000"),
        "cluster_correlation_score": d("0.200000"),
        "current_category_exposure": d("0.150000"),
        "liquidity_score": d("0.850000"),
        "resolution_risk_tier": "low",
        "team_fit_score": d("0.900000"),
    }
    values.update(overrides)
    return StrategyCandidatePortfolioFitScoreV10Input(**values)


def result_values(result):
    return {
        "market_id": result.market_id,
        "category": result.category,
        "cost_adjusted_edge_bps": result.cost_adjusted_edge_bps,
        "cluster_correlation_score": result.cluster_correlation_score,
        "current_category_exposure": result.current_category_exposure,
        "liquidity_score": result.liquidity_score,
        "resolution_risk_tier": result.resolution_risk_tier,
        "team_fit_score": result.team_fit_score,
        "portfolio_fit_status": result.portfolio_fit_status,
        "fit_score": result.fit_score,
        "fit_penalties": result.fit_penalties,
        "reason_codes": result.reason_codes,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }


def assert_safe_payload(value):
    if type(value) is dict:
        for key, item in value.items():
            assert type(key) is str
            assert_safe_payload(item)
        return
    if type(value) is list:
        for item in value:
            assert_safe_payload(item)
        return
    assert type(value) in {str, bool}


def test_strategy_scores_strong_candidate_as_portfolio_fit_readonly_report():
    result = score_strategy_candidate_portfolio_fit_v10(candidate_input())

    assert type(result) is StrategyCandidatePortfolioFitScoreV10Result
    assert result.market_id == "market-alpha"
    assert result.category == "macro"
    assert result.portfolio_fit_status == "fit"
    assert result.fit_score == d("0.795000")
    assert result.fit_penalties == StrategyCandidatePortfolioFitScoreV10Penalties(
        edge_penalty=d("0.000000"),
        correlation_penalty=d("0.000000"),
        category_exposure_penalty=d("0.000000"),
        liquidity_penalty=d("0.000000"),
        resolution_risk_penalty=d("0.000000"),
        team_fit_penalty=d("0.000000"),
    )
    assert result.reason_codes == (
        "fit_score_meets_floor",
        "positive_cost_adjusted_edge",
        "cluster_correlation_within_limit",
        "category_exposure_within_limit",
        "liquidity_score_supported",
        "resolution_risk_low",
        "team_fit_supported",
        "portfolio_fit_clear",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == strategy_candidate_portfolio_fit_score_v10_payload(result)


def test_strategy_watches_candidate_when_portfolio_penalties_drag_fit_score():
    result = score_strategy_candidate_portfolio_fit_v10(
        candidate_input(
            market_id="market-watch",
            cost_adjusted_edge_bps=d("150.000000"),
            cluster_correlation_score=d("0.820000"),
            current_category_exposure=d("0.450000"),
            liquidity_score=d("0.400000"),
            resolution_risk_tier="medium",
            team_fit_score=d("0.450000"),
        ),
    )

    assert result.portfolio_fit_status == "watch"
    assert result.fit_score == d("0.140500")
    assert result.fit_penalties.total_penalty == d("0.215000")
    assert result.fit_penalties.correlation_penalty == d("0.060000")
    assert result.fit_penalties.category_exposure_penalty == d("0.060000")
    assert result.fit_penalties.liquidity_penalty == d("0.030000")
    assert result.fit_penalties.resolution_risk_penalty == d("0.050000")
    assert result.fit_penalties.team_fit_penalty == d("0.015000")
    assert result.reason_codes == (
        "fit_score_below_fit_floor",
        "positive_cost_adjusted_edge",
        "cluster_correlation_penalty_applied",
        "category_exposure_penalty_applied",
        "liquidity_penalty_applied",
        "resolution_risk_medium_penalty_applied",
        "team_fit_penalty_applied",
    )


def test_strategy_blocks_candidate_with_nonpositive_edge_and_hard_portfolio_limits():
    result = score_strategy_candidate_portfolio_fit_v10(
        candidate_input(
            market_id="market-blocked",
            cost_adjusted_edge_bps=d("-20.000000"),
            cluster_correlation_score=d("0.910000"),
            current_category_exposure=d("0.880000"),
            liquidity_score=d("0.200000"),
            resolution_risk_tier="critical",
            team_fit_score=d("0.250000"),
        ),
    )

    assert result.portfolio_fit_status == "blocked"
    assert result.fit_score == d("0.000000")
    assert result.fit_penalties.edge_penalty == d("0.240000")
    assert result.fit_penalties.correlation_penalty == d("0.105000")
    assert result.fit_penalties.category_exposure_penalty == d("0.200000")
    assert result.fit_penalties.liquidity_penalty == d("0.090000")
    assert result.fit_penalties.resolution_risk_penalty == d("0.300000")
    assert result.fit_penalties.team_fit_penalty == d("0.075000")
    assert result.reason_codes == (
        "cost_adjusted_edge_nonpositive_blocked",
        "cluster_correlation_above_block_limit",
        "category_exposure_above_block_limit",
        "liquidity_score_below_block_floor",
        "resolution_risk_critical_blocked",
        "team_fit_below_block_floor",
    )


def test_strategy_quantizes_decimal_inputs_and_payload_is_json_ready():
    result = score_strategy_candidate_portfolio_fit_v10(
        candidate_input(
            cost_adjusted_edge_bps=d("333.3333334"),
            cluster_correlation_score=d("0.3000004"),
            current_category_exposure=d("0.2400004"),
            liquidity_score=d("0.7700004"),
            team_fit_score=d("0.8800004"),
        ),
    )
    payload = strategy_candidate_portfolio_fit_score_v10_payload(result)

    assert result.cost_adjusted_edge_bps == d("333.333333")
    assert result.cluster_correlation_score == d("0.300000")
    assert result.current_category_exposure == d("0.240000")
    assert result.liquidity_score == d("0.770000")
    assert result.team_fit_score == d("0.880000")
    assert result.fit_score == d("0.740333")
    assert payload == result.payload
    assert payload["fit_score"] == "0.740333"
    assert payload["fit_penalties"]["total_penalty"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_safe_payload(payload)


def test_strategy_rejects_non_decimal_scores_bad_ranges_bad_tiers_and_bad_flags():
    with pytest.raises(ValueError, match="cost_adjusted_edge_bps must be a Decimal"):
        candidate_input(cost_adjusted_edge_bps=350)
    with pytest.raises(ValueError, match="cluster_correlation_score must be less than or equal to one"):
        candidate_input(cluster_correlation_score=d("1.000001"))
    with pytest.raises(ValueError, match="current_category_exposure must be nonnegative"):
        candidate_input(current_category_exposure=d("-0.000001"))
    with pytest.raises(ValueError, match="resolution_risk_tier is not supported"):
        candidate_input(resolution_risk_tier="unknown")
    with pytest.raises(ValueError, match="category must be single-line text"):
        candidate_input(category="macro\npayload")
    with pytest.raises(ValueError, match="input must be paper_only"):
        candidate_input(paper_only=False)
    with pytest.raises(ValueError, match="input must be readonly"):
        candidate_input(readonly=False)


def test_strategy_dataclasses_are_frozen_and_public_build_rejects_bad_type():
    value = candidate_input()
    result = score_strategy_candidate_portfolio_fit_v10(value)

    with pytest.raises(FrozenInstanceError):
        value.market_id = "other-market"
    with pytest.raises(FrozenInstanceError):
        result.portfolio_fit_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        result.fit_penalties.edge_penalty = d("0.100000")
    with pytest.raises(ValueError, match="candidate"):
        score_strategy_candidate_portfolio_fit_v10(object())


def test_strategy_result_rejects_tampered_derived_fields():
    result = score_strategy_candidate_portfolio_fit_v10(candidate_input())
    values = result_values(result)

    with pytest.raises(ValueError, match="fit_score must match portfolio-fit inputs"):
        StrategyCandidatePortfolioFitScoreV10Result(
            **{**values, "fit_score": d("0.900000")},
        )
    with pytest.raises(ValueError, match="portfolio_fit_status must match portfolio-fit inputs"):
        StrategyCandidatePortfolioFitScoreV10Result(
            **{**values, "portfolio_fit_status": "watch"},
        )
    with pytest.raises(ValueError, match="reason_codes must match portfolio-fit inputs"):
        StrategyCandidatePortfolioFitScoreV10Result(
            **{**values, "reason_codes": ("fit_score_meets_floor",)},
        )
    with pytest.raises(ValueError, match="fit_penalties must match portfolio-fit inputs"):
        StrategyCandidatePortfolioFitScoreV10Result(
            **{
                **values,
                "fit_penalties": StrategyCandidatePortfolioFitScoreV10Penalties(
                    edge_penalty=d("0.010000"),
                    correlation_penalty=d("0.000000"),
                    category_exposure_penalty=d("0.000000"),
                    liquidity_penalty=d("0.000000"),
                    resolution_risk_penalty=d("0.000000"),
                    team_fit_penalty=d("0.000000"),
                ),
            },
        )


def test_strategy_payload_rejects_unsafe_nested_values(monkeypatch):
    result = score_strategy_candidate_portfolio_fit_v10(candidate_input())

    def unsafe_penalties_payload(_penalties):
        return {"edge_penalty": d("0.000000")}

    monkeypatch.setattr(module, "_penalties_payload", unsafe_penalties_payload)
    with pytest.raises(ValueError, match="payload Decimal values must be rendered as strings"):
        module.strategy_candidate_portfolio_fit_score_v10_payload(result)


def test_strategy_module_has_no_live_trading_persistence_or_network_surface():
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_portfolio_fit_score_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "auth",
        "wallet",
        "signing",
        "order placement",
        "database",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
