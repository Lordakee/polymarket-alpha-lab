from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_specialist_load_smoothing_v10.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_specialist_load_smoothing_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def specialist_input(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_rates",
        "specialist_domain": "macro_rates_events",
        "queue_depth": d("18"),
        "urgent_candidate_count": d("5"),
        "stale_packet_count": d("4"),
        "recent_error_rate": d("0.240000"),
        "available_analyst_capacity": d("1"),
    }
    values.update(overrides)
    return module.StrategyTeamSpecialistLoadSmoothingV10Input(**values)


def recommend(load_input=None):
    module = api()
    return module.recommend_strategy_team_specialist_load_smoothing_v10(
        load_input if load_input is not None else specialist_input(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_recommends_redistribution_for_overloaded_specialist_team() -> None:
    result = recommend()

    assert is_dataclass(result)
    assert result.team_id == "macro_rates"
    assert result.specialist_domain == "macro_rates_events"
    assert result.smoothing_status == "redistribute_now"
    assert result.recommended_smoothing_action == (
        "shift_urgent_candidates_to_available_analysts"
    )
    assert result.queue_pressure_score == d("0.900000")
    assert result.urgency_pressure_score == d("1.000000")
    assert result.stale_pressure_score == d("1.000000")
    assert result.error_pressure_score == d("0.960000")
    assert result.capacity_gap_score == d("0.750000")
    assert result.smoothing_pressure_score == d("0.939000")
    assert result.reason_codes == (
        "specialist_load_smoothing_input",
        "specialist_load_smoothing_redistribute_now",
        "queue_depth_high",
        "urgent_candidates_high",
        "stale_packets_high",
        "error_rate_high",
        "analyst_capacity_constrained",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_recommends_staged_support_for_moderate_stale_and_error_pressure() -> None:
    result = recommend(
        specialist_input(
            queue_depth=d("7"),
            urgent_candidate_count=d("1"),
            stale_packet_count=d("2"),
            recent_error_rate=d("0.120000"),
            available_analyst_capacity=d("2"),
        ),
    )

    assert result.smoothing_status == "stage_support"
    assert result.recommended_smoothing_action == "pair_review_stale_packets"
    assert result.smoothing_pressure_score == d("0.377000")
    assert result.reason_codes == (
        "specialist_load_smoothing_input",
        "specialist_load_smoothing_stage_support",
        "queue_depth_contained",
        "urgent_candidates_contained",
        "stale_packets_present",
        "error_rate_elevated",
        "analyst_capacity_watch",
    )


def test_recommends_holding_healthy_specialist_load() -> None:
    result = recommend(
        specialist_input(
            queue_depth=d("2"),
            urgent_candidate_count=d("0"),
            stale_packet_count=d("0"),
            recent_error_rate=d("0.020000"),
            available_analyst_capacity=d("5"),
        ),
    )

    assert result.smoothing_status == "hold_capacity"
    assert result.recommended_smoothing_action == "keep_current_specialist_load"
    assert result.smoothing_pressure_score == d("0.042000")
    assert result.reason_codes == (
        "specialist_load_smoothing_input",
        "specialist_load_smoothing_hold_capacity",
        "queue_depth_contained",
        "urgent_candidates_contained",
        "stale_packets_contained",
        "error_rate_contained",
        "analyst_capacity_available",
    )


def test_payload_uses_decimal_strings_and_no_float_values() -> None:
    module = api()
    result = recommend()

    payload = result.payload

    assert payload == module.strategy_team_specialist_load_smoothing_v10_payload(
        result,
    )
    assert payload["team_id"] == "macro_rates"
    assert payload["queue_depth"] == "18"
    assert payload["recent_error_rate"] == "0.240000"
    assert payload["smoothing_pressure_score"] == "0.939000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="result must be"):
        module.strategy_team_specialist_load_smoothing_v10_payload(object())


def test_dataclasses_are_frozen_and_hard_flags_cannot_be_downgraded() -> None:
    module = api()
    load_input = specialist_input()
    result = recommend(load_input)

    for item in (load_input, result):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(item, field.name) is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(load_input, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)

    assert module.__all__ == (
        "StrategyTeamSpecialistLoadSmoothingV10Input",
        "StrategyTeamSpecialistLoadSmoothingV10Result",
        "recommend_strategy_team_specialist_load_smoothing_v10",
        "strategy_team_specialist_load_smoothing_v10_payload",
    )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("queue_depth", 18),
        ("urgent_candidate_count", "1"),
        ("stale_packet_count", _DecimalSubclass("1")),
        ("recent_error_rate", 0),
        ("available_analyst_capacity", 1),
    ),
)
def test_numeric_inputs_reject_non_decimal_values(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        specialist_input(**{field_name: bad_value})


def test_validation_rejects_bad_ranges_strings_flags_and_result_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id must not contain sensitive content"):
        specialist_input(team_id="secret_team")
    with pytest.raises(ValueError, match="specialist_domain must not be empty"):
        specialist_input(specialist_domain="")
    with pytest.raises(ValueError, match="queue_depth must be nonnegative"):
        specialist_input(queue_depth=d("-1"))
    with pytest.raises(ValueError, match="urgent_candidate_count must not exceed queue_depth"):
        specialist_input(urgent_candidate_count=d("19"))
    with pytest.raises(ValueError, match="stale_packet_count must not exceed queue_depth"):
        specialist_input(stale_packet_count=d("19"))
    with pytest.raises(ValueError, match="recent_error_rate must be between 0 and 1"):
        specialist_input(recent_error_rate=d("1.000001"))
    with pytest.raises(ValueError, match="available_analyst_capacity must be an integer Decimal"):
        specialist_input(available_analyst_capacity=d("1.500000"))
    with pytest.raises(ValueError, match="load_input must be"):
        module.recommend_strategy_team_specialist_load_smoothing_v10(object())
    with pytest.raises(ValueError, match="readonly must be True"):
        specialist_input(readonly=False)

    result = recommend()
    with pytest.raises(ValueError, match="smoothing_pressure_score must match inputs"):
        replace(result, smoothing_pressure_score=ZERO)


def test_module_scope_has_no_live_trading_persistence_network_or_float_constants() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.level == 0
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "env",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    }

    assert imports
    assert all(
        fragment not in module_name.lower()
        for module_name in imports
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)
    assert float_constants == []
