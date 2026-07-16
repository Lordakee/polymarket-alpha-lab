from __future__ import annotations

import ast
from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
from itertools import permutations, product
from pathlib import Path
import re
from typing import cast

import pytest

from polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRequirement,
    TeamEvidenceRequirementCoverage,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceWeightAllocation,
)
import polymarket_alpha_lab.team_evidence_aggregation_witness as witness_module


build_team_evidence_requirement_coverage = witness_module.build_team_evidence_requirement_coverage
FRESHNESS_ANCHOR_AT = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 7, 13, 12, 1, tzinfo=UTC)
RECORDED_AT = datetime(2026, 7, 13, 12, 2, tzinfo=UTC)
ASSESSED_AT = datetime(2026, 7, 13, 12, 3, tzinfo=UTC)


def _digest(seed: str) -> str:
    return format(sum((index + 1) * ord(char) for index, char in enumerate(seed)), "064x")


def _requirement(
    requirement_id: str,
    *,
    count: int = 1,
    weight: Decimal = Decimal("0.010000"),
    status: str = "blocked",
) -> TeamEvidenceRequirement:
    return TeamEvidenceRequirement(
        requirement_id=requirement_id,
        minimum_witness_count=count,
        minimum_effective_weight=weight,
        unmet_status=status,
    )


def _record(
    suffix: str,
    *,
    requirement_ids: tuple[str, ...] = ("requirement-a",),
    requested_weight: Decimal = Decimal("0.010000"),
    independence_key: str | None = None,
    correlation_key: str | None = None,
    projection_suffix: str | None = None,
    assessment_suffix: str | None = None,
) -> TeamEvidenceAggregationRecord:
    projection, assessment = projection_suffix or suffix, assessment_suffix or suffix
    lineage_id = f"source-{projection}"
    lineage_digest = _digest(lineage_id)
    content_digest = _digest(f"content-{projection}")
    evidence_id = f"evidence-{projection}"
    evidence_digest = _digest(evidence_id)
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(lineage_id, lineage_digest),
        capture=TeamEvidenceCapture(
            f"capture-{projection}", _digest(f"capture-{projection}"), lineage_id,
            lineage_digest, content_digest, CAPTURED_AT,
        ),
        evidence_revision=TeamEvidenceRevision(
            evidence_id, evidence_digest, None, None, lineage_id, lineage_digest,
            content_digest, requirement_ids, FRESHNESS_ANCHOR_AT, RECORDED_AT,
        ),
        assessment_revision=TeamEvidenceAssessmentRevision(
            f"assessment-{assessment}", _digest(f"assessment-{assessment}"), None, None,
            evidence_id, evidence_digest, ASSESSED_AT, Decimal("0.500000"), requested_weight,
            _digest(f"rationale-{assessment}"), independence_key or f"independence-{assessment}",
            correlation_key or f"correlation-{assessment}",
        ),
    )


def _config(
    requirements: tuple[TeamEvidenceRequirement, ...] = (), **changes: object
) -> TeamEvidenceAggregationConfig:
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


def _copy(value: object, field_name: str, replacement: object) -> object:
    copied = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(copied, field.name, replacement if field.name == field_name else getattr(value, field.name))
    return copied


def _replace_layer(
    record: TeamEvidenceAggregationRecord, layer_name: str, field_name: str, replacement: object
) -> TeamEvidenceAggregationRecord:
    layer = _copy(getattr(record, layer_name), field_name, replacement)
    return cast(TeamEvidenceAggregationRecord, _copy(record, layer_name, layer))


def _coverage_by_id(rows: tuple[TeamEvidenceRequirementCoverage, ...]) -> dict[str, TeamEvidenceRequirementCoverage]:
    return {row.requirement_id: row for row in rows}


def _edge_key(requirement_id: str, record: TeamEvidenceAggregationRecord) -> tuple[str, str, str, str, str]:
    return (
        requirement_id, record.source_lineage.source_lineage_id, record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id, record.capture.capture_id,
    )


def _coverage_edges(
    rows: tuple[TeamEvidenceRequirementCoverage, ...],
) -> tuple[tuple[str, str, str, str, str], ...]:
    return tuple(sorted(
        (item.requirement_id, item.source_lineage_id, item.evidence_revision_id,
         item.assessment_revision_id, item.capture_id)
        for row in rows for item in row.witnesses
    ))


