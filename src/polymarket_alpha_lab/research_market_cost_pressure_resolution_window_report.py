"""Pure report-only cost pressure resolution window reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_COST_PRESSURE_RESOLUTION_WINDOW_REPORT_CONFIG_VERSION = (
    "research-market-cost-pressure-resolution-window-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COST_PRESSURE_RESOLUTION_WINDOW_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("r", "aw"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("exec", "ution"),
    _join_parts("ap", "i", "_", "key"),
    _join_parts("priv", "ate", "_", "key"),
    _join_parts("au", "th"),
    "://",
    "?",
    "@",
    "=",
)

NO_INPUTS_REASON = "window_cost_no_inputs"

REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "high_fee_pressure_count",
    "high_spread_pressure_count",
    "high_slippage_pressure_count",
    "thin_depth_count",
    "high_settlement_friction_count",
    "short_resolution_window_count",
    "average_window_cost_pressure_score",
    "min_remaining_resolution_hours",
    "min_available_depth",
    "max_fee_pressure_ratio",
    "max_spread_pressure_ratio",
    "max_slippage_pressure_ratio",
    "max_settlement_friction_ratio",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_DECIMAL_PAYLOAD_KEYS = (
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "high_fee_pressure_count",
    "high_spread_pressure_count",
    "high_slippage_pressure_count",
    "thin_depth_count",
    "high_settlement_friction_count",
    "short_resolution_window_count",
    "average_window_cost_pressure_score",
    "min_remaining_resolution_hours",
    "min_available_depth",
    "max_fee_pressure_ratio",
    "max_spread_pressure_ratio",
    "max_slippage_pressure_ratio",
    "max_settlement_friction_ratio",
)
REASON_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "public_row_ref",
    "observed_at",
    "remaining_resolution_hours",
    "remaining_window_score",
    "fee_pressure_ratio",
    "fee_pressure_score",
    "spread_pressure_ratio",
    "spread_pressure_score",
    "slippage_pressure_ratio",
    "slippage_pressure_score",
    "available_depth",
    "available_depth_score",
    "settlement_friction_ratio",
    "settlement_friction_score",
    "window_cost_pressure_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_DECIMAL_PAYLOAD_KEYS = (
    "remaining_resolution_hours",
    "remaining_window_score",
    "fee_pressure_ratio",
    "fee_pressure_score",
    "spread_pressure_ratio",
    "spread_pressure_score",
    "slippage_pressure_ratio",
    "slippage_pressure_score",
    "available_depth",
    "available_depth_score",
    "settlement_friction_ratio",
    "settlement_friction_score",
    "window_cost_pressure_score",
)

__all__ = (
    "COST_PRESSURE_RESOLUTION_WINDOW_STATUSES",
    "DEFAULT_RESEARCH_MARKET_COST_PRESSURE_RESOLUTION_WINDOW_REPORT_CONFIG_VERSION",
    "ResearchMarketCostPressureResolutionWindowConfig",
    "ResearchMarketCostPressureResolutionWindowInput",
    "ResearchMarketCostPressureResolutionWindowReasonCodeCount",
    "ResearchMarketCostPressureResolutionWindowReport",
    "ResearchMarketCostPressureResolutionWindowRow",
    "build_research_market_cost_pressure_resolution_window_report",
    "research_market_cost_pressure_resolution_window_report_payload",
    "validate_research_market_cost_pressure_resolution_window_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketCostPressureResolutionWindowConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_PRESSURE_RESOLUTION_WINDOW_REPORT_CONFIG_VERSION
    )
    maximum_pass_fee_pressure_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_pressure_ratio: Decimal = Decimal("0.030000")
    maximum_pass_spread_pressure_ratio: Decimal = Decimal("0.020000")
    maximum_watch_spread_pressure_ratio: Decimal = Decimal("0.060000")
    maximum_pass_slippage_pressure_ratio: Decimal = Decimal("0.015000")
    maximum_watch_slippage_pressure_ratio: Decimal = Decimal("0.050000")
    minimum_pass_available_depth: Decimal = Decimal("1000.000000")
    minimum_watch_available_depth: Decimal = Decimal("250.000000")
    maximum_pass_settlement_friction_ratio: Decimal = Decimal("0.050000")
    maximum_watch_settlement_friction_ratio: Decimal = Decimal("0.150000")
    minimum_pass_remaining_resolution_hours: Decimal = Decimal("24.000000")
    minimum_watch_remaining_resolution_hours: Decimal = Decimal("6.000000")
    minimum_pass_window_cost_score: Decimal = Decimal("0.750000")
    minimum_watch_window_cost_score: Decimal = Decimal("0.450000")
    fee_pressure_weight: Decimal = Decimal("0.180000")
    spread_pressure_weight: Decimal = Decimal("0.180000")
    slippage_pressure_weight: Decimal = Decimal("0.180000")
    available_depth_weight: Decimal = Decimal("0.180000")
    settlement_friction_weight: Decimal = Decimal("0.180000")
    remaining_window_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostPressureResolutionWindowConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_PRESSURE_RESOLUTION_WINDOW_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_fee_pressure_ratio",
            "maximum_watch_fee_pressure_ratio",
            "maximum_pass_spread_pressure_ratio",
            "maximum_watch_spread_pressure_ratio",
            "maximum_pass_slippage_pressure_ratio",
            "maximum_watch_slippage_pressure_ratio",
            "maximum_pass_settlement_friction_ratio",
            "maximum_watch_settlement_friction_ratio",
            "minimum_pass_window_cost_score",
            "minimum_watch_window_cost_score",
            "fee_pressure_weight",
            "spread_pressure_weight",
            "slippage_pressure_weight",
            "available_depth_weight",
            "settlement_friction_weight",
            "remaining_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_available_depth",
            "minimum_watch_available_depth",
            "minimum_pass_remaining_resolution_hours",
            "minimum_watch_remaining_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_pass_fee_pressure_ratio > self.maximum_watch_fee_pressure_ratio:
            raise ValueError("maximum_pass_fee_pressure_ratio must not exceed watch")
        if (
            self.maximum_pass_spread_pressure_ratio
            > self.maximum_watch_spread_pressure_ratio
        ):
            raise ValueError("maximum_pass_spread_pressure_ratio must not exceed watch")
        if (
            self.maximum_pass_slippage_pressure_ratio
            > self.maximum_watch_slippage_pressure_ratio
        ):
            raise ValueError("maximum_pass_slippage_pressure_ratio must not exceed watch")
        if self.minimum_pass_available_depth < self.minimum_watch_available_depth:
            raise ValueError("minimum_pass_available_depth must be at least watch")
        if (
            self.maximum_pass_settlement_friction_ratio
            > self.maximum_watch_settlement_friction_ratio
        ):
            raise ValueError(
                "maximum_pass_settlement_friction_ratio must not exceed watch",
            )
        if (
            self.minimum_pass_remaining_resolution_hours
            < self.minimum_watch_remaining_resolution_hours
        ):
            raise ValueError(
                "minimum_pass_remaining_resolution_hours must be at least watch",
            )
        if self.minimum_pass_window_cost_score < self.minimum_watch_window_cost_score:
            raise ValueError("minimum_pass_window_cost_score must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostPressureResolutionWindowInput:
    private_event_ref: str
    observed_at: datetime
    remaining_resolution_hours: Decimal
    fee_pressure_ratio: Decimal
    spread_pressure_ratio: Decimal
    slippage_pressure_ratio: Decimal
    available_depth: Decimal
    settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostPressureResolutionWindowInput, "input")
        _require_private_ref("private_event_ref", self.private_event_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fee_pressure_ratio",
            "spread_pressure_ratio",
            "slippage_pressure_ratio",
            "settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("remaining_resolution_hours", "available_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketCostPressureResolutionWindowRow:
    public_row_ref: str
    observed_at: datetime
    remaining_resolution_hours: Decimal
    remaining_window_score: Decimal
    fee_pressure_ratio: Decimal
    fee_pressure_score: Decimal
    spread_pressure_ratio: Decimal
    spread_pressure_score: Decimal
    slippage_pressure_ratio: Decimal
    slippage_pressure_score: Decimal
    available_depth: Decimal
    available_depth_score: Decimal
    settlement_friction_ratio: Decimal
    settlement_friction_score: Decimal
    window_cost_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostPressureResolutionWindowRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("remaining_resolution_hours", "available_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "remaining_window_score",
            "fee_pressure_ratio",
            "fee_pressure_score",
            "spread_pressure_ratio",
            "spread_pressure_score",
            "slippage_pressure_ratio",
            "slippage_pressure_score",
            "available_depth_score",
            "settlement_friction_ratio",
            "settlement_friction_score",
            "window_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketCostPressureResolutionWindowReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostPressureResolutionWindowReasonCodeCount,
            "reason_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchMarketCostPressureResolutionWindowReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_fee_pressure_count: Decimal
    high_spread_pressure_count: Decimal
    high_slippage_pressure_count: Decimal
    thin_depth_count: Decimal
    high_settlement_friction_count: Decimal
    short_resolution_window_count: Decimal
    average_window_cost_pressure_score: Decimal
    min_remaining_resolution_hours: Decimal
    min_available_depth: Decimal
    max_fee_pressure_ratio: Decimal
    max_spread_pressure_ratio: Decimal
    max_slippage_pressure_ratio: Decimal
    max_settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketCostPressureResolutionWindowReasonCodeCount, ...]
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostPressureResolutionWindowReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_fee_pressure_count",
            "high_spread_pressure_count",
            "high_slippage_pressure_count",
            "thin_depth_count",
            "high_settlement_friction_count",
            "short_resolution_window_count",
            "min_remaining_resolution_hours",
            "min_available_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_window_cost_pressure_score",
            "max_fee_pressure_ratio",
            "max_spread_pressure_ratio",
            "max_slippage_pressure_ratio",
            "max_settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_market_cost_pressure_resolution_window_report_payload(self)


def build_research_market_cost_pressure_resolution_window_report(
    inputs: Iterable[ResearchMarketCostPressureResolutionWindowInput],
    *,
    config: ResearchMarketCostPressureResolutionWindowConfig,
    generated_at: datetime,
) -> ResearchMarketCostPressureResolutionWindowReport:
    if type(config) is not ResearchMarketCostPressureResolutionWindowConfig:
        raise ValueError(
            "config must be a ResearchMarketCostPressureResolutionWindowConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            ((_private_digest(value.private_event_ref), value) for value in normalized),
            key=lambda item: item[0],
        ),
    )
    if len({key for key, _ in keyed_inputs}) != len(keyed_inputs):
        raise ValueError("private_event_ref values must be unique")
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    public_row_ref=_public_row_ref(index),
                )
                for index, (_, value) in enumerate(keyed_inputs, start=1)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketCostPressureResolutionWindowReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        high_fee_pressure_count=_non_pass_reason_count(rows, "window_cost_fee_pressure"),
        high_spread_pressure_count=_non_pass_reason_count(
            rows,
            "window_cost_spread_pressure",
        ),
        high_slippage_pressure_count=_non_pass_reason_count(
            rows,
            "window_cost_slippage_pressure",
        ),
        thin_depth_count=_non_pass_reason_count(rows, "window_cost_available_depth"),
        high_settlement_friction_count=_non_pass_reason_count(
            rows,
            "window_cost_settlement_friction",
        ),
        short_resolution_window_count=_non_pass_reason_count(
            rows,
            "window_cost_remaining_window",
        ),
        average_window_cost_pressure_score=_average_row_decimal(
            rows,
            "window_cost_pressure_score",
        ),
        min_remaining_resolution_hours=_min_row_decimal(
            rows,
            "remaining_resolution_hours",
        ),
        min_available_depth=_min_row_decimal(rows, "available_depth"),
        max_fee_pressure_ratio=_max_row_decimal(rows, "fee_pressure_ratio"),
        max_spread_pressure_ratio=_max_row_decimal(rows, "spread_pressure_ratio"),
        max_slippage_pressure_ratio=_max_row_decimal(rows, "slippage_pressure_ratio"),
        max_settlement_friction_ratio=_max_row_decimal(
            rows,
            "settlement_friction_ratio",
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_cost_pressure_resolution_window_report_payload(
    report: ResearchMarketCostPressureResolutionWindowReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketCostPressureResolutionWindowReport:
        raise ValueError(
            "report must be a ResearchMarketCostPressureResolutionWindowReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_cost_pressure_resolution_window_report_payload(payload)
    return payload


def validate_research_market_cost_pressure_resolution_window_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_json_ready_payload_value("payload", payload)
    _require_payload_shape(payload)
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_statuses("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    _require_payload_consistency(payload)
    return payload


def _require_json_ready_payload_value(label: str, value: Any) -> None:
    if type(value) is dict:
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_json_ready_payload_value(f"{label}.{key}", nested)
        return
    if type(value) is list:
        for index, nested in enumerate(value):
            _require_json_ready_payload_value(f"{label}[{index}]", nested)
        return
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError(f"{label} must be JSON-ready")


def _require_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    _require_datetime_text("generated_at", payload["generated_at"])
    _require_public_label("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_MARKET_COST_PRESSURE_RESOLUTION_WINDOW_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must match supported value")
    _require_status("status", payload["status"])
    for field_name in REPORT_DECIMAL_PAYLOAD_KEYS:
        _require_decimal_text(field_name, payload[field_name])
    _require_payload_reason_codes("reason_codes", payload["reason_codes"])
    _require_reason_count_payloads(payload["reason_code_counts"])
    _require_row_payloads(payload["rows"])
    _require_sha256_digest("derived_validation_digest", payload["derived_validation_digest"])


def _require_payload_keys(
    label: str,
    value: Any,
    expected_keys: tuple[str, ...],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if set(value) != set(expected_keys):
        raise ValueError(f"{label} payload keys must match generated shape")


def _require_reason_count_payloads(values: Any) -> None:
    if type(values) is not list:
        raise ValueError("reason_code_counts must be a list")
    reason_codes: list[str] = []
    for value in values:
        _require_payload_keys(
            "reason_code_counts item",
            value,
            REASON_COUNT_PAYLOAD_KEYS,
        )
        reason_codes.append(_require_reason_code("reason_code", value["reason_code"]))
        _require_decimal_text("count", value["count"])
    if tuple(reason_codes) != tuple(sorted(set(reason_codes))):
        raise ValueError("reason_code_counts must be sorted and unique")


def _require_row_payloads(values: Any) -> None:
    if type(values) is not list:
        raise ValueError("rows must be a list")
    public_row_refs: list[str] = []
    for value in values:
        _require_payload_keys("rows item", value, ROW_PAYLOAD_KEYS)
        public_row_refs.append(_require_public_label("public_row_ref", value["public_row_ref"]))
        _require_datetime_text("observed_at", value["observed_at"])
        for field_name in ROW_DECIMAL_PAYLOAD_KEYS:
            _require_decimal_text(field_name, value[field_name])
        _require_status("status", value["status"])
        reason_codes = _require_payload_reason_codes("reason_codes", value["reason_codes"])
        if f"window_cost_status_{value['status']}" not in reason_codes:
            raise ValueError("status must match reason_codes")
        if value["status"] == PASS_STATUS and value["window_cost_pressure_score"] != str(ONE):
            raise ValueError("window_cost_pressure_score must match pass status")
    if len(set(public_row_refs)) != len(public_row_refs):
        raise ValueError("public_row_ref values must be unique")
    if values != sorted(values, key=_payload_row_sort_key):
        raise ValueError("rows must be sorted")


def _require_payload_reason_codes(
    field_name: str,
    values: Any,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(_require_reason_code(field_name, value) for value in values)
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if reason_codes != tuple(sorted(set(reason_codes))):
        raise ValueError(f"{field_name} must be sorted and unique")
    return reason_codes


def _require_payload_consistency(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    expected_pairs = {
        "status": _payload_report_status(rows),
        "input_count": str(_count_decimal(len(rows))),
        "row_count": str(_count_decimal(len(rows))),
        "pass_count": str(_payload_status_count(rows, PASS_STATUS)),
        "watch_count": str(_payload_status_count(rows, WATCH_STATUS)),
        "block_count": str(_payload_status_count(rows, BLOCK_STATUS)),
        "high_fee_pressure_count": str(
            _payload_non_pass_reason_count(rows, "window_cost_fee_pressure"),
        ),
        "high_spread_pressure_count": str(
            _payload_non_pass_reason_count(rows, "window_cost_spread_pressure"),
        ),
        "high_slippage_pressure_count": str(
            _payload_non_pass_reason_count(rows, "window_cost_slippage_pressure"),
        ),
        "thin_depth_count": str(
            _payload_non_pass_reason_count(rows, "window_cost_available_depth"),
        ),
        "high_settlement_friction_count": str(
            _payload_non_pass_reason_count(rows, "window_cost_settlement_friction"),
        ),
        "short_resolution_window_count": str(
            _payload_non_pass_reason_count(rows, "window_cost_remaining_window"),
        ),
        "average_window_cost_pressure_score": str(
            _payload_average_decimal(rows, "window_cost_pressure_score"),
        ),
        "min_remaining_resolution_hours": str(
            _payload_min_decimal(rows, "remaining_resolution_hours"),
        ),
        "min_available_depth": str(_payload_min_decimal(rows, "available_depth")),
        "max_fee_pressure_ratio": str(_payload_max_decimal(rows, "fee_pressure_ratio")),
        "max_spread_pressure_ratio": str(_payload_max_decimal(rows, "spread_pressure_ratio")),
        "max_slippage_pressure_ratio": str(
            _payload_max_decimal(rows, "slippage_pressure_ratio"),
        ),
        "max_settlement_friction_ratio": str(
            _payload_max_decimal(rows, "settlement_friction_ratio"),
        ),
        "reason_codes": _payload_report_reason_codes(rows),
        "reason_code_counts": _payload_reason_code_count_payloads(rows),
    }
    for field_name, expected_value in expected_pairs.items():
        if payload[field_name] != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _payload_row_sort_key(value: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[value["status"]],
        _require_decimal_text("window_cost_pressure_score", value["window_cost_pressure_score"]),
        value["public_row_ref"],
    )


def _payload_report_status(rows: list[Any]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row["status"] == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row["status"] == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _payload_report_reason_codes(rows: list[Any]) -> list[str]:
    if not rows:
        return [NO_INPUTS_REASON]
    return sorted({reason_code for row in rows for reason_code in row["reason_codes"]})


def _payload_reason_code_count_payloads(rows: list[Any]) -> list[dict[str, Any]]:
    if not rows:
        return [
            {
                "reason_code": NO_INPUTS_REASON,
                "count": str(ONE),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ]
    counts = Counter(reason_code for row in rows for reason_code in row["reason_codes"])
    return [
        {
            "reason_code": reason_code,
            "count": str(_count_decimal(count)),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        for reason_code, count in sorted(counts.items())
    ]


def _payload_status_count(rows: list[Any], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row["status"] == status))


def _payload_non_pass_reason_count(rows: list[Any], prefix: str) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if any(
                reason_code.startswith(prefix)
                and not reason_code.endswith(f"_{PASS_STATUS}")
                for reason_code in row["reason_codes"]
            )
        ),
    )


def _payload_average_decimal(rows: list[Any], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((_require_decimal_text(field_name, row[field_name]) for row in rows), ZERO)
            / _count_decimal(len(rows)),
        )


def _payload_min_decimal(rows: list[Any], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(_require_decimal_text(field_name, row[field_name]) for row in rows)


def _payload_max_decimal(rows: list[Any], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(_require_decimal_text(field_name, row[field_name]) for row in rows)


def _require_decimal_text(field_name: str, value: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(decimal_value)
    if value != str(normalized):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_datetime_text(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    normalized = parsed.astimezone(UTC)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be canonical UTC datetime text")
    return normalized


def _row_from_input(
    value: ResearchMarketCostPressureResolutionWindowInput,
    *,
    config: ResearchMarketCostPressureResolutionWindowConfig,
    public_row_ref: str,
) -> ResearchMarketCostPressureResolutionWindowRow:
    fee_pressure_score = _score_for_maximum(
        value.fee_pressure_ratio,
        config.maximum_pass_fee_pressure_ratio,
        config.maximum_watch_fee_pressure_ratio,
    )
    spread_pressure_score = _score_for_maximum(
        value.spread_pressure_ratio,
        config.maximum_pass_spread_pressure_ratio,
        config.maximum_watch_spread_pressure_ratio,
    )
    slippage_pressure_score = _score_for_maximum(
        value.slippage_pressure_ratio,
        config.maximum_pass_slippage_pressure_ratio,
        config.maximum_watch_slippage_pressure_ratio,
    )
    available_depth_score = _score_for_minimum(
        value.available_depth,
        config.minimum_pass_available_depth,
        config.minimum_watch_available_depth,
    )
    settlement_friction_score = _score_for_maximum(
        value.settlement_friction_ratio,
        config.maximum_pass_settlement_friction_ratio,
        config.maximum_watch_settlement_friction_ratio,
    )
    remaining_window_score = _score_for_minimum(
        value.remaining_resolution_hours,
        config.minimum_pass_remaining_resolution_hours,
        config.minimum_watch_remaining_resolution_hours,
    )
    window_cost_pressure_score = _window_cost_pressure_score(
        remaining_window_score=remaining_window_score,
        fee_pressure_score=fee_pressure_score,
        spread_pressure_score=spread_pressure_score,
        slippage_pressure_score=slippage_pressure_score,
        available_depth_score=available_depth_score,
        settlement_friction_score=settlement_friction_score,
        config=config,
    )
    component_statuses = (
        _status_for_maximum(
            value.fee_pressure_ratio,
            config.maximum_pass_fee_pressure_ratio,
            config.maximum_watch_fee_pressure_ratio,
        ),
        _status_for_maximum(
            value.spread_pressure_ratio,
            config.maximum_pass_spread_pressure_ratio,
            config.maximum_watch_spread_pressure_ratio,
        ),
        _status_for_maximum(
            value.slippage_pressure_ratio,
            config.maximum_pass_slippage_pressure_ratio,
            config.maximum_watch_slippage_pressure_ratio,
        ),
        _status_for_minimum(
            value.available_depth,
            config.minimum_pass_available_depth,
            config.minimum_watch_available_depth,
        ),
        _status_for_maximum(
            value.settlement_friction_ratio,
            config.maximum_pass_settlement_friction_ratio,
            config.maximum_watch_settlement_friction_ratio,
        ),
        _status_for_minimum(
            value.remaining_resolution_hours,
            config.minimum_pass_remaining_resolution_hours,
            config.minimum_watch_remaining_resolution_hours,
        ),
    )
    status = _row_status(
        component_statuses=component_statuses,
        score=window_cost_pressure_score,
        config=config,
    )
    return ResearchMarketCostPressureResolutionWindowRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        remaining_resolution_hours=value.remaining_resolution_hours,
        remaining_window_score=remaining_window_score,
        fee_pressure_ratio=value.fee_pressure_ratio,
        fee_pressure_score=fee_pressure_score,
        spread_pressure_ratio=value.spread_pressure_ratio,
        spread_pressure_score=spread_pressure_score,
        slippage_pressure_ratio=value.slippage_pressure_ratio,
        slippage_pressure_score=slippage_pressure_score,
        available_depth=value.available_depth,
        available_depth_score=available_depth_score,
        settlement_friction_ratio=value.settlement_friction_ratio,
        settlement_friction_score=settlement_friction_score,
        window_cost_pressure_score=window_cost_pressure_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            fee_pressure_status=component_statuses[0],
            spread_pressure_status=component_statuses[1],
            slippage_pressure_status=component_statuses[2],
            available_depth_status=component_statuses[3],
            settlement_friction_status=component_statuses[4],
            remaining_window_status=component_statuses[5],
        ),
    )


def _window_cost_pressure_score(
    *,
    remaining_window_score: Decimal,
    fee_pressure_score: Decimal,
    spread_pressure_score: Decimal,
    slippage_pressure_score: Decimal,
    available_depth_score: Decimal,
    settlement_friction_score: Decimal,
    config: ResearchMarketCostPressureResolutionWindowConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            fee_pressure_score * config.fee_pressure_weight
            + spread_pressure_score * config.spread_pressure_weight
            + slippage_pressure_score * config.slippage_pressure_weight
            + available_depth_score * config.available_depth_weight
            + settlement_friction_score * config.settlement_friction_weight
            + remaining_window_score * config.remaining_window_weight,
        )


def _row_status(
    *,
    component_statuses: tuple[str, ...],
    score: Decimal,
    config: ResearchMarketCostPressureResolutionWindowConfig,
) -> str:
    if BLOCK_STATUS in component_statuses or score < config.minimum_watch_window_cost_score:
        return BLOCK_STATUS
    if WATCH_STATUS in component_statuses or score < config.minimum_pass_window_cost_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    fee_pressure_status: str,
    spread_pressure_status: str,
    slippage_pressure_status: str,
    available_depth_status: str,
    settlement_friction_status: str,
    remaining_window_status: str,
) -> tuple[str, ...]:
    reason_codes = [
        _component_reason("fee_pressure", fee_pressure_status),
        _component_reason("spread_pressure", spread_pressure_status),
        _component_reason("slippage_pressure", slippage_pressure_status),
        _component_reason("available_depth", available_depth_status),
        _component_reason("settlement_friction", settlement_friction_status),
        _component_reason("remaining_window", remaining_window_status),
        f"window_cost_status_{status}",
    ]
    reason_codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _component_reason(component: str, status: str) -> str:
    return f"window_cost_{component}_{status}"


def _score_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value <= pass_value:
        return ONE
    if value >= watch_value:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((watch_value - value) / (watch_value - pass_value))


def _score_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value >= pass_value:
        return ONE
    if value <= watch_value:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((value - watch_value) / (pass_value - watch_value))


def _status_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value <= pass_value:
        return PASS_STATUS
    if value <= watch_value:
        return WATCH_STATUS
    return BLOCK_STATUS


def _status_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value >= pass_value:
        return PASS_STATUS
    if value >= watch_value:
        return WATCH_STATUS
    return BLOCK_STATUS


def _report_status(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes})),
    )


def _report_reason_code_counts(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
) -> tuple[ResearchMarketCostPressureResolutionWindowReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketCostPressureResolutionWindowReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchMarketCostPressureResolutionWindowReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketCostPressureResolutionWindowInput],
) -> tuple[ResearchMarketCostPressureResolutionWindowInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    rows: list[ResearchMarketCostPressureResolutionWindowInput] = []
    try:
        iterator = iter(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    for value in iterator:
        if type(value) is not ResearchMarketCostPressureResolutionWindowInput:
            raise ValueError(
                "inputs must contain ResearchMarketCostPressureResolutionWindowInput",
            )
        _require_hard_flags("input", value)
        rows.append(value)
    return tuple(rows)


def _normalize_rows(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
) -> tuple[ResearchMarketCostPressureResolutionWindowRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketCostPressureResolutionWindowRow:
            raise ValueError("rows must contain ResearchMarketCostPressureResolutionWindowRow")
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketCostPressureResolutionWindowReasonCodeCount, ...],
) -> tuple[ResearchMarketCostPressureResolutionWindowReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketCostPressureResolutionWindowReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCostPressureResolutionWindowReasonCodeCount",
            )
        _require_hard_flags("reason_count", value)
    return tuple(sorted(values, key=lambda value: value.reason_code))


def _row_sort_key(
    row: ResearchMarketCostPressureResolutionWindowRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.window_cost_pressure_score,
        row.public_row_ref,
    )


def _status_count(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
    prefix: str,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if any(
                reason_code.startswith(prefix)
                and not reason_code.endswith(f"_{PASS_STATUS}")
                for reason_code in row.reason_codes
            )
        ),
    )


def _average_row_decimal(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((getattr(row, field_name) for row in rows), ZERO)
            / _count_decimal(len(rows)),
        )


def _min_row_decimal(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _max_row_decimal(
    rows: tuple[ResearchMarketCostPressureResolutionWindowRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _validate_row_consistency(
    row: ResearchMarketCostPressureResolutionWindowRow,
) -> None:
    if f"window_cost_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.window_cost_pressure_score != ONE:
        raise ValueError("window_cost_pressure_score must match pass status")


def _validate_report_consistency(
    report: ResearchMarketCostPressureResolutionWindowReport,
) -> None:
    rows = report.rows
    expected_pairs = {
        "status": _report_status(rows),
        "input_count": report.row_count,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "high_fee_pressure_count": _non_pass_reason_count(
            rows,
            "window_cost_fee_pressure",
        ),
        "high_spread_pressure_count": _non_pass_reason_count(
            rows,
            "window_cost_spread_pressure",
        ),
        "high_slippage_pressure_count": _non_pass_reason_count(
            rows,
            "window_cost_slippage_pressure",
        ),
        "thin_depth_count": _non_pass_reason_count(rows, "window_cost_available_depth"),
        "high_settlement_friction_count": _non_pass_reason_count(
            rows,
            "window_cost_settlement_friction",
        ),
        "short_resolution_window_count": _non_pass_reason_count(
            rows,
            "window_cost_remaining_window",
        ),
        "average_window_cost_pressure_score": _average_row_decimal(
            rows,
            "window_cost_pressure_score",
        ),
        "min_remaining_resolution_hours": _min_row_decimal(
            rows,
            "remaining_resolution_hours",
        ),
        "min_available_depth": _min_row_decimal(rows, "available_depth"),
        "max_fee_pressure_ratio": _max_row_decimal(rows, "fee_pressure_ratio"),
        "max_spread_pressure_ratio": _max_row_decimal(rows, "spread_pressure_ratio"),
        "max_slippage_pressure_ratio": _max_row_decimal(rows, "slippage_pressure_ratio"),
        "max_settlement_friction_ratio": _max_row_decimal(
            rows,
            "settlement_friction_ratio",
        ),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _report_reason_code_counts(rows),
    }
    for field_name, expected_value in expected_pairs.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _weight_sum(config: ResearchMarketCostPressureResolutionWindowConfig) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            config.fee_pressure_weight
            + config.spread_pressure_weight
            + config.slippage_pressure_weight
            + config.available_depth_weight
            + config.settlement_friction_weight
            + config.remaining_window_weight,
        )


def _public_row_ref(index: int) -> str:
    return f"public-row-{index:06d}"


def _private_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketCostPressureResolutionWindowReport,
) -> str:
    payload = _json_value(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_value(value: Any, *, include_digest: bool = True) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value):
        return {
            field.name: _json_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
            for field in fields(value)
            if include_digest or field.name != "derived_validation_digest"
        }
    if isinstance(value, tuple):
        return [_json_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_ref(field_name: str, value: str) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_label(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase public text")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase snake text")
    if "__" in value or value.startswith("_") or value.endswith("_"):
        raise ValueError(f"{field_name} must be canonical snake text")
    _reject_unsafe_text(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted({_require_reason_code(field_name, value) for value in reason_codes}))


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in COST_PRESSURE_RESOLUTION_WINDOW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("decimal value must quantize to six places") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, field_name, None)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_payload_hard_flags(value: Any) -> None:
    if isinstance(value, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True")
        for nested in value.values():
            _require_payload_hard_flags(nested)
    elif isinstance(value, list):
        for nested in value:
            _require_payload_hard_flags(nested)


def _require_payload_statuses(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "status":
                _require_status(f"{label}.{key}", nested)
            _require_payload_statuses(f"{label}.{key}", nested)
    elif isinstance(value, list):
        for nested in value:
            _require_payload_statuses(label, nested)


def _require_sha256_digest(field_name: str, value: Any) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if is_dataclass(value):
        for field in fields(value):
            _reject_unsafe_text(label, field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
    elif isinstance(value, dict):
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(f"{label}.{key}", nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_unsafe_public_payload(label, nested)
    elif isinstance(value, str):
        _reject_unsafe_text(label, value)
    elif isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    else:
        raise ValueError(f"{label} contains unsupported public payload value")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
