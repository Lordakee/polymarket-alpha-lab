from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_evidence_weighted_probability_adjustment_v2 import (
    DEFAULT_CONFIG_VERSION,
    StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
    StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    StrategyEvidenceWeightedProbabilityAdjustmentV2Report,
    build_strategy_evidence_weighted_probability_adjustment_v2_report,
    strategy_evidence_weighted_probability_adjustment_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe_term(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> StrategyEvidenceWeightedProbabilityAdjustmentV2Config:
    values = {
        "config_version": DEFAULT_CONFIG_VERSION,
        "max_information_age_hours": d("72.000000"),
        "max_probability_adjustment": d("0.150000"),
        "evidence_strength_weight": d("0.250000"),
        "source_reliability_weight": d("0.200000"),
        "information_recency_weight": d("0.150000"),
        "specialist_calibration_weight": d("0.200000"),
        "resolution_rule_clarity_weight": d("0.200000"),
        "contradiction_penalty_multiplier": d("1.000000"),
        "pass_adjustment_weight": d("0.600000"),
        "watch_adjustment_weight": d("0.350000"),
        "reject_contradiction_severity": d("0.750000"),
        "reject_resolution_rule_clarity": d("0.250000"),
    }
    values.update(overrides)
    return StrategyEvidenceWeightedProbabilityAdjustmentV2Config(**values)


def forecast_input(
    **overrides: object,
) -> StrategyEvidenceWeightedProbabilityAdjustmentV2Input:
    values = {
        "forecast_id": "forecast-fed-cut-001",
        "market_slug": "fed-cut-july-2026",
        "observed_at": OBSERVED_AT,
        "raw_probability": d("0.520000"),
        "evidence_signal_probability": d("0.680000"),
        "evidence_strength": d("0.800000"),
        "source_reliability": d("0.900000"),
        "information_age_hours": d("18.000000"),
        "specialist_calibration": d("0.700000"),
        "contradiction_severity": d("0.200000"),
        "resolution_rule_clarity": d("0.850000"),
    }
    values.update(overrides)
    return StrategyEvidenceWeightedProbabilityAdjustmentV2Input(**values)


def report(
    input_row: StrategyEvidenceWeightedProbabilityAdjustmentV2Input | None = None,
    *,
    cfg: StrategyEvidenceWeightedProbabilityAdjustmentV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyEvidenceWeightedProbabilityAdjustmentV2Report:
    return build_strategy_evidence_weighted_probability_adjustment_v2_report(
        input_row or forecast_input(),
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_report_adjusts_raw_probability_with_evidence_quality_factors() -> None:
    digest_report = report()

    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.config_version == DEFAULT_CONFIG_VERSION
    assert digest_report.forecast_id == "forecast-fed-cut-001"
    assert digest_report.market_slug == "fed-cut-july-2026"
    assert digest_report.observed_at == OBSERVED_AT
    assert digest_report.raw_probability == d("0.520000")
    assert digest_report.evidence_signal_probability == d("0.680000")
    assert digest_report.information_recency_score == d("0.750000")
    assert digest_report.support_score == d("0.802500")
    assert digest_report.contradiction_drag == d("0.200000")
    assert digest_report.adjustment_weight == d("0.642000")
    assert digest_report.probability_delta == d("0.102720")
    assert digest_report.adjusted_probability == d("0.622720")
    assert digest_report.assessment_status == "pass"
    assert digest_report.reason_codes == (
        "evidence_strong",
        "source_reliable",
        "information_fresh",
        "specialist_calibrated",
        "contradiction_low",
        "resolution_rule_clear",
        "probability_adjusted_up",
    )
    assert len(digest_report.derived_validation_digest) == 64
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_report_can_reject_weak_stale_contradicted_inputs() -> None:
    weak_report = report(
        forecast_input(
            raw_probability=d("0.700000"),
            evidence_signal_probability=d("0.200000"),
            evidence_strength=d("0.200000"),
            source_reliability=d("0.300000"),
            information_age_hours=d("100.000000"),
            specialist_calibration=d("0.300000"),
            contradiction_severity=d("0.800000"),
            resolution_rule_clarity=d("0.200000"),
        ),
    )

    assert weak_report.information_recency_score == d("0.000000")
    assert weak_report.support_score == d("0.210000")
    assert weak_report.contradiction_drag == d("0.800000")
    assert weak_report.adjustment_weight == d("0.042000")
    assert weak_report.probability_delta == d("-0.021000")
    assert weak_report.adjusted_probability == d("0.679000")
    assert weak_report.assessment_status == "reject"
    assert weak_report.reason_codes == (
        "evidence_weak",
        "source_uncertain",
        "information_stale",
        "specialist_uncertain",
        "contradiction_high",
        "resolution_rule_ambiguous",
        "probability_adjusted_down",
    )


def test_payload_serializes_decimal_strings_and_validates_digest() -> None:
    digest_report = report(
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = strategy_evidence_weighted_probability_adjustment_v2_payload(digest_report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["observed_at"] == "2026-07-06T10:00:00+00:00"
    assert payload["raw_probability"] == "0.520000"
    assert payload["support_score"] == "0.802500"
    assert payload["adjusted_probability"] == "0.622720"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert strategy_evidence_weighted_probability_adjustment_v2_payload(payload) == payload
    assert not _contains_float(payload)


def test_derived_validation_digest_rejects_tampered_report_and_payload() -> None:
    digest_report = report()
    payload = strategy_evidence_weighted_probability_adjustment_v2_payload(digest_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest_report, adjusted_probability=d("0.620000"))

    tampered_payload = dict(payload)
    tampered_payload["adjusted_probability"] = "0.620000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_evidence_weighted_probability_adjustment_v2_payload(tampered_payload)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_evidence_weighted_probability_adjustment_v2_payload(tampered_digest)


def test_validates_decimal_only_flags_times_and_frozen_dataclasses() -> None:
    digest_report = report()

    with pytest.raises(FrozenInstanceError):
        digest_report.adjusted_probability = d("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="raw_probability must be a Decimal"):
        forecast_input(raw_probability=0.52)

    with pytest.raises(ValueError, match="raw_probability must be a Decimal"):
        forecast_input(raw_probability=_DecimalSubclass("0.520000"))

    with pytest.raises(ValueError, match="raw_probability must be finite"):
        forecast_input(raw_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        forecast_input(observed_at=datetime(2026, 7, 6, 10, 0))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(ValueError, match="forecast_input must be readonly"):
        forecast_input(readonly=False)

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)


def test_rejects_unsafe_public_payload_keys_values_and_float_values() -> None:
    payload = strategy_evidence_weighted_probability_adjustment_v2_payload(report())

    downgraded_payload = dict(payload)
    downgraded_payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        strategy_evidence_weighted_probability_adjustment_v2_payload(downgraded_payload)

    float_payload = dict(payload)
    float_payload["support_score"] = 0.5
    with pytest.raises(ValueError, match="float"):
        strategy_evidence_weighted_probability_adjustment_v2_payload(float_payload)


@pytest.mark.parametrize(
    "unsafe_value",
    (
        _unsafe_term("li", "ve"),
        _unsafe_term("au", "th"),
        _unsafe_term("wal", "let"),
        _unsafe_term("or", "der"),
        _unsafe_term("net", "work"),
        _unsafe_term("data", "base"),
        _unsafe_term("pers", "ist"),
        _unsafe_term("sign", "ing"),
        _unsafe_term("muta", "tion"),
        _unsafe_term("b", "uy"),
        _unsafe_term("se", "ll"),
        _unsafe_term("tra", "de"),
    ),
)
def test_rejects_each_unsafe_public_payload_key_and_value(
    unsafe_value: str,
) -> None:
    payload = strategy_evidence_weighted_probability_adjustment_v2_payload(report())

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[unsafe_value] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        strategy_evidence_weighted_probability_adjustment_v2_payload(unsafe_key_payload)

    unsafe_text_payload = dict(payload)
    unsafe_text_payload["forecast_id"] = f"uses-{unsafe_value}"
    with pytest.raises(ValueError, match="unsafe public value"):
        strategy_evidence_weighted_probability_adjustment_v2_payload(unsafe_text_payload)


@pytest.mark.parametrize(
    ("overrides", "match"),
    (
        ({"forecast_id": ""}, "forecast_id"),
        ({"market_slug": " fed-cut "}, "market_slug"),
        ({"raw_probability": d("1.100000")}, "raw_probability"),
        ({"evidence_signal_probability": d("-0.100000")}, "evidence_signal_probability"),
        ({"information_age_hours": d("-1.000000")}, "information_age_hours"),
        ({"contradiction_severity": d("1.100000")}, "contradiction_severity"),
    ),
)
def test_validates_forecast_input_values(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        forecast_input(**overrides)


@pytest.mark.parametrize(
    ("overrides", "match"),
    (
        ({"max_information_age_hours": d("0.000000")}, "max_information_age_hours"),
        ({"max_probability_adjustment": d("0.000000")}, "max_probability_adjustment"),
        ({"evidence_strength_weight": d("0.300000")}, "support weights"),
        ({"pass_adjustment_weight": d("0.200000")}, "pass_adjustment_weight"),
        ({"contradiction_penalty_multiplier": d("1.100000")}, "contradiction"),
    ),
)
def test_validates_config_values(overrides: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        config(**overrides)


def test_module_scope_has_no_forbidden_calls_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_evidence_weighted_probability_adjustment_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
