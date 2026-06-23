"""Pure row codec for persisted paper recommendation quality history reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_quality_history import (
    PaperRecommendationQualityHistoryReport,
    PaperRecommendationQualityHistoryRecurringSubreportRow,
    PaperRecommendationQualityHistoryStatusRow,
)


__all__ = (
    "PaperRecommendationQualityHistoryDbRow",
    "paper_recommendation_quality_history_from_db_row",
    "paper_recommendation_quality_history_report_from_db_row",
    "paper_recommendation_quality_history_report_to_db_row",
    "paper_recommendation_quality_history_to_db_row",
    "from_db_row",
    "to_db_row",
)


HISTORY_STATUSES = ("pass", "watch", "blocked")
SUMMARY_STATUSES = ("pass", "watch", "blocked", "incomplete")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperRecommendationQualityHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    history_status: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
    summary_status_rows_json: list[dict[str, Any]]
    pass_summary_count: int
    watch_summary_count: int
    blocked_summary_count: int
    incomplete_summary_count: int
    duplicate_generated_at_count: int
    recurring_blocked_reason_codes_json: list[str]
    recurring_incomplete_subreports_json: list[dict[str, Any]]
    recurring_incomplete_subreport_count: int
    reason_codes_json: list[str]
    reason_code_count: int
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
        _require_history_status("history_status", self.history_status)
        for field_name in (
            "source_report_count",
            "pass_summary_count",
            "watch_summary_count",
            "blocked_summary_count",
            "incomplete_summary_count",
            "duplicate_generated_at_count",
            "recurring_incomplete_subreport_count",
            "reason_code_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_source_generated_at",
            _as_optional_utc(
                "first_source_generated_at",
                self.first_source_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc(
                "latest_source_generated_at",
                self.latest_source_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "summary_status_rows_json",
            _normalize_summary_status_rows_json(
                "summary_status_rows_json",
                self.summary_status_rows_json,
            ),
        )
        object.__setattr__(
            self,
            "recurring_blocked_reason_codes_json",
            _normalize_string_list(
                "recurring_blocked_reason_codes_json",
                self.recurring_blocked_reason_codes_json,
                require_nonempty=False,
            ),
        )
        object.__setattr__(
            self,
            "recurring_incomplete_subreports_json",
            _normalize_recurring_incomplete_subreports_json(
                "recurring_incomplete_subreports_json",
                self.recurring_incomplete_subreports_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list(
                "reason_codes_json",
                self.reason_codes_json,
                require_nonempty=True,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)


def paper_recommendation_quality_history_to_db_row(
    report: PaperRecommendationQualityHistoryReport,
) -> PaperRecommendationQualityHistoryDbRow:
    if type(report) is not PaperRecommendationQualityHistoryReport:
        raise ValueError("report must be a PaperRecommendationQualityHistoryReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    status_counts = {
        row.summary_status: row.status_count
        for row in report.summary_status_rows
    }
    reason_codes_json = list(payload_json["reason_codes"])
    recurring_incomplete_subreports_json = list(
        payload_json["recurring_incomplete_subreports"],
    )
    return PaperRecommendationQualityHistoryDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        history_status=report.history_status,
        source_report_count=report.source_report_count,
        first_source_generated_at=report.first_source_generated_at,
        latest_source_generated_at=report.latest_source_generated_at,
        summary_status_rows_json=list(payload_json["summary_status_rows"]),
        pass_summary_count=status_counts["pass"],
        watch_summary_count=status_counts["watch"],
        blocked_summary_count=status_counts["blocked"],
        incomplete_summary_count=status_counts["incomplete"],
        duplicate_generated_at_count=report.duplicate_generated_at_count,
        recurring_blocked_reason_codes_json=list(
            payload_json["recurring_blocked_reason_codes"],
        ),
        recurring_incomplete_subreports_json=recurring_incomplete_subreports_json,
        recurring_incomplete_subreport_count=len(recurring_incomplete_subreports_json),
        reason_codes_json=reason_codes_json,
        reason_code_count=len(reason_codes_json),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_recommendation_quality_history_from_db_row(
    row: PaperRecommendationQualityHistoryDbRow,
) -> PaperRecommendationQualityHistoryReport:
    if type(row) is not PaperRecommendationQualityHistoryDbRow:
        raise ValueError("row must be a PaperRecommendationQualityHistoryDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperRecommendationQualityHistoryReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid quality history report: {exc}",
        ) from exc
    if type(report) is not PaperRecommendationQualityHistoryReport:
        raise ValueError("payload_json must recover a PaperRecommendationQualityHistoryReport")
    _validate_report_tree(report)
    expected_row = paper_recommendation_quality_history_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperRecommendationQualityHistoryReport,
) -> PaperRecommendationQualityHistoryDbRow:
    return paper_recommendation_quality_history_to_db_row(report)


def from_db_row(
    row: PaperRecommendationQualityHistoryDbRow,
) -> PaperRecommendationQualityHistoryReport:
    return paper_recommendation_quality_history_from_db_row(row)


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
    row: PaperRecommendationQualityHistoryDbRow,
    expected: PaperRecommendationQualityHistoryDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "history_status",
        "source_report_count",
        "first_source_generated_at",
        "latest_source_generated_at",
        "summary_status_rows_json",
        "pass_summary_count",
        "watch_summary_count",
        "blocked_summary_count",
        "incomplete_summary_count",
        "duplicate_generated_at_count",
        "recurring_blocked_reason_codes_json",
        "recurring_incomplete_subreports_json",
        "recurring_incomplete_subreport_count",
        "reason_codes_json",
        "reason_code_count",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
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
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("quality history DB row values must be JSON serializable")


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


def _normalize_json_object_list(field_name: str, value: object) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        normalized.append(_normalize_json_object(field_name, item))
    return normalized


def _normalize_summary_status_rows_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    rows = _normalize_json_object_list(field_name, value)
    for item in rows:
        try:
            from_jsonable(PaperRecommendationQualityHistoryStatusRow, item)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} contains invalid status rows: {exc}") from exc
    return rows


def _normalize_recurring_incomplete_subreports_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    rows = _normalize_json_object_list(field_name, value)
    for item in rows:
        try:
            from_jsonable(PaperRecommendationQualityHistoryRecurringSubreportRow, item)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} contains invalid recurring subreport rows: {exc}",
            ) from exc
    return rows


def _normalize_string_list(
    field_name: str,
    value: object,
    *,
    require_nonempty: bool,
) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        normalized.append(item)
    if require_nonempty and not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
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


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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


paper_recommendation_quality_history_report_to_db_row = (
    paper_recommendation_quality_history_to_db_row
)
paper_recommendation_quality_history_report_from_db_row = (
    paper_recommendation_quality_history_from_db_row
)
