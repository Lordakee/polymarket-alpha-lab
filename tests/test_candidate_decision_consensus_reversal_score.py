from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.candidate_decision_consensus_reversal_score import (
    CandidateDecisionConsensusReversalScoreConfig,
    CandidateDecisionConsensusReversalScoreInput,
    CandidateDecisionConsensusReversalScoreReport,
    build_candidate_decision_consensus_reversal_score_report,
    candidate_decision_consensus_reversal_score_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 14, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(**overrides: object) -> CandidateDecisionConsensusReversalScoreInput:
    values: dict[str, object] = {
        "redacted_candidate_ref": "redacted:alpha-001",
        "current_consensus_score": d("0.630000"),
        "prior_consensus_score": d("0.620000"),
        "reversal_velocity_score": d("0.100000"),
        "evidence_support_score": d("0.800000"),
        "source_quality_score": d("0.850000"),
        "volatility_score": d("0.150000"),
    }
    values.update(overrides)
    return CandidateDecisionConsensusReversalScoreInput(**values)


def _report(
    *,
    input_value: CandidateDecisionConsensusReversalScoreInput | None = None,
    config: CandidateDecisionConsensusReversalScoreConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CandidateDecisionConsensusReversalScoreReport:
    return build_candidate_decision_consensus_reversal_score_report(
        input_value or _input(),
        config=config or CandidateDecisionConsensusReversalScoreConfig(),
        generated_at=generated_at,
    )


def _contains_float(value: object) -> bool:
    if type(value) is float:
        return True
    if type(value) is dict:
        return any(_contains_float(item) for item in value.values())
    if type(value) is list:
        return any(_contains_float(item) for item in value)
    return False


def _assert_no_public_status_leak(value: object) -> None:
    forbidden_status_values = {"ready", "blocked", "matched", "supported"}
    if type(value) is str:
        assert value not in forbidden_status_values
    elif type(value) is dict:
        for item in value.values():
            _assert_no_public_status_leak(item)
    elif type(value) is list:
        for item in value:
            _assert_no_public_status_leak(item)


def test_stable_consensus_pass_report_is_json_safe() -> None:
    report = _report(
        generated_at=datetime(
            2026,
            7,
            7,
            10,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert type(report) is CandidateDecisionConsensusReversalScoreReport
    assert report.generated_at == GENERATED_AT
    assert report.consensus_delta == d("0.010000")
    assert report.absolute_consensus_delta == d("0.010000")
    assert report.evidence_gap_score == d("0.200000")
    assert report.source_quality_gap_score == d("0.150000")
    assert report.consensus_reversal_score == d("0.140000")
    assert report.reversal_status == "pass"
    assert report.hard_flag_codes == ()
    assert report.reason_codes == (
        "consensus_reversal_pass",
        "consensus_delta_pass",
        "reversal_velocity_pass",
        "evidence_support_pass",
        "source_quality_pass",
        "volatility_pass",
        "consensus_reversal_score_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = candidate_decision_consensus_reversal_score_payload(report)

    assert payload["generated_at"] == "2026-07-07T14:30:00+00:00"
    assert payload["redacted_candidate_ref"] == "redacted:alpha-001"
    assert payload["current_consensus_score"] == "0.630000"
    assert payload["prior_consensus_score"] == "0.620000"
    assert payload["reversal_status"] == "pass"
    assert payload["consensus_reversal_score"] == "0.140000"
    assert payload["reason_codes"] == list(report.reason_codes)
    assert "candidate_id" not in payload
    assert "market_id" not in payload
    assert "market_slug" not in payload
    assert "question" not in payload
    assert "source_report_refs" not in payload
    assert not _contains_float(payload)
    _assert_no_public_status_leak(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_sharp_low_evidence_reversal_blocks_for_manual_research_priority() -> None:
    report = _report(
        input_value=_input(
            current_consensus_score=d("0.310000"),
            prior_consensus_score=d("0.820000"),
            reversal_velocity_score=d("0.920000"),
            evidence_support_score=d("0.150000"),
            source_quality_score=d("0.200000"),
            volatility_score=d("0.800000"),
        ),
    )

    assert report.consensus_delta == d("-0.510000")
    assert report.absolute_consensus_delta == d("0.510000")
    assert report.evidence_gap_score == d("0.850000")
    assert report.source_quality_gap_score == d("0.800000")
    assert report.consensus_reversal_score == d("0.866500")
    assert report.reversal_status == "block"
    assert report.hard_flag_codes == (
        "reversal_velocity_block",
        "weak_evidence_reversal_block",
    )
    assert report.reason_codes == (
        "consensus_reversal_block",
        "consensus_delta_block",
        "reversal_velocity_block",
        "evidence_support_block",
        "source_quality_block",
        "volatility_block",
        "consensus_reversal_score_block",
    )


def test_moderate_reversal_with_thin_evidence_watches() -> None:
    report = _report(
        input_value=_input(
            current_consensus_score=d("0.450000"),
            prior_consensus_score=d("0.650000"),
            reversal_velocity_score=d("0.550000"),
            evidence_support_score=d("0.500000"),
            source_quality_score=d("0.600000"),
            volatility_score=d("0.400000"),
        ),
    )

    assert report.consensus_delta == d("-0.200000")
    assert report.absolute_consensus_delta == d("0.200000")
    assert report.consensus_reversal_score == d("0.492500")
    assert report.reversal_status == "watch"
    assert report.hard_flag_codes == ()
    assert report.reason_codes == (
        "consensus_reversal_watch",
        "consensus_delta_watch",
        "reversal_velocity_watch",
        "evidence_support_watch",
        "source_quality_pass",
        "volatility_pass",
        "consensus_reversal_score_watch",
    )


def test_exact_decimal_validation_and_frozen_dataclasses() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.reversal_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="current_consensus_score must be a Decimal"):
        _input(current_consensus_score=0.63)
    with pytest.raises(ValueError, match="reversal_velocity_weight must be a Decimal"):
        CandidateDecisionConsensusReversalScoreConfig(reversal_velocity_weight=0.45)
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        _report(generated_at=datetime.fromtimestamp(0, UTC).__class__(2026, 7, 7))
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadInput(CandidateDecisionConsensusReversalScoreInput):
            pass


def test_rejects_unsafe_public_payload_and_raw_candidate_refs() -> None:
    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        _input(redacted_candidate_ref="candidate-raw-1")
    with pytest.raises(ValueError, match="unsafe public value"):
        _input(redacted_candidate_ref="redacted:https://example.test/candidate")
    with pytest.raises(ValueError, match="unsafe public value"):
        _input(redacted_candidate_ref="redacted:secret-token-alpha")

    payload = candidate_decision_consensus_reversal_score_payload(_report())
    payload_with_raw_market = dict(payload)
    payload_with_raw_market["market_id"] = "market-1"
    payload_with_unsafe_value = dict(payload)
    payload_with_unsafe_value["reason_codes"] = ["https://example.test/source-ref"]

    with pytest.raises(ValueError, match="unsafe public field"):
        candidate_decision_consensus_reversal_score_payload(payload_with_raw_market)
    with pytest.raises(ValueError, match="unsafe public value"):
        candidate_decision_consensus_reversal_score_payload(payload_with_unsafe_value)


def test_hard_flags_and_safety_flags_are_rechecked_at_payload_boundary() -> None:
    report = _report(
        input_value=_input(
            current_consensus_score=d("0.310000"),
            prior_consensus_score=d("0.820000"),
            reversal_velocity_score=d("0.920000"),
            evidence_support_score=d("0.150000"),
            source_quality_score=d("0.200000"),
            volatility_score=d("0.800000"),
        ),
    )

    unsafe_status_report = object.__new__(CandidateDecisionConsensusReversalScoreReport)
    for field_name, value in report.__dict__.items():
        object.__setattr__(unsafe_status_report, field_name, value)
    object.__setattr__(unsafe_status_report, "reversal_status", "watch")

    unsafe_flag_report = object.__new__(CandidateDecisionConsensusReversalScoreReport)
    for field_name, value in report.__dict__.items():
        object.__setattr__(unsafe_flag_report, field_name, value)
    object.__setattr__(unsafe_flag_report, "readonly", False)

    with pytest.raises(ValueError, match="hard_flag_codes require block status"):
        candidate_decision_consensus_reversal_score_payload(unsafe_status_report)
    with pytest.raises(ValueError, match="readonly must be True"):
        candidate_decision_consensus_reversal_score_payload(unsafe_flag_report)
    with pytest.raises(ValueError, match="paper_only must be True"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        CandidateDecisionConsensusReversalScoreConfig(report_only=False)


def test_deterministic_payload_and_digest_for_same_inputs() -> None:
    offset_time_report = _report(
        generated_at=datetime(
            2026,
            7,
            7,
            10,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )
    utc_report = _report()

    offset_payload = candidate_decision_consensus_reversal_score_payload(
        offset_time_report,
    )
    utc_payload = candidate_decision_consensus_reversal_score_payload(utc_report)

    assert offset_payload == utc_payload
    assert offset_payload["derived_validation_digest"] == utc_payload[
        "derived_validation_digest"
    ]
    assert json.dumps(offset_payload, allow_nan=False, sort_keys=True) == json.dumps(
        utc_payload,
        allow_nan=False,
        sort_keys=True,
    )


def test_report_consistency_rejects_mismatched_fields_and_digest() -> None:
    report = _report()
    inconsistent_report = object.__new__(CandidateDecisionConsensusReversalScoreReport)
    for field_name, value in report.__dict__.items():
        object.__setattr__(inconsistent_report, field_name, value)
    object.__setattr__(inconsistent_report, "consensus_reversal_score", d("0.900000"))

    with pytest.raises(ValueError, match="consensus_reversal_score must match"):
        candidate_decision_consensus_reversal_score_payload(inconsistent_report)

    payload = candidate_decision_consensus_reversal_score_payload(report)
    payload["current_consensus_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        candidate_decision_consensus_reversal_score_payload(payload)


def test_consensus_reversal_module_has_no_persistence_network_or_execution_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_consensus_reversal_score.py",
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
        "supabase",
        "open(",
        ".write(",
        "place_order",
        "create_order",
        "cancel_order",
        "private_key",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
