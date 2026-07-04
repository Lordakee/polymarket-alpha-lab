"""Pure report-only tennis tiebreak pressure fatigue digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_TIEBREAK_PRESSURE_FATIGUE_DIGEST_CONFIG_VERSION",
    "TennisTiebreakPressureFatigueDigestConfig",
    "TennisTiebreakPressureFatigueObservation",
    "TennisTiebreakPressureFatigueDigestRow",
    "TennisTiebreakPressureFatigueReasonCodeCount",
    "TennisTiebreakPressureFatigueDigestReport",
    "build_market_research_tennis_tiebreak_pressure_fatigue_digest",
    "market_research_tennis_tiebreak_pressure_fatigue_digest_payload",
)


DEFAULT_MARKET_RESEARCH_TENNIS_TIEBREAK_PRESSURE_FATIGUE_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-tiebreak-pressure-fatigue-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EMPTY_STATUS = "empty"
BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
PRESSURE_FATIGUE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
DIGEST_STATUSES = (EMPTY_STATUS, BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)

PRESSURE_FATIGUE_DIRECTION = "tiebreak_pressure_fatigue"
RESILIENT_DIRECTION = "tiebreak_pressure_resilient"
PRESSURE_FATIGUE_DIRECTIONS = (PRESSURE_FATIGUE_DIRECTION, RESILIENT_DIRECTION)

RECENT_TIEBREAK_WEIGHT = Decimal("0.180000")
TIEBREAK_POINT_WEIGHT = Decimal("0.160000")
RECENT_MINUTES_WEIGHT = Decimal("0.140000")
DECIDING_SET_WEIGHT = Decimal("0.160000")
PRESSURE_POINT_LOSS_WEIGHT = Decimal("0.180000")
FIRST_SERVE_DROP_WEIGHT = Decimal("0.100000")
RECOVERY_SHORTFALL_WEIGHT = Decimal("0.080000")

STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
RECOMMENDED_NEXT_STEPS = {
    EMPTY_STATUS: (
        "monitor_report_only_market_research_tennis_tiebreak_pressure_fatigue_digest"
    ),
    BLOCKED_STATUS: (
        "block_report_only_market_research_tennis_tiebreak_pressure_fatigue_digest"
    ),
    WATCH_STATUS: (
        "monitor_report_only_market_research_tennis_tiebreak_pressure_fatigue_digest"
    ),
    PASS_STATUS: (
        "allow_report_only_market_research_tennis_tiebreak_pressure_fatigue_digest"
    ),
}

STANDARD_REASON_ORDER = (
    "tennis_tiebreak_pressure_fatigue_digest_empty",
    "tiebreak_pressure_fatigue_blocked",
    "tiebreak_pressure_fatigue_watch",
    "tiebreak_pressure_fatigue_calm",
    "source_fresh",
    "source_stale",
    "recent_tiebreak_load_high",
    "tiebreak_point_load_high",
    "deciding_set_tiebreak_load",
    "pressure_point_loss_high",
    "first_serve_drop_high",
    "short_recovery_window",
    "recent_minutes_load_high",
    "market_probability_move_up",
)


@dataclass(frozen=True)
class TennisTiebreakPressureFatigueDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_TIEBREAK_PRESSURE_FATIGUE_DIGEST_CONFIG_VERSION
    )
    watch_pressure_fatigue_score: Decimal = Decimal("0.450000")
    blocked_pressure_fatigue_score: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    calm_confidence_cap: Decimal = Decimal("0.650000")
    high_recent_tiebreak_count: Decimal = Decimal("2.000000")
    high_tiebreak_point_count: Decimal = Decimal("40.000000")
    high_recent_minutes_played: Decimal = Decimal("180.000000")
    min_recovery_hours: Decimal = Decimal("36.000000")
    high_pressure_point_loss_rate: Decimal = Decimal("0.500000")
    high_first_serve_drop_rate: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisTiebreakPressureFatigueDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_TIEBREAK_PRESSURE_FATIGUE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_pressure_fatigue_score",
            "blocked_pressure_fatigue_score",
            "stale_confidence_cap",
            "calm_confidence_cap",
            "high_pressure_point_loss_rate",
            "high_first_serve_drop_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_pressure_fatigue_score > self.blocked_pressure_fatigue_score:
            raise ValueError(
                "watch_pressure_fatigue_score must not exceed "
                "blocked_pressure_fatigue_score",
            )
        for field_name in (
            "max_source_age_seconds",
            "high_recent_tiebreak_count",
            "high_tiebreak_point_count",
            "high_recent_minutes_played",
            "min_recovery_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisTiebreakPressureFatigueObservation:
    source_id: str
    match_id: str
    condition_id: str
    player_id: str
    opponent_id: str
    tournament: str
    surface: str
    recent_tiebreak_count: Decimal
    tiebreak_point_count: Decimal
    deciding_set_tiebreak_count: Decimal
    pressure_point_loss_rate: Decimal
    first_serve_drop_rate: Decimal
    recovery_hours: Decimal
    recent_minutes_played: Decimal
    implied_probability_move: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisTiebreakPressureFatigueObservation, "observation")
        for field_name in (
            "source_id",
            "match_id",
            "condition_id",
            "player_id",
            "opponent_id",
            "tournament",
            "surface",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "recent_tiebreak_count",
            "tiebreak_point_count",
            "deciding_set_tiebreak_count",
            "recovery_hours",
            "recent_minutes_played",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.deciding_set_tiebreak_count > self.recent_tiebreak_count:
            raise ValueError(
                "deciding_set_tiebreak_count must not exceed recent_tiebreak_count",
            )
        for field_name in (
            "pressure_point_loss_rate",
            "first_serve_drop_rate",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
            _normalize_open_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisTiebreakPressureFatigueDigestRow:
    source_id: str
    match_id: str
    condition_id: str
    player_id: str
    opponent_id: str
    tournament: str
    surface: str
    recent_tiebreak_count: Decimal
    tiebreak_point_count: Decimal
    deciding_set_tiebreak_count: Decimal
    pressure_point_loss_rate: Decimal
    first_serve_drop_rate: Decimal
    recovery_hours: Decimal
    recent_minutes_played: Decimal
    implied_probability_move: Decimal
    pressure_fatigue_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    pressure_fatigue_direction: str
    pressure_fatigue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisTiebreakPressureFatigueDigestRow, "row")
        for field_name in (
            "source_id",
            "match_id",
            "condition_id",
            "player_id",
            "opponent_id",
            "tournament",
            "surface",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "recent_tiebreak_count",
            "tiebreak_point_count",
            "deciding_set_tiebreak_count",
            "recovery_hours",
            "recent_minutes_played",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pressure_point_loss_rate",
            "first_serve_drop_rate",
            "pressure_fatigue_score",
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
            "implied_probability_move",
            _normalize_signed_probability(
                "implied_probability_move",
                self.implied_probability_move,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "pressure_fatigue_direction",
            _require_member(
                "pressure_fatigue_direction",
                self.pressure_fatigue_direction,
                PRESSURE_FATIGUE_DIRECTIONS,
            ),
        )
        object.__setattr__(
            self,
            "pressure_fatigue_status",
            _require_member(
                "pressure_fatigue_status",
                self.pressure_fatigue_status,
                PRESSURE_FATIGUE_STATUSES,
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
class TennisTiebreakPressureFatigueReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisTiebreakPressureFatigueReasonCodeCount, "count")
        object.__setattr__(
            self,
            "reason_code",
            _require_canonical_string("reason_code", self.reason_code),
        )
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
class TennisTiebreakPressureFatigueDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_pressure_fatigue_count: Decimal
    watch_pressure_fatigue_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    pressure_fatigue_signal_count: Decimal
    max_pressure_fatigue_score: Decimal
    average_pressure_fatigue_score: Decimal
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[TennisTiebreakPressureFatigueDigestRow, ...]
    reason_code_counts: tuple[TennisTiebreakPressureFatigueReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisTiebreakPressureFatigueDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_pressure_fatigue_count",
            "watch_pressure_fatigue_count",
            "pass_count",
            "stale_source_count",
            "pressure_fatigue_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pressure_fatigue_score",
            "average_pressure_fatigue_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, DIGEST_STATUSES),
        )
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_canonical_string(
                "recommended_next_step",
                self.recommended_next_step,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_count_rows(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_tennis_tiebreak_pressure_fatigue_digest(
    inputs: Iterable[TennisTiebreakPressureFatigueObservation],
    *,
    config: TennisTiebreakPressureFatigueDigestConfig,
    generated_at: datetime,
) -> TennisTiebreakPressureFatigueDigestReport:
    if type(config) is not TennisTiebreakPressureFatigueDigestConfig:
        raise ValueError(
            "config must be exactly TennisTiebreakPressureFatigueDigestConfig",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_inputs(inputs)
    if not observations:
        return TennisTiebreakPressureFatigueDigestReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            input_count=ZERO,
            row_count=ZERO,
            blocked_pressure_fatigue_count=ZERO,
            watch_pressure_fatigue_count=ZERO,
            pass_count=ZERO,
            stale_source_count=ZERO,
            pressure_fatigue_signal_count=ZERO,
            max_pressure_fatigue_score=ZERO,
            average_pressure_fatigue_score=ZERO,
            digest_status=EMPTY_STATUS,
            recommended_next_step=RECOMMENDED_NEXT_STEPS[EMPTY_STATUS],
            reason_codes=("tennis_tiebreak_pressure_fatigue_digest_empty",),
            rows=(),
            reason_code_counts=(
                TennisTiebreakPressureFatigueReasonCodeCount(
                    reason_code="tennis_tiebreak_pressure_fatigue_digest_empty",
                    count=ZERO,
                    row_ratio=ZERO,
                ),
            ),
        )

    rows = tuple(
        sorted(
            (_digest_row(item, config=config, generated_at=generated_at_utc) for item in observations),
            key=_row_sort_key,
        ),
    )
    row_count = _count(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _status_rollup(rows)
    return TennisTiebreakPressureFatigueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(observations)),
        row_count=row_count,
        blocked_pressure_fatigue_count=_status_count(rows, BLOCKED_STATUS),
        watch_pressure_fatigue_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_count(
            sum(1 for row in rows if "source_stale" in row.reason_codes),
        ),
        pressure_fatigue_signal_count=_count(
            sum(1 for row in rows if row.pressure_fatigue_status != PASS_STATUS),
        ),
        max_pressure_fatigue_score=max(
            (row.pressure_fatigue_score for row in rows),
            default=ZERO,
        ),
        average_pressure_fatigue_score=_average_score(rows),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_counts(rows, reason_codes, row_count),
    )


def market_research_tennis_tiebreak_pressure_fatigue_digest_payload(
    report: TennisTiebreakPressureFatigueDigestReport,
) -> dict[str, Any]:
    if type(report) is not TennisTiebreakPressureFatigueDigestReport:
        raise ValueError("report must be a TennisTiebreakPressureFatigueDigestReport")
    _require_hard_flags(report)
    return _json_ready(report)


def _digest_row(
    observation: TennisTiebreakPressureFatigueObservation,
    *,
    config: TennisTiebreakPressureFatigueDigestConfig,
    generated_at: datetime,
) -> TennisTiebreakPressureFatigueDigestRow:
    source_age_seconds = _source_age_seconds(
        generated_at=generated_at,
        observed_at=observation.observed_at,
    )
    pressure_fatigue_score = _pressure_fatigue_score(observation, config)
    status = _pressure_fatigue_status(pressure_fatigue_score, config)
    direction = (
        RESILIENT_DIRECTION if status == PASS_STATUS else PRESSURE_FATIGUE_DIRECTION
    )
    confidence_cap = _confidence_cap(
        source_age_seconds=source_age_seconds,
        status=status,
        config=config,
    )
    capped_confidence = min(observation.base_confidence, confidence_cap)
    return TennisTiebreakPressureFatigueDigestRow(
        source_id=observation.source_id,
        match_id=observation.match_id,
        condition_id=observation.condition_id,
        player_id=observation.player_id,
        opponent_id=observation.opponent_id,
        tournament=observation.tournament,
        surface=observation.surface,
        recent_tiebreak_count=observation.recent_tiebreak_count,
        tiebreak_point_count=observation.tiebreak_point_count,
        deciding_set_tiebreak_count=observation.deciding_set_tiebreak_count,
        pressure_point_loss_rate=observation.pressure_point_loss_rate,
        first_serve_drop_rate=observation.first_serve_drop_rate,
        recovery_hours=observation.recovery_hours,
        recent_minutes_played=observation.recent_minutes_played,
        implied_probability_move=observation.implied_probability_move,
        pressure_fatigue_score=pressure_fatigue_score,
        observed_at=observation.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=observation.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=capped_confidence,
        pressure_fatigue_direction=direction,
        pressure_fatigue_status=status,
        reason_codes=_row_reason_codes(
            observation,
            source_age_seconds=source_age_seconds,
            status=status,
            config=config,
        ),
    )


def _pressure_fatigue_score(
    observation: TennisTiebreakPressureFatigueObservation,
    config: TennisTiebreakPressureFatigueDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            RECENT_TIEBREAK_WEIGHT
            * _bounded_ratio(
                observation.recent_tiebreak_count,
                config.high_recent_tiebreak_count,
            )
            + TIEBREAK_POINT_WEIGHT
            * _bounded_ratio(
                observation.tiebreak_point_count,
                config.high_tiebreak_point_count,
            )
            + RECENT_MINUTES_WEIGHT
            * _bounded_ratio(
                observation.recent_minutes_played,
                config.high_recent_minutes_played,
            )
            + DECIDING_SET_WEIGHT
            * (ONE if observation.deciding_set_tiebreak_count > ZERO else ZERO)
            + PRESSURE_POINT_LOSS_WEIGHT * observation.pressure_point_loss_rate
            + FIRST_SERVE_DROP_WEIGHT * observation.first_serve_drop_rate
            + RECOVERY_SHORTFALL_WEIGHT
            * _recovery_shortfall_ratio(observation.recovery_hours, config)
        )
    return _normalize_probability("pressure_fatigue_score", score)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    if ratio < ZERO:
        return ZERO
    return ratio


def _recovery_shortfall_ratio(
    recovery_hours: Decimal,
    config: TennisTiebreakPressureFatigueDigestConfig,
) -> Decimal:
    if recovery_hours >= config.min_recovery_hours:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (config.min_recovery_hours - recovery_hours) / config.min_recovery_hours


def _pressure_fatigue_status(
    pressure_fatigue_score: Decimal,
    config: TennisTiebreakPressureFatigueDigestConfig,
) -> str:
    if pressure_fatigue_score >= config.blocked_pressure_fatigue_score:
        return BLOCKED_STATUS
    if pressure_fatigue_score >= config.watch_pressure_fatigue_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    source_age_seconds: Decimal,
    status: str,
    config: TennisTiebreakPressureFatigueDigestConfig,
) -> Decimal:
    if source_age_seconds > config.max_source_age_seconds:
        return config.stale_confidence_cap
    if status == PASS_STATUS:
        return config.calm_confidence_cap
    return ONE


def _row_reason_codes(
    observation: TennisTiebreakPressureFatigueObservation,
    *,
    source_age_seconds: Decimal,
    status: str,
    config: TennisTiebreakPressureFatigueDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if status == BLOCKED_STATUS:
        reasons.append("tiebreak_pressure_fatigue_blocked")
    elif status == WATCH_STATUS:
        reasons.append("tiebreak_pressure_fatigue_watch")
    else:
        reasons.append("tiebreak_pressure_fatigue_calm")
    if source_age_seconds > config.max_source_age_seconds:
        reasons.append("source_stale")
    else:
        reasons.append("source_fresh")
    if observation.recent_tiebreak_count >= config.high_recent_tiebreak_count:
        reasons.append("recent_tiebreak_load_high")
    if observation.tiebreak_point_count >= config.high_tiebreak_point_count:
        reasons.append("tiebreak_point_load_high")
    if observation.deciding_set_tiebreak_count > ZERO:
        reasons.append("deciding_set_tiebreak_load")
    if observation.pressure_point_loss_rate >= config.high_pressure_point_loss_rate:
        reasons.append("pressure_point_loss_high")
    if observation.first_serve_drop_rate >= config.high_first_serve_drop_rate:
        reasons.append("first_serve_drop_high")
    if observation.recovery_hours < config.min_recovery_hours:
        reasons.append("short_recovery_window")
    if observation.recent_minutes_played >= config.high_recent_minutes_played:
        reasons.append("recent_minutes_load_high")
    if observation.implied_probability_move > ZERO:
        reasons.append("market_probability_move_up")
    reasons.extend(observation.upstream_reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _status_rollup(
    rows: tuple[TennisTiebreakPressureFatigueDigestRow, ...],
) -> str:
    if not rows:
        return EMPTY_STATUS
    if any(row.pressure_fatigue_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_fatigue_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[TennisTiebreakPressureFatigueDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.pressure_fatigue_status == status))


def _average_score(
    rows: tuple[TennisTiebreakPressureFatigueDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(
        _sum_decimal(row.pressure_fatigue_score for row in rows),
        _count(len(rows)),
    )


def _report_reason_codes(
    rows: tuple[TennisTiebreakPressureFatigueDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("tennis_tiebreak_pressure_fatigue_digest_empty",)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _reason_counts(
    rows: tuple[TennisTiebreakPressureFatigueDigestRow, ...],
    reason_codes: tuple[str, ...],
    row_count: Decimal,
) -> tuple[TennisTiebreakPressureFatigueReasonCodeCount, ...]:
    return tuple(
        TennisTiebreakPressureFatigueReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
            row_ratio=_ratio(
                _count(sum(1 for row in rows if reason_code in row.reason_codes)),
                row_count,
            ),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[TennisTiebreakPressureFatigueObservation],
) -> tuple[TennisTiebreakPressureFatigueObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain TennisTiebreakPressureFatigueObservation")
    try:
        observations = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must contain TennisTiebreakPressureFatigueObservation",
        ) from exc
    seen_source_ids: set[str] = set()
    for observation in observations:
        if type(observation) is not TennisTiebreakPressureFatigueObservation:
            raise ValueError(
                "inputs must contain TennisTiebreakPressureFatigueObservation",
            )
        _require_hard_flags(observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return observations


def _normalize_rows(value: object) -> tuple[TennisTiebreakPressureFatigueDigestRow, ...]:
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TennisTiebreakPressureFatigueDigestRow:
            raise ValueError("rows must contain TennisTiebreakPressureFatigueDigestRow")
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.source_id for row in value}) != len(value):
        raise ValueError("rows must not contain duplicate source_id values")
    return value


def _normalize_reason_count_rows(
    value: object,
) -> tuple[TennisTiebreakPressureFatigueReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not TennisTiebreakPressureFatigueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TennisTiebreakPressureFatigueReasonCodeCount",
            )
    if value != tuple(sorted(value, key=lambda row: _reason_sort_key(row.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({row.reason_code for row in value}) != len(value):
        raise ValueError("reason_code_counts must not contain duplicate reason_code values")
    return value


def _row_sort_key(
    row: TennisTiebreakPressureFatigueDigestRow,
) -> tuple[Decimal, Decimal, datetime, str, str, str]:
    return (
        STATUS_RANK[row.pressure_fatigue_status],
        -row.pressure_fatigue_score,
        row.observed_at,
        row.match_id,
        row.player_id,
        row.source_id,
    )


def _reason_sort_key(reason_code: str) -> tuple[Decimal, str]:
    if reason_code in STANDARD_REASON_ORDER:
        return (_count(STANDARD_REASON_ORDER.index(reason_code)), reason_code)
    return (_count(len(STANDARD_REASON_ORDER)), reason_code)


def _validate_row(row: TennisTiebreakPressureFatigueDigestRow) -> None:
    if row.deciding_set_tiebreak_count > row.recent_tiebreak_count:
        raise ValueError(
            "deciding_set_tiebreak_count must not exceed recent_tiebreak_count",
        )
    expected_direction = (
        RESILIENT_DIRECTION
        if row.pressure_fatigue_status == PASS_STATUS
        else PRESSURE_FATIGUE_DIRECTION
    )
    if row.pressure_fatigue_direction != expected_direction:
        raise ValueError("pressure_fatigue_direction must match pressure_fatigue_status")
    if row.capped_confidence > row.base_confidence:
        raise ValueError("capped_confidence must not exceed base_confidence")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")


def _validate_report(report: TennisTiebreakPressureFatigueDigestReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_pressure_fatigue_count != _status_count(
        report.rows,
        BLOCKED_STATUS,
    ):
        raise ValueError("blocked_pressure_fatigue_count must match rows")
    if report.watch_pressure_fatigue_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_pressure_fatigue_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _count(
        sum(1 for row in report.rows if "source_stale" in row.reason_codes),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.pressure_fatigue_signal_count != _count(
        sum(1 for row in report.rows if row.pressure_fatigue_status != PASS_STATUS),
    ):
        raise ValueError("pressure_fatigue_signal_count must match rows")
    if report.max_pressure_fatigue_score != max(
        (row.pressure_fatigue_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_pressure_fatigue_score must match rows")
    if report.average_pressure_fatigue_score != _average_score(report.rows):
        raise ValueError("average_pressure_fatigue_score must match rows")
    if report.digest_status != _status_rollup(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_counts(
        report.rows,
        report.reason_codes,
        report.row_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    reasons = tuple(_require_canonical_string("reason_code", item) for item in value)
    if not reasons:
        raise ValueError("reason_codes must not be empty")
    return tuple(sorted(set(reasons), key=_reason_sort_key))


def _normalize_open_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError("upstream_reason_codes must be a tuple")
    reasons = tuple(
        _require_canonical_string("upstream_reason_code", item) for item in value
    )
    return tuple(sorted(set(reasons), key=_reason_sort_key))


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_canonical_string(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _normalize_signed_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < NEGATIVE_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _source_age_seconds(*, generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        age = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds).quantize(QUANTUM)
            + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        )
    age = age.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    if age < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return age


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return total.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")
