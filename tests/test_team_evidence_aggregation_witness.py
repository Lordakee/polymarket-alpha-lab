from __future__ import annotations
import ast
from dataclasses import fields
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from itertools import permutations, product
from pathlib import Path
import re
from typing import cast
from unittest.mock import Mock
import pytest
import polymarket_alpha_lab.team_evidence_aggregation_witness as witness_module
from polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig, TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision, TeamEvidenceCapture, TeamEvidenceRequirement,
    TeamEvidenceRequirementCoverage, TeamEvidenceRequirementWitness,
    TeamEvidenceRevision, TeamEvidenceSourceLineage, TeamEvidenceWeightAllocation,
)
from polymarket_alpha_lab.team_evidence_aggregation_witness import build_team_evidence_requirement_coverage
FRESHNESS_ANCHOR_AT = datetime(2026, 7, 13, 12, 0, tzinfo=UTC); CAPTURED_AT = datetime(2026, 7, 13, 12, 1, tzinfo=UTC); RECORDED_AT = datetime(2026, 7, 13, 12, 2, tzinfo=UTC); ASSESSED_AT = datetime(2026, 7, 13, 12, 3, tzinfo=UTC)
ZERO = Decimal("0.000000")
def _digest(seed: str) -> str:
    return format(sum((index + 1) * ord(char) for index, char in enumerate(seed)), "064x")
def _requirement(requirement_id: str, *, count: int = 1,
                 weight: Decimal = Decimal("0.005000"),
                 status: str = "blocked") -> TeamEvidenceRequirement:
    return TeamEvidenceRequirement(
        requirement_id=requirement_id, minimum_witness_count=count,
        minimum_effective_weight=weight, unmet_status=status,
    )
def _config(requirements: tuple[TeamEvidenceRequirement, ...] = (),
            **changes: object) -> TeamEvidenceAggregationConfig:
    values: dict[str, object] = {
        "config_version": "witness-v1",
        "max_evidence_age_seconds": Decimal("3600.000000"),
        "max_capture_lag_seconds": Decimal("300.000000"),
        "independence_group_weight_cap": Decimal("1.000000"),
        "correlation_group_weight_cap": Decimal("1.000000"),
        "max_requirement_assignments_per_evidence": 32,
        "contradiction_no_probability_max": Decimal("0.250000"),
        "contradiction_yes_probability_min": Decimal("0.750000"),
        "contradiction_watch_score": Decimal("0.250000"),
        "contradiction_block_score": Decimal("0.750000"),
        "publish_probability_floor": Decimal("0.110000"),
        "publish_probability_ceiling": Decimal("0.890000"),
        "maximum_records": 128,
        "maximum_requirements": 32,
        "maximum_requirement_memberships": 1024,
        "maximum_witness_edges": 256,
        "requirements": requirements,
    }
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)
def _record(suffix: str, *, requirement_ids: tuple[str, ...] = (),
            requested_weight: Decimal = Decimal("0.010000"),
            assessment_suffix: str | None = None, independence_key: str | None = None,
            correlation_key: str | None = None, captured_at: datetime = CAPTURED_AT) -> TeamEvidenceAggregationRecord:
    assessment_suffix = assessment_suffix or suffix
    source_id = f"source-{suffix}"
    source_digest = _digest(source_id)
    content_digest = _digest(f"content-{suffix}")
    evidence_id = f"evidence-{suffix}"
    evidence_digest = _digest(evidence_id)
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(source_lineage_id=source_id, source_lineage_digest=source_digest),
        capture=TeamEvidenceCapture(
            capture_id=f"capture-{suffix}", capture_digest=_digest(f"capture-{suffix}"),
            source_lineage_id=source_id, source_lineage_digest=source_digest,
            content_digest=content_digest, captured_at=captured_at,
        ),
        evidence_revision=TeamEvidenceRevision(
            evidence_revision_id=evidence_id, evidence_revision_digest=evidence_digest,
            previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
            source_lineage_id=source_id, source_lineage_digest=source_digest,
            content_digest=content_digest, requirement_ids=requirement_ids,
            freshness_anchor_at=FRESHNESS_ANCHOR_AT, recorded_at=RECORDED_AT,
        ),
        assessment_revision=TeamEvidenceAssessmentRevision(
            assessment_revision_id=f"assessment-{assessment_suffix}",
            assessment_revision_digest=_digest(f"assessment-{assessment_suffix}"),
            previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
            evidence_revision_id=evidence_id, evidence_revision_digest=evidence_digest,
            assessed_at=ASSESSED_AT, probability_yes=Decimal("0.500000"), requested_weight=requested_weight,
            rationale_digest=_digest(f"rationale-{assessment_suffix}"),
            independence_key=independence_key or f"independence-{assessment_suffix}",
            correlation_key=correlation_key or f"correlation-{assessment_suffix}",
        ),
    )
def _copy(value: object, field_name: str, replacement: object) -> object:
    copied = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(copied, field.name, replacement if field.name == field_name else getattr(value, field.name))
    return copied
def _rebuild(value: object, **changes: object) -> object:
    return type(value)(**{field.name: changes.get(field.name, getattr(value, field.name)) for field in fields(value)})
def _replace_layer(record: TeamEvidenceAggregationRecord, layer_name: str,
                   field_name: str, replacement: object) -> TeamEvidenceAggregationRecord:
    layer = _copy(getattr(record, layer_name), field_name, replacement)
    return cast(TeamEvidenceAggregationRecord, _copy(record, layer_name, layer))
def _allocations(records: tuple[TeamEvidenceAggregationRecord, ...],
                 config: TeamEvidenceAggregationConfig) -> tuple[TeamEvidenceWeightAllocation, ...]:
    return allocate_team_evidence_weights(records, config=config)
def _build(records: tuple[TeamEvidenceAggregationRecord, ...],
           config: TeamEvidenceAggregationConfig) -> tuple[TeamEvidenceRequirementCoverage, ...]:
    return build_team_evidence_requirement_coverage(records, _allocations(records, config), config=config)