def _build(
    records: tuple[TeamEvidenceAggregationRecord, ...], config: TeamEvidenceAggregationConfig
) -> tuple[TeamEvidenceRequirementCoverage, ...]:
    return build_team_evidence_requirement_coverage(
        records, allocate_team_evidence_weights(records, config=config), config=config
    )


def _reject(message: str, records: object, allocations: object, config: object) -> None:
    with pytest.raises(ValueError, match=rf"^{re.escape(message)}$"):
        build_team_evidence_requirement_coverage(records, allocations, config=config)  # type: ignore[arg-type]


def test_witness_threshold_is_inclusive_and_rows_are_sorted_for_every_requirement() -> None:
    assert _build((), _config()) == ()
    requirements = (
        _requirement("requirement-z", weight=Decimal("0.020000"), status="watch"),
        _requirement("requirement-a", count=2),
    )
    covered, empty = _build((_record("b"), _record("a")), _config(requirements))
    assert (covered.requirement_id, empty.requirement_id) == ("requirement-a", "requirement-z")
    assert (
        covered.minimum_witness_count, covered.assigned_witness_count, covered.minimum_effective_weight,
        covered.unmet_status, covered.satisfied,
    ) == (2, 2, Decimal("0.010000"), "blocked", True)
    assert tuple(item.source_lineage_id for item in covered.witnesses) == ("source-a", "source-b")
    assert all(item.effective_weight == Decimal("0.010000") for item in covered.witnesses)
    assert all(item.paper_only is item.report_only is item.readonly is True for item in covered.witnesses)
    assert (
        empty.minimum_witness_count, empty.assigned_witness_count, empty.minimum_effective_weight,
        empty.unmet_status, empty.satisfied, empty.witnesses,
    ) == (1, 0, Decimal("0.020000"), "watch", False, ())


def test_zero_minimum_effective_weight_threshold_accepts_only_positive_effective_rows() -> None:
    records = tuple(_record(suffix, independence_key="independence-shared") for suffix in ("z", "a"))
    config = _config(
        (_requirement("requirement-a", count=2, weight=Decimal("0.000000")),),
        independence_group_weight_cap=Decimal("0.000001"),
    )
    allocations = allocate_team_evidence_weights(records, config=config)
    assert tuple(row.effective_weight for row in allocations) == (Decimal("0.000001"), Decimal("0.000000"))
    row = build_team_evidence_requirement_coverage(records, allocations, config=config)[0]
    assert (row.assigned_witness_count, row.satisfied) == (1, False)
    assert tuple((item.source_lineage_id, item.effective_weight) for item in row.witnesses) == (
        ("source-a", Decimal("0.000001")),
    )


def test_witness_enforces_evidence_assignment_and_requirement_independence_capacities() -> None:
    requirements = (_requirement("requirement-a"), _requirement("requirement-b"))
    record = _record("shared", requirement_ids=("requirement-a", "requirement-b"))
    rows = _build((record,), _config(requirements, max_requirement_assignments_per_evidence=1))
    assert tuple(row.assigned_witness_count for row in rows) == (1, 0)
    records = tuple(_record(suffix, independence_key="independence-shared") for suffix in ("a", "b"))
    row = _build(records, _config((_requirement("requirement-a", count=2),)))[0]
    assert (row.assigned_witness_count, row.satisfied) == (1, False)


def test_global_matching_solves_the_greedy_counterexample() -> None:
    records = (
        _record("flexible", requirement_ids=("requirement-a", "requirement-b")),
        _record("a-only", requirement_ids=("requirement-a",)),
    )
    rows = _build(records, _config(
        (_requirement("requirement-a"), _requirement("requirement-b")),
        max_requirement_assignments_per_evidence=1,
    ))
    assert tuple((row.requirement_id, row.witnesses[0].source_lineage_id, row.satisfied) for row in rows) == (
        ("requirement-a", "source-a-only", True), ("requirement-b", "source-flexible", True),
    )


def test_partial_coverage_preserves_explicit_watch_and_blocked_policy() -> None:
    records = (
        _record("watch", requirement_ids=("requirement-watch",)),
        _record("blocked", requirement_ids=("requirement-blocked",)),
    )
    rows = _build(records, _config((
        _requirement("requirement-watch", count=2, status="watch"),
        _requirement("requirement-blocked", count=2, status="blocked"),
    )))
    by_id = _coverage_by_id(rows)
    assert (by_id["requirement-watch"].assigned_witness_count, by_id["requirement-watch"].satisfied,
            by_id["requirement-watch"].unmet_status) == (1, False, "watch")
    assert (by_id["requirement-blocked"].assigned_witness_count, by_id["requirement-blocked"].satisfied,
            by_id["requirement-blocked"].unmet_status) == (1, False, "blocked")


