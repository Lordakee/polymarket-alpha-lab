"""Pure report-only tennis second-serve pressure digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_SECOND_SERVE_PRESSURE_DIGEST_CONFIG_VERSION",
    "TennisSecondServePressureDigestConfig",
    "TennisSecondServePressureObservation",
    "TennisSecondServePressureDigestRow",
    "TennisSecondServePressureReasonCodeCount",
    "TennisSecondServePressureDigestReport",
    "build_market_research_tennis_second_serve_pressure_digest",
    "market_research_tennis_second_serve_pressure_digest_payload",
)


DEFAULT_MARKET_RESEARCH_TENNIS_SECOND_SERVE_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-second-serve-pressure-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PRESSURE_DIRECTION = "second_serve_pressure"
RESILIENT_DIRECTION = "second_serve_resilient"

EMPTY_STATUS = "empty"
BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
PRESSURE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
DIGEST_STATUSES = (EMPTY_STATUS, BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
MARKET_TYPES = ("match", "set", "game")
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
RECOMMENDED_NEXT_STEPS = {
    EMPTY_STATUS: "monitor_report_only_market_research_tennis_second_serve_pressure_digest",
    BLOCKED_STATUS: "block_report_only_market_research_tennis_second_serve_pressure_digest",
    WATCH_STATUS: "monitor_report_only_market_research_tennis_second_serve_pressure_digest",
    PASS_STATUS: "allow_report_only_market_research_tennis_second_serve_pressure_digest",
}

STANDARD_REASON_ORDER = (
    "tennis_second_serve_pressure_digest_empty",
    "second_serve_pressure_blocked",
    "second_serve_pressure_watch",
    "second_serve_pressure_calm",
    "source_fresh",
    "source_stale",
    "second_serve_win_rate_drop_high",
    "double_fault_pressure_high",
    "break_point_exposure_high",
    "fast_surface_amplifies_second_serve",
    "fatigue_travel_pressure_high",
)


@dataclass(frozen=True)
class TennisSecondServePressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_SECOND_SERVE_PRESSURE_DIGEST_CONFIG_VERSION
    )
    watch_pressure_score: Decimal = Decimal("0.450000")
    blocked_pressure_score: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    calm_confidence_cap: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisSecondServePressureDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_SECOND_SERVE_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_pressure_score", "blocked_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_pressure_score > self.blocked_pressure_score:
            raise ValueError(
                "watch_pressure_score must not exceed blocked_pressure_score",
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in ("stale_confidence_cap", "calm_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisSecondServePressureObservation:
    source_id: str
    event_id: str
    market_type: str
    market_slug: str
    player: str
    opponent: str
    tournament: str
    surface: str
    second_serve_win_rate_drop: Decimal
    double_fault_pressure: Decimal
    break_point_exposure: Decimal
    surface_speed_adjustment: Decimal
    fatigue_travel_score: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisSecondServePressureObservation, "observation")
        for field_name in (
            "source_id",
            "event_id",
            "market_slug",
            "player",
            "opponent",
            "tournament",
            "surface",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        for field_name in (
            "second_serve_win_rate_drop",
            "double_fault_pressure",
            "break_point_exposure",
            "surface_speed_adjustment",
            "fatigue_travel_score",
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
class TennisSecondServePressureDigestRow:
    source_id: str
    event_id: str
    market_type: str
    market_slug: str
    player: str
    opponent: str
    tournament: str
    surface: str
    second_serve_win_rate_drop: Decimal
    double_fault_pressure: Decimal
    break_point_exposure: Decimal
    surface_speed_adjustment: Decimal
    fatigue_travel_score: Decimal
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
        _require_exact_type(self, TennisSecondServePressureDigestRow, "row")
        for field_name in (
            "source_id",
            "event_id",
            "market_slug",
            "player",
            "opponent",
            "tournament",
            "surface",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        for field_name in (
            "second_serve_win_rate_drop",
            "double_fault_pressure",
            "break_point_exposure",
            "surface_speed_adjustment",
            "fatigue_travel_score",
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
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _require_member(
            "pressure_direction",
            self.pressure_direction,
            (PRESSURE_DIRECTION, RESILIENT_DIRECTION),
        )
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisSecondServePressureReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisSecondServePressureReasonCodeCount, "count")
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
class TennisSecondServePressureDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_pressure_count: Decimal
    watch_pressure_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    pressure_signal_count: Decimal
    max_pressure_score: Decimal
    average_pressure_score: Decimal
    risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[TennisSecondServePressureDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TennisSecondServePressureReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisSecondServePressureDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_SECOND_SERVE_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_pressure_count",
            "watch_pressure_count",
            "pass_count",
            "stale_source_count",
            "pressure_signal_count",
            "max_pressure_score",
            "average_pressure_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
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


def build_market_research_tennis_second_serve_pressure_digest(
    inputs: Iterable[TennisSecondServePressureObservation],
    *,
    config: TennisSecondServePressureDigestConfig,
    generated_at: datetime,
) -> TennisSecondServePressureDigestReport:
    if type(config) is not TennisSecondServePressureDigestConfig:
        raise ValueError(
            "config must be exactly TennisSecondServePressureDigestConfig",
        )
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
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    reason_codes = _report_reason_codes(rows)
    return TennisSecondServePressureDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_pressure_count=_status_count(rows, BLOCKED_STATUS),
        watch_pressure_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "source_stale"),
        pressure_signal_count=_direction_count(rows, PRESSURE_DIRECTION),
        max_pressure_score=_max_row_decimal(rows, "pressure_score"),
        average_pressure_score=_ratio(
            _sum_decimal(row.pressure_score for row in rows),
            row_count,
        ),
        risk_score=_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_tennis_second_serve_pressure_digest_payload(
    report: TennisSecondServePressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not TennisSecondServePressureDigestReport:
        raise ValueError(
            "report must be exactly TennisSecondServePressureDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    value: TennisSecondServePressureObservation,
    *,
    config: TennisSecondServePressureDigestConfig,
    generated_at: datetime,
) -> TennisSecondServePressureDigestRow:
    pressure_score = _pressure_score(value)
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _pressure_status(pressure_score, config=config)
    direction = PRESSURE_DIRECTION if status != PASS_STATUS else RESILIENT_DIRECTION
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return TennisSecondServePressureDigestRow(
        source_id=value.source_id,
        event_id=value.event_id,
        market_type=value.market_type,
        market_slug=value.market_slug,
        player=value.player,
        opponent=value.opponent,
        tournament=value.tournament,
        surface=value.surface,
        second_serve_win_rate_drop=value.second_serve_win_rate_drop,
        double_fault_pressure=value.double_fault_pressure,
        break_point_exposure=value.break_point_exposure,
        surface_speed_adjustment=value.surface_speed_adjustment,
        fatigue_travel_score=value.fatigue_travel_score,
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


def _pressure_score(value: TennisSecondServePressureObservation) -> Decimal:
    return _pressure_score_from_values(
        second_serve_win_rate_drop=value.second_serve_win_rate_drop,
        double_fault_pressure=value.double_fault_pressure,
        break_point_exposure=value.break_point_exposure,
        surface_speed_adjustment=value.surface_speed_adjustment,
        fatigue_travel_score=value.fatigue_travel_score,
    )


def _pressure_score_from_values(
    *,
    second_serve_win_rate_drop: Decimal,
    double_fault_pressure: Decimal,
    break_point_exposure: Decimal,
    surface_speed_adjustment: Decimal,
    fatigue_travel_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            second_serve_win_rate_drop * Decimal("0.350000")
            + double_fault_pressure * Decimal("0.200000")
            + break_point_exposure * Decimal("0.200000")
            + surface_speed_adjustment * Decimal("0.100000")
            + fatigue_travel_score * Decimal("0.150000")
        )
    return _clamp_probability(_quantize_decimal(raw_score))


def _pressure_status(
    pressure_score: Decimal,
    *,
    config: TennisSecondServePressureDigestConfig,
) -> str:
    if pressure_score >= config.blocked_pressure_score:
        return BLOCKED_STATUS
    if pressure_score >= config.watch_pressure_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: TennisSecondServePressureDigestConfig,
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
    value: TennisSecondServePressureObservation,
    status: str,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("second_serve_pressure_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("second_serve_pressure_watch")
    else:
        reason_codes.append("second_serve_pressure_calm")
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    if value.second_serve_win_rate_drop >= Decimal("0.250000"):
        reason_codes.append("second_serve_win_rate_drop_high")
    if value.double_fault_pressure >= Decimal("0.600000"):
        reason_codes.append("double_fault_pressure_high")
    if value.break_point_exposure >= Decimal("0.650000"):
        reason_codes.append("break_point_exposure_high")
    if value.surface_speed_adjustment >= Decimal("0.500000"):
        reason_codes.append("fast_surface_amplifies_second_serve")
    if value.fatigue_travel_score >= Decimal("0.650000"):
        reason_codes.append("fatigue_travel_pressure_high")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[TennisSecondServePressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("tennis_second_serve_pressure_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[TennisSecondServePressureDigestRow, ...],
) -> tuple[TennisSecondServePressureReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        TennisSecondServePressureReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[TennisSecondServePressureObservation],
) -> tuple[TennisSecondServePressureObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not TennisSecondServePressureObservation:
            raise ValueError("inputs must contain TennisSecondServePressureObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[TennisSecondServePressureDigestRow],
) -> tuple[TennisSecondServePressureDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TennisSecondServePressureDigestRow:
            raise ValueError("rows must contain TennisSecondServePressureDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[TennisSecondServePressureReasonCodeCount],
) -> tuple[TennisSecondServePressureReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not TennisSecondServePressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain TennisSecondServePressureReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: _reason_sort_key(value.reason_code)))


def _validate_row(row: TennisSecondServePressureDigestRow) -> None:
    if row.pressure_score != _pressure_score_from_values(
        second_serve_win_rate_drop=row.second_serve_win_rate_drop,
        double_fault_pressure=row.double_fault_pressure,
        break_point_exposure=row.break_point_exposure,
        surface_speed_adjustment=row.surface_speed_adjustment,
        fatigue_travel_score=row.fatigue_travel_score,
    ):
        raise ValueError("pressure_score must match row factors")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.capped_confidence > row.base_confidence:
        raise ValueError("capped_confidence must not exceed base_confidence")
    if row.pressure_status == PASS_STATUS and row.pressure_direction != RESILIENT_DIRECTION:
        raise ValueError("pressure_direction must match pressure_status")
    if row.pressure_status != PASS_STATUS and row.pressure_direction != PRESSURE_DIRECTION:
        raise ValueError("pressure_direction must match pressure_status")


def _validate_report(report: TennisSecondServePressureDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if (
        report.blocked_pressure_count
        + report.watch_pressure_count
        + report.pass_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.pressure_signal_count != _direction_count(report.rows, PRESSURE_DIRECTION):
        raise ValueError("pressure_signal_count must match rows")
    if report.max_pressure_score != _max_row_decimal(report.rows, "pressure_score"):
        raise ValueError("max_pressure_score must match rows")
    if report.average_pressure_score != _ratio(
        _sum_decimal(row.pressure_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_pressure_score must match rows")
    if report.risk_score != _risk_score(report.rows):
        raise ValueError("risk_score must match rows")
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


def _digest_status(rows: tuple[TennisSecondServePressureDigestRow, ...]) -> str:
    if not rows:
        return EMPTY_STATUS
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _risk_score(rows: tuple[TennisSecondServePressureDigestRow, ...]) -> Decimal:
    row_count = _count_decimal(len(rows))
    if row_count == ZERO:
        return ZERO
    pressure_ratio = _ratio(
        _status_count(rows, BLOCKED_STATUS) + _status_count(rows, WATCH_STATUS),
        row_count,
    )
    max_score = _max_row_decimal(rows, "pressure_score")
    average_score = _ratio(
        _sum_decimal(row.pressure_score for row in rows),
        row_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        score = (
            max_score * Decimal("0.500000")
            + average_score * Decimal("0.300000")
            + pressure_ratio * Decimal("0.200000")
        )
    return _clamp_probability(_quantize_decimal(score))


def _status_count(
    rows: tuple[TennisSecondServePressureDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_status == status))


def _direction_count(
    rows: tuple[TennisSecondServePressureDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_direction == direction))


def _reason_count(
    rows: tuple[TennisSecondServePressureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[TennisSecondServePressureDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must contain Decimal entries")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
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


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


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
    return tuple(sorted(normalized, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[Decimal, Decimal, str]:
    if reason_code in STANDARD_REASON_ORDER:
        return (
            ZERO,
            _count_decimal(STANDARD_REASON_ORDER.index(reason_code)),
            reason_code,
        )
    return (ONE, ZERO, reason_code)


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: TennisSecondServePressureDigestRow,
) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.pressure_status],
        -row.pressure_score,
        row.event_id,
        row.market_slug,
        row.player,
        row.source_id,
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
    return value
