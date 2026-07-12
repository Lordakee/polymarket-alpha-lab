from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


COUNT_QUANT = Decimal("0.000001")
UNSAFE_REASON_CODES = (
    "unsafe_account_text",
    "unsafe_execute_text",
    "unsafe_key_text",
    "unsafe_live_text",
    "unsafe_order_text",
    "unsafe_private_key_text",
    "unsafe_sign_text",
    "unsafe_submit_text",
    "unsafe_wallet_text",
)
UNSAFE_TEXT_MATCHERS = (
    ("account", "unsafe_account_text"),
    ("execute", "unsafe_execute_text"),
    ("execution", "unsafe_execute_text"),
    ("key", "unsafe_key_text"),
    ("live", "unsafe_live_text"),
    ("order", "unsafe_order_text"),
    ("private-key", "unsafe_private_key_text"),
    ("private_key", "unsafe_private_key_text"),
    ("private key", "unsafe_private_key_text"),
    ("sign", "unsafe_sign_text"),
    ("submit", "unsafe_submit_text"),
    ("wallet", "unsafe_wallet_text"),
)


@dataclass(frozen=True)
class PublicPayloadExecutionTextSafetyInput:
    candidate_id: str
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PublicPayloadExecutionTextSafetyInput:
            raise ValueError("PublicPayloadExecutionTextSafetyInput does not support subclassing")
        _require_public_string("candidate_id", self.candidate_id)
        if type(self.payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_json_payload(self.payload)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class PublicPayloadExecutionTextSafetyRow:
    candidate_id: str
    safety_status: str
    unsafe_field_count: Decimal
    unsafe_fields: tuple[str, ...]
    reason_codes: tuple[str, ...]
    redaction_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PublicPayloadExecutionTextSafetyRow:
            raise ValueError("PublicPayloadExecutionTextSafetyRow does not support subclassing")
        _require_public_string("candidate_id", self.candidate_id)
        _require_hard_flags("row", self)
        _require_decimal_count("unsafe_field_count", self.unsafe_field_count)
        _require_string_tuple("unsafe_fields", self.unsafe_fields)
        _require_reason_codes(self.reason_codes)
        expected_count = _count(len(self.unsafe_fields))
        if self.unsafe_field_count != expected_count:
            raise ValueError("unsafe_field_count must match unsafe_fields")
        expected_status = "unsafe" if self.unsafe_fields else "safe"
        if self.safety_status != expected_status:
            raise ValueError("safety_status must match unsafe_field_count")
        expected_redaction = bool(self.unsafe_fields)
        if self.redaction_required is not expected_redaction:
            raise ValueError("redaction_required must match unsafe_field_count")
        if self.unsafe_fields:
            if self.reason_codes == ("execution_text_safety_clear",):
                raise ValueError("reason_codes must match unsafe_fields")
        elif self.reason_codes != ("execution_text_safety_clear",):
            raise ValueError("reason_codes must match unsafe_fields")


@dataclass(frozen=True)
class PublicPayloadExecutionTextSafetyRollupReport:
    generated_at: datetime
    candidate_count: Decimal
    unsafe_field_count: Decimal
    safety_status: str
    reason_codes: tuple[str, ...]
    redaction_required: bool
    rows: tuple[PublicPayloadExecutionTextSafetyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PublicPayloadExecutionTextSafetyRollupReport:
            raise ValueError(
                "PublicPayloadExecutionTextSafetyRollupReport does not support subclassing",
            )
        _require_aware_datetime("generated_at", self.generated_at)
        _require_hard_flags("report", self)
        _require_decimal_count("candidate_count", self.candidate_count)
        _require_decimal_count("unsafe_field_count", self.unsafe_field_count)
        _require_rows(self.rows)
        expected_candidate_count = _count(len(self.rows))
        if self.candidate_count != expected_candidate_count:
            raise ValueError("candidate_count must match rows")
        expected_unsafe_count = _sum_counts(
            tuple(row.unsafe_field_count for row in self.rows),
        )
        if self.unsafe_field_count != expected_unsafe_count:
            raise ValueError("unsafe_field_count must match rows")
        expected_status = "unsafe" if self.unsafe_field_count > Decimal("0") else "safe"
        if self.safety_status != expected_status:
            raise ValueError("safety_status must match rows")
        expected_redaction = self.safety_status == "unsafe"
        if self.redaction_required is not expected_redaction:
            raise ValueError("redaction_required must match safety_status")
        if self.reason_codes != _report_reason_codes(self.rows):
            raise ValueError("reason_codes must match rows")


def build_public_payload_execution_text_safety_rollup_report(
    candidates: list[PublicPayloadExecutionTextSafetyInput]
    | tuple[PublicPayloadExecutionTextSafetyInput, ...],
    *,
    generated_at: datetime,
) -> PublicPayloadExecutionTextSafetyRollupReport:
    _require_aware_datetime("generated_at", generated_at)
    rows = tuple(_row_from_candidate(candidate) for candidate in candidates)
    return PublicPayloadExecutionTextSafetyRollupReport(
        generated_at=generated_at.astimezone(UTC),
        candidate_count=_count(len(rows)),
        unsafe_field_count=_sum_counts(tuple(row.unsafe_field_count for row in rows)),
        safety_status="unsafe" if any(row.safety_status == "unsafe" for row in rows) else "safe",
        reason_codes=_report_reason_codes(rows),
        redaction_required=any(row.redaction_required for row in rows),
        rows=rows,
    )


def public_payload_execution_text_safety_rollup_report_payload(
    report: PublicPayloadExecutionTextSafetyRollupReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is PublicPayloadExecutionTextSafetyRollupReport:
        payload = _public_payload_from_report(report)
        _reject_public_numeric_values(payload)
        _require_hard_flags("payload", _PayloadFlags(payload))
        return payload
    if type(report) is dict:
        _reject_public_numeric_values(report)
        _require_hard_flags("payload", _PayloadFlags(report))
        return _json_ready(report)
    raise ValueError("report must be a PublicPayloadExecutionTextSafetyRollupReport")


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_candidate(
    candidate: PublicPayloadExecutionTextSafetyInput,
) -> PublicPayloadExecutionTextSafetyRow:
    if type(candidate) is not PublicPayloadExecutionTextSafetyInput:
        raise ValueError("candidate must be a PublicPayloadExecutionTextSafetyInput")
    unsafe_fields, reason_codes = _scan_payload(candidate.payload)
    has_unsafe_fields = bool(unsafe_fields)
    return PublicPayloadExecutionTextSafetyRow(
        candidate_id=candidate.candidate_id,
        safety_status="unsafe" if has_unsafe_fields else "safe",
        unsafe_field_count=_count(len(unsafe_fields)),
        unsafe_fields=unsafe_fields,
        reason_codes=reason_codes if has_unsafe_fields else ("execution_text_safety_clear",),
        redaction_required=has_unsafe_fields,
    )


def _scan_payload(payload: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    unsafe_fields: list[str] = []
    reason_codes: set[str] = set()
    _scan_value(payload, "", unsafe_fields, reason_codes)
    return tuple(unsafe_fields), _ordered_reason_codes(reason_codes)


def _scan_value(
    value: Any,
    path: str,
    unsafe_fields: list[str],
    reason_codes: set[str],
) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload JSON object keys must be strings")
            child_path = f"{path}.{key}" if path else key
            key_reason_codes = _reason_codes_from_text(key)
            for reason_code in key_reason_codes:
                unsafe_fields.append(child_path)
                reason_codes.add(reason_code)
            _scan_value(item, child_path, unsafe_fields, reason_codes)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            _scan_value(item, child_path, unsafe_fields, reason_codes)
        return
    if type(value) is str:
        value_reason_codes = _reason_codes_from_text(value)
        if value_reason_codes:
            unsafe_fields.append(path or "<root>")
            reason_codes.update(value_reason_codes)


def _reason_codes_from_text(value: str) -> tuple[str, ...]:
    lowered = value.lower()
    matched = {
        reason_code
        for fragment, reason_code in UNSAFE_TEXT_MATCHERS
        if fragment in lowered
    }
    return _ordered_reason_codes(matched)


def _ordered_reason_codes(reason_codes: set[str]) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in UNSAFE_REASON_CODES if reason_code in reason_codes)


def _report_reason_codes(
    rows: tuple[PublicPayloadExecutionTextSafetyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("execution_text_safety_empty",)
    unsafe_reason_codes: set[str] = set()
    for row in rows:
        unsafe_reason_codes.update(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in UNSAFE_REASON_CODES
        )
    if unsafe_reason_codes:
        return ("execution_text_safety_unsafe", *_ordered_reason_codes(unsafe_reason_codes))
    return ("execution_text_safety_clear",)


def _public_payload_from_report(
    report: PublicPayloadExecutionTextSafetyRollupReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.astimezone(UTC).isoformat(),
        "candidate_count": _decimal_payload(report.candidate_count),
        "unsafe_field_count": _decimal_payload(report.unsafe_field_count),
        "safety_status": report.safety_status,
        "reason_codes": list(report.reason_codes),
        "redaction_required": report.redaction_required,
        "rows": [_public_payload_from_row(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _public_payload_from_row(row: PublicPayloadExecutionTextSafetyRow) -> dict[str, Any]:
    return {
        "candidate_id": row.candidate_id,
        "safety_status": row.safety_status,
        "unsafe_field_count": _decimal_payload(row.unsafe_field_count),
        "unsafe_fields": list(row.unsafe_fields),
        "reason_codes": list(row.reason_codes),
        "redaction_required": row.redaction_required,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not str or not item:
            raise ValueError(f"{field_name} must contain non-empty strings")
    return value


def _require_reason_codes(value: object) -> tuple[str, ...]:
    allowed = {
        "execution_text_safety_clear",
        "execution_text_safety_empty",
        "execution_text_safety_unsafe",
        *UNSAFE_REASON_CODES,
    }
    codes = _require_string_tuple("reason_codes", value)
    for code in codes:
        if code not in allowed:
            raise ValueError("reason_codes contains an unknown reason code")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    return codes


def _require_rows(value: object) -> tuple[PublicPayloadExecutionTextSafetyRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not PublicPayloadExecutionTextSafetyRow:
            raise ValueError("rows must contain PublicPayloadExecutionTextSafetyRow values")
    return value


def _require_aware_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value


def _require_decimal_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be non-negative")
    if value != value.quantize(COUNT_QUANT):
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _require_json_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload JSON object keys must be strings")
            _require_json_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _require_json_payload(item)
        return
    if value is None or type(value) in (str, bool, int, float):
        return
    raise ValueError("payload must contain JSON-compatible values")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _decimal_payload(value: Decimal) -> str:
    return f"{value.quantize(COUNT_QUANT):.6f}"


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    total = Decimal("0")
    for value in values:
        total += value
    return total.quantize(COUNT_QUANT)
