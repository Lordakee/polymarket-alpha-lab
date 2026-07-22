from __future__ import annotations
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, Inexact, ROUND_UP, getcontext, setcontext
from hashlib import sha256
import importlib
import json
import pytest
from polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights
from polymarket_alpha_lab.team_evidence_aggregation_codec import team_evidence_aggregation_config_digest, team_evidence_aggregation_core_digest, team_evidence_aggregation_payload, validate_team_evidence_aggregation_core_digest
from polymarket_alpha_lab.team_evidence_aggregation_temporal import assess_team_evidence_temporal
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig, TeamEvidenceAggregationInput, TeamEvidenceAggregationRecord, TeamEvidenceAggregationResult,
    TeamEvidenceAssessmentRevision, TeamEvidenceCapture, TeamEvidenceContradictionResult, TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceDiagnosticRow, TeamEvidenceRequirement, TeamEvidenceRequirementCoverage,
    TeamEvidenceRevision, TeamEvidenceSourceLineage, select_team_evidence_canonical_capture_records, select_team_evidence_canonical_current_records,
)
from polymarket_alpha_lab.team_evidence_aggregation_witness import build_team_evidence_requirement_coverage
BASE_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)
def d(value: str) -> Decimal:
    return Decimal(value)
def digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()
BASE_CONFIG_VALUES: dict[str, object] = {
    "config_version": "generic-test-v1",
    "max_evidence_age_seconds": d("60.000000"),
    "max_capture_lag_seconds": d("20.000000"),
    "independence_group_weight_cap": d("1.000000"),
    "correlation_group_weight_cap": d("1.000000"),
    "max_requirement_assignments_per_evidence": 2,
    "contradiction_no_probability_max": d("0.250000"),
    "contradiction_yes_probability_min": d("0.750000"),
    "contradiction_watch_score": d("0.250000"),
    "contradiction_block_score": d("0.750000"),
    "publish_probability_floor": d("0.110000"),
    "publish_probability_ceiling": d("0.890000"),
    "maximum_records": 128,
    "maximum_requirements": 32,
    "maximum_requirement_memberships": 1024,
    "maximum_witness_edges": 256,
    "requirements": (),
}
def config(**changes: object) -> TeamEvidenceAggregationConfig:
    values = dict(BASE_CONFIG_VALUES)
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)
def root_record(
    stem: str,
    *,
    freshness_anchor_offset: int = 50,
    captured_offset: int = 55,
    recorded_offset: int = 60,
    assessed_offset: int = 65,
    probability_yes: Decimal = d("0.600000"),
    requested_weight: Decimal = d("0.200000"),
    requirement_ids: tuple[str, ...] = (),
    independence_key: str | None = None,
    correlation_key: str | None = None,
) -> TeamEvidenceAggregationRecord:
    source_lineage_id = f"lineage:{stem}"
    source_lineage_digest = digest(f"lineage-digest:{stem}")
    content_digest = digest(f"content:{stem}")
    evidence_revision_id = f"evidence:{stem}"
    evidence_revision_digest = digest(f"evidence-digest:{stem}")
    lineage = TeamEvidenceSourceLineage(source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest)
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}",
        capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=source_lineage_id,
        source_lineage_digest=source_lineage_digest,
        content_digest=content_digest,
        captured_at=BASE_TIME + timedelta(seconds=captured_offset),
    )
    evidence_revision = TeamEvidenceRevision(
        evidence_revision_id=evidence_revision_id,
        evidence_revision_digest=evidence_revision_digest,
        previous_evidence_revision_id=None,
        previous_evidence_revision_digest=None,
        source_lineage_id=source_lineage_id,
        source_lineage_digest=source_lineage_digest,
        content_digest=content_digest,
        requirement_ids=requirement_ids,
        freshness_anchor_at=BASE_TIME + timedelta(seconds=freshness_anchor_offset),
        recorded_at=BASE_TIME + timedelta(seconds=recorded_offset),
    )
    assessment_revision = TeamEvidenceAssessmentRevision(
        assessment_revision_id=f"assessment:{stem}",
        assessment_revision_digest=digest(f"assessment-digest:{stem}"),
        previous_assessment_revision_id=None,
        previous_assessment_revision_digest=None,
        evidence_revision_id=evidence_revision_id,
        evidence_revision_digest=evidence_revision_digest,
        assessed_at=BASE_TIME + timedelta(seconds=assessed_offset),
        probability_yes=probability_yes,
        requested_weight=requested_weight,
        rationale_digest=digest(f"rationale:{stem}"),
        independence_key=independence_key or f"ind:{stem}",
        correlation_key=correlation_key or f"corr:{stem}",
    )
    return TeamEvidenceAggregationRecord(source_lineage=lineage, capture=capture, evidence_revision=evidence_revision, assessment_revision=assessment_revision)
def recapture(record: TeamEvidenceAggregationRecord, *, stem: str, captured_offset: int) -> TeamEvidenceAggregationRecord:
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}",
        capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=record.capture.source_lineage_id,
        source_lineage_digest=record.capture.source_lineage_digest,
        content_digest=record.capture.content_digest,
        captured_at=BASE_TIME + timedelta(seconds=captured_offset),
    )
    return replace(record, capture=capture)
def selection(record: TeamEvidenceAggregationRecord) -> TeamEvidenceCurrentRevisionSelection:
    return TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id=record.evidence_revision.evidence_revision_id,
        evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
        assessment_revision_id=record.assessment_revision.assessment_revision_id,
        assessment_revision_digest=record.assessment_revision.assessment_revision_digest,
    )
def aggregation_input(records: tuple[TeamEvidenceAggregationRecord, ...], *, current_records: tuple[TeamEvidenceAggregationRecord, ...], evaluated_at: datetime = EVALUATED_AT) -> TeamEvidenceAggregationInput:
    return TeamEvidenceAggregationInput(
        evaluated_at=evaluated_at,
        records=records,
        current_revisions=tuple(selection(record) for record in current_records),
    )
def diagnostic_key(row: TeamEvidenceDiagnosticRow) -> tuple[object, ...]:
    return row.assessment_revision_id, row.evidence_revision_id, row.captured_at, row.capture_id, row.source_lineage_id
def diagnostic_row_for_record(
    result: TeamEvidenceAggregationResult,
    record: TeamEvidenceAggregationRecord,
) -> TeamEvidenceDiagnosticRow:
    identity = (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )
    matches = tuple(
        row
        for row in result.diagnostics
        if (
            row.source_lineage_id,
            row.capture_id,
            row.evidence_revision_id,
            row.assessment_revision_id,
        )
        == identity
    )
    assert len(matches) == 1
    return matches[0]
def api():
    return importlib.import_module("polymarket_alpha_lab.team_evidence_aggregation")
def build(input_value: TeamEvidenceAggregationInput, config_value: TeamEvidenceAggregationConfig) -> TeamEvidenceAggregationResult:
    return api().build_team_evidence_aggregation_result(input_value, config=config_value)
def requirement(requirement_id: str, *, count: int = 1, weight: str = "0.000001", status: str = "watch") -> TeamEvidenceRequirement:
    return TeamEvidenceRequirement(requirement_id, count, d(weight), status)
def record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return record.assessment_revision.assessment_revision_id, record.evidence_revision.evidence_revision_id, record.capture.captured_at, record.capture.capture_id, record.source_lineage.source_lineage_id
def record_variant(
    record: TeamEvidenceAggregationRecord,
    *,
    capture: dict[str, object] | None = None,
    evidence: dict[str, object] | None = None,
    assessment: dict[str, object] | None = None,
) -> TeamEvidenceAggregationRecord:
    revision = replace(record.evidence_revision, **(evidence or {}))
    capture_values: dict[str, object] = {
        "source_lineage_id": revision.source_lineage_id,
        "source_lineage_digest": revision.source_lineage_digest,
        "content_digest": revision.content_digest,
    }
    capture_values.update(capture or {})
    captured = replace(record.capture, **capture_values)
    assessment_values: dict[str, object] = {
        "evidence_revision_id": revision.evidence_revision_id,
        "evidence_revision_digest": revision.evidence_revision_digest,
    }
    assessment_values.update(assessment or {})
    assessed = replace(record.assessment_revision, **assessment_values)
    return TeamEvidenceAggregationRecord(
        record.source_lineage,
        captured,
        revision,
        assessed,
    )
