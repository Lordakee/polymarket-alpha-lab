from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_resolution_clause_ambiguity_matrix_report as api
from polymarket_alpha_lab.research_event_resolution_clause_ambiguity_matrix_report import (
    ResearchEventResolutionClauseAmbiguityMatrixConfig,
    ResearchEventResolutionClauseAmbiguityMatrixReport,
    ResearchEventResolutionClauseAmbiguityMatrixSubject,
    build_research_event_resolution_clause_ambiguity_matrix_report,
    research_event_resolution_clause_ambiguity_matrix_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_clause_ambiguity_matrix_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def subject(
    **overrides: object,
) -> ResearchEventResolutionClauseAmbiguityMatrixSubject:
    values = {
        "public_event_bucket": "policy_resolution",
        "authority_clarity": d("0.950000"),
        "boundary_condition_count": d("0.000000"),
        "conflicting_interpretation_pressure": d("0.050000"),
        "deadline_proximity": d("0.050000"),
    }
    values.update(overrides)
    return ResearchEventResolutionClauseAmbiguityMatrixSubject(**values)


def report(
    *subjects: ResearchEventResolutionClauseAmbiguityMatrixSubject,
    config: ResearchEventResolutionClauseAmbiguityMatrixConfig | None = None,
) -> ResearchEventResolutionClauseAmbiguityMatrixReport:
    return build_research_event_resolution_clause_ambiguity_matrix_report(
        subjects,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_public_api_declares_report_only_clause_ambiguity_matrix_surface() -> None:
    assert api.DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION == (
        "research-event-resolution-clause-ambiguity-matrix-report-v0"
    )
    assert api.RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_DIMENSIONS == (
        "authority_clarity",
        "boundary_condition_count",
        "conflicting_interpretation_pressure",
        "deadline_proximity",
    )
    assert api.RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_CONFIG_VERSION",
        "RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_DIMENSIONS",
        "RESOLUTION_CLAUSE_AMBIGUITY_MATRIX_STATUSES",
        "ResearchEventResolutionClauseAmbiguityMatrixConfig",
        "ResearchEventResolutionClauseAmbiguityMatrixReport",
        "ResearchEventResolutionClauseAmbiguityMatrixRow",
        "ResearchEventResolutionClauseAmbiguityMatrixSubject",
        "build_research_event_resolution_clause_ambiguity_matrix_report",
        "research_event_resolution_clause_ambiguity_matrix_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(ResearchEventResolutionClauseAmbiguityMatrixConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True
    assert field_defaults["authority_clarity_watch_floor"] == d("0.800000")
    assert field_defaults["authority_clarity_block_floor"] == d("0.550000")
    assert field_defaults["boundary_condition_watch_count"] == d("2.000000")
    assert field_defaults["boundary_condition_block_count"] == d("5.000000")
    assert field_defaults["conflicting_interpretation_watch_ceiling"] == d("0.300000")
    assert field_defaults["conflicting_interpretation_block_ceiling"] == d("0.700000")
    assert field_defaults["deadline_proximity_watch_ceiling"] == d("0.500000")
    assert field_defaults["deadline_proximity_block_ceiling"] == d("0.850000")
    assert field_defaults["watch_ambiguity_score_threshold"] == d("0.250000")
    assert field_defaults["block_ambiguity_score_threshold"] == d("0.600000")


def test_clause_ambiguity_matrix_scores_pass_watch_and_block_rows() -> None:
    result = report(
        subject(public_event_bucket="pass_bucket"),
        subject(
            public_event_bucket="watch_bucket",
            authority_clarity=d("0.720000"),
            boundary_condition_count=d("3.000000"),
            conflicting_interpretation_pressure=d("0.400000"),
            deadline_proximity=d("0.550000"),
        ),
        subject(
            public_event_bucket="block_bucket",
            authority_clarity=d("0.400000"),
            boundary_condition_count=d("6.000000"),
            conflicting_interpretation_pressure=d("0.850000"),
            deadline_proximity=d("0.900000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.event_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.lowest_authority_clarity == d("0.400000")
    assert result.highest_boundary_condition_count == d("6.000000")
    assert result.highest_conflicting_interpretation_pressure == d("0.850000")
    assert result.highest_deadline_proximity == d("0.900000")
    assert result.highest_clause_ambiguity_score == d("0.745000")
    assert result.status == "block"
    assert result.reason_codes == (
        "clause_ambiguity_matrix_report_block_rows",
        "clause_ambiguity_matrix_report_watch_rows",
        "authority_clarity_block",
        "boundary_condition_count_block",
        "conflicting_interpretation_pressure_block",
        "deadline_proximity_block",
        "clause_ambiguity_score_block",
        "authority_clarity_watch",
        "boundary_condition_count_watch",
        "conflicting_interpretation_pressure_watch",
        "deadline_proximity_watch",
        "clause_ambiguity_score_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_no_non_decimal_public_numbers(result)

    blocked, watched, passed = result.rows
    assert tuple(row.public_event_bucket for row in result.rows) == (
        "block_bucket",
        "watch_bucket",
        "pass_bucket",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert blocked.clause_ambiguity_score == d("0.745000")
    assert blocked.reason_codes == (
        "authority_clarity_block",
        "boundary_condition_count_block",
        "conflicting_interpretation_pressure_block",
        "deadline_proximity_block",
        "clause_ambiguity_score_block",
    )
    assert watched.clause_ambiguity_score == d("0.374250")
    assert watched.reason_codes == (
        "authority_clarity_watch",
        "boundary_condition_count_watch",
        "conflicting_interpretation_pressure_watch",
        "deadline_proximity_watch",
        "clause_ambiguity_score_watch",
    )
    assert passed.clause_ambiguity_score == d("0.037500")
    assert passed.reason_codes == ("clause_ambiguity_clear",)


def test_boundary_thresholds_are_inclusive_for_watch_and_block() -> None:
    watched = report(
        subject(
            public_event_bucket="threshold_watch",
            authority_clarity=d("0.550000"),
            boundary_condition_count=d("2.000000"),
            conflicting_interpretation_pressure=d("0.300000"),
            deadline_proximity=d("0.500000"),
        ),
    )
    assert watched.status == "watch"
    assert watched.rows[0].status == "watch"
    assert watched.rows[0].clause_ambiguity_score == d("0.370000")
    assert watched.rows[0].reason_codes == (
        "authority_clarity_watch",
        "boundary_condition_count_watch",
        "conflicting_interpretation_pressure_watch",
        "deadline_proximity_watch",
        "clause_ambiguity_score_watch",
    )

    blocked = report(
        subject(
            public_event_bucket="threshold_block",
            boundary_condition_count=d("5.000000"),
        ),
    )
    assert blocked.status == "block"
    assert blocked.rows[0].reason_codes == ("boundary_condition_count_block",)


def test_payload_is_deterministic_public_safe_and_digest_checked() -> None:
    first = report(
        subject(public_event_bucket="z_pass"),
        subject(
            public_event_bucket="a_watch",
            boundary_condition_count=d("2.000000"),
        ),
    )
    second = report(
        subject(
            public_event_bucket="a_watch",
            boundary_condition_count=d("2.000000"),
        ),
        subject(public_event_bucket="z_pass"),
    )

    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest

    payload = research_event_resolution_clause_ambiguity_matrix_report_payload(first)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["event_count"] == "2.000000"
    assert payload["highest_clause_ambiguity_score"] == "0.100000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert research_event_resolution_clause_ambiguity_matrix_report_payload(payload) == payload
    assert_digest(payload["derived_validation_digest"])
    assert_no_float_values(payload)
    assert_no_forbidden_public_terms(payload)

    with pytest.raises(FrozenInstanceError):
        first.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["event_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_clause_ambiguity_matrix_report_payload(tampered)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_clause_ambiguity_matrix_report_payload(
            unsafe_key_payload,
        )


def test_custom_thresholds_and_validation_are_enforced() -> None:
    custom = ResearchEventResolutionClauseAmbiguityMatrixConfig(
        authority_clarity_watch_floor=d("0.700000"),
        authority_clarity_block_floor=d("0.300000"),
        boundary_condition_watch_count=d("4.000000"),
        boundary_condition_block_count=d("8.000000"),
        conflicting_interpretation_watch_ceiling=d("0.600000"),
        conflicting_interpretation_block_ceiling=d("0.900000"),
        deadline_proximity_watch_ceiling=d("0.700000"),
        deadline_proximity_block_ceiling=d("0.950000"),
        watch_ambiguity_score_threshold=d("0.400000"),
        block_ambiguity_score_threshold=d("0.800000"),
    )
    result = report(
        subject(
            authority_clarity=d("0.720000"),
            boundary_condition_count=d("3.000000"),
            conflicting_interpretation_pressure=d("0.400000"),
            deadline_proximity=d("0.550000"),
        ),
        config=custom,
    )
    assert result.status == "pass"
    assert result.rows[0].reason_codes == ("clause_ambiguity_clear",)

    with pytest.raises(ValueError, match="unsafe"):
        subject(public_event_bucket="candidate_123")
    with pytest.raises(ValueError, match="Decimal"):
        subject(authority_clarity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        subject(conflicting_interpretation_pressure=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventResolutionClauseAmbiguityMatrixConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        subject(report_only=False)
    with pytest.raises(ValueError, match="block"):
        ResearchEventResolutionClauseAmbiguityMatrixConfig(
            authority_clarity_block_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="threshold"):
        ResearchEventResolutionClauseAmbiguityMatrixConfig(
            block_ambiguity_score_threshold=d("0.250000"),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report(subject()).rows[0], status="review")


def test_empty_report_blocks_without_clause_evidence() -> None:
    result = report()

    assert result.event_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.lowest_authority_clarity == d("0.000000")
    assert result.highest_boundary_condition_count == d("0.000000")
    assert result.highest_conflicting_interpretation_pressure == d("0.000000")
    assert result.highest_deadline_proximity == d("0.000000")
    assert result.highest_clause_ambiguity_score == d("0.000000")
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == (
        "clause_ambiguity_matrix_report_empty",
        "clause_evidence_missing",
    )
    assert result.reason_code_counts == ()


def test_module_does_not_import_db_network_trading_or_live_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    banned_fragments = (
        "asyncpg",
        "psycopg",
        "requests",
        "urllib",
        "websocket",
        "sqlalchemy",
        "supabase",
        "order",
        "trade",
        "wallet",
        "live",
    )
    assert not any(
        fragment in module_name.lower()
        for fragment in banned_fragments
        for module_name in imported_modules
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_no_non_decimal_public_numbers(value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            assert_no_non_decimal_public_numbers(item_value)
        return
    if isinstance(value, tuple):
        for item in value:
            assert_no_non_decimal_public_numbers(item)
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected non-Decimal public number: {value!r}")


def assert_no_forbidden_public_terms(payload: dict[str, Any]) -> None:
    public_json = str(payload).lower()
    forbidden_terms = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )
    assert all(term not in public_json for term in forbidden_terms)
