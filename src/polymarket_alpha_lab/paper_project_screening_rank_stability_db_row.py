"""Pure row codec for paper project screening rank stability reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    PaperProjectScreeningRankStabilityReport,
    STABILITY_STATUSES,
)


__all__ = (
    "PaperProjectScreeningRankStabilityDbRow",
    "from_db_row",
    "paper_project_screening_rank_stability_from_db_row",
    "paper_project_screening_rank_stability_report_from_db_row",
    "paper_project_screening_rank_stability_report_to_db_row",
    "paper_project_screening_rank_stability_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    stability_status: str
    reason_codes_json: list[str]
    source_report_count: int
    candidate_count: int
    stable_count: int
    watch_count: int
    blocked_count: int
    stable_ready_count: int
    unstable_ready_count: int
    scoring_side_changed_count: int
    source_status_changed_count: int
    screening_status_changed_count: int
    research_bucket_changed_count: int
    latest_generated_at: datetime | None
    top_stable_market_slug: str | None
    rows_json: list[Any]
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
        _require_stability_status("stability_status", self.stability_status)
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json(
                "reason_codes_json",
                self.reason_codes_json,
            ),
        )
        for field_name in (
            "source_report_count",
            "candidate_count",
            "stable_count",
            "watch_count",
            "blocked_count",
            "stable_ready_count",
            "unstable_ready_count",
            "scoring_side_changed_count",
            "source_status_changed_count",
            "screening_status_changed_count",
            "research_bucket_changed_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        if self.top_stable_market_slug is not None:
            _require_canonical_string(
                "top_stable_market_slug",
                self.top_stable_market_slug,
            )
        object.__setattr__(
            self,
            "rows_json",
            _normalize_json_array("rows_json", self.rows_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_constructor_payload_consistency(self)


def paper_project_screening_rank_stability_to_db_row(
    report: PaperProjectScreeningRankStabilityReport,
) -> PaperProjectScreeningRankStabilityDbRow:
    if type(report) is not PaperProjectScreeningRankStabilityReport:
        raise ValueError("report must be a PaperProjectScreeningRankStabilityReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    rows_json = payload_json.get("rows")
    if not isinstance(rows_json, list):
        raise ValueError("payload_json rows must be a JSON array")
    return PaperProjectScreeningRankStabilityDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        stability_status=report.stability_status,
        reason_codes_json=list(report.reason_codes),
        source_report_count=report.source_report_count,
        candidate_count=report.candidate_count,
        stable_count=report.stable_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        stable_ready_count=report.stable_ready_count,
        unstable_ready_count=report.unstable_ready_count,
        scoring_side_changed_count=report.scoring_side_changed_count,
        source_status_changed_count=report.source_status_changed_count,
        screening_status_changed_count=report.screening_status_changed_count,
        research_bucket_changed_count=report.research_bucket_changed_count,
        latest_generated_at=report.latest_generated_at,
        top_stable_market_slug=report.top_stable_market_slug,
        rows_json=rows_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_project_screening_rank_stability_from_db_row(
    row: PaperProjectScreeningRankStabilityDbRow,
) -> PaperProjectScreeningRankStabilityReport:
    if type(row) is not PaperProjectScreeningRankStabilityDbRow:
        raise ValueError("row must be a PaperProjectScreeningRankStabilityDbRow")
    _reject_json_floats(row.rows_json)
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    if row.rows_json != row.payload_json.get("rows"):
        raise ValueError("rows_json must match payload_json")
    _validate_row_scalars_match_payload(row)
    try:
        report = from_jsonable(
            PaperProjectScreeningRankStabilityReport,
            row.payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid project screening rank stability report: {exc}",
        ) from exc
    if type(report) is not PaperProjectScreeningRankStabilityReport:
        raise ValueError(
            "payload_json must recover a PaperProjectScreeningRankStabilityReport",
        )
    _validate_report_tree(report)
    expected_row = paper_project_screening_rank_stability_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperProjectScreeningRankStabilityReport,
) -> PaperProjectScreeningRankStabilityDbRow:
    return paper_project_screening_rank_stability_to_db_row(report)


def from_db_row(
    row: PaperProjectScreeningRankStabilityDbRow,
) -> PaperProjectScreeningRankStabilityReport:
    return paper_project_screening_rank_stability_from_db_row(row)


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
    row: PaperProjectScreeningRankStabilityDbRow,
    expected: PaperProjectScreeningRankStabilityDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "stability_status",
        "reason_codes_json",
        "source_report_count",
        "candidate_count",
        "stable_count",
        "watch_count",
        "blocked_count",
        "stable_ready_count",
        "unstable_ready_count",
        "scoring_side_changed_count",
        "source_status_changed_count",
        "screening_status_changed_count",
        "research_bucket_changed_count",
        "latest_generated_at",
        "top_stable_market_slug",
        "rows_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_constructor_payload_consistency(
    row: PaperProjectScreeningRankStabilityDbRow,
) -> None:
    _validate_json_hard_flags(row.payload_json, "payload_json")
    for flag_name in ("paper_only", "report_only", "readonly"):
        _require_payload_value(row.payload_json, flag_name, getattr(row, flag_name))
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _require_payload_value(row.payload_json, "rows", row.rows_json, row_field_name="rows_json")
    _validate_row_scalars_match_payload(row)


def _validate_row_scalars_match_payload(
    row: PaperProjectScreeningRankStabilityDbRow,
) -> None:
    for field_name in (
        "generated_at",
        "config_version",
        "stability_status",
        "source_report_count",
        "candidate_count",
        "stable_count",
        "watch_count",
        "blocked_count",
        "stable_ready_count",
        "unstable_ready_count",
        "scoring_side_changed_count",
        "source_status_changed_count",
        "screening_status_changed_count",
        "research_bucket_changed_count",
        "latest_generated_at",
        "top_stable_market_slug",
    ):
        _require_payload_value(row.payload_json, field_name, getattr(row, field_name))
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
    raise ValueError("project screening rank stability row values must be JSON serializable")


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


def _normalize_json_array(field_name: str, value: object) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return normalized


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in reason_codes:
        reason_code = _require_reason_code(field_name, item)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
        normalized.append(reason_code)
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


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
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


def _require_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


paper_project_screening_rank_stability_report_to_db_row = (
    paper_project_screening_rank_stability_to_db_row
)
paper_project_screening_rank_stability_report_from_db_row = (
    paper_project_screening_rank_stability_from_db_row
)