def successor(
    record: TeamEvidenceAggregationRecord,
    stem: str,
    *,
    freshness_anchor_offset: int = 51,
    captured_offset: int = 56,
    recorded_offset: int = 61,
    assessed_offset: int = 66,
) -> TeamEvidenceAggregationRecord:
    content_digest = digest(f"content:{stem}")
    evidence_id = f"evidence:{stem}"
    evidence_digest = digest(f"evidence-digest:{stem}")
    return record_variant(
        record,
        capture={
            "capture_id": f"capture:{stem}",
            "capture_digest": digest(f"capture-digest:{stem}"),
            "content_digest": content_digest,
            "captured_at": BASE_TIME + timedelta(seconds=captured_offset),
        },
        evidence={
            "evidence_revision_id": evidence_id,
            "evidence_revision_digest": evidence_digest,
            "previous_evidence_revision_id": record.evidence_revision.evidence_revision_id,
            "previous_evidence_revision_digest": record.evidence_revision.evidence_revision_digest,
            "content_digest": content_digest,
            "freshness_anchor_at": BASE_TIME
            + timedelta(seconds=freshness_anchor_offset),
            "recorded_at": BASE_TIME + timedelta(seconds=recorded_offset),
        },
        assessment={
            "assessment_revision_id": f"assessment:{stem}",
            "assessment_revision_digest": digest(f"assessment-digest:{stem}"),
            "previous_assessment_revision_id": (
                record.assessment_revision.assessment_revision_id
            ),
            "previous_assessment_revision_digest": (
                record.assessment_revision.assessment_revision_digest
            ),
            "evidence_revision_id": evidence_id,
            "evidence_revision_digest": evidence_digest,
            "assessed_at": BASE_TIME + timedelta(seconds=assessed_offset),
            "rationale_digest": digest(f"rationale:{stem}"),
        },
    )
def assessment_successor(
    record: TeamEvidenceAggregationRecord,
    stem: str,
    *,
    assessed_offset: int = 66,
) -> TeamEvidenceAggregationRecord:
    return record_variant(
        record,
        assessment={
            "assessment_revision_id": f"assessment:{stem}",
            "assessment_revision_digest": digest(f"assessment-digest:{stem}"),
            "previous_assessment_revision_id": (
                record.assessment_revision.assessment_revision_id
            ),
            "previous_assessment_revision_digest": (
                record.assessment_revision.assessment_revision_digest
            ),
            "assessed_at": BASE_TIME + timedelta(seconds=assessed_offset),
            "probability_yes": d("0.610000"),
            "rationale_digest": digest(f"rationale:{stem}"),
        },
    )
def bypassed(value: object, **changes: object) -> object:
    clone = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(clone, field.name, changes.get(field.name, getattr(value, field.name)))
    return clone
def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
def self_digested(result: TeamEvidenceAggregationResult, **changes: object) -> TeamEvidenceAggregationResult:
    provisional = replace(result, **changes, core_digest="0" * 64)
    return replace(provisional, core_digest=team_evidence_aggregation_core_digest(provisional))
def crossed_records(requirement_ids: tuple[str, ...]) -> tuple[TeamEvidenceAggregationRecord, ...]:
    records = []
    for source, projection in (("a", "z"), ("z", "a")):
        base = root_record(f"cross-source-{source}", requirement_ids=requirement_ids)
        records.append(record_variant(base, capture={"capture_id": f"capture:cross-{projection}"}, evidence={"evidence_revision_id": f"evidence:cross-{projection}"}, assessment={"assessment_revision_id": f"assessment:cross-{projection}"}))
    return tuple(records)
def ready_fixture(
    *,
    requirements: tuple[TeamEvidenceRequirement, ...] = (),
) -> tuple[TeamEvidenceAggregationInput, TeamEvidenceAggregationConfig, TeamEvidenceAggregationResult]:
    ids = tuple(item.requirement_id for item in requirements)
    record = root_record("ready", requested_weight=d("0.400000"), requirement_ids=ids)
    config_value = config(requirements=requirements)
    input_value = aggregation_input((record,), current_records=(record,))
    return input_value, config_value, build(input_value, config_value)
DISPOSITION_CASES = (
    ("not_current_revision", "not_current_revision"),
    ("duplicate_capture", "duplicate_capture"),
    ("freshness_anchor_after_evaluation", "freshness_anchor_after_evaluation"),
    ("capture_after_evaluation", "capture_after_evaluation"),
    ("evidence_revision_after_evaluation", "evidence_revision_after_evaluation"),
    ("assessment_revision_after_evaluation", "assessment_revision_after_evaluation"),
    ("stale", "stale"),
    ("capture_before_freshness_anchor", "capture_before_freshness_anchor"),
    ("capture_lag_exceeded", "capture_lag_exceeded"),
    ("zero_requested_weight", "zero_requested_weight"),
    ("included", "included"),
)
def disposition_fixture(
    case: str,
) -> tuple[TeamEvidenceAggregationInput, TeamEvidenceAggregationConfig, TeamEvidenceAggregationRecord]:
    values: dict[str, dict[str, object]] = {
        "freshness_anchor_after_evaluation": dict(freshness_anchor_offset=101, captured_offset=101, recorded_offset=101, assessed_offset=101),
        "capture_after_evaluation": dict(freshness_anchor_offset=90, captured_offset=101, recorded_offset=101, assessed_offset=101),
        "evidence_revision_after_evaluation": dict(freshness_anchor_offset=50, captured_offset=55, recorded_offset=101, assessed_offset=101),
        "assessment_revision_after_evaluation": dict(freshness_anchor_offset=50, captured_offset=55, recorded_offset=60, assessed_offset=101),
        "stale": dict(freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42),
        "capture_before_freshness_anchor": dict(freshness_anchor_offset=50, captured_offset=49, recorded_offset=50, assessed_offset=51),
        "capture_lag_exceeded": dict(freshness_anchor_offset=50, captured_offset=71, recorded_offset=71, assessed_offset=72),
        "zero_requested_weight": dict(requested_weight=d("0.000000")),
    }
    canonical = root_record(f"case-{case}", **values.get(case, {}))
    if case == "duplicate_capture":
        target = recapture(canonical, stem="case-duplicate-later", captured_offset=56)
        records = (target, canonical)
    else:
        target, records = canonical, (canonical,)
    current = () if case == "not_current_revision" else (canonical,)
    return aggregation_input(records, current_records=current), config(), target
def test_builder_calls_both_canonical_selectors_with_exact_input_and_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, record, calls = api(), root_record("selector-spy"), []
    input_value = aggregation_input((record,), current_records=(record,))
    config_value = config()
    def capture_selector(value, *, config):
        calls.append(("capture", value, config))
        return select_team_evidence_canonical_capture_records(value, config=config)
    def current_selector(value, *, config):
        calls.append(("current", value, config))
        return select_team_evidence_canonical_current_records(value, config=config)
    monkeypatch.setattr(module, "select_team_evidence_canonical_capture_records", capture_selector)
    monkeypatch.setattr(module, "select_team_evidence_canonical_current_records", current_selector)
    module.build_team_evidence_aggregation_result(input_value, config=config_value)
    assert calls == [("capture", input_value, config_value), ("current", input_value, config_value)]
def test_canonical_capture_is_true_for_a_wholly_noncurrent_revision() -> None:
    current = root_record("noncurrent-root")
    noncurrent = successor(current, "noncurrent-successor")
    result = build(aggregation_input((noncurrent, current), current_records=(current,)), config())
    row = diagnostic_row_for_record(result, noncurrent)
    assert [(row.canonical_capture, row.selected_current_revision, row.disposition)] == [
        (True, False, "not_current_revision")
    ]
