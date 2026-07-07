from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_memory_update_policy.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.research_memory_update_policy")


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-memory-update-policy-v1-test",
        "min_pass_evidence_quality": d("0.750000"),
        "min_watch_evidence_quality": d("0.500000"),
        "min_update_prediction_bias_bps": d("100.000000"),
        "high_prediction_bias_bps": d("600.000000"),
        "min_pass_postmortem_completeness": d("0.800000"),
        "min_watch_postmortem_completeness": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchMemoryUpdatePolicyConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "summary_digest": digest("a"),
        "event_settlement_status": "settled",
        "evidence_quality": d("0.900000"),
        "prediction_bias_bps": d("820.000000"),
        "postmortem_completeness": d("0.850000"),
        "sanitized_summary": "Resolution evidence was strong after final outcome.",
        "sanitized_lesson": "Increase calibration caution when late evidence clusters.",
    }
    values.update(overrides)
    return module.ResearchMemoryUpdateCandidate(**values)


def build_report(*rows: object, cfg=None):
    module = api()
    return module.build_research_memory_update_policy_report(
        rows,
        config=cfg if cfg is not None else config(),
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


def test_should_update_prepares_sanitized_upstream_plan() -> None:
    module = api()
    report = build_report(candidate())
    row = report.rows[0]
    payload = module.research_memory_update_policy_payload(report)

    assert report.report_status == "pass"
    assert report.input_summary_count == d("1")
    assert report.row_count == d("1")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.upstream_prepare_count == d("1")
    assert report.review_count == d("0")
    assert report.suppress_count == d("0")
    assert report.average_readiness_score == d("0.932500")
    assert report.reason_codes == ("upstream_updates_prepared",)
    assert row.public_status == "pass"
    assert row.write_plan_action == "prepare_upstream_summary"
    assert row.upstream_prepare is True
    assert row.reason_codes == (
        "event_settled",
        "evidence_quality_pass",
        "prediction_bias_high",
        "postmortem_complete",
        "memory_update_prepared",
    )
    assert payload["rows"][0]["summary_digest"] == digest("a")
    assert payload["rows"][0]["readiness_score"] == "0.932500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_review_needed_holds_plan_without_prepare_flag() -> None:
    report = build_report(
        candidate(
            summary_digest=digest("b"),
            evidence_quality=d("0.620000"),
            prediction_bias_bps=d("250.000000"),
            postmortem_completeness=d("0.700000"),
        ),
    )
    row = report.rows[0]

    assert report.report_status == "watch"
    assert report.pass_count == d("0")
    assert report.watch_count == d("1")
    assert report.block_count == d("0")
    assert report.upstream_prepare_count == d("0")
    assert report.review_count == d("1")
    assert report.suppress_count == d("0")
    assert row.public_status == "watch"
    assert row.write_plan_action == "hold_for_review"
    assert row.upstream_prepare is False
    assert row.reason_codes == (
        "event_settled",
        "evidence_quality_watch",
        "prediction_bias_meaningful",
        "postmortem_review_needed",
        "memory_update_review_required",
    )


def test_reject_update_suppresses_bad_or_unresolved_memory() -> None:
    report = build_report(
        candidate(
            summary_digest=digest("c"),
            event_settlement_status="void",
            evidence_quality=d("0.920000"),
            prediction_bias_bps=d("900.000000"),
            postmortem_completeness=d("0.900000"),
        ),
        candidate(
            summary_digest=digest("d"),
            evidence_quality=d("0.400000"),
            prediction_bias_bps=d("50.000000"),
            postmortem_completeness=d("0.300000"),
        ),
    )

    assert report.report_status == "block"
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("2")
    assert report.suppress_count == d("2")
    assert tuple(row.public_status for row in report.rows) == ("block", "block")
    assert tuple(row.write_plan_action for row in report.rows) == (
        "suppress_upstream_summary",
        "suppress_upstream_summary",
    )
    assert "event_void" in report.rows[0].reason_codes
    assert report.rows[1].reason_codes == (
        "event_settled",
        "evidence_quality_block",
        "prediction_bias_low",
        "postmortem_incomplete",
        "memory_update_blocked",
    )
    assert report.reason_codes == ("upstream_updates_suppressed",)


def test_type_rejection_decimal_only_frozen_and_strict_public_members() -> None:
    module = api()

    with pytest.raises(ValueError, match="summary_digest must be a string"):
        candidate(summary_digest=_StringSubclass(digest("a")))

    with pytest.raises(ValueError, match="evidence_quality must be a Decimal"):
        candidate(evidence_quality=1)

    with pytest.raises(ValueError, match="prediction_bias_bps must be a Decimal"):
        candidate(prediction_bias_bps=_DecimalSubclass("100.000000"))

    with pytest.raises(ValueError, match="event_settlement_status must be one of"):
        candidate(event_settlement_status="resolved")

    with pytest.raises(ValueError, match="evidence_quality must be at most 1"):
        candidate(evidence_quality=d("1.000001"))

    with pytest.raises(ValueError, match="postmortem_completeness must be nonnegative"):
        candidate(postmortem_completeness=d("-0.000001"))

    with pytest.raises(ValueError, match="prediction_bias_bps must be finite"):
        candidate(prediction_bias_bps=Decimal("NaN"))

    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        replace(
            build_report(candidate(summary_digest=digest("b")), candidate()),
            rows=tuple(reversed(build_report(candidate(summary_digest=digest("b")), candidate()).rows)),
        )

    with pytest.raises(FrozenInstanceError):
        item = candidate()
        item.event_settlement_status = "pending"  # type: ignore[misc]

    with pytest.raises(ValueError, match="report must be a ResearchMemoryUpdatePolicyReport"):
        module.research_memory_update_policy_payload(candidate())


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "min_pass_evidence_quality",
        "min_watch_evidence_quality",
        "min_update_prediction_bias_bps",
        "high_prediction_bias_bps",
        "min_pass_postmortem_completeness",
        "min_watch_postmortem_completeness",
        "evidence_quality",
        "prediction_bias_bps",
        "postmortem_completeness",
        "readiness_score",
        "input_summary_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "upstream_prepare_count",
        "review_count",
        "suppress_count",
        "average_readiness_score",
    }

    for cls in (
        module.ResearchMemoryUpdatePolicyConfig,
        module.ResearchMemoryUpdateCandidate,
        module.ResearchMemoryUpdatePlanRow,
        module.ResearchMemoryUpdatePolicyReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal

    sample_report = build_report(candidate())
    assert_public_numeric_values_are_decimal(config())
    assert_public_numeric_values_are_decimal(candidate())
    assert_public_numeric_values_are_decimal(sample_report)


@pytest.mark.parametrize(
    "overrides",
    (
        {"sanitized_summary": "raw_candidate_id abc should not appear"},
        {"sanitized_summary": "market_id 123 should not appear"},
        {"sanitized_summary": "market_slug example should not appear"},
        {"sanitized_summary": "source_url https://example.invalid"},
        {"sanitized_lesson": "dsn postgres://hidden"},
        {"sanitized_lesson": "private token leaked"},
        {"sanitized_lesson": "wallet auth surface"},
        {"sanitized_lesson": "open order trade position"},
        {"sanitized_lesson": "buy sell recommendation language"},
    ),
)
def test_leak_rejection_blocks_unsafe_public_strings(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        candidate(**overrides)


def test_payload_leak_rejection_blocks_unsafe_keys_values_and_digest_tampering() -> None:
    module = api()
    report = build_report(candidate())
    payload = module.research_memory_update_policy_payload(report)

    bad_key_payload = dict(payload)
    bad_key_payload["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_memory_update_policy_payload(bad_key_payload)

    bad_value_payload = dict(payload)
    bad_value_payload["reason_codes"] = ["source_text hidden"]
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_memory_update_policy_payload(bad_value_payload)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_memory_update_policy_payload(tampered)


def test_hard_flags_are_required_on_inputs_rows_reports_and_payloads() -> None:
    module = api()

    for item in (config(), candidate(), build_report(candidate()).rows[0], build_report(candidate())):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(candidate(readonly=False))

    payload = module.research_memory_update_policy_payload(build_report(candidate()))
    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_memory_update_policy_payload(payload)


def test_output_is_deterministic_for_row_order_payload_and_digest() -> None:
    module = api()
    first = build_report(
        candidate(summary_digest=digest("c"), event_settlement_status="pending"),
        candidate(summary_digest=digest("a")),
        candidate(summary_digest=digest("b"), evidence_quality=d("0.300000")),
    )
    second = build_report(
        candidate(summary_digest=digest("b"), evidence_quality=d("0.300000")),
        candidate(summary_digest=digest("c"), event_settlement_status="pending"),
        candidate(summary_digest=digest("a")),
    )

    first_payload = module.research_memory_update_policy_payload(first)
    second_payload = module.research_memory_update_policy_payload(second)

    assert tuple(row.summary_digest for row in first.rows) == (
        digest("b"),
        digest("c"),
        digest("a"),
    )
    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_empty_input_is_watch_report_only_plan() -> None:
    report = build_report()

    assert report.report_status == "watch"
    assert report.input_summary_count == d("0")
    assert report.row_count == d("0")
    assert report.reason_codes == ("no_summaries_supplied",)


def test_module_scope_has_no_external_persistence_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
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
