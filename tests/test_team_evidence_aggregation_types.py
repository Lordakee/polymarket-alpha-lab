from __future__ import annotations

import ast
from dataclasses import MISSING, FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_UP, getcontext, setcontext
import inspect
from pathlib import Path
import re
from typing import get_type_hints

import pytest

import polymarket_alpha_lab.team_evidence_aggregation_types as types_module
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAggregationResult,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceContradictionResult,
    TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceDiagnosticRow,
    TeamEvidenceRequirement,
    TeamEvidenceRequirementCoverage,
    TeamEvidenceRequirementWitness,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceTemporalAssessment,
    TeamEvidenceWeightAllocation,
)


ANCHOR = datetime(2026, 7, 13, 10, 30, tzinfo=UTC)
CAPTURED = datetime(2026, 7, 13, 10, 34, tzinfo=UTC)
RECORDED = datetime(2026, 7, 13, 10, 35, tzinfo=UTC)
ASSESSED = datetime(2026, 7, 13, 10, 36, tzinfo=UTC)
EVALUATED = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
HARD_FLAGS = ("paper_only", "report_only", "readonly")


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**changes: object) -> TeamEvidenceAggregationConfig:
    values: dict[str, object] = {
        "config_version": "agg-test-v1",
        "max_evidence_age_seconds": d("7200.000000"),
        "max_capture_lag_seconds": d("300.000000"),
        "independence_group_weight_cap": d("0.730000"),
        "correlation_group_weight_cap": d("0.610000"),
        "max_requirement_assignments_per_evidence": 3,
        "contradiction_no_probability_max": d("0.210000"),
        "contradiction_yes_probability_min": d("0.790000"),
        "contradiction_watch_score": d("0.310000"),
        "contradiction_block_score": d("0.670000"),
        "publish_probability_floor": d("0.110000"),
        "publish_probability_ceiling": d("0.890000"),
        "maximum_records": 8,
        "maximum_requirements": 4,
        "maximum_requirement_memberships": 16,
        "maximum_witness_edges": 12,
        "requirements": (
            TeamEvidenceRequirement(
                requirement_id="macro.release",
                minimum_witness_count=1,
                minimum_effective_weight=d("0.120000"),
                unmet_status="blocked",
            ),
        ),
    }
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)


def lineage_graph(**changes: object) -> TeamEvidenceAggregationRecord:
    prefix = str(changes.pop("prefix", "alpha"))
    chars = {"alpha": "abcdef", "beta": "123456", "gamma": "789abc"}[prefix]
    lineage_values: dict[str, object] = {
        "source_lineage_id": f"lineage.{prefix}",
        "source_lineage_digest": digest(chars[0]),
    }
    capture_values: dict[str, object] = {
        "capture_id": f"capture.{prefix}.1",
        "capture_digest": digest(chars[1]),
        "source_lineage_id": lineage_values["source_lineage_id"],
        "source_lineage_digest": lineage_values["source_lineage_digest"],
        "content_digest": digest(chars[2]),
        "captured_at": CAPTURED,
    }
    evidence_values: dict[str, object] = {
        "evidence_revision_id": f"evidence.{prefix}.1",
        "evidence_revision_digest": digest(chars[3]),
        "previous_evidence_revision_id": None,
        "previous_evidence_revision_digest": None,
        "source_lineage_id": lineage_values["source_lineage_id"],
        "source_lineage_digest": lineage_values["source_lineage_digest"],
        "content_digest": capture_values["content_digest"],
        "requirement_ids": ("macro.release",),
        "freshness_anchor_at": ANCHOR,
        "recorded_at": RECORDED,
    }
    assessment_values: dict[str, object] = {
        "assessment_revision_id": f"assessment.{prefix}.1",
        "assessment_revision_digest": digest(chars[4]),
        "previous_assessment_revision_id": None,
        "previous_assessment_revision_digest": None,
        "evidence_revision_id": evidence_values["evidence_revision_id"],
        "evidence_revision_digest": evidence_values["evidence_revision_digest"],
        "assessed_at": ASSESSED,
        "probability_yes": d("0.640000"),
        "requested_weight": d("0.400000"),
        "rationale_digest": digest(chars[5]),
        "independence_key": f"desk.{prefix}",
        "correlation_key": "macro.shared",
    }
    for name, values in (
        ("source_lineage", lineage_values),
        ("capture", capture_values),
        ("evidence_revision", evidence_values),
        ("assessment_revision", assessment_values),
    ):
        values.update(changes.pop(name, {}))
    if changes:
        raise AssertionError(f"unknown lineage_graph changes: {tuple(changes)}")
    lineage = TeamEvidenceSourceLineage(**lineage_values)
    capture = TeamEvidenceCapture(**capture_values)
    evidence = TeamEvidenceRevision(**evidence_values)
    assessment = TeamEvidenceAssessmentRevision(**assessment_values)
    return TeamEvidenceAggregationRecord(
        source_lineage=lineage,
        capture=capture,
        evidence_revision=evidence,
        assessment_revision=assessment,
    )


def aggregation_input(**changes: object) -> TeamEvidenceAggregationInput:
    record = changes.pop("record", None) or lineage_graph()
    values: dict[str, object] = {
        "evaluated_at": EVALUATED,
        "records": (record,),
        "current_revisions": (
            TeamEvidenceCurrentRevisionSelection(
                evidence_revision_id=record.evidence_revision.evidence_revision_id,
                evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
                assessment_revision_id=record.assessment_revision.assessment_revision_id,
                assessment_revision_digest=record.assessment_revision.assessment_revision_digest,
            ),
        ),
    }
    values.update(changes)
    return TeamEvidenceAggregationInput(**values)


def expected_record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )


def _derived_values() -> tuple[object, ...]:
    temporal = TeamEvidenceTemporalAssessment(
        capture_id="capture.alpha.1", evidence_revision_id="evidence.alpha.1",
        assessment_revision_id="assessment.alpha.1", evidence_age_seconds=d("5400"),
        capture_lag_seconds=d("240"), effective_at_evaluation=True,
        captured_at_evaluation=True, evidence_revision_available_at_evaluation=True,
        assessment_revision_available_at_evaluation=True, fresh=True, timely=True,
    )
    allocation = TeamEvidenceWeightAllocation(
        source_lineage_id="lineage.alpha", capture_id="capture.alpha.1",
        evidence_revision_id="evidence.alpha.1", assessment_revision_id="assessment.alpha.1",
        independence_key="desk.alpha", correlation_key="macro.shared",
        requested_weight=d("0.4"), independence_allocated_weight=d("0.3"),
        effective_weight=d("0.2"), independence_cap_applied=True,
        correlation_cap_applied=True,
    )
    witness = TeamEvidenceRequirementWitness(
        requirement_id="macro.release", source_lineage_id="lineage.alpha",
        capture_id="capture.alpha.1", evidence_revision_id="evidence.alpha.1",
        assessment_revision_id="assessment.alpha.1", independence_key="desk.alpha",
        effective_weight=d("0.2"),
    )
    coverage = TeamEvidenceRequirementCoverage(
        requirement_id="macro.release", minimum_witness_count=1,
        assigned_witness_count=1, minimum_effective_weight=d("0.12"),
        unmet_status="blocked", satisfied=True, witnesses=(witness,),
    )
    diagnostic = TeamEvidenceDiagnosticRow(
        source_lineage_id="lineage.alpha", capture_id="capture.alpha.1",
        captured_at=CAPTURED, evidence_revision_id="evidence.alpha.1",
        assessment_revision_id="assessment.alpha.1", probability_yes=d("0.64"),
        requested_weight=d("0.4"), independence_allocated_weight=d("0.3"),
        effective_weight=d("0.2"), evidence_age_seconds=d("5400"),
        capture_lag_seconds=d("240"), captured_at_evaluation=True,
        evidence_revision_available_at_evaluation=True,
        assessment_revision_available_at_evaluation=True,
        selected_current_revision=True, canonical_capture=True, disposition="included",
    )
    contradiction = TeamEvidenceContradictionResult(
        yes_support_weight=d("1.2"), no_support_weight=d("0.8"),
        neutral_weight=d("0.4"), contradiction_score=d("0.3"), status="watch",
    )
    result = TeamEvidenceAggregationResult(
        evaluated_at=EVALUATED, config_version="agg-test-v1", config_digest=digest("7"),
        status="watch", diagnostic_record_count=1, arithmetic_record_count=1,
        requested_weight_total=d("1.2"), independence_allocated_weight_total=d("1.1"),
        effective_weight_total=d("1.0"), arithmetic_probability_yes=d("0.64"),
        publishable_probability_yes=d("0.64"), contradiction=contradiction,
        requirement_coverage=(coverage,), diagnostics=(diagnostic,),
        reason_codes=("coverage.watch",), core_digest=digest("8"),
    )
    return temporal, allocation, witness, coverage, diagnostic, contradiction, result


