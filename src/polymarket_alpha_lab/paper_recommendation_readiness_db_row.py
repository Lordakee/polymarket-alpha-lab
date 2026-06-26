"""Pure row codec for persisted paper recommendation readiness reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_readiness import (
    PaperRecommendationReadinessReport,
)


__all__ = (
    "PaperRecommendationReadinessDbRow",
    "paper_recommendation_readiness_from_db_row",
    "paper_recommendation_readiness_report_from_db_row",
    "paper_recommendation_readiness_report_to_db_row",
    "paper_recommendation_readiness_to_db_row",
    "from_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
READINESS_STATUSES = ("ready", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperRecommendationReadinessDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    top_adjusted_net_probability_edge: Decimal
    total_cost_per_share: Decimal
    readiness_status_counts_json: dict[str, int]
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
        _require_nonnegative_int("input_count", self.input_count)
        _require_nonnegative_int("row_count", self.row_count)
        _require_nonnegative_int("ready_count", self.ready_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_decimal(
            "top_adjusted_net_probability_edge",
            self.top_adjusted_net_probability_edge,
        )
        _require_nonnegative_decimal("total_cost_per_share", self.total_cost_per_share)
        object.__setattr__(
            self,
            "readiness_status_counts_json",
            _normalize_readiness_status_counts_json(
                "readiness_status_counts_json",
                self.readiness_status_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _require_hard_flags("DB row", self)
        _validate_row_scalars_match_payload(self)
        _validate_readiness_status_counts_match_payload(self)
        if self.report_sha256 != _report_sha256(self.payload_json):
            raise ValueError("report_sha256 must match payload_json")


def paper_recommendation_readiness_to_db_row(
    report: PaperRecommendationReadinessReport,
) -> PaperRecommendationReadinessDbRow:
    if type(report) is not PaperRecommendationReadinessReport:
        raise ValueError("report must be a PaperRecommendationReadinessReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperRecommendationReadinessDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        input_count=report.input_count,
        row_count=report.row_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        top_adjusted_net_probability_edge=report.top_adjusted_net_probability_edge,
        total_cost_per_share=report.total_cost_per_share,
        readiness_status_counts_json=_readiness_status_counts(report),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_recommendation_readiness_from_db_row(
    row: PaperRecommendationReadinessDbRow,
) -> PaperRecommendationReadinessReport:
    if type(row) is not PaperRecommendationReadinessDbRow:
        raise ValueError("row must be a PaperRecommendationReadinessDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperRecommendationReadinessReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid readiness report: {exc}",
        ) from exc
    if type(report) is not PaperRecommendationReadinessReport:
        raise ValueError("payload_json must recover a PaperRecommendationReadinessReport")
    _validate_report_tree(report)
    expected_row = paper_recommendation_readiness_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperRecommendationReadinessReport,
) -> PaperRecommendationReadinessDbRow:
    return paper_recommendation_readiness_to_db_row(report)


def from_db_row(
    row: PaperRecommendationReadinessDbRow,
) -> PaperRecommendationReadinessReport:
    return paper_recommendation_readiness_from_db_row(row)


def _readiness_status_counts(
    report: PaperRecommendationReadinessReport,
) -> dict[str, int]:
    return {
        "ready": report.ready_count,
        "watch": report.watch_count,
        "blocked": report.blocked_count,
    }


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
    row: PaperRecommendationReadinessDbRow,
    expected: PaperRecommendationReadinessDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "top_adjusted_net_probability_edge",
        "total_cost_per_share",
        "readiness_status_counts_json",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_scalars_match_payload(
    row: PaperRecommendationReadinessDbRow,
) -> None:
    for field_name in (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "top_adjusted_net_probability_edge",
        "total_cost_per_share",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if not _json_values_match(
            row.payload_json.get(field_name),
            _json_ready(getattr(row, field_name)),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_readiness_status_counts_match_payload(
    row: PaperRecommendationReadinessDbRow,
) -> None:
    expected_counts = {
        "ready": row.payload_json.get("ready_count"),
        "watch": row.payload_json.get("watch_count"),
        "blocked": row.payload_json.get("blocked_count"),
    }
    if not _json_values_match(row.readiness_status_counts_json, expected_counts):
        raise ValueError("readiness_status_counts_json must match payload_json")


def _json_values_match(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return False
        return all(_json_values_match(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return False
        return all(
            _json_values_match(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


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
    raise ValueError("readiness DB row values must be JSON serializable")


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


def _normalize_readiness_status_counts_json(
    field_name: str,
    value: object,
) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    if set(value) != set(READINESS_STATUSES):
        raise ValueError(
            f"{field_name} must contain ready, watch, and blocked counts",
        )
    normalized: dict[str, int] = {}
    for status in READINESS_STATUSES:
        count = value[status]
        _require_nonnegative_int(status, count)
        normalized[status] = count
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


def _require_finite_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value != _quantize(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _quantize(value: Decimal) -> Decimal:
    _require_finite_decimal("decimal", value)
    return value.quantize(QUANTUM)


paper_recommendation_readiness_report_to_db_row = (
    paper_recommendation_readiness_to_db_row
)
paper_recommendation_readiness_report_from_db_row = (
    paper_recommendation_readiness_from_db_row
)
