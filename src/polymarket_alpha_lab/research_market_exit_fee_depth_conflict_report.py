"""Report-only exit fee/depth conflict gate."""

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
    "DEFAULT_RESEARCH_MARKET_EXIT_FEE_DEPTH_CONFLICT_CONFIG_VERSION",
    "ResearchMarketExitFeeDepthConflictConfig",
    "ResearchMarketExitFeeDepthConflictInput",
    "ResearchMarketExitFeeDepthConflictReasonCodeCount",
    "ResearchMarketExitFeeDepthConflictReport",
    "ResearchMarketExitFeeDepthConflictRow",
    "build_research_market_exit_fee_depth_conflict_report",
    "research_market_exit_fee_depth_conflict_report_payload",
)


DEFAULT_RESEARCH_MARKET_EXIT_FEE_DEPTH_CONFLICT_CONFIG_VERSION = (
    "research-market-exit-fee-depth-conflict-report-v1"
)
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

REASON_MISSING_INPUTS = "missing_exit_fee_depth_conflict_inputs"
REASON_PASS = "exit_fee_depth_conflict_pass"
REASON_WATCH = "exit_fee_depth_conflict_watch"
REASON_BLOCK = "exit_fee_depth_conflict_block"
REASON_EDGE_NON_POSITIVE = "model_probability_not_above_market_probability"
REASON_NET_EDGE_WATCH = "net_probability_edge_watch"
REASON_NET_EDGE_BLOCK = "net_probability_edge_block"
REASON_FEE_DEPTH_DRAG_WATCH = "fee_depth_drag_watch"
REASON_FEE_DEPTH_DRAG_BLOCK = "fee_depth_drag_block"
REASON_DRAG_TO_EDGE_WATCH = "drag_to_edge_ratio_watch"
REASON_DRAG_TO_EDGE_BLOCK = "drag_to_edge_ratio_block"
REASON_DEPTH_COVERAGE_WATCH = "depth_coverage_watch"
REASON_DEPTH_COVERAGE_BLOCK = "depth_coverage_block"
REASON_EXIT_FEE_RATE_WATCH = "exit_fee_rate_watch"
REASON_EXIT_FEE_RATE_BLOCK = "exit_fee_rate_block"
REASON_DEPTH_SHORTFALL_PENALTY = "depth_shortfall_penalty_applied"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_PASS,
    REASON_WATCH,
    REASON_BLOCK,
    REASON_EDGE_NON_POSITIVE,
    REASON_NET_EDGE_WATCH,
    REASON_NET_EDGE_BLOCK,
    REASON_FEE_DEPTH_DRAG_WATCH,
    REASON_FEE_DEPTH_DRAG_BLOCK,
    REASON_DRAG_TO_EDGE_WATCH,
    REASON_DRAG_TO_EDGE_BLOCK,
    REASON_DEPTH_COVERAGE_WATCH,
    REASON_DEPTH_COVERAGE_BLOCK,
    REASON_EXIT_FEE_RATE_WATCH,
    REASON_EXIT_FEE_RATE_BLOCK,
    REASON_DEPTH_SHORTFALL_PENALTY,
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
class ResearchMarketExitFeeDepthConflictConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_EXIT_FEE_DEPTH_CONFLICT_CONFIG_VERSION
    pass_net_probability_edge_threshold: Decimal = Decimal("0.030000")
    watch_net_probability_edge_threshold: Decimal = Decimal("0.005000")
    fee_depth_drag_watch_threshold: Decimal = Decimal("0.040000")
    fee_depth_drag_block_threshold: Decimal = Decimal("0.080000")
    drag_to_edge_watch_threshold: Decimal = Decimal("0.500000")
    drag_to_edge_block_threshold: Decimal = Decimal("1.000000")
    depth_coverage_watch_threshold: Decimal = Decimal("0.750000")
    depth_coverage_block_threshold: Decimal = Decimal("0.350000")
    exit_fee_rate_watch_threshold: Decimal = Decimal("0.040000")
    exit_fee_rate_block_threshold: Decimal = Decimal("0.070000")
    minimum_depth_coverage_ratio: Decimal = Decimal("1.000000")
    depth_shortfall_penalty_rate: Decimal = Decimal("0.040000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketExitFeeDepthConflictConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitFeeDepthConflictConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_FEE_DEPTH_CONFLICT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_probability_edge_threshold",
            "watch_net_probability_edge_threshold",
            "fee_depth_drag_watch_threshold",
            "fee_depth_drag_block_threshold",
            "drag_to_edge_watch_threshold",
            "drag_to_edge_block_threshold",
            "depth_coverage_watch_threshold",
            "depth_coverage_block_threshold",
            "exit_fee_rate_watch_threshold",
            "exit_fee_rate_block_threshold",
            "minimum_depth_coverage_ratio",
            "depth_shortfall_penalty_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_net_probability_edge_threshold
            < self.watch_net_probability_edge_threshold
        ):
            raise ValueError(
                "pass_net_probability_edge_threshold must be at least "
                "watch_net_probability_edge_threshold",
            )
        _require_ascending(
            "fee_depth_drag",
            self.fee_depth_drag_watch_threshold,
            self.fee_depth_drag_block_threshold,
        )
        _require_ascending(
            "drag_to_edge_ratio",
            self.drag_to_edge_watch_threshold,
            self.drag_to_edge_block_threshold,
        )
        _require_descending(
            "depth_coverage",
            self.depth_coverage_watch_threshold,
            self.depth_coverage_block_threshold,
        )
        _require_ascending(
            "exit_fee_rate",
            self.exit_fee_rate_watch_threshold,
            self.exit_fee_rate_block_threshold,
        )
        if self.minimum_depth_coverage_ratio <= ZERO:
            raise ValueError("minimum_depth_coverage_ratio must be positive")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketExitFeeDepthConflictInput:
    private_research_reference: str
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    exit_fee_rate: Decimal
    bid_ask_spread_rate: Decimal
    exit_slippage_rate: Decimal
    depth_coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketExitFeeDepthConflictInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitFeeDepthConflictInput, "input")
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
            "exit_fee_rate",
            "bid_ask_spread_rate",
            "exit_slippage_rate",
            "depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketExitFeeDepthConflictRow:
    signal_digest: str
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    exit_fee_rate: Decimal
    bid_ask_spread_rate: Decimal
    exit_slippage_rate: Decimal
    depth_coverage_ratio: Decimal
    depth_shortfall_penalty: Decimal
    fee_depth_drag_rate: Decimal
    net_probability_edge: Decimal
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
            "ResearchMarketExitFeeDepthConflictRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitFeeDepthConflictRow, "row")
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
            "exit_fee_rate",
            "bid_ask_spread_rate",
            "exit_slippage_rate",
            "depth_coverage_ratio",
            "depth_shortfall_penalty",
            "fee_depth_drag_rate",
            "drag_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_edge",
            _decimal("net_probability_edge", self.net_probability_edge),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _set_or_validate_digest(self, "row")
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketExitFeeDepthConflictReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketExitFeeDepthConflictReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitFeeDepthConflictReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketExitFeeDepthConflictReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    worst_net_probability_edge: Decimal | None
    average_net_probability_edge: Decimal | None
    max_fee_depth_drag_rate: Decimal
    max_drag_to_edge_ratio: Decimal
    min_depth_coverage_ratio: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketExitFeeDepthConflictReasonCodeCount, ...]
    rows: tuple[ResearchMarketExitFeeDepthConflictRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketExitFeeDepthConflictReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitFeeDepthConflictReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_FEE_DEPTH_CONFLICT_CONFIG_VERSION
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
            "worst_net_probability_edge",
            "average_net_probability_edge",
            "min_depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_fee_depth_drag_rate", "max_drag_to_edge_ratio"):
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