def test_selected_current_revision_is_pair_level_across_recaptures() -> None:
    canonical = root_record("pair-level")
    duplicate = recapture(canonical, stem="pair-level-later", captured_offset=56)
    result = build(aggregation_input((duplicate, canonical), current_records=(canonical,)), config())
    assert [(row.capture_id, row.selected_current_revision, row.canonical_capture, row.disposition) for row in result.diagnostics] == [
        (canonical.capture.capture_id, True, True, "included"),
        (duplicate.capture.capture_id, True, False, "duplicate_capture"),
    ]
def test_every_supplied_record_has_exactly_one_sorted_diagnostic_row(monkeypatch: pytest.MonkeyPatch) -> None:
    module, temporal_calls = api(), []
    selected = root_record("z-selected")
    duplicate = recapture(selected, stem="z-selected-later", captured_offset=56)
    noncurrent = root_record("a-noncurrent")
    input_value = aggregation_input((selected, noncurrent, duplicate), current_records=(selected,))
    policy = config()
    def temporal(record, *, evaluated_at, config):
        assessment = assess_team_evidence_temporal(record, evaluated_at=evaluated_at, config=config)
        temporal_calls.append((record, evaluated_at, config, assessment))
        return assessment
    monkeypatch.setattr(module, "assess_team_evidence_temporal", temporal)
    result = module.build_team_evidence_aggregation_result(input_value, config=policy)
    assert result.diagnostic_record_count == len(input_value.records)
    assert len(result.diagnostics) == len(input_value.records)
    assert tuple(diagnostic_key(row) for row in result.diagnostics) == tuple(sorted(diagnostic_key(row) for row in result.diagnostics))
    assert tuple((row.source_lineage_id, row.capture_id, row.evidence_revision_id, row.assessment_revision_id) for row in result.diagnostics) == tuple((record.source_lineage.source_lineage_id, record.capture.capture_id, record.evidence_revision.evidence_revision_id, record.assessment_revision.assessment_revision_id) for record in input_value.records)
    assert tuple(call[:3] for call in temporal_calls) == tuple((record, input_value.evaluated_at, policy) for record in input_value.records)
    for row, (record, _, _, temporal_value) in zip(result.diagnostics, temporal_calls, strict=True):
        assert diagnostic_key(row) == record_key(record)
        assert (row.captured_at, row.probability_yes, row.requested_weight) == (record.capture.captured_at, record.assessment_revision.probability_yes, record.assessment_revision.requested_weight)
        assert (row.evidence_age_seconds, row.capture_lag_seconds, row.captured_at_evaluation, row.evidence_revision_available_at_evaluation, row.assessment_revision_available_at_evaluation) == (temporal_value.evidence_age_seconds, temporal_value.capture_lag_seconds, temporal_value.captured_at_evaluation, temporal_value.evidence_revision_available_at_evaluation, temporal_value.assessment_revision_available_at_evaluation)
@pytest.mark.parametrize(("case", "expected_disposition"), DISPOSITION_CASES, ids=[item[0] for item in DISPOSITION_CASES])
def test_preallocation_dispositions_follow_exact_precedence(case: str, expected_disposition: str) -> None:
    input_value, config_value, target = disposition_fixture(case)
    result = build(input_value, config_value)
    row = diagnostic_row_for_record(result, target)
    assert row.disposition == expected_disposition
    if case != "included":
        assert (row.independence_allocated_weight, row.effective_weight) == (d("0.000000"),) * 2
        assert (str(row.independence_allocated_weight), str(row.effective_weight)) == ("0.000000",) * 2
    if case == "duplicate_capture":
        assert tuple(row.disposition for row in result.diagnostics) == ("included", "duplicate_capture")
    else:
        assert len(result.diagnostics) == 1
def test_independence_cap_exhausted_is_distinct_from_zero_request() -> None:
    kept = root_record("a-independence-kept", requested_weight=d("0.000001"), independence_key="ind:shared")
    exhausted = root_record("z-independence-exhausted", requested_weight=d("0.000001"), independence_key="ind:shared")
    policy = config(independence_group_weight_cap=d("0.000001"))
    result = build(aggregation_input((exhausted, kept), current_records=(exhausted, kept)), policy)
    row = diagnostic_row_for_record(result, exhausted)
    assert (row.requested_weight, row.independence_allocated_weight, row.effective_weight, row.disposition) == (d("0.000001"), d("0.000000"), d("0.000000"), "independence_cap_exhausted")
    assert diagnostic_row_for_record(result, kept).disposition == "included"
    assert sum((item.independence_allocated_weight for item in result.diagnostics), d("0.000000")) == d("0.000001")
def test_correlation_cap_exhausted_requires_positive_stage_one_weight() -> None:
    kept = root_record("a-correlation-kept", requested_weight=d("0.000001"), correlation_key="corr:shared")
    exhausted = root_record("z-correlation-exhausted", requested_weight=d("0.000001"), correlation_key="corr:shared")
    policy = config(correlation_group_weight_cap=d("0.000001"))
    result = build(aggregation_input((exhausted, kept), current_records=(exhausted, kept)), policy)
    row = diagnostic_row_for_record(result, exhausted)
    assert row.requested_weight > d("0.000000") and row.independence_allocated_weight > d("0.000000")
    assert (row.effective_weight, row.disposition) == (d("0.000000"), "correlation_cap_exhausted")
    assert diagnostic_row_for_record(result, kept).disposition == "included"
    assert sum((item.effective_weight for item in result.diagnostics), d("0.000000")) == d("0.000001")
def test_earlier_identity_dispositions_dominate_later_temporal_and_weight_gates() -> None:
    canonical = root_record("precedence-duplicate", freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42, requested_weight=d("0.000000"))
    duplicate = recapture(canonical, stem="precedence-duplicate-future", captured_offset=101)
    duplicate_result = build(aggregation_input((canonical, duplicate), current_records=(canonical,)), config())
    assert diagnostic_row_for_record(duplicate_result, duplicate).disposition == "duplicate_capture"
    noncurrent = root_record("precedence-noncurrent", freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=101)
    result = build(aggregation_input((noncurrent,), current_records=()), config())
    assert result.diagnostics[0].disposition == "not_current_revision"
TEMPORAL_PRECEDENCE_CASES = (
    ("freshness_anchor_after_evaluation", dict(freshness_anchor_offset=101, captured_offset=102, recorded_offset=102, assessed_offset=102)),
    ("capture_after_evaluation", dict(freshness_anchor_offset=90, captured_offset=101, recorded_offset=102, assessed_offset=102)),
    ("evidence_revision_after_evaluation", dict(freshness_anchor_offset=50, captured_offset=55, recorded_offset=101, assessed_offset=102)),
    ("assessment_revision_after_evaluation", dict(freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=101)),
    ("stale", dict(freshness_anchor_offset=39, captured_offset=38, recorded_offset=41, assessed_offset=42)),
    ("capture_before_freshness_anchor", dict(freshness_anchor_offset=50, captured_offset=49, recorded_offset=50, assessed_offset=51, requested_weight=d("0.000000"))),
    ("capture_lag_exceeded", dict(freshness_anchor_offset=50, captured_offset=71, recorded_offset=71, assessed_offset=72, requested_weight=d("0.000000"))),
)
@pytest.mark.parametrize(("expected", "overrides"), TEMPORAL_PRECEDENCE_CASES, ids=[item[0] for item in TEMPORAL_PRECEDENCE_CASES])
def test_feasible_temporal_disposition_overlaps_use_exact_precedence(expected: str, overrides: dict[str, object]) -> None:
    record = root_record(f"overlap-{expected}", **overrides)
    row = build(aggregation_input((record,), current_records=(record,)), config()).diagnostics[0]
    assert (row.disposition, row.independence_allocated_weight, row.effective_weight) == (expected, d("0.000000"), d("0.000000"))
def pipeline_spy(monkeypatch: pytest.MonkeyPatch):
    module, calls, owned = api(), [], []
    def allocate(records, *, config):
        calls.append(("allocation", records, config))
        allocations = allocate_team_evidence_weights(records, config=config)
        owned[:] = [records, allocations]
        return allocations
    def witness(records, allocations, *, config):
        calls.append(("witness", records, allocations, config))
        return build_team_evidence_requirement_coverage(records, allocations, config=config)
    monkeypatch.setattr(module, "allocate_team_evidence_weights", allocate)
    monkeypatch.setattr(module, "build_team_evidence_requirement_coverage", witness)
    return module, calls, owned
