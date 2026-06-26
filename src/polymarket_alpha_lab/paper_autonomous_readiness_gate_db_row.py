"""Pure row codec for paper autonomous readiness gate reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_readiness_gate import (
    PaperAutonomousReadinessGateReport,
    READINESS_STATUSES,
)

__all__ = (
    "PaperAutonomousReadinessGateDbRow",
    "from_db_row",
    "paper_autonomous_readiness_gate_from_db_row",
    "paper_autonomous_readiness_gate_report_from_db_row",
    "paper_autonomous_readiness_gate_report_to_db_row",
    "paper_autonomous_readiness_gate_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "readiness_status",
    "recommended_next_step",
    "source_statuses_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousReadinessGateDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    readiness_status: str
    recommended_next_step: str
    source_statuses_json: list[dict[str, Any]]
    source_config_versions_json: list[list[str]]
    reason_code_counts_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_readiness_status("readiness_status", self.readiness_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "source_statuses_json",
            _normalize_json_object_array(
                "source_statuses_json",
                self.source_statuses_json,
            ),
        )
        object.__setattr__(
            self,
            "source_config_versions_json",
            _normalize_string_pair_array(
                "source_config_versions_json",
                self.source_config_versions_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_json_object_array(
                "reason_code_counts_json",
                self.reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_materialized_fields_match_payload(self)
        _validate_json_hard_flags(self.payload_json, "payload_json")


def paper_autonomous_readiness_gate_to_db_row(
    report: PaperAutonomousReadinessGateReport,
) -> PaperAutonomousReadinessGateDbRow:
    if type(report) is not PaperAutonomousReadinessGateReport:
        raise ValueError("report must be a PaperAutonomousReadinessGateReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    source_statuses_json = payload_json.get("source_statuses")
    source_config_versions_json = payload_json.get("source_config_versions")
    reason_code_counts_json = payload_json.get("reason_code_counts")
    reason_codes_json = payload_json.get("reason_codes")
    if not isinstance(source_statuses_json, list):
        raise ValueError("payload_json source_statuses must be a JSON array")
    if not isinstance(source_config_versions_json, list):
        raise ValueError("payload_json source_config_versions must be a JSON array")
    if not isinstance(reason_code_counts_json, list):
        raise ValueError("payload_json reason_code_counts must be a JSON array")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    return PaperAutonomousReadinessGateDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        readiness_status=report.readiness_status,
        recommended_next_step=report.recommended_next_step,
        source_statuses_json=source_statuses_json,
        source_config_versions_json=source_config_versions_json,
        reason_code_counts_json=reason_code_counts_json,
        reason_codes_json=reason_codes_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_readiness_gate_from_db_row(
    row: PaperAutonomousReadinessGateDbRow,
) -> PaperAutonomousReadinessGateReport:
    if type(row) is not PaperAutonomousReadinessGateDbRow:
        raise ValueError("row must be a PaperAutonomousReadinessGateDbRow")
    _reject_json_floats(row.source_statuses_json)
    _reject_json_floats(row.source_config_versions_json)
    _reject_json_floats(row.reason_code_counts_json)
    _reject_json_floats(row.reason_codes_json)
    _reject_json_floats(row.payload_json)
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    if row.source_statuses_json != row.payload_json.get("source_statuses"):
        raise ValueError("source_statuses_json must match payload_json")
    if row.source_config_versions_json != row.payload_json.get("source_config_versions"):
        raise ValueError("source_config_versions_json must match payload_json")
    if row.reason_code_counts_json != row.payload_json.get("reason_code_counts"):
        raise ValueError("reason_code_counts_json must match payload_json")
    if row.reason_codes_json != row.payload_json.get("reason_codes"):
        raise ValueError("reason_codes_json must match payload_json")

    try:
        report = from_jsonable(PaperAutonomousReadinessGateReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid readiness gate report: {exc}",
        ) from exc
    if type(report) is not PaperAutonomousReadinessGateReport:
        raise ValueError("payload_json must recover a PaperAutonomousReadinessGateReport")
    _validate_report_tree(report)
    expected_row = paper_autonomous_readiness_gate_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperAutonomousReadinessGateReport,
) -> PaperAutonomousReadinessGateDbRow:
    return paper_autonomous_readiness_gate_to_db_row(report)


def from_db_row(
    row: PaperAutonomousReadinessGateDbRow,
) -> PaperAutonomousReadinessGateReport:
    return paper_autonomous_readiness_gate_from_db_row(row)


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


def _validate_row_matches_payload(
    row: PaperAutonomousReadinessGateDbRow,
    expected: PaperAutonomousReadinessGateDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperAutonomousReadinessGateDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at"),
        "config_version": payload_json.get("config_version"),
        "readiness_status": payload_json.get("readiness_status"),
        "recommended_next_step": payload_json.get("recommended_next_step"),
        "source_statuses_json": payload_json.get("source_statuses"),
        "source_config_versions_json": payload_json.get("source_config_versions"),
        "reason_code_counts_json": payload_json.get("reason_code_counts"),
        "reason_codes_json": payload_json.get("reason_codes"),
        "paper_only": payload_json.get("paper_only"),
        "report_only": payload_json.get("report_only"),
        "readonly": payload_json.get("readonly"),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "readiness_status": row.readiness_status,
        "recommended_next_step": row.recommended_next_step,
        "source_statuses_json": row.source_statuses_json,
        "source_config_versions_json": row.source_config_versions_json,
        "reason_code_counts_json": row.reason_code_counts_json,
        "reason_codes_json": row.reason_codes_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _MATERIALIZED_FIELDS:
        if actual_values[field_name] != expected_values[field_name]:
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
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
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
    raise ValueError("readiness gate DB row values must be JSON serializable")


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


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
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


def _normalize_string_pair_array(
    field_name: str,
    value: object,
) -> list[list[str]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    rows: list[list[str]] = []
    for item in normalized:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"{field_name} must contain source/version pairs")
        source_name, config_version = item
        _require_canonical_string(field_name, source_name)
        _require_canonical_string(field_name, config_version)
        rows.append([source_name, config_version])
    return rows


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    previous: str | None = None
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        normalized.append(item)
        seen.add(item)
        previous = item
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
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
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_readiness_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


paper_autonomous_readiness_gate_report_to_db_row = (
    paper_autonomous_readiness_gate_to_db_row
)
paper_autonomous_readiness_gate_report_from_db_row = (
    paper_autonomous_readiness_gate_from_db_row
)
