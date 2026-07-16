from __future__ import annotations
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypeVar, cast
from polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRequirement,
    TeamEvidenceRequirementCoverage,
    TeamEvidenceRequirementWitness,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceWeightAllocation,
)
__all__ = ("build_team_evidence_requirement_coverage",)
_IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS = 32
_IMPLEMENTATION_MAXIMUM_REQUIREMENTS = 32
_IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS = 1024
_IMPLEMENTATION_MAXIMUM_WITNESS_EDGES = 256
_FIXED_SIX = Decimal("0.000000")
_CANONICAL_ERRORS = (ArithmeticError, AttributeError, RecursionError, TypeError, ValueError)
_JoinKey = tuple[str, str, str, str]
_EdgeKey = tuple[str, str, str, str, str]
_T = TypeVar("_T")
_CANONICAL_TYPES = (TeamEvidenceAggregationConfig, TeamEvidenceAggregationRecord, TeamEvidenceAssessmentRevision, TeamEvidenceCapture, TeamEvidenceRequirement, TeamEvidenceRevision, TeamEvidenceSourceLineage, TeamEvidenceWeightAllocation)
def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )
def _join_key_from_record(record: TeamEvidenceAggregationRecord) -> _JoinKey:
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )
def _join_key_from_allocation(allocation: TeamEvidenceWeightAllocation) -> _JoinKey:
    return (
        allocation.source_lineage_id,
        allocation.capture_id,
        allocation.evidence_revision_id,
        allocation.assessment_revision_id,
    )
def _candidate_edge_key(
    requirement_id: str,
    record: TeamEvidenceAggregationRecord,
) -> _EdgeKey:
    return (
        requirement_id,
        record.source_lineage.source_lineage_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
        record.capture.capture_id,
    )
