from __future__ import annotations

from collections import deque
from typing import TypeVar, cast

from polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig, TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision, TeamEvidenceCapture, TeamEvidenceRequirement,
    TeamEvidenceRequirementCoverage, TeamEvidenceRequirementWitness,
    TeamEvidenceRevision, TeamEvidenceSourceLineage, TeamEvidenceWeightAllocation,
)


__all__ = ("build_team_evidence_requirement_coverage",)

_IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS = 32
_IMPLEMENTATION_MAXIMUM_REQUIREMENTS = 32
_IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS = 1024
_IMPLEMENTATION_MAXIMUM_WITNESS_EDGES = 256
_IDENTIFIER_EDGE_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
_IDENTIFIER_CHARACTERS = _IDENTIFIER_EDGE_CHARACTERS + "._:-"
_CANONICAL_ERRORS = (AttributeError, ArithmeticError, TypeError, ValueError)

_JoinKey = tuple[str, str, str, str]
_CandidateEdgeKey = tuple[str, str, str, str, str]
_SemanticKey = tuple[str, ...]
_BoundedEdge = tuple[_SemanticKey, _SemanticKey, int, int]
_T = TypeVar("_T")

def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id, record.evidence_revision.evidence_revision_id,
        record.capture.captured_at, record.capture.capture_id, record.source_lineage.source_lineage_id,
    )

def _join_key_from_record(record: TeamEvidenceAggregationRecord) -> _JoinKey:
    return (record.source_lineage.source_lineage_id, record.capture.capture_id,
            record.evidence_revision.evidence_revision_id,
            record.assessment_revision.assessment_revision_id)


def _join_key_from_allocation(allocation: TeamEvidenceWeightAllocation) -> _JoinKey:
    return (allocation.source_lineage_id, allocation.capture_id,
            allocation.evidence_revision_id, allocation.assessment_revision_id)


def _join_key_from_edge(edge: _CandidateEdgeKey) -> _JoinKey:
    return edge[1], edge[4], edge[2], edge[3]


def _candidate_edge_key(requirement_id: str, record: TeamEvidenceAggregationRecord) -> _CandidateEdgeKey:
    return (requirement_id, record.source_lineage.source_lineage_id,
            record.evidence_revision.evidence_revision_id,
            record.assessment_revision.assessment_revision_id, record.capture.capture_id)


def _validate_hard_flags(path: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{path}.{field_name} must preserve "
                             "paper_only=True, report_only=True, readonly=True")