def test_materializer_end_to_end_dependency_order_is_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    module, calls = api(), []
    names = (
        "select_team_evidence_canonical_capture_records", "select_team_evidence_canonical_current_records",
        "assess_team_evidence_temporal", "allocate_team_evidence_weights", "build_team_evidence_requirement_coverage",
        "team_evidence_aggregation_config_digest", "team_evidence_aggregation_core_digest", "validate_team_evidence_aggregation_core_digest",
    )
    for name in names:
        original = getattr(module, name)
        def traced(*args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(*args, **kwargs)
        monkeypatch.setattr(module, name, traced)
    record = root_record("end-to-end-order")
    module.build_team_evidence_aggregation_result(aggregation_input((record,), current_records=(record,)), config=config())
    assert tuple(calls) == names
def test_allocation_and_witness_receive_the_exact_same_candidate_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    module, calls, owned = pipeline_spy(monkeypatch)
    kept = root_record("flow-a", requested_weight=d("0.000001"), independence_key="ind:flow")
    exhausted = root_record("flow-b", requested_weight=d("0.000001"), independence_key="ind:flow")
    stale = root_record("flow-c-stale", freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42)
    noncurrent = root_record("flow-d-noncurrent")
    policy = config(independence_group_weight_cap=d("0.000001"))
    input_value = aggregation_input((noncurrent, stale, exhausted, kept), current_records=(kept, exhausted, stale))
    expected_candidates = tuple(sorted((kept, exhausted), key=record_key))
    canonical_allocations = allocate_team_evidence_weights(expected_candidates, config=policy)
    module.build_team_evidence_aggregation_result(input_value, config=policy)
    assert calls == [("allocation", expected_candidates, policy), ("witness", expected_candidates, canonical_allocations, policy)]
    assert calls[1][1] is owned[0]
    assert calls[1][2] is owned[1]
def test_requirement_coverage_witnesses_preserve_exact_five_field_candidate_edge_order() -> None:
    requirements = (requirement("req:a", count=2, weight="0.100000", status="blocked"), requirement("req:b", count=2, weight="0.100000"))
    records = crossed_records(("req:b", "req:a"))
    result = build(aggregation_input(records[::-1], current_records=records[::-1]), config(requirements=requirements))
    keys = tuple((coverage.requirement_id, witness.source_lineage_id, witness.evidence_revision_id, witness.assessment_revision_id, witness.capture_id) for coverage in result.requirement_coverage for witness in coverage.witnesses)
    expected = tuple(sorted((req.requirement_id, record.source_lineage.source_lineage_id, record.evidence_revision.evidence_revision_id, record.assessment_revision.assessment_revision_id, record.capture.capture_id) for req in requirements for record in records))
    assert keys == expected == tuple(sorted(keys))
    assert tuple(item.source_lineage.source_lineage_id for item in sorted(records, key=record_key)) == ("lineage:cross-source-z", "lineage:cross-source-a")
    assert keys[:2] == (("req:a", "lineage:cross-source-a", "evidence:cross-z", "assessment:cross-z", "capture:cross-z"), ("req:a", "lineage:cross-source-z", "evidence:cross-a", "assessment:cross-a", "capture:cross-a"))
def test_old_exact_pair_remains_current_while_successors_are_present() -> None:
    old = root_record("old-pair")
    assessment = assessment_successor(old, "old-pair-assessment-2")
    revision = successor(assessment, "old-pair-evidence-2")
    result = build(aggregation_input((revision, assessment, old), current_records=(old,)), config())
    assert diagnostic_row_for_record(result, old).selected_current_revision is True
    assert diagnostic_row_for_record(result, old).disposition == "included"
    successor_rows = tuple(diagnostic_row_for_record(result, item) for item in (assessment, revision))
    assert successor_rows and all(row.disposition == "not_current_revision" for row in successor_rows)
RECAPTURE_NON_REPAIR_CASES = (
    ("freshness_anchor_after_evaluation", 102, "freshness_anchor_after_evaluation"),
    ("capture_after_evaluation", 102, "capture_after_evaluation"),
    ("stale", 41, "stale"),
    ("capture_lag_exceeded", 72, "capture_lag_exceeded"),
    ("evidence_revision_after_evaluation", 56, "evidence_revision_after_evaluation"),
    ("assessment_revision_after_evaluation", 56, "assessment_revision_after_evaluation"),
)
@pytest.mark.parametrize(("case", "recaptured_offset", "expected_disposition"), RECAPTURE_NON_REPAIR_CASES, ids=[item[0] for item in RECAPTURE_NON_REPAIR_CASES])
def test_recapture_cannot_repair_freshness_lag_or_availability(case: str, recaptured_offset: int, expected_disposition: str) -> None:
    _, policy, canonical = disposition_fixture(case)
    duplicate = recapture(canonical, stem=f"{case}-recaptured", captured_offset=recaptured_offset)
    result = build(aggregation_input((duplicate, canonical), current_records=(canonical,)), policy)
    assert tuple((row.capture_id, row.selected_current_revision, row.canonical_capture, row.disposition) for row in result.diagnostics) == ((canonical.capture.capture_id, True, True, expected_disposition), (duplicate.capture.capture_id, True, False, "duplicate_capture"))
    assert (result.arithmetic_record_count, result.effective_weight_total) == (0, d("0.000000"))
def test_future_evidence_or_assessment_revision_never_leaks_into_historical_arithmetic() -> None:
    evidence_future = root_record("a-evidence-future", recorded_offset=101, assessed_offset=101)
    assessment_future = root_record("b-assessment-future", assessed_offset=101)
    result = build(aggregation_input((assessment_future, evidence_future), current_records=(assessment_future, evidence_future)), config())
    assert tuple(row.disposition for row in result.diagnostics) == ("evidence_revision_after_evaluation", "assessment_revision_after_evaluation")
    assert result.arithmetic_record_count == 0
    assert result.effective_weight_total == d("0.000000")
def test_malformed_allocator_output_reaches_real_witness_once_with_exact_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    module, record, policy, malformed, allocation_calls, witness_calls = api(), root_record("owner-validation"), config(), [], [], []
    owner_witness = module.build_team_evidence_requirement_coverage
    monkeypatch.setattr(module, "allocate_team_evidence_weights", lambda records, *, config: allocation_calls.append(records) or malformed)
    def witness_spy(records, allocations, *, config):
        witness_calls.append((records, allocations, config)); assert allocations is malformed
        return owner_witness(records, allocations, config=config)
    monkeypatch.setattr(module, "build_team_evidence_requirement_coverage", witness_spy)
    with pytest.raises(ValueError) as error:
        module.build_team_evidence_aggregation_result(aggregation_input((record,), current_records=(record,)), config=policy)
    assert str(error.value) == "allocations must be an exact tuple"
    assert len(allocation_calls) == len(witness_calls) == 1 and witness_calls[0][1] is malformed and getattr(malformed, "callback_count", 0) == 0
def test_retired_requirement_ids_reject_only_positive_effective_candidates() -> None:
    active, retired = requirement("req:active"), ("req:retired",)
    positive = root_record("retired-positive", requirement_ids=retired)
    with pytest.raises(ValueError) as error:
        build(aggregation_input((positive,), current_records=(positive,)), config(requirements=(active,)))
    assert str(error.value) == "positive-effective requirement ID must exist in config.requirements"
    zero = root_record("retired-zero", requirement_ids=retired, requested_weight=d("0.000000"))
    stale = root_record("retired-stale", requirement_ids=retired, freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42)
    allowed = build(aggregation_input((zero, stale), current_records=(zero, stale)), config(requirements=(active,)))
    assert (diagnostic_row_for_record(allowed, zero).disposition, diagnostic_row_for_record(allowed, stale).disposition) == ("zero_requested_weight", "stale")
    kept = root_record("a-retired-cap-kept", requirement_ids=(active.requirement_id,), requested_weight=d("0.000001"), independence_key="ind:retired")
    exhausted = root_record("z-retired-cap-exhausted", requirement_ids=retired, requested_weight=d("0.000001"), independence_key="ind:retired")
    capped = build(aggregation_input((exhausted, kept), current_records=(exhausted, kept)), config(requirements=(active,), independence_group_weight_cap=d("0.000001")))
    assert diagnostic_row_for_record(capped, exhausted).disposition == "independence_cap_exhausted"
def assert_selector_rejection(monkeypatch: pytest.MonkeyPatch, input_value: TeamEvidenceAggregationInput, description: str) -> None:
    module, policy, calls = api(), config(), []
    def capture_selector(value, *, config):
        calls.append(("capture", value, config))
        return select_team_evidence_canonical_capture_records(value, config=config)
    def current_selector(value, *, config):
        calls.append(("current", value, config))
        return select_team_evidence_canonical_current_records(value, config=config)
    def allocation_must_not_run(*args, **kwargs):
        raise AssertionError("allocation called after selector rejection")
    monkeypatch.setattr(module, "select_team_evidence_canonical_capture_records", capture_selector)
    monkeypatch.setattr(module, "select_team_evidence_canonical_current_records", current_selector)
    monkeypatch.setattr(module, "allocate_team_evidence_weights", allocation_must_not_run)
    with pytest.raises(ValueError) as error:
        module.build_team_evidence_aggregation_result(input_value, config=policy)
    assert str(error.value) == description
    assert calls == [("capture", input_value, policy)]
def test_builder_rejects_conflicting_functional_dependencies_through_selectors(monkeypatch: pytest.MonkeyPatch) -> None:
    alpha, beta = root_record("fd-alpha"), root_record("fd-beta")
    conflict = record_variant(beta, capture={"capture_id": alpha.capture.capture_id})
    assert_selector_rejection(monkeypatch, aggregation_input((alpha, conflict), current_records=()), "capture.capture_id must determine one complete projection")
def test_builder_rejects_nonclosed_revision_chains_through_selectors(monkeypatch: pytest.MonkeyPatch) -> None:
    root = root_record("chain")
    cycle = successor(root, "chain-cycle")
    cycle = record_variant(cycle, evidence={"previous_evidence_revision_id": cycle.evidence_revision.evidence_revision_id, "previous_evidence_revision_digest": cycle.evidence_revision.evidence_revision_digest})
    assert_selector_rejection(monkeypatch, aggregation_input((root, cycle), current_records=()), "evidence_revision graph must be one connected linear chain")
def test_builder_rejects_invalid_local_time_order_through_selectors(monkeypatch: pytest.MonkeyPatch) -> None:
    record = root_record("bad-local-order", captured_offset=61, recorded_offset=60)
    assert_selector_rejection(monkeypatch, aggregation_input((record,), current_records=(record,)), "evidence_revision canonical capture.captured_at must be at or before recorded_at")
def test_builder_rejects_two_current_pairs_in_one_lineage_through_selectors(monkeypatch: pytest.MonkeyPatch) -> None:
    root = root_record("two-current")
    newer = assessment_successor(root, "two-current-newer")
    assert_selector_rejection(monkeypatch, aggregation_input((root, newer), current_records=(root, newer)), "current_revisions permits at most one current pair per source lineage")
def test_builder_rejects_anchor_only_noop_successor_through_selectors(monkeypatch: pytest.MonkeyPatch) -> None:
    root = root_record("anchor-noop")
    newer = successor(root, "anchor-noop-newer")
    noop = record_variant(newer, evidence={"content_digest": root.evidence_revision.content_digest, "requirement_ids": root.evidence_revision.requirement_ids, "freshness_anchor_at": BASE_TIME + timedelta(seconds=51)})
    assert_selector_rejection(monkeypatch, aggregation_input((root, noop), current_records=()), "evidence_revision successor must contain a semantic change")
def test_builder_rejects_recapture_that_changes_revision_owned_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    root = root_record("bad-recapture")
    changed = record_variant(recapture(root, stem="bad-recapture-later", captured_offset=56), evidence={"requirement_ids": ("req:changed",)})
    assert_selector_rejection(monkeypatch, aggregation_input((root, changed), current_records=()), "evidence_revision.evidence_revision_id must determine one complete projection")
def weighted_result(
    values: tuple[tuple[str, str], ...],
    *,
    requirements: tuple[TeamEvidenceRequirement, ...] = (),
    requirement_ids: tuple[str, ...] = (),
) -> TeamEvidenceAggregationResult:
    records = tuple(root_record(f"weighted-{index}", probability_yes=d(probability), requested_weight=d(weight), requirement_ids=requirement_ids) for index, (probability, weight) in enumerate(values))
    policy = config(requirements=requirements)
    return build(aggregation_input(records[::-1], current_records=records[::-1]), policy)
def test_weighted_probability_uses_included_effective_weights_and_one_final_quantization() -> None:
    result = weighted_result((("0.200000", "0.300000"), ("0.800000", "0.700000")))
    assert (result.requested_weight_total, result.independence_allocated_weight_total, result.effective_weight_total) == (d("1.000000"),) * 3
    assert result.arithmetic_record_count == 2
    assert result.arithmetic_probability_yes == d("0.620000")
def test_diagnostic_and_arithmetic_universes_have_exact_counts_and_weights() -> None:
    included = root_record("a-mixed-included", requested_weight=d("0.000001"))
    independence_kept = root_record("b-mixed-independence-kept", requested_weight=d("0.000001"), independence_key="ind:mixed")
    independence_exhausted = root_record("c-mixed-independence-exhausted", requested_weight=d("0.000001"), independence_key="ind:mixed")
    correlation_kept = root_record("d-mixed-correlation-kept", requested_weight=d("0.000001"), correlation_key="corr:mixed")
    correlation_exhausted = root_record("e-mixed-correlation-exhausted", requested_weight=d("0.000001"), correlation_key="corr:mixed")
    zero = root_record("f-mixed-zero", requested_weight=d("0.000000"))
    stale = root_record("g-mixed-stale", freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42)
    noncurrent = root_record("h-mixed-noncurrent")
    candidates = (included, independence_kept, independence_exhausted, correlation_kept, correlation_exhausted)
    input_value = aggregation_input(candidates + (zero, stale, noncurrent), current_records=candidates + (zero, stale))
    result = build(input_value, config(independence_group_weight_cap=d("0.000001"), correlation_group_weight_cap=d("0.000001")))
    assert (result.diagnostic_record_count, result.arithmetic_record_count) == (8, 3)
    assert tuple(row.disposition for row in result.diagnostics) == ("included", "included", "independence_cap_exhausted", "included", "correlation_cap_exhausted", "zero_requested_weight", "stale", "not_current_revision")
    assert (result.requested_weight_total, result.independence_allocated_weight_total, result.effective_weight_total) == (d("0.000005"), d("0.000004"), d("0.000003"))
def test_probability_is_canonical_pyes_without_complement_prior_market_or_log_odds() -> None:
    result = weighted_result((("0.200000", "1.000000"),))
    assert result.arithmetic_probability_yes == d("0.200000")
    assert result.arithmetic_probability_yes != d("0.800000")
def test_weighted_probability_does_not_quantize_products_before_sum() -> None:
    result = weighted_result((("0.000001", "0.500000"), ("0.000001", "0.500000")))
    assert result.arithmetic_probability_yes == d("0.000001")
@pytest.mark.parametrize(("probabilities", "expected"), ((("0.000000", "0.000001"), "0.000000"), (("0.000001", "0.000002"), "0.000002")), ids=("tie-to-even-zero", "tie-to-even-two"))
def test_weighted_probability_uses_round_half_even_at_final_tie(probabilities: tuple[str, str], expected: str) -> None:
    lower, upper = probabilities
    assert weighted_result(((lower, "0.500000"), (upper, "0.500000"))).arithmetic_probability_yes == d(expected)
def test_hostile_ambient_decimal_context_preserves_result_payload_and_digest() -> None:
    records = (root_record("hostile-a", probability_yes=d("0.123457"), requested_weight=d("0.333333")), root_record("hostile-b", probability_yes=d("0.765431"), requested_weight=d("0.666667")))
    input_value, policy = aggregation_input(records, current_records=records), config()
    baseline = build(input_value, policy)
    baseline_payload = team_evidence_aggregation_payload(baseline)
    original, hostile = getcontext().copy(), getcontext().copy()
    hostile.prec, hostile.rounding, hostile.traps[Inexact] = 6, ROUND_UP, True
    setcontext(hostile)
    try:
        hostile_result = build(input_value, policy)
        hostile_payload = team_evidence_aggregation_payload(hostile_result)
    finally:
        setcontext(original)
    assert hostile_result == baseline
    assert canonical_bytes(hostile_payload) == canonical_bytes(baseline_payload)
    assert hostile_result.core_digest == baseline.core_digest
def test_one_sided_support_has_no_contradiction_even_when_watch_threshold_is_zero() -> None:
    policy = config(contradiction_watch_score=d("0.000000"))
    records = (root_record("one-sided-yes", probability_yes=d("0.750000"), requested_weight=d("0.700000")), root_record("one-sided-neutral", probability_yes=d("0.500000"), requested_weight=d("0.300000")))
    result = build(aggregation_input(records, current_records=records), policy)
    assert result.contradiction == TeamEvidenceContradictionResult(yes_support_weight=d("0.700000"), no_support_weight=d("0.000000"), neutral_weight=d("0.300000"), contradiction_score=d("0.000000"), status="none")
CONTRADICTION_BOUNDARY_CASES = ((d("0.750000"), d("0.050000"), d("0.125000"), "none"), (d("0.700000"), d("0.100000"), d("0.250000"), "watch"), (d("0.500000"), d("0.300000"), d("0.750000"), "blocked"))
@pytest.mark.parametrize(("yes_weight", "no_weight", "expected_score", "expected_status"), CONTRADICTION_BOUNDARY_CASES, ids=("below-watch", "watch-boundary", "block-boundary"))
def test_contradiction_thresholds_are_inclusive_and_block_is_checked_first(yes_weight: Decimal, no_weight: Decimal, expected_score: Decimal, expected_status: str) -> None:
    result = weighted_result((("0.750000", str(yes_weight)), ("0.250000", str(no_weight))))
    assert result.contradiction.contradiction_score == expected_score
    assert result.contradiction.status == expected_status
def test_neutral_weight_is_reported_but_does_not_dilute_opposing_support() -> None:
    result = weighted_result((("0.750000", "0.050000"), ("0.250000", "0.050000"), ("0.500000", "0.900000")))
    assert result.contradiction == TeamEvidenceContradictionResult(d("0.050000"), d("0.050000"), d("0.900000"), d("1.000000"), "blocked")
STATUS_REASON_CASES = (
    ("no_arithmetic_plus_block_and_watch_requirements", "blocked", ("blocking_requirement_unmet", "no_arithmetic_evidence", "watch_requirement_unmet")),
    ("contradiction_blocked_plus_watch_requirement", "blocked", ("contradiction_blocked", "watch_requirement_unmet")),
    ("blocking_requirement_plus_contradiction_blocked", "blocked", ("blocking_requirement_unmet", "contradiction_blocked")),
    ("blocking_and_watch_requirements_plus_contradiction_blocked", "blocked", ("blocking_requirement_unmet", "contradiction_blocked", "watch_requirement_unmet")),
    ("blocking_requirement_plus_contradiction_watch", "blocked", ("blocking_requirement_unmet", "contradiction_watch")),
    ("watch_requirement_plus_contradiction_watch", "watch", ("contradiction_watch", "watch_requirement_unmet")),
)
@pytest.mark.parametrize(("case", "expected_status", "expected_reasons"), STATUS_REASON_CASES, ids=[item[0] for item in STATUS_REASON_CASES])
def test_status_precedence_and_mixed_reason_tuples_are_exact(case: str, expected_status: str, expected_reasons: tuple[str, ...]) -> None:
    blocked_requirement, watch_requirement = requirement("req:block", status="blocked"), requirement("req:watch")
    if case == "no_arithmetic_plus_block_and_watch_requirements":
        requirements, values = (blocked_requirement, watch_requirement), ()
    elif case == "contradiction_blocked_plus_watch_requirement":
        requirements, values = (watch_requirement,), (("0.750000", "0.500000"), ("0.250000", "0.300000"))
    elif case.endswith("contradiction_blocked"):
        requirements = (blocked_requirement, watch_requirement) if case.startswith("blocking_and_watch") else (blocked_requirement,)
        values = (("0.750000", "0.500000"), ("0.250000", "0.300000"))
    else:
        requirements = (blocked_requirement,) if case.startswith("blocking") else (watch_requirement,)
        values = (("0.750000", "0.700000"), ("0.250000", "0.100000"))
    result = weighted_result(values, requirements=requirements)
    assert (result.status, result.reason_codes, result.publishable_probability_yes) == (expected_status, expected_reasons, None)
READY_PUBLICATION_CASES = (
    (d("0.050000"), d("0.110000"), ("aggregation_ready", "publish_probability_floor_applied")),
    (d("0.950000"), d("0.890000"), ("aggregation_ready", "publish_probability_ceiling_applied")),
    (d("0.110000"), d("0.110000"), ("aggregation_ready",)),
    (d("0.890000"), d("0.890000"), ("aggregation_ready",)),
    (d("0.500000"), d("0.500000"), ("aggregation_ready",)),
)
@pytest.mark.parametrize(("probability", "expected_publishable", "expected_reasons"), READY_PUBLICATION_CASES, ids=("below-floor", "above-ceiling", "at-floor", "at-ceiling", "in-range"))
def test_ready_publication_uses_only_supplied_nonbtc_bounds(probability: Decimal, expected_publishable: Decimal, expected_reasons: tuple[str, ...]) -> None:
    result = weighted_result(((str(probability), "1.000000"),))
    assert (result.status, result.arithmetic_probability_yes, result.publishable_probability_yes, result.reason_codes) == ("ready", probability, expected_publishable, expected_reasons)
def test_nonready_result_retains_arithmetic_probability_but_never_publishes() -> None:
    result = weighted_result((("0.500000", "1.000000"),), requirements=(requirement("req:watch"),))
    assert (result.status, result.arithmetic_probability_yes, result.publishable_probability_yes, result.reason_codes) == ("watch", d("0.500000"), None, ("watch_requirement_unmet",))
def test_empty_input_is_typed_blocked_no_arithmetic_result(monkeypatch: pytest.MonkeyPatch) -> None:
    module, calls, _ = pipeline_spy(monkeypatch)
    requirements = (requirement("req:block", status="blocked"), requirement("req:watch"))
    policy = config(requirements=requirements)
    result = module.build_team_evidence_aggregation_result(aggregation_input((), current_records=()), config=policy)
    assert calls == [("allocation", (), policy), ("witness", (), (), policy)]
    assert (result.diagnostic_record_count, result.arithmetic_record_count) == (0, 0)
    assert (result.requested_weight_total, result.independence_allocated_weight_total, result.effective_weight_total) == (d("0.000000"),) * 3
    assert result.arithmetic_probability_yes is result.publishable_probability_yes is None
    assert result.contradiction == TeamEvidenceContradictionResult(d("0.000000"), d("0.000000"), d("0.000000"), d("0.000000"), "none")
    zero_values = (result.requested_weight_total, result.independence_allocated_weight_total, result.effective_weight_total, result.contradiction.yes_support_weight, result.contradiction.no_support_weight, result.contradiction.neutral_weight, result.contradiction.contradiction_score)
    assert tuple(str(value) for value in zero_values) == ("0.000000",) * len(zero_values)
    assert (result.status, result.reason_codes) == ("blocked", ("blocking_requirement_unmet", "no_arithmetic_evidence", "watch_requirement_unmet"))
def test_all_excluded_input_is_blocked_without_erasing_diagnostics() -> None:
    stale = root_record("all-excluded", freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42)
    result = build(aggregation_input((stale,), current_records=(stale,)), config())
    assert (result.status, result.arithmetic_record_count, result.reason_codes) == ("blocked", 0, ("no_arithmetic_evidence",))
    assert len(result.diagnostics) == 1 and result.diagnostics[0].disposition == "stale"
def test_result_contains_exactly_one_coverage_row_per_config_requirement() -> None:
    requirements = (requirement("req:z"), requirement("req:a", status="blocked"))
    result = weighted_result((), requirements=requirements)
    assert tuple(row.requirement_id for row in result.requirement_coverage) == tuple(item.requirement_id for item in config(requirements=requirements).requirements)
    assert len(result.requirement_coverage) == len(requirements)
def test_zero_candidate_requirement_preserves_every_configured_coverage_field() -> None:
    configured = requirement("req:zero", count=2, weight="0.400000", status="blocked")
    input_value, policy = aggregation_input((), current_records=()), config(requirements=(configured,))
    result = build(input_value, policy)
    assert result.requirement_coverage == (TeamEvidenceRequirementCoverage(requirement_id="req:zero", minimum_witness_count=2, assigned_witness_count=0, minimum_effective_weight=d("0.400000"), unmet_status="blocked", satisfied=False, witnesses=()),)
    assert api().validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=policy) is None
