"""Offline contract tests for the Node 2C team evidence aggregation reducer.

Governing plan: docs/superpowers/plans/
2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md
Scope: Task 2.1-2.4 (batch 1), Task 3.1-3.3 and Task 4.1 (batch 2), plus the
review-required Decimal-context invariance assertions on rejection paths.

Spy contract pinned here: the production module must bind the consumed
predecessor functions (both selectors, allocator, witness builder) as plain
module-level names, because the monkeypatch spies patch those names in the
production module namespace and then delegate to the real implementations.

Drift note: the plan pins rejection-test regexes ``functional dependency`` and
``semantic field``, but the frozen reviewed predecessor never raises those
strings; its stable messages are ``... must determine one complete projection``
(functional-dependency conflicts) and ``... successor must contain a semantic
change`` (no-op successor). The three affected tests match the frozen
predecessor messages instead; no assertion was weakened. Compact formatting
(wide lines, single blank separators) keeps this file within the plan's
900-line ceiling.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, Inexact, ROUND_UP, getcontext
from hashlib import sha256

import pytest

import polymarket_alpha_lab.team_evidence_aggregation as team_evidence_aggregation
from polymarket_alpha_lab.team_evidence_aggregation import (
    build_team_evidence_aggregation_result, validate_team_evidence_aggregation_result)
from polymarket_alpha_lab.team_evidence_aggregation_codec import (
    team_evidence_aggregation_config_digest, team_evidence_aggregation_core_digest,
    team_evidence_aggregation_payload, validate_team_evidence_aggregation_core_digest)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig, TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord, TeamEvidenceAggregationResult,
    TeamEvidenceAssessmentRevision, TeamEvidenceCapture, TeamEvidenceContradictionResult,
    TeamEvidenceCurrentRevisionSelection, TeamEvidenceDiagnosticRow, TeamEvidenceRequirement,
    TeamEvidenceRequirementCoverage, TeamEvidenceRevision, TeamEvidenceSourceLineage)

BASE_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)
MISMATCH = "aggregation result must equal rematerialized result"
MISSING = object()
build = build_team_evidence_aggregation_result
validate = validate_team_evidence_aggregation_result

def d(value: str) -> Decimal:
    return Decimal(value)

def digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()

BASE_CONFIG_VALUES: dict[str, object] = {
    "config_version": "generic-test-v1",
    "max_evidence_age_seconds": d("60.000000"), "max_capture_lag_seconds": d("20.000000"),
    "independence_group_weight_cap": d("1.000000"), "correlation_group_weight_cap": d("1.000000"),
    "max_requirement_assignments_per_evidence": 2,
    "contradiction_no_probability_max": d("0.250000"), "contradiction_yes_probability_min": d("0.750000"),
    "contradiction_watch_score": d("0.250000"), "contradiction_block_score": d("0.750000"),
    "publish_probability_floor": d("0.110000"), "publish_probability_ceiling": d("0.890000"),
    "maximum_records": 128, "maximum_requirements": 32,
    "maximum_requirement_memberships": 1024, "maximum_witness_edges": 256,
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
    lineage = TeamEvidenceSourceLineage(
        source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest)
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}", capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest,
        content_digest=content_digest, captured_at=BASE_TIME + timedelta(seconds=captured_offset))
    evidence_revision = TeamEvidenceRevision(
        evidence_revision_id=evidence_revision_id, evidence_revision_digest=evidence_revision_digest,
        previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
        source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest,
        content_digest=content_digest, requirement_ids=requirement_ids,
        freshness_anchor_at=BASE_TIME + timedelta(seconds=freshness_anchor_offset),
        recorded_at=BASE_TIME + timedelta(seconds=recorded_offset))
    assessment_revision = TeamEvidenceAssessmentRevision(
        assessment_revision_id=f"assessment:{stem}",
        assessment_revision_digest=digest(f"assessment-digest:{stem}"),
        previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
        evidence_revision_id=evidence_revision_id, evidence_revision_digest=evidence_revision_digest,
        assessed_at=BASE_TIME + timedelta(seconds=assessed_offset),
        probability_yes=probability_yes, requested_weight=requested_weight,
        rationale_digest=digest(f"rationale:{stem}"),
        independence_key=independence_key or f"ind:{stem}", correlation_key=correlation_key or f"corr:{stem}")
    return TeamEvidenceAggregationRecord(
        source_lineage=lineage, capture=capture, evidence_revision=evidence_revision,
        assessment_revision=assessment_revision)

def recapture(
    record: TeamEvidenceAggregationRecord,
    *,
    stem: str,
    captured_offset: int,
) -> TeamEvidenceAggregationRecord:
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}", capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=record.capture.source_lineage_id,
        source_lineage_digest=record.capture.source_lineage_digest,
        content_digest=record.capture.content_digest,
        captured_at=BASE_TIME + timedelta(seconds=captured_offset))
    return replace(record, capture=capture)

def selection(record: TeamEvidenceAggregationRecord) -> TeamEvidenceCurrentRevisionSelection:
    return TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id=record.evidence_revision.evidence_revision_id,
        evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
        assessment_revision_id=record.assessment_revision.assessment_revision_id,
        assessment_revision_digest=record.assessment_revision.assessment_revision_digest)

def aggregation_input(
    records: tuple[TeamEvidenceAggregationRecord, ...],
    *,
    current_records: tuple[TeamEvidenceAggregationRecord, ...],
    evaluated_at: datetime = EVALUATED_AT,
) -> TeamEvidenceAggregationInput:
    return TeamEvidenceAggregationInput(
        evaluated_at=evaluated_at, records=records,
        current_revisions=tuple(selection(record) for record in current_records))

def diagnostic_key(row: TeamEvidenceDiagnosticRow) -> tuple[object, ...]:
    return (
        row.assessment_revision_id, row.evidence_revision_id, row.captured_at,
        row.capture_id, row.source_lineage_id)

def diagnostic_row_for_record(
    result: TeamEvidenceAggregationResult,
    record: TeamEvidenceAggregationRecord,
) -> TeamEvidenceDiagnosticRow:
    expected_identity = (
        record.source_lineage.source_lineage_id, record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id)
    matches = tuple(
        row for row in result.diagnostics
        if (row.source_lineage_id, row.capture_id, row.evidence_revision_id,
            row.assessment_revision_id) == expected_identity)
    assert len(matches) == 1
    return matches[0]

config_value: TeamEvidenceAggregationConfig = config()
BASE_RECORD: TeamEvidenceAggregationRecord = root_record("alpha")
input_value: TeamEvidenceAggregationInput = aggregation_input(
    (BASE_RECORD,), current_records=(BASE_RECORD,))
LOW_RECORD: TeamEvidenceAggregationRecord = root_record(
    "a-low", probability_yes=d("0.200000"), requested_weight=d("0.300000"))
HIGH_RECORD: TeamEvidenceAggregationRecord = root_record(
    "b-high", probability_yes=d("0.800000"), requested_weight=d("0.700000"))
STALE_RECORD: TeamEvidenceAggregationRecord = root_record(
    "c-stale", freshness_anchor_offset=39, captured_offset=40,
    recorded_offset=41, assessed_offset=42)

def record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id, record.capture.captured_at,
        record.capture.capture_id, record.source_lineage.source_lineage_id)

def requirement(
    requirement_id: str,
    *,
    minimum_witness_count: int = 1,
    minimum_effective_weight: Decimal = d("0.000000"),
    unmet_status: str = "watch",
) -> TeamEvidenceRequirement:
    return TeamEvidenceRequirement(
        requirement_id=requirement_id, minimum_witness_count=minimum_witness_count,
        minimum_effective_weight=minimum_effective_weight, unmet_status=unmet_status)

BLOCKED_REQUIREMENT = requirement("req:blocked", unmet_status="blocked")
WATCH_REQUIREMENT = requirement("req:watch", unmet_status="watch")
CORE_REQUIREMENT = requirement("req:core")

def result_for(*records, config_value=config(), evaluated_at=EVALUATED_AT):
    return build(aggregation_input(
        records, current_records=records, evaluated_at=evaluated_at), config=config_value)

def context_state():
    """Snapshot the caller's active Decimal context flags, traps, and settings."""
    context = getcontext()
    return context.prec, context.rounding, dict(context.flags), dict(context.traps)

