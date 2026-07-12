from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_cost_sensitivity_break_even_report import (
    DEFAULT_PROBABILITY_EVENT_COST_SENSITIVITY_BREAK_EVEN_REPORT_VERSION,
    ProbabilityEventCostSensitivityBreakEvenReport,
    build_probability_event_cost_sensitivity_break_even_report,
    probability_event_cost_sensitivity_break_even_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_cost_sensitivity_break_even_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(
    *,
    raw_edge_probability: Decimal = d("0.040000"),
    base_cost_probability: Decimal = d("0.010000"),
    stressed_cost_probability: Decimal = d("0.005000"),
    slippage_shock_probability: Decimal = d("0.003000"),
    uncertainty_buffer_probability: Decimal = d("0.002000"),
) -> ProbabilityEventCostSensitivityBreakEvenReport:
    return build_probability_event_cost_sensitivity_break_even_report(
        raw_edge_probability=raw_edge_probability,
        base_cost_probability=base_cost_probability,
        stressed_cost_probability=stressed_cost_probability,
        slippage_shock_probability=slippage_shock_probability,
        uncertainty_buffer_probability=uncertainty_buffer_probability,
    )


def expected_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("payload_digest")
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def term(*parts: str) -> str:
    return "".join(parts)


def test_builds_above_break_even_report_payload_and_digest() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert type(report) is ProbabilityEventCostSensitivityBreakEvenReport
    assert report.config_version == (
        DEFAULT_PROBABILITY_EVENT_COST_SENSITIVITY_BREAK_EVEN_REPORT_VERSION
    )
    assert report.raw_edge_probability == d("0.040000")
    assert report.base_cost_probability == d("0.010000")
    assert report.stressed_cost_probability == d("0.005000")
    assert report.slippage_shock_probability == d("0.003000")
    assert report.uncertainty_buffer_probability == d("0.002000")
    assert report.total_cost_probability == d("0.020000")
    assert report.cost_headroom_probability == d("0.020000")
    assert report.break_even_status == "above_break_even"
    assert report.reason_codes == (
        "probability_event_cost_sensitivity_headroom_positive",
    )
    assert report.manual_next_step == "manual_review_cost_headroom_before_paper_decision"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.payload_digest) == 64

    payload = report.public_payload
    assert probability_event_cost_sensitivity_break_even_report_payload(report) == payload
    assert payload == {
        "config_version": (
            "probability-event-cost-sensitivity-break-even-report-v0"
        ),
        "raw_edge_probability": "0.040000",
        "base_cost_probability": "0.010000",
        "stressed_cost_probability": "0.005000",
        "slippage_shock_probability": "0.003000",
        "uncertainty_buffer_probability": "0.002000",
        "total_cost_probability": "0.020000",
        "cost_headroom_probability": "0.020000",
        "break_even_status": "above_break_even",
        "reason_codes": (
            "probability_event_cost_sensitivity_headroom_positive",
        ),
        "manual_next_step": "manual_review_cost_headroom_before_paper_decision",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }
    assert payload["payload_digest"] == expected_digest(payload)


def test_classifies_exact_and_below_break_even_risk() -> None:
    exact = build_report(raw_edge_probability=d("0.020000"))
    below = build_report(raw_edge_probability=d("0.015000"))

    assert exact.total_cost_probability == d("0.020000")
    assert exact.cost_headroom_probability == d("0.000000")
    assert exact.break_even_status == "at_break_even"
    assert exact.reason_codes == (
        "probability_event_cost_sensitivity_headroom_zero",
    )
    assert exact.manual_next_step == "manual_review_zero_headroom_before_paper_decision"

    assert below.total_cost_probability == d("0.020000")
    assert below.cost_headroom_probability == d("-0.005000")
    assert below.break_even_status == "below_break_even"
    assert below.reason_codes == (
        "probability_event_cost_sensitivity_headroom_negative",
    )
    assert below.manual_next_step == "manual_reprice_cost_assumptions_before_paper_decision"


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("raw_edge_probability", 1),
        ("base_cost_probability", 0.1),
        ("stressed_cost_probability", "0.010000"),
        ("slippage_shock_probability", _DecimalSubclass("0.001000")),
        ("uncertainty_buffer_probability", None),
    ),
)
def test_requires_exact_decimal_probability_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    kwargs: dict[str, object] = {
        "raw_edge_probability": d("0.040000"),
        "base_cost_probability": d("0.010000"),
        "stressed_cost_probability": d("0.005000"),
        "slippage_shock_probability": d("0.003000"),
        "uncertainty_buffer_probability": d("0.002000"),
    }
    kwargs[field_name] = bad_value

    with pytest.raises(ValueError, match=f"{field_name}.*Decimal"):
        build_probability_event_cost_sensitivity_break_even_report(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    (
        "raw_edge_probability",
        "base_cost_probability",
        "stressed_cost_probability",
        "slippage_shock_probability",
        "uncertainty_buffer_probability",
    ),
)
def test_rejects_probability_values_outside_zero_to_one(field_name: str) -> None:
    kwargs = {
        "raw_edge_probability": d("0.040000"),
        "base_cost_probability": d("0.010000"),
        "stressed_cost_probability": d("0.005000"),
        "slippage_shock_probability": d("0.003000"),
        "uncertainty_buffer_probability": d("0.002000"),
    }
    kwargs[field_name] = d("1.000001")

    with pytest.raises(ValueError, match=f"{field_name}.*between 0 and 1"):
        build_probability_event_cost_sensitivity_break_even_report(**kwargs)


def test_dataclass_is_frozen_final_flag_guarded_and_digest_guarded() -> None:
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.break_even_status = "below_break_even"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)

    with pytest.raises(ValueError, match="subclass"):
        type("BadReport", (ProbabilityEventCostSensitivityBreakEvenReport,), {})

    decimal_fields = {
        item.name
        for item in fields(ProbabilityEventCostSensitivityBreakEvenReport)
        if item.type is Decimal
    }
    assert decimal_fields == {
        "raw_edge_probability",
        "base_cost_probability",
        "stressed_cost_probability",
        "slippage_shock_probability",
        "uncertainty_buffer_probability",
        "total_cost_probability",
        "cost_headroom_probability",
    }


def test_module_is_report_only_without_unsafe_or_durable_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    forbidden_fragments = (
        term("l", "i", "v", "e"),
        term("a", "u", "t", "h"),
        term("w", "a", "l", "l", "e", "t"),
        term("private", "_", "k", "e", "y"),
        term("api", "_", "k", "e", "y"),
        term("secret", "_", "k", "e", "y"),
        term("s", "i", "g", "n"),
        term("json", "l"),
        "open(",
        "path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in lowered

    assert "paper_only: bool = True" in source
    assert "report_only: bool = True" in source
    assert "readonly: bool = True" in source
