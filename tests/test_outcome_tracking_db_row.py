from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.outcome_tracking_db_row import (
    OutcomeTrackingReportDbRow,
    outcome_tracking_report_from_db_row,
    outcome_tracking_report_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 19, 19, 0, tzinfo=UTC)
CONFIG_VERSION = "outcome-tracker-db-v0"


class OutcomeTrackingReportSubclass(OutcomeTrackingReport):
    pass


def _observation(suffix: str = "1") -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=GENERATED_AT,
        source_packet_id=f"packet-{suffix}",
        condition_id=f"condition-{suffix}",
        token_id=f"token-{suffix}",
        market_slug=f"market-{suffix}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.6000"),
        actual_outcome_value=Decimal("1"),
    )


def _resolved_report(suffix: str = "1") -> OutcomeTrackingReport:
    observation = _observation(suffix)
    evidence_report = build_paper_forecast_evidence_report(
        (observation,),
        config=PaperForecastEvidenceConfig(
            config_version=CONFIG_VERSION,
            min_probability_observations=1,
            min_edge_observations=0,
        ),
        generated_at=GENERATED_AT,
    )
    return OutcomeTrackingReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        observations=(observation,),
        forecast_evidence_report=evidence_report,
    )


def _empty_report() -> OutcomeTrackingReport:
    return OutcomeTrackingReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        total_markets_checked=0,
        resolved_count=0,
        pending_count=0,
        observations=(),
        forecast_evidence_report=None,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_outcome_tracking_db_row_serializes_summary_payload_and_round_trips():
    report = _resolved_report()

    row = outcome_tracking_report_to_db_row(report)

    assert type(row) is OutcomeTrackingReportDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.total_markets_checked == 1
    assert row.resolved_count == 1
    assert row.pending_count == 0
    assert row.observation_count == 1
    assert isinstance(report.forecast_evidence_report, PaperForecastEvidenceReport)
    assert row.forecast_evidence_status == report.forecast_evidence_report.status
    assert row.paper_only is True
    assert row.payload_json["generated_at"] == "2026-06-19T19:00:00+00:00"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.payload_json["observations"][0]["predicted_probability"] == "0.6000"
    assert row.payload_json["observations"][0]["actual_outcome_value"] == "1"
    assert row.payload_json["forecast_evidence_report"]["paper_only"] is True
    _assert_no_floats(row.payload_json)

    assert outcome_tracking_report_from_db_row(row) == report


def test_outcome_tracking_db_row_handles_empty_report_without_evidence_status():
    report = _empty_report()

    row = outcome_tracking_report_to_db_row(report)

    assert row.total_markets_checked == 0
    assert row.resolved_count == 0
    assert row.pending_count == 0
    assert row.observation_count == 0
    assert row.forecast_evidence_status is None
    assert row.payload_json["forecast_evidence_report"] is None
    assert outcome_tracking_report_from_db_row(row) == report


def test_outcome_tracking_db_row_hash_uses_full_payload_and_is_deterministic():
    report = _resolved_report("1")
    same_report = OutcomeTrackingReport(**report.__dict__)
    different_payload_same_summary = _resolved_report("2")

    first = outcome_tracking_report_to_db_row(report)
    second = outcome_tracking_report_to_db_row(same_report)
    different = outcome_tracking_report_to_db_row(different_payload_same_summary)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != different.report_sha256
    assert first.total_markets_checked == different.total_markets_checked
    assert first.resolved_count == different.resolved_count


def test_outcome_tracking_db_row_is_frozen():
    row = outcome_tracking_report_to_db_row(_empty_report())

    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]


def test_outcome_tracking_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(ValueError, match="OutcomeTrackingReport"):
        outcome_tracking_report_to_db_row(object())

    report = _empty_report()
    subclass = OutcomeTrackingReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="OutcomeTrackingReport"):
        outcome_tracking_report_to_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_outcome_tracking_db_row_rejects_false_report_flags(flag_name: str):
    report = _empty_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        outcome_tracking_report_to_db_row(report)


def test_outcome_tracking_db_row_rejects_unsafe_stored_flags():
    row = outcome_tracking_report_to_db_row(_empty_report())
    malformed = OutcomeTrackingReportDbRow(
        report_sha256="a" * 64,
        generated_at=row.generated_at,
        config_version=row.config_version,
        total_markets_checked=row.total_markets_checked,
        resolved_count=row.resolved_count,
        pending_count=row.pending_count,
        observation_count=row.observation_count,
        forecast_evidence_status=row.forecast_evidence_status,
        payload_json={**row.payload_json, "readonly": False},
    )

    with pytest.raises(ValueError, match="readonly"):
        outcome_tracking_report_from_db_row(malformed)


def test_outcome_tracking_db_row_wraps_payload_recovery_errors_as_value_error():
    row = outcome_tracking_report_to_db_row(_empty_report())
    malformed = OutcomeTrackingReportDbRow(
        report_sha256="a" * 64,
        generated_at=row.generated_at,
        config_version=row.config_version,
        total_markets_checked=row.total_markets_checked,
        resolved_count=row.resolved_count,
        pending_count=row.pending_count,
        observation_count=row.observation_count,
        forecast_evidence_status=row.forecast_evidence_status,
        payload_json={
            key: value
            for key, value in row.payload_json.items()
            if key != "observations"
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        outcome_tracking_report_from_db_row(malformed)


def test_outcome_tracking_db_row_validates_row_shape_and_rejects_floats():
    row = outcome_tracking_report_to_db_row(_empty_report())

    with pytest.raises(ValueError, match="report_sha256"):
        OutcomeTrackingReportDbRow(
            report_sha256="bad",
            generated_at=row.generated_at,
            config_version=row.config_version,
            total_markets_checked=row.total_markets_checked,
            resolved_count=row.resolved_count,
            pending_count=row.pending_count,
            observation_count=row.observation_count,
            forecast_evidence_status=row.forecast_evidence_status,
            payload_json=row.payload_json,
        )

    with pytest.raises(ValueError, match="payload_json"):
        OutcomeTrackingReportDbRow(
            report_sha256="a" * 64,
            generated_at=row.generated_at,
            config_version=row.config_version,
            total_markets_checked=row.total_markets_checked,
            resolved_count=row.resolved_count,
            pending_count=row.pending_count,
            observation_count=row.observation_count,
            forecast_evidence_status=row.forecast_evidence_status,
            payload_json={**row.payload_json, "bad_float": 0.1},
        )