def _is_identifier(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return (
        0 < len(encoded) <= 160
        and value[0] in _IDENTIFIER_EDGE_CHARACTERS
        and value[-1] in _IDENTIFIER_EDGE_CHARACTERS
        and all(character in _IDENTIFIER_CHARACTERS for character in value)
    )


def _canonical_equal(value: object, normalized: object) -> bool:
    if type(value) is not type(normalized):
        return False
    value_type = type(value)
    if value_type.__module__ == "decimal" and value_type.__name__ == "Decimal":
        return value.as_tuple() == normalized.as_tuple()
    if value_type.__module__ == "datetime" and value_type.__name__ == "datetime":
        return value == normalized and value.tzinfo is normalized.tzinfo
    if value_type is tuple:
        return len(value) == len(normalized) and all(
            _canonical_equal(left, right) for left, right in zip(value, normalized, strict=True))
    slots = getattr(value_type, "__slots__", None)
    if type(slots) is tuple:
        return all(_canonical_equal(getattr(value, name), getattr(normalized, name)) for name in slots)
    return value == normalized


def _canonical_reconstruction(path: str, value: _T) -> _T:
    try:
        slots = type(value).__slots__
        normalized = type(value)(**{name: getattr(value, name) for name in slots})
    except _CANONICAL_ERRORS:
        raise ValueError(f"{path} must be canonical") from None
    if not _canonical_equal(value, normalized):
        raise ValueError(f"{path} must be canonical")
    return cast(_T, normalized)


def _validate_record_layers(record: TeamEvidenceAggregationRecord, index: int) -> None:
    path = f"allocation_input_records[{index}]"
    _validate_hard_flags(path, record)
    layers = (
        ("source_lineage", record.source_lineage, TeamEvidenceSourceLineage),
        ("capture", record.capture, TeamEvidenceCapture),
        ("evidence_revision", record.evidence_revision, TeamEvidenceRevision),
        ("assessment_revision", record.assessment_revision, TeamEvidenceAssessmentRevision),
    )
    if any(type(layer) is not expected for _, layer, expected in layers):
        raise ValueError(f"{path} must be canonical")
    for layer_name, layer, _ in layers:
        _validate_hard_flags(f"{path}.{layer_name}", layer)


def _validate_resource_fields(config: TeamEvidenceAggregationConfig) -> None:
    maxima = (
        ("max_requirement_assignments_per_evidence", _IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS),
        ("maximum_records", 128),
        ("maximum_requirements", _IMPLEMENTATION_MAXIMUM_REQUIREMENTS),
        ("maximum_requirement_memberships", _IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS),
        ("maximum_witness_edges", _IMPLEMENTATION_MAXIMUM_WITNESS_EDGES),
    )
    for field_name, maximum in maxima:
        value = getattr(config, field_name, None)
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(f"config.{field_name} must be an exact int within its implementation maximum")


def _validate_requirements(config: TeamEvidenceAggregationConfig) -> tuple[TeamEvidenceRequirement, ...]:
    requirements = config.requirements
    if type(requirements) is not tuple:
        raise ValueError("config.requirements must contain exact unique requirements sorted by requirement_id")
    for index, requirement in enumerate(requirements):
        if type(requirement) is not TeamEvidenceRequirement:
            raise ValueError(f"config.requirements[{index}] must be exactly TeamEvidenceRequirement")
        _validate_hard_flags(f"config.requirements[{index}]", requirement)
    keys = tuple(requirement.requirement_id for requirement in requirements)
    if (
        len(requirements) > config.maximum_requirements
        or not all(_is_identifier(key) for key in keys)
        or len(set(keys)) != len(keys)
        or keys != tuple(sorted(keys))
    ):
        raise ValueError("config.requirements must contain exact unique requirements sorted by requirement_id")
    typed = cast(tuple[TeamEvidenceRequirement, ...], requirements)
    for index, requirement in enumerate(typed):
        _canonical_reconstruction(f"config.requirements[{index}]", requirement)
    return typed


def _validate_memberships(records: tuple[TeamEvidenceAggregationRecord, ...],
                          config: TeamEvidenceAggregationConfig) -> None:
    revision_by_id: dict[str, TeamEvidenceRevision] = {}
    membership_count = 0
    for record in records:
        revision = record.evidence_revision
        previous = revision_by_id.get(revision.evidence_revision_id)
        if previous is not None:
            if not _canonical_equal(previous, revision):
                raise ValueError("repeated evidence revision identity must have one exact projection")
            continue
        revision_by_id[revision.evidence_revision_id] = revision
        membership_count += len(revision.requirement_ids)
        if (
            membership_count > config.maximum_requirement_memberships
            or membership_count > _IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS
        ):
            raise ValueError("distinct evidence revision requirement memberships exceed "
                             "config.maximum_requirement_memberships or 1024")


def _validate_witness_inputs(
    allocation_input_records: object, allocations: object, config: object,
) -> tuple[tuple[TeamEvidenceAggregationRecord, ...], tuple[TeamEvidenceWeightAllocation, ...]]:
    if type(allocation_input_records) is not tuple:
        raise ValueError("allocation_input_records must be an exact tuple")
    if type(allocations) is not tuple:
        raise ValueError("allocations must be an exact tuple")
    if type(config) is not TeamEvidenceAggregationConfig:
        raise ValueError("config must be exactly TeamEvidenceAggregationConfig")
    typed_config = cast(TeamEvidenceAggregationConfig, config)
    for index, record in enumerate(allocation_input_records):
        if type(record) is not TeamEvidenceAggregationRecord:
            raise ValueError(f"allocation_input_records[{index}] must be exactly TeamEvidenceAggregationRecord")
    for index, allocation in enumerate(allocations):
        if type(allocation) is not TeamEvidenceWeightAllocation:
            raise ValueError(f"allocations[{index}] must be exactly TeamEvidenceWeightAllocation")
    records = cast(tuple[TeamEvidenceAggregationRecord, ...], allocation_input_records)
    typed_allocations = cast(tuple[TeamEvidenceWeightAllocation, ...], allocations)
    _validate_hard_flags("config", typed_config)
    for index, record in enumerate(records):
        _validate_record_layers(record, index)
    for index, allocation in enumerate(typed_allocations):
        _validate_hard_flags(f"allocations[{index}]", allocation)
    _validate_resource_fields(typed_config)
    if len(records) > typed_config.maximum_records or len(records) > 128:
        raise ValueError("allocation_input_records exceeds config.maximum_records or 128")
    if len(typed_allocations) > typed_config.maximum_records or len(typed_allocations) > 128:
        raise ValueError("allocations exceeds config.maximum_records or 128")
    _validate_requirements(typed_config)
    _canonical_reconstruction("config", typed_config)
    for index, record in enumerate(records):
        _canonical_reconstruction(f"allocation_input_records[{index}]", record)
    for index, allocation in enumerate(typed_allocations):
        _canonical_reconstruction(f"allocations[{index}]", allocation)
    _validate_memberships(records, typed_config)
    canonical_allocations = allocate_team_evidence_weights(allocation_input_records, config=typed_config)
    if typed_allocations != canonical_allocations:
        raise ValueError("allocations must equal canonical recomputation for allocation_input_records")
    _validate_allocation_join(records, canonical_allocations)
    return records, canonical_allocations


def _validate_allocation_join(records: tuple[TeamEvidenceAggregationRecord, ...],
                              allocations: tuple[TeamEvidenceWeightAllocation, ...]) -> None:
    record_keys = tuple(_join_key_from_record(record) for record in records)
    allocation_keys = tuple(_join_key_from_allocation(allocation) for allocation in allocations)
    if (
        len(set(record_keys)) != len(record_keys)
        or len(set(allocation_keys)) != len(allocation_keys)
        or tuple(sorted(record_keys)) != tuple(sorted(allocation_keys))
    ):
        raise ValueError("record/allocation join keys must match exactly")
    record_by_key = {_join_key_from_record(record): record for record in records}
    for allocation in allocations:
        record = record_by_key[_join_key_from_allocation(allocation)]
        assessment = record.assessment_revision
        if allocation.independence_key != assessment.independence_key:
            raise ValueError("allocation.independence_key must match assessment_revision.independence_key")
        if allocation.correlation_key != assessment.correlation_key:
            raise ValueError("allocation.correlation_key must match assessment_revision.correlation_key")
        if not _canonical_equal(allocation.requested_weight, assessment.requested_weight):
            raise ValueError("allocation.requested_weight must match assessment_revision.requested_weight")


def _build_candidate_edges(
    allocation_input_records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...], *, config: TeamEvidenceAggregationConfig,
) -> tuple[_CandidateEdgeKey, ...]:
    record_by_key = {
        _join_key_from_record(record): record for record in allocation_input_records
    }
    requirement_by_id = {
        requirement.requirement_id: requirement for requirement in config.requirements
    }
    positive = tuple(allocation for allocation in allocations if not allocation.effective_weight.is_zero())
    for allocation in positive:
        record = record_by_key[_join_key_from_allocation(allocation)]
        if any(
            requirement_id not in requirement_by_id
            for requirement_id in record.evidence_revision.requirement_ids
        ):
            raise ValueError("positive-effective requirement ID must exist in config.requirements")
    edges: list[_CandidateEdgeKey] = []
    for allocation in positive:
        record = record_by_key[_join_key_from_allocation(allocation)]
        for requirement_id in record.evidence_revision.requirement_ids:
            requirement = requirement_by_id[requirement_id]
            if allocation.effective_weight < requirement.minimum_effective_weight:
                continue
            if (
                len(edges) >= config.maximum_witness_edges
                or len(edges) >= _IMPLEMENTATION_MAXIMUM_WITNESS_EDGES
            ):
                raise ValueError(
                    "candidate witness edge count exceeds config.maximum_witness_edges"
                )
            edges.append(_candidate_edge_key(requirement_id, record))
    return tuple(sorted(edges))


