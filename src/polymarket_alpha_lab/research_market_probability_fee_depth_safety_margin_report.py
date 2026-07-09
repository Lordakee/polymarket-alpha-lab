from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_REPORT_CONFIG_VERSION = (
    "research-market-probability-fee-depth-safety-margin-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_STATUSES = (
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
NO_INPUTS_REASON = "safety_margin_no_inputs"


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
    _join_parts("d", "s", "n"),
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
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("ap", "i", "_", "key"),
    _join_parts("priv", "ate", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
    "://",
    "?",
    "@",
    "=",
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_REPORT_CONFIG_VERSION",
    "PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_STATUSES",
    "ResearchMarketProbabilityFeeDepthSafetyMarginConfig",
    "ResearchMarketProbabilityFeeDepthSafetyMarginInput",
    "ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount",
    "ResearchMarketProbabilityFeeDepthSafetyMarginReport",
    "ResearchMarketProbabilityFeeDepthSafetyMarginRow",
    "build_research_market_probability_fee_depth_safety_margin_report",
    "research_market_probability_fee_depth_safety_margin_report_payload",
    "validate_research_market_probability_fee_depth_safety_margin_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeDepthSafetyMarginConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_REPORT_CONFIG_VERSION
    )
    minimum_pass_probability_edge: Decimal = Decimal("0.080000")
    minimum_watch_probability_edge: Decimal = Decimal("0.030000")
    maximum_pass_fee_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_ratio: Decimal = Decimal("0.030000")
    minimum_pass_available_depth: Decimal = Decimal("1000.000000")
    minimum_watch_available_depth: Decimal = Decimal("250.000000")
    minimum_pass_safety_margin_score: Decimal = Decimal("0.750000")
    minimum_watch_safety_margin_score: Decimal = Decimal("0.450000")
    probability_edge_weight: Decimal = Decimal("0.400000")
    fee_efficiency_weight: Decimal = Decimal("0.250000")
    depth_resilience_weight: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityFeeDepthSafetyMarginConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_probability_edge",
            "minimum_watch_probability_edge",
            "maximum_pass_fee_ratio",
            "maximum_watch_fee_ratio",
            "minimum_pass_safety_margin_score",
            "minimum_watch_safety_margin_score",
            "probability_edge_weight",
            "fee_efficiency_weight",
            "depth_resilience_weight",
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
        if self.minimum_pass_probability_edge < self.minimum_watch_probability_edge:
            raise ValueError("minimum_pass_probability_edge must be at least watch")
        if self.maximum_pass_fee_ratio > self.maximum_watch_fee_ratio:
            raise ValueError("maximum_pass_fee_ratio must not exceed watch")
        if self.minimum_pass_available_depth < self.minimum_watch_available_depth:
            raise ValueError("minimum_pass_available_depth must be at least watch")
        if self.minimum_pass_safety_margin_score < self.minimum_watch_safety_margin_score:
            raise ValueError("minimum_pass_safety_margin_score must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeDepthSafetyMarginInput:
    private_ref: str
    observed_at: datetime
    research_probability: Decimal
    venue_probability: Decimal
    fee_ratio: Decimal
    available_depth: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityFeeDepthSafetyMarginInput, "input")
        _require_private_ref("private_ref", self.private_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "research_probability",
            "venue_probability",
            "fee_ratio",
        ):
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
class ResearchMarketProbabilityFeeDepthSafetyMarginRow:
    public_row_ref: str
    observed_at: datetime
    research_probability: Decimal
    venue_probability: Decimal
    probability_edge: Decimal
    probability_edge_score: Decimal
    fee_ratio: Decimal
    fee_efficiency_score: Decimal
    available_depth: Decimal
    depth_resilience_score: Decimal
    safety_margin_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityFeeDepthSafetyMarginRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "research_probability",
            "venue_probability",
            "probability_edge_score",
            "fee_ratio",
            "fee_efficiency_score",
            "depth_resilience_score",
            "safety_margin_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_edge",
            _require_edge_decimal("probability_edge", self.probability_edge),
        )
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
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
class ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount,
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
class ResearchMarketProbabilityFeeDepthSafetyMarginReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_probability_edge_count: Decimal
    high_fee_count: Decimal
    thin_depth_count: Decimal
    average_safety_margin_score: Decimal
    min_probability_edge: Decimal
    max_fee_ratio: Decimal
    min_available_depth: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityFeeDepthSafetyMarginReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_probability_edge_count",
            "high_fee_count",
            "thin_depth_count",
            "min_available_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_safety_margin_score",
            "max_fee_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_probability_edge",
            _require_edge_decimal("min_probability_edge", self.min_probability_edge),
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
        return research_market_probability_fee_depth_safety_margin_report_payload(self)


