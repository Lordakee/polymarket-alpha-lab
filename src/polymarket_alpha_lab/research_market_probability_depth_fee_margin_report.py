"""Report-only probability depth/fee margin gate."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_FEE_MARGIN_CONFIG_VERSION",
    "ResearchMarketProbabilityDepthFeeMarginConfig",
    "ResearchMarketProbabilityDepthFeeMarginInput",
    "ResearchMarketProbabilityDepthFeeMarginReasonCodeCount",
    "ResearchMarketProbabilityDepthFeeMarginReport",
    "ResearchMarketProbabilityDepthFeeMarginRow",
    "build_research_market_probability_depth_fee_margin_report",
    "research_market_probability_depth_fee_margin_report_payload",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_FEE_MARGIN_CONFIG_VERSION = (
    "research-market-probability-depth-fee-margin-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_probability_depth_fee_margin_inputs"
REASON_PASS = "probability_depth_fee_margin_pass"
REASON_WATCH = "probability_depth_fee_margin_watch"
REASON_BLOCK = "probability_depth_fee_margin_block"
REASON_EDGE_NON_POSITIVE = "model_probability_not_above_market_probability"
REASON_NET_MARGIN_WATCH = "net_probability_margin_watch"
REASON_NET_MARGIN_BLOCK = "net_probability_margin_block"
REASON_TOTAL_DRAG_WATCH = "total_depth_fee_margin_drag_watch"
REASON_TOTAL_DRAG_BLOCK = "total_depth_fee_margin_drag_block"
REASON_DRAG_TO_EDGE_WATCH = "drag_to_edge_ratio_watch"
REASON_DRAG_TO_EDGE_BLOCK = "drag_to_edge_ratio_block"
REASON_DEPTH_COVERAGE_WATCH = "depth_coverage_watch"
REASON_DEPTH_COVERAGE_BLOCK = "depth_coverage_block"
REASON_FEE_RATE_WATCH = "fee_rate_watch"
REASON_FEE_RATE_BLOCK = "fee_rate_block"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_PASS,
    REASON_WATCH,
    REASON_BLOCK,
    REASON_EDGE_NON_POSITIVE,
    REASON_NET_MARGIN_WATCH,
    REASON_NET_MARGIN_BLOCK,
    REASON_TOTAL_DRAG_WATCH,
    REASON_TOTAL_DRAG_BLOCK,
    REASON_DRAG_TO_EDGE_WATCH,
    REASON_DRAG_TO_EDGE_BLOCK,
    REASON_DEPTH_COVERAGE_WATCH,
    REASON_DEPTH_COVERAGE_BLOCK,
    REASON_FEE_RATE_WATCH,
    REASON_FEE_RATE_BLOCK,
)
REASON_CODE_SET = frozenset(REASON_CODES)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "=",
    _join_parts("api", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("candidate", "_", "id"),
    "credential",
    _join_parts("d", "s", "n"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "slug"),
    _join_parts("private", "_", "key"),
    _join_parts("que", "stion"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "market"),
    "secret",
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthFeeMarginConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_FEE_MARGIN_CONFIG_VERSION
    )
    pass_net_probability_margin_rate: Decimal = Decimal("0.030000")
    watch_net_probability_margin_rate: Decimal = Decimal("0.005000")
    watch_total_depth_fee_margin_drag_rate: Decimal = Decimal("0.030000")
    block_total_depth_fee_margin_drag_rate: Decimal = Decimal("0.080000")
    watch_drag_to_edge_ratio: Decimal = Decimal("0.500000")
    block_drag_to_edge_ratio: Decimal = Decimal("1.000000")
    pass_depth_coverage_ratio: Decimal = Decimal("2.000000")
    block_depth_coverage_ratio: Decimal = Decimal("1.000000")
    watch_fee_rate: Decimal = Decimal("0.020000")
    block_fee_rate: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityDepthFeeMarginConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityDepthFeeMarginConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_FEE_MARGIN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_probability_margin_rate",
            "watch_net_probability_margin_rate",
            "watch_total_depth_fee_margin_drag_rate",
            "block_total_depth_fee_margin_drag_rate",
            "watch_drag_to_edge_ratio",
            "block_drag_to_edge_ratio",
            "pass_depth_coverage_ratio",
            "block_depth_coverage_ratio",
            "watch_fee_rate",
            "block_fee_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_net_probability_margin_rate < self.watch_net_probability_margin_rate:
            raise ValueError(
                "pass_net_probability_margin_rate must be at least "
                "watch_net_probability_margin_rate",
            )
        _require_ascending(
            "total_depth_fee_margin_drag_rate",
            self.watch_total_depth_fee_margin_drag_rate,
            self.block_total_depth_fee_margin_drag_rate,
        )
        _require_ascending(
            "drag_to_edge_ratio",
            self.watch_drag_to_edge_ratio,
            self.block_drag_to_edge_ratio,
        )
        _require_descending(
            "depth coverage",
            self.pass_depth_coverage_ratio,
            self.block_depth_coverage_ratio,
        )
        _require_ascending(
            "fee_rate",
            self.watch_fee_rate,
            self.block_fee_rate,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthFeeMarginInput:
    private_research_reference: str
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    fee_rate: Decimal
    spread_rate: Decimal
    depth_cost_rate: Decimal
    confidence_margin_rate: Decimal
    visible_depth_rate: Decimal
    minimum_depth_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityDepthFeeMarginInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityDepthFeeMarginInput, "input")
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_rate",
            "spread_rate",
            "depth_cost_rate",
            "confidence_margin_rate",
            "visible_depth_rate",
            "minimum_depth_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthFeeMarginRow:
    signal_digest: str
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    fee_rate: Decimal
    spread_rate: Decimal
    depth_cost_rate: Decimal
    confidence_margin_rate: Decimal
    total_depth_fee_margin_drag_rate: Decimal
    net_probability_margin_rate: Decimal
    visible_depth_rate: Decimal
    minimum_depth_rate: Decimal
    depth_coverage_ratio: Decimal
    drag_to_edge_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityDepthFeeMarginRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityDepthFeeMarginRow, "row")
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "fee_rate",
            "spread_rate",
            "depth_cost_rate",
            "confidence_margin_rate",
            "total_depth_fee_margin_drag_rate",
            "visible_depth_rate",
            "minimum_depth_rate",
            "depth_coverage_ratio",
            "drag_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_margin_rate",
            _decimal("net_probability_margin_rate", self.net_probability_margin_rate),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _set_or_validate_digest(self, "row")
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthFeeMarginReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityDepthFeeMarginReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityDepthFeeMarginReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityDepthFeeMarginReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_net_probability_margin_rate: Decimal
    min_net_probability_margin_rate: Decimal
    max_total_depth_fee_margin_drag_rate: Decimal
    min_depth_coverage_ratio: Decimal
    max_drag_to_edge_ratio: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketProbabilityDepthFeeMarginReasonCodeCount, ...]
    rows: tuple[ResearchMarketProbabilityDepthFeeMarginRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityDepthFeeMarginReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityDepthFeeMarginReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_DEPTH_FEE_MARGIN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_net_probability_margin_rate",
            "min_net_probability_margin_rate",
            "max_total_depth_fee_margin_drag_rate",
            "min_depth_coverage_ratio",
            "max_drag_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _set_or_validate_digest(self, "report")
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)


def build_research_market_probability_depth_fee_margin_report(
    inputs: Iterable[ResearchMarketProbabilityDepthFeeMarginInput],
    *,
    generated_at: datetime,
    config: ResearchMarketProbabilityDepthFeeMarginConfig | None = None,
) -> ResearchMarketProbabilityDepthFeeMarginReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = ResearchMarketProbabilityDepthFeeMarginConfig() if config is None else config
    if type(active_config) is not ResearchMarketProbabilityDepthFeeMarginConfig:
        raise ValueError("config must be ResearchMarketProbabilityDepthFeeMarginConfig")
    _require_hard_flags("config", active_config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchMarketProbabilityDepthFeeMarginReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        status=status,
        input_count=_decimal_from_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_net_probability_margin_rate=_mean_decimal(
            row.net_probability_margin_rate for row in rows
        ),
        min_net_probability_margin_rate=min(
            (row.net_probability_margin_rate for row in rows),
            default=ZERO,
        ),
        max_total_depth_fee_margin_drag_rate=max(
            (row.total_depth_fee_margin_drag_rate for row in rows),
            default=ZERO,
        ),
        min_depth_coverage_ratio=min(
            (row.depth_coverage_ratio for row in rows),
            default=ZERO,
        ),
        max_drag_to_edge_ratio=max(
            (row.drag_to_edge_ratio for row in rows),
            default=ZERO,
        ),
        reason_codes=_report_reason_codes(rows, status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_depth_fee_margin_report_payload(
    report: ResearchMarketProbabilityDepthFeeMarginReport | Mapping[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketProbabilityDepthFeeMarginReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready_without_digest_validation(report)
        _require_payload_digest(payload)
    elif type(report) is dict:
        _require_hard_flags("payload", _MappingFlags(report))
        _reject_public_numerics(report)
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready_mapping(report)
        _require_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a ResearchMarketProbabilityDepthFeeMarginReport",
        )
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchMarketProbabilityDepthFeeMarginInput,
    *,
    config: ResearchMarketProbabilityDepthFeeMarginConfig,
) -> ResearchMarketProbabilityDepthFeeMarginRow:
    gross_probability_edge = _quantize(item.model_probability - item.market_probability)
    if gross_probability_edge < ZERO:
        gross_probability_edge = ZERO
    total_depth_fee_margin_drag_rate = _quantize(
        item.fee_rate
        + (item.spread_rate / TWO)
        + item.depth_cost_rate
        + item.confidence_margin_rate,
    )
    net_probability_margin_rate = _quantize(
        gross_probability_edge - total_depth_fee_margin_drag_rate,
    )
    depth_coverage_ratio = _safe_ratio(item.visible_depth_rate, item.minimum_depth_rate)
    drag_to_edge_ratio = _safe_ratio(total_depth_fee_margin_drag_rate, gross_probability_edge)
    reason_codes = _row_reason_codes(
        gross_probability_edge=gross_probability_edge,
        net_probability_margin_rate=net_probability_margin_rate,
        total_depth_fee_margin_drag_rate=total_depth_fee_margin_drag_rate,
        depth_coverage_ratio=depth_coverage_ratio,
        drag_to_edge_ratio=drag_to_edge_ratio,
        fee_rate=item.fee_rate,
        config=config,
    )
    return ResearchMarketProbabilityDepthFeeMarginRow(
        signal_digest=_private_reference_digest(item.private_research_reference),
        observed_at=item.observed_at,
        model_probability=item.model_probability,
        market_probability=item.market_probability,
        gross_probability_edge=gross_probability_edge,
        fee_rate=item.fee_rate,
        spread_rate=item.spread_rate,
        depth_cost_rate=item.depth_cost_rate,
        confidence_margin_rate=item.confidence_margin_rate,
        total_depth_fee_margin_drag_rate=total_depth_fee_margin_drag_rate,
        net_probability_margin_rate=net_probability_margin_rate,
        visible_depth_rate=item.visible_depth_rate,
        minimum_depth_rate=item.minimum_depth_rate,
        depth_coverage_ratio=depth_coverage_ratio,
        drag_to_edge_ratio=drag_to_edge_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    gross_probability_edge: Decimal,
    net_probability_margin_rate: Decimal,
    total_depth_fee_margin_drag_rate: Decimal,
    depth_coverage_ratio: Decimal,
    drag_to_edge_ratio: Decimal,
    fee_rate: Decimal,
    config: ResearchMarketProbabilityDepthFeeMarginConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if gross_probability_edge <= ZERO:
        detail_reasons.append(REASON_EDGE_NON_POSITIVE)
    detail_reasons.extend(
        _low_value_reason(
            value=net_probability_margin_rate,
            watch_value=config.pass_net_probability_margin_rate,
            block_value=config.watch_net_probability_margin_rate,
            watch_reason=REASON_NET_MARGIN_WATCH,
            block_reason=REASON_NET_MARGIN_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=total_depth_fee_margin_drag_rate,
            watch_value=config.watch_total_depth_fee_margin_drag_rate,
            block_value=config.block_total_depth_fee_margin_drag_rate,
            watch_reason=REASON_TOTAL_DRAG_WATCH,
            block_reason=REASON_TOTAL_DRAG_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=drag_to_edge_ratio,
            watch_value=config.watch_drag_to_edge_ratio,
            block_value=config.block_drag_to_edge_ratio,
            watch_reason=REASON_DRAG_TO_EDGE_WATCH,
            block_reason=REASON_DRAG_TO_EDGE_BLOCK,
        ),
    )
    detail_reasons.extend(
        _coverage_reason(
            value=depth_coverage_ratio,
            pass_value=config.pass_depth_coverage_ratio,
            block_value=config.block_depth_coverage_ratio,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=fee_rate,
            watch_value=config.watch_fee_rate,
            block_value=config.block_fee_rate,
            watch_reason=REASON_FEE_RATE_WATCH,
            block_reason=REASON_FEE_RATE_BLOCK,
        ),
    )
    if any(reason.endswith("_block") for reason in detail_reasons) or (
        REASON_EDGE_NON_POSITIVE in detail_reasons
    ):
        return _normalize_reason_codes((REASON_BLOCK, *detail_reasons))
    if detail_reasons:
        return _normalize_reason_codes((REASON_WATCH, *detail_reasons))
    return (REASON_PASS,)


def _low_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value < block_value:
        return (block_reason,)
    if value < watch_value:
        return (watch_reason,)
    return ()


def _high_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value >= block_value:
        return (block_reason,)
    if value >= watch_value:
        return (watch_reason,)
    return ()


def _coverage_reason(
    *,
    value: Decimal,
    pass_value: Decimal,
    block_value: Decimal,
) -> tuple[str, ...]:
    if value < block_value:
        return (REASON_DEPTH_COVERAGE_BLOCK,)
    if value < pass_value:
        return (REASON_DEPTH_COVERAGE_WATCH,)
    return ()


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == REASON_BLOCK:
        return STATUS_BLOCK
    if reason_codes[0] == REASON_WATCH:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchMarketProbabilityDepthFeeMarginRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityDepthFeeMarginRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: set[str] = set()
    for row in rows:
        if row.status == status:
            reasons.update(row.reason_codes)
    return _normalize_reason_codes(tuple(sorted(reasons, key=REASON_CODES.index)))


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityDepthFeeMarginRow, ...],
) -> tuple[ResearchMarketProbabilityDepthFeeMarginReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchMarketProbabilityDepthFeeMarginReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _row_sort_key(
    row: ResearchMarketProbabilityDepthFeeMarginRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.drag_to_edge_ratio,
        row.net_probability_margin_rate,
        row.observed_at,
        row.signal_digest,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketProbabilityDepthFeeMarginInput],
) -> tuple[ResearchMarketProbabilityDepthFeeMarginInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen: set[tuple[str, datetime]] = set()
    for item in normalized:
        if type(item) is not ResearchMarketProbabilityDepthFeeMarginInput:
            raise ValueError(
                "inputs must contain ResearchMarketProbabilityDepthFeeMarginInput",
            )
        _require_hard_flags("input", item)
        key = (item.private_research_reference, item.observed_at)
        if key in seen:
            raise ValueError("inputs must be unique by private reference and time")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketProbabilityDepthFeeMarginRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, datetime]] = set()
    for row in normalized:
        if type(row) is not ResearchMarketProbabilityDepthFeeMarginRow:
            raise ValueError("rows must contain ResearchMarketProbabilityDepthFeeMarginRow")
        _require_hard_flags("row", row)
        key = (row.signal_digest, row.observed_at)
        if key in seen:
            raise ValueError("rows must be unique by signal digest and time")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchMarketProbabilityDepthFeeMarginReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMarketProbabilityDepthFeeMarginReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityDepthFeeMarginReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _status_count(
    rows: tuple[ResearchMarketProbabilityDepthFeeMarginRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_count(sum(1 for row in rows if row.status == status))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _validate_row_consistency(row: ResearchMarketProbabilityDepthFeeMarginRow) -> None:
    expected_edge = _quantize(row.model_probability - row.market_probability)
    if expected_edge < ZERO:
        expected_edge = ZERO
    if row.gross_probability_edge != expected_edge:
        raise ValueError("gross_probability_edge must match probabilities")
    expected_total = _quantize(
        row.fee_rate
        + (row.spread_rate / TWO)
        + row.depth_cost_rate
        + row.confidence_margin_rate,
    )
    if row.total_depth_fee_margin_drag_rate != expected_total:
        raise ValueError("total_depth_fee_margin_drag_rate must match components")
    if row.net_probability_margin_rate != _quantize(
        row.gross_probability_edge - row.total_depth_fee_margin_drag_rate,
    ):
        raise ValueError("net_probability_margin_rate must match row fields")
    if row.depth_coverage_ratio != _safe_ratio(
        row.visible_depth_rate,
        row.minimum_depth_rate,
    ):
        raise ValueError("depth_coverage_ratio must match row fields")
    if row.drag_to_edge_ratio != _safe_ratio(
        row.total_depth_fee_margin_drag_rate,
        row.gross_probability_edge,
    ):
        raise ValueError("drag_to_edge_ratio must match row fields")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (REASON_PASS,):
        raise ValueError("pass rows require the pass reason only")


def _validate_report_consistency(
    report: ResearchMarketProbabilityDepthFeeMarginReport,
) -> None:
    rows = report.rows
    expected_values = {
        "input_count": _decimal_from_count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_net_probability_margin_rate": _mean_decimal(
            row.net_probability_margin_rate for row in rows
        ),
        "min_net_probability_margin_rate": min(
            (row.net_probability_margin_rate for row in rows),
            default=ZERO,
        ),
        "max_total_depth_fee_margin_drag_rate": max(
            (row.total_depth_fee_margin_drag_rate for row in rows),
            default=ZERO,
        ),
        "min_depth_coverage_ratio": min(
            (row.depth_coverage_ratio for row in rows),
            default=ZERO,
        ),
        "max_drag_to_edge_ratio": max(
            (row.drag_to_edge_ratio for row in rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    expected_digest = _derived_validation_digest(value, label)
    if current_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    _require_sha256_digest("derived_validation_digest", current_digest)
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    payload = _json_ready_without_digest_validation(value)
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(
        f"{label} digest payload",
        payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready_without_digest_validation(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a dataclass instance")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _json_ready_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _json_ready(value: Any) -> Any:
    if value is None or type(value) is bool:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, Decimal):
        raise ValueError("Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("datetime value must be exactly datetime")
    if type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("public numerics must be Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError("public numerics must not be floats")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    supplied_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", supplied_digest)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    expected_digest = sha256(encoded).hexdigest()
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        if numerator == ZERO:
            return ZERO
        return ONE
    return _quantize(numerator / denominator)


def _decimal_from_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _probability_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} has unsafe public value")


def _require_private_reference(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_ascending(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{name} block threshold must exceed watch threshold")


def _require_descending(name: str, pass_value: Decimal, block_value: Decimal) -> None:
    if pass_value <= block_value:
        raise ValueError(f"{name} pass threshold must exceed block threshold")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_identifier(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes == (REASON_MISSING_INPUTS,):
        return reason_codes
    if reason_codes[0] not in (REASON_PASS, REASON_WATCH, REASON_BLOCK):
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == REASON_PASS and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] == REASON_WATCH and any(
        reason.endswith("_block") for reason in reason_codes[1:]
    ):
        raise ValueError("watch reason_codes must not contain block reasons")
    if reason_codes[0] == REASON_BLOCK and not (
        any(reason.endswith("_block") for reason in reason_codes[1:])
        or REASON_EDGE_NON_POSITIVE in reason_codes
        or REASON_MISSING_INPUTS in reason_codes
    ):
        raise ValueError("block reason_codes require a block detail")
    if tuple(sorted(reason_codes[1:], key=REASON_CODES.index)) != reason_codes[1:]:
        raise ValueError("detail reason_codes must use deterministic sequencing")
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise ValueError("public numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{label} contains a non-finite Decimal")
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{label} contains a Decimal subclass")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} contains a non-UTC-safe datetime")
        return
    if isinstance(value, datetime):
        raise ValueError(f"{label} contains a datetime subclass")
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{label} contains unsafe public numerics")
    if type(value) is str:
        if value != value.strip() or _has_unsafe_public_fragment(value):
            raise ValueError(f"{label} contains unsafe public value")
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} contains unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    raise ValueError(f"{label} is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
