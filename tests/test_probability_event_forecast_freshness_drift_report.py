from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_forecast_freshness_drift_report import (
    ProbabilityEventForecastFreshnessDriftReport,
    build_probability_event_forecast_freshness_drift_report,
    probability_event_forecast_freshness_drift_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_forecast_freshness_drift_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventForecastFreshnessDriftReport:
    values = {
        "forecast_age_hours": d("2.000000"),
        "market_price_move_probability": d("0.020000"),
        "source_refresh_age_hours": d("1.000000"),
        "event_time_to_close_hours": d("48.000000"),
        "model_confidence_drift": d("0.030000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_forecast_freshness_drift_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in (
                "live",
                "auth",
                "wallet",
                "position",
                "database",
                "network",
            ):
                assert forbidden not in lowered_key
            for forbidden in (
                "submit_order",
                "cancel_order",
                "replace_order",
                "create_order",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_fresh_forecast_report_emits_decimal_payload_and_digest() -> None:
    freshness = report()

    assert isinstance(freshness, ProbabilityEventForecastFreshnessDriftReport)
    assert freshness.freshness_status == "fresh"
    assert freshness.drift_level == "low"
    assert freshness.reason_codes == ("forecast_fresh",)
    assert freshness.manual_next_step == "continue_monitoring"
    assert len(freshness.digest) == 64

    payload = freshness.public_payload
    assert payload == probability_event_forecast_freshness_drift_report_payload(
        freshness,
    )
    assert payload["forecast_age_hours"] == "2.000000"
    assert payload["market_price_move_probability"] == "0.020000"
    assert payload["source_refresh_age_hours"] == "1.000000"
    assert payload["event_time_to_close_hours"] == "48.000000"
    assert payload["model_confidence_drift"] == "0.030000"
    assert payload["freshness_status"] == "fresh"
    assert payload["drift_level"] == "low"
    assert payload["manual_next_step"] == "continue_monitoring"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == freshness.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_stale_forecast_report_surfaces_manual_review_reasons() -> None:
    freshness = report(
        forecast_age_hours=d("6.000000"),
        market_price_move_probability=d("0.050000"),
        source_refresh_age_hours=d("3.000000"),
        event_time_to_close_hours=d("4.000000"),
        model_confidence_drift=d("0.100000"),
    )

    assert freshness.freshness_status == "stale"
    assert freshness.drift_level == "medium"
    assert freshness.reason_codes == (
        "forecast_age_watch_stale",
        "market_price_move_watch",
        "source_refresh_watch_stale",
        "event_close_watch_window",
        "model_confidence_drift_watch",
    )
    assert freshness.manual_next_step == "manual_review_forecast_before_reuse"


def test_expired_forecast_report_requires_rebuild_before_reuse() -> None:
    freshness = report(
        forecast_age_hours=d("24.000000"),
        market_price_move_probability=d("0.200000"),
        source_refresh_age_hours=d("12.000000"),
        event_time_to_close_hours=d("1.000000"),
        model_confidence_drift=d("0.250000"),
    )

    assert freshness.freshness_status == "expired"
    assert freshness.drift_level == "high"
    assert freshness.reason_codes == (
        "forecast_age_expired",
        "market_price_move_high",
        "source_refresh_expired",
        "event_close_imminent",
        "model_confidence_drift_high",
    )
    assert freshness.manual_next_step == (
        "refresh_inputs_and_rebuild_forecast_before_reuse"
    )


def test_frozen_flags_decimal_validation_and_report_consistency() -> None:
    freshness = report()

    assert is_dataclass(ProbabilityEventForecastFreshnessDriftReport)
    assert freshness.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        freshness.freshness_status = "expired"  # type: ignore[misc]

    for field in fields(freshness):
        value = getattr(freshness, field.name)
        if field.name.endswith("_hours") or "probability" in field.name:
            assert type(value) is Decimal
        if field.name == "model_confidence_drift":
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(freshness, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(freshness, readonly=False)
    with pytest.raises(ValueError, match="forecast_age_hours"):
        report(forecast_age_hours=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_price_move_probability"):
        report(market_price_move_probability=0.02)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_refresh_age_hours"):
        report(source_refresh_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="event_time_to_close_hours"):
        report(event_time_to_close_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="model_confidence_drift"):
        report(model_confidence_drift=d("1.000001"))
    with pytest.raises(ValueError, match="freshness_status"):
        replace(freshness, freshness_status="ready")
    with pytest.raises(ValueError, match="drift_level"):
        replace(freshness, drift_level="severe")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(freshness, manual_next_step="continue_monitoring_anyway")


def test_public_payload_rejects_tampered_reason_and_numeric_values() -> None:
    freshness = report()

    object.__setattr__(freshness, "reason_codes", ("unsupported_reason",))
    with pytest.raises(ValueError, match="reason_code"):
        probability_event_forecast_freshness_drift_report_payload(freshness)

    rebuilt = report()
    object.__setattr__(rebuilt, "forecast_age_hours", 2)
    with pytest.raises(ValueError, match="numeric payload values"):
        probability_event_forecast_freshness_drift_report_payload(rebuilt)


def test_pure_readonly_report_only_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
