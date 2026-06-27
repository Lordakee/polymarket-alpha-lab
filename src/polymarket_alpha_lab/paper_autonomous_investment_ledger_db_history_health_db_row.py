"""Pure row codec for paper autonomous investment ledger DB-history health reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    HEALTH_STATUSES,
    NEXT_STEP_BY_STATUS,
    PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
)


__all__ = (
    "PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow",
    "from_db_row",
    "paper_autonomous_investment_ledger_db_history_health_report_from_db_row",
    "paper_autonomous_investment_ledger_db_history_health_report_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_REPORT_DECIMAL_PAYLOAD_FIELDS = frozenset(("latest_total_submitted_notional",))


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    health_status: str
    recommended_next_step: str
    ledger_report_count: int
    pass_ledger_report_count: int
    watch_ledger_report_count: int
    blocked_ledger_report_count: int
    latest_ledger_status: str | None
    latest_source_record_count: int | None
    latest_submitted_count: int | None
    latest_held_count: int | None
    latest_blocked_count: int | None
    latest_total_submitted_notional: Decimal | None
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    max_source_age_seconds: int | None
    duplicate_latest_generated_at_count: int
    reason_code_counts_json: list[dict[str, Any]]
    reason_codes_json: list[str]
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
        _require_health_status("health_status", self.health_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_status_next_step(self.health_status, self.recommended_next_step)
        for field_name in (
            "ledger_report_count",
            "pass_ledger_report_count",
            "watch_ledger_report_count",
            "blocked_ledger_report_count",
            "duplicate_latest_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.ledger_report_count != (
            self.pass_ledger_report_count
            + self.watch_ledger_report_count
            + self.blocked_ledger_report_count
        ):
            raise ValueError("ledger_report_count must equal status counts")
        if self.latest_ledger_status is not None:
            _require_ledger_status("latest_ledger_status", self.latest_ledger_status)
        for field_name in (
            "latest_source_record_count",
            "latest_submitted_count",
            "latest_held_count",
            "latest_blocked_count",
            "latest_source_age_seconds",
            "max_source_age_seconds",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_total_submitted_notional",
            _require_optional_nonnegative_decimal(
                "latest_total_submitted_notional",
                self.latest_total_submitted_notional,
            ),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc(
                "latest_source_generated_at",
                self.latest_source_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_json_object_array(
                "reason_code_counts_json",
                self.reason_code_counts_json,
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
        _validate_reason_code_counts_hard_flags(
            "reason_code_counts_json",
            self.reason_code_counts_json,
        )
        _require_hard_flags("DB-history health DB row", self)
        _validate_materialized_fields_match_payload(self)


def paper_autonomous_investment_ledger_db_history_health_report_to_db_row(
    report: Any,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow:
    if type(report) is not PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
        raise ValueError(
            "report must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_codes_json = payload_json.get("reason_codes")
    reason_code_counts_json = payload_json.get("reason_code_counts")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    if not isinstance(reason_code_counts_json, list):
        raise ValueError("payload_json reason_code_counts must be a JSON array")
    return PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        health_status=report.health_status,
        recommended_next_step=report.recommended_next_step,
        ledger_report_count=report.ledger_report_count,
        pass_ledger_report_count=report.pass_ledger_report_count,
        watch_ledger_report_count=report.watch_ledger_report_count,
        blocked_ledger_report_count=report.blocked_ledger_report_count,
        latest_ledger_status=report.latest_ledger_status,
        latest_source_record_count=report.latest_source_record_count,
        latest_submitted_count=report.latest_submitted_count,
        latest_held_count=report.latest_held_count,
        latest_blocked_count=report.latest_blocked_count,
        latest_total_submitted_notional=report.latest_total_submitted_notional,
        latest_source_generated_at=report.latest_source_generated_at,
        latest_source_age_seconds=report.latest_source_age_seconds,
        max_source_age_seconds=report.max_source_age_seconds,
        duplicate_latest_generated_at_count=(
            report.duplicate_latest_generated_at_count
        ),
        reason_code_counts_json=reason_code_counts_json,
        reason_codes_json=reason_codes_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_investment_ledger_db_history_health_report_from_db_row(
    row: PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
    if type(row) is not PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow:
        raise ValueError(
            "row must be a PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow",
        )
    _reject_raw_json_values(row.reason_code_counts_json, "reason_code_counts_json")
    _reject_raw_json_values(row.reason_codes_json, "reason_codes_json")
    _reject_raw_json_values(row.payload_json, "payload_json")
    _validate_raw_payload_hash(row)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_payload_reason_code_counts_hard_flags(row.payload_json)
    payload_json = _normalize_legacy_decimal_payload(row.payload_json)
    _validate_materialized_fields_match_payload(row, payload_json)
    try:
        report = from_jsonable(
            PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid DB-history health report: " f"{exc}",
        ) from exc
    if type(report) is not PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthReport",
        )
    _validate_report_tree(report)
    expected_row = (
        paper_autonomous_investment_ledger_db_history_health_report_to_db_row(
            report,
        )
    )
    _validate_row_matches_payload(row, expected_row, compare_report_sha256=False)
    return report


def to_db_row(report: Any) -> PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow:
    return paper_autonomous_investment_ledger_db_history_health_report_to_db_row(
        report,
    )


def from_db_row(
    row: PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
    return paper_autonomous_investment_ledger_db_history_health_report_from_db_row(
        row,
    )


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
    row: PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow,
    expected: PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow,
    *,
    compare_report_sha256: bool = True,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if field_name == "report_sha256" and not compare_report_sha256:
            continue
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    raw_payload_json = row.payload_json
    if payload_json is None:
        payload_json = _normalize_legacy_decimal_payload(raw_payload_json)
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    if row.report_sha256 != _report_sha256(raw_payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(raw_payload_json, "payload_json")
    _validate_payload_reason_code_counts_hard_flags(raw_payload_json)

    actual_values: dict[str, Any] = {}
    expected_values: dict[str, Any] = {}

    for field_name in _PAYLOAD_SCALAR_FIELDS:
        actual_values[field_name] = _json_ready_field(
            field_name,
            getattr(row, field_name),
        )
        expected_values[field_name] = _payload_value(payload_json, field_name)

    for row_field_name, payload_field_name in _PAYLOAD_JSON_FIELDS:
        actual_values[row_field_name] = _json_ready_field(
            row_field_name,
            getattr(row, row_field_name),
        )
        expected_values[row_field_name] = _payload_value(
            payload_json,
            payload_field_name,
        )

    for field_name in actual_values:
        if not _json_values_equal(actual_values[field_name], expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _payload_value(payload_json: dict[str, Any], field_name: str) -> Any:
    if field_name not in payload_json:
        return _MISSING_PAYLOAD_VALUE
    return payload_json[field_name]


def _json_ready_field(field_name: str, value: Any) -> Any:
    try:
        return _json_ready(value, (field_name,))
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc


def _json_values_equal(left: Any, right: Any) -> bool:
    if left is _MISSING_PAYLOAD_VALUE or right is _MISSING_PAYLOAD_VALUE:
        return left is right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return False
        return all(_json_values_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(
            _json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _validate_payload_reason_code_counts_hard_flags(
    payload_json: dict[str, Any],
) -> None:
    reason_code_counts = _payload_value(payload_json, "reason_code_counts")
    if reason_code_counts is _MISSING_PAYLOAD_VALUE:
        return
    _validate_reason_code_counts_hard_flags(
        "payload_json reason_code_counts",
        reason_code_counts,
    )


def _validate_reason_code_counts_hard_flags(
    field_name: str,
    value: Any,
) -> None:
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        if not _is_reason_code_count_object(item):
            continue
        _require_json_hard_flags(f"{field_name} {index}", item)


def _is_reason_code_count_object(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and type(value.get("reason_code")) is str
        and type(value.get("report_count")) is int
    )


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_raw_payload_hash(
    row: PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow,
) -> None:
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")


def _json_ready(value: Any, field_path: tuple[str | int, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), field_path)
    if isinstance(value, Decimal):
        if not _is_report_decimal_payload_path(field_path):
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
            key: _json_ready(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    raise ValueError("DB-history health DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_raw_json_values(value, field_name)
    except ValueError as exc:
        raise ValueError(f"{field_name} must contain only JSON-safe values") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_raw_json_values(value, field_name)
    except ValueError as exc:
        raise ValueError(f"{field_name} must contain only JSON-safe values") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return normalized


def _normalize_legacy_decimal_payload(
    value: Any,
    field_path: tuple[str | int, ...] = (),
) -> Any:
    if _is_report_decimal_payload_path(field_path):
        field_name = _format_payload_path(field_path)
        if value is None:
            return None
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal string or null")
        return _fixed_six_decimal_string(
            field_name,
            _decimal_from_string(field_name, value),
        )
    if _looks_like_fixed_six_decimal_string(value):
        raise ValueError(
            f"{_format_payload_path(field_path)} is not an allowed Decimal path",
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


def _is_report_decimal_payload_path(field_path: tuple[str | int, ...]) -> bool:
    return len(field_path) == 1 and field_path[0] in _REPORT_DECIMAL_PAYLOAD_FIELDS


def _fixed_six_decimal_string(field_name: str, value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if -value.as_tuple().exponent > 6:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return f"{value:.6f}"


def _decimal_from_string(field_name: str, value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _looks_like_fixed_six_decimal_string(value: Any) -> bool:
    if type(value) is not str:
        return False
    if not re.fullmatch(r"[+-]?\d+\.\d+", value):
        return False
    try:
        Decimal(value)
    except ArithmeticError:
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


def _normalize_string_list(field_name: str, value: object) -> list[str]:
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
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly")):
        _require_json_hard_flags(field_name, value)
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _require_json_hard_flags(field_name: str, value: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


def _reject_raw_json_values(value: Any, field_name: str) -> None:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not be a raw Decimal")
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must not be a raw datetime")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_raw_json_values(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_raw_json_values(item, f"{field_name}[{index}]")


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
        raise ValueError(f"{field_name} must be timezone-aware")
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


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_ledger_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_status_next_step(status: str, next_step: str) -> None:
    expected = NEXT_STEP_BY_STATUS[status]
    if next_step != expected:
        raise ValueError("recommended_next_step must match health_status")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    decimal = _require_fixed_six_decimal(field_name, value)
    if decimal < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _require_fixed_six_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal = Decimal(_fixed_six_decimal_string(field_name, value))
    if decimal != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return decimal


_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "health_status",
    "recommended_next_step",
    "ledger_report_count",
    "pass_ledger_report_count",
    "watch_ledger_report_count",
    "blocked_ledger_report_count",
    "latest_ledger_status",
    "latest_source_record_count",
    "latest_submitted_count",
    "latest_held_count",
    "latest_blocked_count",
    "latest_total_submitted_notional",
    "latest_source_generated_at",
    "latest_source_age_seconds",
    "max_source_age_seconds",
    "duplicate_latest_generated_at_count",
    "reason_code_counts_json",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)

_PAYLOAD_SCALAR_FIELDS = (
    "generated_at",
    "config_version",
    "health_status",
    "recommended_next_step",
    "ledger_report_count",
    "pass_ledger_report_count",
    "watch_ledger_report_count",
    "blocked_ledger_report_count",
    "latest_ledger_status",
    "latest_source_record_count",
    "latest_submitted_count",
    "latest_held_count",
    "latest_blocked_count",
    "latest_total_submitted_notional",
    "latest_source_generated_at",
    "latest_source_age_seconds",
    "max_source_age_seconds",
    "duplicate_latest_generated_at_count",
    "paper_only",
    "report_only",
    "readonly",
)

_PAYLOAD_JSON_FIELDS = (
    ("reason_code_counts_json", "reason_code_counts"),
    ("reason_codes_json", "reason_codes"),
)

_MISSING_PAYLOAD_VALUE = object()
