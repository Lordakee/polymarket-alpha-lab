from __future__ import annotations

import ast
import importlib
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
    / "specialist_team_memory_quality_gate_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_memory_quality_gate_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object):
    module = api()
    values = {
        "team": "alpha_specialists",
        "domain": "macro_rates",
        "memory_sample_count": d("24"),
        "settled_sample_count": d("12"),
        "calibration_error_rate": d("0.090000"),
        "source_family_coverage_ratio": d("0.850000"),
        "last_memory_update_age_seconds": d("43200"),
        "supabase_persistence_ready": True,
        "schema_contract_ready": True,
    }
    values.update(overrides)
    return module.build_specialist_team_memory_quality_gate_report(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_pass_gate_report_payload_and_digest() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.memory_quality_band == "pass"
    assert report.can_use_for_screening is True
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.ready_ratio == d("1.000000")
    assert report.digest == report.public_payload["digest"]

    payload = report.public_payload
    assert payload == {
        "team": "alpha_specialists",
        "domain": "macro_rates",
        "memory_sample_count": "24",
        "settled_sample_count": "12",
        "calibration_error_rate": "0.090000",
        "source_family_coverage_ratio": "0.850000",
        "last_memory_update_age_seconds": "43200",
        "supabase_persistence_ready": True,
        "schema_contract_ready": True,
        "memory_quality_band": "pass",
        "can_use_for_screening": True,
        "blocked_reason_codes": [],
        "attention_reason_codes": [],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": report.digest,
    }
    assert len(report.digest) == 64
    assert_no_float_values(payload)


def test_watch_band_keeps_screening_blocked_until_attention_resolves() -> None:
    report = build_report(
        memory_sample_count=d("10"),
        settled_sample_count=d("4"),
        calibration_error_rate=d("0.170000"),
        source_family_coverage_ratio=d("0.650000"),
        last_memory_update_age_seconds=d("172800"),
    )

    assert report.memory_quality_band == "watch"
    assert report.can_use_for_screening is False
    assert report.ready_ratio == d("0.600000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "specialist_team_memory_sample_watch",
        "specialist_team_settled_sample_watch",
        "specialist_team_calibration_error_watch",
        "specialist_team_source_family_coverage_watch",
        "specialist_team_memory_freshness_watch",
    )


def test_blocked_band_reports_hard_reason_codes_and_not_ready() -> None:
    report = build_report(
        memory_sample_count=d("3"),
        settled_sample_count=d("0"),
        calibration_error_rate=d("0.310000"),
        source_family_coverage_ratio=d("0.450000"),
        last_memory_update_age_seconds=d("345600"),
        supabase_persistence_ready=False,
        schema_contract_ready=False,
    )

    assert report.memory_quality_band == "blocked"
    assert report.can_use_for_screening is False
    assert report.ready_ratio == d("0.000000")
    assert report.blocked_reason_codes == (
        "specialist_team_memory_sample_blocked",
        "specialist_team_settled_sample_blocked",
        "specialist_team_calibration_error_blocked",
        "specialist_team_source_family_coverage_blocked",
        "specialist_team_memory_freshness_blocked",
        "specialist_team_supabase_persistence_not_ready",
        "specialist_team_schema_contract_not_ready",
    )
    assert report.attention_reason_codes == ()


def test_dataclass_is_frozen_decimal_only_and_hard_flagged() -> None:
    report = build_report()

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False  # type: ignore[misc]

    decimal_fields = {
        "memory_sample_count",
        "settled_sample_count",
        "calibration_error_rate",
        "source_family_coverage_ratio",
        "last_memory_update_age_seconds",
        "ready_ratio",
    }
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name in decimal_fields:
            assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "memory_sample_count",
            _DecimalSubclass("24"),
            "memory_sample_count must be exactly Decimal",
        ),
        (
            "settled_sample_count",
            d("1.5"),
            "settled_sample_count must be an integral Decimal",
        ),
        (
            "calibration_error_rate",
            d("1.000001"),
            "calibration_error_rate must be <= 1.000000",
        ),
        (
            "source_family_coverage_ratio",
            d("0.8500001"),
            "source_family_coverage_ratio must use six decimal places or fewer",
        ),
        (
            "last_memory_update_age_seconds",
            d("-1"),
            "last_memory_update_age_seconds must be >= 0.000000",
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


def test_rejects_unsafe_labels_disabled_flags_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="team must not be empty"):
        build_report(team="")
    with pytest.raises(ValueError, match="unsafe public payload"):
        build_report(team="live_team")
    with pytest.raises(ValueError, match="paper_only must be True"):
        build_report(paper_only=False)
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
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