def test_facade_rejects_raw_witness_requirement_id_projection_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    module, record, requirements = api(), root_record("projection-drift"), (requirement("req:a"), requirement("req:b", status="blocked"))
    policy = config(requirements=requirements)
    real = module.build_team_evidence_requirement_coverage
    variants = (
        lambda *a, **k: real(*a, **k)[:-1],
        lambda *a, **k: real(*a, **k) + (TeamEvidenceRequirementCoverage("req:extra", 1, 0, d("0.100000"), "watch", False, ()),),
        lambda *a, **k: real(*a, **k)[::-1],
        lambda *a, **k: (),
    )
    for witness in variants:
        monkeypatch.setattr(module, "build_team_evidence_requirement_coverage", witness)
        with pytest.raises(ValueError) as error:
            module.build_team_evidence_aggregation_result(aggregation_input((record,), current_records=(record,)), config=policy)
        assert str(error.value) == "materialized aggregation result violates canonical invariants"
def assert_rematerialization_rejection(result: object, input_value: TeamEvidenceAggregationInput, policy: TeamEvidenceAggregationConfig) -> None:
    with pytest.raises(ValueError) as error:
        api().validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=policy)
    assert str(error.value) == "aggregation result must equal rematerialized result"
def test_result_validator_returns_exact_none_for_builder_result() -> None:
    input_value, policy, result = ready_fixture()
    assert api().validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=policy) is None