def assert_context_state_unchanged(state):
    """Assert a rejection left the caller's Decimal context exactly unchanged."""
    assert context_state() == state

def rejects_before_allocation(monkeypatch, value, config_for_case, pattern):
    """Assert build fails with ``pattern`` through the selectors, pre-allocation,
    leaving the caller's Decimal context flags and traps exactly unchanged."""
    calls = []
    real = team_evidence_aggregation.allocate_team_evidence_weights
    def spy(records, *, config):
        calls.append((records, config))
        return real(records, config=config)
    monkeypatch.setattr(team_evidence_aggregation, "allocate_team_evidence_weights", spy)
    state = context_state()
    with pytest.raises(ValueError, match=pattern):
        build(value, config=config_for_case)
    assert calls == []
    assert_context_state_unchanged(state)

def forge_result(base_result, changes):
    """Constructor-bypass forgery of any slotted dataclass; MISSING unsets a slot."""
    forged = object.__new__(type(base_result))
    for name in type(base_result).__slots__:
        if changes.get(name) is not MISSING:
            object.__setattr__(forged, name, getattr(base_result, name))
    for name, value in changes.items():
        if value is not MISSING:
            object.__setattr__(forged, name, value)
    return forged

def linked_record(
    stem: str,
    *,
    lineage: TeamEvidenceSourceLineage,
    previous_evidence_id: str | None, previous_evidence_digest: str | None,
    previous_assessment_id: str | None, previous_assessment_digest: str | None,
    content_digest: str,
    freshness_anchor_offset: int = 50, captured_offset: int = 55,
    recorded_offset: int = 60, assessed_offset: int = 65,
) -> TeamEvidenceAggregationRecord:
    """A record on ``lineage`` with explicit revision links (test-only helper)."""
    base = root_record(
        stem, freshness_anchor_offset=freshness_anchor_offset,
        captured_offset=captured_offset, recorded_offset=recorded_offset,
        assessed_offset=assessed_offset)
    evidence = replace(
        base.evidence_revision, previous_evidence_revision_id=previous_evidence_id,
        previous_evidence_revision_digest=previous_evidence_digest,
        source_lineage_id=lineage.source_lineage_id,
        source_lineage_digest=lineage.source_lineage_digest, content_digest=content_digest)
    assessment = replace(
        base.assessment_revision, previous_assessment_revision_id=previous_assessment_id,
        previous_assessment_revision_digest=previous_assessment_digest)
    capture = replace(
        base.capture, source_lineage_id=lineage.source_lineage_id,
        source_lineage_digest=lineage.source_lineage_digest, content_digest=content_digest)
    return replace(
        base, source_lineage=lineage, capture=capture, evidence_revision=evidence,
        assessment_revision=assessment)

def evidence_successor(base: TeamEvidenceAggregationRecord, stem: str, *, content_change=True):
    return linked_record(
        stem,
        lineage=base.source_lineage,
        previous_evidence_id=base.evidence_revision.evidence_revision_id,
        previous_evidence_digest=base.evidence_revision.evidence_revision_digest,
        previous_assessment_id=base.assessment_revision.assessment_revision_id,
        previous_assessment_digest=base.assessment_revision.assessment_revision_digest,
        content_digest=(
            digest(f"content:{stem}") if content_change else base.evidence_revision.content_digest),
        freshness_anchor_offset=offset_of(base.evidence_revision.freshness_anchor_at),
        recorded_offset=offset_of(base.evidence_revision.recorded_at),
        assessed_offset=offset_of(base.assessment_revision.assessed_at))