PUBLIC_FIELD_TYPES = {
    TeamEvidenceSourceLineage: (("source_lineage_id", str), ("source_lineage_digest", str)),
    TeamEvidenceCapture: (("capture_id", str), ("capture_digest", str), ("source_lineage_id", str), ("source_lineage_digest", str), ("content_digest", str), ("captured_at", datetime)),
    TeamEvidenceRevision: (("evidence_revision_id", str), ("evidence_revision_digest", str), ("previous_evidence_revision_id", str | None), ("previous_evidence_revision_digest", str | None), ("source_lineage_id", str), ("source_lineage_digest", str), ("content_digest", str), ("requirement_ids", tuple[str, ...]), ("freshness_anchor_at", datetime), ("recorded_at", datetime)),
    TeamEvidenceAssessmentRevision: (("assessment_revision_id", str), ("assessment_revision_digest", str), ("previous_assessment_revision_id", str | None), ("previous_assessment_revision_digest", str | None), ("evidence_revision_id", str), ("evidence_revision_digest", str), ("assessed_at", datetime), ("probability_yes", Decimal), ("requested_weight", Decimal), ("rationale_digest", str), ("independence_key", str), ("correlation_key", str)),
    TeamEvidenceAggregationRecord: (("source_lineage", TeamEvidenceSourceLineage), ("capture", TeamEvidenceCapture), ("evidence_revision", TeamEvidenceRevision), ("assessment_revision", TeamEvidenceAssessmentRevision)),
    TeamEvidenceCurrentRevisionSelection: (("evidence_revision_id", str), ("evidence_revision_digest", str), ("assessment_revision_id", str), ("assessment_revision_digest", str)),
    TeamEvidenceAggregationInput: (("evaluated_at", datetime), ("records", tuple[TeamEvidenceAggregationRecord, ...]), ("current_revisions", tuple[TeamEvidenceCurrentRevisionSelection, ...])),
    TeamEvidenceRequirement: (("requirement_id", str), ("minimum_witness_count", int), ("minimum_effective_weight", Decimal), ("unmet_status", str)),
    TeamEvidenceAggregationConfig: (("config_version", str), ("max_evidence_age_seconds", Decimal), ("max_capture_lag_seconds", Decimal), ("independence_group_weight_cap", Decimal), ("correlation_group_weight_cap", Decimal), ("max_requirement_assignments_per_evidence", int), ("contradiction_no_probability_max", Decimal), ("contradiction_yes_probability_min", Decimal), ("contradiction_watch_score", Decimal), ("contradiction_block_score", Decimal), ("publish_probability_floor", Decimal), ("publish_probability_ceiling", Decimal), ("maximum_records", int), ("maximum_requirements", int), ("maximum_requirement_memberships", int), ("maximum_witness_edges", int), ("requirements", tuple[TeamEvidenceRequirement, ...])),
    TeamEvidenceTemporalAssessment: (("capture_id", str), ("evidence_revision_id", str), ("assessment_revision_id", str), ("evidence_age_seconds", Decimal), ("capture_lag_seconds", Decimal), ("effective_at_evaluation", bool), ("captured_at_evaluation", bool), ("evidence_revision_available_at_evaluation", bool), ("assessment_revision_available_at_evaluation", bool), ("fresh", bool), ("timely", bool)),
    TeamEvidenceWeightAllocation: (("source_lineage_id", str), ("capture_id", str), ("evidence_revision_id", str), ("assessment_revision_id", str), ("independence_key", str), ("correlation_key", str), ("requested_weight", Decimal), ("independence_allocated_weight", Decimal), ("effective_weight", Decimal), ("independence_cap_applied", bool), ("correlation_cap_applied", bool)),
    TeamEvidenceRequirementWitness: (("requirement_id", str), ("source_lineage_id", str), ("capture_id", str), ("evidence_revision_id", str), ("assessment_revision_id", str), ("independence_key", str), ("effective_weight", Decimal)),
    TeamEvidenceRequirementCoverage: (("requirement_id", str), ("minimum_witness_count", int), ("assigned_witness_count", int), ("minimum_effective_weight", Decimal), ("unmet_status", str), ("satisfied", bool), ("witnesses", tuple[TeamEvidenceRequirementWitness, ...])),
    TeamEvidenceDiagnosticRow: (("source_lineage_id", str), ("capture_id", str), ("captured_at", datetime), ("evidence_revision_id", str), ("assessment_revision_id", str), ("probability_yes", Decimal), ("requested_weight", Decimal), ("independence_allocated_weight", Decimal), ("effective_weight", Decimal), ("evidence_age_seconds", Decimal), ("capture_lag_seconds", Decimal), ("captured_at_evaluation", bool), ("evidence_revision_available_at_evaluation", bool), ("assessment_revision_available_at_evaluation", bool), ("selected_current_revision", bool), ("canonical_capture", bool), ("disposition", str)),
    TeamEvidenceContradictionResult: (("yes_support_weight", Decimal), ("no_support_weight", Decimal), ("neutral_weight", Decimal), ("contradiction_score", Decimal), ("status", str)),
    TeamEvidenceAggregationResult: (("evaluated_at", datetime), ("config_version", str), ("config_digest", str), ("status", str), ("diagnostic_record_count", int), ("arithmetic_record_count", int), ("requested_weight_total", Decimal), ("independence_allocated_weight_total", Decimal), ("effective_weight_total", Decimal), ("arithmetic_probability_yes", Decimal | None), ("publishable_probability_yes", Decimal | None), ("contradiction", TeamEvidenceContradictionResult), ("requirement_coverage", tuple[TeamEvidenceRequirementCoverage, ...]), ("diagnostics", tuple[TeamEvidenceDiagnosticRow, ...]), ("reason_codes", tuple[str, ...]), ("core_digest", str)),
}


def test_public_dataclass_fields_and_type_hints_are_exact() -> None:
    for cls, required in PUBLIC_FIELD_TYPES.items():
        expected = required + tuple((name, bool) for name in HARD_FLAGS)
        assert tuple(field.name for field in fields(cls)) == tuple(name for name, _ in expected)
        assert get_type_hints(cls) == dict(expected)
        for field in fields(cls):
            if field.name in HARD_FLAGS:
                assert field.default is True
            else:
                assert field.default is MISSING


def test_public_dataclasses_are_frozen_slotted_runtime_final_and_exact_typed() -> None:
    record = lineage_graph()
    selection = aggregation_input().current_revisions[0]
    instances = (
        record.source_lineage, record.capture, record.evidence_revision,
        record.assessment_revision, record, selection, aggregation_input(),
        config().requirements[0], config(), *_derived_values(),
    )
    for instance in instances:
        assert not hasattr(instance, "__dict__")
        with pytest.raises(FrozenInstanceError):
            instance.paper_only = False
        with pytest.raises(TypeError):
            type(f"Bad{type(instance).__name__}", (type(instance),), {})
        for flag in HARD_FLAGS:
            with pytest.raises(ValueError, match=flag):
                replace(instance, **{flag: False})
            with pytest.raises(ValueError, match=flag):
                replace(instance, **{flag: 1})
            bypassed = object.__new__(type(instance))
            for field in fields(instance):
                if field.name != flag:
                    object.__setattr__(bypassed, field.name, getattr(instance, field.name))
            with pytest.raises(ValueError, match=flag):
                bypassed.__post_init__()
    with pytest.raises(ValueError, match="source_lineage"):
        replace(record, source_lineage=object())
    with pytest.raises(ValueError, match="contradiction"):
        replace(_derived_values()[-1], contradiction=object())
    bypassed_requirement = _bypassed(config().requirements[0], minimum_effective_weight=d("0.12"))
    with pytest.raises(ValueError, match="requirements"):
        config(requirements=(bypassed_requirement,))
    offset_capture = _bypassed(record.capture, captured_at=record.capture.captured_at.astimezone(timezone(timedelta(hours=2))))
    with pytest.raises(ValueError, match="capture"):
        replace(record, capture=offset_capture)


