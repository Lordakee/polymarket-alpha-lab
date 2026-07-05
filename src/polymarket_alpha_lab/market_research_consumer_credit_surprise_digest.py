"""Pure Phase 1 consumer-credit surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-consumer-credit-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_consumer_credit_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    MATERIAL_SURPRISE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    MATERIAL_SURPRISE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_consumer_credit_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_consumer_credit_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_consumer_credit_surprise_digest",
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
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("ven", "dor"),
        _join_parts("https", "://"),
        _join_parts("http", "://"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchConsumerCreditSurpriseDigestConfig",
    "MarketResearchConsumerCreditSurpriseDigestReasonCodeCount",
    "MarketResearchConsumerCreditSurpriseDigestReport",
    "MarketResearchConsumerCreditSurpriseDigestRow",
    "MarketResearchConsumerCreditSurpriseDigestSignal",
    "build_market_research_consumer_credit_surprise_digest",
    "market_research_consumer_credit_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchConsumerCreditSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("0.030000")
    max_revision_ratio: Decimal = Decimal("0.200000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    watch_confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchConsumerCreditSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchConsumerCreditSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestConfig does not "
                "support subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_positive_count_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_surprise_threshold",
            "max_revision_ratio",
            "min_confirmation_ratio",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_surprise_threshold <= ZERO:
            raise ValueError("material_surprise_threshold must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchConsumerCreditSurpriseDigestSignal:
    condition_id: str
    research_key: str
    release_key: str
    credit_segment: str
    public_signal_reference: str
    observed_at: datetime
    expected_credit_change: Decimal
    actual_credit_change: Decimal
    surprise_score: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchConsumerCreditSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestSignal does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchConsumerCreditSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestSignal does not "
                "support subclassing",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "credit_segment",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference_is_redacted_safe(
            "public_signal_reference",
            self.public_signal_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_credit_change", "actual_credit_change"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "surprise_score",
            "revision_ratio",
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
class MarketResearchConsumerCreditSurpriseDigestRow:
    condition_id: str
    research_key: str
    release_key: str
    credit_segment: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    expected_credit_change: Decimal
    actual_credit_change: Decimal
    surprise_delta: Decimal
    surprise_score: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchConsumerCreditSurpriseDigestRow:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchConsumerCreditSurpriseDigestRow:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestRow does not support "
                "subclassing",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "credit_segment",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("signal_age_seconds", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_credit_change",
            "actual_credit_change",
            "surprise_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "surprise_score",
            "revision_ratio",
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
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=False,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchConsumerCreditSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchConsumerCreditSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchConsumerCreditSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestReasonCodeCount does "
                "not support subclassing",
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
class MarketResearchConsumerCreditSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    material_surprise_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_surprise_score: Decimal | None
    max_signal_age_seconds: Decimal | None
    average_source_count: Decimal | None
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchConsumerCreditSurpriseDigestReport:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchConsumerCreditSurpriseDigestReport:
            raise TypeError(
                "MarketResearchConsumerCreditSurpriseDigestReport does not "
                "support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "material_surprise_count",
            "stale_signal_count",
            "thin_source_count",
            "high_revision_count",
            "confirmation_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_surprise_score",
            "max_signal_age_seconds",
            "average_source_count",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, value),
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
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=False,
                sequence=REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_consumer_credit_surprise_digest(
    signals: Iterable[MarketResearchConsumerCreditSurpriseDigestSignal],
    *,
    config: MarketResearchConsumerCreditSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchConsumerCreditSurpriseDigestReport:
    if type(config) is not MarketResearchConsumerCreditSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchConsumerCreditSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _build_row(signal, config=config, generated_at=generated_at_utc)
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows, reason_codes)
    signal_count = _decimal_count(len(rows))
    return MarketResearchConsumerCreditSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        stale_signal_count=_reason_count(rows, STALE_SIGNAL_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        average_surprise_score=_average_decimal(row.surprise_score for row in rows),
        max_signal_age_seconds=_max_decimal(row.signal_age_seconds for row in rows),
        average_source_count=_average_decimal(row.source_count for row in rows),
        rows=rows,
        reason_code_counts=(
            _row_reason_code_counts(rows)
            if rows
            else _reason_code_counts(reason_codes)
        ),
        reason_codes=reason_codes,
    )


def market_research_consumer_credit_surprise_digest_payload(
    report: MarketResearchConsumerCreditSurpriseDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(report, dict):
        _require_payload_hard_flags("payload", report)
        _require_payload_public_strings("payload", report)
        return _payload_value(report)
    if type(report) is not MarketResearchConsumerCreditSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchConsumerCreditSurpriseDigestReport",
        )
    payload = _payload_value(asdict(report))
    _require_payload_public_strings("payload", payload)
    return payload


def _build_row(
    signal: MarketResearchConsumerCreditSurpriseDigestSignal,
    *,
    config: MarketResearchConsumerCreditSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchConsumerCreditSurpriseDigestRow:
    signal_age_seconds = _datetime_delta_seconds(generated_at, signal.observed_at)
    surprise_delta = _quantize_decimal(
        signal.actual_credit_change - signal.expected_credit_change,
    )
    reason_codes = _row_reason_codes(signal, signal_age_seconds, config=config)
    digest_status = _row_status(reason_codes, signal.base_confidence, config=config)
    decay_factor = _confidence_decay_factor(reason_codes)
    final_confidence = _quantize_ratio(signal.base_confidence * decay_factor)
    return MarketResearchConsumerCreditSurpriseDigestRow(
        condition_id=signal.condition_id,
        research_key=signal.research_key,
        release_key=signal.release_key,
        credit_segment=signal.credit_segment,
        digest_status=digest_status,
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        expected_credit_change=signal.expected_credit_change,
        actual_credit_change=signal.actual_credit_change,
        surprise_delta=surprise_delta,
        surprise_score=signal.surprise_score,
        source_count=signal.source_count,
        revision_ratio=signal.revision_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redact_public_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchConsumerCreditSurpriseDigestSignal,
    signal_age_seconds: Decimal,
    *,
    config: MarketResearchConsumerCreditSurpriseDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        codes.append(STALE_SIGNAL_REASON)
    if signal.surprise_score >= config.material_surprise_threshold:
        codes.append(MATERIAL_SURPRISE_REASON)
    if signal.source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if signal.revision_ratio > config.max_revision_ratio:
        codes.append(HIGH_REVISION_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        codes.append(CONFIRMATION_GAP_REASON)
    if not codes:
        codes.append(READY_REASON)
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in codes)


def _row_status(
    reason_codes: tuple[str, ...],
    base_confidence: Decimal,
    *,
    config: MarketResearchConsumerCreditSurpriseDigestConfig,
) -> str:
    if STALE_SIGNAL_REASON in reason_codes or HIGH_REVISION_REASON in reason_codes:
        return STATUS_BLOCKED
    if (
        THIN_SOURCES_REASON in reason_codes
        and CONFIRMATION_GAP_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if base_confidence < config.watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_WATCH


def _confidence_decay_factor(reason_codes: tuple[str, ...]) -> Decimal:
    penalty = ZERO
    if STALE_SIGNAL_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if (
        MATERIAL_SURPRISE_REASON in reason_codes
        and STALE_SIGNAL_REASON not in reason_codes
        and THIN_SOURCES_REASON not in reason_codes
        and HIGH_REVISION_REASON not in reason_codes
    ):
        penalty += Decimal("0.100000")
    if THIN_SOURCES_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if HIGH_REVISION_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if CONFIRMATION_GAP_REASON in reason_codes:
        penalty += Decimal("0.100000")
    decay = ONE - penalty
    if decay < ZERO:
        return ZERO
    return _quantize_ratio(decay)


def _report_reason_codes(
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_CODE_SEQUENCE if code in present)


def _report_status(
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchConsumerCreditSurpriseDigestReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    raise ValueError("rows are required to count row reason codes")


def _row_reason_code_counts(
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...],
) -> tuple[MarketResearchConsumerCreditSurpriseDigestReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    counts: list[MarketResearchConsumerCreditSurpriseDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                signal_ratio=_ratio(count, signal_count),
            ),
        )
    return tuple(counts)


def _status_count(
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_signals(
    signals: Iterable[MarketResearchConsumerCreditSurpriseDigestSignal],
) -> tuple[MarketResearchConsumerCreditSurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be an iterable of consumer credit signals")
    normalized = tuple(signals)
    for signal in normalized:
        if type(signal) is not MarketResearchConsumerCreditSurpriseDigestSignal:
            raise ValueError(
                "signals must contain exactly "
                "MarketResearchConsumerCreditSurpriseDigestSignal",
            )
        _require_hard_flags("signal", signal)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...],
) -> tuple[MarketResearchConsumerCreditSurpriseDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchConsumerCreditSurpriseDigestRow:
            raise ValueError(
                "rows must contain exactly "
                "MarketResearchConsumerCreditSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchConsumerCreditSurpriseDigestReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)) or not isinstance(
        reason_code_counts,
        tuple,
    ):
        raise ValueError("reason_code_counts must be a tuple")
    for count in reason_code_counts:
        if type(count) is not MarketResearchConsumerCreditSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchConsumerCreditSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    seen_reason_codes: set[str] = set()
    for count in reason_code_counts:
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(count.reason_code)
    expected = tuple(
        sorted(
            reason_code_counts,
            key=lambda item: _reason_rank(item.reason_code),
        ),
    )
    if reason_code_counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return reason_code_counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        try:
            _require_reason_code("reason_code", reason_code)
        except ValueError as exc:
            raise ValueError("reason_codes must contain supported reason codes") from exc
        if reason_code not in sequence:
            raise ValueError("reason_codes must contain supported reason codes")
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must contain unique reason codes")
        seen_reason_codes.add(reason_code)
    if (
        sequence == ROW_REASON_CODE_SEQUENCE
        and READY_REASON in seen_reason_codes
        and len(seen_reason_codes) != 1
    ):
        raise ValueError("ready reason_code must be exclusive")
    if NO_INPUTS_REASON in seen_reason_codes and len(seen_reason_codes) != 1:
        raise ValueError("no_inputs reason_code must be exclusive")
    expected = tuple(
        reason_code for reason_code in sequence if reason_code in seen_reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _validate_row_consistency(row: MarketResearchConsumerCreditSurpriseDigestRow) -> None:
    expected_delta = _quantize_decimal(
        row.actual_credit_change - row.expected_credit_change,
    )
    if row.surprise_delta != expected_delta:
        raise ValueError(
            "surprise_delta must equal actual_credit_change minus "
            "expected_credit_change",
        )
    if row.reason_codes == (READY_REASON,) and row.digest_status != STATUS_READY:
        raise ValueError("ready reason row must have ready digest_status")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("ready digest_status must only use the ready reason code")


def _validate_report_consistency(
    report: MarketResearchConsumerCreditSurpriseDigestReport,
) -> None:
    rows = report.rows
    signal_count = _decimal_count(len(rows))
    if report.signal_count != signal_count:
        raise ValueError("signal_count must equal rows length")
    status_total = (
        report.ready_signal_count
        + report.watch_signal_count
        + report.blocked_signal_count
    )
    if status_total != report.signal_count:
        raise ValueError("status counts must equal signal_count")
    expected_counts = _row_reason_code_counts(rows) if rows else _reason_code_counts(
        report.reason_codes,
    )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows and reason_codes")
    expected_reason_codes = tuple(count.reason_code for count in expected_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(rows, report.reason_codes)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_values = {
        "ready_signal_count": _status_count(rows, STATUS_READY),
        "watch_signal_count": _status_count(rows, STATUS_WATCH),
        "blocked_signal_count": _status_count(rows, STATUS_BLOCKED),
        "material_surprise_count": _reason_count(rows, MATERIAL_SURPRISE_REASON),
        "stale_signal_count": _reason_count(rows, STALE_SIGNAL_REASON),
        "thin_source_count": _reason_count(rows, THIN_SOURCES_REASON),
        "high_revision_count": _reason_count(rows, HIGH_REVISION_REASON),
        "confirmation_gap_count": _reason_count(rows, CONFIRMATION_GAP_REASON),
        "average_surprise_score": _average_decimal(row.surprise_score for row in rows),
        "max_signal_age_seconds": _max_decimal(row.signal_age_seconds for row in rows),
        "average_source_count": _average_decimal(row.source_count for row in rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _row_sort_key(
    row: MarketResearchConsumerCreditSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.surprise_score,
        -row.signal_age_seconds,
        row.condition_id,
        row.release_key,
    )


def _status_rank(status: str) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[status]


def _reason_rank(reason_code: str) -> int:
    if reason_code in REASON_CODE_SEQUENCE:
        return REASON_CODE_SEQUENCE.index(reason_code)
    if reason_code in ROW_REASON_CODE_SEQUENCE:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    raise ValueError(f"unsupported reason_code: {reason_code}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in set(REASON_CODE_SEQUENCE).union(
        ROW_REASON_CODE_SEQUENCE,
    ):
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_reference_is_redacted_safe(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if _join_parts("wal", "let") in lowered:
        raise ValueError(f"{field_name} must be public and redacted")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    return _quantize_decimal(_require_decimal(field_name, value))


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_decimal(decimal_value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize_decimal(seconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_ratio(numerator / denominator)


def _average_decimal(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_decimal(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _quantize_ratio(value: Decimal) -> Decimal:
    quantized = _quantize_decimal(value)
    if quantized < ZERO or quantized > ONE:
        raise ValueError("ratio must be between 0 and 1")
    return quantized


def _redact_public_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_quantize_decimal(value), "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _require_payload_hard_flags(label: str, value: Any) -> None:
    if isinstance(value, dict):
        flag_names = ("paper_only", "report_only", "readonly")
        if any(field_name in value for field_name in flag_names):
            for field_name in flag_names:
                if value.get(field_name) is not True:
                    raise ValueError(f"{label}.{field_name} must be True")
        for item in value.values():
            _require_payload_hard_flags(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _require_payload_hard_flags(label, item)


def _require_payload_public_strings(label: str, value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} must be public and redacted")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                _require_payload_public_strings(label, key)
            _require_payload_public_strings(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _require_payload_public_strings(label, item)
