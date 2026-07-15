from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Final, final
__all__ = (
    "TeamEvidenceSourceLineage",
    "TeamEvidenceCapture",
    "TeamEvidenceRevision",
    "TeamEvidenceAssessmentRevision",
    "TeamEvidenceAggregationRecord",
    "TeamEvidenceCurrentRevisionSelection",
    "TeamEvidenceAggregationInput",
    "TeamEvidenceRequirement",
    "TeamEvidenceAggregationConfig",
    "TeamEvidenceTemporalAssessment",
    "TeamEvidenceWeightAllocation",
    "TeamEvidenceRequirementWitness",
    "TeamEvidenceRequirementCoverage",
    "TeamEvidenceDiagnosticRow",
    "TeamEvidenceContradictionResult",
    "TeamEvidenceAggregationResult",
    "validate_team_evidence_aggregation_input_contract",
    "select_team_evidence_canonical_current_records",
    "select_team_evidence_canonical_capture_records",
)
_QUANTUM: Final = Decimal("0.000001")
_ZERO: Final = Decimal("0.000000")
_ONE: Final = Decimal("1.000000")
_DECIMAL_CONTEXT: Final = Context(prec=64, rounding=ROUND_HALF_EVEN)
_MAX_ASSIGNMENTS_PER_EVIDENCE: Final = 32
_MAX_RECORDS: Final = 128
_MAX_REQUIREMENTS: Final = 32
_MAX_REQUIREMENT_MEMBERSHIPS: Final = 1024
_MAX_WITNESS_EDGES: Final = 256
_IDENTIFIER_RE: Final = re.compile(r"[a-z0-9](?:[a-z0-9._:-]*[a-z0-9])?", re.ASCII)
_DIGEST_RE: Final = re.compile(r"[0-9a-f]{64}", re.ASCII)
_HARD_FLAGS: Final = ("paper_only", "report_only", "readonly")
_PUBLIC_CLASS_NAMES: Final = (
    "TeamEvidenceSourceLineage", "TeamEvidenceCapture", "TeamEvidenceRevision",
    "TeamEvidenceAssessmentRevision", "TeamEvidenceAggregationRecord",
    "TeamEvidenceCurrentRevisionSelection", "TeamEvidenceAggregationInput",
    "TeamEvidenceRequirement", "TeamEvidenceAggregationConfig",
    "TeamEvidenceTemporalAssessment", "TeamEvidenceWeightAllocation",
    "TeamEvidenceRequirementWitness", "TeamEvidenceRequirementCoverage",
    "TeamEvidenceDiagnosticRow", "TeamEvidenceContradictionResult",
    "TeamEvidenceAggregationResult",
)
_DISPOSITIONS: Final = (
    "not_current_revision", "duplicate_capture", "freshness_anchor_after_evaluation",
    "capture_after_evaluation", "evidence_revision_after_evaluation",
    "assessment_revision_after_evaluation", "stale", "capture_before_freshness_anchor",
    "capture_lag_exceeded", "zero_requested_weight", "independence_cap_exhausted",
    "correlation_cap_exhausted", "included",
)

class _ExactPublicDataclass:
    __slots__ = ()
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.__bases__ != (_ExactPublicDataclass,) or cls.__name__ not in _PUBLIC_CLASS_NAMES:
            raise TypeError("public team evidence dataclasses do not support subclassing")

