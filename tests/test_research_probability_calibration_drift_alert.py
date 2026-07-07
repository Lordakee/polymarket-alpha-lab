from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_probability_calibration_drift_alert as api
from polymarket_alpha_lab.research_probability_calibration_drift_alert import (
    ProbabilityCalibrationDriftAlertConfig,
    ProbabilityCalibrationDriftAlertReport,
    ProbabilityCalibrationDriftAlertRow,
    ProbabilityCalibrationDriftAlertSample,
    build_probability_calibration_drift_alert_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _sample(
    *,
    sample_key: str = "sample_a",
    model_probability: Decimal = Decimal("0.520000"),
    team_probability: Decimal = Decimal("0.530000"),
    domain_probability: Decimal = Decimal("0.510000"),
    market_implied_probability: Decimal = Decimal("0.515000"),
    model_confidence: Decimal = Decimal("0.800000"),
    team_confidence: Decimal = Decimal("0.750000"),
    domain_confidence: Decimal = Decimal("0.700000"),
    market_depth_score: Decimal = Decimal("0.650000"),
) -> ProbabilityCalibrationDriftAlertSample:
    return ProbabilityCalibrationDriftAlertSample(
        sample_key=sample_key,
        observed_at=NOW,
        model_probability=model_probability,
        team_probability=team_probability,
        domain_probability=domain_probability,
        market_implied_probability=market_implied_probability,
        model_confidence=model_confidence,
        team_confidence=team_confidence,
        domain_confidence=domain_confidence,
        market_depth_score=market_depth_score,
    )


def _report(
    samples: tuple[ProbabilityCalibrationDriftAlertSample, ...],
    *,
    config: ProbabilityCalibrationDriftAlertConfig | None = None,
) -> ProbabilityCalibrationDriftAlertReport:
    return build_probability_calibration_drift_alert_report(
        samples,
        generated_at=NOW,
        config=config,
    )


def test_pass_alert_when_all_probability_views_are_calibrated() -> None:
    report = _report((_sample(),))

    row = report.rows[0]
    assert report.alert_status == "pass"
    assert report.sample_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert row.alert_status == "pass"
    assert row.max_pairwise_drift == Decimal("0.020000")
    assert row.market_model_drift == Decimal("0.005000")
    assert row.consensus_market_drift == Decimal("0.005000")
    assert row.confidence_weighted_drift_score == Decimal("0.010862")
    assert row.reason_codes == ("probability_calibration_drift_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_watch_alert_reports_team_domain_market_drift() -> None:
    report = _report(
        (
            _sample(
                sample_key="sample_watch",
                model_probability=Decimal("0.660000"),
                team_probability=Decimal("0.570000"),
                domain_probability=Decimal("0.590000"),
                market_implied_probability=Decimal("0.530000"),
                model_confidence=Decimal("0.900000"),
                team_confidence=Decimal("0.850000"),
                domain_confidence=Decimal("0.800000"),
                market_depth_score=Decimal("0.700000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.alert_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.alert_status == "watch"
    assert row.max_pairwise_drift == Decimal("0.130000")
    assert row.model_team_drift == Decimal("0.090000")
    assert row.team_domain_drift == Decimal("0.020000")
    assert row.market_model_drift == Decimal("0.130000")
    assert row.consensus_market_drift == Decimal("0.076667")
    assert row.confidence_weighted_drift_score == Decimal("0.068667")
    assert row.reason_codes == (
        "probability_calibration_drift_watch",
        "max_pairwise_drift_watch",
        "model_team_drift_watch",
        "market_model_drift_watch",
    )


def test_block_alert_when_model_and_market_are_severely_miscalibrated() -> None:
    report = _report(
        (
            _sample(
                sample_key="sample_block",
                model_probability=Decimal("0.850000"),
                team_probability=Decimal("0.610000"),
                domain_probability=Decimal("0.570000"),
                market_implied_probability=Decimal("0.350000"),
                model_confidence=Decimal("0.950000"),
                team_confidence=Decimal("0.900000"),
                domain_confidence=Decimal("0.850000"),
                market_depth_score=Decimal("0.900000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.alert_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.alert_status == "block"
    assert row.max_pairwise_drift == Decimal("0.500000")
    assert row.market_model_drift == Decimal("0.500000")
    assert row.consensus_market_drift == Decimal("0.326667")
    assert row.confidence_weighted_drift_score == Decimal("0.258889")
    assert row.reason_codes == (
        "probability_calibration_drift_block",
        "max_pairwise_drift_block",
        "model_team_drift_block",
        "market_model_drift_block",
        "consensus_market_drift_block",
    )


def test_report_is_deterministic_and_rows_are_sorted_by_public_key() -> None:
    samples = (
        _sample(sample_key="sample_b", model_probability=Decimal("0.560000")),
        _sample(sample_key="sample_a", model_probability=Decimal("0.520000")),
    )

    first = _report(samples)
    second = _report(tuple(reversed(samples)))

    assert tuple(row.sample_key for row in first.rows) == ("sample_a", "sample_b")
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest


def test_payload_serializes_decimal_strings_and_excludes_raw_identifiers() -> None:
    report = _report(
        (
            _sample(
                sample_key="sample_watch",
                model_probability=Decimal("0.660000"),
                team_probability=Decimal("0.570000"),
                domain_probability=Decimal("0.590000"),
                market_implied_probability=Decimal("0.530000"),
            ),
        ),
    )

    payload = report.payload
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["sample_count"] == "1.000000"
    assert payload["rows"][0]["max_pairwise_drift"] == "0.130000"
    assert payload["rows"][0]["market_model_drift"] == "0.130000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "raw" not in encoded.lower()
    assert "source" not in encoded.lower()
    assert "market_id" not in encoded.lower()
    assert "condition_id" not in encoded.lower()
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_dataclasses_are_frozen_exact_types_and_reject_subclassing() -> None:
    report = _report((_sample(),))

    with pytest.raises(FrozenInstanceError):
        report.alert_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadSample(ProbabilityCalibrationDriftAlertSample):
            pass

    with pytest.raises(ValueError, match="sample must be exactly"):
        api._normalize_samples((object(),))  # type: ignore[attr-defined]


def test_strict_decimal_validation_and_hard_flags() -> None:
    with pytest.raises(ValueError, match="model_probability must be a Decimal"):
        _sample(model_probability=0.52)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_probability must be finite"):
        _sample(team_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="domain_probability must use"):
        _sample(domain_probability=Decimal("0.5100001"))

    with pytest.raises(ValueError, match="market_implied_probability must be between zero and one"):
        _sample(market_implied_probability=Decimal("1.000001"))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_probability_calibration_drift_alert_report(
            (
                replace(
                    _sample(),
                    observed_at=datetime(2026, 1, 2, tzinfo=UTC),
                ),
            ),
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="paper_only"):
        ProbabilityCalibrationDriftAlertConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(_sample(), readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report((_sample(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, generated_at=datetime(2026, 1, 1, 0, 1, tzinfo=UTC))


def test_no_unsafe_public_surfaces_or_network_database_dependencies() -> None:
    unsafe_terms = (
        "raw",
        "source",
        "market_id",
        "condition_id",
        "slug",
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
        ProbabilityCalibrationDriftAlertConfig,
        ProbabilityCalibrationDriftAlertSample,
        ProbabilityCalibrationDriftAlertRow,
        ProbabilityCalibrationDriftAlertReport,
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