class _Dinic:
    __slots__ = ("_adjacency",)

    def __init__(self, node_count: int) -> None:
        self._adjacency: list[list[list[int]]] = [[] for _ in range(node_count)]

    def add_edge(self, source: int, target: int, capacity: int) -> None:
        forward = [target, len(self._adjacency[target]), capacity]
        reverse = [source, len(self._adjacency[source]), 0]
        self._adjacency[source].append(forward)
        self._adjacency[target].append(reverse)

    def maximum_flow(self, source: int, sink: int) -> int:
        total = 0
        while True:
            levels = [-1] * len(self._adjacency)
            levels[source] = 0
            queue = deque((source,))
            while queue:
                node = queue.popleft()
                for target, _, capacity in self._adjacency[node]:
                    if capacity > 0 and levels[target] < 0:
                        levels[target] = levels[node] + 1
                        queue.append(target)
            if levels[sink] < 0:
                return total
            next_edge = [0] * len(self._adjacency)
            while True:
                nodes = [source]
                path: list[tuple[int, int]] = []
                while nodes:
                    node = nodes[-1]
                    if node == sink:
                        break
                    while next_edge[node] < len(self._adjacency[node]):
                        edge_index = next_edge[node]
                        edge = self._adjacency[node][edge_index]
                        if edge[2] > 0 and levels[edge[0]] == levels[node] + 1:
                            path.append((node, edge_index))
                            nodes.append(edge[0])
                            break
                        next_edge[node] += 1
                    else:
                        levels[node] = -1
                        nodes.pop()
                        if path:
                            parent, _ = path.pop()
                            next_edge[parent] += 1
                if not nodes:
                    break
                amount = min(self._adjacency[node][index][2] for node, index in path)
                for node, edge_index in path:
                    edge = self._adjacency[node][edge_index]
                    edge[2] -= amount
                    self._adjacency[edge[0]][edge[1]][2] += amount
                total += amount


