"""Pure Phase 1 rates policy surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-rates-policy-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_rates_policy_surprise_digest_no_inputs"
READY_REASON = "market_research_rates_policy_surprise_digest_ready"
STALE_POLICY_SIGNAL_REASON = (
    "market_research_rates_policy_surprise_digest_stale_policy_signal"
)
LOW_PROBABILITY_DELTA_REASON = (
    "market_research_rates_policy_surprise_digest_low_probability_delta"
)
LOW_STATEMENT_SURPRISE_REASON = (
    "market_research_rates_policy_surprise_digest_low_statement_surprise"
)
SOURCE_FAMILY_GAP_REASON = (
    "market_research_rates_policy_surprise_digest_source_family_gap"
)
STALE_SOURCE_RATIO_REASON = (
    "market_research_rates_policy_surprise_digest_stale_source_ratio"
)
CONFIRMATION_GAP_REASON = (
    "market_research_rates_policy_surprise_digest_confirmation_gap"
)

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    STALE_POLICY_SIGNAL_REASON,
    LOW_PROBABILITY_DELTA_REASON,
    LOW_STATEMENT_SURPRISE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_POLICY_SIGNAL_REASON,
    LOW_PROBABILITY_DELTA_REASON,
    LOW_STATEMENT_SURPRISE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
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
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
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
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesPolicySurpriseDigestConfig",
    "MarketResearchRatesPolicySurpriseDigestReasonCodeCount",
    "MarketResearchRatesPolicySurpriseDigestReport",
    "MarketResearchRatesPolicySurpriseDigestRow",
    "MarketResearchRatesPolicySurpriseDigestSignal",
    "build_market_research_rates_policy_surprise_digest",
    "market_research_rates_policy_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRatesPolicySurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_policy_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_implied_probability_delta: Decimal = Decimal("0.050000")
    min_statement_surprise_score: Decimal = Decimal("0.600000")
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
        if cls is not MarketResearchRatesPolicySurpriseDigestConfig:
            raise TypeError(
                "MarketResearchRatesPolicySurpriseDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesPolicySurpriseDigestConfig:
            raise TypeError(
                "MarketResearchRatesPolicySurpriseDigestConfig does not support "
                "subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_policy_signal_age_seconds",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_implied_probability_delta",
            "min_statement_surprise_score",
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
class MarketResearchRatesPolicySurpriseDigestSignal:
    condition_id: str
    rates_policy_key: str
    central_bank: str
    policy_event_key: str
    public_signal_reference: str
    observed_at: datetime
    policy_signal_age_seconds: Decimal
    implied_probability_delta: Decimal
    statement_surprise_score: Decimal
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
        if cls is not MarketResearchRatesPolicySurpriseDigestSignal:
            raise TypeError(
                "MarketResearchRatesPolicySurpriseDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesPolicySurpriseDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchRatesPolicySurpriseDigestSignal",
            )
        for field_name in (
            "condition_id",
            "rates_policy_key",
            "central_bank",
            "policy_event_key",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference_is_redacted_safe(
            "public_signal_reference",
            self.public_signal_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "policy_signal_age_seconds",
            _require_nonnegative_count_decimal(
                "policy_signal_age_seconds",
                self.policy_signal_age_seconds,
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
            "implied_probability_delta",
            "statement_surprise_score",
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
class MarketResearchRatesPolicySurpriseDigestRow:
    condition_id: str
    rates_policy_key: str
    central_bank: str
    policy_event_key: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    policy_signal_age_seconds: Decimal
    implied_probability_delta: Decimal
    statement_surprise_score: Decimal
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
        if cls is not MarketResearchRatesPolicySurpriseDigestRow:
            raise TypeError(
                "MarketResearchRatesPolicySurpriseDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesPolicySurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchRatesPolicySurpriseDigestRow",
            )
        for field_name in (
            "condition_id",
            "rates_policy_key",
            "central_bank",
            "policy_event_key",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "policy_signal_age_seconds",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "implied_probability_delta",
            "statement_surprise_score",
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
            _normalize_reason_codes(self.reason_codes, order=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchRatesPolicySurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesPolicySurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchRatesPolicySurpriseDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesPolicySurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchRatesPolicySurpriseDigestReasonCodeCount",
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
class MarketResearchRatesPolicySurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_policy_signal_count: Decimal
    low_probability_delta_signal_count: Decimal
    low_statement_surprise_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_implied_probability_delta: Decimal
    average_statement_surprise_score: Decimal
    average_confirmation_ratio: Decimal
    max_policy_signal_age_seconds: Decimal
    min_implied_probability_delta: Decimal
    min_statement_surprise_score: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    min_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchRatesPolicySurpriseDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesPolicySurpriseDigestReport:
            raise TypeError(
                "MarketResearchRatesPolicySurpriseDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesPolicySurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchRatesPolicySurpriseDigestReport",
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
            "stale_policy_signal_count",
            "low_probability_delta_signal_count",
            "low_statement_surprise_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
            "total_confidence_decay",
            "max_policy_signal_age_seconds",
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
            "average_implied_probability_delta",
            "average_statement_surprise_score",
            "average_confirmation_ratio",
            "min_implied_probability_delta",
            "min_statement_surprise_score",
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
            _normalize_reason_codes(self.reason_codes, order=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_rates_policy_surprise_digest(
    signals: Iterable[MarketResearchRatesPolicySurpriseDigestSignal],
    *,
    config: MarketResearchRatesPolicySurpriseDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchRatesPolicySurpriseDigestReport:
    cfg = config or MarketResearchRatesPolicySurpriseDigestConfig()
    if type(cfg) is not MarketResearchRatesPolicySurpriseDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchRatesPolicySurpriseDigestConfig",
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
                row.rates_policy_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchRatesPolicySurpriseDigestReport(
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
        stale_policy_signal_count=_reason_signal_count(
            sorted_rows,
            STALE_POLICY_SIGNAL_REASON,
        ),
        low_probability_delta_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_PROBABILITY_DELTA_REASON,
        ),
        low_statement_surprise_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_STATEMENT_SURPRISE_REASON,
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
        total_confidence_decay=_decimal_sum(
            row.confidence_decay_factor for row in sorted_rows
        ),
        average_final_confidence=_ratio(
            _decimal_sum(row.final_confidence for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_implied_probability_delta=_ratio(
            _decimal_sum(row.implied_probability_delta for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_statement_surprise_score=_ratio(
            _decimal_sum(row.statement_surprise_score for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_confirmation_ratio=_ratio(
            _decimal_sum(row.confirmation_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_policy_signal_age_seconds=cfg.max_policy_signal_age_seconds,
        min_implied_probability_delta=cfg.min_implied_probability_delta,
        min_statement_surprise_score=cfg.min_statement_surprise_score,
        min_source_family_count=cfg.min_source_family_count,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        min_confirmation_ratio=cfg.min_confirmation_ratio,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        signal_config_versions=tuple(
            sorted(
                (
                    signal.rates_policy_key,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_rates_policy_surprise_digest_payload(
    report: MarketResearchRatesPolicySurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRatesPolicySurpriseDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchRatesPolicySurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_for_signal(
    signal: MarketResearchRatesPolicySurpriseDigestSignal,
    *,
    config: MarketResearchRatesPolicySurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesPolicySurpriseDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(signal=signal, config=config)
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _final_confidence(signal.base_confidence, confidence_decay_factor)
    return MarketResearchRatesPolicySurpriseDigestRow(
        condition_id=signal.condition_id,
        rates_policy_key=signal.rates_policy_key,
        central_bank=signal.central_bank,
        policy_event_key=signal.policy_event_key,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        observed_at=signal.observed_at,
        signal_age_seconds=_age_seconds(generated_at, signal.observed_at),
        policy_signal_age_seconds=signal.policy_signal_age_seconds,
        implied_probability_delta=signal.implied_probability_delta,
        statement_surprise_score=signal.statement_surprise_score,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
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
    signal: MarketResearchRatesPolicySurpriseDigestSignal,
    config: MarketResearchRatesPolicySurpriseDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.policy_signal_age_seconds > config.max_policy_signal_age_seconds:
        reasons.append(STALE_POLICY_SIGNAL_REASON)
    if signal.implied_probability_delta < config.min_implied_probability_delta:
        reasons.append(LOW_PROBABILITY_DELTA_REASON)
    if signal.statement_surprise_score < config.min_statement_surprise_score:
        reasons.append(LOW_STATEMENT_SURPRISE_REASON)
    if signal.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(STALE_SOURCE_RATIO_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchRatesPolicySurpriseDigestConfig,
) -> Decimal:
    gap_count = sum(1 for reason in reason_codes if reason != READY_REASON)
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
        STALE_POLICY_SIGNAL_REASON in reason_codes
        or LOW_PROBABILITY_DELTA_REASON in reason_codes
        or LOW_STATEMENT_SURPRISE_REASON in reason_codes
        or SOURCE_FAMILY_GAP_REASON in reason_codes
        or STALE_SOURCE_RATIO_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes != (READY_REASON,) or final_confidence < watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_READY


def _report_status(rows: tuple[MarketResearchRatesPolicySurpriseDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "allow_report_only_market_research_rates_policy_surprise_digest"
    if status == STATUS_WATCH:
        return "monitor_report_only_market_research_rates_policy_surprise_digest"
    return "block_report_only_market_research_rates_policy_surprise_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchRatesPolicySurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _reason_code_counts(
    rows: tuple[MarketResearchRatesPolicySurpriseDigestRow, ...],
) -> tuple[MarketResearchRatesPolicySurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    counts: list[MarketResearchRatesPolicySurpriseDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_signal_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    signal_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_signal_count(
    rows: tuple[MarketResearchRatesPolicySurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: MarketResearchRatesPolicySurpriseDigestRow) -> None:
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence decay")
    if row.reason_codes == (READY_REASON,) and row.confidence_decay_factor != ZERO:
        raise ValueError("ready rows must not have confidence decay")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchRatesPolicySurpriseDigestReport) -> None:
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
        ("stale_policy_signal_count", STALE_POLICY_SIGNAL_REASON),
        ("low_probability_delta_signal_count", LOW_PROBABILITY_DELTA_REASON),
        ("low_statement_surprise_signal_count", LOW_STATEMENT_SURPRISE_REASON),
        ("source_family_gap_signal_count", SOURCE_FAMILY_GAP_REASON),
        ("stale_source_signal_count", STALE_SOURCE_RATIO_REASON),
        ("confirmation_gap_signal_count", CONFIRMATION_GAP_REASON),
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
    if report.average_implied_probability_delta != _ratio(
        _decimal_sum(row.implied_probability_delta for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_implied_probability_delta must match rows")
    if report.average_statement_surprise_score != _ratio(
        _decimal_sum(row.statement_surprise_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_statement_surprise_score must match rows")
    if report.average_confirmation_ratio != _ratio(
        _decimal_sum(row.confirmation_ratio for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_confirmation_ratio must match rows")
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
    signals: Iterable[MarketResearchRatesPolicySurpriseDigestSignal],
) -> tuple[MarketResearchRatesPolicySurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain rates policy surprise rows")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must contain rates policy surprise rows") from exc
    seen: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchRatesPolicySurpriseDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchRatesPolicySurpriseDigestSignal",
            )
        if signal.rates_policy_key in seen:
            raise ValueError("rates_policy_key values must be unique")
        seen.add(signal.rates_policy_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchRatesPolicySurpriseDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain rates policy surprise digest rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain rates policy surprise digest rows") from exc
    for row in normalized:
        if type(row) is not MarketResearchRatesPolicySurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchRatesPolicySurpriseDigestRow",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                _row_sort_value(row),
                row.rates_policy_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    if len({row.rates_policy_key for row in normalized}) != len(normalized):
        raise ValueError("rates_policy_key values must be unique")
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
) -> tuple[MarketResearchRatesPolicySurpriseDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in normalized:
        if type(item) is not MarketResearchRatesPolicySurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRatesPolicySurpriseDigestReasonCodeCount",
            )
    if normalized != tuple(
        sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return normalized


def _normalize_reason_codes(value: object, *, order: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain reason code strings") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    reason_order = {reason_code: index for index, reason_code in enumerate(order)}
    if normalized and normalized != tuple(
        sorted(
            normalized,
            key=lambda reason_code: reason_order[reason_code],
        ),
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


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _row_sort_value(row: MarketResearchRatesPolicySurpriseDigestRow) -> int:
    if row.digest_status == STATUS_BLOCKED:
        return 0
    if row.digest_status == STATUS_WATCH:
        return 1
    return 2


def _redacted_reference(value: str) -> str:
    if _is_reference_safe(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _is_reference_safe(value: str) -> bool:
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _json_ready(value: object) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, Decimal):
        raise ValueError("payload Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("payload datetime value", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload datetime value must be exactly datetime")
    if type(value) is int:
        raise ValueError("payload numeric value must use Decimal")
    if type(value) is float:
        raise ValueError("payload must not contain floats")
    if type(value) is bool:
        return value
    if type(value) is str:
        _require_public_string("payload string value", value)
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            _require_public_string("payload object key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("payload value is not JSON serializable")


def _require_reference_is_redacted_safe(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not _is_reference_safe(value) and "://" not in value:
        raise ValueError(f"{field_name} must be redacted")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or not all(
            character in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"{field_name} must be redacted")
        return
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must contain a known digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a timezone offset")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
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
