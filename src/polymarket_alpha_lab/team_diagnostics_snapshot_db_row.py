"""Pure row codec for team diagnostics snapshot reports."""

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
    from polymarket_alpha_lab.team_diagnostics_snapshot import (
        TeamDiagnosticsSnapshotReport,
    )


__all__ = (
    "TeamDiagnosticsSnapshotDbRow",
    "from_db_row",
    "team_diagnostics_snapshot_report_from_db_row",
    "team_diagnostics_snapshot_report_to_db_row",
    "to_db_row",
)


_SNAPSHOT_MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot"
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_FILTER_NAMES = ("team_id", "market_slug", "forecast_id")
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "team_id",
    "market_slug",
    "forecast_id",
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
    "memory_eligible_reference_count",
    "calibration_status",
    "calibration_settled_count",
    "calibration_group_count",
    "event_template_row_count",
    "event_template_status",
    "source_reliability_row_count",
    "source_reliability_missing_source_evidence_count",
    "evidence_quality_status",
    "evidence_quality_pass_count",
    "evidence_quality_watch_count",
    "evidence_quality_blocked_count",
    "evidence_quality_average_quality_score",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)
_COUNT_FIELDS = (
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
    "memory_eligible_reference_count",
    "calibration_settled_count",
    "calibration_group_count",
    "event_template_row_count",
    "source_reliability_row_count",
    "source_reliability_missing_source_evidence_count",
    "evidence_quality_pass_count",
    "evidence_quality_watch_count",
    "evidence_quality_blocked_count",
)
_STATUS_FIELDS = (
    "calibration_status",
    "event_template_status",
    "evidence_quality_status",
)
_PAYLOAD_FIELD_NAMES = (
    "generated_at",
    "config_version",
    "source_config_version",
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
    "memory_eligible_reference_count",
    "calibration_status",
    "calibration_settled_count",
    "calibration_group_count",
    "event_template_row_count",
    "event_template_status",
    "source_reliability_row_count",
    "source_reliability_missing_source_evidence_count",
    "evidence_quality_status",
    "evidence_quality_pass_count",
    "evidence_quality_watch_count",
    "evidence_quality_blocked_count",
    "evidence_quality_average_quality_score",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    team_id: str | None
    market_slug: str | None
    forecast_id: str | None
    forecast_row_count: int
    evidence_row_count: int
    outcome_row_count: int
    memory_eligible_reference_count: int
    calibration_status: str
    calibration_settled_count: int
    calibration_group_count: int
    event_template_row_count: int
    event_template_status: str
    source_reliability_row_count: int
    source_reliability_missing_source_evidence_count: int
    evidence_quality_status: str
    evidence_quality_pass_count: int
    evidence_quality_watch_count: int
    evidence_quality_blocked_count: int
    evidence_quality_average_quality_score: Decimal
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_optional_canonical_string("team_id", self.team_id)
        _require_optional_canonical_string("market_slug", self.market_slug)
        _require_optional_canonical_string("forecast_id", self.forecast_id)
        for field_name in _COUNT_FIELDS:
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in _STATUS_FIELDS:
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_quality_average_quality_score",
            _normalize_probability(
                "evidence_quality_average_quality_score",
                self.evidence_quality_average_quality_score,
            ),
        )
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


