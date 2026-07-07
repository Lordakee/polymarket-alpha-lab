"""Pure row codec for persisted candidate decision score reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.candidate_decision_score import (
    ACTION_STATES,
    CandidateDecisionScoreReport,
    candidate_decision_score_payload,
)
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "CandidateDecisionScoreDbRow",
    "candidate_decision_score_report_from_db_row",
    "candidate_decision_score_report_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MISSING = object()
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_DECIMAL_PAYLOAD_FIELDS = frozenset(
    (
        "forecast_probability",
        "executable_price",
        "gross_edge",
        "estimated_cost_drag",
        "net_edge",
        "cost_score",
        "liquidity_score",
        "evidence_score",
        "resolution_score",
        "team_memory_score",
        "decision_score",
    ),
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_id",
        "market_id",
        "normalized_market_question",
        "primary_team_id",
        "secondary_team_ids",
        "selected_side",
        "forecast_probability",
        "executable_price",
        "gross_edge",
        "estimated_cost_drag",
        "net_edge",
        "cost_score",
        "liquidity_score",
        "evidence_score",
        "resolution_score",
        "team_memory_score",
        "team_memory_policy",
        "decision_score",
        "action",
        "hard_blocker_codes",
        "reason_codes",
        "source_report_refs",
        "derived_validation_digest",
        "boundary_statement",
        *_HARD_FLAG_NAMES,
    ),
)


@dataclass(frozen=True)
class CandidateDecisionScoreDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_id: str
    primary_team_id: str
    action: str
    decision_score: Decimal
    reason_codes_json: list[str]
    source_report_refs_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "config_version",
            "candidate_id",
            "market_id",
            "primary_team_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("action", self.action, ACTION_STATES)
        object.__setattr__(
            self,
            "decision_score",
            _normalize_score_decimal("decision_score", self.decision_score),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_json_array("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "source_report_refs_json",
            _normalize_string_json_array(
                "source_report_refs_json",
                self.source_report_refs_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        require_paper_only_flags("candidate decision score DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_payload_schema(self.payload_json)
        _validate_materialized_fields_match_payload(self)
        report = _validate_payload_recovers_to_compatible_report(self.payload_json)
        _validate_materialized_fields_match_report(self, report)


def candidate_decision_score_report_to_db_row(
    report: CandidateDecisionScoreReport,
) -> CandidateDecisionScoreDbRow:
    if type(report) is not CandidateDecisionScoreReport:
        raise ValueError("report must be a CandidateDecisionScoreReport")
    require_paper_only_flags("CandidateDecisionScoreReport", report)
    payload_json = candidate_decision_score_payload(report)
    return CandidateDecisionScoreDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_id=report.candidate_id,
        market_id=report.market_id,
        primary_team_id=report.primary_team_id,
        action=report.action,
        decision_score=report.decision_score,
        reason_codes_json=list(report.reason_codes),
        source_report_refs_json=list(report.source_report_refs),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def candidate_decision_score_report_from_db_row(
    row: CandidateDecisionScoreDbRow,
) -> CandidateDecisionScoreReport:
    if type(row) is not CandidateDecisionScoreDbRow:
        raise ValueError("row must be a CandidateDecisionScoreDbRow")
    validated = CandidateDecisionScoreDbRow(**_row_values(row))
    return _validate_payload_recovers_to_compatible_report(validated.payload_json)


def _row_values(row: CandidateDecisionScoreDbRow) -> dict[str, Any]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "candidate_id": row.candidate_id,
        "market_id": row.market_id,
        "primary_team_id": row.primary_team_id,
        "action": row.action,
        "decision_score": row.decision_score,
        "reason_codes_json": row.reason_codes_json,
        "source_report_refs_json": row.source_report_refs_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_payload_recovers_to_compatible_report(
    payload_json: dict[str, Any],
) -> CandidateDecisionScoreReport:
    try:
        report = from_jsonable(CandidateDecisionScoreReport, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid candidate decision score report: {exc}") from exc
    if type(report) is not CandidateDecisionScoreReport:
        raise ValueError("payload_json must recover a CandidateDecisionScoreReport")
    require_paper_only_flags("CandidateDecisionScoreReport", report)
    expected_payload_json = candidate_decision_score_payload(report)
    _validate_json_compatible(payload_json, expected_payload_json)
    return report


def _validate_materialized_fields_match_report(
    row: CandidateDecisionScoreDbRow,
    report: CandidateDecisionScoreReport,
) -> None:
    expected_values = {
        "report_sha256": _report_sha256(candidate_decision_score_payload(report)),
        "generated_at": _as_utc("generated_at", report.generated_at),
        "config_version": report.config_version,
        "candidate_id": report.candidate_id,
        "market_id": report.market_id,
        "primary_team_id": report.primary_team_id,
        "action": report.action,
        "decision_score": report.decision_score,
        "reason_codes_json": list(report.reason_codes),
        "source_report_refs_json": list(report.source_report_refs),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "candidate_id": row.candidate_id,
        "market_id": row.market_id,
        "primary_team_id": row.primary_team_id,
        "action": row.action,
        "decision_score": row.decision_score,
        "reason_codes_json": row.reason_codes_json,
        "source_report_refs_json": row.source_report_refs_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        expected_value = expected_values[field_name]
        if type(actual_value) is not type(expected_value) or actual_value != expected_value:
            raise ValueError(f"{field_name} must match recovered report")


def _validate_materialized_fields_match_payload(
    row: CandidateDecisionScoreDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "candidate_id": payload_json.get("candidate_id", _MISSING),
        "market_id": payload_json.get("market_id", _MISSING),
        "primary_team_id": payload_json.get("primary_team_id", _MISSING),
        "action": payload_json.get("action", _MISSING),
        "decision_score": payload_json.get("decision_score", _MISSING),
        "reason_codes_json": payload_json.get("reason_codes", _MISSING),
        "source_report_refs_json": payload_json.get("source_report_refs", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "candidate_id": row.candidate_id,
        "market_id": row.market_id,
        "primary_team_id": row.primary_team_id,
        "action": row.action,
        "decision_score": _fixed_six_decimal_string(
            "decision_score",
            row.decision_score,
        ),
        "reason_codes_json": row.reason_codes_json,
        "source_report_refs_json": row.source_report_refs_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        _require_json_exact_match(field_name, actual_value, expected_values[field_name])


def _validate_payload_schema(payload_json: dict[str, Any]) -> None:
    if set(payload_json) != _REPORT_PAYLOAD_FIELDS:
        missing = sorted(_REPORT_PAYLOAD_FIELDS - set(payload_json))
        if missing:
            raise ValueError(f"payload_json {missing[0]} is required")
        extra = sorted(set(payload_json) - _REPORT_PAYLOAD_FIELDS)
        raise ValueError(f"payload_json {extra[0]} is not allowed")
    for field_name in _DECIMAL_PAYLOAD_FIELDS:
        value = payload_json[field_name]
        if value is not None:
            _fixed_six_decimal_json_string(field_name, value)
    for field_name in ("reason_codes", "source_report_refs", "hard_blocker_codes"):
        _normalize_string_json_array(field_name, payload_json[field_name])
    _normalize_string_json_array("secondary_team_ids", payload_json["secondary_team_ids"])


def _validate_json_compatible(
    actual: object,
    expected: object,
    path: tuple[str, ...] = (),
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{'.'.join(path) or 'payload_json'} has wrong JSON type")
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():  # type: ignore[union-attr]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} keys differ")
        for key in actual:
            _validate_json_compatible(
                actual[key],
                expected[key],  # type: ignore[index]
                (*path, key),
            )
        return
    if isinstance(actual, list):
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} length differs")
        for index, item in enumerate(actual):
            _validate_json_compatible(
                item,
                expected[index],  # type: ignore[index]
                (*path, str(index)),
            )
        return
    if actual != expected:
        raise ValueError(f"{'.'.join(path) or 'payload_json'} differs")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_value(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    reject_unsafe_surface_fields("candidate decision score DB row payload", normalized)
    return normalized


def _copy_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain datetime")
    if type(value) in (str, int, bool):
        return value
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    raise ValueError("JSON value must be a dict, list, string, int, bool, or null")


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    for flag_name in _HARD_FLAG_NAMES:
        if flag_name in value and value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _normalize_string_json_array(field_name: str, value: object) -> list[str]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fixed_six_decimal_json_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _fixed_six_decimal_string(field_name, decimal_value)


def _fixed_six_decimal_string(field_name: str, value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext() as context:
            integer_digits = max(value.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            quantized = value.quantize(_DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must not exceed six decimal places") from exc
    if quantized != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    if quantized.is_zero():
        quantized = _ZERO
    return format(quantized, "f")


def _normalize_score_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    decimal_string = _fixed_six_decimal_string(field_name, value)
    normalized = Decimal(decimal_string)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_json_exact_match(
    field_name: str,
    actual_value: object,
    expected_value: object,
) -> None:
    if type(actual_value) is not type(expected_value) or actual_value != expected_value:
        raise ValueError(f"{field_name} must match payload_json")
