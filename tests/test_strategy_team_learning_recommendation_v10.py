from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_team_learning_recommendation_v10"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_team_learning_recommendation_v10.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_TEAM_LEARNING_RECOMMENDATION_V10_CONFIG_VERSION
        ),
        "min_sample_size": d("30"),
        "stale_review_days": d("30"),
        "min_recent_hit_rate": d("0.500000"),
        "max_calibration_error_watch": d("0.150000"),
        "max_calibration_error_blocked": d("0.250000"),
        "max_source_gap_rate_watch": d("0.200000"),
        "max_source_gap_rate_blocked": d("0.350000"),
        "min_rationale_quality_score": d("0.650000"),
        "watch_training_priority": d("0.300000"),
        "blocked_training_priority": d("0.550000"),
    }
    values.update(overrides)
    return module.StrategyTeamLearningRecommendationV10Config(**values)


def memory_input(**overrides: object) -> Any:
    module = api()
    values = {
        "team_id": "macro_team",
        "category": "macro_rates",
        "recent_hit_rate": d("0.700000"),
        "calibration_error": d("0.050000"),
        "source_gap_rate": d("0.050000"),
        "rationale_quality_score": d("0.850000"),
        "sample_size": d("60"),
        "days_since_review": d("5"),
    }
    values.update(overrides)
    return module.StrategyTeamLearningRecommendationV10Input(**values)


def recommendation(row: Any | None = None, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_team_learning_recommendation_v10(
        row if row is not None else memory_input(),
        config=cfg or config(),
    )


def assert_no_json_numbers(value: object) -> None:
    assert type(value) is not float
    assert not (type(value) is int and type(value) is not bool)
    if isinstance(value, dict):
        for item in value.values():
            assert_no_json_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_json_numbers(item)


def test_recommendation_blocks_when_long_term_memory_is_degraded() -> None:
    module = api()
    result = recommendation(
        memory_input(
            team_id="sports_team",
            category="sports_soccer",
            recent_hit_rate=d("0.350000"),
            calibration_error=d("0.320000"),
            source_gap_rate=d("0.420000"),
            rationale_quality_score=d("0.450000"),
            sample_size=d("12"),
            days_since_review=d("45"),
        ),
    )

    assert is_dataclass(result)
    assert result.team_id == "sports_team"
    assert result.category == "sports_soccer"
    assert result.learning_status == "blocked"
    assert result.recommended_action == "run_deep_calibration_review"
    assert result.training_priority == d("0.519000")
    assert result.reason_codes == (
        "strategy_team_learning_recommendation_v10_recent_hit_rate_low",
        "strategy_team_learning_recommendation_v10_calibration_error_high",
        "strategy_team_learning_recommendation_v10_source_gap_high",
        "strategy_team_learning_recommendation_v10_rationale_quality_low",
        "strategy_team_learning_recommendation_v10_sample_size_low",
        "strategy_team_learning_recommendation_v10_review_stale",
        "strategy_team_learning_recommendation_v10_training_priority_elevated",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.strategy_team_learning_recommendation_v10_payload(result)
    assert result.payload == payload
    assert payload["team_id"] == "sports_team"
    assert payload["learning_status"] == "blocked"
    assert payload["training_priority"] == "0.519000"
    assert payload["sample_size"] == "12"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_json_numbers(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_recommendation_passes_when_memory_metrics_are_healthy() -> None:
    result = recommendation()

    assert result.learning_status == "pass"
    assert result.recommended_action == "keep_current_learning_plan"
    assert result.training_priority == d("0.128333")
    assert result.reason_codes == (
        "strategy_team_learning_recommendation_v10_learning_status_pass",
    )


def test_recommendation_watches_low_rationale_and_stale_review() -> None:
    result = recommendation(
        memory_input(
            recent_hit_rate=d("0.580000"),
            calibration_error=d("0.090000"),
            source_gap_rate=d("0.100000"),
            rationale_quality_score=d("0.500000"),
            sample_size=d("40"),
            days_since_review=d("44"),
        ),
    )

    assert result.learning_status == "watch"
    assert result.recommended_action == "improve_rationale_review"
    assert result.training_priority == d("0.272500")
    assert result.reason_codes == (
        "strategy_team_learning_recommendation_v10_rationale_quality_low",
        "strategy_team_learning_recommendation_v10_review_stale",
    )


def test_validation_rejects_bad_decimal_types_ranges_config_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="recent_hit_rate must be exactly Decimal"):
        memory_input(recent_hit_rate=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="calibration_error must be a Decimal"):
        memory_input(calibration_error=0.1)
    with pytest.raises(ValueError, match="source_gap_rate must be between zero and one"):
        memory_input(source_gap_rate=d("1.100000"))
    with pytest.raises(ValueError, match="sample_size must be integral"):
        memory_input(sample_size=d("3.5"))
    with pytest.raises(ValueError, match="days_since_review must be nonnegative"):
        memory_input(days_since_review=d("-1"))
    with pytest.raises(ValueError, match="team_id must be a nonblank trimmed string"):
        memory_input(team_id=_StringSubclass("macro_team"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_team_learning_recommendation_v10(
            memory_input(),
            config=object(),
        )

    result = recommendation()
    with pytest.raises(ValueError, match="learning_status"):
        replace(result, learning_status="unknown")
    with pytest.raises(ValueError, match="training_priority"):
        replace(result, training_priority=d("2.000000"))
    with pytest.raises(FrozenInstanceError):
        result.training_priority = d("0")  # type: ignore[misc]


def test_public_types_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    module = api()
    values = (config(), memory_input(), recommendation())
    numeric_suffixes = (
        "_rate",
        "_error",
        "_score",
        "_size",
        "_review",
        "_days",
        "_priority",
    )

    assert module.__all__ == (
        "DEFAULT_STRATEGY_TEAM_LEARNING_RECOMMENDATION_V10_CONFIG_VERSION",
        "StrategyTeamLearningRecommendationV10Config",
        "StrategyTeamLearningRecommendationV10Input",
        "StrategyTeamLearningRecommendationV10Report",
        "build_strategy_team_learning_recommendation_v10",
        "strategy_team_learning_recommendation_v10_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        module.StrategyTeamLearningRecommendationV10Config,
        module.StrategyTeamLearningRecommendationV10Input,
        module.StrategyTeamLearningRecommendationV10Report,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes):
                assert hints[field.name] is Decimal


def test_payload_dict_path_is_json_ready_readonly_and_decimal_stringed() -> None:
    module = api()
    payload = recommendation().payload

    assert module.strategy_team_learning_recommendation_v10_payload(payload) == payload
    assert payload["recent_hit_rate"] == "0.700000"
    assert payload["days_since_review"] == "5"

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_team_learning_recommendation_v10_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_team_learning_recommendation_v10_payload(
            {**payload, "sample_size": 60},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_team_learning_recommendation_v10_payload(
            {**payload, "training_priority": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_team_learning_recommendation_v10_payload(
            {**payload, "private_key": "hidden"},
        )


def test_module_is_pure_paper_report_readonly_without_io_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "private_key",
        "account",
        "broker",
        "place_order",
        "submit_order",
        "database",
        "http",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "psycopg",
        "sqlite",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            assert not ({alias.name.split(".", 1)[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in banned_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names
