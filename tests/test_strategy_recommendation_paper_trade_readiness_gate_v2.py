from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_recommendation_paper_trade_readiness_gate_v2 import (
    StrategyRecommendationPaperTradeReadinessConfig,
    StrategyRecommendationPaperTradeReadinessDecision,
    StrategyRecommendationPaperTradeReadinessInput,
    evaluate_strategy_recommendation_paper_trade_readiness,
)


EVALUATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def _config(
    *,
    max_evidence_age_seconds: int = 300,
    min_expected_value_after_costs: Decimal = Decimal("0.020000"),
    min_liquidity_usd: Decimal = Decimal("1000.000000"),
    max_resolution_risk: Decimal = Decimal("0.150000"),
    min_team_approval_count: int = 2,
    required_manual_checks: tuple[str, ...] = (
        "legal_review",
        "resolution_source_review",
    ),
) -> StrategyRecommendationPaperTradeReadinessConfig:
    return StrategyRecommendationPaperTradeReadinessConfig(
        config_version="phase1-v2",
        max_evidence_age_seconds=max_evidence_age_seconds,
        min_expected_value_after_costs=min_expected_value_after_costs,
        min_liquidity_usd=min_liquidity_usd,
        max_resolution_risk=max_resolution_risk,
        min_team_approval_count=min_team_approval_count,
        required_manual_checks=required_manual_checks,
    )


def _candidate(
    *,
    recommendation_id: str = "rec-001",
    market_slug: str = "will-example-resolve-yes",
    side: str = "yes",
    evidence_generated_at: datetime = EVALUATED_AT - timedelta(seconds=120),
    expected_value_before_costs: Decimal = Decimal("0.034000"),
    estimated_cost_per_share: Decimal = Decimal("0.004000"),
    available_liquidity_usd: Decimal = Decimal("2500.000000"),
    resolution_risk: Decimal = Decimal("0.050000"),
    team_approval_count: int = 3,
    completed_manual_checks: tuple[str, ...] = (
        "legal_review",
        "resolution_source_review",
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
    live_trading_enabled: bool = False,
    network_access_allowed: bool = False,
    wallet_required: bool = False,
    orders_allowed: bool = False,
    db_writes_allowed: bool = False,
) -> StrategyRecommendationPaperTradeReadinessInput:
    return StrategyRecommendationPaperTradeReadinessInput(
        recommendation_id=recommendation_id,
        market_slug=market_slug,
        side=side,
        evidence_generated_at=evidence_generated_at,
        expected_value_before_costs=expected_value_before_costs,
        estimated_cost_per_share=estimated_cost_per_share,
        available_liquidity_usd=available_liquidity_usd,
        resolution_risk=resolution_risk,
        team_approval_count=team_approval_count,
        completed_manual_checks=completed_manual_checks,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
        live_trading_enabled=live_trading_enabled,
        network_access_allowed=network_access_allowed,
        wallet_required=wallet_required,
        orders_allowed=orders_allowed,
        db_writes_allowed=db_writes_allowed,
    )


def _evaluate(
    candidate: StrategyRecommendationPaperTradeReadinessInput,
    *,
    config: StrategyRecommendationPaperTradeReadinessConfig | None = None,
    evaluated_at: datetime = EVALUATED_AT,
) -> StrategyRecommendationPaperTradeReadinessDecision:
    return evaluate_strategy_recommendation_paper_trade_readiness(
        candidate,
        config=config or _config(),
        evaluated_at=evaluated_at,
    )


def test_gate_marks_candidate_ready_only_for_paper_execution_when_all_checks_pass():
    decision = _evaluate(_candidate())

    assert decision == StrategyRecommendationPaperTradeReadinessDecision(
        recommendation_id="rec-001",
        market_slug="will-example-resolve-yes",
        side="yes",
        readiness_status="ready",
        evidence_age_seconds=120,
        expected_value_after_costs=Decimal("0.030000"),
        missing_manual_checks=(),
        reason_codes=("paper_trade_ready",),
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True
    assert decision.live_trading_enabled is False
    assert decision.network_access_allowed is False
    assert decision.wallet_required is False
    assert decision.orders_allowed is False
    assert decision.db_writes_allowed is False
    with pytest.raises(FrozenInstanceError):
        decision.readiness_status = "blocked"  # type: ignore[misc]


def test_gate_blocks_with_deterministic_reason_codes_for_all_failed_checks():
    decision = _evaluate(
        _candidate(
            evidence_generated_at=EVALUATED_AT - timedelta(seconds=301),
            expected_value_before_costs=Decimal("0.019000"),
            estimated_cost_per_share=Decimal("0.004000"),
            available_liquidity_usd=Decimal("999.999999"),
            resolution_risk=Decimal("0.150001"),
            team_approval_count=1,
            completed_manual_checks=("resolution_source_review",),
        ),
    )

    assert decision.readiness_status == "blocked"
    assert decision.evidence_age_seconds == 301
    assert decision.expected_value_after_costs == Decimal("0.015000")
    assert decision.missing_manual_checks == ("legal_review",)
    assert decision.reason_codes == (
        "evidence_stale",
        "expected_value_after_costs_below_minimum",
        "liquidity_below_minimum",
        "resolution_risk_above_maximum",
        "team_quorum_not_met",
        "manual_checks_missing",
    )


def test_gate_blocks_future_dated_evidence_without_negative_age():
    decision = _evaluate(
        _candidate(evidence_generated_at=EVALUATED_AT + timedelta(seconds=1)),
    )

    assert decision.readiness_status == "blocked"
    assert decision.evidence_age_seconds == 0
    assert decision.reason_codes == ("evidence_timestamp_after_evaluation",)


def test_gate_uses_decimal_only_cost_arithmetic_and_accepts_aware_evaluation_time():
    evaluated_at = datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7)))
    decision = _evaluate(
        _candidate(
            evidence_generated_at=EVALUATED_AT - timedelta(seconds=240),
            expected_value_before_costs=Decimal("0.100000"),
            estimated_cost_per_share=Decimal("0.070000"),
        ),
        evaluated_at=evaluated_at,
    )

    assert decision.evidence_age_seconds == 240
    assert decision.expected_value_after_costs == Decimal("0.030000")
    assert decision.reason_codes == ("paper_trade_ready",)


