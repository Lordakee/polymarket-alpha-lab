"""Pure read-only probability momentum reducer for market observation histories."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_PROBABILITY_MOMENTUM_MONITOR_CONFIG_VERSION = (
    "market-probability-momentum-monitor-v0"
)
PROBABILITY_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
UNSAFE_PUBLIC_SURFACE_MARKERS = (
    "li" + "ve",
    "a" + "uth",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)

MOMENTUM_STATUSES = (
    "insufficient_observations",
    "stable",
    "momentum",
    "reversal",
    "volatile",
    "volatile_reversal",
)
DIRECTIONS = ("up", "down", "flat")
REASON_CODES = (
    "empty_probability_history",
    "insufficient_probability_history",
    "probability_momentum_stable",
    "probability_momentum_up",
    "probability_momentum_down",
    "probability_reversal_observed",
    "probability_volatility_watch",
)


@dataclass(frozen=True)
class MarketProbabilityMomentumMonitorConfig:
    config_version: str = DEFAULT_MARKET_PROBABILITY_MOMENTUM_MONITOR_CONFIG_VERSION
    reversal_threshold: Decimal = Decimal("0.030000")
    volatility_watch_threshold: Decimal = Decimal("0.040000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumMonitorConfig:
            raise TypeError(
                "MarketProbabilityMomentumMonitorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumMonitorConfig:
            raise ValueError(
                "config must be exactly MarketProbabilityMomentumMonitorConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "reversal_threshold",
            _quantize_probability("reversal_threshold", self.reversal_threshold),
        )
        object.__setattr__(
            self,
            "volatility_watch_threshold",
            _quantize_probability(
                "volatility_watch_threshold",
                self.volatility_watch_threshold,
            ),
        )
        require_paper_only_flags("momentum monitor config", self)
        _reject_unsafe_public_surface("momentum monitor config", self)


@dataclass(frozen=True)
class MarketProbabilityObservation:
    observation_id: str
    observed_at: datetime
    probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityObservation:
            raise TypeError("MarketProbabilityObservation does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityObservation:
            raise ValueError("observation must be exactly MarketProbabilityObservation")
        _require_canonical_string("observation_id", self.observation_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability",
            _quantize_probability("probability", self.probability),
        )
        require_paper_only_flags("probability observation", self)
        _reject_unsafe_public_surface("probability observation", self)


@dataclass(frozen=True)
class MarketProbabilityMovementRow:
    movement_index: Decimal
    observed_at: datetime
    probability: Decimal
    previous_probability: Decimal
    step_change: Decimal
    absolute_step_change: Decimal
    direction: str
    reversal_from_previous: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMovementRow:
            raise TypeError("MarketProbabilityMovementRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMovementRow:
            raise ValueError("movement row must be exactly MarketProbabilityMovementRow")
        object.__setattr__(
            self,
            "movement_index",
            _normalize_positive_count("movement_index", self.movement_index),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability",
            _quantize_probability("probability", self.probability),
        )
        object.__setattr__(
            self,
            "previous_probability",
            _quantize_probability("previous_probability", self.previous_probability),
        )
        object.__setattr__(
            self,
            "step_change",
            _quantize_change("step_change", self.step_change),
        )
        object.__setattr__(
            self,
            "absolute_step_change",
            _quantize_probability("absolute_step_change", self.absolute_step_change),
        )
        _require_member("direction", self.direction, DIRECTIONS)
        if type(self.reversal_from_previous) is not bool:
            raise ValueError("reversal_from_previous must be a bool")
        require_paper_only_flags("movement row", self)
        _validate_movement_row(self)
        _reject_unsafe_public_surface("movement row", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumMonitorReport:
    generated_at: datetime
    config_version: str
    momentum_status: str
    observation_count: Decimal
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    first_probability: Decimal | None
    latest_probability: Decimal | None
    net_probability_change: Decimal
    absolute_probability_change: Decimal
    mean_step_change: Decimal
    mean_absolute_step_change: Decimal
    max_up_step_change: Decimal
    max_down_step_change: Decimal
    reversal_count: Decimal
    volatility_score: Decimal
    direction: str
    movement_rows: tuple[MarketProbabilityMovementRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumMonitorReport:
            raise TypeError(
                "MarketProbabilityMomentumMonitorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumMonitorReport:
            raise ValueError(
                "report must be exactly MarketProbabilityMomentumMonitorReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("momentum_status", self.momentum_status, MOMENTUM_STATUSES)
        object.__setattr__(
            self,
            "observation_count",
            _normalize_count("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_optional_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("first_probability", "latest_probability"):
            object.__setattr__(
                self,
                field_name,
                _quantize_optional_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_probability_change",
            "mean_step_change",
            "max_up_step_change",
            "max_down_step_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_change(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_probability_change",
            "mean_absolute_step_change",
            "volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reversal_count",
            _normalize_count("reversal_count", self.reversal_count),
        )
        _require_member("direction", self.direction, DIRECTIONS)
        object.__setattr__(
            self,
            "movement_rows",
            _normalize_movement_rows(self.movement_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("momentum monitor report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)
        _reject_unsafe_public_surface("momentum monitor report", self)


def build_market_probability_momentum_monitor_report(
    observations: object,
    *,
    config: MarketProbabilityMomentumMonitorConfig,
    generated_at: datetime,
    ) -> MarketProbabilityMomentumMonitorReport:
    if type(config) is not MarketProbabilityMomentumMonitorConfig:
        raise ValueError("config must be a MarketProbabilityMomentumMonitorConfig")
    require_paper_only_flags("momentum monitor config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    ordered_observations = _ordered_observations(normalized_observations)
    movement_rows = _movement_rows(
        ordered_observations,
        reversal_threshold=config.reversal_threshold,
	    )
    observation_count = _count_decimal(len(ordered_observations))
    first_observation = ordered_observations[0] if ordered_observations else None
    latest_observation = ordered_observations[-1] if ordered_observations else None
    net_change = (
        ZERO
        if first_observation is None or latest_observation is None
        else latest_observation.probability - first_observation.probability
    )
    mean_step_change = _mean_step_change(movement_rows)
    mean_absolute_step_change = _mean_absolute_step_change(movement_rows)
    reversal_count = _count_decimal(
        sum(1 for row in movement_rows if row.reversal_from_previous),
    )
    status = _momentum_status(
        observation_count=observation_count,
        reversal_count=reversal_count,
        volatility_score=mean_absolute_step_change,
        volatility_watch_threshold=config.volatility_watch_threshold,
    )
    direction = _direction(net_change)

    return MarketProbabilityMomentumMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        momentum_status=status,
        observation_count=observation_count,
        first_observed_at=None if first_observation is None else first_observation.observed_at,
        latest_observed_at=(
            None if latest_observation is None else latest_observation.observed_at
        ),
        first_probability=(
            None if first_observation is None else first_observation.probability
        ),
        latest_probability=(
            None if latest_observation is None else latest_observation.probability
        ),
        net_probability_change=net_change,
        absolute_probability_change=abs(net_change),
        mean_step_change=mean_step_change,
        mean_absolute_step_change=mean_absolute_step_change,
        max_up_step_change=_max_up_step_change(movement_rows),
        max_down_step_change=_max_down_step_change(movement_rows),
        reversal_count=reversal_count,
        volatility_score=mean_absolute_step_change,
        direction=direction,
        movement_rows=movement_rows,
        reason_codes=_reason_codes(
            observation_count=observation_count,
            reversal_count=reversal_count,
            volatility_score=mean_absolute_step_change,
            volatility_watch_threshold=config.volatility_watch_threshold,
            direction=direction,
        ),
    )


def _normalize_observations(
    observations: object,
) -> tuple[MarketProbabilityObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketProbabilityObservation:
            raise ValueError("observations must contain MarketProbabilityObservation values")
        require_paper_only_flags("probability observation", observation)
        if observation.observation_id in seen_ids:
            raise ValueError("duplicate observation_id values are not allowed")
        seen_ids.add(observation.observation_id)
    return normalized


def _ordered_observations(
    observations: tuple[MarketProbabilityObservation, ...],
) -> tuple[MarketProbabilityObservation, ...]:
    return tuple(
        observation
        for _observed_at, _index, observation in sorted(
            (observation.observed_at, index, observation)
            for index, observation in enumerate(observations)
        )
    )


def _movement_rows(
    observations: tuple[MarketProbabilityObservation, ...],
    *,
    reversal_threshold: Decimal,
) -> tuple[MarketProbabilityMovementRow, ...]:
    rows: list[MarketProbabilityMovementRow] = []
    previous_direction = "flat"
    for index, observation in enumerate(observations[1:], start=1):
        previous_probability = observations[index - 1].probability
        step_change = observation.probability - previous_probability
        direction = _direction(step_change)
        reversal_from_previous = (
            previous_direction != "flat"
            and direction != "flat"
            and direction != previous_direction
            and abs(step_change) >= reversal_threshold
        )
        rows.append(
            MarketProbabilityMovementRow(
                movement_index=_count_decimal(index),
                observed_at=observation.observed_at,
                probability=observation.probability,
                previous_probability=previous_probability,
                step_change=step_change,
                absolute_step_change=abs(step_change),
                direction=direction,
                reversal_from_previous=reversal_from_previous,
            ),
        )
        if direction != "flat":
            previous_direction = direction
    return tuple(rows)


def _momentum_status(
    *,
    observation_count: Decimal,
    reversal_count: Decimal,
    volatility_score: Decimal,
    volatility_watch_threshold: Decimal,
) -> str:
    if observation_count < 2:
        return "insufficient_observations"
    is_volatile = volatility_score >= volatility_watch_threshold
    if is_volatile and reversal_count:
        return "volatile_reversal"
    if is_volatile:
        return "volatile"
    if reversal_count:
        return "reversal"
    if volatility_score == ZERO:
        return "stable"
    return "momentum"


def _reason_codes(
    *,
    observation_count: Decimal,
    reversal_count: Decimal,
    volatility_score: Decimal,
    volatility_watch_threshold: Decimal,
    direction: str,
) -> tuple[str, ...]:
    if observation_count == 0:
        return ("empty_probability_history",)
    if observation_count == 1:
        return ("insufficient_probability_history",)
    codes: list[str] = []
    if reversal_count:
        codes.append("probability_reversal_observed")
    if volatility_score >= volatility_watch_threshold:
        codes.append("probability_volatility_watch")
    if direction == "up":
        codes.append("probability_momentum_up")
    elif direction == "down":
        codes.append("probability_momentum_down")
    else:
        codes.append("probability_momentum_stable")
    return tuple(codes)


def _mean_step_change(rows: tuple[MarketProbabilityMovementRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_change(
        "mean_step_change",
        sum((row.step_change for row in rows), ZERO) / Decimal(len(rows)),
    )


def _mean_absolute_step_change(rows: tuple[MarketProbabilityMovementRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_probability(
        "mean_absolute_step_change",
        sum((row.absolute_step_change for row in rows), ZERO) / Decimal(len(rows)),
    )


def _max_up_step_change(rows: tuple[MarketProbabilityMovementRow, ...]) -> Decimal:
    values = tuple(row.step_change for row in rows if row.step_change > ZERO)
    return max(values) if values else ZERO


def _max_down_step_change(rows: tuple[MarketProbabilityMovementRow, ...]) -> Decimal:
    values = tuple(row.step_change for row in rows if row.step_change < ZERO)
    return min(values) if values else ZERO


def _validate_movement_row(row: MarketProbabilityMovementRow) -> None:
    expected_change = _quantize_change(
        "step_change",
        row.probability - row.previous_probability,
    )
    if row.step_change != expected_change:
        raise ValueError("step_change must match probability movement")
    if row.absolute_step_change != abs(expected_change):
        raise ValueError("absolute_step_change must match step_change")
    if row.direction != _direction(row.step_change):
        raise ValueError("direction must match step_change")


def _validate_report(report: MarketProbabilityMomentumMonitorReport) -> None:
    observation_count = _count_int("observation_count", report.observation_count)
    reversal_count = _count_int("reversal_count", report.reversal_count)
    if observation_count == 0:
        _require_none("first_observed_at", report.first_observed_at)
        _require_none("latest_observed_at", report.latest_observed_at)
        _require_none("first_probability", report.first_probability)
        _require_none("latest_probability", report.latest_probability)
        if report.movement_rows:
            raise ValueError("empty report must not have movement_rows")
    else:
        if report.first_observed_at is None:
            raise ValueError("first_observed_at is required when observations exist")
        if report.latest_observed_at is None:
            raise ValueError("latest_observed_at is required when observations exist")
        if report.first_probability is None:
            raise ValueError("first_probability is required when observations exist")
        if report.latest_probability is None:
            raise ValueError("latest_probability is required when observations exist")
        if report.latest_observed_at > report.generated_at:
            raise ValueError("latest_observed_at must not be after generated_at")
        expected_change = _quantize_change(
            "net_probability_change",
            report.latest_probability - report.first_probability,
        )
        if report.net_probability_change != expected_change:
            raise ValueError("net_probability_change must match endpoints")
    if len(report.movement_rows) != max(0, observation_count - 1):
        raise ValueError("movement_rows must match observation_count")
    if tuple(row.movement_index for row in report.movement_rows) != tuple(
        _count_decimal(index) for index in range(1, len(report.movement_rows) + 1)
    ):
        raise ValueError("movement_rows must be deterministic")
    if tuple(row.observed_at for row in report.movement_rows) != tuple(
        sorted(row.observed_at for row in report.movement_rows),
    ):
        raise ValueError("movement_rows must be deterministic")
    if report.absolute_probability_change != abs(report.net_probability_change):
        raise ValueError("absolute_probability_change must match net_probability_change")
    if report.mean_step_change != _mean_step_change(report.movement_rows):
        raise ValueError("mean_step_change must match movement_rows")
    if report.mean_absolute_step_change != _mean_absolute_step_change(report.movement_rows):
        raise ValueError("mean_absolute_step_change must match movement_rows")
    if report.volatility_score != report.mean_absolute_step_change:
        raise ValueError("volatility_score must match mean_absolute_step_change")
    if report.max_up_step_change != _max_up_step_change(report.movement_rows):
        raise ValueError("max_up_step_change must match movement_rows")
    if report.max_down_step_change != _max_down_step_change(report.movement_rows):
        raise ValueError("max_down_step_change must match movement_rows")
    if reversal_count != sum(1 for row in report.movement_rows if row.reversal_from_previous):
        raise ValueError("reversal_count must match movement_rows")
    if report.direction != _direction(report.net_probability_change):
        raise ValueError("direction must match net_probability_change")
    if report.momentum_status == "insufficient_observations":
        if observation_count > 1:
            raise ValueError("insufficient status requires fewer than two observations")
    elif observation_count < 2:
        raise ValueError("non-insufficient status requires observations")
    if observation_count == 0 and report.reason_codes != ("empty_probability_history",):
        raise ValueError("empty report reason_codes must match observations")
    if observation_count == 1 and report.reason_codes != (
        "insufficient_probability_history",
    ):
        raise ValueError("single-observation report reason_codes must match observations")


def _normalize_movement_rows(
    rows: tuple[MarketProbabilityMovementRow, ...],
) -> tuple[MarketProbabilityMovementRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("movement_rows must be a tuple")
    for row in rows:
        if type(row) is not MarketProbabilityMovementRow:
            raise ValueError("movement_rows must contain MarketProbabilityMovementRow values")
        require_paper_only_flags("movement row", row)
    return rows


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be known probability momentum reason codes")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    expected_order = tuple(
        reason_code for reason_code in _ordered_reason_codes() if reason_code in reason_codes
    )
    if reason_codes != expected_order:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _ordered_reason_codes() -> tuple[str, ...]:
    return (
        "empty_probability_history",
        "insufficient_probability_history",
        "probability_reversal_observed",
        "probability_volatility_watch",
        "probability_momentum_up",
        "probability_momentum_down",
        "probability_momentum_stable",
    )


def _direction(value: Decimal) -> str:
    if value > ZERO:
        return "up"
    if value < ZERO:
        return "down"
    return "flat"


def _quantize_probability(field_name: str, value: Any) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(PROBABILITY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _quantize_optional_probability(field_name: str, value: Any) -> Decimal | None:
    if value is None:
        return None
    return _quantize_probability(field_name, value)


def _quantize_change(field_name: str, value: Any) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value.quantize(PROBABILITY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: Any, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _count_int(field_name: str, value: Decimal) -> int:
    normalized = _normalize_count(field_name, value)
    return int(normalized)


def _normalize_count(field_name: str, value: Any) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _normalize_positive_count(field_name: str, value: Any) -> Decimal:
    decimal_value = _normalize_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no observations")


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: Any) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal")
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


def market_probability_momentum_monitor_payload(
    report: MarketProbabilityMomentumMonitorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is not MarketProbabilityMomentumMonitorReport:
        if type(report) is dict:
            reject_unsafe_surface_fields("momentum monitor payload", report)
            _reject_unsafe_public_surface("momentum monitor payload", report)
            _validate_public_payload(report)
            return dict(report)
        raise ValueError("report must be a MarketProbabilityMomentumMonitorReport")
    require_paper_only_flags("momentum monitor report", report)
    _validate_report(report)
    _validate_report_derived_validation_digest(report)
    _reject_unsafe_public_surface("momentum monitor report", report)
    payload = _json_ready(report)
    reject_unsafe_surface_fields("momentum monitor payload", payload)
    _reject_unsafe_public_surface("momentum monitor payload", payload)
    if type(payload) is not dict:
        raise ValueError("momentum monitor payload must be a JSON object")
    return payload


def _report_payload_without_digest(
    report: MarketProbabilityMomentumMonitorReport,
) -> dict[str, Any]:
    return {
        field.name: _json_ready(getattr(report, field.name))
        for field in fields(report)
        if field.name != DERIVED_VALIDATION_DIGEST_FIELD
    }


def _report_derived_validation_digest(
    report: MarketProbabilityMomentumMonitorReport,
) -> str:
    canonical_payload = json.dumps(
        _report_payload_without_digest(report),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_report_derived_validation_digest(
    report: MarketProbabilityMomentumMonitorReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_sha256(field_name: str, value: Any) -> str:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_public_payload_fields(payload)
    expected_digest = _payload_derived_validation_digest(payload)
    actual_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if actual_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _require_public_payload_fields(payload: dict[str, Any]) -> None:
    expected_fields = tuple(field.name for field in fields(MarketProbabilityMomentumMonitorReport))
    if DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest missing from public payload")
    if tuple(payload) != expected_fields:
        raise ValueError("public payload fields must match momentum monitor schema")


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: _json_ready(value)
        for key, value in payload.items()
        if key != DERIVED_VALIDATION_DIGEST_FIELD
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _reject_unsafe_public_surface(label: str, value: Any) -> None:
    for text in _public_surface_text_values(value):
        normalized_text = text.lower()
        if any(marker in normalized_text for marker in UNSAFE_PUBLIC_SURFACE_MARKERS):
            raise ValueError(f"unsafe public surface in {label}")


def _public_surface_text_values(value: Any) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _public_surface_text_values(asdict(value))
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.append(key)
            values.extend(_public_surface_text_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_public_surface_text_values(item))
        return tuple(values)
    return ()


__all__ = (
    "DEFAULT_MARKET_PROBABILITY_MOMENTUM_MONITOR_CONFIG_VERSION",
    "MarketProbabilityMomentumMonitorConfig",
    "MarketProbabilityMomentumMonitorReport",
    "MarketProbabilityMovementRow",
    "MarketProbabilityObservation",
    "build_market_probability_momentum_monitor_report",
    "market_probability_momentum_monitor_payload",
)
