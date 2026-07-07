from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 16, 30, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_calibration_gap_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(**overrides: object):
    digest = api()
    values = {
        "team_id": "politics",
        "category_id": "politics",
        "strategy_id": "event-momentum-v1",
        "forecast_probability": d("0.640000"),
        "market_implied_probability": d("0.520000"),
        "realized_probability": d("1.000000"),
        "confidence": d("0.720000"),
        "prior_confidence": d("0.600000"),
        "evidence_age_hours": d("6.000000"),
        "reason_codes": ("wide_positive_calibration_gap", "resolved_learning_available"),
    }
    values.update(overrides)
    return digest.StrategyRecommendationCalibrationGapInput(**values)


def config(**overrides: object):
    digest = api()
    values = {
        "config_version": "strategy-recommendation-calibration-gap-digest-v0",
        "material_gap_threshold": d("0.050000"),
        "confidence_drift_threshold": d("0.100000"),
        "stale_evidence_hours": d("24.000000"),
    }
    values.update(overrides)
    return digest.StrategyRecommendationCalibrationGapDigestConfig(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_strategy_recommendation_calibration_gap_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_digest_summarizes_calibration_gaps_learning_and_reason_codes() -> None:
    digest_report = report(
        input_row(
            team_id="crypto_btc",
            category_id="crypto",
            strategy_id="mean-reversion-v1",
            forecast_probability=d("0.690000"),
            market_implied_probability=d("0.540000"),
            realized_probability=d("1.000000"),
            confidence=d("0.850000"),
            prior_confidence=d("0.700000"),
            evidence_age_hours=d("8.000000"),
            reason_codes=(
                "wide_positive_calibration_gap",
                "resolved_learning_available",
                "confidence_increased",
            ),
        ),
        input_row(
            team_id="crypto_eth",
            category_id="crypto",
            strategy_id="mean-reversion-v1",
            forecast_probability=d("0.300000"),
            market_implied_probability=d("0.440000"),
            realized_probability=d("0.000000"),
            confidence=d("0.450000"),
            prior_confidence=d("0.620000"),
            evidence_age_hours=d("30.000000"),
            reason_codes=(
                "wide_negative_calibration_gap",
                "resolved_learning_available",
                "confidence_decreased",
                "stale_evidence",
            ),
        ),
        input_row(
            team_id="politics",
            category_id="politics",
            strategy_id="event-momentum-v1",
            forecast_probability=d("0.510000"),
            market_implied_probability=d("0.500000"),
            realized_probability=None,
            confidence=d("0.550000"),
            prior_confidence=d("0.520000"),
            evidence_age_hours=d("4.000000"),
            reason_codes=("calibration_gap_within_threshold",),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "strategy-recommendation-calibration-gap-digest-v0"
    )
    assert digest_report.source_row_count == d("3")
    assert digest_report.team_count == d("3")
    assert digest_report.category_count == d("2")
    assert digest_report.material_gap_count == d("2")
    assert digest_report.learning_available_count == d("2")
    assert digest_report.confidence_drift_count == d("2")
    assert digest_report.stale_evidence_count == d("1")
    assert digest_report.status == "watch"
    assert digest_report.reason_codes == (
        "material_calibration_gap_detected",
        "resolved_learning_available",
        "confidence_drift_detected",
        "stale_evidence_detected",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    crypto, politics = digest_report.category_rows
    assert crypto.category_id == "crypto"
    assert crypto.team_count == d("2")
    assert crypto.source_row_count == d("2")
    assert crypto.material_gap_count == d("2")
    assert crypto.learning_available_count == d("2")
    assert crypto.confidence_drift_count == d("2")
    assert crypto.stale_evidence_count == d("1")
    assert crypto.mean_absolute_gap == d("0.145000")
    assert crypto.mean_signed_gap == d("0.005000")
    assert crypto.mean_confidence_drift == d("-0.010000")
    assert crypto.status == "watch"
    assert crypto.top_reason_codes == (
        "resolved_learning_available",
        "confidence_decreased",
        "confidence_increased",
        "stale_evidence",
        "wide_negative_calibration_gap",
        "wide_positive_calibration_gap",
    )

    assert politics.category_id == "politics"
    assert politics.material_gap_count == d("0")
    assert politics.learning_available_count == d("0")
    assert politics.mean_absolute_gap == d("0.010000")
    assert politics.status == "pass"


def test_digest_normalizes_utc_and_serializes_json_without_floats() -> None:
    digest = api()
    digest_report = report(
        input_row(),
        generated_at=datetime(2026, 7, 2, 9, 30, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = digest.strategy_recommendation_calibration_gap_digest_payload(
        digest_report,
    )
    payload_text = repr(payload).lower()

    assert digest_report.generated_at == GENERATED_AT
    assert payload["generated_at"] == "2026-07-02T16:30:00+00:00"
    assert payload["source_row_count"] == "1"
    assert payload["category_rows"][0]["mean_absolute_gap"] == "0.120000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == digest_report.derived_validation_digest
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in payload_text

    def assert_no_float(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float(item)
        else:
            assert type(value) is not float

    assert_no_float(payload)


def test_digest_has_tamper_evident_derived_validation_digest() -> None:
    digest = api()
    digest_report = report(input_row())

    assert len(digest_report.derived_validation_digest) == 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest_report, derived_validation_digest="0" * 64)

    object.__setattr__(
        digest_report.category_rows[0],
        "mean_absolute_gap",
        d("0.999000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.strategy_recommendation_calibration_gap_digest_payload(digest_report)


def test_public_payload_validator_rejects_unsafe_surface_values_and_numerics() -> None:
    digest = api()
    payload = digest.strategy_recommendation_calibration_gap_digest_payload(
        report(input_row()),
    )

    digest.validate_strategy_recommendation_calibration_gap_digest_public_payload(
        payload,
    )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        digest.validate_strategy_recommendation_calibration_gap_digest_public_payload(
            {**payload, "wallet": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        digest.validate_strategy_recommendation_calibration_gap_digest_public_payload(
            {**payload, "config_version": "live_trading"},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        digest.validate_strategy_recommendation_calibration_gap_digest_public_payload(
            {**payload, "source_row_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        digest.validate_strategy_recommendation_calibration_gap_digest_public_payload(
            {**payload, "readonly": False},
        )


def test_digest_uses_deterministic_sorting_and_reason_code_ties() -> None:
    digest_report = report(
        input_row(
            team_id="politics",
            category_id="politics",
            strategy_id="zeta",
            forecast_probability=d("0.650000"),
            market_implied_probability=d("0.500000"),
            realized_probability=None,
            confidence=d("0.600000"),
            prior_confidence=d("0.600000"),
            evidence_age_hours=d("1.000000"),
            reason_codes=("wide_positive_calibration_gap", "stale_evidence"),
        ),
        input_row(
            team_id="macro_rates",
            category_id="macro",
            strategy_id="alpha",
            forecast_probability=d("0.200000"),
            market_implied_probability=d("0.350000"),
            realized_probability=None,
            confidence=d("0.600000"),
            prior_confidence=d("0.600000"),
            evidence_age_hours=d("1.000000"),
            reason_codes=("wide_negative_calibration_gap", "stale_evidence"),
        ),
    )

    assert tuple(row.category_id for row in digest_report.category_rows) == (
        "macro",
        "politics",
    )
    assert digest_report.category_rows[0].top_reason_codes == (
        "stale_evidence",
        "wide_negative_calibration_gap",
    )
    assert digest_report.category_rows[1].top_reason_codes == (
        "stale_evidence",
        "wide_positive_calibration_gap",
    )


def test_digest_validates_decimal_inputs_flags_and_frozen_outputs() -> None:
    digest = api()
    digest_report = report(input_row())

    with pytest.raises(FrozenInstanceError):
        digest_report.category_rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        input_row(forecast_probability=0.64)

    with pytest.raises(ValueError, match="forecast_probability"):
        input_row(forecast_probability=_DecimalSubclass("0.640000"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(input_row(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest.StrategyRecommendationCalibrationGapDigestReport(
            generated_at=_DatetimeSubclass(2026, 7, 2, 16, 30, tzinfo=UTC),
            config_version="strategy-recommendation-calibration-gap-digest-v0",
            source_row_count=d("0"),
            team_count=d("0"),
            category_count=d("0"),
            material_gap_count=d("0"),
            learning_available_count=d("0"),
            confidence_drift_count=d("0"),
            stale_evidence_count=d("0"),
            status="pass",
            reason_codes=("calibration_gap_digest_clear",),
            category_rows=(),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(input_row(), generated_at=datetime(2026, 7, 2, 16, 30))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            input_row(),
            generated_at=datetime(2026, 7, 2, 16, 30, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="input must be readonly"):
        input_row(readonly=False)

    with pytest.raises(ValueError, match="source_row_count"):
        replace(digest_report, source_row_count=d("2"))

    with pytest.raises(ValueError, match="category_rows"):
        replace(digest_report, category_rows=(digest_report.category_rows[0],) * 2)


def test_digest_rejects_report_team_count_that_does_not_match_category_rows() -> None:
    digest = api()
    digest_report = report(
        input_row(
            team_id="crypto_btc",
            category_id="crypto",
            strategy_id="alpha",
            forecast_probability=d("0.690000"),
            market_implied_probability=d("0.540000"),
            realized_probability=d("1.000000"),
            confidence=d("0.850000"),
            prior_confidence=d("0.700000"),
            evidence_age_hours=d("8.000000"),
            reason_codes=(
                "wide_positive_calibration_gap",
                "resolved_learning_available",
                "confidence_increased",
            ),
        ),
        input_row(
            team_id="crypto_eth",
            category_id="crypto",
            strategy_id="beta",
            forecast_probability=d("0.300000"),
            market_implied_probability=d("0.440000"),
            realized_probability=d("0.000000"),
            confidence=d("0.450000"),
            prior_confidence=d("0.620000"),
            evidence_age_hours=d("30.000000"),
            reason_codes=(
                "wide_negative_calibration_gap",
                "resolved_learning_available",
                "confidence_decreased",
                "stale_evidence",
            ),
        ),
    )

    with pytest.raises(ValueError, match="team_count must match category_rows"):
        digest.StrategyRecommendationCalibrationGapDigestReport(
            generated_at=digest_report.generated_at,
            config_version=digest_report.config_version,
            source_row_count=digest_report.source_row_count,
            team_count=d("1"),
            category_count=digest_report.category_count,
            material_gap_count=digest_report.material_gap_count,
            learning_available_count=digest_report.learning_available_count,
            confidence_drift_count=digest_report.confidence_drift_count,
            stale_evidence_count=digest_report.stale_evidence_count,
            status=digest_report.status,
            reason_codes=digest_report.reason_codes,
            category_rows=digest_report.category_rows,
        )


def test_digest_rejects_inconsistent_inputs() -> None:
    with pytest.raises(ValueError, match="team_id must match category_id"):
        input_row(team_id="crypto_btc", category_id="politics")

    with pytest.raises(ValueError, match="reason_codes must match input"):
        input_row(reason_codes=("confidence_decreased",))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            input_row(team_id="politics", category_id="politics", strategy_id="alpha"),
            input_row(team_id="politics", category_id="politics", strategy_id="alpha"),
        )

    with pytest.raises(ValueError, match="realized_probability must be 0 or 1"):
        input_row(realized_probability=d("0.500000"))

    with pytest.raises(ValueError, match="evidence_age_hours"):
        config(stale_evidence_hours=d("-1.000000"))


def test_module_scope_has_no_live_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_calibration_gap_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "network",
        "database",
        "db",
        "file io",
        "open(",
        "advice",
        "order",
        "trade",
        "trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
