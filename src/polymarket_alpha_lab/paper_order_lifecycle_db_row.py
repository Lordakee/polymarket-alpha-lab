"""DB row codec for paper order lifecycle records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_order_lifecycle import (
        PaperOrderLifecycleRecord,
    )


__all__ = (
    "PaperOrderLifecycleDbRow",
    "paper_order_lifecycle_record_from_db_row",
    "paper_order_lifecycle_record_to_db_row",
)


_MISSING = object()
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_DECIMAL_PAYLOAD_FIELDS = frozenset(
    (
        "source_execution_notional",
        "fill_notional",
    ),
)


@dataclass(frozen=True)
class PaperOrderLifecycleDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    lifecycle_status: str
    recommended_next_step: str
    source_execution_status: str
    source_execution_notional: Decimal
    fill_notional: Decimal
    is_terminal: bool
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool
    report_only: bool
    readonly: bool

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("lifecycle_status", self.lifecycle_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_canonical_string(
            "source_execution_status",
            self.source_execution_status,
        )
        _require_finite_decimal(
            "source_execution_notional",
            self.source_execution_notional,
        )
        _require_finite_decimal("fill_notional", self.fill_notional)
        if type(self.is_terminal) is not bool:
            raise ValueError("is_terminal must be a bool")
        _validate_reason_codes_json("reason_codes_json", self.reason_codes_json)
        if type(self.payload_json) is not dict:
            raise ValueError("payload_json must be a JSON object")
        _reject_raw_payload_values(self.payload_json, "payload_json")
        _validate_canonical_json_value("payload_json", self.payload_json)
        if type(self.paper_only) is not bool:
            raise ValueError("paper_only must be a bool")
        if type(self.report_only) is not bool:
            raise ValueError("report_only must be a bool")
        if type(self.readonly) is not bool:
            raise ValueError("readonly must be a bool")
        _require_hard_flags("DB row", self)
        _validate_materialized_fields_match_payload(self)
        _validate_json_hard_flags(self.payload_json, "payload_json")


def paper_order_lifecycle_record_to_db_row(
    record: PaperOrderLifecycleRecord,
) -> PaperOrderLifecycleDbRow:
    from polymarket_alpha_lab.paper_order_lifecycle import (
        PaperOrderLifecycleRecord,
    )
    if type(record) is not PaperOrderLifecycleRecord:
        raise ValueError("record must be a PaperOrderLifecycleRecord")
    payload = {
        "generated_at": record.generated_at.isoformat(),
        "config_version": record.config_version,
        "lifecycle_status": record.lifecycle_status,
        "recommended_next_step": record.recommended_next_step,
        "source_execution_status": record.source_execution_status,
        "source_execution_notional": _json_ready(record.source_execution_notional),
        "fill_notional": _json_ready(record.fill_notional),
        "is_terminal": record.is_terminal,
        "reason_codes": list(record.reason_codes),
        "paper_only": record.paper_only,
        "report_only": record.report_only,
        "readonly": record.readonly,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    report_sha256 = hashlib.sha256(payload_json.encode()).hexdigest()
    return PaperOrderLifecycleDbRow(
        report_sha256=report_sha256,
        generated_at=record.generated_at,
        config_version=record.config_version,
        lifecycle_status=record.lifecycle_status,
        recommended_next_step=record.recommended_next_step,
        source_execution_status=record.source_execution_status,
        source_execution_notional=record.source_execution_notional,
        fill_notional=record.fill_notional,
        is_terminal=record.is_terminal,
        reason_codes_json=list(record.reason_codes),
        payload_json=payload,
        paper_only=record.paper_only,
        report_only=record.report_only,
        readonly=record.readonly,
    )


def paper_order_lifecycle_record_from_db_row(
    row: PaperOrderLifecycleDbRow,
) -> PaperOrderLifecycleRecord:
    from polymarket_alpha_lab.paper_order_lifecycle import (
        PaperOrderLifecycleRecord,
    )
    if type(row) is not PaperOrderLifecycleDbRow:
        raise ValueError("row must be a PaperOrderLifecycleDbRow")
    try:
        row.__post_init__()
    except AttributeError as exc:
        raise ValueError("row must be a valid PaperOrderLifecycleDbRow") from exc
    return PaperOrderLifecycleRecord(
        generated_at=row.generated_at,
        config_version=row.config_version,
        lifecycle_status=row.lifecycle_status,
        recommended_next_step=row.recommended_next_step,
        source_execution_status=row.source_execution_status,
        source_execution_notional=row.source_execution_notional,
        fill_notional=row.fill_notional,
        is_terminal=row.is_terminal,
        reason_codes=tuple(row.reason_codes_json),
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _validate_materialized_fields_match_payload(
    row: PaperOrderLifecycleDbRow,
) -> None:
    payload_json = row.payload_json
    _validate_raw_payload_hash(row, payload_json)
    normalized_payload_json = _normalize_legacy_decimal_payload(payload_json)
    expected_values = {
        "generated_at": normalized_payload_json.get("generated_at", _MISSING),
        "config_version": normalized_payload_json.get("config_version", _MISSING),
        "lifecycle_status": normalized_payload_json.get("lifecycle_status", _MISSING),
        "recommended_next_step": normalized_payload_json.get(
            "recommended_next_step",
            _MISSING,
        ),
        "source_execution_status": normalized_payload_json.get(
            "source_execution_status",
            _MISSING,
        ),
        "source_execution_notional": normalized_payload_json.get(
            "source_execution_notional",
            _MISSING,
        ),
        "fill_notional": normalized_payload_json.get("fill_notional", _MISSING),
        "is_terminal": normalized_payload_json.get("is_terminal", _MISSING),
        "reason_codes_json": normalized_payload_json.get("reason_codes", _MISSING),
        "paper_only": normalized_payload_json.get("paper_only", _MISSING),
        "report_only": normalized_payload_json.get("report_only", _MISSING),
        "readonly": normalized_payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "lifecycle_status": row.lifecycle_status,
        "recommended_next_step": row.recommended_next_step,
        "source_execution_status": row.source_execution_status,
        "source_execution_notional": _json_ready(row.source_execution_notional),
        "fill_notional": _json_ready(row.fill_notional),
        "is_terminal": row.is_terminal,
        "reason_codes_json": row.reason_codes_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if actual_value != expected_values[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_raw_payload_hash(
    row: PaperOrderLifecycleDbRow,
    payload_json: dict[str, Any],
) -> None:
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return _decimal_to_six_place_string("JSON Decimal value", value)
    return value


def _normalize_legacy_decimal_payload(
    value: Any,
    field_path: tuple[str | int, ...] = (),
) -> Any:
    if _is_decimal_payload_path(field_path):
        field_name = _format_payload_path(field_path)
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal string")
        return _decimal_string_to_six_place(field_name, value)
    if type(value) is str and _is_decimal_like_string(value):
        raise ValueError(
            f"{_format_payload_path(field_path)} contains a Decimal-like string "
            "outside allowlisted Decimal payload fields",
        )
    if isinstance(value, dict):
        return {
            key: _normalize_legacy_decimal_payload(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _normalize_legacy_decimal_payload(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    return value


def _is_decimal_payload_path(field_path: tuple[str | int, ...]) -> bool:
    return len(field_path) == 1 and field_path[0] in _DECIMAL_PAYLOAD_FIELDS


def _decimal_string_to_six_place(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _decimal_to_six_place_string(field_name, decimal)


def _decimal_to_six_place_string(field_name: str, value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext() as context:
            integer_digits = max(value.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            quantized = value.quantize(_DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must have at most six decimal places") from exc
    if quantized != value:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return format(quantized, "f")


def _is_decimal_like_string(value: str) -> bool:
    if "." not in value and "e" not in value.lower():
        return False
    try:
        Decimal(value)
    except (InvalidOperation, ValueError):
        return False
    return True


def _format_payload_path(field_path: tuple[str | int, ...]) -> str:
    if not field_path:
        return "payload_json"
    formatted = "payload_json"
    for item in field_path:
        if isinstance(item, int):
            formatted = f"{formatted}[{item}]"
        else:
            formatted = f"{formatted}.{item}"
    return formatted


def _reject_raw_payload_values(value: Any, field_name: str) -> None:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not be a raw Decimal")
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must not be a raw datetime")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_raw_payload_values(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_raw_payload_values(item, f"{field_name}[{index}]")


def _validate_canonical_json_value(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) in (str, int, bool):
        return
    if type(value) is float:
        raise ValueError(f"{field_name} JSON value must not be a float")
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_canonical_json_value(f"{field_name} {index}", item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} JSON object keys must be strings")
            _validate_canonical_json_value(f"{field_name} {key}", item)
        return
    raise ValueError(f"{field_name} must contain canonical JSON values")


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(
        flag_name in value
        for flag_name in ("paper_only", "report_only", "readonly")
    ):
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


def _validate_reason_codes_json(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    previous: str | None = None
    for reason_code in value:
        _require_canonical_string(f"{field_name} entries", reason_code)
        if previous is not None and previous >= reason_code:
            raise ValueError(f"{field_name} must be sorted and unique")
        previous = reason_code


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_finite_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
