"""Pure Phase 1 report-only Fed dot plot dispersion digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION",
    "RatesFedDotPlotDispersionDigestConfig",
    "RatesFedDotPlotDispersionObservation",
    "RatesFedDotPlotDispersionDigestRow",
    "RatesFedDotPlotDispersionReasonCodeCount",
    "RatesFedDotPlotDispersionDigestReport",
    "build_market_research_rates_fed_dot_plot_dispersion_digest",
    "market_research_rates_fed_dot_plot_dispersion_digest_payload",
)


DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION = (
    "market-research-rates-fed-dot-plot-dispersion-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
SIGNAL_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANKS = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

EMPTY_REASON = "rates_fed_dot_plot_dispersion_digest_empty"
HIGH_RISK_REASON = "rates_fed_dot_plot_dispersion_high_risk"
WATCH_REASON = "rates_fed_dot_plot_dispersion_watch"
CALM_REASON = "rates_fed_dot_plot_dispersion_calm"
SOURCE_FRESH_REASON = "rates_fed_dot_plot_source_fresh"
SOURCE_STALE_REASON = "rates_fed_dot_plot_source_stale"
THIN_SOURCES_REASON = "rates_fed_dot_plot_thin_sources"
MEDIAN_UPSHIFT_REASON = "rates_fed_dot_plot_median_upshift"
MEDIAN_DOWNSHIFT_REASON = "rates_fed_dot_plot_median_downshift"
MEDIAN_INLINE_REASON = "rates_fed_dot_plot_median_inline"
MEDIAN_REVISION_BLOCKED_REASON = "rates_fed_dot_plot_median_revision_blocked"
MEDIAN_REVISION_WATCH_REASON = "rates_fed_dot_plot_median_revision_watch"
TOTAL_DISPERSION_BLOCKED_REASON = "rates_fed_dot_plot_total_dispersion_blocked"
TOTAL_DISPERSION_WATCH_REASON = "rates_fed_dot_plot_total_dispersion_watch"
TOTAL_DISPERSION_INLINE_REASON = "rates_fed_dot_plot_total_dispersion_inline"
HAWKISH_TAIL_WIDE_REASON = "rates_fed_dot_plot_hawkish_tail_wide"
DOVISH_TAIL_WIDE_REASON = "rates_fed_dot_plot_dovish_tail_wide"
TAIL_BALANCED_REASON = "rates_fed_dot_plot_tail_balanced"
TAIL_SKEW_BLOCKED_REASON = "rates_fed_dot_plot_tail_skew_blocked"
TAIL_SKEW_WATCH_REASON = "rates_fed_dot_plot_tail_skew_watch"
MARKET_EVENT_SENSITIVITY_BLOCKED_REASON = (
    "rates_fed_dot_plot_market_event_sensitivity_blocked"
)
MARKET_EVENT_SENSITIVITY_WATCH_REASON = (
    "rates_fed_dot_plot_market_event_sensitivity_watch"
)
MARKET_EVENT_SENSITIVITY_LOW_REASON = (
    "rates_fed_dot_plot_market_event_sensitivity_low"
)

REASON_CODE_SEQUENCE = (
    HIGH_RISK_REASON,
    WATCH_REASON,
    CALM_REASON,
    SOURCE_FRESH_REASON,
    SOURCE_STALE_REASON,
    THIN_SOURCES_REASON,
    MEDIAN_UPSHIFT_REASON,
    MEDIAN_DOWNSHIFT_REASON,
    MEDIAN_INLINE_REASON,
    MEDIAN_REVISION_BLOCKED_REASON,
    MEDIAN_REVISION_WATCH_REASON,
    TOTAL_DISPERSION_BLOCKED_REASON,
    TOTAL_DISPERSION_WATCH_REASON,
    TOTAL_DISPERSION_INLINE_REASON,
    HAWKISH_TAIL_WIDE_REASON,
    DOVISH_TAIL_WIDE_REASON,
    TAIL_BALANCED_REASON,
    TAIL_SKEW_BLOCKED_REASON,
    TAIL_SKEW_WATCH_REASON,
    MARKET_EVENT_SENSITIVITY_BLOCKED_REASON,
    MARKET_EVENT_SENSITIVITY_WATCH_REASON,
    MARKET_EVENT_SENSITIVITY_LOW_REASON,
    EMPTY_REASON,
)

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: (
        "block_report_only_market_research_rates_fed_dot_plot_dispersion_digest"
    ),
    WATCH_STATUS: "watch_report_only_market_research_rates_fed_dot_plot_dispersion_digest",
    PASS_STATUS: "allow_report_only_market_research_rates_fed_dot_plot_dispersion_digest",
}


@dataclass(frozen=True)
class RatesFedDotPlotDispersionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_total_dispersion_bps: Decimal = Decimal("50.000000")
    blocked_total_dispersion_bps: Decimal = Decimal("100.000000")
    watch_median_revision_bps: Decimal = Decimal("25.000000")
    blocked_median_revision_bps: Decimal = Decimal("50.000000")
    watch_tail_skew_bps: Decimal = Decimal("35.000000")
    blocked_tail_skew_bps: Decimal = Decimal("75.000000")
    watch_market_event_sensitivity: Decimal = Decimal("0.350000")
    blocked_market_event_sensitivity: Decimal = Decimal("0.650000")
    watch_signal_score: Decimal = Decimal("0.350000")
    blocked_signal_score: Decimal = Decimal("0.650000")
    stale_confidence_cap: Decimal = Decimal("0.350000")
    watch_confidence_cap: Decimal = Decimal("0.600000")
    blocked_confidence_cap: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFedDotPlotDispersionDigestConfig:
            raise TypeError(
                "RatesFedDotPlotDispersionDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedDotPlotDispersionDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_source_age_seconds",
            "watch_total_dispersion_bps",
            "blocked_total_dispersion_bps",
            "watch_median_revision_bps",
            "blocked_median_revision_bps",
            "watch_tail_skew_bps",
            "blocked_tail_skew_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_whole_decimal(
                "min_source_count",
                self.min_source_count,
            ),
        )
        for field_name in (
            "watch_market_event_sensitivity",
            "blocked_market_event_sensitivity",
            "watch_signal_score",
            "blocked_signal_score",
            "stale_confidence_cap",
            "watch_confidence_cap",
            "blocked_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedDotPlotDispersionObservation:
    source_id: str
    condition_id: str
    market_slug: str
    meeting_id: str
    central_bank: str
    public_dot_reference: str
    observed_at: datetime
    source_count: Decimal
    median_rate_prior_bps: Decimal
    median_rate_current_bps: Decimal
    hawkish_tail_width_bps: Decimal
    dovish_tail_width_bps: Decimal
    market_event_sensitivity: Decimal
    base_confidence: Decimal
    dot_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFedDotPlotDispersionObservation:
            raise TypeError(
                "RatesFedDotPlotDispersionObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedDotPlotDispersionObservation, "observation")
        for field_name in (
            "source_id",
            "condition_id",
            "market_slug",
            "meeting_id",
            "central_bank",
            "dot_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_dot_reference", self.public_dot_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _normalize_whole_nonnegative_decimal("source_count", self.source_count),
        )
        for field_name in (
            "median_rate_prior_bps",
            "median_rate_current_bps",
            "hawkish_tail_width_bps",
            "dovish_tail_width_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_event_sensitivity", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedDotPlotDispersionDigestRow:
    source_id: str
    condition_id: str
    market_slug: str
    meeting_id: str
    central_bank: str
    signal_status: str
    observed_at: datetime
    source_age_seconds: Decimal
    source_count: Decimal
    median_rate_prior_bps: Decimal
    median_rate_current_bps: Decimal
    median_revision_bps: Decimal
    absolute_median_revision_bps: Decimal
    hawkish_tail_width_bps: Decimal
    dovish_tail_width_bps: Decimal
    total_dispersion_bps: Decimal
    tail_skew_bps: Decimal
    absolute_tail_skew_bps: Decimal
    market_event_sensitivity: Decimal
    signal_score: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    redacted_public_dot_reference: str
    dot_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFedDotPlotDispersionDigestRow:
            raise TypeError(
                "RatesFedDotPlotDispersionDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedDotPlotDispersionDigestRow, "row")
        for field_name in (
            "source_id",
            "condition_id",
            "market_slug",
            "meeting_id",
            "central_bank",
            "dot_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("signal_status", self.signal_status, SIGNAL_STATUSES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "source_count",
            "median_rate_prior_bps",
            "median_rate_current_bps",
            "absolute_median_revision_bps",
            "hawkish_tail_width_bps",
            "dovish_tail_width_bps",
            "total_dispersion_bps",
            "absolute_tail_skew_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "median_revision_bps",
            _normalize_decimal("median_revision_bps", self.median_revision_bps),
        )
        object.__setattr__(
            self,
            "tail_skew_bps",
            _normalize_decimal("tail_skew_bps", self.tail_skew_bps),
        )
        for field_name in (
            "market_event_sensitivity",
            "signal_score",
            "base_confidence",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_dot_reference",
            _require_redacted_reference(
                "redacted_public_dot_reference",
                self.redacted_public_dot_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedDotPlotDispersionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFedDotPlotDispersionReasonCodeCount:
            raise TypeError(
                "RatesFedDotPlotDispersionReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RatesFedDotPlotDispersionReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedDotPlotDispersionDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    thin_source_count: Decimal
    median_revision_alert_count: Decimal
    dispersion_alert_count: Decimal
    hawkish_tail_alert_count: Decimal
    dovish_tail_alert_count: Decimal
    market_event_sensitive_count: Decimal
    max_total_dispersion_bps: Decimal
    average_total_dispersion_bps: Decimal
    max_absolute_median_revision_bps: Decimal
    average_market_event_sensitivity: Decimal
    max_signal_score: Decimal
    average_signal_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RatesFedDotPlotDispersionReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not RatesFedDotPlotDispersionDigestReport:
            raise TypeError(
                "RatesFedDotPlotDispersionDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedDotPlotDispersionDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "thin_source_count",
            "median_revision_alert_count",
            "dispersion_alert_count",
            "hawkish_tail_alert_count",
            "dovish_tail_alert_count",
            "market_event_sensitive_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_dispersion_bps",
            "average_total_dispersion_bps",
            "max_absolute_median_revision_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_market_event_sensitivity",
            "max_signal_score",
            "average_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SIGNAL_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_rates_fed_dot_plot_dispersion_digest(
    observations: Iterable[RatesFedDotPlotDispersionObservation],
    *,
    config: RatesFedDotPlotDispersionDigestConfig,
    generated_at: datetime,
) -> RatesFedDotPlotDispersionDigestReport:
    if type(config) is not RatesFedDotPlotDispersionDigestConfig:
        raise ValueError("config must be exactly RatesFedDotPlotDispersionDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at)
    rows = _sorted_rows(
        tuple(
            _row_from_observation(
                value,
                config=config,
                generated_at=generated_at,
            )
            for value in normalized
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    status = _digest_status(rows)
    return RatesFedDotPlotDispersionDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        median_revision_alert_count=_reason_count(
            rows,
            MEDIAN_REVISION_BLOCKED_REASON,
        )
        + _reason_count(rows, MEDIAN_REVISION_WATCH_REASON),
        dispersion_alert_count=_reason_count(rows, TOTAL_DISPERSION_BLOCKED_REASON)
        + _reason_count(rows, TOTAL_DISPERSION_WATCH_REASON),
        hawkish_tail_alert_count=_reason_count(rows, HAWKISH_TAIL_WIDE_REASON),
        dovish_tail_alert_count=_reason_count(rows, DOVISH_TAIL_WIDE_REASON),
        market_event_sensitive_count=_reason_count(
            rows,
            MARKET_EVENT_SENSITIVITY_BLOCKED_REASON,
        )
        + _reason_count(rows, MARKET_EVENT_SENSITIVITY_WATCH_REASON),
        max_total_dispersion_bps=_max_row_decimal(rows, "total_dispersion_bps"),
        average_total_dispersion_bps=_ratio(
            _sum_decimal(row.total_dispersion_bps for row in rows),
            row_count,
        ),
        max_absolute_median_revision_bps=_max_row_decimal(
            rows,
            "absolute_median_revision_bps",
        ),
        average_market_event_sensitivity=_ratio(
            _sum_decimal(row.market_event_sensitivity for row in rows),
            row_count,
        ),
        max_signal_score=_max_row_decimal(rows, "signal_score"),
        average_signal_score=_ratio(
            _sum_decimal(row.signal_score for row in rows),
            row_count,
        ),
        digest_status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_rates_fed_dot_plot_dispersion_digest_payload(
    report: RatesFedDotPlotDispersionDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesFedDotPlotDispersionDigestReport:
        raise ValueError("report must be exactly RatesFedDotPlotDispersionDigestReport")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a mapping")
    return payload


def _row_from_observation(
    value: RatesFedDotPlotDispersionObservation,
    *,
    config: RatesFedDotPlotDispersionDigestConfig,
    generated_at: datetime,
) -> RatesFedDotPlotDispersionDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    median_revision_bps = _quantize_decimal(
        value.median_rate_current_bps - value.median_rate_prior_bps,
    )
    absolute_median_revision_bps = _abs_decimal(median_revision_bps)
    total_dispersion_bps = _quantize_decimal(
        value.hawkish_tail_width_bps + value.dovish_tail_width_bps,
    )
    tail_skew_bps = _quantize_decimal(
        value.hawkish_tail_width_bps - value.dovish_tail_width_bps,
    )
    absolute_tail_skew_bps = _abs_decimal(tail_skew_bps)
    signal_score = _signal_score(
        absolute_median_revision_bps=absolute_median_revision_bps,
        total_dispersion_bps=total_dispersion_bps,
        absolute_tail_skew_bps=absolute_tail_skew_bps,
        market_event_sensitivity=value.market_event_sensitivity,
        config=config,
    )
    status = _signal_status(
        source_age_seconds=source_age_seconds,
        source_count=value.source_count,
        absolute_median_revision_bps=absolute_median_revision_bps,
        total_dispersion_bps=total_dispersion_bps,
        absolute_tail_skew_bps=absolute_tail_skew_bps,
        market_event_sensitivity=value.market_event_sensitivity,
        signal_score=signal_score,
        config=config,
    )
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return RatesFedDotPlotDispersionDigestRow(
        source_id=value.source_id,
        condition_id=value.condition_id,
        market_slug=value.market_slug,
        meeting_id=value.meeting_id,
        central_bank=value.central_bank,
        signal_status=status,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        source_count=value.source_count,
        median_rate_prior_bps=value.median_rate_prior_bps,
        median_rate_current_bps=value.median_rate_current_bps,
        median_revision_bps=median_revision_bps,
        absolute_median_revision_bps=absolute_median_revision_bps,
        hawkish_tail_width_bps=value.hawkish_tail_width_bps,
        dovish_tail_width_bps=value.dovish_tail_width_bps,
        total_dispersion_bps=total_dispersion_bps,
        tail_skew_bps=tail_skew_bps,
        absolute_tail_skew_bps=absolute_tail_skew_bps,
        market_event_sensitivity=value.market_event_sensitivity,
        signal_score=signal_score,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=_quantize_decimal(min(value.base_confidence, confidence_cap)),
        redacted_public_dot_reference=_redact_reference(value.public_dot_reference),
        dot_config_version=value.dot_config_version,
        reason_codes=_row_reason_codes(
            status=status,
            source_fresh=source_fresh,
            source_count=value.source_count,
            median_revision_bps=median_revision_bps,
            absolute_median_revision_bps=absolute_median_revision_bps,
            total_dispersion_bps=total_dispersion_bps,
            tail_skew_bps=tail_skew_bps,
            absolute_tail_skew_bps=absolute_tail_skew_bps,
            market_event_sensitivity=value.market_event_sensitivity,
            config=config,
        ),
    )


def _signal_score(
    *,
    absolute_median_revision_bps: Decimal,
    total_dispersion_bps: Decimal,
    absolute_tail_skew_bps: Decimal,
    market_event_sensitivity: Decimal,
    config: RatesFedDotPlotDispersionDigestConfig,
) -> Decimal:
    total_dispersion_component = min(
        ONE,
        _ratio(total_dispersion_bps, config.blocked_total_dispersion_bps),
    )
    median_revision_component = min(
        ONE,
        _ratio(absolute_median_revision_bps, config.blocked_median_revision_bps),
    )
    tail_skew_component = min(
        ONE,
        _ratio(absolute_tail_skew_bps, config.blocked_tail_skew_bps),
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            total_dispersion_component * Decimal("0.300000")
            + median_revision_component * Decimal("0.250000")
            + tail_skew_component * Decimal("0.200000")
            + market_event_sensitivity * Decimal("0.250000"),
        )


def _signal_status(
    *,
    source_age_seconds: Decimal,
    source_count: Decimal,
    absolute_median_revision_bps: Decimal,
    total_dispersion_bps: Decimal,
    absolute_tail_skew_bps: Decimal,
    market_event_sensitivity: Decimal,
    signal_score: Decimal,
    config: RatesFedDotPlotDispersionDigestConfig,
) -> str:
    if (
        source_age_seconds > config.max_source_age_seconds
        or source_count < config.min_source_count
        or total_dispersion_bps >= config.blocked_total_dispersion_bps
        or absolute_median_revision_bps >= config.blocked_median_revision_bps
        or absolute_tail_skew_bps >= config.blocked_tail_skew_bps
        or market_event_sensitivity >= config.blocked_market_event_sensitivity
        or signal_score >= config.blocked_signal_score
    ):
        return BLOCKED_STATUS
    if (
        total_dispersion_bps >= config.watch_total_dispersion_bps
        or absolute_median_revision_bps >= config.watch_median_revision_bps
        or absolute_tail_skew_bps >= config.watch_tail_skew_bps
        or market_event_sensitivity >= config.watch_market_event_sensitivity
        or signal_score >= config.watch_signal_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: RatesFedDotPlotDispersionDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == BLOCKED_STATUS:
        caps.append(config.blocked_confidence_cap)
    elif status == WATCH_STATUS:
        caps.append(config.watch_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    *,
    status: str,
    source_fresh: bool,
    source_count: Decimal,
    median_revision_bps: Decimal,
    absolute_median_revision_bps: Decimal,
    total_dispersion_bps: Decimal,
    tail_skew_bps: Decimal,
    absolute_tail_skew_bps: Decimal,
    market_event_sensitivity: Decimal,
    config: RatesFedDotPlotDispersionDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == BLOCKED_STATUS:
        reason_codes.append(HIGH_RISK_REASON)
    elif status == WATCH_STATUS:
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(CALM_REASON)
    reason_codes.append(SOURCE_FRESH_REASON if source_fresh else SOURCE_STALE_REASON)
    if source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if median_revision_bps > ZERO:
        reason_codes.append(MEDIAN_UPSHIFT_REASON)
    elif median_revision_bps < ZERO:
        reason_codes.append(MEDIAN_DOWNSHIFT_REASON)
    else:
        reason_codes.append(MEDIAN_INLINE_REASON)
    if absolute_median_revision_bps >= config.blocked_median_revision_bps:
        reason_codes.append(MEDIAN_REVISION_BLOCKED_REASON)
    elif absolute_median_revision_bps >= config.watch_median_revision_bps:
        reason_codes.append(MEDIAN_REVISION_WATCH_REASON)
    if total_dispersion_bps >= config.blocked_total_dispersion_bps:
        reason_codes.append(TOTAL_DISPERSION_BLOCKED_REASON)
    elif total_dispersion_bps >= config.watch_total_dispersion_bps:
        reason_codes.append(TOTAL_DISPERSION_WATCH_REASON)
    else:
        reason_codes.append(TOTAL_DISPERSION_INLINE_REASON)
    if absolute_tail_skew_bps >= config.watch_tail_skew_bps:
        if tail_skew_bps > ZERO:
            reason_codes.append(HAWKISH_TAIL_WIDE_REASON)
        else:
            reason_codes.append(DOVISH_TAIL_WIDE_REASON)
        if absolute_tail_skew_bps >= config.blocked_tail_skew_bps:
            reason_codes.append(TAIL_SKEW_BLOCKED_REASON)
        else:
            reason_codes.append(TAIL_SKEW_WATCH_REASON)
    else:
        reason_codes.append(TAIL_BALANCED_REASON)
    if market_event_sensitivity >= config.blocked_market_event_sensitivity:
        reason_codes.append(MARKET_EVENT_SENSITIVITY_BLOCKED_REASON)
    elif market_event_sensitivity >= config.watch_market_event_sensitivity:
        reason_codes.append(MARKET_EVENT_SENSITIVITY_WATCH_REASON)
    else:
        reason_codes.append(MARKET_EVENT_SENSITIVITY_LOW_REASON)
    return _normalize_reason_codes(reason_codes)


def _report_reason_codes(
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes, allow_repeated=True)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...],
) -> tuple[RatesFedDotPlotDispersionReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            RatesFedDotPlotDispersionReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RatesFedDotPlotDispersionReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[RatesFedDotPlotDispersionObservation],
    generated_at: datetime,
) -> tuple[RatesFedDotPlotDispersionObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for value in normalized:
        if type(value) is not RatesFedDotPlotDispersionObservation:
            raise ValueError(
                "observations must contain RatesFedDotPlotDispersionObservation values",
            )
        _require_hard_flags(value)
        if value.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id")
        seen_source_ids.add(value.source_id)
        if value.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
    return normalized


def _normalize_rows(
    rows: Iterable[RatesFedDotPlotDispersionDigestRow],
) -> tuple[RatesFedDotPlotDispersionDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not RatesFedDotPlotDispersionDigestRow:
            raise ValueError("rows must contain RatesFedDotPlotDispersionDigestRow")
        _require_hard_flags(row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id")
        seen_source_ids.add(row.source_id)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must use canonical order")
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[RatesFedDotPlotDispersionReasonCodeCount],
) -> tuple[RatesFedDotPlotDispersionReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not RatesFedDotPlotDispersionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "RatesFedDotPlotDispersionReasonCodeCount",
            )
        _require_hard_flags(value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not repeat reason_code")
        seen_codes.add(value.reason_code)
    expected = _reason_count_sequence(normalized)
    if normalized != expected:
        raise ValueError("reason_code_counts must use canonical order")
    return normalized


def _reason_count_sequence(
    values: tuple[RatesFedDotPlotDispersionReasonCodeCount, ...],
) -> tuple[RatesFedDotPlotDispersionReasonCodeCount, ...]:
    by_reason = {value.reason_code: value for value in values}
    return tuple(
        by_reason[reason_code]
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in by_reason
    )


def _validate_config(config: RatesFedDotPlotDispersionDigestConfig) -> None:
    checks = (
        (
            "watch_total_dispersion_bps",
            config.watch_total_dispersion_bps,
            config.blocked_total_dispersion_bps,
        ),
        (
            "watch_median_revision_bps",
            config.watch_median_revision_bps,
            config.blocked_median_revision_bps,
        ),
        (
            "watch_tail_skew_bps",
            config.watch_tail_skew_bps,
            config.blocked_tail_skew_bps,
        ),
        (
            "watch_market_event_sensitivity",
            config.watch_market_event_sensitivity,
            config.blocked_market_event_sensitivity,
        ),
        ("watch_signal_score", config.watch_signal_score, config.blocked_signal_score),
    )
    for field_name, watch_value, blocked_value in checks:
        if watch_value > blocked_value:
            raise ValueError(f"{field_name} must not exceed blocked threshold")


def _validate_row(row: RatesFedDotPlotDispersionDigestRow) -> None:
    if row.median_revision_bps != _quantize_decimal(
        row.median_rate_current_bps - row.median_rate_prior_bps,
    ):
        raise ValueError("median_revision_bps must match median rates")
    if row.absolute_median_revision_bps != _abs_decimal(row.median_revision_bps):
        raise ValueError("absolute_median_revision_bps must match median_revision_bps")
    if row.total_dispersion_bps != _quantize_decimal(
        row.hawkish_tail_width_bps + row.dovish_tail_width_bps,
    ):
        raise ValueError("total_dispersion_bps must match tail widths")
    if row.tail_skew_bps != _quantize_decimal(
        row.hawkish_tail_width_bps - row.dovish_tail_width_bps,
    ):
        raise ValueError("tail_skew_bps must match tail widths")
    if row.absolute_tail_skew_bps != _abs_decimal(row.tail_skew_bps):
        raise ValueError("absolute_tail_skew_bps must match tail_skew_bps")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    _validate_status_reasons(row)


def _validate_status_reasons(row: RatesFedDotPlotDispersionDigestRow) -> None:
    status_reasons = {
        BLOCKED_STATUS: HIGH_RISK_REASON,
        WATCH_STATUS: WATCH_REASON,
        PASS_STATUS: CALM_REASON,
    }
    present = tuple(
        reason for reason in status_reasons.values() if reason in row.reason_codes
    )
    if present != (status_reasons[row.signal_status],):
        raise ValueError("reason_codes must match row state")


def _validate_report(report: RatesFedDotPlotDispersionDigestReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.thin_source_count != _reason_count(report.rows, THIN_SOURCES_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.median_revision_alert_count != (
        _reason_count(report.rows, MEDIAN_REVISION_BLOCKED_REASON)
        + _reason_count(report.rows, MEDIAN_REVISION_WATCH_REASON)
    ):
        raise ValueError("median_revision_alert_count must match rows")
    if report.dispersion_alert_count != (
        _reason_count(report.rows, TOTAL_DISPERSION_BLOCKED_REASON)
        + _reason_count(report.rows, TOTAL_DISPERSION_WATCH_REASON)
    ):
        raise ValueError("dispersion_alert_count must match rows")
    if report.hawkish_tail_alert_count != _reason_count(
        report.rows,
        HAWKISH_TAIL_WIDE_REASON,
    ):
        raise ValueError("hawkish_tail_alert_count must match rows")
    if report.dovish_tail_alert_count != _reason_count(
        report.rows,
        DOVISH_TAIL_WIDE_REASON,
    ):
        raise ValueError("dovish_tail_alert_count must match rows")
    if report.market_event_sensitive_count != (
        _reason_count(report.rows, MARKET_EVENT_SENSITIVITY_BLOCKED_REASON)
        + _reason_count(report.rows, MARKET_EVENT_SENSITIVITY_WATCH_REASON)
    ):
        raise ValueError("market_event_sensitive_count must match rows")
    if report.max_total_dispersion_bps != _max_row_decimal(
        report.rows,
        "total_dispersion_bps",
    ):
        raise ValueError("max_total_dispersion_bps must match rows")
    if report.average_total_dispersion_bps != _ratio(
        _sum_decimal(row.total_dispersion_bps for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_total_dispersion_bps must match rows")
    if report.max_absolute_median_revision_bps != _max_row_decimal(
        report.rows,
        "absolute_median_revision_bps",
    ):
        raise ValueError("max_absolute_median_revision_bps must match rows")
    if report.average_market_event_sensitivity != _ratio(
        _sum_decimal(row.market_event_sensitivity for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_market_event_sensitivity must match rows")
    if report.max_signal_score != _max_row_decimal(report.rows, "signal_score"):
        raise ValueError("max_signal_score must match rows")
    if report.average_signal_score != _ratio(
        _sum_decimal(row.signal_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_signal_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")


def _digest_status(rows: tuple[RatesFedDotPlotDispersionDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.signal_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.signal_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.signal_status == status))


def _reason_count(
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at cannot be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
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
        return value.quantize(QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize_decimal(abs(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    reason_codes: Iterable[str],
    *,
    allow_repeated: bool = False,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    raw_reason_codes = tuple(reason_codes)
    seen_codes: set[str] = set()
    for reason_code in raw_reason_codes:
        _require_reason_code("reason_code", reason_code)
        seen_codes.add(reason_code)
    if not seen_codes:
        raise ValueError("reason_codes must not be empty")
    normalized = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in seen_codes
    )
    if not allow_repeated and raw_reason_codes != normalized:
        raise ValueError("reason_codes must use canonical order")
    return normalized


def _redact_reference(value: str) -> str:
    if _is_reference_safe(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_reference_safe(value: str) -> bool:
    return "://" not in value and "?" not in value


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if not _is_reference_safe(value) and not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be redacted")
    if value.startswith("sha256:") and len(value) != 19:
        raise ValueError(f"{field_name} must be a short sha256 redaction")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _validate_payload_dataclass(value: object) -> None:
    if type(value) is RatesFedDotPlotDispersionDigestConfig:
        _validate_payload_fields(value)
        _validate_config_payload(value)
        return
    if type(value) is RatesFedDotPlotDispersionObservation:
        _validate_payload_fields(value)
        _validate_observation_payload(value)
        return
    if type(value) is RatesFedDotPlotDispersionDigestRow:
        _validate_payload_fields(value)
        _validate_row_payload(value)
        return
    if type(value) is RatesFedDotPlotDispersionReasonCodeCount:
        _validate_payload_fields(value)
        _validate_reason_code_count_payload(value)
        return
    if type(value) is RatesFedDotPlotDispersionDigestReport:
        _validate_payload_fields(value)
        _validate_report_payload(value)
        return
    raise ValueError("payload value must be a known public dataclass")


def _validate_payload_fields(value: object) -> None:
    for field in fields(value):
        _validate_payload_member(field.name, getattr(value, field.name))


def _validate_payload_member(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _validate_payload_dataclass(value)
        return
    if type(value) is tuple:
        for item in value:
            _validate_payload_member(field_name, item)
        return
    if type(value) is Decimal:
        _require_payload_decimal(field_name, value)
        return
    if type(value) is datetime:
        _require_payload_datetime(field_name, value)
        return
    if type(value) in (bool, str):
        return
    if type(value) in (dict, list, set):
        raise ValueError(f"{field_name} must not be a raw container")
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    raise ValueError(f"{field_name} is not JSON serializable")


def _validate_config_payload(
    config: RatesFedDotPlotDispersionDigestConfig,
) -> None:
    _require_exact_type(config, RatesFedDotPlotDispersionDigestConfig, "config")
    _require_canonical_string("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "max_source_age_seconds",
        "watch_total_dispersion_bps",
        "blocked_total_dispersion_bps",
        "watch_median_revision_bps",
        "blocked_median_revision_bps",
        "watch_tail_skew_bps",
        "blocked_tail_skew_bps",
    ):
        _normalize_positive_decimal(field_name, getattr(config, field_name))
    _normalize_positive_whole_decimal("min_source_count", config.min_source_count)
    for field_name in (
        "watch_market_event_sensitivity",
        "blocked_market_event_sensitivity",
        "watch_signal_score",
        "blocked_signal_score",
        "stale_confidence_cap",
        "watch_confidence_cap",
        "blocked_confidence_cap",
    ):
        _normalize_probability(field_name, getattr(config, field_name))
    _validate_config(config)
    _require_hard_flags(config)


def _validate_observation_payload(
    observation: RatesFedDotPlotDispersionObservation,
) -> None:
    _require_exact_type(
        observation,
        RatesFedDotPlotDispersionObservation,
        "observation",
    )
    for field_name in (
        "source_id",
        "condition_id",
        "market_slug",
        "meeting_id",
        "central_bank",
        "dot_config_version",
    ):
        _require_canonical_string(field_name, getattr(observation, field_name))
    _require_canonical_string(
        "public_dot_reference",
        observation.public_dot_reference,
    )
    _require_payload_datetime("observed_at", observation.observed_at)
    _normalize_whole_nonnegative_decimal("source_count", observation.source_count)
    for field_name in (
        "median_rate_prior_bps",
        "median_rate_current_bps",
        "hawkish_tail_width_bps",
        "dovish_tail_width_bps",
    ):
        _normalize_nonnegative_decimal(field_name, getattr(observation, field_name))
    for field_name in ("market_event_sensitivity", "base_confidence"):
        _normalize_probability(field_name, getattr(observation, field_name))
    _require_hard_flags(observation)


def _validate_row_payload(row: RatesFedDotPlotDispersionDigestRow) -> None:
    _require_exact_type(row, RatesFedDotPlotDispersionDigestRow, "row")
    for field_name in (
        "source_id",
        "condition_id",
        "market_slug",
        "meeting_id",
        "central_bank",
        "dot_config_version",
    ):
        _require_canonical_string(field_name, getattr(row, field_name))
    _require_member("signal_status", row.signal_status, SIGNAL_STATUSES)
    _require_payload_datetime("observed_at", row.observed_at)
    for field_name in (
        "source_age_seconds",
        "source_count",
        "median_rate_prior_bps",
        "median_rate_current_bps",
        "absolute_median_revision_bps",
        "hawkish_tail_width_bps",
        "dovish_tail_width_bps",
        "total_dispersion_bps",
        "absolute_tail_skew_bps",
    ):
        _normalize_nonnegative_decimal(field_name, getattr(row, field_name))
    _normalize_decimal("median_revision_bps", row.median_revision_bps)
    _normalize_decimal("tail_skew_bps", row.tail_skew_bps)
    for field_name in (
        "market_event_sensitivity",
        "signal_score",
        "base_confidence",
        "confidence_cap",
        "capped_confidence",
    ):
        _normalize_probability(field_name, getattr(row, field_name))
    _require_redacted_reference(
        "redacted_public_dot_reference",
        row.redacted_public_dot_reference,
    )
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical order")
    _validate_row(row)
    _require_hard_flags(row)


def _validate_reason_code_count_payload(
    reason_count: RatesFedDotPlotDispersionReasonCodeCount,
) -> None:
    _require_exact_type(
        reason_count,
        RatesFedDotPlotDispersionReasonCodeCount,
        "reason code count",
    )
    _require_reason_code("reason_code", reason_count.reason_code)
    _normalize_positive_whole_decimal("count", reason_count.count)
    _normalize_probability("row_ratio", reason_count.row_ratio)
    _require_hard_flags(reason_count)


def _validate_report_payload(
    report: RatesFedDotPlotDispersionDigestReport,
) -> None:
    _require_exact_type(report, RatesFedDotPlotDispersionDigestReport, "report")
    _require_payload_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_RATES_FED_DOT_PLOT_DISPERSION_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "input_count",
        "row_count",
        "blocked_count",
        "watch_count",
        "pass_count",
        "stale_source_count",
        "thin_source_count",
        "median_revision_alert_count",
        "dispersion_alert_count",
        "hawkish_tail_alert_count",
        "dovish_tail_alert_count",
        "market_event_sensitive_count",
    ):
        _normalize_whole_nonnegative_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "max_total_dispersion_bps",
        "average_total_dispersion_bps",
        "max_absolute_median_revision_bps",
    ):
        _normalize_nonnegative_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "average_market_event_sensitivity",
        "max_signal_score",
        "average_signal_score",
    ):
        _normalize_probability(field_name, getattr(report, field_name))
    _require_member("digest_status", report.digest_status, SIGNAL_STATUSES)
    _require_canonical_string("recommended_next_step", report.recommended_next_step)
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must use canonical order")
    if report.reason_codes != _normalize_reason_codes(report.reason_codes):
        raise ValueError("reason_codes must use canonical order")
    if report.reason_code_counts != _normalize_reason_code_counts(
        report.reason_code_counts,
    ):
        raise ValueError("reason_code_counts must use canonical order")
    _validate_report(report)
    _require_hard_flags(report)


def _require_payload_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimals")


def _require_payload_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.tzinfo is not UTC or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC")


def _sorted_rows(
    rows: tuple[RatesFedDotPlotDispersionDigestRow, ...],
) -> tuple[RatesFedDotPlotDispersionDigestRow, ...]:
    decorated = tuple((_row_sort_tuple(row), row) for row in rows)
    return tuple(item[1] for item in sorted(decorated))


def _row_sort_tuple(
    row: RatesFedDotPlotDispersionDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANKS[row.signal_status],
        -row.signal_score,
        row.market_slug,
        row.source_id,
    )


def _payload_value(value: object, field_name: str = "payload value") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        _validate_payload_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name), field.name)
            for field in fields(value)
        }
    if type(value) is Decimal:
        _require_payload_decimal(field_name, value)
        return f"{value:.6f}"
    if type(value) is datetime:
        _require_payload_datetime(field_name, value)
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item, field_name) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("payload value must not be a raw container")
    if type(value) in (bool, str):
        return value
    if type(value) is int:
        raise ValueError("payload value must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    raise ValueError("payload value is not JSON serializable")
