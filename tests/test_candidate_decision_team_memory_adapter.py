from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.candidate_decision_team_memory_adapter import (
    CandidateDecisionTeamMemoryAdapterConfig,
    CandidateDecisionTeamMemoryAdapterInput,
    build_candidate_decision_team_memory_adapter,
    candidate_decision_team_memory_adapter_payload,
)
from polymarket_alpha_lab.candidate_decision_score import CandidateDecisionScoreInput


def _input(**overrides: object) -> CandidateDecisionTeamMemoryAdapterInput:
    values: dict[str, object] = {
        "primary_team_id": "politics",
        "secondary_team_ids": ("crypto_btc",),
        "memory_use_policy": "allow",
        "calibration_score": Decimal("0.900000"),
        "settled_sample_count": Decimal("40"),
        "source_memory_score": Decimal("0.800000"),
        "capacity_score": Decimal("0.700000"),
        "source_report_refs": ("team-memory-readiness-digest:politics:2026-07-07",),
        "source_reason_codes": ("team_memory_readiness_digest_passed",),
    }
    values.update(overrides)
    return CandidateDecisionTeamMemoryAdapterInput(**values)


def _contains_float(value: object) -> bool:
    if type(value) is float:
        return True
    if type(value) is dict:
        return any(_contains_float(item) for item in value.values())
    if type(value) is list:
        return any(_contains_float(item) for item in value)
    return False


def test_allow_output_is_candidate_decision_score_compatible() -> None:
    result = build_candidate_decision_team_memory_adapter(_input())

    assert result.team_memory_policy == "allow"
    assert result.team_memory_score == Decimal("0.800000")
    assert result.reason_codes == (
        "team_memory_adapter_allow",
        "team_memory_policy_allow",
        "settled_sample_count_sufficient",
        "calibration_score_healthy",
        "source_memory_score_healthy",
        "capacity_score_healthy",
    )

    score_input = CandidateDecisionScoreInput(
        candidate_id="candidate-1",
        market_id="market-1",
        normalized_market_question="Will candidate 1 win?",
        primary_team_id=result.primary_team_id,
        secondary_team_ids=result.secondary_team_ids,
        selected_side="yes",
        forecast_probability=Decimal("0.550000"),
        executable_price=Decimal("0.500000"),
        gross_edge=Decimal("0.050000"),
        estimated_cost_drag=Decimal("0.005000"),
        cost_score=Decimal("0.900000"),
        liquidity_score=Decimal("0.900000"),
        evidence_score=Decimal("0.900000"),
        resolution_score=Decimal("0.900000"),
        team_memory_score=result.team_memory_score,
        team_memory_policy=result.team_memory_policy,
        source_report_refs=result.source_report_refs,
        adapter_reason_codes=result.reason_codes,
    )
    assert score_input.team_memory_score == Decimal("0.800000")
    assert score_input.team_memory_policy == "allow"


def test_source_throttle_policy_throttles_and_caps_score() -> None:
    result = build_candidate_decision_team_memory_adapter(
        _input(memory_use_policy="throttle"),
    )

    assert result.team_memory_policy == "throttle"
    assert result.team_memory_score == Decimal("0.600000")
    assert "team_memory_policy_throttle" in result.reason_codes
    assert "team_memory_adapter_throttle" in result.reason_codes


def test_source_block_policy_blocks_and_zeroes_score() -> None:
    result = build_candidate_decision_team_memory_adapter(
        _input(memory_use_policy="block"),
    )

    assert result.team_memory_policy == "block"
    assert result.team_memory_score == Decimal("0.000000")
    assert result.reason_codes[0] == "team_memory_adapter_block"
    assert "team_memory_policy_block" in result.reason_codes


def test_rejects_noncanonical_primary_team() -> None:
    with pytest.raises(ValueError, match="primary_team_id must be a known team"):
        _input(primary_team_id="politics_live")


def test_rejects_duplicate_secondary_teams() -> None:
    with pytest.raises(ValueError, match="secondary_team_ids must be unique"):
        _input(secondary_team_ids=("crypto_btc", "crypto_btc"))


def test_sparse_settled_samples_throttle_even_when_scores_are_healthy() -> None:
    result = build_candidate_decision_team_memory_adapter(
        _input(settled_sample_count=Decimal("3")),
    )

    assert result.team_memory_policy == "throttle"
    assert result.team_memory_score == Decimal("0.600000")
    assert "settled_sample_count_sparse" in result.reason_codes


def test_poor_calibration_hard_blocks_even_when_source_policy_allows() -> None:
    result = build_candidate_decision_team_memory_adapter(
        _input(calibration_score=Decimal("0.200000")),
    )

    assert result.team_memory_policy == "block"
    assert result.team_memory_score == Decimal("0.000000")
    assert "calibration_score_blocking" in result.reason_codes


def test_hard_paper_report_readonly_flags_are_required() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        CandidateDecisionTeamMemoryAdapterConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        _input(readonly=False)


def test_dataclasses_are_frozen_and_require_decimal_values() -> None:
    result = build_candidate_decision_team_memory_adapter(_input())

    with pytest.raises(FrozenInstanceError):
        result.team_memory_policy = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        _input(calibration_score=0.9)


def test_payload_is_json_safe_and_has_no_float_values() -> None:
    result = build_candidate_decision_team_memory_adapter(_input())

    payload = candidate_decision_team_memory_adapter_payload(result)

    assert payload["team_memory_score"] == "0.800000"
    assert payload["source_report_refs"] == [
        "team-memory-readiness-digest:politics:2026-07-07",
    ]
    assert not _contains_float(payload)
    json.dumps(payload, sort_keys=True)


def test_rejects_unsafe_payload_surface_fields() -> None:
    result = build_candidate_decision_team_memory_adapter(_input())
    payload = candidate_decision_team_memory_adapter_payload(result)
    payload["wallet_balance"] = "0"

    with pytest.raises(ValueError, match="unsafe live surface field"):
        candidate_decision_team_memory_adapter_payload(payload)


def test_forbidden_surface_scan() -> None:
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_team_memory_adapter.py",
    ).read_text()

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "click",
        "argparse",
        "open(",
        ".write(",
        "wallet",
        "private_key",
        "place_order",
        "create_order",
        "cancel_order",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
