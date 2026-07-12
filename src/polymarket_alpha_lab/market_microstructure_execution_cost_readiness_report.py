"""Paper-only microstructure execution cost readiness report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_MARKET_MICROSTRUCTURE_EXECUTION_COST_READINESS_CONFIG_VERSION",
    "MarketMicrostructureExecutionCostReadinessConfig",
    "MarketMicrostructureExecutionCostReadinessInput",
    "MarketMicrostructureExecutionCostReadinessReasonCodeCount",
    "MarketMicrostructureExecutionCostReadinessReport",
    "MarketMicrostructureExecutionCostReadinessRow",
    "build_market_microstructure_execution_cost_readiness_report",
    "market_microstructure_execution_cost_readiness_report_payload",
)


DEFAULT_MARKET_MICROSTRUCTURE_EXECUTION_COST_READINESS_CONFIG_VERSION = (
    "market-microstructure-execution-cost-readiness-report-v1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
HIGH_RATIO = Decimal("999999.000000")

BAND_READY = "ready"
BAND_ATTENTION = "attention"
BAND_BLOCKER = "blocker"
BANDS = (BAND_READY, BAND_ATTENTION, BAND_BLOCKER)
BAND_SORT_RANK = {
    BAND_BLOCKER: Decimal("0.000000"),
    BAND_ATTENTION: Decimal("1.000000"),
    BAND_READY: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_execution_cost_readiness_inputs"
REASON_READY = "execution_cost_readiness_ready"
REASON_ATTENTION = "execution_cost_readiness_attention"
REASON_BLOCKER = "execution_cost_readiness_blocker"
REASON_COST_BURDEN_ATTENTION = "cost_burden_attention"
REASON_COST_BURDEN_BLOCKER = "cost_burden_blocker"
REASON_DEPTH_BLOCKER = "depth_below_minimum_blocker"
REASON_EDGE_NON_POSITIVE = "edge_to_threshold_probability_non_positive_blocker"
REASON_SPREAD_ATTENTION = "spread_probability_attention"
REASON_SPREAD_BLOCKER = "spread_probability_blocker"
REASON_TOTAL_COST_ATTENTION = "total_cost_probability_attention"
REASON_TOTAL_COST_BLOCKER = "total_cost_probability_blocker"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_READY,
    REASON_ATTENTION,
    REASON_BLOCKER,
    REASON_COST_BURDEN_ATTENTION,
    REASON_COST_BURDEN_BLOCKER,
    REASON_DEPTH_BLOCKER,
    REASON_EDGE_NON_POSITIVE,
    REASON_SPREAD_ATTENTION,
    REASON_SPREAD_BLOCKER,
    REASON_TOTAL_COST_ATTENTION,
    REASON_TOTAL_COST_BLOCKER,
)
REASON_CODE_SET = frozenset(REASON_CODES)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "=",
    _join_parts("api", "_", "key"),
    _join_parts("candidate", "_", "id"),
    "credential",
    _join_parts("d", "s", "n"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "slug"),
    _join_parts("private", "_", "key"),
    "question",
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "market"),
    "secret",
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
)


@dataclass(frozen=True)
class MarketMicrostructureExecutionCostReadinessConfig:
    config_version: str = (
        DEFAULT_MARKET_MICROSTRUCTURE_EXECUTION_COST_READINESS_CONFIG_VERSION
    )
    spread_attention_threshold: Decimal = Decimal("0.050000")
    spread_blocker_threshold: Decimal = Decimal("0.100000")
    total_cost_attention_threshold: Decimal = Decimal("0.030000")
    total_cost_blocker_threshold: Decimal = Decimal("0.080000")
    cost_burden_attention_threshold: Decimal = Decimal("0.500000")
    cost_burden_blocker_threshold: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketMicrostructureExecutionCostReadinessConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMicrostructureExecutionCostReadinessConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_MICROSTRUCTURE_EXECUTION_COST_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "spread_attention_threshold",
            "spread_blocker_threshold",
            "total_cost_attention_threshold",
            "total_cost_blocker_threshold",
            "cost_burden_attention_threshold",
            "cost_burden_blocker_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending(
            "spread_probability",
            self.spread_attention_threshold,
            self.spread_blocker_threshold,
        )
        _require_ascending(
            "total_cost_probability",
            self.total_cost_attention_threshold,
            self.total_cost_blocker_threshold,
        )
        _require_ascending(
            "cost_burden",
            self.cost_burden_attention_threshold,
            self.cost_burden_blocker_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketMicrostructureExecutionCostReadinessInput:
    private_research_reference: str
    observed_at: datetime
    bid_probability: Decimal
    ask_probability: Decimal
    mid_probability: Decimal
    taker_fee_probability: Decimal
    estimated_slippage_probability: Decimal
    depth_usdc: Decimal
    min_depth_usdc: Decimal
    edge_to_threshold_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketMicrostructureExecutionCostReadinessInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMicrostructureExecutionCostReadinessInput, "input")
        _require_research_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "bid_probability",
            "ask_probability",
            "mid_probability",
            "taker_fee_probability",
            "estimated_slippage_probability",
            "edge_to_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_usdc", "min_depth_usdc"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_depth_usdc <= ZERO:
            raise ValueError("min_depth_usdc must be positive")
        if self.ask_probability < self.bid_probability:
            raise ValueError("ask_probability must be at least bid_probability")
        if self.mid_probability < self.bid_probability:
            raise ValueError("mid_probability must be at least bid_probability")
        if self.mid_probability > self.ask_probability:
            raise ValueError("mid_probability must not exceed ask_probability")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketMicrostructureExecutionCostReadinessRow:
    signal_digest: str
    observed_at: datetime
    bid_probability: Decimal
    ask_probability: Decimal
    mid_probability: Decimal
    taker_fee_probability: Decimal
    estimated_slippage_probability: Decimal
    depth_usdc: Decimal
    min_depth_usdc: Decimal
    edge_to_threshold_probability: Decimal
    spread_probability: Decimal
    total_cost_probability: Decimal
    cost_burden_ratio: Decimal
    depth_coverage_ratio: Decimal
    band: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketMicrostructureExecutionCostReadinessRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMicrostructureExecutionCostReadinessRow, "row")
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "bid_probability",
            "ask_probability",
            "mid_probability",
            "taker_fee_probability",
            "estimated_slippage_probability",
            "edge_to_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_usdc",
            "min_depth_usdc",
            "spread_probability",
            "total_cost_probability",
            "cost_burden_ratio",
            "depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_band("band", self.band)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _set_or_validate_digest(self, "row")
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketMicrostructureExecutionCostReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketMicrostructureExecutionCostReadinessReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketMicrostructureExecutionCostReadinessReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class MarketMicrostructureExecutionCostReadinessReport:
    generated_at: datetime
    config_version: str
    band: str
    input_count: Decimal
    ready_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    average_total_cost_probability: Decimal
    max_spread_probability: Decimal
    max_cost_burden_ratio: Decimal
    min_depth_usdc: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketMicrostructureExecutionCostReadinessReasonCodeCount, ...]
    rows: tuple[MarketMicrostructureExecutionCostReadinessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketMicrostructureExecutionCostReadinessReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketMicrostructureExecutionCostReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_MICROSTRUCTURE_EXECUTION_COST_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_band("band", self.band)
        for field_name in (
            "input_count",
            "ready_count",
            "attention_count",
            "blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_total_cost_probability",
            "max_spread_probability",
            "max_cost_burden_ratio",
            "min_depth_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
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


def build_market_microstructure_execution_cost_readiness_report(
    inputs: Iterable[MarketMicrostructureExecutionCostReadinessInput],
    *,
    generated_at: datetime,
    config: MarketMicrostructureExecutionCostReadinessConfig | None = None,
) -> MarketMicrostructureExecutionCostReadinessReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = (
        MarketMicrostructureExecutionCostReadinessConfig() if config is None else config
    )
    if type(active_config) is not MarketMicrostructureExecutionCostReadinessConfig:
        raise ValueError("config must be MarketMicrostructureExecutionCostReadinessConfig")
    _require_hard_flags("config", active_config)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    band = _report_band(rows)
    return MarketMicrostructureExecutionCostReadinessReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        band=band,
        input_count=_decimal_from_count(len(rows)),
        ready_count=_band_count(rows, BAND_READY),
        attention_count=_band_count(rows, BAND_ATTENTION),
        blocker_count=_band_count(rows, BAND_BLOCKER),
        average_total_cost_probability=_mean_decimal(
            row.total_cost_probability for row in rows
        ),
        max_spread_probability=max(
            (row.spread_probability for row in rows),
            default=ZERO,
        ),
        max_cost_burden_ratio=max(
            (row.cost_burden_ratio for row in rows),
            default=ZERO,
        ),
        min_depth_usdc=min((row.depth_usdc for row in rows), default=ZERO),
        reason_codes=_report_reason_codes(rows, band),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_microstructure_execution_cost_readiness_report_payload(
    report: MarketMicrostructureExecutionCostReadinessReport | Mapping[str, Any],
) -> "FrozenJsonObject":
    if type(report) is MarketMicrostructureExecutionCostReadinessReport:
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
            "report must be a MarketMicrostructureExecutionCostReadinessReport",
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
    item: MarketMicrostructureExecutionCostReadinessInput,
    *,
    config: MarketMicrostructureExecutionCostReadinessConfig,
) -> MarketMicrostructureExecutionCostReadinessRow:
    spread_probability = _quantize(item.ask_probability - item.bid_probability)
    total_cost_probability = _quantize(
        item.taker_fee_probability
        + item.estimated_slippage_probability
        + (spread_probability / TWO),
    )
    cost_burden_ratio = _safe_ratio(
        total_cost_probability,
        item.edge_to_threshold_probability,
    )
    depth_coverage_ratio = _safe_ratio(item.depth_usdc, item.min_depth_usdc)
    reason_codes = _row_reason_codes(
        spread_probability=spread_probability,
        total_cost_probability=total_cost_probability,
        cost_burden_ratio=cost_burden_ratio,
        depth_usdc=item.depth_usdc,
        min_depth_usdc=item.min_depth_usdc,
        edge_to_threshold_probability=item.edge_to_threshold_probability,
        config=config,
    )
    return MarketMicrostructureExecutionCostReadinessRow(
        signal_digest=_research_reference_digest(item.private_research_reference),
        observed_at=item.observed_at,
        bid_probability=item.bid_probability,
        ask_probability=item.ask_probability,
        mid_probability=item.mid_probability,
        taker_fee_probability=item.taker_fee_probability,
        estimated_slippage_probability=item.estimated_slippage_probability,
        depth_usdc=item.depth_usdc,
        min_depth_usdc=item.min_depth_usdc,
        edge_to_threshold_probability=item.edge_to_threshold_probability,
        spread_probability=spread_probability,
        total_cost_probability=total_cost_probability,
        cost_burden_ratio=cost_burden_ratio,
        depth_coverage_ratio=depth_coverage_ratio,
        band=_band_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    spread_probability: Decimal,
    total_cost_probability: Decimal,
    cost_burden_ratio: Decimal,
    depth_usdc: Decimal,
    min_depth_usdc: Decimal,
    edge_to_threshold_probability: Decimal,
    config: MarketMicrostructureExecutionCostReadinessConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if edge_to_threshold_probability <= ZERO:
        detail_reasons.append(REASON_EDGE_NON_POSITIVE)
    detail_reasons.extend(
        _high_value_reason(
            value=cost_burden_ratio,
            attention_value=config.cost_burden_attention_threshold,
            blocker_value=config.cost_burden_blocker_threshold,
            attention_reason=REASON_COST_BURDEN_ATTENTION,
            blocker_reason=REASON_COST_BURDEN_BLOCKER,
        ),
    )
    if depth_usdc < min_depth_usdc:
        detail_reasons.append(REASON_DEPTH_BLOCKER)
    detail_reasons.extend(
        _high_value_reason(
            value=spread_probability,
            attention_value=config.spread_attention_threshold,
            blocker_value=config.spread_blocker_threshold,
            attention_reason=REASON_SPREAD_ATTENTION,
            blocker_reason=REASON_SPREAD_BLOCKER,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=total_cost_probability,
            attention_value=config.total_cost_attention_threshold,
            blocker_value=config.total_cost_blocker_threshold,
            attention_reason=REASON_TOTAL_COST_ATTENTION,
            blocker_reason=REASON_TOTAL_COST_BLOCKER,
        ),
    )
    if any(reason.endswith("_blocker") for reason in detail_reasons):
        return _normalize_reason_codes((REASON_BLOCKER, *detail_reasons))
    if detail_reasons:
        return _normalize_reason_codes((REASON_ATTENTION, *detail_reasons))
    return (REASON_READY,)


def _high_value_reason(
    *,
    value: Decimal,
    attention_value: Decimal,
    blocker_value: Decimal,
    attention_reason: str,
    blocker_reason: str,
) -> tuple[str, ...]:
    if value >= blocker_value:
        return (blocker_reason,)
    if value >= attention_value:
        return (attention_reason,)
    return ()


def _band_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == REASON_BLOCKER:
        return BAND_BLOCKER
    if reason_codes[0] == REASON_ATTENTION:
        return BAND_ATTENTION
    return BAND_READY


def _report_band(
    rows: tuple[MarketMicrostructureExecutionCostReadinessRow, ...],
) -> str:
    if not rows:
        return BAND_BLOCKER
    if any(row.band == BAND_BLOCKER for row in rows):
        return BAND_BLOCKER
    if any(row.band == BAND_ATTENTION for row in rows):
        return BAND_ATTENTION
    return BAND_READY


def _report_reason_codes(
    rows: tuple[MarketMicrostructureExecutionCostReadinessRow, ...],
    band: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: set[str] = set()
    for row in rows:
        if row.band == band:
            reasons.update(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _reason_code_counts(
    rows: tuple[MarketMicrostructureExecutionCostReadinessRow, ...],
) -> tuple[MarketMicrostructureExecutionCostReadinessReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketMicrostructureExecutionCostReadinessReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _row_sort_key(
    row: MarketMicrostructureExecutionCostReadinessRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str]:
    return (
        BAND_SORT_RANK[row.band],
        -row.cost_burden_ratio,
        -row.total_cost_probability,
        row.observed_at,
        row.signal_digest,
    )


def _normalize_inputs(
    inputs: Iterable[MarketMicrostructureExecutionCostReadinessInput],
) -> tuple[MarketMicrostructureExecutionCostReadinessInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen: set[tuple[str, datetime]] = set()
    for item in normalized:
        if type(item) is not MarketMicrostructureExecutionCostReadinessInput:
            raise ValueError(
                "inputs must contain MarketMicrostructureExecutionCostReadinessInput",
            )
        _require_hard_flags("input", item)
        key = (item.private_research_reference, item.observed_at)
        if key in seen:
            raise ValueError("inputs must be unique by reference and time")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketMicrostructureExecutionCostReadinessRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, datetime]] = set()
    for row in normalized:
        if type(row) is not MarketMicrostructureExecutionCostReadinessRow:
            raise ValueError("rows must contain MarketMicrostructureExecutionCostReadinessRow")
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
) -> tuple[MarketMicrostructureExecutionCostReadinessReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not MarketMicrostructureExecutionCostReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketMicrostructureExecutionCostReadinessReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _band_count(
    rows: tuple[MarketMicrostructureExecutionCostReadinessRow, ...],
    band: str,
) -> Decimal:
    return _decimal_from_count(sum(1 for row in rows if row.band == band))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _validate_row_consistency(
    row: MarketMicrostructureExecutionCostReadinessRow,
) -> None:
    if row.ask_probability < row.bid_probability:
        raise ValueError("ask_probability must be at least bid_probability")
    if row.mid_probability < row.bid_probability:
        raise ValueError("mid_probability must be at least bid_probability")
    if row.mid_probability > row.ask_probability:
        raise ValueError("mid_probability must not exceed ask_probability")
    if row.min_depth_usdc <= ZERO:
        raise ValueError("min_depth_usdc must be positive")
    expected_spread = _quantize(row.ask_probability - row.bid_probability)
    if row.spread_probability != expected_spread:
        raise ValueError("spread_probability must match probabilities")
    expected_total = _quantize(
        row.taker_fee_probability
        + row.estimated_slippage_probability
        + (row.spread_probability / TWO),
    )
    if row.total_cost_probability != expected_total:
        raise ValueError("total_cost_probability must match row fields")
    if row.cost_burden_ratio != _safe_ratio(
        row.total_cost_probability,
        row.edge_to_threshold_probability,
    ):
        raise ValueError("cost_burden_ratio must match row fields")
    if row.depth_coverage_ratio != _safe_ratio(row.depth_usdc, row.min_depth_usdc):
        raise ValueError("depth_coverage_ratio must match row fields")
    if row.band != _band_from_reason_codes(row.reason_codes):
        raise ValueError("band must match reason_codes")
    if row.band == BAND_READY and row.reason_codes != (REASON_READY,):
        raise ValueError("ready rows require the ready reason only")


def _validate_report_consistency(
    report: MarketMicrostructureExecutionCostReadinessReport,
) -> None:
    rows = report.rows
    expected_values = {
        "input_count": _decimal_from_count(len(rows)),
        "ready_count": _band_count(rows, BAND_READY),
        "attention_count": _band_count(rows, BAND_ATTENTION),
        "blocker_count": _band_count(rows, BAND_BLOCKER),
        "average_total_cost_probability": _mean_decimal(
            row.total_cost_probability for row in rows
        ),
        "max_spread_probability": max(
            (row.spread_probability for row in rows),
            default=ZERO,
        ),
        "max_cost_burden_ratio": max(
            (row.cost_burden_ratio for row in rows),
            default=ZERO,
        ),
        "min_depth_usdc": min((row.depth_usdc for row in rows), default=ZERO),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.band != _report_band(rows):
        raise ValueError("band must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.band):
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


def _freeze_json_object(value: dict[str, Any]) -> "FrozenJsonObject":
    return FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return FrozenJsonObject(
            {key: _freeze_json_value(item) for key, item in value.items()},
        )
    if type(value) is list:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_numerics(value: Any) -> None:
    if type(value) in (int, float):
        raise ValueError("public numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numerics(item)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(label: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{label} must be a public identifier")
    return value


def _require_research_reference(label: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _as_utc(label: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _nonnegative_decimal(label: str, value: object) -> Decimal:
    decimal_value = _decimal(label, value)
    if decimal_value < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return decimal_value


def _probability_decimal(label: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(label, value)
    if decimal_value > ONE:
        raise ValueError(f"{label} must be no more than 1")
    return decimal_value


def _count_decimal(label: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(label, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{label} must be a whole-count Decimal")
    return decimal_value


def _decimal_from_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return HIGH_RATIO
    return _quantize(numerator / denominator)


def _require_ascending(label: str, attention_value: Decimal, blocker_value: Decimal) -> None:
    if blocker_value <= attention_value:
        raise ValueError(f"{label} block threshold must exceed attention threshold")


def _require_band(label: str, value: object) -> str:
    if type(value) is not str or value not in BANDS:
        raise ValueError(f"{label} must be one of {BANDS}")
    return value


def _require_reason_code(label: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{label} must be a supported reason code")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    normalized = tuple(value)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return normalized


def _require_sha256_digest(label: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be a sha256 hex digest")
    return value


def _research_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        field_values = {field.name: getattr(value, field.name) for field in fields(value)}
        _reject_unsafe_public_payload(
            label,
            field_values,
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public field key")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if allow_json_containers and isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public field in {label}")
