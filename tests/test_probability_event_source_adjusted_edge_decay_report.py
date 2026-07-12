from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_source_adjusted_edge_decay_report import (
    ProbabilityEventSourceAdjustedEdgeDecayReport,
    build_probability_event_source_adjusted_edge_decay_report,
    probability_event_source_adjusted_edge_decay_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_source_adjusted_edge_decay_report.py",
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventSourceAdjustedEdgeDecayReport:
    values = {
        "raw_edge_probability": d("0.180000"),
        "source_age_hours": d("3.000000"),
        "source_quality_probability": d("0.900000"),
        "market_move_probability": d("0.020000"),
        "decay_penalty_probability": d("0.010000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_source_adjusted_edge_decay_report(**values)


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
                "key",
                "sign",
                "database",
                "network",
                "execute",
            ):
                assert forbidden not in lowered_key
            for forbidden in (
                "submit_order",
                "cancel_order",
                "replace_order",
                "create_order",
                "auto_execute",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_ready_source_adjusted_edge_report_emits_decimal_payload_and_digest() -> None:
    adjusted = report()

    assert isinstance(adjusted, ProbabilityEventSourceAdjustedEdgeDecayReport)
    assert adjusted.edge_decay_status == "ready_for_manual_review"
    assert adjusted.source_adjusted_edge_probability == d("0.132000")
    assert adjusted.reason_codes == ("source_adjusted_edge_ready",)
    assert adjusted.manual_next_step == "review_source_adjusted_edge"
    assert len(adjusted.payload_digest) == 64

    payload = adjusted.public_payload
    assert payload == probability_event_source_adjusted_edge_decay_report_payload(adjusted)
    assert payload["raw_edge_probability"] == "0.180000"
    assert payload["source_age_hours"] == "3.000000"
    assert payload["source_quality_probability"] == "0.900000"
    assert payload["market_move_probability"] == "0.020000"
    assert payload["decay_penalty_probability"] == "0.010000"
    assert payload["source_adjusted_edge_probability"] == "0.132000"
    assert payload["edge_decay_status"] == "ready_for_manual_review"
    assert payload["reason_codes"] == ("source_adjusted_edge_ready",)
    assert payload["manual_next_step"] == "review_source_adjusted_edge"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == adjusted.payload_digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_report_surfaces_stale_source_quality_and_market_move_reasons() -> None:
    adjusted = report(
        raw_edge_probability=d("0.120000"),
        source_age_hours=d("30.000000"),
        source_quality_probability=d("0.550000"),
        market_move_probability=d("0.070000"),
        decay_penalty_probability=d("0.020000"),
    )

    assert adjusted.edge_decay_status == "watch"
    assert adjusted.source_adjusted_edge_probability == d("-0.024000")
    assert adjusted.reason_codes == (
        "source_adjusted_edge_nonpositive",
        "source_quality_probability_watch",
        "source_age_hours_stale",
        "market_move_probability_watch",
    )
    assert adjusted.manual_next_step == "refresh_source_and_recompute_edge"


def test_blocked_report_surfaces_expired_source_and_excessive_decay_penalty() -> None:
    adjusted = report(
        raw_edge_probability=d("0.040000"),
        source_age_hours=d("50.000000"),
        source_quality_probability=d("0.350000"),
        market_move_probability=d("0.150000"),
        decay_penalty_probability=d("0.200000"),
    )

    assert adjusted.edge_decay_status == "blocked"
    assert adjusted.source_adjusted_edge_probability == d("-0.336000")
    assert adjusted.reason_codes == (
        "source_adjusted_edge_nonpositive",
        "source_quality_probability_block",
        "source_age_hours_expired",
        "market_move_probability_block",
        "decay_penalty_probability_block",
    )
    assert adjusted.manual_next_step == "do_not_trade_refresh_primary_source"


def test_frozen_decimal_only_flags_and_derived_consistency() -> None:
    adjusted = report()

    assert is_dataclass(ProbabilityEventSourceAdjustedEdgeDecayReport)
    assert adjusted.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        adjusted.edge_decay_status = "blocked"  # type: ignore[misc]

    for field in fields(adjusted):
        value = getattr(adjusted, field.name)
        if field.name.endswith("_probability") or field.name == "source_age_hours":
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(adjusted, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(adjusted, readonly=False)
    with pytest.raises(ValueError, match="raw_edge_probability"):
        report(raw_edge_probability=0.18)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_age_hours"):
        report(source_age_hours=-1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_quality_probability"):
        report(source_quality_probability=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="source_adjusted_edge_probability"):
        replace(adjusted, source_adjusted_edge_probability=d("0.131000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(adjusted, reason_codes=("source_age_hours_expired",))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(adjusted, manual_next_step="trade_now")
    with pytest.raises(ValueError, match="payload_digest"):
        replace(adjusted, payload_digest="0" * 64)


def test_pure_readonly_report_only_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "private_key",
        "secret",
        "signature",
        "signing",
        "database",
        "persist",
        "network",
        "crawl",
        "scrape",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "auto_execute",
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