def _objective_is_feasible(
    candidate_edges: tuple[_CandidateEdgeKey, ...], *, forced_edges: frozenset[_CandidateEdgeKey],
    forbidden_edges: frozenset[_CandidateEdgeKey], blocked_target: int, watch_target: int,
    record_by_edge: dict[_CandidateEdgeKey, TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement], max_assignments_per_evidence: int,
) -> bool:
    candidate_set = set(candidate_edges)
    if forced_edges & forbidden_edges or not forced_edges <= candidate_set:
        return False
    evidence_used: dict[_JoinKey, int] = {}
    pair_used: set[tuple[str, str]] = set()
    requirement_used: dict[str, int] = {}
    severity_used = {"blocked": 0, "watch": 0}
    for edge in sorted(forced_edges):
        record = record_by_edge[edge]
        requirement = requirement_by_id[edge[0]]
        join_key = _join_key_from_record(record)
        evidence_used[join_key] = evidence_used.get(join_key, 0) + 1
        pair = (edge[0], record.assessment_revision.independence_key)
        requirement_used[edge[0]] = requirement_used.get(edge[0], 0) + 1
        if (
            evidence_used[join_key] > max_assignments_per_evidence
            or pair in pair_used
            or requirement_used[edge[0]] > requirement.minimum_witness_count
        ):
            return False
        pair_used.add(pair)
        severity_used[requirement.unmet_status] += 1
    remaining_target = {
        "blocked": blocked_target - severity_used["blocked"],
        "watch": watch_target - severity_used["watch"],
    }
    if remaining_target["blocked"] < 0 or remaining_target["watch"] < 0:
        return False
    remaining_edges = tuple(
        edge
        for edge in candidate_edges
        if edge not in forced_edges and edge not in forbidden_edges
    )
    source_key: _SemanticKey = ("source",)
    sink_key: _SemanticKey = ("sink",)
    severity_key = {
        "blocked": ("severity", "blocked"),
        "watch": ("severity", "watch"),
    }
    bounded: list[_BoundedEdge] = []
    joins = tuple(sorted({_join_key_from_edge(edge) for edge in remaining_edges}))
    for join_key in joins:
        bounded.append((source_key, ("evidence", *join_key), 0,
                        max_assignments_per_evidence - evidence_used.get(join_key, 0)))
    pairs: set[tuple[str, str]] = set()
    for edge in remaining_edges:
        record = record_by_edge[edge]
        pair = (edge[0], record.assessment_revision.independence_key)
        pairs.add(pair)
        bounded.append((("evidence", *_join_key_from_record(record)), ("pair", *pair), 0, 1))
    for pair in sorted(pairs):
        bounded.append((("pair", *pair), ("requirement", pair[0]), 0,
                        0 if pair in pair_used else 1))
    requirement_ids = tuple(sorted({edge[0] for edge in remaining_edges}))
    for requirement_id in requirement_ids:
        requirement = requirement_by_id[requirement_id]
        bounded.append((("requirement", requirement_id), severity_key[requirement.unmet_status], 0,
                        requirement.minimum_witness_count - requirement_used.get(requirement_id, 0)))
    for status in ("blocked", "watch"):
        target = remaining_target[status]
        bounded.append((severity_key[status], sink_key, target, target))
    balance: dict[_SemanticKey, int] = {}
    residual: list[tuple[_SemanticKey, _SemanticKey, int]] = []
    for left, right, lower, upper in bounded:
        if lower < 0 or upper < lower:
            return False
        residual.append((left, right, upper - lower))
        balance[left] = balance.get(left, 0) - lower
        balance[right] = balance.get(right, 0) + lower
    target_total = remaining_target["blocked"] + remaining_target["watch"]
    residual.append((sink_key, source_key, target_total))
    super_source: _SemanticKey = ("super", "source")
    super_sink: _SemanticKey = ("super", "sink")
    required_flow = 0
    for node, amount in tuple(sorted(balance.items())):
        if amount > 0:
            residual.append((super_source, node, amount))
            required_flow += amount
        elif amount < 0:
            residual.append((node, super_sink, -amount))
    node_keys = {super_source, super_sink}
    for left, right, _ in residual:
        node_keys.add(left)
        node_keys.add(right)
    node_id = {key: index for index, key in enumerate(sorted(node_keys))}
    solver = _Dinic(len(node_id))
    for left, right, capacity in sorted(residual):
        solver.add_edge(node_id[left], node_id[right], capacity)
    return solver.maximum_flow(node_id[super_source], node_id[super_sink]) == required_flow


