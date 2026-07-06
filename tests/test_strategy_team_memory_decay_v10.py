from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_memory_decay_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.strategy_team_memory_decay_v10")


def d(value: str) -> Decimal:
    return Decimal(value)


def memory(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_rates",
        "specialty": "finance.macro.rates",
        "past_hit_rate": d("0.820000"),
        "calibration_error": d("0.060000"),
        "sample_size": d("40"),
        "days_since_last_resolved_market": d("20"),
        "recent_source_quality": d("0.880000"),
    }
    values.update(overrides)
    return module.TeamMemoryDecayV10Input(**values)


def score(**overrides: object):
    module = api()
    return module.score_team_memory_decay_v10(memory(**overrides))


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_current_high_quality_memory_stays_trusted_with_low_training_priority() -> None:
    result = score()

    assert is_dataclass(result)
    assert result.team_id == "macro_rates"
    assert result.specialty == "finance.macro.rates"
    assert result.adjusted_trust_score == d("0.880000")
    assert result.memory_status == "trusted"
    assert result.training_priority == "low"
    assert result.reason_codes == (
        "team_memory_trusted",
        "memory_decay_current",
        "hit_rate_strong",
        "calibration_error_low",
        "sample_size_strong",
        "source_quality_strong",
        "training_priority_low",
    )


def test_long_unresolved_gap_decays_trust_and_sets_high_training_priority() -> None:
    result = score(days_since_last_resolved_market=d("220"))

    assert result.adjusted_trust_score == d("0.484000")
    assert result.memory_status == "decayed"
    assert result.training_priority == "high"
    assert result.reason_codes == (
        "team_memory_decayed",
        "memory_decay_long_gap",
        "hit_rate_strong",
        "calibration_error_low",
        "sample_size_strong",
        "source_quality_strong",
        "training_priority_high",
    )


def test_low_sample_and_poor_calibration_watch_memory_before_full_decay() -> None:
    result = score(
        past_hit_rate=d("0.540000"),
        calibration_error=d("0.280000"),
        sample_size=d("5"),
        days_since_last_resolved_market=d("75"),
        recent_source_quality=d("0.420000"),
    )

    assert result.adjusted_trust_score == d("0.478800")
    assert result.memory_status == "watch"
    assert result.training_priority == "medium"
    assert result.reason_codes == (
        "team_memory_watch",
        "memory_decay_recent_gap",
        "hit_rate_watch",
        "calibration_error_high",
        "sample_size_low",
        "source_quality_watch",
        "training_priority_medium",
    )


def test_input_and_output_dataclasses_are_frozen_and_decimal_only() -> None:
    sample = memory()
    result = score()

    for item in (sample, result):
        with pytest.raises(FrozenInstanceError):
            item.team_id = "crypto_btc"  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "past_hit_rate",
                "calibration_error",
                "sample_size",
                "days_since_last_resolved_market",
                "recent_source_quality",
                "adjusted_trust_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("past_hit_rate", 0.82, "past_hit_rate must be exactly Decimal"),
        ("calibration_error", 0, "calibration_error must be exactly Decimal"),
        (
            "recent_source_quality",
            _DecimalSubclass("0.880000"),
            "recent_source_quality must be exactly Decimal",
        ),
        ("sample_size", d("4.5"), "sample_size must be an integral Decimal"),
        (
            "days_since_last_resolved_market",
            d("-1"),
            "days_since_last_resolved_market must be >= 0.000000",
        ),
        ("past_hit_rate", d("1.000001"), "past_hit_rate must be <= 1.000000"),
        ("calibration_error", Decimal("NaN"), "calibration_error must be finite"),
    ),
)
def test_validation_rejects_non_decimal_and_out_of_range_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        memory(**{field_name: bad_value})


def test_validation_rejects_blank_strings_and_wrong_function_input_type() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id must be a non-empty string"):
        memory(team_id=" ")
    with pytest.raises(ValueError, match="specialty must be a non-empty string"):
        memory(specialty="")
    with pytest.raises(ValueError, match="memory must be a TeamMemoryDecayV10Input"):
        module.score_team_memory_decay_v10(object())


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
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
        "http",
        "network",
        "order",
        "pathlib",
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
        "order",
        "persist",
        "rollback",
        "send",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