def test_identifiers_and_sha256_digests_are_strict_and_canonical() -> None:
    for identifier in ("a", "a.b_c-d:e9", "a" * 160):
        assert TeamEvidenceSourceLineage(identifier, digest("a")).source_lineage_id == identifier
    invalid_ids = ("", "A", " a", "a ", "a/b", "a?b", "https://x", "a\nb", "é", ".a", "a-", "a" * 161)
    for identifier in invalid_ids:
        with pytest.raises(ValueError, match="source_lineage_id"):
            TeamEvidenceSourceLineage(identifier, digest("a"))
    class StringSubclass(str):
        pass
    with pytest.raises(ValueError, match="source_lineage_id"):
        TeamEvidenceSourceLineage(StringSubclass("lineage.alpha"), digest("a"))
    for value in (digest("a"), digest("0")):
        assert TeamEvidenceSourceLineage("lineage.alpha", value).source_lineage_digest == value
    for value in (digest("A"), f"sha256:{digest('a')}", "a" * 63, "a" * 65, "g" * 64):
        with pytest.raises(ValueError, match="source_lineage_digest"):
            TeamEvidenceSourceLineage("lineage.alpha", value)


def test_decimal_inputs_check_exact_type_finiteness_and_raw_bounds_before_quantization() -> None:
    assessment = lineage_graph().assessment_revision
    class DecimalSubclass(Decimal):
        pass
    for value in (1, True, 0.5, DecimalSubclass("0.5"), d("NaN"), d("sNaN"), d("Infinity"), d("-Infinity"), d("-0.0000004"), d("1.0000004")):
        with pytest.raises(ValueError, match="probability_yes"):
            replace(assessment, probability_yes=value)
    assert replace(assessment, probability_yes=d("0.1234565")).probability_yes == d("0.123456")
    assert replace(assessment, probability_yes=d("0.1234575")).probability_yes == d("0.123458")
    zero = replace(assessment, probability_yes=d("-0")).probability_yes
    assert zero == d("0.000000") and zero.is_signed() is False


def test_type_decimal_normalization_ignores_hostile_ambient_context() -> None:
    saved = getcontext().copy()
    try:
        setcontext(Context(prec=2, rounding=ROUND_UP))
        record = lineage_graph(assessment_revision={"probability_yes": d("0.1234565"), "requested_weight": d("0.4000004")})
        values = (record.assessment_revision, config(), *_derived_values())
        decimals = [getattr(value, field.name) for value in values for field in fields(value) if isinstance(getattr(value, field.name), Decimal)]
        assert decimals
        assert all(value.is_finite() and value.as_tuple().exponent == -6 for value in decimals)
        assert record.assessment_revision.probability_yes == d("0.123456")
        assert record.assessment_revision.requested_weight == d("0.400000")
    finally:
        setcontext(saved)


def test_datetime_inputs_require_exact_aware_datetime_and_normalize_to_utc() -> None:
    capture = lineage_graph().capture
    class DatetimeSubclass(datetime):
        pass
    for value in (datetime(2026, 7, 13, 10, 0), DatetimeSubclass(2026, 7, 13, 10, tzinfo=UTC)):
        with pytest.raises(ValueError, match="captured_at"):
            replace(capture, captured_at=value)
    offset = datetime(2026, 7, 13, 12, 0, 0, 123456, tzinfo=timezone(timedelta(hours=2)))
    normalized = replace(capture, captured_at=offset).captured_at
    assert normalized == datetime(2026, 7, 13, 10, 0, 0, 123456, tzinfo=UTC)


def test_collection_fields_require_exact_tuples_sort_semantic_sets_and_reject_duplicates() -> None:
    alpha, beta = lineage_graph(), lineage_graph(prefix="beta")
    revision = replace(alpha.evidence_revision, requirement_ids=("z.req", "a.req"))
    assert revision.requirement_ids == ("a.req", "z.req")
    requirement_b = TeamEvidenceRequirement("z.req", 1, d("0.1"), "watch")
    assert tuple(item.requirement_id for item in config(requirements=(requirement_b, config().requirements[0])).requirements) == ("macro.release", "z.req")
    selected = (
        TeamEvidenceCurrentRevisionSelection(beta.evidence_revision.evidence_revision_id, beta.evidence_revision.evidence_revision_digest, beta.assessment_revision.assessment_revision_id, beta.assessment_revision.assessment_revision_digest),
        aggregation_input().current_revisions[0],
    )
    combined = aggregation_input(records=(beta, alpha), current_revisions=selected)
    assert combined.records == tuple(sorted((alpha, beta), key=expected_record_key))
    assert combined.current_revisions == tuple(sorted(selected, key=lambda item: (item.evidence_revision_id, item.assessment_revision_id)))
    temporal, allocation, witness, coverage, diagnostic, contradiction, result = _derived_values()
    witness_b = replace(witness, source_lineage_id="lineage.beta", capture_id="capture.beta.1", evidence_revision_id="evidence.beta.1", assessment_revision_id="assessment.beta.1", independence_key="desk.beta")
    coverage_b = TeamEvidenceRequirementCoverage("z.req", 1, 1, d("0.1"), "watch", True, (replace(witness_b, requirement_id="z.req"),))
    diagnostic_b = replace(diagnostic, source_lineage_id="lineage.beta", capture_id="capture.beta.1", evidence_revision_id="evidence.beta.1", assessment_revision_id="assessment.beta.1")
    sorted_result = replace(result, requirement_coverage=(coverage_b, coverage), diagnostics=(diagnostic_b, diagnostic), reason_codes=("z.reason", "a.reason"), diagnostic_record_count=2)
    assert tuple(item.requirement_id for item in sorted_result.requirement_coverage) == ("macro.release", "z.req")
    assert sorted_result.diagnostics == tuple(sorted((diagnostic, diagnostic_b), key=lambda item: (item.assessment_revision_id, item.evidence_revision_id, item.captured_at, item.capture_id, item.source_lineage_id)))
    assert sorted_result.reason_codes == ("a.reason", "z.reason")
    for bad in (["a.req"], (item for item in ("a.req",)), {"a.req"}, "a.req", b"a.req"):
        with pytest.raises(ValueError, match="requirement_ids"):
            replace(alpha.evidence_revision, requirement_ids=bad)
        builders = (
            lambda: config(requirements=bad), lambda: aggregation_input(records=bad),
            lambda: aggregation_input(current_revisions=bad), lambda: replace(coverage, witnesses=bad),
            lambda: replace(result, requirement_coverage=bad), lambda: replace(result, diagnostics=bad),
            lambda: replace(result, reason_codes=bad),
        )
        for build in builders:
            with pytest.raises(ValueError, match="exact tuple"):
                build()
    duplicate_cases = (
        lambda: replace(alpha.evidence_revision, requirement_ids=("a.req", "a.req")),
        lambda: config(requirements=(config().requirements[0], config().requirements[0])),
        lambda: aggregation_input(records=(alpha, alpha)),
        lambda: aggregation_input(current_revisions=(selected[1], selected[1])),
        lambda: replace(coverage, assigned_witness_count=2, witnesses=(witness, witness)),
        lambda: replace(result, requirement_coverage=(coverage, coverage)),
        lambda: replace(result, diagnostic_record_count=2, diagnostics=(diagnostic, diagnostic)),
        lambda: replace(result, reason_codes=("a.reason", "a.reason")),
    )
    for build in duplicate_cases:
        with pytest.raises(ValueError, match="duplicate"):
            build()
    assert temporal and allocation and contradiction


def test_config_requires_all_policy_fields_and_has_no_default_policy() -> None:
    signature = inspect.signature(TeamEvidenceAggregationConfig)
    policy_fields = tuple(field.name for field in fields(TeamEvidenceAggregationConfig) if field.name not in HARD_FLAGS)
    assert all(signature.parameters[name].default is inspect.Parameter.empty for name in policy_fields)
    values = {field.name: getattr(config(), field.name) for field in fields(TeamEvidenceAggregationConfig)}
    for name in policy_fields:
        omitted = values.copy()
        omitted.pop(name)
        with pytest.raises(TypeError):
            TeamEvidenceAggregationConfig(**omitted)
    assert "DEFAULT_CONFIG" not in types_module.__all__
    assert not hasattr(types_module, "DEFAULT_CONFIG")


def test_config_validates_relationships_and_nonoverridable_resource_maxima() -> None:
    invalid_changes = (
        {"max_evidence_age_seconds": d("-0.000001")}, {"max_capture_lag_seconds": d("NaN")},
        {"independence_group_weight_cap": d("1.000001")}, {"correlation_group_weight_cap": d("Infinity")},
        {"contradiction_watch_score": d("0.7"), "contradiction_block_score": d("0.6")},
        {"publish_probability_floor": d("0.9"), "publish_probability_ceiling": d("0.8")},
        {"max_requirement_assignments_per_evidence": 33}, {"maximum_records": 129},
        {"maximum_requirements": 33}, {"maximum_requirement_memberships": 1025},
        {"maximum_witness_edges": 257}, {"maximum_requirements": 1, "requirements": (config().requirements[0], TeamEvidenceRequirement("z.req", 1, d("0.1"), "watch"))},
    )
    for changes in invalid_changes:
        with pytest.raises(ValueError):
            config(**changes)
    for name in ("max_requirement_assignments_per_evidence", "maximum_records", "maximum_requirements", "maximum_requirement_memberships", "maximum_witness_edges"):
        for value in (0, True, d("1")):
            with pytest.raises(ValueError, match=name):
                config(**{name: value})
    with pytest.raises(ValueError, match="minimum_effective_weight"):
        TeamEvidenceRequirement("macro.release", 1, d("1.000001"), "blocked")


