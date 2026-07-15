from __future__ import annotations

import ast
import importlib
import json
import sys
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.manual_decision_sla_breach_readiness_report"
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "manual_decision_sla_breach_readiness_report.py"
)
sys.path.insert(0, str(SRC_ROOT))


class DecimalSubclass(Decimal):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    decision_id: str,
    *,
    queued_age_hours: Decimal = d("1.000000"),
    market_close_hours: Decimal = d("48.000000"),
    source_refresh_due: bool = False,
    operator_owner_present: bool = True,
    blocking_reason_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    report_module = module()
    return report_module.ManualDecisionSlaBreachReadinessItem(
        decision_id=decision_id,
        queued_age_hours=queued_age_hours,
        market_close_hours=market_close_hours,
        source_refresh_due=source_refresh_due,
        operator_owner_present=operator_owner_present,
        blocking_reason_count=blocking_reason_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any) -> Any:
    report_module = module()
    return report_module.build_manual_decision_sla_breach_readiness_report(
        items,
        config=report_module.ManualDecisionSlaBreachReadinessConfig(
            config_version="manual-decision-sla-breach-readiness-test-v0",
            queued_watch_after_hours=d("4.000000"),
            queued_breach_after_hours=d("8.000000"),
            market_close_urgent_hours=d("6.000000"),
        ),
    )


def assert_json_safe_without_public_numbers(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_json_safe_without_public_numbers(item_value)
    elif isinstance(value, list):
        for item_value in value:
            assert_json_safe_without_public_numbers(item_value)
    else:
        assert value is None or isinstance(value, (str, bool))


def test_builds_manual_decision_sla_breach_rows_and_rollup() -> None:
    report = build_report(
        item("decision-pass"),
        item("decision-watch-age", queued_age_hours=d("4.000001")),
        item("decision-source-due", source_refresh_due=True),
        item("decision-no-owner", operator_owner_present=False),
        item("decision-blocking-reasons", blocking_reason_count=d("2.000000")),
        item(
            "decision-breach",
            queued_age_hours=d("8.000000"),
            market_close_hours=d("2.000000"),
        ),
    )

    assert report.sla_status == "breached"
    assert report.decision_count == d("6.000000")
    assert report.pass_decision_count == d("1.000000")
    assert report.watch_decision_count == d("3.000000")
    assert report.breached_decision_count == d("2.000000")
    assert report.operator_missing_decision_count == d("1.000000")
    assert report.source_refresh_due_decision_count == d("1.000000")
    assert report.blocking_reason_decision_count == d("1.000000")
    assert report.urgent_close_decision_count == d("1.000000")
    assert report.pass_decision_ratio == d("0.166667")
    assert report.reason_codes == (
        "manual_decision_sla_breached",
        "operator_owner_missing",
        "manual_decision_blocking_reasons_present",
        "source_refresh_due_before_manual_decision",
        "manual_decision_queue_age_watch",
    )
    assert tuple(row.decision_id for row in report.rows) == (
        "decision-blocking-reasons",
        "decision-breach",
        "decision-no-owner",
        "decision-pass",
        "decision-source-due",
        "decision-watch-age",
    )
    assert tuple(row.sla_status for row in report.rows) == (
        "breached",
        "breached",
        "watch",
        "pass",
        "watch",
        "watch",
    )
    assert tuple(row.breach_risk for row in report.rows) == (
        "critical",
        "critical",
        "elevated",
        "low",
        "elevated",
        "elevated",
    )
    assert report.rows[0].manual_next_step == "breach_report_only_clear_blocking_reasons"
    assert report.rows[1].reason_codes == (
        "manual_decision_sla_breached",
        "market_close_manual_decision_urgent",
    )
    assert report.rows[2].manual_next_step == "watch_report_only_assign_operator_owner"
    assert report.rows[3].reason_codes == ("manual_decision_sla_ready",)
    assert report.rows[3].manual_next_step == "allow_report_only_manual_decision_review"
    assert report.rows[4].manual_next_step == "watch_report_only_refresh_sources"
    assert report.rows[5].reason_codes == ("manual_decision_queue_age_watch",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_report_only_readonly_and_decimal_safe() -> None:
    report_module = module()
    report = build_report()

    assert type(report) is report_module.ManualDecisionSlaBreachReadinessReport
    assert report.sla_status == "breached"
    assert report.breach_risk == "critical"
    assert report.decision_count == d("0.000000")
    assert report.pass_decision_ratio == d("0.000000")
    assert report.reason_codes == ("no_manual_decision_sla_items",)
    assert report.rows == ()

    payload = report_module.manual_decision_sla_breach_readiness_report_payload(report)
    assert payload["decision_count"] == "0.000000"
    assert payload["pass_decision_ratio"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_json_safe_without_public_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_public_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    report_module = module()
    report = build_report(item("decision-decimal"))

    assert tuple(report_module.__all__) == (
        "DEFAULT_MANUAL_DECISION_SLA_BREACH_READINESS_CONFIG_VERSION",
        "ManualDecisionSlaBreachReadinessConfig",
        "ManualDecisionSlaBreachReadinessItem",
        "ManualDecisionSlaBreachReadinessReport",
        "ManualDecisionSlaBreachReadinessRow",
        "build_manual_decision_sla_breach_readiness_report",
        "manual_decision_sla_breach_readiness_report_payload",
    )
    for dataclass_type_name in (
        "ManualDecisionSlaBreachReadinessConfig",
        "ManualDecisionSlaBreachReadinessItem",
        "ManualDecisionSlaBreachReadinessReport",
        "ManualDecisionSlaBreachReadinessRow",
    ):
        dataclass_type = getattr(report_module, dataclass_type_name)
        assert is_dataclass(dataclass_type)
        assert all(field.init for field in fields(dataclass_type))

    with pytest.raises(FrozenInstanceError):
        report.rows[0].sla_status = "breached"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadItem", (report_module.ManualDecisionSlaBreachReadinessItem,), {})
    with pytest.raises(ValueError, match="queued_age_hours"):
        item("decision-float", queued_age_hours=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="queued_age_hours"):
        item("decision-subclass", queued_age_hours=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="blocking_reason_count"):
        item("decision-fractional", blocking_reason_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        item("decision-paper", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item("decision-report", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        item("decision-readonly", readonly=False)
    with pytest.raises(ValueError, match="decision_count"):
        replace(report, decision_count=d("2.000000"))
    with pytest.raises(ValueError, match="breach_risk"):
        replace(report.rows[0], breach_risk="medium")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(
            report.rows[0],
            manual_next_step="watch_report_only_assign_operator_owner",
        )
    with pytest.raises(ValueError, match="deterministic"):
        replace(
            build_report(item("decision-b"), item("decision-a")),
            rows=tuple(reversed(build_report(item("decision-b"), item("decision-a")).rows)),
        )


def test_payload_digest_rejects_tampering_and_is_immutable() -> None:
    report_module = module()
    report = build_report(item("decision-payload"))
    payload = report_module.manual_decision_sla_breach_readiness_report_payload(report)

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["sla_status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.manual_decision_sla_breach_readiness_report_payload(
            {
                **payload,
                "pass_decision_ratio": "0.500000",
            },
        )


def test_module_is_readonly_report_only_and_external_surface_free() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    assert set(_imported_modules(tree)) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    normalized_names = {
        _normalize_identifier(name)
        for name in _collected_names(tree)
        if _normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "persist",
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "account",
        "broker",
        "submit",
        "cancel",
        "signing",
    ):
        assert not any(fragment in name for name in normalized_names), fragment

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "input",
                "open",
                "print",
                "read",
                "write",
            }


def _imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def _collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