def _maximum_objective(
    candidate_edges: tuple[_CandidateEdgeKey, ...], *,
    record_by_edge: dict[_CandidateEdgeKey, TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement], max_assignments_per_evidence: int,
) -> tuple[int, int]:
    demand = {
        status: sum(
            requirement.minimum_witness_count
            for requirement in requirement_by_id.values()
            if requirement.unmet_status == status
        )
        for status in ("blocked", "watch")
    }
    edge_count = {
        status: sum(
            1
            for edge in candidate_edges
            if requirement_by_id[edge[0]].unmet_status == status
        )
        for status in ("blocked", "watch")
    }
    empty: frozenset[_CandidateEdgeKey] = frozenset()
    low, high = 0, min(demand["blocked"], edge_count["blocked"])
    while low < high:
        middle = (low + high + 1) // 2
        if _objective_is_feasible(
            candidate_edges,
            forced_edges=empty,
            forbidden_edges=empty,
            blocked_target=middle,
            watch_target=0,
            record_by_edge=record_by_edge,
            requirement_by_id=requirement_by_id,
            max_assignments_per_evidence=max_assignments_per_evidence,
        ):
            low = middle
        else:
            high = middle - 1
    blocked = low
    low, high = 0, min(demand["watch"], edge_count["watch"])
    while low < high:
        middle = (low + high + 1) // 2
        if _objective_is_feasible(
            candidate_edges,
            forced_edges=empty,
            forbidden_edges=empty,
            blocked_target=blocked,
            watch_target=middle,
            record_by_edge=record_by_edge,
            requirement_by_id=requirement_by_id,
            max_assignments_per_evidence=max_assignments_per_evidence,
        ):
            low = middle
        else:
            high = middle - 1
    return blocked, low


