"""DB row codec for paper execution reconciliation reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationReport,
)


__all__ = (
    "PaperExecutionReconciliationDbRow",
    "from_db_row",
    "paper_execution_reconciliation_report_from_db_row",
    "paper_execution_reconciliation_report_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_RECONCILIATION_STATUSES = ("reconciled", "has_pending", "has_discrepancies")
_MISSING = object()
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_DECIMAL_QUANTUM = Decimal("0.000001")
_JSON_INTEGER_FIELDS = frozenset(
    {
        "total_positions",
        "filled_pending_count",
        "settled_win_count",
        "settled_loss_count",
        "expired_count",
        "cancelled_count",
    },
)
_JSON_DECIMAL_FIELDS = frozenset(
    {
        "total_fill_notional",
        "total_cost_basis",
        "total_outcome_value",
        "total_pnl",
        "realized_pnl",
        "unrealized_pnl",
        "fill_notional",
        "cost_basis",
        "outcome_value",
        "pnl",
    },
)


@dataclass(frozen=True)
class PaperExecutionReconciliationDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    reconciliation_status: str
    total_positions: int
    filled_pending_count: int
    settled_win_count: int
    settled_loss_count: int
    expired_count: int
    cancelled_count: int
    total_fill_notional: Decimal
    total_cost_basis: Decimal
    total_outcome_value: Decimal | None
    total_pnl: Decimal | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    position_rows_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool
    report_only: bool
    readonly: bool

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.reconciliation_status not in _RECONCILIATION_STATUSES:
            raise ValueError("reconciliation_status must be a known reconciliation status")
        for field_name in (
            "total_positions",
            "filled_pending_count",
            "settled_win_count",
            "settled_loss_count",
            "expired_count",
            "cancelled_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_fill_notional",
            "total_cost_basis",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        if self.total_outcome_value is not None:
            _require_nonnegative_decimal("total_outcome_value", self.total_outcome_value)
        if self.total_pnl is not None:
            _require_decimal("total_pnl", self.total_pnl)
        _require_decimal("realized_pnl", self.realized_pnl)
        _require_decimal("unrealized_pnl", self.unrealized_pnl)
        object.__setattr__(
            self,
            "position_rows_json",
            _normalize_json_array("position_rows_json", self.position_rows_json),
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
        _validate_payload_integer_fields(self.payload_json, "payload_json")
        _validate_payload_decimal_strings(self.payload_json, "payload_json")
        _validate_materialized_fields_match_payload(self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_payload_recovers_to_canonical_report(self.payload_json)


def to_db_row(
    report: PaperExecutionReconciliationReport,
) -> PaperExecutionReconciliationDbRow:
    if type(report) is not PaperExecutionReconciliationReport:
        raise ValueError("report must be a PaperExecutionReconciliationReport")
    _require_hard_flags("report", report)
    payload_json = _json_ready(asdict(report))
    return PaperExecutionReconciliationDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        reconciliation_status=report.reconciliation_status,
        total_positions=report.total_positions,
        filled_pending_count=report.filled_pending_count,
        settled_win_count=report.settled_win_count,
        settled_loss_count=report.settled_loss_count,
        expired_count=report.expired_count,
        cancelled_count=report.cancelled_count,
        total_fill_notional=report.total_fill_notional,
        total_cost_basis=report.total_cost_basis,
        total_outcome_value=report.total_outcome_value,
        total_pnl=report.total_pnl,
        realized_pnl=report.realized_pnl,
        unrealized_pnl=report.unrealized_pnl,
        position_rows_json=payload_json["position_rows"],
        reason_codes_json=payload_json["reason_codes"],
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def from_db_row(
    row: PaperExecutionReconciliationDbRow,
) -> PaperExecutionReconciliationReport:
    if type(row) is not PaperExecutionReconciliationDbRow:
        raise ValueError("row must be a PaperExecutionReconciliationDbRow")
    _reject_json_floats(row.payload_json)
    _validate_payload_integer_fields(row.payload_json, "payload_json")
    try:
        _validate_payload_decimal_strings(row.payload_json, "payload_json")
    except ValueError as exc:
        raise ValueError("payload_json must be canonical") from exc
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row)
    report = _validate_payload_recovers_to_canonical_report(row.payload_json)
    expected_row = to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def _validate_payload_recovers_to_canonical_report(
    payload_json: dict[str, Any],
) -> PaperExecutionReconciliationReport:
    try:
        report = from_jsonable(PaperExecutionReconciliationReport, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid execution reconciliation report: {exc}",
        ) from exc
    if type(report) is not PaperExecutionReconciliationReport:
        raise ValueError(
            "payload_json must recover a PaperExecutionReconciliationReport",
        )
    if not _json_values_match(payload_json, _canonical_report_payload(report)):
        raise ValueError("payload_json must be canonical")
    return report


def paper_execution_reconciliation_report_to_db_row(
    report: PaperExecutionReconciliationReport,
) -> PaperExecutionReconciliationDbRow:
    return to_db_row(report)


def paper_execution_reconciliation_report_from_db_row(
    row: PaperExecutionReconciliationDbRow,
) -> PaperExecutionReconciliationReport:
    return from_db_row(row)


def _validate_row_matches_payload(
    row: PaperExecutionReconciliationDbRow,
    expected: PaperExecutionReconciliationDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "reconciliation_status",
        "total_positions",
        "filled_pending_count",
        "settled_win_count",
        "settled_loss_count",
        "expired_count",
        "cancelled_count",
        "total_fill_notional",
        "total_cost_basis",
        "total_outcome_value",
        "total_pnl",
        "realized_pnl",
        "unrealized_pnl",
        "position_rows_json",
        "reason_codes_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if not _json_values_match(
            getattr(row, field_name),
            getattr(expected, field_name),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperExecutionReconciliationDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "reconciliation_status": payload_json.get(
            "reconciliation_status",
            _MISSING,
        ),
        "total_positions": payload_json.get("total_positions", _MISSING),
        "filled_pending_count": payload_json.get(
            "filled_pending_count",
            _MISSING,
        ),
        "settled_win_count": payload_json.get("settled_win_count", _MISSING),
        "settled_loss_count": payload_json.get("settled_loss_count", _MISSING),
        "expired_count": payload_json.get("expired_count", _MISSING),
        "cancelled_count": payload_json.get("cancelled_count", _MISSING),
        "total_fill_notional": payload_json.get("total_fill_notional", _MISSING),
        "total_cost_basis": payload_json.get("total_cost_basis", _MISSING),
        "total_outcome_value": payload_json.get("total_outcome_value", _MISSING),
        "total_pnl": payload_json.get("total_pnl", _MISSING),
        "realized_pnl": payload_json.get("realized_pnl", _MISSING),
        "unrealized_pnl": payload_json.get("unrealized_pnl", _MISSING),
        "position_rows_json": payload_json.get("position_rows", _MISSING),
        "reason_codes_json": payload_json.get("reason_codes", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "reconciliation_status": row.reconciliation_status,
        "total_positions": row.total_positions,
        "filled_pending_count": row.filled_pending_count,
        "settled_win_count": row.settled_win_count,
        "settled_loss_count": row.settled_loss_count,
        "expired_count": row.expired_count,
        "cancelled_count": row.cancelled_count,
        "total_fill_notional": _json_ready(row.total_fill_notional),
        "total_cost_basis": _json_ready(row.total_cost_basis),
        "total_outcome_value": _json_ready(row.total_outcome_value),
        "total_pnl": _json_ready(row.total_pnl),
        "realized_pnl": _json_ready(row.realized_pnl),
        "unrealized_pnl": _json_ready(row.unrealized_pnl),
        "position_rows_json": row.position_rows_json,
        "reason_codes_json": row.reason_codes_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if not _json_values_match(actual_value, expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _canonical_report_payload(
    report: PaperExecutionReconciliationReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload_json must recover a JSON object")
    _validate_canonical_decimal_strings(payload, "payload_json")
    return payload


def _json_values_match(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if set(left) != set(right):
            return False
        return all(_json_values_match(left[key], right[key]) for key in left)
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(
            _json_values_match(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _validate_canonical_decimal_strings(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_DECIMAL_FIELDS and item is not None:
                _require_canonical_decimal_json_string(child_name, item)
            _validate_canonical_decimal_strings(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_canonical_decimal_strings(item, f"{field_name} {index}")


def _validate_payload_integer_fields(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_INTEGER_FIELDS:
                _require_nonnegative_int(child_name, item)
            _validate_payload_integer_fields(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_integer_fields(item, f"{field_name} {index}")


def _validate_payload_decimal_strings(value: Any, field_name: str) -> None:
    _validate_canonical_decimal_strings(value, field_name)


def _require_canonical_decimal_json_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    try:
        decimal = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a canonical decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be a finite decimal string")
    canonical = decimal.quantize(_DECIMAL_QUANTUM)
    if decimal != canonical or value != str(canonical):
        raise ValueError(f"{field_name} must be canonical")


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
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("execution reconciliation DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _normalize_json_array(field_name: str, value: object) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return [_json_ready(item) for item in value]


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    normalized = _normalize_json_array(field_name, value)
    previous: str | None = None
    for item in normalized:
        _require_canonical_string(f"{field_name} entry", item)
        if previous is not None and previous >= item:
            raise ValueError(f"{field_name} must be sorted and unique")
        previous = item
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if _looks_like_report_payload(value):
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


def _looks_like_report_payload(value: dict[str, Any]) -> bool:
    return (
        any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly"))
        or (
            "generated_at" in value
            and "config_version" in value
            and "reason_codes" in value
        )
    )


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


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


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
