"""DB row codec for paper execution reconciliation reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
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
_DECIMAL_LIKE_PATTERN = re.compile(
    r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$",
)
_RECONCILIATION_STATUSES = ("reconciled", "has_pending", "has_discrepancies")
_MISSING = object()
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_DECIMAL_QUANTUM = Decimal("0.000001")
_MATERIALIZED_DECIMAL_PAYLOAD_PATHS = frozenset(
    {
        ("total_fill_notional",),
        ("total_cost_basis",),
        ("total_outcome_value",),
        ("total_pnl",),
        ("realized_pnl",),
        ("unrealized_pnl",),
    },
)
_DECIMAL_PAYLOAD_PATTERNS = frozenset(
    {
        ("total_fill_notional",),
        ("total_cost_basis",),
        ("total_outcome_value",),
        ("total_pnl",),
        ("realized_pnl",),
        ("unrealized_pnl",),
        ("position_rows", "*", "fill_notional"),
        ("position_rows", "*", "cost_basis"),
        ("position_rows", "*", "outcome_value"),
        ("position_rows", "*", "pnl"),
    },
)
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
        _validate_payload_hash(self)
        _validate_payload_decimal_strings(self.payload_json, "payload_json")
        _validate_materialized_fields_match_payload(self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_payload_recovers_to_compatible_report(self.payload_json)


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
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_payload_integer_fields(payload_json, "payload_json")
    _validate_payload_hash(row, payload_json)
    _validate_payload_decimal_strings(payload_json, "payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row, payload_json)
    report = _validate_payload_recovers_to_compatible_report(payload_json)
    expected_row = to_db_row(report)
    _validate_row_matches_payload(row, expected_row, payload_json)
    return report


def _validate_payload_recovers_to_compatible_report(
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
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        _canonical_report_payload(report),
    )
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
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    for field_name in (
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
    _validate_json_compatible(
        ("position_rows",),
        row.position_rows_json,
        expected.position_rows_json,
    )


def _validate_materialized_fields_match_payload(
    row: PaperExecutionReconciliationDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
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
        "position_rows_json": row.position_rows_json,
        "reason_codes_json": row.reason_codes_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if not _json_values_match(actual_value, expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")
    for field_path in _MATERIALIZED_DECIMAL_PAYLOAD_PATHS:
        field_name = field_path[0]
        _require_materialized_decimal_match(
            field_name,
            getattr(row, field_name),
            expected_values[field_name],
        )


def _canonical_report_payload(
    report: PaperExecutionReconciliationReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload_json must recover a JSON object")
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
    _validate_decimal_payload_strings((), value, field_name)


def _validate_decimal_payload_strings(
    path: tuple[str, ...],
    value: Any,
    field_name: str,
) -> None:
    if _is_decimal_payload_path(path):
        if value is not None:
            _decimal_from_json_string(field_name, value)
        return
    if isinstance(value, str) and _looks_like_decimal_string(value):
        raise ValueError(
            f"{field_name} contains non-allowlisted Decimal-like string",
        )
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_decimal_payload_strings(
                (*path, key),
                item,
                f"{field_name} {key}",
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_decimal_payload_strings(
                (*path, str(index)),
                item,
                f"{field_name} {index}",
            )


def _decimal_from_json_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal string")
    if _decimal_fractional_places(decimal) > 6:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return decimal


def _validate_payload_hash(
    row: PaperExecutionReconciliationDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")


def _validate_payload_compatible_with_canonical_payload(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    try:
        _validate_json_compatible((), payload_json, expected_payload_json)
    except ValueError as exc:
        raise ValueError(
            "payload_json must match canonical execution reconciliation report: "
            f"{exc}",
        ) from exc


def _validate_json_compatible(
    path: tuple[str, ...],
    actual: object,
    expected: object,
) -> None:
    if _is_decimal_payload_path(path):
        _validate_compatible_decimal_path(".".join(path), actual, expected)
        return
    if isinstance(actual, str) and _looks_like_decimal_string(actual):
        raise ValueError(
            f"{'.'.join(path) or 'payload_json'} contains "
            "non-allowlisted Decimal-like string",
        )
    if type(actual) is not type(expected):
        raise ValueError(f"{'.'.join(path) or 'payload_json'} has wrong JSON type")
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():  # type: ignore[union-attr]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} keys differ")
        for key in actual:
            _validate_json_compatible(
                (*path, key),
                actual[key],
                expected[key],  # type: ignore[index]
            )
        return
    if isinstance(actual, list):
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} length differs")
        for index, item in enumerate(actual):
            _validate_json_compatible(
                (*path, str(index)),
                item,
                expected[index],  # type: ignore[index]
            )
        return
    if actual != expected:
        raise ValueError(f"{'.'.join(path) or 'payload_json'} differs")


def _validate_compatible_decimal_path(
    field_name: str,
    actual: object,
    expected: object,
) -> None:
    if actual is None or expected is None:
        if actual is not expected:
            raise ValueError(f"{field_name} differs")
        return
    actual_decimal = _decimal_from_json_string(field_name, actual)
    expected_decimal = _decimal_from_json_string(field_name, expected)
    if actual_decimal != expected_decimal:
        raise ValueError(f"{field_name} differs")


def _is_decimal_payload_path(path: tuple[str, ...]) -> bool:
    for pattern in _DECIMAL_PAYLOAD_PATTERNS:
        if len(path) != len(pattern):
            continue
        if all(
            pattern_part == "*" or pattern_part == path_part
            for pattern_part, path_part in zip(pattern, path, strict=True)
        ):
            return True
    return False


def _looks_like_decimal_string(value: str) -> bool:
    return _DECIMAL_LIKE_PATTERN.fullmatch(value) is not None


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
        return _decimal_to_json(value)
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


def _decimal_to_json(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("JSON Decimal value must be finite")
    if _decimal_fractional_places(value) > 6:
        raise ValueError("JSON Decimal value must have at most six decimal places")
    with localcontext() as context:
        context.prec = max(
            28,
            len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 6,
        )
        quantized = value.quantize(_DECIMAL_QUANTUM)
    if value != quantized:
        raise ValueError("JSON Decimal value must have at most six decimal places")
    if quantized.is_zero():
        quantized = Decimal("0.000000")
    return format(quantized, "f")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_json_array(field_name: str, value: object) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        normalized = [_copy_json_payload(item) for item in value]
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    return normalized


def _copy_json_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain datetime")
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


def _validate_row_core_fields(row: PaperExecutionReconciliationDbRow) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    if row.reconciliation_status not in _RECONCILIATION_STATUSES:
        raise ValueError("reconciliation_status must be a known reconciliation status")
    for field_name in (
        "total_positions",
        "filled_pending_count",
        "settled_win_count",
        "settled_loss_count",
        "expired_count",
        "cancelled_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    for field_name in (
        "total_fill_notional",
        "total_cost_basis",
    ):
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    if row.total_outcome_value is not None:
        _require_nonnegative_decimal("total_outcome_value", row.total_outcome_value)
    if row.total_pnl is not None:
        _require_decimal("total_pnl", row.total_pnl)
    _require_decimal("realized_pnl", row.realized_pnl)
    _require_decimal("unrealized_pnl", row.unrealized_pnl)
    _normalize_json_array("position_rows_json", row.position_rows_json)
    _normalize_reason_codes_json("reason_codes_json", row.reason_codes_json)
    _require_hard_flags("DB row", row)


def _require_materialized_decimal_match(
    field_name: str,
    row_value: Decimal | None,
    payload_value: object,
) -> None:
    if row_value is None:
        if payload_value is not None:
            raise ValueError(f"{field_name} must match payload_json")
        return
    _require_decimal(field_name, row_value)
    if _decimal_fractional_places(row_value) > 6:
        raise ValueError(f"{field_name} must have at most six decimal places")
    if payload_value is None:
        raise ValueError(f"{field_name} must match payload_json")
    payload_decimal = _decimal_from_json_string(field_name, payload_value)
    if payload_decimal != row_value:
        raise ValueError(f"{field_name} must match payload_json")


def _decimal_fractional_places(value: Decimal) -> int:
    return max(-value.as_tuple().exponent, 0)