def offset_of(moment: datetime) -> int:
    return int((moment - BASE_TIME).total_seconds())

DISPOSITION_KWARGS = {
    "not_current_revision": {},
    "freshness_anchor_after_evaluation": dict(freshness_anchor_offset=101, captured_offset=101, recorded_offset=101, assessed_offset=101),
    "capture_after_evaluation": dict(freshness_anchor_offset=90, captured_offset=101, recorded_offset=101, assessed_offset=101),
    "evidence_revision_after_evaluation": dict(recorded_offset=101, assessed_offset=101),
    "assessment_revision_after_evaluation": dict(assessed_offset=101),
    "stale": dict(freshness_anchor_offset=39, captured_offset=40, recorded_offset=41, assessed_offset=42),
    "capture_before_freshness_anchor": dict(captured_offset=49, recorded_offset=50, assessed_offset=51),
    "capture_lag_exceeded": dict(captured_offset=71, recorded_offset=71, assessed_offset=72),
    "zero_requested_weight": dict(requested_weight=d("0.000000")),
    "included": {},
}

def disposition_case(case):
    """One decisive scenario per disposition; records[0] is the decisive row."""
    if case == "duplicate_capture":
        canonical = root_record("d-canonical")
        duplicate = recapture(canonical, stem="d-duplicate", captured_offset=56)
        return (
            aggregation_input((canonical, duplicate), current_records=(canonical,)),
            config(), (duplicate, canonical))
    record = root_record("d-case", **DISPOSITION_KWARGS[case])
    current = () if case == "not_current_revision" else (record,)
    return aggregation_input((record,), current_records=current), config(), (record,)

# Task 2.2: selector boundary and diagnostic universe tests.
def test_builder_calls_both_canonical_selectors_with_exact_input_and_config(monkeypatch):
    record = root_record("selector-spy")
    aggregation_input_value = aggregation_input((record,), current_records=(record,))
    calls = []
    real_capture = team_evidence_aggregation.select_team_evidence_canonical_capture_records
    real_current = team_evidence_aggregation.select_team_evidence_canonical_current_records
    def capture_spy(value, *, config):
        calls.append(("capture", value, config))
        return real_capture(value, config=config)
    def current_spy(value, *, config):
        calls.append(("current", value, config))
        return real_current(value, config=config)
    monkeypatch.setattr(team_evidence_aggregation, "select_team_evidence_canonical_capture_records", capture_spy)
    monkeypatch.setattr(team_evidence_aggregation, "select_team_evidence_canonical_current_records", current_spy)
    build(aggregation_input_value, config=config_value)
    assert calls == [
        ("capture", aggregation_input_value, config_value),
        ("current", aggregation_input_value, config_value)]

def test_canonical_capture_is_true_for_a_wholly_noncurrent_revision():
    record = root_record("orphan-revision")
    result = build(aggregation_input((record,), current_records=()), config=config())
    assert [
        (row.canonical_capture, row.selected_current_revision, row.disposition)
        for row in result.diagnostics
    ] == [(True, False, "not_current_revision")]

def test_selected_current_revision_is_pair_level_across_recaptures():
    canonical = root_record("pair-level")
    duplicate = recapture(canonical, stem="pair-level-later", captured_offset=56)
    result = build(
        aggregation_input((canonical, duplicate), current_records=(canonical,)), config=config())
    assert [
        (row.capture_id, row.selected_current_revision, row.canonical_capture, row.disposition)
        for row in result.diagnostics
    ] == [
        (canonical.capture.capture_id, True, True, "included"),
        (duplicate.capture.capture_id, True, False, "duplicate_capture")]

def test_every_supplied_record_has_exactly_one_sorted_diagnostic_row():
    alpha = root_record("u-alpha")
    alpha_later = recapture(alpha, stem="u-alpha-later", captured_offset=56)
    beta = root_record("u-beta")
    aggregation_input_value = aggregation_input(
        (alpha_later, beta, alpha), current_records=(alpha, beta))
    result = build(aggregation_input_value, config=config())
    assert result.diagnostic_record_count == len(aggregation_input_value.records)
    assert len(result.diagnostics) == len(aggregation_input_value.records)
    assert tuple(diagnostic_key(row) for row in result.diagnostics) == tuple(
        sorted(diagnostic_key(row) for row in result.diagnostics))
    for record in aggregation_input_value.records:
        assert diagnostic_row_for_record(result, record) is not None

# Task 2.3: pre-allocation disposition precedence for all thirteen values.
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

@pytest.mark.parametrize(("case", "expected_disposition"), DISPOSITION_CASES, ids=[c for c, _ in DISPOSITION_CASES])
def test_preallocation_dispositions_follow_exact_precedence(case, expected_disposition):
    aggregation_input_value, config_for_case, records = disposition_case(case)
    result = build(aggregation_input_value, config=config_for_case)
    assert len(result.diagnostics) == len(records)
    assert diagnostic_row_for_record(result, records[0]).disposition == expected_disposition
    if case == "duplicate_capture":
        assert diagnostic_row_for_record(result, records[1]).disposition == "included"

