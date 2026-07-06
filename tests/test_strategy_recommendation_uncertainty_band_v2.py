from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_recommendation_uncertainty_band_v2 import (
    CandidateRecommendationUncertaintyBandV2,
    StrategyRecommendationUncertaintyBandV2Config,
    build_strategy_recommendation_uncertainty_band_v2_report,
    strategy_recommendation_uncertainty_band_v2_payload,
    validate_strategy_recommendation_uncertainty_band_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def _config(**overrides: object) -> StrategyRecommendationUncertaintyBandV2Config:
    values: dict[str, object] = {
        "config_version": "phase1_uncertainty_band_v2",
        "min_uncertainty_adjusted_edge": Decimal("0.020000"),
        "max_uncertainty_width": Decimal("0.080000"),
        "min_confidence": Decimal("0.650000"),
        "max_capital_lockup_ratio": Decimal("0.500000"),
        "forecast_dispersion_weight": Decimal("0.300000"),
        "source_reliability_weight": Decimal("0.050000"),
        "evidence_freshness_weight": Decimal("0.050000"),
        "contradiction_severity_weight": Decimal("0.050000"),
        "liquidity_exit_risk_weight": Decimal("0.050000"),
        "resolution_risk_weight": Decimal("0.050000"),
        "specialist_quorum_weight": Decimal("0.050000"),
        "capital_lockup_weight": Decimal("0.025000"),
    }
    values.update(overrides)
    return StrategyRecommendationUncertaintyBandV2Config(**values)


def _candidate(**overrides: object) -> CandidateRecommendationUncertaintyBandV2:
    values: dict[str, object] = {
        "candidate_id": "rec-alpha",
        "market_slug": "market-alpha",
        "side": "yes",
        "forecast_probability": Decimal("0.680000"),
        "implied_probability": Decimal("0.550000"),
        "confidence": Decimal("0.800000"),
        "target_notional": Decimal("100.000000"),
        "forecast_dispersion": Decimal("0.030000"),
        "source_reliability": Decimal("0.900000"),
        "evidence_freshness": Decimal("0.800000"),
        "contradiction_severity": Decimal("0.100000"),
        "liquidity_exit_risk": Decimal("0.050000"),
        "resolution_risk": Decimal("0.100000"),
        "specialist_quorum": Decimal("0.750000"),
        "capital_lockup_ratio": Decimal("0.200000"),
    }
    values.update(overrides)
    return CandidateRecommendationUncertaintyBandV2(**values)


def _report():
    return build_strategy_recommendation_uncertainty_band_v2_report(
        _candidate(),
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _walk_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        items: list[Any] = []
        for nested in value.values():
            items.extend(_walk_values(nested))
        return items
    if isinstance(value, list):
        items = []
        for nested in value:
            items.extend(_walk_values(nested))
        return items
    return [value]


def test_builds_decimal_only_uncertainty_band_report_payload() -> None:
    report = _report()

    assert report.raw_edge == Decimal("0.130000")
    assert report.confidence_adjusted_edge == Decimal("0.104000")
    assert report.forecast_dispersion_penalty == Decimal("0.009000")
    assert report.source_reliability_penalty == Decimal("0.005000")
    assert report.evidence_freshness_penalty == Decimal("0.010000")
    assert report.contradiction_severity_penalty == Decimal("0.005000")
    assert report.liquidity_exit_risk_penalty == Decimal("0.002500")
    assert report.resolution_risk_penalty == Decimal("0.005000")
    assert report.specialist_quorum_penalty == Decimal("0.012500")
    assert report.capital_lockup_penalty == Decimal("0.005000")
    assert report.total_uncertainty_width == Decimal("0.054000")
    assert report.lower_probability_band == Decimal("0.626000")
    assert report.upper_probability_band == Decimal("0.734000")
    assert report.downside_edge == Decimal("0.076000")
    assert report.upside_edge == Decimal("0.184000")
    assert report.uncertainty_adjusted_edge == Decimal("0.050000")
    assert report.report_status == "paper_recommendable"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = strategy_recommendation_uncertainty_band_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["target_notional"] == "100.000000"
    assert payload["total_uncertainty_width"] == "0.054000"
    assert payload["uncertainty_adjusted_edge"] == "0.050000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert all(not isinstance(value, Decimal) for value in _walk_values(payload))


def test_high_uncertainty_is_reported_as_watch_when_edge_survives() -> None:
    report = build_strategy_recommendation_uncertainty_band_v2_report(
        _candidate(
            forecast_probability=Decimal("0.950000"),
            forecast_dispersion=Decimal("0.150000"),
            source_reliability=Decimal("0.400000"),
            evidence_freshness=Decimal("0.300000"),
            contradiction_severity=Decimal("0.500000"),
            liquidity_exit_risk=Decimal("0.600000"),
            resolution_risk=Decimal("0.500000"),
            specialist_quorum=Decimal("0.400000"),
            capital_lockup_ratio=Decimal("0.700000"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.total_uncertainty_width == Decimal("0.237500")
    assert report.upper_probability_band == Decimal("1.000000")
    assert report.width_status == "width_watch"
    assert report.lockup_status == "lockup_watch"
    assert report.edge_status == "edge_pass"
    assert report.report_status == "paper_watch"
    assert "uncertainty_width_above_limit" in report.reason_codes
    assert "capital_lockup_above_limit" in report.reason_codes


def test_low_uncertainty_adjusted_edge_is_reported_as_reject() -> None:
    report = build_strategy_recommendation_uncertainty_band_v2_report(
        _candidate(forecast_probability=Decimal("0.590000")),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.raw_edge == Decimal("0.040000")
    assert report.uncertainty_adjusted_edge == Decimal("-0.022000")
    assert report.edge_status == "edge_reject"
    assert report.report_status == "paper_reject"
    assert "uncertainty_adjusted_edge_below_minimum" in report.reason_codes


def test_rejects_non_decimal_numeric_inputs() -> None:
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        _candidate(forecast_probability=0.68)

    with pytest.raises(ValueError, match="target_notional must be a Decimal"):
        _candidate(target_notional=100)

    with pytest.raises(ValueError, match="public payload value must not use native numeric types"):
        validate_strategy_recommendation_uncertainty_band_v2_public_payload(
            {
                "safe_reference": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.report_status = "paper_watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        StrategyRecommendationUncertaintyBandV2Config(
            config_version="phase1_uncertainty_band_v2",
            min_uncertainty_adjusted_edge=Decimal("0.020000"),
            max_uncertainty_width=Decimal("0.080000"),
            min_confidence=Decimal("0.650000"),
            max_capital_lockup_ratio=Decimal("0.500000"),
            forecast_dispersion_weight=Decimal("0.300000"),
            source_reliability_weight=Decimal("0.050000"),
            evidence_freshness_weight=Decimal("0.050000"),
            contradiction_severity_weight=Decimal("0.050000"),
            liquidity_exit_risk_weight=Decimal("0.050000"),
            resolution_risk_weight=Decimal("0.050000"),
            specialist_quorum_weight=Decimal("0.050000"),
            capital_lockup_weight=Decimal("0.025000"),
            paper_only=False,
        )

    payload = strategy_recommendation_uncertainty_band_v2_payload(report)
    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        validate_strategy_recommendation_uncertainty_band_v2_public_payload(payload)


def test_payload_rejects_derived_validation_digest_tampering() -> None:
    report = _report()
    object.__setattr__(report, "uncertainty_adjusted_edge", Decimal("0.990000"))

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        strategy_recommendation_uncertainty_band_v2_payload(report)

    payload = strategy_recommendation_uncertainty_band_v2_payload(_report())
    payload["uncertainty_adjusted_edge"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        validate_strategy_recommendation_uncertainty_band_v2_public_payload(payload)


def test_rejects_unsafe_public_keys_and_values() -> None:
    with pytest.raises(ValueError, match="candidate_id has unsafe value"):
        _candidate(candidate_id="live-alpha")

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
    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="public payload key has unsafe value"):
            validate_strategy_recommendation_uncertainty_band_v2_public_payload(
                {f"{unsafe_term}_reference": "safe"},
            )
        with pytest.raises(ValueError, match="public payload value has unsafe value"):
            validate_strategy_recommendation_uncertainty_band_v2_public_payload(
                {"safe_reference": f"paper {unsafe_term}"},
            )