def test_blocked_assignments_have_priority_over_lexically_earlier_watch_edges() -> None:
    record = _record("shared", requirement_ids=("a-watch", "z-blocked"))
    rows = _build((record,), _config(
        (_requirement("a-watch", status="watch"), _requirement("z-blocked")),
        max_requirement_assignments_per_evidence=1,
    ))
    assert tuple(row.assigned_witness_count for row in rows) == (0, 1)


def test_severity_optimum_uses_the_lexically_smallest_edge_set() -> None:
    records = tuple(_record(suffix, requirement_ids=("requirement-a", "requirement-b")) for suffix in ("a", "b"))
    rows = _build(records, _config(
        (_requirement("requirement-a"), _requirement("requirement-b")),
        max_requirement_assignments_per_evidence=1,
    ))
    assert tuple((row.requirement_id, row.witnesses[0].source_lineage_id) for row in rows) == (
        ("requirement-a", "source-a"), ("requirement-b", "source-b"),
    )


def test_assignment_objective_does_not_maximize_fully_satisfied_requirements() -> None:
    record = _record("only", requirement_ids=("requirement-a", "requirement-b"))
    rows = _build((record,), _config(
        (_requirement("requirement-a", count=2), _requirement("requirement-b")),
        max_requirement_assignments_per_evidence=1,
    ))
    assert tuple((row.requirement_id, row.assigned_witness_count, row.satisfied) for row in rows) == (
        ("requirement-a", 1, False), ("requirement-b", 0, False),
    )


def test_witness_recomputes_and_requires_the_exact_canonical_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = (_record("b"), _record("a"))
    config = _config((_requirement("requirement-a", count=2),))
    canonical = allocate_team_evidence_weights(records, config=config)
    calls: list[tuple[object, object]] = []

    def spy(received: tuple[TeamEvidenceAggregationRecord, ...], *, config: TeamEvidenceAggregationConfig) -> tuple[TeamEvidenceWeightAllocation, ...]:
        calls.append((received, config))
        return allocate_team_evidence_weights(received, config=config)

    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", spy)
    build_team_evidence_requirement_coverage(records, canonical, config=config)
    assert len(calls) == 1 and calls[0][0] is records and calls[0][1] is config
    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", allocate_team_evidence_weights)
    altered = cast(TeamEvidenceWeightAllocation, _copy(canonical[0], "effective_weight", Decimal("0.009999")))
    invalid = (
        canonical[:-1], (canonical[0], canonical[0]), canonical + (canonical[0],),
        tuple(reversed(canonical)), (altered, canonical[1]),
    )
    for allocations in invalid:
        _reject("allocations must equal canonical recomputation for allocation_input_records", records, allocations, config)


def test_witness_rejects_join_and_assessment_projection_mismatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records, config = (_record("a"),), _config((_requirement("requirement-a"),))
    allocation = allocate_team_evidence_weights(records, config=config)[0]
    monkeypatch.setattr(
        witness_module, "_build_candidate_edges",
        lambda *args, **kwargs: pytest.fail("candidate construction reached after projection mismatch"),
    )
    cases = (
        ("source_lineage_id", "source-other", "record/allocation join keys must match exactly"),
        ("capture_id", "capture-other", "record/allocation join keys must match exactly"),
        ("evidence_revision_id", "evidence-other", "record/allocation join keys must match exactly"),
        ("assessment_revision_id", "assessment-other", "record/allocation join keys must match exactly"),
        ("independence_key", "independence-other", "allocation.independence_key must match assessment_revision.independence_key"),
        ("correlation_key", "correlation-other", "allocation.correlation_key must match assessment_revision.correlation_key"),
        ("requested_weight", Decimal("0.010001"), "allocation.requested_weight must match assessment_revision.requested_weight"),
    )
    for field_name, replacement, message in cases:
        tampered = (cast(TeamEvidenceWeightAllocation, _copy(allocation, field_name, replacement)),)
        monkeypatch.setattr(
            witness_module, "allocate_team_evidence_weights",
            lambda received, *, config, result=tampered: result,
        )
        _reject(message, records, tampered, config)
    noncanonical = cast(
        TeamEvidenceWeightAllocation,
        _copy(_copy(allocation, "source_lineage_id", "source-other"), "effective_weight", Decimal("0.01000")),
    )
    monkeypatch.setattr(
        witness_module, "allocate_team_evidence_weights",
        lambda received, *, config: (noncanonical,),
    )
    _reject("allocations[0] must be canonical", records, (noncanonical,), config)


