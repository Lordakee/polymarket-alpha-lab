"""Pure Node 2C team evidence aggregation reducer.

Composes the reviewed Node 2A canonical selectors and temporal assessment
with the Node 2B largest-remainder allocation and canonical requirement
witness matching into one immutable aggregation result: one diagnostic row
per supplied record, capped-arithmetic canonical P(YES), contradiction
scoring, strict status precedence, complete reason codes, ready-only
bounded publication, and config/core digest validation through the Node 2A
codec. The public builder and validator share one private semantic
materializer, and every Decimal operation runs inside a local copy of
Context(prec=64, rounding=ROUND_HALF_EVEN); the ambient decimal context is
never read, mutated, or polluted with flags or traps.
"""
from __future__ import annotations

from dataclasses import replace
from decimal import (
    Context,
    Decimal,
    DecimalException,
    ROUND_HALF_EVEN,
    localcontext,
)
from typing import Final

from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAggregationResult,
    TeamEvidenceContradictionResult,
    TeamEvidenceDiagnosticRow,
    TeamEvidenceTemporalAssessment,
    TeamEvidenceWeightAllocation,
    select_team_evidence_canonical_capture_records,
    select_team_evidence_canonical_current_records,
)
from polymarket_alpha_lab.team_evidence_aggregation_codec import (
    team_evidence_aggregation_config_digest,
    team_evidence_aggregation_core_digest,
    validate_team_evidence_aggregation_core_digest,
)
from polymarket_alpha_lab.team_evidence_aggregation_temporal import (
    assess_team_evidence_temporal,
)
from polymarket_alpha_lab.team_evidence_aggregation_allocation import (
    allocate_team_evidence_weights,
)
from polymarket_alpha_lab.team_evidence_aggregation_witness import (
    build_team_evidence_requirement_coverage,
)

__all__ = (
    "build_team_evidence_aggregation_result",
    "validate_team_evidence_aggregation_result",
)

_ZERO: Final = Decimal("0.000000")
_SIX_PLACES: Final = Decimal("0.000001")
_ARITHMETIC_CONTEXT: Final = Context(prec=64, rounding=ROUND_HALF_EVEN)
_ALLOCATION_DISPOSITIONS: Final = frozenset((
    "included",
    "independence_cap_exhausted",
    "correlation_cap_exhausted",
))


def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )


def _record_identity(
    record: TeamEvidenceAggregationRecord,
) -> tuple[str, str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )


def _selected_pair_identity(
    record: TeamEvidenceAggregationRecord,
) -> tuple[str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )


