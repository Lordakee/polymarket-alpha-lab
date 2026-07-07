from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_candidate_attention_queue_v2 import (
    StrategyCandidateAttentionQueueV2Candidate,
    StrategyCandidateAttentionQueueV2Config,
    StrategyCandidateAttentionQueueV2Report,
    build_strategy_candidate_attention_queue_v2_report,
    strategy_candidate_attention_queue_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CONFIG = StrategyCandidateAttentionQueueV2Config(
    config_version="strategy-candidate-attention-queue-v2-phase-1",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    index: int,
    *,
    candidate_id: str | None = None,
    source_verified_edge: Decimal = d("0.040000"),
    market_probability_movement: Decimal = d("0.020000"),
    research_readiness: Decimal = d("0.700000"),
    uncertainty_band_width: Decimal = d("0.200000"),
    liquidity_exit_risk: Decimal = d("0.100000"),
    resolution_ambiguity: Decimal = d("0.100000"),
    portfolio_impact: Decimal = d("0.200000"),
    specialist_confidence: Decimal = d("0.700000"),
    source_reference: str | None = None,
    observed_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyCandidateAttentionQueueV2Candidate:
    return StrategyCandidateAttentionQueueV2Candidate(
        candidate_id=candidate_id or f"candidate-{index}",
        market_slug=f"market-{index}",
        question=f"Will candidate {index} resolve yes?",
        outcome_name="YES",
        side="yes",
        source_reference=source_reference or f"source-ref-{index}",
        source_verified_edge=source_verified_edge,
        market_probability_movement=market_probability_movement,
        research_readiness=research_readiness,
        uncertainty_band_width=uncertainty_band_width,
        liquidity_exit_risk=liquidity_exit_risk,
        resolution_ambiguity=resolution_ambiguity,
        portfolio_impact=portfolio_impact,
        specialist_confidence=specialist_confidence,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=index),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_attention_queue_ranks_candidates_using_all_review_attention_factors():
    report = build_strategy_candidate_attention_queue_v2_report(
        (
            candidate(1),
            candidate(
                2,
                source_verified_edge=d("0.060000"),
                market_probability_movement=d("0.050000"),
                research_readiness=d("0.800000"),
                uncertainty_band_width=d("0.300000"),
                liquidity_exit_risk=d("0.200000"),
                resolution_ambiguity=d("0.150000"),
                portfolio_impact=d("0.400000"),
                specialist_confidence=d("0.900000"),
            ),
            candidate(
                3,
                source_verified_edge=d("0.005000"),
                market_probability_movement=d("0.010000"),
                research_readiness=d("0.300000"),
                uncertainty_band_width=d("0.100000"),
                liquidity_exit_risk=d("0.050000"),
                resolution_ambiguity=d("0.050000"),
                portfolio_impact=d("0.100000"),
                specialist_confidence=d("0.500000"),
            ),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, StrategyCandidateAttentionQueueV2Report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "ready"
    assert report.candidate_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.ready_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.top_candidate_id == "candidate-2"
    assert report.reason_codes == ("candidate_attention_queue_v2_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [row.candidate_id for row in report.rows] == [
        "candidate-2",
        "candidate-1",
        "candidate-3",
    ]
    assert [row.attention_rank for row in report.rows] == [
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    ]

    top = report.rows[0]
    assert top.attention_status == "ready"
    assert top.attention_score == d("1.197500")
    assert top.primary_reason_code == "attention_review_ready"
    assert top.reason_codes == (
        "source_verified_edge_high",
        "market_probability_movement_high",
        "research_readiness_high",
        "uncertainty_band_wide",
        "liquidity_exit_risk_low",
        "resolution_ambiguity_low",
        "portfolio_impact_high",
        "specialist_confidence_high",
    )

    payload = strategy_candidate_attention_queue_v2_payload(report)

    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["source_verified_edge"] == "0.060000"
    assert payload["rows"][0]["attention_score"] == "1.197500"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest


def test_attention_queue_empty_inputs_are_report_only_and_digest_backed():
    report = build_strategy_candidate_attention_queue_v2_report(
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "empty"
    assert report.candidate_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.ready_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.top_candidate_id is None
    assert report.rows == ()
    assert report.reason_codes == ("no_candidates_for_attention_review",)

    payload = strategy_candidate_attention_queue_v2_payload(report)
    assert payload["rows"] == []
    assert payload["derived_validation_digest"] == report.derived_validation_digest


def test_attention_queue_validates_decimals_datetimes_flags_frozen_and_duplicates():
    with pytest.raises(ValueError, match="paper_only"):
        candidate(1, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(1, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        candidate(1, readonly=False)

    with pytest.raises(ValueError, match="Decimal"):
        candidate(1, source_verified_edge="0.010000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability"):
        candidate(1, market_probability_movement=d("1.100000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(1, observed_at=datetime(2026, 7, 6, 12, 0))

    digest_candidate = candidate(1)
    with pytest.raises(FrozenInstanceError):
        digest_candidate.market_slug = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="duplicate candidate_id"):
        build_strategy_candidate_attention_queue_v2_report(
            (candidate(1), candidate(2, candidate_id="candidate-1")),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_strategy_candidate_attention_queue_v2_report(
            (candidate(1),),
            config=CONFIG,
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    report = build_strategy_candidate_attention_queue_v2_report(
        (candidate(1),),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, candidate_count=d("2.000000"))


def test_attention_queue_rejects_tampered_or_unsafe_public_payloads():
    report = build_strategy_candidate_attention_queue_v2_report(
        (candidate(1),),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    payload = strategy_candidate_attention_queue_v2_payload(report)

    tampered = deepcopy(payload)
    tampered["rows"][0]["attention_score"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_attention_queue_v2_payload(tampered)

    downgraded = deepcopy(payload)
    downgraded["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        strategy_candidate_attention_queue_v2_payload(downgraded)

    unsafe_key = deepcopy(payload)
    unsafe_key["live_surface"] = "ready"
    with pytest.raises(ValueError, match="unsafe"):
        strategy_candidate_attention_queue_v2_payload(unsafe_key)

    unsafe_value = deepcopy(payload)
    unsafe_value["public_note"] = "use wallet review"
    with pytest.raises(ValueError, match="unsafe"):
        strategy_candidate_attention_queue_v2_payload(unsafe_value)

    with pytest.raises(ValueError, match="unsafe"):
        candidate(1, source_reference="public wallet source")
