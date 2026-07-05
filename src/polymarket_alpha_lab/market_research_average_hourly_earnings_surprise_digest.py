"""Pure Phase 1 average hourly earnings surprise research reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-average-hourly-earnings-surprise-digest-v0"
)

READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: 0,
    WATCH_STATUS: 1,
    READY_STATUS: 2,
}

REASON_PREFIX = "market_research_average_hourly_earnings_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
MISSING_EVIDENCE_REASON = f"{REASON_PREFIX}missing_evidence"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    MISSING_EVIDENCE_REASON,
    MATERIAL_SURPRISE_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MISSING_EVIDENCE_REASON,
    MATERIAL_SURPRISE_REASON,
    STALE_SIGNAL_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    READY_STATUS: (
        "allow_report_only_market_research_average_hourly_earnings_surprise_digest"
    ),
    WATCH_STATUS: (
        "watch_report_only_market_research_average_hourly_earnings_surprise_digest"
    ),
    BLOCKED_STATUS: (
        "block_report_only_market_research_average_hourly_earnings_surprise_digest"
    ),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_REFERENCE_PREFIXES = (
    "public-",
    "official-",
    "bls-",
    "fred-",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


SENSITIVE_REFERENCE_MARKERS = (
    "://",
    "?",
    "=",
    _join_parts("au", "th"),
    _join_parts("pri", "vate"),
    _join_parts("sec", "ret"),
    _join_parts("sig", "nature"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchAverageHourlyEarningsSurpriseDigestConfig",
    "MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount",
    "MarketResearchAverageHourlyEarningsSurpriseDigestReport",
    "MarketResearchAverageHourlyEarningsSurpriseDigestRow",
    "MarketResearchAverageHourlyEarningsSurpriseDigestSignal",
    "build_market_research_average_hourly_earnings_surprise_digest",
    "market_research_average_hourly_earnings_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchAverageHourlyEarningsSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_ratio: Decimal = Decimal("0.200000")
    max_prior_revision_ratio: Decimal = Decimal("0.500000")
    min_confirmation_ratio: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchAverageHourlyEarningsSurpriseDigestConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchAverageHourlyEarningsSurpriseDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _normalize_positive_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_surprise_ratio",
            "max_prior_revision_ratio",
            "min_confirmation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_surprise_ratio <= ZERO:
            raise ValueError("material_surprise_ratio must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAverageHourlyEarningsSurpriseDigestSignal:
    condition_id: str
    market_slug: str
    release_id: str
    series_id: str
    public_signal_reference: str
    observed_at: datetime
    expected_average_hourly_earnings_growth: Decimal
    actual_average_hourly_earnings_growth: Decimal
    prior_average_hourly_earnings_growth: Decimal
    source_count: Decimal
    confirmation_ratio: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchAverageHourlyEarningsSurpriseDigestSignal does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchAverageHourlyEarningsSurpriseDigestSignal,
            "signal",
        )
        for field_name in (
            "condition_id",
            "market_slug",
            "release_id",
            "series_id",
            "public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_average_hourly_earnings_growth",
            "actual_average_hourly_earnings_growth",
            "prior_average_hourly_earnings_growth",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_growth_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "confirmation_ratio",
            _normalize_ratio_decimal("confirmation_ratio", self.confirmation_ratio),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchAverageHourlyEarningsSurpriseDigestRow:
    condition_id: str
    market_slug: str
    release_id: str
    series_id: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    expected_average_hourly_earnings_growth: Decimal
    actual_average_hourly_earnings_growth: Decimal
    prior_average_hourly_earnings_growth: Decimal
    average_hourly_earnings_surprise_delta: Decimal
    average_hourly_earnings_surprise_ratio: Decimal
    absolute_surprise_ratio: Decimal
    prior_revision_delta: Decimal
    prior_revision_ratio: Decimal
    source_count: Decimal
    confirmation_ratio: Decimal
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchAverageHourlyEarningsSurpriseDigestRow does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchAverageHourlyEarningsSurpriseDigestRow, "row")
        for field_name in (
            "condition_id",
            "market_slug",
            "release_id",
            "series_id",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_average_hourly_earnings_growth",
            "actual_average_hourly_earnings_growth",
            "prior_average_hourly_earnings_growth",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_growth_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_hourly_earnings_surprise_delta",
            "average_hourly_earnings_surprise_ratio",
            "prior_revision_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_age_seconds",
            "absolute_surprise_ratio",
            "prior_revision_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "confirmation_ratio",
            _normalize_ratio_decimal("confirmation_ratio", self.confirmation_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _normalize_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchAverageHourlyEarningsSurpriseDigestReport:
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
    missing_evidence_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_absolute_surprise_ratio: Decimal
    max_absolute_surprise_ratio: Decimal
    average_source_count: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchAverageHourlyEarningsSurpriseDigestReport does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchAverageHourlyEarningsSurpriseDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_AVERAGE_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION
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
            "missing_evidence_count",
            "high_revision_count",
            "confirmation_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_absolute_surprise_ratio",
            "max_absolute_surprise_ratio",
            "average_source_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_average_hourly_earnings_surprise_digest(
    signals: list[MarketResearchAverageHourlyEarningsSurpriseDigestSignal]
    | tuple[MarketResearchAverageHourlyEarningsSurpriseDigestSignal, ...],
    *,
    config: MarketResearchAverageHourlyEarningsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchAverageHourlyEarningsSurpriseDigestReport:
    if type(config) is not MarketResearchAverageHourlyEarningsSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchAverageHourlyEarningsSurpriseDigestConfig",
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
    signal_count = _count_decimal(len(rows))
    reason_code_counts = _expected_reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchAverageHourlyEarningsSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=_status_count(rows, READY_STATUS),
        watch_signal_count=_status_count(rows, WATCH_STATUS),
        blocked_signal_count=_status_count(rows, BLOCKED_STATUS),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        stale_signal_count=_reason_count(rows, STALE_SIGNAL_REASON),
        missing_evidence_count=_reason_count(rows, MISSING_EVIDENCE_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        average_absolute_surprise_ratio=_average_decimal(
            row.absolute_surprise_ratio for row in rows
        ),
        max_absolute_surprise_ratio=_max_decimal(row.absolute_surprise_ratio for row in rows),
        average_source_count=_average_decimal(row.source_count for row in rows),
        max_observed_signal_age_seconds=_max_decimal(row.signal_age_seconds for row in rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_average_hourly_earnings_surprise_digest_payload(
    report: MarketResearchAverageHourlyEarningsSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchAverageHourlyEarningsSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchAverageHourlyEarningsSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _build_row(
    signal: MarketResearchAverageHourlyEarningsSurpriseDigestSignal,
    *,
    config: MarketResearchAverageHourlyEarningsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchAverageHourlyEarningsSurpriseDigestRow:
    signal_age_seconds = _seconds_between(generated_at, signal.observed_at)
    surprise_delta = _quantize_decimal(
        signal.actual_average_hourly_earnings_growth
        - signal.expected_average_hourly_earnings_growth,
    )
    surprise_ratio = _signed_ratio(
        surprise_delta,
        signal.expected_average_hourly_earnings_growth,
    )
    absolute_surprise_ratio = _quantize_decimal(abs(surprise_ratio))
    prior_revision_delta = _quantize_decimal(
        signal.actual_average_hourly_earnings_growth
        - signal.prior_average_hourly_earnings_growth,
    )
    prior_revision_ratio = _quantize_decimal(
        abs(_signed_ratio(prior_revision_delta, signal.prior_average_hourly_earnings_growth)),
    )
    reason_codes = _row_reason_codes(
        signal,
        config=config,
        signal_age_seconds=signal_age_seconds,
        absolute_surprise_ratio=absolute_surprise_ratio,
        prior_revision_ratio=prior_revision_ratio,
    )
    return MarketResearchAverageHourlyEarningsSurpriseDigestRow(
        condition_id=signal.condition_id,
        market_slug=signal.market_slug,
        release_id=signal.release_id,
        series_id=signal.series_id,
        digest_status=_row_status(reason_codes),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        expected_average_hourly_earnings_growth=(
            signal.expected_average_hourly_earnings_growth
        ),
        actual_average_hourly_earnings_growth=signal.actual_average_hourly_earnings_growth,
        prior_average_hourly_earnings_growth=signal.prior_average_hourly_earnings_growth,
        average_hourly_earnings_surprise_delta=surprise_delta,
        average_hourly_earnings_surprise_ratio=surprise_ratio,
        absolute_surprise_ratio=absolute_surprise_ratio,
        prior_revision_delta=prior_revision_delta,
        prior_revision_ratio=prior_revision_ratio,
        source_count=signal.source_count,
        confirmation_ratio=signal.confirmation_ratio,
        redacted_public_signal_reference=_redacted_public_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchAverageHourlyEarningsSurpriseDigestSignal,
    *,
    config: MarketResearchAverageHourlyEarningsSurpriseDigestConfig,
    signal_age_seconds: Decimal,
    absolute_surprise_ratio: Decimal,
    prior_revision_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(MISSING_EVIDENCE_REASON)
    if (
        absolute_surprise_ratio >= config.material_surprise_ratio
        and absolute_surprise_ratio > ZERO
    ):
        reason_codes.append(MATERIAL_SURPRISE_REASON)
    if prior_revision_ratio > config.max_prior_revision_ratio:
        reason_codes.append(HIGH_REVISION_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    if (
        STALE_SIGNAL_REASON in reason_codes
        or MISSING_EVIDENCE_REASON in reason_codes
        or HIGH_REVISION_REASON in reason_codes
    ):
        return BLOCKED_STATUS
    return WATCH_STATUS


def _report_status(
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.digest_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return READY_STATUS


def _expected_reason_code_counts(
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...],
) -> tuple[MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    signal_count = _count_decimal(len(rows))
    counts: list[MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount] = []
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        if reason_code == NO_INPUTS_REASON:
            continue
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                signal_ratio=_ratio(count, signal_count),
            ),
        )
    return tuple(counts)


def _normalize_signals(
    signals: list[MarketResearchAverageHourlyEarningsSurpriseDigestSignal]
    | tuple[MarketResearchAverageHourlyEarningsSurpriseDigestSignal, ...],
) -> tuple[MarketResearchAverageHourlyEarningsSurpriseDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_condition_ids: set[str] = set()
    seen_release_ids: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchAverageHourlyEarningsSurpriseDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchAverageHourlyEarningsSurpriseDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.condition_id in seen_condition_ids:
            raise ValueError("signals must use unique condition_id values")
        if signal.release_id in seen_release_ids:
            raise ValueError("signals must use unique release_id values")
        seen_condition_ids.add(signal.condition_id)
        seen_release_ids.add(signal.release_id)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...],
) -> tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_condition_ids: set[str] = set()
    seen_release_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchAverageHourlyEarningsSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchAverageHourlyEarningsSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
        if row.condition_id in seen_condition_ids:
            raise ValueError("rows must use unique condition_id values")
        if row.release_id in seen_release_ids:
            raise ValueError("rows must use unique release_id values")
        seen_condition_ids.add(row.condition_id)
        seen_release_ids.add(row.release_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for value in reason_code_counts:
        if type(value) is not MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(value.reason_code)
    if reason_code_counts != tuple(sorted(reason_code_counts, key=_reason_count_sort_key)):
        raise ValueError("reason_code_counts must use deterministic ordering")
    return reason_code_counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, sequence)
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
    if sequence == ROW_REASON_CODE_SEQUENCE and READY_REASON in seen_reason_codes:
        if len(seen_reason_codes) != 1:
            raise ValueError("ready reason_code must be exclusive for rows")
    if NO_INPUTS_REASON in seen_reason_codes and len(seen_reason_codes) != 1:
        raise ValueError("no_inputs reason_code must be exclusive")
    canonical = tuple(reason_code for reason_code in sequence if reason_code in seen_reason_codes)
    if reason_codes != canonical:
        raise ValueError("reason_codes must use deterministic ordering")
    return reason_codes


def _validate_row_consistency(
    row: MarketResearchAverageHourlyEarningsSurpriseDigestRow,
) -> None:
    expected_delta = _quantize_decimal(
        row.actual_average_hourly_earnings_growth
        - row.expected_average_hourly_earnings_growth,
    )
    if row.average_hourly_earnings_surprise_delta != expected_delta:
        raise ValueError("average_hourly_earnings_surprise_delta must match growth values")
    expected_ratio = _signed_ratio(
        row.average_hourly_earnings_surprise_delta,
        row.expected_average_hourly_earnings_growth,
    )
    if row.average_hourly_earnings_surprise_ratio != expected_ratio:
        raise ValueError("average_hourly_earnings_surprise_ratio must match surprise delta")
    if row.absolute_surprise_ratio != _quantize_decimal(abs(expected_ratio)):
        raise ValueError("absolute_surprise_ratio must match surprise ratio")
    expected_prior_delta = _quantize_decimal(
        row.actual_average_hourly_earnings_growth
        - row.prior_average_hourly_earnings_growth,
    )
    if row.prior_revision_delta != expected_prior_delta:
        raise ValueError("prior_revision_delta must match actual and prior values")
    expected_prior_ratio = _quantize_decimal(
        abs(_signed_ratio(row.prior_revision_delta, row.prior_average_hourly_earnings_growth)),
    )
    if row.prior_revision_ratio != expected_prior_ratio:
        raise ValueError("prior_revision_ratio must match prior revision delta")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report_consistency(
    report: MarketResearchAverageHourlyEarningsSurpriseDigestReport,
) -> None:
    rows = report.rows
    signal_count = _count_decimal(len(rows))
    if report.signal_count != signal_count:
        raise ValueError("signal_count must match rows")
    expected_counts = (
        ("ready_signal_count", _status_count(rows, READY_STATUS)),
        ("watch_signal_count", _status_count(rows, WATCH_STATUS)),
        ("blocked_signal_count", _status_count(rows, BLOCKED_STATUS)),
        ("material_surprise_count", _reason_count(rows, MATERIAL_SURPRISE_REASON)),
        ("stale_signal_count", _reason_count(rows, STALE_SIGNAL_REASON)),
        ("missing_evidence_count", _reason_count(rows, MISSING_EVIDENCE_REASON)),
        ("high_revision_count", _reason_count(rows, HIGH_REVISION_REASON)),
        ("confirmation_gap_count", _reason_count(rows, CONFIRMATION_GAP_REASON)),
    )
    for field_name, expected in expected_counts:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_absolute_surprise_ratio != _average_decimal(
        row.absolute_surprise_ratio for row in rows
    ):
        raise ValueError("average_absolute_surprise_ratio must match rows")
    if report.max_absolute_surprise_ratio != _max_decimal(
        row.absolute_surprise_ratio for row in rows
    ):
        raise ValueError("max_absolute_surprise_ratio must match rows")
    if report.average_source_count != _average_decimal(row.source_count for row in rows):
        raise ValueError("average_source_count must match rows")
    if report.max_observed_signal_age_seconds != _max_decimal(
        row.signal_age_seconds for row in rows
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    expected_reason_counts = _expected_reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in expected_reason_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _row_sort_key(
    row: MarketResearchAverageHourlyEarningsSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.digest_status],
        -row.absolute_surprise_ratio,
        -row.signal_age_seconds,
        row.release_id,
        row.condition_id,
    )


def _reason_count_sort_key(
    value: MarketResearchAverageHourlyEarningsSurpriseDigestReasonCodeCount,
) -> int:
    return REPORT_REASON_CODE_SEQUENCE.index(value.reason_code)


def _status_count(
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchAverageHourlyEarningsSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_decimal(values: Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _ratio(_sum_decimal(normalized), _count_decimal(len(normalized)))


def _max_decimal(values: Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _signed_ratio(numerator: Decimal, denominator_reference: Decimal) -> Decimal:
    denominator = abs(denominator_reference)
    if denominator == ZERO:
        if numerator == ZERO:
            return ZERO
        if numerator > ZERO:
            return ONE
        return -ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize_decimal(seconds)


def _normalize_growth_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(
    field_name: str,
    value: object,
    sequence: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in sequence:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _redacted_public_reference(value: str) -> str:
    lowered = value.lower()
    if value.startswith(PUBLIC_REFERENCE_PREFIXES) and not any(
        marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS
    ):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    return value
