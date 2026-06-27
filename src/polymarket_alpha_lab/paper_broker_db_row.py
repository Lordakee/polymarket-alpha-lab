"""Pure row codec for persisted paper broker execution records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord


__all__ = (
    "PaperBrokerExecutionDbRow",
    "from_db_row",
    "paper_broker_execution_record_from_db_row",
    "paper_broker_execution_record_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_STRING_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d{1,6})?$")
_EXECUTION_STATUSES = ("paper_submitted", "paper_blocked", "paper_held")
_GATE_STATUSES = ("pass", "watch", "blocked")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_DECIMAL_QUANTUM = Decimal("0.000001")
_JSON_DECIMAL_FIELDS = frozenset(
    {
        "source_proposal_total_notional",
        "execution_notional",
    },
)
_MISSING = object()


@dataclass(frozen=True)
class PaperBrokerExecutionDbRow:
    record_sha256: str
    generated_at: datetime
    config_version: str
    execution_status: str
    recommended_next_step: str
    source_gate_status: str
    source_proposal_count: int
    source_proposal_total_notional: Decimal
    execution_notional: Decimal
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("record_sha256", self.record_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_choice("execution_status", self.execution_status, _EXECUTION_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_choice("source_gate_status", self.source_gate_status, _GATE_STATUSES)
        _require_nonnegative_int("source_proposal_count", self.source_proposal_count)
        _require_nonnegative_decimal(
            "source_proposal_total_notional",
            self.source_proposal_total_notional,
        )
        _require_nonnegative_decimal("execution_notional", self.execution_notional)
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        payload_json = _normalize_json_object("payload_json", self.payload_json)
        _require_hard_flags("DB row", self)
        _validate_payload_contract(self, payload_json)
        canonical_payload_json = _normalize_legacy_decimal_payload_json(payload_json)
        object.__setattr__(self, "payload_json", payload_json)
        canonical_row = _row_with_payload(self, canonical_payload_json)
        _validate_materialized_fields_match_payload(
            canonical_row,
            require_record_sha256=False,
        )
        record = _paper_broker_execution_record_from_payload(canonical_payload_json)
        _validate_row_matches_payload(
            canonical_row,
            record,
            require_record_sha256=False,
        )


def paper_broker_execution_record_to_db_row(
    record: PaperBrokerExecutionRecord,
) -> PaperBrokerExecutionDbRow:
    if type(record) is not PaperBrokerExecutionRecord:
        raise ValueError("record must be a PaperBrokerExecutionRecord")
    _require_hard_flags("record", record)
    payload_json = _json_ready(asdict(record))
    return PaperBrokerExecutionDbRow(
        record_sha256=_record_sha256(payload_json),
        generated_at=record.generated_at,
        config_version=record.config_version,
        execution_status=record.execution_status,
        recommended_next_step=record.recommended_next_step,
        source_gate_status=record.source_gate_status,
        source_proposal_count=record.source_proposal_count,
        source_proposal_total_notional=Decimal(
            payload_json["source_proposal_total_notional"],
        ),
        execution_notional=Decimal(payload_json["execution_notional"]),
        reason_codes_json=list(payload_json["reason_codes"]),
        payload_json=payload_json,
        paper_only=record.paper_only,
        report_only=record.report_only,
        readonly=record.readonly,
    )


def paper_broker_execution_record_from_db_row(
    row: PaperBrokerExecutionDbRow,
) -> PaperBrokerExecutionRecord:
    if type(row) is not PaperBrokerExecutionDbRow:
        raise ValueError("row must be a PaperBrokerExecutionDbRow")
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_payload_contract(row, payload_json)
    canonical_payload_json = _normalize_legacy_decimal_payload_json(payload_json)
    canonical_row = _row_with_payload(row, canonical_payload_json)
    _validate_materialized_fields_match_payload(
        canonical_row,
        require_record_sha256=False,
    )
    record = _paper_broker_execution_record_from_payload(canonical_payload_json)
    _validate_row_matches_payload(
        canonical_row,
        record,
        require_record_sha256=False,
    )
    return record


def _paper_broker_execution_record_from_payload(
    payload_json: dict[str, Any],
) -> PaperBrokerExecutionRecord:
    try:
        record = from_jsonable(PaperBrokerExecutionRecord, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper broker execution record: {exc}",
        ) from exc
    if type(record) is not PaperBrokerExecutionRecord:
        raise ValueError("payload_json must recover a PaperBrokerExecutionRecord")
    _require_hard_flags("record", record)
    if not _values_match_type_strict(payload_json, _json_ready(asdict(record))):
        raise ValueError("payload_json must be canonical")
    return record


def to_db_row(record: PaperBrokerExecutionRecord) -> PaperBrokerExecutionDbRow:
    return paper_broker_execution_record_to_db_row(record)


def from_db_row(row: PaperBrokerExecutionDbRow) -> PaperBrokerExecutionRecord:
    return paper_broker_execution_record_from_db_row(row)


def _validate_row_matches_payload(
    row: PaperBrokerExecutionDbRow,
    record: PaperBrokerExecutionRecord,
    *,
    require_record_sha256: bool = True,
) -> None:
    payload_json = _json_ready(asdict(record))
    if row.payload_json != payload_json:
        raise ValueError("payload_json must be canonical")
    expected_values = {
        "record_sha256": _record_sha256(payload_json),
        "generated_at": record.generated_at,
        "config_version": record.config_version,
        "execution_status": record.execution_status,
        "recommended_next_step": record.recommended_next_step,
        "source_gate_status": record.source_gate_status,
        "source_proposal_count": record.source_proposal_count,
        "source_proposal_total_notional": record.source_proposal_total_notional,
        "execution_notional": record.execution_notional,
        "reason_codes_json": list(payload_json["reason_codes"]),
        "paper_only": record.paper_only,
        "report_only": record.report_only,
        "readonly": record.readonly,
    }
    for field_name, expected_value in expected_values.items():
        if field_name == "record_sha256" and not require_record_sha256:
            continue
        if not _values_match_type_strict(getattr(row, field_name), expected_value):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperBrokerExecutionDbRow,
    *,
    require_record_sha256: bool = True,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "record_sha256": _record_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "execution_status": payload_json.get("execution_status", _MISSING),
        "recommended_next_step": payload_json.get(
            "recommended_next_step",
            _MISSING,
        ),
        "source_gate_status": payload_json.get("source_gate_status", _MISSING),
        "source_proposal_count": payload_json.get(
            "source_proposal_count",
            _MISSING,
        ),
        "source_proposal_total_notional": payload_json.get(
            "source_proposal_total_notional",
            _MISSING,
        ),
        "execution_notional": payload_json.get("execution_notional", _MISSING),
        "reason_codes_json": payload_json.get("reason_codes", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "record_sha256": row.record_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "execution_status": row.execution_status,
        "recommended_next_step": row.recommended_next_step,
        "source_gate_status": row.source_gate_status,
        "source_proposal_count": row.source_proposal_count,
        "source_proposal_total_notional": _decimal_json_preserving_scale(
            "source_proposal_total_notional",
            row.source_proposal_total_notional,
        ),
        "execution_notional": _decimal_json_preserving_scale(
            "execution_notional",
            row.execution_notional,
        ),
        "reason_codes_json": row.reason_codes_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if field_name == "record_sha256" and not require_record_sha256:
            continue
        if not _values_match_type_strict(actual_value, expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _record_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    return _json_ready_path(value, ())


def _json_ready_path(value: Any, field_path: tuple[str | int, ...]) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_path(asdict(value), field_path)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if not _is_json_decimal_path(field_path):
            raise ValueError(
                f"{_format_payload_path(field_path)} is not an allowed Decimal path",
            )
        return _fixed_six_decimal_string(_format_payload_path(field_path), value)
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
        return {
            key: _json_ready_path(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _json_ready_path(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    raise ValueError("paper broker execution DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    _validate_raw_json_value(field_name, value)
    normalized = _copy_json_value(value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _validate_raw_json_value(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) in (str, int, bool):
        return
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not contain float values")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not contain Decimal values")
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must not contain datetime values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} JSON object keys must be strings")
            _validate_raw_json_value(f"{field_name}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_raw_json_value(f"{field_name}.{index}", item)
        return
    raise ValueError(f"{field_name} must contain only JSON values")


def _copy_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    return value


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[str] = []
    previous: str | None = None
    for item in value:
        _require_canonical_string(f"{field_name} entry", item)
        if previous is not None and previous >= item:
            raise ValueError(f"{field_name} must be sorted and unique")
        normalized.append(item)
        previous = item
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if _json_object_requires_hard_flags(
        value,
        field_name,
    ) or any(flag_name in value for flag_name in _HARD_FLAG_NAMES):
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


def _json_object_requires_hard_flags(value: dict[str, Any], field_name: str) -> bool:
    return field_name == "payload_json" or (
        "generated_at" in value and "config_version" in value
    )


def _validate_payload_contract(
    row: PaperBrokerExecutionDbRow,
    payload_json: dict[str, Any],
) -> None:
    _require_json_hard_flags(payload_json, "payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    if row.record_sha256 != _record_sha256(payload_json):
        raise ValueError("record_sha256 must match payload_json")
    _validate_payload_decimal_strings(payload_json, "payload_json")


def _normalize_legacy_decimal_payload_json(payload_json: dict[str, Any]) -> dict[str, Any]:
    normalized = _copy_json_value(payload_json)
    if not isinstance(normalized, dict):
        raise ValueError("payload_json must be a JSON object")
    for field_name in _JSON_DECIMAL_FIELDS:
        if field_name not in normalized:
            continue
        normalized[field_name] = _fixed_six_decimal_json_string(
            f"payload_json {field_name}",
            normalized[field_name],
        )
    return normalized


def _validate_payload_decimal_strings(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_DECIMAL_FIELDS:
                if field_name != "payload_json":
                    raise ValueError(
                        f"{child_name} is not an allowed Decimal payload path",
                    )
                _require_json_decimal_string(child_name, item)
                continue
            _validate_payload_decimal_strings(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_decimal_strings(item, f"{field_name} {index}")


def _require_json_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    _fixed_six_decimal_json_string(field_name, value)


def _fixed_six_decimal_json_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    if _DECIMAL_STRING_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal = Decimal(value)
    except (ArithmeticError, InvalidOperation) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal string")
    return _fixed_six_decimal_string(field_name, decimal)


def _fixed_six_decimal_string(field_name: str, value: object) -> str:
    decimal = _require_fixed_six_decimal(field_name, value)
    return format(decimal, "f")


def _decimal_json_preserving_scale(field_name: str, value: object) -> str:
    decimal = _require_decimal(field_name, value)
    return str(decimal)


def _require_fixed_six_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    try:
        with localcontext() as context:
            integer_digits = max(decimal.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            fixed_decimal = decimal.quantize(_DECIMAL_QUANTUM)
    except (ArithmeticError, InvalidOperation) as exc:
        raise ValueError(f"{field_name} must not exceed six decimal places") from exc
    if decimal != fixed_decimal:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return fixed_decimal


def _is_json_decimal_path(field_path: tuple[str | int, ...]) -> bool:
    return len(field_path) == 1 and field_path[0] in _JSON_DECIMAL_FIELDS


def _format_payload_path(field_path: tuple[str | int, ...]) -> str:
    if not field_path:
        return "JSON value"
    return "payload_json " + " ".join(str(item) for item in field_path)


def _row_with_payload(
    row: PaperBrokerExecutionDbRow,
    payload_json: dict[str, Any],
) -> PaperBrokerExecutionDbRow:
    unchecked = object.__new__(PaperBrokerExecutionDbRow)
    for name, value in row.__dict__.items():
        object.__setattr__(unchecked, name, value)
    object.__setattr__(unchecked, "payload_json", payload_json)
    return unchecked


def _values_match_type_strict(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():
            return False
        return all(
            _values_match_type_strict(actual[key], expected[key])
            for key in actual
        )
    if isinstance(actual, (list, tuple)):
        if len(actual) != len(expected):
            return False
        return all(
            _values_match_type_strict(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected, strict=True)
        )
    return actual == expected


def _require_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    for flag_name in _HARD_FLAG_NAMES:
        if value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


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


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        rendered = ", ".join(choices)
        raise ValueError(f"{field_name} must be one of: {rendered}")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a finite Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    decimal = _require_decimal(field_name, value)
    if decimal < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
