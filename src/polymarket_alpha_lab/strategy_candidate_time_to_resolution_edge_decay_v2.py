"""Pure paper/report time-to-resolution edge decay score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CLOSE_DECAY_WINDOW_HOURS = Decimal("72.000000")
CLOSE_PROXIMITY_EDGE_WEIGHT = Decimal("0.250000")
SOURCE_FRESHNESS_EDGE_WEIGHT = Decimal("0.300000")
SETTLEMENT_LAG_WINDOW_HOURS = Decimal("72.000000")
SETTLEMENT_LAG_EDGE_WEIGHT = Decimal("0.100000")
VELOCITY_PROJECTION_CAP_HOURS = Decimal("24.000000")
UNCERTAINTY_EDGE_WEIGHT = Decimal("0.200000")
MODERATE_EDGE_DECAY_RATIO = Decimal("0.250000")
HIGH_EDGE_DECAY_RATIO = Decimal("0.500000")
SCORE_STATUSES = ("candidate", "watch", "blocked")
SCORE_DECISIONS = ("paper_candidate", "manual_review", "reject")
EDGE_DECAY_RANKS = ("low", "moderate", "high")
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "candidate_id",
    "current_edge_bps",
    "hours_to_close",
    "close_proximity_ratio",
    "close_proximity_decay_bps",
    "source_freshness_decay_ratio",
    "source_freshness_decay_bps",
    "settlement_lag_hours",
    "settlement_lag_ratio",
    "settlement_lag_decay_bps",
    "liquidity_exit_friction_bps",
    "probability_movement_velocity_bps_per_hour",
    "velocity_projection_hours",
    "probability_velocity_decay_bps",
    "uncertainty_ratio",
    "uncertainty_decay_bps",
    "expected_edge_decay_bps",
    "expected_edge_decay_ratio",
    "paper_score_bps",
    "minimum_actionable_score",
    "edge_decay_rank",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyCandidateTimeToResolutionEdgeDecayV2Input:
    candidate_id: str
    current_edge_bps: Decimal
    hours_to_close: Decimal
    source_freshness_decay_ratio: Decimal
    settlement_lag_hours: Decimal
    liquidity_exit_friction_bps: Decimal
    probability_movement_velocity_bps_per_hour: Decimal
    uncertainty_ratio: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "current_edge_bps",
            _normalize_decimal("current_edge_bps", self.current_edge_bps),
        )
        for field_name in (
            "hours_to_close",
            "settlement_lag_hours",
            "liquidity_exit_friction_bps",
            "probability_movement_velocity_bps_per_hour",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_freshness_decay_ratio", "uncertainty_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
            "candidate time to resolution edge decay input",
            self,
        )
        _require_paper_flags("candidate time to resolution edge decay input", self)


@dataclass(frozen=True)
class StrategyCandidateTimeToResolutionEdgeDecayV2Result:
    candidate_id: str
    current_edge_bps: Decimal
    hours_to_close: Decimal
    close_proximity_ratio: Decimal
    close_proximity_decay_bps: Decimal
    source_freshness_decay_ratio: Decimal
    source_freshness_decay_bps: Decimal
    settlement_lag_hours: Decimal
    settlement_lag_ratio: Decimal
    settlement_lag_decay_bps: Decimal
    liquidity_exit_friction_bps: Decimal
    probability_movement_velocity_bps_per_hour: Decimal
    velocity_projection_hours: Decimal
    probability_velocity_decay_bps: Decimal
    uncertainty_ratio: Decimal
    uncertainty_decay_bps: Decimal
    expected_edge_decay_bps: Decimal
    expected_edge_decay_ratio: Decimal
    paper_score_bps: Decimal
    minimum_actionable_score: Decimal
    edge_decay_rank: str
    score_status: str
    score_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in ("current_edge_bps", "paper_score_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "hours_to_close",
            "close_proximity_decay_bps",
            "source_freshness_decay_bps",
            "settlement_lag_hours",
            "settlement_lag_decay_bps",
            "liquidity_exit_friction_bps",
            "probability_movement_velocity_bps_per_hour",
            "velocity_projection_hours",
            "probability_velocity_decay_bps",
            "uncertainty_decay_bps",
            "expected_edge_decay_bps",
            "expected_edge_decay_ratio",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "close_proximity_ratio",
            "source_freshness_decay_ratio",
            "settlement_lag_ratio",
            "uncertainty_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_choice("edge_decay_rank", self.edge_decay_rank, EDGE_DECAY_RANKS)
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
            "candidate time to resolution edge decay result",
            self,
        )
        _require_paper_flags("candidate time to resolution edge decay result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_time_to_resolution_edge_decay_v2_payload(self)


def estimate_strategy_candidate_time_to_resolution_edge_decay_v2(
    score_input: StrategyCandidateTimeToResolutionEdgeDecayV2Input,
) -> StrategyCandidateTimeToResolutionEdgeDecayV2Result:
    if type(score_input) is not StrategyCandidateTimeToResolutionEdgeDecayV2Input:
        raise ValueError(
            "score_input must be a StrategyCandidateTimeToResolutionEdgeDecayV2Input",
        )
    reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
        "candidate time to resolution edge decay input",
        score_input,
    )
    _require_paper_flags("candidate time to resolution edge decay input", score_input)

    close_proximity_ratio = _close_proximity_ratio(score_input.hours_to_close)
    close_proximity_decay_bps = _weighted_edge_decay_bps(
        "close_proximity_decay_bps",
        score_input.current_edge_bps,
        close_proximity_ratio,
        CLOSE_PROXIMITY_EDGE_WEIGHT,
    )
    source_freshness_decay_bps = _weighted_edge_decay_bps(
        "source_freshness_decay_bps",
        score_input.current_edge_bps,
        score_input.source_freshness_decay_ratio,
        SOURCE_FRESHNESS_EDGE_WEIGHT,
    )
    settlement_lag_ratio = _settlement_lag_ratio(score_input.settlement_lag_hours)
    settlement_lag_decay_bps = _weighted_edge_decay_bps(
        "settlement_lag_decay_bps",
        score_input.current_edge_bps,
        settlement_lag_ratio,
        SETTLEMENT_LAG_EDGE_WEIGHT,
    )
    velocity_projection_hours = _velocity_projection_hours(score_input.hours_to_close)
    probability_velocity_decay_bps = _probability_velocity_decay_bps(
        score_input.probability_movement_velocity_bps_per_hour,
        velocity_projection_hours,
    )
    uncertainty_decay_bps = _weighted_edge_decay_bps(
        "uncertainty_decay_bps",
        score_input.current_edge_bps,
        score_input.uncertainty_ratio,
        UNCERTAINTY_EDGE_WEIGHT,
    )
    expected_edge_decay_bps = _expected_edge_decay_bps(
        close_proximity_decay_bps=close_proximity_decay_bps,
        source_freshness_decay_bps=source_freshness_decay_bps,
        settlement_lag_decay_bps=settlement_lag_decay_bps,
        liquidity_exit_friction_bps=score_input.liquidity_exit_friction_bps,
        probability_velocity_decay_bps=probability_velocity_decay_bps,
        uncertainty_decay_bps=uncertainty_decay_bps,
    )
    expected_edge_decay_ratio = _expected_edge_decay_ratio(
        expected_edge_decay_bps,
        score_input.current_edge_bps,
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        score_input.current_edge_bps - expected_edge_decay_bps,
    )
    edge_decay_rank = _edge_decay_rank(expected_edge_decay_ratio)
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return StrategyCandidateTimeToResolutionEdgeDecayV2Result(
        candidate_id=score_input.candidate_id,
        current_edge_bps=score_input.current_edge_bps,
        hours_to_close=score_input.hours_to_close,
        close_proximity_ratio=close_proximity_ratio,
        close_proximity_decay_bps=close_proximity_decay_bps,
        source_freshness_decay_ratio=score_input.source_freshness_decay_ratio,
        source_freshness_decay_bps=source_freshness_decay_bps,
        settlement_lag_hours=score_input.settlement_lag_hours,
        settlement_lag_ratio=settlement_lag_ratio,
        settlement_lag_decay_bps=settlement_lag_decay_bps,
        liquidity_exit_friction_bps=score_input.liquidity_exit_friction_bps,
        probability_movement_velocity_bps_per_hour=(
            score_input.probability_movement_velocity_bps_per_hour
        ),
        velocity_projection_hours=velocity_projection_hours,
        probability_velocity_decay_bps=probability_velocity_decay_bps,
        uncertainty_ratio=score_input.uncertainty_ratio,
        uncertainty_decay_bps=uncertainty_decay_bps,
        expected_edge_decay_bps=expected_edge_decay_bps,
        expected_edge_decay_ratio=expected_edge_decay_ratio,
        paper_score_bps=paper_score_bps,
        minimum_actionable_score=score_input.minimum_actionable_score,
        edge_decay_rank=edge_decay_rank,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            current_edge_bps=score_input.current_edge_bps,
            close_proximity_decay_bps=close_proximity_decay_bps,
            source_freshness_decay_bps=source_freshness_decay_bps,
            settlement_lag_decay_bps=settlement_lag_decay_bps,
            liquidity_exit_friction_bps=score_input.liquidity_exit_friction_bps,
            probability_velocity_decay_bps=probability_velocity_decay_bps,
            uncertainty_decay_bps=uncertainty_decay_bps,
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            edge_decay_rank=edge_decay_rank,
            score_status=score_status,
        ),
    )


def strategy_candidate_time_to_resolution_edge_decay_v2_payload(
    result: StrategyCandidateTimeToResolutionEdgeDecayV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateTimeToResolutionEdgeDecayV2Result:
        raise ValueError(
            "result must be a StrategyCandidateTimeToResolutionEdgeDecayV2Result",
        )
    _require_paper_flags("candidate time to resolution edge decay result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
        "candidate time to resolution edge decay result",
        result,
    )
    return _json_ready(asdict(result))


def reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _close_proximity_ratio(hours_to_close: Decimal) -> Decimal:
    if hours_to_close >= CLOSE_DECAY_WINDOW_HOURS:
        return ZERO
    return _normalize_ratio(
        "close_proximity_ratio",
        (CLOSE_DECAY_WINDOW_HOURS - hours_to_close) / CLOSE_DECAY_WINDOW_HOURS,
    )


def _settlement_lag_ratio(settlement_lag_hours: Decimal) -> Decimal:
    if settlement_lag_hours >= SETTLEMENT_LAG_WINDOW_HOURS:
        return ONE
    return _normalize_ratio(
        "settlement_lag_ratio",
        settlement_lag_hours / SETTLEMENT_LAG_WINDOW_HOURS,
    )


def _weighted_edge_decay_bps(
    field_name: str,
    current_edge_bps: Decimal,
    ratio: Decimal,
    weight: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        field_name,
        _positive_edge_bps(current_edge_bps) * ratio * weight,
    )


def _positive_edge_bps(current_edge_bps: Decimal) -> Decimal:
    if current_edge_bps <= ZERO:
        return ZERO
    return current_edge_bps


def _velocity_projection_hours(hours_to_close: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "velocity_projection_hours",
        min(hours_to_close, VELOCITY_PROJECTION_CAP_HOURS),
    )


def _probability_velocity_decay_bps(
    probability_movement_velocity_bps_per_hour: Decimal,
    velocity_projection_hours: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "probability_velocity_decay_bps",
        probability_movement_velocity_bps_per_hour * velocity_projection_hours,
    )


def _expected_edge_decay_bps(
    *,
    close_proximity_decay_bps: Decimal,
    source_freshness_decay_bps: Decimal,
    settlement_lag_decay_bps: Decimal,
    liquidity_exit_friction_bps: Decimal,
    probability_velocity_decay_bps: Decimal,
    uncertainty_decay_bps: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "expected_edge_decay_bps",
        close_proximity_decay_bps
        + source_freshness_decay_bps
        + settlement_lag_decay_bps
        + liquidity_exit_friction_bps
        + probability_velocity_decay_bps
        + uncertainty_decay_bps,
    )


def _expected_edge_decay_ratio(
    expected_edge_decay_bps: Decimal,
    current_edge_bps: Decimal,
) -> Decimal:
    if current_edge_bps <= ZERO:
        if expected_edge_decay_bps > ZERO:
            return ONE
        return ZERO
    return _normalize_nonnegative_decimal(
        "expected_edge_decay_ratio",
        expected_edge_decay_bps / current_edge_bps,
    )


def _edge_decay_rank(expected_edge_decay_ratio: Decimal) -> str:
    if expected_edge_decay_ratio >= HIGH_EDGE_DECAY_RATIO:
        return "high"
    if expected_edge_decay_ratio >= MODERATE_EDGE_DECAY_RATIO:
        return "moderate"
    return "low"


def _score_status(paper_score_bps: Decimal, minimum_actionable_score: Decimal) -> str:
    if paper_score_bps <= ZERO:
        return "blocked"
    if paper_score_bps < minimum_actionable_score:
        return "watch"
    return "candidate"


def _score_decision(score_status: str) -> str:
    if score_status == "candidate":
        return "paper_candidate"
    if score_status == "watch":
        return "manual_review"
    if score_status == "blocked":
        return "reject"
    raise ValueError("score_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    current_edge_bps: Decimal,
    close_proximity_decay_bps: Decimal,
    source_freshness_decay_bps: Decimal,
    settlement_lag_decay_bps: Decimal,
    liquidity_exit_friction_bps: Decimal,
    probability_velocity_decay_bps: Decimal,
    uncertainty_decay_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    edge_decay_rank: str,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_time_to_resolution_edge_decay_v2",
        f"score_{score_status}",
        f"edge_decay_{edge_decay_rank}",
        _edge_reason_code(current_edge_bps),
    ]
    if close_proximity_decay_bps > ZERO:
        additions.append("close_proximity_decay_applied")
    if source_freshness_decay_bps > ZERO:
        additions.append("source_freshness_decay_applied")
    if settlement_lag_decay_bps > ZERO:
        additions.append("settlement_lag_decay_applied")
    if liquidity_exit_friction_bps > ZERO:
        additions.append("liquidity_exit_friction_applied")
    if probability_velocity_decay_bps > ZERO:
        additions.append("probability_velocity_decay_applied")
    if uncertainty_decay_bps > ZERO:
        additions.append("uncertainty_decay_applied")
    if paper_score_bps <= ZERO:
        additions.append("score_below_zero")
    elif paper_score_bps < minimum_actionable_score:
        additions.append("score_positive_below_minimum")
    else:
        additions.append("minimum_actionable_score_met")
    return _append_reason_codes(existing, tuple(additions))


def _edge_reason_code(current_edge_bps: Decimal) -> str:
    if current_edge_bps > ZERO:
        return "edge_positive"
    if current_edge_bps == ZERO:
        return "edge_flat"
    return "edge_negative"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_result_consistency(
    result: StrategyCandidateTimeToResolutionEdgeDecayV2Result,
) -> None:
    if result.close_proximity_ratio != _close_proximity_ratio(result.hours_to_close):
        raise ValueError("close_proximity_ratio must match hours_to_close")
    if result.close_proximity_decay_bps != _weighted_edge_decay_bps(
        "close_proximity_decay_bps",
        result.current_edge_bps,
        result.close_proximity_ratio,
        CLOSE_PROXIMITY_EDGE_WEIGHT,
    ):
        raise ValueError("close_proximity_decay_bps must match close inputs")
    if result.source_freshness_decay_bps != _weighted_edge_decay_bps(
        "source_freshness_decay_bps",
        result.current_edge_bps,
        result.source_freshness_decay_ratio,
        SOURCE_FRESHNESS_EDGE_WEIGHT,
    ):
        raise ValueError("source_freshness_decay_bps must match freshness inputs")
    if result.settlement_lag_ratio != _settlement_lag_ratio(
        result.settlement_lag_hours,
    ):
        raise ValueError("settlement_lag_ratio must match settlement lag")
    if result.settlement_lag_decay_bps != _weighted_edge_decay_bps(
        "settlement_lag_decay_bps",
        result.current_edge_bps,
        result.settlement_lag_ratio,
        SETTLEMENT_LAG_EDGE_WEIGHT,
    ):
        raise ValueError("settlement_lag_decay_bps must match lag inputs")
    if result.velocity_projection_hours != _velocity_projection_hours(
        result.hours_to_close,
    ):
        raise ValueError("velocity_projection_hours must match hours_to_close")
    if result.probability_velocity_decay_bps != _probability_velocity_decay_bps(
        result.probability_movement_velocity_bps_per_hour,
        result.velocity_projection_hours,
    ):
        raise ValueError("probability_velocity_decay_bps must match velocity inputs")
    if result.uncertainty_decay_bps != _weighted_edge_decay_bps(
        "uncertainty_decay_bps",
        result.current_edge_bps,
        result.uncertainty_ratio,
        UNCERTAINTY_EDGE_WEIGHT,
    ):
        raise ValueError("uncertainty_decay_bps must match uncertainty inputs")
    if result.expected_edge_decay_bps != _expected_edge_decay_bps(
        close_proximity_decay_bps=result.close_proximity_decay_bps,
        source_freshness_decay_bps=result.source_freshness_decay_bps,
        settlement_lag_decay_bps=result.settlement_lag_decay_bps,
        liquidity_exit_friction_bps=result.liquidity_exit_friction_bps,
        probability_velocity_decay_bps=result.probability_velocity_decay_bps,
        uncertainty_decay_bps=result.uncertainty_decay_bps,
    ):
        raise ValueError("expected_edge_decay_bps must match score components")
    if result.expected_edge_decay_ratio != _expected_edge_decay_ratio(
        result.expected_edge_decay_bps,
        result.current_edge_bps,
    ):
        raise ValueError("expected_edge_decay_ratio must match edge decay")
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.current_edge_bps - result.expected_edge_decay_bps,
    ):
        raise ValueError("paper_score_bps must match edge decay")
    if result.edge_decay_rank != _edge_decay_rank(result.expected_edge_decay_ratio):
        raise ValueError("edge_decay_rank must match expected_edge_decay_ratio")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.minimum_actionable_score,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _derived_validation_digest(
    result: StrategyCandidateTimeToResolutionEdgeDecayV2Result,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between {ZERO} and {ONE}")
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
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "SCORE_STATUSES",
    "SCORE_DECISIONS",
    "EDGE_DECAY_RANKS",
    "StrategyCandidateTimeToResolutionEdgeDecayV2Input",
    "StrategyCandidateTimeToResolutionEdgeDecayV2Result",
    "estimate_strategy_candidate_time_to_resolution_edge_decay_v2",
    "strategy_candidate_time_to_resolution_edge_decay_v2_payload",
    "reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload",
)