def test_gate_validates_exact_types_quantization_and_hard_safety_flags():
    with pytest.raises(ValueError, match="config must be"):
        evaluate_strategy_recommendation_paper_trade_readiness(  # type: ignore[arg-type]
            _candidate(),
            config="bad",
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(ValueError, match="candidate must be"):
        evaluate_strategy_recommendation_paper_trade_readiness(  # type: ignore[arg-type]
            "bad",
            config=_config(),
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(ValueError, match="evaluated_at"):
        _evaluate(_candidate(), evaluated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evaluated_at"):
        _evaluate(_candidate(), evaluated_at=_DatetimeSubclass(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="expected_value_before_costs"):
        _candidate(expected_value_before_costs=Decimal("0.0340001"))
    with pytest.raises(ValueError, match="estimated_cost_per_share"):
        _candidate(estimated_cost_per_share=_DecimalSubclass("0.004000"))
    with pytest.raises(ValueError, match="team_approval_count"):
        _candidate(team_approval_count=_IntSubclass(3))
    with pytest.raises(ValueError, match="required_manual_checks"):
        _config(required_manual_checks=("legal_review", "legal_review"))
    with pytest.raises(ValueError, match="paper_only"):
        _candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _candidate(readonly=False)
    with pytest.raises(ValueError, match="live_trading_enabled"):
        _candidate(live_trading_enabled=True)
    with pytest.raises(ValueError, match="network_access_allowed"):
        _candidate(network_access_allowed=True)
    with pytest.raises(ValueError, match="wallet_required"):
        _candidate(wallet_required=True)
    with pytest.raises(ValueError, match="orders_allowed"):
        _candidate(orders_allowed=True)
    with pytest.raises(ValueError, match="db_writes_allowed"):
        _candidate(db_writes_allowed=True)


def test_decision_constructor_rejects_inconsistent_outputs():
    valid = _evaluate(_candidate())

    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid, reason_codes=())
    with pytest.raises(ValueError, match="missing_manual_checks"):
        replace(valid, readiness_status="ready", missing_manual_checks=("legal_review",))
    with pytest.raises(ValueError, match="readiness_status"):
        replace(valid, readiness_status="skip")
    with pytest.raises(ValueError, match="expected_value_after_costs"):
        replace(valid, expected_value_after_costs=Decimal("0.0300001"))