def _coverage_edges(coverage: tuple[TeamEvidenceRequirementCoverage, ...]) -> tuple[tuple[str, str, str, str, str], ...]:
    return tuple(sorted(
        (witness.requirement_id, witness.source_lineage_id, witness.evidence_revision_id,
         witness.assessment_revision_id, witness.capture_id)
        for row in coverage for witness in row.witnesses
    ))
def _reject(message: str, records: object, allocations: object, config: object) -> None:
    with pytest.raises(ValueError, match=rf"^{re.escape(message)}$"):
        build_team_evidence_requirement_coverage(records, allocations, config=config)  # type: ignore[arg-type]
def test_witness_threshold_is_inclusive_and_rows_are_sorted_for_every_requirement() -> None:
    requirement_a = _requirement("requirement-a", count=2, weight=Decimal("0.010000"))
    requirement_z = _requirement(
        "requirement-z", weight=Decimal("0.010000"), status="watch"
    )
    config = _config((requirement_z, requirement_a))
    records = (
        _record("b", requirement_ids=("requirement-a",)),
        _record("a", requirement_ids=("requirement-a",)),
    )
    coverage = _build(records, config)
    assert tuple(row.requirement_id for row in coverage) == ("requirement-a", "requirement-z")
    assert (
        coverage[0].minimum_witness_count,
        coverage[0].minimum_effective_weight,
        coverage[0].unmet_status,
        coverage[0].assigned_witness_count,
        coverage[0].satisfied,
    ) == (2, Decimal("0.010000"), "blocked", 2, True)
    assert tuple(witness.source_lineage_id for witness in coverage[0].witnesses) == (
        "source-a", "source-b"
    )
    assert all(
        type(witness) is TeamEvidenceRequirementWitness
        and witness.effective_weight == Decimal("0.010000")
        and witness.paper_only is witness.report_only is witness.readonly is True
        for witness in coverage[0].witnesses
    )
    assert (
        coverage[1].minimum_witness_count,
        coverage[1].minimum_effective_weight,
        coverage[1].unmet_status,
        coverage[1].assigned_witness_count,
        coverage[1].witnesses,
        coverage[1].satisfied,
    ) == (1, Decimal("0.010000"), "watch", 0, (), False)
    assert tuple(row.assigned_witness_count for row in _build((), config)) == (0, 0) and _build((_record("unscoped"),), _config()) == ()
def test_zero_minimum_effective_weight_threshold_accepts_only_positive_effective_rows() -> None:
    requirement = _requirement("requirement-a", weight=ZERO)
    config = _config(
        (requirement,), independence_group_weight_cap=Decimal("0.000001")
    )
    records = tuple(
        _record(
            suffix,
            requirement_ids=("requirement-a",),
            requested_weight=Decimal("0.000001"),
            independence_key="independence-shared",
        )
        for suffix in ("a", "b")
    )
    allocations = _allocations(records, config)
    assert tuple(row.effective_weight for row in allocations) == (Decimal("0.000001"), ZERO)
    coverage = build_team_evidence_requirement_coverage(records, allocations, config=config)
    assert coverage[0].assigned_witness_count == 1
    assert tuple((row.source_lineage_id, row.effective_weight) for row in coverage[0].witnesses) == (
        ("source-a", Decimal("0.000001")),
    )
def test_witness_enforces_evidence_assignment_and_requirement_independence_capacities() -> None:
    requirements = (_requirement("requirement-a"), _requirement("requirement-b"))
    config = _config(requirements, max_requirement_assignments_per_evidence=1)
    coverage = _build(
        (_record("only", requirement_ids=("requirement-b", "requirement-a")),), config
    )
    assert tuple(row.assigned_witness_count for row in coverage) == (1, 0)
    shared = tuple(
        _record(
            suffix,
            requirement_ids=("requirement-a",),
            independence_key="independence-shared",
        )
        for suffix in ("a", "b")
    )
    coverage = _build(shared, _config((_requirement("requirement-a", count=2),)))
    assert coverage[0].assigned_witness_count == 1
    assert coverage[0].satisfied is False
    assert coverage[0].witnesses[0].source_lineage_id == "source-a"
def test_global_matching_solves_the_greedy_counterexample() -> None:
    config = _config(
        (_requirement("requirement-a"), _requirement("requirement-b")),
        max_requirement_assignments_per_evidence=1,
    )
    records = (
        _record("flexible", requirement_ids=("requirement-a", "requirement-b")),
        _record("a-only", requirement_ids=("requirement-a",)),
    )
    coverage = _build(records, config)
    assert _coverage_edges(coverage) == (
        ("requirement-a", "source-a-only", "evidence-a-only", "assessment-a-only", "capture-a-only"),
        ("requirement-b", "source-flexible", "evidence-flexible", "assessment-flexible", "capture-flexible"),
    )
    assert all(row.satisfied for row in coverage)
def test_partial_coverage_preserves_explicit_watch_and_blocked_policy() -> None:
    requirements = (
        _requirement("requirement-blocked", count=3, status="blocked"),
        _requirement("requirement-watch", count=2, status="watch"),
    )
    records = (
        _record("blocked", requirement_ids=("requirement-blocked",)),
        _record("watch", requirement_ids=("requirement-watch",)),
    )
    coverage = _build(records, _config(requirements))
    assert tuple((row.requirement_id, row.assigned_witness_count, row.satisfied, row.unmet_status) for row in coverage) == (
        ("requirement-blocked", 1, False, "blocked"),
        ("requirement-watch", 1, False, "watch"),
    )
def test_blocked_assignments_have_priority_over_lexically_earlier_watch_edges() -> None:
    requirements = (
        _requirement("source", status="watch"),
        _requirement("watch", status="blocked"),
    )
    config = _config(requirements, max_requirement_assignments_per_evidence=1)
    coverage = _build(
        (_record("only", requirement_ids=("source", "watch"), independence_key="blocked", correlation_key="sink"),), config
    )
    assert tuple(row.assigned_witness_count for row in coverage) == (0, 1)
