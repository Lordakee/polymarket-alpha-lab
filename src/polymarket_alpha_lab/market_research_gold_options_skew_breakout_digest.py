"""Pure Phase 1 gold options skew breakout digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_GOLD_OPTIONS_SKEW_BREAKOUT_DIGEST_CONFIG_VERSION = (
    "market-research-gold-options-skew-breakout-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

WATCH_ABS_SKEW_Z_SCORE = Decimal("1.500000")
BLOCKED_ABS_SKEW_Z_SCORE = Decimal("2.500000")
WATCH_IMPLIED_VOL_CHANGE_PCT = Decimal("0.030000")
WATCH_REAL_YIELD_BETA_PRESSURE = Decimal("0.300000")
WATCH_ETF_FLOW_PROXY = Decimal("0.200000")
WATCH_FUTURES_OI_CHANGE_PCT = Decimal("0.040000")
WATCH_PRESSURE_SCORE = Decimal("0.500000")
BLOCKED_PRESSURE_SCORE = Decimal("0.800000")
MAX_SOURCE_AGE_SECONDS = Decimal("7200.000000")

SKEW_WEIGHT = Decimal("0.400000")
IMPLIED_VOL_WEIGHT = Decimal("0.200000")
REAL_YIELD_WEIGHT = Decimal("0.150000")
ETF_FLOW_WEIGHT = Decimal("0.150000")
FUTURES_OI_WEIGHT = Decimal("0.100000")
REPORT_MAX_PRESSURE_WEIGHT = Decimal("0.700000")
REPORT_BLOCKED_RATIO_WEIGHT = Decimal("0.300000")

BREAKOUT_STATUSES = ("blocked", "watch", "pass")
SKEW_DIRECTIONS = ("call", "put", "neutral")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
EMPTY_REASON_CODE = "gold_options_skew_breakout_digest_empty"
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_GOLD_OPTIONS_SKEW_BREAKOUT_DIGEST_CONFIG_VERSION",
    "GoldOptionsSkewBreakoutDigestConfig",
    "GoldOptionsSkewBreakoutObservation",
    "GoldOptionsSkewBreakoutDigestRow",
    "GoldOptionsSkewBreakoutReasonCodeCount",
    "GoldOptionsSkewBreakoutDigestReport",
    "build_market_research_gold_options_skew_breakout_digest",
    "market_research_gold_options_skew_breakout_digest_payload",
)


@dataclass(frozen=True)
class GoldOptionsSkewBreakoutDigestConfig:
    config_version: str = DEFAULT_GOLD_OPTIONS_SKEW_BREAKOUT_DIGEST_CONFIG_VERSION
    watch_abs_skew_z_score: Decimal = WATCH_ABS_SKEW_Z_SCORE
    blocked_abs_skew_z_score: Decimal = BLOCKED_ABS_SKEW_Z_SCORE
    watch_implied_vol_change_pct: Decimal = WATCH_IMPLIED_VOL_CHANGE_PCT
    watch_real_yield_beta_pressure: Decimal = WATCH_REAL_YIELD_BETA_PRESSURE
    watch_etf_flow_proxy: Decimal = WATCH_ETF_FLOW_PROXY
    watch_futures_oi_change_pct: Decimal = WATCH_FUTURES_OI_CHANGE_PCT
    watch_pressure_score: Decimal = WATCH_PRESSURE_SCORE
    blocked_pressure_score: Decimal = BLOCKED_PRESSURE_SCORE
    max_source_age_seconds: Decimal = MAX_SOURCE_AGE_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldOptionsSkewBreakoutDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_GOLD_OPTIONS_SKEW_BREAKOUT_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_abs_skew_z_score",
            "blocked_abs_skew_z_score",
            "watch_implied_vol_change_pct",
            "watch_real_yield_beta_pressure",
            "watch_etf_flow_proxy",
            "watch_futures_oi_change_pct",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_pressure_score", "blocked_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.blocked_abs_skew_z_score < self.watch_abs_skew_z_score:
            raise ValueError(
                "blocked_abs_skew_z_score must be at least watch_abs_skew_z_score",
            )
        if self.blocked_pressure_score < self.watch_pressure_score:
            raise ValueError(
                "blocked_pressure_score must be at least watch_pressure_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class GoldOptionsSkewBreakoutObservation:
    venue: str
    contract: str
    market_slug: str
    risk_reversal_skew_z_score: Decimal
    implied_vol_change_pct: Decimal
    real_yield_beta_pressure: Decimal
    etf_flow_proxy: Decimal
    futures_oi_change_pct: Decimal
    source_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldOptionsSkewBreakoutObservation, "observation")
        for field_name in ("venue", "contract", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "risk_reversal_skew_z_score",
            "implied_vol_change_pct",
            "real_yield_beta_pressure",
            "etf_flow_proxy",
            "futures_oi_change_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class GoldOptionsSkewBreakoutDigestRow:
    venue: str
    contract: str
    market_slug: str
    risk_reversal_skew_z_score: Decimal
    abs_skew_z_score: Decimal
    implied_vol_change_pct: Decimal
    real_yield_beta_pressure: Decimal
    etf_flow_proxy: Decimal
    futures_oi_change_pct: Decimal
    breakout_pressure_score: Decimal
    source_timestamp: datetime
    source_age_seconds: Decimal
    skew_direction: str
    breakout_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldOptionsSkewBreakoutDigestRow, "row")
        for field_name in ("venue", "contract", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "risk_reversal_skew_z_score",
            "implied_vol_change_pct",
            "real_yield_beta_pressure",
            "etf_flow_proxy",
            "futures_oi_change_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("abs_skew_z_score", "source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "breakout_pressure_score",
            _require_probability(
                "breakout_pressure_score",
                self.breakout_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        _require_member("skew_direction", self.skew_direction, SKEW_DIRECTIONS)
        _require_member("breakout_status", self.breakout_status, BREAKOUT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class GoldOptionsSkewBreakoutReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldOptionsSkewBreakoutReasonCodeCount, "count")
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("count", self)


@dataclass(frozen=True)
class GoldOptionsSkewBreakoutDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    max_abs_skew_z_score: Decimal
    max_breakout_pressure_score: Decimal
    average_breakout_pressure_score: Decimal
    blocked_row_ratio: Decimal
    report_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    reason_code_counts: tuple[GoldOptionsSkewBreakoutReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[GoldOptionsSkewBreakoutDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldOptionsSkewBreakoutDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_GOLD_OPTIONS_SKEW_BREAKOUT_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "max_abs_skew_z_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_breakout_pressure_score",
            "average_breakout_pressure_score",
            "blocked_row_ratio",
            "report_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, BREAKOUT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_gold_options_skew_breakout_digest(
    inputs: Iterable[GoldOptionsSkewBreakoutObservation],
    *,
    config: GoldOptionsSkewBreakoutDigestConfig,
    generated_at: datetime,
) -> GoldOptionsSkewBreakoutDigestReport:
    if type(config) is not GoldOptionsSkewBreakoutDigestConfig:
        raise ValueError("config must be exactly GoldOptionsSkewBreakoutDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    row_count = _count_decimal(len(rows))
    blocked_count = _status_count(rows, "blocked")
    blocked_row_ratio = _ratio(blocked_count, row_count)
    max_breakout_pressure_score = _max_row_decimal(rows, "breakout_pressure_score")

    return GoldOptionsSkewBreakoutDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=row_count,
        blocked_count=blocked_count,
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        stale_source_count=_reason_count(rows, "gold_options_source_stale"),
        max_abs_skew_z_score=_max_row_decimal(rows, "abs_skew_z_score"),
        max_breakout_pressure_score=max_breakout_pressure_score,
        average_breakout_pressure_score=_ratio(
            _sum_decimal(row.breakout_pressure_score for row in rows),
            row_count,
        ),
        blocked_row_ratio=blocked_row_ratio,
        report_risk_score=_report_risk_score(
            max_breakout_pressure_score,
            blocked_row_ratio,
        ),
        digest_status=_digest_status(rows),
        recommended_next_step=_recommended_next_step(_digest_status(rows)),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        rows=rows,
    )


def market_research_gold_options_skew_breakout_digest_payload(
    report: GoldOptionsSkewBreakoutDigestReport,
) -> dict[str, Any]:
    if type(report) is not GoldOptionsSkewBreakoutDigestReport:
        raise ValueError("report must be exactly GoldOptionsSkewBreakoutDigestReport")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_observation(
    value: GoldOptionsSkewBreakoutObservation,
    *,
    config: GoldOptionsSkewBreakoutDigestConfig,
    generated_at: datetime,
) -> GoldOptionsSkewBreakoutDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.source_timestamp)
    source_is_fresh = source_age_seconds <= config.max_source_age_seconds
    abs_skew_z_score = _quantize(abs(value.risk_reversal_skew_z_score))
    breakout_pressure_score = _breakout_pressure_score(value, config=config)
    breakout_status = _breakout_status(
        abs_skew_z_score=abs_skew_z_score,
        breakout_pressure_score=breakout_pressure_score,
        source_is_fresh=source_is_fresh,
        config=config,
    )
    return GoldOptionsSkewBreakoutDigestRow(
        venue=value.venue,
        contract=value.contract,
        market_slug=value.market_slug,
        risk_reversal_skew_z_score=value.risk_reversal_skew_z_score,
        abs_skew_z_score=abs_skew_z_score,
        implied_vol_change_pct=value.implied_vol_change_pct,
        real_yield_beta_pressure=value.real_yield_beta_pressure,
        etf_flow_proxy=value.etf_flow_proxy,
        futures_oi_change_pct=value.futures_oi_change_pct,
        breakout_pressure_score=breakout_pressure_score,
        source_timestamp=value.source_timestamp,
        source_age_seconds=source_age_seconds,
        skew_direction=_skew_direction(value.risk_reversal_skew_z_score, config=config),
        breakout_status=breakout_status,
        reason_codes=_row_reason_codes(
            value,
            abs_skew_z_score=abs_skew_z_score,
            breakout_pressure_score=breakout_pressure_score,
            breakout_status=breakout_status,
            source_is_fresh=source_is_fresh,
            config=config,
        ),
    )


def _breakout_pressure_score(
    value: GoldOptionsSkewBreakoutObservation,
    *,
    config: GoldOptionsSkewBreakoutDigestConfig,
) -> Decimal:
    return _quantize(
        _weighted_component(
            _quantize(abs(value.risk_reversal_skew_z_score)),
            config.blocked_abs_skew_z_score,
            SKEW_WEIGHT,
        )
        + _weighted_component(
            _positive_decimal(value.implied_vol_change_pct),
            config.watch_implied_vol_change_pct,
            IMPLIED_VOL_WEIGHT,
        )
        + _weighted_component(
            _positive_decimal(value.real_yield_beta_pressure),
            config.watch_real_yield_beta_pressure,
            REAL_YIELD_WEIGHT,
        )
        + _weighted_component(
            _positive_decimal(value.etf_flow_proxy),
            config.watch_etf_flow_proxy,
            ETF_FLOW_WEIGHT,
        )
        + _weighted_component(
            _positive_decimal(value.futures_oi_change_pct),
            config.watch_futures_oi_change_pct,
            FUTURES_OI_WEIGHT,
        ),
    )


def _weighted_component(value: Decimal, threshold: Decimal, weight: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if threshold <= ZERO:
            raise ValueError("threshold must be positive")
        return _quantize(min(value / threshold, ONE) * weight)


def _positive_decimal(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    return value


def _breakout_status(
    *,
    abs_skew_z_score: Decimal,
    breakout_pressure_score: Decimal,
    source_is_fresh: bool,
    config: GoldOptionsSkewBreakoutDigestConfig,
) -> str:
    if (
        abs_skew_z_score >= config.blocked_abs_skew_z_score
        or breakout_pressure_score >= config.blocked_pressure_score
    ):
        return "blocked"
    if (
        abs_skew_z_score >= config.watch_abs_skew_z_score
        or breakout_pressure_score >= config.watch_pressure_score
        or not source_is_fresh
    ):
        return "watch"
    return "pass"


def _skew_direction(
    risk_reversal_skew_z_score: Decimal,
    *,
    config: GoldOptionsSkewBreakoutDigestConfig,
) -> str:
    if abs(risk_reversal_skew_z_score) < config.watch_abs_skew_z_score:
        return "neutral"
    if risk_reversal_skew_z_score > ZERO:
        return "call"
    return "put"


def _row_reason_codes(
    value: GoldOptionsSkewBreakoutObservation,
    *,
    abs_skew_z_score: Decimal,
    breakout_pressure_score: Decimal,
    breakout_status: str,
    source_is_fresh: bool,
    config: GoldOptionsSkewBreakoutDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(value.upstream_reason_codes)
    if abs_skew_z_score >= config.blocked_abs_skew_z_score:
        reason_codes.append("gold_options_skew_blocked")
    elif abs_skew_z_score >= config.watch_abs_skew_z_score:
        reason_codes.append("gold_options_skew_watch")
    if value.implied_vol_change_pct >= config.watch_implied_vol_change_pct:
        reason_codes.append("gold_options_iv_pressure_watch")
    if value.real_yield_beta_pressure >= config.watch_real_yield_beta_pressure:
        reason_codes.append("gold_options_real_yield_pressure_watch")
    if value.etf_flow_proxy >= config.watch_etf_flow_proxy:
        reason_codes.append("gold_options_etf_flow_pressure_watch")
    if value.futures_oi_change_pct >= config.watch_futures_oi_change_pct:
        reason_codes.append("gold_options_futures_oi_pressure_watch")
    if breakout_pressure_score >= config.blocked_pressure_score:
        reason_codes.append("gold_options_pressure_score_blocked")
    elif breakout_pressure_score >= config.watch_pressure_score:
        reason_codes.append("gold_options_pressure_score_watch")
    if breakout_status == "pass":
        reason_codes.append("gold_options_pressure_pass")
    reason_codes.append(
        f"gold_options_skew_direction_{_skew_direction(value.risk_reversal_skew_z_score, config=config)}",
    )
    reason_codes.append(
        "gold_options_source_fresh" if source_is_fresh else "gold_options_source_stale",
    )
    return _normalize_reason_codes(tuple(reason_codes))


def _digest_status(rows: tuple[GoldOptionsSkewBreakoutDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.breakout_status == "blocked" for row in rows):
        return "blocked"
    if any(row.breakout_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_gold_options_skew_breakout_digest"
    if status == "watch":
        return "monitor_report_only_market_research_gold_options_skew_breakout_digest"
    return "block_report_only_market_research_gold_options_skew_breakout_digest"


def _reason_code_counts(
    rows: tuple[GoldOptionsSkewBreakoutDigestRow, ...],
) -> tuple[GoldOptionsSkewBreakoutReasonCodeCount, ...]:
    if not rows:
        return (
            GoldOptionsSkewBreakoutReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code=reason_code,
            count=_quantize(count),
            row_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _report_risk_score(
    max_breakout_pressure_score: Decimal,
    blocked_row_ratio: Decimal,
) -> Decimal:
    return _quantize(
        max_breakout_pressure_score * REPORT_MAX_PRESSURE_WEIGHT
        + blocked_row_ratio * REPORT_BLOCKED_RATIO_WEIGHT,
    )


def _normalize_inputs(
    inputs: Iterable[GoldOptionsSkewBreakoutObservation],
) -> tuple[GoldOptionsSkewBreakoutObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must contain gold options skew observations")
    normalized = tuple(inputs)
    seen: set[tuple[str, str, str]] = set()
    for value in normalized:
        if type(value) is not GoldOptionsSkewBreakoutObservation:
            raise ValueError(
                "inputs must contain GoldOptionsSkewBreakoutObservation",
            )
        _require_hard_flags("observation", value)
        key = (value.venue, value.contract, value.market_slug)
        if key in seen:
            raise ValueError("inputs must not contain duplicate gold options surfaces")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: Iterable[GoldOptionsSkewBreakoutDigestRow],
) -> tuple[GoldOptionsSkewBreakoutDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain gold options skew digest rows")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not GoldOptionsSkewBreakoutDigestRow:
            raise ValueError("rows must contain GoldOptionsSkewBreakoutDigestRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({(row.venue, row.contract, row.market_slug) for row in normalized}) != len(
        normalized,
    ):
        raise ValueError("rows must not contain duplicate gold options surfaces")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[GoldOptionsSkewBreakoutReasonCodeCount],
) -> tuple[GoldOptionsSkewBreakoutReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not GoldOptionsSkewBreakoutReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain GoldOptionsSkewBreakoutReasonCodeCount",
            )
        _require_hard_flags("count", item)
    if normalized != tuple(sorted(normalized, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return normalized


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must contain reason code strings")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _validate_row(row: GoldOptionsSkewBreakoutDigestRow) -> None:
    if row.abs_skew_z_score != _quantize(abs(row.risk_reversal_skew_z_score)):
        raise ValueError("abs_skew_z_score must match risk_reversal_skew_z_score")
    expected_direction_reason = f"gold_options_skew_direction_{row.skew_direction}"
    if expected_direction_reason not in row.reason_codes:
        raise ValueError("skew_direction must match reason_codes")
    if row.breakout_status == "pass" and "gold_options_pressure_pass" not in row.reason_codes:
        raise ValueError("pass rows must include pass reason code")
    if row.breakout_status == "blocked" and not any(
        reason_code.endswith("_blocked") for reason_code in row.reason_codes
    ):
        raise ValueError("blocked rows must include blocked reason code")


def _validate_report(report: GoldOptionsSkewBreakoutDigestReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "gold_options_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_abs_skew_z_score != _max_row_decimal(report.rows, "abs_skew_z_score"):
        raise ValueError("max_abs_skew_z_score must match rows")
    if report.max_breakout_pressure_score != _max_row_decimal(
        report.rows,
        "breakout_pressure_score",
    ):
        raise ValueError("max_breakout_pressure_score must match rows")
    if report.average_breakout_pressure_score != _ratio(
        _sum_decimal(row.breakout_pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_breakout_pressure_score must match rows")
    if report.blocked_row_ratio != _ratio(report.blocked_count, report.row_count):
        raise ValueError("blocked_row_ratio must match rows")
    if report.report_risk_score != _report_risk_score(
        report.max_breakout_pressure_score,
        report.blocked_row_ratio,
    ):
        raise ValueError("report_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    expected_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in expected_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _status_count(
    rows: tuple[GoldOptionsSkewBreakoutDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.breakout_status == status))


def _reason_count(
    rows: tuple[GoldOptionsSkewBreakoutDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[GoldOptionsSkewBreakoutDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("source_timestamp must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(whole_seconds + fractional_seconds)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: GoldOptionsSkewBreakoutDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.breakout_status],
        -row.breakout_pressure_score,
        -row.abs_skew_z_score,
        row.venue,
        row.contract,
        row.market_slug,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    return value
