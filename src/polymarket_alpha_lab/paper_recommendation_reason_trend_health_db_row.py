"""Pure row codec for persisted paper recommendation reason trend health reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_reason_trend_health import (
    PaperRecommendationReasonTrendHealthReport,
)


__all__ = (
    "PaperRecommendationReasonTrendHealthDbRow",
    "paper_recommendation_reason_trend_health_from_db_row",
    "paper_recommendation_reason_trend_health_report_from_db_row",
    "paper_recommendation_reason_trend_health_report_to_db_row",
    "paper_recommendation_reason_trend_health_to_db_row",
    "from_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
HEALTH_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperRecommendationReasonTrendHealthDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    health_status: str
    source_report_count: int
    reason_code_count: int
    blocked_status_count: int
    blocked_status_share: Decimal | None
    reject_status_count: int
    reject_status_share: Decimal | None
    new_reason_code_count: int
    transition_count: int
    persistent_reason_codes_json: list[str]
    reason_codes_json: list[str]
    max_blocked_status_share: Decimal
    max_reject_status_share: Decimal
    max_new_reason_code_count: int
    max_transition_count: int
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("health_status", self.health_status)
        for field_name in (
            "source_report_count",
            "reason_code_count",
            "blocked_status_count",
            "reject_status_count",
            "new_reason_code_count",
            "transition_count",
            "max_new_reason_code_count",
            "max_transition_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_status_share",
            _normalize_optional_probability_decimal(
                "blocked_status_share",
                self.blocked_status_share,
            ),
        )
        object.__setattr__(
            self,
            "reject_status_share",
            _normalize_optional_probability_decimal(
                "reject_status_share",
                self.reject_status_share,
            ),
        )
        object.__setattr__(
            self,
            "persistent_reason_codes_json",
            _normalize_string_list(
                "persistent_reason_codes_json",
                self.persistent_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "max_blocked_status_share",
            _normalize_probability_decimal(
                "max_blocked_status_share",
                self.max_blocked_status_share,
            ),
        )
        object.__setattr__(
            self,
            "max_reject_status_share",
            _normalize_probability_decimal(
                "max_reject_status_share",
                self.max_reject_status_share,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def paper_recommendation_reason_trend_health_to_db_row(
    report: PaperRecommendationReasonTrendHealthReport,
) -> PaperRecommendationReasonTrendHealthDbRow:
    if type(report) is not PaperRecommendationReasonTrendHealthReport:
        raise ValueError("report must be a PaperRecommendationReasonTrendHealthReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperRecommendationReasonTrendHealthDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        health_status=report.health_status,
        source_report_count=report.source_report_count,
        reason_code_count=report.reason_code_count,
        blocked_status_count=report.blocked_status_count,
        blocked_status_share=report.blocked_status_share,
        reject_status_count=report.reject_status_count,
        reject_status_share=report.reject_status_share,
        new_reason_code_count=report.new_reason_code_count,
        transition_count=report.transition_count,
        persistent_reason_codes_json=list(payload_json["persistent_reason_codes"]),
        reason_codes_json=list(payload_json["reason_codes"]),
        max_blocked_status_share=report.max_blocked_status_share,
        max_reject_status_share=report.max_reject_status_share,
        max_new_reason_code_count=report.max_new_reason_code_count,
        max_transition_count=report.max_transition_count,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_recommendation_reason_trend_health_from_db_row(
    row: PaperRecommendationReasonTrendHealthDbRow,
) -> PaperRecommendationReasonTrendHealthReport:
    if type(row) is not PaperRecommendationReasonTrendHealthDbRow:
        raise ValueError("row must be a PaperRecommendationReasonTrendHealthDbRow")
    payload_json = _validate_row_payload_consistency(row)
    _reject_json_floats(payload_json)
    try:
        report = from_jsonable(
            PaperRecommendationReasonTrendHealthReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid reason trend health report: {exc}",
        ) from exc
    if type(report) is not PaperRecommendationReasonTrendHealthReport:
        raise ValueError(
            "payload_json must recover a PaperRecommendationReasonTrendHealthReport",
        )
    _validate_report_tree(report)
    expected_row = paper_recommendation_reason_trend_health_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperRecommendationReasonTrendHealthReport,
) -> PaperRecommendationReasonTrendHealthDbRow:
    return paper_recommendation_reason_trend_health_to_db_row(report)


def from_db_row(
    row: PaperRecommendationReasonTrendHealthDbRow,
) -> PaperRecommendationReasonTrendHealthReport:
    return paper_recommendation_reason_trend_health_from_db_row(row)


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
    row: PaperRecommendationReasonTrendHealthDbRow,
    expected: PaperRecommendationReasonTrendHealthDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "health_status",
        "source_report_count",
        "reason_code_count",
        "blocked_status_count",
        "blocked_status_share",
        "reject_status_count",
        "reject_status_share",
        "new_reason_code_count",
        "transition_count",
        "persistent_reason_codes_json",
        "reason_codes_json",
        "max_blocked_status_share",
        "max_reject_status_share",
        "max_new_reason_code_count",
        "max_transition_count",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if _row_field(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_payload_consistency(
    row: PaperRecommendationReasonTrendHealthDbRow,
) -> dict[str, Any]:
    payload_json = _normalize_json_object(
        "payload_json",
        _row_field(row, "payload_json"),
    )
    _validate_json_hard_flags(payload_json, "payload_json")
    for field_name, payload_key in (
        ("generated_at", "generated_at"),
        ("config_version", "config_version"),
        ("health_status", "health_status"),
        ("source_report_count", "source_report_count"),
        ("reason_code_count", "reason_code_count"),
        ("blocked_status_count", "blocked_status_count"),
        ("blocked_status_share", "blocked_status_share"),
        ("reject_status_count", "reject_status_count"),
        ("reject_status_share", "reject_status_share"),
        ("new_reason_code_count", "new_reason_code_count"),
        ("transition_count", "transition_count"),
        ("persistent_reason_codes_json", "persistent_reason_codes"),
        ("reason_codes_json", "reason_codes"),
        ("max_blocked_status_share", "max_blocked_status_share"),
        ("max_reject_status_share", "max_reject_status_share"),
        ("max_new_reason_code_count", "max_new_reason_code_count"),
        ("max_transition_count", "max_transition_count"),
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ):
        if payload_key not in payload_json:
            raise ValueError(f"{field_name} must match payload_json")
        if _json_ready(_row_field(row, field_name)) != payload_json[payload_key]:
            raise ValueError(f"{field_name} must match payload_json")
    if _row_field(row, "report_sha256") != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    return payload_json


def _row_field(row: PaperRecommendationReasonTrendHealthDbRow, field_name: str) -> Any:
    try:
        return getattr(row, field_name)
    except AttributeError as exc:
        raise ValueError(f"{field_name} is required") from exc


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
    raise ValueError("reason trend health DB row values must be JSON serializable")


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


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability_decimal(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


paper_recommendation_reason_trend_health_report_to_db_row = (
    paper_recommendation_reason_trend_health_to_db_row
)
paper_recommendation_reason_trend_health_report_from_db_row = (
    paper_recommendation_reason_trend_health_from_db_row
)
