from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_news_catalyst_timing_risk_report import (
    ProbabilityEventNewsCatalystTimingRiskReport,
    build_probability_event_news_catalyst_timing_risk_report,
    probability_event_news_catalyst_timing_risk_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_news_catalyst_timing_risk_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventNewsCatalystTimingRiskReport:
    values = {
        "catalyst_count": d("2.000000"),
        "next_catalyst_hours": d("48.000000"),
        "forecast_age_hours": d("2.000000"),
        "source_refresh_age_hours": d("1.000000"),
        "market_close_hours": d("96.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_news_catalyst_timing_risk_report(**values)


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
                "order",
                "key",
                "sign",
                "execute",
                "database",
                "jsonl",
                "file_persistence",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_supported_news_catalyst_timing_report_payload_and_digest() -> None:
    timing = report()

    assert isinstance(timing, ProbabilityEventNewsCatalystTimingRiskReport)
    assert timing.catalyst_timing_status == "supported"
    assert timing.reason_codes == ("catalyst_timing_supported",)
    assert timing.manual_next_step == "continue_monitoring_public_catalysts"
    assert len(timing.payload_digest) == 64

    payload = timing.public_payload
    assert payload == probability_event_news_catalyst_timing_risk_report_payload(
        timing,
    )
    assert payload["catalyst_count"] == "2.000000"
    assert payload["next_catalyst_hours"] == "48.000000"
    assert payload["forecast_age_hours"] == "2.000000"
    assert payload["source_refresh_age_hours"] == "1.000000"
    assert payload["market_close_hours"] == "96.000000"
    assert payload["catalyst_timing_status"] == "supported"
    assert payload["reason_codes"] == ["catalyst_timing_supported"]
    assert payload["manual_next_step"] == "continue_monitoring_public_catalysts"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == timing.payload_digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_status_surfaces_stale_research_and_near_catalyst_reasons() -> None:
    timing = report(
        next_catalyst_hours=d("8.000000"),
        forecast_age_hours=d("8.000000"),
        source_refresh_age_hours=d("3.000000"),
        market_close_hours=d("12.000000"),
    )

    assert timing.catalyst_timing_status == "watch"
    assert timing.reason_codes == (
        "next_catalyst_watch_window",
        "forecast_age_watch_stale",
        "source_refresh_watch_stale",
        "market_close_watch_window",
    )
    assert timing.manual_next_step == "manual_review_catalyst_timing_before_reuse"


def test_block_status_requires_refresh_when_catalyst_timing_is_not_reusable() -> None:
    timing = report(
        catalyst_count=d("0.000000"),
        next_catalyst_hours=d("1.000000"),
        forecast_age_hours=d("24.000000"),
        source_refresh_age_hours=d("12.000000"),
        market_close_hours=d("1.000000"),
    )

    assert timing.catalyst_timing_status == "block"
    assert timing.reason_codes == (
        "no_public_catalyst",
        "next_catalyst_imminent",
        "forecast_age_expired",
        "source_refresh_expired",
        "market_close_imminent",
    )
    assert timing.manual_next_step == (
        "refresh_public_news_catalysts_before_probability_use"
    )


def test_frozen_decimal_only_flags_and_consistency_validation() -> None:
    timing = report()

    assert is_dataclass(ProbabilityEventNewsCatalystTimingRiskReport)
    assert timing.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        timing.catalyst_timing_status = "block"  # type: ignore[misc]

    for field in fields(timing):
        value = getattr(timing, field.name)
        if field.name.endswith("_hours") or field.name == "catalyst_count":
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(timing, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(timing, readonly=False)
    with pytest.raises(ValueError, match="catalyst_count"):
        report(catalyst_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="next_catalyst_hours"):
        report(next_catalyst_hours=_DecimalSubclass("8.000000"))
    with pytest.raises(ValueError, match="forecast_age_hours"):
        report(forecast_age_hours=2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_refresh_age_hours"):
        report(source_refresh_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="market_close_hours"):
        report(market_close_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="catalyst_timing_status"):
        replace(timing, catalyst_timing_status="ready")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(timing, manual_next_step="reuse_without_review")


def test_public_payload_rejects_tampered_reason_status_and_numeric_values() -> None:
    timing = report()

    object.__setattr__(timing, "reason_codes", ("unsupported_reason",))
    with pytest.raises(ValueError, match="reason_code"):
        probability_event_news_catalyst_timing_risk_report_payload(timing)

    rebuilt = report()
    object.__setattr__(rebuilt, "catalyst_timing_status", "watch")
    with pytest.raises(ValueError, match="catalyst_timing_status"):
        probability_event_news_catalyst_timing_risk_report_payload(rebuilt)

    numeric = report()
    object.__setattr__(numeric, "forecast_age_hours", 2)
    with pytest.raises(ValueError, match="numeric payload values"):
        probability_event_news_catalyst_timing_risk_report_payload(numeric)


def test_pure_readonly_report_only_module_has_no_io_persistence_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "private_key",
        "order",
        "signature",
        "signing",
        "sign_",
        "execute",
        "execution",
        "database",
        "network",
        "jsonl",
        "persistence",
        "persist",
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
