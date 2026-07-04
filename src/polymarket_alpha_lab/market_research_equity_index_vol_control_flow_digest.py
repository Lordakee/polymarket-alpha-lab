"""Pure Phase 1 equity-index volatility-control flow digest reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION = (
    "market-research-equity-index-vol-control-flow-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
FLOW_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
FLOW_DIRECTIONS = ("deleveraging", "releveraging")

PREFIX = "market_research_equity_index_vol_control_flow_digest_"
READY_REASON = f"{PREFIX}ready"
NO_INPUTS_REASON = f"{PREFIX}no_inputs"
MATERIAL_FLOW_REASON = f"{PREFIX}material_flow"
VOLATILITY_GAP_REASON = f"{PREFIX}volatility_gap"
LARGE_EQUITY_WEIGHT_CHANGE_REASON = f"{PREFIX}large_equity_weight_change"
STALE_SIGNAL_REASON = f"{PREFIX}stale_signal"
THIN_SOURCES_REASON = f"{PREFIX}thin_sources"
MISSING_CONFIRMATION_REASON = f"{PREFIX}missing_confirmation"
SLOW_ACKNOWLEDGEMENT_REASON = f"{PREFIX}slow_acknowledgement"
CONTRADICTION_PRESENT_REASON = f"{PREFIX}contradiction_present"

SIGNAL_REASON_CODE_SEQUENCE = (
    MATERIAL_FLOW_REASON,
    VOLATILITY_GAP_REASON,
    LARGE_EQUITY_WEIGHT_CHANGE_REASON,
)

ROW_REASON_CODE_SEQUENCE = (
    READY_REASON,
    MATERIAL_FLOW_REASON,
    VOLATILITY_GAP_REASON,
    LARGE_EQUITY_WEIGHT_CHANGE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    CONTRADICTION_PRESENT_REASON,
)

REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_FLOW_REASON,
    VOLATILITY_GAP_REASON,
    LARGE_EQUITY_WEIGHT_CHANGE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    CONTRADICTION_PRESENT_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

REASON_CODE_SEQUENCE = REPORT_REASON_CODE_SEQUENCE

QUALITY_REASON_CODES = (
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    CONTRADICTION_PRESENT_REASON,
)

BLOCKING_REASON_CODES = (
    MISSING_CONFIRMATION_REASON,
    CONTRADICTION_PRESENT_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_equity_index_vol_control_flow_digest",
    STATUS_WATCH: "watch_report_only_market_research_equity_index_vol_control_flow_digest",
    STATUS_BLOCKED: "block_report_only_market_research_equity_index_vol_control_flow_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityIndexVolControlFlowDigestConfig",
    "MarketResearchEquityIndexVolControlFlowInputRow",
    "MarketResearchEquityIndexVolControlFlowReasonCodeCount",
    "MarketResearchEquityIndexVolControlFlowReport",
    "MarketResearchEquityIndexVolControlFlowRow",
    "build_market_research_equity_index_vol_control_flow_digest",
    "market_research_equity_index_vol_control_flow_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquityIndexVolControlFlowDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2")
    min_confirmation_count: Decimal = Decimal("1")
    min_abs_estimated_flow_usd: Decimal = Decimal("250000000.000000")
    min_abs_volatility_gap: Decimal = Decimal("0.020000")
    min_abs_equity_weight_change: Decimal = Decimal("0.030000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexVolControlFlowDigestConfig:
            raise TypeError(
                "MarketResearchEquityIndexVolControlFlowDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexVolControlFlowDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEquityIndexVolControlFlowDigestConfig",
            )
        _require_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_signal_age_seconds",
            "min_abs_estimated_flow_usd",
            "min_abs_volatility_gap",
            "min_abs_equity_weight_change",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_source_count", "min_confirmation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexVolControlFlowInputRow:
    research_key: str
    condition_id: str
    index_symbol: str
    vol_control_event_key: str
    flow_direction: str
    signal_reference: str
    signaled_at: datetime
    acknowledged_at: datetime
    source_count: Decimal
    confirmation_count: Decimal
    realized_volatility: Decimal
    target_volatility: Decimal
    equity_weight_before: Decimal
    equity_weight_after: Decimal
    estimated_flow_usd: Decimal
    tracking_volume_ratio: Decimal
    contradiction_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexVolControlFlowInputRow:
            raise TypeError(
                "MarketResearchEquityIndexVolControlFlowInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexVolControlFlowInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchEquityIndexVolControlFlowInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "index_symbol",
            "vol_control_event_key",
            "signal_reference",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_index_symbol("index_symbol", self.index_symbol)
        _require_flow_direction("flow_direction", self.flow_direction)
        object.__setattr__(self, "signaled_at", _as_utc("signaled_at", self.signaled_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in ("source_count", "confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "realized_volatility",
            "target_volatility",
            "equity_weight_before",
            "equity_weight_after",
            "tracking_volume_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_flow_usd",
            _require_finite_decimal("estimated_flow_usd", self.estimated_flow_usd),
        )
        _validate_flow_direction(self.flow_direction, self.estimated_flow_usd)
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexVolControlFlowRow:
    research_key: str
    condition_id: str
    index_symbol: str
    vol_control_event_key: str
    flow_direction: str
    flow_status: str
    signal_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal
    source_count: Decimal
    confirmation_count: Decimal
    realized_volatility: Decimal
    target_volatility: Decimal
    volatility_gap: Decimal
    abs_volatility_gap: Decimal
    equity_weight_before: Decimal
    equity_weight_after: Decimal
    equity_weight_change: Decimal
    abs_equity_weight_change: Decimal
    estimated_flow_usd: Decimal
    flow_abs_usd: Decimal
    tracking_volume_ratio: Decimal
    contradiction_count: Decimal
    redacted_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexVolControlFlowRow:
            raise TypeError(
                "MarketResearchEquityIndexVolControlFlowRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexVolControlFlowRow:
            raise ValueError(
                "row must be exactly MarketResearchEquityIndexVolControlFlowRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "index_symbol",
            "vol_control_event_key",
            "redacted_signal_reference",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_index_symbol("index_symbol", self.index_symbol)
        _require_flow_direction("flow_direction", self.flow_direction)
        _require_flow_status("flow_status", self.flow_status)
        for field_name in ("signal_age_seconds", "acknowledgement_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "realized_volatility",
            "target_volatility",
            "abs_volatility_gap",
            "equity_weight_before",
            "equity_weight_after",
            "abs_equity_weight_change",
            "tracking_volume_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "volatility_gap",
            "equity_weight_change",
            "estimated_flow_usd",
            "flow_abs_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        if self.flow_abs_usd < ZERO:
            raise ValueError("flow_abs_usd must be nonnegative")
        object.__setattr__(
            self,
            "redacted_signal_reference",
            _require_redacted_reference(
                "redacted_signal_reference",
                self.redacted_signal_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexVolControlFlowReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexVolControlFlowReasonCodeCount:
            raise TypeError(
                "MarketResearchEquityIndexVolControlFlowReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexVolControlFlowReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchEquityIndexVolControlFlowReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexVolControlFlowReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    vol_control_event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    material_flow_count: Decimal
    volatility_gap_count: Decimal
    large_equity_weight_change_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    missing_confirmation_count: Decimal
    slow_acknowledgement_count: Decimal
    contradiction_count: Decimal
    net_estimated_flow_usd: Decimal
    gross_estimated_flow_usd: Decimal
    max_flow_abs_usd: Decimal
    average_abs_volatility_gap: Decimal
    average_tracking_volume_ratio: Decimal
    max_signal_age_seconds: Decimal
    rows: tuple[MarketResearchEquityIndexVolControlFlowRow, ...]
    reason_code_counts: tuple[MarketResearchEquityIndexVolControlFlowReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexVolControlFlowReport:
            raise TypeError(
                "MarketResearchEquityIndexVolControlFlowReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexVolControlFlowReport:
            raise ValueError(
                "report must be exactly MarketResearchEquityIndexVolControlFlowReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_flow_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "vol_control_event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "material_flow_count",
            "volatility_gap_count",
            "large_equity_weight_change_count",
            "stale_signal_count",
            "thin_source_count",
            "missing_confirmation_count",
            "slow_acknowledgement_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_estimated_flow_usd",
            "gross_estimated_flow_usd",
            "max_flow_abs_usd",
            "average_abs_volatility_gap",
            "average_tracking_volume_ratio",
            "max_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        if self.gross_estimated_flow_usd < ZERO:
            raise ValueError("gross_estimated_flow_usd must be nonnegative")
        if self.max_flow_abs_usd < ZERO:
            raise ValueError("max_flow_abs_usd must be nonnegative")
        if self.average_abs_volatility_gap < ZERO or self.average_abs_volatility_gap > ONE:
            raise ValueError("average_abs_volatility_gap must be a ratio")
        if self.average_tracking_volume_ratio < ZERO or self.average_tracking_volume_ratio > ONE:
            raise ValueError("average_tracking_volume_ratio must be a ratio")
        if self.max_signal_age_seconds < ZERO:
            raise ValueError("max_signal_age_seconds must be nonnegative")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_equity_index_vol_control_flow_digest(
    rows: list[MarketResearchEquityIndexVolControlFlowInputRow]
    | tuple[MarketResearchEquityIndexVolControlFlowInputRow, ...],
    *,
    config: MarketResearchEquityIndexVolControlFlowDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexVolControlFlowReport:
    if type(config) is not MarketResearchEquityIndexVolControlFlowDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEquityIndexVolControlFlowDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows, generated_at_utc)
    digest_rows = tuple(
        _build_row(input_row, config=config, generated_at=generated_at_utc)
        for input_row in input_rows
    )
    ranked_rows = tuple(sorted(digest_rows, key=_row_sort_key))
    event_count = _count(len(ranked_rows))
    ready_event_count = _status_count(ranked_rows, STATUS_READY)
    watch_event_count = _status_count(ranked_rows, STATUS_WATCH)
    blocked_event_count = _status_count(ranked_rows, STATUS_BLOCKED)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_event_count=blocked_event_count,
        watch_event_count=watch_event_count,
    )
    reason_codes = _report_reason_codes(ranked_rows)

    return MarketResearchEquityIndexVolControlFlowReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        vol_control_event_count=event_count,
        ready_event_count=ready_event_count,
        watch_event_count=watch_event_count,
        blocked_event_count=blocked_event_count,
        material_flow_count=_reason_count(ranked_rows, MATERIAL_FLOW_REASON),
        volatility_gap_count=_reason_count(ranked_rows, VOLATILITY_GAP_REASON),
        large_equity_weight_change_count=_reason_count(
            ranked_rows,
            LARGE_EQUITY_WEIGHT_CHANGE_REASON,
        ),
        stale_signal_count=_reason_count(ranked_rows, STALE_SIGNAL_REASON),
        thin_source_count=_reason_count(ranked_rows, THIN_SOURCES_REASON),
        missing_confirmation_count=_reason_count(
            ranked_rows,
            MISSING_CONFIRMATION_REASON,
        ),
        slow_acknowledgement_count=_reason_count(
            ranked_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        contradiction_count=_sum_decimal(row.contradiction_count for row in ranked_rows),
        net_estimated_flow_usd=_sum_decimal(row.estimated_flow_usd for row in ranked_rows),
        gross_estimated_flow_usd=_sum_decimal(row.flow_abs_usd for row in ranked_rows),
        max_flow_abs_usd=max((row.flow_abs_usd for row in ranked_rows), default=ZERO),
        average_abs_volatility_gap=_ratio(
            _sum_decimal(row.abs_volatility_gap for row in ranked_rows),
            event_count,
        ),
        average_tracking_volume_ratio=_ratio(
            _sum_decimal(row.tracking_volume_ratio for row in ranked_rows),
            event_count,
        ),
        max_signal_age_seconds=max(
            (row.signal_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=_reason_code_counts(
            ranked_rows,
            reason_codes,
            event_count,
        ),
        reason_codes=reason_codes,
    )


def market_research_equity_index_vol_control_flow_digest_payload(
    report: MarketResearchEquityIndexVolControlFlowReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityIndexVolControlFlowReport:
        raise ValueError(
            "report must be a MarketResearchEquityIndexVolControlFlowReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report, _RedactionMap())
    if type(payload) is not dict:
        raise ValueError("payload must be a mapping")
    return payload


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchEquityIndexVolControlFlowInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchEquityIndexVolControlFlowInputRow:
            raise ValueError(
                "rows must contain MarketResearchEquityIndexVolControlFlowInputRow",
            )
        _require_hard_flags("input row", row)
        key = (row.research_key, row.condition_id, row.vol_control_event_key)
        if key in seen:
            raise ValueError("rows must use unique research condition event keys")
        seen.add(key)
        if row.signaled_at > generated_at:
            raise ValueError("signaled_at cannot be after generated_at")
        if row.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at cannot be after generated_at")
        if row.acknowledged_at < row.signaled_at:
            raise ValueError("acknowledged_at cannot be before signaled_at")
    return tuple(
        sorted(
            normalized,
            key=lambda row: (row.research_key, row.condition_id, row.vol_control_event_key),
        ),
    )


def _build_row(
    input_row: MarketResearchEquityIndexVolControlFlowInputRow,
    *,
    config: MarketResearchEquityIndexVolControlFlowDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexVolControlFlowRow:
    signal_age_seconds = _seconds_between(input_row.signaled_at, generated_at)
    acknowledgement_lag_seconds = _seconds_between(
        input_row.signaled_at,
        input_row.acknowledged_at,
    )
    volatility_gap = _finite_decimal(
        input_row.realized_volatility - input_row.target_volatility,
    )
    abs_volatility_gap = abs(volatility_gap).quantize(QUANT)
    equity_weight_change = _finite_decimal(
        input_row.equity_weight_after - input_row.equity_weight_before,
    )
    abs_equity_weight_change = abs(equity_weight_change).quantize(QUANT)
    flow_abs_usd = abs(input_row.estimated_flow_usd).quantize(QUANT)
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        confirmation_count=input_row.confirmation_count,
        flow_abs_usd=flow_abs_usd,
        abs_volatility_gap=abs_volatility_gap,
        abs_equity_weight_change=abs_equity_weight_change,
        contradiction_count=input_row.contradiction_count,
        config=config,
    )
    return MarketResearchEquityIndexVolControlFlowRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        index_symbol=input_row.index_symbol,
        vol_control_event_key=input_row.vol_control_event_key,
        flow_direction=input_row.flow_direction,
        flow_status=_row_status(reason_codes),
        signal_age_seconds=signal_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        confirmation_count=input_row.confirmation_count,
        realized_volatility=input_row.realized_volatility,
        target_volatility=input_row.target_volatility,
        volatility_gap=volatility_gap,
        abs_volatility_gap=abs_volatility_gap,
        equity_weight_before=input_row.equity_weight_before,
        equity_weight_after=input_row.equity_weight_after,
        equity_weight_change=equity_weight_change,
        abs_equity_weight_change=abs_equity_weight_change,
        estimated_flow_usd=input_row.estimated_flow_usd,
        flow_abs_usd=flow_abs_usd,
        tracking_volume_ratio=input_row.tracking_volume_ratio,
        contradiction_count=input_row.contradiction_count,
        redacted_signal_reference=_redacted_reference(input_row.signal_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal,
    source_count: Decimal,
    confirmation_count: Decimal,
    flow_abs_usd: Decimal,
    abs_volatility_gap: Decimal,
    abs_equity_weight_change: Decimal,
    contradiction_count: Decimal,
    config: MarketResearchEquityIndexVolControlFlowDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if flow_abs_usd >= config.min_abs_estimated_flow_usd:
        reasons.append(MATERIAL_FLOW_REASON)
    if abs_volatility_gap >= config.min_abs_volatility_gap:
        reasons.append(VOLATILITY_GAP_REASON)
    if abs_equity_weight_change >= config.min_abs_equity_weight_change:
        reasons.append(LARGE_EQUITY_WEIGHT_CHANGE_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if confirmation_count < config.min_confirmation_count:
        reasons.append(MISSING_CONFIRMATION_REASON)
    if acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if contradiction_count > ZERO:
        reasons.append(CONTRADICTION_PRESENT_REASON)
    if not reasons:
        return (READY_REASON,)
    if not any(reason in QUALITY_REASON_CODES for reason in reasons):
        return (READY_REASON,) + tuple(
            reason for reason in SIGNAL_REASON_CODE_SEQUENCE if reason in reasons
        )
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in reason_codes for reason in BLOCKING_REASON_CODES):
        return STATUS_BLOCKED
    if any(reason in reason_codes for reason in QUALITY_REASON_CODES):
        return STATUS_WATCH
    return STATUS_READY


def _report_status(
    *,
    has_inputs: bool,
    blocked_event_count: Decimal,
    watch_event_count: Decimal,
) -> str:
    if not has_inputs or blocked_event_count > ZERO:
        return STATUS_BLOCKED
    if watch_event_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    rows: tuple[MarketResearchEquityIndexVolControlFlowRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    }
    if not observed:
        return (READY_REASON,)
    return tuple(
        reason_code for reason_code in REPORT_REASON_CODE_SEQUENCE if reason_code in observed
    )


def _reason_code_counts(
    rows: tuple[MarketResearchEquityIndexVolControlFlowRow, ...],
    reason_codes: tuple[str, ...],
    event_count: Decimal,
) -> tuple[MarketResearchEquityIndexVolControlFlowReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        counts = Counter(reason_codes)
    else:
        counts = Counter(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != READY_REASON
        )
        if not counts and reason_codes == (READY_REASON,):
            counts = Counter(reason_codes)
    return tuple(
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            event_ratio=_ratio(_count(count), event_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (
                -item[1],
                REPORT_REASON_CODE_SEQUENCE.index(item[0]),
            ),
        )
    )


def _status_count(
    rows: tuple[MarketResearchEquityIndexVolControlFlowRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.flow_status == status))


def _reason_count(
    rows: tuple[MarketResearchEquityIndexVolControlFlowRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchEquityIndexVolControlFlowRow,
) -> tuple[int, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.flow_status],
        row.vol_control_event_key,
        row.index_symbol,
        row.research_key,
    )


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchEquityIndexVolControlFlowRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    previous_key: tuple[int, str, str, str] | None = None
    for row in rows:
        if type(row) is not MarketResearchEquityIndexVolControlFlowRow:
            raise ValueError("rows must contain MarketResearchEquityIndexVolControlFlowRow")
        _require_hard_flags("row", row)
        row_id = (row.research_key, row.condition_id, row.vol_control_event_key)
        if row_id in seen:
            raise ValueError("rows must use unique research condition event keys")
        seen.add(row_id)
        key = _row_sort_key(row)
        if previous_key is not None and previous_key >= key:
            raise ValueError("rows must use deterministic sort")
        previous_key = key
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchEquityIndexVolControlFlowReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, int] | None = None
    for row in rows:
        if type(row) is not MarketResearchEquityIndexVolControlFlowReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquityIndexVolControlFlowReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, REPORT_REASON_CODE_SEQUENCE.index(row.reason_code))
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic sort")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value, ROW_REASON_CODE_SEQUENCE)
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    if READY_REASON in reason_codes:
        disallowed = tuple(
            reason_code
            for reason_code in reason_codes
            if reason_code != READY_REASON and reason_code not in SIGNAL_REASON_CODE_SEQUENCE
        )
        if disallowed:
            raise ValueError("reason_codes ready cannot be combined with quality reasons")
    if READY_REASON not in reason_codes and not any(
        reason_code in QUALITY_REASON_CODES for reason_code in reason_codes
    ):
        raise ValueError("reason_codes signal-only rows require ready")
    return reason_codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        value,
        REPORT_REASON_CODE_SEQUENCE,
    )
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if any(type(reason_code) is not str for reason_code in reason_codes):
        raise ValueError(f"{field_name} must contain strings")
    if any(reason_code not in allowed_reason_codes for reason_code in reason_codes):
        raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_row(row: MarketResearchEquityIndexVolControlFlowRow) -> None:
    _validate_flow_direction(row.flow_direction, row.estimated_flow_usd)
    if row.flow_abs_usd != abs(row.estimated_flow_usd).quantize(QUANT):
        raise ValueError("flow_abs_usd must match estimated_flow_usd magnitude")
    expected_volatility_gap = _finite_decimal(row.realized_volatility - row.target_volatility)
    if row.volatility_gap != expected_volatility_gap:
        raise ValueError("volatility_gap must match realized_volatility minus target_volatility")
    if row.abs_volatility_gap != abs(row.volatility_gap).quantize(QUANT):
        raise ValueError("abs_volatility_gap must match volatility_gap magnitude")
    expected_weight_change = _finite_decimal(
        row.equity_weight_after - row.equity_weight_before,
    )
    if row.equity_weight_change != expected_weight_change:
        raise ValueError("equity_weight_change must match equity weight inputs")
    if row.abs_equity_weight_change != abs(row.equity_weight_change).quantize(QUANT):
        raise ValueError("abs_equity_weight_change must match equity_weight_change magnitude")
    if row.flow_status != _row_status(row.reason_codes):
        raise ValueError("flow_status must match reason_codes")
    if row.flow_status == STATUS_BLOCKED and not any(
        reason in row.reason_codes for reason in BLOCKING_REASON_CODES
    ):
        raise ValueError("blocked rows require a blocking reason")


def _validate_report(report: MarketResearchEquityIndexVolControlFlowReport) -> None:
    if report.vol_control_event_count != _count(len(report.rows)):
        raise ValueError("vol_control_event_count must match rows")
    if report.ready_event_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_event_count must match rows")
    if report.watch_event_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_event_count must match rows")
    if report.blocked_event_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_event_count must match rows")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_event_count=report.blocked_event_count,
        watch_event_count=report.watch_event_count,
    ):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
        report.vol_control_event_count,
    ):
        raise ValueError("reason_code_counts must match rows")
    _validate_report_reason_metric(report, "material_flow_count", MATERIAL_FLOW_REASON)
    _validate_report_reason_metric(report, "volatility_gap_count", VOLATILITY_GAP_REASON)
    _validate_report_reason_metric(
        report,
        "large_equity_weight_change_count",
        LARGE_EQUITY_WEIGHT_CHANGE_REASON,
    )
    _validate_report_reason_metric(report, "stale_signal_count", STALE_SIGNAL_REASON)
    _validate_report_reason_metric(report, "thin_source_count", THIN_SOURCES_REASON)
    _validate_report_reason_metric(
        report,
        "missing_confirmation_count",
        MISSING_CONFIRMATION_REASON,
    )
    _validate_report_reason_metric(
        report,
        "slow_acknowledgement_count",
        SLOW_ACKNOWLEDGEMENT_REASON,
    )
    if report.contradiction_count != _sum_decimal(
        row.contradiction_count for row in report.rows
    ):
        raise ValueError("contradiction_count must match rows")
    if report.net_estimated_flow_usd != _sum_decimal(
        row.estimated_flow_usd for row in report.rows
    ):
        raise ValueError("net_estimated_flow_usd must match rows")
    if report.gross_estimated_flow_usd != _sum_decimal(
        row.flow_abs_usd for row in report.rows
    ):
        raise ValueError("gross_estimated_flow_usd must match rows")
    if report.max_flow_abs_usd != max(
        (row.flow_abs_usd for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_flow_abs_usd must match rows")
    if report.average_abs_volatility_gap != _ratio(
        _sum_decimal(row.abs_volatility_gap for row in report.rows),
        report.vol_control_event_count,
    ):
        raise ValueError("average_abs_volatility_gap must match rows")
    if report.average_tracking_volume_ratio != _ratio(
        _sum_decimal(row.tracking_volume_ratio for row in report.rows),
        report.vol_control_event_count,
    ):
        raise ValueError("average_tracking_volume_ratio must match rows")
    if report.max_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_age_seconds must match rows")


def _validate_report_reason_metric(
    report: MarketResearchEquityIndexVolControlFlowReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _reason_count(report.rows, reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_index_symbol(field_name: str, value: object) -> str:
    _require_text(field_name, value)
    assert type(value) is str
    parts = value.split(".")
    if value != value.upper() or any(not part.isalnum() for part in parts):
        raise ValueError(f"{field_name} must be an uppercase public index symbol")
    return value


def _require_flow_direction(field_name: str, value: object) -> str:
    if type(value) is not str or value not in FLOW_DIRECTIONS:
        raise ValueError(f"{field_name} must be one of deleveraging or releveraging")
    return value


def _require_flow_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in FLOW_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime interval must be nonnegative")
    delta = end - start
    total_microseconds = (
        (Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND)
        + (Decimal(delta.seconds) * MICROSECONDS_PER_SECOND)
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _finite_decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _finite_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _validate_flow_direction(flow_direction: str, estimated_flow_usd: Decimal) -> None:
    if flow_direction == "deleveraging" and estimated_flow_usd > ZERO:
        raise ValueError("estimated_flow_usd direction mismatch")
    if flow_direction == "releveraging" and estimated_flow_usd < ZERO:
        raise ValueError("estimated_flow_usd direction mismatch")


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_text(field_name, value)
    assert type(value) is str
    if not _reference_is_public(value):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _redacted_reference(value: str) -> str:
    if _reference_is_public(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _reference_is_public(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return False
    if "private" in lowered:
        return False
    return True


class _RedactionMap:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], str] = {}
        self._counters: Counter[str] = Counter()

    def ref(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._values:
            self._counters[kind] += 1
            self._values[key] = f"<redacted-{kind}-{self._counters[kind]:03d}>"
        return self._values[key]


def _payload_value(value: object, redaction_map: _RedactionMap) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item, redaction_map) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, redaction_map) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            field_name = field.name
            if field_name == "condition_id":
                continue
            field_value = getattr(value, field_name)
            payload[field_name] = _payload_value(field_value, redaction_map)
        if isinstance(value, MarketResearchEquityIndexVolControlFlowRow):
            payload["redacted_condition_ref"] = redaction_map.ref(
                "condition",
                value.condition_id,
            )
        return payload
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, redaction_map) for key, item in value.items()
        }
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")
