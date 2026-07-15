from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.operator_research_queue_priority_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values = {
        "queued_item_count": d("0.000000"),
        "urgent_item_count": d("0.000000"),
        "stale_item_count": d("0.000000"),
        "manual_capacity_count": d("1.000000"),
        "oldest_sla_breach_hours": d("0.000000"),
    }
    values.update(overrides)
    inputs = module.OperatorResearchQueuePrioritySlaInput(**values)
    return module.build_operator_research_queue_priority_sla_report(inputs)


def test_empty_queue_returns_clear_readonly_report() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.OperatorResearchQueuePrioritySlaReport
    assert is_dataclass(report)
    assert report.queue_sla_status == "clear"
    assert report.reason_codes == ("operator_research_queue_priority_sla_clear",)
    assert report.manual_next_step == "continue_standard_research_queue_review"
    assert report.queued_item_count == d("0.000000")
    assert report.urgent_item_count == d("0.000000")
    assert report.stale_item_count == d("0.000000")
    assert report.manual_capacity_count == d("1.000000")
    assert report.oldest_sla_breach_hours == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_priority_sla_risk_statuses_reason_codes_and_steps_are_deterministic() -> None:
    watch = build_report(
        queued_item_count=d("3.000000"),
        urgent_item_count=d("1.000000"),
        stale_item_count=d("0.000000"),
        manual_capacity_count=d("2.000000"),
        oldest_sla_breach_hours=d("0.000000"),
    )
    assert watch.queue_sla_status == "watch"
    assert watch.reason_codes == (
        "operator_research_queue_priority_sla_backlog_above_capacity",
        "operator_research_queue_priority_sla_urgent_items_waiting",
    )
    assert watch.manual_next_step == "manually_reprioritize_urgent_research_items"

    breached = build_report(
        queued_item_count=d("8.000000"),
        urgent_item_count=d("2.000000"),
        stale_item_count=d("3.000000"),
        manual_capacity_count=d("1.000000"),
        oldest_sla_breach_hours=d("4.500000"),
    )
    assert breached.queue_sla_status == "breached"
    assert breached.reason_codes == (
        "operator_research_queue_priority_sla_backlog_above_capacity",
        "operator_research_queue_priority_sla_urgent_items_waiting",
        "operator_research_queue_priority_sla_stale_items_waiting",
        "operator_research_queue_priority_sla_oldest_breach_active",
    )
    assert breached.manual_next_step == "manually_triage_stale_and_urgent_research_items"

    blocked = build_report(
        queued_item_count=d("2.000000"),
        urgent_item_count=d("1.000000"),
        stale_item_count=d("0.000000"),
        manual_capacity_count=d("0.000000"),
        oldest_sla_breach_hours=d("0.000000"),
    )
    assert blocked.queue_sla_status == "blocked"
    assert blocked.reason_codes == (
        "operator_research_queue_priority_sla_no_manual_capacity",
        "operator_research_queue_priority_sla_backlog_above_capacity",
        "operator_research_queue_priority_sla_urgent_items_waiting",
    )
    assert blocked.manual_next_step == "manually_assign_research_capacity_before_triage"


def test_public_payload_is_immutable_decimal_string_only_and_digest_bound() -> None:
    module = api()
    report = build_report(
        queued_item_count=d("5.000000"),
        urgent_item_count=d("2.000000"),
        stale_item_count=d("1.000000"),
        manual_capacity_count=d("1.000000"),
        oldest_sla_breach_hours=d("2.250000"),
    )

    payload = report.public_payload
    assert type(payload) is module.OperatorResearchQueuePrioritySlaPublicPayload
    assert payload == module.operator_research_queue_priority_sla_report_payload(report)
    assert payload["queued_item_count"] == "5.000000"
    assert payload["urgent_item_count"] == "2.000000"
    assert payload["stale_item_count"] == "1.000000"
    assert payload["manual_capacity_count"] == "1.000000"
    assert payload["oldest_sla_breach_hours"] == "2.250000"
    assert payload["queue_sla_status"] == "breached"
    assert payload["payload_digest"] == report.payload_digest
    assert report.payload_digest == module.operator_research_queue_priority_sla_report_payload_digest(
        report,
    )
    json.dumps(payload)

    def assert_no_float_values(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float_values(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float_values(item)
        else:
            assert type(value) is not float

    assert_no_float_values(payload)
    with pytest.raises(TypeError, match="immutable"):
        payload["queue_sla_status"] = "clear"

    tampered_payload = dict(payload)
    tampered_payload["queued_item_count"] = "6.000000"
    with pytest.raises(ValueError, match="digest"):
        module.operator_research_queue_priority_sla_report_payload(tampered_payload)


def test_decimal_only_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "OPERATOR_RESEARCH_QUEUE_PRIORITY_SLA_REPORT_VERSION",
        "OperatorResearchQueuePrioritySlaInput",
        "OperatorResearchQueuePrioritySlaPublicPayload",
        "OperatorResearchQueuePrioritySlaReport",
        "build_operator_research_queue_priority_sla_report",
        "operator_research_queue_priority_sla_report_payload",
        "operator_research_queue_priority_sla_report_payload_digest",
    )
    assert is_dataclass(
        module.OperatorResearchQueuePrioritySlaInput(
            queued_item_count=d("1.000000"),
            urgent_item_count=d("0.000000"),
            stale_item_count=d("0.000000"),
            manual_capacity_count=d("1.000000"),
            oldest_sla_breach_hours=d("0.000000"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.queue_sla_status = "watch"
    with pytest.raises(ValueError, match="queued_item_count must be a Decimal"):
        build_report(queued_item_count=1)
    with pytest.raises(ValueError, match="urgent_item_count must be a Decimal"):
        build_report(urgent_item_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="nonnegative"):
        build_report(stale_item_count=d("-1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        module.OperatorResearchQueuePrioritySlaInput(
            queued_item_count=d("0.000000"),
            urgent_item_count=d("0.000000"),
            stale_item_count=d("0.000000"),
            manual_capacity_count=d("1.000000"),
            oldest_sla_breach_hours=d("0.000000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_module_scope_is_readonly_report_only_without_execution_or_persistence_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "submit",
        "cancel",
        "order",
        "execute",
        "jsonl",
        "persist",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
