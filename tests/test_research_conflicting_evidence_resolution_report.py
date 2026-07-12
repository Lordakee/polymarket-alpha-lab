from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_conflicting_evidence_resolution_report import (
    DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION,
    DOMINANT_EVIDENCE_SIDES,
    EVIDENCE_STANCES,
    SOURCE_TYPES,
    STATUSES,
    ResearchConflictingEvidenceResolutionConfig,
    ResearchConflictingEvidenceResolutionEvidenceItem,
    ResearchConflictingEvidenceResolutionReasonCodeCount,
    ResearchConflictingEvidenceResolutionReport,
    ResearchConflictingEvidenceResolutionRow,
    build_research_conflicting_evidence_resolution_report,
    research_conflicting_evidence_resolution_report_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_conflicting_evidence_resolution_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchConflictingEvidenceResolutionConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION,
        "fresh_age_hours": d("24.000000"),
        "stale_age_hours": d("72.000000"),
        "confidence_high_threshold": d("0.750000"),
        "official_weight": d("1.500000"),
        "freshness_weight": d("0.250000"),
        "minimum_independent_source_count": d("3"),
        "severe_conflict_threshold": d("0.350000"),
        "moderate_conflict_threshold": d("0.150000"),
        "dominance_margin_threshold": d("0.200000"),
    }
    values.update(overrides)
    return ResearchConflictingEvidenceResolutionConfig(**values)


def item(
    source_type: str,
    stance: str,
    *,
    age: str,
    official: bool = False,
    confidence: str = "0.700000",
) -> ResearchConflictingEvidenceResolutionEvidenceItem:
    return ResearchConflictingEvidenceResolutionEvidenceItem(
        source_type=source_type,
        freshness_age_hours=d(age),
        stance=stance,
        official=official,
        confidence=d(confidence),
    )


