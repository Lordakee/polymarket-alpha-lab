"""Pure row codec for persisted full paper strategy cycle reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


__all__ = (
    "PaperStrategyCycleReportDbRow",
    "paper_strategy_cycle_report_from_db_row",
    "paper_strategy_cycle_report_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_MISSING = object()


@dataclass(frozen=True)
class PaperStrategyCycleReportDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    scan_market_count: int
    considered_count: int
    snapshot_ready_count: int
    cost_aware_report_count: int
    blocked_counts_json: list[list[object]]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "scan_market_count",
            "considered_count",
            "snapshot_ready_count",
            "cost_aware_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_counts_json",
            _normalize_blocked_counts_json(self.blocked_counts_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_paper_only("DB row", self)
        _require_report_only("DB row", self)
        _validate_materialized_fields_match_payload(self)
        _validate_payload_recovers_to_compatible_report(self.payload_json)


def paper_strategy_cycle_report_to_db_row(
    report: PaperStrategyCycleReport,
) -> PaperStrategyCycleReportDbRow:
    if type(report) is not PaperStrategyCycleReport:
        raise ValueError("report must be a PaperStrategyCycleReport")
    _require_paper_only("report", report)
    _require_report_only("report", report)
    payload_json = _json_ready(asdict(report))
    return PaperStrategyCycleReportDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        scan_market_count=report.scan_market_count,
        considered_count=report.considered_count,
        snapshot_ready_count=report.snapshot_ready_count,
        cost_aware_report_count=report.cost_aware_report_count,
        blocked_counts_json=_blocked_counts_json(payload_json),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def paper_strategy_cycle_report_from_db_row(
    row: PaperStrategyCycleReportDbRow,
) -> PaperStrategyCycleReport:
    if type(row) is not PaperStrategyCycleReportDbRow:
        raise ValueError("row must be a PaperStrategyCycleReportDbRow")
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_materialized_fields_match_payload(row, payload_json)
    return _validate_payload_recovers_to_compatible_report(payload_json)


def _validate_row_core_fields(row: PaperStrategyCycleReportDbRow) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    for field_name in (
        "scan_market_count",
        "considered_count",
        "snapshot_ready_count",
        "cost_aware_report_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    _normalize_blocked_counts_json(row.blocked_counts_json)
    _require_paper_only("DB row", row)
    _require_report_only("DB row", row)


def _validate_payload_recovers_to_compatible_report(
    payload_json: dict[str, Any],
) -> PaperStrategyCycleReport:
    try:
        report = from_jsonable(PaperStrategyCycleReport, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid strategy cycle report: {exc}",
        ) from exc
    if type(report) is not PaperStrategyCycleReport:
        raise ValueError("payload_json must recover a PaperStrategyCycleReport")
    _require_paper_only("report", report)
    _require_report_only("report", report)
    expected_payload_json = _json_ready(asdict(report))
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        expected_payload_json,
    )
    return report


def _validate_materialized_fields_match_payload(
    row: PaperStrategyCycleReportDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "scan_market_count": payload_json.get("scan_market_count", _MISSING),
        "considered_count": payload_json.get("considered_count", _MISSING),
        "snapshot_ready_count": payload_json.get(
            "snapshot_ready_count",
            _MISSING,
        ),
        "cost_aware_report_count": payload_json.get(
            "cost_aware_report_count",
            _MISSING,
        ),
        "blocked_counts_json": payload_json.get("blocked_counts", _MISSING),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": _as_utc("generated_at", row.generated_at).isoformat(),
        "config_version": row.config_version,
        "scan_market_count": row.scan_market_count,
        "considered_count": row.considered_count,
        "snapshot_ready_count": row.snapshot_ready_count,
        "cost_aware_report_count": row.cost_aware_report_count,
        "blocked_counts_json": _normalize_blocked_counts_json(
            row.blocked_counts_json,
        ),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
    }
    for field_name, actual_value in actual_values.items():
        _require_json_exact_match(
            field_name,
            actual_value,
            expected_values[field_name],
        )


def _require_json_exact_match(
    field_name: str,
    actual_value: object,
    expected_value: object,
) -> None:
    if type(actual_value) is not type(expected_value) or actual_value != expected_value:
        raise ValueError(f"{field_name} must match payload_json")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _blocked_counts_json(payload_json: dict[str, Any]) -> list[list[object]]:
    try:
        return _normalize_blocked_counts_json(payload_json["blocked_counts"])
    except KeyError as exc:
        raise ValueError("payload_json blocked_counts is required") from exc


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
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("strategy cycle report DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    _validate_json_flags(normalized, field_name)
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


def _decimal_to_json(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("JSON Decimal value must be finite")
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


def _normalize_blocked_counts_json(value: object) -> list[list[object]]:
    if not isinstance(value, list):
        raise ValueError("blocked_counts_json must be a list of lists")
    normalized: list[list[object]] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("blocked_counts_json entries must be [status, count]")
        status, count = item
        _require_canonical_string("blocked_counts_json status", status)
        _require_positive_int("blocked_counts_json count", count)
        normalized.append([status, count])
    statuses = [status for status, _count in normalized]
    if len(set(statuses)) != len(statuses):
        raise ValueError("blocked_counts_json statuses must be unique")
    if statuses != sorted(statuses):
        raise ValueError("blocked_counts_json must be sorted by status")
    return normalized


def _validate_payload_compatible_with_canonical_payload(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    try:
        _validate_json_compatible((), payload_json, expected_payload_json)
    except ValueError as exc:
        raise ValueError(
            f"payload_json must match canonical strategy cycle report: {exc}",
        ) from exc


def _validate_json_compatible(
    path: tuple[str, ...],
    actual: object,
    expected: object,
) -> None:
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


def _validate_json_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if "paper_only" in value and value.get("paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be present and true")
    if "report_only" in value and value.get("report_only") is not True:
        raise ValueError(f"{field_name} report_only must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_flags(element, f"{child_name} {index}")


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


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_paper_only(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")


def _require_report_only(field_name: str, value: object) -> None:
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
