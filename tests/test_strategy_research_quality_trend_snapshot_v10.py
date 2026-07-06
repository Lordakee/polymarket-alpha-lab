from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_research_quality_trend_snapshot_v10"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot_input(**overrides: object) -> Any:
    module = api()
    values = {
        "category": "crypto",
        "team_id": "team-alpha",
        "recent_packet_count": d("12"),
        "average_completeness_score": d("0.920000"),
        "average_source_confidence_score": d("0.880000"),
        "average_staleness_score": d("0.120000"),
        "calibration_error_bps": d("25.000000"),
        "days_window": d("14"),
    }
    values.update(overrides)
    return module.StrategyResearchQualityTrendSnapshotV10Input(**values)


def build(subject: object | None = None) -> Any:
    module = api()
    return module.build_strategy_research_quality_trend_snapshot_v10(
        snapshot_input() if subject is None else subject,
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
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_has_no_runtime_numbers(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_has_no_runtime_numbers(child)


def test_healthy_quality_trend_snapshot_returns_json_ready_payload() -> None:
    module = api()

    result = build()

    assert isinstance(result, module.StrategyResearchQualityTrendSnapshotV10Report)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.config_version == "strategy-research-quality-trend-snapshot-v10"
    assert result.category == "crypto"
    assert result.team_id == "team-alpha"
    assert result.quality_score == d("0.874500")
    assert result.trend_status == "healthy"
    assert result.improvement_actions == ("maintain_current_research_process",)
    assert result.reason_codes == (
        "sample_sufficient",
        "completeness_strong",
        "source_confidence_strong",
        "staleness_low",
        "calibration_error_controlled",
        "quality_trend_healthy",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    payload = result.payload
    assert payload == module.strategy_research_quality_trend_snapshot_v10_payload(result)
    assert payload["recent_packet_count"] == "12"
    assert payload["average_completeness_score"] == "0.920000"
    assert payload["average_source_confidence_score"] == "0.880000"
    assert payload["average_staleness_score"] == "0.120000"
    assert payload["calibration_error_bps"] == "25.000000"
    assert payload["days_window"] == "14"
    assert payload["quality_score"] == "0.874500"
    assert payload["improvement_actions"] == list(result.improvement_actions)
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_payload_has_no_runtime_numbers(payload)
    assert module.strategy_research_quality_trend_snapshot_v10(payload) == payload


def test_degrading_quality_trend_prioritizes_specific_improvement_actions() -> None:
    result = build(
        snapshot_input(
            recent_packet_count=d("8"),
            average_completeness_score=d("0.520000"),
            average_source_confidence_score=d("0.610000"),
            average_staleness_score=d("0.720000"),
            calibration_error_bps=d("175.000000"),
            days_window=d("7"),
        ),
    )

    assert result.quality_score == d("0.421000")
    assert result.trend_status == "degrading"
    assert result.improvement_actions == (
        "complete_missing_research_sections",
        "raise_source_confidence_quorum",
        "refresh_stale_research_packets",
        "review_calibration_error_drivers",
        "schedule_quality_recovery_review",
    )
    assert result.reason_codes == (
        "sample_sufficient",
        "completeness_weak",
        "source_confidence_weak",
        "staleness_high",
        "calibration_error_high",
        "quality_trend_degrading",
    )


def test_insufficient_sample_is_called_out_even_when_average_scores_are_strong() -> None:
    result = build(snapshot_input(recent_packet_count=d("1")))

    assert result.quality_score == d("0.874500")
    assert result.trend_status == "insufficient_data"
    assert result.improvement_actions == ("increase_recent_research_packet_sample",)
    assert result.reason_codes == (
        "sample_insufficient",
        "completeness_strong",
        "source_confidence_strong",
        "staleness_low",
        "calibration_error_controlled",
        "quality_trend_insufficient_data",
    )


def test_validation_requires_exact_decimal_inputs_frozen_reports_and_matching_codes() -> None:
    module = api()
    result = build()

    with pytest.raises(FrozenInstanceError):
        result.trend_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="recent_packet_count must be a Decimal"):
        snapshot_input(recent_packet_count=12)
    with pytest.raises(ValueError, match="average_completeness_score must be a Decimal"):
        snapshot_input(average_completeness_score=_DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="average_staleness_score must be finite"):
        snapshot_input(average_staleness_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="recent_packet_count must be a whole Decimal"):
        snapshot_input(recent_packet_count=d("1.500000"))
    with pytest.raises(ValueError, match="days_window must be above zero"):
        snapshot_input(days_window=d("0"))
    with pytest.raises(ValueError, match="average_source_confidence_score must be between zero and one"):
        snapshot_input(average_source_confidence_score=d("1.100000"))
    with pytest.raises(ValueError, match="calibration_error_bps must be nonnegative"):
        snapshot_input(calibration_error_bps=d("-1.000000"))
    with pytest.raises(ValueError, match="category must be a canonical nonblank string"):
        snapshot_input(category=" crypto ")
    with pytest.raises(ValueError, match="team_id must be a canonical nonblank string"):
        snapshot_input(team_id="")
    with pytest.raises(ValueError, match="paper_only must be True"):
        snapshot_input(paper_only=False)

    with pytest.raises(ValueError, match="report reason_codes must match"):
        module.StrategyResearchQualityTrendSnapshotV10Report(
            **{**result.__dict__, "reason_codes": ("quality_trend_watch",)},
        )
    with pytest.raises(ValueError, match="report readonly must be True"):
        module.StrategyResearchQualityTrendSnapshotV10Report(
            **{**result.__dict__, "readonly": False},
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()
    payload = build().payload

    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.strategy_research_quality_trend_snapshot_v10_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_research_quality_trend_snapshot_v10_payload(
            {**payload, "quality_score": 0.1},
        )
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_research_quality_trend_snapshot_v10_payload(
            {**payload, "recent_packet_count": 12},
        )
    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_research_quality_trend_snapshot_v10_payload(
            {**payload, "extra": "field"},
        )
    with pytest.raises(ValueError, match="report must be"):
        module.strategy_research_quality_trend_snapshot_v10_payload(object())


def test_module_is_paper_report_readonly_without_io_or_live_surfaces() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_quality_trend_snapshot_v10.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert module.StrategyResearchQualityTrendSnapshotV10Input.__dataclass_params__.frozen
    assert module.StrategyResearchQualityTrendSnapshotV10Report.__dataclass_params__.frozen
    assert module.StrategyResearchQualityTrendSnapshotV10Result is (
        module.StrategyResearchQualityTrendSnapshotV10Report
    )

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
        "open",
        "connect",
        "cancel",
        "create_order",
        "login",
        "place_order",
        "submit_order",
        "trade",
        "wallet",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "auth",
        "wallet",
        "broker",
        "order placement",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "database",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
