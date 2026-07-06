from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_event_resolution_uncertainty_band_v10 import (
    RULE_CHANGE_CONFIRMED,
    RULE_CHANGE_NONE,
    RULE_CHANGE_PROPOSED,
    StrategyEventResolutionUncertaintyBandV10Input,
    StrategyEventResolutionUncertaintyBandV10Result,
    evaluate_strategy_event_resolution_uncertainty_band_v10,
    strategy_event_resolution_uncertainty_band_v10_payload,
)


def _resolution_input(**overrides):
    values = {
        "market_id": "market_resolution_2026_07",
        "resolution_ambiguity_score": Decimal("0.640000"),
        "precedent_score": Decimal("0.300000"),
        "rule_change_status": RULE_CHANGE_PROPOSED,
        "source_disagreement_score": Decimal("0.720000"),
        "time_to_resolution_minutes": Decimal("180.000000"),
        "historical_dispute_rate": Decimal("0.120000"),
        "reason_codes": ("manual_resolution_review",),
    }
    values.update(overrides)
    return StrategyEventResolutionUncertaintyBandV10Input(**values)


def test_event_resolution_uncertainty_band_flags_high_ambiguity_pressure():
    result = evaluate_strategy_event_resolution_uncertainty_band_v10(_resolution_input())

    assert isinstance(result, StrategyEventResolutionUncertaintyBandV10Result)
    assert result.market_id == "market_resolution_2026_07"
    assert result.uncertainty_status == "elevated"
    assert result.lower_confidence_adjustment_bps == Decimal("-4030.000000")
    assert result.upper_confidence_adjustment_bps == Decimal("2015.000000")
    assert result.reason_codes == (
        "manual_resolution_review",
        "event_resolution_uncertainty_band_v10",
        "ambiguity_score_elevated",
        "source_disagreement_elevated",
        "rule_change_proposed",
        "short_time_to_resolution",
        "historical_dispute_rate_elevated",
        "uncertainty_elevated",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == strategy_event_resolution_uncertainty_band_v10_payload(result)


def test_event_resolution_uncertainty_band_blocks_extreme_rule_conflict():
    result = evaluate_strategy_event_resolution_uncertainty_band_v10(
        _resolution_input(
            resolution_ambiguity_score=Decimal("0.900000"),
            precedent_score=Decimal("0.000000"),
            rule_change_status=RULE_CHANGE_CONFIRMED,
            source_disagreement_score=Decimal("0.900000"),
            time_to_resolution_minutes=Decimal("45.000000"),
            historical_dispute_rate=Decimal("0.250000"),
            reason_codes=(),
        ),
    )

    assert result.uncertainty_status == "block"
    assert result.lower_confidence_adjustment_bps == Decimal("-8000.000000")
    assert result.upper_confidence_adjustment_bps == Decimal("4000.000000")
    assert "rule_change_confirmed" in result.reason_codes
    assert "uncertainty_block" in result.reason_codes


def test_event_resolution_uncertainty_band_keeps_clear_precedent_status_ok():
    result = evaluate_strategy_event_resolution_uncertainty_band_v10(
        _resolution_input(
            resolution_ambiguity_score=Decimal("0.100000"),
            precedent_score=Decimal("0.900000"),
            rule_change_status=RULE_CHANGE_NONE,
            source_disagreement_score=Decimal("0.050000"),
            time_to_resolution_minutes=Decimal("4320.000000"),
            historical_dispute_rate=Decimal("0.010000"),
            reason_codes=(),
        ),
    )

    assert result.uncertainty_status == "ok"
    assert result.lower_confidence_adjustment_bps == Decimal("-420.000000")
    assert result.upper_confidence_adjustment_bps == Decimal("210.000000")
    assert result.reason_codes == (
        "event_resolution_uncertainty_band_v10",
        "strong_precedent_support",
        "uncertainty_ok",
    )


def test_event_resolution_uncertainty_band_uses_decimal_inputs_and_validates_ranges():
    with pytest.raises(ValueError, match="resolution_ambiguity_score must be a Decimal"):
        _resolution_input(resolution_ambiguity_score=0.64)

    with pytest.raises(ValueError, match="precedent_score must be between 0 and 1"):
        _resolution_input(precedent_score=Decimal("1.000001"))

    with pytest.raises(ValueError, match="rule_change_status must be"):
        _resolution_input(rule_change_status="pending")

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        _resolution_input(time_to_resolution_minutes=Decimal("-0.000001"))

    with pytest.raises(ValueError, match="market_id must be a canonical nonblank string"):
        _resolution_input(market_id=" market_resolution_2026_07")


def test_event_resolution_uncertainty_band_requires_tuple_reasons_and_hard_flags():
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _resolution_input(reason_codes=["manual_resolution_review"])

    with pytest.raises(ValueError, match="paper_only must be True"):
        _resolution_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        _resolution_input(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _resolution_input(readonly=False)


def test_event_resolution_uncertainty_band_dataclasses_are_frozen():
    source = _resolution_input()
    result = evaluate_strategy_event_resolution_uncertainty_band_v10(source)

    with pytest.raises(FrozenInstanceError):
        source.market_id = "other_market"

    with pytest.raises(FrozenInstanceError):
        result.uncertainty_status = "ok"


def test_event_resolution_uncertainty_band_payload_is_json_ready_readonly_report():
    result = evaluate_strategy_event_resolution_uncertainty_band_v10(_resolution_input())
    payload = strategy_event_resolution_uncertainty_band_v10_payload(result)

    assert payload == result.payload
    assert payload["market_id"] == "market_resolution_2026_07"
    assert payload["resolution_ambiguity_score"] == "0.640000"
    assert payload["precedent_score"] == "0.300000"
    assert payload["rule_change_status"] == RULE_CHANGE_PROPOSED
    assert payload["source_disagreement_score"] == "0.720000"
    assert payload["time_to_resolution_minutes"] == "180.000000"
    assert payload["historical_dispute_rate"] == "0.120000"
    assert payload["uncertainty_status"] == "elevated"
    assert payload["lower_confidence_adjustment_bps"] == "-4030.000000"
    assert payload["upper_confidence_adjustment_bps"] == "2015.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    unsafe = object.__new__(StrategyEventResolutionUncertaintyBandV10Result)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_event_resolution_uncertainty_band_v10_payload(unsafe)
