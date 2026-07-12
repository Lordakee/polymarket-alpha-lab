from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_event_expected_value_uncertainty_band_report import (
    ProbabilityEventExpectedValueUncertaintyBandInput,
    ProbabilityEventExpectedValueUncertaintyBandPublicPayload,
    ProbabilityEventExpectedValueUncertaintyBandReport,
    build_probability_event_expected_value_uncertainty_band_report,
    probability_event_expected_value_uncertainty_band_report_digest,
    probability_event_expected_value_uncertainty_band_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(
    *,
    forecast_probability: Decimal,
    market_probability: Decimal,
    probability_uncertainty: Decimal,
    fee_probability: Decimal,
    slippage_probability: Decimal,
    reason_codes: tuple[str, ...] = (),
) -> ProbabilityEventExpectedValueUncertaintyBandReport:
    return build_probability_event_expected_value_uncertainty_band_report(
        ProbabilityEventExpectedValueUncertaintyBandInput(
            forecast_probability=forecast_probability,
            market_probability=market_probability,
            probability_uncertainty=probability_uncertainty,
            fee_probability=fee_probability,
            slippage_probability=slippage_probability,
            reason_codes=reason_codes,
        ),
    )


def test_pass_band_when_uncertainty_adjusted_expected_value_clears_costs() -> None:
    ev_report = report(
        forecast_probability=d("0.640000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
        reason_codes=("analyst_reviewed",),
    )

    assert type(ev_report) is ProbabilityEventExpectedValueUncertaintyBandReport
    assert ev_report.config_version == (
        "probability-event-expected-value-uncertainty-band-report-v0"
    )
    assert ev_report.ev_band_status == "pass"
    assert ev_report.expected_value_low == d("0.085000")
    assert ev_report.expected_value_high == d("0.125000")
    assert ev_report.reason_codes == (
        "expected_value_uncertainty_band_pass",
        "input_analyst_reviewed",
        "manual_review_expected_value_band_pass",
        "positive_expected_value_low",
    )
    assert ev_report.manual_next_step == (
        "Record the public probability band in the local Supabase/Postgres "
        "paper evidence design notes; keep Phase 1 read-only."
    )
    assert ev_report.paper_only is True
    assert ev_report.report_only is True
    assert ev_report.readonly is True


def test_watch_and_block_bands_reflect_uncertain_or_negative_low_edge() -> None:
    watch_report = report(
        forecast_probability=d("0.560000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
    )
    block_report = report(
        forecast_probability=d("0.530000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
    )

    assert watch_report.ev_band_status == "watch"
    assert watch_report.expected_value_low == d("0.005000")
    assert watch_report.expected_value_high == d("0.045000")
    assert watch_report.reason_codes == (
        "expected_value_low_below_pass_threshold",
        "expected_value_uncertainty_band_watch",
        "manual_review_expected_value_band_watch",
        "positive_expected_value_low",
    )
    assert watch_report.manual_next_step == (
        "Manually review whether the public probability edge survives fees, "
        "slippage, and uncertainty before any later-stage decision."
    )
    assert block_report.ev_band_status == "block"
    assert block_report.expected_value_low == d("-0.025000")
    assert block_report.expected_value_high == d("0.015000")
    assert block_report.reason_codes == (
        "expected_value_low_not_positive",
        "expected_value_uncertainty_band_block",
        "manual_review_expected_value_band_block",
    )
    assert block_report.manual_next_step == (
        "Block this event from Phase 1 expected-value consideration and "
        "capture only the read-only report rationale."
    )


def test_public_payload_and_digest_are_deterministic_decimal_only_and_immutable() -> None:
    ev_report = report(
        forecast_probability=d("0.640000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
        reason_codes=("zeta", "alpha", "alpha"),
    )
    same_report = report(
        forecast_probability=d("0.640000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
        reason_codes=("alpha", "zeta"),
    )

    payload = ev_report.public_payload
    function_payload = probability_event_expected_value_uncertainty_band_report_payload(
        ev_report,
    )

    assert type(payload) is ProbabilityEventExpectedValueUncertaintyBandPublicPayload
    assert payload == function_payload
    assert payload == same_report.public_payload
    assert ev_report.payload_digest == same_report.payload_digest
    assert ev_report.payload_digest == (
        probability_event_expected_value_uncertainty_band_report_digest(ev_report)
    )
    assert len(ev_report.payload_digest) == 64
    assert payload["forecast_probability"] == "0.640000"
    assert payload["expected_value_low"] == "0.085000"
    assert payload["payload_digest"] == ev_report.payload_digest
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert ": 0." not in json.dumps(payload, sort_keys=True)
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["ev_band_status"] = "block"


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_reports() -> None:
    with pytest.raises(ValueError, match="forecast_probability"):
        ProbabilityEventExpectedValueUncertaintyBandInput(
            forecast_probability=0.64,  # type: ignore[arg-type]
            market_probability=d("0.510000"),
            probability_uncertainty=d("0.020000"),
            fee_probability=d("0.010000"),
            slippage_probability=d("0.015000"),
        )
    with pytest.raises(ValueError, match="market_probability"):
        report(
            forecast_probability=d("0.640000"),
            market_probability=_DecimalSubclass("0.510000"),
            probability_uncertainty=d("0.020000"),
            fee_probability=d("0.010000"),
            slippage_probability=d("0.015000"),
        )
    with pytest.raises(ValueError, match="probability_uncertainty"):
        report(
            forecast_probability=d("0.640000"),
            market_probability=d("0.510000"),
            probability_uncertainty=d("1.010000"),
            fee_probability=d("0.010000"),
            slippage_probability=d("0.015000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        report(
            forecast_probability=d("0.640000"),
            market_probability=d("0.510000"),
            probability_uncertainty=d("0.020000"),
            fee_probability=d("0.010000"),
            slippage_probability=d("0.015000"),
            reason_codes=("Needs Review",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            ProbabilityEventExpectedValueUncertaintyBandInput(
                forecast_probability=d("0.640000"),
                market_probability=d("0.510000"),
                probability_uncertainty=d("0.020000"),
                fee_probability=d("0.010000"),
                slippage_probability=d("0.015000"),
            ),
            paper_only=False,
        )
    ev_report = report(
        forecast_probability=d("0.640000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
    )
    with pytest.raises(ValueError, match="expected_value_low"):
        replace(ev_report, expected_value_low=d("0.080000"))
    with pytest.raises(ValueError, match="payload_digest"):
        replace(ev_report, payload_digest="0" * 64)


def test_public_dataclasses_are_frozen() -> None:
    ev_report = report(
        forecast_probability=d("0.640000"),
        market_probability=d("0.510000"),
        probability_uncertainty=d("0.020000"),
        fee_probability=d("0.010000"),
        slippage_probability=d("0.015000"),
    )

    with pytest.raises(FrozenInstanceError):
        ev_report.ev_band_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ev_report.expected_value_low = d("0")  # type: ignore[misc]


def test_owned_module_has_no_execution_surface_or_durable_file_persistence() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "probability_event_expected_value_uncertainty_band_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        ".write",
        "jsonl",
        "wallet",
        "auth",
        "private_key",
        "api_key",
        "signature",
        "sign(",
        "order",
        "submit",
        "cancel",
        "trade",
        "buy",
        "sell",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