def test_candidate_edge_resource_bound_is_checked_before_graph_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirements = (_requirement("requirement-a"), _requirement("requirement-b"))
    records = (_record("a", requirement_ids=("requirement-a", "requirement-b")),)
    passing = _config(requirements, maximum_witness_edges=2)
    allocations = allocate_team_evidence_weights(records, config=passing)
    assert sum(row.assigned_witness_count for row in build_team_evidence_requirement_coverage(
        records, allocations, config=passing
    )) == 2
    monkeypatch.setattr(
        witness_module, "_canonical_optimum_edges",
        lambda *args, **kwargs: pytest.fail("matching graph constructed after edge overflow"),
    )
    _reject(
        "candidate witness edge count exceeds config.maximum_witness_edges",
        records, allocations, _config(requirements, maximum_witness_edges=1),
    )


def test_membership_count_deduplicates_repeated_evidence_revision_projections() -> None:
    requirement_ids = tuple(f"requirement-{index:02d}" for index in range(32))
    requirements = tuple(_requirement(item, weight=Decimal("0.020000")) for item in requirement_ids)
    records = tuple(
        _record(
            f"{index:02d}-{assessment}", requirement_ids=requirement_ids,
            projection_suffix=f"{index:02d}", assessment_suffix=f"{index:02d}-{assessment}",
        )
        for index in range(32) for assessment in ("a", "b")
    )
    rows = _build(records, _config(requirements))
    assert len(rows) == 32
    assert all(row.assigned_witness_count == 0 and row.witnesses == () and row.satisfied is False for row in rows)


def test_witness_assignment_capacity_is_per_record_join_not_evidence_revision() -> None:
    records = tuple(
        _record(
            suffix, projection_suffix="shared", assessment_suffix=suffix,
            independence_key=f"independence-{suffix}",
        )
        for suffix in ("a", "b")
    )
    row = _build(records, _config(
        (_requirement("requirement-a", count=2),), max_requirement_assignments_per_evidence=1,
    ))[0]
    assert (row.assigned_witness_count, row.satisfied) == (2, True)
    assert tuple(item.assessment_revision_id for item in row.witnesses) == ("assessment-a", "assessment-b")


def test_33_by_32_threshold_filtered_memberships_fail_before_recomputation_or_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirement_ids = tuple(f"requirement-{index:02d}" for index in range(32))
    requirements = tuple(_requirement(item, weight=Decimal("0.020000")) for item in requirement_ids)
    records = tuple(_record(f"{index:02d}", requirement_ids=requirement_ids) for index in range(33))
    config = _config(requirements)
    allocations = allocate_team_evidence_weights(records, config=config)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("recomputation or candidates reached after membership overflow")

    monkeypatch.setattr(witness_module, "allocate_team_evidence_weights", forbidden)
    monkeypatch.setattr(witness_module, "_build_candidate_edges", forbidden)
    _reject(
        "distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024",
        records, allocations, config,
    )


def test_positive_effective_records_require_config_resident_requirement_ids() -> None:
    config = _config((_requirement("requirement-a"),))
    positive = _record("positive", requirement_ids=("requirement-retired",))
    _reject(
        "positive-effective requirement ID must exist in config.requirements",
        (positive,), allocate_team_evidence_weights((positive,), config=config), config,
    )
    records = (
        _record("a", requirement_ids=("requirement-a",), independence_key="independence-shared"),
        _record("z", requirement_ids=("requirement-retired",), independence_key="independence-shared"),
    )
    capped = _config(
        (_requirement("requirement-a", weight=Decimal("0.000000")),),
        independence_group_weight_cap=Decimal("0.000001"),
    )
    allocations = allocate_team_evidence_weights(records, config=capped)
    assert tuple(row.effective_weight for row in allocations) == (Decimal("0.000001"), Decimal("0.000000"))
    rows = build_team_evidence_requirement_coverage(records, allocations, config=capped)
    assert tuple(row.requirement_id for row in rows) == ("requirement-a",)
    assert rows[0].assigned_witness_count == 1