def team_diagnostics_snapshot_report_to_db_row(
    report: "TeamDiagnosticsSnapshotReport",
) -> TeamDiagnosticsSnapshotDbRow:
    report_type = _snapshot_report_class()
    if type(report) is not report_type:
        raise ValueError("report must be a TeamDiagnosticsSnapshotReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    reason_codes_json = payload_json.get("reason_codes")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    filters = _extract_filter_values(report.filters)
    return TeamDiagnosticsSnapshotDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        team_id=filters["team_id"],
        market_slug=filters["market_slug"],
        forecast_id=filters["forecast_id"],
        forecast_row_count=report.forecast_row_count,
        evidence_row_count=report.evidence_row_count,
        outcome_row_count=report.outcome_row_count,
        memory_eligible_reference_count=report.memory_eligible_reference_count,
        calibration_status=report.calibration_status,
        calibration_settled_count=report.calibration_settled_count,
        calibration_group_count=report.calibration_group_count,
        event_template_row_count=report.event_template_row_count,
        event_template_status=report.event_template_status,
        source_reliability_row_count=report.source_reliability_row_count,
        source_reliability_missing_source_evidence_count=(
            report.source_reliability_missing_source_evidence_count
        ),
        evidence_quality_status=report.evidence_quality_status,
        evidence_quality_pass_count=report.evidence_quality_pass_count,
        evidence_quality_watch_count=report.evidence_quality_watch_count,
        evidence_quality_blocked_count=report.evidence_quality_blocked_count,
        evidence_quality_average_quality_score=(
            report.evidence_quality_average_quality_score
        ),
        reason_codes_json=reason_codes_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def team_diagnostics_snapshot_report_from_db_row(
    row: TeamDiagnosticsSnapshotDbRow,
) -> "TeamDiagnosticsSnapshotReport":
    if type(row) is not TeamDiagnosticsSnapshotDbRow:
        raise ValueError("row must be a TeamDiagnosticsSnapshotDbRow")
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row, payload_json)

    report_type = _snapshot_report_class()
    try:
        report = from_jsonable(report_type, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid team diagnostics snapshot report: {exc}",
        ) from exc
    if type(report) is not report_type:
        raise ValueError("payload_json must recover a TeamDiagnosticsSnapshotReport")
    _validate_report_tree(report)
    expected_row = team_diagnostics_snapshot_report_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(report: "TeamDiagnosticsSnapshotReport") -> TeamDiagnosticsSnapshotDbRow:
    return team_diagnostics_snapshot_report_to_db_row(report)


def from_db_row(
    row: TeamDiagnosticsSnapshotDbRow,
) -> "TeamDiagnosticsSnapshotReport":
    return team_diagnostics_snapshot_report_from_db_row(row)


def _snapshot_report_class() -> type[Any]:
    module = importlib.import_module(_SNAPSHOT_MODULE_NAME)
    return module.TeamDiagnosticsSnapshotReport


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
    row: TeamDiagnosticsSnapshotDbRow,
) -> None:
    _validate_json_hard_flags(row.payload_json, "payload_json")
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_materialized_fields_match_payload(row, row.payload_json)


def _validate_materialized_fields_match_payload(
    row: TeamDiagnosticsSnapshotDbRow,
    payload_json: dict[str, Any],
) -> None:
    for field_name in _PAYLOAD_FIELD_NAMES:
        _require_payload_value(payload_json, field_name, getattr(row, field_name))
    filters = _filters_from_payload(payload_json)
    for filter_name in _FILTER_NAMES:
        if getattr(row, filter_name) != filters[filter_name]:
            raise ValueError(f"{filter_name} must match payload_json")
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


def _extract_filter_values(filters: object) -> dict[str, str | None]:
    values = {filter_name: None for filter_name in _FILTER_NAMES}
    if isinstance(filters, dict):
        items = tuple(filters.items())
    elif isinstance(filters, (str, bytes)):
        raise ValueError("filters must be filter pairs")
    else:
        try:
            items = tuple(filters)  # type: ignore[arg-type]
        except TypeError as exc:
            raise ValueError("filters must be filter pairs") from exc
    for item in items:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("filters must be filter pairs")
        name, value = item
        if name not in values:
            raise ValueError("filters must use known filter names")
        if values[name] is not None:
            raise ValueError("filters must not contain duplicate names")
        _require_canonical_string(str(name), value)
        values[name] = value
    return values


def _filters_from_payload(payload_json: dict[str, Any]) -> dict[str, str | None]:
    if "filters" not in payload_json:
        raise ValueError("filters must match payload_json")
    return _extract_filter_values(payload_json["filters"])


def _validate_row_matches_payload(
    row: TeamDiagnosticsSnapshotDbRow,
    expected: TeamDiagnosticsSnapshotDbRow,
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
    raise ValueError("team diagnostics snapshot DB row values must be JSON serializable")


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


def _require_optional_canonical_string(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_canonical_string(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_probability(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between zero and one")
    return value