def _quantize_once(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("aggregation arithmetic must be finite Decimal")
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            quantized = value.quantize(_SIX_PLACES)
    except DecimalException:
        raise ValueError("aggregation arithmetic must be quantizable") from None
    return _ZERO if quantized == _ZERO else quantized


def _validate_materialized_result_invariants(
    result: TeamEvidenceAggregationResult,
    *,
    config: TeamEvidenceAggregationConfig,
) -> None:
    """Check final-result contract invariants without rematerializing."""
    with localcontext(_ARITHMETIC_CONTEXT):
        if result.config_version != config.config_version:
            raise ValueError(
                "result.config_version must equal config.config_version"
            )
        if result.config_digest != team_evidence_aggregation_config_digest(config):
            raise ValueError(
                "result.config_digest must equal the canonical config digest"
            )
        if result.diagnostic_record_count != len(result.diagnostics):
            raise ValueError(
                "result.diagnostic_record_count must equal len(result.diagnostics)"
            )
        if result.arithmetic_record_count > result.diagnostic_record_count:
            raise ValueError(
                "result.arithmetic_record_count must not exceed "
                "result.diagnostic_record_count"
            )
        included_rows = tuple(
            row for row in result.diagnostics if row.disposition == "included"
        )
        if result.arithmetic_record_count != len(included_rows):
            raise ValueError(
                "result.arithmetic_record_count must equal the included "
                "diagnostic rows"
            )
        requested_total = _ZERO
        independence_total = _ZERO
        effective_total = _ZERO
        for row in result.diagnostics:
            if row.disposition in _ALLOCATION_DISPOSITIONS:
                requested_total += row.requested_weight
                independence_total += row.independence_allocated_weight
            if row.disposition == "included":
                effective_total += row.effective_weight
        if result.requested_weight_total != requested_total:
            raise ValueError(
                "result.requested_weight_total must equal the diagnostic rows"
            )
        if result.independence_allocated_weight_total != independence_total:
            raise ValueError(
                "result.independence_allocated_weight_total must equal the "
                "diagnostic rows"
            )
        if result.effective_weight_total != effective_total:
            raise ValueError(
                "result.effective_weight_total must equal the included rows"
            )
        requirement_ids = tuple(
            requirement.requirement_id for requirement in config.requirements
        )
        coverage_ids = tuple(
            coverage.requirement_id for coverage in result.requirement_coverage
        )
        if coverage_ids != requirement_ids:
            raise ValueError(
                "result.requirement_coverage must contain exactly one row per "
                "configured requirement"
            )
        for coverage, requirement in zip(
            result.requirement_coverage, config.requirements, strict=True
        ):
            if (
                coverage.minimum_witness_count
                != requirement.minimum_witness_count
                or coverage.minimum_effective_weight
                != requirement.minimum_effective_weight
                or coverage.unmet_status != requirement.unmet_status
            ):
                raise ValueError(
                    "requirement coverage rows must preserve the configured fields"
                )
        unmet_blocked = any(
            not coverage.satisfied and coverage.unmet_status == "blocked"
            for coverage in result.requirement_coverage
        )
        unmet_watch = any(
            not coverage.satisfied and coverage.unmet_status == "watch"
            for coverage in result.requirement_coverage
        )
        arithmetic_is_none = result.arithmetic_probability_yes is None
        expected_blocked = (
            arithmetic_is_none
            or unmet_blocked
            or result.contradiction.status == "blocked"
        )
        expected_watch = unmet_watch or result.contradiction.status == "watch"
        expected_status = (
            "blocked" if expected_blocked else "watch" if expected_watch else "ready"
        )
        if result.status != expected_status:
            raise ValueError(
                "result.status must follow the exact readiness precedence"
            )
        expected_reasons: set[str] = set()
        if arithmetic_is_none:
            expected_reasons.add("no_arithmetic_evidence")
        if unmet_blocked:
            expected_reasons.add("blocking_requirement_unmet")
        if unmet_watch:
            expected_reasons.add("watch_requirement_unmet")
        if result.contradiction.status == "blocked":
            expected_reasons.add("contradiction_blocked")
        if result.contradiction.status == "watch":
            expected_reasons.add("contradiction_watch")
        if result.status != "ready":
            if result.publishable_probability_yes is not None:
                raise ValueError(
                    "non-ready result must not publish a probability"
                )
        else:
            expected_reasons.add("aggregation_ready")
            probability = result.arithmetic_probability_yes
            if probability is None:
                raise ValueError(
                    "ready result must retain an arithmetic probability"
                )
            if probability < config.publish_probability_floor:
                expected_publishable = config.publish_probability_floor
                expected_reasons.add("publish_probability_floor_applied")
            elif probability > config.publish_probability_ceiling:
                expected_publishable = config.publish_probability_ceiling
                expected_reasons.add("publish_probability_ceiling_applied")
            else:
                expected_publishable = probability
            if result.publishable_probability_yes != expected_publishable:
                raise ValueError(
                    "ready result publication must equal the bounded probability"
                )
        if set(result.reason_codes) != expected_reasons:
            raise ValueError(
                "result.reason_codes must equal the applicable static reason set"
            )
    return None


def _materialize_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult:
    """Build the one canonical semantic result from exact input and config."""
    canonical_capture_records = select_team_evidence_canonical_capture_records(
        aggregation_input,
        config=config,
    )
    canonical_current_records = select_team_evidence_canonical_current_records(
        aggregation_input,
        config=config,
    )
    records = tuple(sorted(aggregation_input.records, key=_record_key))
    canonical_capture_identities = frozenset(
        _record_identity(record) for record in canonical_capture_records
    )
    canonical_current_identities = frozenset(
        _record_identity(record) for record in canonical_current_records
    )
    selected_pair_identities = frozenset(
        _selected_pair_identity(record) for record in canonical_current_records
    )
    temporal_assessments: tuple[TeamEvidenceTemporalAssessment, ...] = tuple(
        assess_team_evidence_temporal(
            record,
            evaluated_at=aggregation_input.evaluated_at,
            config=config,
        )
        for record in records
    )
    with localcontext(_ARITHMETIC_CONTEXT):
        preallocation_dispositions: list[str | None] = []
        candidate_records: list[TeamEvidenceAggregationRecord] = []
        for record, temporal in zip(records, temporal_assessments, strict=True):
            disposition: str | None
            if _selected_pair_identity(record) not in selected_pair_identities:
                disposition = "not_current_revision"
            elif _record_identity(record) not in canonical_current_identities:
                disposition = "duplicate_capture"
            elif not temporal.effective_at_evaluation:
                disposition = "freshness_anchor_after_evaluation"
            elif not temporal.captured_at_evaluation:
                disposition = "capture_after_evaluation"
            elif not temporal.evidence_revision_available_at_evaluation:
                disposition = "evidence_revision_after_evaluation"
            elif not temporal.assessment_revision_available_at_evaluation:
                disposition = "assessment_revision_after_evaluation"
            elif not temporal.fresh:
                disposition = "stale"
            elif temporal.capture_lag_seconds < _ZERO:
                disposition = "capture_before_freshness_anchor"
            elif not temporal.timely:
                disposition = "capture_lag_exceeded"
            elif record.assessment_revision.requested_weight == _ZERO:
                disposition = "zero_requested_weight"
            else:
                disposition = None
                candidate_records.append(record)
            preallocation_dispositions.append(disposition)
    allocation_records = tuple(candidate_records)
    allocations = allocate_team_evidence_weights(allocation_records, config=config)
    allocation_identities = tuple(
        (
            allocation.source_lineage_id,
            allocation.capture_id,
            allocation.evidence_revision_id,
            allocation.assessment_revision_id,
        )
        for allocation in allocations
    )
    if allocation_identities != tuple(
        _record_identity(record) for record in allocation_records
    ):
        raise ValueError(
            "allocations must join the allocation-input records exactly"
        )
    allocation_by_identity: dict[
        tuple[str, str, str, str], TeamEvidenceWeightAllocation
    ] = dict(zip(allocation_identities, allocations, strict=True))
    # The witness owns candidate matching; its inherited candidate-edge order
    # is (requirement_id, source_lineage_id, evidence_revision_id,
    # assessment_revision_id, capture_id).
    requirement_coverage = build_team_evidence_requirement_coverage(
        allocation_records,
        allocations,
        config=config,
    )
    with localcontext(_ARITHMETIC_CONTEXT):
        dispositions: list[str] = []
        for record, disposition in zip(
            records, preallocation_dispositions, strict=True
        ):
            if disposition is not None:
                dispositions.append(disposition)
                continue
            allocation = allocation_by_identity[_record_identity(record)]
            if allocation.independence_allocated_weight == _ZERO:
                dispositions.append("independence_cap_exhausted")
            elif allocation.effective_weight == _ZERO:
                dispositions.append("correlation_cap_exhausted")
            else:
                dispositions.append("included")
    diagnostics: list[TeamEvidenceDiagnosticRow] = []
    for record, temporal, disposition in zip(
        records, temporal_assessments, dispositions, strict=True
    ):
        if disposition in _ALLOCATION_DISPOSITIONS:
            allocation = allocation_by_identity[_record_identity(record)]
            independence_weight = allocation.independence_allocated_weight
            effective_weight = allocation.effective_weight
        else:
            independence_weight = _ZERO
            effective_weight = _ZERO
        diagnostics.append(
            TeamEvidenceDiagnosticRow(
                source_lineage_id=record.source_lineage.source_lineage_id,
                capture_id=record.capture.capture_id,
                captured_at=record.capture.captured_at,
                evidence_revision_id=record.evidence_revision.evidence_revision_id,
                assessment_revision_id=(
                    record.assessment_revision.assessment_revision_id
                ),
                probability_yes=record.assessment_revision.probability_yes,
                requested_weight=record.assessment_revision.requested_weight,
                independence_allocated_weight=independence_weight,
                effective_weight=effective_weight,
                evidence_age_seconds=temporal.evidence_age_seconds,
                capture_lag_seconds=temporal.capture_lag_seconds,
                captured_at_evaluation=temporal.captured_at_evaluation,
                evidence_revision_available_at_evaluation=(
                    temporal.evidence_revision_available_at_evaluation
                ),
                assessment_revision_available_at_evaluation=(
                    temporal.assessment_revision_available_at_evaluation
                ),
                selected_current_revision=(
                    _selected_pair_identity(record) in selected_pair_identities
                ),
                canonical_capture=(
                    _record_identity(record) in canonical_capture_identities
                ),
                disposition=disposition,
            )
        )
    with localcontext(_ARITHMETIC_CONTEXT):
        requested_total = _ZERO
        independence_total = _ZERO
        effective_total = _ZERO
        numerator = _ZERO
        denominator = _ZERO
        arithmetic_count = 0
        for row in diagnostics:
            if row.disposition in _ALLOCATION_DISPOSITIONS:
                requested_total += row.requested_weight
                independence_total += row.independence_allocated_weight
            if row.disposition == "included":
                effective_total += row.effective_weight
                numerator += row.probability_yes * row.effective_weight
                denominator += row.effective_weight
                arithmetic_count += 1
        requested_weight_total = _quantize_once(requested_total)
        independence_allocated_weight_total = _quantize_once(independence_total)
        effective_weight_total = _quantize_once(effective_total)
        arithmetic_probability_yes = (
            None
            if denominator == _ZERO
            else _quantize_once(numerator / denominator)
        )
        yes_support = _ZERO
        no_support = _ZERO
        neutral_support = _ZERO
        for row in diagnostics:
            if row.disposition != "included":
                continue
            if row.probability_yes <= config.contradiction_no_probability_max:
                no_support += row.effective_weight
            elif row.probability_yes >= config.contradiction_yes_probability_min:
                yes_support += row.effective_weight
            else:
                neutral_support += row.effective_weight
        if yes_support == _ZERO or no_support == _ZERO:
            contradiction_score = _ZERO
            contradiction_status = "none"
        else:
            smaller_support = yes_support if yes_support < no_support else no_support
            contradiction_score = _quantize_once(
                Decimal(2) * smaller_support / (yes_support + no_support)
            )
            if contradiction_score >= config.contradiction_block_score:
                contradiction_status = "blocked"
            elif contradiction_score >= config.contradiction_watch_score:
                contradiction_status = "watch"
            else:
                contradiction_status = "none"
        contradiction = TeamEvidenceContradictionResult(
            yes_support_weight=_quantize_once(yes_support),
            no_support_weight=_quantize_once(no_support),
            neutral_weight=_quantize_once(neutral_support),
            contradiction_score=contradiction_score,
            status=contradiction_status,
        )
        unmet_blocked = any(
            not coverage.satisfied and coverage.unmet_status == "blocked"
            for coverage in requirement_coverage
        )
        unmet_watch = any(
            not coverage.satisfied and coverage.unmet_status == "watch"
            for coverage in requirement_coverage
        )
        status_is_blocked = (
            arithmetic_probability_yes is None
            or unmet_blocked
            or contradiction.status == "blocked"
        )
        status_is_watch = unmet_watch or contradiction.status == "watch"
        status = (
            "blocked"
            if status_is_blocked
            else "watch" if status_is_watch else "ready"
        )
        reason_codes: set[str] = set()
        if arithmetic_probability_yes is None:
            reason_codes.add("no_arithmetic_evidence")
        if unmet_blocked:
            reason_codes.add("blocking_requirement_unmet")
        if unmet_watch:
            reason_codes.add("watch_requirement_unmet")
        if contradiction.status == "blocked":
            reason_codes.add("contradiction_blocked")
        if contradiction.status == "watch":
            reason_codes.add("contradiction_watch")
        publishable_probability_yes = None
        if status == "ready":
            reason_codes.add("aggregation_ready")
            probability = arithmetic_probability_yes
            if probability < config.publish_probability_floor:
                publishable_probability_yes = config.publish_probability_floor
                reason_codes.add("publish_probability_floor_applied")
            elif probability > config.publish_probability_ceiling:
                publishable_probability_yes = config.publish_probability_ceiling
                reason_codes.add("publish_probability_ceiling_applied")
            else:
                publishable_probability_yes = probability
    provisional = TeamEvidenceAggregationResult(
        evaluated_at=aggregation_input.evaluated_at,
        config_version=config.config_version,
        config_digest=team_evidence_aggregation_config_digest(config),
        status=status,
        diagnostic_record_count=len(diagnostics),
        arithmetic_record_count=arithmetic_count,
        requested_weight_total=requested_weight_total,
        independence_allocated_weight_total=independence_allocated_weight_total,
        effective_weight_total=effective_weight_total,
        arithmetic_probability_yes=arithmetic_probability_yes,
        publishable_probability_yes=publishable_probability_yes,
        contradiction=contradiction,
        requirement_coverage=requirement_coverage,
        diagnostics=tuple(diagnostics),
        reason_codes=tuple(sorted(reason_codes)),
        core_digest="0" * 64,
    )
    core_digest = team_evidence_aggregation_core_digest(provisional)
    final = replace(provisional, core_digest=core_digest)
    _validate_materialized_result_invariants(final, config=config)
    validate_team_evidence_aggregation_core_digest(final)
    return final


def build_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult:
    """Reduce exact input and config to the one canonical result."""
    return _materialize_team_evidence_aggregation_result(
        aggregation_input,
        config=config,
    )


def validate_team_evidence_aggregation_result(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
) -> None:
    """Validate a result by canonical checks plus exact rematerialization."""
    if type(result) is not TeamEvidenceAggregationResult:
        raise ValueError("result must be exactly TeamEvidenceAggregationResult")
    try:
        _validate_materialized_result_invariants(result, config=config)
        validate_team_evidence_aggregation_core_digest(result)
    except (AttributeError, DecimalException, TypeError, ValueError):
        raise ValueError(
            "aggregation result must equal rematerialized result",
        ) from None
    expected = _materialize_team_evidence_aggregation_result(
        aggregation_input,
        config=config,
    )
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            matches_expected = result == expected
    except DecimalException:
        raise ValueError(
            "aggregation result must equal rematerialized result",
        ) from None
    if not matches_expected:
        raise ValueError("aggregation result must equal rematerialized result")
