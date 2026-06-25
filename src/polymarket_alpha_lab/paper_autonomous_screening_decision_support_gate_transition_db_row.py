"""Pure row codec for paper autonomous screening gate transition reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    PaperAutonomousScreeningDecisionSupportGateTransitionReport,
)


__all__ = (
    "PaperAutonomousScreeningDecisionSupportGateTransitionDbRow",
    "from_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_from_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_report_from_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_report_to_db_row",
    "paper_autonomous_screening_decision_support_gate_transition_to_db_row",
    "to_db_row",
)


_GATE_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    gate_report_count: int
    transition_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_from_gate_status: str | None
    latest_to_gate_status: str | None
    latest_introduced_reason_codes_json: list[str]
    latest_cleared_reason_codes_json: list[str]
    latest_persistent_reason_codes_json: list[str]
    status_transition_rows_json: list[dict[str, Any]] | None
    reason_change_rows_json: list[dict[str, Any]] | None
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(
                "first_report_generated_at",
                self.first_report_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("gate_report_count", self.gate_report_count)
        _require_nonnegative_int("transition_count", self.transition_count)
        _require_optional_gate_status(
            "latest_from_gate_status",
            self.latest_from_gate_status,
        )
        _require_optional_gate_status(
            "latest_to_gate_status",
            self.latest_to_gate_status,
        )
        object.__setattr__(
            self,
            "latest_introduced_reason_codes_json",
            _normalize_string_list(
                "latest_introduced_reason_codes_json",
                self.latest_introduced_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "latest_cleared_reason_codes_json",
            _normalize_string_list(
                "latest_cleared_reason_codes_json",
                self.latest_cleared_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "latest_persistent_reason_codes_json",
            _normalize_string_list(
                "latest_persistent_reason_codes_json",
                self.latest_persistent_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "status_transition_rows_json",
            _normalize_optional_json_object_array(
                "status_transition_rows_json",
                self.status_transition_rows_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_change_rows_json",
            _normalize_optional_json_object_array(
                "reason_change_rows_json",
                self.reason_change_rows_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)


def paper_autonomous_screening_decision_support_gate_transition_to_db_row(
    report: Any,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
    if type(report) is not PaperAutonomousScreeningDecisionSupportGateTransitionReport:
        raise ValueError(
            "report must be a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    for field_name in (
        "latest_introduced_reason_codes",
        "latest_cleared_reason_codes",
        "latest_persistent_reason_codes",
    ):
        if not isinstance(payload_json.get(field_name), list):
            raise ValueError(f"payload_json {field_name} must be a JSON array")
    status_transition_rows_json = payload_json.get("status_transition_rows")
    if status_transition_rows_json is not None and not isinstance(
        status_transition_rows_json,
        list,
    ):
        raise ValueError("payload_json status_transition_rows must be a JSON array")
    reason_change_rows_json = payload_json.get("reason_change_rows")
    if reason_change_rows_json is not None and not isinstance(
        reason_change_rows_json,
        list,
    ):
        raise ValueError("payload_json reason_change_rows must be a JSON array")
    return PaperAutonomousScreeningDecisionSupportGateTransitionDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_report_count=report.gate_report_count,
        transition_count=report.transition_count,
        first_report_generated_at=report.first_report_generated_at,
        latest_report_generated_at=report.latest_report_generated_at,
        latest_from_gate_status=report.latest_from_gate_status,
        latest_to_gate_status=report.latest_to_gate_status,
        latest_introduced_reason_codes_json=payload_json[
            "latest_introduced_reason_codes"
        ],
        latest_cleared_reason_codes_json=payload_json[
            "latest_cleared_reason_codes"
        ],
        latest_persistent_reason_codes_json=payload_json[
            "latest_persistent_reason_codes"
        ],
        status_transition_rows_json=status_transition_rows_json,
        reason_change_rows_json=reason_change_rows_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_screening_decision_support_gate_transition_from_db_row(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    if type(row) is not PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
        raise ValueError(
            "row must be a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionDbRow",
        )
    _reject_json_floats(row.latest_introduced_reason_codes_json)
    _reject_json_floats(row.latest_cleared_reason_codes_json)
    _reject_json_floats(row.latest_persistent_reason_codes_json)
    _reject_json_floats(row.status_transition_rows_json)
    _reject_json_floats(row.reason_change_rows_json)
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_row_json_fields_match_payload(row)
    _validate_row_scalars_match_payload(row)
    try:
        report = from_jsonable(
            PaperAutonomousScreeningDecisionSupportGateTransitionReport,
            row.payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid autonomous screening gate transition "
            f"report: {exc}",
        ) from exc
    if type(report) is not PaperAutonomousScreeningDecisionSupportGateTransitionReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousScreeningDecisionSupportGateTransitionReport",
        )
    _validate_report_tree(report)
    expected_row = (
        paper_autonomous_screening_decision_support_gate_transition_to_db_row(
            report,
        )
    )
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: Any,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
    return paper_autonomous_screening_decision_support_gate_transition_to_db_row(
        report,
    )


def from_db_row(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    return paper_autonomous_screening_decision_support_gate_transition_from_db_row(
        row,
    )


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_report_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_report_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_report_tree(item, f"{field_name}.{index}")


def _validate_row_json_fields_match_payload(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
) -> None:
    pairs = (
        (
            "latest_introduced_reason_codes_json",
            "latest_introduced_reason_codes",
        ),
        ("latest_cleared_reason_codes_json", "latest_cleared_reason_codes"),
        (
            "latest_persistent_reason_codes_json",
            "latest_persistent_reason_codes",
        ),
        ("status_transition_rows_json", "status_transition_rows"),
        ("reason_change_rows_json", "reason_change_rows"),
    )
    for row_field, payload_field in pairs:
        if getattr(row, row_field) != row.payload_json.get(payload_field):
            raise ValueError(f"{row_field} must match payload_json")


def _validate_row_scalars_match_payload(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
) -> None:
    for field_name in _SCALAR_PAYLOAD_FIELDS:
        if row.payload_json.get(field_name) != _json_ready(getattr(row, field_name)):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_matches_payload(
    row: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
    expected: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError(
        "autonomous screening gate transition row values must be JSON serializable",
    )


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_optional_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return normalized


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    previous: str | None = None
    for item in value:
        _require_canonical_string(field_name, item)
        if previous is not None and previous >= item:
            raise ValueError(f"{field_name} must be sorted and unique")
        normalized.append(item)
        previous = item
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly")):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_gate_status(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


_SCALAR_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "gate_report_count",
    "transition_count",
    "first_report_generated_at",
    "latest_report_generated_at",
    "latest_from_gate_status",
    "latest_to_gate_status",
)
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "latest_introduced_reason_codes_json",
    "latest_cleared_reason_codes_json",
    "latest_persistent_reason_codes_json",
    "status_transition_rows_json",
    "reason_change_rows_json",
    "paper_only",
    "report_only",
    "readonly",
    *_SCALAR_PAYLOAD_FIELDS,
)


paper_autonomous_screening_decision_support_gate_transition_report_to_db_row = (
    paper_autonomous_screening_decision_support_gate_transition_to_db_row
)
paper_autonomous_screening_decision_support_gate_transition_report_from_db_row = (
    paper_autonomous_screening_decision_support_gate_transition_from_db_row
)
