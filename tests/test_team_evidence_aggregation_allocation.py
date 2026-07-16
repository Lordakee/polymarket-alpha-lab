from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_DOWN, getcontext, localcontext
from itertools import permutations, product
import re
from typing import cast
from unittest.mock import Mock

import pytest

from polymarket_alpha_lab.team_evidence_aggregation_allocation import (
    allocate_team_evidence_weights,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceWeightAllocation,
)


FRESHNESS_ANCHOR_AT = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 7, 13, 12, 1, tzinfo=UTC)
RECORDED_AT = datetime(2026, 7, 13, 12, 2, tzinfo=UTC)
ASSESSED_AT = datetime(2026, 7, 13, 12, 3, tzinfo=UTC)
ZERO = Decimal("0.000000")


def _digest(seed: str) -> str:
    value = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    return format(value, "064x")


def _record(
    suffix: str,
    *,
    requested_weight: Decimal = Decimal("0.400000"),
    independence_key: str | None = None,
    correlation_key: str | None = None,
) -> TeamEvidenceAggregationRecord:
    lineage_id = f"lineage-{suffix}"
    lineage_digest = _digest(lineage_id)
    content_digest = _digest(f"content-{suffix}")
    evidence_id = f"evidence-{suffix}"
    evidence_digest = _digest(evidence_id)
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(
            source_lineage_id=lineage_id,
            source_lineage_digest=lineage_digest,
        ),
        capture=TeamEvidenceCapture(
            capture_id=f"capture-{suffix}",
            capture_digest=_digest(f"capture-{suffix}"),
            source_lineage_id=lineage_id,
            source_lineage_digest=lineage_digest,
            content_digest=content_digest,
            captured_at=CAPTURED_AT,
        ),
        evidence_revision=TeamEvidenceRevision(
            evidence_revision_id=evidence_id,
            evidence_revision_digest=evidence_digest,
            previous_evidence_revision_id=None,
            previous_evidence_revision_digest=None,
            source_lineage_id=lineage_id,
            source_lineage_digest=lineage_digest,
            content_digest=content_digest,
            requirement_ids=(),
            freshness_anchor_at=FRESHNESS_ANCHOR_AT,
            recorded_at=RECORDED_AT,
        ),
        assessment_revision=TeamEvidenceAssessmentRevision(
            assessment_revision_id=f"assessment-{suffix}",
            assessment_revision_digest=_digest(f"assessment-{suffix}"),
            previous_assessment_revision_id=None,
            previous_assessment_revision_digest=None,
            evidence_revision_id=evidence_id,
            evidence_revision_digest=evidence_digest,
            assessed_at=ASSESSED_AT,
            probability_yes=Decimal("0.500000"),
            requested_weight=requested_weight,
            rationale_digest=_digest(f"rationale-{suffix}"),
            independence_key=independence_key or f"independence-{suffix}",
            correlation_key=correlation_key or f"correlation-{suffix}",
        ),
    )


def _config(**changes: object) -> TeamEvidenceAggregationConfig:
    values: dict[str, object] = {
        "config_version": "allocation-v1",
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
        "requirements": (),
    }
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)


def _copy(value: object, field_name: str, replacement: object) -> object:
    copied = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(
            copied,
            field.name,
            replacement if field.name == field_name else getattr(value, field.name),
        )
    return copied


def _replace_layer(
    record: TeamEvidenceAggregationRecord,
    layer_name: str,
    field_name: str,
    replacement: object,
) -> TeamEvidenceAggregationRecord:
    layer = _copy(getattr(record, layer_name), field_name, replacement)
    return cast(TeamEvidenceAggregationRecord, _copy(record, layer_name, layer))


def _reject(message: str, records: object, config: object) -> None:
    with pytest.raises(ValueError, match=rf"^{re.escape(message)}$"):
        allocate_team_evidence_weights(records, config=config)  # type: ignore[arg-type]


def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id, record.capture.captured_at,
        record.capture.capture_id, record.source_lineage.source_lineage_id,
    )


def _micro_units(value: Decimal) -> int:
    return int(value * Decimal(1_000_000))


