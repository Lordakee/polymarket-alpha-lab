from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.strategy_probability_event_value_ranker_v2 as module


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    candidate_id: str,
    *,
    category: str = "macro_rates",
    implied_probability: Decimal = d("0.420000"),
    model_probability: Decimal = d("0.520000"),
    information_quality_score: Decimal = d("0.900000"),
    liquidity_score: Decimal = d("0.700000"),
    specialist_consensus_score: Decimal = d("0.800000"),
    resolution_risk_score: Decimal = d("0.100000"),
    category_exposure_score: Decimal = d("0.200000"),
) -> module.StrategyProbabilityEventValueRankerV2Candidate:
    return module.StrategyProbabilityEventValueRankerV2Candidate(
        candidate_id=candidate_id,
        event_id=f"event_{candidate_id}",
        market_slug=f"market_{candidate_id}",
        outcome_name=f"outcome_{candidate_id}",
        category=category,
        implied_probability=implied_probability,
        model_probability=model_probability,
        information_quality_score=information_quality_score,
        liquidity_score=liquidity_score,
        specialist_consensus_score=specialist_consensus_score,
        resolution_risk_score=resolution_risk_score,
        category_exposure_score=category_exposure_score,
        reason_codes=("source_quality_confirmed",),
    )


def report() -> module.StrategyProbabilityEventValueRankerV2Report:
    return module.build_strategy_probability_event_value_ranker_v2_report(
        (
            candidate("candidate_gamma", implied_probability=d("0.550000"), model_probability=d("0.530000"), information_quality_score=d("0.400000"), liquidity_score=d("0.400000"), specialist_consensus_score=d("0.400000"), resolution_risk_score=d("0.500000"), category_exposure_score=d("0.500000")),
            candidate("candidate_beta", implied_probability=d("0.450000"), model_probability=d("0.510000"), information_quality_score=d("0.800000"), liquidity_score=d("0.900000"), specialist_consensus_score=d("0.700000"), resolution_risk_score=d("0.200000"), category_exposure_score=d("0.700000")),
            candidate("candidate_alpha"),
        ),
        config=module.StrategyProbabilityEventValueRankerV2Config(
            min_recommendation_score=d("0.180000"),
            min_edge=d("0.030000"),
            min_information_quality_score=d("0.600000"),
            min_liquidity_score=d("0.500000"),
            max_resolution_risk_score=d("0.300000"),
            max_category_exposure_score=d("0.400000"),
        ),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),
    )


def test_ranker_sorts_candidates_and_assigns_readonly_postures() -> None:
    ranked = report()

    assert tuple(row.candidate_id for row in ranked.rows) == (
        "candidate_alpha",
        "candidate_beta",
        "candidate_gamma",
    )
    assert tuple(row.recommendation_posture for row in ranked.rows) == (
        "recommend",
        "watch",
        "reject",
    )
    assert ranked.rows[0].rank == d("1.000000")
    assert ranked.rows[0].probability_edge == d("0.100000")
    assert ranked.rows[0].composite_value_score == d("0.405000")
    assert "category_exposure_high" in ranked.rows[1].reason_codes
    assert "edge_not_positive" in ranked.rows[2].reason_codes
    assert ranked.paper_only is True
    assert ranked.report_only is True
    assert ranked.readonly is True


def test_payload_serializes_decimal_values_as_strings_and_keeps_hard_flags() -> None:
    payload = module.strategy_probability_event_value_ranker_v2_payload(report())

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["recommendation_count"] == "3.000000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["rows"][0]["probability_edge"] == "0.100000"
    assert payload["rows"][0]["composite_value_score"] == "0.405000"
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert not any(type(value) is Decimal for value in walk_payload_values(payload))
    assert not any(type(value) is float for value in walk_payload_values(payload))
    assert not any(type(value) is int for value in walk_payload_values(payload))


def test_frozen_dataclasses_and_derived_digest_reject_tampering() -> None:
    ranked = report()
    with pytest.raises(FrozenInstanceError):
        ranked.rows[0].candidate_id = "candidate_other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(ranked.rows[0], derived_validation_digest="0" * 64)

    payload = module.strategy_probability_event_value_ranker_v2_payload(ranked)
    tampered_payload = dict(payload)
    tampered_rows = [dict(row) for row in payload["rows"]]
    tampered_rows[0]["composite_value_score"] = "0.000001"
    tampered_payload["rows"] = tampered_rows
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_probability_event_value_ranker_v2_public_payload(tampered_payload)

    tampered_report = report()
    object.__setattr__(tampered_report.rows[0], "composite_value_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_probability_event_value_ranker_v2_payload(tampered_report)


def test_rejects_unsafe_public_keys_values_and_non_decimal_inputs() -> None:
    with pytest.raises(ValueError, match="must be a Decimal"):
        module.StrategyProbabilityEventValueRankerV2Candidate(
            candidate_id="candidate_bad_numeric",
            event_id="event_bad_numeric",
            market_slug="market_bad_numeric",
            outcome_name="outcome_bad_numeric",
            category="macro_rates",
            implied_probability=d("0.420000"),
            model_probability="0.520000",  # type: ignore[arg-type]
            information_quality_score=d("0.900000"),
            liquidity_score=d("0.700000"),
            specialist_consensus_score=d("0.800000"),
            resolution_risk_score=d("0.100000"),
            category_exposure_score=d("0.200000"),
            reason_codes=("source_quality_confirmed",),
        )

    payload = module.strategy_probability_event_value_ranker_v2_payload(report())
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
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{unsafe_term}_field"] = "safe_value"
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_strategy_probability_event_value_ranker_v2_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = dict(payload)
        unsafe_rows = [dict(row) for row in payload["rows"]]
        unsafe_rows[0]["candidate_id"] = f"candidate_{unsafe_term}"
        unsafe_value_payload["rows"] = unsafe_rows
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_strategy_probability_event_value_ranker_v2_public_payload(
                unsafe_value_payload,
            )


def walk_payload_values(value: Any) -> tuple[object, ...]:
    if type(value) is dict:
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if type(value) is list:
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)