def test_severity_optimum_uses_the_lexically_smallest_edge_set() -> None:
    requirements = (_requirement("requirement-a"), _requirement("requirement-b"))
    records = tuple(
        _record(suffix, requirement_ids=("requirement-a", "requirement-b"))
        for suffix in ("a", "b")
    )
    coverage = _build(records, _config(requirements, max_requirement_assignments_per_evidence=1))
    assert tuple((edge[0], edge[1]) for edge in _coverage_edges(coverage)) == (
        ("requirement-a", "source-a"), ("requirement-b", "source-b")
    )
def test_assignment_objective_does_not_maximize_fully_satisfied_requirements() -> None:
    requirements = (
        _requirement("requirement-a", count=10**10000),
        _requirement("requirement-b", count=1),
    )
    config = _config(requirements, max_requirement_assignments_per_evidence=1)
    coverage = _build(
        (_record("only", requirement_ids=("requirement-a", "requirement-b")),), config
    )
    assert tuple((row.assigned_witness_count, row.satisfied) for row in coverage) == (
        (1, False), (0, False)
    )
    assert coverage[0].minimum_witness_count == 10**10000
def test_witness_recomputes_and_requires_the_exact_canonical_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = tuple(
        _record(suffix, requirement_ids=("requirement-a",)) for suffix in ("a", "b")
    )
    config = _config((_requirement("requirement-a", count=2),))
    canonical = _allocations(records, config)
    calls: list[tuple[object, object]] = []
    def spy(value: object, *, config: object) -> tuple[TeamEvidenceWeightAllocation, ...]:
        calls.append((value, config))
        return allocate_team_evidence_weights(value, config=config)  # type: ignore[arg-type]
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", spy)
    assert build_team_evidence_requirement_coverage(records, canonical, config=config)
    extra = _allocations((_record("extra"),), config)[0]
    altered = cast(
        TeamEvidenceWeightAllocation,
        _rebuild(canonical[0], effective_weight=Decimal("0.009999")),
    )
    bad_values = (
        canonical[:-1],
        canonical + (canonical[0],),
        canonical + (extra,),
        tuple(reversed(canonical)),
        (altered, canonical[1]),
    )
    for bad in bad_values:
        _reject(
            "allocations must equal canonical recomputation for allocation_input_records",
            records,
            bad,
            config,
        )
    assert len(calls) == 3
    assert all(value is records and received is config for value, received in calls)
def test_witness_rejects_join_and_assessment_projection_mismatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _record("a", requirement_ids=("requirement-a",))
    records = (record,)
    config = _config((_requirement("requirement-a"),))
    allocation = _allocations(records, config)[0]
    monkeypatch.setattr(
        witness_module,
        "_build_candidate_edges",
        lambda *args, **kwargs: pytest.fail("candidate construction was reached"),
    )
    cases = (
        ("source_lineage_id", "source-other", "record/allocation join keys must match exactly"),
        ("capture_id", "capture-other", "record/allocation join keys must match exactly"),
        ("evidence_revision_id", "evidence-other", "record/allocation join keys must match exactly"),
        ("assessment_revision_id", "assessment-other", "record/allocation join keys must match exactly"),
        ("independence_key", "independence-other", "allocation.independence_key must match assessment_revision.independence_key"),
        ("correlation_key", "correlation-other", "allocation.correlation_key must match assessment_revision.correlation_key"),
        ("requested_weight", Decimal("0.011000"), "allocation.requested_weight must match assessment_revision.requested_weight"),
    )
    for field_name, replacement, message in cases:
        bad = (cast(TeamEvidenceWeightAllocation, _rebuild(allocation, **{field_name: replacement})),)
        def canonical(*args: object, result: tuple[TeamEvidenceWeightAllocation, ...] = bad, **kwargs: object) -> tuple[TeamEvidenceWeightAllocation, ...]:
            return result
        monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", canonical)
        _reject(message, records, bad, config)
    duplicate_records = (record, _record("a", requirement_ids=("requirement-a",), captured_at=CAPTURED_AT + timedelta(seconds=1)))
    duplicate_allocations = _allocations(duplicate_records, config)
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", lambda *args, **kwargs: duplicate_allocations)
    _reject("record/allocation join keys must match exactly", duplicate_records, duplicate_allocations, config)
def test_candidate_edge_resource_bound_is_checked_before_graph_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirements = (_requirement("requirement-a"), _requirement("requirement-b"))
    record = _record("a", requirement_ids=("requirement-a", "requirement-b"))
    passing = _config(requirements, maximum_witness_edges=2)
    assert sum(row.assigned_witness_count for row in _build((record,), passing)) == 2
    failing = _config(requirements, maximum_witness_edges=1)
    allocations = _allocations((record,), failing)
    monkeypatch.setattr(
        witness_module,
        "_Dinic",
        lambda *args, **kwargs: pytest.fail("matching graph was constructed"),
    )
    _reject(
        "candidate witness edge count exceeds config.maximum_witness_edges",
        (record,), allocations, failing,
    )
