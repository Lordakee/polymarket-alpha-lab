from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.strategy_candidate_research_consensus_gap_penalty_v2 as api
from polymarket_alpha_lab.strategy_candidate_research_consensus_gap_penalty_v2 import (
    StrategyCandidateResearchConsensusGapPenaltyConfig,
    StrategyCandidateResearchConsensusGapPenaltyReport,
    StrategyCandidateResearchConsensusObservation,
    StrategyCandidateResearchConsensusPublicPayloadItem,
    build_strategy_candidate_research_consensus_gap_penalty_v2_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    candidate_id: str = "candidate_a",
    observation_id: str = "observation_a",
    source_id: str = "source_a",
    candidate_probability: Decimal = Decimal("0.700000"),
    research_probability: Decimal = Decimal("0.700000"),
    confidence_score: Decimal = Decimal("0.700000"),
) -> StrategyCandidateResearchConsensusObservation:
    return StrategyCandidateResearchConsensusObservation(
        candidate_id=candidate_id,
        observation_id=observation_id,
        source_id=source_id,
        observed_at=NOW,
        candidate_probability=candidate_probability,
        research_probability=research_probability,
        confidence_score=confidence_score,
    )


def _report(
    observations: tuple[StrategyCandidateResearchConsensusObservation, ...],
    *,
    config: StrategyCandidateResearchConsensusGapPenaltyConfig | None = None,
    public_payload: tuple[StrategyCandidateResearchConsensusPublicPayloadItem, ...] = (),
) -> StrategyCandidateResearchConsensusGapPenaltyReport:
    return build_strategy_candidate_research_consensus_gap_penalty_v2_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_research_consensus_gap_penalties_reduce_consensus_score() -> None:
    config = StrategyCandidateResearchConsensusGapPenaltyConfig(
        consensus_gap_penalty_multiplier=Decimal("1.000000"),
    )

    report = _report(
        (
            _observation(
                observation_id="observation_a",
                source_id="source_a",
                candidate_probability=Decimal("0.800000"),
                research_probability=Decimal("0.500000"),
                confidence_score=Decimal("0.700000"),
            ),
            _observation(
                observation_id="observation_b",
                source_id="source_b",
                candidate_probability=Decimal("0.800000"),
                research_probability=Decimal("0.500000"),
                confidence_score=Decimal("0.700000"),
            ),
        ),
        config=config,
    )

    row = report.rows[0]
    assert report.penalty_status == "watch"
    assert row.consensus_gap == Decimal("0.300000")
    assert row.consensus_gap_penalty == Decimal("0.300000")
    assert row.weak_quorum_penalty == Decimal("0.000000")
    assert row.independent_source_boost == Decimal("0.050000")
    assert row.consensus_score == Decimal("0.450000")
    assert row.penalty_status == "watch"
    assert "research_consensus_gap_penalty" in row.reason_codes
    assert "consensus_score_watch" in row.reason_codes


def test_weak_quorum_penalty_applies_when_observations_are_sparse() -> None:
    config = StrategyCandidateResearchConsensusGapPenaltyConfig(
        min_observation_count=Decimal("3.000000"),
        min_block_score=Decimal("0.250000"),
        weak_quorum_penalty_per_missing_observation=Decimal("0.200000"),
    )

    report = _report(
        (
            _observation(
                candidate_probability=Decimal("0.700000"),
                research_probability=Decimal("0.700000"),
                confidence_score=Decimal("0.700000"),
            ),
        ),
        config=config,
    )

    row = report.rows[0]
    assert report.penalty_status == "watch"
    assert row.observation_count == Decimal("1.000000")
    assert row.weak_quorum_penalty == Decimal("0.400000")
    assert row.consensus_score == Decimal("0.300000")
    assert row.penalty_status == "watch"
    assert "weak_quorum_penalty" in row.reason_codes
    assert "consensus_score_watch" in row.reason_codes


