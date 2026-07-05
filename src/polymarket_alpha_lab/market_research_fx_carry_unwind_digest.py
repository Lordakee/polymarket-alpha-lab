"""Pure report-only FX carry unwind digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_DIGEST_CONFIG_VERSION",
    "FXCarryUnwindDigestConfig",
    "FXCarryUnwindObservation",
    "FXCarryUnwindDigestRow",
    "FXCarryUnwindReasonCodeCount",
    "FXCarryUnwindDigestReport",
    "build_market_research_fx_carry_unwind_digest",
    "market_research_fx_carry_unwind_digest_payload",
)


DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_DIGEST_CONFIG_VERSION = (
    "market-research-fx-carry-unwind-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

UNWIND_DIRECTION = "carry_unwind"
RESILIENT_DIRECTION = "carry_resilient"
UNWIND_DIRECTIONS = (UNWIND_DIRECTION, RESILIENT_DIRECTION)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
UNWIND_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_market_research_fx_carry_unwind_digest",
    WATCH_STATUS: "monitor_report_only_market_research_fx_carry_unwind_digest",
    PASS_STATUS: "allow_report_only_market_research_fx_carry_unwind_digest",
}


@dataclass(frozen=True)
class FXCarryUnwindDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_DIGEST_CONFIG_VERSION
    watch_unwind_score: Decimal = Decimal("0.400000")
    blocked_unwind_score: Decimal = Decimal("0.750000")
    max_source_age_seconds: Decimal = Decimal("900.000000")
    stale_confidence_cap: Decimal = Decimal("0.350000")
    calm_confidence_cap: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not FXCarryUnwindDigestConfig:
            raise TypeError("FXCarryUnwindDigestConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_unwind_score",
            "blocked_unwind_score",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_confidence_cap", "calm_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_unwind_score > self.blocked_unwind_score:
            raise ValueError("watch_unwind_score must not exceed blocked_unwind_score")
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindObservation:
    source_id: str
    market_slug: str
    carry_pair: str
    funding_currency: str
    target_currency: str
    spot_return_pct: Decimal
    rate_differential_pct: Decimal
    volatility_z_score: Decimal
    funding_currency_strength_pct: Decimal
    liquidity_stress_ratio: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not FXCarryUnwindObservation:
            raise TypeError("FXCarryUnwindObservation does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "carry_pair",
            "funding_currency",
            "target_currency",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "spot_return_pct",
            "rate_differential_pct",
            "volatility_z_score",
            "funding_currency_strength_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_stress_ratio",
            _normalize_probability("liquidity_stress_ratio", self.liquidity_stress_ratio),
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
            _normalize_reason_codes(
                self.upstream_reason_codes,
                field_name="upstream_reason_codes",
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindDigestRow:
    source_id: str
    market_slug: str
    carry_pair: str
    funding_currency: str
    target_currency: str
    spot_return_pct: Decimal
    rate_differential_pct: Decimal
    volatility_z_score: Decimal
    funding_currency_strength_pct: Decimal
    liquidity_stress_ratio: Decimal
    unwind_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    unwind_direction: str
    unwind_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not FXCarryUnwindDigestRow:
            raise TypeError("FXCarryUnwindDigestRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "carry_pair",
            "funding_currency",
            "target_currency",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "spot_return_pct",
            "rate_differential_pct",
            "volatility_z_score",
            "funding_currency_strength_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_stress_ratio", "unwind_score"):
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
        for field_name in ("base_confidence", "confidence_cap", "capped_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("unwind_direction", self.unwind_direction, UNWIND_DIRECTIONS)
        _require_member("unwind_status", self.unwind_status, UNWIND_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, field_name="reason_codes"),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not FXCarryUnwindReasonCodeCount:
            raise TypeError("FXCarryUnwindReasonCodeCount does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindReasonCodeCount, "reason_code_count")
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXCarryUnwindDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_unwind_count: Decimal
    watch_unwind_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    carry_unwind_count: Decimal
    max_unwind_score: Decimal
    average_unwind_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[FXCarryUnwindDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[FXCarryUnwindReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not FXCarryUnwindDigestReport:
            raise TypeError("FXCarryUnwindDigestReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FXCarryUnwindDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_FX_CARRY_UNWIND_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_unwind_count",
            "watch_unwind_count",
            "pass_count",
            "stale_source_count",
            "carry_unwind_count",
            "max_unwind_score",
            "average_unwind_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, UNWIND_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, field_name="reason_codes"),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


_PUBLIC_DATACLASS_TYPES = (
    FXCarryUnwindDigestConfig,
    FXCarryUnwindObservation,
    FXCarryUnwindDigestRow,
    FXCarryUnwindReasonCodeCount,
    FXCarryUnwindDigestReport,
)


def build_market_research_fx_carry_unwind_digest(
    inputs: Iterable[FXCarryUnwindObservation],
    *,
    config: FXCarryUnwindDigestConfig,
    generated_at: datetime,
) -> FXCarryUnwindDigestReport:
    if type(config) is not FXCarryUnwindDigestConfig:
        raise ValueError("config must be exactly FXCarryUnwindDigestConfig")
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
    return FXCarryUnwindDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_unwind_count=_status_count(rows, BLOCKED_STATUS),
        watch_unwind_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "source_stale"),
        carry_unwind_count=_direction_count(rows, UNWIND_DIRECTION),
        max_unwind_score=_max_row_decimal(rows, "unwind_score"),
        average_unwind_score=_ratio(
            _sum_decimal(row.unwind_score for row in rows),
            row_count,
        ),
        digest_status=_digest_status(rows),
        recommended_next_step=RECOMMENDED_NEXT_STEPS[_digest_status(rows)],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_fx_carry_unwind_digest_payload(
    report: FXCarryUnwindDigestReport,
) -> dict[str, Any]:
    if type(report) is not FXCarryUnwindDigestReport:
        raise ValueError("report must be exactly FXCarryUnwindDigestReport")
    _require_payload_safe_value("report", report)
    return _payload_value(report)


def _row_from_observation(
    value: FXCarryUnwindObservation,
    *,
    config: FXCarryUnwindDigestConfig,
    generated_at: datetime,
) -> FXCarryUnwindDigestRow:
    unwind_score = _unwind_score(value)
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _unwind_status(unwind_score, config=config)
    direction = UNWIND_DIRECTION if status != PASS_STATUS else RESILIENT_DIRECTION
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return FXCarryUnwindDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        carry_pair=value.carry_pair,
        funding_currency=value.funding_currency,
        target_currency=value.target_currency,
        spot_return_pct=value.spot_return_pct,
        rate_differential_pct=value.rate_differential_pct,
        volatility_z_score=value.volatility_z_score,
        funding_currency_strength_pct=value.funding_currency_strength_pct,
        liquidity_stress_ratio=value.liquidity_stress_ratio,
        unwind_score=unwind_score,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        unwind_direction=direction,
        unwind_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            value=value,
            status=status,
            source_fresh=source_fresh,
        ),
    )


def _unwind_score(value: FXCarryUnwindObservation) -> Decimal:
    spot_component = min(ONE, max(ZERO, -value.spot_return_pct / Decimal("0.080000")))
    volatility_component = min(
        ONE,
        max(ZERO, value.volatility_z_score / Decimal("4.000000")),
    )
    funding_component = min(
        ONE,
        max(ZERO, value.funding_currency_strength_pct / Decimal("0.060000")),
    )
    stress_component = value.liquidity_stress_ratio
    return _quantize_decimal(
        min(
            ONE,
            spot_component * Decimal("0.460000")
            + volatility_component * Decimal("0.100000")
            + funding_component * Decimal("0.210000")
            + stress_component * Decimal("0.400000"),
        ),
    )


def _unwind_status(score: Decimal, *, config: FXCarryUnwindDigestConfig) -> str:
    if score >= config.blocked_unwind_score:
        return BLOCKED_STATUS
    if score >= config.watch_unwind_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: FXCarryUnwindDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == PASS_STATUS:
        caps.append(config.calm_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    value: FXCarryUnwindObservation,
    status: str,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("carry_unwind_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("carry_unwind_watch")
    else:
        reason_codes.append("carry_unwind_calm")
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    if value.spot_return_pct < ZERO:
        reason_codes.append("spot_carry_drawdown")
    if value.volatility_z_score >= Decimal("3.000000"):
        reason_codes.append("volatility_pressure_high")
    if value.funding_currency_strength_pct >= Decimal("0.020000"):
            reason_codes.append("funding_currency_strength")
    if value.liquidity_stress_ratio >= Decimal("0.750000"):
        reason_codes.append("liquidity_stress_high")
    return _canonical_reason_codes(tuple(reason_codes), field_name="reason_codes")


def _report_reason_codes(rows: tuple[FXCarryUnwindDigestRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("fx_carry_unwind_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _canonical_reason_codes(tuple(reason_codes), field_name="reason_codes")


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[FXCarryUnwindDigestRow, ...],
) -> tuple[FXCarryUnwindReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("fx_carry_unwind_digest_empty",):
        return (
            FXCarryUnwindReasonCodeCount(
                reason_code="fx_carry_unwind_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        FXCarryUnwindReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[FXCarryUnwindObservation],
) -> tuple[FXCarryUnwindObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not FXCarryUnwindObservation:
            raise ValueError("inputs must contain FXCarryUnwindObservation")
        _require_hard_flags(value)
        key = value.source_id
        if key in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: Iterable[FXCarryUnwindDigestRow],
) -> tuple[FXCarryUnwindDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not FXCarryUnwindDigestRow:
            raise ValueError("rows must contain FXCarryUnwindDigestRow")
        _require_hard_flags(row)
    canonical = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != canonical:
        raise ValueError("rows must be canonical sorted by status, score, market_slug, source_id")
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[FXCarryUnwindReasonCodeCount],
) -> tuple[FXCarryUnwindReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not FXCarryUnwindReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain FXCarryUnwindReasonCodeCount",
            )
        _require_hard_flags(value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason_code")
        seen.add(value.reason_code)
    canonical = tuple(sorted(normalized, key=lambda value: value.reason_code))
    if normalized != canonical:
        raise ValueError("reason_code_counts must be canonical sorted by reason_code")
    return normalized


def _validate_row(row: FXCarryUnwindDigestRow) -> None:
    if row.unwind_score != _unwind_score(
        FXCarryUnwindObservation(
            source_id=row.source_id,
            market_slug=row.market_slug,
            carry_pair=row.carry_pair,
            funding_currency=row.funding_currency,
            target_currency=row.target_currency,
            spot_return_pct=row.spot_return_pct,
            rate_differential_pct=row.rate_differential_pct,
            volatility_z_score=row.volatility_z_score,
            funding_currency_strength_pct=row.funding_currency_strength_pct,
            liquidity_stress_ratio=row.liquidity_stress_ratio,
            observed_at=row.observed_at,
            base_confidence=row.base_confidence,
            upstream_reason_codes=(),
        ),
    ):
        raise ValueError("unwind_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.unwind_status == PASS_STATUS and row.unwind_direction != RESILIENT_DIRECTION:
        raise ValueError("unwind_direction must match unwind_status")
    if row.unwind_status != PASS_STATUS and row.unwind_direction != UNWIND_DIRECTION:
        raise ValueError("unwind_direction must match unwind_status")


def _validate_report(report: FXCarryUnwindDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if (
        report.blocked_unwind_count
        + report.watch_unwind_count
        + report.pass_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.carry_unwind_count != _direction_count(report.rows, UNWIND_DIRECTION):
        raise ValueError("carry_unwind_count must match rows")
    if report.max_unwind_score != _max_row_decimal(report.rows, "unwind_score"):
        raise ValueError("max_unwind_score must match rows")
    if report.average_unwind_score != _ratio(
        _sum_decimal(row.unwind_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_unwind_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _digest_status(rows: tuple[FXCarryUnwindDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.unwind_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.unwind_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(rows: tuple[FXCarryUnwindDigestRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.unwind_status == status))


def _direction_count(rows: tuple[FXCarryUnwindDigestRow, ...], direction: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.unwind_direction == direction))


def _reason_count(rows: tuple[FXCarryUnwindDigestRow, ...], reason_code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(rows: tuple[FXCarryUnwindDigestRow, ...], field_name: str) -> Decimal:
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


def _reason_code_tuple(
    reason_codes: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    values = tuple(reason_codes)
    for reason_code in values:
        _require_canonical_string("reason_code", reason_code)
    return values


def _canonical_reason_codes(
    reason_codes: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    values = _reason_code_tuple(reason_codes, field_name=field_name)
    normalized: list[str] = []
    for reason_code in values:
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    reason_codes: Iterable[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    values = _reason_code_tuple(reason_codes, field_name=field_name)
    canonical = _canonical_reason_codes(values, field_name=field_name)
    if values != canonical:
        raise ValueError(f"{field_name} must be canonical sorted unique reason codes")
    return values


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(row: FXCarryUnwindDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.unwind_status],
        -row.unwind_score,
        row.market_slug,
        row.source_id,
    )


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        normalized = _normalize_decimal(field_name, value)
        if normalized != value or not value.same_quantum(QUANTUM):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _rebuild_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _rebuild_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("value must be a supported public dataclass")
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    return value
