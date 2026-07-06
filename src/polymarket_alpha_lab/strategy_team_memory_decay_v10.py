"""Pure team memory trust decay scoring for long-horizon specialties."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")

CURRENT_GAP_DAYS = Decimal("30")
RECENT_GAP_DAYS = Decimal("90")
STALE_GAP_DAYS = Decimal("180")

STRONG_HIT_RATE = Decimal("0.700000")
WATCH_HIT_RATE = Decimal("0.500000")
LOW_CALIBRATION_ERROR = Decimal("0.120000")
WATCH_CALIBRATION_ERROR = Decimal("0.250000")
STRONG_SAMPLE_SIZE = Decimal("30")
WATCH_SAMPLE_SIZE = Decimal("10")
STRONG_SOURCE_QUALITY = Decimal("0.750000")
WATCH_SOURCE_QUALITY = Decimal("0.400000")
TRUSTED_SCORE = Decimal("0.750000")
DECAYED_SCORE = Decimal("0.450000")

CURRENT_DECAY_FACTOR = Decimal("1.000000")
RECENT_DECAY_FACTOR = Decimal("0.900000")
STALE_DECAY_FACTOR = Decimal("0.750000")
LONG_DECAY_FACTOR = Decimal("0.550000")
STRONG_SAMPLE_FACTOR = Decimal("1.000000")
WATCH_SAMPLE_FACTOR = Decimal("0.975000")
LOW_SAMPLE_FACTOR = Decimal("0.950000")

MEMORY_STATUSES = ("trusted", "watch", "decayed")
TRAINING_PRIORITIES = ("low", "medium", "high")


@dataclass(frozen=True)
class TeamMemoryDecayV10Input:
    team_id: str
    specialty: str
    past_hit_rate: Decimal
    calibration_error: Decimal
    sample_size: Decimal
    days_since_last_resolved_market: Decimal
    recent_source_quality: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_non_empty_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "specialty",
            _require_non_empty_string("specialty", self.specialty),
        )
        for field_name in (
            "past_hit_rate",
            "calibration_error",
            "recent_source_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_size",
            _normalize_integral_decimal("sample_size", self.sample_size),
        )
        object.__setattr__(
            self,
            "days_since_last_resolved_market",
            _normalize_integral_decimal(
                "days_since_last_resolved_market",
                self.days_since_last_resolved_market,
            ),
        )


@dataclass(frozen=True)
class TeamMemoryDecayV10Result:
    team_id: str
    specialty: str
    adjusted_trust_score: Decimal
    memory_status: str
    training_priority: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_non_empty_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "specialty",
            _require_non_empty_string("specialty", self.specialty),
        )
        object.__setattr__(
            self,
            "adjusted_trust_score",
            _normalize_ratio("adjusted_trust_score", self.adjusted_trust_score),
        )
        if self.memory_status not in MEMORY_STATUSES:
            raise ValueError("memory_status must be trusted, watch, or decayed")
        if self.training_priority not in TRAINING_PRIORITIES:
            raise ValueError("training_priority must be low, medium, or high")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )


def score_team_memory_decay_v10(memory: TeamMemoryDecayV10Input) -> TeamMemoryDecayV10Result:
    if type(memory) is not TeamMemoryDecayV10Input:
        raise ValueError("memory must be a TeamMemoryDecayV10Input")

    decay_reason, decay_factor = _decay_factor(memory.days_since_last_resolved_market)
    hit_reason = _hit_rate_reason(memory.past_hit_rate)
    calibration_reason = _calibration_reason(memory.calibration_error)
    sample_reason, sample_factor = _sample_factor(memory.sample_size)
    source_reason = _source_quality_reason(memory.recent_source_quality)
    raw_score = _raw_trust_score(memory)
    adjusted_score = _clamp_ratio(raw_score * decay_factor * sample_factor)
    memory_status = _memory_status(adjusted_score, decay_reason)
    training_priority = _training_priority(memory_status)

    return TeamMemoryDecayV10Result(
        team_id=memory.team_id,
        specialty=memory.specialty,
        adjusted_trust_score=adjusted_score,
        memory_status=memory_status,
        training_priority=training_priority,
        reason_codes=(
            f"team_memory_{memory_status}",
            decay_reason,
            hit_reason,
            calibration_reason,
            sample_reason,
            source_reason,
            f"training_priority_{training_priority}",
        ),
    )


def _raw_trust_score(memory: TeamMemoryDecayV10Input) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        calibration_component = _clamp_ratio(ONE - memory.calibration_error)
        return _clamp_ratio(
            (memory.past_hit_rate + calibration_component + memory.recent_source_quality) / THREE,
        )


def _decay_factor(days_since_last_resolved_market: Decimal) -> tuple[str, Decimal]:
    if days_since_last_resolved_market <= CURRENT_GAP_DAYS:
        return "memory_decay_current", CURRENT_DECAY_FACTOR
    if days_since_last_resolved_market <= RECENT_GAP_DAYS:
        return "memory_decay_recent_gap", RECENT_DECAY_FACTOR
    if days_since_last_resolved_market <= STALE_GAP_DAYS:
        return "memory_decay_stale_gap", STALE_DECAY_FACTOR
    return "memory_decay_long_gap", LONG_DECAY_FACTOR


def _sample_factor(sample_size: Decimal) -> tuple[str, Decimal]:
    if sample_size >= STRONG_SAMPLE_SIZE:
        return "sample_size_strong", STRONG_SAMPLE_FACTOR
    if sample_size >= WATCH_SAMPLE_SIZE:
        return "sample_size_watch", WATCH_SAMPLE_FACTOR
    return "sample_size_low", LOW_SAMPLE_FACTOR


def _hit_rate_reason(past_hit_rate: Decimal) -> str:
    if past_hit_rate >= STRONG_HIT_RATE:
        return "hit_rate_strong"
    if past_hit_rate >= WATCH_HIT_RATE:
        return "hit_rate_watch"
    return "hit_rate_low"


def _calibration_reason(calibration_error: Decimal) -> str:
    if calibration_error <= LOW_CALIBRATION_ERROR:
        return "calibration_error_low"
    if calibration_error <= WATCH_CALIBRATION_ERROR:
        return "calibration_error_watch"
    return "calibration_error_high"


def _source_quality_reason(recent_source_quality: Decimal) -> str:
    if recent_source_quality >= STRONG_SOURCE_QUALITY:
        return "source_quality_strong"
    if recent_source_quality >= WATCH_SOURCE_QUALITY:
        return "source_quality_watch"
    return "source_quality_low"


def _memory_status(adjusted_score: Decimal, decay_reason: str) -> str:
    if decay_reason == "memory_decay_long_gap" or adjusted_score < DECAYED_SCORE:
        return "decayed"
    if adjusted_score >= TRUSTED_SCORE:
        return "trusted"
    return "watch"


def _training_priority(memory_status: str) -> str:
    if memory_status == "decayed":
        return "high"
    if memory_status == "watch":
        return "medium"
    return "low"


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return value.quantize(SCORE_QUANT)


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


__all__ = (
    "TeamMemoryDecayV10Input",
    "TeamMemoryDecayV10Result",
    "score_team_memory_decay_v10",
)