def test_independence_cap_exhausted_is_distinct_from_zero_request():
    kept = root_record("a-independence-kept", requested_weight=d("0.000001"), independence_key="ind:shared", correlation_key="corr:kept")
    exhausted = root_record("z-independence-exhausted", requested_weight=d("0.000001"), independence_key="ind:shared", correlation_key="corr:exhausted")
    result = result_for(kept, exhausted, config_value=config(independence_group_weight_cap=d("0.000001")))
    independence_exhausted = diagnostic_row_for_record(result, exhausted)
    assert independence_exhausted.requested_weight == d("0.000001")
    assert independence_exhausted.independence_allocated_weight == d("0.000000")
    assert independence_exhausted.effective_weight == d("0.000000")
    assert independence_exhausted.disposition == "independence_cap_exhausted"
    kept_row = diagnostic_row_for_record(result, kept)
    assert kept_row.disposition == "included"
    assert (kept_row.independence_allocated_weight
            + independence_exhausted.independence_allocated_weight == d("0.000001"))

def test_correlation_cap_exhausted_requires_positive_stage_one_weight():
    kept = root_record("a-correlation-kept", requested_weight=d("0.000001"), independence_key="ind:kept", correlation_key="corr:shared")
    exhausted = root_record("z-correlation-exhausted", requested_weight=d("0.000001"), independence_key="ind:exhausted", correlation_key="corr:shared")
    result = result_for(kept, exhausted, config_value=config(correlation_group_weight_cap=d("0.000001")))
    correlation_exhausted = diagnostic_row_for_record(result, exhausted)
    assert correlation_exhausted.requested_weight > d("0.000000")
    assert correlation_exhausted.independence_allocated_weight > d("0.000000")
    assert correlation_exhausted.effective_weight == d("0.000000")
    assert correlation_exhausted.disposition == "correlation_cap_exhausted"
    kept_row = diagnostic_row_for_record(result, kept)
    assert kept_row.disposition == "included"
    assert (kept_row.effective_weight + correlation_exhausted.effective_weight == d("0.000001"))

def test_identity_gates_dominate_all_later_disposition_gates():
    future_zero = dict(freshness_anchor_offset=101, captured_offset=101, recorded_offset=101,
                       assessed_offset=101, requested_weight=d("0.000000"))
    canonical = root_record("precedence-recapture", **future_zero)
    duplicate = recapture(canonical, stem="precedence-recapture-later", captured_offset=102)
    result = build(
        aggregation_input((canonical, duplicate), current_records=(canonical,)), config=config())
    assert diagnostic_row_for_record(result, duplicate).disposition == "duplicate_capture"
    assert diagnostic_row_for_record(result, canonical).disposition == (
        "freshness_anchor_after_evaluation")
    noncurrent = root_record("precedence-noncurrent", **future_zero)
    noncurrent_result = build(
        aggregation_input((noncurrent,), current_records=()), config=config())
    assert len(noncurrent_result.diagnostics) == 1
    assert noncurrent_result.diagnostics[0].disposition == "not_current_revision"

# Task 2.4: allocation/witness data flow and historical-selection tests.
def test_allocation_and_witness_receive_the_exact_same_candidate_tuple(monkeypatch):
    kept = root_record("a-independence-kept", requested_weight=d("0.000001"), independence_key="ind:shared", correlation_key="corr:kept")
    exhausted = root_record("z-independence-exhausted", requested_weight=d("0.000001"), independence_key="ind:shared", correlation_key="corr:exhausted")
    duplicate = recapture(kept, stem="a-independence-later", captured_offset=56)
    aggregation_input_value = aggregation_input(
        (kept, exhausted, duplicate), current_records=(kept, exhausted))
    config_for_flow = config(independence_group_weight_cap=d("0.000001"))
    allocation_calls = []
    witness_calls = []
    real_allocate = team_evidence_aggregation.allocate_team_evidence_weights
    real_witness = team_evidence_aggregation.build_team_evidence_requirement_coverage
    def allocation_spy(records, *, config):
        allocation_calls.append((records, config))
        return real_allocate(records, config=config)
    def witness_spy(allocation_input_records, allocations, *, config):
        witness_calls.append((allocation_input_records, allocations, config))
        return real_witness(allocation_input_records, allocations, config=config)
    monkeypatch.setattr(team_evidence_aggregation, "allocate_team_evidence_weights", allocation_spy)
    monkeypatch.setattr(team_evidence_aggregation, "build_team_evidence_requirement_coverage", witness_spy)
    build(aggregation_input_value, config=config_for_flow)
    expected_candidates = tuple(sorted((kept, exhausted), key=record_key))
    canonical_allocations = real_allocate(expected_candidates, config=config_for_flow)
    assert allocation_calls == [(expected_candidates, config_for_flow)]
    assert witness_calls == [(expected_candidates, canonical_allocations, config_for_flow)]

def test_requirement_coverage_witnesses_preserve_exact_five_field_candidate_edge_order():
    alpha = root_record("w-alpha", requirement_ids=("req:core",), requested_weight=d("0.400000"))
    beta = root_record("w-beta", requirement_ids=("req:core",), requested_weight=d("0.600000"))
    two_witnesses = requirement("req:core", minimum_witness_count=2)
    result = result_for(alpha, beta, config_value=config(requirements=(two_witnesses,)))
    witness_edge_keys = tuple(
        (coverage.requirement_id, witness.source_lineage_id, witness.evidence_revision_id,
         witness.assessment_revision_id, witness.capture_id)
        for coverage in result.requirement_coverage for witness in coverage.witnesses)
    assert witness_edge_keys == tuple(sorted(witness_edge_keys))
    assert len(witness_edge_keys) == 2

def test_old_exact_pair_remains_current_while_successors_are_present():
    old = root_record("o-base")
    successor = evidence_successor(old, "o-successor")
    result = build(
        aggregation_input((old, successor), current_records=(old,)), config=config())
    selected_old_row = diagnostic_row_for_record(result, old)
    assert selected_old_row.selected_current_revision is True
    assert selected_old_row.disposition == "included"
    successor_rows = tuple(
        row for row in result.diagnostics
        if row.evidence_revision_id == successor.evidence_revision.evidence_revision_id)
    assert successor_rows
    assert all(row.disposition == "not_current_revision" for row in successor_rows)