def test_membership_count_deduplicates_repeated_evidence_revision_projections(monkeypatch: pytest.MonkeyPatch) -> None:
    requirement_ids = tuple(f"requirement-{index:02d}" for index in range(32))
    requirements = tuple(_requirement(requirement_id, weight=Decimal("0.020000")) for requirement_id in requirement_ids)
    records = tuple(
        _record(
            f"revision-{index:02d}",
            assessment_suffix=f"revision-{index:02d}-{assessment}",
            requirement_ids=requirement_ids,
        )
        for index in range(32)
        for assessment in ("a", "b")
    )
    coverage = _build(records, _config(requirements))
    assert len(coverage) == 32; assert all(row.assigned_witness_count == 0 and row.witnesses == () for row in coverage)
    tight_records = (_record("tight", requirement_ids=requirement_ids[:2]),); tight_config = _config(requirements, maximum_requirement_memberships=1)
    _reject("distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024", tight_records, _allocations(tight_records, tight_config), tight_config)
    conflict_config = _config(requirements); conflict = (_record("conflict", assessment_suffix="conflict-a", requirement_ids=requirement_ids[:1]), _record("conflict", assessment_suffix="conflict-b", requirement_ids=requirement_ids[1:2]))
    conflict_allocations = _allocations(conflict, conflict_config)
    base = _record("assessment-conflict", requirement_ids=("requirement-00",))
    fork = cast(TeamEvidenceAggregationRecord, _rebuild(base, capture=_rebuild(base.capture, capture_id="capture-fork", capture_digest=_digest("capture-fork")), assessment_revision=_rebuild(base.assessment_revision, independence_key="independence-fork")))
    assessment_conflict = (base, fork); assessment_allocations = _allocations(assessment_conflict, conflict_config)
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", lambda *args, **kwargs: pytest.fail("allocation recomputation was reached"))
    _reject("repeated evidence revision identity must have one exact projection", conflict, conflict_allocations, conflict_config)
    _reject("repeated assessment revision identity must have one exact projection", assessment_conflict, assessment_allocations, conflict_config)
def test_witness_assignment_capacity_is_per_record_join_not_evidence_revision() -> None:
    records = tuple(
        _record(
            "shared", assessment_suffix=f"shared-{suffix}",
            requirement_ids=("requirement-a",), requested_weight=weight,
            independence_key=f"independence-{suffix}", correlation_key="correlation-shared",
        )
        for suffix, weight in (("a", Decimal("0.010000")), ("b", Decimal("0.020000")))
    )
    config = _config((_requirement("requirement-a", count=2),), max_requirement_assignments_per_evidence=1)
    allocations = _allocations(records, config)
    assert tuple(row.correlation_key for row in allocations) == ("correlation-shared",) * 2
    coverage = build_team_evidence_requirement_coverage(records, allocations, config=config)
    assert (coverage[0].assigned_witness_count, coverage[0].satisfied) == (2, True)
    assert tuple(
        (row.source_lineage_id, row.capture_id, row.evidence_revision_id,
         row.assessment_revision_id, row.independence_key, row.effective_weight)
        for row in coverage[0].witnesses
    ) == (
        ("source-shared", "capture-shared", "evidence-shared", "assessment-shared-a", "independence-a", Decimal("0.010000")),
        ("source-shared", "capture-shared", "evidence-shared", "assessment-shared-b", "independence-b", Decimal("0.020000")),
    )
def test_33_by_32_threshold_filtered_memberships_fail_before_recomputation_or_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirement_ids = tuple(f"requirement-{index:02d}" for index in range(32))
    requirements = tuple(
        _requirement(requirement_id, weight=Decimal("0.020000"))
        for requirement_id in requirement_ids
    )
    records = tuple(
        _record(
            f"revision-{index:02d}",
            assessment_suffix=f"revision-{index:02d}-{assessment}",
            requirement_ids=requirement_ids,
        )
        for index in range(33)
        for assessment in ("a", "b")
    )
    config = _config(requirements)
    allocations = _allocations(records, config)
    sentinel = lambda *args, **kwargs: pytest.fail("post-membership work was reached")
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", sentinel)
    monkeypatch.setattr(witness_module, "_build_candidate_edges", sentinel)
    _reject(
        "distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024",
        records, allocations, config,
    )
@pytest.mark.parametrize(
    ("record_count", "allocation_count", "message"),
    ((2, 2, "records exceeds config.maximum_records"),
     (1, 0, "allocations must equal canonical recomputation for allocation_input_records"),
     (1, 2, "allocations must equal canonical recomputation for allocation_input_records")),
    ids=("record-overflow", "allocation-mismatch", "allocation-overflow"),
)
def test_cardinality_rejections_precede_record_and_allocation_element_work(record_count: int, allocation_count: int, message: str, monkeypatch: pytest.MonkeyPatch) -> None:
    hostile = object()
    records, allocations, config = (hostile,) * record_count, (hostile,) * allocation_count, _config(maximum_records=1)
    flags = Mock(wraps=witness_module._validate_hard_flags)
    post_cardinality = lambda *args, **kwargs: pytest.fail("post-cardinality element work was reached")
    monkeypatch.setattr(witness_module, "_validate_hard_flags", flags)
    monkeypatch.setattr(witness_module, "_canonical_reconstruction", post_cardinality)
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", post_cardinality)
    _reject(message, records, allocations, config)
    flags.assert_called_once_with("config", config)
def test_raw_requirement_membership_limit_precedes_record_reconstruction_and_recomputation(monkeypatch: pytest.MonkeyPatch) -> None:
    config, record = _config(maximum_requirement_memberships=1), _record("raw-memberships")
    allocations = _allocations((record,), config)
    oversized = _replace_layer(record, "evidence_revision", "requirement_ids", ("requirement-a", "requirement-b"))
    reconstruction = witness_module._canonical_reconstruction
    def guard(path: str, value: object) -> object:
        if path.startswith("allocation_input_records["):
            pytest.fail("record canonical reconstruction was reached")
        return reconstruction(path, value)
    monkeypatch.setattr(witness_module, "_canonical_reconstruction", guard)
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", lambda *args, **kwargs: pytest.fail("allocation recomputation was reached"))
    _reject("distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024",
            (oversized,), allocations, config)
