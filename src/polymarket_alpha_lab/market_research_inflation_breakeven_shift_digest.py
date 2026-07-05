"""Pure Phase 1 inflation breakeven shift research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_INFLATION_BREAKEVEN_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-inflation-breakeven-shift-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_inflation_breakeven_shift_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
LOW_BREAKEVEN_SHIFT_REASON = f"{REASON_PREFIX}low_breakeven_shift"
MARKET_PROBABILITY_GAP_REASON = f"{REASON_PREFIX}market_probability_gap"
SOURCE_FAMILY_GAP_REASON = f"{REASON_PREFIX}source_family_gap"
STALE_SOURCE_RATIO_REASON = f"{REASON_PREFIX}stale_source_ratio"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    STALE_SIGNAL_REASON,
    LOW_BREAKEVEN_SHIFT_REASON,
    MARKET_PROBABILITY_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_BREAKEVEN_SHIFT_REASON,
    MARKET_PROBABILITY_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_inflation_breakeven_shift_digest",
    STATUS_WATCH: "watch_report_only_market_research_inflation_breakeven_shift_digest",
    STATUS_BLOCKED: "block_report_only_market_research_inflation_breakeven_shift_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("or", "der"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "_", "key"),
        _join_parts("api", "-", "key"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("pri", "vate", "-", "key"),
        _join_parts("ht", "tp://"),
        _join_parts("ht", "tps://"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_INFLATION_BREAKEVEN_SHIFT_DIGEST_CONFIG_VERSION",
    "MarketResearchInflationBreakevenShiftDigestConfig",
    "MarketResearchInflationBreakevenShiftDigestReasonCodeCount",
    "MarketResearchInflationBreakevenShiftDigestReport",
    "MarketResearchInflationBreakevenShiftDigestRow",
    "MarketResearchInflationBreakevenShiftDigestSignal",
    "build_market_research_inflation_breakeven_shift_digest",
    "market_research_inflation_breakeven_shift_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchInflationBreakevenShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_INFLATION_BREAKEVEN_SHIFT_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_breakeven_shift_abs: Decimal = Decimal("0.050000")
    max_market_probability_gap_abs: Decimal = Decimal("0.100000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInflationBreakevenShiftDigestConfig:
            raise TypeError(
                "MarketResearchInflationBreakevenShiftDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInflationBreakevenShiftDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchInflationBreakevenShiftDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_signal_age_seconds",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_breakeven_shift_abs",
            "max_market_probability_gap_abs",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
            "confidence_decay_per_gap",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchInflationBreakevenShiftDigestSignal:
    condition_id: str
    breakeven_key: str
    public_signal_reference: str
    observed_at: datetime
    signal_age_seconds: Decimal
    breakeven_shift: Decimal
    market_probability_gap: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInflationBreakevenShiftDigestSignal:
            raise TypeError(
                "MarketResearchInflationBreakevenShiftDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInflationBreakevenShiftDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchInflationBreakevenShiftDigestSignal",
            )
        for field_name in (
            "condition_id",
            "breakeven_key",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_public_string(
            "public_signal_reference",
            self.public_signal_reference,
            allow_unsafe_fragments=True,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_count_decimal(
                "signal_age_seconds",
                self.signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "breakeven_shift",
            _require_bounded_decimal("breakeven_shift", self.breakeven_shift),
        )
        object.__setattr__(
            self,
            "market_probability_gap",
            _require_bounded_decimal(
                "market_probability_gap",
                self.market_probability_gap,
            ),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        for field_name in (
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchInflationBreakevenShiftDigestRow:
    condition_id: str
    breakeven_key: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    breakeven_shift: Decimal
    breakeven_shift_abs: Decimal
    market_probability_gap: Decimal
    market_probability_gap_abs: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInflationBreakevenShiftDigestRow:
            raise TypeError(
                "MarketResearchInflationBreakevenShiftDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInflationBreakevenShiftDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchInflationBreakevenShiftDigestRow",
            )
        for field_name in ("condition_id", "breakeven_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "breakeven_shift_abs",
            "market_probability_gap_abs",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("breakeven_shift", "market_probability_gap"):
            object.__setattr__(
                self,
                field_name,
                _require_bounded_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_public_signal_reference",
            self.redacted_public_signal_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchInflationBreakevenShiftDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInflationBreakevenShiftDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchInflationBreakevenShiftDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInflationBreakevenShiftDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchInflationBreakevenShiftDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchInflationBreakevenShiftDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    low_breakeven_shift_signal_count: Decimal
    market_probability_gap_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_breakeven_shift_abs: Decimal
    average_market_probability_gap_abs: Decimal
    average_confirmation_ratio: Decimal
    max_signal_age_seconds: Decimal
    min_breakeven_shift_abs: Decimal
    max_market_probability_gap_abs: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    min_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchInflationBreakevenShiftDigestReport:
            raise TypeError(
                "MarketResearchInflationBreakevenShiftDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchInflationBreakevenShiftDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchInflationBreakevenShiftDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "low_breakeven_shift_signal_count",
            "market_probability_gap_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
            "total_confidence_decay",
            "average_breakeven_shift_abs",
            "average_market_probability_gap_abs",
            "max_signal_age_seconds",
            "min_source_family_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_final_confidence",
            "average_confirmation_ratio",
            "min_breakeven_shift_abs",
            "max_market_probability_gap_abs",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_inflation_breakeven_shift_digest(
    signals: Iterable[MarketResearchInflationBreakevenShiftDigestSignal],
    *,
    config: MarketResearchInflationBreakevenShiftDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchInflationBreakevenShiftDigestReport:
    cfg = config or MarketResearchInflationBreakevenShiftDigestConfig()
    if type(cfg) is not MarketResearchInflationBreakevenShiftDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchInflationBreakevenShiftDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
        for signal in normalized_signals
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.breakeven_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchInflationBreakevenShiftDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        signal_count=_decimal_count(len(sorted_rows)),
        ready_signal_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_READY),
        ),
        watch_signal_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_WATCH),
        ),
        blocked_signal_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_BLOCKED),
        ),
        stale_signal_count=_reason_signal_count(sorted_rows, STALE_SIGNAL_REASON),
        low_breakeven_shift_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_BREAKEVEN_SHIFT_REASON,
        ),
        market_probability_gap_signal_count=_reason_signal_count(
            sorted_rows,
            MARKET_PROBABILITY_GAP_REASON,
        ),
        source_family_gap_signal_count=_reason_signal_count(
            sorted_rows,
            SOURCE_FAMILY_GAP_REASON,
        ),
        stale_source_signal_count=_reason_signal_count(
            sorted_rows,
            STALE_SOURCE_RATIO_REASON,
        ),
        confirmation_gap_signal_count=_reason_signal_count(
            sorted_rows,
            CONFIRMATION_GAP_REASON,
        ),
        total_confidence_decay=_sum_decimal(
            row.confidence_decay_factor for row in sorted_rows
        ),
        average_final_confidence=_average_decimal(
            row.final_confidence for row in sorted_rows
        ),
        average_breakeven_shift_abs=_average_decimal(
            row.breakeven_shift_abs for row in sorted_rows
        ),
        average_market_probability_gap_abs=_average_decimal(
            row.market_probability_gap_abs for row in sorted_rows
        ),
        average_confirmation_ratio=_average_decimal(
            row.confirmation_ratio for row in sorted_rows
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_breakeven_shift_abs=cfg.min_breakeven_shift_abs,
        max_market_probability_gap_abs=cfg.max_market_probability_gap_abs,
        min_source_family_count=cfg.min_source_family_count,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        min_confirmation_ratio=cfg.min_confirmation_ratio,
        max_observed_signal_age_seconds=_max_decimal(
            row.signal_age_seconds for row in sorted_rows
        ),
        rows=sorted_rows,
        signal_config_versions=_signal_config_versions(sorted_rows, normalized_signals),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
    )


def market_research_inflation_breakeven_shift_digest_payload(
    report: MarketResearchInflationBreakevenShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchInflationBreakevenShiftDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchInflationBreakevenShiftDigestReport",
        )
    _validate_report(report)
    serialized = _serialize_for_output(report)
    if not isinstance(serialized, dict):
        raise ValueError("serialized report must be a dict")
    return serialized


def _normalize_signals(
    signals: Iterable[MarketResearchInflationBreakevenShiftDigestSignal],
) -> tuple[MarketResearchInflationBreakevenShiftDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError(
            "signals must be an iterable of "
            "MarketResearchInflationBreakevenShiftDigestSignal values",
        )
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError(
            "signals must be an iterable of "
            "MarketResearchInflationBreakevenShiftDigestSignal values",
        ) from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchInflationBreakevenShiftDigestSignal:
            raise ValueError(
                "signals must contain only "
                "MarketResearchInflationBreakevenShiftDigestSignal values",
            )
        _require_hard_flags("signal", item)
        if item.breakeven_key in seen:
            raise ValueError("breakeven_key values must be unique")
        seen.add(item.breakeven_key)
    return items


def _row_for_signal(
    signal: MarketResearchInflationBreakevenShiftDigestSignal,
    *,
    config: MarketResearchInflationBreakevenShiftDigestConfig,
    generated_at: datetime,
) -> MarketResearchInflationBreakevenShiftDigestRow:
    signal_age_seconds = _age_seconds(generated_at=generated_at, observed_at=signal.observed_at)
    breakeven_shift_abs = _abs_decimal(signal.breakeven_shift)
    market_probability_gap_abs = _abs_decimal(signal.market_probability_gap)
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        breakeven_shift_abs=breakeven_shift_abs,
        market_probability_gap_abs=market_probability_gap_abs,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        config=config,
    )
    non_ready_reason_count = sum(1 for reason_code in reason_codes if reason_code != READY_REASON)
    confidence_decay_factor = _clamp_ratio(
        _multiply_decimal(
            _decimal_count(non_ready_reason_count),
            config.confidence_decay_per_gap,
        ),
    )
    final_confidence = _clamp_ratio(signal.base_confidence - confidence_decay_factor)
    digest_status = _row_status(reason_codes, final_confidence, config)
    return MarketResearchInflationBreakevenShiftDigestRow(
        condition_id=signal.condition_id,
        breakeven_key=signal.breakeven_key,
        digest_status=digest_status,
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        breakeven_shift=signal.breakeven_shift,
        breakeven_shift_abs=breakeven_shift_abs,
        market_probability_gap=signal.market_probability_gap,
        market_probability_gap_abs=market_probability_gap_abs,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redacted_reference(signal.public_signal_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    breakeven_shift_abs: Decimal,
    market_probability_gap_abs: Decimal,
    source_family_count: Decimal,
    stale_source_ratio: Decimal,
    confirmation_ratio: Decimal,
    config: MarketResearchInflationBreakevenShiftDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if breakeven_shift_abs < config.min_breakeven_shift_abs:
        reason_codes.append(LOW_BREAKEVEN_SHIFT_REASON)
    if market_probability_gap_abs > config.max_market_probability_gap_abs:
        reason_codes.append(MARKET_PROBABILITY_GAP_REASON)
    if source_family_count < config.min_source_family_count:
        reason_codes.append(SOURCE_FAMILY_GAP_REASON)
    if stale_source_ratio > config.max_stale_source_ratio:
        reason_codes.append(STALE_SOURCE_RATIO_REASON)
    if confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes), sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(
    reason_codes: tuple[str, ...],
    final_confidence: Decimal,
    config: MarketResearchInflationBreakevenShiftDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if final_confidence < config.watch_confidence_threshold:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    _require_status("digest_status", status)
    return NEXT_STEPS[status]


def _row_sort_value(row: MarketResearchInflationBreakevenShiftDigestRow) -> Decimal:
    if row.digest_status == STATUS_BLOCKED:
        return Decimal("0.000000")
    if row.digest_status == STATUS_WATCH:
        return Decimal("1.000000")
    return Decimal("2.000000")


def _reason_signal_count(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    _require_reason_code("reason_code", reason_code)
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
) -> tuple[MarketResearchInflationBreakevenShiftDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.setdefault(reason_code, 0) + 1
    signal_count = _decimal_count(len(rows))
    return tuple(
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            signal_ratio=_divide_decimal(_decimal_count(counts[reason_code]), signal_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _report_reason_codes(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
) -> tuple[str, ...]:
    return tuple(item.reason_code for item in _reason_code_counts(rows))


def _signal_config_versions(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
    signals: tuple[MarketResearchInflationBreakevenShiftDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    versions = {
        signal.breakeven_key: signal.signal_config_version
        for signal in signals
    }
    return tuple((row.breakeven_key, versions[row.breakeven_key]) for row in rows)


def _normalize_rows(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
) -> tuple[MarketResearchInflationBreakevenShiftDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchInflationBreakevenShiftDigestRow:
            raise ValueError(
                "rows must contain only "
                "MarketResearchInflationBreakevenShiftDigestRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchInflationBreakevenShiftDigestReasonCodeCount, ...],
) -> tuple[MarketResearchInflationBreakevenShiftDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not MarketResearchInflationBreakevenShiftDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain only "
                "MarketResearchInflationBreakevenShiftDigestReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
    normalized = tuple(
        sorted(
            counts,
            key=lambda item: _reason_code_position(item.reason_code, REASON_CODE_SEQUENCE),
        ),
    )
    if counts != normalized:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _normalize_signal_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("signal_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("signal_config_versions must contain key/version pairs")
        breakeven_key, config_version = item
        _require_public_string("signal_config_versions key", breakeven_key)
        _require_public_string("signal_config_versions version", config_version)
        normalized.append((breakeven_key, config_version))
    return tuple(normalized)


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    unique: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        unique.add(reason_code)
    normalized = tuple(
        reason_code
        for reason_code in sequence
        if reason_code in unique
    )
    if value != normalized:
        raise ValueError("reason_codes must be sorted deterministically")
    return normalized


def _validate_row(row: MarketResearchInflationBreakevenShiftDigestRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be non-empty")
    if row.breakeven_shift_abs != _abs_decimal(row.breakeven_shift):
        raise ValueError("breakeven_shift_abs must match breakeven_shift")
    if row.market_probability_gap_abs != _abs_decimal(row.market_probability_gap):
        raise ValueError("market_probability_gap_abs must match market_probability_gap")
    if row.final_confidence != _clamp_ratio(row.base_confidence - row.confidence_decay_factor):
        raise ValueError("final_confidence must match base_confidence and decay")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("ready rows must have ready reason_codes")
    if row.digest_status != STATUS_READY and row.reason_codes == (READY_REASON,):
        raise ValueError("non-ready rows must not have ready reason_codes")


def _validate_report(report: MarketResearchInflationBreakevenShiftDigestReport) -> None:
    if type(report) is not MarketResearchInflationBreakevenShiftDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchInflationBreakevenShiftDigestReport",
        )
    _require_hard_flags("report", report)
    _require_six_decimal_public_fields("report", report)
    rows = _normalize_rows(report.rows)
    for row in rows:
        _validate_row(row)
        _require_six_decimal_public_fields("row", row)
    signal_config_versions = _normalize_signal_config_versions(
        report.signal_config_versions,
    )
    reason_code_counts = _normalize_reason_code_counts(report.reason_code_counts)
    for item in reason_code_counts:
        _require_six_decimal_public_fields("reason code count", item)
    _normalize_reason_codes(report.reason_codes, sequence=REASON_CODE_SEQUENCE)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _decimal_count(len(rows)):
        raise ValueError("signal_count must match rows")
    if tuple(key for key, _ in signal_config_versions) != tuple(
        row.breakeven_key for row in rows
    ):
        raise ValueError("signal_config_versions must match rows")
    expected_counts = {
        "ready_signal_count": sum(1 for row in rows if row.digest_status == STATUS_READY),
        "watch_signal_count": sum(1 for row in rows if row.digest_status == STATUS_WATCH),
        "blocked_signal_count": sum(1 for row in rows if row.digest_status == STATUS_BLOCKED),
        "stale_signal_count": sum(1 for row in rows if STALE_SIGNAL_REASON in row.reason_codes),
        "low_breakeven_shift_signal_count": sum(
            1 for row in rows if LOW_BREAKEVEN_SHIFT_REASON in row.reason_codes
        ),
        "market_probability_gap_signal_count": sum(
            1 for row in rows if MARKET_PROBABILITY_GAP_REASON in row.reason_codes
        ),
        "source_family_gap_signal_count": sum(
            1 for row in rows if SOURCE_FAMILY_GAP_REASON in row.reason_codes
        ),
        "stale_source_signal_count": sum(
            1 for row in rows if STALE_SOURCE_RATIO_REASON in row.reason_codes
        ),
        "confirmation_gap_signal_count": sum(
            1 for row in rows if CONFIRMATION_GAP_REASON in row.reason_codes
        ),
    }
    for field_name, expected_count in expected_counts.items():
        if getattr(report, field_name) != _decimal_count(expected_count):
            raise ValueError(f"{field_name} must match rows")
    if report.total_confidence_decay != _sum_decimal(
        row.confidence_decay_factor for row in rows
    ):
        raise ValueError("total_confidence_decay must match rows")
    if report.average_final_confidence != _average_decimal(
        row.final_confidence for row in rows
    ):
        raise ValueError("average_final_confidence must match rows")
    if report.average_breakeven_shift_abs != _average_decimal(
        row.breakeven_shift_abs for row in rows
    ):
        raise ValueError("average_breakeven_shift_abs must match rows")
    if report.average_market_probability_gap_abs != _average_decimal(
        row.market_probability_gap_abs for row in rows
    ):
        raise ValueError("average_market_probability_gap_abs must match rows")
    if report.average_confirmation_ratio != _average_decimal(
        row.confirmation_ratio for row in rows
    ):
        raise ValueError("average_confirmation_ratio must match rows")
    if report.max_observed_signal_age_seconds != _max_decimal(
        row.signal_age_seconds for row in rows
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in expected_reason_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _sorted_rows(
    rows: tuple[MarketResearchInflationBreakevenShiftDigestRow, ...],
) -> tuple[MarketResearchInflationBreakevenShiftDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.breakeven_key,
                row.condition_id,
            ),
        ),
    )


def _age_seconds(*, generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("observed_at", observed_at)
    if observed_at_utc > generated_at_utc:
        raise ValueError("observed_at must not be in the future")
    delta = generated_at_utc - observed_at_utc
    with localcontext(DECIMAL_CONTEXT):
        value = (
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        )
    return _quantize(value)


def _redacted_reference(value: str) -> str:
    _require_public_string(
        "public_signal_reference",
        value,
        allow_unsafe_fragments=True,
    )
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        digest = sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest}"
    return value


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.startswith("sha256:"):
        suffix = value.removeprefix("sha256:")
        if len(suffix) != 12 or any(character not in "0123456789abcdef" for character in suffix):
            raise ValueError(f"{field_name} must be redacted with sha256")
        return
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(
    field_name: str,
    value: object,
    *,
    allow_unsafe_fragments: bool = False,
) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if not allow_unsafe_fragments and _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} must not contain restricted text")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _serialize_for_output(value: Any) -> Any:
    if _is_known_public_dataclass(value):
        _validate_public_dataclass_for_output(value)
        return {
            item_field.name: _serialize_for_output(getattr(value, item_field.name))
            for item_field in fields(value)
        }
    if isinstance(value, (list, dict, set)):
        raise ValueError("payload helper must not receive a raw container")
    if is_dataclass(value):
        raise ValueError("payload helper received an unknown public dataclass")
    if _has_public_flags(value):
        raise ValueError("payload helper received an unknown public object")
    if type(value) is Decimal:
        return format(_require_six_decimal_decimal("serialized numeric", value), "f")
    if type(value) is datetime:
        return _require_payload_datetime_utc("serialized datetime", value).isoformat()
    if isinstance(value, tuple):
        return tuple(_serialize_for_output(item) for item in value)
    if type(value) in (bool, str):
        return value
    raise ValueError("payload helper received an unsupported value")


def _is_known_public_dataclass(value: object) -> bool:
    return type(value) in (
        MarketResearchInflationBreakevenShiftDigestConfig,
        MarketResearchInflationBreakevenShiftDigestSignal,
        MarketResearchInflationBreakevenShiftDigestRow,
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount,
        MarketResearchInflationBreakevenShiftDigestReport,
    )


def _has_public_flags(value: object) -> bool:
    return all(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _validate_public_dataclass_for_output(value: object) -> None:
    if type(value) is MarketResearchInflationBreakevenShiftDigestReport:
        _require_payload_datetime_utc("generated_at", value.generated_at)
        _validate_report(value)
        for row in value.rows:
            _validate_public_dataclass_for_output(row)
        for item in value.reason_code_counts:
            _validate_public_dataclass_for_output(item)
        return
    if type(value) is MarketResearchInflationBreakevenShiftDigestRow:
        _require_payload_datetime_utc("observed_at", value.observed_at)
        MarketResearchInflationBreakevenShiftDigestRow(**_dataclass_values(value))
        return
    if type(value) is MarketResearchInflationBreakevenShiftDigestReasonCodeCount:
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            **_dataclass_values(value),
        )
        return
    if type(value) is MarketResearchInflationBreakevenShiftDigestConfig:
        MarketResearchInflationBreakevenShiftDigestConfig(**_dataclass_values(value))
        return
    if type(value) is MarketResearchInflationBreakevenShiftDigestSignal:
        _require_payload_datetime_utc("observed_at", value.observed_at)
        MarketResearchInflationBreakevenShiftDigestSignal(**_dataclass_values(value))
        return
    raise ValueError("payload helper received an unknown public dataclass")


def _dataclass_values(value: object) -> dict[str, object]:
    return {item_field.name: getattr(value, item_field.name) for item_field in fields(value)}


def _require_payload_datetime_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a valid digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a valid reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_six_decimal_public_fields(field_name: str, value: object) -> None:
    for item_field in fields(value):
        if item_field.type is Decimal or item_field.type == "Decimal":
            _require_six_decimal_decimal(
                f"{field_name} {item_field.name}",
                getattr(value, item_field.name),
            )


def _require_six_decimal_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = value.quantize(QUANT)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if value.as_tuple().exponent != QUANT.as_tuple().exponent or value != quantized:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_bounded_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(max(items))


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("ratio", value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _reason_code_position(reason_code: str, sequence: tuple[str, ...]) -> int:
    try:
        return sequence.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be known") from exc