def build_research_market_probability_fee_depth_safety_margin_report(
    inputs: Iterable[ResearchMarketProbabilityFeeDepthSafetyMarginInput],
    *,
    config: ResearchMarketProbabilityFeeDepthSafetyMarginConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityFeeDepthSafetyMarginReport:
    if type(config) is not ResearchMarketProbabilityFeeDepthSafetyMarginConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityFeeDepthSafetyMarginConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            ((_private_digest(value.private_ref), value) for value in normalized),
            key=lambda item: item[0],
        ),
    )
    if len({key for key, _ in keyed_inputs}) != len(keyed_inputs):
        raise ValueError("private_ref values must be unique")
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
    return ResearchMarketProbabilityFeeDepthSafetyMarginReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        low_probability_edge_count=_non_pass_reason_count(
            rows,
            "safety_margin_probability_edge",
        ),
        high_fee_count=_non_pass_reason_count(rows, "safety_margin_fee_ratio"),
        thin_depth_count=_non_pass_reason_count(rows, "safety_margin_available_depth"),
        average_safety_margin_score=_average_row_decimal(rows, "safety_margin_score"),
        min_probability_edge=_min_row_decimal(rows, "probability_edge"),
        max_fee_ratio=_max_row_decimal(rows, "fee_ratio"),
        min_available_depth=_min_row_decimal(rows, "available_depth"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_fee_depth_safety_margin_report_payload(
    report: ResearchMarketProbabilityFeeDepthSafetyMarginReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketProbabilityFeeDepthSafetyMarginReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilityFeeDepthSafetyMarginReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_probability_fee_depth_safety_margin_report_payload(payload)
    return payload


def validate_research_market_probability_fee_depth_safety_margin_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _require_payload_status_values(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    value: ResearchMarketProbabilityFeeDepthSafetyMarginInput,
    *,
    config: ResearchMarketProbabilityFeeDepthSafetyMarginConfig,
    public_row_ref: str,
) -> ResearchMarketProbabilityFeeDepthSafetyMarginRow:
    probability_edge = _quantize_decimal(
        value.research_probability - value.venue_probability,
    )
    probability_edge_score = _score_for_minimum(
        probability_edge,
        config.minimum_pass_probability_edge,
        config.minimum_watch_probability_edge,
    )
    fee_efficiency_score = _score_for_maximum(
        value.fee_ratio,
        config.maximum_pass_fee_ratio,
        config.maximum_watch_fee_ratio,
    )
    depth_resilience_score = _score_for_minimum(
        value.available_depth,
        config.minimum_pass_available_depth,
        config.minimum_watch_available_depth,
    )
    safety_margin_score = _safety_margin_score(
        probability_edge_score=probability_edge_score,
        fee_efficiency_score=fee_efficiency_score,
        depth_resilience_score=depth_resilience_score,
        config=config,
    )
    probability_edge_status = _status_for_minimum(
        probability_edge,
        config.minimum_pass_probability_edge,
        config.minimum_watch_probability_edge,
    )
    fee_ratio_status = _status_for_maximum(
        value.fee_ratio,
        config.maximum_pass_fee_ratio,
        config.maximum_watch_fee_ratio,
    )
    available_depth_status = _status_for_minimum(
        value.available_depth,
        config.minimum_pass_available_depth,
        config.minimum_watch_available_depth,
    )
    status = _row_status(
        component_statuses=(
            probability_edge_status,
            fee_ratio_status,
            available_depth_status,
        ),
        score=safety_margin_score,
        config=config,
    )
    return ResearchMarketProbabilityFeeDepthSafetyMarginRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        research_probability=value.research_probability,
        venue_probability=value.venue_probability,
        probability_edge=probability_edge,
        probability_edge_score=probability_edge_score,
        fee_ratio=value.fee_ratio,
        fee_efficiency_score=fee_efficiency_score,
        available_depth=value.available_depth,
        depth_resilience_score=depth_resilience_score,
        safety_margin_score=safety_margin_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            probability_edge_status=probability_edge_status,
            fee_ratio_status=fee_ratio_status,
            available_depth_status=available_depth_status,
        ),
    )


