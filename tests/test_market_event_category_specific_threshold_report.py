from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_event_category_specific_threshold_report import (
    DEFAULT_MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_CONFIG_VERSION,
    MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_STATUSES,
    MarketEventCategorySpecificThresholdReport,
    build_market_event_category_specific_threshold_report,
    market_event_category_specific_threshold_report_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


def payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(payload_values(item))
        return tuple(values)
    return (value,)


def report(**overrides: Any) -> MarketEventCategorySpecificThresholdReport:
    values: dict[str, Any] = {
        "category_id": "sports-basketball",
        "min_edge_probability": d("0.030000"),
        "min_source_quality_probability": d("0.700000"),
        "max_cost_probability": d("0.020000"),
        "max_latency_hours": d("6.000000"),
        "manual_override_required": False,
    }
    values.update(overrides)
    return build_market_event_category_specific_threshold_report(**values)


def test_ready_report_builds_public_payload_digest_and_flags() -> None:
    summary = report()

    assert summary.threshold_status == "pass"
    assert summary.reason_codes == ("category_specific_thresholds_ready",)
    assert (
        summary.manual_next_step
        == "Use the category-specific thresholds for paper-only screening review."
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.payload_digest) == 64

    payload = summary.public_payload
    assert payload == market_event_category_specific_threshold_report_payload(summary)
    assert market_event_category_specific_threshold_report_payload(payload) == payload
    assert payload["category_id"] == "sports-basketball"
    assert payload["min_edge_probability"] == "0.030000"
    assert payload["min_source_quality_probability"] == "0.700000"
    assert payload["max_cost_probability"] == "0.020000"
    assert payload["max_latency_hours"] == "6.000000"
    assert payload["manual_override_required"] is False
    assert payload["threshold_status"] == "pass"
    assert payload["reason_codes"] == ["category_specific_thresholds_ready"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == summary.payload_digest
    assert not any(type(value) in (int, float, Decimal) for value in payload_values(payload))

    tampered_payload = dict(payload)
    tampered_payload["threshold_status"] = "block"
    with pytest.raises(ValueError, match="payload_digest"):
        market_event_category_specific_threshold_report_payload(tampered_payload)


def test_threshold_breaches_and_manual_override_drive_status_and_next_step() -> None:
    blocked = report(
        min_edge_probability=d("0.005000"),
        min_source_quality_probability=d("0.400000"),
        max_cost_probability=d("0.060000"),
        max_latency_hours=d("48.000000"),
        manual_override_required=True,
    )

    assert blocked.threshold_status == "block"
    assert blocked.reason_codes == (
        "min_edge_probability_below_category_floor",
        "min_source_quality_probability_below_category_floor",
        "max_cost_probability_above_category_ceiling",
        "max_latency_hours_above_category_ceiling",
        "manual_override_required",
    )
    assert (
        blocked.manual_next_step
        == "Revise category-specific thresholds before paper-only screening review."
    )

    watched = report(manual_override_required=True)

    assert watched.threshold_status == "watch"
    assert watched.reason_codes == ("manual_override_required",)
    assert (
        watched.manual_next_step
        == "Complete manual override review before marking thresholds ready."
    )


def test_validation_rejects_non_decimal_bad_flags_and_inconsistent_reports() -> None:
    with pytest.raises(ValueError, match="min_edge_probability"):
        report(min_edge_probability=0.03)
    with pytest.raises(ValueError, match="min_source_quality_probability"):
        report(min_source_quality_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="max_cost_probability"):
        report(max_cost_probability=d("1.100000"))
    with pytest.raises(ValueError, match="max_latency_hours"):
        report(max_latency_hours=d("0.000000"))
    with pytest.raises(ValueError, match="category_id"):
        report(category_id="")
    with pytest.raises(ValueError, match="manual_override_required"):
        report(manual_override_required="false")
    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)

    summary = report()
    with pytest.raises(FrozenInstanceError):
        summary.threshold_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="threshold_status"):
        replace(summary, threshold_status="block", payload_digest="")
    with pytest.raises(ValueError, match="payload_digest"):
        replace(
            summary,
            max_cost_probability=d("0.040000"),
            payload_digest=summary.payload_digest,
        )


def test_module_is_phase1_readonly_decimal_only_and_public_surface() -> None:
    summary = report()

    assert is_dataclass(summary)
    assert DEFAULT_MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_CONFIG_VERSION == (
        "market-event-category-specific-threshold-report-v0"
    )
    assert MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    for item in fields(summary):
        item_value = getattr(summary, item.name)
        if item.name in {
            "category_id",
            "threshold_status",
            "reason_codes",
            "manual_next_step",
            "payload_digest",
            "paper_only",
            "report_only",
            "readonly",
            "manual_override_required",
        }:
            continue
        assert type(item_value) is Decimal

    import polymarket_alpha_lab.market_event_category_specific_threshold_report as module

    assert module.__all__ == (
        "DEFAULT_MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_CONFIG_VERSION",
        "MARKET_EVENT_CATEGORY_SPECIFIC_THRESHOLD_REPORT_STATUSES",
        "MarketEventCategorySpecificThresholdReport",
        "build_market_event_category_specific_threshold_report",
        "market_event_category_specific_threshold_report_payload",
    )

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

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
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_terms = (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "key" + "s",
        "sign" + "ing",
        "data" + "base",
        "connect",
        "execute",
        "write",
        "open(",
        "jsonl",
        "persist",
        "request",
        "socket",
        "subprocess",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

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
