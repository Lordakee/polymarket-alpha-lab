from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.candidate_decision_cross_team_consensus_score import (
    CandidateDecisionCrossTeamConsensusScoreConfig,
    CandidateDecisionCrossTeamConsensusScoreInput,
    CandidateDecisionCrossTeamConsensusScoreReport,
    build_candidate_decision_cross_team_consensus_score_report,
    candidate_decision_cross_team_consensus_score_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 14, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(**overrides: object) -> CandidateDecisionCrossTeamConsensusScoreInput:
    values: dict[str, object] = {
        "redacted_candidate_ref": "redacted:alpha-001",
        "primary_team_id": "politics",
        "specialist_count": d("4"),
        "agreeing_team_count": d("4"),
        "dissenting_team_count": d("0"),
        "average_confidence_score": d("0.850000"),
        "dissent_severity_score": d("0.000000"),
        "historical_calibration_score": d("0.800000"),
    }
    values.update(overrides)
    return CandidateDecisionCrossTeamConsensusScoreInput(**values)


def _report(
    *,
    input_value: CandidateDecisionCrossTeamConsensusScoreInput | None = None,
    config: CandidateDecisionCrossTeamConsensusScoreConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CandidateDecisionCrossTeamConsensusScoreReport:
    return build_candidate_decision_cross_team_consensus_score_report(
        input_value or _input(),
        config=config or CandidateDecisionCrossTeamConsensusScoreConfig(),
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


def test_consensus_pass_report_is_json_safe_and_uses_public_status_vocabulary() -> None:
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

    assert type(report) is CandidateDecisionCrossTeamConsensusScoreReport
    assert report.generated_at == GENERATED_AT
    assert report.consensus_status == "pass"
    assert report.agreement_ratio == d("1.000000")
    assert report.dissent_ratio == d("0.000000")
    assert report.dissent_pressure_score == d("0.000000")
    assert report.dissent_resistance_score == d("1.000000")
    assert report.consensus_score == d("0.920000")
    assert report.hard_flag_codes == ()
    assert report.reason_codes == (
        "cross_team_consensus_pass",
        "specialist_count_pass",
        "agreement_ratio_pass",
        "dissent_pressure_pass",
        "historical_calibration_pass",
        "consensus_score_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = candidate_decision_cross_team_consensus_score_payload(report)

    assert payload["generated_at"] == "2026-07-07T14:30:00+00:00"
    assert payload["redacted_candidate_ref"] == "redacted:alpha-001"
    assert payload["primary_team_id"] == "politics"
    assert payload["specialist_count"] == "4"
    assert payload["consensus_status"] == "pass"
    assert payload["consensus_score"] == "0.920000"
    assert payload["agreement_ratio"] == "1.000000"
    assert payload["reason_codes"] == list(report.reason_codes)
    assert "candidate_id" not in payload
    assert "market_id" not in payload
    assert "market_slug" not in payload
    assert "question" not in payload
    assert "source_report_refs" not in payload
    assert not _contains_float(payload)
    _assert_no_public_status_leak(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_severe_dissent_blocks_and_sets_hard_flags() -> None:
    report = _report(
        input_value=_input(
            specialist_count=d("4"),
            agreeing_team_count=d("3"),
            dissenting_team_count=d("1"),
            average_confidence_score=d("0.850000"),
            dissent_severity_score=d("0.950000"),
            historical_calibration_score=d("0.800000"),
        ),
    )

    assert report.consensus_status == "block"
    assert report.hard_flag_codes == ("dissent_pressure_block",)
    assert report.dissent_ratio == d("0.250000")
    assert report.dissent_pressure_score == d("0.237500")
    assert report.reason_codes[0] == "cross_team_consensus_block"
    assert "dissent_pressure_block" in report.reason_codes


def test_insufficient_specialists_watch_and_block() -> None:
    watch_report = _report(
        input_value=_input(
            specialist_count=d("2"),
            agreeing_team_count=d("2"),
            dissenting_team_count=d("0"),
        ),
    )
    block_report = _report(
        input_value=_input(
            specialist_count=d("1"),
            agreeing_team_count=d("1"),
            dissenting_team_count=d("0"),
        ),
    )

    assert watch_report.consensus_status == "watch"
    assert watch_report.hard_flag_codes == ()
    assert "specialist_count_watch" in watch_report.reason_codes
    assert block_report.consensus_status == "block"
    assert block_report.hard_flag_codes == ("specialist_count_block",)
    assert "specialist_count_block" in block_report.reason_codes


def test_exact_decimal_validation_and_frozen_dataclasses() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.consensus_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="average_confidence_score must be a Decimal"):
        _input(average_confidence_score=0.85)
    with pytest.raises(ValueError, match="specialist_count must be a whole number"):
        _input(specialist_count=d("2.5"))
    with pytest.raises(ValueError, match="agreement_weight must be a Decimal"):
        CandidateDecisionCrossTeamConsensusScoreConfig(agreement_weight=0.4)
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadInput(CandidateDecisionCrossTeamConsensusScoreInput):
            pass


def test_rejects_unsafe_public_payload_and_raw_candidate_refs() -> None:
    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        _input(redacted_candidate_ref="candidate-raw-1")
    with pytest.raises(ValueError, match="unsafe public value"):
        _input(redacted_candidate_ref="redacted:https://example.test/candidate")

    payload = candidate_decision_cross_team_consensus_score_payload(_report())
    payload_with_raw_market = dict(payload)
    payload_with_raw_market["market_id"] = "market-1"
    payload_with_unsafe_value = dict(payload)
    payload_with_unsafe_value["reason_codes"] = ["https://example.test/source"]

    with pytest.raises(ValueError, match="unsafe public field"):
        candidate_decision_cross_team_consensus_score_payload(payload_with_raw_market)
    with pytest.raises(ValueError, match="unsafe public value"):
        candidate_decision_cross_team_consensus_score_payload(payload_with_unsafe_value)


def test_hard_flags_and_safety_flags_are_rechecked_at_payload_boundary() -> None:
    report = _report(
        input_value=_input(
            specialist_count=d("4"),
            agreeing_team_count=d("3"),
            dissenting_team_count=d("1"),
            dissent_severity_score=d("0.950000"),
        ),
    )

    unsafe_status_report = object.__new__(CandidateDecisionCrossTeamConsensusScoreReport)
    for field_name, value in report.__dict__.items():
        object.__setattr__(unsafe_status_report, field_name, value)
    object.__setattr__(unsafe_status_report, "consensus_status", "pass")

    unsafe_flag_report = object.__new__(CandidateDecisionCrossTeamConsensusScoreReport)
    for field_name, value in report.__dict__.items():
        object.__setattr__(unsafe_flag_report, field_name, value)
    object.__setattr__(unsafe_flag_report, "readonly", False)

    with pytest.raises(ValueError, match="hard_flag_codes require block status"):
        candidate_decision_cross_team_consensus_score_payload(unsafe_status_report)
    with pytest.raises(ValueError, match="readonly must be True"):
        candidate_decision_cross_team_consensus_score_payload(unsafe_flag_report)
    with pytest.raises(ValueError, match="paper_only must be True"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        CandidateDecisionCrossTeamConsensusScoreConfig(report_only=False)


def test_report_consistency_rejects_mismatched_fields_and_digest() -> None:
    report = _report()
    inconsistent_report = object.__new__(CandidateDecisionCrossTeamConsensusScoreReport)
    for field_name, value in report.__dict__.items():
        object.__setattr__(inconsistent_report, field_name, value)
    object.__setattr__(inconsistent_report, "agreement_ratio", d("0.250000"))

    with pytest.raises(ValueError, match="agreement_ratio must match"):
        candidate_decision_cross_team_consensus_score_payload(inconsistent_report)

    payload = candidate_decision_cross_team_consensus_score_payload(report)
    payload["consensus_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        candidate_decision_cross_team_consensus_score_payload(payload)


def test_cross_team_consensus_module_has_no_persistence_network_or_execution_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_cross_team_consensus_score.py",
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
