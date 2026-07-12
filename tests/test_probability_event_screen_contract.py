from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module

import pytest

import polymarket_alpha_lab.probability_event_screen_contract as contract_module
from polymarket_alpha_lab.probability_event_screen_contract import (
    ProbabilityEventScreen,
    validate_probability_event_screen_public_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def screen(**overrides: object) -> ProbabilityEventScreen:
    values = {
        "generated_at": GENERATED_AT,
        "event_ref": "event-alpha",
        "market_ref": "market-alpha-yes-no",
        "yes_executable_probability": d("0.560000"),
        "yes_executable_price": d("0.560000"),
        "no_executable_probability": d("0.440000"),
        "no_executable_price": d("0.440000"),
        "forecast_probability": d("0.630000"),
        "market_probability": d("0.560000"),
        "gross_edge_probability": d("0.070000"),
        "total_cost_probability": d("0.020000"),
        "cost_adjusted_threshold_probability": d("0.580000"),
        "edge_to_threshold_probability": d("0.050000"),
        "liquidity_probability": d("0.900000"),
        "depth_probability": d("0.820000"),
        "spread_probability": d("0.020000"),
        "resolution_risk_readiness": "ready",
        "settlement_risk_readiness": "ready",
        "source_quality_status": "ready",
        "specialist_team_route": "macro",
        "memory_policy_status": "ready",
        "manual_next_step": "manual_review",
    }
    values.update(overrides)
    return ProbabilityEventScreen(**values)


def test_ready_screen_freezes_canonical_public_payload_digest_and_validation() -> None:
    result = screen()

    assert is_dataclass(result)
    assert result.status == "ready"
    assert result.direction == "yes"
    assert result.gross_edge_probability == d("0.070000")
    assert result.edge_to_threshold_probability == d("0.050000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.public_payload
    assert payload["status"] == "ready"
    assert payload["direction"] == "yes"
    assert payload["yes_executable_probability"] == "0.560000"
    assert payload["no_executable_price"] == "0.440000"
    assert payload["forecast_probability"] == "0.630000"
    assert payload["digest"] == result.digest
    assert validate_probability_event_screen_public_payload(payload) == payload

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["status"] = "changed"

    with pytest.raises(FrozenInstanceError):
        result.status = "attention"  # type: ignore[misc]


def test_attention_screen_rolls_up_non_blocking_readiness_and_quality_flags() -> None:
    result = screen(
        liquidity_probability=d("0.480000"),
        resolution_risk_readiness="attention",
        source_quality_status="attention",
        memory_policy_status="attention",
        manual_next_step="refresh_sources",
    )

    assert result.status == "attention"
    assert result.reason_codes == (
        "liquidity_depth_attention",
        "memory_policy_attention",
        "resolution_risk_attention",
        "source_quality_attention",
    )
    assert result.public_payload["manual_next_step"] == "refresh_sources"


def test_blocker_screen_rolls_up_cost_edge_depth_and_risk_blockers() -> None:
    result = screen(
        forecast_probability=d("0.590000"),
        gross_edge_probability=d("0.030000"),
        total_cost_probability=d("0.040000"),
        cost_adjusted_threshold_probability=d("0.600000"),
        edge_to_threshold_probability=d("-0.010000"),
        depth_probability=d("0.090000"),
        spread_probability=d("0.130000"),
        settlement_risk_readiness="blocker",
        manual_next_step="do_not_trade_refresh_resolution_evidence",
    )

    assert result.status == "blocker"
    assert result.reason_codes == (
        "depth_blocker",
        "edge_below_cost_adjusted_threshold",
        "gross_edge_does_not_cover_total_cost",
        "settlement_risk_blocker",
        "spread_blocker",
    )


def test_direction_consistency_requires_yes_market_probability_and_no_complement() -> None:
    yes = screen()
    assert yes.direction == "yes"

    no = screen(
        yes_executable_probability=d("0.650000"),
        yes_executable_price=d("0.650000"),
        no_executable_probability=d("0.350000"),
        no_executable_price=d("0.350000"),
        forecast_probability=d("0.410000"),
        market_probability=d("0.650000"),
        gross_edge_probability=d("0.240000"),
        total_cost_probability=d("0.030000"),
        cost_adjusted_threshold_probability=d("0.620000"),
        edge_to_threshold_probability=d("0.210000"),
    )
    assert no.direction == "no"

    with pytest.raises(
        ValueError,
        match="no_executable_probability must equal 1 - yes_executable_probability",
    ):
        screen(no_executable_probability=d("0.430000"))

    with pytest.raises(
        ValueError,
        match="gross_edge_probability must match the selected direction",
    ):
        screen(gross_edge_probability=d("0.010000"))


def test_rejects_non_decimal_public_numbers_and_phase_flag_changes() -> None:
    for field in fields(ProbabilityEventScreen):
        if field.type is Decimal:
            with pytest.raises(ValueError, match=f"{field.name} must be exactly Decimal"):
                screen(**{field.name: "0.100000"})

    with pytest.raises(ValueError, match="paper_only must be True"):
        screen(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        screen(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        screen(readonly=False)


def test_module_has_no_live_execution_hook_surface() -> None:
    source = inspect.getsource(contract_module).lower()

    forbidden_terms = (
        "requests",
        "httpx",
        "web3",
        "wallet",
        "private key",
        "private_key",
        "api key",
        "api_key",
        "authentication",
        "authorization",
        "auth",
        "sign_order",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "order execution",
        "live trading",
        "live_trading",
    )
    assert all(term not in source for term in forbidden_terms)

    api_names = dir(import_module("polymarket_alpha_lab.probability_event_screen_contract"))
    forbidden_api_fragments = ("wallet", "auth", "order", "trade", "execute", "submit")
    assert not [
        name
        for name in api_names
        if any(fragment in name.lower() for fragment in forbidden_api_fragments)
    ]
