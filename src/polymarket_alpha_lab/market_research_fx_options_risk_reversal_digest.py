"""Pure report-only FX options risk reversal digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_FX_OPTIONS_RISK_REVERSAL_DIGEST_CONFIG_VERSION",
    "FXOptionsRiskReversalDigestConfig",
    "FXOptionsRiskReversalObservation",
    "FXOptionsRiskReversalDigestRow",
    "FXOptionsRiskReversalReasonCodeCount",
    "FXOptionsRiskReversalDigestReport",
    "build_market_research_fx_options_risk_reversal_digest",
    "market_research_fx_options_risk_reversal_digest_payload",
)


DEFAULT_MARKET_RESEARCH_FX_OPTIONS_RISK_REVERSAL_DIGEST_CONFIG_VERSION = (
    "market-research-fx-options-risk-reversal-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
SKEW_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: (
        "block_report_only_market_research_fx_options_risk_reversal_digest"
    ),
    WATCH_STATUS: (
        "watch_report_only_market_research_fx_options_risk_reversal_digest"
    ),
    PASS_STATUS: (
        "allow_report_only_market_research_fx_options_risk_reversal_digest"
    ),
}


@dataclass(frozen=True)
class FXOptionsRiskReversalDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_FX_OPTIONS_RISK_REVERSAL_DIGEST_CONFIG_VERSION
    )
    watch_risk_reversal_shift_bps: Decimal = Decimal("25.000000")
    blocked_risk_reversal_shift_bps: Decimal = Decimal("75.000000")
    watch_absolute_risk_reversal_bps: Decimal = Decimal("50.000000")
    blocked_absolute_risk_reversal_bps: Decimal = Decimal("100.000000")
    watch_stress_score: Decimal = Decimal("0.350000")
    blocked_stress_score: Decimal = Decimal("0.650000")
    max_source_age_seconds: Decimal = Decimal("600.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    watch_confidence_cap: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXOptionsRiskReversalDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FX_OPTIONS_RISK_REVERSAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_risk_reversal_shift_bps",
            "blocked_risk_reversal_shift_bps",
            "watch_absolute_risk_reversal_bps",
            "blocked_absolute_risk_reversal_bps",
            "watch_stress_score",
            "blocked_stress_score",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_confidence_cap", "watch_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_risk_reversal_shift_bps > self.blocked_risk_reversal_shift_bps:
            raise ValueError(
                "watch_risk_reversal_shift_bps must not exceed "
                "blocked_risk_reversal_shift_bps",
            )
        if self.watch_absolute_risk_reversal_bps > self.blocked_absolute_risk_reversal_bps:
            raise ValueError(
                "watch_absolute_risk_reversal_bps must not exceed "
                "blocked_absolute_risk_reversal_bps",
            )
        if self.watch_stress_score > self.blocked_stress_score:
            raise ValueError("watch_stress_score must not exceed blocked_stress_score")
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXOptionsRiskReversalObservation:
    source_id: str
    market_slug: str
    currency_pair: str
    option_tenor: str
    current_risk_reversal_bps: Decimal
    baseline_risk_reversal_bps: Decimal
    implied_volatility_z_score: Decimal
    option_liquidity_stress_ratio: Decimal
    skew_dislocation_ratio: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXOptionsRiskReversalObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "currency_pair",
            "option_tenor",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_risk_reversal_bps",
            "baseline_risk_reversal_bps",
            "implied_volatility_z_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("option_liquidity_stress_ratio", "skew_dislocation_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXOptionsRiskReversalDigestRow:
    source_id: str
    market_slug: str
    currency_pair: str
    option_tenor: str
    current_risk_reversal_bps: Decimal
    baseline_risk_reversal_bps: Decimal
    risk_reversal_shift_bps: Decimal
    absolute_risk_reversal_bps: Decimal
    implied_volatility_z_score: Decimal
    option_liquidity_stress_ratio: Decimal
    skew_dislocation_ratio: Decimal
    stress_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    skew_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXOptionsRiskReversalDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "currency_pair",
            "option_tenor",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_risk_reversal_bps",
            "baseline_risk_reversal_bps",
            "risk_reversal_shift_bps",
            "absolute_risk_reversal_bps",
            "implied_volatility_z_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "option_liquidity_stress_ratio",
            "skew_dislocation_ratio",
            "stress_score",
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
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("skew_status", self.skew_status, SKEW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class FXOptionsRiskReversalReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            FXOptionsRiskReversalReasonCodeCount,
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
class FXOptionsRiskReversalDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_skew_count: Decimal
    watch_skew_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    reversal_steepening_count: Decimal
    reversal_flattening_count: Decimal
    max_stress_score: Decimal
    average_stress_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[FXOptionsRiskReversalDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[FXOptionsRiskReversalReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FXOptionsRiskReversalDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FX_OPTIONS_RISK_REVERSAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_skew_count",
            "watch_skew_count",
            "pass_count",
            "stale_source_count",
            "reversal_steepening_count",
            "reversal_flattening_count",
            "max_stress_score",
            "average_stress_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SKEW_STATUSES)
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


def build_market_research_fx_options_risk_reversal_digest(
    inputs: Iterable[FXOptionsRiskReversalObservation],
    *,
    config: FXOptionsRiskReversalDigestConfig,
    generated_at: datetime,
) -> FXOptionsRiskReversalDigestReport:
    if type(config) is not FXOptionsRiskReversalDigestConfig:
        raise ValueError("config must be exactly FXOptionsRiskReversalDigestConfig")
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
    return FXOptionsRiskReversalDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_skew_count=_status_count(rows, BLOCKED_STATUS),
        watch_skew_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(
            rows,
            "fx_options_risk_reversal_source_stale",
        ),
        reversal_steepening_count=_reason_count(
            rows,
            "fx_options_risk_reversal_steepening",
        ),
        reversal_flattening_count=_reason_count(
            rows,
            "fx_options_risk_reversal_flattening",
        ),
        max_stress_score=_max_row_decimal(rows, "stress_score"),
        average_stress_score=_ratio(
            _sum_decimal(row.stress_score for row in rows),
            row_count,
        ),
        digest_status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_fx_options_risk_reversal_digest_payload(
    report: FXOptionsRiskReversalDigestReport,
) -> dict[str, Any]:
    if type(report) is not FXOptionsRiskReversalDigestReport:
        raise ValueError("report must be exactly FXOptionsRiskReversalDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: FXOptionsRiskReversalObservation,
    *,
    config: FXOptionsRiskReversalDigestConfig,
    generated_at: datetime,
) -> FXOptionsRiskReversalDigestRow:
    risk_reversal_shift_bps = _quantize_decimal(
        value.current_risk_reversal_bps - value.baseline_risk_reversal_bps,
    )
    absolute_risk_reversal_bps = _abs_decimal(value.current_risk_reversal_bps)
    stress_score = _stress_score(
        risk_reversal_shift_bps=risk_reversal_shift_bps,
        absolute_risk_reversal_bps=absolute_risk_reversal_bps,
        implied_volatility_z_score=value.implied_volatility_z_score,
        option_liquidity_stress_ratio=value.option_liquidity_stress_ratio,
        skew_dislocation_ratio=value.skew_dislocation_ratio,
    )
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _skew_status(
        risk_reversal_shift_bps=risk_reversal_shift_bps,
        absolute_risk_reversal_bps=absolute_risk_reversal_bps,
        stress_score=stress_score,
        config=config,
    )
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return FXOptionsRiskReversalDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        currency_pair=value.currency_pair,
        option_tenor=value.option_tenor,
        current_risk_reversal_bps=value.current_risk_reversal_bps,
        baseline_risk_reversal_bps=value.baseline_risk_reversal_bps,
        risk_reversal_shift_bps=risk_reversal_shift_bps,
        absolute_risk_reversal_bps=absolute_risk_reversal_bps,
        implied_volatility_z_score=value.implied_volatility_z_score,
        option_liquidity_stress_ratio=value.option_liquidity_stress_ratio,
        skew_dislocation_ratio=value.skew_dislocation_ratio,
        stress_score=stress_score,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        skew_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            risk_reversal_shift_bps=risk_reversal_shift_bps,
            absolute_risk_reversal_bps=absolute_risk_reversal_bps,
            implied_volatility_z_score=value.implied_volatility_z_score,
            option_liquidity_stress_ratio=value.option_liquidity_stress_ratio,
            skew_dislocation_ratio=value.skew_dislocation_ratio,
            status=status,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _stress_score(
    *,
    risk_reversal_shift_bps: Decimal,
    absolute_risk_reversal_bps: Decimal,
    implied_volatility_z_score: Decimal,
    option_liquidity_stress_ratio: Decimal,
    skew_dislocation_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        shift_component = min(
            ONE,
            _abs_decimal(risk_reversal_shift_bps) / Decimal("100.000000"),
        )
        level_component = min(
            ONE,
            absolute_risk_reversal_bps / Decimal("150.000000"),
        )
        volatility_component = min(
            ONE,
            _abs_decimal(implied_volatility_z_score) / Decimal("4.000000"),
        )
        return _quantize_decimal(
            shift_component * Decimal("0.400000")
            + level_component * Decimal("0.200000")
            + option_liquidity_stress_ratio * Decimal("0.150000")
            + skew_dislocation_ratio * Decimal("0.150000")
            + volatility_component * Decimal("0.100000"),
        )


def _skew_status(
    *,
    risk_reversal_shift_bps: Decimal,
    absolute_risk_reversal_bps: Decimal,
    stress_score: Decimal,
    config: FXOptionsRiskReversalDigestConfig,
) -> str:
    absolute_shift_bps = _abs_decimal(risk_reversal_shift_bps)
    if (
        absolute_shift_bps >= config.blocked_risk_reversal_shift_bps
        or absolute_risk_reversal_bps >= config.blocked_absolute_risk_reversal_bps
        or stress_score >= config.blocked_stress_score
    ):
        return BLOCKED_STATUS
    if (
        absolute_shift_bps >= config.watch_risk_reversal_shift_bps
        or absolute_risk_reversal_bps >= config.watch_absolute_risk_reversal_bps
        or stress_score >= config.watch_stress_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: FXOptionsRiskReversalDigestConfig,
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
    risk_reversal_shift_bps: Decimal,
    absolute_risk_reversal_bps: Decimal,
    implied_volatility_z_score: Decimal,
    option_liquidity_stress_ratio: Decimal,
    skew_dislocation_ratio: Decimal,
    status: str,
    source_fresh: bool,
    config: FXOptionsRiskReversalDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("fx_options_risk_reversal_stress_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("fx_options_risk_reversal_stress_watch")
    else:
        reason_codes.append("fx_options_risk_reversal_stress_calm")
    reason_codes.append(
        "fx_options_risk_reversal_source_fresh"
        if source_fresh
        else "fx_options_risk_reversal_source_stale",
    )
    if risk_reversal_shift_bps > ZERO:
        reason_codes.append("fx_options_risk_reversal_steepening")
    elif risk_reversal_shift_bps < ZERO:
        reason_codes.append("fx_options_risk_reversal_flattening")
    else:
        reason_codes.append("fx_options_risk_reversal_inline")
    absolute_shift_bps = _abs_decimal(risk_reversal_shift_bps)
    if absolute_shift_bps >= config.blocked_risk_reversal_shift_bps:
        reason_codes.append("fx_options_risk_reversal_shift_blocked")
    elif absolute_shift_bps >= config.watch_risk_reversal_shift_bps:
        reason_codes.append("fx_options_risk_reversal_shift_watch")
    if absolute_risk_reversal_bps >= config.blocked_absolute_risk_reversal_bps:
        reason_codes.append("fx_options_risk_reversal_level_blocked")
    elif absolute_risk_reversal_bps >= config.watch_absolute_risk_reversal_bps:
        reason_codes.append("fx_options_risk_reversal_level_watch")
    if _abs_decimal(implied_volatility_z_score) >= Decimal("3.000000"):
        reason_codes.append("implied_volatility_z_high")
    if option_liquidity_stress_ratio >= Decimal("0.750000"):
        reason_codes.append("option_liquidity_stress_high")
    if skew_dislocation_ratio >= Decimal("0.750000"):
        reason_codes.append("skew_dislocation_high")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[FXOptionsRiskReversalDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("fx_options_risk_reversal_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[FXOptionsRiskReversalDigestRow, ...],
) -> tuple[FXOptionsRiskReversalReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("fx_options_risk_reversal_digest_empty",):
        return (
            FXOptionsRiskReversalReasonCodeCount(
                reason_code="fx_options_risk_reversal_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        FXOptionsRiskReversalReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[FXOptionsRiskReversalObservation],
) -> tuple[FXOptionsRiskReversalObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not FXOptionsRiskReversalObservation:
            raise ValueError("inputs must contain FXOptionsRiskReversalObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[FXOptionsRiskReversalDigestRow],
) -> tuple[FXOptionsRiskReversalDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not FXOptionsRiskReversalDigestRow:
            raise ValueError("rows must contain FXOptionsRiskReversalDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[FXOptionsRiskReversalReasonCodeCount],
) -> tuple[FXOptionsRiskReversalReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not FXOptionsRiskReversalReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain FXOptionsRiskReversalReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: FXOptionsRiskReversalDigestRow) -> None:
    if row.risk_reversal_shift_bps != _quantize_decimal(
        row.current_risk_reversal_bps - row.baseline_risk_reversal_bps,
    ):
        raise ValueError("risk_reversal_shift_bps must match current minus baseline")
    if row.absolute_risk_reversal_bps != _abs_decimal(row.current_risk_reversal_bps):
        raise ValueError("absolute_risk_reversal_bps must match current magnitude")
    if row.stress_score != _stress_score(
        risk_reversal_shift_bps=row.risk_reversal_shift_bps,
        absolute_risk_reversal_bps=row.absolute_risk_reversal_bps,
        implied_volatility_z_score=row.implied_volatility_z_score,
        option_liquidity_stress_ratio=row.option_liquidity_stress_ratio,
        skew_dislocation_ratio=row.skew_dislocation_ratio,
    ):
        raise ValueError("stress_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_status_code = (
        "fx_options_risk_reversal_stress_calm"
        if row.skew_status == PASS_STATUS
        else f"fx_options_risk_reversal_stress_{row.skew_status}"
    )
    if expected_status_code not in row.reason_codes:
        raise ValueError("skew_status must match reason_codes")


def _validate_report(report: FXOptionsRiskReversalDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_skew_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_skew_count must match rows")
    if report.watch_skew_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_skew_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "fx_options_risk_reversal_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.reversal_steepening_count != _reason_count(
        report.rows,
        "fx_options_risk_reversal_steepening",
    ):
        raise ValueError("reversal_steepening_count must match rows")
    if report.reversal_flattening_count != _reason_count(
        report.rows,
        "fx_options_risk_reversal_flattening",
    ):
        raise ValueError("reversal_flattening_count must match rows")
    if report.max_stress_score != _max_row_decimal(report.rows, "stress_score"):
        raise ValueError("max_stress_score must match rows")
    if report.average_stress_score != _ratio(
        _sum_decimal(row.stress_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_stress_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _digest_status(rows: tuple[FXOptionsRiskReversalDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.skew_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.skew_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(rows: tuple[FXOptionsRiskReversalDigestRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.skew_status == status))


def _reason_count(
    rows: tuple[FXOptionsRiskReversalDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[FXOptionsRiskReversalDigestRow, ...],
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
    row: FXOptionsRiskReversalDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.skew_status],
        -row.stress_score,
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
