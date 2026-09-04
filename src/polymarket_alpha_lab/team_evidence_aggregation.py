from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights
from polymarket_alpha_lab.team_evidence_aggregation_codec import (
    team_evidence_aggregation_config_digest,
    team_evidence_aggregation_core_digest,
    validate_team_evidence_aggregation_core_digest,
)
from polymarket_alpha_lab.team_evidence_aggregation_temporal import assess_team_evidence_temporal
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    datetime as _CanonicalDatetime,
    TeamEvidenceAggregationConfig, TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord, TeamEvidenceAggregationResult,
    TeamEvidenceContradictionResult, TeamEvidenceDiagnosticRow,
    TeamEvidenceRequirementCoverage, TeamEvidenceRequirementWitness,
    TeamEvidenceTemporalAssessment,
    TeamEvidenceWeightAllocation,
    select_team_evidence_canonical_capture_records,
    select_team_evidence_canonical_current_records,
)
from polymarket_alpha_lab.team_evidence_aggregation_witness import build_team_evidence_requirement_coverage

__all__ = ("build_team_evidence_aggregation_result", "validate_team_evidence_aggregation_result")

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2")
_SIX_PLACES = Decimal("0.000001")
_EMPTY_CORE_DIGEST = "0" * 64
_ARITHMETIC_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_ALLOCATION_DISPOSITIONS = ("included", "independence_cap_exhausted", "correlation_cap_exhausted")
_INVARIANT_ERROR = "materialized aggregation result violates canonical invariants"
_RESULT_MISMATCH = "aggregation result must equal rematerialized result"
_RESULT_ERRORS = (AttributeError, DecimalException, TypeError, UnicodeError,
                  ValueError)
_PREFLIGHT_MAXIMUM_REQUIREMENTS = 32
_PREFLIGHT_MAXIMUM_DIAGNOSTICS = 128
_PREFLIGHT_MAXIMUM_WITNESSES = 256
_PREFLIGHT_MAXIMUM_REASON_CODES = 16

_RecordIdentity = tuple[str, str, str, str]
_SelectedPairIdentity = tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class _EvaluatedRecord:
    record: TeamEvidenceAggregationRecord
    temporal: TeamEvidenceTemporalAssessment
    selected_current_revision: bool
    canonical_capture: bool
    disposition: str | None


@dataclass(frozen=True, slots=True)
class _ArithmeticSummary:
    record_count: int
    requested_weight_total: Decimal
    independence_allocated_weight_total: Decimal
    effective_weight_total: Decimal
    probability_yes: Decimal | None
    contradiction: TeamEvidenceContradictionResult


def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (record.assessment_revision.assessment_revision_id,
            record.evidence_revision.evidence_revision_id,
            record.capture.captured_at, record.capture.capture_id,
            record.source_lineage.source_lineage_id)


def _diagnostic_key(row: TeamEvidenceDiagnosticRow) -> tuple[object, ...]:
    return (row.assessment_revision_id, row.evidence_revision_id,
            row.captured_at, row.capture_id, row.source_lineage_id)


def _record_identity(record: TeamEvidenceAggregationRecord) -> _RecordIdentity:
    return (record.source_lineage.source_lineage_id, record.capture.capture_id,
            record.evidence_revision.evidence_revision_id,
            record.assessment_revision.assessment_revision_id)


def _selected_pair_identity(record: TeamEvidenceAggregationRecord) -> _SelectedPairIdentity:
    return (record.source_lineage.source_lineage_id,
            record.evidence_revision.evidence_revision_id,
            record.assessment_revision.assessment_revision_id)


def _same_decimal_representation(left: object, right: Decimal) -> bool:
    return type(left) is Decimal and left.as_tuple() == right.as_tuple()


def _same_optional_decimal(left: object, right: Decimal | None) -> bool:
    if right is None:
        return left is None
    return _same_decimal_representation(left, right)


