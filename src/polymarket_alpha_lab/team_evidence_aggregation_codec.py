from __future__ import annotations as _annotations

import dataclasses as _dataclasses
import datetime as _datetime
import decimal as _decimal
import hashlib as _hashlib
import json as _json
import typing as _typing

import polymarket_alpha_lab.team_evidence_aggregation_types as _types


__all__ = (
    "team_evidence_aggregation_config_payload",
    "team_evidence_aggregation_input_payload",
    "team_evidence_aggregation_config_digest",
    "team_evidence_aggregation_core_payload",
    "team_evidence_aggregation_payload",
    "team_evidence_aggregation_core_digest",
    "validate_team_evidence_aggregation_core_digest",
)


_CONFIG_SCHEMA: _typing.Final = "pal.team_evidence_aggregation.config.v1"
_INPUT_SCHEMA: _typing.Final = "pal.team_evidence_aggregation.input.v1"
_CORE_SCHEMA: _typing.Final = "pal.team_evidence_aggregation.core.v1"
_RESULT_SCHEMA: _typing.Final = "pal.team_evidence_aggregation.result.v1"
_CONFIG_DOMAIN: _typing.Final = b"pal.team_evidence_aggregation.config.v1\x00"
_CORE_DOMAIN: _typing.Final = b"pal.team_evidence_aggregation.core.v1\x00"


