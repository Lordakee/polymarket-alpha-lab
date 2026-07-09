"""Readonly probability gap stability report for manual research triage."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_GAP_STABILITY_CONFIG_VERSION = (
    "research-market-probability-gap-stability-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "gap_stability_pass"
WATCH_REASON = "gap_stability_watch"
BLOCK_REASON = "gap_stability_block"
ADJUSTED_GAP_WATCH_REASON = "adjusted_gap_watch"
ADJUSTED_GAP_BLOCK_REASON = "adjusted_gap_block"
SPREAD_WIDTH_WATCH_REASON = "spread_width_watch"
SPREAD_WIDTH_BLOCK_REASON = "spread_width_block"
DEPTH_WATCH_REASON = "depth_watch"
DEPTH_BLOCK_REASON = "depth_block"
FEE_DRAG_WATCH_REASON = "fee_drag_watch"
FEE_DRAG_BLOCK_REASON = "fee_drag_block"
VOLATILITY_WATCH_REASON = "volatility_watch"
VOLATILITY_BLOCK_REASON = "volatility_block"
BOOK_AGE_WATCH_REASON = "book_age_watch"
BOOK_AGE_BLOCK_REASON = "book_age_block"
LIQUIDITY_UNCERTAINTY_WATCH_REASON = "liquidity_uncertainty_watch"
LIQUIDITY_UNCERTAINTY_BLOCK_REASON = "liquidity_uncertainty_block"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    ADJUSTED_GAP_WATCH_REASON,
    ADJUSTED_GAP_BLOCK_REASON,
    SPREAD_WIDTH_WATCH_REASON,
    SPREAD_WIDTH_BLOCK_REASON,
    DEPTH_WATCH_REASON,
    DEPTH_BLOCK_REASON,
    FEE_DRAG_WATCH_REASON,
    FEE_DRAG_BLOCK_REASON,
    VOLATILITY_WATCH_REASON,
    VOLATILITY_BLOCK_REASON,
    BOOK_AGE_WATCH_REASON,
    BOOK_AGE_BLOCK_REASON,
    LIQUIDITY_UNCERTAINTY_WATCH_REASON,
    LIQUIDITY_UNCERTAINTY_BLOCK_REASON,
)
REASON_CODE_SET = frozenset(ROW_REASON_CODES)

PASS_STABILITY_SCORE = Decimal("0.833333")
WATCH_STABILITY_SCORE = Decimal("0.500000")
BLOCK_STABILITY_SCORE = Decimal("0.000000")

__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_GAP_STABILITY_CONFIG_VERSION",
    "MarketProbabilityGapStabilityConfig",
    "MarketProbabilityGapStabilitySignal",
    "MarketProbabilityGapStabilityRow",
    "MarketProbabilityGapStabilityReasonCodeCount",
    "MarketProbabilityGapStabilityReport",
    "build_research_market_probability_gap_stability_report",
    "research_market_probability_gap_stability_report_payload",
)


@dataclass(frozen=True)
class MarketProbabilityGapStabilityConfig:
    watch_adjusted_gap: Decimal = Decimal("0.030000")
    block_adjusted_gap: Decimal = Decimal("0.015000")
    watch_spread_width: Decimal = Decimal("0.020000")
    block_spread_width: Decimal = Decimal("0.040000")
    watch_depth_score: Decimal = Decimal("0.650000")
    block_depth_score: Decimal = Decimal("0.300000")
    watch_fee_drag: Decimal = Decimal("0.010000")
    block_fee_drag: Decimal = Decimal("0.020000")
    watch_volatility_score: Decimal = Decimal("0.400000")
    block_volatility_score: Decimal = Decimal("0.800000")
    watch_book_age_seconds: Decimal = Decimal("1800.000000")
    block_book_age_seconds: Decimal = Decimal("3600.000000")
    watch_liquidity_uncertainty: Decimal = Decimal("0.400000")
    block_liquidity_uncertainty: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityGapStabilityConfig, "config")
        for field_name in (
            "watch_adjusted_gap",
            "block_adjusted_gap",
            "watch_spread_width",
            "block_spread_width",
            "watch_fee_drag",
            "block_fee_drag",
            "watch_book_age_seconds",
            "block_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_depth_score",
            "block_depth_score",
            "watch_volatility_score",
            "block_volatility_score",
            "watch_liquidity_uncertainty",
            "block_liquidity_uncertainty",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_adjusted_gap >= self.watch_adjusted_gap:
            raise ValueError("block_adjusted_gap must be below watch_adjusted_gap")
        if self.block_spread_width <= self.watch_spread_width:
            raise ValueError("block_spread_width must exceed watch_spread_width")
        if self.block_depth_score >= self.watch_depth_score:
            raise ValueError("block_depth_score must be below watch_depth_score")
        if self.block_fee_drag <= self.watch_fee_drag:
            raise ValueError("block_fee_drag must exceed watch_fee_drag")
        if self.block_volatility_score <= self.watch_volatility_score:
            raise ValueError("block_volatility_score must exceed watch_volatility_score")
        if self.block_book_age_seconds <= self.watch_book_age_seconds:
            raise ValueError("block_book_age_seconds must exceed watch_book_age_seconds")
        if self.block_liquidity_uncertainty <= self.watch_liquidity_uncertainty:
            raise ValueError(
                "block_liquidity_uncertainty must exceed watch_liquidity_uncertainty",
            )
        require_paper_only_flags("config", self)
        _reject_private_reference_fields("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class MarketProbabilityGapStabilitySignal:
    case_digest: str
    model_probability: Decimal
    book_probability: Decimal
    spread_width: Decimal
    depth_score: Decimal
    fee_drag: Decimal
    volatility_score: Decimal
    book_age_seconds: Decimal
    liquidity_uncertainty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityGapStabilitySignal, "signal")
        _require_digest("case_digest", self.case_digest)
        for field_name in ("model_probability", "book_probability"):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("spread_width", "fee_drag", "book_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_score",
            "volatility_score",
            "liquidity_uncertainty",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("signal", self)
        _reject_private_reference_fields("signal", self)
        reject_unsafe_surface_fields("signal", self)


@dataclass(frozen=True)
class MarketProbabilityGapStabilityRow:
    case_digest: str
    model_probability: Decimal
    book_probability: Decimal
    absolute_probability_gap: Decimal
    spread_width: Decimal
    fee_drag: Decimal
    adjusted_gap: Decimal
    depth_score: Decimal
    volatility_score: Decimal
    book_age_seconds: Decimal
    liquidity_uncertainty: Decimal
    stability_score: Decimal
    stability_status: str
    manual_research_ready: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    validation_config: InitVar[MarketProbabilityGapStabilityConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: MarketProbabilityGapStabilityConfig | None,
    ) -> None:
        _require_exact_type(self, MarketProbabilityGapStabilityRow, "row")
        _require_digest("case_digest", self.case_digest)
        for field_name in (
            "model_probability",
            "book_probability",
            "absolute_probability_gap",
            "spread_width",
            "fee_drag",
            "adjusted_gap",
            "depth_score",
            "volatility_score",
            "book_age_seconds",
            "liquidity_uncertainty",
            "stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "model_probability",
            "book_probability",
            "depth_score",
            "volatility_score",
            "liquidity_uncertainty",
            "stability_score",
        ):
            _require_unit_range(field_name, getattr(self, field_name))
        _require_choice("stability_status", self.stability_status, STATUSES)
        if type(self.manual_research_ready) is not bool:
            raise ValueError("manual_research_ready must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(
            self,
            _normalize_validation_config(validation_config),
        )
        require_paper_only_flags("row", self)
        _reject_private_reference_fields("row", self)
        reject_unsafe_surface_fields("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class MarketProbabilityGapStabilityReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketProbabilityGapStabilityReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        require_paper_only_flags("reason code count", self)
        _reject_private_reference_fields("reason code count", self)
        reject_unsafe_surface_fields("reason code count", self)


@dataclass(frozen=True)
class MarketProbabilityGapStabilityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_stability_score: Decimal
    min_stability_score: Decimal
    max_adjusted_gap: Decimal
    rows: tuple[MarketProbabilityGapStabilityRow, ...]
    reason_code_counts: tuple[MarketProbabilityGapStabilityReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityGapStabilityReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_GAP_STABILITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, STATUSES)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_stability_score",
            "min_stability_score",
            "max_adjusted_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_stability_score", "min_stability_score"):
            _require_unit_range(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        _reject_private_reference_fields("report", self)
        reject_unsafe_surface_fields("report", self)
        _set_or_validate_digest(self, "report")


def build_research_market_probability_gap_stability_report(
    signals: Iterable[MarketProbabilityGapStabilitySignal],
    *,
    generated_at: datetime,
    config: MarketProbabilityGapStabilityConfig | None = None,
) -> MarketProbabilityGapStabilityReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = MarketProbabilityGapStabilityConfig() if config is None else config
    if type(active_config) is not MarketProbabilityGapStabilityConfig:
        raise ValueError("config must be MarketProbabilityGapStabilityConfig")
    require_paper_only_flags("config", active_config)
    normalized_signals = _normalize_signals(signals)
    report_rows = tuple(
        sorted(
            (
                _row_from_signal(signal, config=active_config)
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    case_count = _decimal_from_int(len(report_rows))
    return MarketProbabilityGapStabilityReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_RESEARCH_MARKET_PROBABILITY_GAP_STABILITY_CONFIG_VERSION,
        report_status=_report_status(report_rows),
        case_count=case_count,
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        mean_stability_score=_mean_decimal(
            row.stability_score for row in report_rows
        ),
        min_stability_score=min(
            (row.stability_score for row in report_rows),
            default=ZERO,
        ),
        max_adjusted_gap=max((row.adjusted_gap for row in report_rows), default=ZERO),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows),
    )


def research_market_probability_gap_stability_report_payload(
    report: MarketProbabilityGapStabilityReport,
) -> "FrozenJsonObject":
    if type(report) is not MarketProbabilityGapStabilityReport:
        raise ValueError("report must be exactly MarketProbabilityGapStabilityReport")
    require_paper_only_flags("report", report)
    _reject_private_reference_fields("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_private_reference_fields("payload", payload)
    reject_unsafe_surface_fields("payload", payload)
    _require_payload_digest(payload)
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


def _row_from_signal(
    signal: MarketProbabilityGapStabilitySignal,
    *,
    config: MarketProbabilityGapStabilityConfig,
) -> MarketProbabilityGapStabilityRow:
    absolute_probability_gap = _quantize(
        abs(signal.model_probability - signal.book_probability),
    )
    adjusted_gap = _clamp_floor_zero(
        absolute_probability_gap - signal.spread_width - signal.fee_drag,
    )
    reason_codes = _reason_codes_for_values(
        adjusted_gap=adjusted_gap,
        spread_width=signal.spread_width,
        depth_score=signal.depth_score,
        fee_drag=signal.fee_drag,
        volatility_score=signal.volatility_score,
        book_age_seconds=signal.book_age_seconds,
        liquidity_uncertainty=signal.liquidity_uncertainty,
        config=config,
    )
    stability_status = _status_from_reason_codes(reason_codes)
    return MarketProbabilityGapStabilityRow(
        case_digest=signal.case_digest,
        model_probability=signal.model_probability,
        book_probability=signal.book_probability,
        absolute_probability_gap=absolute_probability_gap,
        spread_width=signal.spread_width,
        fee_drag=signal.fee_drag,
        adjusted_gap=adjusted_gap,
        depth_score=signal.depth_score,
        volatility_score=signal.volatility_score,
        book_age_seconds=signal.book_age_seconds,
        liquidity_uncertainty=signal.liquidity_uncertainty,
        stability_score=_stability_score(stability_status),
        stability_status=stability_status,
        manual_research_ready=stability_status == STATUS_PASS,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _reason_codes_for_values(
    *,
    adjusted_gap: Decimal,
    spread_width: Decimal,
    depth_score: Decimal,
    fee_drag: Decimal,
    volatility_score: Decimal,
    book_age_seconds: Decimal,
    liquidity_uncertainty: Decimal,
    config: MarketProbabilityGapStabilityConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    has_block_reason = False

    gap_reason = _low_value_reason(
        value=adjusted_gap,
        watch_value=config.watch_adjusted_gap,
        block_value=config.block_adjusted_gap,
        watch_reason=ADJUSTED_GAP_WATCH_REASON,
        block_reason=ADJUSTED_GAP_BLOCK_REASON,
    )
    if gap_reason is not None:
        detail_reasons.append(gap_reason)
        has_block_reason = has_block_reason or gap_reason == ADJUSTED_GAP_BLOCK_REASON

    for reason in (
        _high_value_reason(
            value=spread_width,
            watch_value=config.watch_spread_width,
            block_value=config.block_spread_width,
            watch_reason=SPREAD_WIDTH_WATCH_REASON,
            block_reason=SPREAD_WIDTH_BLOCK_REASON,
        ),
        _low_value_reason(
            value=depth_score,
            watch_value=config.watch_depth_score,
            block_value=config.block_depth_score,
            watch_reason=DEPTH_WATCH_REASON,
            block_reason=DEPTH_BLOCK_REASON,
        ),
        _high_value_reason(
            value=fee_drag,
            watch_value=config.watch_fee_drag,
            block_value=config.block_fee_drag,
            watch_reason=FEE_DRAG_WATCH_REASON,
            block_reason=FEE_DRAG_BLOCK_REASON,
        ),
        _high_value_reason(
            value=volatility_score,
            watch_value=config.watch_volatility_score,
            block_value=config.block_volatility_score,
            watch_reason=VOLATILITY_WATCH_REASON,
            block_reason=VOLATILITY_BLOCK_REASON,
        ),
        _high_value_reason(
            value=book_age_seconds,
            watch_value=config.watch_book_age_seconds,
            block_value=config.block_book_age_seconds,
            watch_reason=BOOK_AGE_WATCH_REASON,
            block_reason=BOOK_AGE_BLOCK_REASON,
        ),
        _high_value_reason(
            value=liquidity_uncertainty,
            watch_value=config.watch_liquidity_uncertainty,
            block_value=config.block_liquidity_uncertainty,
            watch_reason=LIQUIDITY_UNCERTAINTY_WATCH_REASON,
            block_reason=LIQUIDITY_UNCERTAINTY_BLOCK_REASON,
        ),
    ):
        if reason is None:
            continue
        detail_reasons.append(reason)
        has_block_reason = has_block_reason or reason.endswith("_block")

    if has_block_reason:
        return (BLOCK_REASON, *detail_reasons)
    if detail_reasons:
        return (WATCH_REASON, *detail_reasons)
    return (PASS_REASON,)


def _low_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str | None:
    if value < block_value:
        return block_reason
    if value < watch_value:
        return watch_reason
    return None


def _high_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str | None:
    if value >= block_value:
        return block_reason
    if value >= watch_value:
        return watch_reason
    return None


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _stability_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return BLOCK_STABILITY_SCORE
    if status == STATUS_WATCH:
        return WATCH_STABILITY_SCORE
    return PASS_STABILITY_SCORE


def _report_status(rows: tuple[MarketProbabilityGapStabilityRow, ...]) -> str:
    if any(row.stability_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.stability_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_signals(
    signals: Iterable[MarketProbabilityGapStabilitySignal],
) -> tuple[MarketProbabilityGapStabilitySignal, ...]:
    if isinstance(signals, (str, bytes, dict)):
        raise ValueError("signals must be an iterable of signal rows")
    normalized = tuple(signals)
    seen_case_digests: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketProbabilityGapStabilitySignal:
            raise ValueError(
                "signals must contain MarketProbabilityGapStabilitySignal",
            )
        require_paper_only_flags("signal", signal)
        if signal.case_digest in seen_case_digests:
            raise ValueError("case_digest values must be unique")
        seen_case_digests.add(signal.case_digest)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketProbabilityGapStabilityRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_case_digests: set[str] = set()
    for row in normalized:
        if type(row) is not MarketProbabilityGapStabilityRow:
            raise ValueError("rows must contain MarketProbabilityGapStabilityRow")
        require_paper_only_flags("row", row)
        if row.case_digest in seen_case_digests:
            raise ValueError("rows case_digest values must be unique")
        seen_case_digests.add(row.case_digest)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[MarketProbabilityGapStabilityReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not MarketProbabilityGapStabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketProbabilityGapStabilityReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: MarketProbabilityGapStabilityRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.stability_status],
        row.stability_score,
        row.adjusted_gap,
        row.case_digest,
    )


def _reason_code_counts(
    rows: tuple[MarketProbabilityGapStabilityRow, ...],
) -> tuple[MarketProbabilityGapStabilityReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketProbabilityGapStabilityReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[MarketProbabilityGapStabilityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.stability_status == status))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _normalize_validation_config(
    config: MarketProbabilityGapStabilityConfig | None,
) -> MarketProbabilityGapStabilityConfig:
    if config is None:
        return MarketProbabilityGapStabilityConfig()
    if type(config) is not MarketProbabilityGapStabilityConfig:
        raise ValueError("validation_config must be MarketProbabilityGapStabilityConfig")
    require_paper_only_flags("validation_config", config)
    return config


def _validate_row_consistency(
    row: MarketProbabilityGapStabilityRow,
    config: MarketProbabilityGapStabilityConfig,
) -> None:
    if row.absolute_probability_gap != _quantize(
        abs(row.model_probability - row.book_probability),
    ):
        raise ValueError("absolute_probability_gap must match probabilities")
    expected_adjusted_gap = _clamp_floor_zero(
        row.absolute_probability_gap - row.spread_width - row.fee_drag,
    )
    if row.adjusted_gap != expected_adjusted_gap:
        raise ValueError("adjusted_gap must match gap after spread and fee drag")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.stability_status != expected_status:
        raise ValueError("stability_status must match reason_codes")
    if row.manual_research_ready != (row.stability_status == STATUS_PASS):
        raise ValueError("manual_research_ready must match stability_status")
    if row.stability_score != _stability_score(row.stability_status):
        raise ValueError("stability_score must match stability_status")
    expected_reason_codes = _reason_codes_for_values(
        adjusted_gap=row.adjusted_gap,
        spread_width=row.spread_width,
        depth_score=row.depth_score,
        fee_drag=row.fee_drag,
        volatility_score=row.volatility_score,
        book_age_seconds=row.book_age_seconds,
        liquidity_uncertainty=row.liquidity_uncertainty,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row stability fields")


def _validate_report_consistency(report: MarketProbabilityGapStabilityReport) -> None:
    expected_case_count = _decimal_from_int(len(report.rows))
    expected_values = {
        "case_count": expected_case_count,
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "mean_stability_score": _mean_decimal(
            row.stability_score for row in report.rows
        ),
        "min_stability_score": min(
            (row.stability_score for row in report.rows),
            default=ZERO,
        ),
        "max_adjusted_gap": max((row.adjusted_gap for row in report.rows), default=ZERO),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")


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
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and len(reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    if reason_codes[0] == WATCH_REASON and any(
        reason.endswith("_block") for reason in reason_codes[1:]
    ):
        raise ValueError("watch reason_codes must not contain block reasons")
    if reason_codes[0] == BLOCK_REASON and not any(
        reason.endswith("_block") for reason in reason_codes[1:]
    ):
        raise ValueError("block reason_codes must include a block detail")
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    _reject_private_reference_fields(f"{label} digest payload", ready_value)
    reject_unsafe_surface_fields(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _require_payload_digest(payload: dict[str, Any]) -> None:
    supplied_digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", supplied_digest)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected_digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _unit_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    _require_unit_range(name, normalized)
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


def _clamp_floor_zero(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_unit_range(name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between zero and one")


def _reject_private_reference_fields(label: str, payload: object) -> None:
    unsafe_fragments = (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in unsafe_fragments):
            raise ValueError(f"unsafe private reference field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()
