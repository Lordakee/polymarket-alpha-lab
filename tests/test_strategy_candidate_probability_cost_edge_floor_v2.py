from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_candidate_probability_cost_edge_floor_v2 import (
    StrategyCandidateProbabilityCostEdgeFloorV2Candidate,
    StrategyCandidateProbabilityCostEdgeFloorV2Config,
    StrategyCandidateProbabilityCostEdgeFloorV2Score,
    build_strategy_candidate_probability_cost_edge_floor_v2_report,
    score_strategy_candidate_probability_cost_edge_floor_v2,
    strategy_candidate_probability_cost_edge_floor_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=5)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateProbabilityCostEdgeFloorV2Config:
    values = {
        "config_version": "phase1-probability-cost-edge-floor-v2",
        "min_cost_adjusted_probability_edge": d("0.010000"),
    }
    values.update(overrides)
    return StrategyCandidateProbabilityCostEdgeFloorV2Config(**values)


def candidate(
    candidate_id: str = "candidate-alpha",
    **overrides: object,
) -> StrategyCandidateProbabilityCostEdgeFloorV2Candidate:
    values = {
        "candidate_id": candidate_id,
        "market_slug": "public-market-alpha",
        "side": "yes",
        "observed_at": OBSERVED_AT,
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.560000"),
        "fee_probability_floor": d("0.006000"),
        "spread_probability_floor": d("0.010000"),
        "settlement_probability_floor": d("0.004000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyCandidateProbabilityCostEdgeFloorV2Candidate(**values)


def test_score_accepts_only_when_edge_clears_all_friction_floors() -> None:
    accepted = score_strategy_candidate_probability_cost_edge_floor_v2(
        candidate(),
        config=config(),
        generated_at=GENERATED_AT,
    )
    rejected = score_strategy_candidate_probability_cost_edge_floor_v2(
        candidate(
            "candidate-beta",
            forecast_probability=d("0.590000"),
            fee_probability_floor=d("0.012000"),
            spread_probability_floor=d("0.010000"),
            settlement_probability_floor=d("0.009000"),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert accepted.decision == "accepted"
    assert accepted.gross_probability_edge == d("0.060000")
    assert accepted.total_friction_probability_floor == d("0.020000")
    assert accepted.required_probability_edge == d("0.030000")
    assert accepted.cost_adjusted_probability_edge == d("0.040000")
    assert accepted.edge_floor_surplus == d("0.030000")
    assert "probability_edge_floor_cleared" in accepted.reason_codes

    assert rejected.decision == "rejected"
    assert rejected.gross_probability_edge == d("0.030000")
    assert rejected.total_friction_probability_floor == d("0.031000")
    assert rejected.cost_adjusted_probability_edge == d("-0.001000")
    assert rejected.edge_floor_surplus == d("-0.011000")
    assert "settlement_floor_not_cleared" in rejected.reason_codes
    assert "minimum_edge_buffer_not_cleared" in rejected.reason_codes


def test_report_sorts_scores_and_serializes_deterministically() -> None:
    report = build_strategy_candidate_probability_cost_edge_floor_v2_report(
        (
            candidate(
                "candidate-rejected",
                forecast_probability=d("0.590000"),
                fee_probability_floor=d("0.012000"),
                spread_probability_floor=d("0.010000"),
                settlement_probability_floor=d("0.009000"),
            ),
            candidate("candidate-accepted"),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )
    payload = strategy_candidate_probability_cost_edge_floor_v2_payload(report)
    payload_again = strategy_candidate_probability_cost_edge_floor_v2_payload(report)

    assert report.candidate_count == 2
    assert report.accepted_count == 1
    assert report.rejected_count == 1
    assert tuple(score.candidate_id for score in report.scores) == (
        "candidate-accepted",
        "candidate-rejected",
    )
    assert len(report.derived_validation_digest) == 64
    assert payload == payload_again
    assert payload["scores"][0]["forecast_probability"] == "0.620000"
    assert payload["scores"][0]["decision"] == "accepted"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_digest_detects_score_tampering() -> None:
    score = score_strategy_candidate_probability_cost_edge_floor_v2(
        candidate(),
        config=config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        StrategyCandidateProbabilityCostEdgeFloorV2Score(
            candidate_id=score.candidate_id,
            market_slug=score.market_slug,
            side=score.side,
            observed_at=score.observed_at,
            forecast_probability=score.forecast_probability,
            market_probability=score.market_probability,
            gross_probability_edge=score.gross_probability_edge,
            fee_probability_floor=score.fee_probability_floor,
            spread_probability_floor=score.spread_probability_floor,
            settlement_probability_floor=score.settlement_probability_floor,
            total_friction_probability_floor=score.total_friction_probability_floor,
            min_cost_adjusted_probability_edge=score.min_cost_adjusted_probability_edge,
            required_probability_edge=score.required_probability_edge,
            cost_adjusted_probability_edge=score.cost_adjusted_probability_edge,
            edge_floor_surplus=score.edge_floor_surplus + d("0.000001"),
            age_seconds=score.age_seconds,
            decision=score.decision,
            reason_codes=score.reason_codes,
            derived_validation_digest=score.derived_validation_digest,
        )


def test_requires_decimal_inputs_and_readonly_safety_flags() -> None:
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        candidate(forecast_probability=0.62)

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)


def test_observed_at_must_not_be_after_generated_at() -> None:
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        score_strategy_candidate_probability_cost_edge_floor_v2(
            candidate(observed_at=GENERATED_AT + timedelta(seconds=1)),
            config=config(),
            generated_at=GENERATED_AT,
        )
