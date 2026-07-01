"""Pure row codec for persisted paper trade attribution reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_trade_attribution import PaperTradeAttributionReport


__all__ = (
    "PaperTradeAttributionReportDbRow",
    "paper_trade_attribution_report_from_db_row",
    "paper_trade_attribution_report_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ZERO = Decimal("0")
_MISSING = object()
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_JSON_INTEGER_FIELDS = frozenset(
    {
        "trade_count",
        "row_count",
        "market_count",
        "filled_count",
        "complete_fill_count",
        "partial_fill_count",
    },
)
_JSON_OPTIONAL_INTEGER_FIELDS = frozenset(
    {
        "resolved_count",
        "pending_count",
        "realized_win_count",
        "realized_loss_count",
    },
)
_JSON_DECIMAL_FIELDS = frozenset(
    {
        "total_requested_size",
        "total_filled_size",
        "total_unfilled_size",
        "total_notional",
    },
)
_MATERIALIZED_DECIMAL_PAYLOAD_PATHS = frozenset(
    (field_name,) for field_name in _JSON_DECIMAL_FIELDS
)


@dataclass(frozen=True)
class PaperTradeAttributionReportDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    trade_count: int
    row_count: int
    market_count: int
    filled_count: int
    complete_fill_count: int
    partial_fill_count: int
    resolved_count: int | None
    pending_count: int | None
    realized_win_count: int | None
    realized_loss_count: int | None
    total_requested_size: Decimal
    total_filled_size: Decimal
    total_unfilled_size: Decimal
    total_notional: Decimal
    first_trade_decision_at: datetime | None
    latest_trade_decision_at: datetime | None
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
        for field_name in _JSON_INTEGER_FIELDS:
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in _JSON_OPTIONAL_INTEGER_FIELDS:
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in _JSON_DECIMAL_FIELDS:
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_trade_decision_at",
            _as_optional_utc("first_trade_decision_at", self.first_trade_decision_at),
        )
        object.__setattr__(
            self,
            "latest_trade_decision_at",
            _as_optional_utc("latest_trade_decision_at", self.latest_trade_decision_at),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_payload_integer_fields(self.payload_json, "payload_json")
        _validate_payload_decimal_strings(self.payload_json, "payload_json")
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_summary_consistency(self)
        _validate_materialized_fields_match_payload(self)
        _validate_payload_recovers_to_compatible_report(self.payload_json)


def paper_trade_attribution_report_to_db_row(
    report: PaperTradeAttributionReport,
) -> PaperTradeAttributionReportDbRow:
    if type(report) is not PaperTradeAttributionReport:
        raise ValueError("report must be a PaperTradeAttributionReport")
    _require_hard_flags("report", report)
    payload_json = _json_ready(asdict(report))
    return PaperTradeAttributionReportDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        trade_count=report.trade_count,
        row_count=report.row_count,
        market_count=report.market_count,
        filled_count=report.filled_count,
        complete_fill_count=report.complete_fill_count,
        partial_fill_count=report.partial_fill_count,
        resolved_count=report.resolved_count,
        pending_count=report.pending_count,
        realized_win_count=report.realized_win_count,
        realized_loss_count=report.realized_loss_count,
        total_requested_size=report.total_requested_size,
        total_filled_size=report.total_filled_size,
        total_unfilled_size=report.total_unfilled_size,
        total_notional=report.total_notional,
        first_trade_decision_at=report.first_trade_decision_at,
        latest_trade_decision_at=report.latest_trade_decision_at,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_trade_attribution_report_from_db_row(
    row: PaperTradeAttributionReportDbRow,
) -> PaperTradeAttributionReport:
    if type(row) is not PaperTradeAttributionReportDbRow:
        raise ValueError("row must be a PaperTradeAttributionReportDbRow")
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_payload_integer_fields(payload_json, "payload_json")
    _validate_payload_decimal_strings(payload_json, "payload_json")
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row, payload_json)
    report = _validate_payload_recovers_to_compatible_report(payload_json)
    expected_row = paper_trade_attribution_report_to_db_row(report)
    if not _json_values_match(_summary_values(row), _summary_values(expected_row)):
        raise ValueError("summary columns must match payload_json")
    return report


def _validate_row_core_fields(row: PaperTradeAttributionReportDbRow) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    for field_name in _JSON_INTEGER_FIELDS:
        _require_nonnegative_int(field_name, getattr(row, field_name))
    for field_name in _JSON_OPTIONAL_INTEGER_FIELDS:
        _require_optional_nonnegative_int(field_name, getattr(row, field_name))
    for field_name in _JSON_DECIMAL_FIELDS:
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    _as_optional_utc("first_trade_decision_at", row.first_trade_decision_at)
    _as_optional_utc("latest_trade_decision_at", row.latest_trade_decision_at)
    _require_hard_flags("DB row", row)
    _validate_summary_consistency(row)


def _summary_values(row: PaperTradeAttributionReportDbRow) -> tuple[Any, ...]:
    return (
        row.generated_at,
        row.config_version,
        row.trade_count,
        row.row_count,
        row.market_count,
        row.filled_count,
        row.complete_fill_count,
        row.partial_fill_count,
        row.resolved_count,
        row.pending_count,
        row.realized_win_count,
        row.realized_loss_count,
        row.total_requested_size,
        row.total_filled_size,
        row.total_unfilled_size,
        row.total_notional,
        row.first_trade_decision_at,
        row.latest_trade_decision_at,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _validate_materialized_fields_match_payload(
    row: PaperTradeAttributionReportDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "trade_count": payload_json.get("trade_count", _MISSING),
        "row_count": payload_json.get("row_count", _MISSING),
        "market_count": payload_json.get("market_count", _MISSING),
        "filled_count": payload_json.get("filled_count", _MISSING),
        "complete_fill_count": payload_json.get("complete_fill_count", _MISSING),
        "partial_fill_count": payload_json.get("partial_fill_count", _MISSING),
        "resolved_count": payload_json.get("resolved_count", _MISSING),
        "pending_count": payload_json.get("pending_count", _MISSING),
        "realized_win_count": payload_json.get("realized_win_count", _MISSING),
        "realized_loss_count": payload_json.get("realized_loss_count", _MISSING),
        "first_trade_decision_at": payload_json.get(
            "first_trade_decision_at",
            _MISSING,
        ),
        "latest_trade_decision_at": payload_json.get(
            "latest_trade_decision_at",
            _MISSING,
        ),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": _as_utc("generated_at", row.generated_at).isoformat(),
        "config_version": row.config_version,
        "trade_count": row.trade_count,
        "row_count": row.row_count,
        "market_count": row.market_count,
        "filled_count": row.filled_count,
        "complete_fill_count": row.complete_fill_count,
        "partial_fill_count": row.partial_fill_count,
        "resolved_count": row.resolved_count,
        "pending_count": row.pending_count,
        "realized_win_count": row.realized_win_count,
        "realized_loss_count": row.realized_loss_count,
        "first_trade_decision_at": (
            None
            if row.first_trade_decision_at is None
            else _as_utc(
                "first_trade_decision_at",
                row.first_trade_decision_at,
            ).isoformat()
        ),
        "latest_trade_decision_at": (
            None
            if row.latest_trade_decision_at is None
            else _as_utc(
                "latest_trade_decision_at",
                row.latest_trade_decision_at,
            ).isoformat()
        ),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        _require_json_exact_match(field_name, actual_value, expected_values[field_name])
    for field_path in _MATERIALIZED_DECIMAL_PAYLOAD_PATHS:
        field_name = field_path[0]
        _require_materialized_decimal_match(
            field_name,
            getattr(row, field_name),
            payload_json.get(field_name, _MISSING),
        )


def _require_json_exact_match(
    field_name: str,
    actual_value: object,
    expected_value: object,
) -> None:
    if type(actual_value) is not type(expected_value) or actual_value != expected_value:
        raise ValueError(f"{field_name} must match payload_json")


def _require_materialized_decimal_match(
    field_name: str,
    row_value: Decimal,
    payload_value: object,
) -> None:
    if type(payload_value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    try:
        payload_decimal = Decimal(payload_value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must match payload_json") from exc
    if not payload_decimal.is_finite() or payload_decimal != row_value:
        raise ValueError(f"{field_name} must match payload_json")


def _validate_payload_recovers_to_compatible_report(
    payload_json: dict[str, Any],
) -> PaperTradeAttributionReport:
    try:
        report = from_jsonable(PaperTradeAttributionReport, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper trade attribution report: {exc}",
        ) from exc
    if type(report) is not PaperTradeAttributionReport:
        raise ValueError("payload_json must recover a PaperTradeAttributionReport")
    _require_hard_flags("report", report)
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        _canonical_report_payload(report),
    )
    return report


def _canonical_report_payload(report: PaperTradeAttributionReport) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload_json must recover a JSON object")
    _validate_payload_decimal_strings(payload, "payload_json")
    return payload


def _json_values_match(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return False
        return all(_json_values_match(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        if len(left) != len(right):
            return False
        return all(
            _json_values_match(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _validate_summary_consistency(row: PaperTradeAttributionReportDbRow) -> None:
    if row.row_count > row.trade_count:
        raise ValueError("row_count must not exceed trade_count")
    if row.market_count > row.row_count:
        raise ValueError("market_count must not exceed row_count")
    if row.filled_count > row.trade_count:
        raise ValueError("filled_count must not exceed trade_count")
    if row.complete_fill_count + row.partial_fill_count > row.trade_count:
        raise ValueError("fill status counts must not exceed trade_count")
    if row.trade_count == 0:
        for field_name in (
            "row_count",
            "market_count",
            "filled_count",
            "complete_fill_count",
            "partial_fill_count",
        ):
            if getattr(row, field_name) != 0:
                raise ValueError(f"{field_name} must be zero")
        for field_name in _JSON_DECIMAL_FIELDS:
            if getattr(row, field_name) != ZERO:
                raise ValueError(f"{field_name} must be zero")
        if row.first_trade_decision_at is not None:
            raise ValueError("first_trade_decision_at must be absent without trades")
        if row.latest_trade_decision_at is not None:
            raise ValueError("latest_trade_decision_at must be absent without trades")
    else:
        if row.first_trade_decision_at is None:
            raise ValueError("first_trade_decision_at is required with trades")
        if row.latest_trade_decision_at is None:
            raise ValueError("latest_trade_decision_at is required with trades")
        if row.latest_trade_decision_at < row.first_trade_decision_at:
            raise ValueError("latest_trade_decision_at cannot precede first")
    outcome_counts = (
        row.resolved_count,
        row.pending_count,
        row.realized_win_count,
        row.realized_loss_count,
    )
    if any(value is None for value in outcome_counts):
        if any(value is not None for value in outcome_counts):
            raise ValueError("outcome counts must be all present or all absent")
        return
    if row.resolved_count + row.pending_count != row.trade_count:
        raise ValueError("resolved_count + pending_count must equal trade_count")
    if row.realized_win_count + row.realized_loss_count != row.resolved_count:
        raise ValueError("realized counts must equal resolved_count")


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
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("paper trade attribution DB row values must be JSON serializable")


def _decimal_to_json(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("JSON Decimal value must be finite")
    if value.is_zero():
        return "0"
    return str(value)


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    _validate_json_hard_flags(normalized, field_name)
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


def _validate_payload_integer_fields(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_INTEGER_FIELDS:
                _require_json_nonnegative_int(child_name, item)
            elif key in _JSON_OPTIONAL_INTEGER_FIELDS:
                _require_json_optional_nonnegative_int(child_name, item)
            else:
                _validate_payload_integer_fields(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_integer_fields(item, f"{field_name} {index}")


def _require_json_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_json_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_json_nonnegative_int(field_name, value)


def _validate_payload_decimal_strings(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_DECIMAL_FIELDS:
                _require_decimal_json_string(child_name, item)
            else:
                _validate_payload_decimal_strings(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_decimal_strings(item, f"{field_name} {index}")


def _require_decimal_json_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal = Decimal(value)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal string")


def _validate_payload_compatible_with_canonical_payload(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    try:
        _validate_json_compatible((), payload_json, expected_payload_json)
    except ValueError as exc:
        raise ValueError(
            f"payload_json must match canonical paper trade attribution report: {exc}",
        ) from exc


def _validate_json_compatible(
    path: tuple[str, ...],
    actual: object,
    expected: object,
) -> None:
    if _is_decimal_payload_path(path):
        _validate_compatible_decimal_path(".".join(path), actual, expected)
        return
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


def _is_decimal_payload_path(path: tuple[str, ...]) -> bool:
    return bool(path) and path[-1] in _JSON_DECIMAL_FIELDS


def _validate_compatible_decimal_path(
    field_name: str,
    actual: object,
    expected: object,
) -> None:
    if type(actual) is not str or type(expected) is not str:
        raise ValueError(f"{field_name} has wrong JSON type")
    try:
        actual_decimal = Decimal(actual)
        expected_decimal = Decimal(expected)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is not a Decimal string") from exc
    if (
        not actual_decimal.is_finite()
        or not expected_decimal.is_finite()
        or actual_decimal != expected_decimal
    ):
        raise ValueError(f"{field_name} differs")


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if _looks_like_report_or_row_payload(value) or any(
        flag_name in value for flag_name in _HARD_FLAG_NAMES
    ):
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


def _looks_like_report_or_row_payload(value: dict[str, Any]) -> bool:
    if "generated_at" in value and "config_version" in value:
        return True
    return all(key in value for key in ("market_slug", "side", "status", "trade_count"))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
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


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
