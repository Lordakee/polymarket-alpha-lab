"""Pure Phase 1 equity-index pre-market gap fade digest reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION = (
    "market-research-equity-index-pre-market-gap-fade-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
GAP_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
GAP_DIRECTIONS = ("gap_up", "gap_down", "flat")

PREFIX = "market_research_equity_index_pre_market_gap_fade_digest_"
READY_REASON = f"{PREFIX}ready"
NO_INPUTS_REASON = f"{PREFIX}no_inputs"
MATERIAL_GAP_REASON = f"{PREFIX}material_gap"
FADE_PRESSURE_REASON = f"{PREFIX}fade_pressure"
EXTENDED_OVERNIGHT_RANGE_REASON = f"{PREFIX}extended_overnight_range"
COUNTER_TREND_GAP_REASON = f"{PREFIX}counter_trend_gap"
LOW_OPENING_LIQUIDITY_REASON = f"{PREFIX}low_opening_liquidity"
STALE_SIGNAL_REASON = f"{PREFIX}stale_signal"
THIN_SOURCES_REASON = f"{PREFIX}thin_sources"
MISSING_CONFIRMATION_REASON = f"{PREFIX}missing_confirmation"
SLOW_ACKNOWLEDGEMENT_REASON = f"{PREFIX}slow_acknowledgement"
CONTRADICTION_PRESENT_REASON = f"{PREFIX}contradiction_present"

ROW_REASON_CODE_SEQUENCE = (
    READY_REASON,
    MATERIAL_GAP_REASON,
    FADE_PRESSURE_REASON,
    EXTENDED_OVERNIGHT_RANGE_REASON,
    COUNTER_TREND_GAP_REASON,
    LOW_OPENING_LIQUIDITY_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    CONTRADICTION_PRESENT_REASON,
)

REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_GAP_REASON,
    FADE_PRESSURE_REASON,
    EXTENDED_OVERNIGHT_RANGE_REASON,
    COUNTER_TREND_GAP_REASON,
    LOW_OPENING_LIQUIDITY_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    CONTRADICTION_PRESENT_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

REASON_CODE_SEQUENCE = REPORT_REASON_CODE_SEQUENCE
BLOCKING_REASON_CODES = (
    MISSING_CONFIRMATION_REASON,
    CONTRADICTION_PRESENT_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_equity_index_pre_market_gap_fade_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_equity_index_pre_market_gap_fade_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_equity_index_pre_market_gap_fade_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityIndexPreMarketGapFadeDigestConfig",
    "MarketResearchEquityIndexPreMarketGapFadeInputRow",
    "MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount",
    "MarketResearchEquityIndexPreMarketGapFadeReport",
    "MarketResearchEquityIndexPreMarketGapFadeRow",
    "build_market_research_equity_index_pre_market_gap_fade_digest",
    "market_research_equity_index_pre_market_gap_fade_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquityIndexPreMarketGapFadeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2")
    min_confirmation_count: Decimal = Decimal("1")
    min_abs_pre_market_gap_pct: Decimal = Decimal("0.006000")
    min_fade_pressure_score: Decimal = Decimal("0.650000")
    min_overnight_range_pct: Decimal = Decimal("0.010000")
    min_abs_prior_day_trend_pct: Decimal = Decimal("0.012000")
    max_opening_liquidity_ratio: Decimal = Decimal("0.350000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexPreMarketGapFadeDigestConfig:
            raise TypeError(
                "MarketResearchEquityIndexPreMarketGapFadeDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexPreMarketGapFadeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEquityIndexPreMarketGapFadeDigestConfig",
            )
        _require_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_signal_age_seconds",
            "min_abs_pre_market_gap_pct",
            "min_fade_pressure_score",
            "min_overnight_range_pct",
            "min_abs_prior_day_trend_pct",
            "max_opening_liquidity_ratio",
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
        for field_name in (
            "min_abs_pre_market_gap_pct",
            "min_fade_pressure_score",
            "min_overnight_range_pct",
            "min_abs_prior_day_trend_pct",
            "max_opening_liquidity_ratio",
        ):
            if getattr(self, field_name) > ONE:
                raise ValueError(f"{field_name} must be at most 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexPreMarketGapFadeInputRow:
    research_key: str
    condition_id: str
    index_symbol: str
    gap_event_key: str
    signal_reference: str
    signaled_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    confirmation_count: Decimal
    pre_market_gap_pct: Decimal
    overnight_range_pct: Decimal
    prior_day_trend_pct: Decimal
    fade_pressure_score: Decimal
    opening_liquidity_ratio: Decimal
    contradiction_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexPreMarketGapFadeInputRow:
            raise TypeError(
                "MarketResearchEquityIndexPreMarketGapFadeInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexPreMarketGapFadeInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchEquityIndexPreMarketGapFadeInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "gap_event_key",
            "signal_reference",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_index_symbol("index_symbol", self.index_symbol)
        object.__setattr__(self, "signaled_at", _as_utc("signaled_at", self.signaled_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in ("source_count", "confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overnight_range_pct",
            "fade_pressure_score",
            "opening_liquidity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pre_market_gap_pct", "prior_day_trend_pct"):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexPreMarketGapFadeRow:
    research_key: str
    condition_id: str
    index_symbol: str
    gap_event_key: str
    gap_status: str
    gap_direction: str
    signal_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    confirmation_count: Decimal
    pre_market_gap_pct: Decimal
    gap_abs_pct: Decimal
    overnight_range_pct: Decimal
    prior_day_trend_pct: Decimal
    fade_pressure_score: Decimal
    opening_liquidity_ratio: Decimal
    contradiction_count: Decimal
    redacted_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexPreMarketGapFadeRow:
            raise TypeError(
                "MarketResearchEquityIndexPreMarketGapFadeRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexPreMarketGapFadeRow:
            raise ValueError(
                "row must be exactly MarketResearchEquityIndexPreMarketGapFadeRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "gap_event_key",
            "redacted_signal_reference",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_index_symbol("index_symbol", self.index_symbol)
        _require_gap_status("gap_status", self.gap_status)
        _require_gap_direction("gap_direction", self.gap_direction)
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_decimal(
                "signal_age_seconds",
                self.signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in ("source_count", "confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gap_abs_pct",
            "overnight_range_pct",
            "fade_pressure_score",
            "opening_liquidity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pre_market_gap_pct", "prior_day_trend_pct"):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
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
class MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount:
            raise TypeError(
                "MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount",
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
class MarketResearchEquityIndexPreMarketGapFadeReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    gap_event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    material_gap_count: Decimal
    fade_pressure_count: Decimal
    extended_overnight_range_count: Decimal
    counter_trend_gap_count: Decimal
    low_opening_liquidity_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    missing_confirmation_count: Decimal
    slow_acknowledgement_count: Decimal
    contradiction_count: Decimal
    average_gap_abs_pct: Decimal
    max_gap_abs_pct: Decimal
    average_fade_pressure_score: Decimal
    average_opening_liquidity_ratio: Decimal
    max_signal_age_seconds: Decimal
    rows: tuple[MarketResearchEquityIndexPreMarketGapFadeRow, ...]
    reason_code_counts: tuple[MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityIndexPreMarketGapFadeReport:
            raise TypeError(
                "MarketResearchEquityIndexPreMarketGapFadeReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityIndexPreMarketGapFadeReport:
            raise ValueError(
                "report must be exactly MarketResearchEquityIndexPreMarketGapFadeReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gap_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "gap_event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "material_gap_count",
            "fade_pressure_count",
            "extended_overnight_range_count",
            "counter_trend_gap_count",
            "low_opening_liquidity_count",
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
            "average_gap_abs_pct",
            "max_gap_abs_pct",
            "average_fade_pressure_score",
            "average_opening_liquidity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_nonnegative_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
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


def build_market_research_equity_index_pre_market_gap_fade_digest(
    rows: list[MarketResearchEquityIndexPreMarketGapFadeInputRow]
    | tuple[MarketResearchEquityIndexPreMarketGapFadeInputRow, ...],
    *,
    config: MarketResearchEquityIndexPreMarketGapFadeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchEquityIndexPreMarketGapFadeReport:
    cfg = config or MarketResearchEquityIndexPreMarketGapFadeDigestConfig()
    if type(cfg) is not MarketResearchEquityIndexPreMarketGapFadeDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEquityIndexPreMarketGapFadeDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows, generated_at_utc)
    digest_rows = tuple(
        _build_row(input_row, config=cfg, generated_at=generated_at_utc)
        for input_row in input_rows
    )
    ranked_rows = tuple(sorted(digest_rows, key=_row_sort_key))
    event_count = _count(len(ranked_rows))
    ready_event_count = _status_count(ranked_rows, STATUS_READY)
    watch_event_count = _status_count(ranked_rows, STATUS_WATCH)
    blocked_event_count = _status_count(ranked_rows, STATUS_BLOCKED)
    reason_codes = _report_reason_codes(ranked_rows)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_event_count=blocked_event_count,
        watch_event_count=watch_event_count,
    )

    return MarketResearchEquityIndexPreMarketGapFadeReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        gap_event_count=event_count,
        ready_event_count=ready_event_count,
        watch_event_count=watch_event_count,
        blocked_event_count=blocked_event_count,
        material_gap_count=_reason_count(ranked_rows, MATERIAL_GAP_REASON),
        fade_pressure_count=_reason_count(ranked_rows, FADE_PRESSURE_REASON),
        extended_overnight_range_count=_reason_count(
            ranked_rows,
            EXTENDED_OVERNIGHT_RANGE_REASON,
        ),
        counter_trend_gap_count=_reason_count(ranked_rows, COUNTER_TREND_GAP_REASON),
        low_opening_liquidity_count=_reason_count(
            ranked_rows,
            LOW_OPENING_LIQUIDITY_REASON,
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
        average_gap_abs_pct=_ratio(
            _sum_decimal(row.gap_abs_pct for row in ranked_rows),
            event_count,
        ),
        max_gap_abs_pct=max((row.gap_abs_pct for row in ranked_rows), default=ZERO),
        average_fade_pressure_score=_ratio(
            _sum_decimal(row.fade_pressure_score for row in ranked_rows),
            event_count,
        ),
        average_opening_liquidity_ratio=_ratio(
            _sum_decimal(row.opening_liquidity_ratio for row in ranked_rows),
            event_count,
        ),
        max_signal_age_seconds=max(
            (row.signal_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=_reason_code_counts(ranked_rows, reason_codes, event_count),
        reason_codes=reason_codes,
    )


def market_research_equity_index_pre_market_gap_fade_digest_payload(
    report: MarketResearchEquityIndexPreMarketGapFadeReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityIndexPreMarketGapFadeReport:
        raise ValueError(
            "report must be a MarketResearchEquityIndexPreMarketGapFadeReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report, _RedactionMap())
    if type(payload) is not dict:
        raise ValueError("payload must be a mapping")
    return payload


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchEquityIndexPreMarketGapFadeInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchEquityIndexPreMarketGapFadeInputRow:
            raise ValueError(
                "rows must contain MarketResearchEquityIndexPreMarketGapFadeInputRow",
            )
        _require_hard_flags("input row", row)
        key = (row.research_key, row.condition_id, row.gap_event_key)
        if key in seen:
            raise ValueError("duplicate research condition gap event keys are not allowed")
        seen.add(key)
        if row.signaled_at > generated_at:
            raise ValueError("signaled_at cannot be after generated_at")
        if row.acknowledged_at is not None:
            if row.acknowledged_at > generated_at:
                raise ValueError("acknowledged_at cannot be after generated_at")
            if row.acknowledged_at < row.signaled_at:
                raise ValueError("acknowledged_at cannot be before signaled_at")
    return tuple(
        sorted(
            normalized,
            key=lambda row: (row.research_key, row.condition_id, row.gap_event_key),
        ),
    )


def _build_row(
    input_row: MarketResearchEquityIndexPreMarketGapFadeInputRow,
    *,
    config: MarketResearchEquityIndexPreMarketGapFadeDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexPreMarketGapFadeRow:
    signal_age_seconds = _seconds_between(input_row.signaled_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.signaled_at, input_row.acknowledged_at)
    )
    gap_abs_pct = abs(input_row.pre_market_gap_pct).quantize(QUANT)
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        confirmation_count=input_row.confirmation_count,
        gap_abs_pct=gap_abs_pct,
        pre_market_gap_pct=input_row.pre_market_gap_pct,
        overnight_range_pct=input_row.overnight_range_pct,
        prior_day_trend_pct=input_row.prior_day_trend_pct,
        fade_pressure_score=input_row.fade_pressure_score,
        opening_liquidity_ratio=input_row.opening_liquidity_ratio,
        contradiction_count=input_row.contradiction_count,
        config=config,
    )
    return MarketResearchEquityIndexPreMarketGapFadeRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        index_symbol=input_row.index_symbol,
        gap_event_key=input_row.gap_event_key,
        gap_status=_row_status(reason_codes),
        gap_direction=_gap_direction(input_row.pre_market_gap_pct),
        signal_age_seconds=signal_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        confirmation_count=input_row.confirmation_count,
        pre_market_gap_pct=input_row.pre_market_gap_pct,
        gap_abs_pct=gap_abs_pct,
        overnight_range_pct=input_row.overnight_range_pct,
        prior_day_trend_pct=input_row.prior_day_trend_pct,
        fade_pressure_score=input_row.fade_pressure_score,
        opening_liquidity_ratio=input_row.opening_liquidity_ratio,
        contradiction_count=input_row.contradiction_count,
        redacted_signal_reference=_redacted_reference(input_row.signal_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_count: Decimal,
    confirmation_count: Decimal,
    gap_abs_pct: Decimal,
    pre_market_gap_pct: Decimal,
    overnight_range_pct: Decimal,
    prior_day_trend_pct: Decimal,
    fade_pressure_score: Decimal,
    opening_liquidity_ratio: Decimal,
    contradiction_count: Decimal,
    config: MarketResearchEquityIndexPreMarketGapFadeDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gap_abs_pct >= config.min_abs_pre_market_gap_pct:
        reasons.append(MATERIAL_GAP_REASON)
    if fade_pressure_score >= config.min_fade_pressure_score:
        reasons.append(FADE_PRESSURE_REASON)
    if overnight_range_pct >= config.min_overnight_range_pct:
        reasons.append(EXTENDED_OVERNIGHT_RANGE_REASON)
    if _is_counter_trend_gap(
        pre_market_gap_pct=pre_market_gap_pct,
        gap_abs_pct=gap_abs_pct,
        prior_day_trend_pct=prior_day_trend_pct,
        config=config,
    ):
        reasons.append(COUNTER_TREND_GAP_REASON)
    if opening_liquidity_ratio <= config.max_opening_liquidity_ratio:
        reasons.append(LOW_OPENING_LIQUIDITY_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if confirmation_count < config.min_confirmation_count:
        reasons.append(MISSING_CONFIRMATION_REASON)
    if (
        acknowledgement_lag_seconds is not None
        and acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds
    ):
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if contradiction_count > ZERO:
        reasons.append(CONTRADICTION_PRESENT_REASON)
    if not reasons:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _is_counter_trend_gap(
    *,
    pre_market_gap_pct: Decimal,
    gap_abs_pct: Decimal,
    prior_day_trend_pct: Decimal,
    config: MarketResearchEquityIndexPreMarketGapFadeDigestConfig,
) -> bool:
    if gap_abs_pct < config.min_abs_pre_market_gap_pct:
        return False
    if abs(prior_day_trend_pct).quantize(QUANT) < config.min_abs_prior_day_trend_pct:
        return False
    return pre_market_gap_pct * prior_day_trend_pct < ZERO


def _gap_direction(pre_market_gap_pct: Decimal) -> str:
    if pre_market_gap_pct > ZERO:
        return "gap_up"
    if pre_market_gap_pct < ZERO:
        return "gap_down"
    return "flat"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in reason_codes for reason in BLOCKING_REASON_CODES):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


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
    rows: tuple[MarketResearchEquityIndexPreMarketGapFadeRow, ...],
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
    rows: tuple[MarketResearchEquityIndexPreMarketGapFadeRow, ...],
    reason_codes: tuple[str, ...],
    event_count: Decimal,
) -> tuple[MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ONE,
            ),
        )
    counts = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    )
    if not counts and reason_codes == (READY_REASON,):
        counts = Counter(READY_REASON for row in rows)
    return tuple(
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
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
    rows: tuple[MarketResearchEquityIndexPreMarketGapFadeRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[MarketResearchEquityIndexPreMarketGapFadeRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchEquityIndexPreMarketGapFadeRow,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.gap_status],
        -row.gap_abs_pct,
        -row.fade_pressure_score,
        row.gap_event_key,
        row.index_symbol,
        row.research_key,
    )


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchEquityIndexPreMarketGapFadeRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    previous_key: tuple[int, Decimal, Decimal, str, str, str] | None = None
    for row in rows:
        if type(row) is not MarketResearchEquityIndexPreMarketGapFadeRow:
            raise ValueError("rows must contain MarketResearchEquityIndexPreMarketGapFadeRow")
        _require_hard_flags("row", row)
        row_id = (row.research_key, row.condition_id, row.gap_event_key)
        if row_id in seen:
            raise ValueError("rows must use unique research condition gap event keys")
        seen.add(row_id)
        key = _row_sort_key(row)
        if previous_key is not None and previous_key >= key:
            raise ValueError("rows must use deterministic ranking")
        previous_key = key
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, int] | None = None
    for row in rows:
        if type(row) is not MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, REPORT_REASON_CODE_SEQUENCE.index(row.reason_code))
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic ranking")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value, ROW_REASON_CODE_SEQUENCE)
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
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


def _validate_row(row: MarketResearchEquityIndexPreMarketGapFadeRow) -> None:
    if row.gap_abs_pct != abs(row.pre_market_gap_pct).quantize(QUANT):
        raise ValueError("gap_abs_pct must match pre_market_gap_pct magnitude")
    if row.gap_direction != _gap_direction(row.pre_market_gap_pct):
        raise ValueError("gap_direction must match pre_market_gap_pct")
    if row.gap_status != _row_status(row.reason_codes):
        if row.reason_codes == (READY_REASON,):
            raise ValueError("ready rows require ready status")
        raise ValueError("gap_status must match reason_codes")
    if row.gap_status == STATUS_BLOCKED and not any(
        reason in row.reason_codes for reason in BLOCKING_REASON_CODES
    ):
        raise ValueError("blocked rows require a blocking reason")


def _validate_report(report: MarketResearchEquityIndexPreMarketGapFadeReport) -> None:
    if report.gap_event_count != _count(len(report.rows)):
        raise ValueError("gap_event_count must match rows")
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
        report.gap_event_count,
    ):
        raise ValueError("reason_code_counts must match rows")
    _validate_report_reason_metric(report, "material_gap_count", MATERIAL_GAP_REASON)
    _validate_report_reason_metric(report, "fade_pressure_count", FADE_PRESSURE_REASON)
    _validate_report_reason_metric(
        report,
        "extended_overnight_range_count",
        EXTENDED_OVERNIGHT_RANGE_REASON,
    )
    _validate_report_reason_metric(
        report,
        "counter_trend_gap_count",
        COUNTER_TREND_GAP_REASON,
    )
    _validate_report_reason_metric(
        report,
        "low_opening_liquidity_count",
        LOW_OPENING_LIQUIDITY_REASON,
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
    if report.average_gap_abs_pct != _ratio(
        _sum_decimal(row.gap_abs_pct for row in report.rows),
        report.gap_event_count,
    ):
        raise ValueError("average_gap_abs_pct must match rows")
    if report.max_gap_abs_pct != max((row.gap_abs_pct for row in report.rows), default=ZERO):
        raise ValueError("max_gap_abs_pct must match rows")
    if report.average_fade_pressure_score != _ratio(
        _sum_decimal(row.fade_pressure_score for row in report.rows),
        report.gap_event_count,
    ):
        raise ValueError("average_fade_pressure_score must match rows")
    if report.average_opening_liquidity_ratio != _ratio(
        _sum_decimal(row.opening_liquidity_ratio for row in report.rows),
        report.gap_event_count,
    ):
        raise ValueError("average_opening_liquidity_ratio must match rows")
    if report.max_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_age_seconds must match rows")


def _validate_report_reason_metric(
    report: MarketResearchEquityIndexPreMarketGapFadeReport,
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


def _require_gap_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in GAP_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")
    return value


def _require_gap_direction(field_name: str, value: object) -> str:
    if type(value) is not str or value not in GAP_DIRECTIONS:
        raise ValueError(f"{field_name} must be gap_up, gap_down, or flat")
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


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


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


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


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


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
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
        if isinstance(value, MarketResearchEquityIndexPreMarketGapFadeRow):
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
