from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_context_gap_escalation_v10"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def escalation_input(**overrides: object) -> Any:
    module = api()
    values = {
        "market_id": "fed-july-policy-path",
        "required_primary_source_count": d("3.000000"),
        "missing_primary_source_count": d("0.000000"),
        "context_age_minutes": d("30.000000"),
        "market_move_bps_since_research": d("25.000000"),
        "time_to_resolution_minutes": d("4320.000000"),
        "domain_specialist_confidence": d("0.950000"),
    }
    values.update(overrides)
    return module.StrategyMarketContextGapEscalationV10Input(**values)


def evaluate(**overrides: object) -> Any:
    module = api()
    return module.evaluate_strategy_market_context_gap_escalation_v10(
        escalation_input(**overrides),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
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


def test_complete_context_returns_clear_readonly_payload() -> None:
    module = api()

    result = evaluate()

    assert isinstance(result, module.StrategyMarketContextGapEscalationV10Result)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.escalation_score == d("0.014167")
    assert result.escalation_tier == "clear"
    assert result.required_action == "continue_screening"
    assert result.context_gap_reasons == ()
    assert result.reason_codes == ("context_gap_escalation_clear",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_incomplete_required_context_escalates_even_when_other_drivers_are_calm() -> None:
    result = evaluate(
        required_primary_source_count=d("4.000000"),
        missing_primary_source_count=d("1.000000"),
        context_age_minutes=d("45.000000"),
        market_move_bps_since_research=d("40.000000"),
        time_to_resolution_minutes=d("2880.000000"),
        domain_specialist_confidence=d("0.900000"),
    )

    assert result.missing_primary_source_score == d("0.087500")
    assert result.escalation_score == d("0.111750")
    assert result.escalation_tier == "escalate"
    assert result.required_action == "assign_context_research"
    assert result.context_gap_reasons == ("missing_primary_sources",)
    assert result.reason_codes == (
        "context_gap_escalate",
        "missing_primary_sources",
    )


def test_compounded_context_gap_blocks_until_required_context_is_refreshed() -> None:
    result = evaluate(
        required_primary_source_count=d("3.000000"),
        missing_primary_source_count=d("2.000000"),
        context_age_minutes=d("1500.000000"),
        market_move_bps_since_research=d("900.000000"),
        time_to_resolution_minutes=d("120.000000"),
        domain_specialist_confidence=d("0.350000"),
    )

    assert result.missing_primary_source_score == d("0.233333")
    assert result.stale_context_score == d("0.200000")
    assert result.market_movement_score == d("0.180000")
    assert result.resolution_timing_score == d("0.137500")
    assert result.confidence_gap_score == d("0.065000")
    assert result.escalation_score == d("0.815833")
    assert result.escalation_tier == "block_until_researched"
    assert result.required_action == "block_until_required_context_refreshed"
    assert result.context_gap_reasons == (
        "missing_primary_sources",
        "stale_context",
        "market_moved_since_research",
        "near_resolution",
        "low_domain_confidence",
    )
    assert result.reason_codes == (
        "context_gap_block_until_researched",
        "missing_primary_sources",
        "context_critical_stale",
        "market_move_extreme_since_research",
        "resolution_imminent",
        "domain_confidence_low",
    )


def test_payload_serializes_decimals_as_strings_and_exposes_result_payload() -> None:
    module = api()
    result = evaluate(
        required_primary_source_count=d("3.000000"),
        missing_primary_source_count=d("2.000000"),
        context_age_minutes=d("1500.000000"),
        market_move_bps_since_research=d("900.000000"),
        time_to_resolution_minutes=d("120.000000"),
        domain_specialist_confidence=d("0.350000"),
    )

    payload = module.strategy_market_context_gap_escalation_v10_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert result.payload == payload
    assert payload["market_id"] == "fed-july-policy-path"
    assert payload["required_primary_source_count"] == "3.000000"
    assert payload["missing_primary_source_count"] == "2.000000"
    assert payload["context_age_minutes"] == "1500.000000"
    assert payload["market_move_bps_since_research"] == "900.000000"
    assert payload["time_to_resolution_minutes"] == "120.000000"
    assert payload["domain_specialist_confidence"] == "0.350000"
    assert payload["escalation_score"] == "0.815833"
    assert payload["escalation_tier"] == "block_until_researched"
    assert payload["required_action"] == "block_until_required_context_refreshed"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"0.815833"' in encoded
    assert_payload_has_no_runtime_numbers(payload)


def test_validation_rejects_non_decimal_granular_nonfinite_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_id must be a nonblank trimmed string"):
        escalation_input(market_id=" fed ")
    with pytest.raises(ValueError, match="required_primary_source_count must be exactly Decimal"):
        escalation_input(required_primary_source_count=_DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="context_age_minutes must be a Decimal"):
        escalation_input(context_age_minutes=30)
    with pytest.raises(ValueError, match="market_move_bps_since_research precision is too granular"):
        escalation_input(market_move_bps_since_research=d("25.0000001"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be finite"):
        escalation_input(time_to_resolution_minutes=d("NaN"))
    with pytest.raises(ValueError, match="missing_primary_source_count must be nonnegative"):
        escalation_input(missing_primary_source_count=d("-1.000000"))
    with pytest.raises(ValueError, match="missing_primary_source_count must be a whole Decimal"):
        escalation_input(missing_primary_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="required_primary_source_count must be positive"):
        escalation_input(required_primary_source_count=d("0.000000"))
    with pytest.raises(ValueError, match="missing_primary_source_count must not exceed required_primary_source_count"):
        escalation_input(
            required_primary_source_count=d("2.000000"),
            missing_primary_source_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="domain_specialist_confidence must be between 0 and 1"):
        escalation_input(domain_specialist_confidence=d("1.100000"))
    with pytest.raises(ValueError, match="input readonly must be True"):
        escalation_input(readonly=False)

    with pytest.raises(ValueError, match="input_row must be a StrategyMarketContextGapEscalationV10Input"):
        module.evaluate_strategy_market_context_gap_escalation_v10(object())

    result = evaluate()
    with pytest.raises(FrozenInstanceError):
        result.escalation_tier = "escalate"  # type: ignore[misc]
    with pytest.raises(ValueError, match="result report_only must be True"):
        module.StrategyMarketContextGapEscalationV10Result(
            **{**result.__dict__, "report_only": False},
        )


def test_result_revalidates_derived_scores_tier_action_reasons_and_codes() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(ValueError, match="escalation_score must match score components"):
        module.StrategyMarketContextGapEscalationV10Result(
            **{**result.__dict__, "escalation_score": d("0.500000")},
        )
    with pytest.raises(ValueError, match="escalation_tier must match inputs and score"):
        module.StrategyMarketContextGapEscalationV10Result(
            **{**result.__dict__, "escalation_tier": "watch"},
        )
    with pytest.raises(ValueError, match="required_action must match escalation_tier"):
        module.StrategyMarketContextGapEscalationV10Result(
            **{**result.__dict__, "required_action": "assign_context_research"},
        )
    with pytest.raises(ValueError, match="context_gap_reasons must match inputs"):
        module.StrategyMarketContextGapEscalationV10Result(
            **{**result.__dict__, "context_gap_reasons": ("missing_primary_sources",)},
        )
    with pytest.raises(ValueError, match="reason_codes must match inputs"):
        module.StrategyMarketContextGapEscalationV10Result(
            **{**result.__dict__, "reason_codes": ("context_gap_watch",)},
        )


def test_module_is_paper_report_readonly_without_io_or_execution_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_context_gap_escalation_v10.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "auth",
        "cancel",
        "connect",
        "create_order",
        "login",
        "open",
        "place_order",
        "submit_order",
        "trade",
        "wallet",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "api_key",
        "private_key",
        "secret",
        "signing",
        "sqlite",
        "postgres",
        "psycopg",
        "requests",
        "httpx",
        "urllib",
        "wallet",
    )
    lowered = source.lower()
    for term in forbidden_terms:
        assert term not in lowered
