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
        _validate_summary_consistency(self)


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
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperTradeCostAuditReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper trade cost audit report: {exc}",
        ) from exc
    if type(report) is not PaperTradeCostAuditReport:
        raise ValueError("payload_json must recover a PaperTradeCostAuditReport")
    _require_hard_flags("report", report)
    expected_row = paper_trade_cost_audit_report_to_db_row(report)
    if row.report_sha256 != expected_row.report_sha256:
        raise ValueError("report_sha256 must match payload_json")
    if _summary_values(row) != _summary_values(expected_row):
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


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    for flag_name in ("paper_only", "report_only", "readonly"):
        if flag_name in value and value[flag_name] is not True:
            raise ValueError(f"{field_name} {flag_name} must be true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


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
