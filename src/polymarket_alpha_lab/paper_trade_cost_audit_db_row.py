"""Pure row codec for persisted paper trade cost audit reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport


__all__ = (
    "PaperTradeCostAuditReportDbRow",
    "paper_trade_cost_audit_report_from_db_row",
    "paper_trade_cost_audit_report_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
_MISSING = object()
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_JSON_INTEGER_FIELDS = frozenset(
    {
        "trade_count",
        "partial_fill_count",
        "negative_cost_adjusted_edge_count",
    },
)
_JSON_DECIMAL_FIELDS = frozenset(
    {
        "total_filled_size",
        "total_requested_size",
        "fill_rate",
        "mean_theoretical_edge",
        "mean_cost_adjusted_edge",
        "mean_edge_cost_drag",
        "total_edge_cost_drag",
        "mean_research_slippage",
        "mean_fill_slippage",
        "largest_single_trade_cost_drag",
    },
)
_JSON_QUANTIZED_DECIMAL_FIELDS = frozenset(
    {
        "fill_rate",
        "mean_theoretical_edge",
        "mean_cost_adjusted_edge",
        "mean_edge_cost_drag",
        "total_edge_cost_drag",
        "mean_research_slippage",
        "mean_fill_slippage",
        "largest_single_trade_cost_drag",
    },
)


@dataclass(frozen=True)
class PaperTradeCostAuditReportDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    trade_count: int
    total_filled_size: Decimal
    total_requested_size: Decimal
    fill_rate: Decimal | None
    mean_theoretical_edge: Decimal | None
    mean_cost_adjusted_edge: Decimal | None
    mean_edge_cost_drag: Decimal | None
    total_edge_cost_drag: Decimal | None
    mean_research_slippage: Decimal | None
    mean_fill_slippage: Decimal | None
    partial_fill_count: int
    negative_cost_adjusted_edge_count: int
    largest_single_trade_cost_drag: Decimal | None
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
        for field_name in (
            "trade_count",
            "partial_fill_count",
            "negative_cost_adjusted_edge_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_filled_size",
            "total_requested_size",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_optional_probability_decimal("fill_rate", self.fill_rate)
        for field_name in (
            "mean_theoretical_edge",
            "mean_cost_adjusted_edge",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "mean_edge_cost_drag",
            "total_edge_cost_drag",
            "mean_research_slippage",
            "mean_fill_slippage",
            "largest_single_trade_cost_drag",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
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
        _validate_payload_recovers_to_canonical_report(self.payload_json)


def paper_trade_cost_audit_report_to_db_row(
    report: PaperTradeCostAuditReport,
) -> PaperTradeCostAuditReportDbRow:
    if type(report) is not PaperTradeCostAuditReport:
        raise ValueError("report must be a PaperTradeCostAuditReport")
    _require_hard_flags("report", report)
    payload_json = _json_ready(asdict(report))
    return PaperTradeCostAuditReportDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        trade_count=report.trade_count,
        total_filled_size=report.total_filled_size,
        total_requested_size=report.total_requested_size,
        fill_rate=report.fill_rate,
        mean_theoretical_edge=report.mean_theoretical_edge,
        mean_cost_adjusted_edge=report.mean_cost_adjusted_edge,
        mean_edge_cost_drag=report.mean_edge_cost_drag,
        total_edge_cost_drag=report.total_edge_cost_drag,
        mean_research_slippage=report.mean_research_slippage,
        mean_fill_slippage=report.mean_fill_slippage,
        partial_fill_count=report.partial_fill_count,
        negative_cost_adjusted_edge_count=report.negative_cost_adjusted_edge_count,
        largest_single_trade_cost_drag=report.largest_single_trade_cost_drag,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_trade_cost_audit_report_from_db_row(
    row: PaperTradeCostAuditReportDbRow,
) -> PaperTradeCostAuditReport:
    if type(row) is not PaperTradeCostAuditReportDbRow:
        raise ValueError("row must be a PaperTradeCostAuditReportDbRow")
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
    expected_row = paper_trade_cost_audit_report_to_db_row(report)
    if not _json_values_match(_summary_values(row), _summary_values(expected_row)):
        raise ValueError("summary columns must match payload_json")
    return report


def _summary_values(row: PaperTradeCostAuditReportDbRow) -> tuple[Any, ...]:
    return (
        row.generated_at,
        row.config_version,
        row.trade_count,
        row.total_filled_size,
        row.total_requested_size,
        row.fill_rate,
        row.mean_theoretical_edge,
        row.mean_cost_adjusted_edge,
        row.mean_edge_cost_drag,
        row.total_edge_cost_drag,
        row.mean_research_slippage,
        row.mean_fill_slippage,
        row.partial_fill_count,
        row.negative_cost_adjusted_edge_count,
        row.largest_single_trade_cost_drag,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _validate_materialized_fields_match_payload(
    row: PaperTradeCostAuditReportDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "trade_count": payload_json.get("trade_count", _MISSING),
        "total_filled_size": payload_json.get("total_filled_size", _MISSING),
        "total_requested_size": payload_json.get("total_requested_size", _MISSING),
        "fill_rate": payload_json.get("fill_rate", _MISSING),
        "mean_theoretical_edge": payload_json.get("mean_theoretical_edge", _MISSING),
        "mean_cost_adjusted_edge": payload_json.get(
            "mean_cost_adjusted_edge",
            _MISSING,
        ),
        "mean_edge_cost_drag": payload_json.get("mean_edge_cost_drag", _MISSING),
        "total_edge_cost_drag": payload_json.get("total_edge_cost_drag", _MISSING),
        "mean_research_slippage": payload_json.get(
            "mean_research_slippage",
            _MISSING,
        ),
        "mean_fill_slippage": payload_json.get("mean_fill_slippage", _MISSING),
        "partial_fill_count": payload_json.get("partial_fill_count", _MISSING),
        "negative_cost_adjusted_edge_count": payload_json.get(
            "negative_cost_adjusted_edge_count",
            _MISSING,
        ),
        "largest_single_trade_cost_drag": payload_json.get(
            "largest_single_trade_cost_drag",
            _MISSING,
        ),
        "paper_only": payload_json.get("paper_only", _MISSING),
        "report_only": payload_json.get("report_only", _MISSING),
        "readonly": payload_json.get("readonly", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "trade_count": row.trade_count,
        "total_filled_size": _json_ready(row.total_filled_size),
        "total_requested_size": _json_ready(row.total_requested_size),
        "fill_rate": _json_ready(row.fill_rate),
        "mean_theoretical_edge": _json_ready(row.mean_theoretical_edge),
        "mean_cost_adjusted_edge": _json_ready(row.mean_cost_adjusted_edge),
        "mean_edge_cost_drag": _json_ready(row.mean_edge_cost_drag),
        "total_edge_cost_drag": _json_ready(row.total_edge_cost_drag),
        "mean_research_slippage": _json_ready(row.mean_research_slippage),
        "mean_fill_slippage": _json_ready(row.mean_fill_slippage),
        "partial_fill_count": row.partial_fill_count,
        "negative_cost_adjusted_edge_count": row.negative_cost_adjusted_edge_count,
        "largest_single_trade_cost_drag": _json_ready(
            row.largest_single_trade_cost_drag,
        ),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name, actual_value in actual_values.items():
        if not _json_values_match(actual_value, expected_values[field_name]):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_payload_recovers_to_canonical_report(
    payload_json: dict[str, Any],
) -> PaperTradeCostAuditReport:
    try:
        report = from_jsonable(PaperTradeCostAuditReport, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper trade cost audit report: {exc}",
        ) from exc
    if type(report) is not PaperTradeCostAuditReport:
        raise ValueError("payload_json must recover a PaperTradeCostAuditReport")
    _require_hard_flags("report", report)
    if not _json_values_match(payload_json, _canonical_report_payload(report)):
        raise ValueError("payload_json must be canonical")
    return report


def _canonical_report_payload(report: PaperTradeCostAuditReport) -> dict[str, Any]:
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


def _validate_summary_consistency(row: PaperTradeCostAuditReportDbRow) -> None:
    if row.total_filled_size > row.total_requested_size:
        raise ValueError("total_filled_size must not exceed total_requested_size")
    if row.partial_fill_count > row.trade_count:
        raise ValueError("partial_fill_count cannot exceed trade_count")
    if row.negative_cost_adjusted_edge_count > row.trade_count:
        raise ValueError("negative_cost_adjusted_edge_count cannot exceed trade_count")
    if row.trade_count == 0:
        for field_name in (
            "total_filled_size",
            "total_requested_size",
        ):
            if getattr(row, field_name) != ZERO:
                raise ValueError(f"{field_name} must be zero")
        for field_name in (
            "fill_rate",
            "mean_theoretical_edge",
            "mean_cost_adjusted_edge",
            "mean_edge_cost_drag",
            "total_edge_cost_drag",
            "mean_research_slippage",
            "mean_fill_slippage",
            "largest_single_trade_cost_drag",
        ):
            if getattr(row, field_name) is not None:
                raise ValueError(f"{field_name} must be None")
        if row.partial_fill_count != 0:
            raise ValueError("partial_fill_count must be zero")
        if row.negative_cost_adjusted_edge_count != 0:
            raise ValueError("negative_cost_adjusted_edge_count must be zero")
        return
    _require_positive_decimal("total_requested_size", row.total_requested_size)
    _require_positive_decimal("total_filled_size", row.total_filled_size)
    for field_name in (
        "fill_rate",
        "mean_theoretical_edge",
        "mean_cost_adjusted_edge",
        "mean_edge_cost_drag",
        "total_edge_cost_drag",
        "mean_research_slippage",
        "largest_single_trade_cost_drag",
    ):
        _require_present(field_name, getattr(row, field_name))
    expected_fill_rate = _quantize_ratio(row.total_filled_size / row.total_requested_size)
    if row.fill_rate != expected_fill_rate:
        raise ValueError("fill_rate must match filled and requested size")


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
    raise ValueError("paper trade cost audit DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = {key: _json_ready(item) for key, item in value.items()}
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    _reject_json_floats(normalized)
    _validate_json_hard_flags(normalized, field_name)
    return normalized


def _validate_payload_integer_fields(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_INTEGER_FIELDS:
                _require_json_nonnegative_int(child_name, item)
            else:
                _validate_payload_integer_fields(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_integer_fields(item, f"{field_name} {index}")


def _require_json_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _validate_payload_decimal_strings(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child_name = f"{field_name} {key}"
            if key in _JSON_DECIMAL_FIELDS and item is not None:
                _require_canonical_decimal_json_string(
                    child_name,
                    item,
                    quantized=key in _JSON_QUANTIZED_DECIMAL_FIELDS,
                )
            _validate_payload_decimal_strings(item, child_name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_decimal_strings(item, f"{field_name} {index}")


def _require_canonical_decimal_json_string(
    field_name: str,
    value: object,
    *,
    quantized: bool,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal string")
    canonical = decimal.quantize(RATIO_QUANTUM) if quantized else decimal
    if value != str(canonical):
        raise ValueError(f"{field_name} must be canonical")


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if _looks_like_report_payload(
        value,
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


def _looks_like_report_payload(value: dict[str, Any]) -> bool:
    return (
        "generated_at" in value
        and "config_version" in value
        and (
            "reason_codes" in value
            or "trade_count" in value
            or "paper_only" in value
            or "report_only" in value
            or "readonly" in value
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
    if not isinstance(value, datetime):
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


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_positive_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_present(field_name: str, value: object) -> None:
    if value is None:
        raise ValueError(f"{field_name} is required when trade_count is positive")


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