def test_witness_is_input_requirement_and_adjacency_permutation_invariant() -> None:
    requirements = (
        _requirement("requirement-a", count=2), _requirement("requirement-b", count=2, status="watch"),
    )
    adjacency = (
        ("a", ("requirement-a", "requirement-b")),
        ("b", ("requirement-a",)),
        ("c", ("requirement-b",)),
    )
    baseline: tuple[TeamEvidenceRequirementCoverage, ...] | None = None
    for reversals in product((False, True), repeat=3):
        records = tuple(
            _record(suffix, requirement_ids=tuple(reversed(ids)) if reverse else ids)
            for (suffix, ids), reverse in zip(adjacency, reversals, strict=True)
        )
        for record_order in permutations(records):
            for requirement_order in permutations(requirements):
                actual = _build(record_order, _config(requirement_order))
                baseline = actual if baseline is None else baseline
                assert actual == baseline


def test_witness_rejects_wrong_types_hard_flags_and_resource_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirement, record = _requirement("requirement-a"), _record("a")
    config = _config((requirement,))
    allocation = allocate_team_evidence_weights((record,), config=config)[0]
    _reject("allocation_input_records must be an exact tuple", [record], (allocation,), config)
    _reject("allocations must be an exact tuple", (record,), [allocation], config)
    _reject("config must be exactly TeamEvidenceAggregationConfig", (record,), (allocation,), object())
    _reject("allocation_input_records[0] must be exactly TeamEvidenceAggregationRecord", (object(),), (allocation,), config)
    _reject("allocations[0] must be exactly TeamEvidenceWeightAllocation", (record,), (object(),), config)
    _reject(
        "config.requirements[0] must be exactly TeamEvidenceRequirement", (record,), (allocation,),
        _copy(config, "requirements", (object(),)),
    )
    false_flags = (
        (_copy(config, "paper_only", False), (record,), (allocation,)),
        (_copy(config, "requirements", (_copy(requirement, "report_only", False),)), (record,), (allocation,)),
        (config, (_copy(record, "readonly", False),), (allocation,)),
        (config, (record,), (_copy(allocation, "paper_only", False),)),
        (config, (_replace_layer(record, "evidence_revision", "report_only", False),), (allocation,)),
    )
    for bad_config, records, allocations in false_flags:
        with pytest.raises(ValueError, match="preserve paper_only=True, report_only=True, readonly=True"):
            build_team_evidence_requirement_coverage(records, allocations, config=bad_config)  # type: ignore[arg-type]
    maxima = {
        "max_requirement_assignments_per_evidence": 32, "maximum_records": 128,
        "maximum_requirements": 32, "maximum_requirement_memberships": 1024, "maximum_witness_edges": 256,
    }
    for field_name, maximum in maxima.items():
        for bad_value in (True, 0, -1, maximum + 1):
            _reject(
                f"config.{field_name} must be an exact int within its implementation maximum",
                (record,), (allocation,), _copy(config, field_name, bad_value),
            )
    malformed = (
        _copy(requirement, "minimum_witness_count", True), _copy(requirement, "minimum_witness_count", 0),
        _copy(requirement, "minimum_effective_weight", 0.01),
        _copy(requirement, "minimum_effective_weight", Decimal("0.01000")),
        _copy(requirement, "unmet_status", "review"),
    )
    for bad_requirement in malformed:
        _reject(
            "config.requirements[0] must be canonical", (record,), (allocation,),
            _copy(config, "requirements", (bad_requirement,)),
        )
    requirement_b = _requirement("requirement-b")
    for bad_requirements in ((requirement_b, requirement), (requirement, requirement)):
        _reject(
            "config.requirements must contain exact unique requirements sorted by requirement_id",
            (record,), (allocation,), _copy(config, "requirements", bad_requirements),
        )
    with pytest.raises(ValueError):
        build_team_evidence_requirement_coverage(
            (record, _record("b")), (allocation,), config=_config((requirement,), maximum_records=1)
        )
    with pytest.raises(ValueError):
        overflow_config = _copy(config, "maximum_requirements", 1)
        overflow_config = _copy(
            overflow_config,
            "requirements",
            (requirement, _requirement("requirement-b")),
        )
        build_team_evidence_requirement_coverage(
            (record,), (allocation,), config=overflow_config,
        )
    surrogate = _replace_layer(record, "evidence_revision", "requirement_ids", ("\ud800",))
    _reject("allocation_input_records[0] must be canonical", (surrogate,), (allocation,), config)
    projections = (
        _record("a", projection_suffix="shared", assessment_suffix="a", requirement_ids=("requirement-a",)),
        _record("b", projection_suffix="shared", assessment_suffix="b", requirement_ids=("requirement-b",)),
    )
    projection_config = _config((requirement, requirement_b))
    _reject(
        "repeated evidence revision identity must have one exact projection",
        projections, allocate_team_evidence_weights(projections, config=projection_config), projection_config,
    )
    records = (record, _record("b"))
    two_record_config = _config((requirement,), maximum_records=2)
    allocations = allocate_team_evidence_weights(records, config=two_record_config)
    monkeypatch.setattr(
        witness_module, "allocate_team_evidence_weights",
        lambda *args, **kwargs: pytest.fail("allocation recomputation reached after record overflow"),
    )
    _reject(
        "allocation_input_records exceeds config.maximum_records or 128",
        records, allocations, _config((requirement,), maximum_records=1),
    )