def test_recapture_cannot_repair_freshness_lag_or_availability():
    canonical = root_record("repair", captured_offset=71, recorded_offset=71, assessed_offset=72)
    duplicate = recapture(canonical, stem="repair-later", captured_offset=72)
    result = build(
        aggregation_input((canonical, duplicate), current_records=(canonical,)), config=config())
    assert diagnostic_row_for_record(result, canonical).disposition == "capture_lag_exceeded"
    assert diagnostic_row_for_record(result, duplicate).disposition == "duplicate_capture"
    assert result.arithmetic_record_count == 0

def test_future_evidence_or_assessment_revision_never_leaks_into_historical_arithmetic():
    future_evidence = root_record("h-alpha", recorded_offset=101, assessed_offset=101)
    future_assessment = root_record("h-beta", recorded_offset=60, assessed_offset=101)
    historical_result = build(
        aggregation_input(
            (future_evidence, future_assessment),
            current_records=(future_evidence, future_assessment),
            evaluated_at=BASE_TIME + timedelta(seconds=100)), config=config())
    assert tuple(row.disposition for row in historical_result.diagnostics) == (
        "evidence_revision_after_evaluation", "assessment_revision_after_evaluation")
    assert historical_result.arithmetic_record_count == 0
    assert historical_result.effective_weight_total == d("0.000000")

def test_builder_rejects_conflicting_functional_dependencies_through_selectors(monkeypatch):
    # Plan regex "functional dependency"; predecessor message is the projection error.
    first = root_record("fd-first")
    second = root_record("fd-second")
    conflicting_capture = TeamEvidenceCapture(
        capture_id=first.capture.capture_id, capture_digest=second.capture.capture_digest,
        source_lineage_id=second.capture.source_lineage_id,
        source_lineage_digest=second.capture.source_lineage_digest,
        content_digest=second.capture.content_digest,
        captured_at=second.capture.captured_at)
    rejects_before_allocation(
        monkeypatch,
        aggregation_input((first, replace(second, capture=conflicting_capture)), current_records=(first,)),
        config(), "must determine one complete projection")

def test_builder_rejects_nonclosed_revision_chains_through_selectors(monkeypatch):
    root = root_record("chain-root")
    tip = evidence_successor(root, "chain-tip")
    cycle_one = linked_record(
        "chain-cycle-one", lineage=root.source_lineage,
        previous_evidence_id="evidence:chain-cycle-two", previous_evidence_digest=digest("evidence-digest:chain-cycle-two"),
        previous_assessment_id=None, previous_assessment_digest=None,
        content_digest=digest("content:chain-cycle-one"))
    cycle_two = linked_record(
        "chain-cycle-two", lineage=root.source_lineage,
        previous_evidence_id="evidence:chain-cycle-one", previous_evidence_digest=digest("evidence-digest:chain-cycle-one"),
        previous_assessment_id=None, previous_assessment_digest=None,
        content_digest=digest("content:chain-cycle-two"))
    rejects_before_allocation(
        monkeypatch,
        aggregation_input((root, tip, cycle_one, cycle_two), current_records=(root,)),
        config(), "linear chain")

def test_builder_rejects_invalid_local_time_order_through_selectors(monkeypatch):
    record = root_record("time-order", captured_offset=61, recorded_offset=60, assessed_offset=65)
    rejects_before_allocation(
        monkeypatch, aggregation_input((record,), current_records=(record,)),
        config(), "canonical capture.*recorded_at")

def test_builder_rejects_two_current_pairs_in_one_lineage_through_selectors(monkeypatch):
    base = root_record("pair-base")
    successor = evidence_successor(base, "pair-successor")
    rejects_before_allocation(
        monkeypatch,
        aggregation_input((base, successor), current_records=(base, successor)),
        config(), "one current.*lineage")

def test_builder_rejects_anchor_only_noop_successor_through_selectors(monkeypatch):
    # Plan regex "semantic field"; predecessor message is the semantic-change error.
    base = root_record("anchor-base")
    noop = evidence_successor(base, "anchor-noop", content_change=False)
    rejects_before_allocation(
        monkeypatch, aggregation_input((base, noop), current_records=(base,)),
        config(), "must contain a semantic change")

def test_builder_rejects_recapture_that_changes_revision_owned_fields(monkeypatch):
    # Plan regex "functional dependency"; predecessor message is the projection error.
    canonical = root_record("owned")
    changed = recapture(
        root_record("owned", probability_yes=d("0.700000")), stem="owned-later",
        captured_offset=56)
    rejects_before_allocation(
        monkeypatch, aggregation_input((canonical, changed), current_records=(canonical,)),
        config(), "must determine one complete projection")

# Task 3.1: arithmetic and universe tests.
def test_weighted_probability_uses_included_effective_weights_and_one_final_quantization():
    result = result_for(LOW_RECORD, HIGH_RECORD)
    assert result.requested_weight_total == d("1.000000")
    assert result.independence_allocated_weight_total == d("1.000000")
    assert result.effective_weight_total == d("1.000000")
    assert result.arithmetic_record_count == 2
    assert result.arithmetic_probability_yes == d("0.620000")

def test_diagnostic_and_arithmetic_universes_have_exact_counts_and_weights():
    duplicate = recapture(LOW_RECORD, stem="a-low-later", captured_offset=56)
    noncurrent = root_record("d-noncurrent")
    mixed_result = build(
        aggregation_input(
            (LOW_RECORD, duplicate, HIGH_RECORD, STALE_RECORD, noncurrent),
            current_records=(LOW_RECORD, HIGH_RECORD, STALE_RECORD)), config=config())
    assert mixed_result.diagnostic_record_count == 5
    assert mixed_result.arithmetic_record_count == 2
    assert tuple(row.disposition for row in mixed_result.diagnostics) == (
        "included", "duplicate_capture", "included", "stale", "not_current_revision")
    assert mixed_result.effective_weight_total == sum(
        (row.effective_weight for row in mixed_result.diagnostics
         if row.disposition == "included"), d("0.000000"))

