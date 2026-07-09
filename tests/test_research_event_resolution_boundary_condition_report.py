from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_resolution_boundary_condition_report as api
from polymarket_alpha_lab.research_event_resolution_boundary_condition_report import (
    ResearchEventResolutionBoundaryConditionConfig,
    ResearchEventResolutionBoundaryConditionReport,
    ResearchEventResolutionBoundaryConditionSubject,
    build_research_event_resolution_boundary_condition_report,
    research_event_resolution_boundary_condition_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_boundary_condition_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def subject(**overrides: object) -> ResearchEventResolutionBoundaryConditionSubject:
    values = {
        "public_event_bucket": "macro_policy",
        "date_boundary_precision": d("0.950000"),
        "threshold_definition_clarity": d("0.950000"),
        "exception_clause_coverage": d("0.900000"),
        "authority_traceability": d("0.950000"),
        "contradiction_pressure": d("0.050000"),
        "reviewer_verification_coverage": d("0.900000"),
    }
    values.update(overrides)
    return ResearchEventResolutionBoundaryConditionSubject(**values)


def report(
    *subjects: ResearchEventResolutionBoundaryConditionSubject,
    config: ResearchEventResolutionBoundaryConditionConfig | None = None,
) -> ResearchEventResolutionBoundaryConditionReport:
    return build_research_event_resolution_boundary_condition_report(
        subjects,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_public_api_declares_report_only_boundary_condition_surface() -> None:
    assert api.DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION == (
        "research-event-resolution-boundary-condition-report-v0"
    )
    assert api.RESOLUTION_BOUNDARY_CONDITION_DIMENSIONS == (
        "date_boundary",
        "threshold_definition",
        "exception_clause",
        "authority_traceability",
        "contradiction_pressure",
        "reviewer_verification",
    )
    assert api.RESOLUTION_BOUNDARY_CONDITION_STATUSES == ("pass", "watch", "block")
    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_BOUNDARY_CONDITION_CONFIG_VERSION",
        "RESOLUTION_BOUNDARY_CONDITION_DIMENSIONS",
        "RESOLUTION_BOUNDARY_CONDITION_STATUSES",
        "ResearchEventResolutionBoundaryConditionConfig",
        "ResearchEventResolutionBoundaryConditionReport",
        "ResearchEventResolutionBoundaryConditionRow",
        "ResearchEventResolutionBoundaryConditionSubject",
        "build_research_event_resolution_boundary_condition_report",
        "research_event_resolution_boundary_condition_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(ResearchEventResolutionBoundaryConditionConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True
    assert field_defaults["date_boundary_watch_floor"] == d("0.750000")
    assert field_defaults["date_boundary_block_floor"] == d("0.500000")
    assert field_defaults["threshold_definition_watch_floor"] == d("0.750000")
    assert field_defaults["threshold_definition_block_floor"] == d("0.500000")
    assert field_defaults["contradiction_pressure_watch_ceiling"] == d("0.350000")
    assert field_defaults["contradiction_pressure_block_ceiling"] == d("0.700000")
    assert field_defaults["watch_risk_score_threshold"] == d("0.250000")
    assert field_defaults["block_risk_score_threshold"] == d("0.600000")


def test_boundary_condition_report_scores_pass_watch_and_block_deterministically() -> None:
    result = report(
        subject(public_event_bucket="pass_bucket"),
        subject(
            public_event_bucket="watch_bucket",
            date_boundary_precision=d("0.700000"),
            threshold_definition_clarity=d("0.720000"),
            exception_clause_coverage=d("0.650000"),
            authority_traceability=d("0.680000"),
            contradiction_pressure=d("0.400000"),
            reviewer_verification_coverage=d("0.700000"),
        ),
        subject(
            public_event_bucket="block_bucket",
            date_boundary_precision=d("0.450000"),
            threshold_definition_clarity=d("0.400000"),
            exception_clause_coverage=d("0.350000"),
            authority_traceability=d("0.300000"),
            contradiction_pressure=d("0.850000"),
            reviewer_verification_coverage=d("0.400000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-event-resolution-boundary-condition-report-v0"
    )
    assert result.event_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.lowest_date_boundary_precision == d("0.450000")
    assert result.lowest_threshold_definition_clarity == d("0.400000")
    assert result.lowest_exception_clause_coverage == d("0.350000")
    assert result.lowest_authority_traceability == d("0.300000")
    assert result.highest_contradiction_pressure == d("0.850000")
    assert result.lowest_reviewer_verification_coverage == d("0.400000")
    assert result.highest_boundary_condition_risk_score == d("0.650000")
    assert result.status == "block"
    assert result.reason_codes == (
        "boundary_condition_report_block_rows",
        "boundary_condition_report_watch_rows",
        "date_boundary_block",
        "threshold_definition_block",
        "exception_clause_block",
        "authority_traceability_block",
        "contradiction_pressure_block",
        "reviewer_verification_block",
        "boundary_condition_risk_block",
        "date_boundary_watch",
        "threshold_definition_watch",
        "exception_clause_watch",
        "authority_traceability_watch",
        "contradiction_pressure_watch",
        "reviewer_verification_watch",
        "boundary_condition_risk_watch",
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
    assert blocked.boundary_condition_risk_score == d("0.650000")
    assert blocked.reason_codes == (
        "date_boundary_block",
        "threshold_definition_block",
        "exception_clause_block",
        "authority_traceability_block",
        "contradiction_pressure_block",
        "reviewer_verification_block",
        "boundary_condition_risk_block",
    )
    assert watched.boundary_condition_risk_score == d("0.321500")
    assert watched.reason_codes == (
        "date_boundary_watch",
        "threshold_definition_watch",
        "exception_clause_watch",
        "authority_traceability_watch",
        "contradiction_pressure_watch",
        "reviewer_verification_watch",
        "boundary_condition_risk_watch",
    )
    assert passed.boundary_condition_risk_score == d("0.065000")
    assert passed.reason_codes == ("boundary_condition_clear",)

    same_result = report(
        subject(
            public_event_bucket="block_bucket",
            date_boundary_precision=d("0.450000"),
            threshold_definition_clarity=d("0.400000"),
            exception_clause_coverage=d("0.350000"),
            authority_traceability=d("0.300000"),
            contradiction_pressure=d("0.850000"),
            reviewer_verification_coverage=d("0.400000"),
        ),
        subject(public_event_bucket="pass_bucket"),
        subject(
            public_event_bucket="watch_bucket",
            date_boundary_precision=d("0.700000"),
            threshold_definition_clarity=d("0.720000"),
            exception_clause_coverage=d("0.650000"),
            authority_traceability=d("0.680000"),
            contradiction_pressure=d("0.400000"),
            reviewer_verification_coverage=d("0.700000"),
        ),
    )
    assert same_result.rows == result.rows
    assert same_result.derived_validation_digest == result.derived_validation_digest


def test_payload_is_public_safe_decimal_only_and_digest_checked() -> None:
    result = report(subject(public_event_bucket="payload_bucket"))
    payload = research_event_resolution_boundary_condition_report_payload(result)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["event_count"] == "1.000000"
    assert payload["highest_boundary_condition_risk_score"] == "0.065000"
    assert payload["rows"][0]["boundary_condition_risk_score"] == "0.065000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert_digest(payload["derived_validation_digest"])
    assert_no_float_values(payload)
    assert_no_non_decimal_public_numbers(result)
    assert research_event_resolution_boundary_condition_report_payload(payload) == payload

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_boundary_condition_report_payload(tampered)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_boundary_condition_report_payload(unsafe_key_payload)

    with pytest.raises(ValueError, match="unsafe"):
        subject(public_event_bucket="candidate_123")
    with pytest.raises(ValueError, match="Decimal"):
        subject(date_boundary_precision=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        subject(threshold_definition_clarity=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="review")
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventResolutionBoundaryConditionConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        subject(report_only=False)


def test_empty_report_blocks_for_missing_reviewer_verification_coverage() -> None:
    result = report()

    assert result.event_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.lowest_date_boundary_precision == d("0.000000")
    assert result.highest_contradiction_pressure == d("0.000000")
    assert result.lowest_reviewer_verification_coverage == d("0.000000")
    assert result.highest_boundary_condition_risk_score == d("0.000000")
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == (
        "boundary_condition_report_empty",
        "reviewer_verification_missing",
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
