"""Pure report-only market cost regime shift alert report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "COST_REGIME_SHIFT_ALERT_STATUSES",
    "DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION",
    "ResearchMarketCostRegimeShiftAlertConfig",
    "ResearchMarketCostRegimeShiftAlertInput",
    "ResearchMarketCostRegimeShiftAlertReasonCodeCount",
    "ResearchMarketCostRegimeShiftAlertReport",
    "ResearchMarketCostRegimeShiftAlertRow",
    "build_research_market_cost_regime_shift_alert_report",
    "research_market_cost_regime_shift_alert_report_payload",
    "validate_research_market_cost_regime_shift_alert_report_payload",
)


DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION = (
    "research-market-cost-regime-shift-alert-report-v0"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COST_REGIME_SHIFT_ALERT_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
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
    "candidate",
    "candidate" "_" "id",
    "dsn",
    "live",
    "market" "_" "id",
    "market" "-" "id",
    "market" "." "id",
    "market" "_" "slug",
    "market" "-" "slug",
    "market" "." "slug",
    "order",
    "private" "_" "key",
    "question",
    "raw" "_" "candidate" "_" "id",
    "recommendation",
    "secret",
    "sizing",
    "source" "_" "text",
    "source" "-" "text",
    "source" "." "text",
    "source" "_" "url",
    "source" "-" "url",
    "source" "." "url",
    "table" "_" "name",
    "table" "-" "name",
    "table" "." "name",
    "token",
    "tra" "de",
    "url",
    "wal" "let",
)
REPORT_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "status",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_current_total_cost_rate",
        "max_cost_increase_rate",
        "average_cost_increase_rate",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
ROW_PAYLOAD_KEYS = frozenset(
    {
        "case_digest",
        "baseline_spread_rate",
        "current_spread_rate",
        "baseline_depth_impact_rate",
        "current_depth_impact_rate",
        "baseline_slippage_rate",
        "current_slippage_rate",
        "baseline_fee_drag_rate",
        "current_fee_drag_rate",
        "baseline_volatility_cost_rate",
        "current_volatility_cost_rate",
        "baseline_settlement_friction_rate",
        "current_settlement_friction_rate",
        "baseline_total_cost_rate",
        "current_total_cost_rate",
        "cost_increase_rate",
        "alert_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    },
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    {
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    },
)
REPORT_DECIMAL_PAYLOAD_FIELDS = frozenset(
    {
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_current_total_cost_rate",
        "max_cost_increase_rate",
        "average_cost_increase_rate",
    },
)
ROW_DECIMAL_PAYLOAD_FIELDS = frozenset(
    {
        "baseline_spread_rate",
        "current_spread_rate",
        "baseline_depth_impact_rate",
        "current_depth_impact_rate",
        "baseline_slippage_rate",
        "current_slippage_rate",
        "baseline_fee_drag_rate",
        "current_fee_drag_rate",
        "baseline_volatility_cost_rate",
        "current_volatility_cost_rate",
        "baseline_settlement_friction_rate",
        "current_settlement_friction_rate",
        "baseline_total_cost_rate",
        "current_total_cost_rate",
        "cost_increase_rate",
    },
)


@dataclass(frozen=True)
class ResearchMarketCostRegimeShiftAlertConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION
    watch_total_cost_rate: Decimal = Decimal("0.060000")
    block_total_cost_rate: Decimal = Decimal("0.100000")
    watch_cost_increase_rate: Decimal = Decimal("0.020000")
    block_cost_increase_rate: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostRegimeShiftAlertConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_total_cost_rate",
            "block_total_cost_rate",
            "watch_cost_increase_rate",
            "block_cost_increase_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_total_cost_rate <= self.watch_total_cost_rate:
            raise ValueError("block_total_cost_rate must exceed watch_total_cost_rate")
        if self.block_cost_increase_rate <= self.watch_cost_increase_rate:
            raise ValueError(
                "block_cost_increase_rate must exceed watch_cost_increase_rate",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostRegimeShiftAlertInput:
    source_reference: str
    baseline_spread_rate: Decimal
    current_spread_rate: Decimal
    baseline_depth_impact_rate: Decimal
    current_depth_impact_rate: Decimal
    baseline_slippage_rate: Decimal
    current_slippage_rate: Decimal
    baseline_fee_drag_rate: Decimal
    current_fee_drag_rate: Decimal
    baseline_volatility_cost_rate: Decimal
    current_volatility_cost_rate: Decimal
    baseline_settlement_friction_rate: Decimal
    current_settlement_friction_rate: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostRegimeShiftAlertInput, "input")
        _require_raw_reference("source_reference", self.source_reference)
        for field_name in (
            "baseline_spread_rate",
            "current_spread_rate",
            "baseline_depth_impact_rate",
            "current_depth_impact_rate",
            "baseline_slippage_rate",
            "current_slippage_rate",
            "baseline_fee_drag_rate",
            "current_fee_drag_rate",
            "baseline_volatility_cost_rate",
            "current_volatility_cost_rate",
            "baseline_settlement_friction_rate",
            "current_settlement_friction_rate",
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
class ResearchMarketCostRegimeShiftAlertRow:
    case_digest: str
    baseline_spread_rate: Decimal
    current_spread_rate: Decimal
    baseline_depth_impact_rate: Decimal
    current_depth_impact_rate: Decimal
    baseline_slippage_rate: Decimal
    current_slippage_rate: Decimal
    baseline_fee_drag_rate: Decimal
    current_fee_drag_rate: Decimal
    baseline_volatility_cost_rate: Decimal
    current_volatility_cost_rate: Decimal
    baseline_settlement_friction_rate: Decimal
    current_settlement_friction_rate: Decimal
    baseline_total_cost_rate: Decimal
    current_total_cost_rate: Decimal
    cost_increase_rate: Decimal
    alert_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostRegimeShiftAlertRow, "row")
        _require_sha256_digest("case_digest", self.case_digest)
        for field_name in (
            "baseline_spread_rate",
            "current_spread_rate",
            "baseline_depth_impact_rate",
            "current_depth_impact_rate",
            "baseline_slippage_rate",
            "current_slippage_rate",
            "baseline_fee_drag_rate",
            "current_fee_drag_rate",
            "baseline_volatility_cost_rate",
            "current_volatility_cost_rate",
            "baseline_settlement_friction_rate",
            "current_settlement_friction_rate",
            "baseline_total_cost_rate",
            "current_total_cost_rate",
            "cost_increase_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("alert_status", self.alert_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        if f"cost_regime_status_{self.alert_status}" not in self.reason_codes:
            raise ValueError("alert_status must match reason_codes")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketCostRegimeShiftAlertReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostRegimeShiftAlertReasonCodeCount,
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
class ResearchMarketCostRegimeShiftAlertReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_current_total_cost_rate: Decimal
    max_cost_increase_rate: Decimal
    average_cost_increase_rate: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketCostRegimeShiftAlertReasonCodeCount, ...]
    rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostRegimeShiftAlertReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
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
            "max_current_total_cost_rate",
            "max_cost_increase_rate",
            "average_cost_increase_rate",
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


def build_research_market_cost_regime_shift_alert_report(
    inputs: Iterable[ResearchMarketCostRegimeShiftAlertInput],
    *,
    config: ResearchMarketCostRegimeShiftAlertConfig,
    generated_at: datetime,
) -> ResearchMarketCostRegimeShiftAlertReport:
    if type(config) is not ResearchMarketCostRegimeShiftAlertConfig:
        raise ValueError("config must be a ResearchMarketCostRegimeShiftAlertConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketCostRegimeShiftAlertReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        max_current_total_cost_rate=_max_row_decimal(rows, "current_total_cost_rate"),
        max_cost_increase_rate=_max_row_decimal(rows, "cost_increase_rate"),
        average_cost_increase_rate=_average_row_decimal(rows, "cost_increase_rate"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_cost_regime_shift_alert_report_payload(
    report: ResearchMarketCostRegimeShiftAlertReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketCostRegimeShiftAlertReport:
        raise ValueError("report must be a ResearchMarketCostRegimeShiftAlertReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_cost_regime_shift_alert_report_payload(payload)
    return payload


def validate_research_market_cost_regime_shift_alert_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_public_report_payload_shape(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    value: ResearchMarketCostRegimeShiftAlertInput,
    *,
    config: ResearchMarketCostRegimeShiftAlertConfig,
) -> ResearchMarketCostRegimeShiftAlertRow:
    baseline_total_cost_rate = _sum_rates(
        value.baseline_spread_rate,
        value.baseline_depth_impact_rate,
        value.baseline_slippage_rate,
        value.baseline_fee_drag_rate,
        value.baseline_volatility_cost_rate,
        value.baseline_settlement_friction_rate,
    )
    current_total_cost_rate = _sum_rates(
        value.current_spread_rate,
        value.current_depth_impact_rate,
        value.current_slippage_rate,
        value.current_fee_drag_rate,
        value.current_volatility_cost_rate,
        value.current_settlement_friction_rate,
    )
    cost_increase_rate = _increase_rate(current_total_cost_rate, baseline_total_cost_rate)
    status = _row_status(
        current_total_cost_rate,
        cost_increase_rate,
        config=config,
    )
    return ResearchMarketCostRegimeShiftAlertRow(
        case_digest=_reference_digest(value.source_reference),
        baseline_spread_rate=value.baseline_spread_rate,
        current_spread_rate=value.current_spread_rate,
        baseline_depth_impact_rate=value.baseline_depth_impact_rate,
        current_depth_impact_rate=value.current_depth_impact_rate,
        baseline_slippage_rate=value.baseline_slippage_rate,
        current_slippage_rate=value.current_slippage_rate,
        baseline_fee_drag_rate=value.baseline_fee_drag_rate,
        current_fee_drag_rate=value.current_fee_drag_rate,
        baseline_volatility_cost_rate=value.baseline_volatility_cost_rate,
        current_volatility_cost_rate=value.current_volatility_cost_rate,
        baseline_settlement_friction_rate=value.baseline_settlement_friction_rate,
        current_settlement_friction_rate=value.current_settlement_friction_rate,
        baseline_total_cost_rate=baseline_total_cost_rate,
        current_total_cost_rate=current_total_cost_rate,
        cost_increase_rate=cost_increase_rate,
        alert_status=status,
        reason_codes=_row_reason_codes(value, status=status),
    )


def _row_status(
    current_total_cost_rate: Decimal,
    cost_increase_rate: Decimal,
    *,
    config: ResearchMarketCostRegimeShiftAlertConfig,
) -> str:
    if (
        current_total_cost_rate >= config.block_total_cost_rate
        or cost_increase_rate >= config.block_cost_increase_rate
    ):
        return BLOCK_STATUS
    if (
        current_total_cost_rate >= config.watch_total_cost_rate
        or cost_increase_rate >= config.watch_cost_increase_rate
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    value: ResearchMarketCostRegimeShiftAlertInput,
    *,
    status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in value.upstream_reason_codes]
    component_pairs = (
        (
            "cost_regime_spread_shift",
            value.current_spread_rate,
            value.baseline_spread_rate,
        ),
        (
            "cost_regime_depth_shift",
            value.current_depth_impact_rate,
            value.baseline_depth_impact_rate,
        ),
        (
            "cost_regime_slippage_shift",
            value.current_slippage_rate,
            value.baseline_slippage_rate,
        ),
        (
            "cost_regime_fee_drag_shift",
            value.current_fee_drag_rate,
            value.baseline_fee_drag_rate,
        ),
        (
            "cost_regime_volatility_shift",
            value.current_volatility_cost_rate,
            value.baseline_volatility_cost_rate,
        ),
        (
            "cost_regime_settlement_friction_shift",
            value.current_settlement_friction_rate,
            value.baseline_settlement_friction_rate,
        ),
    )
    for reason_code, current_rate, baseline_rate in component_pairs:
        if current_rate > baseline_rate:
            reason_codes.append(reason_code)
    if status == WATCH_STATUS:
        reason_codes.append("cost_regime_shift_watch")
    if status == BLOCK_STATUS:
        reason_codes.append("cost_regime_shift_block")
    reason_codes.append(f"cost_regime_status_{status}")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _normalize_inputs(
    inputs: Iterable[ResearchMarketCostRegimeShiftAlertInput],
) -> tuple[ResearchMarketCostRegimeShiftAlertInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketCostRegimeShiftAlertInput:
            raise ValueError(
                "inputs must contain ResearchMarketCostRegimeShiftAlertInput",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketCostRegimeShiftAlertRow],
) -> tuple[ResearchMarketCostRegimeShiftAlertRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketCostRegimeShiftAlertRow:
            raise ValueError("rows must contain ResearchMarketCostRegimeShiftAlertRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketCostRegimeShiftAlertReasonCodeCount],
) -> tuple[ResearchMarketCostRegimeShiftAlertReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketCostRegimeShiftAlertReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCostRegimeShiftAlertReasonCodeCount",
            )
        _require_hard_flags(count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_report_consistency(report: ResearchMarketCostRegimeShiftAlertReport) -> None:
    for row in report.rows:
        if row.baseline_total_cost_rate != _sum_rates(
            row.baseline_spread_rate,
            row.baseline_depth_impact_rate,
            row.baseline_slippage_rate,
            row.baseline_fee_drag_rate,
            row.baseline_volatility_cost_rate,
            row.baseline_settlement_friction_rate,
        ):
            raise ValueError("baseline_total_cost_rate must match row components")
        if row.current_total_cost_rate != _sum_rates(
            row.current_spread_rate,
            row.current_depth_impact_rate,
            row.current_slippage_rate,
            row.current_fee_drag_rate,
            row.current_volatility_cost_rate,
            row.current_settlement_friction_rate,
        ):
            raise ValueError("current_total_cost_rate must match row components")
        if row.cost_increase_rate != _increase_rate(
            row.current_total_cost_rate,
            row.baseline_total_cost_rate,
        ):
            raise ValueError("cost_increase_rate must match row totals")
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
    if report.max_current_total_cost_rate != _max_row_decimal(
        report.rows,
        "current_total_cost_rate",
    ):
        raise ValueError("max_current_total_cost_rate must match rows")
    if report.max_cost_increase_rate != _max_row_decimal(
        report.rows,
        "cost_increase_rate",
    ):
        raise ValueError("max_cost_increase_rate must match rows")
    if report.average_cost_increase_rate != _average_row_decimal(
        report.rows,
        "cost_increase_rate",
    ):
        raise ValueError("average_cost_increase_rate must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.alert_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.alert_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_regime_shift_alert_report_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...],
) -> tuple[ResearchMarketCostRegimeShiftAlertReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketCostRegimeShiftAlertReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.alert_status == status))


def _max_row_decimal(
    rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketCostRegimeShiftAlertRow, ...],
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


def _increase_rate(current_value: Decimal, baseline_value: Decimal) -> Decimal:
    return _quantize_decimal(max(current_value - baseline_value, ZERO))


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
    if type(value) is not str or value not in COST_REGIME_SHIFT_ALERT_STATUSES:
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


def _validate_public_report_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    _require_payload_hard_flags(payload)
    _require_payload_datetime("generated_at", payload["generated_at"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_MARKET_COST_REGIME_SHIFT_ALERT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", payload["status"])
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_payload_decimal(field_name, payload[field_name])
    _validate_payload_reason_codes("reason_codes", payload["reason_codes"])
    _validate_reason_code_count_payloads(payload["reason_code_counts"])
    _validate_row_payloads(payload["rows"])


def _validate_row_payloads(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("rows must be a list")
    for index, row_payload in enumerate(value):
        if type(row_payload) is not dict:
            raise ValueError(f"rows[{index}] must be a dict")
        _require_payload_keys(f"rows[{index}]", row_payload, ROW_PAYLOAD_KEYS)
        _require_payload_hard_flags(row_payload)
        _require_sha256_digest("case_digest", row_payload["case_digest"])
        for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
            _require_payload_decimal(field_name, row_payload[field_name])
        _require_status("alert_status", row_payload["alert_status"])
        _validate_payload_reason_codes(
            f"rows[{index}].reason_codes",
            row_payload["reason_codes"],
        )


def _validate_reason_code_count_payloads(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("reason_code_counts must be a list")
    for index, count_payload in enumerate(value):
        if type(count_payload) is not dict:
            raise ValueError(f"reason_code_counts[{index}] must be a dict")
        _require_payload_keys(
            f"reason_code_counts[{index}]",
            count_payload,
            REASON_CODE_COUNT_PAYLOAD_KEYS,
        )
        _require_payload_hard_flags(count_payload)
        _require_public_identifier("reason_code", count_payload["reason_code"])
        if _contains_unsafe_public_term(count_payload["reason_code"]):
            raise ValueError("reason_code has unsafe public payload")
        _require_payload_decimal("count", count_payload["count"])


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    if actual_keys != expected_keys:
        raise ValueError(f"{label} must have the expected public payload fields")


def _require_payload_datetime(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UTC datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be a UTC datetime string")


def _require_payload_decimal(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    normalized = _normalize_nonnegative_decimal(field_name, parsed)
    if f"{normalized:.6f}" != value:
        raise ValueError(f"{field_name} must be a six-place decimal string")


def _validate_payload_reason_codes(field_name: str, value: object) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    _normalize_reason_codes(value, allow_empty=False)


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
    row: ResearchMarketCostRegimeShiftAlertRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.alert_status],
        -row.cost_increase_rate,
        -row.current_total_cost_rate,
        row.case_digest,
    )


def _reference_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketCostRegimeShiftAlertReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketCostRegimeShiftAlertReport,
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
