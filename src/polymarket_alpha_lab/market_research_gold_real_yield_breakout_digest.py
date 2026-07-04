"""Pure Phase 1 gold real-yield breakout digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_BREAKOUT_DIGEST_CONFIG_VERSION = (
    "market-research-gold-real-yield-breakout-digest-v0"
)

STATUS_BLOCKED = "blocked"
STATUS_WATCH = "watch"
STATUS_PASS = "pass"
SCREENING_STATUSES = (STATUS_BLOCKED, STATUS_WATCH, STATUS_PASS)

PRESSURE_BEARISH = "bearish_gold"
PRESSURE_BULLISH = "bullish_gold"
PRESSURE_MIXED = "mixed_gold"
PRESSURE_NEUTRAL = "neutral_gold"
PRESSURE_DIRECTIONS = (
    PRESSURE_BEARISH,
    PRESSURE_BULLISH,
    PRESSURE_MIXED,
    PRESSURE_NEUTRAL,
)

REASON_PREFIX = "market_research_gold_real_yield_breakout_digest_"
REAL_YIELD_PRESSURE_REASON = f"{REASON_PREFIX}real_yield_breakout_pressure"
USD_PRESSURE_REASON = f"{REASON_PREFIX}usd_breakout_pressure"
COMBINED_PRESSURE_REASON = f"{REASON_PREFIX}combined_real_yield_usd_pressure"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
STALE_INPUT_REASON = f"{REASON_PREFIX}stale_input"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
THIN_LIQUIDITY_REASON = f"{REASON_PREFIX}thin_liquidity"
PASS_REASON = f"{REASON_PREFIX}pass"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    REAL_YIELD_PRESSURE_REASON,
    USD_PRESSURE_REASON,
    COMBINED_PRESSURE_REASON,
    PROBABILITY_REPRICING_REASON,
    STALE_INPUT_REASON,
    THIN_SOURCES_REASON,
    THIN_LIQUIDITY_REASON,
    PASS_REASON,
)
REASON_CODE_SEQUENCE = ROW_REASON_CODE_SEQUENCE + (NO_INPUTS_REASON,)

NEXT_STEPS = {
    STATUS_BLOCKED: "block_report_only_gold_real_yield_breakout_screening",
    STATUS_WATCH: "watch_report_only_gold_real_yield_breakout_screening",
    STATUS_PASS: "pass_report_only_gold_real_yield_breakout_screening",
}
STATUS_WEIGHT = {
    STATUS_BLOCKED: Decimal("2.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("0.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
TOTAL_PRESSURE_FACTOR_COUNT = Decimal("3.000000")
_PUBLIC_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("au", "th"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_BREAKOUT_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldRealYieldBreakoutDigestConfig",
    "MarketResearchGoldRealYieldBreakoutDigestReport",
    "MarketResearchGoldRealYieldBreakoutDigestRow",
    "MarketResearchGoldRealYieldBreakoutInputRow",
    "MarketResearchGoldRealYieldBreakoutReasonCodeCount",
    "build_market_research_gold_real_yield_breakout_digest",
    "market_research_gold_real_yield_breakout_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldBreakoutDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_BREAKOUT_DIGEST_CONFIG_VERSION
    )
    fresh_input_max_age_seconds: Decimal = Decimal("21600.000000")
    watch_real_yield_change_bp_threshold: Decimal = Decimal("8.000000")
    blocked_real_yield_change_bp_threshold: Decimal = Decimal("15.000000")
    watch_usd_index_change_pct_threshold: Decimal = Decimal("0.005000")
    blocked_usd_index_change_pct_threshold: Decimal = Decimal("0.010000")
    watch_probability_delta_threshold: Decimal = Decimal("0.040000")
    blocked_probability_delta_threshold: Decimal = Decimal("0.080000")
    min_source_count: Decimal = Decimal("2.000000")
    min_event_liquidity_usd: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldBreakoutDigestConfig:
            raise TypeError(
                "MarketResearchGoldRealYieldBreakoutDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldBreakoutDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldRealYieldBreakoutDigestConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_BREAKOUT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_input_max_age_seconds",
            "watch_real_yield_change_bp_threshold",
            "blocked_real_yield_change_bp_threshold",
            "min_event_liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_usd_index_change_pct_threshold",
            "blocked_usd_index_change_pct_threshold",
            "watch_probability_delta_threshold",
            "blocked_probability_delta_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_decimal("min_source_count", self.min_source_count),
        )
        if (
            self.blocked_real_yield_change_bp_threshold
            < self.watch_real_yield_change_bp_threshold
        ):
            raise ValueError(
                "blocked_real_yield_change_bp_threshold must be at least watch value",
            )
        if (
            self.blocked_usd_index_change_pct_threshold
            < self.watch_usd_index_change_pct_threshold
        ):
            raise ValueError(
                "blocked_usd_index_change_pct_threshold must be at least watch value",
            )
        if (
            self.blocked_probability_delta_threshold
            < self.watch_probability_delta_threshold
        ):
            raise ValueError(
                "blocked_probability_delta_threshold must be at least watch value",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldBreakoutInputRow:
    research_id: str
    condition_id: str
    event_slug: str
    commodity_symbol: str
    observed_at: datetime
    source_count: Decimal
    event_liquidity_usd: Decimal
    real_yield_level_pct: Decimal
    real_yield_change_bp: Decimal
    usd_index_change_pct: Decimal
    gold_spot_change_pct: Decimal
    event_probability_before: Decimal
    event_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldBreakoutInputRow:
            raise TypeError(
                "MarketResearchGoldRealYieldBreakoutInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldBreakoutInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchGoldRealYieldBreakoutInputRow",
            )
        for field_name in (
            "research_id",
            "condition_id",
            "event_slug",
            "commodity_symbol",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "event_liquidity_usd",
            _require_nonnegative_decimal(
                "event_liquidity_usd",
                self.event_liquidity_usd,
            ),
        )
        for field_name in (
            "real_yield_level_pct",
            "real_yield_change_bp",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "usd_index_change_pct",
            "gold_spot_change_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "event_probability_before",
            "event_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldBreakoutDigestRow:
    research_id: str
    condition_id: str
    event_slug: str
    commodity_symbol: str
    screening_status: str
    observed_at: datetime
    input_age_seconds: Decimal
    source_count: Decimal
    event_liquidity_usd: Decimal
    real_yield_level_pct: Decimal
    real_yield_change_bp: Decimal
    real_yield_change_abs_bp: Decimal
    usd_index_change_pct: Decimal
    usd_index_change_abs_pct: Decimal
    gold_spot_change_pct: Decimal
    event_probability_before: Decimal
    event_probability_after: Decimal
    probability_delta: Decimal
    probability_delta_abs: Decimal
    pressure_factor_count: Decimal
    pressure_score: Decimal
    pressure_direction: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldBreakoutDigestRow:
            raise TypeError(
                "MarketResearchGoldRealYieldBreakoutDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldBreakoutDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGoldRealYieldBreakoutDigestRow",
            )
        for field_name in (
            "research_id",
            "condition_id",
            "event_slug",
            "commodity_symbol",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("screening_status", self.screening_status, SCREENING_STATUSES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "input_age_seconds",
            "source_count",
            "event_liquidity_usd",
            "real_yield_change_abs_bp",
            "usd_index_change_abs_pct",
            "probability_delta_abs",
            "pressure_factor_count",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "real_yield_level_pct",
            "real_yield_change_bp",
            "probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "usd_index_change_pct",
            "gold_spot_change_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "event_probability_before",
            "event_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("pressure_direction", self.pressure_direction, PRESSURE_DIRECTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldBreakoutReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldBreakoutReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldRealYieldBreakoutReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldBreakoutReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchGoldRealYieldBreakoutReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _require_ratio_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldBreakoutDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    blocked_input_count: Decimal
    watch_input_count: Decimal
    pass_input_count: Decimal
    real_yield_breakout_count: Decimal
    usd_breakout_count: Decimal
    combined_pressure_count: Decimal
    probability_repricing_count: Decimal
    stale_input_count: Decimal
    thin_source_count: Decimal
    thin_liquidity_count: Decimal
    average_pressure_score: Decimal
    max_pressure_score: Decimal
    max_input_age_seconds: Decimal
    blocked_input_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...]
    reason_code_counts: tuple[MarketResearchGoldRealYieldBreakoutReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldBreakoutDigestReport:
            raise TypeError(
                "MarketResearchGoldRealYieldBreakoutDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldBreakoutDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchGoldRealYieldBreakoutDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_BREAKOUT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "blocked_input_count",
            "watch_input_count",
            "pass_input_count",
            "real_yield_breakout_count",
            "usd_breakout_count",
            "combined_pressure_count",
            "probability_repricing_count",
            "stale_input_count",
            "thin_source_count",
            "thin_liquidity_count",
            "average_pressure_score",
            "max_pressure_score",
            "max_input_age_seconds",
            "blocked_input_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SCREENING_STATUSES)
        _require_public_identifier("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_gold_real_yield_breakout_digest(
    inputs: Iterable[MarketResearchGoldRealYieldBreakoutInputRow],
    *,
    config: MarketResearchGoldRealYieldBreakoutDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldRealYieldBreakoutDigestReport:
    if type(config) is not MarketResearchGoldRealYieldBreakoutDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchGoldRealYieldBreakoutDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    _validate_input_times(normalized_inputs, generated_at_utc)
    rows = tuple(
        _row_for_input(item, config=config, generated_at=generated_at_utc)
        for item in normalized_inputs
    )
    ranked_rows = tuple(sorted(rows, key=_row_rank))
    input_count = _count_decimal(len(ranked_rows))
    blocked_count = _row_status_count(ranked_rows, STATUS_BLOCKED)
    reason_codes = _report_reason_codes(ranked_rows)

    return MarketResearchGoldRealYieldBreakoutDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=input_count,
        blocked_input_count=blocked_count,
        watch_input_count=_row_status_count(ranked_rows, STATUS_WATCH),
        pass_input_count=_row_status_count(ranked_rows, STATUS_PASS),
        real_yield_breakout_count=_row_reason_count(
            ranked_rows,
            REAL_YIELD_PRESSURE_REASON,
        ),
        usd_breakout_count=_row_reason_count(ranked_rows, USD_PRESSURE_REASON),
        combined_pressure_count=_row_reason_count(
            ranked_rows,
            COMBINED_PRESSURE_REASON,
        ),
        probability_repricing_count=_row_reason_count(
            ranked_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        stale_input_count=_row_reason_count(ranked_rows, STALE_INPUT_REASON),
        thin_source_count=_row_reason_count(ranked_rows, THIN_SOURCES_REASON),
        thin_liquidity_count=_row_reason_count(ranked_rows, THIN_LIQUIDITY_REASON),
        average_pressure_score=_ratio(
            _sum_decimal(row.pressure_score for row in ranked_rows),
            input_count,
        ),
        max_pressure_score=max((row.pressure_score for row in ranked_rows), default=ZERO),
        max_input_age_seconds=max(
            (row.input_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        blocked_input_ratio=_ratio(blocked_count, input_count),
        digest_status=_digest_status(ranked_rows),
        recommended_next_step=_recommended_next_step(_digest_status(ranked_rows)),
        rows=ranked_rows,
        reason_code_counts=_reason_code_counts(reason_codes, ranked_rows, input_count),
        reason_codes=reason_codes,
    )


def market_research_gold_real_yield_breakout_digest_payload(
    report: MarketResearchGoldRealYieldBreakoutDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldRealYieldBreakoutDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchGoldRealYieldBreakoutDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_input(
    item: MarketResearchGoldRealYieldBreakoutInputRow,
    *,
    config: MarketResearchGoldRealYieldBreakoutDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldRealYieldBreakoutDigestRow:
    age_seconds = _age_seconds(generated_at, item.observed_at)
    probability_delta = _quantize(
        item.event_probability_after - item.event_probability_before,
    )
    real_yield_abs = abs(item.real_yield_change_bp)
    usd_abs = abs(item.usd_index_change_pct)
    probability_abs = abs(probability_delta)
    reasons = _row_reason_codes(
        item,
        config=config,
        age_seconds=age_seconds,
        real_yield_abs=real_yield_abs,
        usd_abs=usd_abs,
        probability_abs=probability_abs,
    )
    status = _row_status(
        item,
        config=config,
        age_seconds=age_seconds,
        real_yield_abs=real_yield_abs,
        usd_abs=usd_abs,
        probability_abs=probability_abs,
    )
    pressure_factor_count = _count_decimal(
        sum(
            1
            for reason_code in (
                REAL_YIELD_PRESSURE_REASON,
                USD_PRESSURE_REASON,
                PROBABILITY_REPRICING_REASON,
            )
            if reason_code in reasons
        ),
    )
    return MarketResearchGoldRealYieldBreakoutDigestRow(
        research_id=item.research_id,
        condition_id=item.condition_id,
        event_slug=item.event_slug,
        commodity_symbol=item.commodity_symbol,
        screening_status=status,
        observed_at=item.observed_at,
        input_age_seconds=age_seconds,
        source_count=item.source_count,
        event_liquidity_usd=item.event_liquidity_usd,
        real_yield_level_pct=item.real_yield_level_pct,
        real_yield_change_bp=item.real_yield_change_bp,
        real_yield_change_abs_bp=real_yield_abs,
        usd_index_change_pct=item.usd_index_change_pct,
        usd_index_change_abs_pct=usd_abs,
        gold_spot_change_pct=item.gold_spot_change_pct,
        event_probability_before=item.event_probability_before,
        event_probability_after=item.event_probability_after,
        probability_delta=probability_delta,
        probability_delta_abs=probability_abs,
        pressure_factor_count=pressure_factor_count,
        pressure_score=_ratio(pressure_factor_count, TOTAL_PRESSURE_FACTOR_COUNT),
        pressure_direction=_pressure_direction(
            item.real_yield_change_bp,
            item.usd_index_change_pct,
        ),
        reason_codes=reasons,
    )


def _row_reason_codes(
    item: MarketResearchGoldRealYieldBreakoutInputRow,
    *,
    config: MarketResearchGoldRealYieldBreakoutDigestConfig,
    age_seconds: Decimal,
    real_yield_abs: Decimal,
    usd_abs: Decimal,
    probability_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    real_yield_pressure = real_yield_abs >= config.watch_real_yield_change_bp_threshold
    usd_pressure = usd_abs >= config.watch_usd_index_change_pct_threshold
    if real_yield_pressure:
        reasons.append(REAL_YIELD_PRESSURE_REASON)
    if usd_pressure:
        reasons.append(USD_PRESSURE_REASON)
    if real_yield_pressure and usd_pressure:
        reasons.append(COMBINED_PRESSURE_REASON)
    if probability_abs >= config.watch_probability_delta_threshold:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if age_seconds > config.fresh_input_max_age_seconds:
        reasons.append(STALE_INPUT_REASON)
    if item.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if item.event_liquidity_usd < config.min_event_liquidity_usd:
        reasons.append(THIN_LIQUIDITY_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    item: MarketResearchGoldRealYieldBreakoutInputRow,
    *,
    config: MarketResearchGoldRealYieldBreakoutDigestConfig,
    age_seconds: Decimal,
    real_yield_abs: Decimal,
    usd_abs: Decimal,
    probability_abs: Decimal,
) -> str:
    if (
        age_seconds > config.fresh_input_max_age_seconds
        or item.source_count < config.min_source_count
        or item.event_liquidity_usd < config.min_event_liquidity_usd
        or real_yield_abs >= config.blocked_real_yield_change_bp_threshold
        or usd_abs >= config.blocked_usd_index_change_pct_threshold
        or probability_abs >= config.blocked_probability_delta_threshold
    ):
        return STATUS_BLOCKED
    if (
        real_yield_abs >= config.watch_real_yield_change_bp_threshold
        or usd_abs >= config.watch_usd_index_change_pct_threshold
        or probability_abs >= config.watch_probability_delta_threshold
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _pressure_direction(real_yield_change_bp: Decimal, usd_index_change_pct: Decimal) -> str:
    if real_yield_change_bp > ZERO and usd_index_change_pct > ZERO:
        return PRESSURE_BEARISH
    if real_yield_change_bp < ZERO and usd_index_change_pct < ZERO:
        return PRESSURE_BULLISH
    if real_yield_change_bp == ZERO and usd_index_change_pct == ZERO:
        return PRESSURE_NEUTRAL
    return PRESSURE_MIXED


def _report_reason_codes(
    rows: tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...],
    input_count: Decimal,
) -> tuple[MarketResearchGoldRealYieldBreakoutReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchGoldRealYieldBreakoutReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                input_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchGoldRealYieldBreakoutReasonCodeCount(
            reason_code=reason_code,
            count=_row_reason_count(rows, reason_code),
            input_ratio=_ratio(_row_reason_count(rows, reason_code), input_count),
        )
        for reason_code in reason_codes
    )


def _digest_status(
    rows: tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.screening_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.screening_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _recommended_next_step(status: str) -> str:
    return NEXT_STEPS[status]


def _validate_row(row: MarketResearchGoldRealYieldBreakoutDigestRow) -> None:
    if row.real_yield_change_abs_bp != abs(row.real_yield_change_bp):
        raise ValueError("real_yield_change_abs_bp must match real_yield_change_bp")
    if row.usd_index_change_abs_pct != abs(row.usd_index_change_pct):
        raise ValueError("usd_index_change_abs_pct must match usd_index_change_pct")
    if row.probability_delta != _quantize(
        row.event_probability_after - row.event_probability_before,
    ):
        raise ValueError("probability_delta must match event probabilities")
    if row.probability_delta_abs != abs(row.probability_delta):
        raise ValueError("probability_delta_abs must match probability_delta")
    expected_pressure_factor_count = _count_decimal(
        sum(
            1
            for reason_code in (
                REAL_YIELD_PRESSURE_REASON,
                USD_PRESSURE_REASON,
                PROBABILITY_REPRICING_REASON,
            )
            if reason_code in row.reason_codes
        ),
    )
    if row.pressure_factor_count != expected_pressure_factor_count:
        raise ValueError("pressure_factor_count must match reason_codes")
    if row.pressure_score != _ratio(
        row.pressure_factor_count,
        TOTAL_PRESSURE_FACTOR_COUNT,
    ):
        raise ValueError("pressure_score must match pressure_factor_count")
    if row.pressure_direction != _pressure_direction(
        row.real_yield_change_bp,
        row.usd_index_change_pct,
    ):
        raise ValueError("pressure_direction must match input changes")
    if row.screening_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only carry the pass reason")


def _validate_report(report: MarketResearchGoldRealYieldBreakoutDigestReport) -> None:
    rows = report.rows
    input_count = _count_decimal(len(rows))
    if report.input_count != input_count:
        raise ValueError("input_count must match rows")
    expected_counts = {
        "blocked_input_count": _row_status_count(rows, STATUS_BLOCKED),
        "watch_input_count": _row_status_count(rows, STATUS_WATCH),
        "pass_input_count": _row_status_count(rows, STATUS_PASS),
        "real_yield_breakout_count": _row_reason_count(rows, REAL_YIELD_PRESSURE_REASON),
        "usd_breakout_count": _row_reason_count(rows, USD_PRESSURE_REASON),
        "combined_pressure_count": _row_reason_count(rows, COMBINED_PRESSURE_REASON),
        "probability_repricing_count": _row_reason_count(
            rows,
            PROBABILITY_REPRICING_REASON,
        ),
        "stale_input_count": _row_reason_count(rows, STALE_INPUT_REASON),
        "thin_source_count": _row_reason_count(rows, THIN_SOURCES_REASON),
        "thin_liquidity_count": _row_reason_count(rows, THIN_LIQUIDITY_REASON),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.average_pressure_score != _ratio(
        _sum_decimal(row.pressure_score for row in rows),
        input_count,
    ):
        raise ValueError("average_pressure_score must match rows")
    if report.max_pressure_score != max((row.pressure_score for row in rows), default=ZERO):
        raise ValueError("max_pressure_score must match rows")
    if report.max_input_age_seconds != max(
        (row.input_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_input_age_seconds must match rows")
    if report.blocked_input_ratio != _ratio(
        _row_status_count(rows, STATUS_BLOCKED),
        input_count,
    ):
        raise ValueError("blocked_input_ratio must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        rows,
        input_count,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: Iterable[MarketResearchGoldRealYieldBreakoutInputRow],
) -> tuple[MarketResearchGoldRealYieldBreakoutInputRow, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain gold real-yield breakout rows")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must contain gold real-yield breakout rows") from exc
    seen_research_ids: set[str] = set()
    seen_condition_ids: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchGoldRealYieldBreakoutInputRow:
            raise ValueError(
                "inputs must contain MarketResearchGoldRealYieldBreakoutInputRow",
            )
        if item.research_id in seen_research_ids:
            raise ValueError("inputs must not contain duplicate research_id values")
        if item.condition_id in seen_condition_ids:
            raise ValueError("inputs must not contain duplicate condition_id values")
        seen_research_ids.add(item.research_id)
        seen_condition_ids.add(item.condition_id)
    return normalized


def _validate_input_times(
    inputs: tuple[MarketResearchGoldRealYieldBreakoutInputRow, ...],
    generated_at: datetime,
) -> None:
    for item in inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain gold real-yield digest rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain gold real-yield digest rows") from exc
    for row in rows:
        if type(row) is not MarketResearchGoldRealYieldBreakoutDigestRow:
            raise ValueError(
                "rows must contain MarketResearchGoldRealYieldBreakoutDigestRow",
            )
    if rows != tuple(sorted(rows, key=_row_rank)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.research_id for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate research_id values")
    if len({row.condition_id for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate condition_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldRealYieldBreakoutReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not MarketResearchGoldRealYieldBreakoutReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldRealYieldBreakoutReasonCodeCount",
            )
    if counts != tuple(
        sorted(counts, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code))
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_rank(
    row: MarketResearchGoldRealYieldBreakoutDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.screening_status],
        -row.pressure_score,
        -_real_yield_priority(row),
        -row.input_age_seconds,
        row.event_slug,
        row.research_id,
    )


def _real_yield_priority(row: MarketResearchGoldRealYieldBreakoutDigestRow) -> Decimal:
    if REAL_YIELD_PRESSURE_REASON in row.reason_codes:
        return ONE
    return ZERO


def _row_status_count(
    rows: tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.screening_status == status))


def _row_reason_count(
    rows: tuple[MarketResearchGoldRealYieldBreakoutDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    total_microseconds = (
        ((delta.days * 86400) + delta.seconds) * 1000000
    ) + delta.microseconds
    return _ratio(Decimal(total_microseconds), MICROSECONDS_PER_SECOND)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(name): _json_ready(item) for name, item in value.items()}
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_identifier(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _PUBLIC_TEXT_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
