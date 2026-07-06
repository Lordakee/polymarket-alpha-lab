from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_team_review_capacity_forecast_v10 import (
    DEFAULT_STRATEGY_TEAM_REVIEW_CAPACITY_FORECAST_V10_CONFIG_VERSION,
    REASON_CODES,
    REVIEW_CAPACITY_STATUSES,
    StrategyTeamReviewCapacityForecastV10Config,
    StrategyTeamReviewCapacityForecastV10Input,
    StrategyTeamReviewCapacityForecastV10Report,
    forecast_strategy_team_review_capacity_v10,
    strategy_team_review_capacity_forecast_v10_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _forecast(**overrides: object) -> StrategyTeamReviewCapacityForecastV10Input:
    values = {
        "active_analyst_count": d("2"),
        "urgent_candidate_count": d("3"),
        "stale_packet_count": d("1"),
        "average_review_minutes": d("60.000000"),
        "quality_rework_rate": d("0.100000"),
    }
    values.update(overrides)
    return StrategyTeamReviewCapacityForecastV10Input(**values)


def test_capacity_forecast_blocks_when_rework_adjusted_demand_exceeds_capacity() -> None:
    report = forecast_strategy_team_review_capacity_v10(
        _forecast(
            active_analyst_count=d("1"),
            urgent_candidate_count=d("8"),
            stale_packet_count=d("4"),
            average_review_minutes=d("45.000000"),
            quality_rework_rate=d("0.200000"),
        ),
    )

    assert type(report) is StrategyTeamReviewCapacityForecastV10Report
    assert (
        report.config_version
        == DEFAULT_STRATEGY_TEAM_REVIEW_CAPACITY_FORECAST_V10_CONFIG_VERSION
    )
    assert report.total_candidate_count == d("12")
    assert report.adjusted_review_minutes_per_candidate == d("54.000000")
    assert report.available_review_minutes == d("360.000000")
    assert report.demand_review_minutes == d("648.000000")
    assert report.forecast_capacity_candidate_count == d("6.666667")
    assert report.projected_backlog_candidate_count == d("5.333333")
    assert report.capacity_gap_minutes == d("288.000000")
    assert report.capacity_gap_candidate_count == d("5.333333")
    assert report.capacity_buffer_minutes == d("0.000000")
    assert report.capacity_buffer_ratio == d("0.000000")
    assert report.demand_coverage_ratio == d("0.555556")
    assert report.review_capacity_status == "blocked"
    assert report.reason_codes == (
        "active_analyst_capacity_available",
        "urgent_candidates_present",
        "stale_packets_present",
        "quality_rework_load",
        "capacity_gap_present",
        "review_capacity_blocked",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_decimal_public_metrics(report)


def test_capacity_forecast_watches_when_buffer_is_below_minimum() -> None:
    report = forecast_strategy_team_review_capacity_v10(
        _forecast(
            active_analyst_count=d("2"),
            urgent_candidate_count=d("4"),
            stale_packet_count=d("1"),
            average_review_minutes=d("120.000000"),
            quality_rework_rate=d("0.000000"),
        ),
    )

    assert report.total_candidate_count == d("5")
    assert report.available_review_minutes == d("720.000000")
    assert report.demand_review_minutes == d("600.000000")
    assert report.capacity_buffer_minutes == d("120.000000")
    assert report.capacity_buffer_ratio == d("0.166667")
    assert report.demand_coverage_ratio == d("1.200000")
    assert report.review_capacity_status == "watch"
    assert report.reason_codes == (
        "active_analyst_capacity_available",
        "urgent_candidates_present",
        "stale_packets_present",
        "capacity_buffer_watch",
        "review_capacity_watch",
    )


def test_capacity_forecast_passes_empty_queue_and_payload_is_json_ready() -> None:
    report = forecast_strategy_team_review_capacity_v10(
        _forecast(
            active_analyst_count=d("0"),
            urgent_candidate_count=d("0"),
            stale_packet_count=d("0"),
            average_review_minutes=d("30.000000"),
            quality_rework_rate=d("0.000000"),
        ),
    )

    payload = strategy_team_review_capacity_forecast_v10_payload(report)

    assert report.review_capacity_status == "pass"
    assert report.reason_codes == (
        "review_queue_clear",
        "no_active_analysts",
        "capacity_buffer_sufficient",
        "review_capacity_pass",
    )
    assert payload == report.payload
    assert payload["active_analyst_count"] == "0"
    assert payload["urgent_candidate_count"] == "0"
    assert payload["stale_packet_count"] == "0"
    assert payload["average_review_minutes"] == "30.000000"
    assert payload["quality_rework_rate"] == "0.000000"
    assert payload["forecast_capacity_candidate_count"] == "0.000000"
    assert payload["demand_coverage_ratio"] == "1.000000"
    assert payload["review_capacity_status"] == "pass"
    assert payload["reason_codes"] == [
        "review_queue_clear",
        "no_active_analysts",
        "capacity_buffer_sufficient",
        "review_capacity_pass",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_capacity_forecast_validates_decimal_only_inputs_flags_and_freezing() -> None:
    forecast = _forecast()
    report = forecast_strategy_team_review_capacity_v10(forecast)

    assert is_dataclass(forecast)
    assert is_dataclass(report)
    with pytest.raises(FrozenInstanceError):
        forecast.active_analyst_count = d("3")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.review_capacity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="active_analyst_count must be a Decimal"):
        _forecast(active_analyst_count=2)
    with pytest.raises(ValueError, match="urgent_candidate_count must be a whole Decimal"):
        _forecast(urgent_candidate_count=d("1.500000"))
    with pytest.raises(ValueError, match="average_review_minutes must be positive"):
        _forecast(average_review_minutes=d("0.000000"))
    with pytest.raises(ValueError, match="quality_rework_rate must be between"):
        _forecast(quality_rework_rate=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(forecast, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="analyst_review_minutes_per_day must be positive"):
        StrategyTeamReviewCapacityForecastV10Config(
            analyst_review_minutes_per_day=d("0.000000"),
        )
    with pytest.raises(ValueError, match="minimum_capacity_buffer_ratio must be a Decimal"):
        StrategyTeamReviewCapacityForecastV10Config(
            minimum_capacity_buffer_ratio=_DecimalSubclass("0.200000"),
        )


def test_capacity_forecast_blocks_when_candidates_exist_without_active_analysts() -> None:
    report = forecast_strategy_team_review_capacity_v10(
        _forecast(
            active_analyst_count=d("0"),
            urgent_candidate_count=d("2"),
            stale_packet_count=d("1"),
            average_review_minutes=d("50.000000"),
            quality_rework_rate=d("0.000000"),
        ),
    )

    assert report.review_capacity_status == "blocked"
    assert report.available_review_minutes == d("0.000000")
    assert report.demand_review_minutes == d("150.000000")
    assert report.projected_backlog_candidate_count == d("3.000000")
    assert report.capacity_gap_candidate_count == d("3.000000")
    assert report.reason_codes == (
        "no_active_analysts",
        "urgent_candidates_present",
        "stale_packets_present",
        "capacity_gap_present",
        "review_capacity_blocked",
    )


def test_capacity_forecast_exposes_only_pure_report_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_team_review_capacity_forecast_v10",
    )
    source = inspect.getsource(module)
    tree = ast.parse(source)
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "network",
        "persist",
        "live",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "wallet",
        "account",
        "broker",
        "submit",
        "cancel",
        "signing",
        "trade",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
    )

    assert REVIEW_CAPACITY_STATUSES == ("pass", "watch", "blocked")
    assert "review_capacity_blocked" in REASON_CODES
    assert module.__all__ == (
        "DEFAULT_STRATEGY_TEAM_REVIEW_CAPACITY_FORECAST_V10_CONFIG_VERSION",
        "REASON_CODES",
        "REVIEW_CAPACITY_STATUSES",
        "StrategyTeamReviewCapacityForecastV10Config",
        "StrategyTeamReviewCapacityForecastV10Input",
        "StrategyTeamReviewCapacityForecastV10Report",
        "forecast_strategy_team_review_capacity_v10",
        "strategy_team_review_capacity_forecast_v10_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "decimal",
        "typing",
        "polymarket_alpha_lab",
    }

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names


def _assert_decimal_public_metrics(value: object) -> None:
    assert is_dataclass(value)
    for field in fields(value):
        if field.name.endswith(
            (
                "minutes",
                "rate",
                "ratio",
                "count",
            ),
        ):
            assert type(getattr(value, field.name)) is Decimal


def _assert_no_floats(value: Any) -> None:
    assert not isinstance(value, float)
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)
