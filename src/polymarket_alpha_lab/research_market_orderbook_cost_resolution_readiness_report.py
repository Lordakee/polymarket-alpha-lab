"""Report-only sanitized book cost and resolution readiness reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ORDERBOOK_COST_RESOLUTION_READINESS_STATUSES",
    "DEFAULT_RESEARCH_MARKET_ORDERBOOK_COST_RESOLUTION_READINESS_REPORT_CONFIG_VERSION",
    "ResearchMarketOrderbookCostResolutionReadinessConfig",
    "ResearchMarketOrderbookCostResolutionReadinessInput",
    "ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount",
    "ResearchMarketOrderbookCostResolutionReadinessReport",
    "ResearchMarketOrderbookCostResolutionReadinessRow",
    "build_research_market_orderbook_cost_resolution_readiness_report",
    "research_market_orderbook_cost_resolution_readiness_report_digest",
    "research_market_orderbook_cost_resolution_readiness_report_payload",
)


DEFAULT_RESEARCH_MARKET_ORDERBOOK_COST_RESOLUTION_READINESS_REPORT_CONFIG_VERSION = (
    "book-cost-resolution-readiness-report-v0"
)
ORDERBOOK_COST_RESOLUTION_READINESS_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("exec", "ution"),
    _join_parts("li", "ve"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    "://",
)

SUMMARY_REASON_PRIORITY = (
    "depth_stability_block",
    "spread_width_block",
    "fee_drag_block",
    "slippage_pressure_block",
    "settlement_friction_block",
    "resolution_window_block",
    "depth_stability_watch",
    "spread_width_watch",
    "fee_drag_watch",
    "slippage_pressure_watch",
    "settlement_friction_watch",
    "resolution_window_watch",
)


@dataclass(frozen=True)
class ResearchMarketOrderbookCostResolutionReadinessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_ORDERBOOK_COST_RESOLUTION_READINESS_REPORT_CONFIG_VERSION
    )
    minimum_pass_depth_stability_ratio: Decimal = Decimal("0.800000")
    minimum_watch_depth_stability_ratio: Decimal = Decimal("0.500000")
    maximum_pass_spread_ratio: Decimal = Decimal("0.020000")
    maximum_watch_spread_ratio: Decimal = Decimal("0.060000")
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    maximum_pass_slippage_pressure_ratio: Decimal = Decimal("0.020000")
    maximum_watch_slippage_pressure_ratio: Decimal = Decimal("0.080000")
    maximum_pass_settlement_friction_ratio: Decimal = Decimal("0.100000")
    maximum_watch_settlement_friction_ratio: Decimal = Decimal("0.300000")
    maximum_pass_resolution_window_risk_ratio: Decimal = Decimal("0.100000")
    maximum_watch_resolution_window_risk_ratio: Decimal = Decimal("0.400000")
    depth_stability_weight: Decimal = Decimal("0.250000")
    spread_weight: Decimal = Decimal("0.200000")
    fee_drag_weight: Decimal = Decimal("0.150000")
    slippage_pressure_weight: Decimal = Decimal("0.200000")
    settlement_friction_weight: Decimal = Decimal("0.100000")
    resolution_window_weight: Decimal = Decimal("0.100000")
    minimum_pass_readiness_score: Decimal = Decimal("0.750000")
    minimum_watch_readiness_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookCostResolutionReadinessConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_ORDERBOOK_COST_RESOLUTION_READINESS_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_depth_stability_ratio",
            "minimum_watch_depth_stability_ratio",
            "maximum_pass_spread_ratio",
            "maximum_watch_spread_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "maximum_pass_slippage_pressure_ratio",
            "maximum_watch_slippage_pressure_ratio",
            "maximum_pass_settlement_friction_ratio",
            "maximum_watch_settlement_friction_ratio",
            "maximum_pass_resolution_window_risk_ratio",
            "maximum_watch_resolution_window_risk_ratio",
            "depth_stability_weight",
            "spread_weight",
            "fee_drag_weight",
            "slippage_pressure_weight",
            "settlement_friction_weight",
            "resolution_window_weight",
            "minimum_pass_readiness_score",
            "minimum_watch_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.minimum_pass_depth_stability_ratio
            <= self.minimum_watch_depth_stability_ratio
        ):
            raise ValueError("minimum_pass_depth_stability_ratio must exceed watch")
        for field_name in (
            "maximum_pass_spread_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_pass_slippage_pressure_ratio",
            "maximum_pass_settlement_friction_ratio",
            "maximum_pass_resolution_window_risk_ratio",
        ):
            watch_name = field_name.replace("maximum_pass", "maximum_watch")
            if getattr(self, field_name) >= getattr(self, watch_name):
                raise ValueError(f"{field_name} must be below watch")
        if self.minimum_pass_readiness_score <= self.minimum_watch_readiness_score:
            raise ValueError("minimum_pass_readiness_score must exceed watch")
        weight_sum = _quantize(
            self.depth_stability_weight
            + self.spread_weight
            + self.fee_drag_weight
            + self.slippage_pressure_weight
            + self.settlement_friction_weight
            + self.resolution_window_weight,
        )
        if weight_sum != ONE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookCostResolutionReadinessInput:
    public_readiness_ref: str
    observed_at: datetime
    depth_stability_ratio: Decimal
    spread_ratio: Decimal
    fee_drag_ratio: Decimal
    slippage_pressure_ratio: Decimal
    settlement_friction_ratio: Decimal
    resolution_window_risk_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookCostResolutionReadinessInput,
            "input",
        )
        _require_public_label("public_readiness_ref", self.public_readiness_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "depth_stability_ratio",
            "spread_ratio",
            "fee_drag_ratio",
            "slippage_pressure_ratio",
            "settlement_friction_ratio",
            "resolution_window_risk_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookCostResolutionReadinessRow:
    public_readiness_ref: str
    observed_at: datetime
    depth_stability_ratio: Decimal
    depth_stability_score: Decimal
    spread_ratio: Decimal
    spread_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    slippage_pressure_ratio: Decimal
    slippage_pressure_score: Decimal
    settlement_friction_ratio: Decimal
    settlement_friction_score: Decimal
    resolution_window_risk_ratio: Decimal
    resolution_window_score: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookCostResolutionReadinessRow,
            "row",
        )
        _require_public_label("public_readiness_ref", self.public_readiness_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "depth_stability_ratio",
            "depth_stability_score",
            "spread_ratio",
            "spread_score",
            "fee_drag_ratio",
            "fee_drag_score",
            "slippage_pressure_ratio",
            "slippage_pressure_score",
            "settlement_friction_ratio",
            "settlement_friction_score",
            "resolution_window_risk_ratio",
            "resolution_window_score",
            "readiness_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookCostResolutionReadinessReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal | None
    min_depth_stability_ratio: Decimal
    max_spread_ratio: Decimal
    max_fee_drag_ratio: Decimal
    max_slippage_pressure_ratio: Decimal
    max_settlement_friction_ratio: Decimal
    max_resolution_window_risk_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookCostResolutionReadinessReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
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
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_readiness_score is not None:
            object.__setattr__(
                self,
                "average_readiness_score",
                _require_ratio_decimal(
                    "average_readiness_score",
                    self.average_readiness_score,
                ),
            )
        for field_name in (
            "min_depth_stability_ratio",
            "max_spread_ratio",
            "max_fee_drag_ratio",
            "max_slippage_pressure_ratio",
            "max_settlement_friction_ratio",
            "max_resolution_window_risk_ratio",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_orderbook_cost_resolution_readiness_report_payload(self)


def build_research_market_orderbook_cost_resolution_readiness_report(
    inputs: Iterable[ResearchMarketOrderbookCostResolutionReadinessInput],
    *,
    config: ResearchMarketOrderbookCostResolutionReadinessConfig,
    generated_at: datetime,
) -> ResearchMarketOrderbookCostResolutionReadinessReport:
    if type(config) is not ResearchMarketOrderbookCostResolutionReadinessConfig:
        raise ValueError(
            "config must be a ResearchMarketOrderbookCostResolutionReadinessConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs, generated_at_utc)
    rows = tuple(
        _row_for_input(item, config=config)
        for item in sorted(normalized, key=lambda item: item.public_readiness_ref)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_readiness_score": _average_readiness_score(rows),
        "min_depth_stability_ratio": _minimum_row_value(
            rows,
            "depth_stability_ratio",
        ),
        "max_spread_ratio": _maximum_row_value(rows, "spread_ratio"),
        "max_fee_drag_ratio": _maximum_row_value(rows, "fee_drag_ratio"),
        "max_slippage_pressure_ratio": _maximum_row_value(
            rows,
            "slippage_pressure_ratio",
        ),
        "max_settlement_friction_ratio": _maximum_row_value(
            rows,
            "settlement_friction_ratio",
        ),
        "max_resolution_window_risk_ratio": _maximum_row_value(
            rows,
            "resolution_window_risk_ratio",
        ),
        "status": _summary_status(rows),
        "reason_codes": _summary_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketOrderbookCostResolutionReadinessReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_orderbook_cost_resolution_readiness_report_payload(
    value: ResearchMarketOrderbookCostResolutionReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketOrderbookCostResolutionReadinessReport:
        _require_hard_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchMarketOrderbookCostResolutionReadinessReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_hard_flags("payload", payload, require_here=True)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_market_orderbook_cost_resolution_readiness_report_digest(
    report: ResearchMarketOrderbookCostResolutionReadinessReport,
) -> str:
    if type(report) is not ResearchMarketOrderbookCostResolutionReadinessReport:
        raise ValueError(
            "report must be a ResearchMarketOrderbookCostResolutionReadinessReport",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")
    return report.derived_validation_digest


def _row_for_input(
    item: ResearchMarketOrderbookCostResolutionReadinessInput,
    *,
    config: ResearchMarketOrderbookCostResolutionReadinessConfig,
) -> ResearchMarketOrderbookCostResolutionReadinessRow:
    depth_stability_score = _direct_score(
        item.depth_stability_ratio,
        pass_value=config.minimum_pass_depth_stability_ratio,
        watch_value=config.minimum_watch_depth_stability_ratio,
    )
    spread_score = _inverse_score(
        item.spread_ratio,
        pass_value=config.maximum_pass_spread_ratio,
        watch_value=config.maximum_watch_spread_ratio,
    )
    fee_drag_score = _inverse_score(
        item.fee_drag_ratio,
        pass_value=config.maximum_pass_fee_drag_ratio,
        watch_value=config.maximum_watch_fee_drag_ratio,
    )
    slippage_pressure_score = _inverse_score(
        item.slippage_pressure_ratio,
        pass_value=config.maximum_pass_slippage_pressure_ratio,
        watch_value=config.maximum_watch_slippage_pressure_ratio,
    )
    settlement_friction_score = _inverse_score(
        item.settlement_friction_ratio,
        pass_value=config.maximum_pass_settlement_friction_ratio,
        watch_value=config.maximum_watch_settlement_friction_ratio,
    )
    resolution_window_score = _inverse_score(
        item.resolution_window_risk_ratio,
        pass_value=config.maximum_pass_resolution_window_risk_ratio,
        watch_value=config.maximum_watch_resolution_window_risk_ratio,
    )
    readiness_score = _weighted_readiness_score(
        depth_stability_score=depth_stability_score,
        spread_score=spread_score,
        fee_drag_score=fee_drag_score,
        slippage_pressure_score=slippage_pressure_score,
        settlement_friction_score=settlement_friction_score,
        resolution_window_score=resolution_window_score,
        config=config,
    )
    component_codes = _component_reason_codes(item, config)
    status = _row_status(readiness_score, component_codes, config)
    return ResearchMarketOrderbookCostResolutionReadinessRow(
        public_readiness_ref=item.public_readiness_ref,
        observed_at=item.observed_at,
        depth_stability_ratio=item.depth_stability_ratio,
        depth_stability_score=depth_stability_score,
        spread_ratio=item.spread_ratio,
        spread_score=spread_score,
        fee_drag_ratio=item.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        slippage_pressure_ratio=item.slippage_pressure_ratio,
        slippage_pressure_score=slippage_pressure_score,
        settlement_friction_ratio=item.settlement_friction_ratio,
        settlement_friction_score=settlement_friction_score,
        resolution_window_risk_ratio=item.resolution_window_risk_ratio,
        resolution_window_score=resolution_window_score,
        readiness_score=readiness_score,
        status=status,
        reason_codes=_row_reason_codes(status, component_codes, item.reason_codes),
    )


def _component_reason_codes(
    item: ResearchMarketOrderbookCostResolutionReadinessInput,
    config: ResearchMarketOrderbookCostResolutionReadinessConfig,
) -> tuple[str, ...]:
    return (
        _low_value_component_reason(
            prefix="depth_stability",
            value=item.depth_stability_ratio,
            pass_threshold=config.minimum_pass_depth_stability_ratio,
            block_threshold=config.minimum_watch_depth_stability_ratio,
        ),
        _high_value_component_reason(
            prefix="spread_width",
            value=item.spread_ratio,
            pass_threshold=config.maximum_pass_spread_ratio,
            block_threshold=config.maximum_watch_spread_ratio,
        ),
        _high_value_component_reason(
            prefix="fee_drag",
            value=item.fee_drag_ratio,
            pass_threshold=config.maximum_pass_fee_drag_ratio,
            block_threshold=config.maximum_watch_fee_drag_ratio,
        ),
        _high_value_component_reason(
            prefix="slippage_pressure",
            value=item.slippage_pressure_ratio,
            pass_threshold=config.maximum_pass_slippage_pressure_ratio,
            block_threshold=config.maximum_watch_slippage_pressure_ratio,
        ),
        _high_value_component_reason(
            prefix="settlement_friction",
            value=item.settlement_friction_ratio,
            pass_threshold=config.maximum_pass_settlement_friction_ratio,
            block_threshold=config.maximum_watch_settlement_friction_ratio,
        ),
        _high_value_component_reason(
            prefix="resolution_window",
            value=item.resolution_window_risk_ratio,
            pass_threshold=config.maximum_pass_resolution_window_risk_ratio,
            block_threshold=config.maximum_watch_resolution_window_risk_ratio,
        ),
    )


def _row_status(
    readiness_score: Decimal,
    component_codes: tuple[str, ...],
    config: ResearchMarketOrderbookCostResolutionReadinessConfig,
) -> str:
    if any(code.endswith("_block") for code in component_codes):
        return "block"
    if readiness_score < config.minimum_watch_readiness_score:
        return "block"
    if any(code.endswith("_watch") for code in component_codes):
        return "watch"
    if readiness_score < config.minimum_pass_readiness_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    status: str,
    component_codes: tuple[str, ...],
    input_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(
            (f"book_readiness_{status}",)
            + component_codes
            + tuple(f"input_{code}" for code in input_codes),
        )),
        allow_empty=False,
    )


def _summary_status(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_book_readiness_inputs",)
    status = _summary_status(rows)
    row_codes = {code for row in rows for code in row.reason_codes}
    codes = [f"book_readiness_{status}"]
    codes.extend(code for code in SUMMARY_REASON_PRIORITY if code in row_codes)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
) -> tuple[ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount(
                reason_code="no_book_readiness_inputs",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter(code for row in rows for code in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount(
            reason_code=code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / row_count),
        )
        for code, count in sorted(counter.items(), key=lambda item: _reason_sort_key(item[0]))
    )


def _low_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _high_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value > block_threshold:
        return f"{prefix}_block"
    if value > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _direct_score(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value >= pass_value:
        return ONE
    if value <= watch_value:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize((value - watch_value) / (pass_value - watch_value))


def _inverse_score(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value <= pass_value:
        return ONE
    if value >= watch_value:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize((watch_value - value) / (watch_value - pass_value))


def _weighted_readiness_score(
    *,
    depth_stability_score: Decimal,
    spread_score: Decimal,
    fee_drag_score: Decimal,
    slippage_pressure_score: Decimal,
    settlement_friction_score: Decimal,
    resolution_window_score: Decimal,
    config: ResearchMarketOrderbookCostResolutionReadinessConfig,
) -> Decimal:
    return _quantize(
        depth_stability_score * config.depth_stability_weight
        + spread_score * config.spread_weight
        + fee_drag_score * config.fee_drag_weight
        + slippage_pressure_score * config.slippage_pressure_weight
        + settlement_friction_score * config.settlement_friction_weight
        + resolution_window_score * config.resolution_window_weight,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketOrderbookCostResolutionReadinessInput],
    generated_at: datetime,
) -> tuple[ResearchMarketOrderbookCostResolutionReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketOrderbookCostResolutionReadinessInput:
            raise ValueError(
                "inputs must contain ResearchMarketOrderbookCostResolutionReadinessInput values",
            )
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if value.public_readiness_ref in seen:
            raise ValueError("public_readiness_ref values must be unique")
        seen.add(value.public_readiness_ref)
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
) -> tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketOrderbookCostResolutionReadinessRow:
            raise ValueError(
                "rows must contain ResearchMarketOrderbookCostResolutionReadinessRow values",
            )
    return rows


def _normalize_reason_code_counts(
    counts: tuple[
        ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount values",
            )
    return counts


def _status_count(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_readiness_score(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext() as context:
        context.prec = 28
        return _quantize(sum(row.readiness_score for row in rows) / Decimal(len(rows)))


def _minimum_row_value(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchMarketOrderbookCostResolutionReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _validate_report(report: ResearchMarketOrderbookCostResolutionReadinessReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must equal row count")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must equal block rows")
    if report.average_readiness_score != _average_readiness_score(rows):
        raise ValueError("average_readiness_score must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    expected = _payload_derived_validation_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _derived_validation_digest(values: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            {
                key: _json_ready(value)
                for key, value in values.items()
                if key != "derived_validation_digest"
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketOrderbookCostResolutionReadinessReport,
) -> str:
    return _payload_derived_validation_digest(_json_ready(report))


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            {
                key: value
                for key, value in payload.items()
                if key != "derived_validation_digest"
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return _format_decimal(value)
    if type(value) is datetime:
        return value.isoformat()
    return value


def _format_decimal(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value().quantize(QUANTUM):
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    _reject_unsafe_text(name, value)
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    _reject_unsafe_text(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(dict.fromkeys(_require_reason_code(name, value) for value in values))
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in ORDERBOOK_COST_RESOLUTION_READINESS_STATUSES:
        raise ValueError(f"{name} must be a valid status")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{label} {flag} must be True")


def _require_payload_hard_flags(
    label: str,
    value: object,
    *,
    require_here: bool = False,
) -> None:
    if type(value) is dict:
        if require_here or any(flag in value for flag in ("paper_only", "report_only", "readonly")):
            for flag in ("paper_only", "report_only", "readonly"):
                if value.get(flag) is not True:
                    raise ValueError(f"{label} {flag} must be True")
        for item in value.values():
            _require_payload_hard_flags(label, item)
    elif type(value) is list:
        for item in value:
            _require_payload_hard_flags(label, item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for text in _walk_public_text(value):
        _reject_unsafe_text(label, text)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{label} contains unsafe public payload fragment")


def _walk_public_text(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        values: list[str] = []
        for field in fields(value):
            values.append(field.name)
            values.extend(_walk_public_text(getattr(value, field.name)))
        return tuple(values)
    if type(value) is dict:
        values = []
        for key, item in value.items():
            values.append(str(key))
            values.extend(_walk_public_text(item))
        return tuple(values)
    if type(value) in (tuple, list):
        values = []
        for item in value:
            values.extend(_walk_public_text(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    priority = (
        "book_readiness_block",
        "book_readiness_watch",
        "book_readiness_pass",
        *SUMMARY_REASON_PRIORITY,
    )
    try:
        return (priority.index(reason_code), reason_code)
    except ValueError:
        return (len(priority), reason_code)
