from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_recommendation_portfolio_impact_v2 import (
    CandidateStrategyRecommendationV2,
    ExistingPortfolioPositionV2,
    StrategyRecommendationPortfolioImpactV2Config,
    build_strategy_recommendation_portfolio_impact_v2_report,
    strategy_recommendation_portfolio_impact_v2_payload,
    validate_strategy_recommendation_portfolio_impact_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
SETTLES_ON = date(2026, 11, 3)


def _config() -> StrategyRecommendationPortfolioImpactV2Config:
    return StrategyRecommendationPortfolioImpactV2Config(
        config_version="phase1_portfolio_impact_v2",
        fee_rate=Decimal("0.010000"),
        slippage_rate=Decimal("0.005000"),
        min_confidence=Decimal("0.600000"),
        min_cost_adjusted_edge=Decimal("0.020000"),
        max_exit_liquidity_ratio=Decimal("0.200000"),
        max_category_post_share=Decimal("0.600000"),
        max_correlated_outcome_post_share=Decimal("0.500000"),
        max_settlement_date_post_share=Decimal("0.700000"),
    )


def _candidate(**overrides: object) -> CandidateStrategyRecommendationV2:
    values: dict[str, object] = {
        "candidate_id": "rec-alpha",
        "market_slug": "market-alpha",
        "category_id": "policy",
        "outcome_group_id": "case-alpha",
        "side": "yes",
        "forecast_probability": Decimal("0.620000"),
        "implied_probability": Decimal("0.550000"),
        "confidence": Decimal("0.800000"),
        "target_notional": Decimal("100.000000"),
        "exit_liquidity": Decimal("1000.000000"),
        "spread": Decimal("0.010000"),
        "settlement_date": SETTLES_ON,
    }
    values.update(overrides)
    return CandidateStrategyRecommendationV2(**values)


def _positions() -> tuple[ExistingPortfolioPositionV2, ...]:
    return (
        ExistingPortfolioPositionV2(
            position_id="pos-alpha",
            market_slug="market-beta",
            category_id="policy",
            outcome_group_id="case-alpha",
            notional=Decimal("100.000000"),
            settlement_date=SETTLES_ON,
        ),
        ExistingPortfolioPositionV2(
            position_id="pos-beta",
            market_slug="market-gamma",
            category_id="macro",
            outcome_group_id="rate-path",
            notional=Decimal("200.000000"),
            settlement_date=date(2027, 1, 15),
        ),
    )


def _report():
    return build_strategy_recommendation_portfolio_impact_v2_report(
        _candidate(),
        existing_positions=_positions(),
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_builds_decimal_only_incremental_impact_report_payload() -> None:
    report = _report()

    assert report.raw_edge == Decimal("0.070000")
    assert report.cost_drag == Decimal("0.025000")
    assert report.cost_adjusted_edge == Decimal("0.045000")
    assert report.confidence_haircut_rate == Decimal("0.200000")
    assert report.confidence_haircut_edge == Decimal("0.036000")
    assert report.exit_liquidity_ratio == Decimal("0.100000")
    assert report.category_post_share == Decimal("0.500000")
    assert report.correlated_outcome_post_share == Decimal("0.500000")
    assert report.settlement_date_post_share == Decimal("0.500000")
    assert report.report_status == "paper_recommendable"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = strategy_recommendation_portfolio_impact_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["settlement_date"] == "2026-11-03"
    assert payload["target_notional"] == "100.000000"
    assert payload["cost_adjusted_edge"] == "0.045000"
    assert payload["confidence_haircut_edge"] == "0.036000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert all(not isinstance(value, Decimal) for value in payload.values())


def test_high_risk_portfolio_impact_is_reported_as_watch() -> None:
    report = build_strategy_recommendation_portfolio_impact_v2_report(
        _candidate(
            target_notional=Decimal("400.000000"),
            exit_liquidity=Decimal("1000.000000"),
        ),
        existing_positions=_positions(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.exit_feasibility_status == "exit_liquidity_watch"
    assert report.category_concentration_status == "category_concentration_watch"
    assert report.correlated_outcome_status == "correlated_outcome_watch"
    assert report.settlement_date_cluster_status == "settlement_date_cluster_watch"
    assert report.report_status == "paper_watch"
    assert "exit_liquidity_ratio_above_limit" in report.reason_codes


def test_low_cost_adjusted_edge_is_reported_as_reject() -> None:
    report = build_strategy_recommendation_portfolio_impact_v2_report(
        _candidate(forecast_probability=Decimal("0.570000")),
        existing_positions=_positions(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.cost_adjusted_edge == Decimal("-0.005000")
    assert report.report_status == "paper_reject"
    assert "cost_adjusted_edge_below_minimum" in report.reason_codes


def test_rejects_non_decimal_numeric_inputs() -> None:
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        _candidate(forecast_probability=0.62)

    with pytest.raises(ValueError, match="target_notional must be a Decimal"):
        _candidate(target_notional=100)


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.report_status = "paper_watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        StrategyRecommendationPortfolioImpactV2Config(
            config_version="phase1_portfolio_impact_v2",
            fee_rate=Decimal("0.010000"),
            slippage_rate=Decimal("0.005000"),
            min_confidence=Decimal("0.600000"),
            min_cost_adjusted_edge=Decimal("0.020000"),
            max_exit_liquidity_ratio=Decimal("0.200000"),
            max_category_post_share=Decimal("0.600000"),
            max_correlated_outcome_post_share=Decimal("0.500000"),
            max_settlement_date_post_share=Decimal("0.700000"),
            paper_only=False,
        )


def test_payload_rejects_derived_validation_digest_tampering() -> None:
    report = _report()
    object.__setattr__(report, "cost_adjusted_edge", Decimal("0.990000"))

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        strategy_recommendation_portfolio_impact_v2_payload(report)


def test_rejects_unsafe_public_keys_and_values() -> None:
    with pytest.raises(ValueError, match="candidate_id has unsafe value"):
        _candidate(candidate_id="live-alpha")

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="public payload key has unsafe value"):
            validate_strategy_recommendation_portfolio_impact_v2_public_payload(
                {f"{unsafe_term}_reference": "safe"},
            )
        with pytest.raises(ValueError, match="public payload value has unsafe value"):
            validate_strategy_recommendation_portfolio_impact_v2_public_payload(
                {"safe_reference": f"paper {unsafe_term}"},
            )
