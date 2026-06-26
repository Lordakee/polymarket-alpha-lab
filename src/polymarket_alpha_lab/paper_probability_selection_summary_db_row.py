"""Pure row codec for persisted paper probability selection summary reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_probability_selection_summary import (
    PaperProbabilitySelectionSummaryReport,
    PaperProbabilitySelectionSummaryRow,
)


__all__ = (
    "PaperProbabilitySelectionSummaryDbRow",
    "paper_probability_selection_summary_from_db_row",
    "paper_probability_selection_summary_report_from_db_row",
    "paper_probability_selection_summary_report_to_db_row",
    "paper_probability_selection_summary_to_db_row",
    "from_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_cost_stress_config_version: str
    queue_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    missing_stress_count: int
    rows_json: list[dict[str, Any]]
    reason_codes_json: list[str]
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
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "source_queue_config_version",
            self.source_queue_config_version,
        )
        _require_canonical_string(
            "source_cost_stress_config_version",
            self.source_cost_stress_config_version,
        )
        for field_name in (
            "queue_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "missing_stress_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "rows_json",
            _normalize_rows_json("rows_json", self.rows_json),
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
        _validate_constructor_payload_consistency(self)


def paper_probability_selection_summary_to_db_row(
    report: PaperProbabilitySelectionSummaryReport,
) -> PaperProbabilitySelectionSummaryDbRow:
    if type(report) is not PaperProbabilitySelectionSummaryReport:
        raise ValueError("report must be a PaperProbabilitySelectionSummaryReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperProbabilitySelectionSummaryDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_queue_config_version=report.source_queue_config_version,
        source_cost_stress_config_version=report.source_cost_stress_config_version,
        queue_count=report.queue_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        missing_stress_count=report.missing_stress_count,
        rows_json=list(payload_json["rows"]),
        reason_codes_json=list(payload_json["reason_codes"]),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_probability_selection_summary_from_db_row(
    row: PaperProbabilitySelectionSummaryDbRow,
) -> PaperProbabilitySelectionSummaryReport:
    if type(row) is not PaperProbabilitySelectionSummaryDbRow:
        raise ValueError("row must be a PaperProbabilitySelectionSummaryDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperProbabilitySelectionSummaryReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid selection summary report: {exc}",
        ) from exc
    if type(report) is not PaperProbabilitySelectionSummaryReport:
        raise ValueError(
            "payload_json must recover a PaperProbabilitySelectionSummaryReport",
        )
    _validate_report_tree(report)
    expected_row = paper_probability_selection_summary_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperProbabilitySelectionSummaryReport,
) -> PaperProbabilitySelectionSummaryDbRow:
    return paper_probability_selection_summary_to_db_row(report)


def from_db_row(
    row: PaperProbabilitySelectionSummaryDbRow,
) -> PaperProbabilitySelectionSummaryReport:
    return paper_probability_selection_summary_from_db_row(row)


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
    row: PaperProbabilitySelectionSummaryDbRow,
    expected: PaperProbabilitySelectionSummaryDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "source_queue_config_version",
        "source_cost_stress_config_version",
        "queue_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "missing_stress_count",
        "rows_json",
        "reason_codes_json",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_constructor_payload_consistency(
    row: PaperProbabilitySelectionSummaryDbRow,
) -> None:
    _validate_json_hard_flags(row.payload_json, "payload_json")
    for flag_name in ("paper_only", "report_only", "readonly"):
        _require_payload_value(row.payload_json, flag_name, getattr(row, flag_name))
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    for field_name in (
        "generated_at",
        "config_version",
        "source_queue_config_version",
        "source_cost_stress_config_version",
        "queue_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "missing_stress_count",
    ):
        _require_payload_value(row.payload_json, field_name, getattr(row, field_name))
    _require_payload_value(row.payload_json, "rows", row.rows_json, row_field_name="rows_json")
    _require_payload_value(
        row.payload_json,
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
    raise ValueError("selection summary DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_rows_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        _validate_json_hard_flags(item, field_name)
        try:
            selection_row = from_jsonable(PaperProbabilitySelectionSummaryRow, item)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} {exc}") from exc
        if type(selection_row) is not PaperProbabilitySelectionSummaryRow:
            raise ValueError(f"{field_name} must contain selection summary rows")
        normalized_item = _json_ready(asdict(selection_row))
        if not isinstance(normalized_item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        normalized.append(normalized_item)
    return normalized


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
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
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
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


paper_probability_selection_summary_report_to_db_row = (
    paper_probability_selection_summary_to_db_row
)
paper_probability_selection_summary_report_from_db_row = (
    paper_probability_selection_summary_from_db_row
)
