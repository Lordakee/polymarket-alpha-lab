"""Pure report-only tennis medical-timeout momentum shift digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_MEDICAL_TIMEOUT_MOMENTUM_SHIFT_DIGEST_CONFIG_VERSION",
    "TennisMedicalTimeoutMomentumShiftDigestConfig",
    "TennisMedicalTimeoutMomentumShiftObservation",
    "TennisMedicalTimeoutMomentumShiftDigestRow",
    "TennisMedicalTimeoutMomentumShiftReasonCodeCount",
    "TennisMedicalTimeoutMomentumShiftDigestReport",
    "build_market_research_tennis_medical_timeout_momentum_shift_digest",
    "market_research_tennis_medical_timeout_momentum_shift_digest_payload",
)


DEFAULT_MARKET_RESEARCH_TENNIS_MEDICAL_TIMEOUT_MOMENTUM_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-medical-timeout-momentum-shift-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SHIFT_DIRECTION = "medical_timeout_momentum_shift"
STABLE_DIRECTION = "medical_timeout_stable"

EMPTY_STATUS = "empty"
BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
SHIFT_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
DIGEST_STATUSES = (EMPTY_STATUS, BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
MARKET_TYPES = ("match_probability", "set_probability")
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
RECOMMENDED_NEXT_STEPS = {
    EMPTY_STATUS: (
        "monitor_report_only_market_research_tennis_medical_timeout_momentum_shift_digest"
    ),
    BLOCKED_STATUS: (
        "block_report_only_market_research_tennis_medical_timeout_momentum_shift_digest"
    ),
    WATCH_STATUS: (
        "monitor_report_only_market_research_tennis_medical_timeout_momentum_shift_digest"
    ),
    PASS_STATUS: (
        "allow_report_only_market_research_tennis_medical_timeout_momentum_shift_digest"
    ),
}

STANDARD_REASON_ORDER = (
    "tennis_medical_timeout_momentum_shift_digest_empty",
    "medical_timeout_momentum_shift_blocked",
    "medical_timeout_momentum_shift_watch",
    "medical_timeout_momentum_shift_calm",
    "source_fresh",
    "source_stale",
    "medical_timeout_reported",
    "trainer_visit_cluster",
    "trainer_visit_reported",
    "serve_speed_drop_detected",
    "movement_score_decline",
    "market_momentum_pressure_high",
    "market_probability_move_up",
)


@dataclass(frozen=True)
class TennisMedicalTimeoutMomentumShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_MEDICAL_TIMEOUT_MOMENTUM_SHIFT_DIGEST_CONFIG_VERSION
    )
    watch_momentum_shift_score: Decimal = Decimal("0.450000")
    blocked_momentum_shift_score: Decimal = Decimal("0.700000")
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    stale_confidence_cap: Decimal = Decimal("0.350000")
    stable_confidence_cap: Decimal = Decimal("0.650000")
    serve_speed_drop_kph_threshold: Decimal = Decimal("3.000000")
    movement_decline_threshold: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TennisMedicalTimeoutMomentumShiftDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_MEDICAL_TIMEOUT_MOMENTUM_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_momentum_shift_score", "blocked_momentum_shift_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_momentum_shift_score > self.blocked_momentum_shift_score:
            raise ValueError(
                "watch_momentum_shift_score must not exceed blocked_momentum_shift_score",
            )
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _normalize_positive_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        for field_name in ("stale_confidence_cap", "stable_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "serve_speed_drop_kph_threshold",
            _normalize_positive_decimal(
                "serve_speed_drop_kph_threshold",
                self.serve_speed_drop_kph_threshold,
            ),
        )
        object.__setattr__(
            self,
            "movement_decline_threshold",
            _normalize_positive_probability(
                "movement_decline_threshold",
                self.movement_decline_threshold,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisMedicalTimeoutMomentumShiftObservation:
    source_id: str
    event_id: str
    market_slug: str
    market_type: str
    player_id: str
    opponent_id: str
    tournament: str
    set_id: str
    medical_timeout_count: Decimal
    trainer_visit_count: Decimal
    serve_speed_drop_kph: Decimal
    movement_score_change: Decimal
    momentum_pressure_score: Decimal
    implied_probability_move: Decimal
    observed_at: datetime
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TennisMedicalTimeoutMomentumShiftObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "event_id",
            "market_slug",
            "player_id",
            "opponent_id",
            "tournament",
            "set_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        for field_name in (
            "medical_timeout_count",
            "trainer_visit_count",
            "serve_speed_drop_kph",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "movement_score_change",
            _normalize_signed_probability(
                "movement_score_change",
                self.movement_score_change,
            ),
        )
        object.__setattr__(
            self,
            "momentum_pressure_score",
            _normalize_probability(
                "momentum_pressure_score",
                self.momentum_pressure_score,
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
class TennisMedicalTimeoutMomentumShiftDigestRow:
    source_id: str
    event_id: str
    market_slug: str
    market_type: str
    player_id: str
    opponent_id: str
    tournament: str
    set_id: str
    medical_timeout_count: Decimal
    trainer_visit_count: Decimal
    serve_speed_drop_kph: Decimal
    movement_score_change: Decimal
    momentum_pressure_score: Decimal
    implied_probability_move: Decimal
    momentum_shift_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    shift_direction: str
    shift_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TennisMedicalTimeoutMomentumShiftDigestRow, "row")
        for field_name in (
            "source_id",
            "event_id",
            "market_slug",
            "player_id",
            "opponent_id",
            "tournament",
            "set_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        for field_name in (
            "medical_timeout_count",
            "trainer_visit_count",
            "serve_speed_drop_kph",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "movement_score_change",
            _normalize_signed_probability(
                "movement_score_change",
                self.movement_score_change,
            ),
        )
        for field_name in (
            "momentum_pressure_score",
            "momentum_shift_score",
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
        _require_member(
            "shift_direction",
            self.shift_direction,
            (SHIFT_DIRECTION, STABLE_DIRECTION),
        )
        _require_member("shift_status", self.shift_status, SHIFT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class TennisMedicalTimeoutMomentumShiftReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TennisMedicalTimeoutMomentumShiftReasonCodeCount,
            "count",
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
class TennisMedicalTimeoutMomentumShiftDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_shift_count: Decimal
    watch_shift_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    medical_timeout_signal_count: Decimal
    trainer_visit_signal_count: Decimal
    serve_speed_drop_signal_count: Decimal
    movement_decline_signal_count: Decimal
    max_momentum_shift_score: Decimal
    average_momentum_shift_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TennisMedicalTimeoutMomentumShiftReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TennisMedicalTimeoutMomentumShiftDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_MEDICAL_TIMEOUT_MOMENTUM_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_shift_count",
            "watch_shift_count",
            "pass_count",
            "stale_source_count",
            "medical_timeout_signal_count",
            "trainer_visit_signal_count",
            "serve_speed_drop_signal_count",
            "movement_decline_signal_count",
            "max_momentum_shift_score",
            "average_momentum_shift_score",
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


def build_market_research_tennis_medical_timeout_momentum_shift_digest(
    inputs: Iterable[TennisMedicalTimeoutMomentumShiftObservation],
    *,
    config: TennisMedicalTimeoutMomentumShiftDigestConfig,
    generated_at: datetime,
) -> TennisMedicalTimeoutMomentumShiftDigestReport:
    if type(config) is not TennisMedicalTimeoutMomentumShiftDigestConfig:
        raise ValueError(
            "config must be exactly TennisMedicalTimeoutMomentumShiftDigestConfig",
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
    return TennisMedicalTimeoutMomentumShiftDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_shift_count=_status_count(rows, BLOCKED_STATUS),
        watch_shift_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "source_stale"),
        medical_timeout_signal_count=_reason_count(rows, "medical_timeout_reported"),
        trainer_visit_signal_count=_trainer_visit_signal_count(rows),
        serve_speed_drop_signal_count=_reason_count(rows, "serve_speed_drop_detected"),
        movement_decline_signal_count=_reason_count(rows, "movement_score_decline"),
        max_momentum_shift_score=_max_row_decimal(rows, "momentum_shift_score"),
        average_momentum_shift_score=_ratio(
            _sum_decimal(row.momentum_shift_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_tennis_medical_timeout_momentum_shift_digest_payload(
    report: TennisMedicalTimeoutMomentumShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not TennisMedicalTimeoutMomentumShiftDigestReport:
        raise ValueError(
            "report must be exactly TennisMedicalTimeoutMomentumShiftDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    value: TennisMedicalTimeoutMomentumShiftObservation,
    *,
    config: TennisMedicalTimeoutMomentumShiftDigestConfig,
    generated_at: datetime,
) -> TennisMedicalTimeoutMomentumShiftDigestRow:
    momentum_shift_score = _momentum_shift_score(value)
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_observation_age_seconds
    status = _shift_status(momentum_shift_score, config=config)
    direction = SHIFT_DIRECTION if status != PASS_STATUS else STABLE_DIRECTION
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return TennisMedicalTimeoutMomentumShiftDigestRow(
        source_id=value.source_id,
        event_id=value.event_id,
        market_slug=value.market_slug,
        market_type=value.market_type,
        player_id=value.player_id,
        opponent_id=value.opponent_id,
        tournament=value.tournament,
        set_id=value.set_id,
        medical_timeout_count=value.medical_timeout_count,
        trainer_visit_count=value.trainer_visit_count,
        serve_speed_drop_kph=value.serve_speed_drop_kph,
        movement_score_change=value.movement_score_change,
        momentum_pressure_score=value.momentum_pressure_score,
        implied_probability_move=value.implied_probability_move,
        momentum_shift_score=momentum_shift_score,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        shift_direction=direction,
        shift_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            value=value,
            status=status,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _momentum_shift_score(
    value: TennisMedicalTimeoutMomentumShiftObservation,
) -> Decimal:
    return _momentum_shift_score_from_values(
        medical_timeout_count=value.medical_timeout_count,
        trainer_visit_count=value.trainer_visit_count,
        serve_speed_drop_kph=value.serve_speed_drop_kph,
        movement_score_change=value.movement_score_change,
        momentum_pressure_score=value.momentum_pressure_score,
    )


def _momentum_shift_score_from_values(
    *,
    medical_timeout_count: Decimal,
    trainer_visit_count: Decimal,
    serve_speed_drop_kph: Decimal,
    movement_score_change: Decimal,
    momentum_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        medical_timeout_component = _clamp_probability(
            medical_timeout_count / Decimal("1.000000"),
        )
        trainer_visit_component = _clamp_probability(
            trainer_visit_count / Decimal("2.000000"),
        )
        serve_speed_component = _clamp_probability(
            serve_speed_drop_kph / Decimal("15.000000"),
        )
        movement_decline_component = _clamp_probability(
            -movement_score_change / Decimal("0.300000"),
        )
        raw_score = (
            medical_timeout_component * Decimal("0.300000")
            + trainer_visit_component * Decimal("0.150000")
            + serve_speed_component * Decimal("0.200000")
            + movement_decline_component * Decimal("0.200000")
            + momentum_pressure_score * Decimal("0.150000")
        )
    return _quantize_decimal(raw_score)


def _shift_status(
    momentum_shift_score: Decimal,
    *,
    config: TennisMedicalTimeoutMomentumShiftDigestConfig,
) -> str:
    if momentum_shift_score >= config.blocked_momentum_shift_score:
        return BLOCKED_STATUS
    if momentum_shift_score >= config.watch_momentum_shift_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: TennisMedicalTimeoutMomentumShiftDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == PASS_STATUS:
        caps.append(config.stable_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    value: TennisMedicalTimeoutMomentumShiftObservation,
    status: str,
    source_fresh: bool,
    config: TennisMedicalTimeoutMomentumShiftDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("medical_timeout_momentum_shift_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("medical_timeout_momentum_shift_watch")
    else:
        reason_codes.append("medical_timeout_momentum_shift_calm")
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    if value.medical_timeout_count > ZERO:
        reason_codes.append("medical_timeout_reported")
    if value.trainer_visit_count >= Decimal("2.000000"):
        reason_codes.append("trainer_visit_cluster")
    elif value.trainer_visit_count > ZERO:
        reason_codes.append("trainer_visit_reported")
    if value.serve_speed_drop_kph >= config.serve_speed_drop_kph_threshold:
        reason_codes.append("serve_speed_drop_detected")
    if value.movement_score_change <= -config.movement_decline_threshold:
        reason_codes.append("movement_score_decline")
    if value.momentum_pressure_score >= Decimal("0.400000"):
        reason_codes.append("market_momentum_pressure_high")
    if value.implied_probability_move >= Decimal("0.050000"):
        reason_codes.append("market_probability_move_up")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("tennis_medical_timeout_momentum_shift_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...],
) -> tuple[TennisMedicalTimeoutMomentumShiftReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        TennisMedicalTimeoutMomentumShiftReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[TennisMedicalTimeoutMomentumShiftObservation],
) -> tuple[TennisMedicalTimeoutMomentumShiftObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not TennisMedicalTimeoutMomentumShiftObservation:
            raise ValueError(
                "inputs must contain TennisMedicalTimeoutMomentumShiftObservation",
            )
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[TennisMedicalTimeoutMomentumShiftDigestRow],
) -> tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TennisMedicalTimeoutMomentumShiftDigestRow:
            raise ValueError(
                "rows must contain TennisMedicalTimeoutMomentumShiftDigestRow",
            )
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[TennisMedicalTimeoutMomentumShiftReasonCodeCount],
) -> tuple[TennisMedicalTimeoutMomentumShiftReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not TennisMedicalTimeoutMomentumShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TennisMedicalTimeoutMomentumShiftReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: _reason_sort_key(value.reason_code)))


def _validate_row(row: TennisMedicalTimeoutMomentumShiftDigestRow) -> None:
    if row.momentum_shift_score != _momentum_shift_score_from_values(
        medical_timeout_count=row.medical_timeout_count,
        trainer_visit_count=row.trainer_visit_count,
        serve_speed_drop_kph=row.serve_speed_drop_kph,
        movement_score_change=row.movement_score_change,
        momentum_pressure_score=row.momentum_pressure_score,
    ):
        raise ValueError("momentum_shift_score must match row factors")
    if row.shift_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("shift_status must match reason_codes")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.capped_confidence > row.base_confidence:
        raise ValueError("capped_confidence must not exceed base_confidence")
    if row.shift_status == PASS_STATUS and row.shift_direction != STABLE_DIRECTION:
        raise ValueError("shift_direction must match shift_status")
    if row.shift_status != PASS_STATUS and row.shift_direction != SHIFT_DIRECTION:
        raise ValueError("shift_direction must match shift_status")


def _validate_report(report: TennisMedicalTimeoutMomentumShiftDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_shift_count + report.watch_shift_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.medical_timeout_signal_count != _reason_count(
        report.rows,
        "medical_timeout_reported",
    ):
        raise ValueError("medical_timeout_signal_count must match rows")
    if report.trainer_visit_signal_count != _trainer_visit_signal_count(report.rows):
        raise ValueError("trainer_visit_signal_count must match rows")
    if report.serve_speed_drop_signal_count != _reason_count(
        report.rows,
        "serve_speed_drop_detected",
    ):
        raise ValueError("serve_speed_drop_signal_count must match rows")
    if report.movement_decline_signal_count != _reason_count(
        report.rows,
        "movement_score_decline",
    ):
        raise ValueError("movement_decline_signal_count must match rows")
    if report.max_momentum_shift_score != _max_row_decimal(
        report.rows,
        "momentum_shift_score",
    ):
        raise ValueError("max_momentum_shift_score must match rows")
    if report.average_momentum_shift_score != _ratio(
        _sum_decimal(row.momentum_shift_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_momentum_shift_score must match rows")
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


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "medical_timeout_momentum_shift_blocked" in reason_codes:
        return BLOCKED_STATUS
    if "medical_timeout_momentum_shift_watch" in reason_codes:
        return WATCH_STATUS
    if "medical_timeout_momentum_shift_calm" in reason_codes:
        return PASS_STATUS
    raise ValueError("shift_status must match reason_codes")


def _digest_status(rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...]) -> str:
    if not rows:
        return EMPTY_STATUS
    if any(row.shift_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.shift_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.shift_status == status))


def _trainer_visit_signal_count(
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "trainer_visit_reported" in row.reason_codes
            or "trainer_visit_cluster" in row.reason_codes
        ),
    )


def _reason_count(
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[TennisMedicalTimeoutMomentumShiftDigestRow, ...],
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


def _normalize_positive_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    row: TennisMedicalTimeoutMomentumShiftDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.shift_status],
        -row.momentum_shift_score,
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
