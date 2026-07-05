"""Pure Phase 1 gold rate sensitivity research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_RATE_SENSITIVITY_DIGEST_CONFIG_VERSION = (
    "market-research-gold-rate-sensitivity-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_gold_rate_sensitivity_digest_no_inputs"
READY_REASON = "market_research_gold_rate_sensitivity_digest_ready"
STALE_SIGNAL_REASON = "market_research_gold_rate_sensitivity_digest_stale_signal"
LOW_REAL_RATE_BETA_REASON = (
    "market_research_gold_rate_sensitivity_digest_low_real_rate_beta"
)
LOW_NOMINAL_RATE_BETA_REASON = (
    "market_research_gold_rate_sensitivity_digest_low_nominal_rate_beta"
)
RATE_VOLATILITY_GAP_REASON = (
    "market_research_gold_rate_sensitivity_digest_rate_volatility_gap"
)
INVERSE_RATE_CONFIRMATION_GAP_REASON = (
    "market_research_gold_rate_sensitivity_digest_inverse_rate_confirmation_gap"
)
SOURCE_FAMILY_GAP_REASON = (
    "market_research_gold_rate_sensitivity_digest_source_family_gap"
)
STALE_SOURCE_RATIO_REASON = (
    "market_research_gold_rate_sensitivity_digest_stale_source_ratio"
)

REASON_CODE_SEQUENCE = (
    INVERSE_RATE_CONFIRMATION_GAP_REASON,
    STALE_SIGNAL_REASON,
    LOW_REAL_RATE_BETA_REASON,
    LOW_NOMINAL_RATE_BETA_REASON,
    RATE_VOLATILITY_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_REAL_RATE_BETA_REASON,
    LOW_NOMINAL_RATE_BETA_REASON,
    RATE_VOLATILITY_GAP_REASON,
    INVERSE_RATE_CONFIRMATION_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
)
BLOCKING_ROW_REASON_CODES = (
    STALE_SIGNAL_REASON,
    LOW_REAL_RATE_BETA_REASON,
    LOW_NOMINAL_RATE_BETA_REASON,
    RATE_VOLATILITY_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
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
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("api", "_", "key"),
        _join_parts("api", "-", "key"),
        _join_parts("api", "key"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_RATE_SENSITIVITY_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldRateSensitivityDigestConfig",
    "MarketResearchGoldRateSensitivityDigestReasonCodeCount",
    "MarketResearchGoldRateSensitivityDigestReport",
    "MarketResearchGoldRateSensitivityDigestRow",
    "MarketResearchGoldRateSensitivityDigestSignal",
    "build_market_research_gold_rate_sensitivity_digest",
    "market_research_gold_rate_sensitivity_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldRateSensitivityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_RATE_SENSITIVITY_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_real_rate_beta: Decimal = Decimal("0.550000")
    min_nominal_rate_beta: Decimal = Decimal("0.300000")
    max_rate_volatility_score: Decimal = Decimal("0.700000")
    min_inverse_rate_confirmation: Decimal = Decimal("0.650000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRateSensitivityDigestConfig:
            raise TypeError(
                "MarketResearchGoldRateSensitivityDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRateSensitivityDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchGoldRateSensitivityDigestConfig",
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
            "min_real_rate_beta",
            "min_nominal_rate_beta",
            "max_rate_volatility_score",
            "min_inverse_rate_confirmation",
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
class MarketResearchGoldRateSensitivityDigestSignal:
    condition_id: str
    gold_rate_key: str
    rate_family: str
    public_signal_reference: str
    observed_at: datetime
    real_rate_beta: Decimal
    nominal_rate_beta: Decimal
    rate_volatility_score: Decimal
    inverse_rate_confirmation: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRateSensitivityDigestSignal:
            raise TypeError(
                "MarketResearchGoldRateSensitivityDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRateSensitivityDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchGoldRateSensitivityDigestSignal",
            )
        for field_name in (
            "condition_id",
            "gold_rate_key",
            "rate_family",
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
            "real_rate_beta",
            "nominal_rate_beta",
            "rate_volatility_score",
            "inverse_rate_confirmation",
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
class MarketResearchGoldRateSensitivityDigestRow:
    condition_id: str
    gold_rate_key: str
    rate_family: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    real_rate_beta: Decimal
    nominal_rate_beta: Decimal
    rate_volatility_score: Decimal
    inverse_rate_confirmation: Decimal
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
        if cls is not MarketResearchGoldRateSensitivityDigestRow:
            raise TypeError(
                "MarketResearchGoldRateSensitivityDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRateSensitivityDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGoldRateSensitivityDigestRow",
            )
        for field_name in ("condition_id", "gold_rate_key", "rate_family"):
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
            "real_rate_beta",
            "nominal_rate_beta",
            "rate_volatility_score",
            "inverse_rate_confirmation",
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
class MarketResearchGoldRateSensitivityDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRateSensitivityDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldRateSensitivityDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRateSensitivityDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchGoldRateSensitivityDigestReasonCodeCount",
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
class MarketResearchGoldRateSensitivityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    low_real_rate_beta_signal_count: Decimal
    low_nominal_rate_beta_signal_count: Decimal
    rate_volatility_gap_signal_count: Decimal
    inverse_rate_confirmation_gap_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_real_rate_beta: Decimal
    average_inverse_rate_confirmation: Decimal
    max_signal_age_seconds: Decimal
    min_real_rate_beta: Decimal
    min_nominal_rate_beta: Decimal
    max_rate_volatility_score: Decimal
    min_inverse_rate_confirmation: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchGoldRateSensitivityDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchGoldRateSensitivityDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRateSensitivityDigestReport:
            raise TypeError(
                "MarketResearchGoldRateSensitivityDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRateSensitivityDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchGoldRateSensitivityDigestReport",
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
            "low_real_rate_beta_signal_count",
            "low_nominal_rate_beta_signal_count",
            "rate_volatility_gap_signal_count",
            "inverse_rate_confirmation_gap_signal_count",
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
            "average_real_rate_beta",
            "average_inverse_rate_confirmation",
            "min_real_rate_beta",
            "min_nominal_rate_beta",
            "max_rate_volatility_score",
            "min_inverse_rate_confirmation",
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


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchGoldRateSensitivityDigestConfig,
    MarketResearchGoldRateSensitivityDigestSignal,
    MarketResearchGoldRateSensitivityDigestRow,
    MarketResearchGoldRateSensitivityDigestReasonCodeCount,
    MarketResearchGoldRateSensitivityDigestReport,
)


def build_market_research_gold_rate_sensitivity_digest(
    signals: Iterable[MarketResearchGoldRateSensitivityDigestSignal],
    *,
    config: MarketResearchGoldRateSensitivityDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchGoldRateSensitivityDigestReport:
    cfg = (
        MarketResearchGoldRateSensitivityDigestConfig()
        if config is None
        else config
    )
    if type(cfg) is not MarketResearchGoldRateSensitivityDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchGoldRateSensitivityDigestConfig",
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
            key=lambda row: (_row_sort_value(row), row.gold_rate_key, row.condition_id),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchGoldRateSensitivityDigestReport(
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
        low_real_rate_beta_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_REAL_RATE_BETA_REASON,
        ),
        low_nominal_rate_beta_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_NOMINAL_RATE_BETA_REASON,
        ),
        rate_volatility_gap_signal_count=_reason_signal_count(
            sorted_rows,
            RATE_VOLATILITY_GAP_REASON,
        ),
        inverse_rate_confirmation_gap_signal_count=_reason_signal_count(
            sorted_rows,
            INVERSE_RATE_CONFIRMATION_GAP_REASON,
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
        average_real_rate_beta=_ratio(
            _decimal_sum(row.real_rate_beta for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_inverse_rate_confirmation=_ratio(
            _decimal_sum(row.inverse_rate_confirmation for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_real_rate_beta=cfg.min_real_rate_beta,
        min_nominal_rate_beta=cfg.min_nominal_rate_beta,
        max_rate_volatility_score=cfg.max_rate_volatility_score,
        min_inverse_rate_confirmation=cfg.min_inverse_rate_confirmation,
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
                    signal.gold_rate_key,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_gold_rate_sensitivity_digest_payload(
    report: MarketResearchGoldRateSensitivityDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldRateSensitivityDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchGoldRateSensitivityDigestReport",
        )
    _require_payload_safe_value("report", report)
    _require_hard_flags("report", report)
    _validate_report(report)
    serialized = _json_ready(report)
    if not isinstance(serialized, dict):
        raise ValueError("serialized report must be a dict")
    return serialized


def _row_for_signal(
    signal: MarketResearchGoldRateSensitivityDigestSignal,
    *,
    config: MarketResearchGoldRateSensitivityDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldRateSensitivityDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(signal=signal, config=config, generated_at=generated_at)
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _final_confidence(signal.base_confidence, confidence_decay_factor)
    return MarketResearchGoldRateSensitivityDigestRow(
        condition_id=signal.condition_id,
        gold_rate_key=signal.gold_rate_key,
        rate_family=signal.rate_family,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        observed_at=signal.observed_at,
        signal_age_seconds=_age_seconds(generated_at, signal.observed_at),
        real_rate_beta=signal.real_rate_beta,
        nominal_rate_beta=signal.nominal_rate_beta,
        rate_volatility_score=signal.rate_volatility_score,
        inverse_rate_confirmation=signal.inverse_rate_confirmation,
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
    signal: MarketResearchGoldRateSensitivityDigestSignal,
    config: MarketResearchGoldRateSensitivityDigestConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    signal_age_seconds = _age_seconds(generated_at, signal.observed_at)
    reasons: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if signal.real_rate_beta < config.min_real_rate_beta:
        reasons.append(LOW_REAL_RATE_BETA_REASON)
    if signal.nominal_rate_beta < config.min_nominal_rate_beta:
        reasons.append(LOW_NOMINAL_RATE_BETA_REASON)
    if signal.rate_volatility_score > config.max_rate_volatility_score:
        reasons.append(RATE_VOLATILITY_GAP_REASON)
    if signal.inverse_rate_confirmation < config.min_inverse_rate_confirmation:
        reasons.append(INVERSE_RATE_CONFIRMATION_GAP_REASON)
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
    config: MarketResearchGoldRateSensitivityDigestConfig,
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
    if any(reason_code in reason_codes for reason_code in BLOCKING_ROW_REASON_CODES):
        return STATUS_BLOCKED
    if reason_codes != (READY_REASON,) or final_confidence < watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_READY


def _report_status(
    rows: tuple[MarketResearchGoldRateSensitivityDigestRow, ...],
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
        return "allow_report_only_market_research_gold_rate_sensitivity_digest"
    if status == STATUS_WATCH:
        return "monitor_report_only_market_research_gold_rate_sensitivity_digest"
    return "block_report_only_market_research_gold_rate_sensitivity_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchGoldRateSensitivityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _reason_code_counts(
    rows: tuple[MarketResearchGoldRateSensitivityDigestRow, ...],
) -> tuple[MarketResearchGoldRateSensitivityDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchGoldRateSensitivityDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    counts: list[MarketResearchGoldRateSensitivityDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_signal_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchGoldRateSensitivityDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    signal_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_signal_count(
    rows: tuple[MarketResearchGoldRateSensitivityDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: MarketResearchGoldRateSensitivityDigestRow) -> None:
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence decay")
    if row.reason_codes == (READY_REASON,) and row.confidence_decay_factor != ZERO:
        raise ValueError("ready rows must not have confidence decay")
    has_blocking_reason = any(
        reason_code in row.reason_codes for reason_code in BLOCKING_ROW_REASON_CODES
    )
    if row.digest_status == STATUS_BLOCKED and not has_blocking_reason:
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status != STATUS_BLOCKED and has_blocking_reason:
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchGoldRateSensitivityDigestReport) -> None:
    for row in report.rows:
        _require_hard_flags("row", row)
    for reason_code_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_code_count)
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
        ("low_real_rate_beta_signal_count", LOW_REAL_RATE_BETA_REASON),
        ("low_nominal_rate_beta_signal_count", LOW_NOMINAL_RATE_BETA_REASON),
        ("rate_volatility_gap_signal_count", RATE_VOLATILITY_GAP_REASON),
        (
            "inverse_rate_confirmation_gap_signal_count",
            INVERSE_RATE_CONFIRMATION_GAP_REASON,
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
    if report.average_real_rate_beta != _ratio(
        _decimal_sum(row.real_rate_beta for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_real_rate_beta must match rows")
    if report.average_inverse_rate_confirmation != _ratio(
        _decimal_sum(row.inverse_rate_confirmation for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_inverse_rate_confirmation must match rows")
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
    signals: Iterable[MarketResearchGoldRateSensitivityDigestSignal],
) -> tuple[MarketResearchGoldRateSensitivityDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain gold rate sensitivity rows")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must contain gold rate sensitivity rows") from exc
    seen: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchGoldRateSensitivityDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchGoldRateSensitivityDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.gold_rate_key in seen:
            raise ValueError("gold_rate_key values must be unique")
        seen.add(signal.gold_rate_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchGoldRateSensitivityDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must contain gold rate sensitivity digest rows")
    normalized = rows
    for row in normalized:
        if type(row) is not MarketResearchGoldRateSensitivityDigestRow:
            raise ValueError(
                "rows must contain MarketResearchGoldRateSensitivityDigestRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (_row_sort_value(row), row.gold_rate_key, row.condition_id),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    if len({row.gold_rate_key for row in normalized}) != len(normalized):
        raise ValueError("gold_rate_key values must be unique")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("signal_config_versions must contain pairs")
    normalized = value
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not tuple or len(item) != 2:
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
) -> tuple[MarketResearchGoldRateSensitivityDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = value
    for item in normalized:
        if type(item) is not MarketResearchGoldRateSensitivityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldRateSensitivityDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    if normalized != tuple(
        sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must contain reason code strings")
    normalized = value
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    reason_sequence = {
        reason_code: index for index, reason_code in enumerate(sequence)
    }
    if normalized and normalized != tuple(
        sorted(normalized, key=lambda reason_code: reason_sequence[reason_code]),
    ):
        raise ValueError("reason_codes must be sorted")
    return normalized


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize(seconds + micros)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _row_sort_value(row: MarketResearchGoldRateSensitivityDigestRow) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]


def _redacted_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("JSON dataclass must be a supported public dataclass")
        ready: dict[str, Any] = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                if item is not True:
                    raise ValueError(f"{field.name} must be True")
            ready[field.name] = _json_ready(item)
        return ready
    if type(value) is Decimal:
        if _require_decimal("JSON Decimal value", value) != value:
            raise ValueError("JSON Decimal value must be quantized to six decimals")
        if not value.same_quantum(QUANT):
            raise ValueError("JSON Decimal value must be quantized to six decimals")
        return format(value, "f")
    if isinstance(value, Decimal):
        raise ValueError("payload numerics must be exact Decimals")
    if type(value) is datetime:
        _as_utc("JSON datetime value", value)
        if value.tzinfo is not UTC:
            raise ValueError("JSON datetime value must be normalized to UTC")
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("JSON value must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return value
    return value


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        decimal_value = _require_decimal(field_name, value)
        if decimal_value != value or not value.same_quantum(QUANT):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _rebuild_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _rebuild_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} contains unknown reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains disallowed text")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize(value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_count_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
