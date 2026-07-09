"""Report-only liquidity probability reversal buffer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_REVERSAL_BUFFER_CONFIG_VERSION",
    "ResearchMarketLiquidityProbabilityReversalBufferConfig",
    "ResearchMarketLiquidityProbabilityReversalBufferInput",
    "ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount",
    "ResearchMarketLiquidityProbabilityReversalBufferReport",
    "ResearchMarketLiquidityProbabilityReversalBufferRow",
    "build_research_market_liquidity_probability_reversal_buffer_report",
    "research_market_liquidity_probability_reversal_buffer_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_REVERSAL_BUFFER_CONFIG_VERSION = (
    "research-market-liquidity-probability-reversal-buffer-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
HIGH_RATIO = Decimal("999999.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_liquidity_probability_reversal_buffer_inputs"
REASON_PASS = "liquidity_probability_reversal_buffer_pass"
REASON_WATCH = "liquidity_probability_reversal_buffer_watch"
REASON_BLOCK = "liquidity_probability_reversal_buffer_block"
REASON_NET_WATCH = "net_reversal_buffer_watch"
REASON_NET_BLOCK = "net_reversal_buffer_block"
REASON_PROBABILITY_WATCH = "probability_reversal_watch"
REASON_PROBABILITY_BLOCK = "probability_reversal_block"
REASON_DEPTH_WATCH = "depth_coverage_watch"
REASON_DEPTH_BLOCK = "depth_coverage_block"
REASON_RATIO_WATCH = "reversal_to_buffer_ratio_watch"
REASON_RATIO_BLOCK = "reversal_to_buffer_ratio_block"
REASON_FRICTION_WATCH = "friction_buffer_watch"
REASON_FRICTION_BLOCK = "friction_buffer_block"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_BLOCK,
    REASON_WATCH,
    REASON_PASS,
    REASON_NET_BLOCK,
    REASON_NET_WATCH,
    REASON_PROBABILITY_BLOCK,
    REASON_PROBABILITY_WATCH,
    REASON_DEPTH_BLOCK,
    REASON_DEPTH_WATCH,
    REASON_RATIO_BLOCK,
    REASON_RATIO_WATCH,
    REASON_FRICTION_BLOCK,
    REASON_FRICTION_WATCH,
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
    _join_parts("mar", "ket", "_", "sl", "ug"),
    _join_parts("private", "_", "key"),
    _join_parts("que", "stion"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "mar", "ket"),
    "secret",
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("pos", "ition"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityReversalBufferConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_REVERSAL_BUFFER_CONFIG_VERSION
    )
    pass_net_reversal_buffer_rate: Decimal = Decimal("0.030000")
    watch_net_reversal_buffer_rate: Decimal = Decimal("0.005000")
    watch_probability_reversal_rate: Decimal = Decimal("0.100000")
    block_probability_reversal_rate: Decimal = Decimal("0.250000")
    watch_min_depth_coverage_ratio: Decimal = Decimal("1.000000")
    block_min_depth_coverage_ratio: Decimal = Decimal("0.500000")
    watch_reversal_to_buffer_ratio: Decimal = Decimal("0.800000")
    block_reversal_to_buffer_ratio: Decimal = Decimal("1.500000")
    watch_friction_buffer_rate: Decimal = Decimal("0.030000")
    block_friction_buffer_rate: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityReversalBufferConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityReversalBufferConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_REVERSAL_BUFFER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_reversal_buffer_rate",
            "watch_net_reversal_buffer_rate",
            "watch_probability_reversal_rate",
            "block_probability_reversal_rate",
            "watch_min_depth_coverage_ratio",
            "block_min_depth_coverage_ratio",
            "watch_reversal_to_buffer_ratio",
            "block_reversal_to_buffer_ratio",
            "watch_friction_buffer_rate",
            "block_friction_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_net_reversal_buffer_rate < self.watch_net_reversal_buffer_rate:
            raise ValueError(
                "pass_net_reversal_buffer_rate must be at least "
                "watch_net_reversal_buffer_rate",
            )
        _require_ascending(
            "probability_reversal_rate",
            self.watch_probability_reversal_rate,
            self.block_probability_reversal_rate,
        )
        _require_descending(
            "depth_coverage_ratio",
            self.watch_min_depth_coverage_ratio,
            self.block_min_depth_coverage_ratio,
        )
        _require_ascending(
            "reversal_to_buffer_ratio",
            self.watch_reversal_to_buffer_ratio,
            self.block_reversal_to_buffer_ratio,
        )
        _require_ascending(
            "friction_buffer_rate",
            self.watch_friction_buffer_rate,
            self.block_friction_buffer_rate,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityReversalBufferInput:
    private_research_reference: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    liquidity_buffer_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_buffer_rate: Decimal
    confidence_buffer_rate: Decimal
    available_depth: Decimal
    required_depth: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityReversalBufferInput does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityReversalBufferInput,
            "input",
        )
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("prior_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_buffer_rate",
            "exit_spread_rate",
            "exit_slippage_buffer_rate",
            "confidence_buffer_rate",
            "available_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_depth",
            _positive_decimal("required_depth", self.required_depth),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityReversalBufferRow:
    signal_digest: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    probability_reversal_rate: Decimal
    liquidity_buffer_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_buffer_rate: Decimal
    confidence_buffer_rate: Decimal
    friction_buffer_rate: Decimal
    usable_liquidity_buffer_rate: Decimal
    net_reversal_buffer_rate: Decimal
    reversal_to_buffer_ratio: Decimal
    available_depth: Decimal
    required_depth: Decimal
    depth_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityReversalBufferRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityReversalBufferRow,
            "row",
        )
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("prior_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_reversal_rate",
            "liquidity_buffer_rate",
            "exit_spread_rate",
            "exit_slippage_buffer_rate",
            "confidence_buffer_rate",
            "friction_buffer_rate",
            "reversal_to_buffer_ratio",
            "available_depth",
            "depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "usable_liquidity_buffer_rate",
            "net_reversal_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_depth",
            _positive_decimal("required_depth", self.required_depth),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _set_or_validate_digest(self, "row")
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityProbabilityReversalBufferReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_reversal_rate: Decimal
    min_net_reversal_buffer_rate: Decimal
    max_reversal_to_buffer_ratio: Decimal
    min_depth_coverage_ratio: Decimal
    max_friction_buffer_rate: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketLiquidityProbabilityReversalBufferRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityProbabilityReversalBufferReport does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityProbabilityReversalBufferReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_PROBABILITY_REVERSAL_BUFFER_CONFIG_VERSION
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
            "average_probability_reversal_rate",
            "min_net_reversal_buffer_rate",
            "max_reversal_to_buffer_ratio",
            "min_depth_coverage_ratio",
            "max_friction_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
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


def build_research_market_liquidity_probability_reversal_buffer_report(
    inputs: Iterable[ResearchMarketLiquidityProbabilityReversalBufferInput],
    *,
    generated_at: datetime,
    config: ResearchMarketLiquidityProbabilityReversalBufferConfig | None = None,
) -> ResearchMarketLiquidityProbabilityReversalBufferReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = (
        ResearchMarketLiquidityProbabilityReversalBufferConfig()
        if config is None
        else config
    )
    if type(active_config) is not ResearchMarketLiquidityProbabilityReversalBufferConfig:
        raise ValueError(
            "config must be ResearchMarketLiquidityProbabilityReversalBufferConfig",
        )
    _require_hard_flags("config", active_config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchMarketLiquidityProbabilityReversalBufferReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        status=status,
        input_count=_decimal_from_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_probability_reversal_rate=_mean_decimal(
            row.probability_reversal_rate for row in rows
        ),
        min_net_reversal_buffer_rate=min(
            (row.net_reversal_buffer_rate for row in rows),
            default=ZERO,
        ),
        max_reversal_to_buffer_ratio=max(
            (row.reversal_to_buffer_ratio for row in rows),
            default=ZERO,
        ),
        min_depth_coverage_ratio=min(
            (row.depth_coverage_ratio for row in rows),
            default=ZERO,
        ),
        max_friction_buffer_rate=max(
            (row.friction_buffer_rate for row in rows),
            default=ZERO,
        ),
        reason_codes=_report_reason_codes(rows, status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_liquidity_probability_reversal_buffer_report_payload(
    report: ResearchMarketLiquidityProbabilityReversalBufferReport | Mapping[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketLiquidityProbabilityReversalBufferReport:
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
            "report must be a ResearchMarketLiquidityProbabilityReversalBufferReport",
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
    item: ResearchMarketLiquidityProbabilityReversalBufferInput,
    *,
    config: ResearchMarketLiquidityProbabilityReversalBufferConfig,
) -> ResearchMarketLiquidityProbabilityReversalBufferRow:
    probability_reversal_rate = _abs_decimal(
        item.current_probability - item.prior_probability,
    )
    friction_buffer_rate = _quantize(
        (item.exit_spread_rate / TWO)
        + item.exit_slippage_buffer_rate
        + item.confidence_buffer_rate,
    )
    usable_liquidity_buffer_rate = _quantize(
        item.liquidity_buffer_rate - friction_buffer_rate,
    )
    net_reversal_buffer_rate = _quantize(
        usable_liquidity_buffer_rate - probability_reversal_rate,
    )
    reversal_to_buffer_ratio = _safe_ratio(
        probability_reversal_rate,
        usable_liquidity_buffer_rate,
    )
    depth_coverage_ratio = _safe_ratio(item.available_depth, item.required_depth)
    reason_codes = _row_reason_codes(
        probability_reversal_rate=probability_reversal_rate,
        friction_buffer_rate=friction_buffer_rate,
        net_reversal_buffer_rate=net_reversal_buffer_rate,
        reversal_to_buffer_ratio=reversal_to_buffer_ratio,
        depth_coverage_ratio=depth_coverage_ratio,
        config=config,
    )
    return ResearchMarketLiquidityProbabilityReversalBufferRow(
        signal_digest=_private_reference_digest(item.private_research_reference),
        observed_at=item.observed_at,
        prior_probability=item.prior_probability,
        current_probability=item.current_probability,
        probability_reversal_rate=probability_reversal_rate,
        liquidity_buffer_rate=item.liquidity_buffer_rate,
        exit_spread_rate=item.exit_spread_rate,
        exit_slippage_buffer_rate=item.exit_slippage_buffer_rate,
        confidence_buffer_rate=item.confidence_buffer_rate,
        friction_buffer_rate=friction_buffer_rate,
        usable_liquidity_buffer_rate=usable_liquidity_buffer_rate,
        net_reversal_buffer_rate=net_reversal_buffer_rate,
        reversal_to_buffer_ratio=reversal_to_buffer_ratio,
        available_depth=item.available_depth,
        required_depth=item.required_depth,
        depth_coverage_ratio=depth_coverage_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    probability_reversal_rate: Decimal,
    friction_buffer_rate: Decimal,
    net_reversal_buffer_rate: Decimal,
    reversal_to_buffer_ratio: Decimal,
    depth_coverage_ratio: Decimal,
    config: ResearchMarketLiquidityProbabilityReversalBufferConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    detail_reasons.extend(
        _low_value_reason(
            value=net_reversal_buffer_rate,
            watch_value=config.pass_net_reversal_buffer_rate,
            block_value=config.watch_net_reversal_buffer_rate,
            watch_reason=REASON_NET_WATCH,
            block_reason=REASON_NET_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=probability_reversal_rate,
            watch_value=config.watch_probability_reversal_rate,
            block_value=config.block_probability_reversal_rate,
            watch_reason=REASON_PROBABILITY_WATCH,
            block_reason=REASON_PROBABILITY_BLOCK,
        ),
    )
    detail_reasons.extend(
        _low_value_reason(
            value=depth_coverage_ratio,
            watch_value=config.watch_min_depth_coverage_ratio,
            block_value=config.block_min_depth_coverage_ratio,
            watch_reason=REASON_DEPTH_WATCH,
            block_reason=REASON_DEPTH_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=reversal_to_buffer_ratio,
            watch_value=config.watch_reversal_to_buffer_ratio,
            block_value=config.block_reversal_to_buffer_ratio,
            watch_reason=REASON_RATIO_WATCH,
            block_reason=REASON_RATIO_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=friction_buffer_rate,
            watch_value=config.watch_friction_buffer_rate,
            block_value=config.block_friction_buffer_rate,
            watch_reason=REASON_FRICTION_WATCH,
            block_reason=REASON_FRICTION_BLOCK,
        ),
    )
    status = _status_from_detail_reasons(detail_reasons)
    if status == STATUS_BLOCK:
        return (REASON_BLOCK, *detail_reasons)
    if status == STATUS_WATCH:
        return (REASON_WATCH, *detail_reasons)
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


def _status_from_detail_reasons(reason_codes: Iterable[str]) -> str:
    codes = tuple(reason_codes)
    if any(code.endswith("_block") for code in codes):
        return STATUS_BLOCK
    if any(code.endswith("_watch") for code in codes):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: Iterable[str]) -> str:
    codes = tuple(reason_codes)
    if REASON_BLOCK in codes or any(code.endswith("_block") for code in codes):
        return STATUS_BLOCK
    if REASON_WATCH in codes or any(code.endswith("_watch") for code in codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchMarketLiquidityProbabilityReversalBufferRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    statuses = tuple(row.status for row in rows)
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityProbabilityReversalBufferRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    codes: list[str] = []
    if status == STATUS_BLOCK:
        codes.append(REASON_BLOCK)
    elif status == STATUS_WATCH:
        codes.append(REASON_WATCH)
    else:
        codes.append(REASON_PASS)
    for reason_code in REASON_CODES:
        if reason_code in (REASON_MISSING_INPUTS, REASON_BLOCK, REASON_WATCH, REASON_PASS):
            continue
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityProbabilityReversalBufferRow, ...],
) -> tuple[ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_count(counter[reason_code]),
        )
        for reason_code in REASON_CODES
        if counter[reason_code] > 0
    )


def _row_sort_key(
    row: ResearchMarketLiquidityProbabilityReversalBufferRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.reversal_to_buffer_ratio,
        row.net_reversal_buffer_rate,
        row.signal_digest,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketLiquidityProbabilityReversalBufferInput],
) -> tuple[ResearchMarketLiquidityProbabilityReversalBufferInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchMarketLiquidityProbabilityReversalBufferInput:
            raise ValueError(
                "inputs must contain ResearchMarketLiquidityProbabilityReversalBufferInput",
            )
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketLiquidityProbabilityReversalBufferRow],
) -> tuple[ResearchMarketLiquidityProbabilityReversalBufferRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of report rows")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMarketLiquidityProbabilityReversalBufferRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityProbabilityReversalBufferRow",
            )
        _require_hard_flags("row", row)
        if row.signal_digest in seen:
            raise ValueError("rows must have unique signal_digest values")
        seen.add(row.signal_digest)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of reason codes")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount],
) -> tuple[ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not duplicate reason_code")
        seen.add(item.reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODES.index(item.reason_code),
        ),
    )


def _validate_row_consistency(
    row: ResearchMarketLiquidityProbabilityReversalBufferRow,
) -> None:
    probability_reversal_rate = _abs_decimal(row.current_probability - row.prior_probability)
    friction_buffer_rate = _quantize(
        (row.exit_spread_rate / TWO)
        + row.exit_slippage_buffer_rate
        + row.confidence_buffer_rate,
    )
    usable_liquidity_buffer_rate = _quantize(
        row.liquidity_buffer_rate - friction_buffer_rate,
    )
    net_reversal_buffer_rate = _quantize(
        usable_liquidity_buffer_rate - probability_reversal_rate,
    )
    reversal_to_buffer_ratio = _safe_ratio(
        probability_reversal_rate,
        usable_liquidity_buffer_rate,
    )
    depth_coverage_ratio = _safe_ratio(row.available_depth, row.required_depth)
    expected_values = {
        "probability_reversal_rate": probability_reversal_rate,
        "friction_buffer_rate": friction_buffer_rate,
        "usable_liquidity_buffer_rate": usable_liquidity_buffer_rate,
        "net_reversal_buffer_rate": net_reversal_buffer_rate,
        "reversal_to_buffer_ratio": reversal_to_buffer_ratio,
        "depth_coverage_ratio": depth_coverage_ratio,
    }
    for field_name, expected_value in expected_values.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match row inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketLiquidityProbabilityReversalBufferReport,
) -> None:
    rows = report.rows
    expected = {
        "input_count": _decimal_from_count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_probability_reversal_rate": _mean_decimal(
            row.probability_reversal_rate for row in rows
        ),
        "min_net_reversal_buffer_rate": min(
            (row.net_reversal_buffer_rate for row in rows),
            default=ZERO,
        ),
        "max_reversal_to_buffer_ratio": max(
            (row.reversal_to_buffer_ratio for row in rows),
            default=ZERO,
        ),
        "min_depth_coverage_ratio": min(
            (row.depth_coverage_ratio for row in rows),
            default=ZERO,
        ),
        "max_friction_buffer_rate": max(
            (row.friction_buffer_rate for row in rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match report rows")
    expected_reasons = _report_reason_codes(rows, expected_status)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report rows")
    expected_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match report rows")


def _status_count(
    rows: Iterable[ResearchMarketLiquidityProbabilityReversalBufferRow],
    status: str,
) -> Decimal:
    return _decimal_from_count(sum(1 for row in rows if row.status == status))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        if numerator <= ZERO:
            return ZERO
        return HIGH_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _decimal_from_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return normalized


def _probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value cannot be quantized") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        flag = getattr(value, field_name)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_text(field_name, normalized)
    return normalized


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > 2048:
        raise ValueError(f"{field_name} is too long")
    return normalized


def _require_reason_code(field_name: str, value: object) -> str:
    normalized = _require_public_identifier(field_name, value)
    if normalized not in REASON_CODE_SET:
        raise ValueError(f"{field_name} is not a supported reason code")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_ascending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value >= block_value:
        raise ValueError(f"watch_{field_name} must be below block threshold")


def _require_descending(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value <= block_value:
        raise ValueError(f"watch_{field_name} must exceed block threshold")


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _set_or_validate_digest(value: object, label: str) -> None:
    digest = getattr(value, "derived_validation_digest")
    expected_digest = _derived_validation_digest(_values_without_digest(value))
    if digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != expected_digest:
        raise ValueError(f"derived_validation_digest must match {label} payload")


def _values_without_digest(value: object) -> dict[str, object]:
    if not is_dataclass(value):
        raise ValueError("value must be a dataclass")
    values = asdict(value)
    values.pop("derived_validation_digest", None)
    return values


def _derived_validation_digest(values: Mapping[str, object]) -> str:
    payload = _json_ready_mapping(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready_without_digest_validation(value: object) -> dict[str, Any]:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _json_ready_mapping(values: Mapping[str, object]) -> dict[str, Any]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return format(value, ".6f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is dict or isinstance(value, FrozenJsonObject):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list) or isinstance(value, FrozenJsonArray):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


def _require_payload_digest(payload: Mapping[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    expected_digest = _derived_validation_digest(values)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")


def _freeze_json_object(payload: dict[str, Any]) -> "FrozenJsonObject":
    return FrozenJsonObject(
        {key: _freeze_json_value(value) for key, value in payload.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if type(value) is dict or isinstance(value, FrozenJsonObject):
        for item in value.values():
            _reject_public_numerics(item)
    elif type(value) in (list, tuple) or isinstance(value, FrozenJsonArray):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name == "private_research_reference":
                continue
            _reject_unsafe_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                field_value,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict or isinstance(value, FrozenJsonObject):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose mutable dict values")
        for key, item in value.items():
            _reject_unsafe_text(f"{label}.{key}", str(key))
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) in (tuple, list) or isinstance(value, FrozenJsonArray):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public field {label}")