def test_contradiction_probability_bounds_validate_raw_values_before_canonical_order() -> None:
    for no_max, yes_min in ((d("-0.0000001"), d("0.8")), (d("0.2"), d("1.0000001")), (d("0.2"), d("0.2")), (d("0.8"), d("0.2")), (d("0.2000004"), d("0.2000005"))):
        with pytest.raises(ValueError, match="contradiction"):
            config(contradiction_no_probability_max=no_max, contradiction_yes_probability_min=yes_min)


def test_record_constructor_enforces_all_local_cross_layer_relationships() -> None:
    record = lineage_graph()
    changes = (
        ("capture.source_lineage_id", {"capture": replace(record.capture, source_lineage_id="lineage.other")}),
        ("capture.source_lineage_digest", {"capture": replace(record.capture, source_lineage_digest=digest("9"))}),
        ("evidence_revision.source_lineage_id", {"evidence_revision": replace(record.evidence_revision, source_lineage_id="lineage.other")}),
        ("evidence_revision.source_lineage_digest", {"evidence_revision": replace(record.evidence_revision, source_lineage_digest=digest("9"))}),
        ("capture.content_digest", {"capture": replace(record.capture, content_digest=digest("9"))}),
        ("assessment_revision.evidence_revision_id", {"assessment_revision": replace(record.assessment_revision, evidence_revision_id="evidence.other.1")}),
        ("assessment_revision.evidence_revision_digest", {"assessment_revision": replace(record.assessment_revision, evidence_revision_digest=digest("9"))}),
    )
    for path, change in changes:
        with pytest.raises(ValueError, match=path.replace(".", r"\.")):
            replace(record, **change)
    with pytest.raises(ValueError, match="capture"):
        replace(record, capture=object())
    bypassed = object.__new__(TeamEvidenceCapture)
    for field in fields(record.capture):
        object.__setattr__(bypassed, field.name, False if field.name == "readonly" else getattr(record.capture, field.name))
    with pytest.raises(ValueError, match="capture.readonly"):
        replace(record, capture=bypassed)


def test_derived_types_enforce_exact_scalars_statuses_weights_and_sorted_children() -> None:
    temporal, allocation, witness, coverage, diagnostic, contradiction, result = _derived_values()
    signed = replace(temporal, evidence_age_seconds=d("-0.0000004"), capture_lag_seconds=d("-2"))
    assert signed.evidence_age_seconds == d("0.000000") and signed.capture_lag_seconds == d("-2.000000")
    assert contradiction.yes_support_weight == d("1.200000") and result.requested_weight_total == d("1.200000")
    assert replace(result, arithmetic_probability_yes=None, publishable_probability_yes=None)
    for disposition in (
        "not_current_revision", "duplicate_capture", "freshness_anchor_after_evaluation",
        "capture_after_evaluation", "evidence_revision_after_evaluation",
        "assessment_revision_after_evaluation", "stale", "capture_before_freshness_anchor",
        "capture_lag_exceeded", "zero_requested_weight", "independence_cap_exhausted",
        "correlation_cap_exhausted", "included",
    ):
        assert replace(diagnostic, disposition=disposition).disposition == disposition
    for status in ("none", "watch", "blocked"):
        assert replace(contradiction, status=status).status == status
    for status in ("ready", "watch", "blocked"):
        assert replace(result, status=status).status == status
    invalid = (
        lambda: replace(temporal, fresh=1), lambda: replace(allocation, effective_weight=d("0.31")),
        lambda: replace(allocation, independence_allocated_weight=d("0.41")),
        lambda: replace(witness, effective_weight=d("1.000001")),
        lambda: replace(coverage, assigned_witness_count=0),
        lambda: replace(coverage, witnesses=(replace(witness, requirement_id="other.req"),)),
        lambda: replace(coverage, minimum_effective_weight=d("0.21")),
        lambda: replace(diagnostic, probability_yes=d("1.000001")),
        lambda: replace(diagnostic, disposition="other"), lambda: replace(contradiction, status="other"),
        lambda: replace(result, status="other"), lambda: replace(result, arithmetic_probability_yes=1),
        lambda: replace(result, diagnostic_record_count=True), lambda: replace(result, core_digest="bad"),
    )
    for build in invalid:
        with pytest.raises(ValueError):
            build()

EXPECTED_IMPORTS = {
    "team_evidence_aggregation_types.py": {"__future__", "collections", "dataclasses", "datetime", "decimal", "re", "typing"},
    "team_evidence_aggregation_codec.py": {"__future__", "dataclasses", "datetime", "decimal", "hashlib", "json", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_temporal.py": {"__future__", "datetime", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
}
EXPECTED_ALL = {
    "team_evidence_aggregation_types.py": ("TeamEvidenceSourceLineage", "TeamEvidenceCapture", "TeamEvidenceRevision", "TeamEvidenceAssessmentRevision", "TeamEvidenceAggregationRecord", "TeamEvidenceCurrentRevisionSelection", "TeamEvidenceAggregationInput", "TeamEvidenceRequirement", "TeamEvidenceAggregationConfig", "TeamEvidenceTemporalAssessment", "TeamEvidenceWeightAllocation", "TeamEvidenceRequirementWitness", "TeamEvidenceRequirementCoverage", "TeamEvidenceDiagnosticRow", "TeamEvidenceContradictionResult", "TeamEvidenceAggregationResult", "validate_team_evidence_aggregation_input_contract", "select_team_evidence_canonical_current_records", "select_team_evidence_canonical_capture_records"),
    "team_evidence_aggregation_codec.py": ("team_evidence_aggregation_config_payload", "team_evidence_aggregation_input_payload", "team_evidence_aggregation_config_digest", "team_evidence_aggregation_core_payload", "team_evidence_aggregation_payload", "team_evidence_aggregation_core_digest", "validate_team_evidence_aggregation_core_digest"),
    "team_evidence_aggregation_temporal.py": ("assess_team_evidence_temporal",),
}
HARD_MAXIMA = {"max_requirement_assignments_per_evidence": ("_MAX_ASSIGNMENTS_PER_EVIDENCE", 32), "maximum_records": ("_MAX_RECORDS", 128), "maximum_requirements": ("_MAX_REQUIREMENTS", 32), "maximum_requirement_memberships": ("_MAX_REQUIREMENT_MEMBERSHIPS", 1024), "maximum_witness_edges": ("_MAX_WITNESS_EDGES", 256)}
APPROVED_SCHEMAS = {"pal.team_evidence_aggregation.config.v1", "pal.team_evidence_aggregation.input.v1", "pal.team_evidence_aggregation.core.v1", "pal.team_evidence_aggregation.result.v1"}
FORBIDDEN_WORDS = frozenset("account accounts argparse auth authenticate authenticated authentication authorization bitcoin browser browsers btc builtins cache cached caches caching callback callable capital cli client clients credential credentials csv database databases db decode decoder deserialize directory dsn env environment environments exchange exchanges execute execution external file files filesystem float hook http https io jsonl legacy log logger logging migration migrations network networks order orders packet persist persistence postgres postgresql process processes random randomness receipt request requests scrape scraper scraping service services sign signing sizing socket sockets sql storage store stores subprocess supabase tea temp tempfile temporary tfe tfr tmp token tokens trade trades trading wallet wallets".split())
FORBIDDEN_CALLS = frozenset("__import__ __repr__ breakpoint choice choices commit connect eval exec execute executemany float fork getenv getrandbits import_module input load loads monotonic now open perf_counter popen print random randint randrange read_bytes read_text repr rollback shuffle spawn system timestamp today total_seconds uniform urandom utcnow write_bytes write_text".split())
FORBIDDEN_PHRASES = {("api", "key"), ("capital", "allocation"), ("db", "row"), ("default", "config"), ("evidence", "aggregation", "id"), ("exchange", "mutation"), ("forecast", "evidence", "id"), ("forecast", "id"), ("forecast", "result", "id"), ("key", "material"), ("legacy", "projection"), ("private", "key"), ("run", "id"), ("secret", "key")}
UNSAFE_MODULE_TOKEN = re.compile(r"(?<![A-Za-z0-9_])(?:aiohttp|argparse|click|csv|httpx|importlib|logging|os|pathlib|psycopg|random|requests|secrets|shutil|socket|sqlite3|sqlalchemy|subprocess|supabase|sys|tempfile|typer|urllib)\s*\.", re.IGNORECASE)
ROOT = Path(__file__).resolve().parents[1]
def _node_2a_source(name: str) -> str: return (ROOT / "src" / "polymarket_alpha_lab" / name).read_text(encoding="utf-8")
def _node_2a_tree(name: str) -> ast.Module: return ast.parse(_node_2a_source(name), filename=name)
def _node_2a_dotted(node: ast.AST) -> str:
    return node.id if isinstance(node, ast.Name) else f"{_node_2a_dotted(node.value)}.{node.attr}".lstrip(".") if isinstance(node, ast.Attribute) else ""
def _node_2a_words(value: str) -> tuple[str, ...]: return tuple(part.lower() for part in re.findall(r"[A-Z]+(?=[A-Z][a-z]|[^A-Za-z]|$)|[A-Z]?[a-z]+|[0-9]+", value))
def _node_2a_forbidden_identifier(value: str) -> bool:
    words = _node_2a_words(value)
    return bool(set(words) & FORBIDDEN_WORDS or any(words[index:index + len(phrase)] == phrase for phrase in FORBIDDEN_PHRASES for index in range(len(words) - len(phrase) + 1)))
def _node_2a_safe_error_value(node: ast.AST) -> bool:
    dotted = _node_2a_dotted(node)
    return bool((words := _node_2a_words(dotted)) and (words[-1] in {"digest", "flag", "id", "index", "kind", "maximum", "name", "path", "suffix"} or dotted.endswith(".__name__")))
def test_node_2a_production_imports_equal_exact_allowlists() -> None:
    for name, expected in EXPECTED_IMPORTS.items():
        actual: list[str] = []
        for node in ast.walk(_node_2a_tree(name)):
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith(".") for alias in node.names)
                actual.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0 and isinstance(node.module, str) and node.module
                actual.append(node.module)
        assert len(actual) == len(set(actual)) and set(actual) == expected
