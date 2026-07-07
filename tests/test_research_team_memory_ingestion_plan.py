from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_team_memory_ingestion_plan import (
    RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION,
    ResearchTeamMemoryIngestionPlanConfig,
    ResearchTeamMemoryIngestionPlanInput,
    ResearchTeamMemoryIngestionPlanReport,
    ResearchTeamMemoryIngestionPlanRow,
    build_research_team_memory_ingestion_plan,
    research_team_memory_ingestion_plan_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_memory_ingestion_plan.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**overrides: object) -> ResearchTeamMemoryIngestionPlanConfig:
    values = {
        "config_version": RESEARCH_TEAM_MEMORY_INGESTION_PLAN_CONFIG_VERSION,
        "min_pass_field_family_coverage": d("0.900000"),
        "min_watch_field_family_coverage": d("0.700000"),
        "min_pass_dedupe_key_coverage": d("0.850000"),
        "min_watch_dedupe_key_coverage": d("0.650000"),
        "min_pass_postmortem_record_coverage": d("0.800000"),
        "min_watch_postmortem_record_coverage": d("0.600000"),
        "min_pass_source_summary_coverage": d("0.850000"),
        "min_watch_source_summary_coverage": d("0.650000"),
        "min_pass_safety_boundary_coverage": d("0.950000"),
        "min_watch_safety_boundary_coverage": d("0.750000"),
    }
    values.update(overrides)
    return ResearchTeamMemoryIngestionPlanConfig(**values)


def plan_input(**overrides: object) -> ResearchTeamMemoryIngestionPlanInput:
    values = {
        "plan_digest": digest("a"),
        "memory_scope": "long_term_research_memory",
        "field_family_coverage": d("0.950000"),
        "dedupe_key_coverage": d("0.900000"),
        "postmortem_record_coverage": d("0.850000"),
        "source_summary_coverage": d("0.920000"),
        "safety_boundary_coverage": d("0.970000"),
        "sanitized_plan_summary": (
            "Redacted team memory plan keeps digest keys and summary buckets."
        ),
    }
    values.update(overrides)
    return ResearchTeamMemoryIngestionPlanInput(**values)


def report(
    rows: tuple[ResearchTeamMemoryIngestionPlanInput, ...],
    *,
    cfg: ResearchTeamMemoryIngestionPlanConfig | None = None,
) -> ResearchTeamMemoryIngestionPlanReport:
    return build_research_team_memory_ingestion_plan(rows, config=cfg or config())


def test_pass_watch_and_block_rows_generate_public_ingestion_plan() -> None:
    summary = report(
        (
            plan_input(
                plan_digest=digest("c"),
                memory_scope="postmortem_learning_memory",
                dedupe_key_coverage=d("0.600000"),
                sanitized_plan_summary=(
                    "Postmortem memory plan waits for duplicate protection."
                ),
            ),
            plan_input(
                plan_digest=digest("b"),
                memory_scope="source_summary_memory",
                sanitized_plan_summary=(
                    "Source summary memory plan keeps family digests and buckets."
                ),
            ),
            plan_input(
                plan_digest=digest("a"),
                field_family_coverage=d("0.800000"),
                dedupe_key_coverage=d("0.780000"),
                postmortem_record_coverage=d("0.700000"),
                source_summary_coverage=d("0.760000"),
                safety_boundary_coverage=d("0.900000"),
                sanitized_plan_summary=(
                    "Long horizon memory plan needs one more review pass."
                ),
            ),
        ),
    )

    assert type(summary) is ResearchTeamMemoryIngestionPlanReport
    assert summary.report_status == "block"
    assert summary.next_step == "block_memory_ingestion_until_plan_is_safe"
    assert summary.plan_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.prepare_count == d("1")
    assert summary.review_count == d("1")
    assert summary.blocked_count == d("1")
    assert summary.average_readiness_score == d("0.852333")
    assert summary.reason_codes == (
        "research_team_memory_ingestion_plans_pass",
        "research_team_memory_ingestion_plans_watch",
        "research_team_memory_ingestion_plans_block",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.plan_key for row in summary.rows) == (
        "redacted-research-team-memory-ingestion-plan-001",
        "redacted-research-team-memory-ingestion-plan-002",
        "redacted-research-team-memory-ingestion-plan-003",
    )
    assert tuple(row.memory_scope for row in summary.rows) == (
        "long_term_research_memory",
        "source_summary_memory",
        "postmortem_learning_memory",
    )
    assert tuple(row.public_status for row in summary.rows) == (
        "watch",
        "pass",
        "block",
    )
    assert set(row.public_status for row in summary.rows) <= {"pass", "watch", "block"}

    watched, passed, blocked = summary.rows
    assert watched.ingestion_plan_action == (
        "hold_report_only_memory_ingestion_plan_for_review"
    )
    assert watched.ingestion_allowed is False
    assert watched.readiness_score == d("0.783000")
    assert watched.field_families == (
        "memory_identity",
        "claim_summary",
        "probability_context",
        "review_cadence",
        "outcome_feedback",
    )
    assert watched.dedupe_keys == (
        "memory_key_digest",
        "event_family_digest",
        "claim_digest",
        "time_bucket",
    )
    assert watched.postmortem_records == (
        "resolved_probability_bucket",
        "forecast_error_bucket",
        "lesson_digest",
        "review_state",
    )
    assert watched.source_summaries == (
        "source_family_digest",
        "evidence_window_bucket",
        "summary_digest",
        "agreement_bucket",
    )
    assert watched.safety_boundaries == (
        "credential_redaction",
        "storage_target_redaction",
        "raw_evidence_redaction",
        "report_only_no_write",
    )
    assert watched.reason_codes == (
        "long_term_research_memory_scope",
        "field_family_coverage_watch",
        "dedupe_key_coverage_watch",
        "postmortem_record_coverage_watch",
        "source_summary_coverage_watch",
        "safety_boundary_coverage_watch",
        "memory_ingestion_plan_review_required",
    )
    assert passed.ingestion_plan_action == "prepare_report_only_memory_ingestion_plan"
    assert passed.ingestion_allowed is True
    assert passed.readiness_score == d("0.917000")
    assert blocked.ingestion_plan_action == "block_report_only_memory_ingestion_plan"
    assert blocked.ingestion_allowed is False
    assert blocked.reason_codes == (
        "postmortem_learning_memory_scope",
        "field_family_coverage_pass",
        "dedupe_key_coverage_block",
        "postmortem_record_coverage_pass",
        "source_summary_coverage_pass",
        "safety_boundary_coverage_pass",
        "memory_ingestion_plan_blocked",
    )