def _test_cap_stage(
    weights: tuple[int, ...],
    groups: tuple[str, ...],
    cap: int,
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> tuple[int, ...]:
    result = list(weights)
    for group in dict.fromkeys(groups):
        indexes = tuple(i for i, key in enumerate(groups) if key == group)
        total = sum(weights[i] for i in indexes)
        if total <= cap:
            continue
        floors = {i: weights[i] * cap // total for i in indexes}
        remainders = {i: weights[i] * cap % total for i in indexes}
        ranked = sorted(indexes, key=lambda i: (-remainders[i], _record_key(records[i])))
        for index in ranked[: cap - sum(floors.values())]:
            floors[index] += 1
        for index in indexes:
            result[index] = floors[index]
    return tuple(result)


def _forbidden_reversed_stage_result(
    records: tuple[TeamEvidenceAggregationRecord, ...],
    config: TeamEvidenceAggregationConfig,
) -> tuple[Decimal, ...]:
    ordered = tuple(sorted(records, key=_record_key))
    requested = tuple(_micro_units(row.assessment_revision.requested_weight) for row in ordered)
    correlation_first = _test_cap_stage(
        requested,
        tuple(row.assessment_revision.correlation_key for row in ordered),
        _micro_units(config.correlation_group_weight_cap),
        ordered,
    )
    independence_second = _test_cap_stage(
        correlation_first,
        tuple(row.assessment_revision.independence_key for row in ordered),
        _micro_units(config.independence_group_weight_cap),
        ordered,
    )
    return tuple(Decimal(value).scaleb(-6) for value in independence_second)


def _context_state(context: Context) -> tuple[object, ...]:
    return (
        context.prec, context.rounding, context.Emin, context.Emax,
        context.capitals, context.clamp,
        tuple(context.flags.items()), tuple(context.traps.items()),
    )


def _signature(
    rows: tuple[TeamEvidenceWeightAllocation, ...],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            type(row),
            row.source_lineage_id,
            row.capture_id,
            row.evidence_revision_id,
            row.assessment_revision_id,
            row.independence_key,
            row.correlation_key,
            row.requested_weight.as_tuple(),
            row.independence_allocated_weight.as_tuple(),
            row.effective_weight.as_tuple(),
            row.independence_cap_applied,
            row.correlation_cap_applied,
            row.paper_only,
            row.report_only,
            row.readonly,
        )
        for row in rows
    )


def _weight_rows(rows: tuple[TeamEvidenceWeightAllocation, ...]) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            row.requested_weight,
            row.independence_allocated_weight,
            row.effective_weight,
            row.independence_cap_applied,
            row.correlation_cap_applied,
        )
        for row in rows
    )


def test_allocate_team_evidence_weights_returns_uncapped_rows_in_canonical_order() -> None:
    first = _record("a", requested_weight=Decimal("0.600000"))
    second = _record("b", requested_weight=Decimal("0.400000"))
    rows = allocate_team_evidence_weights((second, first), config=_config())
    assert tuple(row.assessment_revision_id for row in rows) == ("assessment-a", "assessment-b")
    assert tuple(
        (row.source_lineage_id, row.capture_id, row.evidence_revision_id) for row in rows
    ) == (("lineage-a", "capture-a", "evidence-a"), ("lineage-b", "capture-b", "evidence-b"))
    assert _weight_rows(rows) == (
        (Decimal("0.600000"), Decimal("0.600000"), Decimal("0.600000"), False, False),
        (Decimal("0.400000"), Decimal("0.400000"), Decimal("0.400000"), False, False),
    )


def test_empty_allocation_input_returns_empty_tuple() -> None:
    assert allocate_team_evidence_weights((), config=_config()) == ()


def test_allocate_team_evidence_weights_applies_independence_cap_only() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.600000"), independence_key="i-shared"),
        _record("b", requested_weight=Decimal("0.400000"), independence_key="i-shared"),
    )
    rows = allocate_team_evidence_weights(
        records,
        config=_config(independence_group_weight_cap=Decimal("0.500000")),
    )
    assert _weight_rows(rows) == (
        (Decimal("0.600000"), Decimal("0.300000"), Decimal("0.300000"), True, False),
        (Decimal("0.400000"), Decimal("0.200000"), Decimal("0.200000"), True, False),
    )


def test_allocate_team_evidence_weights_applies_correlation_cap_only() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.600000"), correlation_key="c-shared"),
        _record("b", requested_weight=Decimal("0.400000"), correlation_key="c-shared"),
    )
    rows = allocate_team_evidence_weights(
        records,
        config=_config(correlation_group_weight_cap=Decimal("0.500000")),
    )
    assert _weight_rows(rows) == (
        (Decimal("0.600000"), Decimal("0.600000"), Decimal("0.300000"), False, True),
        (Decimal("0.400000"), Decimal("0.400000"), Decimal("0.200000"), False, True),
    )