def test_node_2a_literal_all_tuples_equal_exact_public_surfaces() -> None:
    for name, expected in EXPECTED_ALL.items():
        tree = _node_2a_tree(name)
        assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)]
        assert len(assignments) == 1
        assignment = assignments[0]
        assert len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Name)
        assert isinstance(assignment.value, ast.Tuple) and all(isinstance(item, ast.Constant) and type(item.value) is str for item in assignment.value.elts)
        actual = tuple(item.value for item in assignment.value.elts)
        assert actual == expected and len(actual) == len(set(actual))
        assert sum(isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == "__all__" for node in ast.walk(tree)) == 1
def test_node_2a_ast_rejects_forbidden_references_calls_and_float_surfaces() -> None:
    assert all(_node_2a_forbidden_identifier(value) for value in ("run_id", "forecast_id", "evidence_aggregation_id", "team_evidence_aggregation_id", "team_forecast_result_id", "team_forecast_evidence_id"))
    for name in EXPECTED_IMPORTS:
        source = _node_2a_source(name); tree = _node_2a_tree(name)
        assert UNSAFE_MODULE_TOKEN.search(source) is None
        for node in ast.walk(tree):
            assert not isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Lambda, ast.Yield, ast.YieldFrom))
            assert not (isinstance(node, ast.Constant) and type(node.value) is float)
            if isinstance(node, (ast.Name, ast.Attribute, ast.arg, ast.FunctionDef, ast.ClassDef)):
                identifier = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else node.arg if isinstance(node, ast.arg) else node.name
                assert identifier not in {"Path", "PurePath"} and not _node_2a_forbidden_identifier(identifier)
            if isinstance(node, ast.alias):
                assert not _node_2a_forbidden_identifier(node.name) and (node.asname is None or not _node_2a_forbidden_identifier(node.asname))
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value not in {"0.020000", "0.980000", "evidence_id", "forecast_id", "run_id", "tea:v1", "team_evidence_aggregation_id", "team_forecast_evidence_id", "team_forecast_result_id", "tfr:v1", "tfe:v1"}
                assert not _node_2a_forbidden_identifier(node.value)
            if isinstance(node, ast.FormattedValue):
                assert node.conversion not in {ord("a"), ord("r")}
            if isinstance(node, ast.Call):
                target = _node_2a_dotted(node.func)
                assert target and target.rsplit(".", 1)[-1] not in FORBIDDEN_CALLS and (target.rsplit(".", 1)[-1] != "compile" or target == "re.compile") and not (isinstance(node.func, ast.Name) and node.func.id == "hash")
                if target.rsplit(".", 1)[-1].endswith(("Error", "Exception")):
                    assert all(isinstance(argument, ast.Constant) and type(argument.value) is str or isinstance(argument, ast.JoinedStr) and all(not isinstance(part, ast.FormattedValue) or _node_2a_safe_error_value(part.value) for part in argument.values) for argument in node.args)
            if isinstance(node, ast.ExceptHandler):
                assert node.type is not None and not any(_node_2a_dotted(item).rsplit(".", 1)[-1] in {"BaseException", "Exception"} for item in ast.walk(node.type) if isinstance(item, (ast.Name, ast.Attribute)))
        for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            arguments = (*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs, *((function.args.vararg,) if function.args.vararg else ()), *((function.args.kwarg,) if function.args.kwarg else ()))
            assert all(not ({"callback", "callable", "handler", "hook"} & set(_node_2a_words(argument.arg + " " + (ast.unparse(argument.annotation) if argument.annotation else "")))) for argument in arguments)
            called = {call.func.id for call in ast.walk(function) if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)}
            assert all(argument.arg not in called or function.name == "_canonical_instance" and argument.arg == "expected" and argument.annotation is not None and ast.unparse(argument.annotation) == "type[object]" for argument in arguments)