def _canonical_optimum_edges(
    candidate_edges: tuple[_CandidateEdgeKey, ...], *, blocked_target: int, watch_target: int,
    record_by_edge: dict[_CandidateEdgeKey, TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement], max_assignments_per_evidence: int,
) -> tuple[_CandidateEdgeKey, ...]:
    forced: set[_CandidateEdgeKey] = set()
    forbidden: set[_CandidateEdgeKey] = set()
    for edge in candidate_edges:
        trial = frozenset(forced | {edge})
        if _objective_is_feasible(
            candidate_edges,
            forced_edges=trial,
            forbidden_edges=frozenset(forbidden),
            blocked_target=blocked_target,
            watch_target=watch_target,
            record_by_edge=record_by_edge,
            requirement_by_id=requirement_by_id,
            max_assignments_per_evidence=max_assignments_per_evidence,
        ):
            forced.add(edge)
        else:
            forbidden.add(edge)
    severity_count = {
        status: sum(
            1
            for edge in forced
            if requirement_by_id[edge[0]].unmet_status == status
        )
        for status in ("blocked", "watch")
    }
    if (
        len(forced) != blocked_target + watch_target
        or severity_count["blocked"] != blocked_target
        or severity_count["watch"] != watch_target
        or not _objective_is_feasible(
            candidate_edges,
            forced_edges=frozenset(forced),
            forbidden_edges=frozenset(forbidden),
            blocked_target=blocked_target,
            watch_target=watch_target,
            record_by_edge=record_by_edge,
            requirement_by_id=requirement_by_id,
            max_assignments_per_evidence=max_assignments_per_evidence,
        )
    ):
        raise ValueError("internal witness matching invariant failed")
    return tuple(sorted(forced))


def _materialize_coverage(
    selected_edges: tuple[_CandidateEdgeKey, ...], records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...], config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceRequirementCoverage, ...]:
    record_by_key = {_join_key_from_record(record): record for record in records}
    allocation_by_key = {
        _join_key_from_allocation(allocation): allocation for allocation in allocations
    }
    rows: list[TeamEvidenceRequirementCoverage] = []
    for requirement in config.requirements:
        assigned = tuple(edge for edge in selected_edges if edge[0] == requirement.requirement_id)
        witnesses = tuple(
            TeamEvidenceRequirementWitness(
                requirement_id=edge[0],
                source_lineage_id=record_by_key[_join_key_from_edge(edge)].source_lineage.source_lineage_id,
                capture_id=record_by_key[_join_key_from_edge(edge)].capture.capture_id,
                evidence_revision_id=record_by_key[_join_key_from_edge(edge)].evidence_revision.evidence_revision_id,
                assessment_revision_id=record_by_key[_join_key_from_edge(edge)].assessment_revision.assessment_revision_id,
                independence_key=allocation_by_key[_join_key_from_edge(edge)].independence_key,
                effective_weight=allocation_by_key[_join_key_from_edge(edge)].effective_weight,
                paper_only=True,
                report_only=True,
                readonly=True,
            )
            for edge in assigned
        )
        count = len(witnesses)
        rows.append(
            TeamEvidenceRequirementCoverage(
                requirement_id=requirement.requirement_id,
                minimum_witness_count=requirement.minimum_witness_count,
                assigned_witness_count=count,
                minimum_effective_weight=requirement.minimum_effective_weight,
                unmet_status=requirement.unmet_status,
                satisfied=count >= requirement.minimum_witness_count,
                witnesses=witnesses,
                paper_only=True,
                report_only=True,
                readonly=True,
            )
        )
    return tuple(rows)


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
    candidate_edges = _build_candidate_edges(
        records,
        canonical_allocations,
        config=config,
    )
    record_by_key = {_join_key_from_record(record): record for record in records}
    record_by_edge = {
        edge: record_by_key[_join_key_from_edge(edge)] for edge in candidate_edges
    }
    requirement_by_id = {
        requirement.requirement_id: requirement for requirement in config.requirements
    }
    blocked_target, watch_target = _maximum_objective(
        candidate_edges,
        record_by_edge=record_by_edge,
        requirement_by_id=requirement_by_id,
        max_assignments_per_evidence=config.max_requirement_assignments_per_evidence,
    )
    selected_edges = _canonical_optimum_edges(
        candidate_edges,
        blocked_target=blocked_target,
        watch_target=watch_target,
        record_by_edge=record_by_edge,
        requirement_by_id=requirement_by_id,
        max_assignments_per_evidence=config.max_requirement_assignments_per_evidence,
    )
    return _materialize_coverage(
        selected_edges,
        records,
        canonical_allocations,
        config,
    )
