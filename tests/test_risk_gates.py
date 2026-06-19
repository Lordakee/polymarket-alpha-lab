from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import pytest

from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet
from polymarket_alpha_lab.risk import (
    RiskGateConfig,
    RiskGateDecision,
    RiskGateReason,
    evaluate_research_packet_risk,
)


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("0.026"),
        "confidence": Decimal("0.60"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def test_risk_gate_accepts_packet_that_meets_config():
    decision = evaluate_research_packet_risk(
        complete_packet(),
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is True
    assert decision.config_version == "v1"
    assert decision.reasons == ()


def test_risk_gate_rejects_invalid_public_inputs():
    with pytest.raises(ValueError, match="packet"):
        evaluate_research_packet_risk(
            object(),
            RiskGateConfig(config_version="v1"),
        )
    with pytest.raises(ValueError, match="config"):
        evaluate_research_packet_risk(
            complete_packet(),
            object(),
        )


def test_risk_gate_rejects_with_deterministic_reason_codes():
    packet = complete_packet(
        strategy_type="experimental",
        confidence=Decimal("0.40"),
        cost_adjusted_edge=Decimal("-0.01"),
        spread=Decimal("0.20"),
        slippage_estimate=Decimal("0.05"),
        max_executable_size=Decimal("0.5"),
        risk_tags=("rules", "blocked-theme", "blocked-second"),
    )
    config = RiskGateConfig(
        config_version="v2",
        min_confidence=Decimal("0.55"),
        min_cost_adjusted_edge=Decimal("0.01"),
        max_spread=Decimal("0.05"),
        max_slippage_estimate=Decimal("0.01"),
        min_max_executable_size=Decimal("1"),
        allowed_strategy_types=("market_quality",),
        blocked_risk_tags=("blocked-theme", "blocked-second"),
    )

    decision = evaluate_research_packet_risk(packet, config)

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == [
        "strategy_not_allowed",
        "blocked_risk_tag",
        "blocked_risk_tag",
        "low_confidence",
        "low_cost_adjusted_edge",
        "wide_spread",
        "high_slippage",
        "insufficient_executable_size",
    ]
    assert decision.reasons[0].field_name == "strategy_type"
    assert decision.reasons[1].observed_value == "blocked-theme"
    assert decision.reasons[2].observed_value == "blocked-second"
    assert decision.reasons[3].observed_value == Decimal("0.40")
    assert decision.reasons[3].threshold == Decimal("0.55")


def test_risk_gate_reports_incomplete_packet_before_numeric_gates():
    packet = complete_packet(
        confidence=None,
        cost_adjusted_edge=Decimal("NaN"),
        risk_tags=(),
    )

    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == ["incomplete_packet"]
    assert decision.reasons[0].field_name == "missing_required_fields"
    assert "confidence" in str(decision.reasons[0].observed_value)
    assert "cost_adjusted_edge" in str(decision.reasons[0].observed_value)
    assert "risk_tags" in str(decision.reasons[0].observed_value)


@pytest.mark.parametrize(
    "field_name",
    [
        "confidence",
        "cost_adjusted_edge",
        "spread",
        "slippage_estimate",
        "max_executable_size",
    ],
)
def test_risk_gate_treats_non_decimal_numeric_gate_fields_as_incomplete(field_name):
    packet = replace(complete_packet(), **{field_name: cast(Any, "0.60")})

    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    observed = str(decision.reasons[0].observed_value)
    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == ["incomplete_packet"]
    assert field_name in observed
    if field_name == "max_executable_size":
        assert "positive_max_executable_size" not in observed


def test_risk_gate_treats_nonpositive_executable_size_as_incomplete_packet():
    packet = complete_packet(max_executable_size=Decimal("0"))

    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == ["incomplete_packet"]
    observed = str(decision.reasons[0].observed_value)
    assert "max_executable_size" in observed
    assert "positive_max_executable_size" not in observed


def test_risk_gate_accepts_threshold_equal_values():
    config = RiskGateConfig(
        config_version="v1",
        min_confidence=Decimal("0.60"),
        min_cost_adjusted_edge=Decimal("0.026"),
        max_spread=Decimal("0.02"),
        max_slippage_estimate=Decimal("0.004"),
        min_max_executable_size=Decimal("100"),
    )

    decision = evaluate_research_packet_risk(complete_packet(), config)

    assert decision.accepted is True
    assert decision.reasons == ()


def test_risk_gate_config_normalizes_sequences_to_tuples():
    config = RiskGateConfig(
        config_version="v1",
        allowed_strategy_types=["market_quality"],
        blocked_risk_tags=["rules"],
    )

    assert config.allowed_strategy_types == ("market_quality",)
    assert config.blocked_risk_tags == ("rules",)


@pytest.mark.parametrize(
    "config_kwargs",
    [
        {"config_version": "v1", "min_confidence": Decimal("NaN")},
        {"config_version": "v1", "min_confidence": "0.50"},
        {"config_version": "v1", "min_confidence": Decimal("-0.01")},
        {"config_version": "v1", "min_confidence": Decimal("1.01")},
        {"config_version": "v1", "min_cost_adjusted_edge": Decimal("Infinity")},
        {"config_version": "v1", "max_spread": Decimal("NaN")},
        {"config_version": "v1", "max_spread": Decimal("0")},
        {"config_version": "v1", "max_slippage_estimate": Decimal("Infinity")},
        {"config_version": "v1", "max_slippage_estimate": Decimal("-0.01")},
        {"config_version": "v1", "min_max_executable_size": Decimal("-Infinity")},
        {"config_version": "v1", "min_max_executable_size": Decimal("0")},
        {"config_version": "v1", "allowed_strategy_types": "market_quality"},
        {"config_version": "v1", "allowed_strategy_types": b"market_quality"},
        {"config_version": "v1", "allowed_strategy_types": (123,)},
        {"config_version": "v1", "allowed_strategy_types": ("market_quality", " ")},
        {"config_version": "v1", "blocked_risk_tags": "liquidity"},
        {"config_version": "v1", "blocked_risk_tags": b"liquidity"},
        {"config_version": "v1", "blocked_risk_tags": (123,)},
        {"config_version": "v1", "blocked_risk_tags": ("liquidity", "")},
        {"config_version": " "},
        {"config_version": 123},
    ],
)
def test_risk_gate_config_rejects_invalid_values(config_kwargs):
    with pytest.raises(ValueError):
        RiskGateConfig(**config_kwargs)


def test_risk_gate_decision_rejects_invalid_states():
    reason = RiskGateReason(
        code="low_confidence",
        message="confidence is below minimum",
        field_name="confidence",
        observed_value=Decimal("0.40"),
        threshold=Decimal("0.55"),
    )

    with pytest.raises(ValueError, match="accepted"):
        RiskGateDecision(accepted=True, config_version="v1", reasons=(reason,))
    with pytest.raises(ValueError, match="rejected"):
        RiskGateDecision(accepted=False, config_version="v1", reasons=())
    with pytest.raises(ValueError, match="reasons"):
        RiskGateDecision(accepted=False, config_version="v1", reasons=("bad",))
    with pytest.raises(ValueError, match="reasons"):
        RiskGateDecision(accepted=False, config_version="v1", reasons=None)
    with pytest.raises(ValueError, match="config_version"):
        RiskGateDecision(accepted=False, config_version=123, reasons=(reason,))
    with pytest.raises(ValueError, match="accepted"):
        RiskGateDecision(accepted="yes", config_version="v1", reasons=())


@pytest.mark.parametrize(
    "reason_kwargs",
    [
        {
            "code": "unknown_code",
            "message": "message",
            "field_name": "confidence",
        },
        {
            "code": 123,
            "message": "message",
            "field_name": "confidence",
        },
        {
            "code": "low_confidence",
            "message": 123,
            "field_name": "confidence",
        },
        {
            "code": "low_confidence",
            "message": " ",
            "field_name": "confidence",
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": 123,
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": " ",
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": "confidence",
            "observed_value": object(),
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": "confidence",
            "threshold": object(),
        },
    ],
)
def test_risk_gate_reason_rejects_invalid_public_values(reason_kwargs):
    with pytest.raises(ValueError):
        RiskGateReason(**reason_kwargs)


def test_risk_gate_is_available_from_package_root():
    import polymarket_alpha_lab as lab

    assert lab.RiskGateConfig is RiskGateConfig
    assert lab.RiskGateDecision is RiskGateDecision
    assert lab.RiskGateReason is RiskGateReason
    assert lab.evaluate_research_packet_risk is evaluate_research_packet_risk
