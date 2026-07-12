from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_liquidity_cost_curve_readiness_report"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def report_input(**overrides: object) -> Any:
    module = api()
    values = {
        "small_size_cost_probability": d("0.010000"),
        "medium_size_cost_probability": d("0.020000"),
        "large_size_cost_probability": d("0.030000"),
        "depth_decay_probability": d("0.100000"),
        "max_acceptable_cost_probability": d("0.050000"),
    }
    values.update(overrides)
    return module.ProbabilityEventLiquidityCostCurveReadinessInput(**values)


def build_report(**overrides: object) -> Any:
    module = api()
    return module.build_probability_event_liquidity_cost_curve_readiness_report(
        report_input(**overrides),
    )


def assert_decimal_only(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_payload_has_no_runtime_numbers(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_has_no_runtime_numbers(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_has_no_runtime_numbers(child)


def test_pass_curve_recommends_large_manual_band_and_public_payload() -> None:
    module = api()

    report = build_report()

    assert isinstance(report, module.ProbabilityEventLiquidityCostCurveReadinessReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.curve_status == "pass"
    assert report.recommended_manual_size_band == "large"
    assert report.reason_codes == ("liquidity_cost_curve_pass",)
    assert report.manual_next_step == "document_large_band_for_manual_phase1_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only(report)

    payload = report.public_payload
    assert payload == module.probability_event_liquidity_cost_curve_readiness_report_payload(
        report,
    )
    assert payload["small_size_cost_probability"] == "0.010000"
    assert payload["medium_size_cost_probability"] == "0.020000"
    assert payload["large_size_cost_probability"] == "0.030000"
    assert payload["depth_decay_probability"] == "0.100000"
    assert payload["max_acceptable_cost_probability"] == "0.050000"
    assert payload["curve_status"] == "pass"
    assert payload["recommended_manual_size_band"] == "large"
    assert payload["reason_codes"] == ["liquidity_cost_curve_pass"]
    assert payload["manual_next_step"] == (
        "document_large_band_for_manual_phase1_review"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == report.payload_digest
    assert module.probability_event_liquidity_cost_curve_readiness_report_digest(
        report,
    ).endswith(report.payload_digest + ")")
    assert_payload_has_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["curve_status"] = "blocked"


def test_watch_curve_recommends_medium_band_when_large_cost_is_too_high() -> None:
    report = build_report(
        large_size_cost_probability=d("0.070000"),
        depth_decay_probability=d("0.180000"),
    )

    assert report.curve_status == "watch"
    assert report.recommended_manual_size_band == "medium"
    assert report.reason_codes == (
        "liquidity_cost_curve_watch",
        "large_size_cost_above_limit",
    )
    assert report.manual_next_step == "manually_review_medium_band_cost_curve"


def test_block_curve_recommends_none_when_small_cost_or_depth_decay_blocks() -> None:
    small_cost_block = build_report(
        small_size_cost_probability=d("0.060000"),
        medium_size_cost_probability=d("0.070000"),
        large_size_cost_probability=d("0.080000"),
    )

    assert small_cost_block.curve_status == "blocked"
    assert small_cost_block.recommended_manual_size_band == "none"
    assert small_cost_block.reason_codes == (
        "liquidity_cost_curve_blocked",
        "small_size_cost_above_limit",
        "medium_size_cost_above_limit",
        "large_size_cost_above_limit",
    )
    assert small_cost_block.manual_next_step == (
        "do_not_use_curve_until_manual_liquidity_cost_review"
    )

    depth_block = build_report(depth_decay_probability=d("0.410000"))
    assert depth_block.curve_status == "blocked"
    assert depth_block.recommended_manual_size_band == "none"
    assert depth_block.reason_codes == (
        "liquidity_cost_curve_blocked",
        "depth_decay_probability_blocked",
    )


def test_validation_rejects_non_decimal_nonfinite_granular_flags_and_derived_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="small_size_cost_probability must be exactly Decimal"):
        report_input(small_size_cost_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="medium_size_cost_probability must be exactly Decimal"):
        report_input(medium_size_cost_probability=0.02)
    with pytest.raises(ValueError, match="large_size_cost_probability must be finite"):
        report_input(large_size_cost_probability=d("NaN"))
    with pytest.raises(ValueError, match="depth_decay_probability must be between 0 and 1"):
        report_input(depth_decay_probability=d("1.100000"))
    with pytest.raises(ValueError, match="max_acceptable_cost_probability precision is too granular"):
        report_input(max_acceptable_cost_probability=d("0.0500001"))
    with pytest.raises(ValueError, match="input paper_only must be True"):
        report_input(paper_only=False)
    with pytest.raises(ValueError, match="inputs must be a ProbabilityEventLiquidityCostCurveReadinessInput"):
        module.build_probability_event_liquidity_cost_curve_readiness_report(object())

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.curve_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="curve_status must match inputs"):
        replace(report, curve_status="watch")
    with pytest.raises(ValueError, match="recommended_manual_size_band must match"):
        replace(report, recommended_manual_size_band="small")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(report, reason_codes=("liquidity_cost_curve_watch",))
    with pytest.raises(ValueError, match="manual_next_step must match"):
        replace(report, manual_next_step="manual_review_medium_band_cost_curve")
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="payload_digest must match"):
        replace(report, payload_digest="0" * 64)


def test_report_only_module_exposes_no_execution_or_persistence_surface() -> None:
    module = api()
    forbidden_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "keys",
        "sign",
        "signature",
        "auto",
        "execute",
        "execution",
        "jsonl",
        "persist",
    )

    public_names = tuple(name.lower() for name in module.__all__)
    assert not any(
        term in public_name
        for public_name in public_names
        for term in forbidden_terms
    )

    payload = build_report().public_payload
    serialized = json.dumps(payload, sort_keys=True).lower()
    assert "only" in serialized
    assert not any(term in serialized for term in forbidden_terms)