def test_allocate_team_evidence_weights_applies_independence_before_correlation() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.600000"), independence_key="i1", correlation_key="c1"),
        _record("b", requested_weight=Decimal("0.400000"), independence_key="i1", correlation_key="c2"),
        _record("c", requested_weight=Decimal("0.400000"), independence_key="i2", correlation_key="c1"),
    )
    config = _config(
        independence_group_weight_cap=Decimal("0.500000"),
        correlation_group_weight_cap=Decimal("0.500000"),
    )
    production = tuple(row.effective_weight for row in allocate_team_evidence_weights(records, config=config))
    forbidden = _forbidden_reversed_stage_result(records, config)
    assert production == (Decimal("0.214286"), Decimal("0.200000"), Decimal("0.285714"))
    assert forbidden == (Decimal("0.214286"), Decimal("0.285714"), Decimal("0.200000"))
    assert production != forbidden


def test_largest_remainder_conserves_cap_and_breaks_equal_remainders_by_record_key() -> None:
    records = tuple(
        _record(suffix, requested_weight=Decimal("0.000001"), independence_key="i-shared")
        for suffix in ("a", "b", "c")
    )
    rows = allocate_team_evidence_weights(
        tuple(reversed(records)),
        config=_config(independence_group_weight_cap=Decimal("0.000002")),
    )
    expected = (Decimal("0.000001"), Decimal("0.000001"), Decimal("0.000000"))
    assert tuple(row.independence_allocated_weight for row in rows) == expected
    assert tuple(row.effective_weight for row in rows) == expected
    assert sum((row.independence_allocated_weight for row in rows), ZERO) == Decimal("0.000002")


def test_largest_remainder_preserves_the_alabama_paradox_regression() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.000001"), independence_key="i-shared"),
        _record("b", requested_weight=Decimal("0.000003"), independence_key="i-shared"),
        _record("c", requested_weight=Decimal("0.000003"), independence_key="i-shared"),
    )
    cap_three = allocate_team_evidence_weights(
        records,
        config=_config(independence_group_weight_cap=Decimal("0.000003")),
    )
    cap_four = allocate_team_evidence_weights(
        records,
        config=_config(independence_group_weight_cap=Decimal("0.000004")),
    )
    weights_three = tuple(row.independence_allocated_weight for row in cap_three)
    weights_four = tuple(row.independence_allocated_weight for row in cap_four)
    assert weights_three == (Decimal("0.000001"), Decimal("0.000001"), Decimal("0.000001"))
    assert weights_four == (Decimal("0.000000"), Decimal("0.000002"), Decimal("0.000002"))
    assert sum(weights_three, ZERO) == Decimal("0.000003")
    assert sum(weights_four, ZERO) == Decimal("0.000004")
    assert weights_three[0] - weights_four[0] == Decimal("0.000001")


def test_cap_smaller_than_positive_record_count_assigns_only_available_micro_units() -> None:
    records = tuple(
        _record(suffix, requested_weight=Decimal("0.000001"), independence_key="i-shared")
        for suffix in ("a", "b", "c")
    )
    rows = allocate_team_evidence_weights(
        tuple(reversed(records)),
        config=_config(independence_group_weight_cap=Decimal("0.000001")),
    )
    assert tuple(row.independence_allocated_weight for row in rows) == (
        Decimal("0.000001"), Decimal("0.000000"), Decimal("0.000000")
    )


def test_zero_stage_one_and_stage_two_allocations_remain_exact_zero() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.000001"), independence_key="i-a", correlation_key="c-shared"),
        _record("b", requested_weight=Decimal("0.000001"), independence_key="i-b", correlation_key="c-shared"),
        _record("c", requested_weight=Decimal("0.000001"), independence_key="i-c", correlation_key="c-c"),
        _record("d", requested_weight=Decimal("0.000001"), independence_key="i-c", correlation_key="c-d"),
    )
    rows = allocate_team_evidence_weights(
        records,
        config=_config(
            independence_group_weight_cap=Decimal("0.000001"),
            correlation_group_weight_cap=Decimal("0.000001"),
        ),
    )
    by_id = {row.assessment_revision_id: row for row in rows}
    assert (
        by_id["assessment-d"].independence_allocated_weight,
        by_id["assessment-d"].effective_weight,
    ) == (ZERO, ZERO)
    assert (
        by_id["assessment-b"].independence_allocated_weight,
        by_id["assessment-b"].effective_weight,
    ) == (Decimal("0.000001"), ZERO)
    zeros = tuple(
        value
        for row in rows
        for value in (row.independence_allocated_weight, row.effective_weight)
        if value == ZERO
    )
    assert tuple(value.as_tuple() for value in zeros) == (ZERO.as_tuple(),) * 3
    assert tuple(value.is_signed() for value in zeros) == (False, False, False)