def test_payload_is_redacted_decimal_only_and_contains_required_families() -> None:
    payload = research_team_memory_ingestion_plan_payload(report((plan_input(),)))
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert payload["ingestion_plan_mode"] == (
        "local_supabase_postgres_report_only_memory_ingestion_plan"
    )
    assert payload["report_status"] == "pass"
    assert payload["rows"][0]["plan_key"] == (
        "redacted-research-team-memory-ingestion-plan-001"
    )
    assert "plan_digest" not in payload["rows"][0]
    assert payload["rows"][0]["readiness_score"] == "0.917000"
    assert payload["rows"][0]["field_families"] == [
        "memory_identity",
        "claim_summary",
        "probability_context",
        "review_cadence",
        "outcome_feedback",
    ]
    assert payload["rows"][0]["dedupe_keys"] == [
        "memory_key_digest",
        "event_family_digest",
        "claim_digest",
        "time_bucket",
    ]
    assert payload["rows"][0]["postmortem_records"] == [
        "resolved_probability_bucket",
        "forecast_error_bucket",
        "lesson_digest",
        "review_state",
    ]
    assert payload["rows"][0]["source_summaries"] == [
        "source_family_digest",
        "evidence_window_bucket",
        "summary_digest",
        "agreement_bucket",
    ]
    assert payload["rows"][0]["safety_boundaries"] == [
        "credential_redaction",
        "storage_target_redaction",
        "raw_evidence_redaction",
        "report_only_no_write",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))
    for forbidden in (
        digest("a"),
        "dsn",
        "table",
        "private",
        "token",
        "raw source url",
        "raw source text",
        "raw_source_url",
        "raw_source_text",
        "source_url",
        "source_text",
        "service_role",
        "connection_string",
    ):
        assert forbidden not in encoded


