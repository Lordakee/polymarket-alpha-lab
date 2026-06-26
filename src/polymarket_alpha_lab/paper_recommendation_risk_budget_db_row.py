"""Pure row codec for persisted paper recommendation risk budget reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetReport,
)


__all__ = (
    "PaperRecommendationRiskBudgetDbRow",
    "paper_recommendation_risk_budget_from_db_row",
    "paper_recommendation_risk_budget_report_from_db_row",
    "paper_recommendation_risk_budget_report_to_db_row",
    "paper_recommendation_risk_budget_to_db_row",
    "from_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NOTIONAL_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
STATUSES = ("pass", "watch", "blocked")
REASON_CODES = {
    "risk_budget_passed",
    "empty_selection",
    "total_utilization_cap_exceeded",
    "single_recommendation_share_exceeded",
    "min_remaining_notional_breached",
    "max_selected_count_exceeded",
    "near_total_utilization_cap",
    "near_single_recommendation_share_cap",
    "near_min_remaining_notional",
    "near_max_selected_count",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_MISSING = object()


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    status: str
    reason_codes_json: list[str]
    total_suggested_notional: Decimal
    remaining_total_notional: Decimal | None
    total_notional_utilization: Decimal | None
    largest_single_recommendation_share: Decimal | None
    selected_count: int
    blocked_count: int
    nav_notional: Decimal | None
    max_total_utilization: Decimal
    max_single_recommendation_share: Decimal
    min_remaining_notional: Decimal
    max_selected_count: int
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
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        _require_notional("total_suggested_notional", self.total_suggested_notional)
        _require_optional_notional(
            "remaining_total_notional",
            self.remaining_total_notional,
        )
        _require_optional_ratio(
            "total_notional_utilization",
            self.total_notional_utilization,
        )
        _require_optional_ratio(
            "largest_single_recommendation_share",
            self.largest_single_recommendation_share,
        )
        _require_nonnegative_int("selected_count", self.selected_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_optional_notional("nav_notional", self.nav_notional)
        _require_ratio("max_total_utilization", self.max_total_utilization)
        if self.max_total_utilization <= ZERO:
            raise ValueError("max_total_utilization must be positive")
        _require_ratio(
            "max_single_recommendation_share",
            self.max_single_recommendation_share,
        )
        if self.max_single_recommendation_share <= ZERO:
            raise ValueError("max_single_recommendation_share must be positive")
        _require_notional("min_remaining_notional", self.min_remaining_notional)
        _require_positive_int("max_selected_count", self.max_selected_count)
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_materialized_fields_match_payload(self)
        _validate_json_hard_flags(self.payload_json, "payload_json")


def paper_recommendation_risk_budget_to_db_row(
    report: PaperRecommendationRiskBudgetReport,
) -> PaperRecommendationRiskBudgetDbRow:
    if type(report) is not PaperRecommendationRiskBudgetReport:
        raise ValueError("report must be a PaperRecommendationRiskBudgetReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperRecommendationRiskBudgetDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        reason_codes_json=list(report.reason_codes),
        total_suggested_notional=report.total_suggested_notional,
        remaining_total_notional=report.remaining_total_notional,
        total_notional_utilization=report.total_notional_utilization,
        largest_single_recommendation_share=report.largest_single_recommendation_share,
        selected_count=report.selected_count,
        blocked_count=report.blocked_count,
        nav_notional=report.nav_notional,
        max_total_utilization=report.max_total_utilization,
        max_single_recommendation_share=report.max_single_recommendation_share,
        min_remaining_notional=report.min_remaining_notional,
        max_selected_count=report.max_selected_count,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_recommendation_risk_budget_from_db_row(
    row: PaperRecommendationRiskBudgetDbRow,
) -> PaperRecommendationRiskBudgetReport:
    if type(row) is not PaperRecommendationRiskBudgetDbRow:
        raise ValueError("row must be a PaperRecommendationRiskBudgetDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperRecommendationRiskBudgetReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid risk budget report: {exc}",
        ) from exc
    if type(report) is not PaperRecommendationRiskBudgetReport:
        raise ValueError("payload_json must recover a PaperRecommendationRiskBudgetReport")
    _validate_report_tree(report)
    expected_row = paper_recommendation_risk_budget_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(report: PaperRecommendationRiskBudgetReport) -> PaperRecommendationRiskBudgetDbRow:
    return paper_recommendation_risk_budget_to_db_row(report)


def from_db_row(row: PaperRecommendationRiskBudgetDbRow) -> PaperRecommendationRiskBudgetReport:
    return paper_recommendation_risk_budget_from_db_row(row)


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
    row: PaperRecommendationRiskBudgetDbRow,
    expected: PaperRecommendationRiskBudgetDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "status",
        "reason_codes_json",
        "total_suggested_notional",
        "remaining_total_notional",
        "total_notional_utilization",
        "largest_single_recommendation_share",
        "selected_count",
        "blocked_count",
        "nav_notional",
        "max_total_utilization",
        "max_single_recommendation_share",
        "min_remaining_notional",
        "max_selected_count",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperRecommendationRiskBudgetDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "status": payload_json.get("status", _MISSING),
        "reason_codes_json": payload_json.get("reason_codes", _MISSING),
        "total_suggested_notional": payload_json.get(
            "total_suggested_notional",
            _MISSING,
        ),
        "remaining_total_notional": payload_json.get(
            "remaining_total_notional",
            _MISSING,
        ),
        "total_notional_utilization": payload_json.get(
            "total_notional_utilization",
            _MISSING,
        ),
        "largest_single_recommendation_share": payload_json.get(
            "largest_single_recommendation_share",
            _MISSING,
        ),
        "selected_count": payload_json.get("selected_count", _MISSING),
        "blocked_count": payload_json.get("blocked_count", _MISSING),
        "nav_notional": payload_json.get("nav_notional", _MISSING),
        "max_total_utilization": payload_json.get(
            "max_total_utilization",
            _MISSING,
        ),
        "max_single_recommendation_share": payload_json.get(
            "max_single_recommendation_share",
            _MISSING,
        ),
        "min_remaining_notional": payload_json.get("min_remaining_notional", _MISSING),
        "max_selected_count": payload_json.get("max_selected_count", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "status": row.status,
        "reason_codes_json": row.reason_codes_json,
        "total_suggested_notional": _json_ready(row.total_suggested_notional),
        "remaining_total_notional": _json_ready(row.remaining_total_notional),
        "total_notional_utilization": _json_ready(row.total_notional_utilization),
        "largest_single_recommendation_share": _json_ready(
            row.largest_single_recommendation_share,
        ),
        "selected_count": row.selected_count,
        "blocked_count": row.blocked_count,
        "nav_notional": _json_ready(row.nav_notional),
        "max_total_utilization": _json_ready(row.max_total_utilization),
        "max_single_recommendation_share": _json_ready(
            row.max_single_recommendation_share,
        ),
        "min_remaining_notional": _json_ready(row.min_remaining_notional),
        "max_selected_count": row.max_selected_count,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if actual_value != expected_values[field_name]:
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
    raise ValueError("risk budget DB row values must be JSON serializable")


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
        raise ValueError(f"{field_name} must match risk budget semantics")
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


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_notional(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_notional(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_optional_notional(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_notional(field_name, value)


def _require_ratio(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    if value != _quantize_ratio(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_optional_ratio(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_ratio(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _quantize_notional(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("notional", value)
    return value.quantize(NOTIONAL_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


paper_recommendation_risk_budget_report_to_db_row = (
    paper_recommendation_risk_budget_to_db_row
)
paper_recommendation_risk_budget_report_from_db_row = (
    paper_recommendation_risk_budget_from_db_row
)