def _restricted_growth_partitions(size: int) -> tuple[tuple[int, ...], ...]:
    partitions = ((),) if size == 0 else ((0,),)
    for _ in range(1, size):
        partitions = tuple(prefix + (value,) for prefix in partitions for value in range(max(prefix) + 2))
    return partitions


def _oracle_optimum_edges(
    candidate_edges: tuple[tuple[str, str, str, str, str], ...],
    *,
    evidence_capacity: int,
    independence_key_by_source: dict[str, str],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
) -> tuple[tuple[int, int], tuple[tuple[str, str, str, str, str], ...]]:
    best_objective = (-1, -1)
    best_edges: tuple[tuple[str, str, str, str, str], ...] | None = None
    for mask in range(1 << len(candidate_edges)):
        selected = tuple(edge for index, edge in enumerate(candidate_edges) if mask & (1 << index))
        evidence_counts: dict[tuple[str, str, str, str], int] = {}
        independence_pairs: set[tuple[str, str]] = set()
        requirement_counts: dict[str, int] = {}
        for edge in selected:
            requirement_id, source, evidence, assessment, capture = edge
            record_key = (source, capture, evidence, assessment)
            evidence_counts[record_key] = evidence_counts.get(record_key, 0) + 1
            pair = (requirement_id, independence_key_by_source[source])
            requirement_counts[requirement_id] = requirement_counts.get(requirement_id, 0) + 1
            if (
                evidence_counts[record_key] > evidence_capacity or pair in independence_pairs
                or requirement_counts[requirement_id] > requirement_by_id[requirement_id].minimum_witness_count
            ):
                break
            independence_pairs.add(pair)
        else:
            objective = tuple(sum(
                count for requirement_id, count in requirement_counts.items()
                if requirement_by_id[requirement_id].unmet_status == status
            ) for status in ("blocked", "watch"))
            canonical = tuple(sorted(selected))
            if objective > best_objective or (
                objective == best_objective and (best_edges is None or canonical < best_edges)
            ):
                best_objective, best_edges = cast(tuple[int, int], objective), canonical
    assert best_edges is not None
    return best_objective, best_edges


