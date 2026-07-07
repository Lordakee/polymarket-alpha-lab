from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_resolution_rule_memory_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_resolution_rule_memory_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "resolution-rule-memory-gate-v2-test",
        "target_team_id": "macro_rates",
        "target_category_id": "finance.macro.rates",
        "target_rule_template_id": "fed-rate-decision-final-source",
        "min_outcome_sample_size": d("12"),
        "watch_min_outcome_sample_size": d("6"),
        "max_recent_error_rate": d("0.150000"),
        "watch_max_recent_error_rate": d("0.250000"),
        "min_source_hierarchy_familiarity_score": d("0.750000"),
        "watch_min_source_hierarchy_familiarity_score": d("0.550000"),
        "max_resolution_rule_age_seconds": d("15552000.000000"),
        "watch_max_resolution_rule_age_seconds": d("31536000.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistResolutionRuleMemoryGateV2Config(**values)


def memory(**overrides: object):
    module = api()
    values = {
        "memory_id": "macro-resolution-current",
        "team_id": "macro_rates",
        "category_id": "finance.macro.rates",
        "specialist_id": "macro-resolution-specialist",
        "rule_template_id": "fed-rate-decision-final-source",
        "outcome_sample_size": d("18"),
        "recent_error_rate": d("0.050000"),
        "source_hierarchy_familiarity_score": d("0.900000"),
        "latest_resolution_rule_at": GENERATED_AT - timedelta(days=1),
    }
    values.update(overrides)
    return module.TeamSpecialistResolutionRuleMemoryGateV2Memory(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_resolution_rule_memory_gate_v2(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_resolution_rule_memory_gate_sorts_and_summarizes_rows() -> None:
    report = build_report(
        memory(memory_id="macro-resolution-current"),
        memory(
            memory_id="macro-resolution-watch",
            outcome_sample_size=d("8"),
            recent_error_rate=d("0.200000"),
            source_hierarchy_familiarity_score=d("0.650000"),
            latest_resolution_rule_at=GENERATED_AT - timedelta(days=240),
        ),
        memory(
            memory_id="politics-resolution-blocked",
            team_id="politics",
            category_id="politics",
            specialist_id="politics-resolution-specialist",
            rule_template_id="election-certification-final-source",
            outcome_sample_size=d("3"),
            recent_error_rate=d("0.400000"),
            source_hierarchy_familiarity_score=d("0.300000"),
            latest_resolution_rule_at=GENERATED_AT - timedelta(days=500),
        ),
    )

    assert report.report_status == "blocked"
    assert report.source_memory_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.category_mismatch_count == d("1")
    assert report.rule_template_mismatch_count == d("1")
    assert report.outcome_sample_size_below_minimum_count == d("2")
    assert report.recent_error_rate_above_limit_count == d("2")
    assert report.source_hierarchy_familiarity_below_minimum_count == d("2")
    assert report.stale_resolution_rule_memory_count == d("2")
    assert tuple(row.memory_id for row in report.rows) == (
        "politics-resolution-blocked",
        "macro-resolution-watch",
        "macro-resolution-current",
    )
    assert tuple(row.row_status for row in report.rows) == ("blocked", "watch", "pass")
    assert tuple(row.category_match for row in report.rows) == (d("0"), d("1"), d("1"))
    assert tuple(row.rule_template_match for row in report.rows) == (
        d("0"),
        d("1"),
        d("1"),
    )
    assert report.rows[1].resolution_rule_age_seconds == d("20736000.000000")
    assert report.rows[1].reason_codes == (
        "category_match",
        "rule_template_match",
        "outcome_sample_size_watch",
        "recent_error_rate_watch",
        "source_hierarchy_familiarity_watch",
        "resolution_rule_memory_watch",
    )
    assert report.rows[2].reason_codes == (
        "category_match",
        "rule_template_match",
        "outcome_sample_size_sufficient",
        "recent_error_rate_low",
        "source_hierarchy_familiarity_strong",
        "resolution_rule_memory_recent",
    )
    assert report.reason_codes == (
        "category_mismatch_present",
        "rule_template_mismatch_present",
        "outcome_sample_size_below_minimum_present",
        "recent_error_rate_above_limit_present",
        "source_hierarchy_familiarity_below_minimum_present",
        "stale_resolution_rule_memory_present",
    )


def test_all_experience_present_passes_and_payload_digest_is_stable() -> None:
    module = api()
    report = build_report(memory())

    assert report.report_status == "pass"
    assert report.reason_codes == ("resolution_rule_memory_experience_ready",)
    assert report.average_recent_error_rate == d("0.050000")
    assert report.average_source_hierarchy_familiarity_score == d("0.900000")
    assert isinstance(report.derived_validation_digest, str)
    assert len(report.derived_validation_digest) == 64

    payload = module.team_specialist_resolution_rule_memory_gate_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_memory_count"] == "1"
    assert payload["average_recent_error_rate"] == "0.050000"
    assert payload["rows"][0]["outcome_sample_size"] == "18"
    assert payload["rows"][0]["resolution_rule_age_seconds"] == "86400.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_float_values(payload)

    tampered = dict(payload)
    tampered["average_recent_error_rate"] = "0.060000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_resolution_rule_memory_gate_v2_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_memory = memory()
    sample_report = build_report(sample_memory)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_memory, sample_row, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        memory(readonly=False)


def test_validation_rejects_non_decimal_ranges_and_threshold_inversions() -> None:
    module = api()

    with pytest.raises(ValueError, match="outcome_sample_size must be a Decimal"):
        memory(outcome_sample_size=18)
    with pytest.raises(ValueError, match="outcome_sample_size must be a whole number"):
        memory(outcome_sample_size=d("18.5"))
    with pytest.raises(ValueError, match="recent_error_rate must be a Decimal"):
        memory(recent_error_rate=_DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="recent_error_rate must be at most 1"):
        memory(recent_error_rate=d("1.000001"))
    with pytest.raises(ValueError, match="source_hierarchy_familiarity_score must be finite"):
        memory(source_hierarchy_familiarity_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="watch_min_outcome_sample_size must not exceed"):
        module.TeamSpecialistResolutionRuleMemoryGateV2Config(
            watch_min_outcome_sample_size=d("13"),
        )
    with pytest.raises(ValueError, match="max_recent_error_rate must not exceed"):
        module.TeamSpecialistResolutionRuleMemoryGateV2Config(
            max_recent_error_rate=d("0.300000"),
        )
    with pytest.raises(ValueError, match="target_category_id must match target_team_id"):
        module.TeamSpecialistResolutionRuleMemoryGateV2Config(
            target_team_id="politics",
            target_category_id="finance.macro.rates",
        )


def test_report_rejects_derived_validation_digest_tampering_and_unsorted_rows() -> None:
    report = build_report(
        memory(memory_id="macro-resolution-current"),
        memory(
            memory_id="macro-resolution-watch",
            outcome_sample_size=d("8"),
            recent_error_rate=d("0.200000"),
            source_hierarchy_familiarity_score=d("0.650000"),
            latest_resolution_rule_at=GENERATED_AT - timedelta(days=240),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        replace(report, rows=(report.rows[1], report.rows[0]))
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(report, reason_codes=("resolution_rule_memory_experience_ready",))


@pytest.mark.parametrize(
    "payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "wallet_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy signal"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "live trade"},
        {"paper_only": True, "report_only": True, "readonly": True, "network": "mainnet"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ),
)
def test_unsafe_public_payload_keys_values_and_flag_downgrades_rejected(
    payload: dict[str, object],
) -> None:
    module = api()

    with pytest.raises(ValueError):
        module.team_specialist_resolution_rule_memory_gate_v2_payload(payload)


def test_public_string_values_reject_unsafe_live_surface_terms() -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        memory(memory_id="live-resolution-memory")
    with pytest.raises(ValueError, match="unsafe public value"):
        memory(rule_template_id="buy-side-resolution-template")


def test_module_scope_has_no_network_auth_wallet_order_db_or_trading_surface() -> None:
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
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
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
