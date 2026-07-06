from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
import ast
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_market_postmortem_template_v10 import (
    MarketPostmortemTemplateInput,
    MarketPostmortemTemplateResult,
    build_market_postmortem_template,
    market_postmortem_template_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def postmortem_input(**overrides):
    values = {
        "market_id": "market-123",
        "category": "macro",
        "forecast_probability": d("0.620000"),
        "settled_outcome_probability": d("1.000000"),
        "entry_price_probability": d("0.550000"),
        "cost_adjusted_edge_bps": d("250.000000"),
        "source_gap_count": d("2"),
        "resolution_ambiguity_score": d("0.200000"),
    }
    values.update(overrides)
    return MarketPostmortemTemplateInput(**values)


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_builds_watch_postmortem_with_calibration_lessons_and_payload() -> None:
    result = build_market_postmortem_template(postmortem_input())

    assert isinstance(result, MarketPostmortemTemplateResult)
    assert is_dataclass(result)
    assert result.market_id == "market-123"
    assert result.category == "macro"
    assert result.calibration_delta_bps == d("3800.000000")
    assert result.postmortem_status == "watch"
    assert result.lesson_tags == (
        "underestimated_settled_outcome",
        "entry_below_forecast",
        "source_gap_present",
        "resolution_ambiguity_present",
    )
    assert result.followup_actions == (
        "recalibrate_category_forecast_priors",
        "close_source_coverage_gap",
        "review_resolution_rules_before_next_entry",
    )
    assert result.reason_codes == (
        "market_postmortem_template",
        "calibration_delta_material",
        "source_gap_detected",
        "resolution_ambiguity_detected",
        "cost_adjusted_edge_positive",
        "postmortem_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    payload = result.payload
    assert payload == market_postmortem_template_payload(result)
    assert payload["forecast_probability"] == "0.620000"
    assert payload["settled_outcome_probability"] == "1.000000"
    assert payload["entry_price_probability"] == "0.550000"
    assert payload["cost_adjusted_edge_bps"] == "250.000000"
    assert payload["source_gap_count"] == "2.000000"
    assert payload["resolution_ambiguity_score"] == "0.200000"
    assert payload["calibration_delta_bps"] == "3800.000000"
    assert payload["postmortem_status"] == "watch"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_pass_postmortem_records_clean_calibration_reference() -> None:
    result = build_market_postmortem_template(
        postmortem_input(
            forecast_probability=d("0.970000"),
            settled_outcome_probability=d("1.000000"),
            entry_price_probability=d("0.950000"),
            cost_adjusted_edge_bps=d("400.000000"),
            source_gap_count=d("0"),
            resolution_ambiguity_score=d("0.000000"),
        ),
    )

    assert result.calibration_delta_bps == d("300.000000")
    assert result.postmortem_status == "pass"
    assert result.lesson_tags == ("well_calibrated", "entry_below_forecast")
    assert result.followup_actions == ("record_market_as_calibration_reference",)
    assert result.reason_codes == (
        "market_postmortem_template",
        "calibration_delta_within_threshold",
        "no_source_gap",
        "resolution_clear",
        "cost_adjusted_edge_positive",
        "postmortem_pass",
    )


def test_blocked_postmortem_prioritizes_ambiguous_resolution_and_cost_drag() -> None:
    result = build_market_postmortem_template(
        postmortem_input(
            forecast_probability=d("0.880000"),
            settled_outcome_probability=d("0.000000"),
            entry_price_probability=d("0.900000"),
            cost_adjusted_edge_bps=d("-50.000000"),
            source_gap_count=d("0"),
            resolution_ambiguity_score=d("0.750000"),
        ),
    )

    assert result.calibration_delta_bps == d("-8800.000000")
    assert result.postmortem_status == "blocked"
    assert result.lesson_tags == (
        "overestimated_settled_outcome",
        "entry_above_forecast",
        "cost_adjusted_edge_nonpositive",
        "resolution_ambiguity_present",
    )
    assert result.followup_actions == (
        "recalibrate_category_forecast_priors",
        "tighten_cost_adjusted_entry_gate",
        "review_resolution_rules_before_next_entry",
    )
    assert result.reason_codes == (
        "market_postmortem_template",
        "calibration_delta_material",
        "no_source_gap",
        "resolution_ambiguity_blocked",
        "cost_adjusted_edge_nonpositive",
        "postmortem_blocked",
    )


def test_inputs_use_decimal_only_values_and_validate_ranges() -> None:
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        postmortem_input(forecast_probability=0.62)

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="forecast_probability must be exactly Decimal"):
        postmortem_input(forecast_probability=DecimalSubclass("0.620000"))

    with pytest.raises(ValueError, match="forecast_probability must be between 0 and 1"):
        postmortem_input(forecast_probability=d("1.000001"))

    with pytest.raises(ValueError, match="settled_outcome_probability must be 0 or 1"):
        postmortem_input(settled_outcome_probability=d("0.500000"))

    with pytest.raises(ValueError, match="source_gap_count must be nonnegative"):
        postmortem_input(source_gap_count=d("-1"))

    with pytest.raises(ValueError, match="source_gap_count must be a whole Decimal"):
        postmortem_input(source_gap_count=d("1.500000"))

    with pytest.raises(ValueError, match="resolution_ambiguity_score must be between 0 and 1"):
        postmortem_input(resolution_ambiguity_score=d("1.000001"))


def test_inputs_and_outputs_are_readonly_frozen_and_flag_guarded() -> None:
    template_input = postmortem_input()
    result = build_market_postmortem_template(template_input)

    with pytest.raises(FrozenInstanceError):
        template_input.category = "sports"

    with pytest.raises(FrozenInstanceError):
        result.postmortem_status = "pass"

    with pytest.raises(ValueError, match="paper_only must be True"):
        postmortem_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        postmortem_input(readonly=False)

    unsafe = object.__new__(MarketPostmortemTemplateResult)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        market_postmortem_template_payload(unsafe)


def test_module_is_pure_report_only_and_contains_no_io_or_execution_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_postmortem_template_v10.py")
    source = path.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "private_key",
        "account",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "trade",
        "database",
        "db",
        "persist",
        "network",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "psycopg",
        "open(",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    banned_imports = {
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "psycopg",
    }
    banned_calls = {
        "open",
        "connect",
        "create_order",
        "place_order",
        "submit_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
