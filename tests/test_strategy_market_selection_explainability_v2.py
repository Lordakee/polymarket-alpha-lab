from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.strategy_market_selection_explainability_v2 as explainability_v2_module
from polymarket_alpha_lab.strategy_market_selection_explainability_v2 import (
    MarketSelectionDecisionInputV2,
    MarketSelectionExplainabilityV2Config,
    MarketSelectionExplainabilityV2Report,
    MarketSelectionExplanationV2Row,
    build_market_selection_explainability_v2_report,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketSelectionExplainabilityV2Config:
    values = {
        "config_version": "market-selection-explainability-v2",
        "low_confidence_threshold": d("0.550000"),
        "high_resolution_risk_threshold": d("0.350000"),
        "high_spread_threshold": d("0.080000"),
    }
    values.update(overrides)
    return MarketSelectionExplainabilityV2Config(**values)


def decision_input(**overrides: object) -> MarketSelectionDecisionInputV2:
    values = {
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "screening_status": "passed",
        "decision": "selected",
        "selected_side": "yes",
        "recommendation_score": d("0.820000"),
        "readiness_score": d("0.740000"),
        "selection_score": d("0.790000"),
        "expected_edge_per_share": d("0.080000"),
        "total_cost_per_share": d("0.020000"),
        "liquidity_score": d("0.660000"),
        "confidence": d("0.710000"),
        "spread": d("0.030000"),
        "resolution_risk": d("0.180000"),
        "screening_reason_codes": ("policy_passed", "liquid_market"),
        "decision_reason_codes": ("selected_by_policy", "positive_edge"),
        "evidence_gap_codes": (),
    }
    values.update(overrides)
    return MarketSelectionDecisionInputV2(**values)


def report(
    rows: tuple[MarketSelectionDecisionInputV2, ...],
    *,
    cfg: MarketSelectionExplainabilityV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketSelectionExplainabilityV2Report:
    return build_market_selection_explainability_v2_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_v2_summarizes_selected_market_into_auditable_sections() -> None:
    result = report((decision_input(),))

    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "market-selection-explainability-v2"
    assert result.row_count == 1
    assert result.selected_count == 1
    assert result.human_review_required_count == 0
    assert result.reason_codes == ("market_selection_explainability_v2_ready",)

    row = result.explanation_rows[0]
    assert row.market_slug == "fed-cut-june-2026"
    assert row.decision == "selected"
    assert row.selected_side == "yes"
    assert row.explanation_bullets == (
        "Market fed-cut-june-2026 screened passed and selected yes.",
        "Screening inputs: recommendation 0.820000, readiness 0.740000, selection 0.790000.",
        "Decision economics: edge 0.080000 per share after 0.020000 total cost.",
        "Risk inputs: confidence 0.710000, liquidity 0.660000, spread 0.030000, resolution risk 0.180000.",
        "Screening reasons: policy_passed, liquid_market.",
        "Decision reasons: selected_by_policy, positive_edge.",
    )
    assert row.positive_drivers == (
        "Selected yes by decision policy.",
        "Positive expected edge per share: 0.080000.",
        "Recommendation score 0.820000 supports prioritization.",
        "Readiness score 0.740000 supports operational readiness.",
        "Liquidity score 0.660000 supports execution quality.",
        "Confidence 0.710000 is at or above the review threshold 0.550000.",
    )
    assert row.negative_drivers == (
        "Total cost per share: 0.020000.",
        "Spread: 0.030000.",
        "Resolution risk: 0.180000.",
    )
    assert row.missing_evidence == ()
    assert row.human_review_notes == ()
    assert row.reason_codes == (
        "policy_passed",
        "liquid_market",
        "selected_by_policy",
        "positive_edge",
    )


def test_v2_flags_missing_evidence_and_review_notes_from_decision_inputs() -> None:
    result = report(
        (
            decision_input(
                market_slug="rainfall-threshold-2026",
                question="Will rainfall exceed the threshold in 2026?",
                screening_status="watch",
                decision="not_selected",
                selected_side="none",
                recommendation_score=d("0.420000"),
                readiness_score=d("0.310000"),
                selection_score=d("0.500000"),
                expected_edge_per_share=None,
                total_cost_per_share=None,
                liquidity_score=None,
                confidence=None,
                spread=None,
                resolution_risk=d("0.620000"),
                screening_reason_codes=("source_action_watch",),
                decision_reason_codes=("insufficient_edge",),
                evidence_gap_codes=("missing_resolution_source", "stale_forecast"),
            ),
        ),
    )

    assert result.selected_count == 0
    assert result.human_review_required_count == 1

    row = result.explanation_rows[0]
    assert row.explanation_bullets == (
        "Market rainfall-threshold-2026 screened watch and decision not_selected.",
        "Screening inputs: recommendation 0.420000, readiness 0.310000, selection 0.500000.",
        "Decision economics: edge unavailable and total cost unavailable.",
        "Risk inputs: confidence unavailable, liquidity unavailable, spread unavailable, resolution risk 0.620000.",
        "Screening reasons: source_action_watch.",
        "Decision reasons: insufficient_edge.",
        "Evidence gaps: missing_resolution_source, stale_forecast, expected_edge_per_share_unavailable, liquidity_score_unavailable, confidence_unavailable, spread_unavailable.",
    )
    assert row.positive_drivers == ()
    assert row.negative_drivers == (
        "Decision not_selected prevented selection.",
        "No selected side is available.",
        "Expected edge per share is unavailable.",
        "Liquidity score is unavailable.",
        "Confidence is unavailable.",
        "Spread is unavailable.",
        "Resolution risk 0.620000 is above the review threshold 0.350000.",
    )
    assert row.missing_evidence == (
        "missing_resolution_source",
        "stale_forecast",
        "expected_edge_per_share_unavailable",
        "liquidity_score_unavailable",
        "confidence_unavailable",
        "spread_unavailable",
    )
    assert row.human_review_notes == (
        "Review evidence gaps before promotion: missing_resolution_source, stale_forecast, expected_edge_per_share_unavailable, liquidity_score_unavailable, confidence_unavailable, spread_unavailable.",
        "Review elevated resolution risk before selection: 0.620000.",
        "Review non-selected decision before any manual override: not_selected.",
    )


def test_v2_validates_types_consistency_utc_and_hard_flags() -> None:
    shifted_result = report(
        (decision_input(),),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted_result.generated_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        shifted_result.explanation_rows[0].decision = "skipped"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" ")
    with pytest.raises(ValueError, match="recommendation_score"):
        decision_input(recommendation_score=d("1.000001"))
    with pytest.raises(ValueError, match="decision"):
        decision_input(decision="trade_now")
    with pytest.raises(ValueError, match="selected rows"):
        decision_input(selected_side="none")
    with pytest.raises(ValueError, match="decision_input must be paper_only"):
        decision_input(paper_only=False)
    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        report((decision_input(),), generated_at="bad")  # type: ignore[arg-type]

    valid_row = MarketSelectionExplanationV2Row(
        market_slug="fed-cut-june-2026",
        question="Will the Fed cut rates by June 2026?",
        screening_status="passed",
        decision="selected",
        selected_side="yes",
        explanation_bullets=("Audit bullet.",),
        positive_drivers=("Positive driver.",),
        negative_drivers=(),
        missing_evidence=(),
        human_review_notes=(),
        reason_codes=("selected_by_policy",),
    )
    MarketSelectionExplainabilityV2Report(
        generated_at=GENERATED_AT,
        config_version="market-selection-explainability-v2",
        row_count=1,
        selected_count=1,
        human_review_required_count=0,
        explanation_rows=(valid_row,),
        reason_codes=("market_selection_explainability_v2_ready",),
    )
    with pytest.raises(ValueError, match="selected_count"):
        MarketSelectionExplainabilityV2Report(
            generated_at=GENERATED_AT,
            config_version="market-selection-explainability-v2",
            row_count=1,
            selected_count=0,
            human_review_required_count=0,
            explanation_rows=(valid_row,),
            reason_codes=("market_selection_explainability_v2_ready",),
        )
    with pytest.raises(ValueError, match="human_review_required_count"):
        MarketSelectionExplainabilityV2Report(
            generated_at=GENERATED_AT,
            config_version="market-selection-explainability-v2",
            row_count=1,
            selected_count=1,
            human_review_required_count=1,
            explanation_rows=(valid_row,),
            reason_codes=("market_selection_explainability_v2_ready",),
        )
    with pytest.raises(ValueError, match="explanation_rows"):
        replace(
            shifted_result,
            explanation_rows=(object(),),  # type: ignore[arg-type]
        )


def test_v2_stays_pure_and_excludes_network_db_and_trading_actions() -> None:
    source = Path(explainability_v2_module.__file__).read_text()
    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "websocket",
        "create_order",
        "submit_order",
        "execute_trade",
        "trade_client",
    )

    assert not any(term in source for term in forbidden_terms)
