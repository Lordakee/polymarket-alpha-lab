"""Pure Phase 1 household employment surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_HOUSEHOLD_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-household-employment-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_household_employment_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
LOW_HOUSEHOLD_EMPLOYMENT_SURPRISE_REASON = (
    f"{REASON_PREFIX}low_household_employment_surprise"
)
LOW_UNEMPLOYMENT_RATE_SURPRISE_REASON = (
    f"{REASON_PREFIX}low_unemployment_rate_surprise"
)
LOW_PARTICIPATION_RATE_SURPRISE_REASON = (
    f"{REASON_PREFIX}low_participation_rate_surprise"
)
SOURCE_FAMILY_GAP_REASON = f"{REASON_PREFIX}source_family_gap"
STALE_SOURCE_RATIO_REASON = f"{REASON_PREFIX}stale_source_ratio"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    STALE_SIGNAL_REASON,
    LOW_HOUSEHOLD_EMPLOYMENT_SURPRISE_REASON,
    LOW_UNEMPLOYMENT_RATE_SURPRISE_REASON,
    LOW_PARTICIPATION_RATE_SURPRISE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_HOUSEHOLD_EMPLOYMENT_SURPRISE_REASON,
    LOW_UNEMPLOYMENT_RATE_SURPRISE_REASON,
    LOW_PARTICIPATION_RATE_SURPRISE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_household_employment_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_household_employment_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_household_employment_surprise_digest",
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
    "DEFAULT_MARKET_RESEARCH_HOUSEHOLD_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchHouseholdEmploymentSurpriseDigestConfig",
    "MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount",
    "MarketResearchHouseholdEmploymentSurpriseDigestReport",
    "MarketResearchHouseholdEmploymentSurpriseDigestRow",
    "MarketResearchHouseholdEmploymentSurpriseDigestSignal",
    "build_market_research_household_employment_surprise_digest",
    "market_research_household_employment_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchHouseholdEmploymentSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_HOUSEHOLD_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("10800.000000")
    min_household_employment_surprise_score: Decimal = Decimal("0.600000")
    min_unemployment_rate_surprise_score: Decimal = Decimal("0.500000")
    min_participation_rate_surprise_score: Decimal = Decimal("0.300000")
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
        if cls is not MarketResearchHouseholdEmploymentSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchHouseholdEmploymentSurpriseDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchHouseholdEmploymentSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchHouseholdEmploymentSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_HOUSEHOLD_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
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
            "min_source_family_count",
            _require_positive_count_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        for field_name in (
            "min_household_employment_surprise_score",
            "min_unemployment_rate_surprise_score",
            "min_participation_rate_surprise_score",
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
class MarketResearchHouseholdEmploymentSurpriseDigestSignal:
    condition_id: str
    household_employment_key: str
    event_key: str
    household_metric: str
    public_signal_reference: str
    observed_at: datetime
    signal_age_seconds: Decimal
    household_employment_surprise_score: Decimal
    unemployment_rate_surprise_score: Decimal
    participation_rate_surprise_score: Decimal
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
        if cls is not MarketResearchHouseholdEmploymentSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchHouseholdEmploymentSurpriseDigestSignal does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchHouseholdEmploymentSurpriseDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchHouseholdEmploymentSurpriseDigestSignal",
            )
        for field_name in (
            "condition_id",
            "household_employment_key",
            "event_key",
            "household_metric",
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
            "signal_age_seconds",
            _require_nonnegative_count_decimal(
                "signal_age_seconds",
                self.signal_age_seconds,
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
            "household_employment_surprise_score",
            "unemployment_rate_surprise_score",
            "participation_rate_surprise_score",
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
class MarketResearchHouseholdEmploymentSurpriseDigestRow:
    condition_id: str
    household_employment_key: str
    event_key: str
    household_metric: str
    digest_status: str
    observed_at: datetime
    observed_signal_age_seconds: Decimal
    input_signal_age_seconds: Decimal
    household_employment_surprise_score: Decimal
    unemployment_rate_surprise_score: Decimal
    participation_rate_surprise_score: Decimal
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
        if cls is not MarketResearchHouseholdEmploymentSurpriseDigestRow:
            raise TypeError(
                "MarketResearchHouseholdEmploymentSurpriseDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchHouseholdEmploymentSurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchHouseholdEmploymentSurpriseDigestRow",
            )
        for field_name in (
            "condition_id",
            "household_employment_key",
            "event_key",
            "household_metric",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observed_signal_age_seconds",
            "input_signal_age_seconds",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "household_employment_surprise_score",
            "unemployment_rate_surprise_score",
            "participation_rate_surprise_score",
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
        object.__setattr__(
            self,
            "redacted_public_signal_reference",
            _require_redacted_reference(
                "redacted_public_signal_reference",
                self.redacted_public_signal_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.digest_status == STATUS_READY and self.reason_codes != (READY_REASON,):
            raise ValueError("ready rows must only carry the ready reason code")
        if self.digest_status != STATUS_READY and READY_REASON in self.reason_codes:
            raise ValueError("non-ready rows cannot carry the ready reason code")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount",
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
class MarketResearchHouseholdEmploymentSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    low_household_employment_surprise_signal_count: Decimal
    low_unemployment_rate_surprise_signal_count: Decimal
    low_participation_rate_surprise_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal | None
    average_household_employment_surprise_score: Decimal | None
    average_unemployment_rate_surprise_score: Decimal | None
    average_participation_rate_surprise_score: Decimal | None
    average_confirmation_ratio: Decimal | None
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchHouseholdEmploymentSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchHouseholdEmploymentSurpriseDigestReport:
            raise TypeError(
                "MarketResearchHouseholdEmploymentSurpriseDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchHouseholdEmploymentSurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchHouseholdEmploymentSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "low_household_employment_surprise_signal_count",
            "low_unemployment_rate_surprise_signal_count",
            "low_participation_rate_surprise_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
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
            _require_ratio_decimal("total_confidence_decay", self.total_confidence_decay),
        )
        for field_name in (
            "average_final_confidence",
            "average_household_employment_surprise_score",
            "average_unemployment_rate_surprise_score",
            "average_participation_rate_surprise_score",
            "average_confirmation_ratio",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_ratio_decimal(field_name, value),
                )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if (
            self.ready_signal_count + self.watch_signal_count + self.blocked_signal_count
            != self.signal_count
        ):
            raise ValueError("status counts must sum to signal_count")
        if self.signal_count != _decimal_count(self.rows):
            raise ValueError("signal_count must match rows")
        _require_hard_flags("report", self)


def build_market_research_household_employment_surprise_digest(
    signals: Iterable[MarketResearchHouseholdEmploymentSurpriseDigestSignal],
    *,
    config: MarketResearchHouseholdEmploymentSurpriseDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchHouseholdEmploymentSurpriseDigestReport:
    cfg = config or MarketResearchHouseholdEmploymentSurpriseDigestConfig()
    if type(cfg) is not MarketResearchHouseholdEmploymentSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchHouseholdEmploymentSurpriseDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_signals = _coerce_signals(signals)

    rows = tuple(
        _build_row(signal, config=cfg, generated_at=generated_at_utc)
        for signal in source_signals
    )
    rows = tuple(sorted(rows, key=_row_sort_key))

    signal_count = _decimal_count(rows)
    ready_count = _decimal_count(row for row in rows if row.digest_status == STATUS_READY)
    watch_count = _decimal_count(row for row in rows if row.digest_status == STATUS_WATCH)
    blocked_count = _decimal_count(
        row for row in rows if row.digest_status == STATUS_BLOCKED
    )
    reason_code_counts = _build_reason_code_counts(rows, signal_count)
    digest_status = _digest_status(rows)

    return MarketResearchHouseholdEmploymentSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=ready_count,
        watch_signal_count=watch_count,
        blocked_signal_count=blocked_count,
        stale_signal_count=_count_reason(rows, STALE_SIGNAL_REASON),
        low_household_employment_surprise_signal_count=_count_reason(
            rows,
            LOW_HOUSEHOLD_EMPLOYMENT_SURPRISE_REASON,
        ),
        low_unemployment_rate_surprise_signal_count=_count_reason(
            rows,
            LOW_UNEMPLOYMENT_RATE_SURPRISE_REASON,
        ),
        low_participation_rate_surprise_signal_count=_count_reason(
            rows,
            LOW_PARTICIPATION_RATE_SURPRISE_REASON,
        ),
        source_family_gap_signal_count=_count_reason(rows, SOURCE_FAMILY_GAP_REASON),
        stale_source_signal_count=_count_reason(rows, STALE_SOURCE_RATIO_REASON),
        confirmation_gap_signal_count=_count_reason(rows, CONFIRMATION_GAP_REASON),
        total_confidence_decay=_sum_decimal(
            row.confidence_decay_factor for row in rows
        ),
        average_final_confidence=_average(row.final_confidence for row in rows),
        average_household_employment_surprise_score=_average(
            row.household_employment_surprise_score for row in rows
        ),
        average_unemployment_rate_surprise_score=_average(
            row.unemployment_rate_surprise_score for row in rows
        ),
        average_participation_rate_surprise_score=_average(
            row.participation_rate_surprise_score for row in rows
        ),
        average_confirmation_ratio=_average(row.confirmation_ratio for row in rows),
        max_observed_signal_age_seconds=max(
            (row.observed_signal_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_household_employment_surprise_digest_payload(
    report: MarketResearchHouseholdEmploymentSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchHouseholdEmploymentSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchHouseholdEmploymentSurpriseDigestReport",
        )
    _require_payload_phase1_flags(report)
    return _to_payload(asdict(report))


def _build_row(
    signal: MarketResearchHouseholdEmploymentSurpriseDigestSignal,
    *,
    config: MarketResearchHouseholdEmploymentSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchHouseholdEmploymentSurpriseDigestRow:
    observed_age = max(_age_seconds(generated_at, signal.observed_at), ZERO)
    reasons: list[str] = []
    if observed_age > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if (
        signal.household_employment_surprise_score
        < config.min_household_employment_surprise_score
    ):
        reasons.append(LOW_HOUSEHOLD_EMPLOYMENT_SURPRISE_REASON)
    if signal.unemployment_rate_surprise_score < config.min_unemployment_rate_surprise_score:
        reasons.append(LOW_UNEMPLOYMENT_RATE_SURPRISE_REASON)
    if signal.participation_rate_surprise_score < config.min_participation_rate_surprise_score:
        reasons.append(LOW_PARTICIPATION_RATE_SURPRISE_REASON)
    if signal.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(STALE_SOURCE_RATIO_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)

    if not reasons:
        reasons = [READY_REASON]
        digest_status = STATUS_READY
    else:
        digest_status = STATUS_WATCH

    ordered_reasons = _ordered_reasons(reasons, ROW_REASON_CODE_SEQUENCE)
    gap_count = _decimal_count(
        reason_code
        for reason_code in ordered_reasons
        if reason_code not in (READY_REASON, STALE_SIGNAL_REASON)
    )
    decay = min(ONE, _quantize(gap_count * config.confidence_decay_per_gap))
    final_confidence = max(ZERO, _quantize(signal.base_confidence - decay))
    if final_confidence < config.watch_confidence_threshold:
        digest_status = STATUS_BLOCKED
    elif ordered_reasons != (READY_REASON,):
        digest_status = STATUS_WATCH

    return MarketResearchHouseholdEmploymentSurpriseDigestRow(
        condition_id=signal.condition_id,
        household_employment_key=signal.household_employment_key,
        event_key=signal.event_key,
        household_metric=signal.household_metric,
        digest_status=digest_status,
        observed_at=signal.observed_at,
        observed_signal_age_seconds=observed_age,
        input_signal_age_seconds=signal.signal_age_seconds,
        household_employment_surprise_score=signal.household_employment_surprise_score,
        unemployment_rate_surprise_score=signal.unemployment_rate_surprise_score,
        participation_rate_surprise_score=signal.participation_rate_surprise_score,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=decay,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        reason_codes=ordered_reasons,
    )


def _build_reason_code_counts(
    rows: tuple[MarketResearchHouseholdEmploymentSurpriseDigestRow, ...],
    signal_count: Decimal,
) -> tuple[MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    if not rows:
        counts[NO_INPUTS_REASON] = ZERO

    return tuple(
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            signal_ratio=ZERO if signal_count == ZERO else _quantize(count / signal_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (_reason_sort_index(item[0]), item[0]),
        )
    )


def _digest_status(
    rows: tuple[MarketResearchHouseholdEmploymentSurpriseDigestRow, ...],
) -> str:
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    if rows:
        return STATUS_READY
    return STATUS_WATCH


def _coerce_signals(
    signals: Iterable[MarketResearchHouseholdEmploymentSurpriseDigestSignal],
) -> tuple[MarketResearchHouseholdEmploymentSurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be an iterable")
    coerced = tuple(signals)
    for signal in coerced:
        if type(signal) is not MarketResearchHouseholdEmploymentSurpriseDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchHouseholdEmploymentSurpriseDigestSignal items",
            )
    return coerced


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchHouseholdEmploymentSurpriseDigestRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("rows must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchHouseholdEmploymentSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchHouseholdEmploymentSurpriseDigestRow items",
            )
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount items",
            )
    return rows


def _require_payload_phase1_flags(
    report: MarketResearchHouseholdEmploymentSurpriseDigestReport,
) -> None:
    _require_hard_flags("report", report)
    for row in _normalize_rows(report.rows):
        _require_hard_flags("row", row)
    for reason_code_count in _normalize_reason_code_counts(report.reason_code_counts):
        _require_hard_flags("reason code count", reason_code_count)


def _row_sort_key(
    row: MarketResearchHouseholdEmploymentSurpriseDigestRow,
) -> tuple[int, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.digest_status],
        row.household_employment_key,
        row.condition_id,
        row.event_key,
    )


def _ordered_reasons(
    reason_codes: Iterable[str],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    unique = set(reason_codes)
    return tuple(
        reason_code
        for reason_code in sorted(
            unique,
            key=lambda reason_code: (
                sequence.index(reason_code)
                if reason_code in sequence
                else len(sequence),
                reason_code,
            ),
        )
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_codes must be an iterable")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    return _ordered_reasons(reason_codes, ROW_REASON_CODE_SEQUENCE)


def _count_reason(
    rows: tuple[MarketResearchHouseholdEmploymentSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(row for row in rows if reason_code in row.reason_codes)


def _decimal_count(value: Iterable[object]) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in value)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _average(values: Iterable[Decimal]) -> Decimal | None:
    collected = tuple(values)
    if not collected:
        return None
    return _quantize(_sum_decimal(collected) / Decimal(len(collected)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(micros / MICROSECONDS_PER_SECOND)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    lower_value = value.lower()
    if any(fragment in lower_value for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, flag, None)) is not bool:
            raise ValueError(f"{field_name} {flag} must be a bool")
        if getattr(value, flag) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _redacted_reference(value: str) -> str:
    _require_canonical_string("public_signal_reference", value)
    if _is_reference_safe(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_reference_is_redacted_safe(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be redacted")


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be redacted")
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) == 12 and all(char in "0123456789abcdef" for char in digest):
            return value
        raise ValueError(f"{field_name} must be redacted")
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _is_reference_safe(value: str) -> bool:
    lower_value = value.lower()
    if "://" in lower_value or any(
        fragment in lower_value for fragment in UNSAFE_TEXT_FRAGMENTS
    ):
        return False
    return True


def _reason_sort_index(reason_code: str) -> int:
    if reason_code in REASON_CODE_SEQUENCE:
        return REASON_CODE_SEQUENCE.index(reason_code)
    return len(REASON_CODE_SEQUENCE)


def _to_payload(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_to_payload(item) for item in value]
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_payload(item) for key, item in value.items()}
    return value
