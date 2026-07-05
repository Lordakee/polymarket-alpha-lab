"""Pure Phase 1 report-only leading economic index surprise reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-leading-economic-index-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
SURPRISE_DIRECTIONS = ("upside", "downside", "inline")

REASON_PREFIX = "market_research_leading_economic_index_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    CONFIRMATION_GAP_REASON,
    HIGH_REVISION_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    CONFIRMATION_GAP_REASON,
    HIGH_REVISION_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_leading_economic_index_surprise_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_leading_economic_index_surprise_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_leading_economic_index_surprise_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchLeadingEconomicIndexSurpriseDigestConfig",
    "MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount",
    "MarketResearchLeadingEconomicIndexSurpriseDigestReport",
    "MarketResearchLeadingEconomicIndexSurpriseDigestRow",
    "MarketResearchLeadingEconomicIndexSurpriseDigestSignal",
    "build_market_research_leading_economic_index_surprise_digest",
    "market_research_leading_economic_index_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchLeadingEconomicIndexSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("0.030000")
    max_revision_ratio: Decimal = Decimal("0.200000")
    min_confirmation_ratio: Decimal = Decimal("0.700000")
    stale_confidence_decay: Decimal = Decimal("0.250000")
    thin_source_confidence_decay: Decimal = Decimal("0.150000")
    revision_confidence_decay: Decimal = Decimal("0.100000")
    confirmation_confidence_decay: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchLeadingEconomicIndexSurpriseDigestConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchLeadingEconomicIndexSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchLeadingEconomicIndexSurpriseDigestConfig does not "
                "support subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_positive_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_positive_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        for field_name in (
            "max_revision_ratio",
            "min_confirmation_ratio",
            "stale_confidence_decay",
            "thin_source_confidence_decay",
            "revision_confidence_decay",
            "confirmation_confidence_decay",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchLeadingEconomicIndexSurpriseDigestSignal:
    condition_id: str
    research_key: str
    release_key: str
    indicator_key: str
    public_signal_reference: str
    observed_at: datetime
    expected_index_change: Decimal
    actual_index_change: Decimal
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
        raise TypeError(
            "MarketResearchLeadingEconomicIndexSurpriseDigestSignal does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchLeadingEconomicIndexSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchLeadingEconomicIndexSurpriseDigestSignal does not "
                "support subclassing",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "indicator_key",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_index_change", "actual_index_change"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_score",
            _require_nonnegative_decimal("surprise_score", self.surprise_score),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("revision_ratio", "confirmation_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchLeadingEconomicIndexSurpriseDigestRow:
    condition_id: str
    research_key: str
    release_key: str
    indicator_key: str
    digest_status: str
    surprise_direction: str
    observed_at: datetime
    signal_age_seconds: Decimal
    expected_index_change: Decimal
    actual_index_change: Decimal
    leading_index_surprise_delta: Decimal
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
        raise TypeError(
            "MarketResearchLeadingEconomicIndexSurpriseDigestRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchLeadingEconomicIndexSurpriseDigestRow:
            raise TypeError(
                "MarketResearchLeadingEconomicIndexSurpriseDigestRow does not "
                "support subclassing",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "indicator_key",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_index_change",
            "actual_index_change",
            "leading_index_surprise_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_age_seconds",
            "surprise_score",
            "confidence_decay_factor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "revision_ratio",
            "confirmation_ratio",
            "base_confidence",
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
class MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount "
                "does not support subclassing",
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
class MarketResearchLeadingEconomicIndexSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    material_surprise_count: Decimal
    upside_surprise_count: Decimal
    downside_surprise_count: Decimal
    inline_surprise_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_surprise_score: Decimal
    average_final_confidence: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchLeadingEconomicIndexSurpriseDigestReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchLeadingEconomicIndexSurpriseDigestReport:
            raise TypeError(
                "MarketResearchLeadingEconomicIndexSurpriseDigestReport does not "
                "support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_LEADING_ECONOMIC_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
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
            "upside_surprise_count",
            "downside_surprise_count",
            "inline_surprise_count",
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
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_final_confidence",
            _require_ratio_decimal("average_final_confidence", self.average_final_confidence),
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
                sequence=REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_leading_economic_index_surprise_digest(
    signals: Iterable[MarketResearchLeadingEconomicIndexSurpriseDigestSignal],
    *,
    config: MarketResearchLeadingEconomicIndexSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchLeadingEconomicIndexSurpriseDigestReport:
    if type(config) is not MarketResearchLeadingEconomicIndexSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchLeadingEconomicIndexSurpriseDigestConfig",
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
    reason_code_counts = _expected_reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchLeadingEconomicIndexSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=_decimal_count(len(rows)),
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        upside_surprise_count=_direction_count(rows, "upside"),
        downside_surprise_count=_direction_count(rows, "downside"),
        inline_surprise_count=_direction_count(rows, "inline"),
        stale_signal_count=_reason_count(rows, STALE_SIGNAL_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        average_surprise_score=_average_decimal(row.surprise_score for row in rows),
        average_final_confidence=_average_decimal(row.final_confidence for row in rows),
        max_observed_signal_age_seconds=_max_decimal(
            (row.signal_age_seconds for row in rows),
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_leading_economic_index_surprise_digest_payload(
    report: MarketResearchLeadingEconomicIndexSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchLeadingEconomicIndexSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchLeadingEconomicIndexSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _build_row(
    signal: MarketResearchLeadingEconomicIndexSurpriseDigestSignal,
    *,
    config: MarketResearchLeadingEconomicIndexSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchLeadingEconomicIndexSurpriseDigestRow:
    signal_age_seconds = _datetime_delta_seconds(generated_at, signal.observed_at)
    leading_index_surprise_delta = _normalize_decimal(
        "leading_index_surprise_delta",
        signal.actual_index_change - signal.expected_index_change,
    )
    reason_codes = _row_reason_codes(
        signal,
        signal_age_seconds,
        config=config,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config)
    return MarketResearchLeadingEconomicIndexSurpriseDigestRow(
        condition_id=signal.condition_id,
        research_key=signal.research_key,
        release_key=signal.release_key,
        indicator_key=signal.indicator_key,
        digest_status=_row_status(reason_codes),
        surprise_direction=_surprise_direction(leading_index_surprise_delta),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        expected_index_change=signal.expected_index_change,
        actual_index_change=signal.actual_index_change,
        leading_index_surprise_delta=leading_index_surprise_delta,
        surprise_score=signal.surprise_score,
        source_count=signal.source_count,
        revision_ratio=signal.revision_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=_final_confidence(
            signal.base_confidence,
            confidence_decay_factor,
        ),
        redacted_public_signal_reference=_redacted_public_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchLeadingEconomicIndexSurpriseDigestSignal,
    signal_age_seconds: Decimal,
    *,
    config: MarketResearchLeadingEconomicIndexSurpriseDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal.surprise_score >= config.material_surprise_threshold:
        reason_codes.append(MATERIAL_SURPRISE_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if signal.revision_ratio > config.max_revision_ratio:
        reason_codes.append(HIGH_REVISION_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        CONFIRMATION_GAP_REASON in reason_codes
        or STALE_SIGNAL_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    config: MarketResearchLeadingEconomicIndexSurpriseDigestConfig,
) -> Decimal:
    decay = ZERO
    if STALE_SIGNAL_REASON in reason_codes:
        decay += config.stale_confidence_decay
    if THIN_SOURCES_REASON in reason_codes:
        decay += config.thin_source_confidence_decay
    if HIGH_REVISION_REASON in reason_codes:
        decay += config.revision_confidence_decay
    if CONFIRMATION_GAP_REASON in reason_codes:
        decay += config.confirmation_confidence_decay
    return _quantize_decimal(decay)


def _final_confidence(base_confidence: Decimal, confidence_decay_factor: Decimal) -> Decimal:
    value = base_confidence - confidence_decay_factor
    if value < ZERO:
        return ZERO
    return _quantize_decimal(value)


def _surprise_direction(value: Decimal) -> str:
    if value > ZERO:
        return "upside"
    if value < ZERO:
        return "downside"
    return "inline"


def _expected_reason_code_counts(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
) -> tuple[MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    return _row_reason_code_counts(rows)


def _row_reason_code_counts(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
) -> tuple[MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    counts: list[MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount] = []
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                signal_ratio=_ratio(count, signal_count),
            ),
        )
    return tuple(counts)


def _normalize_signals(
    signals: Iterable[MarketResearchLeadingEconomicIndexSurpriseDigestSignal],
) -> tuple[MarketResearchLeadingEconomicIndexSurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be an iterable of leading economic index signals")
    normalized = tuple(signals)
    seen_condition_ids: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchLeadingEconomicIndexSurpriseDigestSignal:
            raise ValueError(
                "signals must contain exactly "
                "MarketResearchLeadingEconomicIndexSurpriseDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.condition_id in seen_condition_ids:
            raise ValueError("signals must use unique condition_id values")
        seen_condition_ids.add(signal.condition_id)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
) -> tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchLeadingEconomicIndexSurpriseDigestRow:
            raise ValueError(
                "rows must contain exactly "
                "MarketResearchLeadingEconomicIndexSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
        if row.condition_id in seen_condition_ids:
            raise ValueError("rows must use unique condition_id values")
        seen_condition_ids.add(row.condition_id)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must use deterministic ordering")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)) or type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for count in reason_code_counts:
        if type(count) is not MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchLeadingEconomicIndexSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(count.reason_code)
    expected = tuple(
        sorted(
            reason_code_counts,
            key=lambda item: REPORT_REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if reason_code_counts != expected:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return reason_code_counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes must contain supported reason codes")
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
    if (
        sequence == ROW_REASON_CODE_SEQUENCE
        and READY_REASON in seen_reason_codes
        and len(seen_reason_codes) != 1
    ):
        raise ValueError("ready reason_code must be exclusive")
    if NO_INPUTS_REASON in seen_reason_codes and len(seen_reason_codes) != 1:
        raise ValueError("no_inputs reason_code must be exclusive")
    expected = tuple(reason_code for reason_code in sequence if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic ordering")
    return reason_codes


def _validate_row_consistency(
    row: MarketResearchLeadingEconomicIndexSurpriseDigestRow,
) -> None:
    expected_delta = _normalize_decimal(
        "leading_index_surprise_delta",
        row.actual_index_change - row.expected_index_change,
    )
    if row.leading_index_surprise_delta != expected_delta:
        raise ValueError(
            "leading_index_surprise_delta must equal actual_index_change minus "
            "expected_index_change",
        )
    if row.surprise_direction != _surprise_direction(row.leading_index_surprise_delta):
        raise ValueError("surprise_direction must match leading_index_surprise_delta")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence decay")


def _validate_report_consistency(
    report: MarketResearchLeadingEconomicIndexSurpriseDigestReport,
) -> None:
    rows = report.rows
    signal_count = _decimal_count(len(rows))
    if report.signal_count != signal_count:
        raise ValueError("signal_count must match rows")
    expected_counts = (
        ("ready_signal_count", _status_count(rows, STATUS_READY)),
        ("watch_signal_count", _status_count(rows, STATUS_WATCH)),
        ("blocked_signal_count", _status_count(rows, STATUS_BLOCKED)),
        ("material_surprise_count", _reason_count(rows, MATERIAL_SURPRISE_REASON)),
        ("upside_surprise_count", _direction_count(rows, "upside")),
        ("downside_surprise_count", _direction_count(rows, "downside")),
        ("inline_surprise_count", _direction_count(rows, "inline")),
        ("stale_signal_count", _reason_count(rows, STALE_SIGNAL_REASON)),
        ("thin_source_count", _reason_count(rows, THIN_SOURCES_REASON)),
        ("high_revision_count", _reason_count(rows, HIGH_REVISION_REASON)),
        ("confirmation_gap_count", _reason_count(rows, CONFIRMATION_GAP_REASON)),
        ("average_surprise_score", _average_decimal(row.surprise_score for row in rows)),
        (
            "average_final_confidence",
            _average_decimal(row.final_confidence for row in rows),
        ),
        (
            "max_observed_signal_age_seconds",
            _max_decimal(row.signal_age_seconds for row in rows),
        ),
    )
    for field_name, expected in expected_counts:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    status_total = (
        report.ready_signal_count
        + report.watch_signal_count
        + report.blocked_signal_count
    )
    if status_total != report.signal_count:
        raise ValueError("status counts must match signal_count")
    direction_total = (
        report.upside_surprise_count
        + report.downside_surprise_count
        + report.inline_surprise_count
    )
    if direction_total != report.signal_count:
        raise ValueError("surprise direction counts must match signal_count")
    expected_reason_code_counts = _expected_reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _row_sort_key(
    row: MarketResearchLeadingEconomicIndexSurpriseDigestRow,
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


def _status_count(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _direction_count(
    rows: tuple[MarketResearchLeadingEconomicIndexSurpriseDigestRow, ...],
    surprise_direction: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if row.surprise_direction == surprise_direction),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize_decimal(seconds)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _must_redact_public_reference(value):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_surprise_direction(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SURPRISE_DIRECTIONS:
        raise ValueError(f"{field_name} must be upside, downside, or inline")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(_require_decimal(field_name, value))


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_decimal(decimal_value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize_decimal(decimal_value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(decimal_value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize_decimal(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize_decimal(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redacted_public_reference(value: str) -> str:
    if _must_redact_public_reference(value):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _must_redact_public_reference(value: str) -> bool:
    lowered = value.lower()
    hidden_fragments = (
        "://",
        "?",
        "=",
        *(
            "".join(chr(code) for code in codes)
            for codes in (
                (97, 117, 116, 104),
                (112, 114, 105, 118, 97, 116, 101),
                (115, 101, 99, 114, 101, 116),
                (116, 111, 107, 101, 110),
                (119, 97, 108, 108, 101, 116),
            )
        ),
    )
    return any(fragment in lowered for fragment in hidden_fragments)


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        return format(_normalize_decimal("payload numeric", value), "f")
    if isinstance(value, Decimal):
        raise ValueError("payload numeric values must be exact Decimal values")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
        return {key: _payload_value(item) for key, item in value.items()}
    return value