def test_production_matching_equals_the_bruteforce_small_graph_oracle() -> None:
    for evidence_count in range(1, 4):
        evidence_names = tuple(chr(ord("a") + index) for index in range(evidence_count))
        for requirement_count in range(1, 3):
            requirement_ids = tuple(f"requirement-{chr(ord('a') + index)}" for index in range(requirement_count))
            for bits in product((False, True), repeat=evidence_count * requirement_count):
                adjacency = tuple(tuple(
                    requirement_ids[requirement_index] for requirement_index in range(requirement_count)
                    if bits[evidence_index * requirement_count + requirement_index]
                ) for evidence_index in range(evidence_count))
                for evidence_capacity in (1, 2):
                    for partition in _restricted_growth_partitions(evidence_count):
                        demand_values = tuple(value for value in (1, 2) if value <= evidence_count)
                        for demands in product(demand_values, repeat=requirement_count):
                            for statuses in product(("blocked", "watch"), repeat=requirement_count):
                                requirements = tuple(
                                    _requirement(item, count=demands[index], status=statuses[index])
                                    for index, item in enumerate(requirement_ids)
                                )
                                records = tuple(
                                    _record(
                                        evidence_names[index], requirement_ids=adjacency[index],
                                        independence_key=f"independence-{partition[index]}",
                                    ) for index in range(evidence_count)
                                )
                                rows = _build(records, _config(
                                    requirements, max_requirement_assignments_per_evidence=evidence_capacity,
                                ))
                                candidates = tuple(sorted(
                                    _edge_key(requirement_id, records[index])
                                    for index in range(evidence_count) for requirement_id in adjacency[index]
                                ))
                                oracle = _oracle_optimum_edges(
                                    candidates, evidence_capacity=evidence_capacity,
                                    independence_key_by_source={
                                        row.source_lineage.source_lineage_id: row.assessment_revision.independence_key
                                        for row in records
                                    },
                                    requirement_by_id={row.requirement_id: row for row in requirements},
                                )
                                objective = tuple(sum(
                                    row.assigned_witness_count for row in rows if row.unmet_status == status
                                ) for status in ("blocked", "watch"))
                                case = (evidence_count, requirement_count, bits, evidence_capacity, partition, demands, statuses)
                                assert objective == oracle[0], case
                                assert _coverage_edges(rows) == oracle[1], case


@pytest.mark.parametrize(
    ("adjacency", "expected_pairs"),
    (
        ("complete-k3-3", (
            ("requirement-a", "source-a"), ("requirement-b", "source-b"),
            ("requirement-c", "source-c"),
        )),
        ("six-edge-cycle", (
            ("requirement-a", "source-a"), ("requirement-b", "source-b"),
            ("requirement-c", "source-c"),
        )),
    ),
)
def test_three_by_three_unit_capacity_uses_wider_lexical_optimum(
    adjacency: str, expected_pairs: tuple[tuple[str, str], ...]
) -> None:
    requirement_ids = ("requirement-a", "requirement-b", "requirement-c")
    memberships = (requirement_ids,) * 3 if adjacency == "complete-k3-3" else (
        ("requirement-a", "requirement-b"), ("requirement-b", "requirement-c"),
        ("requirement-a", "requirement-c"),
    )
    records = tuple(
        _record(chr(ord("a") + index), requirement_ids=memberships[index]) for index in range(3)
    )
    rows = _build(records, _config(
        tuple(_requirement(item) for item in requirement_ids), max_requirement_assignments_per_evidence=1,
    ))
    assert tuple(
        (row.requirement_id, item.source_lineage_id) for row in rows for item in row.witnesses
    ) == expected_pairs


def _name_segments(value: str) -> tuple[str, ...]:
    return tuple(match.group(0).lower() for match in re.finditer(
        r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+", value
    ))


