"""Pure report-only FX carry unwind pressure digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_PRESSURE_DIGEST_CONFIG_VERSION",
    "FXCarryUnwindPressureDigestConfig",
    "FXCarryUnwindPressureObservation",
    "FXCarryUnwindPressureDigestRow",
    "FXCarryUnwindPressureReasonCodeCount",
    "FXCarryUnwindPressureDigestReport",
    "build_market_research_fx_carry_unwind_pressure_digest",
    "market_research_fx_carry_unwind_pressure_digest_payload",
)


DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-fx-carry-unwind-pressure-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CARRY_PRESSURE_DIRECTION = "carry_unwind_pressure"
CARRY_CALM_DIRECTION = "carry_pressure_calm"
PRESSURE_DIRECTIONS = (CARRY_PRESSURE_DIRECTION, CARRY_CALM_DIRECTION)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
PRESSURE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_market_research_fx_carry_unwind_pressure_digest",
    WATCH_STATUS: "watch_report_only_market_research_fx_carry_unwind_pressure_digest",
    PASS_STATUS: "allow_report_only_market_research_fx_carry_unwind_pressure_digest",
}


@dataclass(frozen=True)
class FXCarryUnwindPressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_PRESSURE_DIGEST_CONFIG_VERSION
    )
    watch_pressure_score: Decimal = Decimal("0.350000")
    blocked_pressure_score: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("900.000000")
    stale_confidence_cap: Decimal = Decimal("0.350000")
    watch_confidence_cap: Decimal = Decimal("0.650000")
    calm_confidence_cap: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindPressureDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_pressure_score",
            "blocked_pressure_score",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_confidence_cap",
            "watch_confidence_cap",
            "calm_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_pressure_score > self.blocked_pressure_score:
            raise ValueError("watch_pressure_score must not exceed blocked_pressure_score")
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindPressureObservation:
    source_id: str
    market_slug: str
    carry_pair: str
    funding_currency: str
    target_currency: str
    carry_return_pct: Decimal
    funding_currency_return_pct: Decimal
    volatility_z_score: Decimal
    rate_differential_compression_pct: Decimal
    liquidity_stress_ratio: Decimal
    positioning_unwind_ratio: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindPressureObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "carry_pair",
            "funding_currency",
            "target_currency",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "carry_return_pct",
            "funding_currency_return_pct",
            "volatility_z_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rate_differential_compression_pct",
            _normalize_nonnegative_decimal(
                "rate_differential_compression_pct",
                self.rate_differential_compression_pct,
            ),
        )
        for field_name in (
            "liquidity_stress_ratio",
            "positioning_unwind_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindPressureDigestRow:
    source_id: str
    market_slug: str
    carry_pair: str
    funding_currency: str
    target_currency: str
    carry_return_pct: Decimal
    funding_currency_return_pct: Decimal
    volatility_z_score: Decimal
    rate_differential_compression_pct: Decimal
    liquidity_stress_ratio: Decimal
    positioning_unwind_ratio: Decimal
    pressure_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    pressure_direction: str
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindPressureDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "carry_pair",
            "funding_currency",
            "target_currency",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "carry_return_pct",
            "funding_currency_return_pct",
            "volatility_z_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rate_differential_compression_pct",
            _normalize_nonnegative_decimal(
                "rate_differential_compression_pct",
                self.rate_differential_compression_pct,
            ),
        )
        for field_name in (
            "liquidity_stress_ratio",
            "positioning_unwind_ratio",
            "pressure_score",
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
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        _require_member("pressure_direction", self.pressure_direction, PRESSURE_DIRECTIONS)
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindPressureReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            FXCarryUnwindPressureReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _normalize_probability("row_ratio", self.row_ratio))
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindPressureDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_pressure_count: Decimal
    watch_pressure_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    carry_pressure_count: Decimal
    max_pressure_score: Decimal
    average_pressure_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[FXCarryUnwindPressureDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[FXCarryUnwindPressureReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindPressureDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_pressure_count",
            "watch_pressure_count",
            "pass_count",
            "stale_source_count",
            "carry_pressure_count",
            "max_pressure_score",
            "average_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, PRESSURE_STATUSES)
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


def build_market_research_fx_carry_unwind_pressure_digest(
    inputs: Iterable[FXCarryUnwindPressureObservation],
    *,
    config: FXCarryUnwindPressureDigestConfig,
    generated_at: datetime,
) -> FXCarryUnwindPressureDigestReport:
    if type(config) is not FXCarryUnwindPressureDigestConfig:
        raise ValueError("config must be exactly FXCarryUnwindPressureDigestConfig")
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
    return FXCarryUnwindPressureDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_pressure_count=_status_count(rows, BLOCKED_STATUS),
        watch_pressure_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "fx_carry_pressure_source_stale"),
        carry_pressure_count=_direction_count(rows, CARRY_PRESSURE_DIRECTION),
        max_pressure_score=_max_row_decimal(rows, "pressure_score"),
        average_pressure_score=_ratio(
            _sum_decimal(row.pressure_score for row in rows),
            row_count,
        ),
        digest_status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_fx_carry_unwind_pressure_digest_payload(
    report: FXCarryUnwindPressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not FXCarryUnwindPressureDigestReport:
        raise ValueError("report must be exactly FXCarryUnwindPressureDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: FXCarryUnwindPressureObservation,
    *,
    config: FXCarryUnwindPressureDigestConfig,
    generated_at: datetime,
) -> FXCarryUnwindPressureDigestRow:
    pressure_score = _pressure_score(value)
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _pressure_status(pressure_score, config=config)
    direction = (
        CARRY_CALM_DIRECTION if status == PASS_STATUS else CARRY_PRESSURE_DIRECTION
    )
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return FXCarryUnwindPressureDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        carry_pair=value.carry_pair,
        funding_currency=value.funding_currency,
        target_currency=value.target_currency,
        carry_return_pct=value.carry_return_pct,
        funding_currency_return_pct=value.funding_currency_return_pct,
        volatility_z_score=value.volatility_z_score,
        rate_differential_compression_pct=value.rate_differential_compression_pct,
        liquidity_stress_ratio=value.liquidity_stress_ratio,
        positioning_unwind_ratio=value.positioning_unwind_ratio,
        pressure_score=pressure_score,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        pressure_direction=direction,
        pressure_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            value=value,
            status=status,
            source_fresh=source_fresh,
        ),
    )


def _pressure_score(value: FXCarryUnwindPressureObservation) -> Decimal:
    carry_drawdown_component = min(
        ONE,
        max(ZERO, -value.carry_return_pct / Decimal("0.080000")),
    )
    funding_rally_component = min(
        ONE,
        max(ZERO, value.funding_currency_return_pct / Decimal("0.060000")),
    )
    volatility_component = min(
        ONE,
        max(ZERO, value.volatility_z_score / Decimal("4.000000")),
    )
    compression_component = min(
        ONE,
        max(ZERO, value.rate_differential_compression_pct / Decimal("0.030000")),
    )
    return _quantize_decimal(
        carry_drawdown_component * Decimal("0.300000")
        + funding_rally_component * Decimal("0.180000")
        + volatility_component * Decimal("0.140000")
        + compression_component * Decimal("0.120000")
        + value.liquidity_stress_ratio * Decimal("0.140000")
        + value.positioning_unwind_ratio * Decimal("0.120000"),
    )


def _pressure_status(
    score: Decimal,
    *,
    config: FXCarryUnwindPressureDigestConfig,
) -> str:
    if score >= config.blocked_pressure_score:
        return BLOCKED_STATUS
    if score >= config.watch_pressure_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: FXCarryUnwindPressureDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == WATCH_STATUS:
        caps.append(config.watch_confidence_cap)
    if status == PASS_STATUS:
        caps.append(config.calm_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    value: FXCarryUnwindPressureObservation,
    status: str,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("fx_carry_unwind_pressure_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("fx_carry_unwind_pressure_watch")
    else:
        reason_codes.append("fx_carry_unwind_pressure_calm")
    reason_codes.append(
        "fx_carry_pressure_source_fresh"
        if source_fresh
        else "fx_carry_pressure_source_stale",
    )
    if value.carry_return_pct < ZERO:
        reason_codes.append("carry_leg_drawdown")
    if value.funding_currency_return_pct >= Decimal("0.020000"):
        reason_codes.append("funding_currency_rally")
    if value.volatility_z_score >= Decimal("3.000000"):
        reason_codes.append("volatility_pressure_high")
    if value.rate_differential_compression_pct >= Decimal("0.020000"):
        reason_codes.append("rate_differential_compression_high")
    if value.liquidity_stress_ratio >= Decimal("0.750000"):
        reason_codes.append("liquidity_stress_high")
    if value.positioning_unwind_ratio >= Decimal("0.750000"):
        reason_codes.append("positioning_unwind_high")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[FXCarryUnwindPressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("fx_carry_unwind_pressure_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[FXCarryUnwindPressureDigestRow, ...],
) -> tuple[FXCarryUnwindPressureReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("fx_carry_unwind_pressure_digest_empty",):
        return (
            FXCarryUnwindPressureReasonCodeCount(
                reason_code="fx_carry_unwind_pressure_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        FXCarryUnwindPressureReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[FXCarryUnwindPressureObservation],
) -> tuple[FXCarryUnwindPressureObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not FXCarryUnwindPressureObservation:
            raise ValueError("inputs must contain FXCarryUnwindPressureObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[FXCarryUnwindPressureDigestRow],
) -> tuple[FXCarryUnwindPressureDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not FXCarryUnwindPressureDigestRow:
            raise ValueError("rows must contain FXCarryUnwindPressureDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[FXCarryUnwindPressureReasonCodeCount],
) -> tuple[FXCarryUnwindPressureReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not FXCarryUnwindPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain FXCarryUnwindPressureReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: FXCarryUnwindPressureDigestRow) -> None:
    if row.pressure_score != _pressure_score(
        FXCarryUnwindPressureObservation(
            source_id=row.source_id,
            market_slug=row.market_slug,
            carry_pair=row.carry_pair,
            funding_currency=row.funding_currency,
            target_currency=row.target_currency,
            carry_return_pct=row.carry_return_pct,
            funding_currency_return_pct=row.funding_currency_return_pct,
            volatility_z_score=row.volatility_z_score,
            rate_differential_compression_pct=row.rate_differential_compression_pct,
            liquidity_stress_ratio=row.liquidity_stress_ratio,
            positioning_unwind_ratio=row.positioning_unwind_ratio,
            observed_at=row.observed_at,
            base_confidence=row.base_confidence,
            upstream_reason_codes=(),
        ),
    ):
        raise ValueError("pressure_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.pressure_status == PASS_STATUS and row.pressure_direction != CARRY_CALM_DIRECTION:
        raise ValueError("pressure_direction must match pressure_status")
    if row.pressure_status != PASS_STATUS and row.pressure_direction != CARRY_PRESSURE_DIRECTION:
        raise ValueError("pressure_direction must match pressure_status")
    expected_status_code = (
        "fx_carry_unwind_pressure_calm"
        if row.pressure_status == PASS_STATUS
        else f"fx_carry_unwind_pressure_{row.pressure_status}"
    )
    if expected_status_code not in row.reason_codes:
        raise ValueError("pressure_status must match reason_codes")


def _validate_report(report: FXCarryUnwindPressureDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_pressure_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_pressure_count must match rows")
    if report.watch_pressure_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_pressure_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "fx_carry_pressure_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.carry_pressure_count != _direction_count(
        report.rows,
        CARRY_PRESSURE_DIRECTION,
    ):
        raise ValueError("carry_pressure_count must match rows")
    if report.max_pressure_score != _max_row_decimal(report.rows, "pressure_score"):
        raise ValueError("max_pressure_score must match rows")
    if report.average_pressure_score != _ratio(
        _sum_decimal(row.pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_pressure_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _digest_status(rows: tuple[FXCarryUnwindPressureDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(rows: tuple[FXCarryUnwindPressureDigestRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_status == status))


def _direction_count(
    rows: tuple[FXCarryUnwindPressureDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_direction == direction))


def _reason_count(
    rows: tuple[FXCarryUnwindPressureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[FXCarryUnwindPressureDigestRow, ...],
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
    row: FXCarryUnwindPressureDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.pressure_status],
        -row.pressure_score,
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