def test_probability_is_canonical_pyes_without_complement_prior_market_or_log_odds():
    record = root_record("solo-complement", probability_yes=d("0.200000"), requested_weight=d("0.500000"))
    canonical_result = result_for(record)
    assert canonical_result.arithmetic_probability_yes == d("0.200000")
    assert canonical_result.arithmetic_probability_yes != d("0.800000")

def test_weighted_probability_does_not_quantize_products_before_sum():
    one = root_record("q-one", probability_yes=d("0.000001"), requested_weight=d("0.500000"))
    two = root_record("q-two", probability_yes=d("0.000001"), requested_weight=d("0.500000"))
    result = result_for(one, two)
    assert result.arithmetic_probability_yes == d("0.000001")

def test_hostile_ambient_decimal_context_preserves_result_payload_and_digest():
    baseline = result_for(LOW_RECORD, HIGH_RECORD, config_value=config_value)
    baseline_payload = team_evidence_aggregation_payload(baseline)
    baseline_digest = baseline.core_digest
    context = getcontext()
    saved_prec, saved_rounding, saved_traps = (
        context.prec, context.rounding, dict(context.traps))
    try:
        context.prec = 6
        context.rounding = ROUND_UP
        context.traps[Inexact] = True
        hostile = result_for(LOW_RECORD, HIGH_RECORD, config_value=config_value)
    finally:
        context.prec, context.rounding = saved_prec, saved_rounding
        for key, value in saved_traps.items():
            context.traps[key] = value
    assert hostile == baseline
    assert team_evidence_aggregation_payload(hostile) == baseline_payload
    assert hostile.core_digest == baseline_digest

# Task 3.2: contradiction boundary tests.
def test_one_sided_support_has_no_contradiction_even_when_watch_threshold_is_zero():
    yes = root_record("one-sided-yes", probability_yes=d("0.750000"), requested_weight=d("0.700000"))
    neutral = root_record("one-sided-neutral", probability_yes=d("0.500000"), requested_weight=d("0.300000"))
    one_sided_result = result_for(
        yes, neutral, config_value=config(contradiction_watch_score=d("0.000000")))
    assert one_sided_result.contradiction == TeamEvidenceContradictionResult(
        yes_support_weight=d("0.700000"), no_support_weight=d("0.000000"),
        neutral_weight=d("0.300000"), contradiction_score=d("0.000000"), status="none")

CONTRADICTION_BOUNDARY_CASES = (
    (d("0.700000"), d("0.100000"), d("0.250000"), "watch"),
    (d("0.500000"), d("0.300000"), d("0.750000"), "blocked"),
)

@pytest.mark.parametrize(
    ("yes_weight", "no_weight", "expected_score", "expected_status"), CONTRADICTION_BOUNDARY_CASES)
def test_contradiction_thresholds_are_inclusive_and_block_is_checked_first(
    yes_weight, no_weight, expected_score, expected_status):
    yes = root_record("boundary-yes", probability_yes=d("0.750000"), requested_weight=yes_weight)
    no = root_record("boundary-no", probability_yes=d("0.250000"), requested_weight=no_weight)
    boundary_result = result_for(yes, no)
    assert boundary_result.contradiction.contradiction_score == expected_score
    assert boundary_result.contradiction.status == expected_status

def test_neutral_weight_is_reported_but_does_not_dilute_opposing_support():
    yes = root_record("neutral-yes", probability_yes=d("0.750000"), requested_weight=d("0.100000"))
    no = root_record("neutral-no", probability_yes=d("0.250000"), requested_weight=d("0.100000"))
    neutral = root_record("neutral-mid", probability_yes=d("0.500000"), requested_weight=d("0.900000"))
    neutral_result = result_for(yes, no, neutral)
    assert neutral_result.contradiction.neutral_weight == d("0.900000")
    assert neutral_result.contradiction.contradiction_score == d("1.000000")

# Task 3.3: readiness precedence, exact reasons, and publication.
STATUS_REASON_CASES = (
    ("no_arithmetic_plus_block_and_watch_requirements", "blocked",
     ("blocking_requirement_unmet", "no_arithmetic_evidence", "watch_requirement_unmet")),
    ("contradiction_blocked_plus_watch_requirement", "blocked",
     ("contradiction_blocked", "watch_requirement_unmet")),
    ("blocking_requirement_plus_contradiction_watch", "blocked",
     ("blocking_requirement_unmet", "contradiction_watch")),
    ("watch_requirement_plus_contradiction_watch", "watch",
     ("contradiction_watch", "watch_requirement_unmet")),
)

@pytest.mark.parametrize(
    ("scenario", "expected_status", "expected_reasons"),
    STATUS_REASON_CASES, ids=[row[0] for row in STATUS_REASON_CASES])
def test_status_precedence_and_mixed_reason_tuples_are_exact(
    scenario, expected_status, expected_reasons):
    if scenario == "no_arithmetic_plus_block_and_watch_requirements":
        value = aggregation_input((STALE_RECORD,), current_records=(STALE_RECORD,))
        config_for_case = config(requirements=(BLOCKED_REQUIREMENT, WATCH_REQUIREMENT))
    else:
        blocked_scenario = scenario == "contradiction_blocked_plus_watch_requirement"
        yes_weight, no_weight = (
            (d("0.500000"), d("0.300000")) if blocked_scenario else (d("0.700000"), d("0.100000")))
        yes = root_record("s-yes", probability_yes=d("0.750000"), requested_weight=yes_weight)
        no = root_record("s-no", probability_yes=d("0.250000"), requested_weight=no_weight)
        value = aggregation_input((yes, no), current_records=(yes, no))
        unmet = (BLOCKED_REQUIREMENT if scenario == "blocking_requirement_plus_contradiction_watch"
                 else WATCH_REQUIREMENT)
        config_for_case = config(requirements=(unmet,))
    result = build(value, config=config_for_case)
    assert result.status == expected_status
    assert result.reason_codes == expected_reasons
    assert result.publishable_probability_yes is None