def test_builder_and_validator_never_call_each_others_public_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    module = api()
    public_builder = module.build_team_evidence_aggregation_result
    public_validator = module.validate_team_evidence_aggregation_result
    input_value, policy = aggregation_input((root_record("public-noncalls"),), current_records=()), config()
    monkeypatch.setattr(module, "validate_team_evidence_aggregation_result", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("builder called public validator")))
    result = public_builder(input_value, config=policy)
    monkeypatch.setattr(module, "build_team_evidence_aggregation_result", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("validator called public builder")))
    assert public_validator(result, aggregation_input=input_value, config=policy) is None
@pytest.mark.parametrize("dependency", ("input", "config"))
def test_result_validator_rejects_unchanged_valid_result_for_different_input_or_config(dependency: str) -> None:
    input_value, policy, result = ready_fixture()
    if dependency == "input":
        input_value = replace(input_value, evaluated_at=EVALUATED_AT + timedelta(seconds=1))
    else:
        policy = config(max_evidence_age_seconds=d("49.000000"))
    assert_rematerialization_rejection(result, input_value, policy)
def test_result_validator_rejects_constructor_valid_semantic_result_with_recomputed_digest() -> None:
    input_value, policy, result = ready_fixture()
    semantic = replace(result, reason_codes=("aggregation_ready", "semantic_change"), core_digest="0" * 64)
    semantic = replace(semantic, core_digest=team_evidence_aggregation_core_digest(semantic))
    assert type(semantic) is TeamEvidenceAggregationResult and semantic != result
    assert semantic.core_digest == team_evidence_aggregation_core_digest(semantic)
    assert_rematerialization_rejection(semantic, input_value, policy)
