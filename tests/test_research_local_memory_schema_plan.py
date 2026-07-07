from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_local_memory_schema_plan import (
    RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION,
    ResearchLocalMemorySchemaPlanConfig,
    ResearchLocalMemorySchemaPlanInput,
    ResearchLocalMemorySchemaPlanReport,
    ResearchLocalMemorySchemaPlanRow,
    build_research_local_memory_schema_plan,
    research_local_memory_schema_plan_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_local_memory_schema_plan.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**overrides: object) -> ResearchLocalMemorySchemaPlanConfig:
    values = {
        "config_version": RESEARCH_LOCAL_MEMORY_SCHEMA_PLAN_CONFIG_VERSION,
        "min_pass_redaction_coverage": d("0.900000"),
        "min_watch_redaction_coverage": d("0.700000"),
        "min_pass_lineage_coverage": d("0.850000"),
        "min_watch_lineage_coverage": d("0.650000"),
        "min_pass_review_coverage": d("0.800000"),
        "min_watch_review_coverage": d("0.500000"),
    }
    values.update(overrides)
    return ResearchLocalMemorySchemaPlanConfig(**values)


def schema_input(**overrides: object) -> ResearchLocalMemorySchemaPlanInput:
    values = {
        "schema_digest": digest("a"),
        "memory_scope": "long_term_memory",
        "redaction_coverage": d("0.950000"),
        "lineage_coverage": d("0.900000"),
        "review_coverage": d("0.850000"),
        "sanitized_schema_notes": "Redacted memory shape keeps digest keys and review buckets.",
    }
    values.update(overrides)
    return ResearchLocalMemorySchemaPlanInput(**values)


def report(
    rows: tuple[ResearchLocalMemorySchemaPlanInput, ...],
    *,
    cfg: ResearchLocalMemorySchemaPlanConfig | None = None,
) -> ResearchLocalMemorySchemaPlanReport:
    return build_research_local_memory_schema_plan(rows, config=cfg or config())


def test_pass_watch_and_block_rows_generate_redacted_schema_plan() -> None:
    summary = report(
        (
            schema_input(
                schema_digest=digest("c"),
                memory_scope="postmortem_result",
                lineage_coverage=d("0.600000"),
                sanitized_schema_notes="Hold replay lesson shape until lineage coverage improves.",
            ),
            schema_input(
                schema_digest=digest("b"),
                memory_scope="source_registry",
                sanitized_schema_notes="Registry shape keeps source family digests only.",
            ),
            schema_input(
                schema_digest=digest("a"),
                redaction_coverage=d("0.820000"),
                lineage_coverage=d("0.700000"),
                review_coverage=d("0.700000"),
                sanitized_schema_notes="Long horizon memory shape needs reviewer confirmation.",
            ),
        ),
    )

    assert type(summary) is ResearchLocalMemorySchemaPlanReport
    assert summary.report_status == "block"
    assert summary.schema_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.prepare_schema_count == d("1")
    assert summary.review_count == d("1")
    assert summary.suppress_count == d("1")
    assert summary.average_readiness_score == d("0.819333")
    assert summary.reason_codes == (
        "local_memory_schema_plans_prepared",
        "local_memory_schema_plans_review_required",
        "local_memory_schema_plans_blocked",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.schema_key for row in summary.rows) == (
        "redacted-local-memory-schema-001",
        "redacted-local-memory-schema-002",
        "redacted-local-memory-schema-003",
    )
    assert tuple(row.memory_scope for row in summary.rows) == (
        "long_term_memory",
        "source_registry",
        "postmortem_result",
    )
    assert tuple(row.public_status for row in summary.rows) == (
        "watch",
        "pass",
        "block",
    )
    assert set(row.public_status for row in summary.rows) <= {"pass", "watch", "block"}

    watched, passed, blocked = summary.rows
    assert watched.schema_plan_action == "hold_redacted_schema_plan_for_review"
    assert watched.prepare_schema is False
    assert watched.readiness_score == d("0.748000")
    assert watched.field_groups == (
        "memory_key_digest",
        "topic_family_code",
        "sanitized_claim_digest",
        "confidence_bucket",
        "last_review_bucket",
    )
    assert watched.reason_codes == (
        "long_term_memory_scope",
        "redaction_coverage_watch",
        "lineage_coverage_watch",
        "review_coverage_watch",
        "local_memory_schema_plan_review_required",
    )
    assert passed.schema_plan_action == "prepare_redacted_schema_plan"
    assert passed.prepare_schema is True
    assert passed.readiness_score == d("0.907500")
    assert passed.field_groups == (
        "source_family_digest",
        "publication_window_bucket",
        "evidence_method_code",
        "recency_bucket",
        "redaction_state",
    )
    assert passed.reason_codes == (
        "source_registry_scope",
        "redaction_coverage_pass",
        "lineage_coverage_pass",
        "review_coverage_pass",
        "local_memory_schema_plan_prepared",
    )
    assert blocked.schema_plan_action == "suppress_redacted_schema_plan"
    assert blocked.prepare_schema is False
    assert blocked.field_groups == (
        "review_digest",
        "settlement_bucket",
        "calibration_bucket",
        "lesson_digest",
        "review_state",
    )
    assert blocked.reason_codes == (
        "postmortem_result_scope",
        "redaction_coverage_pass",
        "lineage_coverage_block",
        "review_coverage_pass",
        "local_memory_schema_plan_blocked",
    )