def test_cap_flags_are_group_level_and_equality_does_not_activate_them() -> None:
    independence = allocate_team_evidence_weights(
        (
            _record("a", requested_weight=Decimal("0.600000"), independence_key="i-over"),
            _record("b", requested_weight=Decimal("0.000001"), independence_key="i-over"),
            _record("c", requested_weight=Decimal("0.400000"), independence_key="i-equal"),
            _record("d", requested_weight=Decimal("0.200000"), independence_key="i-equal"),
        ),
        config=_config(independence_group_weight_cap=Decimal("0.600000")),
    )
    assert tuple(row.independence_cap_applied for row in independence) == (True, True, False, False)
    assert independence[1].independence_allocated_weight == independence[1].requested_weight
    correlation = allocate_team_evidence_weights(
        (
            _record("a", requested_weight=Decimal("0.600000"), correlation_key="c-over"),
            _record("b", requested_weight=Decimal("0.000001"), correlation_key="c-over"),
            _record("c", requested_weight=Decimal("0.400000"), correlation_key="c-equal"),
            _record("d", requested_weight=Decimal("0.200000"), correlation_key="c-equal"),
        ),
        config=_config(correlation_group_weight_cap=Decimal("0.600000")),
    )
    assert tuple(row.correlation_cap_applied for row in correlation) == (True, True, False, False)
    assert correlation[1].effective_weight == correlation[1].independence_allocated_weight


def test_allocation_never_increases_weights_and_every_group_respects_its_cap() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.400000"), independence_key="i1", correlation_key="c1"),
        _record("b", requested_weight=Decimal("0.300000"), independence_key="i1", correlation_key="c2"),
        _record("c", requested_weight=Decimal("0.200000"), independence_key="i2", correlation_key="c1"),
        _record("d", requested_weight=Decimal("0.100000"), independence_key="i3", correlation_key="c2"),
    )
    config = _config(
        independence_group_weight_cap=Decimal("0.500000"),
        correlation_group_weight_cap=Decimal("0.400000"),
    )
    rows = allocate_team_evidence_weights(records, config=config)
    assert all(ZERO <= row.effective_weight <= row.independence_allocated_weight <= row.requested_weight for row in rows)
    independence_totals = {
        key: sum((row.independence_allocated_weight for row in rows if row.independence_key == key), ZERO)
        for key in ("i1", "i2", "i3")
    }
    correlation_totals = {
        key: sum((row.effective_weight for row in rows if row.correlation_key == key), ZERO)
        for key in ("c1", "c2")
    }
    assert independence_totals == {
        "i1": Decimal("0.500000"),
        "i2": Decimal("0.200000"),
        "i3": Decimal("0.100000"),
    }
    assert correlation_totals == {"c1": Decimal("0.400000"), "c2": Decimal("0.314286")}
    assert all(total <= config.independence_group_weight_cap for total in independence_totals.values())
    assert all(total <= config.correlation_group_weight_cap for total in correlation_totals.values())


