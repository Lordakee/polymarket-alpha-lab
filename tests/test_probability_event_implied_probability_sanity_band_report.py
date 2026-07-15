from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_implied_probability_sanity_band_report import (
    ProbabilityEventImpliedProbabilitySanityBandInput,
    ProbabilityEventImpliedProbabilitySanityBandReport,
    ProbabilityEventImpliedProbabilitySanityBandRow,
    build_probability_event_implied_probability_sanity_band_report,
    probability_event_implied_probability_sanity_band_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 9, 15, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def band_input(**overrides: object) -> ProbabilityEventImpliedProbabilitySanityBandInput:
    values = {
        "event_id": "event-alpha",
        "market_slug": "fed-cut-by-september",
        "yes_probability": d("0.560000"),
        "no_probability": d("0.440000"),
        "forecast_probability": d("0.570000"),
        "reference_probability_low": d("0.520000"),
        "reference_probability_high": d("0.610000"),
        "spread_probability": d("0.030000"),
        "reason_codes": ("source_ready",),
    }
    values.update(overrides)
    return ProbabilityEventImpliedProbabilitySanityBandInput(**values)


def build_report(
    *inputs: ProbabilityEventImpliedProbabilitySanityBandInput,
) -> ProbabilityEventImpliedProbabilitySanityBandReport:
    return build_probability_event_implied_probability_sanity_band_report(
        inputs,
        config_version="implied-probability-sanity-band-v0",
        generated_at=GENERATED_AT,
    )


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_pass_rows_confirm_yes_no_forecast_band_and_spread_sanity() -> None:
    report = build_report(
        band_input(
            event_id="event-alpha",
            market_slug="alpha",
            yes_probability=d("0.560000"),
            no_probability=d("0.440000"),
            forecast_probability=d("0.570000"),
            reference_probability_low=d("0.520000"),
            reference_probability_high=d("0.610000"),
            spread_probability=d("0.030000"),
        ),
        band_input(
            event_id="event-beta",
            market_slug="beta",
            yes_probability=d("0.420000"),
            no_probability=d("0.580000"),
            forecast_probability=d("0.410000"),
            reference_probability_low=d("0.390000"),
            reference_probability_high=d("0.450000"),
            spread_probability=d("0.020000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "implied-probability-sanity-band-v0"
    assert report.input_count == 2
    assert report.row_count == 2
    assert report.pass_count == 2
    assert report.watch_count == 0
    assert report.block_count == 0
    assert report.pass_ratio == d("1.000000")
    assert report.max_band_gap == d("0.000000")
    assert report.max_yes_no_sum_gap == d("0.000000")
    assert report.max_spread_probability == d("0.030000")
    assert report.report_status == "pass"
    assert report.reason_codes == ("implied_probability_sanity_band_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    alpha = report.rows[0]
    assert alpha.market_slug == "alpha"
    assert alpha.yes_no_sum_probability == d("1.000000")
    assert alpha.yes_no_sum_gap == d("0.000000")
    assert alpha.reference_mid_probability == d("0.565000")
    assert alpha.forecast_reference_mid_gap == d("0.005000")
    assert alpha.band_gap == d("0.000000")
    assert alpha.sanity_status == "pass"
    assert alpha.reason_codes == (
        "implied_probability_sanity_band_pass",
        "source_ready",
    )
    assert alpha.manual_next_step == "no_manual_action_required"


def test_watch_and_block_rows_emit_reason_codes_manual_next_steps_and_rollups() -> None:
    report = build_report(
        band_input(
            event_id="event-block",
            market_slug="block",
            yes_probability=d("0.660000"),
            no_probability=d("0.420000"),
            forecast_probability=d("0.700000"),
            reference_probability_low=d("0.430000"),
            reference_probability_high=d("0.500000"),
            spread_probability=d("0.110000"),
            reason_codes=("source_ready",),
        ),
        band_input(
            event_id="event-watch",
            market_slug="watch",
            yes_probability=d("0.620000"),
            no_probability=d("0.380000"),
            forecast_probability=d("0.600000"),
            reference_probability_low=d("0.500000"),
            reference_probability_high=d("0.570000"),
            spread_probability=d("0.060000"),
            reason_codes=("source_ready",),
        ),
        band_input(
            event_id="event-pass",
            market_slug="pass",
            yes_probability=d("0.550000"),
            no_probability=d("0.450000"),
            forecast_probability=d("0.540000"),
            reference_probability_low=d("0.500000"),
            reference_probability_high=d("0.570000"),
            spread_probability=d("0.030000"),
            reason_codes=("source_ready",),
        ),
    )

    block = report.rows[0]
    assert block.market_slug == "block"
    assert block.yes_no_sum_probability == d("1.080000")
    assert block.yes_no_sum_gap == d("0.080000")
    assert block.reference_mid_probability == d("0.465000")
    assert block.forecast_reference_mid_gap == d("0.235000")
    assert block.band_gap == d("0.200000")
    assert block.sanity_status == "block"
    assert block.reason_codes == (
        "implied_probability_sanity_band_block",
        "source_ready",
        "yes_no_sum_block",
        "forecast_above_reference_band_block",
        "spread_probability_block",
    )
    assert block.manual_next_step == "manual_review_required_before_research_use"

    watch = report.rows[1]
    assert watch.market_slug == "watch"
    assert watch.band_gap == d("0.030000")
    assert watch.sanity_status == "watch"
    assert watch.reason_codes == (
        "implied_probability_sanity_band_watch",
        "source_ready",
        "forecast_above_reference_band_watch",
        "spread_probability_watch",
    )
    assert watch.manual_next_step == "manual_verify_probability_inputs"

    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.block_count == 1
    assert report.pass_ratio == d("0.333333")
    assert report.max_band_gap == d("0.200000")
    assert report.max_yes_no_sum_gap == d("0.080000")
    assert report.max_spread_probability == d("0.110000")
    assert report.report_status == "block"
    assert report.reason_codes == (
        "implied_probability_sanity_band_block",
        "yes_no_sum_block",
        "forecast_above_reference_band_block",
        "spread_probability_block",
        "forecast_above_reference_band_watch",
        "spread_probability_watch",
    )


def test_empty_report_is_pass_with_zero_decimal_rollups() -> None:
    report = build_report()

    assert report.input_count == 0
    assert report.row_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.block_count == 0
    assert report.pass_ratio == d("0.000000")
    assert report.max_band_gap == d("0.000000")
    assert report.max_yes_no_sum_gap == d("0.000000")
    assert report.max_spread_probability == d("0.000000")
    assert report.report_status == "pass"
    assert report.reason_codes == ("implied_probability_sanity_band_pass",)
    assert report.rows == ()


def test_direct_constructors_validate_consistency_utc_ordering_and_safety_flags() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_probability_event_implied_probability_sanity_band_report(
        [band_input()],
        config_version="implied-probability-sanity-band-v0",
        generated_at=datetime(2026, 7, 12, 5, 15, tzinfo=eastern),
    )
    assert report.generated_at == GENERATED_AT

    rebuilt_row = ProbabilityEventImpliedProbabilitySanityBandRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="band_gap"):
        replace(report.rows[0], band_gap=d("0.010000"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=3)
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="paper_only"):
        replace(band_input(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_frozen_dataclasses_decimal_only_and_payload_decimal_strings() -> None:
    source = band_input()
    report = build_report(source)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        source.forecast_probability = d("0.650000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.sanity_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    for cls in (
        ProbabilityEventImpliedProbabilitySanityBandInput,
        ProbabilityEventImpliedProbabilitySanityBandRow,
        ProbabilityEventImpliedProbabilitySanityBandReport,
    ):
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name.endswith("probability") or field.name.endswith("gap"):
                assert hints[field.name] is Decimal

    payload = probability_event_implied_probability_sanity_band_report_payload(report)
    assert payload["generated_at"] == "2026-07-12T09:15:00+00:00"
    assert payload["pass_ratio"] == "1.000000"
    assert payload["max_band_gap"] == "0.000000"
    assert payload["rows"][0]["forecast_probability"] == "0.570000"
    assert payload["rows"][0]["manual_next_step"] == "no_manual_action_required"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("yes_probability", Decimal("-0.000001"), "yes_probability"),
        ("no_probability", Decimal("1.000001"), "no_probability"),
        ("forecast_probability", Decimal("NaN"), "forecast_probability"),
        ("reference_probability_low", Decimal("-0.000001"), "reference_probability_low"),
        ("reference_probability_high", Decimal("1.000001"), "reference_probability_high"),
        ("spread_probability", Decimal("-0.000001"), "spread_probability"),
    ),
)
def test_inputs_reject_invalid_probability_values(
    field_name: str,
    bad_value: Decimal,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        replace(band_input(), **{field_name: bad_value})


def test_decimal_only_rejects_float_subclasses_bad_ranges_and_bad_build_inputs() -> None:
    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="yes_probability"):
        replace(band_input(), yes_probability=0.56)
    with pytest.raises(ValueError, match="forecast_probability"):
        replace(band_input(), forecast_probability=DecimalSubclass("0.570000"))
    with pytest.raises(ValueError, match="reference_probability"):
        replace(
            band_input(),
            reference_probability_low=d("0.620000"),
            reference_probability_high=d("0.610000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_probability_event_implied_probability_sanity_band_report(
            [band_input()],
            config_version="implied-probability-sanity-band-v0",
            generated_at="2026-07-12T09:15:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_probability_event_implied_probability_sanity_band_report(
            [object()],
            config_version="implied-probability-sanity-band-v0",
            generated_at=GENERATED_AT,
        )


def test_module_scope_is_report_only_paper_only_readonly_and_has_no_io_surface() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "probability_event_implied_probability_sanity_band_report.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {
                "open",
                "read",
                "write",
                "request",
                "submit",
                "connect",
            }

    assert imports == [
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
    ]
    source = path.read_text(encoding="utf-8").lower()
    for forbidden in ("wallet", "auth", "private_key", "order", "live", "http", "urllib", "requests"):
        assert forbidden not in source