def _safety_margin_score(
    *,
    probability_edge_score: Decimal,
    fee_efficiency_score: Decimal,
    depth_resilience_score: Decimal,
    config: ResearchMarketProbabilityFeeDepthSafetyMarginConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            probability_edge_score * config.probability_edge_weight
            + fee_efficiency_score * config.fee_efficiency_weight
            + depth_resilience_score * config.depth_resilience_weight,
        )


def _row_status(
    *,
    component_statuses: tuple[str, ...],
    score: Decimal,
    config: ResearchMarketProbabilityFeeDepthSafetyMarginConfig,
) -> str:
    if BLOCK_STATUS in component_statuses or score < config.minimum_watch_safety_margin_score:
        return BLOCK_STATUS
    if WATCH_STATUS in component_statuses or score < config.minimum_pass_safety_margin_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    probability_edge_status: str,
    fee_ratio_status: str,
    available_depth_status: str,
) -> tuple[str, ...]:
    reason_codes = [
        _component_reason("probability_edge", probability_edge_status),
        _component_reason("fee_ratio", fee_ratio_status),
        _component_reason("available_depth", available_depth_status),
        f"safety_margin_status_{status}",
    ]
    reason_codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _component_reason(component: str, status: str) -> str:
    return f"safety_margin_{component}_{status}"


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
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes})),
    )


def _report_reason_code_counts(
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
) -> tuple[ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketProbabilityFeeDepthSafetyMarginInput],
) -> tuple[ResearchMarketProbabilityFeeDepthSafetyMarginInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    rows: list[ResearchMarketProbabilityFeeDepthSafetyMarginInput] = []
    try:
        iterator = iter(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    for value in iterator:
        if type(value) is not ResearchMarketProbabilityFeeDepthSafetyMarginInput:
            raise ValueError(
                "inputs must contain ResearchMarketProbabilityFeeDepthSafetyMarginInput",
            )
        _require_hard_flags("input", value)
        rows.append(value)
    return tuple(rows)


def _normalize_rows(
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
) -> tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilityFeeDepthSafetyMarginRow:
            raise ValueError("rows must contain ResearchMarketProbabilityFeeDepthSafetyMarginRow")
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount, ...],
) -> tuple[ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount",
            )
        _require_hard_flags("reason_count", value)
    return tuple(sorted(values, key=lambda value: value.reason_code))


def _row_sort_key(
    row: ResearchMarketProbabilityFeeDepthSafetyMarginRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.safety_margin_score,
        row.public_row_ref,
    )


def _status_count(
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
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
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
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
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _max_row_decimal(
    rows: tuple[ResearchMarketProbabilityFeeDepthSafetyMarginRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _validate_row_consistency(
    row: ResearchMarketProbabilityFeeDepthSafetyMarginRow,
) -> None:
    if f"safety_margin_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.safety_margin_score != ONE:
        raise ValueError("safety_margin_score must match pass status")


def _validate_report_consistency(
    report: ResearchMarketProbabilityFeeDepthSafetyMarginReport,
) -> None:
    rows = report.rows
    expected_pairs = {
        "status": _report_status(rows),
        "input_count": report.row_count,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "low_probability_edge_count": _non_pass_reason_count(
            rows,
            "safety_margin_probability_edge",
        ),
        "high_fee_count": _non_pass_reason_count(rows, "safety_margin_fee_ratio"),
        "thin_depth_count": _non_pass_reason_count(rows, "safety_margin_available_depth"),
        "average_safety_margin_score": _average_row_decimal(rows, "safety_margin_score"),
        "min_probability_edge": _min_row_decimal(rows, "probability_edge"),
        "max_fee_ratio": _max_row_decimal(rows, "fee_ratio"),
        "min_available_depth": _min_row_decimal(rows, "available_depth"),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _report_reason_code_counts(rows),
    }
    for field_name, expected_value in expected_pairs.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _weight_sum(config: ResearchMarketProbabilityFeeDepthSafetyMarginConfig) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            config.probability_edge_weight
            + config.fee_efficiency_weight
            + config.depth_resilience_weight,
        )


def _public_row_ref(index: int) -> str:
    return f"public-row-{index:06d}"


def _private_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketProbabilityFeeDepthSafetyMarginReport,
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
    if value not in PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_edge_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
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


def _require_payload_status_values(value: Any) -> None:
    if isinstance(value, dict):
        for field_name, nested in value.items():
            if field_name == "status":
                _require_status(field_name, nested)
            _require_payload_status_values(nested)
    elif isinstance(value, list):
        for nested in value:
            _require_payload_status_values(nested)


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
