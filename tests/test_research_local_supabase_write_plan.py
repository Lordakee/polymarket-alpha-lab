from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_local_supabase_write_plan import (
    RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION,
    ResearchLocalSupabaseWritePlanConfig,
    ResearchLocalSupabaseWritePlanItem,
    ResearchLocalSupabaseWritePlanReport,
    ResearchLocalSupabaseWritePlanRow,
    build_research_local_supabase_write_plan,
    research_local_supabase_write_plan_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_local_supabase_write_plan.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**overrides: object) -> ResearchLocalSupabaseWritePlanConfig:
    values = {
        "config_version": RESEARCH_LOCAL_SUPABASE_WRITE_PLAN_CONFIG_VERSION,
        "min_pass_evidence_quality": d("0.750000"),
        "min_watch_evidence_quality": d("0.500000"),
        "min_pass_redaction_quality": d("0.900000"),
        "min_watch_redaction_quality": d("0.700000"),
        "min_pass_review_completeness": d("0.800000"),
        "min_watch_review_completeness": d("0.500000"),
    }
    values.update(overrides)
    return ResearchLocalSupabaseWritePlanConfig(**values)


def item(**overrides: object) -> ResearchLocalSupabaseWritePlanItem:
    values = {
        "item_digest": digest("a"),
        "plan_scope": "long_term_memory",
        "evidence_quality": d("0.900000"),
        "redaction_quality": d("0.950000"),
        "review_completeness": d("0.850000"),
        "sanitized_summary": "Outcome evidence retained as a redacted research note.",
    }
    values.update(overrides)
    return ResearchLocalSupabaseWritePlanItem(**values)


def report(
    items: tuple[ResearchLocalSupabaseWritePlanItem, ...],
    *,
    cfg: ResearchLocalSupabaseWritePlanConfig | None = None,
) -> ResearchLocalSupabaseWritePlanReport:
    return build_research_local_supabase_write_plan(items, config=cfg or config())


def test_pass_watch_and_block_rows_generate_redacted_write_plan() -> None:
    summary = report(
        (
            item(
                item_digest=digest("c"),
                plan_scope="postmortem_summary",
                redaction_quality=d("0.600000"),
                sanitized_summary="Needs stronger redaction before local retention.",
            ),
            item(
                item_digest=digest("b"),
                plan_scope="source_registry",
                sanitized_summary="Registered public source family quality only.",
            ),
            item(
                item_digest=digest("a"),
                evidence_quality=d("0.620000"),
                redaction_quality=d("0.820000"),
                review_completeness=d("0.700000"),
                sanitized_summary="Memory candidate needs reviewer confirmation.",
            ),
        ),
    )

    assert type(summary) is ResearchLocalSupabaseWritePlanReport
    assert summary.report_status == "block"
    assert summary.item_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.prepare_write_count == d("1")
    assert summary.review_count == d("1")
    assert summary.suppress_count == d("1")
    assert summary.average_readiness_score == d("0.799167")
    assert summary.reason_codes == (
        "local_write_plans_prepared",
        "local_write_plans_review_required",
        "local_write_plans_blocked",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.plan_key for row in summary.rows) == (
        "redacted-local-write-plan-001",
        "redacted-local-write-plan-002",
        "redacted-local-write-plan-003",
    )
    assert tuple(row.plan_scope for row in summary.rows) == (
        "long_term_memory",
        "source_registry",
        "postmortem_summary",
    )
    assert tuple(row.public_status for row in summary.rows) == (
        "watch",
        "pass",
        "block",
    )
    assert set(row.public_status for row in summary.rows) <= {"pass", "watch", "block"}

    watch, passed, blocked = summary.rows
    assert watch.write_plan_action == "hold_redacted_local_record_for_review"
    assert watch.prepare_write is False
    assert watch.readiness_score == d("0.710000")
    assert watch.reason_codes == (
        "long_term_memory_scope",
        "evidence_quality_watch",
        "redaction_quality_watch",
        "review_completeness_watch",
        "local_write_plan_review_required",
    )
    assert passed.write_plan_action == "prepare_redacted_local_record"
    assert passed.prepare_write is True
    assert passed.readiness_score == d("0.905000")
    assert passed.reason_codes == (
        "source_registry_scope",
        "evidence_quality_pass",
        "redaction_quality_pass",
        "review_completeness_pass",
        "local_write_plan_prepared",
    )
    assert blocked.write_plan_action == "suppress_redacted_local_record"
    assert blocked.prepare_write is False
    assert blocked.reason_codes == (
        "postmortem_summary_scope",
        "evidence_quality_pass",
        "redaction_quality_block",
        "review_completeness_pass",
        "local_write_plan_block",
    )


