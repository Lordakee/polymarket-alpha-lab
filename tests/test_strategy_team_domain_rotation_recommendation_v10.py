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
    / "strategy_team_domain_rotation_recommendation_v10.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_domain_rotation_recommendation_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def domain_input(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "current_domain": "macro_events",
        "recent_hit_rate": d("0.420000"),
        "calibration_error_bps": d("420.000000"),
        "source_gap_rate": d("0.450000"),
        "queue_pressure_score": d("0.700000"),
        "days_in_domain": d("45.000000"),
        "domain_learning_score": d("0.650000"),
    }
    values.update(overrides)
    return module.StrategyTeamDomainRotationRecommendationV10Input(**values)


def recommend(rotation_input=None):
    module = api()
    return module.recommend_strategy_team_domain_rotation_v10(
        rotation_input if rotation_input is not None else domain_input(),
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


def test_recommendation_rotates_mature_domain_with_pressure() -> None:
    result = recommend()

    assert is_dataclass(result)
    assert result.team_id == "macro_team"
    assert result.current_domain == "macro_events"
    assert result.rotation_status == "rotate"
    assert result.recommended_domain_action == "rotate_to_adjacent_domain"
    assert result.rotation_priority == d("0.509000")
    assert result.calibration_pressure_score == d("0.420000")
    assert result.domain_tenure_pressure_score == d("0.500000")
    assert result.domain_learning_gap_score == d("0.350000")
    assert result.reason_codes == (
        "team_domain_rotation_input",
        "team_domain_rotation_rotate",
        "hit_rate_weak",
        "calibration_error_high",
        "source_gap_high",
        "queue_pressure_high",
        "domain_tenure_mature",
        "domain_learning_sufficient",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_recommendation_watches_short_tenure_despite_high_pressure() -> None:
    result = recommend(
        domain_input(
            recent_hit_rate=d("0.300000"),
            calibration_error_bps=d("600.000000"),
            source_gap_rate=d("0.600000"),
            queue_pressure_score=d("0.800000"),
            days_in_domain=d("7.000000"),
            domain_learning_score=d("0.400000"),
        ),
    )

    assert result.rotation_status == "watch"
    assert result.recommended_domain_action == "extend_domain_learning_window"
    assert result.rotation_priority == d("0.701778")
    assert result.reason_codes == (
        "team_domain_rotation_input",
        "team_domain_rotation_watch",
        "hit_rate_weak",
        "calibration_error_high",
        "source_gap_high",
        "queue_pressure_high",
        "domain_tenure_short",
        "domain_learning_developing",
    )


def test_recommendation_watches_source_gap_before_rotation() -> None:
    result = recommend(
        domain_input(
            recent_hit_rate=d("0.650000"),
            calibration_error_bps=d("180.000000"),
            source_gap_rate=d("0.380000"),
            queue_pressure_score=d("0.300000"),
            days_in_domain=d("14.000000"),
            domain_learning_score=d("0.550000"),
        ),
    )

    assert result.rotation_status == "watch"
    assert result.recommended_domain_action == "repair_sources_before_rotation"
    assert result.rotation_priority == d("0.305056")
    assert result.reason_codes == (
        "team_domain_rotation_input",
        "team_domain_rotation_watch",
        "hit_rate_stable",
        "calibration_error_contained",
        "source_gap_elevated",
        "queue_pressure_contained",
        "domain_tenure_short",
        "domain_learning_developing",
    )


def test_recommendation_holds_healthy_domain() -> None:
    result = recommend(
        domain_input(
            recent_hit_rate=d("0.780000"),
            calibration_error_bps=d("80.000000"),
            source_gap_rate=d("0.050000"),
            queue_pressure_score=d("0.100000"),
            days_in_domain=d("10.000000"),
            domain_learning_score=d("0.820000"),
        ),
    )

    assert result.rotation_status == "hold"
    assert result.recommended_domain_action == "continue_current_domain"
    assert result.rotation_priority == d("0.125111")
    assert result.reason_codes == (
        "team_domain_rotation_input",
        "team_domain_rotation_hold",
        "hit_rate_stable",
        "calibration_error_contained",
        "source_gap_contained",
        "queue_pressure_contained",
        "domain_tenure_short",
        "domain_learning_sufficient",
    )


def test_payload_uses_decimal_strings_and_no_float_values() -> None:
    module = api()
    result = recommend()

    payload = result.payload

    assert payload == module.strategy_team_domain_rotation_recommendation_v10_payload(
        result,
    )
    assert payload["team_id"] == "macro_team"
    assert payload["recent_hit_rate"] == "0.420000"
    assert payload["calibration_error_bps"] == "420.000000"
    assert payload["rotation_priority"] == "0.509000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="result must be"):
        module.strategy_team_domain_rotation_recommendation_v10_payload(object())


def test_dataclasses_are_frozen_and_hard_flags_cannot_be_downgraded() -> None:
    module = api()
    rotation_input = domain_input()
    result = recommend(rotation_input)

    for item in (rotation_input, result):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(item, field.name) is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(rotation_input, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)

    assert module.__all__ == (
        "StrategyTeamDomainRotationRecommendationV10Input",
        "StrategyTeamDomainRotationRecommendationV10Result",
        "recommend_strategy_team_domain_rotation_v10",
        "strategy_team_domain_rotation_recommendation_v10_payload",
    )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("recent_hit_rate", 1),
        ("calibration_error_bps", 12),
        ("source_gap_rate", "0.100000"),
        ("queue_pressure_score", _DecimalSubclass("0.100000")),
        ("days_in_domain", 12),
        ("domain_learning_score", 0),
    ),
)
def test_numeric_inputs_reject_non_decimal_values(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        domain_input(**{field_name: bad_value})


def test_validation_rejects_bad_ranges_strings_flags_and_result_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id must not contain sensitive content"):
        domain_input(team_id="secret_team")
    with pytest.raises(ValueError, match="current_domain must not be empty"):
        domain_input(current_domain="")
    with pytest.raises(ValueError, match="recent_hit_rate must be between 0 and 1"):
        domain_input(recent_hit_rate=d("1.000001"))
    with pytest.raises(ValueError, match="calibration_error_bps must be finite"):
        domain_input(calibration_error_bps=Decimal("NaN"))
    with pytest.raises(ValueError, match="source_gap_rate must be between 0 and 1"):
        domain_input(source_gap_rate=d("-0.000001"))
    with pytest.raises(ValueError, match="days_in_domain must be an integer Decimal"):
        domain_input(days_in_domain=d("1.500000"))
    with pytest.raises(ValueError, match="domain_learning_score must be between 0 and 1"):
        domain_input(domain_learning_score=d("-0.000001"))
    with pytest.raises(ValueError, match="rotation_input must be"):
        module.recommend_strategy_team_domain_rotation_v10(object())
    with pytest.raises(ValueError, match="readonly must be True"):
        domain_input(readonly=False)

    result = recommend()
    with pytest.raises(ValueError, match="rotation_priority must match inputs"):
        replace(result, rotation_priority=ZERO)


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
        "order",
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
