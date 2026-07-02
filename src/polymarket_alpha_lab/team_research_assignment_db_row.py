"""Pure row codec for team research assignment reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.json_recovery import from_jsonable

if TYPE_CHECKING:
    from polymarket_alpha_lab.team_research_assignment import (
        TeamResearchAssignmentReport,
    )


__all__ = (
    "TeamResearchAssignmentDbRow",
    "from_db_row",
    "team_research_assignment_report_from_db_row",
    "team_research_assignment_report_to_db_row",
    "to_db_row",
)


_ASSIGNMENT_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment"
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_queue_config_version",
    "source_route_config_version",
    "source_memory_config_version",
    "assignment_status",
    "assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)
_COUNT_FIELDS = (
    "assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
)
_VERSION_FIELDS = (
    "config_version",
    "source_queue_config_version",
    "source_route_config_version",
    "source_memory_config_version",
)
_PAYLOAD_FIELD_NAMES = (
    "generated_at",
    "config_version",
    "source_queue_config_version",
    "source_route_config_version",
    "source_memory_config_version",
    "assignment_status",
    "assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamResearchAssignmentDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_route_config_version: str
    source_memory_config_version: str
    assignment_status: str
    assignment_count: int
    assigned_count: int
    watch_count: int
    blocked_count: int
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in _VERSION_FIELDS:
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_canonical_string("assignment_status", self.assignment_status)
        for field_name in _COUNT_FIELDS:
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_constructor_payload_consistency(self)


def team_research_assignment_report_to_db_row(
    report: "TeamResearchAssignmentReport",
) -> TeamResearchAssignmentDbRow:
    report_type = _assignment_report_class()
    if type(report) is not report_type:
        raise ValueError("report must be a TeamResearchAssignmentReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    reason_codes_json = payload_json.get("reason_codes")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    return TeamResearchAssignmentDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_queue_config_version=report.source_queue_config_version,
        source_route_config_version=report.source_route_config_version,
        source_memory_config_version=report.source_memory_config_version,
        assignment_status=report.assignment_status,
        assignment_count=report.assignment_count,
        assigned_count=report.assigned_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        reason_codes_json=reason_codes_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def team_research_assignment_report_from_db_row(
    row: TeamResearchAssignmentDbRow,
) -> "TeamResearchAssignmentReport":
    if type(row) is not TeamResearchAssignmentDbRow:
        raise ValueError("row must be a TeamResearchAssignmentDbRow")
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row, payload_json)

    report_type = _assignment_report_class()
    try:
        report = from_jsonable(report_type, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid team research assignment report: {exc}",
        ) from exc
    if type(report) is not report_type:
        raise ValueError("payload_json must recover a TeamResearchAssignmentReport")
    _validate_report_tree(report)
    expected_row = team_research_assignment_report_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(report: "TeamResearchAssignmentReport") -> TeamResearchAssignmentDbRow:
    return team_research_assignment_report_to_db_row(report)


def from_db_row(
    row: TeamResearchAssignmentDbRow,
) -> "TeamResearchAssignmentReport":
    return team_research_assignment_report_from_db_row(row)


def _assignment_report_class() -> type[Any]:
    module = importlib.import_module(_ASSIGNMENT_MODULE_NAME)
    return module.TeamResearchAssignmentReport


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


def _validate_constructor_payload_consistency(
    row: TeamResearchAssignmentDbRow,
) -> None:
    _validate_json_hard_flags(row.payload_json, "payload_json")
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_materialized_fields_match_payload(row, row.payload_json)


def _validate_materialized_fields_match_payload(
    row: TeamResearchAssignmentDbRow,
    payload_json: dict[str, Any],
) -> None:
    for field_name in _PAYLOAD_FIELD_NAMES:
        _require_payload_value(payload_json, field_name, getattr(row, field_name))
    _require_payload_value(
        payload_json,
        "reason_codes",
        row.reason_codes_json,
        row_field_name="reason_codes_json",
    )


def _require_payload_value(
    payload_json: dict[str, Any],
    payload_field_name: str,
    value: Any,
    *,
    row_field_name: str | None = None,
) -> None:
    field_name = row_field_name or payload_field_name
    if payload_field_name not in payload_json:
        raise ValueError(f"{field_name} must match payload_json")
    if payload_json[payload_field_name] != _json_ready(value):
        raise ValueError(f"{field_name} must match payload_json")


def _validate_row_matches_payload(
    row: TeamResearchAssignmentDbRow,
    expected: TeamResearchAssignmentDbRow,
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
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("team research assignment DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        copied = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(copied, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    _validate_json_hard_flags(copied, field_name)
    return copied


def _copy_json_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain datetime")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_payload(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_payload(item) for item in value]
    raise ValueError("JSON value must be a dict, list, string, int, bool, or null")


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        reason_code = _require_reason_code(field_name, item)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        normalized.append(reason_code)
        seen.add(reason_code)
    return normalized


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    _require_canonical_string(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical tokens")
    return value


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if _looks_like_report_payload(value) or any(key in value for key in _HARD_FLAG_NAMES):
        for flag_name in _HARD_FLAG_NAMES:
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _looks_like_report_payload(value: dict[str, Any]) -> bool:
    return "generated_at" in value and "config_version" in value


def _has_hard_flag(value: Any) -> bool:
    return any(hasattr(value, flag_name) for flag_name in _HARD_FLAG_NAMES)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


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


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
