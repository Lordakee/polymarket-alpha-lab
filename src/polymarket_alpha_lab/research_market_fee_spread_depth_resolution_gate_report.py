"""Pure report-only fee/spread/depth/resolution gate reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "FEE_SPREAD_DEPTH_RESOLUTION_GATE_STATUSES",
    "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_RESOLUTION_GATE_REPORT_CONFIG_VERSION",
    "ResearchMarketFeeSpreadDepthResolutionGateConfig",
    "ResearchMarketFeeSpreadDepthResolutionGateInput",
    "ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount",
    "ResearchMarketFeeSpreadDepthResolutionGateReport",
    "ResearchMarketFeeSpreadDepthResolutionGateRow",
    "build_research_market_fee_spread_depth_resolution_gate_report",
    "research_market_fee_spread_depth_resolution_gate_report_payload",
    "validate_research_market_fee_spread_depth_resolution_gate_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_RESOLUTION_GATE_REPORT_CONFIG_VERSION = (
    "research-market-fee-spread-depth-resolution-gate-report-v1"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
FEE_SPREAD_DEPTH_RESOLUTION_GATE_STATUSES = (
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
DECIMAL_CONTEXT = Context(prec=64)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
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


@dataclass(frozen=True)
class ResearchMarketFeeSpreadDepthResolutionGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_RESOLUTION_GATE_REPORT_CONFIG_VERSION
    )
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    maximum_pass_spread_width_ratio: Decimal = Decimal("0.030000")
    maximum_watch_spread_width_ratio: Decimal = Decimal("0.080000")
    minimum_pass_available_depth: Decimal = Decimal("1000.000000")
    minimum_watch_available_depth: Decimal = Decimal("250.000000")
    maximum_pass_resolution_friction_ratio: Decimal = Decimal("0.050000")
    maximum_watch_resolution_friction_ratio: Decimal = Decimal("0.150000")
    maximum_pass_settlement_delay_hours: Decimal = Decimal("24.000000")
    maximum_watch_settlement_delay_hours: Decimal = Decimal("72.000000")
    minimum_pass_gate_score: Decimal = Decimal("0.750000")
    minimum_watch_gate_score: Decimal = Decimal("0.450000")
    fee_drag_weight: Decimal = Decimal("0.200000")
    spread_width_weight: Decimal = Decimal("0.200000")
    available_depth_weight: Decimal = Decimal("0.250000")
    resolution_friction_weight: Decimal = Decimal("0.200000")
    settlement_timing_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthResolutionGateConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_RESOLUTION_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "maximum_pass_spread_width_ratio",
            "maximum_watch_spread_width_ratio",
            "maximum_pass_resolution_friction_ratio",
            "maximum_watch_resolution_friction_ratio",
            "minimum_pass_gate_score",
            "minimum_watch_gate_score",
            "fee_drag_weight",
            "spread_width_weight",
            "available_depth_weight",
            "resolution_friction_weight",
            "settlement_timing_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_available_depth",
            "minimum_watch_available_depth",
            "maximum_pass_settlement_delay_hours",
            "maximum_watch_settlement_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.maximum_pass_spread_width_ratio > self.maximum_watch_spread_width_ratio:
            raise ValueError("maximum_pass_spread_width_ratio must not exceed watch")
        if self.minimum_pass_available_depth < self.minimum_watch_available_depth:
            raise ValueError("minimum_pass_available_depth must be at least watch")
        if (
            self.maximum_pass_resolution_friction_ratio
            > self.maximum_watch_resolution_friction_ratio
        ):
            raise ValueError(
                "maximum_pass_resolution_friction_ratio must not exceed watch",
            )
        if (
            self.maximum_pass_settlement_delay_hours
            > self.maximum_watch_settlement_delay_hours
        ):
            raise ValueError("maximum_pass_settlement_delay_hours must not exceed watch")
        if self.minimum_pass_gate_score < self.minimum_watch_gate_score:
            raise ValueError("minimum_pass_gate_score must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadDepthResolutionGateInput:
    private_event_ref: str
    observed_at: datetime
    fee_drag_ratio: Decimal
    spread_width_ratio: Decimal
    available_depth: Decimal
    resolution_friction_ratio: Decimal
    settlement_delay_hours: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthResolutionGateInput, "input")
        _require_private_ref("private_event_ref", self.private_event_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fee_drag_ratio",
            "spread_width_ratio",
            "resolution_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("available_depth", "settlement_delay_hours"):
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
class ResearchMarketFeeSpreadDepthResolutionGateRow:
    public_row_ref: str
    observed_at: datetime
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    spread_width_ratio: Decimal
    spread_width_score: Decimal
    available_depth: Decimal
    available_depth_score: Decimal
    resolution_friction_ratio: Decimal
    resolution_friction_score: Decimal
    settlement_delay_hours: Decimal
    settlement_timing_score: Decimal
    gate_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthResolutionGateRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("available_depth", "settlement_delay_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_drag_ratio",
            "fee_drag_score",
            "spread_width_ratio",
            "spread_width_score",
            "available_depth_score",
            "resolution_friction_ratio",
            "resolution_friction_score",
            "settlement_timing_score",
            "gate_score",
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
class ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount,
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
class ResearchMarketFeeSpreadDepthResolutionGateReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_fee_drag_count: Decimal
    wide_spread_count: Decimal
    thin_depth_count: Decimal
    high_resolution_friction_count: Decimal
    delayed_settlement_count: Decimal
    average_gate_score: Decimal
    min_available_depth: Decimal
    max_fee_drag_ratio: Decimal
    max_spread_width_ratio: Decimal
    max_resolution_friction_ratio: Decimal
    max_settlement_delay_hours: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthResolutionGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_fee_drag_count",
            "wide_spread_count",
            "thin_depth_count",
            "high_resolution_friction_count",
            "delayed_settlement_count",
            "min_available_depth",
            "max_settlement_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_gate_score",
            "max_fee_drag_ratio",
            "max_spread_width_ratio",
            "max_resolution_friction_ratio",
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
        return research_market_fee_spread_depth_resolution_gate_report_payload(self)


def build_research_market_fee_spread_depth_resolution_gate_report(
    inputs: Iterable[ResearchMarketFeeSpreadDepthResolutionGateInput],
    *,
    config: ResearchMarketFeeSpreadDepthResolutionGateConfig,
    generated_at: datetime,
) -> ResearchMarketFeeSpreadDepthResolutionGateReport:
    if type(config) is not ResearchMarketFeeSpreadDepthResolutionGateConfig:
        raise ValueError(
            "config must be a ResearchMarketFeeSpreadDepthResolutionGateConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            (
                (
                    _private_digest(value.private_event_ref),
                    value,
                )
                for value in normalized
            ),
            key=lambda item: item[0],
        ),
    )
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
    return ResearchMarketFeeSpreadDepthResolutionGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        high_fee_drag_count=_non_pass_reason_count(rows, "gate_fee_drag"),
        wide_spread_count=_non_pass_reason_count(rows, "gate_spread_width"),
        thin_depth_count=_non_pass_reason_count(rows, "gate_available_depth"),
        high_resolution_friction_count=_non_pass_reason_count(
            rows,
            "gate_resolution_friction",
        ),
        delayed_settlement_count=_non_pass_reason_count(
            rows,
            "gate_settlement_timing",
        ),
        average_gate_score=_average_row_decimal(rows, "gate_score"),
        min_available_depth=_min_row_decimal(rows, "available_depth"),
        max_fee_drag_ratio=_max_row_decimal(rows, "fee_drag_ratio"),
        max_spread_width_ratio=_max_row_decimal(rows, "spread_width_ratio"),
        max_resolution_friction_ratio=_max_row_decimal(
            rows,
            "resolution_friction_ratio",
        ),
        max_settlement_delay_hours=_max_row_decimal(rows, "settlement_delay_hours"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_spread_depth_resolution_gate_report_payload(
    report: ResearchMarketFeeSpreadDepthResolutionGateReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeSpreadDepthResolutionGateReport:
        raise ValueError(
            "report must be a ResearchMarketFeeSpreadDepthResolutionGateReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_spread_depth_resolution_gate_report_payload(payload)
    return payload


def validate_research_market_fee_spread_depth_resolution_gate_report_payload(
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
    value: ResearchMarketFeeSpreadDepthResolutionGateInput,
    *,
    config: ResearchMarketFeeSpreadDepthResolutionGateConfig,
    public_row_ref: str,
) -> ResearchMarketFeeSpreadDepthResolutionGateRow:
    fee_drag_score = _score_for_maximum(
        value.fee_drag_ratio,
        config.maximum_pass_fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    spread_width_score = _score_for_maximum(
        value.spread_width_ratio,
        config.maximum_pass_spread_width_ratio,
        config.maximum_watch_spread_width_ratio,
    )
    available_depth_score = _score_for_minimum(
        value.available_depth,
        config.minimum_pass_available_depth,
        config.minimum_watch_available_depth,
    )
    resolution_friction_score = _score_for_maximum(
        value.resolution_friction_ratio,
        config.maximum_pass_resolution_friction_ratio,
        config.maximum_watch_resolution_friction_ratio,
    )
    settlement_timing_score = _score_for_maximum(
        value.settlement_delay_hours,
        config.maximum_pass_settlement_delay_hours,
        config.maximum_watch_settlement_delay_hours,
    )
    gate_score = _gate_score(
        fee_drag_score=fee_drag_score,
        spread_width_score=spread_width_score,
        available_depth_score=available_depth_score,
        resolution_friction_score=resolution_friction_score,
        settlement_timing_score=settlement_timing_score,
        config=config,
    )
    component_statuses = (
        _status_for_maximum(
            value.fee_drag_ratio,
            config.maximum_pass_fee_drag_ratio,
            config.maximum_watch_fee_drag_ratio,
        ),
        _status_for_maximum(
            value.spread_width_ratio,
            config.maximum_pass_spread_width_ratio,
            config.maximum_watch_spread_width_ratio,
        ),
        _status_for_minimum(
            value.available_depth,
            config.minimum_pass_available_depth,
            config.minimum_watch_available_depth,
        ),
        _status_for_maximum(
            value.resolution_friction_ratio,
            config.maximum_pass_resolution_friction_ratio,
            config.maximum_watch_resolution_friction_ratio,
        ),
        _status_for_maximum(
            value.settlement_delay_hours,
            config.maximum_pass_settlement_delay_hours,
            config.maximum_watch_settlement_delay_hours,
        ),
    )
    status = _gate_status(
        component_statuses=component_statuses,
        gate_score=gate_score,
        config=config,
    )
    return ResearchMarketFeeSpreadDepthResolutionGateRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        fee_drag_ratio=value.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        spread_width_ratio=value.spread_width_ratio,
        spread_width_score=spread_width_score,
        available_depth=value.available_depth,
        available_depth_score=available_depth_score,
        resolution_friction_ratio=value.resolution_friction_ratio,
        resolution_friction_score=resolution_friction_score,
        settlement_delay_hours=value.settlement_delay_hours,
        settlement_timing_score=settlement_timing_score,
        gate_score=gate_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            fee_drag_status=component_statuses[0],
            spread_width_status=component_statuses[1],
            available_depth_status=component_statuses[2],
            resolution_friction_status=component_statuses[3],
            settlement_timing_status=component_statuses[4],
        ),
    )


def _gate_score(
    *,
    fee_drag_score: Decimal,
    spread_width_score: Decimal,
    available_depth_score: Decimal,
    resolution_friction_score: Decimal,
    settlement_timing_score: Decimal,
    config: ResearchMarketFeeSpreadDepthResolutionGateConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            fee_drag_score * config.fee_drag_weight
            + spread_width_score * config.spread_width_weight
            + available_depth_score * config.available_depth_weight
            + resolution_friction_score * config.resolution_friction_weight
            + settlement_timing_score * config.settlement_timing_weight,
        )


def _gate_status(
    *,
    component_statuses: tuple[str, ...],
    gate_score: Decimal,
    config: ResearchMarketFeeSpreadDepthResolutionGateConfig,
) -> str:
    if BLOCK_STATUS in component_statuses or gate_score < config.minimum_watch_gate_score:
        return BLOCK_STATUS
    if WATCH_STATUS in component_statuses or gate_score < config.minimum_pass_gate_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    fee_drag_status: str,
    spread_width_status: str,
    available_depth_status: str,
    resolution_friction_status: str,
    settlement_timing_status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in input_reason_codes]
    reason_codes.extend(
        (
            f"gate_status_{status}",
            f"gate_fee_drag_{fee_drag_status}",
            f"gate_spread_width_{spread_width_status}",
            f"gate_available_depth_{available_depth_status}",
            f"gate_resolution_friction_{resolution_friction_status}",
            f"gate_settlement_timing_{settlement_timing_status}",
        ),
    )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


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
    if value > watch_value:
        return BLOCK_STATUS
    if value > pass_value:
        return WATCH_STATUS
    return PASS_STATUS


def _status_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value < watch_value:
        return BLOCK_STATUS
    if value < pass_value:
        return WATCH_STATUS
    return PASS_STATUS


def _normalize_inputs(
    inputs: Iterable[ResearchMarketFeeSpreadDepthResolutionGateInput],
) -> tuple[ResearchMarketFeeSpreadDepthResolutionGateInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketFeeSpreadDepthResolutionGateInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeSpreadDepthResolutionGateInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketFeeSpreadDepthResolutionGateRow],
) -> tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketFeeSpreadDepthResolutionGateRow:
            raise ValueError("rows must contain ResearchMarketFeeSpreadDepthResolutionGateRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount],
) -> tuple[ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount",
            )
        _require_hard_flags("reason_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(
    row: ResearchMarketFeeSpreadDepthResolutionGateRow,
) -> None:
    if f"gate_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketFeeSpreadDepthResolutionGateReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.high_fee_drag_count != _non_pass_reason_count(
        report.rows,
        "gate_fee_drag",
    ):
        raise ValueError("high_fee_drag_count must match rows")
    if report.wide_spread_count != _non_pass_reason_count(
        report.rows,
        "gate_spread_width",
    ):
        raise ValueError("wide_spread_count must match rows")
    if report.thin_depth_count != _non_pass_reason_count(
        report.rows,
        "gate_available_depth",
    ):
        raise ValueError("thin_depth_count must match rows")
    if report.high_resolution_friction_count != _non_pass_reason_count(
        report.rows,
        "gate_resolution_friction",
    ):
        raise ValueError("high_resolution_friction_count must match rows")
    if report.delayed_settlement_count != _non_pass_reason_count(
        report.rows,
        "gate_settlement_timing",
    ):
        raise ValueError("delayed_settlement_count must match rows")
    if report.average_gate_score != _average_row_decimal(report.rows, "gate_score"):
        raise ValueError("average_gate_score must match rows")
    if report.min_available_depth != _min_row_decimal(report.rows, "available_depth"):
        raise ValueError("min_available_depth must match rows")
    if report.max_fee_drag_ratio != _max_row_decimal(report.rows, "fee_drag_ratio"):
        raise ValueError("max_fee_drag_ratio must match rows")
    if report.max_spread_width_ratio != _max_row_decimal(
        report.rows,
        "spread_width_ratio",
    ):
        raise ValueError("max_spread_width_ratio must match rows")
    if report.max_resolution_friction_ratio != _max_row_decimal(
        report.rows,
        "resolution_friction_ratio",
    ):
        raise ValueError("max_resolution_friction_ratio must match rows")
    if report.max_settlement_delay_hours != _max_row_decimal(
        report.rows,
        "settlement_delay_hours",
    ):
        raise ValueError("max_settlement_delay_hours must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("gate_no_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_code_counts(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
) -> tuple[ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in _report_reason_codes(rows):
        counts[reason_code] = ZERO
    if not rows:
        counts["gate_no_inputs"] = ONE
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
    reason_prefix: str,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                f"{reason_prefix}_{WATCH_STATUS}" in row.reason_codes
                or f"{reason_prefix}_{BLOCK_STATUS}" in row.reason_codes
            )
        ),
    )


def _max_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthResolutionGateRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _weight_sum(config: ResearchMarketFeeSpreadDepthResolutionGateConfig) -> Decimal:
    return _quantize_decimal(
        config.fee_drag_weight
        + config.spread_width_weight
        + config.available_depth_weight
        + config.resolution_friction_weight
        + config.settlement_timing_weight,
    )


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
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


def _require_private_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public label")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public payload")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if type(value) is str and "-" in value:
        raise ValueError(f"{field_name} must use underscores")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FEE_SPREAD_DEPTH_RESOLUTION_GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


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
    row: ResearchMarketFeeSpreadDepthResolutionGateRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], row.gate_score, row.public_row_ref)


def _private_digest(*parts: str) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _public_row_ref(index: int) -> str:
    return f"gate_group_{index:03d}"


def _report_derived_validation_digest(
    report: ResearchMarketFeeSpreadDepthResolutionGateReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketFeeSpreadDepthResolutionGateReport,
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
    return sha256(encoded_payload.encode("utf-8")).hexdigest()


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value_label: str, value: object, path: str = "") -> None:
    current_path = path or value_label
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(value_label, asdict(value), current_path)
        return
    if type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{value_label} has unsafe public numeric payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{value_label} has unsafe public payload")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"{value_label} has unsafe public payload at {current_path}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{current_path}.{key} must be True")
            _reject_unsafe_public_payload(value_label, item, f"{current_path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(value_label, item, f"{current_path}[{index}]")
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
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