def _exact_self(value: object, expected: type[object], path: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{path} must be exactly {expected.__name__}")

def _hard_flags(path: str, value: object) -> None:
    for name in _HARD_FLAGS:
        try:
            flag = getattr(value, name)
        except AttributeError as error:
            raise ValueError(f"{path}.{name} must be exact True") from error
        if flag is not True:
            raise ValueError(f"{path}.{name} must be exact True")

def _identifier(path: str, value: object) -> str:
    if type(value) is not str or len(value.encode("utf-8")) > 160 or _IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact canonical identifier")
    return value

def _digest(path: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact lowercase SHA-256 digest")
    return value

def _optional_identifier(path: str, value: object) -> str | None:
    return None if value is None else _identifier(path, value)

def _optional_digest(path: str, value: object) -> str | None:
    return None if value is None else _digest(path, value)

def _decimal(
    path: str,
    value: object,
    *,
    minimum: Decimal | None = None,
    maximum: Decimal | None = None,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{path} must be an exact finite Decimal")
    with localcontext(_DECIMAL_CONTEXT):
        try:
            if not value.is_finite():
                raise ValueError(f"{path} must be an exact finite Decimal")
            if minimum is not None and value < minimum:
                raise ValueError(f"{path} is below its raw bound")
            if maximum is not None and value > maximum:
                raise ValueError(f"{path} exceeds its raw bound")
            normalized = value.quantize(_QUANTUM)
        except InvalidOperation as error:
            raise ValueError(f"{path} must normalize to fixed-six Decimal") from error
        return _ZERO if normalized == _ZERO else normalized

def _decimal_less(left: Decimal, right: Decimal) -> bool:
    with localcontext(_DECIMAL_CONTEXT):
        return left < right

def _decimal_chain(*values: Decimal) -> bool:
    with localcontext(_DECIMAL_CONTEXT):
        return all(left <= right for left, right in zip(values, values[1:]))

def _ratio(path: str, value: object) -> Decimal:
    return _decimal(path, value, minimum=_ZERO, maximum=_ONE)
def _nonnegative_decimal(path: str, value: object) -> Decimal:
    return _decimal(path, value, minimum=_ZERO)
def _signed_decimal(path: str, value: object) -> Decimal:
    return _decimal(path, value)
def _datetime(path: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{path} must be an exact aware datetime")
    return value.astimezone(UTC)
def _positive_int(path: str, value: object, *, maximum: int | None = None) -> int:
    if type(value) is not int or value < 1 or (maximum is not None and value > maximum):
        suffix = "" if maximum is None else f" in 1..{maximum}"
        raise ValueError(f"{path} must be an exact positive int{suffix}")
    return value

def _nonnegative_int(path: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{path} must be an exact nonnegative int")
    return value

def _bool(path: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be an exact bool")
    return value
def _member(path: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{path} must be one of the closed statuses")
    return value
def _exact_tuple(path: str, value: object) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{path} must be an exact tuple")
    return value
def _identifier_tuple(path: str, value: object) -> tuple[str, ...]:
    items = tuple(_identifier(f"{path}[{index}]", item) for index, item in enumerate(_exact_tuple(path, value)))
    if len(set(items)) != len(items):
        raise ValueError(f"{path} contains duplicate identifiers")
    return tuple(sorted(items))
def _typed_tuple(path: str, value: object, expected: type[object]) -> tuple[object, ...]:
    items = _exact_tuple(path, value)
    for index, item in enumerate(items):
        if type(item) is not expected:
            raise ValueError(f"{path}[{index}] must be exactly {expected.__name__}")
        _canonical_instance(f"{path}[{index}]", item, expected)
    return items
def _predecessor_pair(path: str, predecessor_id: object, predecessor_digest: object) -> tuple[str | None, str | None]:
    normalized_id = _optional_identifier(f"{path}_id", predecessor_id)
    normalized_digest = _optional_digest(f"{path}_digest", predecessor_digest)
    if (normalized_id is None) != (normalized_digest is None):
        raise ValueError(f"{path}_id and {path}_digest must both be absent or present")
    return normalized_id, normalized_digest

def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )

def _selection_key(selection: TeamEvidenceCurrentRevisionSelection) -> tuple[str, str]:
    return selection.evidence_revision_id, selection.assessment_revision_id

def _witness_key(witness: TeamEvidenceRequirementWitness) -> tuple[str, str, str, str, str]:
    return (
        witness.requirement_id, witness.source_lineage_id, witness.evidence_revision_id,
        witness.assessment_revision_id, witness.capture_id,
    )

def _diagnostic_key(row: TeamEvidenceDiagnosticRow) -> tuple[object, ...]:
    return row.assessment_revision_id, row.evidence_revision_id, row.captured_at, row.capture_id, row.source_lineage_id

def _requirement_key(requirement: TeamEvidenceRequirement) -> str:
    return requirement.requirement_id

def _capture_key(capture: TeamEvidenceCapture) -> tuple[datetime, str, str]:
    return capture.captured_at, capture.capture_id, capture.capture_digest

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceSourceLineage(_ExactPublicDataclass):
    source_lineage_id: str
    source_lineage_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceSourceLineage, "source_lineage")
        object.__setattr__(self, "source_lineage_id", _identifier("source_lineage_id", self.source_lineage_id))
        object.__setattr__(self, "source_lineage_digest", _digest("source_lineage_digest", self.source_lineage_digest))
        _hard_flags("source_lineage", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceCapture(_ExactPublicDataclass):
    capture_id: str
    capture_digest: str
    source_lineage_id: str
    source_lineage_digest: str
    content_digest: str
    captured_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceCapture, "capture")
        for name in ("capture_id", "source_lineage_id"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        for name in ("capture_digest", "source_lineage_digest", "content_digest"):
            object.__setattr__(self, name, _digest(name, getattr(self, name)))
        object.__setattr__(self, "captured_at", _datetime("captured_at", self.captured_at))
        _hard_flags("capture", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceRevision(_ExactPublicDataclass):
    evidence_revision_id: str
    evidence_revision_digest: str
    previous_evidence_revision_id: str | None
    previous_evidence_revision_digest: str | None
    source_lineage_id: str
    source_lineage_digest: str
    content_digest: str
    requirement_ids: tuple[str, ...]
    freshness_anchor_at: datetime
    recorded_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceRevision, "evidence_revision")
        object.__setattr__(self, "evidence_revision_id", _identifier("evidence_revision_id", self.evidence_revision_id))
        object.__setattr__(self, "evidence_revision_digest", _digest("evidence_revision_digest", self.evidence_revision_digest))
        previous = _predecessor_pair("previous_evidence_revision", self.previous_evidence_revision_id, self.previous_evidence_revision_digest)
        object.__setattr__(self, "previous_evidence_revision_id", previous[0])
        object.__setattr__(self, "previous_evidence_revision_digest", previous[1])
        object.__setattr__(self, "source_lineage_id", _identifier("source_lineage_id", self.source_lineage_id))
        object.__setattr__(self, "source_lineage_digest", _digest("source_lineage_digest", self.source_lineage_digest))
        object.__setattr__(self, "content_digest", _digest("content_digest", self.content_digest))
        object.__setattr__(self, "requirement_ids", _identifier_tuple("requirement_ids", self.requirement_ids))
        object.__setattr__(self, "freshness_anchor_at", _datetime("freshness_anchor_at", self.freshness_anchor_at))
        object.__setattr__(self, "recorded_at", _datetime("recorded_at", self.recorded_at))
        _hard_flags("evidence_revision", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceAssessmentRevision(_ExactPublicDataclass):
    assessment_revision_id: str
    assessment_revision_digest: str
    previous_assessment_revision_id: str | None
    previous_assessment_revision_digest: str | None
    evidence_revision_id: str
    evidence_revision_digest: str
    assessed_at: datetime
    probability_yes: Decimal
    requested_weight: Decimal
    rationale_digest: str
    independence_key: str
    correlation_key: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceAssessmentRevision, "assessment_revision")
        object.__setattr__(self, "assessment_revision_id", _identifier("assessment_revision_id", self.assessment_revision_id))
        object.__setattr__(self, "assessment_revision_digest", _digest("assessment_revision_digest", self.assessment_revision_digest))
        previous = _predecessor_pair("previous_assessment_revision", self.previous_assessment_revision_id, self.previous_assessment_revision_digest)
        object.__setattr__(self, "previous_assessment_revision_id", previous[0])
        object.__setattr__(self, "previous_assessment_revision_digest", previous[1])
        object.__setattr__(self, "evidence_revision_id", _identifier("evidence_revision_id", self.evidence_revision_id))
        object.__setattr__(self, "evidence_revision_digest", _digest("evidence_revision_digest", self.evidence_revision_digest))
        object.__setattr__(self, "assessed_at", _datetime("assessed_at", self.assessed_at))
        object.__setattr__(self, "probability_yes", _ratio("probability_yes", self.probability_yes))
        object.__setattr__(self, "requested_weight", _ratio("requested_weight", self.requested_weight))
        object.__setattr__(self, "rationale_digest", _digest("rationale_digest", self.rationale_digest))
        object.__setattr__(self, "independence_key", _identifier("independence_key", self.independence_key))
        object.__setattr__(self, "correlation_key", _identifier("correlation_key", self.correlation_key))
        _hard_flags("assessment_revision", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceAggregationRecord(_ExactPublicDataclass):
    source_lineage: TeamEvidenceSourceLineage
    capture: TeamEvidenceCapture
    evidence_revision: TeamEvidenceRevision
    assessment_revision: TeamEvidenceAssessmentRevision
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceAggregationRecord, "record")
        for name, expected in (("source_lineage", TeamEvidenceSourceLineage), ("capture", TeamEvidenceCapture), ("evidence_revision", TeamEvidenceRevision), ("assessment_revision", TeamEvidenceAssessmentRevision)):
            value = getattr(self, name)
            if type(value) is not expected:
                raise ValueError(f"{name} must be exactly {expected.__name__}")
            _canonical_instance(name, value, expected)
        lineage = self.source_lineage
        for layer_name, layer in (("capture", self.capture), ("evidence_revision", self.evidence_revision)):
            if layer.source_lineage_id != lineage.source_lineage_id:
                raise ValueError(f"{layer_name}.source_lineage_id must match source_lineage.source_lineage_id")
            if layer.source_lineage_digest != lineage.source_lineage_digest:
                raise ValueError(f"{layer_name}.source_lineage_digest must match source_lineage.source_lineage_digest")
        if self.capture.content_digest != self.evidence_revision.content_digest:
            raise ValueError("capture.content_digest must match evidence_revision.content_digest")
        if self.assessment_revision.evidence_revision_id != self.evidence_revision.evidence_revision_id:
            raise ValueError("assessment_revision.evidence_revision_id must match evidence_revision.evidence_revision_id")
        if self.assessment_revision.evidence_revision_digest != self.evidence_revision.evidence_revision_digest:
            raise ValueError("assessment_revision.evidence_revision_digest must match evidence_revision.evidence_revision_digest")
        _hard_flags("record", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceCurrentRevisionSelection(_ExactPublicDataclass):
    evidence_revision_id: str
    evidence_revision_digest: str
    assessment_revision_id: str
    assessment_revision_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceCurrentRevisionSelection, "current_revision")
        for name in ("evidence_revision_id", "assessment_revision_id"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        for name in ("evidence_revision_digest", "assessment_revision_digest"):
            object.__setattr__(self, name, _digest(name, getattr(self, name)))
        _hard_flags("current_revision", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceAggregationInput(_ExactPublicDataclass):
    evaluated_at: datetime
    records: tuple[TeamEvidenceAggregationRecord, ...]
    current_revisions: tuple[TeamEvidenceCurrentRevisionSelection, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceAggregationInput, "aggregation_input")
        object.__setattr__(self, "evaluated_at", _datetime("evaluated_at", self.evaluated_at))
        records = _typed_tuple("records", self.records, TeamEvidenceAggregationRecord)
        if len({_record_key(item) for item in records}) != len(records):
            raise ValueError("records contains duplicate canonical record key")
        object.__setattr__(self, "records", tuple(sorted(records, key=_record_key)))
        selections = _typed_tuple("current_revisions", self.current_revisions, TeamEvidenceCurrentRevisionSelection)
        if len({_selection_key(item) for item in selections}) != len(selections):
            raise ValueError("current_revisions contains duplicate selected pair")
        object.__setattr__(self, "current_revisions", tuple(sorted(selections, key=_selection_key)))
        _hard_flags("aggregation_input", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceRequirement(_ExactPublicDataclass):
    requirement_id: str
    minimum_witness_count: int
    minimum_effective_weight: Decimal
    unmet_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceRequirement, "requirement")
        object.__setattr__(self, "requirement_id", _identifier("requirement_id", self.requirement_id))
        object.__setattr__(self, "minimum_witness_count", _positive_int("minimum_witness_count", self.minimum_witness_count))
        object.__setattr__(self, "minimum_effective_weight", _ratio("minimum_effective_weight", self.minimum_effective_weight))
        object.__setattr__(self, "unmet_status", _member("unmet_status", self.unmet_status, ("watch", "blocked")))
        _hard_flags("requirement", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceAggregationConfig(_ExactPublicDataclass):
    config_version: str
    max_evidence_age_seconds: Decimal
    max_capture_lag_seconds: Decimal
    independence_group_weight_cap: Decimal
    correlation_group_weight_cap: Decimal
    max_requirement_assignments_per_evidence: int
    contradiction_no_probability_max: Decimal
    contradiction_yes_probability_min: Decimal
    contradiction_watch_score: Decimal
    contradiction_block_score: Decimal
    publish_probability_floor: Decimal
    publish_probability_ceiling: Decimal
    maximum_records: int
    maximum_requirements: int
    maximum_requirement_memberships: int
    maximum_witness_edges: int
    requirements: tuple[TeamEvidenceRequirement, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceAggregationConfig, "config")
        object.__setattr__(self, "config_version", _identifier("config_version", self.config_version))
        for name in ("max_evidence_age_seconds", "max_capture_lag_seconds"):
            object.__setattr__(self, name, _nonnegative_decimal(name, getattr(self, name)))
        for name in ("independence_group_weight_cap", "correlation_group_weight_cap", "contradiction_no_probability_max", "contradiction_yes_probability_min", "contradiction_watch_score", "contradiction_block_score", "publish_probability_floor", "publish_probability_ceiling"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        maxima = (
            ("max_requirement_assignments_per_evidence", _MAX_ASSIGNMENTS_PER_EVIDENCE),
            ("maximum_records", _MAX_RECORDS), ("maximum_requirements", _MAX_REQUIREMENTS),
            ("maximum_requirement_memberships", _MAX_REQUIREMENT_MEMBERSHIPS),
            ("maximum_witness_edges", _MAX_WITNESS_EDGES),
        )
        for name, maximum in maxima:
            object.__setattr__(self, name, _positive_int(name, getattr(self, name), maximum=maximum))
        if not _decimal_less(self.contradiction_no_probability_max, self.contradiction_yes_probability_min):
            raise ValueError("config.contradiction probability bounds require canonical no < yes")
        if not _decimal_chain(self.contradiction_watch_score, self.contradiction_block_score):
            raise ValueError("config.contradiction_watch_score must not exceed contradiction_block_score")
        if not _decimal_chain(self.publish_probability_floor, self.publish_probability_ceiling):
            raise ValueError("config.publish_probability_floor must not exceed publish_probability_ceiling")
        requirements = _typed_tuple("requirements", self.requirements, TeamEvidenceRequirement)
        keys = tuple(item.requirement_id for item in requirements)
        if len(set(keys)) != len(keys):
            raise ValueError("requirements contains duplicate requirement_id")
        if len(requirements) > self.maximum_requirements:
            raise ValueError("requirements exceeds config.maximum_requirements")
        object.__setattr__(self, "requirements", tuple(sorted(requirements, key=_requirement_key)))
        _hard_flags("config", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceTemporalAssessment(_ExactPublicDataclass):
    capture_id: str
    evidence_revision_id: str
    assessment_revision_id: str
    evidence_age_seconds: Decimal
    capture_lag_seconds: Decimal
    effective_at_evaluation: bool
    captured_at_evaluation: bool
    evidence_revision_available_at_evaluation: bool
    assessment_revision_available_at_evaluation: bool
    fresh: bool
    timely: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceTemporalAssessment, "temporal_assessment")
        for name in ("capture_id", "evidence_revision_id", "assessment_revision_id"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        for name in ("evidence_age_seconds", "capture_lag_seconds"):
            object.__setattr__(self, name, _signed_decimal(name, getattr(self, name)))
        for name in ("effective_at_evaluation", "captured_at_evaluation", "evidence_revision_available_at_evaluation", "assessment_revision_available_at_evaluation", "fresh", "timely"):
            _bool(name, getattr(self, name))
        _hard_flags("temporal_assessment", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceWeightAllocation(_ExactPublicDataclass):
    source_lineage_id: str
    capture_id: str
    evidence_revision_id: str
    assessment_revision_id: str
    independence_key: str
    correlation_key: str
    requested_weight: Decimal
    independence_allocated_weight: Decimal
    effective_weight: Decimal
    independence_cap_applied: bool
    correlation_cap_applied: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceWeightAllocation, "allocation")
        for name in ("source_lineage_id", "capture_id", "evidence_revision_id", "assessment_revision_id", "independence_key", "correlation_key"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        for name in ("requested_weight", "independence_allocated_weight", "effective_weight"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if not _decimal_chain(self.effective_weight, self.independence_allocated_weight, self.requested_weight):
            raise ValueError("allocation weights require 0 <= effective <= independence <= requested")
        _bool("independence_cap_applied", self.independence_cap_applied)
        _bool("correlation_cap_applied", self.correlation_cap_applied)
        _hard_flags("allocation", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceRequirementWitness(_ExactPublicDataclass):
    requirement_id: str
    source_lineage_id: str
    capture_id: str
    evidence_revision_id: str
    assessment_revision_id: str
    independence_key: str
    effective_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceRequirementWitness, "witness")
        for name in ("requirement_id", "source_lineage_id", "capture_id", "evidence_revision_id", "assessment_revision_id", "independence_key"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        object.__setattr__(self, "effective_weight", _ratio("effective_weight", self.effective_weight))
        _hard_flags("witness", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceRequirementCoverage(_ExactPublicDataclass):
    requirement_id: str
    minimum_witness_count: int
    assigned_witness_count: int
    minimum_effective_weight: Decimal
    unmet_status: str
    satisfied: bool
    witnesses: tuple[TeamEvidenceRequirementWitness, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceRequirementCoverage, "coverage")
        object.__setattr__(self, "requirement_id", _identifier("requirement_id", self.requirement_id))
        object.__setattr__(self, "minimum_witness_count", _positive_int("minimum_witness_count", self.minimum_witness_count))
        object.__setattr__(self, "assigned_witness_count", _nonnegative_int("assigned_witness_count", self.assigned_witness_count))
        object.__setattr__(self, "minimum_effective_weight", _ratio("minimum_effective_weight", self.minimum_effective_weight))
        object.__setattr__(self, "unmet_status", _member("unmet_status", self.unmet_status, ("watch", "blocked")))
        _bool("satisfied", self.satisfied)
        witnesses = _typed_tuple("witnesses", self.witnesses, TeamEvidenceRequirementWitness)
        keys = tuple(_witness_key(item) for item in witnesses)
        if len(set(keys)) != len(keys):
            raise ValueError("witnesses contains duplicate witness identity")
        if any(item.requirement_id != self.requirement_id for item in witnesses):
            raise ValueError("witnesses.requirement_id must match coverage.requirement_id")
        with localcontext(_DECIMAL_CONTEXT):
            if any(item.effective_weight < self.minimum_effective_weight for item in witnesses):
                raise ValueError("witnesses.effective_weight must meet coverage.minimum_effective_weight")
        if self.assigned_witness_count != len(witnesses):
            raise ValueError("assigned_witness_count must equal len(witnesses)")
        if self.satisfied != (self.assigned_witness_count >= self.minimum_witness_count):
            raise ValueError("satisfied must match witness count coverage")
        object.__setattr__(self, "witnesses", tuple(sorted(witnesses, key=_witness_key)))
        _hard_flags("coverage", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceDiagnosticRow(_ExactPublicDataclass):
    source_lineage_id: str
    capture_id: str
    captured_at: datetime
    evidence_revision_id: str
    assessment_revision_id: str
    probability_yes: Decimal
    requested_weight: Decimal
    independence_allocated_weight: Decimal
    effective_weight: Decimal
    evidence_age_seconds: Decimal
    capture_lag_seconds: Decimal
    captured_at_evaluation: bool
    evidence_revision_available_at_evaluation: bool
    assessment_revision_available_at_evaluation: bool
    selected_current_revision: bool
    canonical_capture: bool
    disposition: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceDiagnosticRow, "diagnostic")
        for name in ("source_lineage_id", "capture_id", "evidence_revision_id", "assessment_revision_id"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        object.__setattr__(self, "captured_at", _datetime("captured_at", self.captured_at))
        for name in ("probability_yes", "requested_weight", "independence_allocated_weight", "effective_weight"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if not _decimal_chain(self.effective_weight, self.independence_allocated_weight, self.requested_weight):
            raise ValueError("diagnostic weights require 0 <= effective <= independence <= requested")
        for name in ("evidence_age_seconds", "capture_lag_seconds"):
            object.__setattr__(self, name, _signed_decimal(name, getattr(self, name)))
        for name in ("captured_at_evaluation", "evidence_revision_available_at_evaluation", "assessment_revision_available_at_evaluation", "selected_current_revision", "canonical_capture"):
            _bool(name, getattr(self, name))
        object.__setattr__(self, "disposition", _member("disposition", self.disposition, _DISPOSITIONS))
        _hard_flags("diagnostic", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceContradictionResult(_ExactPublicDataclass):
    yes_support_weight: Decimal
    no_support_weight: Decimal
    neutral_weight: Decimal
    contradiction_score: Decimal
    status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceContradictionResult, "contradiction")
        for name in ("yes_support_weight", "no_support_weight", "neutral_weight"):
            object.__setattr__(self, name, _nonnegative_decimal(name, getattr(self, name)))
        object.__setattr__(self, "contradiction_score", _ratio("contradiction_score", self.contradiction_score))
        object.__setattr__(self, "status", _member("status", self.status, ("none", "watch", "blocked")))
        _hard_flags("contradiction", self)

@final
@dataclass(frozen=True, slots=True)

class TeamEvidenceAggregationResult(_ExactPublicDataclass):
    evaluated_at: datetime
    config_version: str
    config_digest: str
    status: str
    diagnostic_record_count: int
    arithmetic_record_count: int
    requested_weight_total: Decimal
    independence_allocated_weight_total: Decimal
    effective_weight_total: Decimal
    arithmetic_probability_yes: Decimal | None
    publishable_probability_yes: Decimal | None
    contradiction: TeamEvidenceContradictionResult
    requirement_coverage: tuple[TeamEvidenceRequirementCoverage, ...]
    diagnostics: tuple[TeamEvidenceDiagnosticRow, ...]
    reason_codes: tuple[str, ...]
    core_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    def __post_init__(self) -> None:
        _exact_self(self, TeamEvidenceAggregationResult, "result")
        object.__setattr__(self, "evaluated_at", _datetime("evaluated_at", self.evaluated_at))
        object.__setattr__(self, "config_version", _identifier("config_version", self.config_version))
        object.__setattr__(self, "config_digest", _digest("config_digest", self.config_digest))
        object.__setattr__(self, "status", _member("status", self.status, ("ready", "watch", "blocked")))
        object.__setattr__(self, "diagnostic_record_count", _nonnegative_int("diagnostic_record_count", self.diagnostic_record_count))
        object.__setattr__(self, "arithmetic_record_count", _nonnegative_int("arithmetic_record_count", self.arithmetic_record_count))
        if self.arithmetic_record_count > self.diagnostic_record_count:
            raise ValueError("arithmetic_record_count must not exceed diagnostic_record_count")
        for name in ("requested_weight_total", "independence_allocated_weight_total", "effective_weight_total"):
            object.__setattr__(self, name, _nonnegative_decimal(name, getattr(self, name)))
        if not _decimal_chain(self.effective_weight_total, self.independence_allocated_weight_total, self.requested_weight_total):
            raise ValueError("result totals require effective <= independence <= requested")
        for name in ("arithmetic_probability_yes", "publishable_probability_yes"):
            value = getattr(self, name)
            object.__setattr__(self, name, None if value is None else _ratio(name, value))
        if type(self.contradiction) is not TeamEvidenceContradictionResult:
            raise ValueError("contradiction must be exactly TeamEvidenceContradictionResult")
        _canonical_instance("contradiction", self.contradiction, TeamEvidenceContradictionResult)
        coverage = _typed_tuple("requirement_coverage", self.requirement_coverage, TeamEvidenceRequirementCoverage)
        coverage_keys = tuple(item.requirement_id for item in coverage)
        if len(set(coverage_keys)) != len(coverage_keys):
            raise ValueError("requirement_coverage contains duplicate requirement_id")
        object.__setattr__(self, "requirement_coverage", tuple(sorted(coverage, key=_requirement_key)))
        diagnostics = _typed_tuple("diagnostics", self.diagnostics, TeamEvidenceDiagnosticRow)
        diagnostic_keys = tuple(_diagnostic_key(item) for item in diagnostics)
        if len(set(diagnostic_keys)) != len(diagnostic_keys):
            raise ValueError("diagnostics contains duplicate canonical record key")
        if self.diagnostic_record_count != len(diagnostics):
            raise ValueError("diagnostic_record_count must equal len(diagnostics)")
        object.__setattr__(self, "diagnostics", tuple(sorted(diagnostics, key=_diagnostic_key)))
        object.__setattr__(self, "reason_codes", _identifier_tuple("reason_codes", self.reason_codes))
        object.__setattr__(self, "core_digest", _digest("core_digest", self.core_digest))
        _hard_flags("result", self)

def _canonical_equal(value: object, normalized: object) -> bool:
    if type(value) is not type(normalized):
        return False
    if type(value) is Decimal:
        return value.as_tuple() == normalized.as_tuple()
    if type(value) is datetime:
        return value == normalized and value.tzinfo is UTC
    if type(value) is tuple:
        return len(value) == len(normalized) and all(_canonical_equal(left, right) for left, right in zip(value, normalized))
    if type(value).__name__ in _PUBLIC_CLASS_NAMES:
        return all(_canonical_equal(getattr(value, name), getattr(normalized, name)) for name in type(value).__slots__)
    return value == normalized

def _canonical_instance(path: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{path} must be exactly {expected.__name__}")
    _hard_flags(path, value)
    try:
        normalized = expected(**{name: getattr(value, name) for name in expected.__slots__})
        canonical = _canonical_equal(value, normalized)
    except AttributeError as error:
        raise ValueError(f"{path} must contain every canonical field") from error
    if not canonical:
        raise ValueError(f"{path} must contain exact canonical scalar and tuple values")

def _validate_chain(nodes: tuple[object, ...], kind: str) -> None:
    id_name = f"{kind}_revision_id"
    digest_name = f"{kind}_revision_digest"
    previous_id_name = f"previous_{kind}_revision_id"
    previous_digest_name = f"previous_{kind}_revision_digest"
    by_id = {getattr(node, id_name): node for node in nodes}
    roots: list[object] = []
    successors: dict[str, object] = {}
    for node in nodes:
        previous_id = getattr(node, previous_id_name)
        if previous_id is None:
            roots.append(node)
            continue
        predecessor = by_id.get(previous_id)
        if predecessor is None:
            raise ValueError(f"{kind}_revision.previous_{kind}_revision_id must reference the same lineage chain")
        if getattr(predecessor, digest_name) != getattr(node, previous_digest_name):
            raise ValueError(f"{kind}_revision.previous_{kind}_revision_digest must match predecessor")
        if previous_id in successors:
            raise ValueError(f"{kind}_revision graph must not fork")
        successors[previous_id] = node
    if len(roots) != 1:
        raise ValueError(f"{kind}_revision graph must have exactly one root")
    visited: set[str] = set()
    current: object | None = roots[0]
    while current is not None:
        current_id = getattr(current, id_name)
        if current_id in visited:
            raise ValueError(f"{kind}_revision graph must not contain a cycle")
        visited.add(current_id)
        current = successors.get(current_id)
    if len(visited) != len(nodes):
        raise ValueError(f"{kind}_revision graph must be one connected linear chain")
    for node in nodes:
        previous_id = getattr(node, previous_id_name)
        if previous_id is None:
            continue
        predecessor = by_id[previous_id]
        if kind == "evidence":
            if node.recorded_at < predecessor.recorded_at:
                raise ValueError("evidence_revision.recorded_at must be nondecreasing")
            content_changed = node.content_digest != predecessor.content_digest
            if not content_changed and node.requirement_ids == predecessor.requirement_ids:
                raise ValueError("evidence_revision successor must contain a semantic change")
            if node.freshness_anchor_at != predecessor.freshness_anchor_at and not content_changed:
                raise ValueError("evidence_revision.freshness_anchor_at change requires changed content_digest")
        else:
            if node.assessed_at < predecessor.assessed_at:
                raise ValueError("assessment_revision.assessed_at must be nondecreasing")
            with localcontext(_DECIMAL_CONTEXT):
                semantic = (node.evidence_revision_id, node.evidence_revision_digest, node.probability_yes, node.requested_weight, node.rationale_digest, node.independence_key, node.correlation_key)
                prior = (predecessor.evidence_revision_id, predecessor.evidence_revision_digest, predecessor.probability_yes, predecessor.requested_weight, predecessor.rationale_digest, predecessor.independence_key, predecessor.correlation_key)
                if semantic == prior:
                    raise ValueError("assessment_revision successor must contain a semantic change")

def _validated_input_indexes(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[tuple[TeamEvidenceAggregationRecord, ...], tuple[TeamEvidenceAggregationRecord, ...], tuple[TeamEvidenceAggregationRecord, ...]]:
    _canonical_instance("aggregation_input", aggregation_input, TeamEvidenceAggregationInput)
    _canonical_instance("config", config, TeamEvidenceAggregationConfig)
    for index, requirement in enumerate(config.requirements):
        _canonical_instance(f"config.requirements[{index}]", requirement, TeamEvidenceRequirement)
    for index, record in enumerate(aggregation_input.records):
        _canonical_instance(f"records[{index}]", record, TeamEvidenceAggregationRecord)
        _canonical_instance(f"records[{index}].source_lineage", record.source_lineage, TeamEvidenceSourceLineage)
        _canonical_instance(f"records[{index}].capture", record.capture, TeamEvidenceCapture)
        _canonical_instance(f"records[{index}].evidence_revision", record.evidence_revision, TeamEvidenceRevision)
        _canonical_instance(f"records[{index}].assessment_revision", record.assessment_revision, TeamEvidenceAssessmentRevision)
    for index, selection in enumerate(aggregation_input.current_revisions):
        _canonical_instance(f"current_revisions[{index}]", selection, TeamEvidenceCurrentRevisionSelection)
    records = tuple(sorted(aggregation_input.records, key=_record_key))
    if len(records) > config.maximum_records or len(records) > _MAX_RECORDS:
        raise ValueError("records exceeds config.maximum_records or 128")
    if len(config.requirements) > config.maximum_requirements or len(config.requirements) > _MAX_REQUIREMENTS:
        raise ValueError("config.requirements exceeds config.maximum_requirements or 32")
    record_keys = tuple(_record_key(record) for record in records)
    if len(set(record_keys)) != len(record_keys):
        raise ValueError("records contains duplicate canonical record key")
    pairs = tuple((record.capture.capture_id, record.assessment_revision.assessment_revision_id) for record in records)
    if len(set(pairs)) != len(pairs):
        raise ValueError("records contains duplicate capture_id and assessment_revision_id pair")
    layer_specs = (
        ("source_lineage", "source_lineage_id", "source_lineage_digest"),
        ("capture", "capture_id", "capture_digest"),
        ("evidence_revision", "evidence_revision_id", "evidence_revision_digest"),
        ("assessment_revision", "assessment_revision_id", "assessment_revision_digest"),
    )
    layer_maps: dict[str, dict[str, object]] = {}
    for path, id_name, digest_name in layer_specs:
        id_map: dict[str, object] = {}
        digest_map: dict[str, str] = {}
        for record in records:
            projection = getattr(record, path)
            identity = getattr(projection, id_name)
            projection_digest = getattr(projection, digest_name)
            with localcontext(_DECIMAL_CONTEXT):
                projection_conflict = identity in id_map and id_map[identity] != projection
            if projection_conflict:
                raise ValueError(f"{path}.{id_name} must determine one complete projection")
            if projection_digest in digest_map and digest_map[projection_digest] != identity:
                raise ValueError(f"{path}.{digest_name} must not alias two IDs")
            id_map[identity] = projection
            digest_map[projection_digest] = identity
        layer_maps[path] = id_map
    evidence_by_id = layer_maps["evidence_revision"]
    memberships = 0
    for revision in evidence_by_id.values():
        count = len(revision.requirement_ids)
        if count > config.max_requirement_assignments_per_evidence or count > _MAX_ASSIGNMENTS_PER_EVIDENCE:
            raise ValueError("evidence_revision.requirement_ids exceeds configured or hard maximum")
        memberships += count
    if memberships > config.maximum_requirement_memberships or memberships > _MAX_REQUIREMENT_MEMBERSHIPS:
        raise ValueError("distinct evidence revision requirement memberships exceeds configured or hard maximum")
    evidence_groups: defaultdict[str, list[object]] = defaultdict(list)
    for revision in evidence_by_id.values():
        evidence_groups[revision.source_lineage_id].append(revision)
    for nodes in evidence_groups.values():
        _validate_chain(tuple(nodes), "evidence")
    assessment_groups: defaultdict[str, list[object]] = defaultdict(list)
    for assessment in layer_maps["assessment_revision"].values():
        revision = evidence_by_id.get(assessment.evidence_revision_id)
        if revision is None or revision.evidence_revision_digest != assessment.evidence_revision_digest:
            raise ValueError("assessment_revision.evidence_revision must resolve exactly")
        assessment_groups[revision.source_lineage_id].append(assessment)
    for nodes in assessment_groups.values():
        _validate_chain(tuple(nodes), "assessment")
    captures_by_evidence: defaultdict[str, set[TeamEvidenceCapture]] = defaultdict(set)
    assessments_by_evidence: defaultdict[str, set[TeamEvidenceAssessmentRevision]] = defaultdict(set)
    for record in records:
        captures_by_evidence[record.evidence_revision.evidence_revision_id].add(record.capture)
        assessments_by_evidence[record.evidence_revision.evidence_revision_id].add(record.assessment_revision)
    canonical: dict[str, TeamEvidenceCapture] = {}
    for evidence_id, captures in captures_by_evidence.items():
        canonical[evidence_id] = min(captures, key=_capture_key)
        revision = evidence_by_id[evidence_id]
        if canonical[evidence_id].captured_at > revision.recorded_at:
            raise ValueError("evidence_revision canonical capture.captured_at must be at or before recorded_at")
        if any(revision.recorded_at > assessment.assessed_at for assessment in assessments_by_evidence[evidence_id]):
            raise ValueError("evidence_revision.recorded_at must be at or before assessment_revision.assessed_at")
    canonical_records = tuple(record for record in records if record.capture == canonical[record.evidence_revision.evidence_revision_id])
    current_records: list[TeamEvidenceAggregationRecord] = []
    selected_lineages: set[str] = set()
    for selection in aggregation_input.current_revisions:
        matches = tuple(record for record in records if record.evidence_revision.evidence_revision_id == selection.evidence_revision_id and record.evidence_revision.evidence_revision_digest == selection.evidence_revision_digest and record.assessment_revision.assessment_revision_id == selection.assessment_revision_id and record.assessment_revision.assessment_revision_digest == selection.assessment_revision_digest)
        if not matches:
            raise ValueError("current_revisions exact four-ID/digest pair must resolve to supplied records")
        lineage_id = matches[0].source_lineage.source_lineage_id
        if lineage_id in selected_lineages:
            raise ValueError("current_revisions permits at most one current pair per source lineage")
        selected_lineages.add(lineage_id)
        canonical_matches = tuple(record for record in matches if record.capture == canonical[selection.evidence_revision_id])
        if len(canonical_matches) != 1:
            raise ValueError("current_revisions selected pair must exist on the evidence-global canonical capture")
        current_records.append(canonical_matches[0])
    return records, tuple(sorted(current_records, key=_record_key)), canonical_records

def validate_team_evidence_aggregation_input_contract(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> None:
    _validated_input_indexes(aggregation_input, config=config)
    return None

def select_team_evidence_canonical_current_records(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceAggregationRecord, ...]:
    return _validated_input_indexes(aggregation_input, config=config)[1]

def select_team_evidence_canonical_capture_records(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceAggregationRecord, ...]:
    return _validated_input_indexes(aggregation_input, config=config)[2]