READY_PUBLICATION_CASES = (
    (d("0.050000"), d("0.110000"), ("aggregation_ready", "publish_probability_floor_applied")),
    (d("0.950000"), d("0.890000"), ("aggregation_ready", "publish_probability_ceiling_applied")),
    (d("0.110000"), d("0.110000"), ("aggregation_ready",)),
    (d("0.890000"), d("0.890000"), ("aggregation_ready",)),
    (d("0.500000"), d("0.500000"), ("aggregation_ready",)),
)

@pytest.mark.parametrize(
    ("probability", "expected_publishable", "expected_reasons"), READY_PUBLICATION_CASES)
def test_ready_publication_uses_only_supplied_nonbtc_bounds(
    probability, expected_publishable, expected_reasons):
    record = root_record("publish", probability_yes=probability, requested_weight=d("1.000000"))
    result = result_for(record)
    assert result.status == "ready"
    assert result.arithmetic_probability_yes == probability
    assert result.publishable_probability_yes == expected_publishable
    assert result.reason_codes == expected_reasons

def test_nonready_result_retains_arithmetic_probability_but_never_publishes():
    yes = root_record("n-yes", probability_yes=d("0.750000"), requested_weight=d("0.700000"))
    no = root_record("n-no", probability_yes=d("0.250000"), requested_weight=d("0.100000"))
    result = result_for(yes, no, config_value=config(requirements=(WATCH_REQUIREMENT,)))
    assert result.status == "watch"
    assert result.arithmetic_probability_yes == d("0.687500")
    assert result.publishable_probability_yes is None

def test_empty_input_is_typed_blocked_no_arithmetic_result():
    result = build(
        aggregation_input((), current_records=()),
        config=config(requirements=(BLOCKED_REQUIREMENT, WATCH_REQUIREMENT)))
    assert result.diagnostic_record_count == 0
    assert result.arithmetic_record_count == 0
    assert result.requested_weight_total == d("0.000000")
    assert result.independence_allocated_weight_total == d("0.000000")
    assert result.effective_weight_total == d("0.000000")
    assert result.arithmetic_probability_yes is None
    assert result.publishable_probability_yes is None
    assert result.contradiction == TeamEvidenceContradictionResult(
        yes_support_weight=d("0.000000"), no_support_weight=d("0.000000"),
        neutral_weight=d("0.000000"), contradiction_score=d("0.000000"), status="none")
    assert tuple(row.requirement_id for row in result.requirement_coverage) == (
        "req:blocked", "req:watch")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "blocking_requirement_unmet", "no_arithmetic_evidence", "watch_requirement_unmet")

def test_all_excluded_input_is_blocked_without_erasing_diagnostics():
    excluded_duplicate = recapture(STALE_RECORD, stem="c-stale-later", captured_offset=41)
    excluded_noncurrent = root_record("ex-noncurrent")
    result = build(
        aggregation_input(
            (STALE_RECORD, excluded_duplicate, excluded_noncurrent),
            current_records=(STALE_RECORD,)), config=config())
    assert result.diagnostic_record_count == 3
    assert len(result.diagnostics) == 3
    assert result.arithmetic_record_count == 0
    assert result.status == "blocked"
    assert "no_arithmetic_evidence" in result.reason_codes
    assert result.publishable_probability_yes is None

def test_result_contains_exactly_one_coverage_row_per_config_requirement():
    assigned = root_record("cov-assigned", requirement_ids=("req:alpha",), requested_weight=d("0.400000"))
    config_for_coverage = config(
        requirements=(requirement("req:alpha"), requirement("req:beta"), requirement("req:gamma")))
    result = result_for(assigned, config_value=config_for_coverage)
    assert tuple(row.requirement_id for row in result.requirement_coverage) == tuple(
        item.requirement_id for item in config_for_coverage.requirements)
    rows = {row.requirement_id: row for row in result.requirement_coverage}
    assert rows["req:alpha"].assigned_witness_count == 1
    assert rows["req:alpha"].satisfied is True
    assert rows["req:beta"].assigned_witness_count == 0
    assert rows["req:beta"].satisfied is False
    assert rows["req:gamma"].witnesses == ()

def test_zero_candidate_requirement_preserves_every_configured_coverage_field():
    assigned = root_record("cov-zero-assigned", requirement_ids=("req:assigned",), requested_weight=d("0.500000"))
    orphan = requirement(
        "req:orphan", minimum_witness_count=2, minimum_effective_weight=d("0.100000"),
        unmet_status="blocked")
    result = result_for(
        assigned, config_value=config(requirements=(orphan, requirement("req:assigned"))))
    row = next(
        item for item in result.requirement_coverage if item.requirement_id == "req:orphan")
    assert row.minimum_witness_count == 2
    assert row.minimum_effective_weight == d("0.100000")
    assert row.unmet_status == "blocked"
    assert row.assigned_witness_count == 0
    assert row.satisfied is False
    assert row.witnesses == ()

# Task 4.1: rematerialization and tamper tests (constructor-bypass forgery).
def test_result_validator_returns_exact_none_for_builder_result():
    result = build(input_value, config=config_value)
    assert validate(result, aggregation_input=input_value, config=config_value) is None