def build_research_market_exit_fee_depth_conflict_report(
    inputs: Iterable[ResearchMarketExitFeeDepthConflictInput],
    *,
    generated_at: datetime,
    config: ResearchMarketExitFeeDepthConflictConfig | None = None,
) -> ResearchMarketExitFeeDepthConflictReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = ResearchMarketExitFeeDepthConflictConfig() if config is None else config
    if type(active_config) is not ResearchMarketExitFeeDepthConflictConfig:
        raise ValueError("config must be ResearchMarketExitFeeDepthConflictConfig")
    _require_hard_flags("config", active_config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchMarketExitFeeDepthConflictReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        status=status,
        input_count=_decimal_from_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        worst_net_probability_edge=min(
            (row.net_probability_edge for row in rows),
            default=None,
        ),
        average_net_probability_edge=_mean_optional_decimal(
            row.net_probability_edge for row in rows
        ),
        max_fee_depth_drag_rate=max(
            (row.fee_depth_drag_rate for row in rows),
            default=ZERO,
        ),
        max_drag_to_edge_ratio=max(
            (row.drag_to_edge_ratio for row in rows),
            default=ZERO,
        ),
        min_depth_coverage_ratio=min(
            (row.depth_coverage_ratio for row in rows),
            default=None,
        ),
        reason_codes=_report_reason_codes(rows, status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_exit_fee_depth_conflict_report_payload(
    report: ResearchMarketExitFeeDepthConflictReport | Mapping[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketExitFeeDepthConflictReport:
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
        raise ValueError("report must be a ResearchMarketExitFeeDepthConflictReport")
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
    item: ResearchMarketExitFeeDepthConflictInput,
    *,
    config: ResearchMarketExitFeeDepthConflictConfig,
) -> ResearchMarketExitFeeDepthConflictRow:
    gross_probability_edge = _quantize(item.model_probability - item.market_probability)
    if gross_probability_edge < ZERO:
        gross_probability_edge = ZERO
    depth_shortfall_penalty = _depth_shortfall_penalty(item.depth_coverage_ratio, config)
    fee_depth_drag_rate = _quantize(
        item.exit_fee_rate
        + (item.bid_ask_spread_rate / TWO)
        + item.exit_slippage_rate
        + depth_shortfall_penalty,
    )
    net_probability_edge = _quantize(gross_probability_edge - fee_depth_drag_rate)
    drag_to_edge_ratio = _safe_ratio(fee_depth_drag_rate, gross_probability_edge)
    reason_codes = _row_reason_codes(
        gross_probability_edge=gross_probability_edge,
        net_probability_edge=net_probability_edge,
        fee_depth_drag_rate=fee_depth_drag_rate,
        drag_to_edge_ratio=drag_to_edge_ratio,
        depth_coverage_ratio=item.depth_coverage_ratio,
        exit_fee_rate=item.exit_fee_rate,
        depth_shortfall_penalty=depth_shortfall_penalty,
        config=config,
    )
    return ResearchMarketExitFeeDepthConflictRow(
        signal_digest=_private_reference_digest(item.private_research_reference),
        observed_at=item.observed_at,
        model_probability=item.model_probability,
        market_probability=item.market_probability,
        gross_probability_edge=gross_probability_edge,
        exit_fee_rate=item.exit_fee_rate,
        bid_ask_spread_rate=item.bid_ask_spread_rate,
        exit_slippage_rate=item.exit_slippage_rate,
        depth_coverage_ratio=item.depth_coverage_ratio,
        depth_shortfall_penalty=depth_shortfall_penalty,
        fee_depth_drag_rate=fee_depth_drag_rate,
        net_probability_edge=net_probability_edge,
        drag_to_edge_ratio=drag_to_edge_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _depth_shortfall_penalty(
    depth_coverage_ratio: Decimal,
    config: ResearchMarketExitFeeDepthConflictConfig,
) -> Decimal:
    if depth_coverage_ratio >= config.minimum_depth_coverage_ratio:
        return ZERO
    shortfall = _quantize(config.minimum_depth_coverage_ratio - depth_coverage_ratio)
    return _quantize(shortfall * config.depth_shortfall_penalty_rate)


def _row_reason_codes(
    *,
    gross_probability_edge: Decimal,
    net_probability_edge: Decimal,
    fee_depth_drag_rate: Decimal,
    drag_to_edge_ratio: Decimal,
    depth_coverage_ratio: Decimal,
    exit_fee_rate: Decimal,
    depth_shortfall_penalty: Decimal,
    config: ResearchMarketExitFeeDepthConflictConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if gross_probability_edge <= ZERO:
        detail_reasons.append(REASON_EDGE_NON_POSITIVE)
    detail_reasons.extend(
        _low_value_reason(
            value=net_probability_edge,
            watch_value=config.pass_net_probability_edge_threshold,
            block_value=config.watch_net_probability_edge_threshold,
            watch_reason=REASON_NET_EDGE_WATCH,
            block_reason=REASON_NET_EDGE_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=fee_depth_drag_rate,
            watch_value=config.fee_depth_drag_watch_threshold,
            block_value=config.fee_depth_drag_block_threshold,
            watch_reason=REASON_FEE_DEPTH_DRAG_WATCH,
            block_reason=REASON_FEE_DEPTH_DRAG_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=drag_to_edge_ratio,
            watch_value=config.drag_to_edge_watch_threshold,
            block_value=config.drag_to_edge_block_threshold,
            watch_reason=REASON_DRAG_TO_EDGE_WATCH,
            block_reason=REASON_DRAG_TO_EDGE_BLOCK,
        ),
    )
    detail_reasons.extend(
        _low_value_reason(
            value=depth_coverage_ratio,
            watch_value=config.depth_coverage_watch_threshold,
            block_value=config.depth_coverage_block_threshold,
            watch_reason=REASON_DEPTH_COVERAGE_WATCH,
            block_reason=REASON_DEPTH_COVERAGE_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=exit_fee_rate,
            watch_value=config.exit_fee_rate_watch_threshold,
            block_value=config.exit_fee_rate_block_threshold,
            watch_reason=REASON_EXIT_FEE_RATE_WATCH,
            block_reason=REASON_EXIT_FEE_RATE_BLOCK,
        ),
    )
    if depth_shortfall_penalty > ZERO:
        detail_reasons.append(REASON_DEPTH_SHORTFALL_PENALTY)
    if any(reason.endswith("_block") for reason in detail_reasons) or (
        REASON_EDGE_NON_POSITIVE in detail_reasons
    ):
        return _normalize_reason_codes((REASON_BLOCK, *detail_reasons))
    if any(reason.endswith("_watch") for reason in detail_reasons):
        return _normalize_reason_codes((REASON_WATCH, *detail_reasons))
    return _normalize_reason_codes((REASON_PASS, *detail_reasons))


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


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if REASON_BLOCK in reason_codes:
        return STATUS_BLOCK
    if REASON_WATCH in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchMarketExitFeeDepthConflictRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketExitFeeDepthConflictRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: set[str] = set()
    for row in rows:
        if row.status == status:
            reasons.update(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _reason_code_counts(
    rows: tuple[ResearchMarketExitFeeDepthConflictRow, ...],
) -> tuple[ResearchMarketExitFeeDepthConflictReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchMarketExitFeeDepthConflictReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _row_sort_key(
    row: ResearchMarketExitFeeDepthConflictRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, datetime, str]:
    return (
        STATUS_SORT_RANK[row.status],
        row.net_probability_edge,
        -row.drag_to_edge_ratio,
        row.depth_coverage_ratio,
        row.observed_at,
        row.signal_digest,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketExitFeeDepthConflictInput],
) -> tuple[ResearchMarketExitFeeDepthConflictInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen: set[tuple[str, datetime]] = set()
    for item in normalized:
        if type(item) is not ResearchMarketExitFeeDepthConflictInput:
            raise ValueError("inputs must contain ResearchMarketExitFeeDepthConflictInput")
        _require_hard_flags("input", item)
        key = (item.private_research_reference, item.observed_at)
        if key in seen:
            raise ValueError("inputs must be unique by private reference and time")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketExitFeeDepthConflictRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, datetime]] = set()
    for row in normalized:
        if type(row) is not ResearchMarketExitFeeDepthConflictRow:
            raise ValueError("rows must contain ResearchMarketExitFeeDepthConflictRow")
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
) -> tuple[ResearchMarketExitFeeDepthConflictReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMarketExitFeeDepthConflictReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketExitFeeDepthConflictReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _status_count(rows: tuple[ResearchMarketExitFeeDepthConflictRow, ...], status: str) -> Decimal:
    return _decimal_from_count(sum(1 for row in rows if row.status == status))


def _mean_optional_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _validate_row_consistency(row: ResearchMarketExitFeeDepthConflictRow) -> None:
    expected_edge = _quantize(row.model_probability - row.market_probability)
    if expected_edge < ZERO:
        expected_edge = ZERO
    if row.gross_probability_edge != expected_edge:
        raise ValueError("gross_probability_edge must match probabilities")
    expected_total = _quantize(
        row.exit_fee_rate
        + (row.bid_ask_spread_rate / TWO)
        + row.exit_slippage_rate
        + row.depth_shortfall_penalty,
    )
    if row.fee_depth_drag_rate != expected_total:
        raise ValueError("fee_depth_drag_rate must match components")
    if row.net_probability_edge != _quantize(
        row.gross_probability_edge - row.fee_depth_drag_rate,
    ):
        raise ValueError("net_probability_edge must match row fields")
    if row.drag_to_edge_ratio != _safe_ratio(
        row.fee_depth_drag_rate,
        row.gross_probability_edge,
    ):
        raise ValueError("drag_to_edge_ratio must match row fields")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and REASON_PASS not in row.reason_codes:
        raise ValueError("pass rows require the pass reason")


def _validate_report_consistency(report: ResearchMarketExitFeeDepthConflictReport) -> None:
    rows = report.rows
    expected_values = {
        "input_count": _decimal_from_count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "worst_net_probability_edge": min(
            (row.net_probability_edge for row in rows),
            default=None,
        ),
        "average_net_probability_edge": _mean_optional_decimal(
            row.net_probability_edge for row in rows
        ),
        "max_fee_depth_drag_rate": max(
            (row.fee_depth_drag_rate for row in rows),
            default=ZERO,
        ),
        "max_drag_to_edge_ratio": max(
            (row.drag_to_edge_ratio for row in rows),
            default=ZERO,
        ),
        "min_depth_coverage_ratio": min(
            (row.depth_coverage_ratio for row in rows),
            default=None,
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
        return FrozenJsonArray(tuple(_freeze_json_value(item) for item in value))
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_ascending(label: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"{label} block threshold must be at least watch threshold")


def _require_descending(label: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value > watch_value:
        raise ValueError(f"{label} block threshold must not exceed watch threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 4096:
        raise ValueError(f"{field_name} is too long")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} must be supported")
    return value


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal(field_name, value)


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        seen.add(reason_code)
    if not seen:
        raise ValueError("reason_codes must be non-empty")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _decimal_from_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        if numerator <= ZERO:
            return ZERO
        return HIGH_RATIO
    return _quantize(numerator / denominator)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _private_reference_digest(value: str) -> str:
    canonical = json.dumps(
        {"private_research_reference": value},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float):
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
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            for item in value:
                _reject_unsafe_public_payload(label, item, current_path)
            return
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}.{index}",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public field at {path}.{key}")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public field at {path}")