def _quantize_once(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("aggregation arithmetic must be finite Decimal")
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            normalized = value.quantize(_SIX_PLACES)
    except DecimalException:
        raise ValueError("aggregation arithmetic must be quantizable") from None
    return _ZERO if normalized.is_zero() else normalized


def _quantized_sum(values: tuple[Decimal, ...]) -> Decimal:
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            total = _ZERO
            for value in values:
                if type(value) is not Decimal or not value.is_finite():
                    raise ValueError(
                        "aggregation arithmetic must be finite Decimal"
                    )
                total += value
    except DecimalException:
        raise ValueError("aggregation arithmetic must be quantizable") from None
    return _quantize_once(total)


def _preallocation_disposition(
    record: TeamEvidenceAggregationRecord,
    temporal: TeamEvidenceTemporalAssessment,
    *,
    canonical_current_identities: frozenset[_RecordIdentity],
    selected_pair_identities: frozenset[_SelectedPairIdentity],
) -> str | None:
    if _selected_pair_identity(record) not in selected_pair_identities:
        return "not_current_revision"
    if _record_identity(record) not in canonical_current_identities:
        return "duplicate_capture"
    if not temporal.effective_at_evaluation:
        return "freshness_anchor_after_evaluation"
    if not temporal.captured_at_evaluation:
        return "capture_after_evaluation"
    if not temporal.evidence_revision_available_at_evaluation:
        return "evidence_revision_after_evaluation"
    if not temporal.assessment_revision_available_at_evaluation:
        return "assessment_revision_after_evaluation"
    if not temporal.fresh:
        return "stale"
    with localcontext(_ARITHMETIC_CONTEXT):
        if temporal.capture_lag_seconds < _ZERO:
            return "capture_before_freshness_anchor"
    if not temporal.timely:
        return "capture_lag_exceeded"
    with localcontext(_ARITHMETIC_CONTEXT):
        if record.assessment_revision.requested_weight == _ZERO:
            return "zero_requested_weight"
    return None


def _evaluate_records(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    canonical_capture_identities: frozenset[_RecordIdentity],
    canonical_current_identities: frozenset[_RecordIdentity],
    selected_pair_identities: frozenset[_SelectedPairIdentity],
    config: TeamEvidenceAggregationConfig,
) -> tuple[_EvaluatedRecord, ...]:
    evaluated: list[_EvaluatedRecord] = []
    for record in sorted(aggregation_input.records, key=_record_key):
        temporal = assess_team_evidence_temporal(
            record, evaluated_at=aggregation_input.evaluated_at, config=config)
        evaluated.append(
            _EvaluatedRecord(
                record=record, temporal=temporal,
                selected_current_revision=_selected_pair_identity(record)
                in selected_pair_identities,
                canonical_capture=_record_identity(record)
                in canonical_capture_identities,
                disposition=_preallocation_disposition(
                    record, temporal,
                    canonical_current_identities=canonical_current_identities,
                    selected_pair_identities=selected_pair_identities)))
    return tuple(evaluated)


def _final_candidate_disposition(allocation: TeamEvidenceWeightAllocation) -> str:
    with localcontext(_ARITHMETIC_CONTEXT):
        if allocation.independence_allocated_weight == _ZERO:
            return "independence_cap_exhausted"
        if allocation.effective_weight == _ZERO:
            return "correlation_cap_exhausted"
    return "included"


def _require_materialized_invariant(condition: bool) -> None:
    if not condition:
        raise ValueError(_INVARIANT_ERROR)


def _require_config_coverage_projection(
    coverage: tuple[TeamEvidenceRequirementCoverage, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> None:
    _require_materialized_invariant(
        type(coverage) is tuple and len(coverage) == len(config.requirements))
    for row, requirement in zip(coverage, config.requirements, strict=True):
        _require_materialized_invariant(
            type(row) is TeamEvidenceRequirementCoverage
            and type(row.requirement_id) is str
            and row.requirement_id == requirement.requirement_id
            and type(row.minimum_witness_count) is int
            and row.minimum_witness_count == requirement.minimum_witness_count
            and _same_decimal_representation(
                row.minimum_effective_weight,
                requirement.minimum_effective_weight)
            and type(row.unmet_status) is str
            and row.unmet_status == requirement.unmet_status)


def _all_exact(expected_type: type[object], values: tuple[object, ...]) -> bool:
    return all(type(value) is expected_type for value in values)


def _exact_contradiction_shape(value: object) -> bool:
    return (
        type(value) is TeamEvidenceContradictionResult
        and _all_exact(Decimal, (
            value.yes_support_weight, value.no_support_weight,
            value.neutral_weight, value.contradiction_score))
        and type(value.status) is str
        and _all_exact(bool, (
            value.paper_only, value.report_only, value.readonly)))


def _exact_witness_shape(value: object) -> bool:
    return (
        type(value) is TeamEvidenceRequirementWitness
        and _all_exact(str, (
            value.requirement_id, value.source_lineage_id, value.capture_id,
            value.evidence_revision_id, value.assessment_revision_id,
            value.independence_key))
        and type(value.effective_weight) is Decimal
        and _all_exact(bool, (
            value.paper_only, value.report_only, value.readonly)))


def _exact_coverage_shape(value: object) -> bool:
    return (
        type(value) is TeamEvidenceRequirementCoverage
        and _all_exact(str, (value.requirement_id, value.unmet_status))
        and _all_exact(int, (
            value.minimum_witness_count, value.assigned_witness_count))
        and type(value.minimum_effective_weight) is Decimal
        and type(value.witnesses) is tuple
        and _all_exact(bool, (
            value.satisfied, value.paper_only, value.report_only,
            value.readonly)))


def _exact_diagnostic_shape(value: object) -> bool:
    return (
        type(value) is TeamEvidenceDiagnosticRow
        and _all_exact(str, (
            value.source_lineage_id, value.capture_id,
            value.evidence_revision_id, value.assessment_revision_id,
            value.disposition))
        and type(value.captured_at) is _CanonicalDatetime
        and _all_exact(Decimal, (
            value.probability_yes, value.requested_weight,
            value.independence_allocated_weight, value.effective_weight,
            value.evidence_age_seconds, value.capture_lag_seconds))
        and _all_exact(bool, (
            value.captured_at_evaluation,
            value.evidence_revision_available_at_evaluation,
            value.assessment_revision_available_at_evaluation,
            value.selected_current_revision, value.canonical_capture,
            value.paper_only, value.report_only, value.readonly)))


def _exact_result_shape(result: TeamEvidenceAggregationResult) -> bool:
    return (
        type(result.evaluated_at) is _CanonicalDatetime
        and _all_exact(str, (
            result.config_version, result.config_digest, result.status,
            result.core_digest))
        and _all_exact(int, (
            result.diagnostic_record_count, result.arithmetic_record_count))
        and _all_exact(Decimal, (
            result.requested_weight_total,
            result.independence_allocated_weight_total,
            result.effective_weight_total))
        and (result.arithmetic_probability_yes is None
             or type(result.arithmetic_probability_yes) is Decimal)
        and (result.publishable_probability_yes is None
             or type(result.publishable_probability_yes) is Decimal)
        and type(result.requirement_coverage) is tuple
        and type(result.diagnostics) is tuple
        and type(result.reason_codes) is tuple
        and _all_exact(bool, (
            result.paper_only, result.report_only, result.readonly)))


def _preflight_result_shape(result: TeamEvidenceAggregationResult) -> None:
    _require_materialized_invariant(
        _exact_result_shape(result)
        and _exact_contradiction_shape(result.contradiction))
    coverage = result.requirement_coverage
    diagnostics = result.diagnostics
    reason_codes = result.reason_codes
    _require_materialized_invariant(
        len(coverage) <= _PREFLIGHT_MAXIMUM_REQUIREMENTS
        and len(diagnostics) <= _PREFLIGHT_MAXIMUM_DIAGNOSTICS
        and len(reason_codes) <= _PREFLIGHT_MAXIMUM_REASON_CODES)
    _require_materialized_invariant(
        all(type(code) is str for code in reason_codes))
    witness_count = 0
    for row in coverage:
        _require_materialized_invariant(_exact_coverage_shape(row))
        witnesses = row.witnesses
        witness_count += len(witnesses)
        _require_materialized_invariant(
            witness_count <= _PREFLIGHT_MAXIMUM_WITNESSES)
        for witness in witnesses:
            _require_materialized_invariant(_exact_witness_shape(witness))
    for row in diagnostics:
        _require_materialized_invariant(_exact_diagnostic_shape(row))


def _build_diagnostics(
    evaluated_records: tuple[_EvaluatedRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...],
) -> tuple[TeamEvidenceDiagnosticRow, ...]:
    rows: list[TeamEvidenceDiagnosticRow] = []
    allocation_index = 0
    for evaluated in evaluated_records:
        record = evaluated.record
        temporal = evaluated.temporal
        if evaluated.disposition is None:
            _require_materialized_invariant(allocation_index < len(allocations))
            allocation = allocations[allocation_index]
            allocation_index += 1
            independence_weight = allocation.independence_allocated_weight
            effective_weight = allocation.effective_weight
            disposition = _final_candidate_disposition(allocation)
        else:
            independence_weight = _ZERO
            effective_weight = _ZERO
            disposition = evaluated.disposition
        rows.append(
            TeamEvidenceDiagnosticRow(
                source_lineage_id=record.source_lineage.source_lineage_id,
                capture_id=record.capture.capture_id, captured_at=record.capture.captured_at,
                evidence_revision_id=record.evidence_revision.evidence_revision_id,
                assessment_revision_id=record.assessment_revision.assessment_revision_id,
                probability_yes=record.assessment_revision.probability_yes,
                requested_weight=record.assessment_revision.requested_weight,
                independence_allocated_weight=independence_weight,
                effective_weight=effective_weight,
                evidence_age_seconds=temporal.evidence_age_seconds,
                capture_lag_seconds=temporal.capture_lag_seconds,
                captured_at_evaluation=temporal.captured_at_evaluation,
                evidence_revision_available_at_evaluation=
                temporal.evidence_revision_available_at_evaluation,
                assessment_revision_available_at_evaluation=
                temporal.assessment_revision_available_at_evaluation,
                selected_current_revision=evaluated.selected_current_revision,
                canonical_capture=evaluated.canonical_capture,
                disposition=disposition))
    _require_materialized_invariant(allocation_index == len(allocations))
    return tuple(rows)


def _weighted_probability(included: tuple[TeamEvidenceDiagnosticRow, ...]) -> Decimal | None:
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            numerator = _ZERO
            denominator = _ZERO
            for row in included:
                numerator += row.probability_yes * row.effective_weight
                denominator += row.effective_weight
            if denominator == _ZERO:
                return None
            probability = numerator / denominator
            if probability < _ZERO or probability > _ONE:
                raise ValueError("arithmetic_probability_yes must be within canonical probability bounds")
    except DecimalException:
        raise ValueError("aggregation arithmetic must be quantizable") from None
    return _quantize_once(probability)


def _build_contradiction(
    included: tuple[TeamEvidenceDiagnosticRow, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceContradictionResult:
    yes_values: list[Decimal] = []
    no_values: list[Decimal] = []
    neutral_values: list[Decimal] = []
    with localcontext(_ARITHMETIC_CONTEXT):
        for row in included:
            if row.probability_yes <= config.contradiction_no_probability_max:
                no_values.append(row.effective_weight)
            elif row.probability_yes >= config.contradiction_yes_probability_min:
                yes_values.append(row.effective_weight)
            else:
                neutral_values.append(row.effective_weight)
    yes_weight = _quantized_sum(tuple(yes_values))
    no_weight = _quantized_sum(tuple(no_values))
    neutral_weight = _quantized_sum(tuple(neutral_values))
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            if yes_weight == _ZERO or no_weight == _ZERO:
                score, status = _ZERO, "none"
            else:
                score = _quantize_once(_TWO * min(yes_weight, no_weight)
                                       / (yes_weight + no_weight))
                if score >= config.contradiction_block_score:
                    status = "blocked"
                elif score >= config.contradiction_watch_score:
                    status = "watch"
                else:
                    status = "none"
    except DecimalException:
        raise ValueError("aggregation arithmetic must be quantizable") from None
    return TeamEvidenceContradictionResult(
        yes_support_weight=yes_weight, no_support_weight=no_weight,
        neutral_weight=neutral_weight, contradiction_score=score, status=status)


def _summarize_arithmetic(
    diagnostics: tuple[TeamEvidenceDiagnosticRow, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> _ArithmeticSummary:
    allocation_rows = tuple(row for row in diagnostics
                            if row.disposition in _ALLOCATION_DISPOSITIONS)
    included = tuple(row for row in diagnostics if row.disposition == "included")
    return _ArithmeticSummary(
        record_count=len(included),
        requested_weight_total=_quantized_sum(tuple(row.requested_weight
                                                     for row in allocation_rows)),
        independence_allocated_weight_total=_quantized_sum(tuple(
            row.independence_allocated_weight for row in allocation_rows)),
        effective_weight_total=_quantized_sum(tuple(row.effective_weight
                                                     for row in included)),
        probability_yes=_weighted_probability(included),
        contradiction=_build_contradiction(included, config=config),
    )


def _derive_status_fields(
    probability_yes: Decimal | None,
    contradiction: TeamEvidenceContradictionResult,
    coverage: tuple[TeamEvidenceRequirementCoverage, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[str, Decimal | None, tuple[str, ...]]:
    unmet_blocked = any(not row.satisfied and row.unmet_status == "blocked"
                        for row in coverage)
    unmet_watch = any(not row.satisfied and row.unmet_status == "watch"
                      for row in coverage)
    blocked = probability_yes is None or unmet_blocked or contradiction.status == "blocked"
    watch = unmet_watch or contradiction.status == "watch"
    status = "blocked" if blocked else "watch" if watch else "ready"
    codes: set[str] = set()
    if probability_yes is None:
        codes.add("no_arithmetic_evidence")
    if unmet_blocked:
        codes.add("blocking_requirement_unmet")
    if unmet_watch:
        codes.add("watch_requirement_unmet")
    if contradiction.status == "blocked":
        codes.add("contradiction_blocked")
    elif contradiction.status == "watch":
        codes.add("contradiction_watch")
    publishable: Decimal | None = None
    if status == "ready":
        codes.add("aggregation_ready")
        _require_materialized_invariant(probability_yes is not None)
        with localcontext(_ARITHMETIC_CONTEXT):
            if probability_yes < config.publish_probability_floor:
                publishable = config.publish_probability_floor
                codes.add("publish_probability_floor_applied")
            elif probability_yes > config.publish_probability_ceiling:
                publishable = config.publish_probability_ceiling
                codes.add("publish_probability_ceiling_applied")
            else:
                publishable = probability_yes
    return status, publishable, tuple(sorted(codes))


def _validate_materialized_result_invariants(
    result: TeamEvidenceAggregationResult,
    *,
    config: TeamEvidenceAggregationConfig,
    expected_config_digest: str,
) -> None:
    _require_materialized_invariant(
        type(result) is TeamEvidenceAggregationResult
        and result.paper_only is True and result.report_only is True
        and result.readonly is True)
    _require_materialized_invariant(result.config_version == config.config_version)
    _require_materialized_invariant(result.config_digest == expected_config_digest)
    coverage = result.requirement_coverage
    _require_config_coverage_projection(coverage, config=config)
    diagnostics = result.diagnostics
    _require_materialized_invariant(type(diagnostics) is tuple and all(
        type(row) is TeamEvidenceDiagnosticRow for row in diagnostics))
    diagnostic_keys = tuple(_diagnostic_key(row) for row in diagnostics)
    _require_materialized_invariant(
        diagnostic_keys == tuple(sorted(diagnostic_keys))
        and len(set(diagnostic_keys)) == len(diagnostic_keys)
        and type(result.diagnostic_record_count) is int
        and result.diagnostic_record_count == len(diagnostics))
    with localcontext(_ARITHMETIC_CONTEXT):
        for row in diagnostics:
            _require_materialized_invariant(row.paper_only is True
                                            and row.report_only is True
                                            and row.readonly is True)
            if row.disposition not in _ALLOCATION_DISPOSITIONS:
                _require_materialized_invariant(
                    _same_decimal_representation(row.independence_allocated_weight, _ZERO)
                    and _same_decimal_representation(row.effective_weight, _ZERO))
            elif row.disposition == "independence_cap_exhausted":
                _require_materialized_invariant(
                    row.requested_weight > _ZERO
                    and _same_decimal_representation(row.independence_allocated_weight, _ZERO)
                    and _same_decimal_representation(row.effective_weight, _ZERO))
            elif row.disposition == "correlation_cap_exhausted":
                _require_materialized_invariant(
                    row.requested_weight > _ZERO
                    and row.independence_allocated_weight > _ZERO
                    and _same_decimal_representation(row.effective_weight, _ZERO))
            else:
                _require_materialized_invariant(row.effective_weight > _ZERO)
    summary = _summarize_arithmetic(diagnostics, config=config)
    _require_materialized_invariant(
        type(result.arithmetic_record_count) is int
        and result.arithmetic_record_count == summary.record_count
        and _same_decimal_representation(result.requested_weight_total,
                                         summary.requested_weight_total)
        and _same_decimal_representation(result.independence_allocated_weight_total,
                                         summary.independence_allocated_weight_total)
        and _same_decimal_representation(result.effective_weight_total,
                                         summary.effective_weight_total)
        and _same_optional_decimal(result.arithmetic_probability_yes,
                                   summary.probability_yes)
        and result.contradiction == summary.contradiction)
    status, publishable, reason_codes = _derive_status_fields(
        summary.probability_yes, summary.contradiction,
        coverage, config=config)
    _require_materialized_invariant(
        result.status == status
        and _same_optional_decimal(result.publishable_probability_yes, publishable)
        and result.reason_codes == reason_codes)


def _materialize_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult:
    canonical_capture_records = select_team_evidence_canonical_capture_records(
        aggregation_input, config=config)
    canonical_current_records = select_team_evidence_canonical_current_records(
        aggregation_input, config=config)
    canonical_capture_identities = frozenset(_record_identity(record)
                                             for record in canonical_capture_records)
    canonical_current_identities = frozenset(_record_identity(record)
                                             for record in canonical_current_records)
    selected_pair_identities = frozenset(_selected_pair_identity(record)
                                         for record in canonical_current_records)
    evaluated_records = _evaluate_records(
        aggregation_input,
        canonical_capture_identities=canonical_capture_identities,
        canonical_current_identities=canonical_current_identities,
        selected_pair_identities=selected_pair_identities,
        config=config,
    )
    allocation_input_records = tuple(
        evaluated.record
        for evaluated in evaluated_records
        if evaluated.disposition is None
    )
    allocations = allocate_team_evidence_weights(allocation_input_records, config=config)
    coverage = build_team_evidence_requirement_coverage(
        allocation_input_records, allocations, config=config)
    _require_config_coverage_projection(coverage, config=config)
    diagnostics = _build_diagnostics(evaluated_records, allocations)
    summary = _summarize_arithmetic(diagnostics, config=config)
    status, publishable, reason_codes = _derive_status_fields(
        summary.probability_yes, summary.contradiction, coverage, config=config)
    config_digest = team_evidence_aggregation_config_digest(config)
    provisional = TeamEvidenceAggregationResult(
        evaluated_at=aggregation_input.evaluated_at, config_version=config.config_version,
        config_digest=config_digest, status=status,
        diagnostic_record_count=len(diagnostics),
        arithmetic_record_count=summary.record_count,
        requested_weight_total=summary.requested_weight_total,
        independence_allocated_weight_total=summary.independence_allocated_weight_total,
        effective_weight_total=summary.effective_weight_total,
        arithmetic_probability_yes=summary.probability_yes,
        publishable_probability_yes=publishable,
        contradiction=summary.contradiction, requirement_coverage=coverage,
        diagnostics=diagnostics, reason_codes=reason_codes,
        core_digest=_EMPTY_CORE_DIGEST)
    core_digest = team_evidence_aggregation_core_digest(provisional)
    final = replace(provisional, core_digest=core_digest)
    _validate_materialized_result_invariants(
        final, config=config, expected_config_digest=config_digest)
    validate_team_evidence_aggregation_core_digest(final)
    return final


def build_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult:
    return _materialize_team_evidence_aggregation_result(aggregation_input, config=config)


def validate_team_evidence_aggregation_result(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
) -> None:
    if type(result) is not TeamEvidenceAggregationResult:
        raise ValueError("result must be exactly TeamEvidenceAggregationResult")
    with localcontext(_ARITHMETIC_CONTEXT):
        try:
            _preflight_result_shape(result)
            validate_team_evidence_aggregation_core_digest(result)
        except _RESULT_ERRORS:
            raise ValueError(_RESULT_MISMATCH) from None
        expected = _materialize_team_evidence_aggregation_result(
            aggregation_input, config=config)
        try:
            _validate_materialized_result_invariants(
                result, config=config, expected_config_digest=expected.config_digest)
            matches_expected = result == expected
        except _RESULT_ERRORS:
            raise ValueError(_RESULT_MISMATCH) from None
    if not matches_expected:
        raise ValueError(_RESULT_MISMATCH)
    return None
