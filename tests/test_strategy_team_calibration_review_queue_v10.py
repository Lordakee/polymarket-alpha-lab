from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_team_calibration_review_queue_v10"


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def queue_module():
    return importlib.import_module(MODULE_NAME)


def _build_result(**overrides: object):
    module = queue_module()
    fields = {
        "team_id": "team-alpha",
        "category": "macro",
        "resolved_market_count": d("64"),
        "recent_calibration_error": d("0.190000"),
        "hit_rate": d("0.420000"),
        "confidence_bias_score": d("0.140000"),
        "days_since_last_review": d("75"),
        "source_gap_rate": d("0.230000"),
    }
    fields.update(overrides)
    return module.build_team_calibration_review_queue_v10(**fields)


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return tuple(values)
    return (value,)


def test_queues_high_risk_team_calibration_review() -> None:
    result = _build_result()

    assert result.team_id == "team-alpha"
    assert result.category == "macro"
    assert result.review_status == "queued"
    assert result.review_priority == d("1.000000")
    assert result.recommended_review_type == "calibration_deep_dive"
    assert result.reason_codes == (
        "critical_calibration_error",
        "low_hit_rate",
        "overconfidence_bias",
        "stale_review_window",
        "source_gap",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_monitor_and_up_to_date_paths_are_stable() -> None:
    monitor = _build_result(
        resolved_market_count=d("34"),
        recent_calibration_error=d("0.090000"),
        hit_rate=d("0.570000"),
        confidence_bias_score=d("-0.080000"),
        days_since_last_review=d("12"),
        source_gap_rate=d("0.040000"),
    )

    assert monitor.review_status == "monitor"
    assert monitor.review_priority == d("0.250000")
    assert monitor.recommended_review_type == "monitoring_review"
    assert monitor.reason_codes == (
        "elevated_calibration_error",
        "elevated_confidence_bias",
    )

    up_to_date = _build_result(
        resolved_market_count=d("90"),
        recent_calibration_error=d("0.020000"),
        hit_rate=d("0.640000"),
        confidence_bias_score=d("0.010000"),
        days_since_last_review=d("15"),
        source_gap_rate=d("0.020000"),
    )

    assert up_to_date.review_status == "up_to_date"
    assert up_to_date.review_priority == d("0.000000")
    assert up_to_date.recommended_review_type == "no_review_needed"
    assert up_to_date.reason_codes == ("stable_calibration",)


def test_insufficient_history_blocks_review_queueing_until_sample_is_larger() -> None:
    result = _build_result(
        resolved_market_count=d("11"),
        recent_calibration_error=d("0.400000"),
        hit_rate=d("0.250000"),
        confidence_bias_score=d("0.300000"),
        days_since_last_review=d("200"),
        source_gap_rate=d("0.900000"),
    )

    assert result.review_status == "insufficient_data"
    assert result.review_priority == d("0.000000")
    assert result.recommended_review_type == "sample_size_review"
    assert result.reason_codes == ("insufficient_resolved_markets",)


def test_payload_uses_decimal_strings_and_rechecks_boundary() -> None:
    result = _build_result()

    payload = result.payload
    values = _walk_values(payload)

    assert payload["resolved_market_count"] == "64"
    assert payload["recent_calibration_error"] == "0.190000"
    assert payload["review_priority"] == "1.000000"
    assert payload["reason_codes"] == [
        "critical_calibration_error",
        "low_hit_rate",
        "overconfidence_bias",
        "stale_review_window",
        "source_gap",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, (Decimal, float)) for value in values)
    json.dumps(payload, sort_keys=True)

    object.__setattr__(result, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        result.payload


def test_rejects_non_decimal_invalid_values_and_inconsistent_results() -> None:
    module = queue_module()

    with pytest.raises(ValueError, match="team_id"):
        _build_result(team_id=" team-alpha")
    with pytest.raises(ValueError, match="category"):
        _build_result(category="")
    with pytest.raises(ValueError, match="resolved_market_count"):
        _build_result(resolved_market_count=64)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recent_calibration_error"):
        _build_result(recent_calibration_error=d("-0.000001"))
    with pytest.raises(ValueError, match="hit_rate"):
        _build_result(hit_rate=d("1.000001"))
    with pytest.raises(ValueError, match="confidence_bias_score"):
        _build_result(confidence_bias_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_gap_rate"):
        _build_result(source_gap_rate=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="days_since_last_review"):
        _build_result(days_since_last_review=d("1.500000"))
    with pytest.raises(ValueError, match="config"):
        _build_result(config="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        module.TeamCalibrationReviewQueueV10Config(paper_only=False)

    result = _build_result()
    with pytest.raises(ValueError, match="review_priority"):
        replace(result, review_priority=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("critical_calibration_error",))


def test_public_dataclasses_are_frozen_and_exact_type_checked() -> None:
    module = queue_module()
    result = _build_result()

    with pytest.raises(FrozenInstanceError):
        result.review_status = "monitor"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(module.TeamCalibrationReviewQueueV10Config):
            pass


def test_module_stays_readonly_report_scope() -> None:
    module = queue_module()
    source = inspect.getsource(module)
    lowered_source = source.lower()
    forbidden_markers = (
        "net" + "work",
        "li" + "ve",
        "tra" + "de",
        "au" + "th",
        "wall" + "et",
        "ord" + "er",
        "bro" + "ker",
        "can" + "cel",
        "rep" + "lace",
        "sig" + "ning",
    )

    assert all(marker not in lowered_source for marker in forbidden_markers)

    tree = ast.parse(source)
    imports = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports.isdisjoint(
        {
            "asyncio",
            "httpx",
            "pathlib",
            "pickle",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
        },
    )

    forbidden_name_calls = {"eval", "exec", "open", "compile", "__import__"}
    forbidden_attribute_calls = {
        "connect",
        "execute",
        "post",
        "put",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_name_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attribute_calls