def _validate_hard_flags(path: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{path}.{field_name} must preserve paper_only=True, report_only=True, readonly=True")
def _canonical_equal(value: object, normalized: object) -> bool:
    if type(value) is not type(normalized):
        return False
    value_type = type(value)
    if value_type is Decimal:
        bounded = (value.is_finite() and value.same_quantum(_FIXED_SIX)
                   and (value.is_zero() or value.adjusted() <= 57))
        return bounded and (value is normalized or value.as_tuple() == normalized.as_tuple())
    if value_type is datetime:
        return value.tzinfo is UTC and (value is normalized or value == normalized)
    if value_type is str:
        return len(value) <= 160 and (value is normalized or value == normalized)
    if value_type is tuple:
        return value is normalized or (len(value) == len(normalized) and all(
            _canonical_equal(left, right)
            for left, right in zip(value, normalized, strict=True)
        ))
    if value_type in _CANONICAL_TYPES:
        slots = value_type.__slots__
        return all(
            _canonical_equal(getattr(value, name), getattr(normalized, name))
            for name in slots
        )
    return value is normalized or value == normalized
def _validate_representation(path: str, value: object) -> None:
    try:
        if not _canonical_equal(value, value):
            raise ValueError
    except _CANONICAL_ERRORS:
        raise ValueError(f"{path} must be canonical") from None
def _canonical_reconstruction(path: str, value: _T) -> _T:
    try:
        slots = type(value).__slots__
        normalized = type(value)(**{name: getattr(value, name) for name in slots})
    except _CANONICAL_ERRORS:
        raise ValueError(f"{path} must be canonical") from None
    if not _canonical_equal(value, normalized):
        raise ValueError(f"{path} must be canonical")
    return cast(_T, normalized)
def _validate_resource(field_name: str, value: object, maximum: int) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"config.{field_name} must be an exact int within its implementation maximum")
def _validate_witness_inputs(
    allocation_input_records: object,
    allocations: object,
    config: object,
) -> tuple[tuple[TeamEvidenceAggregationRecord, ...], tuple[TeamEvidenceWeightAllocation, ...]]:
    if type(allocation_input_records) is not tuple:
        raise ValueError("allocation_input_records must be an exact tuple")
    if type(allocations) is not tuple:
        raise ValueError("allocations must be an exact tuple")
    if type(config) is not TeamEvidenceAggregationConfig:
        raise ValueError("config must be exactly TeamEvidenceAggregationConfig")
    typed_config = cast(TeamEvidenceAggregationConfig, config)
    typed_records = cast(tuple[TeamEvidenceAggregationRecord, ...], allocation_input_records)
    typed_allocations = cast(tuple[TeamEvidenceWeightAllocation, ...], allocations)
    resource_fields = (
        ("max_requirement_assignments_per_evidence", _IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS),
        ("maximum_records", 128),
        ("maximum_requirements", _IMPLEMENTATION_MAXIMUM_REQUIREMENTS),
        ("maximum_requirement_memberships", _IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS),
        ("maximum_witness_edges", _IMPLEMENTATION_MAXIMUM_WITNESS_EDGES),
    )
    for field_name, maximum in resource_fields:
        _validate_resource(field_name, getattr(typed_config, field_name, None), maximum)
    _validate_hard_flags("config", typed_config)
    if len(typed_records) > typed_config.maximum_records or len(typed_records) > 128:
        raise ValueError("records exceeds config.maximum_records")
    if (len(typed_allocations) != len(typed_records)
            or len(typed_allocations) > typed_config.maximum_records
            or len(typed_allocations) > 128):
        raise ValueError("allocations must equal canonical recomputation for allocation_input_records")
    requirements = getattr(typed_config, "requirements", None)
    if (type(requirements) is not tuple
            or len(requirements) > typed_config.maximum_requirements
            or len(requirements) > _IMPLEMENTATION_MAXIMUM_REQUIREMENTS):
        raise ValueError("config.requirements must contain exact unique requirements sorted by requirement_id")
    for index, record in enumerate(typed_records):
        if type(record) is not TeamEvidenceAggregationRecord:
            raise ValueError(f"allocation_input_records[{index}] must be exactly TeamEvidenceAggregationRecord")
    for index, allocation in enumerate(typed_allocations):
        if type(allocation) is not TeamEvidenceWeightAllocation:
            raise ValueError(f"allocations[{index}] must be exactly TeamEvidenceWeightAllocation")
    for index, requirement in enumerate(requirements):
        if type(requirement) is not TeamEvidenceRequirement:
            raise ValueError(f"config.requirements[{index}] must be exactly TeamEvidenceRequirement")
    membership_limit = min(typed_config.maximum_requirement_memberships,
                           _IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS)
    layers = (("source_lineage", TeamEvidenceSourceLineage),
              ("capture", TeamEvidenceCapture),
              ("evidence_revision", TeamEvidenceRevision),
              ("assessment_revision", TeamEvidenceAssessmentRevision))
    for index, record in enumerate(typed_records):
        if any(type(getattr(record, name, None)) is not expected for name, expected in layers):
            raise ValueError(f"allocation_input_records[{index}] must be canonical")
    for index, record in enumerate(typed_records):
        _validate_hard_flags(f"allocation_input_records[{index}]", record)
        for layer_name, _ in layers:
            _validate_hard_flags(f"allocation_input_records[{index}].{layer_name}", getattr(record, layer_name))
    for index, allocation in enumerate(typed_allocations):
        _validate_hard_flags(f"allocations[{index}]", allocation)
    for index, requirement in enumerate(requirements):
        _validate_hard_flags(f"config.requirements[{index}]", requirement)
    for index, record in enumerate(typed_records):
        revision = record.evidence_revision
        revision_id = getattr(revision, "evidence_revision_id", None)
        requirement_ids = getattr(revision, "requirement_ids", None)
        if type(revision_id) is not str or not 0 < len(revision_id) <= 160 or type(requirement_ids) is not tuple:
            raise ValueError(f"allocation_input_records[{index}] must be canonical")
        if len(requirement_ids) > membership_limit:
            raise ValueError("distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024")
        if any(type(item) is not str or not 0 < len(item) <= 160 for item in requirement_ids):
            raise ValueError(f"allocation_input_records[{index}] must be canonical")
    for index, requirement in enumerate(requirements):
        _validate_representation(f"config.requirements[{index}]", requirement)
    for index, record in enumerate(typed_records):
        _validate_representation(f"allocation_input_records[{index}]", record)
    for index, allocation in enumerate(typed_allocations):
        _validate_representation(f"allocations[{index}]", allocation)
    _validate_representation("config", typed_config)
    membership_counts: dict[str, int] = {}
    memberships = 0
    for record in typed_records:
        revision = record.evidence_revision
        prior_count = membership_counts.get(revision.evidence_revision_id, 0)
        current_count = max(prior_count, len(revision.requirement_ids))
        memberships += current_count - prior_count
        membership_counts[revision.evidence_revision_id] = current_count
        if memberships > membership_limit:
            raise ValueError("distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024")
    for index, requirement in enumerate(requirements):
        _canonical_reconstruction(f"config.requirements[{index}]", requirement)
    requirement_ids = tuple(item.requirement_id for item in requirements)
    if (
        len(set(requirement_ids)) != len(requirement_ids)
        or requirement_ids != tuple(sorted(requirement_ids))
    ):
        raise ValueError(
            "config.requirements must contain exact unique requirements sorted by requirement_id"
        )
    for index, record in enumerate(typed_records):
        _canonical_reconstruction(f"allocation_input_records[{index}]", record)
    for index, allocation in enumerate(typed_allocations):
        _canonical_reconstruction(f"allocations[{index}]", allocation)
    _canonical_reconstruction("config", typed_config)
    ordered_records = tuple(sorted(typed_records, key=_record_key))
    projection_maps: tuple[dict[str, object], dict[str, object]] = ({}, {})
    for record in ordered_records:
        for revision, revision_id, kind, projections in (
            (record.evidence_revision, record.evidence_revision.evidence_revision_id, "evidence", projection_maps[0]),
            (record.assessment_revision, record.assessment_revision.assessment_revision_id, "assessment", projection_maps[1]),
        ):
            prior = projections.get(revision_id)
            if prior is not None and not _canonical_equal(prior, revision):
                raise ValueError(f"repeated {kind} revision identity must have one exact projection")
            projections[revision_id] = revision
    canonical_allocations = allocate_team_evidence_weights(
        allocation_input_records,
        config=typed_config,
    )
    if not _canonical_equal(typed_allocations, canonical_allocations):
        raise ValueError(
            "allocations must equal canonical recomputation for allocation_input_records"
        )
    record_joins = tuple(_join_key_from_record(record) for record in ordered_records)
    allocation_joins = tuple(
        _join_key_from_allocation(allocation) for allocation in canonical_allocations
    )
    if (
        len(set(record_joins)) != len(record_joins)
        or len(set(allocation_joins)) != len(allocation_joins)
        or record_joins != allocation_joins
    ):
        raise ValueError("record/allocation join keys must match exactly")
    for record, allocation in zip(
        ordered_records, canonical_allocations, strict=True
    ):
        assessment = record.assessment_revision
        if allocation.independence_key != assessment.independence_key:
            raise ValueError(
                "allocation.independence_key must match "
                "assessment_revision.independence_key"
            )
        if allocation.correlation_key != assessment.correlation_key:
            raise ValueError(
                "allocation.correlation_key must match "
                "assessment_revision.correlation_key"
            )
        if not _canonical_equal(allocation.requested_weight, assessment.requested_weight):
            raise ValueError(
                "allocation.requested_weight must match "
                "assessment_revision.requested_weight"
            )
    return ordered_records, canonical_allocations
