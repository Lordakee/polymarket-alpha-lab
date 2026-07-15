from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_knowledge_base_index_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_knowledge_base_index_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values = {
        "playbook_ready": True,
        "risk_register_ready": True,
        "memory_quality_ready": True,
        "postmortem_ready": True,
        "learning_dashboard_ready": True,
        "source_family_feedback_ready": True,
        "supabase_memory_ready": True,
        "public_payload_safety_ready": True,
    }
    values.update(overrides)
    return module.build_specialist_team_knowledge_base_index_report(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_ready_report_has_public_payload_digest_and_decimal_ratio() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.knowledge_base_index_ready is True
    assert report.index_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.ready_ratio == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.digest) == 64

    payload = report.public_payload
    assert payload == {
        "playbook_ready": True,
        "risk_register_ready": True,
        "memory_quality_ready": True,
        "postmortem_ready": True,
        "learning_dashboard_ready": True,
        "source_family_feedback_ready": True,
        "supabase_memory_ready": True,
        "public_payload_safety_ready": True,
        "knowledge_base_index_ready": True,
        "index_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": report.digest,
    }
    assert payload["digest"] == report.digest
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_attention_report_scores_partial_index_without_blockers() -> None:
    report = build_report(
        postmortem_ready=False,
        learning_dashboard_ready=False,
        source_family_feedback_ready=False,
    )

    assert report.knowledge_base_index_ready is False
    assert report.index_band == "attention"
    assert report.ready_ratio == d("0.625000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "specialist_team_postmortem_index_attention",
        "specialist_team_learning_dashboard_index_attention",
        "specialist_team_source_family_feedback_index_attention",
    )


def test_blocked_report_prioritizes_core_index_gaps() -> None:
    report = build_report(
        playbook_ready=False,
        risk_register_ready=False,
        memory_quality_ready=False,
        supabase_memory_ready=False,
        public_payload_safety_ready=False,
    )

    assert report.knowledge_base_index_ready is False
    assert report.index_band == "blocked"
    assert report.ready_ratio == d("0.375000")
    assert report.blocked_reason_codes == (
        "specialist_team_playbook_index_blocked",
        "specialist_team_risk_register_index_blocked",
        "specialist_team_memory_quality_index_blocked",
        "specialist_team_supabase_memory_index_blocked",
        "specialist_team_public_payload_safety_index_blocked",
    )
    assert report.attention_reason_codes == ()


def test_frozen_dataclass_decimal_only_and_hard_flags() -> None:
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.ready_ratio = d("0.500000")  # type: ignore[misc]

    decimal_fields = {"ready_ratio"}
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name in decimal_fields:
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        build_report(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        build_report(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(readonly=False)


@pytest.mark.parametrize(
    "field_name",
    (
        "playbook_ready",
        "risk_register_ready",
        "memory_quality_ready",
        "postmortem_ready",
        "learning_dashboard_ready",
        "source_family_feedback_ready",
        "supabase_memory_ready",
        "public_payload_safety_ready",
    ),
)
def test_rejects_non_bool_readiness_inputs(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be a bool"):
        build_report(**{field_name: 1})


def test_report_rejects_digest_or_derived_field_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="digest must match report payload"):
        replace(report, digest="0" * 64)
    with pytest.raises(ValueError, match="knowledge_base_index_ready must match reason codes"):
        replace(report, knowledge_base_index_ready=False)
    with pytest.raises(ValueError, match="ready_ratio must match readiness inputs"):
        replace(report, ready_ratio=d("0.500000"))


def test_module_scope_is_readonly_report_only_and_side_effect_free() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "subprocess",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_calls = {
        "connect",
        "delete",
        "execute",
        "from_env",
        "get",
        "open",
        "patch",
        "post",
        "put",
        "read_text",
        "remove",
        "replace",
        "request",
        "send",
        "submit",
        "unlink",
        "write",
        "write_text",
    }
    forbidden_attributes = {
        "auth",
        "buy",
        "cancel",
        "connect",
        "delete",
        "execute",
        "insert",
        "order",
        "persist",
        "sell",
        "sign",
        "trade",
        "update",
        "wallet",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_calls)
    assert not (set(attribute_names) & forbidden_attributes)
