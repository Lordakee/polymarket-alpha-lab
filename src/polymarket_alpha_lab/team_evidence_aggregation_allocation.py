from __future__ import annotations

from decimal import (
    Context,
    Decimal,
    DecimalException,
    ROUND_HALF_EVEN,
    localcontext,
)
from typing import TypeVar, cast

from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceWeightAllocation,
)


__all__ = ("allocate_team_evidence_weights",)


_WEIGHT_QUANTUM = Decimal("0.000001")
_MICRO_UNITS_PER_ONE = 1_000_000
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_IMPLEMENTATION_MAXIMUM_RECORDS = 128
_ZERO_WEIGHT = Decimal("0.000000")
_ONE_WEIGHT = Decimal("1.000000")
_IDENTIFIER_EDGE_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
_IDENTIFIER_CHARACTERS = _IDENTIFIER_EDGE_CHARACTERS + "._:-"
_CANONICAL_ERRORS = (AttributeError, DecimalException, TypeError, ValueError)


_T = TypeVar("_T")


def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )


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


def _validate_group_key(field_name: str, value: object) -> str:
    if not _is_identifier(value):
        raise ValueError(f"{field_name} must be an exact canonical identifier")
    return cast(str, value)


def _validate_hard_flags(path: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(
                f"{path}.{field_name} must preserve "
                "paper_only=True, report_only=True, readonly=True"
            )


def _canonical_ratio(
    field_name: str,
    value: object,
    *,
    positive: bool,
) -> Decimal:
    error = (
        f"{field_name} must be an exact finite canonical fixed-six Decimal "
        f"in {'(0, 1]' if positive else '[0, 1]'}"
    )
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(error)
    if value.is_zero() and value.is_signed():
        raise ValueError(error)
    try:
        with localcontext(_DECIMAL_CONTEXT):
            if value > _ONE_WEIGHT or value < _ZERO_WEIGHT:
                raise ValueError(error)
            if positive and value == _ZERO_WEIGHT:
                raise ValueError(error)
            normalized = value.quantize(_WEIGHT_QUANTUM)
    except DecimalException:
        raise ValueError(error) from None
    if value.as_tuple() != normalized.as_tuple():
        raise ValueError(error)
    return value


def _canonical_equal(value: object, normalized: object) -> bool:
    if type(value) is not type(normalized):
        return False
    if type(value) is Decimal:
        return value.as_tuple() == normalized.as_tuple()
    value_type = type(value)
    if value_type.__module__ == "datetime" and value_type.__name__ == "datetime":
        return value == normalized and value.tzinfo is normalized.tzinfo
    if type(value) is tuple:
        return len(value) == len(normalized) and all(
            _canonical_equal(left, right)
            for left, right in zip(value, normalized, strict=True)
        )
    slots = getattr(value_type, "__slots__", None)
    if type(slots) is tuple:
        return all(
            _canonical_equal(getattr(value, name), getattr(normalized, name))
            for name in slots
        )
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


def _is_canonical_utc_datetime(value: object) -> bool:
    value_type = type(value)
    if value_type.__module__ != "datetime" or value_type.__name__ != "datetime":
        return False
    timezone_value = value.tzinfo
    timezone_type = type(timezone_value)
    return timezone_value is not None and timezone_value is getattr(
        timezone_type,
        "utc",
        None,
    )


def _validate_record_shape(
    record: TeamEvidenceAggregationRecord,
    *,
    index: int,
) -> None:
    _validate_hard_flags(f"records[{index}]", record)
    layers = (
        ("source_lineage", record.source_lineage, TeamEvidenceSourceLineage),
        ("capture", record.capture, TeamEvidenceCapture),
        ("evidence_revision", record.evidence_revision, TeamEvidenceRevision),
        ("assessment_revision", record.assessment_revision, TeamEvidenceAssessmentRevision),
    )
    if any(type(layer) is not expected for _, layer, expected in layers):
        raise ValueError(f"records[{index}] must be canonical")
    for layer_name, layer, _ in layers:
        _validate_hard_flags(f"records[{index}].{layer_name}", layer)
    key_values = (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )
    if not all(_is_identifier(value) for value in key_values):
        raise ValueError(f"records[{index}] must be canonical")
    if not _is_canonical_utc_datetime(record.capture.captured_at):
        raise ValueError(f"records[{index}] must be canonical")
    _canonical_ratio(
        f"records[{index}].assessment_revision.requested_weight",
        record.assessment_revision.requested_weight,
        positive=True,
    )
    _validate_group_key(
        f"records[{index}].assessment_revision.independence_key",
        record.assessment_revision.independence_key,
    )
    _validate_group_key(
        f"records[{index}].assessment_revision.correlation_key",
        record.assessment_revision.correlation_key,
    )


def _validate_allocation_inputs(
    records: object,
    config: object,
) -> tuple[TeamEvidenceAggregationRecord, ...]:
    if type(records) is not tuple:
        raise ValueError("records must be an exact tuple")
    if type(config) is not TeamEvidenceAggregationConfig:
        raise ValueError("config must be exactly TeamEvidenceAggregationConfig")
    typed_config = cast(TeamEvidenceAggregationConfig, config)
    _validate_hard_flags("config", typed_config)
    for index, record in enumerate(records):
        if type(record) is not TeamEvidenceAggregationRecord:
            raise ValueError(
                f"records[{index}] must be exactly TeamEvidenceAggregationRecord"
            )
    maximum_records = typed_config.maximum_records
    if (
        type(maximum_records) is not int
        or not 1 <= maximum_records <= _IMPLEMENTATION_MAXIMUM_RECORDS
    ):
        raise ValueError("config.maximum_records must be an exact int in 1..128")
    if len(records) > maximum_records or len(records) > _IMPLEMENTATION_MAXIMUM_RECORDS:
        raise ValueError("records exceeds config.maximum_records")
    _canonical_ratio(
        "config.independence_group_weight_cap",
        typed_config.independence_group_weight_cap,
        positive=False,
    )
    _canonical_ratio(
        "config.correlation_group_weight_cap",
        typed_config.correlation_group_weight_cap,
        positive=False,
    )
    _canonical_reconstruction("config", typed_config)
    typed_records = cast(tuple[TeamEvidenceAggregationRecord, ...], records)
    for index, record in enumerate(typed_records):
        _validate_record_shape(record, index=index)
    ordered = tuple(sorted(typed_records, key=_record_key))
    if len({_record_key(record) for record in ordered}) != len(ordered):
        raise ValueError("records contains duplicate canonical record key")
    for index, record in enumerate(ordered):
        _canonical_reconstruction(f"records[{index}]", record)
    return ordered


def _weight_to_micro_units(field_name: str, value: object) -> int:
    weight = _canonical_ratio(field_name, value, positive=False)
    _, digits, exponent = weight.as_tuple()
    assert exponent == -6
    units = 0
    for digit in digits:
        units = units * 10 + digit
    return units


def _micro_units_to_weight(value: int) -> Decimal:
    assert type(value) is int and 0 <= value <= _MICRO_UNITS_PER_ONE
    if value == 0:
        return _ZERO_WEIGHT
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(
            f"{value // _MICRO_UNITS_PER_ONE}."
            f"{value % _MICRO_UNITS_PER_ONE:06d}"
        )


def _apportion_micro_units(
    indexed_weights: tuple[tuple[int, int], ...],
    *,
    cap_micro_units: int,
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> tuple[tuple[int, int], ...]:
    total = sum(weight for _, weight in indexed_weights)
    if total <= cap_micro_units:
        return indexed_weights
    floors: dict[int, int] = {}
    remainders: dict[int, int] = {}
    for index, weight in indexed_weights:
        numerator = weight * cap_micro_units
        floors[index], remainders[index] = divmod(numerator, total)
    remaining = cap_micro_units - sum(floors.values())
    ranked = sorted(
        (index for index, _ in indexed_weights),
        key=lambda index: (-remainders[index], _record_key(records[index])),
    )
    for index in ranked[:remaining]:
        floors[index] += 1
    result = tuple((index, floors[index]) for index, _ in indexed_weights)
    assert sum(weight for _, weight in result) == cap_micro_units
    assert all(0 <= weight <= dict(indexed_weights)[index] for index, weight in result)
    return result


def _apply_cap_stage(
    input_micro_units: tuple[int, ...],
    *,
    group_keys: tuple[str, ...],
    cap_micro_units: int,
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    output = list(input_micro_units)
    flags = [False] * len(input_micro_units)
    for group_key in dict.fromkeys(group_keys):
        indexes = tuple(index for index, key in enumerate(group_keys) if key == group_key)
        indexed = tuple((index, input_micro_units[index]) for index in indexes)
        strict_over_cap = sum(weight for _, weight in indexed) > cap_micro_units
        if strict_over_cap:
            for index, weight in _apportion_micro_units(
                indexed,
                cap_micro_units=cap_micro_units,
                records=records,
            ):
                output[index] = weight
                flags[index] = True
    result = tuple(output)
    assert all(0 <= value <= input_micro_units[index] for index, value in enumerate(result))
    return result, tuple(flags)


def allocate_team_evidence_weights(
    records: tuple[TeamEvidenceAggregationRecord, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceWeightAllocation, ...]:
    ordered = _validate_allocation_inputs(records, config)
    if not ordered:
        return ()
    requested = tuple(
        _weight_to_micro_units(
            f"records[{index}].assessment_revision.requested_weight",
            record.assessment_revision.requested_weight,
        )
        for index, record in enumerate(ordered)
    )
    independence_keys = tuple(
        record.assessment_revision.independence_key for record in ordered
    )
    correlation_keys = tuple(
        record.assessment_revision.correlation_key for record in ordered
    )
    independence, independence_flags = _apply_cap_stage(
        requested,
        group_keys=independence_keys,
        cap_micro_units=_weight_to_micro_units(
            "config.independence_group_weight_cap",
            config.independence_group_weight_cap,
        ),
        records=ordered,
    )
    effective, correlation_flags = _apply_cap_stage(
        independence,
        group_keys=correlation_keys,
        cap_micro_units=_weight_to_micro_units(
            "config.correlation_group_weight_cap",
            config.correlation_group_weight_cap,
        ),
        records=ordered,
    )
    return tuple(
        TeamEvidenceWeightAllocation(
            source_lineage_id=record.source_lineage.source_lineage_id,
            capture_id=record.capture.capture_id,
            evidence_revision_id=record.evidence_revision.evidence_revision_id,
            assessment_revision_id=record.assessment_revision.assessment_revision_id,
            independence_key=independence_keys[index],
            correlation_key=correlation_keys[index],
            requested_weight=_micro_units_to_weight(requested[index]),
            independence_allocated_weight=_micro_units_to_weight(independence[index]),
            effective_weight=_micro_units_to_weight(effective[index]),
            independence_cap_applied=independence_flags[index],
            correlation_cap_applied=correlation_flags[index],
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for index, record in enumerate(ordered)
    )