_FIELD_NAMES: _typing.Final[dict[type[object], tuple[str, ...]]] = {
    _types.TeamEvidenceSourceLineage: (
        "source_lineage_id",
        "source_lineage_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceCapture: (
        "capture_id",
        "capture_digest",
        "source_lineage_id",
        "source_lineage_digest",
        "content_digest",
        "captured_at",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceRevision: (
        "evidence_revision_id",
        "evidence_revision_digest",
        "previous_evidence_revision_id",
        "previous_evidence_revision_digest",
        "source_lineage_id",
        "source_lineage_digest",
        "content_digest",
        "requirement_ids",
        "freshness_anchor_at",
        "recorded_at",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceAssessmentRevision: (
        "assessment_revision_id",
        "assessment_revision_digest",
        "previous_assessment_revision_id",
        "previous_assessment_revision_digest",
        "evidence_revision_id",
        "evidence_revision_digest",
        "assessed_at",
        "probability_yes",
        "requested_weight",
        "rationale_digest",
        "independence_key",
        "correlation_key",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceAggregationRecord: (
        "source_lineage",
        "capture",
        "evidence_revision",
        "assessment_revision",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceCurrentRevisionSelection: (
        "evidence_revision_id",
        "evidence_revision_digest",
        "assessment_revision_id",
        "assessment_revision_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceAggregationInput: (
        "evaluated_at",
        "records",
        "current_revisions",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceRequirement: (
        "requirement_id",
        "minimum_witness_count",
        "minimum_effective_weight",
        "unmet_status",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceAggregationConfig: (
        "config_version",
        "max_evidence_age_seconds",
        "max_capture_lag_seconds",
        "independence_group_weight_cap",
        "correlation_group_weight_cap",
        "max_requirement_assignments_per_evidence",
        "contradiction_no_probability_max",
        "contradiction_yes_probability_min",
        "contradiction_watch_score",
        "contradiction_block_score",
        "publish_probability_floor",
        "publish_probability_ceiling",
        "maximum_records",
        "maximum_requirements",
        "maximum_requirement_memberships",
        "maximum_witness_edges",
        "requirements",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceTemporalAssessment: (
        "capture_id",
        "evidence_revision_id",
        "assessment_revision_id",
        "evidence_age_seconds",
        "capture_lag_seconds",
        "effective_at_evaluation",
        "captured_at_evaluation",
        "evidence_revision_available_at_evaluation",
        "assessment_revision_available_at_evaluation",
        "fresh",
        "timely",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceWeightAllocation: (
        "source_lineage_id",
        "capture_id",
        "evidence_revision_id",
        "assessment_revision_id",
        "independence_key",
        "correlation_key",
        "requested_weight",
        "independence_allocated_weight",
        "effective_weight",
        "independence_cap_applied",
        "correlation_cap_applied",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceRequirementWitness: (
        "requirement_id",
        "source_lineage_id",
        "capture_id",
        "evidence_revision_id",
        "assessment_revision_id",
        "independence_key",
        "effective_weight",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceRequirementCoverage: (
        "requirement_id",
        "minimum_witness_count",
        "assigned_witness_count",
        "minimum_effective_weight",
        "unmet_status",
        "satisfied",
        "witnesses",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceDiagnosticRow: (
        "source_lineage_id",
        "capture_id",
        "captured_at",
        "evidence_revision_id",
        "assessment_revision_id",
        "probability_yes",
        "requested_weight",
        "independence_allocated_weight",
        "effective_weight",
        "evidence_age_seconds",
        "capture_lag_seconds",
        "captured_at_evaluation",
        "evidence_revision_available_at_evaluation",
        "assessment_revision_available_at_evaluation",
        "selected_current_revision",
        "canonical_capture",
        "disposition",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceContradictionResult: (
        "yes_support_weight",
        "no_support_weight",
        "neutral_weight",
        "contradiction_score",
        "status",
        "paper_only",
        "report_only",
        "readonly",
    ),
    _types.TeamEvidenceAggregationResult: (
        "evaluated_at",
        "config_version",
        "config_digest",
        "status",
        "diagnostic_record_count",
        "arithmetic_record_count",
        "requested_weight_total",
        "independence_allocated_weight_total",
        "effective_weight_total",
        "arithmetic_probability_yes",
        "publishable_probability_yes",
        "contradiction",
        "requirement_coverage",
        "diagnostics",
        "reason_codes",
        "core_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
}


for _registered_class, _registered_names in _FIELD_NAMES.items():
    if _registered_names != tuple(
        _field.name for _field in _dataclasses.fields(_registered_class)
    ):
        raise RuntimeError("team evidence codec field registry is inconsistent")


def _decimal_string(value: object, *, path: str) -> str:
    if type(value) is not _decimal.Decimal or not value.is_finite():
        raise ValueError(f"{path} must be an exact finite Decimal")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{path} must have exact fixed-six Decimal exponent")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{path} must use unsigned canonical zero")
    return format(value, ".6f")


def _datetime_string(value: object, *, path: str) -> str:
    if type(value) is not _datetime.datetime or value.tzinfo is not _datetime.UTC:
        raise ValueError(f"{path} must be an exact aware UTC datetime")
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d}T"
        f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}."
        f"{value.microsecond:06d}+00:00"
    )


def _direct_map(value: object, *, path: str) -> dict[str, object]:
    value_type = type(value)
    field_names = _FIELD_NAMES.get(value_type)
    if field_names is None:
        raise ValueError(f"{path} must be an exact registered team evidence dataclass")
    try:
        raw_fields = {name: getattr(value, name) for name in field_names}
    except AttributeError as error:
        raise ValueError(f"{path} must contain every canonical field") from error
    encoded = {
        name: _encode_value(field_value, path=f"{path}.{name}")
        for name, field_value in raw_fields.items()
    }
    try:
        normalized = value_type(**raw_fields)
    except (AttributeError, TypeError, UnicodeError) as error:
        raise ValueError(f"{path} must contain canonical field values") from error
    normalized_encoded = {
        name: _encode_value(getattr(normalized, name), path=f"{path}.{name}")
        for name in field_names
    }
    if encoded != normalized_encoded:
        raise ValueError(f"{path} must contain exact canonical scalar and tuple values")
    return encoded


def _encode_value(value: object, *, path: str) -> object:
    if type(value) in _FIELD_NAMES:
        return _direct_map(value, path=path)
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        return value
    if type(value) is str:
        return value
    if type(value) is _decimal.Decimal:
        return _decimal_string(value, path=path)
    if type(value) is _datetime.datetime:
        return _datetime_string(value, path=path)
    if type(value) is tuple:
        return [
            _encode_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path} contains a non-canonical or non-JSON-ready value")


def _top_level_map(
    value: object,
    expected_type: type[object],
    *,
    path: str,
) -> dict[str, object]:
    if type(value) is not expected_type:
        raise ValueError(f"{path} must be exactly {expected_type.__name__}")
    return _direct_map(value, path=path)


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return _json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def team_evidence_aggregation_config_payload(
    config: _types.TeamEvidenceAggregationConfig,
) -> dict[str, object]:
    return {
        "schema_version": _CONFIG_SCHEMA,
        "config": _top_level_map(
            config,
            _types.TeamEvidenceAggregationConfig,
            path="config",
        ),
    }


def team_evidence_aggregation_input_payload(
    aggregation_input: _types.TeamEvidenceAggregationInput,
) -> dict[str, object]:
    return {
        "schema_version": _INPUT_SCHEMA,
        "input": _top_level_map(
            aggregation_input,
            _types.TeamEvidenceAggregationInput,
            path="input",
        ),
    }


def team_evidence_aggregation_config_digest(
    config: _types.TeamEvidenceAggregationConfig,
) -> str:
    payload = team_evidence_aggregation_config_payload(config)
    return _hashlib.sha256(_CONFIG_DOMAIN + _canonical_bytes(payload)).hexdigest()


def team_evidence_aggregation_core_payload(
    result: _types.TeamEvidenceAggregationResult,
) -> dict[str, object]:
    direct = _top_level_map(
        result,
        _types.TeamEvidenceAggregationResult,
        path="result",
    )
    return {
        "schema_version": _CORE_SCHEMA,
        "result": {
            name: direct[name]
            for name in _FIELD_NAMES[_types.TeamEvidenceAggregationResult]
            if name != "core_digest"
        },
    }


def team_evidence_aggregation_payload(
    result: _types.TeamEvidenceAggregationResult,
) -> dict[str, object]:
    validate_team_evidence_aggregation_core_digest(result)
    return {
        "schema_version": _RESULT_SCHEMA,
        "result": _top_level_map(
            result,
            _types.TeamEvidenceAggregationResult,
            path="result",
        ),
    }


def team_evidence_aggregation_core_digest(
    result: _types.TeamEvidenceAggregationResult,
) -> str:
    payload = team_evidence_aggregation_core_payload(result)
    return _hashlib.sha256(_CORE_DOMAIN + _canonical_bytes(payload)).hexdigest()


def validate_team_evidence_aggregation_core_digest(
    result: _types.TeamEvidenceAggregationResult,
) -> None:
    recomputed = team_evidence_aggregation_core_digest(result)
    if result.core_digest != recomputed:
        raise ValueError("result.core_digest does not match canonical core payload")
    return None
