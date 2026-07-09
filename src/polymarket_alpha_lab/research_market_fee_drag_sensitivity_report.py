"""Pure report-only fee drag sensitivity report for manual research edge."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION",
    "FEE_DRAG_SENSITIVITY_STATUSES",
    "ResearchMarketFeeDragSensitivityConfig",
    "ResearchMarketFeeDragSensitivityInput",
    "ResearchMarketFeeDragSensitivityReasonCodeCount",
    "ResearchMarketFeeDragSensitivityReport",
    "ResearchMarketFeeDragSensitivityRow",
    "build_research_market_fee_drag_sensitivity_report",
    "research_market_fee_drag_sensitivity_report_payload",
    "validate_research_market_fee_drag_sensitivity_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION = (
    "research-market-fee-drag-sensitivity-report-v0"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
FEE_DRAG_SENSITIVITY_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

UNSAFE_PUBLIC_TERMS = (
    "://",
    "@",
    "?",
    "=",
    "api" "_" "key",
    "au" "th",
    "dsn",
    "live",
    "market" "_" "id",
    "market" "_" "slug",
    "order",
    "position",
    "private" "_" "key",
    "question",
    "raw" "_" "candidate" "_" "id",
    "reco" "mmend",
    "secret",
    "siz" "ing",
    "size",
    "table" "_" "name",
    "token",
    "tra" "de",
    "url",
    "wal" "let",
)


@dataclass(frozen=True)
class ResearchMarketFeeDragSensitivityConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION
    base_manual_edge_rate: Decimal = Decimal("0.020000")
    watch_minimum_edge_needed_rate: Decimal = Decimal("0.060000")
    block_minimum_edge_needed_rate: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragSensitivityConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "base_manual_edge_rate",
            "watch_minimum_edge_needed_rate",
            "block_minimum_edge_needed_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.base_manual_edge_rate > self.watch_minimum_edge_needed_rate:
            raise ValueError("base_manual_edge_rate must not exceed watch threshold")
        if self.block_minimum_edge_needed_rate <= self.watch_minimum_edge_needed_rate:
            raise ValueError(
                "block_minimum_edge_needed_rate must exceed "
                "watch_minimum_edge_needed_rate",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeDragSensitivityInput:
    raw_candidate_id: str
    fee_rate: Decimal
    spread_rate: Decimal
    slippage_rate: Decimal
    settlement_friction_rate: Decimal
    confidence_haircut_rate: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragSensitivityInput, "input")
        _require_raw_reference("raw_candidate_id", self.raw_candidate_id)
        for field_name in (
            "fee_rate",
            "spread_rate",
            "slippage_rate",
            "settlement_friction_rate",
            "confidence_haircut_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes, allow_empty=True),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketFeeDragSensitivityRow:
    candidate_digest: str
    fee_rate: Decimal
    spread_rate: Decimal
    slippage_rate: Decimal
    settlement_friction_rate: Decimal
    confidence_haircut_rate: Decimal
    total_friction_rate: Decimal
    base_manual_edge_rate: Decimal
    minimum_edge_needed_rate: Decimal
    manual_research_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragSensitivityRow, "row")
        _require_sha256_digest("candidate_digest", self.candidate_digest)
        for field_name in (
            "fee_rate",
            "spread_rate",
            "slippage_rate",
            "settlement_friction_rate",
            "confidence_haircut_rate",
            "total_friction_rate",
            "base_manual_edge_rate",
            "minimum_edge_needed_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("manual_research_status", self.manual_research_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        if f"fee_drag_status_{self.manual_research_status}" not in self.reason_codes:
            raise ValueError("manual_research_status must match reason_codes")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketFeeDragSensitivityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeDragSensitivityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_identifier("reason_code", self.reason_code)
        if _contains_unsafe_public_term(self.reason_code):
            raise ValueError("reason_code has unsafe public payload")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketFeeDragSensitivityReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    base_manual_edge_rate: Decimal
    max_minimum_edge_needed_rate: Decimal
    average_minimum_edge_needed_rate: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeDragSensitivityReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeDragSensitivityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragSensitivityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "base_manual_edge_rate",
            "max_minimum_edge_needed_rate",
            "average_minimum_edge_needed_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )


def build_research_market_fee_drag_sensitivity_report(
    inputs: Iterable[ResearchMarketFeeDragSensitivityInput],
    *,
    config: ResearchMarketFeeDragSensitivityConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDragSensitivityReport:
    if type(config) is not ResearchMarketFeeDragSensitivityConfig:
        raise ValueError("config must be a ResearchMarketFeeDragSensitivityConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketFeeDragSensitivityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        base_manual_edge_rate=config.base_manual_edge_rate,
        max_minimum_edge_needed_rate=_max_row_decimal(rows, "minimum_edge_needed_rate"),
        average_minimum_edge_needed_rate=_average_row_decimal(
            rows,
            "minimum_edge_needed_rate",
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_drag_sensitivity_report_payload(
    report: ResearchMarketFeeDragSensitivityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeDragSensitivityReport:
        raise ValueError("report must be a ResearchMarketFeeDragSensitivityReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_drag_sensitivity_report_payload(payload)
    return payload


def validate_research_market_fee_drag_sensitivity_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    value: ResearchMarketFeeDragSensitivityInput,
    *,
    config: ResearchMarketFeeDragSensitivityConfig,
) -> ResearchMarketFeeDragSensitivityRow:
    total_friction_rate = _sum_rates(
        value.fee_rate,
        value.spread_rate,
        value.slippage_rate,
        value.settlement_friction_rate,
        value.confidence_haircut_rate,
    )
    minimum_edge_needed_rate = _quantize_decimal(
        config.base_manual_edge_rate + total_friction_rate,
    )
    status = _row_status(minimum_edge_needed_rate, config=config)
    return ResearchMarketFeeDragSensitivityRow(
        candidate_digest=_candidate_digest(value.raw_candidate_id),
        fee_rate=value.fee_rate,
        spread_rate=value.spread_rate,
        slippage_rate=value.slippage_rate,
        settlement_friction_rate=value.settlement_friction_rate,
        confidence_haircut_rate=value.confidence_haircut_rate,
        total_friction_rate=total_friction_rate,
        base_manual_edge_rate=config.base_manual_edge_rate,
        minimum_edge_needed_rate=minimum_edge_needed_rate,
        manual_research_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            fee_rate=value.fee_rate,
            spread_rate=value.spread_rate,
            slippage_rate=value.slippage_rate,
            settlement_friction_rate=value.settlement_friction_rate,
            confidence_haircut_rate=value.confidence_haircut_rate,
            status=status,
        ),
    )


def _row_status(
    minimum_edge_needed_rate: Decimal,
    *,
    config: ResearchMarketFeeDragSensitivityConfig,
) -> str:
    if minimum_edge_needed_rate >= config.block_minimum_edge_needed_rate:
        return BLOCK_STATUS
    if minimum_edge_needed_rate >= config.watch_minimum_edge_needed_rate:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    fee_rate: Decimal,
    spread_rate: Decimal,
    slippage_rate: Decimal,
    settlement_friction_rate: Decimal,
    confidence_haircut_rate: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in upstream_reason_codes]
    if fee_rate > ZERO:
        reason_codes.append("fee_drag_fee_component")
    if spread_rate > ZERO:
        reason_codes.append("fee_drag_spread_component")
    if slippage_rate > ZERO:
        reason_codes.append("fee_drag_slippage_component")
    if settlement_friction_rate > ZERO:
        reason_codes.append("fee_drag_settlement_friction_component")
    if confidence_haircut_rate > ZERO:
        reason_codes.append("fee_drag_confidence_haircut_component")
    if status == WATCH_STATUS:
        reason_codes.append("fee_drag_minimum_edge_watch")
    if status == BLOCK_STATUS:
        reason_codes.append("fee_drag_minimum_edge_block")
    reason_codes.append(f"fee_drag_status_{status}")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _normalize_inputs(
    inputs: Iterable[ResearchMarketFeeDragSensitivityInput],
) -> tuple[ResearchMarketFeeDragSensitivityInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketFeeDragSensitivityInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeDragSensitivityInput",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketFeeDragSensitivityRow],
) -> tuple[ResearchMarketFeeDragSensitivityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketFeeDragSensitivityRow:
            raise ValueError("rows must contain ResearchMarketFeeDragSensitivityRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketFeeDragSensitivityReasonCodeCount],
) -> tuple[ResearchMarketFeeDragSensitivityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketFeeDragSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeDragSensitivityReasonCodeCount",
            )
        _require_hard_flags(count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_report_consistency(report: ResearchMarketFeeDragSensitivityReport) -> None:
    for row in report.rows:
        if row.total_friction_rate != _sum_rates(
            row.fee_rate,
            row.spread_rate,
            row.slippage_rate,
            row.settlement_friction_rate,
            row.confidence_haircut_rate,
        ):
            raise ValueError("total_friction_rate must match row components")
        if row.minimum_edge_needed_rate != _quantize_decimal(
            row.base_manual_edge_rate + row.total_friction_rate,
        ):
            raise ValueError("minimum_edge_needed_rate must match row friction")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.max_minimum_edge_needed_rate != _max_row_decimal(
        report.rows,
        "minimum_edge_needed_rate",
    ):
        raise ValueError("max_minimum_edge_needed_rate must match rows")
    if report.average_minimum_edge_needed_rate != _average_row_decimal(
        report.rows,
        "minimum_edge_needed_rate",
    ):
        raise ValueError("average_minimum_edge_needed_rate must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketFeeDragSensitivityRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.manual_research_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.manual_research_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeDragSensitivityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("fee_drag_sensitivity_report_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketFeeDragSensitivityRow, ...],
) -> tuple[ResearchMarketFeeDragSensitivityReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketFeeDragSensitivityReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketFeeDragSensitivityRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.manual_research_status == status))


def _max_row_decimal(
    rows: tuple[ResearchMarketFeeDragSensitivityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketFeeDragSensitivityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _sum_rates(*values: Decimal) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    return total


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_raw_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FEE_DRAG_SENSITIVITY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _normalize_reason_codes(
    reason_codes: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    _require_payload_hard_flags_at(value, "payload")


def _require_payload_hard_flags_at(value: object, path: str) -> None:
    if isinstance(value, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in value and value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True at {path}")
        for key, item in value.items():
            _require_payload_hard_flags_at(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_payload_hard_flags_at(item, f"{path}[{index}]")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _row_sort_key(
    row: ResearchMarketFeeDragSensitivityRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.manual_research_status],
        -row.minimum_edge_needed_rate,
        row.candidate_digest,
    )


def _candidate_digest(raw_candidate_id: str) -> str:
    return hashlib.sha256(raw_candidate_id.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketFeeDragSensitivityReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketFeeDragSensitivityReport,
) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived_validation_digest payload", digest_payload)
    encoded_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _reject_unsafe_public_payload(value_label: str, value: object, path: str = "") -> None:
    current_path = path or value_label
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(value_label, asdict(value), current_path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{value_label} has unsafe public payload")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"{value_label} has unsafe public payload at {current_path}")
            _reject_unsafe_public_payload(value_label, item, f"{current_path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(value_label, item, f"{current_path}[{index}]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(value_label, item, f"{current_path}[{index}]")
        return
    if type(value) is str and _contains_unsafe_public_term(value):
        raise ValueError(f"{value_label} has unsafe public payload at {current_path}")


def _json_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value