@pytest.mark.parametrize(("layer_name", "field_name"), (
    ("capture", "captured_at"), ("evidence_revision", "freshness_anchor_at"),
    ("evidence_revision", "recorded_at"), ("assessment_revision", "assessed_at"),
))
def test_runtimeerror_from_datetime_offset_maps_to_stable_record_canonical_error_before_recomputation(layer_name: str, field_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    class RaisingOffset(tzinfo):
        def utcoffset(self, value: datetime | None) -> timedelta | None: raise RuntimeError("unsafe offset callback")
    config, record = _config(), _record("hostile-timezone")
    allocations = _allocations((record,), config)
    hostile = datetime(2026, 7, 13, 12, 1, tzinfo=RaisingOffset())
    malformed = _replace_layer(record, layer_name, field_name, hostile)
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", lambda *args, **kwargs: pytest.fail("allocation recomputation was reached"))
    _reject("allocation_input_records[0] must be canonical", (malformed,), allocations, config)
@pytest.mark.parametrize("hostile", (Decimal((0, (1,) + (0,) * 100_000, -100_002)),
                                     Decimal((0, (1,) * 100_000, -6)), Decimal("NaN")))
def test_hostile_decimal_rejects_for_each_owner_before_reconstruction_or_recomputation(hostile: Decimal, monkeypatch: pytest.MonkeyPatch) -> None:
    requirement = _requirement("requirement-a")
    config, record = _config((requirement,)), _record("hostile-decimal")
    records = (record,); allocations = _allocations(records, config)
    cases = (
        ("config must be canonical", records, allocations, _copy(config, "max_evidence_age_seconds", hostile)),
        ("config.requirements[0] must be canonical", records, allocations, _copy(config, "requirements", (_copy(requirement, "minimum_effective_weight", hostile),))),
        ("allocation_input_records[0] must be canonical", (_replace_layer(record, "assessment_revision", "requested_weight", hostile),), allocations, config),
        ("allocations[0] must be canonical", records, (_copy(allocations[0], "effective_weight", hostile),), config),
    )
    sentinel = lambda *args, **kwargs: pytest.fail("representation-sensitive reconstruction or recomputation was reached")
    monkeypatch.setattr(witness_module, "_canonical_reconstruction", sentinel)
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", sentinel)
    for message, bad_records, bad_allocations, bad_config in cases:
        _reject(message, bad_records, bad_allocations, bad_config)
def test_positive_effective_records_require_config_resident_requirement_ids() -> None:
    config = _config((_requirement("requirement-active", weight=ZERO),))
    positive = _record("positive", requirement_ids=("requirement-retired",))
    _reject(
        "positive-effective requirement ID must exist in config.requirements",
        (positive,), _allocations((positive,), config), config,
    )
    capped_config = _config(
        (_requirement("requirement-active", weight=ZERO),),
        independence_group_weight_cap=Decimal("0.000001"),
    )
    records = (
        _record(
            "a",
            requirement_ids=("requirement-active",),
            requested_weight=Decimal("0.000001"),
            independence_key="independence-shared",
        ),
        _record(
            "b",
            requirement_ids=("requirement-retired",),
            requested_weight=Decimal("0.000001"),
            independence_key="independence-shared",
        ),
    )
    coverage = _build(records, capped_config)
    assert tuple(row.requirement_id for row in coverage) == ("requirement-active",)
    assert coverage[0].assigned_witness_count == 1
def test_witness_is_input_requirement_and_adjacency_permutation_invariant() -> None:
    requirements = (_requirement("requirement-a"), _requirement("requirement-b"))
    baseline: tuple[TeamEvidenceRequirementCoverage, ...] | None = None
    memberships = ("requirement-a", "requirement-b")
    for record_order in permutations(("a", "b")):
        for requirement_order in permutations(requirements):
            for first_memberships in permutations(memberships):
                for second_memberships in permutations(memberships):
                    by_suffix = {
                        "a": _record("a", requirement_ids=first_memberships),
                        "b": _record("b", requirement_ids=second_memberships),
                    }
                    records = tuple(by_suffix[suffix] for suffix in record_order)
                    result = _build(records, _config(requirement_order, max_requirement_assignments_per_evidence=1))
                    baseline = result if baseline is None else baseline
                    assert result == baseline
def test_witness_rejects_wrong_types_hard_flags_and_resource_values(monkeypatch: pytest.MonkeyPatch) -> None:
    requirement = _requirement("requirement-a")
    config = _config((requirement,))
    record = _record("a", requirement_ids=("requirement-a",))
    records = (record,)
    allocations = _allocations(records, config)
    for bad in ([record], (item for item in records), type("TupleChild", (tuple,), {})(records)):
        _reject("allocation_input_records must be an exact tuple", bad, allocations, config)
    for bad in ([allocations[0]], (item for item in allocations)):
        _reject("allocations must be an exact tuple", records, bad, config)
    _reject("config must be exactly TeamEvidenceAggregationConfig", records, allocations, Mock(spec=config))
    _reject("allocation_input_records[0] must be exactly TeamEvidenceAggregationRecord", (Mock(spec=record),), allocations, config)
    _reject("allocations[0] must be exactly TeamEvidenceWeightAllocation", records, (Mock(spec=allocations[0]),), config)
    _reject("config.requirements[0] must be exactly TeamEvidenceRequirement", records, allocations, _copy(config, "requirements", (Mock(spec=requirement),)))
    _reject("allocation_input_records[0] must be canonical", (_copy(record, "source_lineage", object()),), (_copy(allocations[0], "paper_only", False),), config)
    maxima = {
        "max_requirement_assignments_per_evidence": 32,
        "maximum_records": 128,
        "maximum_requirements": 32,
        "maximum_requirement_memberships": 1024,
        "maximum_witness_edges": 256,
    }
    for field_name, maximum in maxima.items():
        for bad in (True, 0, Decimal("1.000000"), maximum + 1):
            _reject(
                f"config.{field_name} must be an exact int within its implementation maximum",
                records, allocations, _copy(config, field_name, bad),
            )
    flag_error = "must preserve paper_only=True, report_only=True, readonly=True"
    for flag in ("paper_only", "report_only", "readonly"):
        _reject(f"config.{flag} {flag_error}", records, allocations, _copy(config, flag, False))
        bad_req = _copy(requirement, flag, False)
        _reject(f"config.requirements[0].{flag} {flag_error}", records, allocations, _copy(config, "requirements", (bad_req,)))
        _reject(f"allocation_input_records[0].{flag} {flag_error}", (_copy(record, flag, False),), allocations, config)
        _reject(f"allocations[0].{flag} {flag_error}", records, (_copy(allocations[0], flag, False),), config)
        for layer in ("source_lineage", "capture", "evidence_revision", "assessment_revision"):
            bad_record = _replace_layer(record, layer, flag, False)
            _reject(f"allocation_input_records[0].{layer}.{flag} {flag_error}", (bad_record,), allocations, config)
    for field_name, bad in (
        ("requirement_id", []),
        ("minimum_witness_count", True),
        ("minimum_witness_count", 0),
        ("minimum_effective_weight", Decimal("0.01000")),
        ("minimum_effective_weight", True),
        ("unmet_status", "ignored"),
    ):
        bad_req = _copy(requirement, field_name, bad)
        _reject("config.requirements[0] must be canonical", records, allocations, _copy(config, "requirements", (bad_req,)))
    requirement_b = _requirement("requirement-b")
    _reject("config.requirements must contain exact unique requirements sorted by requirement_id", records, allocations, _copy(_copy(config, "maximum_requirements", 1), "requirements", (requirement, requirement_b)))
    for malformed in ((requirement_b, requirement), (requirement, requirement)):
        _reject(
            "config.requirements must contain exact unique requirements sorted by requirement_id",
            records, allocations, _copy(config, "requirements", malformed),
        )
    _reject("config must be canonical", records, allocations, _copy(config, "max_evidence_age_seconds", Decimal("3600.0")))
    bad_record = _replace_layer(record, "assessment_revision", "probability_yes", Decimal("0.50"))
    _reject("allocation_input_records[0] must be canonical", (bad_record,), allocations, config)
    noncanonical_utc = datetime(2026, 7, 13, 12, 1, tzinfo=timezone(timedelta(0), "zero"))
    bad_record = _replace_layer(record, "capture", "captured_at", noncanonical_utc)
    _reject("allocation_input_records[0] must be canonical", (bad_record,), allocations, config)
    _reject("allocation_input_records[0] must be canonical", (_replace_layer(record, "evidence_revision", "requirement_ids", ["requirement-a"]),), allocations, config)
    nested: object = "requirement-a"
    for _ in range(2_000): nested = (nested,)
    comparator = Mock(wraps=witness_module._canonical_equal); monkeypatch.setattr(witness_module, "_canonical_equal", comparator)
    nested_cases = (
        ("config must be canonical", records, allocations, _copy(config, "config_version", nested)), ("config.requirements[0] must be canonical", records, allocations, _copy(config, "requirements", (_copy(requirement, "requirement_id", nested),))), ("config.requirements[0] must be canonical", records, allocations, _copy(config, "requirements", (_copy(requirement, "minimum_witness_count", nested),))),
        ("allocation_input_records[0] must be canonical", (_replace_layer(record, "source_lineage", "source_lineage_id", nested),), allocations, config), ("allocations[0] must be canonical", records, (_copy(allocations[0], "source_lineage_id", nested),), config),
    )
    for args in nested_cases: comparator.reset_mock(); _reject(*args); assert sum(type(call.args[0]) is tuple for call in comparator.call_args_list) < 32
    _reject("allocations[0] must be canonical", records, (_copy(allocations[0], "effective_weight", Decimal("0.01000")),), config)
    overflow_config = _config((requirement,), maximum_records=1); _reject("records exceeds config.maximum_records", (record, _record("b", requirement_ids=("requirement-a",))), _allocations(records, overflow_config), overflow_config)
    sparse = object.__new__(TeamEvidenceAggregationRecord); [object.__setattr__(sparse, name, True) for name in ("paper_only", "report_only", "readonly")]; _reject("allocation_input_records[0] must be canonical", (sparse,), allocations, config)
def _restricted_growth_partitions(size: int) -> tuple[tuple[int, ...], ...]:
    if size == 0:
        return ((),)
    values: list[tuple[int, ...]] = []
    def extend(prefix: tuple[int, ...]) -> None:
        if len(prefix) == size:
            values.append(prefix)
            return
        for item in range(max(prefix) + 2):
            extend(prefix + (item,))
    extend((0,))
    return tuple(values)
def _oracle_optimum_edges(
    candidate_edges: tuple[tuple[str, str, str, str, str], ...],
    *,
    evidence_capacity: int,
    independence_key_by_source: dict[str, str],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
) -> tuple[tuple[int, int], tuple[tuple[str, str, str, str, str], ...]]:
    optimum = (-1, -1)
    optimum_edges: tuple[tuple[str, str, str, str, str], ...] | None = None
    for mask in range(1 << len(candidate_edges)):
        selected = tuple(sorted(
            edge for index, edge in enumerate(candidate_edges) if mask & (1 << index)
        ))
        source_counts: dict[str, int] = {}
        requirement_counts: dict[str, int] = {}
        independence_pairs: set[tuple[str, str]] = set()
        valid = True
        for edge in selected:
            requirement_id, source = edge[:2]
            source_counts[source] = source_counts.get(source, 0) + 1
            requirement_counts[requirement_id] = requirement_counts.get(requirement_id, 0) + 1
            pair = (requirement_id, independence_key_by_source[source])
            if (
                source_counts[source] > evidence_capacity
                or requirement_counts[requirement_id] > requirement_by_id[requirement_id].minimum_witness_count
                or pair in independence_pairs
            ):
                valid = False
                break
            independence_pairs.add(pair)
        if not valid:
            continue
        objective = tuple(
            sum(
                count
                for requirement_id, count in requirement_counts.items()
                if requirement_by_id[requirement_id].unmet_status == severity
            )
            for severity in ("blocked", "watch")
        )
        if objective > optimum or (objective == optimum and (optimum_edges is None or selected < optimum_edges)):
            optimum, optimum_edges = cast(tuple[int, int], objective), selected
    assert optimum_edges is not None
    return optimum, optimum_edges
def test_production_matching_equals_the_bruteforce_small_graph_oracle() -> None:
    letters = ("a", "b", "c")
    for evidence_count in range(1, 4):
        for requirement_count in range(1, 3):
            requirement_ids = tuple(f"requirement-{letters[index]}" for index in range(requirement_count))
            edge_slots = evidence_count * requirement_count
            for adjacency_bits in product((False, True), repeat=edge_slots):
                memberships = tuple(
                    tuple(requirement_ids[requirement_index] for requirement_index in range(requirement_count) if adjacency_bits[source_index * requirement_count + requirement_index])
                    for source_index in range(evidence_count)
                )
                for evidence_capacity in (1, 2):
                    for partition in _restricted_growth_partitions(evidence_count):
                        records = tuple(
                            _record(
                                letters[index],
                                requirement_ids=memberships[index],
                                independence_key=f"independence-{partition[index]}",
                            )
                            for index in range(evidence_count)
                        )
                        independence = {
                            record.source_lineage.source_lineage_id: record.assessment_revision.independence_key
                            for record in records
                        }
                        for demands in product((1, 2), repeat=requirement_count):
                            if any(demand > evidence_count for demand in demands):
                                continue
                            for statuses in product(("blocked", "watch"), repeat=requirement_count):
                                requirements = tuple(
                                    _requirement(requirement_ids[index], count=demands[index], status=statuses[index])
                                    for index in range(requirement_count)
                                )
                                config = _config(requirements, max_requirement_assignments_per_evidence=evidence_capacity)
                                coverage = _build(records, config)
                                actual_edges = _coverage_edges(coverage)
                                requirement_by_id = {row.requirement_id: row for row in requirements}
                                expected_objective, expected_edges = _oracle_optimum_edges(
                                    tuple(sorted(
                                        (
                                            requirement_id,
                                            record.source_lineage.source_lineage_id,
                                            record.evidence_revision.evidence_revision_id,
                                            record.assessment_revision.assessment_revision_id,
                                            record.capture.capture_id,
                                        )
                                        for record in records
                                        for requirement_id in record.evidence_revision.requirement_ids
                                    )),
                                    evidence_capacity=evidence_capacity,
                                    independence_key_by_source=independence,
                                    requirement_by_id=requirement_by_id,
                                )
                                actual_objective = tuple(
                                    sum(row.assigned_witness_count for row in coverage if row.unmet_status == severity)
                                    for severity in ("blocked", "watch")
                                )
                                assert actual_objective == expected_objective
                                assert actual_edges == expected_edges
@pytest.mark.parametrize(
    ("adjacency", "expected_pairs"),
    (
        ("complete-k3-3", (("requirement-a", "source-a"), ("requirement-b", "source-b"), ("requirement-c", "source-c"))),
        ("six-edge-cycle", (("requirement-a", "source-a"), ("requirement-b", "source-b"), ("requirement-c", "source-c"))),
    ),
)
def test_three_by_three_unit_capacity_uses_wider_lexical_optimum(
    adjacency: str,
    expected_pairs: tuple[tuple[str, str], ...],
) -> None:
    requirement_ids = ("requirement-a", "requirement-b", "requirement-c")
    memberships = (
        (requirement_ids,) * 3
        if adjacency == "complete-k3-3"
        else ((requirement_ids[:2]), (requirement_ids[1:]), (requirement_ids[::2]))
    )
    records = tuple(
        _record(suffix, requirement_ids=cast(tuple[str, ...], memberships[index]))
        for index, suffix in enumerate(("a", "b", "c"))
    )
    coverage = _build(
        records,
        _config(tuple(_requirement(value) for value in requirement_ids), max_requirement_assignments_per_evidence=1),
    )
    assert tuple((edge[0], edge[1]) for edge in _coverage_edges(coverage)) == expected_pairs
EXPECTED_IMPORTS = {
    "team_evidence_aggregation_allocation.py": {
        "__future__", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_witness.py": {
        "__future__", "collections", "datetime", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
        "polymarket_alpha_lab.team_evidence_aggregation_allocation",
    },
}
EXPECTED_EXPORTS = {
    "team_evidence_aggregation_allocation.py": ("allocate_team_evidence_weights",),
    "team_evidence_aggregation_witness.py": ("build_team_evidence_requirement_coverage",),
}
MAX_LINES = {
    "src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py": 450,
    "src/polymarket_alpha_lab/team_evidence_aggregation_witness.py": 650,
    "tests/test_team_evidence_aggregation_allocation.py": 600,
    "tests/test_team_evidence_aggregation_witness.py": 900,
}
HARD_MAXIMA = {
    "team_evidence_aggregation_allocation.py": {"_IMPLEMENTATION_MAXIMUM_RECORDS": 128},
    "team_evidence_aggregation_witness.py": {
        "_IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS": 32,
        "_IMPLEMENTATION_MAXIMUM_REQUIREMENTS": 32,
        "_IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS": 1024,
        "_IMPLEMENTATION_MAXIMUM_WITNESS_EDGES": 256,
    },
}
FORBIDDEN_WORDS = frozenset(
    "account accounts adapter auth authentication authorization bitcoin btc callback callable capital cli client connect credential credentials database db dsn exchange execution filesystem getenv hook legacy logger logging network order orders packet persistence postgres process random randomness signing sizing spawn sql store supabase token tokens trade trading wallet".split()
)
FORBIDDEN_PHRASES = {
    ("allocation", "capital"), ("capital", "allocation"), ("db", "row"),
    ("forecast", "packet"), ("legacy", "projection"), ("node", "2", "c"),
    ("package", "root", "export"), ("private", "key"),
}
FORBIDDEN_CALLS = {
    "__import__", "choice", "choices", "compile", "connect", "eval", "exec",
    "execute", "float", "getenv", "getrandbits", "hash", "import_module", "input",
    "now", "open", "print", "randint", "random", "randrange", "read_text", "repr",
    "shuffle", "sign", "spawn", "timestamp", "total_seconds", "trade", "uniform",
    "urandom", "utcnow", "write_text",
}
def _words(value: str) -> tuple[str, ...]:
    return tuple(part.lower() for part in re.findall(r"[A-Z]+(?=[A-Z][a-z]|[^A-Za-z]|$)|[A-Z]?[a-z]+|[0-9]+", value))
def _forbidden_identifier(value: str) -> bool:
    words = _words(value)
    return bool(
        set(words) & FORBIDDEN_WORDS
        or any(words[index:index + len(phrase)] == phrase for phrase in FORBIDDEN_PHRASES for index in range(len(words) - len(phrase) + 1))
    )
def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}".lstrip(".")
    return ""