@pytest.mark.parametrize("field_change", ({"status": "watch"}, {"diagnostic_record_count": 999}, {"arithmetic_probability_yes": d("0.123456")}, {"publishable_probability_yes": None}, {"reason_codes": ("aggregation_ready", "contradiction_watch")}, {"core_digest": "f" * 64}, {"config_digest": "e" * 64}), ids=("status", "diagnostic_record_count", "arithmetic_probability_yes", "publishable_probability_yes", "reason_codes", "core_digest", "config_digest"))
def test_result_validator_rejects_every_tampered_top_level_field(field_change: dict[str, object]) -> None:
    input_value, policy, result = ready_fixture()
    assert_rematerialization_rejection(bypassed(result, **field_change), input_value, policy)
def test_result_validator_rejects_tampered_nested_contradiction() -> None:
    records = (root_record("forge-yes", probability_yes=d("0.750000"), requested_weight=d("0.600000")), root_record("forge-no", probability_yes=d("0.250000"), requested_weight=d("0.400000")))
    input_value, policy = aggregation_input(records, current_records=records), config()
    result = build(input_value, policy)
    contradiction = replace(result.contradiction, yes_support_weight=d("0.400000"), no_support_weight=d("0.600000"))
    tampered = self_digested(result, contradiction=contradiction)
    assert validate_team_evidence_aggregation_core_digest(tampered) is None
    assert_rematerialization_rejection(tampered, input_value, policy)
def test_result_validator_rejects_tampered_diagnostic() -> None:
    input_value, policy, result = ready_fixture()
    tampered = self_digested(result, diagnostics=(replace(result.diagnostics[0], capture_id="capture:self-digested-forgery"),))
    assert validate_team_evidence_aggregation_core_digest(tampered) is None
    assert_rematerialization_rejection(tampered, input_value, policy)
def test_result_validator_rejects_self_digested_nested_semantic_tampers() -> None:
    configured = requirement("req:self-digested")
    records = crossed_records((configured.requirement_id,))
    input_value, policy = aggregation_input(records, current_records=records), config(requirements=(configured,))
    result = build(input_value, policy)
    coverage, witness = result.requirement_coverage[0], result.requirement_coverage[0].witnesses[0]
    other = next(record for record in records if record.source_lineage.source_lineage_id != witness.source_lineage_id)
    forged_witness = replace(witness, source_lineage_id=other.source_lineage.source_lineage_id, capture_id=other.capture.capture_id, evidence_revision_id=other.evidence_revision.evidence_revision_id, assessment_revision_id=other.assessment_revision.assessment_revision_id, independence_key=other.assessment_revision.independence_key, effective_weight=diagnostic_row_for_record(result, other).effective_weight)
    tampered = self_digested(result, requirement_coverage=(replace(coverage, witnesses=(forged_witness,)),))
    assert validate_team_evidence_aggregation_core_digest(tampered) is None
    assert_rematerialization_rejection(tampered, input_value, policy)
def test_result_validator_rejects_missing_extra_duplicate_or_reordered_requirement_coverage() -> None:
    requirements = (requirement("req:a"), requirement("req:b", status="blocked"))
    input_value, policy, result = ready_fixture(requirements=requirements)
    extra = TeamEvidenceRequirementCoverage("req:extra", 1, 0, d("0.100000"), "watch", False, ())
    variants = (result.requirement_coverage[:-1], result.requirement_coverage + (extra,), result.requirement_coverage + result.requirement_coverage[:1], result.requirement_coverage[::-1])
    for coverage in variants:
        assert_rematerialization_rejection(bypassed(result, requirement_coverage=coverage), input_value, policy)
