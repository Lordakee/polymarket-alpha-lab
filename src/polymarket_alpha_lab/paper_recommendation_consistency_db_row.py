"""Pure row codec for persisted paper recommendation consistency reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_consistency import (
    PaperRecommendationConsistencyReport,
)


__all__ = (
    "PaperRecommendationConsistencyDbRow",
    "paper_recommendation_consistency_from_db_row",
    "paper_recommendation_consistency_report_from_db_row",
    "paper_recommendation_consistency_report_to_db_row",
    "paper_recommendation_consistency_to_db_row",
    "from_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
STATUSES = ("pass", "watch", "blocked")
REASON_CODES = {
    "recommendation_consistency_passed",
    "empty_recommendation_facts",
    "edge_spread_exceeds_consistency_cap",
    "score_spread_exceeds_consistency_cap",
    "missing_recommendation_sources",
    "recommendation_status_disagreement",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "consistency_status",
    "reason_codes_json",
    "group_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "max_edge_spread",
    "max_score_spread",
    "min_source_count",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperRecommendationConsistencyDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    consistency_status: str
    reason_codes_json: list[str]
    group_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    max_edge_spread: Decimal
    max_score_spread: Decimal
    min_source_count: int
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
        _require_status("consistency_status", self.consistency_status)
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        _require_nonnegative_int("group_count", self.group_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_quantized_nonnegative_decimal("max_edge_spread", self.max_edge_spread)
        _require_quantized_nonnegative_decimal(
            "max_score_spread",
            self.max_score_spread,
        )
        _require_positive_int("min_source_count", self.min_source_count)
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_matches_payload_json(self)
        _validate_json_hard_flags(self.payload_json, "payload_json")


def paper_recommendation_consistency_to_db_row(
    report: PaperRecommendationConsistencyReport,
) -> PaperRecommendationConsistencyDbRow:
    if type(report) is not PaperRecommendationConsistencyReport:
        raise ValueError("report must be a PaperRecommendationConsistencyReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperRecommendationConsistencyDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        consistency_status=report.consistency_status,
        reason_codes_json=list(report.reason_codes),
        group_count=report.group_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        max_edge_spread=report.max_edge_spread,
        max_score_spread=report.max_score_spread,
        min_source_count=report.min_source_count,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_recommendation_consistency_from_db_row(
    row: PaperRecommendationConsistencyDbRow,
) -> PaperRecommendationConsistencyReport:
    if type(row) is not PaperRecommendationConsistencyDbRow:
        raise ValueError("row must be a PaperRecommendationConsistencyDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperRecommendationConsistencyReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid consistency report: {exc}",
        ) from exc
    if type(report) is not PaperRecommendationConsistencyReport:
        raise ValueError("payload_json must recover a PaperRecommendationConsistencyReport")
    _validate_report_tree(report)
    expected_row = paper_recommendation_consistency_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperRecommendationConsistencyReport,
) -> PaperRecommendationConsistencyDbRow:
    return paper_recommendation_consistency_to_db_row(report)


def from_db_row(
    row: PaperRecommendationConsistencyDbRow,
) -> PaperRecommendationConsistencyReport:
    return paper_recommendation_consistency_from_db_row(row)


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
    row: PaperRecommendationConsistencyDbRow,
    expected: PaperRecommendationConsistencyDbRow,
) -> None:
    for field_name in (*_MATERIALIZED_FIELDS, "payload_json"):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_matches_payload_json(
    row: PaperRecommendationConsistencyDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at"),
        "config_version": payload_json.get("config_version"),
        "consistency_status": payload_json.get("consistency_status"),
        "reason_codes_json": payload_json.get("reason_codes"),
        "group_count": payload_json.get("group_count"),
        "pass_count": payload_json.get("pass_count"),
        "watch_count": payload_json.get("watch_count"),
        "blocked_count": payload_json.get("blocked_count"),
        "max_edge_spread": payload_json.get("max_edge_spread"),
        "max_score_spread": payload_json.get("max_score_spread"),
        "min_source_count": payload_json.get("min_source_count"),
        "paper_only": payload_json.get("paper_only"),
        "report_only": payload_json.get("report_only"),
        "readonly": payload_json.get("readonly"),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "consistency_status": row.consistency_status,
        "reason_codes_json": row.reason_codes_json,
        "group_count": row.group_count,
        "pass_count": row.pass_count,
        "watch_count": row.watch_count,
        "blocked_count": row.blocked_count,
        "max_edge_spread": _json_ready(row.max_edge_spread),
        "max_score_spread": _json_ready(row.max_score_spread),
        "min_source_count": row.min_source_count,
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
    raise ValueError("consistency DB row values must be JSON serializable")


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


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
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
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical tokens")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must match consistency semantics")
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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_quantized_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _quantize_decimal(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("decimal", value)
    return value.quantize(QUANTUM)


paper_recommendation_consistency_report_to_db_row = (
    paper_recommendation_consistency_to_db_row
)
paper_recommendation_consistency_report_from_db_row = (
    paper_recommendation_consistency_from_db_row
)
