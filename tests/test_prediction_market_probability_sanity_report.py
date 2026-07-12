from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.prediction_market_probability_sanity_report import (
    PredictionMarketProbabilitySanityInput,
    PredictionMarketProbabilitySanityReport,
    PredictionMarketProbabilitySanityRow,
    build_prediction_market_probability_sanity_report,
    prediction_market_probability_sanity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 15, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def sanity_input(**overrides: object) -> PredictionMarketProbabilitySanityInput:
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "forecast_probability": d("0.640000"),
        "market_probability": d("0.560000"),
        "bid_implied_probability": d("0.550000"),
        "ask_implied_probability": d("0.570000"),
        "cost_adjusted_threshold": d("0.585000"),
        "edge_to_threshold": d("0.055000"),
        "reason_codes": ("source_ready",),
    }
    values.update(overrides)
    return PredictionMarketProbabilitySanityInput(**values)


def build_report(
    *inputs: PredictionMarketProbabilitySanityInput,
) -> PredictionMarketProbabilitySanityReport:
    return build_prediction_market_probability_sanity_report(
        inputs,
        config_version="probability-sanity-v0",
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


def test_ready_rows_confirm_probability_direction_threshold_and_spread_sanity() -> None:
    report = build_report(
        sanity_input(
            candidate_id="candidate-alpha",
            market_slug="alpha",
            forecast_probability=d("0.640000"),
            market_probability=d("0.560000"),
            bid_implied_probability=d("0.550000"),
            ask_implied_probability=d("0.570000"),
            cost_adjusted_threshold=d("0.585000"),
            edge_to_threshold=d("0.055000"),
        ),
        sanity_input(
            candidate_id="candidate-beta",
            market_slug="beta",
            forecast_probability=d("0.410000"),
            market_probability=d("0.490000"),
            bid_implied_probability=d("0.480000"),
            ask_implied_probability=d("0.500000"),
            cost_adjusted_threshold=d("0.445000"),
            edge_to_threshold=d("-0.035000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-sanity-v0"
    assert report.input_count == 2
    assert report.row_count == 2
    assert report.ready_count == 2
    assert report.blocked_count == 0
    assert report.ready_ratio == d("1.000000")
    assert report.max_probability_gap == d("0.080000")
    assert report.report_status == "ready"
    assert report.reason_codes == ("probability_sanity_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    alpha = report.rows[0]
    assert alpha.market_slug == "alpha"
    assert alpha.probability_gap == d("0.080000")
    assert alpha.bid_ask_mid_probability == d("0.560000")
    assert alpha.bid_ask_mid_gap == d("0.000000")
    assert alpha.threshold_probability_gap == d("0.055000")
    assert alpha.sanity_status == "ready"
    assert alpha.inconsistency_reasons == ()
    assert alpha.blocker_reasons == ()
    assert alpha.reason_codes == ("probability_sanity_ready", "source_ready")

    beta = report.rows[1]
    assert beta.probability_gap == d("-0.080000")
    assert beta.threshold_probability_gap == d("-0.035000")
    assert beta.reason_codes == ("probability_sanity_ready", "source_ready")


def test_inconsistent_rows_emit_directional_reasons_blockers_and_rollup_metrics() -> None:
    report = build_report(
        sanity_input(
            candidate_id="candidate-blocked",
            market_slug="bad-spread",
            forecast_probability=d("0.620000"),
            market_probability=d("0.570000"),
            bid_implied_probability=d("0.610000"),
            ask_implied_probability=d("0.590000"),
            cost_adjusted_threshold=d("0.580000"),
            edge_to_threshold=d("-0.020000"),
            reason_codes=("source_ready",),
        ),
        sanity_input(
            candidate_id="candidate-ready",
            market_slug="ready",
            forecast_probability=d("0.600000"),
            market_probability=d("0.550000"),
            bid_implied_probability=d("0.540000"),
            ask_implied_probability=d("0.560000"),
            cost_adjusted_threshold=d("0.580000"),
            edge_to_threshold=d("0.020000"),
            reason_codes=("source_ready",),
        ),
    )

    blocked = report.rows[0]
    assert blocked.sanity_status == "blocked"
    assert blocked.probability_gap == d("0.050000")
    assert blocked.bid_ask_mid_probability == d("0.600000")
    assert blocked.bid_ask_mid_gap == d("-0.030000")
    assert blocked.threshold_probability_gap == d("0.040000")
    assert blocked.inconsistency_reasons == (
        "bid_above_ask",
        "edge_to_threshold_direction_mismatch",
        "edge_to_threshold_value_mismatch",
        "market_probability_outside_bid_ask",
    )
    assert blocked.blocker_reasons == (
        "bid_ask_implied_probability_inconsistent",
        "edge_to_threshold_inconsistent",
        "market_probability_bid_ask_inconsistent",
    )
    assert blocked.reason_codes == (
        "probability_sanity_blocked",
        "source_ready",
        "bid_above_ask",
        "edge_to_threshold_direction_mismatch",
        "edge_to_threshold_value_mismatch",
        "market_probability_outside_bid_ask",
        "bid_ask_implied_probability_inconsistent",
        "edge_to_threshold_inconsistent",
        "market_probability_bid_ask_inconsistent",
    )

    assert report.ready_count == 1
    assert report.blocked_count == 1
    assert report.ready_ratio == d("0.500000")
    assert report.max_probability_gap == d("0.050000")
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "probability_sanity_blocked",
        "bid_above_ask",
        "edge_to_threshold_direction_mismatch",
        "edge_to_threshold_value_mismatch",
        "market_probability_outside_bid_ask",
        "bid_ask_implied_probability_inconsistent",
        "edge_to_threshold_inconsistent",
        "market_probability_bid_ask_inconsistent",
    )


def test_empty_report_is_ready_with_zero_decimal_rollups() -> None:
    report = build_report()

    assert report.input_count == 0
    assert report.row_count == 0
    assert report.ready_count == 0
    assert report.blocked_count == 0
    assert report.ready_ratio == d("0.000000")
    assert report.max_probability_gap == d("0.000000")
    assert report.report_status == "ready"
    assert report.reason_codes == ("probability_sanity_ready",)
    assert report.rows == ()


def test_direct_constructors_validate_consistency_utc_and_safety_flags() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_prediction_market_probability_sanity_report(
        [sanity_input()],
        config_version="probability-sanity-v0",
        generated_at=datetime(2026, 7, 11, 11, 30, tzinfo=eastern),
    )
    assert report.generated_at == GENERATED_AT

    rebuilt_row = PredictionMarketProbabilitySanityRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="probability_gap"):
        replace(report.rows[0], probability_gap=d("0.010000"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=3)
    with pytest.raises(ValueError, match="paper_only"):
        replace(sanity_input(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_frozen_dataclasses_decimal_only_and_payload_decimal_strings() -> None:
    source = sanity_input()
    report = build_report(source)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        source.forecast_probability = d("0.650000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.sanity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    for cls in (
        PredictionMarketProbabilitySanityInput,
        PredictionMarketProbabilitySanityRow,
        PredictionMarketProbabilitySanityReport,
    ):
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name.endswith("probability") or field.name.endswith("gap"):
                assert hints[field.name] is Decimal
            if field.name == "edge_to_threshold":
                assert hints[field.name] is Decimal

    payload = prediction_market_probability_sanity_report_payload(report)
    assert payload["generated_at"] == "2026-07-11T15:30:00+00:00"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["max_probability_gap"] == "0.080000"
    assert payload["rows"][0]["forecast_probability"] == "0.640000"
    assert payload["rows"][0]["edge_to_threshold"] == "0.055000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("forecast_probability", Decimal("-0.000001"), "forecast_probability"),
        ("market_probability", Decimal("1.000001"), "market_probability"),
        ("bid_implied_probability", Decimal("NaN"), "bid_implied_probability"),
        ("ask_implied_probability", Decimal("-0.000001"), "ask_implied_probability"),
        ("cost_adjusted_threshold", Decimal("1.000001"), "cost_adjusted_threshold"),
    ),
)
def test_inputs_reject_invalid_probability_values(
    field_name: str,
    bad_value: Decimal,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        replace(sanity_input(), **{field_name: bad_value})


def test_decimal_only_rejects_float_subclasses_and_bad_build_inputs() -> None:
    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="forecast_probability"):
        replace(sanity_input(), forecast_probability=0.64)
    with pytest.raises(ValueError, match="market_probability"):
        replace(sanity_input(), market_probability=DecimalSubclass("0.560000"))
    with pytest.raises(ValueError, match="edge_to_threshold"):
        replace(sanity_input(), edge_to_threshold=0.055)
    with pytest.raises(ValueError, match="generated_at"):
        build_prediction_market_probability_sanity_report(
            [sanity_input()],
            config_version="probability-sanity-v0",
            generated_at="2026-07-11T15:30:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_prediction_market_probability_sanity_report(
            [object()],
            config_version="probability-sanity-v0",
            generated_at=GENERATED_AT,
        )


def test_module_scope_is_report_only_paper_only_readonly_and_has_no_io_surface() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "prediction_market_probability_sanity_report.py"
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
    for forbidden in ("wallet", "auth", "private_key", "http", "urllib", "requests"):
        assert forbidden not in source