def test_node_2a_ast_locks_dataclass_flags_policy_defaults_and_resource_maxima() -> None:
    tree = _node_2a_tree("team_evidence_aggregation_types.py")
    public_classes = EXPECTED_ALL["team_evidence_aggregation_types.py"][:16]
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    assert set(public_classes) == {name for name in classes if name.startswith("TeamEvidence")}
    for class_name in public_classes:
        node = classes[class_name]
        assert len(node.bases) == 1 and _node_2a_dotted(node.bases[0]) == "_ExactPublicDataclass"
        assert len(node.decorator_list) == 2 and _node_2a_dotted(node.decorator_list[0]) == "final"
        decorator = node.decorator_list[1]
        assert isinstance(decorator, ast.Call) and _node_2a_dotted(decorator.func) == "dataclass" and not decorator.args
        assert {keyword.arg: ast.literal_eval(keyword.value) for keyword in decorator.keywords} == {"frozen": True, "slots": True}
        declared = {item.target.id: item for item in node.body if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)}
        expected_fields = tuple(field for field, _ in PUBLIC_FIELD_TYPES[getattr(types_module, class_name)]) + HARD_FLAGS
        assert tuple(declared) == expected_fields
        assert all(item.value is None for field, item in declared.items() if field not in HARD_FLAGS)
        assert all(_node_2a_dotted(declared[field].annotation) == "bool" and isinstance(declared[field].value, ast.Constant) and declared[field].value.value is True for field in HARD_FLAGS)
        post_init = next(item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__post_init__")
        calls = [item for item in ast.walk(post_init) if isinstance(item, ast.Call)]
        assert any(_node_2a_dotted(call.func) == "_exact_self" and len(call.args) >= 2 and _node_2a_dotted(call.args[0]) == "self" and _node_2a_dotted(call.args[1]) == class_name for call in calls)
        assert any(_node_2a_dotted(call.func) == "_hard_flags" and any(_node_2a_dotted(argument) == "self" for argument in call.args) for call in calls)
    base = classes["_ExactPublicDataclass"]
    guard = next(item for item in base.body if isinstance(item, ast.FunctionDef) and item.name == "__init_subclass__")
    assert any(isinstance(item, ast.Raise) and isinstance(item.exc, ast.Call) and _node_2a_dotted(item.exc.func) == "TypeError" for item in ast.walk(guard)) and any(isinstance(item, ast.Name) and item.id == "_PUBLIC_CLASS_NAMES" for item in ast.walk(guard)) and any(isinstance(item, ast.Attribute) and item.attr == "__bases__" for item in ast.walk(guard))
    assert tuple(item.value for item in next(node for node in tree.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_PUBLIC_CLASS_NAMES").value.elts) == public_classes
    constants = {node.target.id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.startswith("_MAX_")}
    assert constants == {constant: value for constant, value in HARD_MAXIMA.values()} and {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id.startswith("_MAX_")} == set(constants)
    config_post = next(item for item in classes["TeamEvidenceAggregationConfig"].body if isinstance(item, ast.FunctionDef) and item.name == "__post_init__")
    bounded_pairs = {(item.elts[0].value, item.elts[1].id) for item in ast.walk(config_post) if isinstance(item, ast.Tuple) and len(item.elts) == 2 and isinstance(item.elts[0], ast.Constant) and item.elts[0].value in HARD_MAXIMA and isinstance(item.elts[1], ast.Name)}
    assert bounded_pairs == {(field, constant) for field, (constant, _) in HARD_MAXIMA.items()}
    assert any(isinstance(item, ast.Call) and _node_2a_dotted(item.func) == "_positive_int" and any(keyword.arg == "maximum" and _node_2a_dotted(keyword.value) == "maximum" for keyword in item.keywords) for item in ast.walk(config_post))
    positive_int = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_positive_int")
    assert any(isinstance(item, ast.Compare) and _node_2a_dotted(item.left) == "value" and any(isinstance(operator, ast.Gt) for operator in item.ops) and any(_node_2a_dotted(value) == "maximum" for value in item.comparators) for item in ast.walk(positive_int)) and any(isinstance(item, ast.Raise) for item in ast.walk(positive_int))
    assert next(node for node in tree.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_HARD_FLAGS").value.elts and tuple(item.value for item in next(node for node in tree.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_HARD_FLAGS").value.elts) == HARD_FLAGS
    exact_self = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_exact_self"); hard_guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_hard_flags"); assert any(isinstance(item, ast.Compare) and isinstance(item.left, ast.Call) and _node_2a_dotted(item.left.func) == "type" and any(isinstance(operator, ast.IsNot) for operator in item.ops) and any(_node_2a_dotted(value) == "expected" for value in item.comparators) for item in ast.walk(exact_self)) and any(isinstance(item, ast.Raise) for item in ast.walk(exact_self)) and any(isinstance(item, ast.Compare) and _node_2a_dotted(item.left) == "flag" and any(isinstance(operator, ast.IsNot) for operator in item.ops) and any(isinstance(value, ast.Constant) and value.value is True for value in item.comparators) for item in ast.walk(hard_guard)) and any(isinstance(item, ast.Raise) for item in ast.walk(hard_guard))
    for module_name in EXPECTED_IMPORTS:
        schemas = {node.value for node in ast.walk(_node_2a_tree(module_name)) if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("pal.team_evidence_aggregation.")}
        assert schemas == (APPROVED_SCHEMAS if module_name == "team_evidence_aggregation_codec.py" else set())
def test_node_2a_physical_line_ceilings_are_enforced() -> None:
    production_limits = {"team_evidence_aggregation_types.py": 900, "team_evidence_aggregation_codec.py": 500, "team_evidence_aggregation_temporal.py": 300}
    test_limits = {"test_team_evidence_aggregation_types.py": 900, "test_team_evidence_aggregation_codec.py": 600, "test_team_evidence_aggregation_temporal.py": 450}
    production_counts = {name: len((ROOT / "src" / "polymarket_alpha_lab" / name).read_text(encoding="utf-8").splitlines()) for name in production_limits}
    test_counts = {name: len((ROOT / "tests" / name).read_text(encoding="utf-8").splitlines()) for name in test_limits}
    assert all(production_counts[name] <= limit for name, limit in production_limits.items())
    assert all(test_counts[name] <= limit for name, limit in test_limits.items())
    assert sum(production_counts.values()) <= 1700 and sum(test_counts.values()) <= 1950
def _selection(record: TeamEvidenceAggregationRecord) -> TeamEvidenceCurrentRevisionSelection:
    return TeamEvidenceCurrentRevisionSelection(
        record.evidence_revision.evidence_revision_id, record.evidence_revision.evidence_revision_digest,
        record.assessment_revision.assessment_revision_id, record.assessment_revision.assessment_revision_digest,
    )


def _record_variant(record: TeamEvidenceAggregationRecord, *, capture: dict[str, object] | None = None, evidence: dict[str, object] | None = None, assessment: dict[str, object] | None = None) -> TeamEvidenceAggregationRecord:
    revision = replace(record.evidence_revision, **(evidence or {}))
    capture_values = {"content_digest": revision.content_digest, "source_lineage_id": revision.source_lineage_id, "source_lineage_digest": revision.source_lineage_digest}
    capture_values.update(capture or {})
    captured = replace(record.capture, **capture_values)
    assessment_values = {"evidence_revision_id": revision.evidence_revision_id, "evidence_revision_digest": revision.evidence_revision_digest}
    assessment_values.update(assessment or {})
    assessed = replace(record.assessment_revision, **assessment_values)
    return TeamEvidenceAggregationRecord(record.source_lineage, captured, revision, assessed)


def _successor(record: TeamEvidenceAggregationRecord, index: int = 2, **changes: dict[str, object]) -> TeamEvidenceAggregationRecord:
    character = {2: "9", 3: "0", 4: "b"}.get(index, "c")
    evidence = {"evidence_revision_id": f"evidence.alpha.{index}", "evidence_revision_digest": digest(character), "previous_evidence_revision_id": record.evidence_revision.evidence_revision_id, "previous_evidence_revision_digest": record.evidence_revision.evidence_revision_digest, "content_digest": digest(character), "recorded_at": RECORDED + timedelta(minutes=index - 1)}
    assessment = {"assessment_revision_id": f"assessment.alpha.{index}", "assessment_revision_digest": digest("d" if index == 2 else character), "previous_assessment_revision_id": record.assessment_revision.assessment_revision_id, "previous_assessment_revision_digest": record.assessment_revision.assessment_revision_digest, "assessed_at": ASSESSED + timedelta(minutes=index - 1)}
    capture = {"capture_id": f"capture.alpha.{index}", "capture_digest": digest("e" if index == 2 else character), "captured_at": CAPTURED + timedelta(minutes=index - 1)}
    evidence.update(changes.get("evidence", {})); assessment.update(changes.get("assessment", {})); capture.update(changes.get("capture", {}))
    return _record_variant(record, capture=capture, evidence=evidence, assessment=assessment)


def _assessment_successor(record: TeamEvidenceAggregationRecord, index: int = 2, **changes: object) -> TeamEvidenceAggregationRecord:
    values = {"assessment_revision_id": f"assessment.alpha.{index}", "assessment_revision_digest": digest("9" if index == 2 else "0"), "previous_assessment_revision_id": record.assessment_revision.assessment_revision_id, "previous_assessment_revision_digest": record.assessment_revision.assessment_revision_digest, "assessed_at": ASSESSED + timedelta(minutes=index - 1), "probability_yes": d("0.650000")}
    values.update(changes)
    return _record_variant(record, assessment=values)


def _recapture(record: TeamEvidenceAggregationRecord, index: int = 2) -> TeamEvidenceAggregationRecord:
    return _record_variant(record, capture={"capture_id": f"capture.re.{index}", "capture_digest": digest(format(index % 16, "x")), "captured_at": CAPTURED + timedelta(minutes=index)})


def _bypassed(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def _validate(value: TeamEvidenceAggregationInput, policy: TeamEvidenceAggregationConfig | None = None) -> None:
    return types_module.validate_team_evidence_aggregation_input_contract(value, config=policy or config())


def _current(value: TeamEvidenceAggregationInput, policy: TeamEvidenceAggregationConfig | None = None) -> tuple[TeamEvidenceAggregationRecord, ...]:
    return types_module.select_team_evidence_canonical_current_records(value, config=policy or config())


def _captures(value: TeamEvidenceAggregationInput, policy: TeamEvidenceAggregationConfig | None = None) -> tuple[TeamEvidenceAggregationRecord, ...]:
    return types_module.select_team_evidence_canonical_capture_records(value, config=policy or config())


def test_validate_input_contract_returns_exact_none_for_valid_closed_graph() -> None:
    alpha, beta = lineage_graph(), lineage_graph(prefix="beta")
    assert _validate(aggregation_input()) is None
    assert _validate(aggregation_input(records=(beta, alpha), current_revisions=(_selection(beta), _selection(alpha)))) is None


def test_validate_input_contract_accepts_empty_records_and_empty_selections() -> None:
    assert _validate(aggregation_input(records=(), current_revisions=())) is None


def test_validate_input_contract_enforces_record_requirement_and_distinct_revision_membership_limits() -> None:
    base = lineage_graph()
    recaptures = tuple(_recapture(base, index) for index in range(1, 130))
    requirements = tuple(TeamEvidenceRequirement(f"req.{index}", 1, d("0.1"), "watch") for index in range(33))
    ids32 = tuple(f"req.{index}" for index in range(32))
    roots = tuple(_record_variant(base, capture={"capture_id": f"capture.limit.{index}", "capture_digest": f"{index + 1:064x}"}, evidence={"evidence_revision_id": f"evidence.limit.{index}", "evidence_revision_digest": f"{index + 101:064x}", "requirement_ids": ids32}, assessment={"assessment_revision_id": f"assessment.limit.{index}", "assessment_revision_digest": f"{index + 201:064x}"}) for index in range(33))
    cases = (
        (aggregation_input(records=recaptures[:3], current_revisions=()), config(maximum_records=2)),
        (aggregation_input(records=recaptures, current_revisions=()), config(maximum_records=128)),
        (aggregation_input(records=(), current_revisions=()), _bypassed(config(maximum_requirements=1), requirements=requirements[:2])),
        (aggregation_input(records=(), current_revisions=()), _bypassed(config(maximum_requirements=32), requirements=requirements)),
        (aggregation_input(record=_record_variant(base, evidence={"requirement_ids": ("a.1", "a.2", "a.3", "a.4")})), config(max_requirement_assignments_per_evidence=3)),
        (aggregation_input(record=_record_variant(base, evidence={"requirement_ids": ids32 + ("req.32",)})), config(max_requirement_assignments_per_evidence=32)),
        (aggregation_input(records=roots[:2], current_revisions=()), config(max_requirement_assignments_per_evidence=32, maximum_requirement_memberships=63)),
        (aggregation_input(records=roots, current_revisions=()), config(maximum_records=128, max_requirement_assignments_per_evidence=32, maximum_requirement_memberships=1024)),
    )
    for value, policy in cases:
        with pytest.raises(ValueError, match="maximum|requirement|records"):
            _validate(value, policy)


def test_validate_input_contract_rejects_functional_dependency_conflicts() -> None:
    alpha, beta = lineage_graph(), lineage_graph(prefix="beta")
    source = lineage_graph(prefix="beta", source_lineage={"source_lineage_id": alpha.source_lineage.source_lineage_id}, capture={"source_lineage_id": alpha.source_lineage.source_lineage_id}, evidence_revision={"source_lineage_id": alpha.source_lineage.source_lineage_id})
    variants = (
        ("source_lineage", source), ("capture", _record_variant(beta, capture={"capture_id": alpha.capture.capture_id})),
        ("evidence_revision", _record_variant(beta, evidence={"evidence_revision_id": alpha.evidence_revision.evidence_revision_id})),
        ("assessment_revision", _record_variant(beta, assessment={"assessment_revision_id": alpha.assessment_revision.assessment_revision_id})),
    )
    for path, variant in variants:
        with pytest.raises(ValueError, match=path):
            _validate(aggregation_input(records=(alpha, variant), current_revisions=()))


def test_validate_input_contract_rejects_duplicate_capture_assessment_pairs() -> None:
    base = lineage_graph()
    duplicate_pair = _record_variant(
        base,
        capture={"capture_digest": digest("1"), "captured_at": CAPTURED + timedelta(seconds=1)},
    )
    with pytest.raises(ValueError, match="duplicate capture_id and assessment_revision_id pair"):
        _validate(aggregation_input(records=(base, duplicate_pair), current_revisions=()))


def test_validate_input_contract_rejects_same_layer_digest_aliases() -> None:
    alpha, beta = lineage_graph(), lineage_graph(prefix="beta")
    variants = (
        lineage_graph(prefix="beta", source_lineage={"source_lineage_digest": alpha.source_lineage.source_lineage_digest}, capture={"source_lineage_digest": alpha.source_lineage.source_lineage_digest}, evidence_revision={"source_lineage_digest": alpha.source_lineage.source_lineage_digest}),
        _record_variant(beta, capture={"capture_digest": alpha.capture.capture_digest}),
        _record_variant(beta, evidence={"evidence_revision_digest": alpha.evidence_revision.evidence_revision_digest}),
        _record_variant(beta, assessment={"assessment_revision_digest": alpha.assessment_revision.assessment_revision_digest}),
    )
    for variant in variants:
        with pytest.raises(ValueError, match="digest"):
            _validate(aggregation_input(records=(alpha, variant), current_revisions=()))
    shared = _record_variant(beta, capture={"content_digest": alpha.capture.content_digest}, evidence={"content_digest": alpha.capture.content_digest})
    assert _validate(aggregation_input(records=(alpha, shared), current_revisions=())) is None


def test_validate_input_contract_rejects_invalid_evidence_revision_graphs() -> None:
    base, successor = lineage_graph(), _successor(lineage_graph())
    fork = _successor(base, 3)
    cycle_root = _record_variant(base, evidence={"previous_evidence_revision_id": successor.evidence_revision.evidence_revision_id, "previous_evidence_revision_digest": successor.evidence_revision.evidence_revision_digest})
    cross = lineage_graph(prefix="beta", evidence_revision={"previous_evidence_revision_id": base.evidence_revision.evidence_revision_id, "previous_evidence_revision_digest": base.evidence_revision.evidence_revision_digest})
    merge = _record_variant(successor, capture={"capture_id": "capture.merge.1", "capture_digest": digest("2")}, evidence={"previous_evidence_revision_id": None, "previous_evidence_revision_digest": None}, assessment={"assessment_revision_id": "assessment.merge.1", "assessment_revision_digest": digest("1")})
    cases = ((successor,), (base, _record_variant(successor, evidence={"previous_evidence_revision_digest": digest("1")})), (base, _record_variant(successor, evidence={"previous_evidence_revision_id": None, "previous_evidence_revision_digest": None})), (base, successor, fork), (base, successor, merge), (base, successor, _record_variant(fork, evidence={"previous_evidence_revision_id": None, "previous_evidence_revision_digest": None})), (cycle_root, successor), (base, cross))
    for records in cases:
        with pytest.raises(ValueError, match="evidence"):
            _validate(aggregation_input(records=records, current_revisions=()))


def test_validate_input_contract_rejects_invalid_assessment_revision_graphs() -> None:
    base, successor = lineage_graph(), _assessment_successor(lineage_graph())
    fork = _assessment_successor(base, 3)
    cycle_root = _record_variant(base, assessment={"previous_assessment_revision_id": successor.assessment_revision.assessment_revision_id, "previous_assessment_revision_digest": successor.assessment_revision.assessment_revision_digest})
    cross = lineage_graph(prefix="beta", assessment_revision={"previous_assessment_revision_id": base.assessment_revision.assessment_revision_id, "previous_assessment_revision_digest": base.assessment_revision.assessment_revision_digest})
    merge = _record_variant(successor, capture={"capture_id": "capture.merge.2", "capture_digest": digest("1")}, assessment={"previous_assessment_revision_id": None, "previous_assessment_revision_digest": None, "probability_yes": d("0.66")})
    cases = ((successor,), (base, _record_variant(successor, assessment={"previous_assessment_revision_digest": digest("1")})), (base, _record_variant(successor, assessment={"previous_assessment_revision_id": None, "previous_assessment_revision_digest": None})), (base, successor, fork), (base, successor, merge), (base, successor, _record_variant(fork, assessment={"previous_assessment_revision_id": None, "previous_assessment_revision_digest": None})), (cycle_root, successor), (base, cross))
    for records in cases:
        with pytest.raises(ValueError, match="assessment"):
            _validate(aggregation_input(records=records, current_revisions=()))


def test_validate_input_contract_rejects_evidence_noops_and_invalid_anchor_changes() -> None:
    base = lineage_graph(); successor = _successor(base)
    rejected = (
        {"content_digest": base.evidence_revision.content_digest, "requirement_ids": base.evidence_revision.requirement_ids, "freshness_anchor_at": base.evidence_revision.freshness_anchor_at},
        {"content_digest": base.evidence_revision.content_digest, "requirement_ids": base.evidence_revision.requirement_ids, "freshness_anchor_at": base.evidence_revision.freshness_anchor_at, "recorded_at": RECORDED + timedelta(minutes=2)},
        {"content_digest": base.evidence_revision.content_digest, "freshness_anchor_at": ANCHOR + timedelta(minutes=1)},
        {"content_digest": base.evidence_revision.content_digest, "requirement_ids": ("other.req",), "freshness_anchor_at": ANCHOR + timedelta(minutes=1)},
    )
    for changes in rejected:
        with pytest.raises(ValueError, match="evidence_revision"):
            _validate(aggregation_input(records=(base, _record_variant(successor, evidence=changes)), current_revisions=()))
    accepted = ({"content_digest": digest("1")}, {"content_digest": base.evidence_revision.content_digest, "requirement_ids": ("other.req",)}, {"content_digest": digest("1"), "freshness_anchor_at": ANCHOR + timedelta(minutes=1)})
    for changes in accepted:
        assert _validate(aggregation_input(records=(base, _record_variant(successor, evidence=changes)), current_revisions=())) is None


def test_validate_input_contract_rejects_assessment_noops() -> None:
    base = lineage_graph(); successor = _assessment_successor(base)
    no_op = _record_variant(successor, assessment={"probability_yes": base.assessment_revision.probability_yes, "requested_weight": base.assessment_revision.requested_weight, "rationale_digest": base.assessment_revision.rationale_digest, "independence_key": base.assessment_revision.independence_key, "correlation_key": base.assessment_revision.correlation_key})
    with pytest.raises(ValueError, match="assessment_revision"):
        _validate(aggregation_input(records=(base, no_op), current_revisions=()))
    for changes in ({"probability_yes": d("0.66")}, {"requested_weight": d("0.41")}, {"rationale_digest": digest("1")}, {"independence_key": "desk.other"}, {"correlation_key": "macro.other"}):
        assert _validate(aggregation_input(records=(base, _record_variant(no_op, assessment=changes)), current_revisions=())) is None
    assert _validate(aggregation_input(records=(base, _successor(base)), current_revisions=())) is None


def test_recapture_may_change_only_capture_identity_and_time() -> None:
    base, recapture = lineage_graph(), _recapture(lineage_graph())
    assert _validate(aggregation_input(records=(recapture, base), current_revisions=(_selection(base),))) is None
    changes = (("evidence", {"requirement_ids": ("other.req",)}), ("evidence", {"freshness_anchor_at": ANCHOR + timedelta(minutes=1)}), ("evidence", {"recorded_at": RECORDED + timedelta(minutes=1)}), ("assessment", {"probability_yes": d("0.65")}), ("assessment", {"requested_weight": d("0.41")}), ("assessment", {"rationale_digest": digest("1")}), ("assessment", {"independence_key": "desk.other"}), ("assessment", {"correlation_key": "macro.other"}), ("assessment", {"assessed_at": ASSESSED + timedelta(minutes=1)}))
    for layer, change in changes:
        with pytest.raises(ValueError, match=f"{layer}_revision"):
            _validate(aggregation_input(records=(base, _record_variant(recapture, **{layer: change})), current_revisions=()))


def test_validate_input_contract_enforces_nondecreasing_edge_times_and_accepts_equal_times() -> None:
    base = lineage_graph()
    with pytest.raises(ValueError, match="recorded_at"):
        _validate(aggregation_input(records=(base, _successor(base, evidence={"recorded_at": RECORDED - timedelta(seconds=1)})), current_revisions=()))
    with pytest.raises(ValueError, match="assessed_at"):
        _validate(aggregation_input(records=(base, _assessment_successor(base, assessed_at=ASSESSED - timedelta(seconds=1))), current_revisions=()))
    assert _validate(aggregation_input(records=(base, _successor(base, evidence={"recorded_at": RECORDED}, assessment={"assessed_at": ASSESSED})), current_revisions=())) is None


def test_validate_input_contract_enforces_local_availability_order() -> None:
    base = lineage_graph()
    for bad in (_record_variant(base, capture={"captured_at": RECORDED + timedelta(seconds=1)}), _record_variant(base, evidence={"recorded_at": ASSESSED + timedelta(seconds=1)})):
        with pytest.raises(ValueError, match="captured_at|recorded_at|assessed_at"):
            _validate(aggregation_input(record=bad))
    assert _validate(aggregation_input(records=(base, _record_variant(_recapture(base), capture={"captured_at": ASSESSED + timedelta(hours=1)})), current_revisions=(_selection(base),))) is None


def test_validate_input_contract_rejects_unresolved_or_mismatched_current_selection() -> None:
    base, successor = lineage_graph(), _successor(lineage_graph())
    missing = TeamEvidenceCurrentRevisionSelection("evidence.missing", digest("1"), "assessment.missing", digest("2"))
    mismatches = (missing, replace(_selection(base), evidence_revision_digest=digest("1")), replace(_selection(base), assessment_revision_digest=digest("1")), TeamEvidenceCurrentRevisionSelection(base.evidence_revision.evidence_revision_id, base.evidence_revision.evidence_revision_digest, successor.assessment_revision.assessment_revision_id, successor.assessment_revision.assessment_revision_digest))
    for selected in mismatches:
        with pytest.raises(ValueError, match="current_revisions"):
            _validate(aggregation_input(records=(base, successor), current_revisions=(selected,)))
    later_only = _record_variant(_assessment_successor(base), capture={"capture_id": "capture.later.1", "capture_digest": digest("1"), "captured_at": CAPTURED + timedelta(minutes=3)})
    with pytest.raises(ValueError, match="canonical capture"):
        _validate(aggregation_input(records=(base, later_only), current_revisions=(_selection(later_only),)))


def test_validate_input_contract_rejects_two_current_pairs_in_one_lineage() -> None:
    base, assessment = lineage_graph(), _assessment_successor(lineage_graph())
    with pytest.raises(ValueError, match="one current pair"):
        _validate(aggregation_input(records=(base, assessment), current_revisions=(_selection(base), _selection(assessment))))
    successor = _successor(base)
    with pytest.raises(ValueError, match="one current pair"):
        _validate(aggregation_input(records=(base, successor), current_revisions=(_selection(base), _selection(successor))))


def test_validate_input_contract_accepts_exact_old_pair_while_successors_are_present() -> None:
    base, successor = lineage_graph(), _successor(lineage_graph())
    value = aggregation_input(records=(successor, base), current_revisions=(_selection(base),))
    assert _validate(value) is None and _current(value) == (base,)


def test_select_canonical_current_records_returns_empty_tuple() -> None:
    assert _current(aggregation_input(records=(), current_revisions=())) == ()


def test_select_canonical_current_records_returns_one_exact_record_per_selection_in_canonical_order() -> None:
    alpha, beta = lineage_graph(), lineage_graph(prefix="beta")
    value = aggregation_input(records=(beta, alpha), current_revisions=(_selection(beta), _selection(alpha)))
    assert _current(value) == tuple(sorted((alpha, beta), key=expected_record_key))


def test_select_canonical_current_records_uses_evidence_global_earliest_capture_across_assessments() -> None:
    base = lineage_graph(); selected = _assessment_successor(base); later = _recapture(selected)
    assert _current(aggregation_input(records=(later, selected, base), current_revisions=(_selection(selected),))) == (selected,)


def test_select_canonical_current_records_rejects_missing_canonical_combination() -> None:
    base = lineage_graph(); selected = _record_variant(_assessment_successor(base), capture={"capture_id": "capture.later.2", "capture_digest": digest("1"), "captured_at": CAPTURED + timedelta(minutes=2)})
    with pytest.raises(ValueError, match="canonical capture"):
        _current(aggregation_input(records=(base, selected), current_revisions=(_selection(selected),)))


def test_select_canonical_current_records_has_no_temporal_latest_or_tip_fallback() -> None:
    base, successor = lineage_graph(), _successor(lineage_graph())
    value = aggregation_input(evaluated_at=ANCHOR, records=(successor, base), current_revisions=(_selection(base),))
    assert _current(value) == (base,)


def test_select_canonical_capture_records_returns_each_assessment_on_each_revision_global_capture() -> None:
    base = lineage_graph(); assessment = _assessment_successor(base); later = _recapture(base)
    assert _captures(aggregation_input(records=(later, assessment, base), current_revisions=())) == tuple(sorted((base, assessment), key=expected_record_key))


def test_select_canonical_capture_records_includes_wholly_noncurrent_revisions() -> None:
    base = lineage_graph(); successor = _successor(base); later = _recapture(successor)
    value = aggregation_input(records=(later, successor, base), current_revisions=(_selection(base),))
    assert _captures(value) == tuple(sorted((base, successor), key=expected_record_key))


def test_both_selectors_share_complete_validation_and_agree_on_current_identity() -> None:
    base = lineage_graph(); successor = _successor(base)
    hostile = (aggregation_input(records=(successor,), current_revisions=()), aggregation_input(records=(base, _record_variant(successor, evidence={"recorded_at": RECORDED - timedelta(seconds=1)})), current_revisions=()), aggregation_input(records=(base,), current_revisions=(TeamEvidenceCurrentRevisionSelection("evidence.missing", digest("1"), "assessment.missing", digest("2")),)))
    for value in hostile:
        for selector in (_current, _captures):
            with pytest.raises(ValueError):
                selector(value)
    valid = aggregation_input(records=(successor, base), current_revisions=(_selection(base),))
    assert all(record in _captures(valid) for record in _current(valid))