def test_payload_is_redacted_decimal_only_and_contains_hard_flags() -> None:
    payload = research_local_supabase_write_plan_payload(report((item(),)))
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["write_plan_mode"] == "report_only_redacted_local_research_write_plan"
    assert payload["report_status"] == "pass"
    assert payload["rows"][0]["plan_key"] == "redacted-local-write-plan-001"
    assert "item_digest" not in payload["rows"][0]
    assert payload["rows"][0]["readiness_score"] == "0.905000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))
    for forbidden in (
        digest("a"),
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "postgres://",
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
        assert forbidden not in encoded.lower()


def test_type_rejection_decimal_only_frozen_and_strict_members() -> None:
    with pytest.raises(ValueError, match="min_pass_evidence_quality"):
        config(min_pass_evidence_quality=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_redaction_quality"):
        config(min_watch_redaction_quality=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="item_digest"):
        item(item_digest=_StringSubclass(digest("a")))
    with pytest.raises(ValueError, match="evidence_quality"):
        item(evidence_quality=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="redaction_quality"):
        item(redaction_quality=_DecimalSubclass("0.950000"))
    with pytest.raises(ValueError, match="plan_scope"):
        item(plan_scope="real_table")
    with pytest.raises(ValueError, match="between 0 and 1"):
        item(review_completeness=d("1.000001"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        item(evidence_quality=d("-0.000001"))
    with pytest.raises(ValueError, match="items"):
        build_research_local_supabase_write_plan([item()], config=config())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="items"):
        build_research_local_supabase_write_plan((object(),), config=config())  # type: ignore[arg-type]

    frozen = item()
    with pytest.raises(FrozenInstanceError):
        frozen.evidence_quality = d("0.100000")  # type: ignore[misc]

    summary = report((item(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="public_status"):
        replace(summary.rows[0], public_status="ready")
    two_row_summary = report((item(), item(item_digest=digest("b"))))
    with pytest.raises(ValueError, match="rows"):
        replace(two_row_summary, rows=tuple(reversed(two_row_summary.rows)))


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    numeric_fields = {
        "min_pass_evidence_quality",
        "min_watch_evidence_quality",
        "min_pass_redaction_quality",
        "min_watch_redaction_quality",
        "min_pass_review_completeness",
        "min_watch_review_completeness",
        "evidence_quality",
        "redaction_quality",
        "review_completeness",
        "plan_rank",
        "readiness_score",
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "prepare_write_count",
        "review_count",
        "suppress_count",
        "average_readiness_score",
    }
    for cls in (
        ResearchLocalSupabaseWritePlanConfig,
        ResearchLocalSupabaseWritePlanItem,
        ResearchLocalSupabaseWritePlanRow,
        ResearchLocalSupabaseWritePlanReport,
    ):
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in numeric_fields:
                assert hints[field.name] is Decimal

    assert_public_numeric_values_are_decimal(config())
    assert_public_numeric_values_are_decimal(item())
    assert_public_numeric_values_are_decimal(report((item(),)))


@pytest.mark.parametrize(
    "summary_text",
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
    ),
)
def test_leak_rejection_blocks_unsafe_public_strings(summary_text: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        item(sanitized_summary=summary_text)


def test_payload_leak_rejection_blocks_unsafe_keys_values_and_bad_flags() -> None:
    payload = research_local_supabase_write_plan_payload(report((item(),)))

    with pytest.raises(ValueError, match="unsafe public"):
        research_local_supabase_write_plan_payload({**payload, "market_id": "hidden"})
    with pytest.raises(ValueError, match="unsafe public"):
        research_local_supabase_write_plan_payload(
            {**payload, "reason_codes": ["source_text hidden"]},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        research_local_supabase_write_plan_payload(
            {**payload, "real_table_name": "hidden"},
        )
    with pytest.raises(ValueError, match="readonly"):
        research_local_supabase_write_plan_payload({**payload, "readonly": False})


def test_hard_flags_are_required_on_inputs_rows_reports_and_payloads() -> None:
    for value in (config(), item(), report((item(),)).rows[0], report((item(),))):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report((item(readonly=False),))


def test_output_is_deterministic_for_equivalent_inputs() -> None:
    first = report(
        (
            item(item_digest=digest("c"), plan_scope="source_registry"),
            item(item_digest=digest("b"), plan_scope="postmortem_summary"),
            item(item_digest=digest("a"), plan_scope="long_term_memory"),
        ),
    )
    second = report(
        (
            item(item_digest=digest("a"), plan_scope="long_term_memory"),
            item(item_digest=digest("b"), plan_scope="postmortem_summary"),
            item(item_digest=digest("c"), plan_scope="source_registry"),
        ),
    )

    first_payload = research_local_supabase_write_plan_payload(first)
    second_payload = research_local_supabase_write_plan_payload(second)

    assert tuple(row.plan_scope for row in first.rows) == (
        "long_term_memory",
        "source_registry",
        "postmortem_summary",
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
    assert summary.item_count == d("0")
    assert summary.rows == ()
    assert summary.reason_codes == ("no_write_plan_items_supplied",)
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
