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
    / "team_research_memory_compaction_policy.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_research_memory_compaction_policy",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-research-memory-compaction-policy-v1-test",
        "min_domain_summary_count": d("1"),
        "min_pass_evidence_quality": d("0.750000"),
        "min_watch_evidence_quality": d("0.500000"),
        "max_pass_prediction_bias_bps": d("300.000000"),
        "max_watch_prediction_bias_bps": d("600.000000"),
        "min_pass_postmortem_completeness": d("0.800000"),
        "min_watch_postmortem_completeness": d("0.500000"),
    }
    values.update(overrides)
    return module.TeamResearchMemoryCompactionPolicyConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "summary_digest": digest("a"),
        "domain_label": "macro-calendar",
        "evidence_quality": d("0.900000"),
        "prediction_bias_bps": d("100.000000"),
        "postmortem_completeness": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamResearchMemoryCompactionCandidate(**values)


def build_report(*rows: object, cfg=None):
    module = api()
    return module.build_team_research_memory_compaction_policy(
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


def test_compaction_pass_prepares_report_only_digest_plan() -> None:
    module = api()
    report = build_report(
        candidate(summary_digest=digest("a"), domain_label="macro-calendar"),
        candidate(
            summary_digest=digest("b"),
            domain_label="macro-calendar",
            evidence_quality=d("0.800000"),
            prediction_bias_bps=d("200.000000"),
            postmortem_completeness=d("0.850000"),
        ),
    )
    row = report.rows[0]
    payload = module.team_research_memory_compaction_policy_payload(report)
    rendered = json.dumps(payload, sort_keys=True)

    assert report.report_status == "pass"
    assert report.input_summary_count == d("2")
    assert report.domain_count == d("1")
    assert report.row_count == d("1")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.upstream_prepare_count == d("1")
    assert report.review_count == d("0")
    assert report.suppress_count == d("0")
    assert report.average_compaction_score == d("0.833750")
    assert report.reason_codes == ("upstream_compaction_plans_prepared",)
    assert row.public_status == "pass"
    assert row.plan_action == "prepare_upstream_compaction_digest"
    assert row.upstream_prepare is True
    assert row.summary_count == d("2")
    assert row.average_evidence_quality == d("0.850000")
    assert row.average_prediction_bias_bps == d("150.000000")
    assert row.max_prediction_bias_bps == d("200.000000")
    assert row.average_postmortem_completeness == d("0.875000")
    assert row.reason_codes == (
        "domain_summary_count_pass",
        "evidence_quality_pass",
        "prediction_bias_low",
        "postmortem_complete",
        "memory_compaction_prepared",
    )
    assert payload["rows"][0]["compaction_score"] == "0.833750"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "macro-calendar" not in rendered
    assert digest("a") not in rendered
    assert digest("b") not in rendered
    assert_no_float_values(payload)


def test_manual_review_watch_holds_compaction_plan() -> None:
    report = build_report(
        candidate(
            summary_digest=digest("c"),
            evidence_quality=d("0.650000"),
            prediction_bias_bps=d("420.000000"),
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
    assert report.average_compaction_score == d("0.580000")
    assert report.reason_codes == ("manual_compaction_reviews_required",)
    assert row.public_status == "watch"
    assert row.plan_action == "hold_for_manual_review"
    assert row.upstream_prepare is False
    assert row.reason_codes == (
        "domain_summary_count_pass",
        "evidence_quality_watch",
        "prediction_bias_watch",
        "postmortem_review_needed",
        "memory_compaction_review_required",
    )


def test_quality_insufficient_block_suppresses_compaction_plan() -> None:
    report = build_report(
        candidate(
            summary_digest=digest("d"),
            evidence_quality=d("0.400000"),
            prediction_bias_bps=d("800.000000"),
            postmortem_completeness=d("0.300000"),
        ),
    )
    row = report.rows[0]

    assert report.report_status == "block"
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("1")
    assert report.suppress_count == d("1")
    assert report.reason_codes == ("compaction_plans_suppressed",)
    assert row.public_status == "block"
    assert row.plan_action == "suppress_compaction_digest"
    assert row.upstream_prepare is False
    assert row.reason_codes == (
        "domain_summary_count_pass",
        "evidence_quality_block",
        "prediction_bias_block",
        "postmortem_incomplete",
        "memory_compaction_blocked",
    )


def test_type_rejection_decimal_only_frozen_and_strict_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="summary_digest must be a string"):
        candidate(summary_digest=_StringSubclass(digest("a")))

    with pytest.raises(ValueError, match="domain_label must be a string"):
        candidate(domain_label=_StringSubclass("macro-calendar"))

    with pytest.raises(ValueError, match="evidence_quality must be a Decimal"):
        candidate(evidence_quality=1)

    with pytest.raises(ValueError, match="prediction_bias_bps must be a Decimal"):
        candidate(prediction_bias_bps=_DecimalSubclass("100.000000"))

    with pytest.raises(ValueError, match="evidence_quality must be at most 1"):
        candidate(evidence_quality=d("1.000001"))

    with pytest.raises(ValueError, match="postmortem_completeness must be nonnegative"):
        candidate(postmortem_completeness=d("-0.000001"))

    with pytest.raises(ValueError, match="prediction_bias_bps must be finite"):
        candidate(prediction_bias_bps=Decimal("NaN"))

    report = build_report(
        candidate(summary_digest=digest("a"), domain_label="domain-a"),
        candidate(
            summary_digest=digest("b"),
            domain_label="domain-b",
            evidence_quality=d("0.300000"),
        ),
    )
    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        replace(report, rows=tuple(reversed(report.rows)))

    with pytest.raises(ValueError, match="public_status must be one of"):
        replace(report.rows[0], public_status="ready")

    with pytest.raises(FrozenInstanceError):
        item = candidate()
        item.domain_label = "other-domain"  # type: ignore[misc]

    with pytest.raises(ValueError, match="report must be a TeamResearchMemoryCompaction"):
        module.team_research_memory_compaction_policy_payload(candidate())


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "min_domain_summary_count",
        "min_pass_evidence_quality",
        "min_watch_evidence_quality",
        "max_pass_prediction_bias_bps",
        "max_watch_prediction_bias_bps",
        "min_pass_postmortem_completeness",
        "min_watch_postmortem_completeness",
        "evidence_quality",
        "prediction_bias_bps",
        "postmortem_completeness",
        "summary_count",
        "average_evidence_quality",
        "average_prediction_bias_bps",
        "max_prediction_bias_bps",
        "average_postmortem_completeness",
        "minimum_evidence_quality",
        "minimum_postmortem_completeness",
        "compaction_score",
        "input_summary_count",
        "domain_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "upstream_prepare_count",
        "review_count",
        "suppress_count",
        "average_compaction_score",
    }

    for cls in (
        module.TeamResearchMemoryCompactionPolicyConfig,
        module.TeamResearchMemoryCompactionCandidate,
        module.TeamResearchMemoryCompactionPlanRow,
        module.TeamResearchMemoryCompactionPolicyReport,
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
        {"domain_label": "raw_candidate_id abc should not appear"},
        {"domain_label": "market_id 123 should not appear"},
        {"domain_label": "market_slug example should not appear"},
        {"domain_label": "market question should not appear"},
        {"domain_label": "source_ref hidden"},
        {"domain_label": "source_url https://example.invalid"},
        {"domain_label": "source_text hidden"},
        {"domain_label": "dsn postgres://hidden"},
        {"domain_label": "private token leaked"},
        {"domain_label": "wallet auth surface"},
        {"domain_label": "open order trade position"},
        {"domain_label": "buy sell recommendation language"},
        {"domain_label": "真实表名 table"},
    ),
)
def test_leak_rejection_blocks_unsafe_public_strings(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        candidate(**overrides)


def test_payload_leak_rejection_blocks_unsafe_keys_values_and_digest_tampering() -> None:
    module = api()
    report = build_report(candidate())
    payload = module.team_research_memory_compaction_policy_payload(report)

    bad_key_payload = dict(payload)
    bad_key_payload["source_url"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_research_memory_compaction_policy_payload(bad_key_payload)

    bad_value_payload = dict(payload)
    bad_value_payload["reason_codes"] = ["buy sell recommendation"]
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_research_memory_compaction_policy_payload(bad_value_payload)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_research_memory_compaction_policy_payload(tampered)


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
        candidate(readonly=False)

    payload = module.team_research_memory_compaction_policy_payload(build_report(candidate()))
    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.team_research_memory_compaction_policy_payload(payload)


def test_output_is_deterministic_for_row_order_payload_and_digest() -> None:
    module = api()
    first = build_report(
        candidate(summary_digest=digest("c"), domain_label="domain-c"),
        candidate(summary_digest=digest("a"), domain_label="domain-a"),
        candidate(
            summary_digest=digest("b"),
            domain_label="domain-b",
            evidence_quality=d("0.300000"),
        ),
    )
    second = build_report(
        candidate(
            summary_digest=digest("b"),
            domain_label="domain-b",
            evidence_quality=d("0.300000"),
        ),
        candidate(summary_digest=digest("c"), domain_label="domain-c"),
        candidate(summary_digest=digest("a"), domain_label="domain-a"),
    )

    first_payload = module.team_research_memory_compaction_policy_payload(first)
    second_payload = module.team_research_memory_compaction_policy_payload(second)

    assert tuple(row.public_status for row in first.rows) == ("block", "pass", "pass")
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
    assert report.domain_count == d("0")
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