def test_payload_is_redacted_decimal_only_and_contains_hard_flags() -> None:
    payload = research_local_memory_schema_plan_payload(report((schema_input(),)))
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert payload["schema_plan_mode"] == (
        "report_only_redacted_local_supabase_memory_schema_plan"
    )
    assert payload["report_status"] == "pass"
    assert payload["rows"][0]["schema_key"] == "redacted-local-memory-schema-001"
    assert "schema_digest" not in payload["rows"][0]
    assert payload["rows"][0]["readiness_score"] == "0.907500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))
    for forbidden in (
        digest("a"),
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "postgres://",
        "postgresql://",
        "database_url",
        "connection_string",
        "real_table",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in encoded


def test_type_rejection_decimal_only_frozen_and_strict_members() -> None:
    with pytest.raises(ValueError, match="min_pass_redaction_coverage"):
        config(min_pass_redaction_coverage=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_lineage_coverage"):
        config(min_watch_lineage_coverage=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="schema_digest"):
        schema_input(schema_digest=_StringSubclass(digest("a")))
    with pytest.raises(ValueError, match="redaction_coverage"):
        schema_input(redaction_coverage=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lineage_coverage"):
        schema_input(lineage_coverage=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="memory_scope"):
        schema_input(memory_scope="real_table")
    with pytest.raises(ValueError, match="between 0 and 1"):
        schema_input(review_coverage=d("1.000001"))
    with pytest.raises(ValueError, match="required decimal precision"):
        schema_input(redaction_coverage=d("0.9000001"))
    with pytest.raises(ValueError, match="inputs"):
        build_research_local_memory_schema_plan([schema_input()], config=config())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="inputs"):
        build_research_local_memory_schema_plan((object(),), config=config())  # type: ignore[arg-type]

    frozen = schema_input()
    with pytest.raises(FrozenInstanceError):
        frozen.redaction_coverage = d("0.100000")  # type: ignore[misc]

    summary = report((schema_input(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="public_status"):
        replace(summary.rows[0], public_status="ready")
    two_row_summary = report((schema_input(), schema_input(schema_digest=digest("b"))))
    with pytest.raises(ValueError, match="rows"):
        replace(two_row_summary, rows=tuple(reversed(two_row_summary.rows)))


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    numeric_fields = {
        "min_pass_redaction_coverage",
        "min_watch_redaction_coverage",
        "min_pass_lineage_coverage",
        "min_watch_lineage_coverage",
        "min_pass_review_coverage",
        "min_watch_review_coverage",
        "redaction_coverage",
        "lineage_coverage",
        "review_coverage",
        "schema_rank",
        "readiness_score",
        "schema_count",
        "pass_count",
        "watch_count",
        "block_count",
        "prepare_schema_count",
        "review_count",
        "suppress_count",
        "average_readiness_score",
    }
    for cls in (
        ResearchLocalMemorySchemaPlanConfig,
        ResearchLocalMemorySchemaPlanInput,
        ResearchLocalMemorySchemaPlanRow,
        ResearchLocalMemorySchemaPlanReport,
    ):
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in numeric_fields:
                assert hints[field.name] is Decimal

    assert_public_numeric_values_are_decimal(config())
    assert_public_numeric_values_are_decimal(schema_input())
    assert_public_numeric_values_are_decimal(report((schema_input(),)))


@pytest.mark.parametrize(
    "notes",
    (
        "raw candidate id should not appear",
        "candidate_id should not appear",
        "market_id hidden",
        "market_slug hidden",
        "market question hidden",
        "source_ref hidden",
        "source_url https://example.invalid",
        "source_text hidden",
        "dsn postgres://hidden",
        "real table: hidden",
        "private token leaked",
        "wallet auth surface",
        "open order trade position",
        "buy sell recommendation language",
        "URL should be blocked",
    ),
)
def test_leak_rejection_blocks_unsafe_public_strings(notes: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        schema_input(sanitized_schema_notes=notes)


def test_payload_leak_rejection_blocks_unsafe_keys_values_and_bad_flags() -> None:
    payload = research_local_memory_schema_plan_payload(report((schema_input(),)))

    with pytest.raises(ValueError, match="unsafe public"):
        research_local_memory_schema_plan_payload({**payload, "market_id": "hidden"})
    with pytest.raises(ValueError, match="unsafe public"):
        research_local_memory_schema_plan_payload(
            {**payload, "reason_codes": ["source_text hidden"]},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        research_local_memory_schema_plan_payload(
            {**payload, "real_table_name": "hidden"},
        )
    with pytest.raises(ValueError, match="readonly"):
        research_local_memory_schema_plan_payload({**payload, "readonly": False})


def test_hard_flags_are_required_on_inputs_rows_reports_and_payloads() -> None:
    for value in (
        config(),
        schema_input(),
        report((schema_input(),)).rows[0],
        report((schema_input(),)),
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
        schema_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report((schema_input(readonly=False),))


def test_output_is_deterministic_for_equivalent_inputs() -> None:
    first = report(
        (
            schema_input(schema_digest=digest("c"), memory_scope="source_registry"),
            schema_input(schema_digest=digest("b"), memory_scope="postmortem_result"),
            schema_input(schema_digest=digest("a"), memory_scope="long_term_memory"),
        ),
    )
    second = report(
        (
            schema_input(schema_digest=digest("a"), memory_scope="long_term_memory"),
            schema_input(schema_digest=digest("b"), memory_scope="postmortem_result"),
            schema_input(schema_digest=digest("c"), memory_scope="source_registry"),
        ),
    )

    first_payload = research_local_memory_schema_plan_payload(first)
    second_payload = research_local_memory_schema_plan_payload(second)

    assert tuple(row.memory_scope for row in first.rows) == (
        "long_term_memory",
        "source_registry",
        "postmortem_result",
    )
    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_empty_input_is_watch_report_only_plan() -> None:
    summary = report(())

    assert summary.report_status == "watch"
    assert summary.schema_count == d("0")
    assert summary.rows == ()
    assert summary.reason_codes == ("no_local_memory_schema_inputs_supplied",)
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