def test_result_validator_rejects_wrong_exact_result_type_and_constructor_bypass() -> None:
    input_value, policy, result = ready_fixture()
    with pytest.raises(ValueError) as error:
        api().validate_team_evidence_aggregation_result(object(), aggregation_input=input_value, config=policy)
    assert str(error.value) == "result must be exactly TeamEvidenceAggregationResult"
    incomplete = object.__new__(TeamEvidenceAggregationResult)
    for field in fields(result):
        if field.name != "core_digest": object.__setattr__(incomplete, field.name, getattr(result, field.name))
    assert_rematerialization_rejection(incomplete, input_value, policy)
def test_result_validator_rejects_constructor_bypassed_snan_with_stable_mismatch_error() -> None:
    input_value, policy, result = ready_fixture()
    assert_rematerialization_rejection(bypassed(result, requested_weight_total=Decimal("sNaN")), input_value, policy)
def test_result_validator_maps_bypassed_wrong_field_type() -> None:
    input_value, policy, result = ready_fixture()
    assert_rematerialization_rejection(bypassed(result, effective_weight_total="0.400000"), input_value, policy)
def test_result_validator_codec_precedes_rematerialization_and_supplied_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    input_value, policy, result, module, events = *ready_fixture(), api(), []
    original_materialize = module._materialize_team_evidence_aggregation_result
    monkeypatch.setattr(module, "_materialize_team_evidence_aggregation_result", lambda *a, **k: events.append("rematerialize") or original_materialize(*a, **k))
    assert module.validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=policy) is None
    assert events == ["rematerialize"]; events.clear()
    class EqualityTripwire:
        def __eq__(self, other: object) -> bool:
            events.append("field-equality"); raise RuntimeError("supplied-result callback executed")
    hostile, codec_validator = bypassed(result, config_version=EqualityTripwire()), module.validate_team_evidence_aggregation_core_digest
    monkeypatch.setattr(module, "validate_team_evidence_aggregation_core_digest", lambda value: events.append("supplied-codec") or codec_validator(value) if value is hostile else codec_validator(value))
    with pytest.raises(ValueError) as error:
        module.validate_team_evidence_aggregation_result(hostile, aggregation_input=input_value, config=policy)
    assert str(error.value) == "aggregation result must equal rematerialized result" and events == ["supplied-codec"]
def test_result_validator_preserves_malformed_input_and_config_errors() -> None:
    ready_input, policy, result = ready_fixture()
    alpha, beta = root_record("validator-fd-alpha"), root_record("validator-fd-beta")
    conflict = record_variant(beta, capture={"capture_id": alpha.capture.capture_id})
    malformed_input = aggregation_input((alpha, conflict), current_records=())
    malformed_config = bypassed(policy, maximum_records=0)
    cases = ((malformed_input, policy, "capture.capture_id must determine one complete projection"), (ready_input, malformed_config, "maximum_records must be an exact positive int in 1..128"))
    for input_value, config_value, description in cases:
        with pytest.raises(ValueError) as error:
            api().validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=config_value)
        assert str(error.value) == description
def test_result_validator_is_hostile_decimal_context_invariant() -> None:
    input_value, policy, result = ready_fixture()
    forged = self_digested(result, diagnostics=(replace(result.diagnostics[0], capture_id="capture:hostile-forgery"),))
    original, hostile = getcontext().copy(), getcontext().copy()
    hostile.prec, hostile.rounding, hostile.traps[Inexact] = 6, ROUND_UP, True
    hostile.clear_flags()
    setcontext(hostile)
    expected_context = getcontext().copy()
    try:
        assert api().validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=policy) is None
        assert_rematerialization_rejection(forged, input_value, policy)
        assert (getcontext().prec, getcontext().rounding, getcontext().traps, getcontext().flags) == (expected_context.prec, expected_context.rounding, expected_context.traps, expected_context.flags)
    finally:
        setcontext(original)
def test_materializer_uses_codec_helpers_in_exact_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    module, calls = api(), []
    record = root_record("codec-sequence")
    input_value, policy = aggregation_input((record,), current_records=(record,)), config()
    def config_digest(value):
        calls.append(("config", value))
        return team_evidence_aggregation_config_digest(value)
    def core_digest(value):
        calls.append(("core", value))
        return team_evidence_aggregation_core_digest(value)
    def core_validator(value):
        calls.append(("validate", value))
        return validate_team_evidence_aggregation_core_digest(value)
    monkeypatch.setattr(module, "team_evidence_aggregation_config_digest", config_digest)
    monkeypatch.setattr(module, "team_evidence_aggregation_core_digest", core_digest)
    monkeypatch.setattr(module, "validate_team_evidence_aggregation_core_digest", core_validator)
    result = module.build_team_evidence_aggregation_result(input_value, config=policy)
    assert tuple(name for name, _ in calls) == ("config", "core", "validate")
    assert calls[0][1] is policy and calls[1][1].core_digest == "0" * 64 and calls[2][1] is result
    calls.clear()
    assert module.validate_team_evidence_aggregation_result(result, aggregation_input=input_value, config=policy) is None
    assert tuple(name for name, _ in calls) == ("validate", "config", "core", "validate")
    assert calls[0][1] is result and calls[-1][1] is not result
def test_builder_config_digest_equals_exact_codec_digest() -> None:
    _, policy, result = ready_fixture(); assert result.config_digest == team_evidence_aggregation_config_digest(policy)
def test_builder_core_digest_equals_exact_codec_digest() -> None:
    _, _, result = ready_fixture(); assert result.core_digest == team_evidence_aggregation_core_digest(result)
def test_core_digest_changes_when_any_semantic_result_field_changes() -> None:
    configured = requirement("req:digest", weight="0.100000")
    record = root_record("digest-fields", requested_weight=d("0.600000"), requirement_ids=(configured.requirement_id,))
    policy = config(independence_group_weight_cap=d("0.500000"), correlation_group_weight_cap=d("0.400000"), requirements=(configured,))
    result = build(aggregation_input((record,), current_records=(record,)), policy)
    variants = (
        replace(result, evaluated_at=EVALUATED_AT + timedelta(seconds=1)), replace(result, config_version="generic-test-v2"), replace(result, config_digest="f" * 64), replace(result, status="watch"),
        replace(result, arithmetic_record_count=0), replace(result, requested_weight_total=d("0.700000")), replace(result, independence_allocated_weight_total=d("0.450000")), replace(result, effective_weight_total=d("0.300000")),
        replace(result, arithmetic_probability_yes=d("0.500000")), replace(result, publishable_probability_yes=d("0.500000")), replace(result, contradiction=replace(result.contradiction, status="watch")),
        replace(result, diagnostics=(replace(result.diagnostics[0], probability_yes=d("0.500000")),)), replace(result, diagnostics=(replace(result.diagnostics[0], capture_id="capture:digest-change"),)), replace(result, diagnostics=(replace(result.diagnostics[0], evidence_age_seconds=d("49.000000")),)),
        replace(result, contradiction=replace(result.contradiction, neutral_weight=d("0.300000"))), replace(result, requirement_coverage=(replace(result.requirement_coverage[0], minimum_witness_count=2, satisfied=False),)), replace(result, reason_codes=("aggregation_ready", "semantic_change")),
    )
    assert all(team_evidence_aggregation_core_digest(item) != result.core_digest for item in variants)
def test_semantic_tuple_permutations_produce_equal_results_payloads_and_digests() -> None:
    requirements = (requirement("req:a", weight="0.100000"), requirement("req:b", weight="0.100000", status="blocked"))
    ids = tuple(item.requirement_id for item in requirements)
    records = (root_record("permutation-a", requirement_ids=ids[::-1]), root_record("permutation-b", requirement_ids=ids))
    forward_config, reverse_config = config(requirements=requirements), config(requirements=requirements[::-1])
    forward_input = aggregation_input(records, current_records=records)
    reverse_input = aggregation_input(records[::-1], current_records=records[::-1])
    forward, reverse = build(forward_input, forward_config), build(reverse_input, reverse_config)
    assert forward_config == reverse_config and forward_input == reverse_input and forward == reverse
    assert team_evidence_aggregation_payload(forward) == team_evidence_aggregation_payload(reverse)
    assert forward.config_digest == reverse.config_digest and forward.core_digest == reverse.core_digest
