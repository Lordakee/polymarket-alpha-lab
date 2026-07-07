from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
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
    / "team_specialist_research_memory_decay_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_research_memory_decay_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-research-memory-decay-gate-v2-test",
        "stale_research_after_seconds": d("2592000.000000"),
        "outdated_playbook_after_seconds": d("1209600.000000"),
        "recent_feedback_window_seconds": d("604800.000000"),
        "stale_research_penalty": d("0.300000"),
        "outdated_playbook_penalty": d("0.250000"),
        "recent_feedback_boost": d("0.100000"),
        "min_pass_score": d("0.700000"),
        "min_watch_score": d("0.450000"),
    }
    values.update(overrides)
    return module.TeamSpecialistResearchMemoryDecayGateV2Config(**values)


def memory(**overrides: object):
    module = api()
    values = {
        "memory_id": "research-memory-current",
        "team_id": "macro_rates",
        "category_id": "finance.macro.rates",
        "specialist_id": "rates-research-specialist",
        "playbook_id": "rates-playbook-v2",
        "baseline_memory_score": d("0.760000"),
        "latest_research_at": GENERATED_AT - timedelta(days=1),
        "playbook_updated_at": GENERATED_AT - timedelta(days=1),
        "latest_feedback_at": GENERATED_AT - timedelta(days=1),
        "recent_feedback_count": d("3"),
    }
    values.update(overrides)
    return module.TeamSpecialistResearchMemoryDecayGateV2Memory(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_research_memory_decay_gate_v2(
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


def test_memory_decay_scoring_sorts_and_summarizes_rows() -> None:
    report = build_report(
        memory(memory_id="research-memory-current"),
        memory(
            memory_id="research-memory-outdated",
            latest_feedback_at=None,
            recent_feedback_count=d("0"),
            playbook_updated_at=GENERATED_AT - timedelta(days=30),
        ),
        memory(
            memory_id="research-memory-stale",
            latest_research_at=GENERATED_AT - timedelta(days=45),
            playbook_updated_at=GENERATED_AT - timedelta(days=30),
            latest_feedback_at=None,
            recent_feedback_count=d("0"),
        ),
    )

    assert report.report_status == "blocked"
    assert report.source_memory_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.outdated_playbook_count == d("2")
    assert report.recent_feedback_boost_count == d("1")
    assert report.average_adjusted_memory_score == d("0.526667")
    assert tuple(row.memory_id for row in report.rows) == (
        "research-memory-stale",
        "research-memory-outdated",
        "research-memory-current",
    )
    assert tuple(row.adjusted_memory_score for row in report.rows) == (
        d("0.210000"),
        d("0.510000"),
        d("0.860000"),
    )
    assert tuple(row.row_status for row in report.rows) == ("blocked", "watch", "pass")
    assert report.reason_codes == (
        "stale_research_memory_present",
        "outdated_playbook_present",
        "recent_feedback_boost_present",
    )


def test_outdated_playbook_penalty_applies_without_research_staleness() -> None:
    report = build_report(
        memory(
            latest_feedback_at=None,
            recent_feedback_count=d("0"),
            playbook_updated_at=GENERATED_AT - timedelta(days=15),
        ),
    )

    row = report.rows[0]
    assert row.research_age_seconds == d("86400.000000")
    assert row.playbook_age_seconds == d("1296000.000000")
    assert row.outdated_playbook_penalty == d("0.250000")
    assert row.stale_research_penalty == d("0.000000")
    assert row.recent_feedback_boost_applied == d("0.000000")
    assert row.adjusted_memory_score == d("0.510000")
    assert row.row_status == "watch"
    assert row.reason_codes == ("outdated_playbook",)


def test_recent_feedback_boost_requires_recent_feedback_inside_window() -> None:
    boosted = build_report(memory()).rows[0]
    old_feedback = build_report(
        memory(
            latest_feedback_at=GENERATED_AT - timedelta(days=10),
            recent_feedback_count=d("3"),
        ),
    ).rows[0]

    assert boosted.recent_feedback_boost_applied == d("0.100000")
    assert boosted.adjusted_memory_score == d("0.860000")
    assert boosted.reason_codes == ("recent_feedback_boost", "research_memory_current")
    assert old_feedback.recent_feedback_boost_applied == d("0.000000")
    assert old_feedback.adjusted_memory_score == d("0.760000")
    assert old_feedback.reason_codes == ("research_memory_current",)


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(memory())

    payload = module.team_specialist_research_memory_decay_gate_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_memory_count"] == "1"
    assert payload["average_adjusted_memory_score"] == "0.860000"
    assert payload["rows"][0]["adjusted_memory_score"] == "0.860000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_research_memory_decay_gate_v2_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_memory = memory()
    sample_report = build_report(sample_memory)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_memory, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(memory(readonly=False))


def test_report_rejects_derived_validation_digest_tampering() -> None:
    module = api()
    report = build_report(memory())
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["derived_validation_digest"] = "f" * 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistResearchMemoryDecayGateV2Report(**values)


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
        module.team_specialist_research_memory_decay_gate_v2_payload(payload)


def test_public_string_values_reject_unsafe_live_surface_terms() -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        memory(memory_id="live-research-memory")
    with pytest.raises(ValueError, match="unsafe public value"):
        memory(playbook_id="sell-side-playbook")


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
