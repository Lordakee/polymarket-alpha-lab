"""Pure paper/report/readonly candidate resolution timeline pressure v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MINUS_ONE = Decimal("-1.000000")

MAX_RESOLUTION_MINUTES = Decimal("1440.000000")
RESOLUTION_URGENT_MINUTES = Decimal("60.000000")
RESOLUTION_NEAR_MINUTES = Decimal("360.000000")
RESOLUTION_PRESSURE_RANGE_MINUTES = Decimal("1380.000000")

SOURCE_CADENCE_SLOW_MINUTES = Decimal("360.000000")
DEPENDENCY_HEAVY_COUNT = Decimal("3.000000")
DEPENDENCY_CAP_COUNT = Decimal("5.000000")
MARKET_MOVE_OBSERVED = Decimal("0.030000")
MARKET_MOVE_LARGE = Decimal("0.100000")
MARKET_MOVE_CAP = Decimal("0.150000")
QUEUE_AGED_MINUTES = Decimal("120.000000")
QUEUE_STALE_MINUTES = Decimal("720.000000")
QUEUE_CAP_MINUTES = Decimal("720.000000")

WEIGHT_RESOLUTION = Decimal("0.300000")
WEIGHT_SOURCE_CADENCE = Decimal("0.200000")
WEIGHT_DEPENDENCIES = Decimal("0.200000")
WEIGHT_MARKET_MOVE = Decimal("0.150000")
WEIGHT_QUEUE_AGE = Decimal("0.150000")

WATCH_PRESSURE_THRESHOLD = Decimal("0.250000")
ELEVATED_PRESSURE_THRESHOLD = Decimal("0.500000")
CRITICAL_PRESSURE_THRESHOLD = Decimal("0.750000")

REVIEW_NOW_MINUTES = Decimal("15.000000")
EXPEDITE_REVIEW_MINUTES = Decimal("60.000000")
MONITOR_REVIEW_MINUTES = Decimal("240.000000")
NORMAL_REVIEW_MINUTES = Decimal("720.000000")

PRESSURE_STATUSES = ("normal", "watch", "elevated", "critical")
REVIEW_ACTIONS = (
    "normal_queue",
    "monitor_queue",
    "expedite_review",
    "review_now",
)
REASON_CODES = (
    "pressure_status_normal",
    "pressure_status_watch",
    "pressure_status_elevated",
    "pressure_status_critical",
    "resolution_window_sufficient",
    "resolution_window_near",
    "resolution_window_urgent",
    "source_cadence_fresh",
    "source_cadence_slow",
    "source_cadence_misses_resolution",
    "dependencies_clear",
    "dependencies_pending",
    "dependencies_heavy",
    "market_move_stable",
    "market_move_observed",
    "market_move_large",
    "review_queue_fresh",
    "review_queue_aged",
    "review_queue_stale",
)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimelinePressureV10Input:
    candidate_id: str
    market_slug: str
    outcome_name: str
    time_to_resolution_minutes: Decimal
    source_update_cadence_minutes: Decimal
    pending_resolution_dependencies: Decimal
    market_move_since_last_research: Decimal
    review_queue_age_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("candidate_id", self.candidate_id)
        _require_identifier("market_slug", self.market_slug)
        _require_canonical_string("outcome_name", self.outcome_name)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "source_update_cadence_minutes",
            _normalize_nonnegative_decimal(
                "source_update_cadence_minutes",
                self.source_update_cadence_minutes,
            ),
        )
        object.__setattr__(
            self,
            "pending_resolution_dependencies",
            _normalize_whole_nonnegative_decimal(
                "pending_resolution_dependencies",
                self.pending_resolution_dependencies,
            ),
        )
        object.__setattr__(
            self,
            "market_move_since_last_research",
            _normalize_probability_delta(
                "market_move_since_last_research",
                self.market_move_since_last_research,
            ),
        )
        object.__setattr__(
            self,
            "review_queue_age_minutes",
            _normalize_nonnegative_decimal(
                "review_queue_age_minutes",
                self.review_queue_age_minutes,
            ),
        )
        reject_unsafe_surface_fields("resolution timeline pressure input", self)
        require_paper_only_flags("resolution timeline pressure input", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimelinePressureV10Result:
    candidate_id: str
    market_slug: str
    outcome_name: str
    time_to_resolution_minutes: Decimal
    source_update_cadence_minutes: Decimal
    pending_resolution_dependencies: Decimal
    market_move_since_last_research: Decimal
    review_queue_age_minutes: Decimal
    resolution_time_pressure: Decimal
    source_cadence_pressure: Decimal
    dependency_pressure: Decimal
    market_move_pressure: Decimal
    review_queue_pressure: Decimal
    pressure_score: Decimal
    pressure_status: str
    review_action: str
    recommended_review_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("candidate_id", self.candidate_id)
        _require_identifier("market_slug", self.market_slug)
        _require_canonical_string("outcome_name", self.outcome_name)
        for field_name in (
            "time_to_resolution_minutes",
            "source_update_cadence_minutes",
            "review_queue_age_minutes",
            "recommended_review_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pending_resolution_dependencies",
            _normalize_whole_nonnegative_decimal(
                "pending_resolution_dependencies",
                self.pending_resolution_dependencies,
            ),
        )
        object.__setattr__(
            self,
            "market_move_since_last_research",
            _normalize_probability_delta(
                "market_move_since_last_research",
                self.market_move_since_last_research,
            ),
        )
        for field_name in (
            "resolution_time_pressure",
            "source_cadence_pressure",
            "dependency_pressure",
            "market_move_pressure",
            "review_queue_pressure",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        _require_choice("review_action", self.review_action, REVIEW_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        reject_unsafe_surface_fields("resolution timeline pressure result", self)
        require_paper_only_flags("resolution timeline pressure result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_resolution_timeline_pressure_v10_payload(self)


def build_strategy_candidate_resolution_timeline_pressure_v10(
    candidate: StrategyCandidateResolutionTimelinePressureV10Input,
) -> StrategyCandidateResolutionTimelinePressureV10Result:
    if type(candidate) is not StrategyCandidateResolutionTimelinePressureV10Input:
        raise ValueError(
            "candidate must be a StrategyCandidateResolutionTimelinePressureV10Input",
        )
    reject_unsafe_surface_fields("resolution timeline pressure input", candidate)
    require_paper_only_flags("resolution timeline pressure input", candidate)

    resolution_time_pressure = _resolution_time_pressure(
        candidate.time_to_resolution_minutes,
    )
    source_cadence_pressure = _source_cadence_pressure(
        candidate.source_update_cadence_minutes,
        candidate.time_to_resolution_minutes,
    )
    dependency_pressure = _ratio_capped(
        candidate.pending_resolution_dependencies,
        DEPENDENCY_CAP_COUNT,
    )
    market_move_pressure = _ratio_capped(
        _abs_decimal(candidate.market_move_since_last_research),
        MARKET_MOVE_CAP,
    )
    review_queue_pressure = _ratio_capped(
        candidate.review_queue_age_minutes,
        QUEUE_CAP_MINUTES,
    )
    pressure_score = _weighted_score(
        resolution_time_pressure=resolution_time_pressure,
        source_cadence_pressure=source_cadence_pressure,
        dependency_pressure=dependency_pressure,
        market_move_pressure=market_move_pressure,
        review_queue_pressure=review_queue_pressure,
    )
    pressure_status = _pressure_status(pressure_score)
    return StrategyCandidateResolutionTimelinePressureV10Result(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        outcome_name=candidate.outcome_name,
        time_to_resolution_minutes=candidate.time_to_resolution_minutes,
        source_update_cadence_minutes=candidate.source_update_cadence_minutes,
        pending_resolution_dependencies=candidate.pending_resolution_dependencies,
        market_move_since_last_research=candidate.market_move_since_last_research,
        review_queue_age_minutes=candidate.review_queue_age_minutes,
        resolution_time_pressure=resolution_time_pressure,
        source_cadence_pressure=source_cadence_pressure,
        dependency_pressure=dependency_pressure,
        market_move_pressure=market_move_pressure,
        review_queue_pressure=review_queue_pressure,
        pressure_score=pressure_score,
        pressure_status=pressure_status,
        review_action=_review_action(pressure_status),
        recommended_review_minutes=_recommended_review_minutes(
            pressure_status,
            candidate.time_to_resolution_minutes,
        ),
        reason_codes=_reason_codes(candidate, pressure_status),
    )


def strategy_candidate_resolution_timeline_pressure_v10_payload(
    result: StrategyCandidateResolutionTimelinePressureV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateResolutionTimelinePressureV10Result:
        raise ValueError(
            "result must be a StrategyCandidateResolutionTimelinePressureV10Result",
        )
    reject_unsafe_surface_fields("resolution timeline pressure result", result)
    require_paper_only_flags("resolution timeline pressure result", result)
    payload = json_ready_no_floats(result)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("resolution timeline pressure payload", payload)
    return payload


def _resolution_time_pressure(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes <= RESOLUTION_URGENT_MINUTES:
        return ONE
    if time_to_resolution_minutes >= MAX_RESOLUTION_MINUTES:
        return ZERO
    return _q(
        (MAX_RESOLUTION_MINUTES - time_to_resolution_minutes)
        / RESOLUTION_PRESSURE_RANGE_MINUTES,
    )


def _source_cadence_pressure(
    source_update_cadence_minutes: Decimal,
    time_to_resolution_minutes: Decimal,
) -> Decimal:
    if time_to_resolution_minutes <= ZERO:
        return ONE
    return _ratio_capped(source_update_cadence_minutes, time_to_resolution_minutes)


def _weighted_score(
    *,
    resolution_time_pressure: Decimal,
    source_cadence_pressure: Decimal,
    dependency_pressure: Decimal,
    market_move_pressure: Decimal,
    review_queue_pressure: Decimal,
) -> Decimal:
    return _q(
        (resolution_time_pressure * WEIGHT_RESOLUTION)
        + (source_cadence_pressure * WEIGHT_SOURCE_CADENCE)
        + (dependency_pressure * WEIGHT_DEPENDENCIES)
        + (market_move_pressure * WEIGHT_MARKET_MOVE)
        + (review_queue_pressure * WEIGHT_QUEUE_AGE),
    )


def _pressure_status(pressure_score: Decimal) -> str:
    if pressure_score >= CRITICAL_PRESSURE_THRESHOLD:
        return "critical"
    if pressure_score >= ELEVATED_PRESSURE_THRESHOLD:
        return "elevated"
    if pressure_score >= WATCH_PRESSURE_THRESHOLD:
        return "watch"
    return "normal"


def _review_action(pressure_status: str) -> str:
    if pressure_status == "critical":
        return "review_now"
    if pressure_status == "elevated":
        return "expedite_review"
    if pressure_status == "watch":
        return "monitor_queue"
    if pressure_status == "normal":
        return "normal_queue"
    raise ValueError("pressure_status must be supported")


def _recommended_review_minutes(
    pressure_status: str,
    time_to_resolution_minutes: Decimal,
) -> Decimal:
    if pressure_status == "critical":
        return _min_decimal(REVIEW_NOW_MINUTES, time_to_resolution_minutes)
    if pressure_status == "elevated":
        return _min_decimal(EXPEDITE_REVIEW_MINUTES, time_to_resolution_minutes)
    if pressure_status == "watch":
        return _min_decimal(MONITOR_REVIEW_MINUTES, time_to_resolution_minutes)
    if pressure_status == "normal":
        return _min_decimal(NORMAL_REVIEW_MINUTES, time_to_resolution_minutes)
    raise ValueError("pressure_status must be supported")


def _reason_codes(
    candidate: StrategyCandidateResolutionTimelinePressureV10Input,
    pressure_status: str,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            f"pressure_status_{pressure_status}",
            _resolution_reason_code(candidate.time_to_resolution_minutes),
            _source_cadence_reason_code(
                candidate.source_update_cadence_minutes,
                candidate.time_to_resolution_minutes,
            ),
            _dependency_reason_code(candidate.pending_resolution_dependencies),
            _market_move_reason_code(candidate.market_move_since_last_research),
            _review_queue_reason_code(candidate.review_queue_age_minutes),
        ),
    )


def _resolution_reason_code(time_to_resolution_minutes: Decimal) -> str:
    if time_to_resolution_minutes <= RESOLUTION_URGENT_MINUTES:
        return "resolution_window_urgent"
    if time_to_resolution_minutes <= RESOLUTION_NEAR_MINUTES:
        return "resolution_window_near"
    return "resolution_window_sufficient"


def _source_cadence_reason_code(
    source_update_cadence_minutes: Decimal,
    time_to_resolution_minutes: Decimal,
) -> str:
    if (
        time_to_resolution_minutes > ZERO
        and source_update_cadence_minutes >= time_to_resolution_minutes
    ):
        return "source_cadence_misses_resolution"
    if source_update_cadence_minutes >= SOURCE_CADENCE_SLOW_MINUTES:
        return "source_cadence_slow"
    return "source_cadence_fresh"


def _dependency_reason_code(pending_resolution_dependencies: Decimal) -> str:
    if pending_resolution_dependencies >= DEPENDENCY_HEAVY_COUNT:
        return "dependencies_heavy"
    if pending_resolution_dependencies > ZERO:
        return "dependencies_pending"
    return "dependencies_clear"


def _market_move_reason_code(market_move_since_last_research: Decimal) -> str:
    absolute_move = _abs_decimal(market_move_since_last_research)
    if absolute_move >= MARKET_MOVE_LARGE:
        return "market_move_large"
    if absolute_move >= MARKET_MOVE_OBSERVED:
        return "market_move_observed"
    return "market_move_stable"


def _review_queue_reason_code(review_queue_age_minutes: Decimal) -> str:
    if review_queue_age_minutes >= QUEUE_STALE_MINUTES:
        return "review_queue_stale"
    if review_queue_age_minutes >= QUEUE_AGED_MINUTES:
        return "review_queue_aged"
    return "review_queue_fresh"


def _validate_result(
    result: StrategyCandidateResolutionTimelinePressureV10Result,
) -> None:
    expected_resolution_time_pressure = _resolution_time_pressure(
        result.time_to_resolution_minutes,
    )
    expected_source_cadence_pressure = _source_cadence_pressure(
        result.source_update_cadence_minutes,
        result.time_to_resolution_minutes,
    )
    expected_dependency_pressure = _ratio_capped(
        result.pending_resolution_dependencies,
        DEPENDENCY_CAP_COUNT,
    )
    expected_market_move_pressure = _ratio_capped(
        _abs_decimal(result.market_move_since_last_research),
        MARKET_MOVE_CAP,
    )
    expected_review_queue_pressure = _ratio_capped(
        result.review_queue_age_minutes,
        QUEUE_CAP_MINUTES,
    )
    expected_pressure_score = _weighted_score(
        resolution_time_pressure=expected_resolution_time_pressure,
        source_cadence_pressure=expected_source_cadence_pressure,
        dependency_pressure=expected_dependency_pressure,
        market_move_pressure=expected_market_move_pressure,
        review_queue_pressure=expected_review_queue_pressure,
    )
    expected_pressure_status = _pressure_status(expected_pressure_score)
    expected_review_action = _review_action(expected_pressure_status)
    expected_recommended_review_minutes = _recommended_review_minutes(
        expected_pressure_status,
        result.time_to_resolution_minutes,
    )
    if result.resolution_time_pressure != expected_resolution_time_pressure:
        raise ValueError("resolution_time_pressure must match candidate fields")
    if result.source_cadence_pressure != expected_source_cadence_pressure:
        raise ValueError("source_cadence_pressure must match candidate fields")
    if result.dependency_pressure != expected_dependency_pressure:
        raise ValueError("dependency_pressure must match candidate fields")
    if result.market_move_pressure != expected_market_move_pressure:
        raise ValueError("market_move_pressure must match candidate fields")
    if result.review_queue_pressure != expected_review_queue_pressure:
        raise ValueError("review_queue_pressure must match candidate fields")
    if result.pressure_score != expected_pressure_score:
        raise ValueError("pressure_score must match candidate fields")
    if result.pressure_status != expected_pressure_status:
        raise ValueError("pressure_status must match pressure_score")
    if result.review_action != expected_review_action:
        raise ValueError("review_action must match pressure_status")
    if result.recommended_review_minutes != expected_recommended_review_minutes:
        raise ValueError("recommended_review_minutes must match pressure_status")
    expected_reason_codes = _normalize_reason_codes(
        (
            f"pressure_status_{expected_pressure_status}",
            _resolution_reason_code(result.time_to_resolution_minutes),
            _source_cadence_reason_code(
                result.source_update_cadence_minutes,
                result.time_to_resolution_minutes,
            ),
            _dependency_reason_code(result.pending_resolution_dependencies),
            _market_move_reason_code(result.market_move_since_last_research),
            _review_queue_reason_code(result.review_queue_age_minutes),
        ),
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match candidate fields")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_string_tuple("reason_codes", values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return normalized


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < MINUS_ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _q(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = numerator / denominator
    if ratio >= ONE:
        return ONE
    if ratio <= ZERO:
        return ZERO
    return _q(ratio)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _q(ZERO - value)
    return _q(value)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return _q(left)
    return _q(right)


def _q(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT)


__all__ = (
    "PRESSURE_STATUSES",
    "REVIEW_ACTIONS",
    "REASON_CODES",
    "StrategyCandidateResolutionTimelinePressureV10Input",
    "StrategyCandidateResolutionTimelinePressureV10Result",
    "build_strategy_candidate_resolution_timeline_pressure_v10",
    "strategy_candidate_resolution_timeline_pressure_v10_payload",
)