def test_node_2b_child_local_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
    root = Path(__file__).resolve().parents[1]
    names = ("team_evidence_aggregation_allocation.py", "team_evidence_aggregation_witness.py")
    paths = {name: root / "src" / "polymarket_alpha_lab" / name for name in names}
    expected_imports = {
        names[0]: {"__future__", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
        names[1]: {
            "__future__", "collections", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types",
            "polymarket_alpha_lab.team_evidence_aggregation_allocation",
        },
    }
    expected_exports = {
        names[0]: ("allocate_team_evidence_weights",),
        names[1]: ("build_team_evidence_requirement_coverage",),
    }
    expected_maxima = {
        names[0]: {"_IMPLEMENTATION_MAXIMUM_RECORDS": 128},
        names[1]: {
            "_IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS": 32,
            "_IMPLEMENTATION_MAXIMUM_REQUIREMENTS": 32,
            "_IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS": 1024,
            "_IMPLEMENTATION_MAXIMUM_WITNESS_EDGES": 256,
        },
    }
    forbidden_sequences = {
        ("node", "2", "c"), ("forecast", "packet"), ("db", "row"), ("store",), ("cli",),
        ("persistence",), ("network",), ("filesystem",), ("process",), ("logging",), ("auth",),
        ("account",), ("credential",), ("token",), ("wallet",), ("signing",), ("order",),
        ("sizing",), ("allocation", "to", "capital"), ("execution",), ("exchange",), ("trading",),
        ("random",), ("randomness",),
    }
    banned_calls = {
        "open", "print", "input", "eval", "exec", "compile", "__import__", "repr", "hash", "float",
    }
    for name, path in paths.items():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
                assert all(alias.name != "polymarket_alpha_lab" for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0 and node.module
                imports.add(node.module)
                assert node.module != "polymarket_alpha_lab"
        assert imports == expected_imports[name]

        all_assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        )]
        assert len(all_assignments) == 1 and isinstance(all_assignments[0].value, ast.Tuple)
        assert sum(
            isinstance(node, ast.Name) and node.id == "__all__" and isinstance(node.ctx, ast.Store)
            for node in ast.walk(tree)
        ) == 1
        elements = all_assignments[0].value.elts
        assert all(isinstance(element, ast.Constant) and type(element.value) is str for element in elements)
        exports = tuple(cast(str, element.value) for element in elements if isinstance(element, ast.Constant))
        assert exports == expected_exports[name] and len(exports) == len(set(exports))

        identifiers: list[tuple[str, ...]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                identifiers.append(_name_segments(node.id))
                assert node.id != "float"
            elif isinstance(node, ast.Attribute):
                identifiers.append(_name_segments(node.attr))
                assert not (isinstance(node.value, ast.Name) and node.value.id == "polymarket_alpha_lab")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                identifiers.extend(_name_segments(module) for module in modules)
            if isinstance(node, ast.Constant):
                assert type(node.value) is not float
                assert not (type(node.value) is str and node.value.strip() == "float")
            if isinstance(node, ast.FormattedValue):
                assert node.conversion not in (ord("a"), ord("r"))
            if isinstance(node, ast.ExceptHandler):
                assert node.type is not None
                assert not {
                    item.id for item in ast.walk(node.type) if isinstance(item, ast.Name)
                }.intersection({"Exception", "BaseException"})
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in banned_calls
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in {
                        "now", "utcnow", "total_seconds", "timestamp", "import_module",
                        "random", "randint", "randrange", "choice", "shuffle",
                    }
        for segments in identifiers:
            assert not any(any(
                segments[index:index + len(sequence)] == sequence
                for index in range(len(segments) - len(sequence) + 1)
            ) for sequence in forbidden_sequences if len(sequence) <= len(segments))
        for function in (
            node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            parameters = {
                argument.arg for argument in (
                    function.args.posonlyargs + function.args.args + function.args.kwonlyargs
                )
            }
            assert not any(
                isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in parameters
                for node in ast.walk(function)
            )
        lowered = source.lower()
        assert re.search(r"\bbtc\b|\bbitcoin\b", lowered) is None
        assert not any(token in lowered for token in (
            "0.020000", "0.980000", "tea:v1", "tfr:v1", "tfe:v1", "legacy projection",
            "legacy projections", "legacy_projection", "from polymarket_alpha_lab import",
        ))
        assignments: dict[str, list[object]] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments.setdefault(target.id, []).append(
                            node.value.value if isinstance(node.value, ast.Constant) else None
                        )
        for constant_name, value in expected_maxima[name].items():
            assert assignments.get(constant_name) == [value]
            assert constant_name not in exports

    witness_tree = ast.parse(paths[names[1]].read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in witness_tree.body if isinstance(node, ast.FunctionDef)
    }
    reachable = {"build_team_evidence_requirement_coverage"}
    pending = ["build_team_evidence_requirement_coverage"]
    allocation_call_reachable = False
    while pending:
        function = functions[pending.pop()]
        for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
            if isinstance(call.func, ast.Name) and call.func.id == "allocate_team_evidence_weights":
                allocation_call_reachable = True
            elif (
                isinstance(call.func, ast.Name)
                and call.func.id in functions
                and call.func.id not in reachable
            ):
                reachable.add(call.func.id)
                pending.append(call.func.id)
    assert allocation_call_reachable
    max_lines = {
        "src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py": 450,
        "src/polymarket_alpha_lab/team_evidence_aggregation_witness.py": 650,
        "tests/test_team_evidence_aggregation_allocation.py": 600,
        "tests/test_team_evidence_aggregation_witness.py": 900,
    }
    counts = {relative: len((root / relative).read_text(encoding="utf-8").splitlines()) for relative in max_lines}
    assert all(counts[path] <= maximum for path, maximum in max_lines.items())
    assert sum(count for path, count in counts.items() if path.startswith("src/")) <= 1_100
    assert sum(count for path, count in counts.items() if path.startswith("tests/")) <= 1_500