def test_allocation_rejects_wrong_exact_types_duplicate_keys_and_resource_overflow() -> None:
    record, config = _record("a"), _config()
    for bad_records in ([record], (item for item in (record,)), type("TupleChild", (tuple,), {})((record,))):
        _reject("records must be an exact tuple", bad_records, config)
    for final_type in (TeamEvidenceAggregationConfig, TeamEvidenceAggregationRecord):
        with pytest.raises(TypeError):
            type(f"Bad{final_type.__name__}", (final_type,), {})
    _reject("config must be exactly TeamEvidenceAggregationConfig", (record,), Mock(spec=config))
    _reject(
        "records[1] must be exactly TeamEvidenceAggregationRecord",
        (record, Mock(spec=record)),
        config,
    )
    _reject("records contains duplicate canonical record key", (record, record), config)
    for bad_maximum in (True, 0, 1.0, Decimal("128.000000"), 129):
        _reject(
            "config.maximum_records must be an exact int in 1..128",
            (record,),
            _copy(config, "maximum_records", bad_maximum),
        )
    _reject(
        "records exceeds config.maximum_records",
        (_record("a"), _record("b")),
        _config(maximum_records=1),
    )
    _reject(
        "records exceeds config.maximum_records",
        tuple(_record(f"r{index:03d}") for index in range(129)),
        config,
    )

    class DecimalChild(Decimal):
        pass

    class StringChild(str):
        pass

    wrong_types = (True, 1, 0.5, DecimalChild("0.500000"))
    bad_caps = wrong_types + (
        Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity"),
        Decimal("-0.000000"), Decimal("-0.000001"), Decimal("1.000001"),
        Decimal("0.50000"), Decimal("0.1234567"),
    )
    for cap_name, bad_cap in product(
        ("independence_group_weight_cap", "correlation_group_weight_cap"), bad_caps
    ):
        _reject(
            f"config.{cap_name} must be an exact finite canonical fixed-six Decimal in [0, 1]",
            (record,),
            _copy(config, cap_name, bad_cap),
        )
    bad_weights = wrong_types + (
        ZERO, Decimal("-0.000000"), Decimal("NaN"), Decimal("sNaN"),
        Decimal("Infinity"), Decimal("-Infinity"), Decimal("-0.000001"),
        Decimal("1.000001"), Decimal("0.50000"), Decimal("0.1234567"),
    )
    requested_error = (
        "records[0].assessment_revision.requested_weight must be an exact finite "
        "canonical fixed-six Decimal in (0, 1]"
    )
    for bad_weight in bad_weights:
        _reject(
            requested_error,
            (_replace_layer(record, "assessment_revision", "requested_weight", bad_weight),),
            config,
        )
    for field_name, bad_key in product(
        ("independence_key", "correlation_key"),
        (1, StringChild("valid-key"), "", "Bad", "bad/key", "a" * 161, "\ud800"),
    ):
        _reject(
            f"records[0].assessment_revision.{field_name} must be an exact canonical identifier",
            (_replace_layer(record, "assessment_revision", field_name, bad_key),),
            config,
        )
    for flag in ("paper_only", "report_only", "readonly"):
        _reject(
            f"config.{flag} must preserve paper_only=True, report_only=True, readonly=True",
            (record,),
            _copy(config, flag, False),
        )
        _reject(
            f"records[0].{flag} must preserve paper_only=True, report_only=True, readonly=True",
            (cast(TeamEvidenceAggregationRecord, _copy(record, flag, False)),),
            config,
        )
        for layer in ("source_lineage", "capture", "evidence_revision", "assessment_revision"):
            _reject(
                f"records[0].{layer}.{flag} must preserve paper_only=True, report_only=True, readonly=True",
                (_replace_layer(record, layer, flag, False),),
                config,
            )
    _reject(
        "records[0] must be canonical",
        (_replace_layer(record, "assessment_revision", "assessment_revision_id", StringChild("assessment-a")),),
        config,
    )
    noncanonical_utc = datetime(
        2026, 7, 13, 12, 1, tzinfo=timezone(timedelta(0), "noncanonical-zero-offset")
    )
    _reject(
        "records[0] must be canonical",
        (_replace_layer(record, "capture", "captured_at", noncanonical_utc),),
        config,
    )
    _reject(
        "config must be canonical",
        (record,),
        _copy(config, "max_evidence_age_seconds", Decimal("3600.0")),
    )
    _reject(
        "records[0] must be canonical",
        (_replace_layer(record, "assessment_revision", "probability_yes", Decimal("0.50")),),
        config,
    )
    _reject("records[0] must be canonical", (_replace_layer(record, "evidence_revision", "requirement_ids", ("\ud800",)),), config)


def test_allocation_is_permutation_and_hostile_decimal_context_invariant() -> None:
    records = (
        _record("a", requested_weight=Decimal("0.600000"), independence_key="i1", correlation_key="c1"),
        _record("b", requested_weight=Decimal("0.400000"), independence_key="i1", correlation_key="c2"),
        _record("c", requested_weight=Decimal("0.400000"), independence_key="i2", correlation_key="c1"),
    )
    config = _config(
        independence_group_weight_cap=Decimal("0.500000"),
        correlation_group_weight_cap=Decimal("0.500000"),
    )
    outer_before = _context_state(getcontext())
    baseline = allocate_team_evidence_weights(records, config=config)
    baseline_signature = _signature(baseline)
    assert _context_state(getcontext()) == outer_before
    for ordering in permutations(records):
        normal_before = _context_state(getcontext())
        normal = allocate_team_evidence_weights(ordering, config=config)
        assert normal == baseline and _signature(normal) == baseline_signature
        assert _context_state(getcontext()) == normal_before
        with localcontext(Context(prec=4, rounding=ROUND_DOWN)):
            hostile_before = _context_state(getcontext())
            hostile = allocate_team_evidence_weights(ordering, config=config)
            assert hostile == baseline and _signature(hostile) == baseline_signature
            assert all(type(row) is TeamEvidenceWeightAllocation for row in hostile)
            assert _context_state(getcontext()) == hostile_before
