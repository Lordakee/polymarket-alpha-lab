"""Pure report-only physical gold premium spike digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_PHYSICAL_PREMIUM_SPIKE_DIGEST_CONFIG_VERSION",
    "GoldPhysicalPremiumSpikeDigestConfig",
    "GoldPhysicalPremiumSpikeObservation",
    "GoldPhysicalPremiumSpikeDigestRow",
    "GoldPhysicalPremiumSpikeReasonCodeCount",
    "GoldPhysicalPremiumSpikeDigestReport",
    "build_market_research_gold_physical_premium_spike_digest",
    "market_research_gold_physical_premium_spike_digest_payload",
)


DEFAULT_MARKET_RESEARCH_GOLD_PHYSICAL_PREMIUM_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-gold-physical-premium-spike-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
DIGEST_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

EMPTY_REASON = "physical_gold_premium_spike_digest_empty"
PASS_REASON = "physical_gold_premium_spike_pass"
WATCH_REASON = "physical_gold_premium_spike_watch"
BLOCKED_REASON = "physical_gold_premium_spike_blocked"
PREMIUM_ELEVATED_REASON = "physical_premium_bps_elevated"
PREMIUM_EXTREME_REASON = "physical_premium_bps_extreme"
LEASE_RATE_REASON = "lease_rate_pressure_high"
ETF_FLOW_REASON = "etf_flow_stress_high"
LOCAL_FX_REASON = "local_fx_stress_high"
DELIVERY_DELAY_REASON = "delivery_delay_elevated"
SOURCE_FRESH_REASON = "source_fresh"
SOURCE_STALE_REASON = "source_stale"
SOURCE_QUORUM_MET_REASON = "source_quorum_met"
SOURCE_QUORUM_LOW_REASON = "source_quorum_low"

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_market_research_gold_physical_premium_spike_digest",
    WATCH_STATUS: "watch_report_only_market_research_gold_physical_premium_spike_digest",
    PASS_STATUS: "allow_report_only_market_research_gold_physical_premium_spike_digest",
}


@dataclass(frozen=True)
class GoldPhysicalPremiumSpikeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_PHYSICAL_PREMIUM_SPIKE_DIGEST_CONFIG_VERSION
    )
    watch_risk_score: Decimal = Decimal("0.350000")
    blocked_risk_score: Decimal = Decimal("0.700000")
    premium_component_ceiling_bps: Decimal = Decimal("500.000000")
    watch_physical_premium_bps: Decimal = Decimal("150.000000")
    blocked_physical_premium_bps: Decimal = Decimal("500.000000")
    high_lease_rate_pressure: Decimal = Decimal("0.700000")
    high_etf_flow_stress: Decimal = Decimal("0.700000")
    high_local_fx_stress: Decimal = Decimal("0.700000")
    high_delivery_delay_days: Decimal = Decimal("7.000000")
    delivery_component_ceiling_days: Decimal = Decimal("14.000000")
    max_source_age_seconds: Decimal = Decimal("900.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldPhysicalPremiumSpikeDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_PHYSICAL_PREMIUM_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_risk_score", "blocked_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "premium_component_ceiling_bps",
            "blocked_physical_premium_bps",
            "delivery_component_ceiling_days",
            "max_source_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_physical_premium_bps",
            "high_delivery_delay_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_lease_rate_pressure",
            "high_etf_flow_stress",
            "high_local_fx_stress",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_risk_score > self.blocked_risk_score:
            raise ValueError("watch_risk_score must not exceed blocked_risk_score")
        if self.watch_physical_premium_bps > self.blocked_physical_premium_bps:
            raise ValueError(
                "watch_physical_premium_bps must not exceed blocked_physical_premium_bps",
            )
        if self.blocked_physical_premium_bps > self.premium_component_ceiling_bps:
            raise ValueError(
                "blocked_physical_premium_bps must not exceed premium_component_ceiling_bps",
            )
        if self.high_delivery_delay_days > self.delivery_component_ceiling_days:
            raise ValueError(
                "high_delivery_delay_days must not exceed delivery_component_ceiling_days",
            )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_whole_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class GoldPhysicalPremiumSpikeObservation:
    source_id: str
    region: str
    venue: str
    market_slug: str
    physical_premium_bps: Decimal
    lease_rate_pressure: Decimal
    etf_flow_stress: Decimal
    local_fx_stress: Decimal
    delivery_delay_days: Decimal
    source_count: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldPhysicalPremiumSpikeObservation, "observation")
        for field_name in ("source_id", "region", "venue", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "physical_premium_bps",
            _normalize_nonnegative_decimal(
                "physical_premium_bps",
                self.physical_premium_bps,
            ),
        )
        for field_name in (
            "lease_rate_pressure",
            "etf_flow_stress",
            "local_fx_stress",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "delivery_delay_days",
            _normalize_nonnegative_decimal(
                "delivery_delay_days",
                self.delivery_delay_days,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_whole_decimal(
                "source_count",
                _normalize_nonnegative_decimal("source_count", self.source_count),
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class GoldPhysicalPremiumSpikeDigestRow:
    source_id: str
    region: str
    venue: str
    market_slug: str
    physical_premium_bps: Decimal
    lease_rate_pressure: Decimal
    etf_flow_stress: Decimal
    local_fx_stress: Decimal
    delivery_delay_days: Decimal
    source_count: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    risk_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldPhysicalPremiumSpikeDigestRow, "row")
        for field_name in ("source_id", "region", "venue", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "physical_premium_bps",
            _normalize_nonnegative_decimal(
                "physical_premium_bps",
                self.physical_premium_bps,
            ),
        )
        for field_name in (
            "lease_rate_pressure",
            "etf_flow_stress",
            "local_fx_stress",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "delivery_delay_days",
            "source_count",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_whole_decimal("source_count", self.source_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class GoldPhysicalPremiumSpikeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldPhysicalPremiumSpikeReasonCodeCount, "reason_count")
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _normalize_probability("row_ratio", self.row_ratio))
        _require_hard_flags(self)


@dataclass(frozen=True)
class GoldPhysicalPremiumSpikeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    low_quorum_count: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[GoldPhysicalPremiumSpikeReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldPhysicalPremiumSpikeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_PHYSICAL_PREMIUM_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "low_quorum_count",
            "max_risk_score",
            "average_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_gold_physical_premium_spike_digest(
    inputs: Iterable[GoldPhysicalPremiumSpikeObservation],
    *,
    config: GoldPhysicalPremiumSpikeDigestConfig,
    generated_at: datetime,
) -> GoldPhysicalPremiumSpikeDigestReport:
    if type(config) is not GoldPhysicalPremiumSpikeDigestConfig:
        raise ValueError("config must be exactly GoldPhysicalPremiumSpikeDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(
        row
        for _, row in sorted(
            (
                (
                    _row_sort_values(row),
                    row,
                )
                for row in (
                    _row_from_observation(
                        value,
                        config=config,
                        generated_at=generated_at,
                    )
                    for value in normalized
                )
            ),
        )
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    status = _digest_status(rows)
    return GoldPhysicalPremiumSpikeDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON),
        low_quorum_count=_reason_count(rows, SOURCE_QUORUM_LOW_REASON),
        max_risk_score=_max_row_decimal(rows, "risk_score"),
        average_risk_score=_ratio(_sum_decimal(row.risk_score for row in rows), row_count),
        digest_status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_gold_physical_premium_spike_digest_payload(
    report: GoldPhysicalPremiumSpikeDigestReport,
) -> dict[str, Any]:
    if type(report) is not GoldPhysicalPremiumSpikeDigestReport:
        raise ValueError("report must be exactly GoldPhysicalPremiumSpikeDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: GoldPhysicalPremiumSpikeObservation,
    *,
    config: GoldPhysicalPremiumSpikeDigestConfig,
    generated_at: datetime,
) -> GoldPhysicalPremiumSpikeDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    source_quorum_met = value.source_count >= config.min_source_count
    risk_score = _risk_score(value, config=config)
    status = _row_status(
        risk_score,
        source_fresh=source_fresh,
        source_quorum_met=source_quorum_met,
        config=config,
    )
    return GoldPhysicalPremiumSpikeDigestRow(
        source_id=value.source_id,
        region=value.region,
        venue=value.venue,
        market_slug=value.market_slug,
        physical_premium_bps=value.physical_premium_bps,
        lease_rate_pressure=value.lease_rate_pressure,
        etf_flow_stress=value.etf_flow_stress,
        local_fx_stress=value.local_fx_stress,
        delivery_delay_days=value.delivery_delay_days,
        source_count=value.source_count,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        risk_score=risk_score,
        digest_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            value=value,
            config=config,
            status=status,
            source_fresh=source_fresh,
            source_quorum_met=source_quorum_met,
        ),
    )


def _risk_score(
    value: GoldPhysicalPremiumSpikeObservation,
    *,
    config: GoldPhysicalPremiumSpikeDigestConfig,
) -> Decimal:
    return _quantize_decimal(
        _component(value.physical_premium_bps, config.premium_component_ceiling_bps)
        * Decimal("0.380000")
        + value.lease_rate_pressure * Decimal("0.180000")
        + value.etf_flow_stress * Decimal("0.160000")
        + value.local_fx_stress * Decimal("0.140000")
        + _component(value.delivery_delay_days, config.delivery_component_ceiling_days)
        * Decimal("0.140000"),
    )


def _component(value: Decimal, ceiling: Decimal) -> Decimal:
    return min(ONE, _ratio(value, ceiling))


def _row_status(
    risk_score: Decimal,
    *,
    source_fresh: bool,
    source_quorum_met: bool,
    config: GoldPhysicalPremiumSpikeDigestConfig,
) -> str:
    if not source_fresh or not source_quorum_met:
        return BLOCKED_STATUS
    if risk_score >= config.blocked_risk_score:
        return BLOCKED_STATUS
    if risk_score >= config.watch_risk_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    value: GoldPhysicalPremiumSpikeObservation,
    config: GoldPhysicalPremiumSpikeDigestConfig,
    status: str,
    source_fresh: bool,
    source_quorum_met: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append(BLOCKED_REASON)
    elif status == WATCH_STATUS:
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(PASS_REASON)

    reason_codes.append(SOURCE_FRESH_REASON if source_fresh else SOURCE_STALE_REASON)
    reason_codes.append(
        SOURCE_QUORUM_MET_REASON if source_quorum_met else SOURCE_QUORUM_LOW_REASON,
    )

    if value.physical_premium_bps >= config.blocked_physical_premium_bps:
        reason_codes.append(PREMIUM_EXTREME_REASON)
    elif value.physical_premium_bps >= config.watch_physical_premium_bps:
        reason_codes.append(PREMIUM_ELEVATED_REASON)
    if value.lease_rate_pressure >= config.high_lease_rate_pressure:
        reason_codes.append(LEASE_RATE_REASON)
    if value.etf_flow_stress >= config.high_etf_flow_stress:
        reason_codes.append(ETF_FLOW_REASON)
    if value.local_fx_stress >= config.high_local_fx_stress:
        reason_codes.append(LOCAL_FX_REASON)
    if value.delivery_delay_days >= config.high_delivery_delay_days:
        reason_codes.append(DELIVERY_DELAY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _normalize_reason_codes(reason for row in rows for reason in row.reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...],
) -> tuple[GoldPhysicalPremiumSpikeReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            GoldPhysicalPremiumSpikeReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        count_row
        for _, count_row in sorted(
            (
                (
                    reason_code,
                    GoldPhysicalPremiumSpikeReasonCodeCount(
                        reason_code=reason_code,
                        count=_reason_count(rows, reason_code),
                        row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
                    ),
                )
                for reason_code in reason_codes
            ),
        )
    )


def _normalize_inputs(
    inputs: Iterable[GoldPhysicalPremiumSpikeObservation],
) -> tuple[GoldPhysicalPremiumSpikeObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not GoldPhysicalPremiumSpikeObservation:
            raise ValueError("inputs must contain GoldPhysicalPremiumSpikeObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[GoldPhysicalPremiumSpikeDigestRow],
) -> tuple[GoldPhysicalPremiumSpikeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not GoldPhysicalPremiumSpikeDigestRow:
            raise ValueError("rows must contain GoldPhysicalPremiumSpikeDigestRow")
        _require_hard_flags(row)
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id")
        seen.add(row.source_id)
    return tuple(row for _, row in sorted((_row_sort_values(row), row) for row in normalized))


def _normalize_reason_code_counts(
    values: Iterable[GoldPhysicalPremiumSpikeReasonCodeCount],
) -> tuple[GoldPhysicalPremiumSpikeReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not GoldPhysicalPremiumSpikeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain GoldPhysicalPremiumSpikeReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(item for _, item in sorted((item.reason_code, item) for item in normalized))


def _validate_row(row: GoldPhysicalPremiumSpikeDigestRow) -> None:
    if row.digest_status == BLOCKED_STATUS and BLOCKED_REASON not in row.reason_codes:
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == WATCH_STATUS and WATCH_REASON not in row.reason_codes:
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == PASS_STATUS and PASS_REASON not in row.reason_codes:
        raise ValueError("digest_status must match reason_codes")
    if row.source_age_seconds == ZERO and SOURCE_STALE_REASON in row.reason_codes:
        raise ValueError("source_age_seconds must match source freshness")


def _validate_report(report: GoldPhysicalPremiumSpikeDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.low_quorum_count != _reason_count(report.rows, SOURCE_QUORUM_LOW_REASON):
        raise ValueError("low_quorum_count must match rows")
    if report.max_risk_score != _max_row_decimal(report.rows, "risk_score"):
        raise ValueError("max_risk_score must match rows")
    if report.average_risk_score != _ratio(
        _sum_decimal(row.risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _digest_status(rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.digest_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[GoldPhysicalPremiumSpikeDigestRow, ...],
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
    if later < earlier:
        raise ValueError("observed_at must not be after generated_at")
    delta = later - earlier
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


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_decimal(value)
    if quantized != value:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return quantized


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


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


def _row_sort_values(
    row: GoldPhysicalPremiumSpikeDigestRow,
) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.digest_status],
        -row.risk_score,
        row.region,
        row.venue,
        row.market_slug,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
