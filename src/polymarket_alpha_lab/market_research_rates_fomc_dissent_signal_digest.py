"""Pure report-only FOMC dissent and dot-plot signal digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_FOMC_DISSENT_SIGNAL_DIGEST_CONFIG_VERSION",
    "RatesFOMCDissentSignalDigestConfig",
    "RatesFOMCDissentSignalObservation",
    "RatesFOMCDissentSignalDigestRow",
    "RatesFOMCDissentSignalReasonCodeCount",
    "RatesFOMCDissentSignalDigestReport",
    "build_market_research_rates_fomc_dissent_signal_digest",
    "market_research_rates_fomc_dissent_signal_digest_payload",
)


DEFAULT_MARKET_RESEARCH_RATES_FOMC_DISSENT_SIGNAL_DIGEST_CONFIG_VERSION = (
    "market-research-rates-fomc-dissent-signal-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DISSENT_SCORE_DENOMINATOR = Decimal("2.000000")
DOT_SHIFT_SCORE_DENOMINATOR = Decimal("50.000000")
DOT_DISPERSION_SCORE_DENOMINATOR = Decimal("100.000000")

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
SIGNAL_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_market_research_rates_fomc_dissent_signal_digest",
    WATCH_STATUS: "watch_report_only_market_research_rates_fomc_dissent_signal_digest",
    PASS_STATUS: "allow_report_only_market_research_rates_fomc_dissent_signal_digest",
}


@dataclass(frozen=True)
class RatesFOMCDissentSignalDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_FOMC_DISSENT_SIGNAL_DIGEST_CONFIG_VERSION
    )
    watch_dissent_count: Decimal = Decimal("1.000000")
    blocked_dissent_count: Decimal = Decimal("2.000000")
    watch_median_dot_shift_bps: Decimal = Decimal("25.000000")
    blocked_median_dot_shift_bps: Decimal = Decimal("50.000000")
    watch_dot_dispersion_bps: Decimal = Decimal("50.000000")
    blocked_dot_dispersion_bps: Decimal = Decimal("100.000000")
    watch_signal_score: Decimal = Decimal("0.350000")
    blocked_signal_score: Decimal = Decimal("0.650000")
    max_source_age_seconds: Decimal = Decimal("600.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    watch_confidence_cap: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFOMCDissentSignalDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FOMC_DISSENT_SIGNAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_dissent_count", "blocked_dissent_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_median_dot_shift_bps",
            "blocked_median_dot_shift_bps",
            "watch_dot_dispersion_bps",
            "blocked_dot_dispersion_bps",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_signal_score",
            "blocked_signal_score",
            "stale_confidence_cap",
            "watch_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_dissent_count > self.blocked_dissent_count:
            raise ValueError("watch_dissent_count must not exceed blocked_dissent_count")
        if self.watch_median_dot_shift_bps > self.blocked_median_dot_shift_bps:
            raise ValueError(
                "watch_median_dot_shift_bps must not exceed "
                "blocked_median_dot_shift_bps",
            )
        if self.watch_dot_dispersion_bps > self.blocked_dot_dispersion_bps:
            raise ValueError(
                "watch_dot_dispersion_bps must not exceed blocked_dot_dispersion_bps",
            )
        if self.watch_signal_score > self.blocked_signal_score:
            raise ValueError("watch_signal_score must not exceed blocked_signal_score")
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFOMCDissentSignalObservation:
    source_id: str
    market_slug: str
    meeting_id: str
    dissent_count: Decimal
    hawkish_dissent_count: Decimal
    dovish_dissent_count: Decimal
    median_dot_shift_bps: Decimal
    dot_dispersion_bps: Decimal
    committee_disagreement_score: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFOMCDissentSignalObservation, "observation")
        for field_name in ("source_id", "market_slug", "meeting_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "dissent_count",
            "hawkish_dissent_count",
            "dovish_dissent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "median_dot_shift_bps",
            _normalize_decimal("median_dot_shift_bps", self.median_dot_shift_bps),
        )
        object.__setattr__(
            self,
            "dot_dispersion_bps",
            _normalize_nonnegative_decimal("dot_dispersion_bps", self.dot_dispersion_bps),
        )
        object.__setattr__(
            self,
            "committee_disagreement_score",
            _normalize_probability(
                "committee_disagreement_score",
                self.committee_disagreement_score,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_confidence",
            _normalize_probability("base_confidence", self.base_confidence),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _validate_dissent_balance(
            dissent_count=self.dissent_count,
            hawkish_dissent_count=self.hawkish_dissent_count,
            dovish_dissent_count=self.dovish_dissent_count,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFOMCDissentSignalDigestRow:
    source_id: str
    market_slug: str
    meeting_id: str
    dissent_count: Decimal
    hawkish_dissent_count: Decimal
    dovish_dissent_count: Decimal
    median_dot_shift_bps: Decimal
    absolute_median_dot_shift_bps: Decimal
    dot_dispersion_bps: Decimal
    committee_disagreement_score: Decimal
    signal_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    signal_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFOMCDissentSignalDigestRow, "row")
        for field_name in ("source_id", "market_slug", "meeting_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "dissent_count",
            "hawkish_dissent_count",
            "dovish_dissent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "median_dot_shift_bps",
            _normalize_decimal("median_dot_shift_bps", self.median_dot_shift_bps),
        )
        for field_name in (
            "absolute_median_dot_shift_bps",
            "dot_dispersion_bps",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "committee_disagreement_score",
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
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("signal_status", self.signal_status, SIGNAL_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFOMCDissentSignalReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RatesFOMCDissentSignalReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFOMCDissentSignalDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_signal_count: Decimal
    watch_signal_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    hawkish_dissent_signal_count: Decimal
    dovish_dissent_signal_count: Decimal
    dot_plot_upshift_count: Decimal
    dot_plot_downshift_count: Decimal
    max_signal_score: Decimal
    average_signal_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesFOMCDissentSignalDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RatesFOMCDissentSignalReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFOMCDissentSignalDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FOMC_DISSENT_SIGNAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_signal_count",
            "watch_signal_count",
            "pass_count",
            "stale_source_count",
            "hawkish_dissent_signal_count",
            "dovish_dissent_signal_count",
            "dot_plot_upshift_count",
            "dot_plot_downshift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_signal_score", "average_signal_score"):
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


def build_market_research_rates_fomc_dissent_signal_digest(
    inputs: Iterable[RatesFOMCDissentSignalObservation],
    *,
    config: RatesFOMCDissentSignalDigestConfig,
    generated_at: datetime,
) -> RatesFOMCDissentSignalDigestReport:
    if type(config) is not RatesFOMCDissentSignalDigestConfig:
        raise ValueError("config must be exactly RatesFOMCDissentSignalDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    status = _digest_status(rows)
    return RatesFOMCDissentSignalDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_signal_count=_status_count(rows, BLOCKED_STATUS),
        watch_signal_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "rates_fomc_source_stale"),
        hawkish_dissent_signal_count=_reason_count(
            rows,
            "rates_fomc_dissent_hawkish",
        ),
        dovish_dissent_signal_count=_reason_count(rows, "rates_fomc_dissent_dovish"),
        dot_plot_upshift_count=_reason_count(rows, "rates_fomc_dot_plot_upshift"),
        dot_plot_downshift_count=_reason_count(rows, "rates_fomc_dot_plot_downshift"),
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


def market_research_rates_fomc_dissent_signal_digest_payload(
    report: RatesFOMCDissentSignalDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesFOMCDissentSignalDigestReport:
        raise ValueError("report must be exactly RatesFOMCDissentSignalDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: RatesFOMCDissentSignalObservation,
    *,
    config: RatesFOMCDissentSignalDigestConfig,
    generated_at: datetime,
) -> RatesFOMCDissentSignalDigestRow:
    absolute_median_dot_shift_bps = _abs_decimal(value.median_dot_shift_bps)
    signal_score = _signal_score(
        dissent_count=value.dissent_count,
        absolute_median_dot_shift_bps=absolute_median_dot_shift_bps,
        dot_dispersion_bps=value.dot_dispersion_bps,
        committee_disagreement_score=value.committee_disagreement_score,
    )
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _signal_status(
        dissent_count=value.dissent_count,
        absolute_median_dot_shift_bps=absolute_median_dot_shift_bps,
        dot_dispersion_bps=value.dot_dispersion_bps,
        signal_score=signal_score,
        config=config,
    )
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return RatesFOMCDissentSignalDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        meeting_id=value.meeting_id,
        dissent_count=value.dissent_count,
        hawkish_dissent_count=value.hawkish_dissent_count,
        dovish_dissent_count=value.dovish_dissent_count,
        median_dot_shift_bps=value.median_dot_shift_bps,
        absolute_median_dot_shift_bps=absolute_median_dot_shift_bps,
        dot_dispersion_bps=value.dot_dispersion_bps,
        committee_disagreement_score=value.committee_disagreement_score,
        signal_score=signal_score,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=_quantize_decimal(min(value.base_confidence, confidence_cap)),
        signal_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            dissent_count=value.dissent_count,
            hawkish_dissent_count=value.hawkish_dissent_count,
            dovish_dissent_count=value.dovish_dissent_count,
            median_dot_shift_bps=value.median_dot_shift_bps,
            absolute_median_dot_shift_bps=absolute_median_dot_shift_bps,
            dot_dispersion_bps=value.dot_dispersion_bps,
            committee_disagreement_score=value.committee_disagreement_score,
            status=status,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _signal_score(
    *,
    dissent_count: Decimal,
    absolute_median_dot_shift_bps: Decimal,
    dot_dispersion_bps: Decimal,
    committee_disagreement_score: Decimal,
) -> Decimal:
    dissent_component = min(ONE, _ratio(dissent_count, DISSENT_SCORE_DENOMINATOR))
    dot_shift_component = min(
        ONE,
        _ratio(absolute_median_dot_shift_bps, DOT_SHIFT_SCORE_DENOMINATOR),
    )
    dot_dispersion_component = min(
        ONE,
        _ratio(dot_dispersion_bps, DOT_DISPERSION_SCORE_DENOMINATOR),
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            dissent_component * Decimal("0.350000")
            + dot_shift_component * Decimal("0.250000")
            + dot_dispersion_component * Decimal("0.250000")
            + committee_disagreement_score * Decimal("0.150000"),
        )


def _signal_status(
    *,
    dissent_count: Decimal,
    absolute_median_dot_shift_bps: Decimal,
    dot_dispersion_bps: Decimal,
    signal_score: Decimal,
    config: RatesFOMCDissentSignalDigestConfig,
) -> str:
    if (
        dissent_count >= config.blocked_dissent_count
        or absolute_median_dot_shift_bps >= config.blocked_median_dot_shift_bps
        or dot_dispersion_bps >= config.blocked_dot_dispersion_bps
        or signal_score >= config.blocked_signal_score
    ):
        return BLOCKED_STATUS
    if (
        dissent_count >= config.watch_dissent_count
        or absolute_median_dot_shift_bps >= config.watch_median_dot_shift_bps
        or dot_dispersion_bps >= config.watch_dot_dispersion_bps
        or signal_score >= config.watch_signal_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: RatesFOMCDissentSignalDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == WATCH_STATUS:
        caps.append(config.watch_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    dissent_count: Decimal,
    hawkish_dissent_count: Decimal,
    dovish_dissent_count: Decimal,
    median_dot_shift_bps: Decimal,
    absolute_median_dot_shift_bps: Decimal,
    dot_dispersion_bps: Decimal,
    committee_disagreement_score: Decimal,
    status: str,
    source_fresh: bool,
    config: RatesFOMCDissentSignalDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("rates_fomc_dissent_signal_high_risk")
    elif status == WATCH_STATUS:
        reason_codes.append("rates_fomc_dissent_signal_watch")
    else:
        reason_codes.append("rates_fomc_dissent_signal_calm")
    reason_codes.append(
        "rates_fomc_source_fresh" if source_fresh else "rates_fomc_source_stale",
    )
    if dissent_count == ZERO:
        reason_codes.append("rates_fomc_dissent_none")
    elif hawkish_dissent_count > dovish_dissent_count:
        reason_codes.append("rates_fomc_dissent_hawkish")
    elif dovish_dissent_count > hawkish_dissent_count:
        reason_codes.append("rates_fomc_dissent_dovish")
    else:
        reason_codes.append("rates_fomc_dissent_balanced")
    if median_dot_shift_bps > ZERO:
        reason_codes.append("rates_fomc_dot_plot_upshift")
    elif median_dot_shift_bps < ZERO:
        reason_codes.append("rates_fomc_dot_plot_downshift")
    else:
        reason_codes.append("rates_fomc_dot_plot_inline")
    if dissent_count >= config.blocked_dissent_count:
        reason_codes.append("rates_fomc_dissent_count_blocked")
    elif dissent_count >= config.watch_dissent_count:
        reason_codes.append("rates_fomc_dissent_count_watch")
    if absolute_median_dot_shift_bps >= config.blocked_median_dot_shift_bps:
        reason_codes.append("rates_fomc_dot_shift_blocked")
    elif absolute_median_dot_shift_bps >= config.watch_median_dot_shift_bps:
        reason_codes.append("rates_fomc_dot_shift_watch")
    if dot_dispersion_bps >= config.blocked_dot_dispersion_bps:
        reason_codes.append("rates_fomc_dot_dispersion_blocked")
    elif dot_dispersion_bps >= config.watch_dot_dispersion_bps:
        reason_codes.append("rates_fomc_dot_dispersion_watch")
    if committee_disagreement_score >= Decimal("0.750000"):
        reason_codes.append("rates_fomc_committee_disagreement_high")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[RatesFOMCDissentSignalDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("rates_fomc_dissent_signal_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesFOMCDissentSignalDigestRow, ...],
) -> tuple[RatesFOMCDissentSignalReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("rates_fomc_dissent_signal_digest_empty",):
        return (
            RatesFOMCDissentSignalReasonCodeCount(
                reason_code="rates_fomc_dissent_signal_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RatesFOMCDissentSignalReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[RatesFOMCDissentSignalObservation],
) -> tuple[RatesFOMCDissentSignalObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not RatesFOMCDissentSignalObservation:
            raise ValueError("inputs must contain RatesFOMCDissentSignalObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[RatesFOMCDissentSignalDigestRow],
) -> tuple[RatesFOMCDissentSignalDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not RatesFOMCDissentSignalDigestRow:
            raise ValueError("rows must contain RatesFOMCDissentSignalDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[RatesFOMCDissentSignalReasonCodeCount],
) -> tuple[RatesFOMCDissentSignalReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not RatesFOMCDissentSignalReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain RatesFOMCDissentSignalReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_dissent_balance(
    *,
    dissent_count: Decimal,
    hawkish_dissent_count: Decimal,
    dovish_dissent_count: Decimal,
) -> None:
    if dissent_count != _quantize_decimal(hawkish_dissent_count + dovish_dissent_count):
        raise ValueError("dissent_count must equal hawkish plus dovish dissent counts")


def _validate_row(row: RatesFOMCDissentSignalDigestRow) -> None:
    _validate_dissent_balance(
        dissent_count=row.dissent_count,
        hawkish_dissent_count=row.hawkish_dissent_count,
        dovish_dissent_count=row.dovish_dissent_count,
    )
    if row.absolute_median_dot_shift_bps != _abs_decimal(row.median_dot_shift_bps):
        raise ValueError("absolute_median_dot_shift_bps must match shift magnitude")
    if row.signal_score != _signal_score(
        dissent_count=row.dissent_count,
        absolute_median_dot_shift_bps=row.absolute_median_dot_shift_bps,
        dot_dispersion_bps=row.dot_dispersion_bps,
        committee_disagreement_score=row.committee_disagreement_score,
    ):
        raise ValueError("signal_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_status_code = {
        BLOCKED_STATUS: "rates_fomc_dissent_signal_high_risk",
        WATCH_STATUS: "rates_fomc_dissent_signal_watch",
        PASS_STATUS: "rates_fomc_dissent_signal_calm",
    }[row.signal_status]
    if expected_status_code not in row.reason_codes:
        raise ValueError("signal_status must match reason_codes")


def _validate_report(report: RatesFOMCDissentSignalDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_signal_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_signal_count must match rows")
    if report.watch_signal_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_signal_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, "rates_fomc_source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.hawkish_dissent_signal_count != _reason_count(
        report.rows,
        "rates_fomc_dissent_hawkish",
    ):
        raise ValueError("hawkish_dissent_signal_count must match rows")
    if report.dovish_dissent_signal_count != _reason_count(
        report.rows,
        "rates_fomc_dissent_dovish",
    ):
        raise ValueError("dovish_dissent_signal_count must match rows")
    if report.dot_plot_upshift_count != _reason_count(
        report.rows,
        "rates_fomc_dot_plot_upshift",
    ):
        raise ValueError("dot_plot_upshift_count must match rows")
    if report.dot_plot_downshift_count != _reason_count(
        report.rows,
        "rates_fomc_dot_plot_downshift",
    ):
        raise ValueError("dot_plot_downshift_count must match rows")
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
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _digest_status(rows: tuple[RatesFOMCDissentSignalDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.signal_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.signal_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[RatesFOMCDissentSignalDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.signal_status == status))


def _reason_count(
    rows: tuple[RatesFOMCDissentSignalDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[RatesFOMCDissentSignalDigestRow, ...],
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
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
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
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: RatesFOMCDissentSignalDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.signal_status],
        -row.signal_score,
        row.market_slug,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