def _build_candidate_edges(
    allocation_input_records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[_EdgeKey, ...]:
    requirement_by_id = {
        requirement.requirement_id: requirement for requirement in config.requirements
    }
    candidates: list[_EdgeKey] = []
    for record, allocation in zip(allocation_input_records, allocations, strict=True):
        if allocation.effective_weight.is_zero():
            continue
        for requirement_id in record.evidence_revision.requirement_ids:
            requirement = requirement_by_id.get(requirement_id)
            if requirement is None:
                raise ValueError(
                    "positive-effective requirement ID must exist in config.requirements"
                )
            if allocation.effective_weight >= requirement.minimum_effective_weight:
                if (
                    len(candidates) >= config.maximum_witness_edges
                    or len(candidates) >= _IMPLEMENTATION_MAXIMUM_WITNESS_EDGES
                ):
                    raise ValueError(
                        "candidate witness edge count exceeds config.maximum_witness_edges"
                    )
                candidates.append(_candidate_edge_key(requirement_id, record))
    return tuple(sorted(candidates))
class _Dinic:
    __slots__ = ("_adjacency",)
    def __init__(self, node_count: int) -> None:
        self._adjacency: list[list[list[int]]] = [[] for _ in range(node_count)]
    def add_edge(self, source: int, target: int, capacity: int) -> None:
        forward = [target, len(self._adjacency[target]), capacity]
        reverse = [source, len(self._adjacency[source]), 0]
        self._adjacency[source].append(forward)
        self._adjacency[target].append(reverse)
    def _levels(self, source: int, sink: int) -> list[int]:
        levels = [-1] * len(self._adjacency)
        levels[source] = 0
        pending = deque((source,))
        while pending:
            node = pending.popleft()
            for target, _, capacity in self._adjacency[node]:
                if capacity > 0 and levels[target] < 0:
                    levels[target] = levels[node] + 1
                    pending.append(target)
        return levels if levels[sink] >= 0 else []
    def _send_one(
        self,
        source: int,
        sink: int,
        levels: list[int],
        indexes: list[int],
    ) -> int:
        nodes = [source]
        selected: list[int] = []
        limits = [_IMPLEMENTATION_MAXIMUM_WITNESS_EDGES]
        while nodes:
            node = nodes[-1]
            if node == sink:
                amount = limits[-1]
                for parent, edge_index in zip(nodes[:-1], selected, strict=True):
                    edge = self._adjacency[parent][edge_index]
                    edge[2] -= amount
                    self._adjacency[edge[0]][edge[1]][2] += amount
                return amount
            while indexes[node] < len(self._adjacency[node]):
                edge = self._adjacency[node][indexes[node]]
                if edge[2] > 0 and levels[edge[0]] == levels[node] + 1:
                    break
                indexes[node] += 1
            if indexes[node] == len(self._adjacency[node]):
                levels[node] = -1
                nodes.pop()
                if selected:
                    selected.pop()
                    limits.pop()
                    if nodes:
                        indexes[nodes[-1]] += 1
                continue
            edge_index = indexes[node]
            edge = self._adjacency[node][edge_index]
            selected.append(edge_index)
            nodes.append(edge[0])
            limits.append(min(limits[-1], edge[2]))
        return 0
    def maximum_flow(self, source: int, sink: int) -> int:
        total = 0
        while levels := self._levels(source, sink):
            indexes = [0] * len(self._adjacency)
            while amount := self._send_one(source, sink, levels, indexes):
                total += amount
        return total
def _objective_is_feasible(
    candidate_edges: tuple[_EdgeKey, ...],
    *,
    forced_edges: frozenset[_EdgeKey],
    forbidden_edges: frozenset[_EdgeKey],
    blocked_target: int,
    watch_target: int,
    record_by_edge: dict[_EdgeKey, TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
    max_assignments_per_evidence: int,
) -> bool:
    candidate_set = frozenset(candidate_edges)
    if forced_edges & forbidden_edges or not forced_edges <= candidate_set:
        return False
    record_counts: dict[_JoinKey, int] = {}
    pair_counts: dict[tuple[str, str], int] = {}
    requirement_counts: dict[str, int] = {}
    severity_counts = {"blocked": 0, "watch": 0}
    degrees: dict[str, int] = {}
    for edge in candidate_edges:
        degrees[edge[0]] = degrees.get(edge[0], 0) + 1
    demands = {
        requirement_id: min(requirement.minimum_witness_count, degrees.get(requirement_id, 0))
        for requirement_id, requirement in requirement_by_id.items()
    }
    for edge in sorted(forced_edges):
        record = record_by_edge.get(edge)
        if record is None:
            return False
        join = _join_key_from_record(record)
        pair = (edge[0], record.assessment_revision.independence_key)
        record_counts[join] = record_counts.get(join, 0) + 1
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
        requirement_counts[edge[0]] = requirement_counts.get(edge[0], 0) + 1
        severity = requirement_by_id[edge[0]].unmet_status
        severity_counts[severity] += 1
        if (
            record_counts[join] > max_assignments_per_evidence
            or pair_counts[pair] > 1
            or requirement_counts[edge[0]] > demands[edge[0]]
        ):
            return False
    remaining_targets = {
        "blocked": blocked_target - severity_counts["blocked"],
        "watch": watch_target - severity_counts["watch"],
    }
    if min(remaining_targets.values()) < 0:
        return False
    residual_edges = tuple(
        edge
        for edge in candidate_edges
        if edge not in forced_edges and edge not in forbidden_edges
    )
    source_key = ("terminal", "source")
    sink_key = ("terminal", "sink")
    super_source_key = ("terminal", "super-source")
    super_sink_key = ("terminal", "super-sink")
    evidence_keys = {
        _join_key_from_record(record_by_edge[edge]) for edge in residual_edges
    }
    pair_keys = {
        (edge[0], record_by_edge[edge].assessment_revision.independence_key)
        for edge in residual_edges
    }
    semantic_keys: set[tuple[str, ...]] = {
        source_key,
        sink_key,
        super_source_key,
        super_sink_key,
        ("severity", "blocked"),
        ("severity", "watch"),
    }
    semantic_keys.update(("evidence", *join) for join in evidence_keys)
    semantic_keys.update(("pair", *pair) for pair in pair_keys)
    semantic_keys.update(("requirement", value) for value in requirement_by_id)
    node_by_key = {key: index for index, key in enumerate(sorted(semantic_keys))}
    graph = _Dinic(len(node_by_key))
    source = node_by_key[source_key]
    sink = node_by_key[sink_key]
    for join in sorted(evidence_keys):
        graph.add_edge(
            source,
            node_by_key[("evidence", *join)],
            max_assignments_per_evidence - record_counts.get(join, 0),
        )
    for edge in residual_edges:
        record = record_by_edge[edge]
        join = _join_key_from_record(record)
        pair = (edge[0], record.assessment_revision.independence_key)
        graph.add_edge(
            node_by_key[("evidence", *join)],
            node_by_key[("pair", *pair)],
            1,
        )
    for pair in sorted(pair_keys):
        graph.add_edge(
            node_by_key[("pair", *pair)],
            node_by_key[("requirement", pair[0])],
            1 - pair_counts.get(pair, 0),
        )
    for requirement_id, requirement in sorted(requirement_by_id.items()):
        graph.add_edge(
            node_by_key[("requirement", requirement_id)],
            node_by_key[("severity", requirement.unmet_status)],
            demands[requirement_id] - requirement_counts.get(requirement_id, 0),
        )
    balances = {key: 0 for key in semantic_keys}
    for severity in ("blocked", "watch"):
        severity_key = ("severity", severity)
        lower = remaining_targets[severity]
        graph.add_edge(node_by_key[severity_key], sink, 0)
        balances[severity_key] -= lower
        balances[sink_key] += lower
    graph.add_edge(sink, source, sum(remaining_targets.values()))
    super_source = node_by_key[super_source_key]
    super_sink = node_by_key[super_sink_key]
    total_positive = 0
    for key in sorted(semantic_keys):
        balance = balances[key]
        if balance > 0:
            graph.add_edge(super_source, node_by_key[key], balance)
            total_positive += balance
        elif balance < 0:
            graph.add_edge(node_by_key[key], super_sink, -balance)
    return graph.maximum_flow(super_source, super_sink) == total_positive
def _severity_upper_bound(
    severity: str,
    candidate_edges: tuple[_EdgeKey, ...],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
) -> int:
    edge_limit = sum(
        requirement_by_id[edge[0]].unmet_status == severity for edge in candidate_edges
    )
    total = 0
    for requirement_id, requirement in requirement_by_id.items():
        if requirement.unmet_status != severity:
            continue
        degree = sum(edge[0] == requirement_id for edge in candidate_edges)
        total = min(edge_limit, total + min(requirement.minimum_witness_count, degree))
    return total
def _maximum_objective(
    candidate_edges: tuple[_EdgeKey, ...],
    *,
    record_by_edge: dict[_EdgeKey, TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
    max_assignments_per_evidence: int,
) -> tuple[int, int]:
    def feasible(blocked: int, watch: int) -> bool:
        return _objective_is_feasible(
            candidate_edges,
            forced_edges=frozenset(),
            forbidden_edges=frozenset(),
            blocked_target=blocked,
            watch_target=watch,
            record_by_edge=record_by_edge,
            requirement_by_id=requirement_by_id,
            max_assignments_per_evidence=max_assignments_per_evidence,
        )
    low, high = 0, _severity_upper_bound(
        "blocked", candidate_edges, requirement_by_id
    )
    while low < high:
        middle = (low + high + 1) // 2
        if feasible(middle, 0):
            low = middle
        else:
            high = middle - 1
    blocked = low
    low, high = 0, _severity_upper_bound("watch", candidate_edges, requirement_by_id)
    while low < high:
        middle = (low + high + 1) // 2
        if feasible(blocked, middle):
            low = middle
        else:
            high = middle - 1
    return blocked, low
def _canonical_optimum_edges(
    candidate_edges: tuple[_EdgeKey, ...],
    *,
    blocked_target: int,
    watch_target: int,
    record_by_edge: dict[_EdgeKey, TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
    max_assignments_per_evidence: int,
) -> tuple[_EdgeKey, ...]:
    forced: frozenset[_EdgeKey] = frozenset()
    forbidden: frozenset[_EdgeKey] = frozenset()
    for edge in sorted(candidate_edges):
        proposed = forced | {edge}
        if _objective_is_feasible(
            candidate_edges,
            forced_edges=proposed,
            forbidden_edges=forbidden,
            blocked_target=blocked_target,
            watch_target=watch_target,
            record_by_edge=record_by_edge,
            requirement_by_id=requirement_by_id,
            max_assignments_per_evidence=max_assignments_per_evidence,
        ):
            forced = proposed
        else:
            forbidden |= {edge}
    result = tuple(sorted(forced))
    severity_counts = {
        severity: sum(
            requirement_by_id[edge[0]].unmet_status == severity for edge in result
        )
        for severity in ("blocked", "watch")
    }
    if (
        len(result) != blocked_target + watch_target
        or severity_counts != {"blocked": blocked_target, "watch": watch_target}
    ):
        raise ValueError("internal witness matching invariant failed")
    return result
def build_team_evidence_requirement_coverage(
    allocation_input_records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceRequirementCoverage, ...]:
    records, canonical_allocations = _validate_witness_inputs(
        allocation_input_records,
        allocations,
        config,
    )
    candidates = _build_candidate_edges(
        records,
        canonical_allocations,
        config=config,
    )
    record_by_join = {_join_key_from_record(record): record for record in records}
    allocation_by_join = {
        _join_key_from_allocation(allocation): allocation
        for allocation in canonical_allocations
    }
    requirement_by_id = {
        requirement.requirement_id: requirement for requirement in config.requirements
    }
    record_by_edge = {
        edge: record_by_join[(edge[1], edge[4], edge[2], edge[3])]
        for edge in candidates
    }
    blocked_target, watch_target = _maximum_objective(
        candidates,
        record_by_edge=record_by_edge,
        requirement_by_id=requirement_by_id,
        max_assignments_per_evidence=config.max_requirement_assignments_per_evidence,
    )
    selected = _canonical_optimum_edges(
        candidates,
        blocked_target=blocked_target,
        watch_target=watch_target,
        record_by_edge=record_by_edge,
        requirement_by_id=requirement_by_id,
        max_assignments_per_evidence=config.max_requirement_assignments_per_evidence,
    )
    coverage: list[TeamEvidenceRequirementCoverage] = []
    for requirement in config.requirements:
        requirement_edges = tuple(
            edge for edge in selected if edge[0] == requirement.requirement_id
        )
        witnesses = tuple(
            TeamEvidenceRequirementWitness(
                requirement_id=edge[0],
                source_lineage_id=edge[1],
                capture_id=edge[4],
                evidence_revision_id=edge[2],
                assessment_revision_id=edge[3],
                independence_key=record_by_edge[edge].assessment_revision.independence_key,
                effective_weight=allocation_by_join[
                    (edge[1], edge[4], edge[2], edge[3])
                ].effective_weight,
                paper_only=True,
                report_only=True,
                readonly=True,
            )
            for edge in requirement_edges
        )
        assigned = len(witnesses)
        coverage.append(
            TeamEvidenceRequirementCoverage(
                requirement_id=requirement.requirement_id,
                minimum_witness_count=requirement.minimum_witness_count,
                assigned_witness_count=assigned,
                minimum_effective_weight=requirement.minimum_effective_weight,
                unmet_status=requirement.unmet_status,
                satisfied=assigned >= requirement.minimum_witness_count,
                witnesses=witnesses,
                paper_only=True,
                report_only=True,
                readonly=True,
            )
        )
    return tuple(coverage)