def report(
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    *,
    cfg: ResearchConflictingEvidenceResolutionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchConflictingEvidenceResolutionReport:
    return build_research_conflicting_evidence_resolution_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item_value in value.values():
            nested.extend(walk_payload_values(item_value))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item_value in value:
            nested.extend(walk_payload_values(item_value))
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


def test_public_api_declares_readonly_resolution_contract() -> None:
    assert DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION == (
        "research-conflicting-evidence-resolution-report-v0"
    )
    assert STATUSES == ("ready", "attention", "blocker")
    assert EVIDENCE_STANCES == ("supports_yes", "supports_no", "neutral")
    assert DOMINANT_EVIDENCE_SIDES == ("supports_yes", "supports_no", "balanced", "none")
    assert SOURCE_TYPES == ("official", "primary", "secondary", "aggregator", "other")

    defaults = {
        field.name: field.default
        for field in fields(ResearchConflictingEvidenceResolutionConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True
    assert defaults["minimum_independent_source_count"] == d("3")
    assert defaults["severe_conflict_threshold"] == d("0.350000")


def test_blocks_manual_review_when_high_confidence_sides_conflict() -> None:
    summary = report(
        (
            item(
                "official",
                "supports_yes",
                age="4.000000",
                official=True,
                confidence="0.950000",
            ),
            item("primary", "supports_yes", age="18.000000", confidence="0.850000"),
            item(
                "official",
                "supports_no",
                age="2.000000",
                official=True,
                confidence="0.900000",
            ),
            item("secondary", "supports_no", age="20.000000", confidence="0.800000"),
            item("aggregator", "neutral", age="10.000000", confidence="0.600000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.status == "blocker"
    assert summary.evidence_item_count == d("5")
    assert summary.supports_yes_count == d("2")
    assert summary.supports_no_count == d("2")
    assert summary.neutral_count == d("1")
    assert summary.independent_source_count == d("4")
    assert summary.required_extra_independent_sources == d("0")
    assert summary.manual_review_required is True
    assert summary.preflight_ready_count == d("0")
    assert summary.preflight_attention_count == d("0")
    assert summary.preflight_blocker_count == d("1")

    row = summary.row
    assert row.dominant_evidence_side == "balanced"
    assert row.conflict_severity_score == d("0.900000")
    assert row.yes_weighted_confidence == d("2.546875")
    assert row.no_weighted_confidence == d("2.397500")
    assert row.neutral_weighted_confidence == d("0.681250")
    assert row.required_extra_independent_sources == d("0")
    assert row.manual_review_required is True
    assert row.status == "blocker"
    assert row.reason_codes == (
        "conflicting_evidence_severe",
        "dominant_side_balanced",
        "manual_review_required",
        "resolution_blocker",
    )
    assert summary.reason_codes == row.reason_codes


def test_attention_when_quorum_missing_even_without_material_conflict() -> None:
    summary = report(
        (
            item(
                "official",
                "supports_yes",
                age="12.000000",
                official=True,
                confidence="0.880000",
            ),
            item("primary", "supports_yes", age="30.000000", confidence="0.700000"),
            item("secondary", "neutral", age="50.000000", confidence="0.400000"),
        ),
        cfg=config(minimum_independent_source_count=d("4")),
    )

    assert summary.status == "attention"
    assert summary.independent_source_count == d("3")
    assert summary.required_extra_independent_sources == d("1")
    assert summary.manual_review_required is True
    assert summary.preflight_ready_count == d("0")
    assert summary.preflight_attention_count == d("1")
    assert summary.preflight_blocker_count == d("0")
    assert summary.row.dominant_evidence_side == "supports_yes"
    assert summary.row.conflict_severity_score == d("0.000000")
    assert summary.row.reason_codes == (
        "insufficient_independent_sources",
        "manual_review_required",
        "resolution_attention",
    )


def test_ready_when_fresh_official_dominant_evidence_has_source_quorum() -> None:
    summary = report(
        (
            item(
                "official",
                "supports_no",
                age="6.000000",
                official=True,
                confidence="0.920000",
            ),
            item("primary", "supports_no", age="14.000000", confidence="0.820000"),
            item("secondary", "supports_no", age="36.000000", confidence="0.620000"),
            item("aggregator", "neutral", age="40.000000", confidence="0.500000"),
        ),
    )

    assert summary.status == "ready"
    assert summary.row.dominant_evidence_side == "supports_no"
    assert summary.row.conflict_severity_score == d("0.000000")
    assert summary.required_extra_independent_sources == d("0")
    assert summary.manual_review_required is False
    assert summary.reason_codes == ("resolution_ready",)
    assert summary.preflight_ready_count == d("1")
    assert summary.preflight_attention_count == d("0")
    assert summary.preflight_blocker_count == d("0")


def test_payload_and_digest_are_deterministic_public_safe_and_string_numeric() -> None:
    input_items = (
        item("official", "supports_yes", age="4.000000", official=True, confidence="0.900000"),
        item("primary", "supports_no", age="12.000000", confidence="0.820000"),
        item("secondary", "neutral", age="48.000000", confidence="0.500000"),
    )

    first = report(input_items)
    second = report(input_items)
    payload_first = research_conflicting_evidence_resolution_report_payload(first)
    payload_second = research_conflicting_evidence_resolution_report_payload(second)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload_first == payload_second
    assert len(first.derived_validation_digest) == 64
    assert payload_first["derived_validation_digest"] == first.derived_validation_digest
    assert payload_first["row"]["conflict_severity_score"] == "0.820000"
    assert payload_first["row"]["dominant_evidence_side"] == "balanced"
    assert payload_first["generated_at"] == "2026-07-11T12:00:00+00:00"
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
        "source_url",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "position_size",
        "position sizing",
    ):
        assert fragment not in payload_text

    tampered = dict(payload_first)
    tampered["status"] = "ready"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_conflicting_evidence_resolution_report_payload(tampered)


def test_validation_rejects_non_decimal_inputs_bad_flags_and_unsafe_strings() -> None:
    with pytest.raises(ValueError, match="freshness_age_hours must be a Decimal"):
        item("official", "supports_yes", age="1.000000", confidence="0.900000").__class__(
            source_type="official",
            freshness_age_hours=1,  # type: ignore[arg-type]
            stance="supports_yes",
            official=True,
            confidence=d("0.900000"),
        )
    with pytest.raises(ValueError, match="confidence must be a Decimal"):
        item(
            "primary",
            "supports_yes",
            age="1.000000",
            confidence="0.900000",
        ).__class__(
            source_type="primary",
            freshness_age_hours=d("1.000000"),
            stance="supports_yes",
            official=False,
            confidence=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="source_type must be a supported source type"):
        item("source_url", "supports_yes", age="1.000000")
    with pytest.raises(ValueError, match="stance must be a supported evidence stance"):
        item("official", "yes", age="1.000000")
    with pytest.raises(ValueError, match="official must be a bool"):
        ResearchConflictingEvidenceResolutionEvidenceItem(
            source_type="official",
            freshness_age_hours=d("1.000000"),
            stance="supports_yes",
            official=1,  # type: ignore[arg-type]
            confidence=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchConflictingEvidenceResolutionEvidenceItem(
            source_type="official",
            freshness_age_hours=d("1.000000"),
            stance="supports_yes",
            official=True,
            confidence=d("0.900000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_research_conflicting_evidence_resolution_report(
            (
                ResearchConflictingEvidenceResolutionEvidenceItem(
                    source_type="official",
                    freshness_age_hours=d("1.000000"),
                    stance="supports_yes",
                    official=True,
                    confidence=d("0.900000"),
                    readonly=False,
                ),
            ),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="fresh_age_hours must be below stale_age_hours"):
        config(fresh_age_hours=d("72.000000"), stale_age_hours=d("24.000000"))
    with pytest.raises(ValueError, match="dominance_margin_threshold"):
        config(dominance_margin_threshold=d("1.000001"))


def test_dataclasses_are_frozen_decimal_only_and_consistency_checked() -> None:
    sample_config = config()
    sample_item = item("official", "supports_yes", age="4.000000", official=True)
    sample_report = report(
        (
            sample_item,
            item("primary", "supports_no", age="8.000000", confidence="0.800000"),
            item("secondary", "neutral", age="48.000000", confidence="0.500000"),
        ),
    )
    sample_row = sample_report.row
    sample_count = sample_report.reason_code_counts[0]

    for value in (sample_config, sample_item, sample_row, sample_count, sample_report):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(sample_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status must match row"):
        replace(sample_report, status="ready")
    with pytest.raises(ValueError, match="manual_review_required must match row"):
        replace(sample_report, manual_review_required=False)
    with pytest.raises(ValueError, match="reason_codes must match row status"):
        replace(sample_row, reason_codes=("resolution_ready",))


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
        "database",
        "wallet",
        "auth",
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
        "buy",
        "sell",
        "trade",
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
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "buy",
        "sell",
        "recommend",
        "position_size",
        "position sizing",
    ):
        assert fragment not in source_text