@pytest.mark.parametrize(
    "field_change",
    (
        {"status": "watch"}, {"diagnostic_record_count": 999},
        {"arithmetic_probability_yes": d("0.123456")},
        {"publishable_probability_yes": None},
        {"reason_codes": ("aggregation_ready", "contradiction_watch")},
        {"core_digest": "f" * 64}, {"config_digest": "e" * 64},
    ),
)
def test_result_validator_rejects_every_tampered_top_level_field(field_change):
    result = build(input_value, config=config_value)
    with pytest.raises(ValueError, match=MISMATCH):
        validate(forge_result(result, field_change), aggregation_input=input_value, config=config_value)

def test_result_validator_rejects_tampered_nested_contradiction():
    result = build(input_value, config=config_value)
    tampered = forge_result(result, {"contradiction": replace(result.contradiction, status="watch")})
    with pytest.raises(ValueError, match=MISMATCH):
        validate(tampered, aggregation_input=input_value, config=config_value)

def test_result_validator_rejects_tampered_diagnostic():
    result = build(input_value, config=config_value)
    tampered_row = replace(result.diagnostics[0], disposition="not_current_revision")
    with pytest.raises(ValueError, match=MISMATCH):
        validate(forge_result(result, {"diagnostics": (tampered_row,)}), aggregation_input=input_value, config=config_value)

def test_result_validator_rejects_missing_extra_duplicate_or_reordered_requirement_coverage():
    config_for_coverage = config(requirements=(BLOCKED_REQUIREMENT, WATCH_REQUIREMENT))
    result = build(input_value, config=config_for_coverage)
    first, second = result.requirement_coverage
    extra_row = TeamEvidenceRequirementCoverage(
        requirement_id="req:extra", minimum_witness_count=1, assigned_witness_count=0,
        minimum_effective_weight=d("0.000000"), unmet_status="watch", satisfied=False, witnesses=())
    for tampered_coverage in ((second,), (first, second, extra_row), (first, first), (second, first)):
        with pytest.raises(ValueError, match=MISMATCH):
            validate(
                forge_result(result, {"requirement_coverage": tampered_coverage}),
                aggregation_input=input_value, config=config_for_coverage)

def test_result_validator_rejects_wrong_exact_result_type_and_constructor_bypass():
    result = build(input_value, config=config_value)
    with pytest.raises(ValueError, match="result must be exactly TeamEvidenceAggregationResult"):
        validate(input_value, aggregation_input=input_value, config=config_value)
    with pytest.raises(ValueError, match=MISMATCH):
        validate(
            forge_result(result, {"reason_codes": MISSING}),
            aggregation_input=input_value, config=config_value)

def test_result_validator_rejects_constructor_bypassed_snan_with_stable_mismatch_error():
    result = build(input_value, config=config_value)
    with pytest.raises(ValueError, match=MISMATCH):
        validate(
            forge_result(result, {"effective_weight_total": Decimal("sNaN")}),
            aggregation_input=input_value, config=config_value)

def test_validator_rejections_preserve_caller_decimal_context_flags_and_traps():
    """Every validator rejection path leaves the caller's Decimal context
    (flags such as Inexact/Rounded/InvalidOperation/DivisionByZero, traps,
    precision, rounding) exactly as it was before the rejected call."""
    result = build(input_value, config=config_value)
    nan_row = forge_result(result.diagnostics[0], {"probability_yes": Decimal("sNaN")})
    for changes in (
        {"publishable_probability_yes": Decimal("sNaN")},
        {"effective_weight_total": Decimal("sNaN")}, {"requested_weight_total": Decimal("NaN")},
        {"diagnostics": (nan_row,)},
        {"arithmetic_probability_yes": d("0.123456")}, {"status": "watch"},
        {"core_digest": "f" * 64}, {"reason_codes": MISSING},
    ):
        state = context_state()
        with pytest.raises(ValueError, match=MISMATCH):
            validate(
                forge_result(result, changes), aggregation_input=input_value,
                config=config_value)
        assert_context_state_unchanged(state)
def test_builder_config_digest_equals_exact_codec_digest():
    result = build(input_value, config=config_value)
    assert result.config_digest == team_evidence_aggregation_config_digest(config_value)

def test_builder_core_digest_equals_exact_codec_digest():
    result = build(input_value, config=config_value)
    assert result.core_digest == team_evidence_aggregation_core_digest(result)
    assert validate_team_evidence_aggregation_core_digest(result) is None

def test_core_digest_changes_when_any_semantic_result_field_changes():
    result = build(input_value, config=config_value)
    changed_input = aggregation_input(
        (root_record("alpha", probability_yes=d("0.610000")),), current_records=(BASE_RECORD,))
    changed_probability = build(changed_input, config=config_value)
    assert changed_probability.core_digest != result.core_digest
    for changes in (
        {"status": "watch"}, {"publishable_probability_yes": None},
        {"reason_codes": ("aggregation_ready", "contradiction_watch")},
    ):
        assert team_evidence_aggregation_core_digest(forge_result(result, changes)) != result.core_digest

def test_semantic_tuple_permutations_produce_equal_results_payloads_and_digests():
    one = root_record("perm-one", requirement_ids=("req:core",), probability_yes=d("0.300000"), requested_weight=d("0.400000"))
    two = root_record("perm-two", requirement_ids=("req:core",), probability_yes=d("0.600000"), requested_weight=d("0.600000"))
    config_for_perm = config(requirements=(CORE_REQUIREMENT,))
    result_one = result_for(one, two, config_value=config_for_perm)
    result_two = result_for(two, one, config_value=config_for_perm)
    assert result_one == result_two
    assert team_evidence_aggregation_payload(result_one) == (
        team_evidence_aggregation_payload(result_two))
    assert result_one.core_digest == result_two.core_digest
