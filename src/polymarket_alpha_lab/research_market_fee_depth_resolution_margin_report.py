"""Pure report-only fee/depth/resolution margin reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "FEE_DEPTH_RESOLUTION_MARGIN_STATUSES",
    "DEFAULT_RESEARCH_MARKET_FEE_DEPTH_RESOLUTION_MARGIN_REPORT_CONFIG_VERSION",
    "ResearchMarketFeeDepthResolutionMarginConfig",
    "ResearchMarketFeeDepthResolutionMarginInput",
    "ResearchMarketFeeDepthResolutionMarginReasonCodeCount",
    "ResearchMarketFeeDepthResolutionMarginReport",
    "ResearchMarketFeeDepthResolutionMarginRow",
    "build_research_market_fee_depth_resolution_margin_report",
    "research_market_fee_depth_resolution_margin_report_payload",
    "validate_research_market_fee_depth_resolution_margin_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_DEPTH_RESOLUTION_MARGIN_REPORT_CONFIG_VERSION = (
    "research-market-fee-depth-resolution-margin-report-v1"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
FEE_DEPTH_RESOLUTION_MARGIN_STATUSES = (
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
class ResearchMarketFeeDepthResolutionMarginConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_DEPTH_RESOLUTION_MARGIN_REPORT_CONFIG_VERSION
    )
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    minimum_pass_available_depth: Decimal = Decimal("1000.000000")
    minimum_watch_available_depth: Decimal = Decimal("250.000000")
    minimum_pass_resolution_margin_ratio: Decimal = Decimal("0.100000")
    minimum_watch_resolution_margin_ratio: Decimal = Decimal("0.030000")
    minimum_pass_margin_score: Decimal = Decimal("0.750000")
    minimum_watch_margin_score: Decimal = Decimal("0.450000")
    fee_drag_weight: Decimal = Decimal("0.300000")
    available_depth_weight: Decimal = Decimal("0.350000")
    resolution_margin_weight: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthResolutionMarginConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_DEPTH_RESOLUTION_MARGIN_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "minimum_pass_resolution_margin_ratio",
            "minimum_watch_resolution_margin_ratio",
            "minimum_pass_margin_score",
            "minimum_watch_margin_score",
            "fee_drag_weight",
            "available_depth_weight",
            "resolution_margin_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_available_depth",
            "minimum_watch_available_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.minimum_pass_available_depth < self.minimum_watch_available_depth:
            raise ValueError("minimum_pass_available_depth must be at least watch")
        if (
            self.minimum_pass_resolution_margin_ratio
            < self.minimum_watch_resolution_margin_ratio
        ):
            raise ValueError(
                "minimum_pass_resolution_margin_ratio must be at least watch",
            )
        if self.minimum_pass_margin_score < self.minimum_watch_margin_score:
            raise ValueError("minimum_pass_margin_score must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthResolutionMarginInput:
    private_signal_ref: str
    observed_at: datetime
    fee_drag_ratio: Decimal
    available_depth: Decimal
    resolution_margin_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthResolutionMarginInput, "input")
        _require_private_ref("private_signal_ref", self.private_signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("fee_drag_ratio", "resolution_margin_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthResolutionMarginRow:
    public_row_ref: str
    observed_at: datetime
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    available_depth: Decimal
    available_depth_score: Decimal
    resolution_margin_ratio: Decimal
    resolution_margin_score: Decimal
    margin_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthResolutionMarginRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        for field_name in (
            "fee_drag_ratio",
            "fee_drag_score",
            "available_depth_score",
            "resolution_margin_ratio",
            "resolution_margin_score",
            "margin_score",
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
class ResearchMarketFeeDepthResolutionMarginReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeDepthResolutionMarginReasonCodeCount,
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
class ResearchMarketFeeDepthResolutionMarginReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_fee_drag_count: Decimal
    thin_depth_count: Decimal
    low_resolution_margin_count: Decimal
    average_margin_score: Decimal
    min_available_depth: Decimal
    max_fee_drag_ratio: Decimal
    min_resolution_margin_ratio: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeDepthResolutionMarginReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthResolutionMarginReport, "report")
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
            "thin_depth_count",
            "low_resolution_margin_count",
            "min_available_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_margin_score",
            "max_fee_drag_ratio",
            "min_resolution_margin_ratio",
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
        return research_market_fee_depth_resolution_margin_report_payload(self)


def build_research_market_fee_depth_resolution_margin_report(
    inputs: Iterable[ResearchMarketFeeDepthResolutionMarginInput],
    *,
    config: ResearchMarketFeeDepthResolutionMarginConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDepthResolutionMarginReport:
    if type(config) is not ResearchMarketFeeDepthResolutionMarginConfig:
        raise ValueError("config must be a ResearchMarketFeeDepthResolutionMarginConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            ((_private_digest(value.private_signal_ref), value) for value in normalized),
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
    return ResearchMarketFeeDepthResolutionMarginReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        high_fee_drag_count=_non_pass_reason_count(rows, "margin_fee_drag"),
        thin_depth_count=_non_pass_reason_count(rows, "margin_available_depth"),
        low_resolution_margin_count=_non_pass_reason_count(
            rows,
            "margin_resolution_margin",
        ),
        average_margin_score=_average_row_decimal(rows, "margin_score"),
        min_available_depth=_min_row_decimal(rows, "available_depth"),
        max_fee_drag_ratio=_max_row_decimal(rows, "fee_drag_ratio"),
        min_resolution_margin_ratio=_min_row_decimal(rows, "resolution_margin_ratio"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_depth_resolution_margin_report_payload(
    report: ResearchMarketFeeDepthResolutionMarginReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeDepthResolutionMarginReport:
        raise ValueError("report must be a ResearchMarketFeeDepthResolutionMarginReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_depth_resolution_margin_report_payload(payload)
    return payload


def validate_research_market_fee_depth_resolution_margin_report_payload(
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
    value: ResearchMarketFeeDepthResolutionMarginInput,
    *,
    config: ResearchMarketFeeDepthResolutionMarginConfig,
    public_row_ref: str,
) -> ResearchMarketFeeDepthResolutionMarginRow:
    fee_drag_score = _score_for_maximum(
        value.fee_drag_ratio,
        config.maximum_pass_fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    available_depth_score = _score_for_minimum(
        value.available_depth,
        config.minimum_pass_available_depth,
        config.minimum_watch_available_depth,
    )
    resolution_margin_score = _score_for_minimum(
        value.resolution_margin_ratio,
        config.minimum_pass_resolution_margin_ratio,
        config.minimum_watch_resolution_margin_ratio,
    )
    margin_score = _margin_score(
        fee_drag_score=fee_drag_score,
        available_depth_score=available_depth_score,
        resolution_margin_score=resolution_margin_score,
        config=config,
    )
    fee_drag_status = _status_for_maximum(
        value.fee_drag_ratio,
        config.maximum_pass_fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    available_depth_status = _status_for_minimum(
        value.available_depth,
        config.minimum_pass_available_depth,
        config.minimum_watch_available_depth,
    )
    resolution_margin_status = _status_for_minimum(
        value.resolution_margin_ratio,
        config.minimum_pass_resolution_margin_ratio,
        config.minimum_watch_resolution_margin_ratio,
    )
    status = _margin_status(
        component_statuses=(
            fee_drag_status,
            available_depth_status,
            resolution_margin_status,
        ),
        margin_score=margin_score,
        config=config,
    )
    return ResearchMarketFeeDepthResolutionMarginRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        fee_drag_ratio=value.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        available_depth=value.available_depth,
        available_depth_score=available_depth_score,
        resolution_margin_ratio=value.resolution_margin_ratio,
        resolution_margin_score=resolution_margin_score,
        margin_score=margin_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            fee_drag_status=fee_drag_status,
            available_depth_status=available_depth_status,
            resolution_margin_status=resolution_margin_status,
        ),
    )


def _margin_score(
    *,
    fee_drag_score: Decimal,
    available_depth_score: Decimal,
    resolution_margin_score: Decimal,
    config: ResearchMarketFeeDepthResolutionMarginConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            fee_drag_score * config.fee_drag_weight
            + available_depth_score * config.available_depth_weight
            + resolution_margin_score * config.resolution_margin_weight,
        )


def _margin_status(
    *,
    component_statuses: tuple[str, ...],
    margin_score: Decimal,
    config: ResearchMarketFeeDepthResolutionMarginConfig,
) -> str:
    if BLOCK_STATUS in component_statuses or margin_score < config.minimum_watch_margin_score:
        return BLOCK_STATUS
    if WATCH_STATUS in component_statuses or margin_score < config.minimum_pass_margin_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    fee_drag_status: str,
    available_depth_status: str,
    resolution_margin_status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in input_reason_codes]
    reason_codes.extend(
        (
            f"margin_status_{status}",
            f"margin_fee_drag_{fee_drag_status}",
            f"margin_available_depth_{available_depth_status}",
            f"margin_resolution_margin_{resolution_margin_status}",
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
    inputs: Iterable[ResearchMarketFeeDepthResolutionMarginInput],
) -> tuple[ResearchMarketFeeDepthResolutionMarginInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketFeeDepthResolutionMarginInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeDepthResolutionMarginInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketFeeDepthResolutionMarginRow],
) -> tuple[ResearchMarketFeeDepthResolutionMarginRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketFeeDepthResolutionMarginRow:
            raise ValueError("rows must contain ResearchMarketFeeDepthResolutionMarginRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketFeeDepthResolutionMarginReasonCodeCount],
) -> tuple[ResearchMarketFeeDepthResolutionMarginReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketFeeDepthResolutionMarginReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeDepthResolutionMarginReasonCodeCount",
            )
        _require_hard_flags("reason_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: ResearchMarketFeeDepthResolutionMarginRow) -> None:
    if f"margin_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketFeeDepthResolutionMarginReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.high_fee_drag_count != _non_pass_reason_count(
        report.rows,
        "margin_fee_drag",
    ):
        raise ValueError("high_fee_drag_count must match rows")
    if report.thin_depth_count != _non_pass_reason_count(
        report.rows,
        "margin_available_depth",
    ):
        raise ValueError("thin_depth_count must match rows")
    if report.low_resolution_margin_count != _non_pass_reason_count(
        report.rows,
        "margin_resolution_margin",
    ):
        raise ValueError("low_resolution_margin_count must match rows")
    if report.average_margin_score != _average_row_decimal(report.rows, "margin_score"):
        raise ValueError("average_margin_score must match rows")
    if report.min_available_depth != _min_row_decimal(report.rows, "available_depth"):
        raise ValueError("min_available_depth must match rows")
    if report.max_fee_drag_ratio != _max_row_decimal(report.rows, "fee_drag_ratio"):
        raise ValueError("max_fee_drag_ratio must match rows")
    if report.min_resolution_margin_ratio != _min_row_decimal(
        report.rows,
        "resolution_margin_ratio",
    ):
        raise ValueError("min_resolution_margin_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("margin_no_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_code_counts(
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
) -> tuple[ResearchMarketFeeDepthResolutionMarginReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in _report_reason_codes(rows):
        counts[reason_code] = ZERO
    if not rows:
        counts["margin_no_inputs"] = ONE
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketFeeDepthResolutionMarginReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
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
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketFeeDepthResolutionMarginRow, ...],
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


def _weight_sum(config: ResearchMarketFeeDepthResolutionMarginConfig) -> Decimal:
    return _quantize_decimal(
        config.fee_drag_weight
        + config.available_depth_weight
        + config.resolution_margin_weight,
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
    if type(value) is not str or value not in FEE_DEPTH_RESOLUTION_MARGIN_STATUSES:
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
    row: ResearchMarketFeeDepthResolutionMarginRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], row.margin_score, row.public_row_ref)


def _private_digest(*parts: str) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _public_row_ref(index: int) -> str:
    return f"margin_group_{index:03d}"


def _report_derived_validation_digest(
    report: ResearchMarketFeeDepthResolutionMarginReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketFeeDepthResolutionMarginReport,
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