def test_independent_source_boosts_raise_consensus_score() -> None:
    one_source = _report(
        (
            _observation(
                observation_id="observation_a",
                source_id="source_a",
                candidate_probability=Decimal("0.600000"),
                research_probability=Decimal("0.600000"),
                confidence_score=Decimal("0.600000"),
            ),
            _observation(
                observation_id="observation_b",
                source_id="source_a",
                candidate_probability=Decimal("0.600000"),
                research_probability=Decimal("0.600000"),
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )
    three_sources = _report(
        (
            _observation(
                observation_id="observation_a",
                source_id="source_a",
                candidate_probability=Decimal("0.600000"),
                research_probability=Decimal("0.600000"),
                confidence_score=Decimal("0.600000"),
            ),
            _observation(
                observation_id="observation_b",
                source_id="source_b",
                candidate_probability=Decimal("0.600000"),
                research_probability=Decimal("0.600000"),
                confidence_score=Decimal("0.600000"),
            ),
            _observation(
                observation_id="observation_c",
                source_id="source_c",
                candidate_probability=Decimal("0.600000"),
                research_probability=Decimal("0.600000"),
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )

    one_source_row = one_source.rows[0]
    boosted_row = three_sources.rows[0]
    assert one_source_row.independent_source_boost == Decimal("0.000000")
    assert boosted_row.independent_source_boost == Decimal("0.100000")
    assert boosted_row.consensus_score > one_source_row.consensus_score
    assert boosted_row.penalty_status == "pass"
    assert "independent_source_boost" in boosted_row.reason_codes


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    report = _report(
        (
            _observation(observation_id="observation_a", source_id="source_a"),
            _observation(observation_id="observation_b", source_id="source_b"),
        ),
        public_payload=(
            StrategyCandidateResearchConsensusPublicPayloadItem("safe_key", "safe value"),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_consensus_gap"] == "0.000000"
    assert payload["rows"][0]["observation_count"] == "2.000000"
    assert payload["rows"][0]["independent_source_boost"] == "0.050000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(
        (
            _observation(observation_id="observation_a", source_id="source_a"),
            _observation(observation_id="observation_b", source_id="source_b"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.penalty_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(StrategyCandidateResearchConsensusGapPenaltyConfig):
            pass


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        StrategyCandidateResearchConsensusGapPenaltyConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        StrategyCandidateResearchConsensusObservation(
            candidate_id="candidate_a",
            observation_id="observation_a",
            source_id="source_a",
            observed_at=NOW,
            candidate_probability=Decimal("0.700000"),
            research_probability=Decimal("0.700000"),
            confidence_score=Decimal("0.700000"),
            report_only=False,
        )

    report = _report(
        (
            _observation(observation_id="observation_a", source_id="source_a"),
            _observation(observation_id="observation_b", source_id="source_b"),
        ),
    )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(
        (
            _observation(observation_id="observation_a", source_id="source_a"),
            _observation(observation_id="observation_b", source_id="source_b"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                StrategyCandidateResearchConsensusPublicPayloadItem(
                    "safe_key",
                    "changed value",
                ),
            ),
        )


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for key in (
        "live_key",
        "auth_key",
        "wallet_key",
        "order_key",
        "network_key",
        "database_key",
        "persist_key",
        "signing_key",
        "mutation_key",
        "buy_key",
        "sell_key",
        "trade_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            StrategyCandidateResearchConsensusPublicPayloadItem(key, "safe value")

    for value in (
        "live item",
        "auth item",
        "wallet item",
        "order item",
        "network item",
        "database item",
        "persist item",
        "signing item",
        "mutation item",
        "buy item",
        "sell item",
        "trade item",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            StrategyCandidateResearchConsensusPublicPayloadItem("safe_key", value)

    with pytest.raises(ValueError, match="unsafe public"):
        _observation(source_id="buy_signal")


def test_no_unsafe_public_surfaces_are_exposed() -> None:
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
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        StrategyCandidateResearchConsensusGapPenaltyConfig,
        StrategyCandidateResearchConsensusObservation,
        StrategyCandidateResearchConsensusPublicPayloadItem,
        api.StrategyCandidateResearchConsensusGapPenaltyRow,
        StrategyCandidateResearchConsensusGapPenaltyReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
