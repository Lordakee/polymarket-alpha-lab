from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_domain_risk_register_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_domain_risk_register_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "domain": "macro_rates",
        "team_code": "finance",
        "known_risk_count": d("4"),
        "unmitigated_risk_count": d("0"),
        "playbook_ready": True,
        "source_reliability_ready": True,
        "memory_quality_ready": True,
        "last_risk_review_age_seconds": d("86400"),
    }
    values.update(overrides)
    return module.build_specialist_team_domain_risk_register_report(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_ready_readonly_risk_register_report_payload_and_digest() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.domain == "macro_rates"
    assert report.team_code == "finance"
    assert report.known_risk_count == d("4")
    assert report.unmitigated_risk_count == d("0")
    assert report.risk_register_ready is True
    assert report.risk_score == d("1.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.digest == report.public_payload["digest"]

    payload = report.public_payload
    assert payload == {
        "domain": "macro_rates",
        "team_code": "finance",
        "known_risk_count": "4",
        "unmitigated_risk_count": "0",
        "playbook_ready": True,
        "source_reliability_ready": True,
        "memory_quality_ready": True,
        "last_risk_review_age_seconds": "86400",
        "risk_register_ready": True,
        "risk_score": "1.000000",
        "blocked_reason_codes": [],
        "attention_reason_codes": [],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": report.digest,
    }
    assert len(report.digest) == 64
    assert set(report.digest) <= set("0123456789abcdef")
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_unmitigated_risks_and_missing_gates_block_register() -> None:
    report = build_report(
        known_risk_count=d("6"),
        unmitigated_risk_count=d("2"),
        playbook_ready=False,
        source_reliability_ready=False,
        memory_quality_ready=False,
        last_risk_review_age_seconds=d("3456000"),
    )

    assert report.risk_register_ready is False
    assert report.risk_score == d("0.111111")
    assert report.ready_ratio == d("0.111111")
    assert report.blocked_reason_codes == (
        "specialist_team_domain_unmitigated_risks_present",
        "specialist_team_domain_playbook_not_ready",
        "specialist_team_domain_source_reliability_not_ready",
        "specialist_team_domain_memory_quality_not_ready",
    )
    assert report.attention_reason_codes == (
        "specialist_team_domain_risk_review_stale",
    )


def test_zero_known_risks_need_attention_but_do_not_block_by_themselves() -> None:
    report = build_report(known_risk_count=d("0"), unmitigated_risk_count=d("0"))

    assert report.risk_register_ready is False
    assert report.risk_score == d("0.800000")
    assert report.ready_ratio == d("0.800000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "specialist_team_domain_no_known_risks_recorded",
    )


def test_frozen_dataclass_decimal_only_and_hard_readonly_flags() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "SpecialistTeamDomainRiskRegisterReport",
        "build_specialist_team_domain_risk_register_report",
    )
    assert report.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        report.risk_register_ready = False  # type: ignore[misc]

    decimal_fields = {
        "known_risk_count",
        "unmitigated_risk_count",
        "last_risk_review_age_seconds",
        "risk_score",
        "ready_ratio",
    }
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
    ("field_name", "bad_value", "message"),
    (
        ("known_risk_count", _DecimalSubclass("1"), "known_risk_count must be exactly Decimal"),
        ("known_risk_count", d("1.5"), "known_risk_count must be an integral Decimal"),
        ("known_risk_count", d("-1"), "known_risk_count must be >= 0.000000"),
        (
            "unmitigated_risk_count",
            d("5"),
            "unmitigated_risk_count must be <= known_risk_count",
        ),
        (
            "last_risk_review_age_seconds",
            86400,
            "last_risk_review_age_seconds must be exactly Decimal",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_report(**{field_name: bad_value})


def test_rejects_unsafe_labels_bool_subclasses_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="domain must not be empty"):
        build_report(domain="")
    with pytest.raises(ValueError, match="unsafe public payload"):
        build_report(team_code="live_trading_team")
    with pytest.raises(ValueError, match="playbook_ready must be exactly bool"):
        build_report(playbook_ready=1)
    with pytest.raises(ValueError, match="digest must match report payload"):
        replace(build_report(), digest="0" * 64)
    with pytest.raises(ValueError, match="digest must match report payload"):
        replace(build_report(), ready_ratio=d("0.500000"))


def test_module_scope_has_no_database_network_or_execution_surface() -> None:
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
        "supabase",
        "trade",
        "wallet",
    )
    forbidden_call_fragments = (
        "auth",
        "connect",
        "delete",
        "execute",
        "insert",
        "order",
        "persist",
        "post",
        "put",
        "request",
        "send",
        "trade",
        "update",
        "upsert",
        "wallet",
    )

    assert float_constants == []
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        fragment in call_name.lower()
        for call_name in call_names
        for fragment in forbidden_call_fragments
    )
    assert not any(
        fragment in attribute_name.lower()
        for attribute_name in attribute_names
        for fragment in forbidden_call_fragments
    )
