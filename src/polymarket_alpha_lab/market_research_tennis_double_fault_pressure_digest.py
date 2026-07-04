"""Pure report-only tennis double-fault pressure digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_DOUBLE_FAULT_PRESSURE_DIGEST_CONFIG_VERSION",
    "TennisDoubleFaultPressureDigestConfig",
    "TennisDoubleFaultPressureObservation",
    "TennisDoubleFaultPressureDigestRow",
    "TennisDoubleFaultPressureReasonCodeCount",
    "TennisDoubleFaultPressureDigestReport",
    "build_market_research_tennis_double_fault_pressure_digest",
    "market_research_tennis_double_fault_pressure_digest_payload",
)


DEFAULT_MARKET_RESEARCH_TENNIS_DOUBLE_FAULT_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-double-fault-pressure-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PRESSURE_DIRECTION = "double_fault_pressure"
RESILIENT_DIRECTION = "serve_hold_resilient"

EMPTY_STATUS = "empty"
BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
PRESSURE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
DIGEST_STATUSES = (EMPTY_STATUS, BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
RECOMMENDED_NEXT_STEPS = {
    EMPTY_STATUS: "monitor_report_only_market_research_tennis_double_fault_pressure_digest",
    BLOCKED_STATUS: "block_report_only_market_research_tennis_double_fault_pressure_digest",
    WATCH_STATUS: "monitor_report_only_market_research_tennis_double_fault_pressure_digest",
    PASS_STATUS: "allow_report_only_market_research_tennis_double_fault_pressure_digest",
}

STANDARD_REASON_ORDER = (
    "tennis_double_fault_pressure_digest_empty",
    "double_fault_pressure_blocked",
    "double_fault_pressure_watch",
    "double_fault_pressure_calm",
    "source_fresh",
    "source_stale",
    "double_fault_rate_high",
    "first_serve_instability",
    "second_serve_exposed",
    "break_point_pressure_high",
    "low_service_game_sample",
    "market_probability_move_up",
)


@dataclass(frozen=True)
class TennisDoubleFaultPressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_DOUBLE_FAULT_PRESSURE_DIGEST_CONFIG_VERSION
    )
    watch_pressure_score: Decimal = Decimal("0.450000")
    blocked_pressure_score: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    calm_confidence_cap: Decimal = Decimal("0.650000")
    min_recent_service_games: Decimal = Decimal("20.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisDoubleFaultPressureDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_DOUBLE_FAULT_PRESSURE_DIGEST_CONFIG_VERSION
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
        object.__setattr__(
            self,
            "min_recent_service_games",
            _normalize_positive_decimal(
                "min_recent_service_games",
                self.min_recent_service_games,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisDoubleFaultPressureObservation:
    source_id: str
    event_id: str
    market_slug: str
    player_id: str
    opponent_id: str
    tournament: str
    surface: str
    double_fault_rate: Decimal
    first_serve_in_rate: Decimal
    second_serve_points_won_rate: Decimal
    break_point_pressure_rate: Decimal
    recent_service_game_count: Decimal
    implied_probability_move: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisDoubleFaultPressureObservation, "observation")
        for field_name in (
            "source_id",
            "event_id",
            "market_slug",
            "player_id",
            "opponent_id",
            "tournament",
            "surface",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "double_fault_rate",
            "first_serve_in_rate",
            "second_serve_points_won_rate",
            "break_point_pressure_rate",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_service_game_count",
            _normalize_nonnegative_decimal(
                "recent_service_game_count",
                self.recent_service_game_count,
            ),
        )
        object.__setattr__(
            self,
            "implied_probability_move",
            _normalize_signed_probability(
                "implied_probability_move",
                self.implied_probability_move,
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
class TennisDoubleFaultPressureDigestRow:
    source_id: str
    event_id: str
    market_slug: str
    player_id: str
    opponent_id: str
    tournament: str
    surface: str
    double_fault_rate: Decimal
    first_serve_in_rate: Decimal
    second_serve_points_won_rate: Decimal
    break_point_pressure_rate: Decimal
    recent_service_game_count: Decimal
    implied_probability_move: Decimal
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
        _require_exact_type(self, TennisDoubleFaultPressureDigestRow, "row")
        for field_name in (
            "source_id",
            "event_id",
            "market_slug",
            "player_id",
            "opponent_id",
            "tournament",
            "surface",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "double_fault_rate",
            "first_serve_in_rate",
            "second_serve_points_won_rate",
            "break_point_pressure_rate",
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
        object.__setattr__(
            self,
            "recent_service_game_count",
            _normalize_nonnegative_decimal(
                "recent_service_game_count",
                self.recent_service_game_count,
            ),
        )
        object.__setattr__(
            self,
            "implied_probability_move",
            _normalize_signed_probability(
                "implied_probability_move",
                self.implied_probability_move,
            ),
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
class TennisDoubleFaultPressureReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisDoubleFaultPressureReasonCodeCount, "count")
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
class TennisDoubleFaultPressureDigestReport:
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
    digest_status: str
    recommended_next_step: str
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TennisDoubleFaultPressureReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisDoubleFaultPressureDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_DOUBLE_FAULT_PRESSURE_DIGEST_CONFIG_VERSION
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


def build_market_research_tennis_double_fault_pressure_digest(
    inputs: Iterable[TennisDoubleFaultPressureObservation],
    *,
    config: TennisDoubleFaultPressureDigestConfig,
    generated_at: datetime,
) -> TennisDoubleFaultPressureDigestReport:
    if type(config) is not TennisDoubleFaultPressureDigestConfig:
        raise ValueError(
            "config must be exactly TennisDoubleFaultPressureDigestConfig",
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
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return TennisDoubleFaultPressureDigestReport(
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
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_tennis_double_fault_pressure_digest_payload(
    report: TennisDoubleFaultPressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not TennisDoubleFaultPressureDigestReport:
        raise ValueError(
            "report must be exactly TennisDoubleFaultPressureDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    value: TennisDoubleFaultPressureObservation,
    *,
    config: TennisDoubleFaultPressureDigestConfig,
    generated_at: datetime,
) -> TennisDoubleFaultPressureDigestRow:
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
    return TennisDoubleFaultPressureDigestRow(
        source_id=value.source_id,
        event_id=value.event_id,
        market_slug=value.market_slug,
        player_id=value.player_id,
        opponent_id=value.opponent_id,
        tournament=value.tournament,
        surface=value.surface,
        double_fault_rate=value.double_fault_rate,
        first_serve_in_rate=value.first_serve_in_rate,
        second_serve_points_won_rate=value.second_serve_points_won_rate,
        break_point_pressure_rate=value.break_point_pressure_rate,
        recent_service_game_count=value.recent_service_game_count,
        implied_probability_move=value.implied_probability_move,
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
            config=config,
        ),
    )


def _pressure_score(value: TennisDoubleFaultPressureObservation) -> Decimal:
    return _pressure_score_from_values(
        double_fault_rate=value.double_fault_rate,
        first_serve_in_rate=value.first_serve_in_rate,
        second_serve_points_won_rate=value.second_serve_points_won_rate,
        break_point_pressure_rate=value.break_point_pressure_rate,
    )


def _pressure_score_from_values(
    *,
    double_fault_rate: Decimal,
    first_serve_in_rate: Decimal,
    second_serve_points_won_rate: Decimal,
    break_point_pressure_rate: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        double_fault_component = _clamp_probability(
            double_fault_rate / Decimal("0.150000"),
        )
        first_serve_component = _clamp_probability(
            (Decimal("0.650000") - first_serve_in_rate) / Decimal("0.250000"),
        )
        second_serve_component = _clamp_probability(
            (Decimal("0.550000") - second_serve_points_won_rate)
            / Decimal("0.250000"),
        )
        raw_score = (
            double_fault_component * Decimal("0.450000")
            + first_serve_component * Decimal("0.200000")
            + second_serve_component * Decimal("0.250000")
            + break_point_pressure_rate * Decimal("0.100000")
        )
    return _quantize_decimal(raw_score)


def _pressure_status(
    pressure_score: Decimal,
    *,
    config: TennisDoubleFaultPressureDigestConfig,
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
    config: TennisDoubleFaultPressureDigestConfig,
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
    value: TennisDoubleFaultPressureObservation,
    status: str,
    source_fresh: bool,
    config: TennisDoubleFaultPressureDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("double_fault_pressure_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("double_fault_pressure_watch")
    else:
        reason_codes.append("double_fault_pressure_calm")
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    if value.double_fault_rate >= Decimal("0.100000"):
        reason_codes.append("double_fault_rate_high")
    if value.first_serve_in_rate <= Decimal("0.550000"):
        reason_codes.append("first_serve_instability")
    if value.second_serve_points_won_rate <= Decimal("0.450000"):
        reason_codes.append("second_serve_exposed")
    if value.break_point_pressure_rate >= Decimal("0.650000"):
        reason_codes.append("break_point_pressure_high")
    if value.recent_service_game_count < config.min_recent_service_games:
        reason_codes.append("low_service_game_sample")
    if value.implied_probability_move >= Decimal("0.050000"):
        reason_codes.append("market_probability_move_up")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("tennis_double_fault_pressure_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...],
) -> tuple[TennisDoubleFaultPressureReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        TennisDoubleFaultPressureReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[TennisDoubleFaultPressureObservation],
) -> tuple[TennisDoubleFaultPressureObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not TennisDoubleFaultPressureObservation:
            raise ValueError("inputs must contain TennisDoubleFaultPressureObservation")
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[TennisDoubleFaultPressureDigestRow],
) -> tuple[TennisDoubleFaultPressureDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TennisDoubleFaultPressureDigestRow:
            raise ValueError("rows must contain TennisDoubleFaultPressureDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[TennisDoubleFaultPressureReasonCodeCount],
) -> tuple[TennisDoubleFaultPressureReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not TennisDoubleFaultPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain TennisDoubleFaultPressureReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: _reason_sort_key(value.reason_code)))


def _validate_row(row: TennisDoubleFaultPressureDigestRow) -> None:
    if row.pressure_score != _pressure_score_from_values(
        double_fault_rate=row.double_fault_rate,
        first_serve_in_rate=row.first_serve_in_rate,
        second_serve_points_won_rate=row.second_serve_points_won_rate,
        break_point_pressure_rate=row.break_point_pressure_rate,
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


def _validate_report(report: TennisDoubleFaultPressureDigestReport) -> None:
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


def _digest_status(rows: tuple[TennisDoubleFaultPressureDigestRow, ...]) -> str:
    if not rows:
        return EMPTY_STATUS
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_status == status))


def _direction_count(
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.pressure_direction == direction))


def _reason_count(
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[TennisDoubleFaultPressureDigestRow, ...],
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


def _normalize_signed_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
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
    row: TennisDoubleFaultPressureDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.pressure_status],
        -row.pressure_score,
        row.event_id,
        row.market_slug,
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
