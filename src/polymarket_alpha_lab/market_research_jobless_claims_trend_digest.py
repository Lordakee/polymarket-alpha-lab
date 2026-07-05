"""Pure Phase 1 jobless claims trend digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION = (
    "market-research-jobless-claims-trend-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_jobless_claims_trend_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
LOW_CLAIMS_CHANGE_REASON = f"{REASON_PREFIX}low_claims_change"
LOW_CLAIMS_CHANGE_RATIO_REASON = f"{REASON_PREFIX}low_claims_change_ratio"
SOURCE_FAMILY_GAP_REASON = f"{REASON_PREFIX}source_family_gap"
STALE_SOURCE_RATIO_REASON = f"{REASON_PREFIX}stale_source_ratio"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    STALE_RELEASE_REASON,
    LOW_CLAIMS_CHANGE_REASON,
    LOW_CLAIMS_CHANGE_RATIO_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_RELEASE_REASON,
    LOW_CLAIMS_CHANGE_REASON,
    LOW_CLAIMS_CHANGE_RATIO_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_jobless_claims_trend_digest",
    STATUS_WATCH: "watch_report_only_market_research_jobless_claims_trend_digest",
    STATUS_BLOCKED: "block_report_only_market_research_jobless_claims_trend_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CONFIDENCE_DECAY_PER_REASON = Decimal("0.100000")
MAX_CONFIDENCE_DECAY = Decimal("0.400000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


SENSITIVE_REFERENCE_FRAGMENTS = frozenset(
    (
        "://",
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION",
    "MarketResearchJoblessClaimsTrendDigestConfig",
    "MarketResearchJoblessClaimsTrendDigestReasonCodeCount",
    "MarketResearchJoblessClaimsTrendDigestReport",
    "MarketResearchJoblessClaimsTrendDigestRow",
    "MarketResearchJoblessClaimsTrendDigestSignal",
    "build_market_research_jobless_claims_trend_digest",
    "market_research_jobless_claims_trend_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchJoblessClaimsTrendDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
    max_release_age_seconds: Decimal = Decimal("7200.000000")
    min_claims_change: Decimal = Decimal("5000.000000")
    min_claims_change_ratio: Decimal = Decimal("0.020000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoblessClaimsTrendDigestConfig:
            raise TypeError(
                "MarketResearchJoblessClaimsTrendDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoblessClaimsTrendDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchJoblessClaimsTrendDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_release_age_seconds",
            "min_claims_change",
            "min_claims_change_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
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
            "max_stale_source_ratio",
            "min_confirmation_ratio",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchJoblessClaimsTrendDigestSignal:
    condition_id: str
    claims_market_key: str
    release_key: str
    public_signal_reference: str
    released_at: datetime
    prior_claims: Decimal
    current_claims: Decimal
    claims_change: Decimal
    claims_change_ratio: Decimal
    four_week_average_claims: Decimal
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
        if cls is not MarketResearchJoblessClaimsTrendDigestSignal:
            raise TypeError(
                "MarketResearchJoblessClaimsTrendDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoblessClaimsTrendDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchJoblessClaimsTrendDigestSignal",
            )
        for field_name in (
            "condition_id",
            "claims_market_key",
            "release_key",
            "public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        for field_name in (
            "prior_claims",
            "current_claims",
            "four_week_average_claims",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "claims_change",
            _require_finite_decimal("claims_change", self.claims_change),
        )
        for field_name in (
            "claims_change_ratio",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchJoblessClaimsTrendDigestRow:
    condition_id: str
    claims_market_key: str
    release_key: str
    digest_status: str
    released_at: datetime
    release_age_seconds: Decimal
    prior_claims: Decimal
    current_claims: Decimal
    claims_change: Decimal
    claims_change_ratio: Decimal
    four_week_average_claims: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    final_confidence: Decimal
    signal_config_version: str
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoblessClaimsTrendDigestRow:
            raise TypeError(
                "MarketResearchJoblessClaimsTrendDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoblessClaimsTrendDigestRow:
            raise ValueError("row must be exactly MarketResearchJoblessClaimsTrendDigestRow")
        for field_name in (
            "condition_id",
            "claims_market_key",
            "release_key",
            "signal_config_version",
            "redacted_public_signal_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        for field_name in (
            "prior_claims",
            "current_claims",
            "four_week_average_claims",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "claims_change",
            _require_finite_decimal("claims_change", self.claims_change),
        )
        for field_name in (
            "claims_change_ratio",
            "stale_source_ratio",
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
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_status_reason_codes(self.digest_status, self.reason_codes)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchJoblessClaimsTrendDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchJoblessClaimsTrendDigestReasonCodeCount",
            )
        _require_known_reason_code("reason_code", self.reason_code)
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
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchJoblessClaimsTrendDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_release_signal_count: Decimal
    low_claims_change_signal_count: Decimal
    low_claims_change_ratio_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    average_final_confidence: Decimal | None
    average_claims_change: Decimal | None
    average_claims_change_ratio: Decimal | None
    average_confirmation_ratio: Decimal | None
    max_release_age_seconds: Decimal
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...]
    reason_code_counts: tuple[MarketResearchJoblessClaimsTrendDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoblessClaimsTrendDigestReport:
            raise TypeError(
                "MarketResearchJoblessClaimsTrendDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoblessClaimsTrendDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchJoblessClaimsTrendDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_digest_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_release_signal_count",
            "low_claims_change_signal_count",
            "low_claims_change_ratio_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        average_validators = (
            ("average_final_confidence", _require_ratio_decimal),
            ("average_claims_change", _require_finite_decimal),
            ("average_claims_change_ratio", _require_ratio_decimal),
            ("average_confirmation_ratio", _require_ratio_decimal),
        )
        for field_name, validator in average_validators:
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    validator(field_name, value),
                )
        object.__setattr__(
            self,
            "max_release_age_seconds",
            _require_nonnegative_decimal(
                "max_release_age_seconds",
                self.max_release_age_seconds,
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
            _normalize_reason_codes(self.reason_codes, REASON_CODE_SEQUENCE),
        )
        if (
            self.ready_signal_count + self.watch_signal_count + self.blocked_signal_count
            != self.signal_count
        ):
            raise ValueError("status counts must sum to signal_count")
        if self.signal_count != _decimal_count(self.rows):
            raise ValueError("signal_count must equal row count")
        _validate_report_status_counts(self)
        _validate_report_reason_signal_counts(self)
        _validate_report_aggregates(self)
        _validate_report_reason_codes(self.digest_status, self.reason_codes, self.rows)
        _validate_report_reason_code_counts(self.reason_code_counts, self.rows)
        _require_hard_flags("report", self)


def build_market_research_jobless_claims_trend_digest(
    signals: tuple[object, ...],
    *,
    config: MarketResearchJoblessClaimsTrendDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchJoblessClaimsTrendDigestReport:
    if config is None:
        config = MarketResearchJoblessClaimsTrendDigestConfig()
    if type(config) is not MarketResearchJoblessClaimsTrendDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchJoblessClaimsTrendDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_signals = _normalize_signals(signals)
    rows = tuple(
        _build_digest_row(signal, config=config, generated_at=generated_at_utc)
        for signal in source_signals
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    signal_count = _decimal_count(sorted_rows)
    ready_count = _decimal_count(
        row for row in sorted_rows if row.digest_status == STATUS_READY
    )
    watch_count = _decimal_count(
        row for row in sorted_rows if row.digest_status == STATUS_WATCH
    )
    blocked_count = _decimal_count(
        row for row in sorted_rows if row.digest_status == STATUS_BLOCKED
    )
    digest_status = _digest_status(blocked_count, watch_count, signal_count)
    reason_counts = _build_reason_code_counts(sorted_rows)
    reason_codes = _digest_reason_codes(sorted_rows)
    if not sorted_rows:
        reason_codes = (NO_INPUTS_REASON,)
    return MarketResearchJoblessClaimsTrendDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=ready_count,
        watch_signal_count=watch_count,
        blocked_signal_count=blocked_count,
        stale_release_signal_count=_reason_count(sorted_rows, STALE_RELEASE_REASON),
        low_claims_change_signal_count=_reason_count(
            sorted_rows,
            LOW_CLAIMS_CHANGE_REASON,
        ),
        low_claims_change_ratio_signal_count=_reason_count(
            sorted_rows,
            LOW_CLAIMS_CHANGE_RATIO_REASON,
        ),
        source_family_gap_signal_count=_reason_count(sorted_rows, SOURCE_FAMILY_GAP_REASON),
        stale_source_signal_count=_reason_count(sorted_rows, STALE_SOURCE_RATIO_REASON),
        confirmation_gap_signal_count=_reason_count(sorted_rows, CONFIRMATION_GAP_REASON),
        average_final_confidence=_optional_average(
            tuple(row.final_confidence for row in sorted_rows),
        ),
        average_claims_change=_optional_average(
            tuple(row.claims_change for row in sorted_rows),
        ),
        average_claims_change_ratio=_optional_average(
            tuple(row.claims_change_ratio for row in sorted_rows),
        ),
        average_confirmation_ratio=_optional_average(
            tuple(row.confirmation_ratio for row in sorted_rows),
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def market_research_jobless_claims_trend_digest_payload(
    report: MarketResearchJoblessClaimsTrendDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchJoblessClaimsTrendDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchJoblessClaimsTrendDigestReport",
        )
    _require_payload_public_dataclass(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_digest_row(
    signal: MarketResearchJoblessClaimsTrendDigestSignal,
    *,
    config: MarketResearchJoblessClaimsTrendDigestConfig,
    generated_at: datetime,
) -> MarketResearchJoblessClaimsTrendDigestRow:
    if signal.released_at > generated_at:
        raise ValueError("released_at must not be after generated_at")
    release_age_seconds = _seconds_between(signal.released_at, generated_at)
    reasons: list[str] = []
    if release_age_seconds > config.max_release_age_seconds:
        reasons.append(STALE_RELEASE_REASON)
    if abs(signal.claims_change) < config.min_claims_change:
        reasons.append(LOW_CLAIMS_CHANGE_REASON)
    if abs(signal.claims_change_ratio) < config.min_claims_change_ratio:
        reasons.append(LOW_CLAIMS_CHANGE_RATIO_REASON)
    if signal.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(STALE_SOURCE_RATIO_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    reason_codes = _normalize_reason_codes(tuple(reasons), ROW_REASON_CODE_SEQUENCE)
    status = _row_status(reason_codes, config.watch_confidence_threshold)
    return MarketResearchJoblessClaimsTrendDigestRow(
        condition_id=signal.condition_id,
        claims_market_key=signal.claims_market_key,
        release_key=signal.release_key,
        digest_status=status,
        released_at=signal.released_at,
        release_age_seconds=release_age_seconds,
        prior_claims=signal.prior_claims,
        current_claims=signal.current_claims,
        claims_change=signal.claims_change,
        claims_change_ratio=signal.claims_change_ratio,
        four_week_average_claims=signal.four_week_average_claims,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        final_confidence=_final_confidence(signal.base_confidence, reason_codes),
        signal_config_version=signal.signal_config_version,
        redacted_public_signal_reference=_redact_reference(signal.public_signal_reference),
        reason_codes=reason_codes,
    )


def _row_status(reason_codes: tuple[str, ...], watch_confidence_threshold: Decimal) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            STALE_RELEASE_REASON,
            SOURCE_FAMILY_GAP_REASON,
            STALE_SOURCE_RATIO_REASON,
        )
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    final_confidence = _final_confidence(ONE, reason_codes)
    if final_confidence < watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_WATCH


def _digest_status(
    blocked_count: Decimal,
    watch_count: Decimal,
    signal_count: Decimal,
) -> str:
    if signal_count == ZERO:
        return STATUS_BLOCKED
    if blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(
    row: MarketResearchJoblessClaimsTrendDigestRow,
) -> tuple[int, Decimal, str, str, str]:
    rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    return (
        rank,
        -row.release_age_seconds,
        row.claims_market_key,
        row.condition_id,
        row.release_key,
    )


def _digest_reason_codes(
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if seen == {READY_REASON}:
        return (READY_REASON,)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _build_reason_code_counts(
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...],
) -> tuple[MarketResearchJoblessClaimsTrendDigestReasonCodeCount, ...]:
    total = _decimal_count(rows)
    if total == ZERO:
        return (
            MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    counts: list[MarketResearchJoblessClaimsTrendDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code == NO_INPUTS_REASON:
            continue
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    signal_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_count(
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(row for row in rows if reason_code in row.reason_codes)


def _normalize_signals(
    signals: tuple[object, ...],
) -> tuple[MarketResearchJoblessClaimsTrendDigestSignal, ...]:
    if type(signals) is not tuple:
        raise ValueError("signals must be a tuple")
    normalized: list[MarketResearchJoblessClaimsTrendDigestSignal] = []
    for signal in signals:
        if type(signal) is not MarketResearchJoblessClaimsTrendDigestSignal:
            raise ValueError(
                "signals must contain exactly "
                "MarketResearchJoblessClaimsTrendDigestSignal values",
            )
        _require_hard_flags("signal", signal)
        normalized.append(signal)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...],
) -> tuple[MarketResearchJoblessClaimsTrendDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[MarketResearchJoblessClaimsTrendDigestRow] = []
    for row in rows:
        if type(row) is not MarketResearchJoblessClaimsTrendDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchJoblessClaimsTrendDigestRow",
            )
        normalized.append(row)
    ordered = tuple(sorted(normalized, key=_row_sort_key))
    if ordered != tuple(normalized):
        raise ValueError("rows must be deterministic")
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchJoblessClaimsTrendDigestReasonCodeCount, ...],
) -> tuple[MarketResearchJoblessClaimsTrendDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[MarketResearchJoblessClaimsTrendDigestReasonCodeCount] = []
    for count in counts:
        if type(count) is not MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchJoblessClaimsTrendDigestReasonCodeCount",
            )
        normalized.append(count)
    ordered = tuple(
        sorted(
            normalized,
            key=lambda item: (REASON_CODE_SEQUENCE.index(item.reason_code), item.reason_code),
        ),
    )
    if ordered != tuple(normalized):
        raise ValueError("reason_code_counts must be deterministic")
    return tuple(normalized)


def _validate_row_status_reason_codes(
    digest_status: str,
    reason_codes: tuple[str, ...],
) -> None:
    expected = _row_status(reason_codes, ZERO)
    if digest_status == STATUS_READY and expected != STATUS_READY:
        raise ValueError("digest_status must match reason_codes")
    if digest_status == STATUS_BLOCKED and not any(
        reason_code in reason_codes
        for reason_code in (
            STALE_RELEASE_REASON,
            SOURCE_FAMILY_GAP_REASON,
            STALE_SOURCE_RATIO_REASON,
        )
    ):
        raise ValueError("digest_status must match reason_codes")
    if digest_status == STATUS_WATCH and reason_codes == (READY_REASON,):
        raise ValueError("digest_status must match reason_codes")


def _validate_report_reason_codes(
    digest_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...],
) -> None:
    expected = _digest_reason_codes(rows)
    if reason_codes != expected:
        raise ValueError("reason_codes must summarize rows")
    if digest_status != _digest_status(
        _decimal_count(row for row in rows if row.digest_status == STATUS_BLOCKED),
        _decimal_count(row for row in rows if row.digest_status == STATUS_WATCH),
        _decimal_count(rows),
    ):
        raise ValueError("digest_status must summarize rows")


def _validate_report_status_counts(
    report: MarketResearchJoblessClaimsTrendDigestReport,
) -> None:
    expected_counts = (
        ("ready_signal_count", STATUS_READY),
        ("watch_signal_count", STATUS_WATCH),
        ("blocked_signal_count", STATUS_BLOCKED),
    )
    for field_name, digest_status in expected_counts:
        expected = _decimal_count(
            row for row in report.rows if row.digest_status == digest_status
        )
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must summarize rows")


def _validate_report_reason_signal_counts(
    report: MarketResearchJoblessClaimsTrendDigestReport,
) -> None:
    expected_counts = (
        ("stale_release_signal_count", STALE_RELEASE_REASON),
        ("low_claims_change_signal_count", LOW_CLAIMS_CHANGE_REASON),
        ("low_claims_change_ratio_signal_count", LOW_CLAIMS_CHANGE_RATIO_REASON),
        ("source_family_gap_signal_count", SOURCE_FAMILY_GAP_REASON),
        ("stale_source_signal_count", STALE_SOURCE_RATIO_REASON),
        ("confirmation_gap_signal_count", CONFIRMATION_GAP_REASON),
    )
    for field_name, reason_code in expected_counts:
        expected = _reason_count(report.rows, reason_code)
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must summarize rows")


def _validate_report_aggregates(report: MarketResearchJoblessClaimsTrendDigestReport) -> None:
    expected_averages = (
        (
            "average_final_confidence",
            _optional_average(tuple(row.final_confidence for row in report.rows)),
        ),
        (
            "average_claims_change",
            _optional_average(tuple(row.claims_change for row in report.rows)),
        ),
        (
            "average_claims_change_ratio",
            _optional_average(tuple(row.claims_change_ratio for row in report.rows)),
        ),
        (
            "average_confirmation_ratio",
            _optional_average(tuple(row.confirmation_ratio for row in report.rows)),
        ),
    )
    for field_name, expected in expected_averages:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must summarize rows")

    expected_max_release_age_seconds = max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_release_age_seconds != expected_max_release_age_seconds:
        raise ValueError("max_release_age_seconds must summarize rows")


def _validate_report_reason_code_counts(
    reason_code_counts: tuple[MarketResearchJoblessClaimsTrendDigestReasonCodeCount, ...],
    rows: tuple[MarketResearchJoblessClaimsTrendDigestRow, ...],
) -> None:
    if reason_code_counts != _build_reason_code_counts(rows):
        raise ValueError("reason_code_counts must summarize rows")


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_known_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        if reason_code not in sequence:
            raise ValueError("reason_code is not valid for this scope")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_known_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_digest_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANT)
        except InvalidOperation as exc:
            raise ValueError("decimal value could not be quantized") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _optional_average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _ratio(sum(values, ZERO), _decimal_count(values))


def _decimal_count(values: object) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))  # type: ignore[union-attr]


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("seconds", total)


def _final_confidence(base_confidence: Decimal, reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == (READY_REASON,):
        return _require_ratio_decimal("final_confidence", base_confidence)
    reason_count = _decimal_count(
        reason_code for reason_code in reason_codes if reason_code != READY_REASON
    )
    decay = min(reason_count * CONFIDENCE_DECAY_PER_REASON, MAX_CONFIDENCE_DECAY)
    return max(ZERO, _quantize(base_confidence - decay))


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if not any(fragment in lowered for fragment in SENSITIVE_REFERENCE_FRAGMENTS):
        return value
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _require_payload_public_dataclass(value: object) -> None:
    label = _payload_public_dataclass_label(value)
    _require_hard_flags(label, value)
    for field in fields(value):
        _require_payload_public_field(field.name, getattr(value, field.name))
    if type(value) is MarketResearchJoblessClaimsTrendDigestConfig:
        _require_payload_config(value)
        return
    if type(value) is MarketResearchJoblessClaimsTrendDigestSignal:
        _require_payload_signal(value)
        return
    if type(value) is MarketResearchJoblessClaimsTrendDigestRow:
        _require_payload_row(value)
        return
    if type(value) is MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
        _require_payload_reason_code_count(value)
        return
    if type(value) is MarketResearchJoblessClaimsTrendDigestReport:
        _require_payload_report(value)


def _payload_public_dataclass_label(value: object) -> str:
    if type(value) is MarketResearchJoblessClaimsTrendDigestConfig:
        return "config"
    if type(value) is MarketResearchJoblessClaimsTrendDigestSignal:
        return "signal"
    if type(value) is MarketResearchJoblessClaimsTrendDigestRow:
        return "row"
    if type(value) is MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
        return "reason count"
    if type(value) is MarketResearchJoblessClaimsTrendDigestReport:
        return "report"
    raise ValueError("payload dataclasses must be exact public digest records")


def _payload_public_dataclass_label_or_none(value: object) -> str | None:
    if type(value) is MarketResearchJoblessClaimsTrendDigestConfig:
        return "config"
    if type(value) is MarketResearchJoblessClaimsTrendDigestSignal:
        return "signal"
    if type(value) is MarketResearchJoblessClaimsTrendDigestRow:
        return "row"
    if type(value) is MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
        return "reason count"
    if type(value) is MarketResearchJoblessClaimsTrendDigestReport:
        return "report"
    return None


def _require_payload_public_field(field_name: str, value: object) -> None:
    if field_name == "rows":
        if type(value) is not tuple:
            raise ValueError("rows must be a tuple")
        for item in value:
            if type(item) is not MarketResearchJoblessClaimsTrendDigestRow:
                raise ValueError(
                    "row must be exactly MarketResearchJoblessClaimsTrendDigestRow",
                )
            _require_payload_public_dataclass(item)
        return
    if field_name == "reason_code_counts":
        if type(value) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for item in value:
            if type(item) is not MarketResearchJoblessClaimsTrendDigestReasonCodeCount:
                raise ValueError(
                    "reason count must be exactly "
                    "MarketResearchJoblessClaimsTrendDigestReasonCodeCount",
                )
            _require_payload_public_dataclass(item)
        return
    if type(value) is Decimal:
        _require_payload_six_decimal(field_name, value)
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is datetime:
        _require_payload_utc_datetime(field_name, value)
        return
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be exactly datetime")
    if _payload_public_dataclass_label_or_none(value) is not None:
        _require_payload_public_dataclass(value)
        return
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("payload dataclasses must be exact public digest records")
    if type(value) is tuple:
        for item in value:
            _require_payload_public_field(field_name, item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal for numeric values")
    raise ValueError("payload contains unsupported value")


def _require_payload_config(
    value: MarketResearchJoblessClaimsTrendDigestConfig,
) -> None:
    _require_canonical_string("config_version", value.config_version)
    if (
        value.config_version
        != DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "max_release_age_seconds",
        "min_claims_change",
        "min_claims_change_ratio",
    ):
        _require_positive_decimal(field_name, getattr(value, field_name))
    _require_positive_count_decimal(
        "min_source_family_count",
        value.min_source_family_count,
    )
    for field_name in (
        "max_stale_source_ratio",
        "min_confirmation_ratio",
        "watch_confidence_threshold",
    ):
        _require_ratio_decimal(field_name, getattr(value, field_name))


def _require_payload_signal(
    value: MarketResearchJoblessClaimsTrendDigestSignal,
) -> None:
    for field_name in (
        "condition_id",
        "claims_market_key",
        "release_key",
        "public_signal_reference",
        "signal_config_version",
    ):
        _require_canonical_string(field_name, getattr(value, field_name))
    _require_payload_utc_datetime("released_at", value.released_at)
    for field_name in (
        "prior_claims",
        "current_claims",
        "four_week_average_claims",
    ):
        _require_nonnegative_decimal(field_name, getattr(value, field_name))
    _require_finite_decimal("claims_change", value.claims_change)
    for field_name in (
        "claims_change_ratio",
        "stale_source_ratio",
        "confirmation_ratio",
        "base_confidence",
    ):
        _require_ratio_decimal(field_name, getattr(value, field_name))
    _require_nonnegative_count_decimal(
        "source_family_count",
        value.source_family_count,
    )


def _require_payload_row(value: MarketResearchJoblessClaimsTrendDigestRow) -> None:
    for field_name in (
        "condition_id",
        "claims_market_key",
        "release_key",
        "signal_config_version",
        "redacted_public_signal_reference",
    ):
        _require_canonical_string(field_name, getattr(value, field_name))
    _require_digest_status("digest_status", value.digest_status)
    _require_payload_utc_datetime("released_at", value.released_at)
    _require_nonnegative_decimal("release_age_seconds", value.release_age_seconds)
    for field_name in (
        "prior_claims",
        "current_claims",
        "four_week_average_claims",
    ):
        _require_nonnegative_decimal(field_name, getattr(value, field_name))
    _require_finite_decimal("claims_change", value.claims_change)
    for field_name in (
        "claims_change_ratio",
        "stale_source_ratio",
        "confirmation_ratio",
        "base_confidence",
        "final_confidence",
    ):
        _require_ratio_decimal(field_name, getattr(value, field_name))
    _require_nonnegative_count_decimal(
        "source_family_count",
        value.source_family_count,
    )
    reason_codes = _normalize_reason_codes(value.reason_codes, ROW_REASON_CODE_SEQUENCE)
    _validate_row_status_reason_codes(value.digest_status, reason_codes)


def _require_payload_reason_code_count(
    value: MarketResearchJoblessClaimsTrendDigestReasonCodeCount,
) -> None:
    _require_known_reason_code("reason_code", value.reason_code)
    _require_positive_count_decimal("count", value.count)
    _require_ratio_decimal("signal_ratio", value.signal_ratio)


def _require_payload_report(
    value: MarketResearchJoblessClaimsTrendDigestReport,
) -> None:
    _require_payload_utc_datetime("generated_at", value.generated_at)
    _require_canonical_string("config_version", value.config_version)
    if (
        value.config_version
        != DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_digest_status("digest_status", value.digest_status)
    if value.recommended_next_step != NEXT_STEPS[value.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    for field_name in (
        "signal_count",
        "ready_signal_count",
        "watch_signal_count",
        "blocked_signal_count",
        "stale_release_signal_count",
        "low_claims_change_signal_count",
        "low_claims_change_ratio_signal_count",
        "source_family_gap_signal_count",
        "stale_source_signal_count",
        "confirmation_gap_signal_count",
    ):
        _require_nonnegative_count_decimal(field_name, getattr(value, field_name))
    average_validators = (
        ("average_final_confidence", _require_ratio_decimal),
        ("average_claims_change", _require_finite_decimal),
        ("average_claims_change_ratio", _require_ratio_decimal),
        ("average_confirmation_ratio", _require_ratio_decimal),
    )
    for field_name, validator in average_validators:
        field_value = getattr(value, field_name)
        if field_value is not None:
            validator(field_name, field_value)
    _require_nonnegative_decimal(
        "max_release_age_seconds",
        value.max_release_age_seconds,
    )
    rows = _normalize_rows(value.rows)
    reason_code_counts = _normalize_reason_code_counts(value.reason_code_counts)
    reason_codes = _normalize_reason_codes(value.reason_codes, REASON_CODE_SEQUENCE)
    if (
        value.ready_signal_count + value.watch_signal_count + value.blocked_signal_count
        != value.signal_count
    ):
        raise ValueError("status counts must sum to signal_count")
    if value.signal_count != _decimal_count(rows):
        raise ValueError("signal_count must equal row count")
    _validate_report_status_counts(value)
    _validate_report_reason_signal_counts(value)
    _validate_report_aggregates(value)
    _validate_report_reason_codes(value.digest_status, reason_codes, rows)
    _validate_report_reason_code_counts(reason_code_counts, rows)


def _require_payload_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be normalized to UTC")


def _require_payload_six_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must be six-decimal")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        _require_payload_six_decimal("payload Decimal value", value)
        return f"{value:.6f}"
    if isinstance(value, Decimal):
        raise ValueError("payload Decimal value must be exactly Decimal")
    if type(value) is datetime:
        _require_payload_utc_datetime("payload datetime value", value)
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload datetime value must be exactly datetime")
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("payload contains unsupported value")
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload numeric values must use Decimal")
    raise ValueError("payload contains unsupported value")