def test_node_2b_child_local_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
    root = Path(__file__).resolve().parents[1]
    production_paths = tuple(
        root / "src" / "polymarket_alpha_lab" / name for name in EXPECTED_IMPORTS
    )
    trees: dict[str, ast.Module] = {}
    for path in production_paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=path.name)
        trees[path.name] = tree
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
                assert all(alias.name != "polymarket_alpha_lab" for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0 and isinstance(node.module, str) and node.module
                imports.append(node.module)
                assert node.module != "polymarket_alpha_lab"
        assert len(imports) == len(set(imports))
        assert set(imports) == EXPECTED_IMPORTS[path.name]
        assignments = [
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
        ]
        assert len(assignments) == 1
        assignment = assignments[0]
        assert len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Name)
        assert isinstance(assignment.value, ast.Tuple)
        exports = tuple(
            item.value
            for item in assignment.value.elts
            if isinstance(item, ast.Constant) and type(item.value) is str
        )
        assert len(exports) == len(assignment.value.elts)
        assert exports == EXPECTED_EXPORTS[path.name] and len(exports) == len(set(exports))
        assert sum(isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == "__all__" for node in ast.walk(tree)) == 1
        for node in ast.walk(tree):
            assert not (isinstance(node, ast.Constant) and type(node.value) is float)
            if isinstance(node, ast.Attribute):
                assert not (isinstance(node.value, ast.Name) and node.value.id == "polymarket_alpha_lab")
            if isinstance(node, (ast.Name, ast.Attribute, ast.arg, ast.FunctionDef, ast.ClassDef)):
                value = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else node.arg if isinstance(node, ast.arg) else node.name
                assert not _forbidden_identifier(value)
                assert value not in FORBIDDEN_CALLS
            if isinstance(node, ast.alias):
                assert not _forbidden_identifier(node.name)
                assert node.asname is None or not _forbidden_identifier(node.asname)
                assert node.name.rsplit(".", 1)[-1] not in FORBIDDEN_CALLS
                assert node.asname is None or node.asname not in FORBIDDEN_CALLS
            if isinstance(node, ast.FormattedValue):
                assert node.conversion not in {ord("a"), ord("r")}
            if isinstance(node, ast.ExceptHandler):
                assert node.type is not None
                assert not any(
                    _dotted(item).rsplit(".", 1)[-1] in {"Exception", "BaseException"}
                    for item in ast.walk(node.type)
                    if isinstance(item, (ast.Name, ast.Attribute))
                )
        for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            arguments = tuple(filter(None, (*function.args.posonlyargs, *function.args.args, function.args.vararg, *function.args.kwonlyargs, function.args.kwarg)))
            called = {
                call.func.id for call in ast.walk(function)
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            }
            assert all(argument.arg not in called for argument in arguments)
        annotations = [node.annotation for node in ast.walk(tree) if isinstance(node, (ast.arg, ast.AnnAssign)) and node.annotation is not None]
        annotations += [node.returns for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None]
        assert not any(_dotted(item).rsplit(".", 1)[-1] == "float" or (isinstance(item, ast.Constant) and item.value == "float") for annotation in annotations for item in ast.walk(annotation))
        lowered = source.lower()
        for token in (
            "0.020000", "0.980000", "tea:v1", "tfr:v1", "tfe:v1",
            "bitcoin", "btc", "legacy_projection", "legacy projection", "from polymarket_alpha_lab import",
        ):
            assert token not in lowered
    witness_functions = {
        node.name: node
        for node in trees["team_evidence_aggregation_witness.py"].body
        if isinstance(node, ast.FunctionDef)
    }
    builder = witness_functions["build_team_evidence_requirement_coverage"]
    validator = witness_functions["_validate_witness_inputs"]
    assert any(
        isinstance(node, ast.Call) and _dotted(node.func) == "_validate_witness_inputs"
        for node in ast.walk(builder)
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "allocate_team_evidence_weights"
        for node in ast.walk(validator)
    )
    for name, expected in HARD_MAXIMA.items():
        assignments = [
            (node.targets[0].id, node.value.value)
            for node in trees[name].body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id.startswith("_IMPLEMENTATION_MAXIMUM_")
            and isinstance(node.value, ast.Constant)
            and type(node.value.value) is int
        ]
        assert len(assignments) == len(expected) and dict(assignments) == expected
        assert set(dict(assignments)).isdisjoint(EXPECTED_EXPORTS[name])
    line_counts = {
        relative: len((root / relative).read_text(encoding="utf-8").splitlines())
        for relative in MAX_LINES
    }
    assert all(line_counts[path] <= maximum for path, maximum in MAX_LINES.items())
    assert sum(line_counts[path] for path in MAX_LINES if path.startswith("src/")) <= 1_100
    assert sum(line_counts[path] for path in MAX_LINES if path.startswith("tests/")) <= 1_500
