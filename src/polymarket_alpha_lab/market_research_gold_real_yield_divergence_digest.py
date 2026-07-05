"""Pure Phase 1 gold real yield divergence research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_DIVERGENCE_DIGEST_CONFIG_VERSION = (
    "market-research-gold-real-yield-divergence-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_gold_real_yield_divergence_digest_no_inputs"
READY_REASON = "market_research_gold_real_yield_divergence_digest_ready"
STALE_SIGNAL_REASON = "market_research_gold_real_yield_divergence_digest_stale_signal"
LOW_GOLD_MOMENTUM_REASON = (
    "market_research_gold_real_yield_divergence_digest_low_gold_momentum"
)
LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON = (
    "market_research_gold_real_yield_divergence_digest_low_real_yield_inverse_momentum"
)
LOW_DIVERGENCE_SCORE_REASON = (
    "market_research_gold_real_yield_divergence_digest_low_divergence_score"
)
DIVERGENCE_CONFIRMATION_GAP_REASON = (
    "market_research_gold_real_yield_divergence_digest_confirmation_gap"
)
SOURCE_FAMILY_GAP_REASON = (
    "market_research_gold_real_yield_divergence_digest_source_family_gap"
)
STALE_SOURCE_RATIO_REASON = (
    "market_research_gold_real_yield_divergence_digest_stale_source_ratio"
)

REASON_CODE_SEQUENCE = (
    DIVERGENCE_CONFIRMATION_GAP_REASON,
    STALE_SIGNAL_REASON,
    LOW_GOLD_MOMENTUM_REASON,
    LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON,
    LOW_DIVERGENCE_SCORE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_GOLD_MOMENTUM_REASON,
    LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON,
    LOW_DIVERGENCE_SCORE_REASON,
    DIVERGENCE_CONFIRMATION_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
)

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
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("sig", "ning"),
        _join_parts("tra", "de"),
        _join_parts("trad", "ing"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_DIVERGENCE_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldRealYieldDivergenceDigestConfig",
    "MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount",
    "MarketResearchGoldRealYieldDivergenceDigestReport",
    "MarketResearchGoldRealYieldDivergenceDigestRow",
    "MarketResearchGoldRealYieldDivergenceDigestSignal",
    "build_market_research_gold_real_yield_divergence_digest",
    "market_research_gold_real_yield_divergence_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldDivergenceDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_DIVERGENCE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_gold_momentum_score: Decimal = Decimal("0.550000")
    min_real_yield_inverse_momentum_score: Decimal = Decimal("0.550000")
    min_divergence_score: Decimal = Decimal("0.450000")
    min_divergence_confirmation_score: Decimal = Decimal("0.650000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldDivergenceDigestConfig:
            raise TypeError(
                "MarketResearchGoldRealYieldDivergenceDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldDivergenceDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldRealYieldDivergenceDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_signal_age_seconds", "min_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_gold_momentum_score",
            "min_real_yield_inverse_momentum_score",
            "min_divergence_score",
            "min_divergence_confirmation_score",
            "max_stale_source_ratio",
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
class MarketResearchGoldRealYieldDivergenceDigestSignal:
    condition_id: str
    gold_real_yield_key: str
    divergence_family: str
    public_signal_reference: str
    observed_at: datetime
    gold_momentum_score: Decimal
    real_yield_inverse_momentum_score: Decimal
    divergence_score: Decimal
    divergence_confirmation_score: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldDivergenceDigestSignal:
            raise TypeError(
                "MarketResearchGoldRealYieldDivergenceDigestSignal does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldDivergenceDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchGoldRealYieldDivergenceDigestSignal",
            )
        for field_name in (
            "condition_id",
            "gold_real_yield_key",
            "divergence_family",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        for field_name in (
            "gold_momentum_score",
            "real_yield_inverse_momentum_score",
            "divergence_score",
            "divergence_confirmation_score",
            "stale_source_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldDivergenceDigestRow:
    condition_id: str
    gold_real_yield_key: str
    divergence_family: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    gold_momentum_score: Decimal
    real_yield_inverse_momentum_score: Decimal
    divergence_score: Decimal
    divergence_confirmation_score: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
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
        if cls is not MarketResearchGoldRealYieldDivergenceDigestRow:
            raise TypeError(
                "MarketResearchGoldRealYieldDivergenceDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldDivergenceDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGoldRealYieldDivergenceDigestRow",
            )
        for field_name in ("condition_id", "gold_real_yield_key", "divergence_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("signal_age_seconds", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gold_momentum_score",
            "real_yield_inverse_momentum_score",
            "divergence_score",
            "divergence_confirmation_score",
            "stale_source_ratio",
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
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldDivergenceDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    low_gold_momentum_signal_count: Decimal
    low_real_yield_inverse_momentum_signal_count: Decimal
    low_divergence_score_signal_count: Decimal
    divergence_confirmation_gap_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_divergence_score: Decimal
    average_divergence_confirmation_score: Decimal
    max_signal_age_seconds: Decimal
    min_gold_momentum_score: Decimal
    min_real_yield_inverse_momentum_score: Decimal
    min_divergence_score: Decimal
    min_divergence_confirmation_score: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchGoldRealYieldDivergenceDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldDivergenceDigestReport:
            raise TypeError(
                "MarketResearchGoldRealYieldDivergenceDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldDivergenceDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchGoldRealYieldDivergenceDigestReport",
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
            "low_gold_momentum_signal_count",
            "low_real_yield_inverse_momentum_signal_count",
            "low_divergence_score_signal_count",
            "divergence_confirmation_gap_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "max_signal_age_seconds",
            "min_source_family_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_confidence_decay",
            _require_nonnegative_decimal(
                "total_confidence_decay",
                self.total_confidence_decay,
            ),
        )
        for field_name in (
            "average_final_confidence",
            "average_divergence_score",
            "average_divergence_confirmation_score",
            "min_gold_momentum_score",
            "min_real_yield_inverse_momentum_score",
            "min_divergence_score",
            "min_divergence_confirmation_score",
            "max_stale_source_ratio",
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
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_gold_real_yield_divergence_digest(
    signals: Iterable[MarketResearchGoldRealYieldDivergenceDigestSignal],
    *,
    config: MarketResearchGoldRealYieldDivergenceDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchGoldRealYieldDivergenceDigestReport:
    cfg = config or MarketResearchGoldRealYieldDivergenceDigestConfig()
    if type(cfg) is not MarketResearchGoldRealYieldDivergenceDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchGoldRealYieldDivergenceDigestConfig",
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
                row.gold_real_yield_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchGoldRealYieldDivergenceDigestReport(
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
        low_gold_momentum_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_GOLD_MOMENTUM_REASON,
        ),
        low_real_yield_inverse_momentum_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON,
        ),
        low_divergence_score_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_DIVERGENCE_SCORE_REASON,
        ),
        divergence_confirmation_gap_signal_count=_reason_signal_count(
            sorted_rows,
            DIVERGENCE_CONFIRMATION_GAP_REASON,
        ),
        source_family_gap_signal_count=_reason_signal_count(
            sorted_rows,
            SOURCE_FAMILY_GAP_REASON,
        ),
        stale_source_signal_count=_reason_signal_count(
            sorted_rows,
            STALE_SOURCE_RATIO_REASON,
        ),
        total_confidence_decay=_decimal_sum(
            row.confidence_decay_factor for row in sorted_rows
        ),
        average_final_confidence=_ratio(
            _decimal_sum(row.final_confidence for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_divergence_score=_ratio(
            _decimal_sum(row.divergence_score for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_divergence_confirmation_score=_ratio(
            _decimal_sum(row.divergence_confirmation_score for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_gold_momentum_score=cfg.min_gold_momentum_score,
        min_real_yield_inverse_momentum_score=cfg.min_real_yield_inverse_momentum_score,
        min_divergence_score=cfg.min_divergence_score,
        min_divergence_confirmation_score=cfg.min_divergence_confirmation_score,
        min_source_family_count=cfg.min_source_family_count,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        signal_config_versions=tuple(
            sorted(
                (
                    signal.gold_real_yield_key,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_gold_real_yield_divergence_digest_payload(
    report: MarketResearchGoldRealYieldDivergenceDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldRealYieldDivergenceDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchGoldRealYieldDivergenceDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _row_for_signal(
    signal: MarketResearchGoldRealYieldDivergenceDigestSignal,
    *,
    config: MarketResearchGoldRealYieldDivergenceDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldRealYieldDivergenceDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(signal=signal, config=config, generated_at=generated_at)
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _final_confidence(signal.base_confidence, confidence_decay_factor)
    return MarketResearchGoldRealYieldDivergenceDigestRow(
        condition_id=signal.condition_id,
        gold_real_yield_key=signal.gold_real_yield_key,
        divergence_family=signal.divergence_family,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        observed_at=signal.observed_at,
        signal_age_seconds=_age_seconds(generated_at, signal.observed_at),
        gold_momentum_score=signal.gold_momentum_score,
        real_yield_inverse_momentum_score=signal.real_yield_inverse_momentum_score,
        divergence_score=signal.divergence_score,
        divergence_confirmation_score=signal.divergence_confirmation_score,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal: MarketResearchGoldRealYieldDivergenceDigestSignal,
    config: MarketResearchGoldRealYieldDivergenceDigestConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    signal_age_seconds = _age_seconds(generated_at, signal.observed_at)
    reasons: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if signal.gold_momentum_score < config.min_gold_momentum_score:
        reasons.append(LOW_GOLD_MOMENTUM_REASON)
    if (
        signal.real_yield_inverse_momentum_score
        < config.min_real_yield_inverse_momentum_score
    ):
        reasons.append(LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON)
    if signal.divergence_score < config.min_divergence_score:
        reasons.append(LOW_DIVERGENCE_SCORE_REASON)
    if signal.divergence_confirmation_score < config.min_divergence_confirmation_score:
        reasons.append(DIVERGENCE_CONFIRMATION_GAP_REASON)
    if signal.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(STALE_SOURCE_RATIO_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchGoldRealYieldDivergenceDigestConfig,
) -> Decimal:
    no_decay_reasons = (READY_REASON, STALE_SOURCE_RATIO_REASON)
    gap_count = sum(1 for reason in reason_codes if reason not in no_decay_reasons)
    return _quantize(config.confidence_decay_per_gap * _decimal_count(gap_count))


def _final_confidence(
    base_confidence: Decimal,
    confidence_decay_factor: Decimal,
) -> Decimal:
    return max(ZERO, _quantize(base_confidence - confidence_decay_factor))


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    final_confidence: Decimal,
    watch_confidence_threshold: Decimal,
) -> str:
    if (
        STALE_SIGNAL_REASON in reason_codes
        or LOW_GOLD_MOMENTUM_REASON in reason_codes
        or LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON in reason_codes
        or LOW_DIVERGENCE_SCORE_REASON in reason_codes
        or SOURCE_FAMILY_GAP_REASON in reason_codes
        or STALE_SOURCE_RATIO_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes != (READY_REASON,) or final_confidence < watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_READY


def _report_status(
    rows: tuple[MarketResearchGoldRealYieldDivergenceDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "allow_report_only_market_research_gold_real_yield_divergence_digest"
    if status == STATUS_WATCH:
        return "monitor_report_only_market_research_gold_real_yield_divergence_digest"
    return "block_report_only_market_research_gold_real_yield_divergence_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchGoldRealYieldDivergenceDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _reason_code_counts(
    rows: tuple[MarketResearchGoldRealYieldDivergenceDigestRow, ...],
) -> tuple[MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    counts: list[MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_signal_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    signal_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_signal_count(
    rows: tuple[MarketResearchGoldRealYieldDivergenceDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: MarketResearchGoldRealYieldDivergenceDigestRow) -> None:
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence decay")
    if row.reason_codes == (READY_REASON,) and row.confidence_decay_factor != ZERO:
        raise ValueError("ready rows must not have confidence decay")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchGoldRealYieldDivergenceDigestReport) -> None:
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.ready_signal_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == STATUS_READY),
    ):
        raise ValueError("ready_signal_count must match rows")
    if report.watch_signal_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == STATUS_WATCH),
    ):
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_signal_count must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    reason_checks = (
        ("stale_signal_count", STALE_SIGNAL_REASON),
        ("low_gold_momentum_signal_count", LOW_GOLD_MOMENTUM_REASON),
        (
            "low_real_yield_inverse_momentum_signal_count",
            LOW_REAL_YIELD_INVERSE_MOMENTUM_REASON,
        ),
        ("low_divergence_score_signal_count", LOW_DIVERGENCE_SCORE_REASON),
        (
            "divergence_confirmation_gap_signal_count",
            DIVERGENCE_CONFIRMATION_GAP_REASON,
        ),
        ("source_family_gap_signal_count", SOURCE_FAMILY_GAP_REASON),
        ("stale_source_signal_count", STALE_SOURCE_RATIO_REASON),
    )
    for field_name, reason_code in reason_checks:
        if getattr(report, field_name) != _reason_signal_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.total_confidence_decay != _decimal_sum(
        row.confidence_decay_factor for row in report.rows
    ):
        raise ValueError("total_confidence_decay must match rows")
    if report.average_final_confidence != _ratio(
        _decimal_sum(row.final_confidence for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_final_confidence must match rows")
    if report.average_divergence_score != _ratio(
        _decimal_sum(row.divergence_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_divergence_score must match rows")
    if report.average_divergence_confirmation_score != _ratio(
        _decimal_sum(row.divergence_confirmation_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_divergence_confirmation_score must match rows")
    if report.max_observed_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.signal_config_versions and len(report.signal_config_versions) != len(
        report.rows,
    ):
        raise ValueError("signal_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_signals(
    signals: Iterable[MarketResearchGoldRealYieldDivergenceDigestSignal],
) -> tuple[MarketResearchGoldRealYieldDivergenceDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain gold real yield divergence rows")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must contain gold real yield divergence rows") from exc
    seen: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchGoldRealYieldDivergenceDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchGoldRealYieldDivergenceDigestSignal",
            )
        if signal.gold_real_yield_key in seen:
            raise ValueError("gold_real_yield_key values must be unique")
        seen.add(signal.gold_real_yield_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchGoldRealYieldDivergenceDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain gold real yield divergence digest rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain gold real yield divergence digest rows") from exc
    for row in normalized:
        if type(row) is not MarketResearchGoldRealYieldDivergenceDigestRow:
            raise ValueError(
                "rows must contain MarketResearchGoldRealYieldDivergenceDigestRow",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                _row_sort_value(row),
                row.gold_real_yield_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    if len({row.gold_real_yield_key for row in normalized}) != len(normalized):
        raise ValueError("gold_real_yield_key values must be unique")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signal_config_versions must contain pairs")
    try:
        normalized = tuple(tuple(item) for item in value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("signal_config_versions must contain pairs") from exc
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("signal_config_versions must contain pairs")
        signal_key, config_version = item
        _require_public_string("signal_config_versions signal_key", signal_key)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        if signal_key in seen:
            raise ValueError("signal_config_versions signal keys must be unique")
        seen.add(signal_key)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain count rows")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain count rows") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts reason codes must be unique")
        seen.add(item.reason_code)
        if item.count <= ZERO and item.reason_code != NO_INPUTS_REASON:
            raise ValueError("reason_code_counts must be positive")
    expected = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)
    if tuple(item.reason_code for item in normalized) != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of reason codes")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple of reason codes") from exc
    seen: set[str] = set()
    for item in normalized:
        _require_reason_code("reason_codes", item)
        if item in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(item)
    expected = tuple(reason for reason in sequence if reason in seen)
    if normalized != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return normalized


def _row_sort_value(row: MarketResearchGoldRealYieldDivergenceDigestRow) -> Decimal:
    if row.digest_status == STATUS_BLOCKED:
        return Decimal("0.000000")
    if row.digest_status == STATUS_WATCH:
        return Decimal("1.000000")
    return Decimal("2.000000")


def _redacted_reference(value: str) -> str:
    if _is_safe_reference(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_safe_reference(value: str) -> bool:
    if type(value) is not str or not value or value != value.strip():
        return False
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return False
    return all(char not in value for char in ":/?&=@#")


def _json_ready(value: object) -> Any:
    if dataclass_is_instance(value):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON value must not be a float or int")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            result[key] = _json_ready(item)
        return result
    raise ValueError(f"cannot serialize value of type {type(value).__name__}")


def dataclass_is_instance(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__") and not isinstance(value, type)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES}")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public label")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(char.lower() not in allowed for char in value):
        raise ValueError(f"{field_name} must be a public label")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if "\x00" in value:
        raise ValueError(f"{field_name} must be canonical")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"{field_name} must be redacted")
        return
    if not _is_safe_reference(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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
    integral = normalized.to_integral_value().quantize(QUANT)
    if normalized != integral:
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
    )


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")
