"""Pure row codec for persisted paper autonomous proposal risk gate reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_proposal import PROPOSAL_STATUSES
from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    PaperAutonomousProposalRiskGateReport,
)


__all__ = (
    "PaperAutonomousProposalRiskGateDbRow",
    "from_db_row",
    "paper_autonomous_proposal_risk_gate_report_from_db_row",
    "paper_autonomous_proposal_risk_gate_report_to_db_row",
    "to_db_row",
)


ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")
GATE_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_proposal_to_paper_broker",
    "watch": "hold_paper_proposal_for_risk_review",
    "blocked": "block_paper_proposal_pending_risk_repair",
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_DECIMAL_PAYLOAD_FIELDS = frozenset({"source_proposal_total_notional"})
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_next_step",
    "source_proposal_status",
    "source_proposal_count",
    "source_proposal_total_notional",
    "blocked_reason_codes_json",
    "watch_reason_codes_json",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)
_MISSING = object()


@dataclass(frozen=True)
class PaperAutonomousProposalRiskGateDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    source_proposal_status: str
    source_proposal_count: int
    source_proposal_total_notional: Decimal
    blocked_reason_codes_json: tuple[str, ...]
    watch_reason_codes_json: tuple[str, ...]
    reason_codes_json: tuple[str, ...]
    payload_json: Mapping[str, Any]
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
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        _require_source_proposal_status(
            "source_proposal_status",
            self.source_proposal_status,
        )
        _require_nonnegative_int(
            "source_proposal_count",
            self.source_proposal_count,
        )
        object.__setattr__(
            self,
            "source_proposal_total_notional",
            _normalize_nonnegative_decimal(
                "source_proposal_total_notional",
                self.source_proposal_total_notional,
            ),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes_json",
            _normalize_string_list(
                "blocked_reason_codes_json",
                self.blocked_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "watch_reason_codes_json",
            _normalize_string_list(
                "watch_reason_codes_json",
                self.watch_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_payload_decimal_strings(self.payload_json)
        _validate_materialized_fields_match_payload(self, self.payload_json)
        _validate_payload_recovers_to_compatible_report(self.payload_json)


def to_db_row(
    report: PaperAutonomousProposalRiskGateReport,
) -> PaperAutonomousProposalRiskGateDbRow:
    return paper_autonomous_proposal_risk_gate_report_to_db_row(report)


def from_db_row(
    row: PaperAutonomousProposalRiskGateDbRow,
) -> PaperAutonomousProposalRiskGateReport:
    return paper_autonomous_proposal_risk_gate_report_from_db_row(row)


def paper_autonomous_proposal_risk_gate_report_to_db_row(
    report: PaperAutonomousProposalRiskGateReport,
) -> PaperAutonomousProposalRiskGateDbRow:
    if type(report) is not PaperAutonomousProposalRiskGateReport:
        raise ValueError("report must be a PaperAutonomousProposalRiskGateReport")
    _require_hard_flags("report", report)
    payload_json = _json_ready(asdict(report))
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    blocked_reason_codes_json = payload_json.get("blocked_reason_codes")
    watch_reason_codes_json = payload_json.get("watch_reason_codes")
    reason_codes_json = payload_json.get("reason_codes")
    return PaperAutonomousProposalRiskGateDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_status=report.gate_status,
        recommended_next_step=report.recommended_next_step,
        source_proposal_status=report.source_proposal_status,
        source_proposal_count=report.source_proposal_count,
        source_proposal_total_notional=report.source_proposal_total_notional,
        blocked_reason_codes_json=_normalize_string_list(
            "blocked_reason_codes_json",
            blocked_reason_codes_json,
        ),
        watch_reason_codes_json=_normalize_string_list(
            "watch_reason_codes_json",
            watch_reason_codes_json,
        ),
        reason_codes_json=_normalize_string_list(
            "reason_codes_json",
            reason_codes_json,
        ),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_proposal_risk_gate_report_from_db_row(
    row: PaperAutonomousProposalRiskGateDbRow,
) -> PaperAutonomousProposalRiskGateReport:
    if type(row) is not PaperAutonomousProposalRiskGateDbRow:
        raise ValueError("row must be a PaperAutonomousProposalRiskGateDbRow")
    _validate_row_shape(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_payload_decimal_strings(payload_json)
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_materialized_fields_match_payload(row, payload_json)
    return _validate_payload_recovers_to_compatible_report(payload_json)


def _validate_row_shape(row: PaperAutonomousProposalRiskGateDbRow) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    _require_gate_status("gate_status", row.gate_status)
    _require_canonical_string("recommended_next_step", row.recommended_next_step)
    if row.recommended_next_step != NEXT_STEP_BY_STATUS[row.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    _require_source_proposal_status(
        "source_proposal_status",
        row.source_proposal_status,
    )
    _require_nonnegative_int("source_proposal_count", row.source_proposal_count)
    _normalize_nonnegative_decimal(
        "source_proposal_total_notional",
        row.source_proposal_total_notional,
    )
    _normalize_string_list("blocked_reason_codes_json", row.blocked_reason_codes_json)
    _normalize_string_list("watch_reason_codes_json", row.watch_reason_codes_json)
    _normalize_string_list("reason_codes_json", row.reason_codes_json)
    _normalize_json_object("payload_json", row.payload_json)
    _require_hard_flags("DB row", row)


def _validate_materialized_fields_match_payload(
    row: PaperAutonomousProposalRiskGateDbRow,
    payload_json: Mapping[str, Any],
) -> None:
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "gate_status": payload_json.get("gate_status", _MISSING),
        "recommended_next_step": payload_json.get("recommended_next_step", _MISSING),
        "source_proposal_status": payload_json.get(
            "source_proposal_status",
            _MISSING,
        ),
        "source_proposal_count": payload_json.get(
            "source_proposal_count",
            _MISSING,
        ),
        "source_proposal_total_notional": payload_json.get(
            "source_proposal_total_notional",
            _MISSING,
        ),
        "blocked_reason_codes_json": payload_json.get(
            "blocked_reason_codes",
            _MISSING,
        ),
        "watch_reason_codes_json": payload_json.get("watch_reason_codes", _MISSING),
        "reason_codes_json": payload_json.get("reason_codes", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": _as_utc("generated_at", row.generated_at).isoformat(),
        "config_version": row.config_version,
        "gate_status": row.gate_status,
        "recommended_next_step": row.recommended_next_step,
        "source_proposal_status": row.source_proposal_status,
        "source_proposal_count": row.source_proposal_count,
        "source_proposal_total_notional": _fixed_six_decimal_string(
            "source_proposal_total_notional",
            row.source_proposal_total_notional,
        ),
        "blocked_reason_codes_json": _normalize_string_list(
            "blocked_reason_codes_json",
            row.blocked_reason_codes_json,
        ),
        "watch_reason_codes_json": _normalize_string_list(
            "watch_reason_codes_json",
            row.watch_reason_codes_json,
        ),
        "reason_codes_json": _normalize_string_list(
            "reason_codes_json",
            row.reason_codes_json,
        ),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _MATERIALIZED_FIELDS:
        if not _json_equal_strict(actual_values[field_name], expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_payload_recovers_to_compatible_report(
    payload_json: Mapping[str, Any],
) -> PaperAutonomousProposalRiskGateReport:
    try:
        report = from_jsonable(
            PaperAutonomousProposalRiskGateReport,
            _mutable_json_payload(payload_json),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid paper autonomous proposal risk gate "
            f"report: {exc}",
        ) from exc
    if type(report) is not PaperAutonomousProposalRiskGateReport:
        raise ValueError(
            "payload_json must recover a PaperAutonomousProposalRiskGateReport",
        )
    _require_hard_flags("report", report)
    canonical_payload = _canonical_report_payload(report)
    if not _json_equal_strict(payload_json, canonical_payload):
        raise ValueError(
            "payload_json must match canonical paper autonomous proposal risk "
            "gate report",
        )
    return report


def _canonical_report_payload(
    report: PaperAutonomousProposalRiskGateReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload_json must recover a JSON object")
    _validate_payload_decimal_strings(payload)
    return payload


def _report_sha256(payload_json: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _mutable_json_payload(payload_json),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any, field_path: tuple[str | int, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), field_path)
    if isinstance(value, Decimal):
        if len(field_path) != 1 or field_path[0] not in _DECIMAL_PAYLOAD_FIELDS:
            raise ValueError(f"{_format_payload_path(field_path)} is not a Decimal field")
        return _fixed_six_decimal_string(_format_payload_path(field_path), value)
    if isinstance(value, datetime):
        return _as_utc(_format_payload_path(field_path), value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {
            key: _json_ready(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    raise ValueError("risk gate DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, Mapping):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _copy_json_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain raw Decimal")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain raw datetime")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_payload(item)
        return MappingProxyType(copied)
    if isinstance(value, (list, tuple)):
        return tuple(_copy_json_payload(item) for item in value)
    raise ValueError("JSON value must be a dict, list, string, int, bool, or null")


def _normalize_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    previous: str | None = None
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        normalized.append(item)
        seen.add(item)
        previous = item
    return tuple(normalized)


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, Mapping):
        return
    if any(flag_name in value for flag_name in _HARD_FLAG_NAMES):
        for flag_name in _HARD_FLAG_NAMES:
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, Mapping):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _validate_payload_decimal_strings(payload_json: Mapping[str, Any]) -> None:
    _require_json_decimal_string(
        "payload_json source_proposal_total_notional",
        payload_json.get("source_proposal_total_notional"),
    )


def _require_json_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    decimal = _decimal_from_string(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    canonical = decimal.quantize(QUANTUM)
    if value != str(canonical):
        raise ValueError(f"{field_name} must be a canonical decimal string")


def _fixed_six_decimal_string(field_name: str, value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    value_tuple = value.as_tuple()
    excess_decimal_places = -value_tuple.exponent - 6
    if excess_decimal_places > 0 and any(
        digit != 0 for digit in value_tuple.digits[-excess_decimal_places:]
    ):
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return f"{value:.6f}"


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return Decimal(_fixed_six_decimal_string(field_name, value))


def _decimal_from_string(field_name: str, value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _json_equal_strict(left: Any, right: Any) -> bool:
    if isinstance(left, Mapping):
        if not isinstance(right, Mapping):
            return False
        if left.keys() != right.keys():
            return False
        return all(_json_equal_strict(left[key], right[key]) for key in left)
    if isinstance(right, Mapping):
        return False
    if isinstance(left, (list, tuple)):
        if not isinstance(right, (list, tuple)):
            return False
        if len(left) != len(right):
            return False
        return all(
            _json_equal_strict(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(right, (list, tuple)):
        return False
    if type(left) is not type(right):
        return False
    return left == right


def _mutable_json_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _mutable_json_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mutable_json_payload(item) for item in value]
    return value


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


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_source_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be a known proposal status")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
