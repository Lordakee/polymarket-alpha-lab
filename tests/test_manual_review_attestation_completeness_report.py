from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.manual_review_attestation_completeness_report import (
    ATTESTATION_STATUSES,
    DEFAULT_MANUAL_REVIEW_ATTESTATION_COMPLETENESS_CONFIG_VERSION,
    MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS,
    ManualReviewAttestationCompletenessConfig,
    ManualReviewAttestationCompletenessInput,
    ManualReviewAttestationCompletenessReport,
    ManualReviewAttestationCompletenessSectionRow,
    build_manual_review_attestation_completeness_report,
    manual_review_attestation_completeness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 14, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/manual_review_attestation_completeness_report.py",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def review_input(**overrides: object) -> ManualReviewAttestationCompletenessInput:
    values = {
        "operator_id": "operator-42",
        "reviewed_screen": True,
        "reviewed_sources": True,
        "reviewed_costs": True,
        "reviewed_memory_policy": True,
        "reviewed_resolution_rules": True,
        "attestation_text_present": True,
    }
    values.update(overrides)
    return ManualReviewAttestationCompletenessInput(**values)


def build_report(
    item: ManualReviewAttestationCompletenessInput,
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: ManualReviewAttestationCompletenessConfig | None = None,
) -> ManualReviewAttestationCompletenessReport:
    return build_manual_review_attestation_completeness_report(
        item,
        config=cfg if cfg is not None else ManualReviewAttestationCompletenessConfig(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload_values(item))
        return tuple(nested)
    return (value,)


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
    if isinstance(value, (dict, list, tuple)):
        children = value.values() if isinstance(value, dict) else value
        for child in children:
            assert_public_numeric_values_are_decimal(child)


def test_public_api_declares_required_sections_statuses_and_hard_flags() -> None:
    assert DEFAULT_MANUAL_REVIEW_ATTESTATION_COMPLETENESS_CONFIG_VERSION == (
        "manual-review-attestation-completeness-report-v0"
    )
    assert ATTESTATION_STATUSES == ("complete", "incomplete")
    assert MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS == (
        "operator_id",
        "reviewed_screen",
        "reviewed_sources",
        "reviewed_costs",
        "reviewed_memory_policy",
        "reviewed_resolution_rules",
        "attestation_text_present",
    )

    defaults = {
        field.name: field.default
        for field in fields(ManualReviewAttestationCompletenessConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True


def test_complete_attestation_reports_complete_without_trade_authorization() -> None:
    report = build_report(
        review_input(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.attestation_status == "complete"
    assert report.operator_id == "operator-42"
    assert report.required_section_count == d("7")
    assert report.completed_section_count == d("7")
    assert report.missing_section_count == d("0")
    assert report.missing_sections == ()
    assert report.reason_codes == ("manual_review_attestation_complete",)
    assert report.manual_next_step == "manual_review_attestation_complete_report_only"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.section, row.is_complete) for row in report.rows) == (
        ("operator_id", True),
        ("reviewed_screen", True),
        ("reviewed_sources", True),
        ("reviewed_costs", True),
        ("reviewed_memory_policy", True),
        ("reviewed_resolution_rules", True),
        ("attestation_text_present", True),
    )


def test_missing_sections_report_incomplete_with_manual_next_step() -> None:
    report = build_report(
        review_input(
            operator_id="",
            reviewed_sources=False,
            reviewed_costs=False,
            reviewed_memory_policy=False,
            attestation_text_present=False,
        ),
    )

    assert report.attestation_status == "incomplete"
    assert report.operator_id is None
    assert report.required_section_count == d("7")
    assert report.completed_section_count == d("2")
    assert report.missing_section_count == d("5")
    assert report.missing_sections == (
        "operator_id",
        "reviewed_sources",
        "reviewed_costs",
        "reviewed_memory_policy",
        "attestation_text_present",
    )
    assert report.reason_codes == (
        "manual_review_operator_id_missing",
        "manual_review_sources_not_reviewed",
        "manual_review_costs_not_reviewed",
        "manual_review_memory_policy_not_reviewed",
        "manual_review_attestation_text_missing",
    )
    assert report.manual_next_step == "complete_missing_manual_review_sections_before_any_use"


def test_payload_and_digest_are_deterministic_public_safe_and_string_numeric() -> None:
    first = build_report(review_input(reviewed_resolution_rules=False))
    second = build_report(review_input(reviewed_resolution_rules=False))
    payload_first = manual_review_attestation_completeness_report_payload(first)
    payload_second = manual_review_attestation_completeness_report_payload(second)

    assert first.report_digest == second.report_digest
    assert payload_first == payload_second
    assert len(first.report_digest) == 64
    assert payload_first["report_digest"] == first.report_digest
    assert payload_first["required_section_count"] == "7"
    assert payload_first["missing_section_count"] == "1"
    assert payload_first["generated_at"] == "2026-07-11T14:30:00+00:00"
    assert not any(
        type(value) in (Decimal, int, float)
        for value in walk_payload_values(payload_first)
    )

    payload_text = repr(payload_first).lower()
    for fragment in (
        "candidate_id",
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "wal" "let",
        "au" "th",
        "ord" "er",
        "tra" "de",
        "li" "ve",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "position_size",
        "position sizing",
    ):
        assert fragment not in payload_text

    tampered = dict(payload_first)
    tampered["manual_next_step"] = "manual_review_attestation_complete_report_only"
    with pytest.raises(ValueError, match="report_digest"):
        manual_review_attestation_completeness_report_payload(tampered)


def test_validation_rejects_non_bool_sections_raw_ids_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="reviewed_screen must be a bool"):
        review_input(reviewed_screen=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="operator_id must be a public operator identifier"):
        review_input(operator_id=" operator-42 ")
    with pytest.raises(ValueError, match="operator_id must not contain raw public identifiers"):
        review_input(operator_id="candidate_id-42")
    with pytest.raises(ValueError, match="paper_only must be True"):
        review_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        ManualReviewAttestationCompletenessConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_manual_review_attestation_completeness_report(
            review_input(readonly=False),
            config=ManualReviewAttestationCompletenessConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(review_input(), generated_at=datetime(2026, 7, 11, 14, 30))


def test_dataclasses_are_frozen_decimal_only_and_consistency_checked() -> None:
    sample_config = ManualReviewAttestationCompletenessConfig()
    sample_input = review_input()
    sample_report = build_report(sample_input)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_input, sample_row, sample_report):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="report_digest must match report fields"):
        replace(sample_report, report_digest="0" * 64)
    with pytest.raises(ValueError, match="missing_sections must match rows"):
        replace(sample_report, missing_sections=("reviewed_screen",))
    with pytest.raises(ValueError, match="reason_codes must match row"):
        replace(sample_row, reason_code="manual_review_sources_not_reviewed")


def test_module_scope_has_no_durable_or_action_surfaces() -> None:
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
        "request",
        "urllib",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "supabase",
        "client",
        "broker",
        "store",
        "data" "base",
        "wal" "let",
        "au" "th",
    )
    forbidden_call_or_attribute_names = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "fetch",
        "insert",
        "send",
        "submit",
        "sign",
        "b" "uy",
        "se" "ll",
        "tra" "de",
        "write",
    }
    source_text = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for fragment in (
        "wal" "let",
        "au" "th",
        "ord" "er",
        "tra" "de",
        "li" "ve execution",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "position_size",
        "position sizing",
    ):
        assert fragment not in source_text
