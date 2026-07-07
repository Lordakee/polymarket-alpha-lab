from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_evidence_collection_gap_plan",
    )


def subject(
    case_ref: str,
    domain_ref: str,
    *,
    coverage_ratio: str = "1.000000",
    freshest_evidence_age_hours: str = "1.000000",
    conflict_score: str = "0.000000",
    traceability_ratio: str = "1.000000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    plan = module()
    return plan.ResearchEvidenceCollectionGapSubject(
        case_ref=case_ref,
        domain_ref=domain_ref,
        coverage_ratio=d(coverage_ratio),
        freshest_evidence_age_hours=d(freshest_evidence_age_hours),
        conflict_score=d(conflict_score),
        traceability_ratio=d(traceability_ratio),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_plan(*subjects: object, **overrides: object):
    plan = module()
    config = plan.ResearchEvidenceCollectionGapPlanConfig(**overrides)
    return plan.build_research_evidence_collection_gap_plan(
        subjects,
        config=config,
    )


def test_scores_pass_watch_and_block_collection_gaps() -> None:
    clear = subject("case-clear", "macro")
    watch = subject(
        "case-watch",
        "sports",
        coverage_ratio="0.800000",
        freshest_evidence_age_hours="30.000000",
    )
    block = subject(
        "case-block",
        "crypto",
        coverage_ratio="0.000000",
        freshest_evidence_age_hours="96.000000",
        conflict_score="0.800000",
        traceability_ratio="0.000000",
    )

    result = build_plan(watch, clear, block)

    assert is_dataclass(result)
    assert result.status == "block"
    assert result.input_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.highest_priority_score == d("0.940000")
    assert result.reason_codes == (
        "collection_gap_status_block",
        "coverage_below_floor",
        "evidence_age_above_floor",
        "conflict_pressure_present",
        "traceability_below_floor",
    )

    assert tuple(row.case_ref for row in result.rows) == (
        "case-block",
        "case-watch",
        "case-clear",
    )
    assert tuple(row.priority_rank for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    block_row, watch_row, pass_row = result.rows
    assert block_row.priority_score == d("0.940000")
    assert block_row.coverage_gap_score == d("1.000000")
    assert block_row.freshness_gap_score == d("1.000000")
    assert block_row.conflict_gap_score == d("0.800000")
    assert block_row.traceability_gap_score == d("1.000000")
    assert block_row.gap_codes == (
        "collection_gap_status_block",
        "coverage_below_floor",
        "evidence_age_above_floor",
        "conflict_pressure_present",
        "traceability_below_floor",
    )

    assert watch_row.priority_score == d("0.110000")
    assert watch_row.status == "watch"
    assert watch_row.gap_codes == (
        "collection_gap_status_watch",
        "coverage_below_floor",
        "evidence_age_above_floor",
    )

    assert pass_row.priority_score == d("0.000000")
    assert pass_row.status == "pass"
    assert pass_row.gap_codes == ("collection_gap_status_pass",)


def test_public_payload_is_redacted_json_ready_and_tamper_evident() -> None:
    plan = module()
    result = build_plan(
        subject(
            "case-block",
            "macro",
            coverage_ratio="0.000000",
            freshest_evidence_age_hours="96.000000",
            conflict_score="0.800000",
            traceability_ratio="0.000000",
        ),
    )

    payload = plan.research_evidence_collection_gap_plan_payload(result)

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["highest_priority_score"] == "0.940000"
    assert payload["rows"][0]["priority_score"] == "0.940000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert _float_paths(payload) == ()

    joined_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate",
        "market",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
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
        assert forbidden not in joined_payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_rejects_non_exact_decimal_inputs() -> None:
    plan = module()

    with pytest.raises(ValueError, match="coverage_ratio"):
        plan.ResearchEvidenceCollectionGapSubject(
            case_ref="case-alpha",
            domain_ref="macro",
            coverage_ratio=1,  # type: ignore[arg-type]
            freshest_evidence_age_hours=d("1.000000"),
            conflict_score=d("0.000000"),
            traceability_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="conflict_score"):
        plan.ResearchEvidenceCollectionGapSubject(
            case_ref="case-alpha",
            domain_ref="macro",
            coverage_ratio=d("1.000000"),
            freshest_evidence_age_hours=d("1.000000"),
            conflict_score=DecimalSubclass("0.000000"),
            traceability_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="min_coverage_ratio"):
        plan.ResearchEvidenceCollectionGapPlanConfig(
            min_coverage_ratio=1,  # type: ignore[arg-type]
        )


def test_rejects_leaky_public_identifiers_and_payload_terms() -> None:
    plan = module()

    with pytest.raises(ValueError, match="unsafe|canonical"):
        subject("candidate-123", "macro")
    with pytest.raises(ValueError, match="unsafe|canonical"):
        subject("case-alpha", "market-slug")
    with pytest.raises(ValueError, match="unsafe|canonical"):
        subject("case-alpha", "orders")
    with pytest.raises(ValueError, match="unsafe|canonical"):
        subject("case-alpha", "https://example.test/evidence")

    result = build_plan(subject("case-clear", "macro"))
    payload = plan.research_evidence_collection_gap_plan_payload(result)
    unsafe_payload = dict(payload)
    unsafe_payload["token"] = "redacted"

    with pytest.raises(ValueError, match="unsafe|unexpected"):
        plan.research_evidence_collection_gap_plan_payload(unsafe_payload)


def test_frozen_hard_flags_and_public_status_contract() -> None:
    result = build_plan(subject("case-clear", "macro"))

    for value in (result, result.rows[0]):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    assert {result.status, *(row.status for row in result.rows)} <= {
        "pass",
        "watch",
        "block",
    }

    with pytest.raises(ValueError, match="paper_only"):
        subject("case-bad", "macro", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_output_is_deterministic_across_input_order() -> None:
    clear = subject("case-clear", "macro")
    watch = subject(
        "case-watch",
        "sports",
        coverage_ratio="0.800000",
        freshest_evidence_age_hours="30.000000",
    )
    block = subject(
        "case-block",
        "crypto",
        coverage_ratio="0.000000",
        freshest_evidence_age_hours="96.000000",
        conflict_score="0.800000",
        traceability_ratio="0.000000",
    )

    first = build_plan(clear, watch, block)
    second = build_plan(block, clear, watch)

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module().research_evidence_collection_gap_plan_payload(
        first,
    ) == module().research_evidence_collection_gap_plan_payload(second)


def test_module_scope_is_local_readonly_report_only_and_non_execution() -> None:
    plan = module()
    source = inspect.getsource(plan)
    lowered = source.lower()
    tree = ast.parse(source)

    assert plan.__all__ == (
        "DEFAULT_RESEARCH_EVIDENCE_COLLECTION_GAP_PLAN_CONFIG_VERSION",
        "ResearchEvidenceCollectionGapPlanConfig",
        "ResearchEvidenceCollectionGapReport",
        "ResearchEvidenceCollectionGapRow",
        "ResearchEvidenceCollectionGapSubject",
        "build_research_evidence_collection_gap_plan",
        "research_evidence_collection_gap_plan_payload",
    )
    assert "paper_only: bool = true" in lowered
    assert "report_only: bool = true" in lowered
    assert "readonly: bool = true" in lowered
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    for forbidden in (
        "candidate",
        "market",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "requests.",
        "httpx.",
        "socket.",
        "insert(",
        "update(",
        "delete(",
    ):
        assert forbidden not in lowered


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    if type(value) is float:
        return (path,)
    return ()
