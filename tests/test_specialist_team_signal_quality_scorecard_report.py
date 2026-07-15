from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.specialist_team_signal_quality_scorecard_report import (
    DEFAULT_SPECIALIST_TEAM_SIGNAL_QUALITY_SCORECARD_REPORT_CONFIG_VERSION,
    SpecialistTeamSignalQualityScorecardInput,
    SpecialistTeamSignalQualityScorecardReport,
    build_specialist_team_signal_quality_scorecard_report,
    validate_specialist_team_signal_quality_scorecard_public_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/specialist_team_signal_quality_scorecard_report.py",
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def signal_input(
    team: str = "team-alpha",
    *,
    source_quorum_score: str = "0.950000",
    forecast_track_record_score: str = "0.900000",
    calibration_score: str = "0.850000",
    recency_score: str = "0.800000",
    contradiction_penalty: str = "0.100000",
) -> SpecialistTeamSignalQualityScorecardInput:
    return SpecialistTeamSignalQualityScorecardInput(
        team=team,
        source_quorum_score=d(source_quorum_score),
        forecast_track_record_score=d(forecast_track_record_score),
        calibration_score=d(calibration_score),
        recency_score=d(recency_score),
        contradiction_penalty=d(contradiction_penalty),
    )


def assert_no_public_numbers(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"public payload numeric value leaked: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numbers(item)
    if type(value) is list:
        for item in value:
            assert_no_public_numbers(item)


def test_builds_strong_readonly_scorecard_with_public_digest() -> None:
    report = build_specialist_team_signal_quality_scorecard_report(
        signal_input(),
    )

    assert is_dataclass(report)
    assert type(report) is SpecialistTeamSignalQualityScorecardReport
    assert report.config_version == (
        DEFAULT_SPECIALIST_TEAM_SIGNAL_QUALITY_SCORECARD_REPORT_CONFIG_VERSION
    )
    assert report.team == "team-alpha"
    assert report.source_quorum_score == d("0.950000")
    assert report.forecast_track_record_score == d("0.900000")
    assert report.calibration_score == d("0.850000")
    assert report.recency_score == d("0.800000")
    assert report.contradiction_penalty == d("0.100000")
    assert report.weighted_score == d("0.882500")
    assert report.quality_band == "strong_signal_quality"
    assert report.reason_codes == ("signal_quality_strong",)
    assert report.manual_next_step == "continue_readonly_paper_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload["source_quorum_score"] == "0.950000"
    assert payload["forecast_track_record_score"] == "0.900000"
    assert payload["calibration_score"] == "0.850000"
    assert payload["recency_score"] == "0.800000"
    assert payload["contradiction_penalty"] == "0.100000"
    assert payload["weighted_score"] == "0.882500"
    assert payload["quality_band"] == "strong_signal_quality"
    assert payload["reason_codes"] == ["signal_quality_strong"]
    assert payload["manual_next_step"] == "continue_readonly_paper_review"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    assert validate_specialist_team_signal_quality_scorecard_public_payload(payload)
    assert_no_public_numbers(payload)


def test_review_and_insufficient_bands_emit_stable_reason_codes() -> None:
    review_report = build_specialist_team_signal_quality_scorecard_report(
        signal_input(
            "team-beta",
            source_quorum_score="0.620000",
            forecast_track_record_score="0.700000",
            calibration_score="0.650000",
            recency_score="0.620000",
            contradiction_penalty="0.300000",
        ),
    )

    assert review_report.weighted_score == d("0.654000")
    assert review_report.quality_band == "manual_review_signal_quality"
    assert review_report.reason_codes == (
        "source_quorum_watch",
        "forecast_track_record_watch",
        "calibration_watch",
        "recency_watch",
        "contradiction_penalty_watch",
        "weighted_score_watch",
    )
    assert review_report.manual_next_step == "manually_review_team_signal_inputs"

    insufficient_report = build_specialist_team_signal_quality_scorecard_report(
        signal_input(
            "team-gamma",
            source_quorum_score="0.550000",
            forecast_track_record_score="0.600000",
            calibration_score="0.400000",
            recency_score="0.500000",
            contradiction_penalty="0.700000",
        ),
    )

    assert insufficient_report.weighted_score == d("0.497500")
    assert insufficient_report.quality_band == "insufficient_signal_quality"
    assert insufficient_report.reason_codes == (
        "source_quorum_low",
        "forecast_track_record_watch",
        "calibration_low",
        "recency_low",
        "contradiction_penalty_high",
        "weighted_score_low",
    )
    assert insufficient_report.manual_next_step == "manually_rebuild_team_signal_evidence"


def test_inputs_reports_and_payloads_are_frozen_decimal_only_and_tamper_checked() -> None:
    report = build_specialist_team_signal_quality_scorecard_report(signal_input())

    with pytest.raises(FrozenInstanceError):
        report.quality_band = "manual_review_signal_quality"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="paper_only"):
        replace(signal_input(), paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        SpecialistTeamSignalQualityScorecardInput(
            team="team-alpha",
            source_quorum_score=DecimalSubclass("0.900000"),
            forecast_track_record_score=d("0.900000"),
            calibration_score=d("0.900000"),
            recency_score=d("0.900000"),
            contradiction_penalty=d("0.100000"),
        )

    with pytest.raises(ValueError, match="score"):
        SpecialistTeamSignalQualityScorecardInput(
            team="team-alpha",
            source_quorum_score=d("1.100000"),
            forecast_track_record_score=d("0.900000"),
            calibration_score=d("0.900000"),
            recency_score=d("0.900000"),
            contradiction_penalty=d("0.100000"),
        )

    tampered = dict(report.public_payload)
    tampered["weighted_score"] = "0.000000"
    assert not validate_specialist_team_signal_quality_scorecard_public_payload(tampered)

    numeric_payload = dict(report.public_payload)
    numeric_payload["weighted_score"] = d("0.882500")
    assert not validate_specialist_team_signal_quality_scorecard_public_payload(
        numeric_payload,
    )


def test_module_has_no_mutation_or_secret_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").casefold()
    unsafe_fragments = tuple(
        bytes.fromhex(value).decode("ascii")
        for value in (
            "6c697665",
            "61757468",
            "77616c6c6574",
            "6f72646572",
            "6b657973",
            "7369676e696e67",
            "657865637574696f6e",
        )
    )

    for fragment in unsafe_fragments:
        assert fragment not in source
    assert "open(" not in source
    assert ".write(" not in source
    assert "pathlib" not in source