def test_type_rejection_decimal_only_frozen_and_strict_members() -> None:
    with pytest.raises(ValueError, match="min_pass_field_family_coverage"):
        config(min_pass_field_family_coverage=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_dedupe_key_coverage"):
        config(min_watch_dedupe_key_coverage=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="plan_digest"):
        plan_input(plan_digest=_StringSubclass(digest("a")))
    with pytest.raises(ValueError, match="field_family_coverage"):
        plan_input(field_family_coverage=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dedupe_key_coverage"):
        plan_input(dedupe_key_coverage=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="memory_scope"):
        plan_input(memory_scope="storage_target")
    with pytest.raises(ValueError, match="between 0 and 1"):
        plan_input(source_summary_coverage=d("1.000001"))
    with pytest.raises(ValueError, match="required decimal precision"):
        plan_input(safety_boundary_coverage=d("0.9000001"))
    with pytest.raises(ValueError, match="inputs"):
        build_research_team_memory_ingestion_plan([plan_input()], config=config())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="inputs"):
        build_research_team_memory_ingestion_plan((object(),), config=config())  # type: ignore[arg-type]

    frozen = plan_input()
    with pytest.raises(FrozenInstanceError):
        frozen.field_family_coverage = d("0.100000")  # type: ignore[misc]

    summary = report((plan_input(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="public_status"):
        replace(summary.rows[0], public_status="watch")
    with pytest.raises(ValueError, match="readiness_score"):
        replace(summary.rows[0], readiness_score=d("0.100000"))
    two_row_summary = report((plan_input(), plan_input(plan_digest=digest("b"))))
    with pytest.raises(ValueError, match="rows"):
        replace(two_row_summary, rows=tuple(reversed(two_row_summary.rows)))


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    numeric_fields = {
        "min_pass_field_family_coverage",
        "min_watch_field_family_coverage",
        "min_pass_dedupe_key_coverage",
        "min_watch_dedupe_key_coverage",
        "min_pass_postmortem_record_coverage",
        "min_watch_postmortem_record_coverage",
        "min_pass_source_summary_coverage",
        "min_watch_source_summary_coverage",
        "min_pass_safety_boundary_coverage",
        "min_watch_safety_boundary_coverage",
        "field_family_coverage",
        "dedupe_key_coverage",
        "postmortem_record_coverage",
        "source_summary_coverage",
        "safety_boundary_coverage",
        "plan_rank",
        "readiness_score",
        "plan_count",
        "pass_count",
        "watch_count",
        "block_count",
        "prepare_count",
        "review_count",
        "blocked_count",
        "average_readiness_score",
    }
    for cls in (
        ResearchTeamMemoryIngestionPlanConfig,
        ResearchTeamMemoryIngestionPlanInput,
        ResearchTeamMemoryIngestionPlanRow,
        ResearchTeamMemoryIngestionPlanReport,
    ):
        assert is_dataclass(cls)
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in numeric_fields:
                assert hints[field.name] is Decimal

    assert_public_numeric_values_are_decimal(config())
    assert_public_numeric_values_are_decimal(plan_input())
    assert_public_numeric_values_are_decimal(report((plan_input(),)))


@pytest.mark.parametrize(
    "summary_text",
    (
        "dsn hidden",
        "storage table hidden",
        "private credential leaked",
        "bearer token leaked",
        "raw source url should not appear",
        "raw source text should not appear",
        "source_url hidden",
        "source_text hidden",
        "service_role hidden",
        "connection_string hidden",
        "https://example.invalid/reference",
    ),
)
def test_leak_rejection_blocks_unsafe_public_strings(summary_text: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        plan_input(sanitized_plan_summary=summary_text)


def test_payload_leak_rejection_blocks_unsafe_keys_values_and_bad_flags() -> None:
    payload = research_team_memory_ingestion_plan_payload(report((plan_input(),)))

    with pytest.raises(ValueError, match="unsafe public"):
        research_team_memory_ingestion_plan_payload({**payload, "dsn": "hidden"})
    with pytest.raises(ValueError, match="unsafe public"):
        research_team_memory_ingestion_plan_payload(
            {**payload, "reason_codes": ["raw source text hidden"]},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        research_team_memory_ingestion_plan_payload(
            {**payload, "storage_table": "hidden"},
        )
    with pytest.raises(ValueError, match="readonly"):
        research_team_memory_ingestion_plan_payload({**payload, "readonly": False})


def test_hard_flags_are_required_on_inputs_rows_reports_and_payloads() -> None:
    for value in (
        config(),
        plan_input(),
        report((plan_input(),)).rows[0],
        report((plan_input(),)),
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        plan_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report((plan_input(readonly=False),))


def test_output_is_deterministic_for_equivalent_inputs() -> None:
    first = report(
        (
            plan_input(plan_digest=digest("c"), memory_scope="source_summary_memory"),
            plan_input(
                plan_digest=digest("b"),
                memory_scope="postmortem_learning_memory",
            ),
            plan_input(plan_digest=digest("a"), memory_scope="long_term_research_memory"),
        ),
    )
    second = report(
        (
            plan_input(plan_digest=digest("a"), memory_scope="long_term_research_memory"),
            plan_input(
                plan_digest=digest("b"),
                memory_scope="postmortem_learning_memory",
            ),
            plan_input(plan_digest=digest("c"), memory_scope="source_summary_memory"),
        ),
    )

    first_payload = research_team_memory_ingestion_plan_payload(first)
    second_payload = research_team_memory_ingestion_plan_payload(second)

    assert tuple(row.memory_scope for row in first.rows) == (
        "long_term_research_memory",
        "source_summary_memory",
        "postmortem_learning_memory",
    )
    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_empty_input_is_blocked_report_only_plan() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.next_step == "block_memory_ingestion_until_plan_is_safe"
    assert summary.plan_count == d("0")
    assert summary.rows == ()
    assert summary.reason_codes == ("no_research_team_memory_ingestion_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_module_has_no_external_persistence_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    call_names: list[str] = []
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
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
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
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "upsert",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_names for name in call_names)


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
        for child in value.values():
            assert_public_numeric_values_are_decimal(child)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            assert_public_numeric_values_are_decimal(child)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item_value in value.values():
            values.extend(_walk_payload_values(item_value))
    elif isinstance(value, list):
        for item_value in value:
            values.extend(_walk_payload_values(item_value))
    else:
        values.append(value)
    return tuple(values)


def _is_forbidden_number(value: object) -> bool:
    return type(value) is int or type(value) is float
