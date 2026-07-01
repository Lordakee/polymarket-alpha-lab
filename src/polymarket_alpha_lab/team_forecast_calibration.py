"""Paper-only calibration diagnostics for team forecast rows."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_FLOOR, localcontext
from typing import Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
GROUP_TYPES = frozenset(("team", "category", "event_template"))
STATUSES = frozenset(("candidate", "validated"))
YES = "yes"


@dataclass(frozen=True)
class TeamForecastCalibrationConfig:
    config_version: str = "team-forecast-calibration-v0"
    bucket_count: int = 10
    min_settled_forecasts: int = 30
    min_group_settled_forecasts: int | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("bucket_count", self.bucket_count)
        _require_nonnegative_int("min_settled_forecasts", self.min_settled_forecasts)
        if self.min_group_settled_forecasts is None:
            object.__setattr__(
                self,
                "min_group_settled_forecasts",
                self.min_settled_forecasts,
            )
        else:
            _require_nonnegative_int(
                "min_group_settled_forecasts",
                self.min_group_settled_forecasts,
            )
        _require_safety_flags("TeamForecastCalibrationConfig", self)


@dataclass(frozen=True)
class TeamForecastCalibrationBucket:
    bucket_label: str
    lower_probability: Decimal
    upper_probability: Decimal
    forecast_count: int
    settled_count: int
    observed_yes_rate: Decimal
    average_forecast_probability: Decimal
    average_confidence: Decimal
    average_brier_score: Decimal
    calibration_error: Decimal
    directionally_correct_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("bucket_label", self.bucket_label)
        object.__setattr__(
            self,
            "lower_probability",
            _normalize_probability("lower_probability", self.lower_probability),
        )
        object.__setattr__(
            self,
            "upper_probability",
            _normalize_probability("upper_probability", self.upper_probability),
        )
        if self.upper_probability <= self.lower_probability:
            raise ValueError("upper_probability must be greater than lower_probability")
        if self.bucket_label != _bucket_label(
            self.lower_probability,
            self.upper_probability,
        ):
            raise ValueError("bucket_label must match bucket bounds")
        _require_nonnegative_int("forecast_count", self.forecast_count)
        _require_nonnegative_int("settled_count", self.settled_count)
        if self.settled_count > self.forecast_count:
            raise ValueError("settled_count must not exceed forecast_count")
        for field_name in (
            "observed_yes_rate",
            "average_forecast_probability",
            "average_confidence",
            "average_brier_score",
            "calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_nonnegative_int(
            "directionally_correct_count",
            self.directionally_correct_count,
        )
        if self.directionally_correct_count > self.settled_count:
            raise ValueError(
                "directionally_correct_count must not exceed settled_count",
            )
        if self.settled_count == 0:
            for field_name in (
                "observed_yes_rate",
                "average_forecast_probability",
                "average_confidence",
                "average_brier_score",
                "calibration_error",
            ):
                if getattr(self, field_name) != ZERO:
                    raise ValueError(f"{field_name} must be zero without settlements")
        else:
            expected_error = _absolute_decimal(
                self.average_forecast_probability - self.observed_yes_rate,
            )
            if self.calibration_error != expected_error:
                raise ValueError("calibration_error must match bucket means")
        _require_safety_flags("TeamForecastCalibrationBucket", self)


@dataclass(frozen=True)
class TeamForecastCalibrationGroup:
    group_type: str
    group_key: str
    team_id: str
    category_id: str | None
    event_template: str | None
    forecast_count: int
    settled_count: int
    observed_yes_rate: Decimal
    average_forecast_probability: Decimal
    average_confidence: Decimal
    average_brier_score: Decimal
    calibration_error: Decimal
    directionally_correct_count: int
    status: str
    reason_codes: tuple[str, ...]
    buckets: tuple[TeamForecastCalibrationBucket, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.group_type not in GROUP_TYPES:
            raise ValueError("group_type must be a known calibration group type")
        _require_canonical_string("group_key", self.group_key)
        _require_canonical_string("team_id", self.team_id)
        if self.category_id is not None:
            _require_canonical_string("category_id", self.category_id)
        if self.event_template is not None:
            _require_canonical_string("event_template", self.event_template)
        if self.group_type == "team":
            if self.category_id is not None or self.event_template is not None:
                raise ValueError("team groups must not include finer keys")
        if self.group_type == "category":
            if self.category_id is None or self.event_template is not None:
                raise ValueError("category groups must include only category_id")
        if self.group_type == "event_template":
            if self.category_id is None or self.event_template is None:
                raise ValueError("event_template groups must include fine keys")
        _require_nonnegative_int("forecast_count", self.forecast_count)
        _require_nonnegative_int("settled_count", self.settled_count)
        if self.settled_count > self.forecast_count:
            raise ValueError("settled_count must not exceed forecast_count")
        for field_name in (
            "observed_yes_rate",
            "average_forecast_probability",
            "average_confidence",
            "average_brier_score",
            "calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_nonnegative_int(
            "directionally_correct_count",
            self.directionally_correct_count,
        )
        if self.directionally_correct_count > self.settled_count:
            raise ValueError(
                "directionally_correct_count must not exceed settled_count",
            )
        if self.status not in STATUSES:
            raise ValueError("status must be candidate or validated")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "buckets", _normalize_buckets(self.buckets))
        if self.forecast_count != sum(bucket.forecast_count for bucket in self.buckets):
            raise ValueError("forecast_count must match buckets")
        if self.settled_count != sum(bucket.settled_count for bucket in self.buckets):
            raise ValueError("settled_count must match buckets")
        if self.directionally_correct_count != sum(
            bucket.directionally_correct_count for bucket in self.buckets
        ):
            raise ValueError("directionally_correct_count must match buckets")
        if self.settled_count == 0:
            for field_name in (
                "observed_yes_rate",
                "average_forecast_probability",
                "average_confidence",
                "average_brier_score",
                "calibration_error",
            ):
                if getattr(self, field_name) != ZERO:
                    raise ValueError(f"{field_name} must be zero without settlements")
        else:
            expected_error = _absolute_decimal(
                self.average_forecast_probability - self.observed_yes_rate,
            )
            if self.calibration_error != expected_error:
                raise ValueError("calibration_error must match group means")
        _require_safety_flags("TeamForecastCalibrationGroup", self)


@dataclass(frozen=True)
class TeamForecastCalibrationReport:
    generated_at: datetime
    config_version: str
    forecast_count: int
    settled_count: int
    duplicate_forecast_count: int
    duplicate_outcome_count: int
    orphan_outcome_count: int
    status: str
    reason_codes: tuple[str, ...]
    groups: tuple[TeamForecastCalibrationGroup, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_count",
            "settled_count",
            "duplicate_forecast_count",
            "duplicate_outcome_count",
            "orphan_outcome_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.settled_count > self.forecast_count:
            raise ValueError("settled_count must not exceed forecast_count")
        if self.status not in STATUSES:
            raise ValueError("status must be candidate or validated")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "groups", _normalize_groups(self.groups))
        _require_safety_flags("TeamForecastCalibrationReport", self)


def build_team_forecast_calibration_report(
    forecast_rows: object,
    outcome_rows: object,
    *,
    config: TeamForecastCalibrationConfig,
    generated_at: datetime,
) -> TeamForecastCalibrationReport:
    if type(config) is not TeamForecastCalibrationConfig:
        raise ValueError("config must be a TeamForecastCalibrationConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    forecasts = _forecast_items(forecast_rows)
    outcomes = _outcome_items(outcome_rows)
    latest_forecasts, duplicate_forecast_count = _latest_forecasts(forecasts)
    latest_outcomes, duplicate_outcome_count = _latest_outcomes(outcomes)
    orphan_outcome_count = sum(
        1 for forecast_id in latest_outcomes if forecast_id not in latest_forecasts
    )
    matched_outcomes = {
        forecast_id: outcome
        for forecast_id, outcome in latest_outcomes.items()
        if forecast_id in latest_forecasts
    }
    for forecast_id, outcome in matched_outcomes.items():
        _require_pair(latest_forecasts[forecast_id], outcome)

    settled_count = len(matched_outcomes)
    status = _status(settled_count, config.min_settled_forecasts)
    reason_codes = _report_reason_codes(
        forecast_count=len(latest_forecasts),
        settled_count=settled_count,
        duplicate_forecast_count=duplicate_forecast_count,
        duplicate_outcome_count=duplicate_outcome_count,
        orphan_outcome_count=orphan_outcome_count,
        config=config,
    )
    groups = _build_groups(
        tuple(latest_forecasts.values()),
        matched_outcomes,
        config=config,
    )

    return TeamForecastCalibrationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast_count=len(latest_forecasts),
        settled_count=settled_count,
        duplicate_forecast_count=duplicate_forecast_count,
        duplicate_outcome_count=duplicate_outcome_count,
        orphan_outcome_count=orphan_outcome_count,
        status=status,
        reason_codes=reason_codes,
        groups=groups,
    )


@dataclass(frozen=True)
class _ForecastItem:
    forecast_id: str
    generated_at: datetime
    payload_sha256: str
    team_id: str
    market_slug: str
    category_id: str
    event_template: str
    forecast_probability: Decimal
    confidence: Decimal


@dataclass(frozen=True)
class _OutcomeItem:
    outcome_id: str
    forecast_id: str
    generated_at: datetime
    team_id: str
    market_slug: str
    resolved_at: datetime
    actual_outcome: str
    directionally_correct: bool


def _forecast_items(value: object) -> tuple[_ForecastItem, ...]:
    rows = _rows_tuple("forecast_rows", value)
    items: list[_ForecastItem] = []
    for row in rows:
        if type(row) is not TeamForecastDbRow:
            raise ValueError("forecast_rows must contain TeamForecastDbRow values")
        _require_safety_flags("TeamForecastDbRow", row)
        clean = TeamForecastDbRow(
            **{field.name: getattr(row, field.name) for field in fields(TeamForecastDbRow)}
        )
        packet = team_forecast_from_db_row(clean)
        items.append(
            _ForecastItem(
                forecast_id=clean.forecast_id,
                generated_at=clean.generated_at,
                payload_sha256=clean.payload_sha256,
                team_id=clean.team_id,
                market_slug=clean.market_slug,
                category_id=packet.category_id,
                event_template=packet.event_template,
                forecast_probability=clean.forecast_probability,
                confidence=clean.confidence,
            ),
        )
    return tuple(items)


def _outcome_items(value: object) -> tuple[_OutcomeItem, ...]:
    rows = _rows_tuple("outcome_rows", value)
    items: list[_OutcomeItem] = []
    for row in rows:
        if type(row) is not TeamForecastOutcomeDbRow:
            raise ValueError("outcome_rows must contain TeamForecastOutcomeDbRow values")
        _require_safety_flags("TeamForecastOutcomeDbRow", row)
        clean = TeamForecastOutcomeDbRow(
            **{
                field.name: getattr(row, field.name)
                for field in fields(TeamForecastOutcomeDbRow)
            }
        )
        outcome = team_forecast_outcome_from_db_row(clean)
        items.append(
            _OutcomeItem(
                outcome_id=clean.outcome_id,
                forecast_id=clean.forecast_id,
                generated_at=clean.generated_at,
                team_id=clean.team_id,
                market_slug=clean.market_slug,
                resolved_at=clean.resolved_at,
                actual_outcome=outcome.actual_outcome,
                directionally_correct=outcome.directionally_correct,
            ),
        )
    return tuple(items)


def _rows_tuple(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    return tuple(value)


def _latest_forecasts(
    items: tuple[_ForecastItem, ...],
) -> tuple[dict[str, _ForecastItem], int]:
    latest: dict[str, _ForecastItem] = {}
    duplicate_count = 0
    for item in items:
        current = latest.get(item.forecast_id)
        if current is None:
            latest[item.forecast_id] = item
        else:
            duplicate_count += 1
            if _forecast_rank(item) > _forecast_rank(current):
                latest[item.forecast_id] = item
    return latest, duplicate_count


def _latest_outcomes(
    items: tuple[_OutcomeItem, ...],
) -> tuple[dict[str, _OutcomeItem], int]:
    latest: dict[str, _OutcomeItem] = {}
    duplicate_count = 0
    for item in items:
        current = latest.get(item.forecast_id)
        if current is None:
            latest[item.forecast_id] = item
        else:
            duplicate_count += 1
            if _outcome_rank(item) > _outcome_rank(current):
                latest[item.forecast_id] = item
    return latest, duplicate_count


def _forecast_rank(item: _ForecastItem) -> tuple[datetime, str]:
    return item.generated_at, item.payload_sha256


def _outcome_rank(item: _OutcomeItem) -> tuple[datetime, datetime, str]:
    return item.resolved_at, item.generated_at, item.outcome_id


def _require_pair(forecast: _ForecastItem, outcome: _OutcomeItem) -> None:
    if outcome.team_id != forecast.team_id:
        raise ValueError("outcome team_id must match forecast team_id")
    if outcome.market_slug != forecast.market_slug:
        raise ValueError("outcome market_slug must match forecast market_slug")


def _build_groups(
    forecasts: tuple[_ForecastItem, ...],
    outcomes: dict[str, _OutcomeItem],
    *,
    config: TeamForecastCalibrationConfig,
) -> tuple[TeamForecastCalibrationGroup, ...]:
    team_map: dict[tuple[str], list[_ForecastItem]] = {}
    category_map: dict[tuple[str, str], list[_ForecastItem]] = {}
    event_map: dict[tuple[str, str, str], list[_ForecastItem]] = {}
    for forecast in forecasts:
        team_map.setdefault((forecast.team_id,), []).append(forecast)
        category_map.setdefault((forecast.team_id, forecast.category_id), []).append(forecast)
        event_map.setdefault(
            (forecast.team_id, forecast.category_id, forecast.event_template),
            [],
        ).append(forecast)

    groups: list[TeamForecastCalibrationGroup] = []
    for (team_id,), items in sorted(team_map.items()):
        groups.append(
            _build_group(
                group_type="team",
                group_key=team_id,
                team_id=team_id,
                category_id=None,
                event_template=None,
                forecasts=tuple(items),
                outcomes=outcomes,
                config=config,
            ),
        )
    for (team_id, category_id), items in sorted(category_map.items()):
        if _settled_count(tuple(items), outcomes) < config.min_group_settled_forecasts:
            continue
        groups.append(
            _build_group(
                group_type="category",
                group_key=f"{team_id}:{category_id}",
                team_id=team_id,
                category_id=category_id,
                event_template=None,
                forecasts=tuple(items),
                outcomes=outcomes,
                config=config,
            ),
        )
    for (team_id, category_id, event_template), items in sorted(event_map.items()):
        if _settled_count(tuple(items), outcomes) < config.min_group_settled_forecasts:
            continue
        groups.append(
            _build_group(
                group_type="event_template",
                group_key=f"{team_id}:{category_id}:{event_template}",
                team_id=team_id,
                category_id=category_id,
                event_template=event_template,
                forecasts=tuple(items),
                outcomes=outcomes,
                config=config,
            ),
        )
    return tuple(groups)


def _build_group(
    *,
    group_type: str,
    group_key: str,
    team_id: str,
    category_id: str | None,
    event_template: str | None,
    forecasts: tuple[_ForecastItem, ...],
    outcomes: dict[str, _OutcomeItem],
    config: TeamForecastCalibrationConfig,
) -> TeamForecastCalibrationGroup:
    buckets = _build_buckets(forecasts, outcomes, config.bucket_count)
    settled = tuple(
        (forecast, outcomes[forecast.forecast_id])
        for forecast in forecasts
        if forecast.forecast_id in outcomes
    )
    settled_count = len(settled)
    return TeamForecastCalibrationGroup(
        group_type=group_type,
        group_key=group_key,
        team_id=team_id,
        category_id=category_id,
        event_template=event_template,
        forecast_count=len(forecasts),
        settled_count=settled_count,
        observed_yes_rate=_observed_yes_rate(settled),
        average_forecast_probability=_average_probability(settled),
        average_confidence=_average_confidence(settled),
        average_brier_score=_average_brier_score(settled),
        calibration_error=_calibration_error(settled),
        directionally_correct_count=_directionally_correct_count(settled),
        status=_status(settled_count, config.min_settled_forecasts),
        reason_codes=_sample_reason_codes(settled_count, config.min_settled_forecasts),
        buckets=buckets,
    )


def _build_buckets(
    forecasts: tuple[_ForecastItem, ...],
    outcomes: dict[str, _OutcomeItem],
    bucket_count: int,
) -> tuple[TeamForecastCalibrationBucket, ...]:
    grouped: dict[int, list[_ForecastItem]] = {}
    for forecast in forecasts:
        grouped.setdefault(
            _bucket_index(forecast.forecast_probability, bucket_count),
            [],
        ).append(forecast)

    buckets: list[TeamForecastCalibrationBucket] = []
    for index, items in sorted(grouped.items()):
        lower, upper = _bucket_bounds(index, bucket_count)
        settled = tuple(
            (forecast, outcomes[forecast.forecast_id])
            for forecast in items
            if forecast.forecast_id in outcomes
        )
        buckets.append(
            TeamForecastCalibrationBucket(
                bucket_label=_bucket_label(lower, upper),
                lower_probability=lower,
                upper_probability=upper,
                forecast_count=len(items),
                settled_count=len(settled),
                observed_yes_rate=_observed_yes_rate(settled),
                average_forecast_probability=_average_probability(settled),
                average_confidence=_average_confidence(settled),
                average_brier_score=_average_brier_score(settled),
                calibration_error=_calibration_error(settled),
                directionally_correct_count=_directionally_correct_count(settled),
            ),
        )
    return tuple(buckets)


def _settled_count(
    forecasts: tuple[_ForecastItem, ...],
    outcomes: dict[str, _OutcomeItem],
) -> int:
    return sum(1 for forecast in forecasts if forecast.forecast_id in outcomes)


def _status(settled_count: int, minimum: int) -> str:
    if settled_count >= minimum:
        return "validated"
    return "candidate"


def _report_reason_codes(
    *,
    forecast_count: int,
    settled_count: int,
    duplicate_forecast_count: int,
    duplicate_outcome_count: int,
    orphan_outcome_count: int,
    config: TeamForecastCalibrationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if duplicate_forecast_count > 0:
        reason_codes.append("duplicate_forecasts_deduplicated")
    if duplicate_outcome_count > 0:
        reason_codes.append("duplicate_outcomes_deduplicated")
    reason_codes.extend(
        _sample_reason_codes(settled_count, config.min_settled_forecasts),
    )
    if forecast_count == 0:
        reason_codes.append("no_forecasts")
    if settled_count == 0:
        reason_codes.append("no_settled_forecasts")
    if orphan_outcome_count > 0:
        reason_codes.append("orphan_outcomes_ignored")
    return _normalize_reason_codes(tuple(reason_codes))


def _sample_reason_codes(settled_count: int, minimum: int) -> tuple[str, ...]:
    if settled_count >= minimum:
        return ("min_settled_forecasts_met",)
    return ("insufficient_settled_forecasts",)


def _observed_yes_rate(settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...]) -> Decimal:
    return _mean(tuple(_actual_yes(outcome) for _, outcome in settled))


def _average_probability(settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...]) -> Decimal:
    return _mean(tuple(forecast.forecast_probability for forecast, _ in settled))


def _average_confidence(settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...]) -> Decimal:
    return _mean(tuple(forecast.confidence for forecast, _ in settled))


def _average_brier_score(settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...]) -> Decimal:
    return _mean(tuple(_brier_score(forecast, outcome) for forecast, outcome in settled))


def _calibration_error(settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...]) -> Decimal:
    if not settled:
        return ZERO
    return _absolute_decimal(_average_probability(settled) - _observed_yes_rate(settled))


def _directionally_correct_count(
    settled: tuple[tuple[_ForecastItem, _OutcomeItem], ...],
) -> int:
    return sum(1 for _, outcome in settled if outcome.directionally_correct is True)


def _actual_yes(outcome: _OutcomeItem) -> Decimal:
    if outcome.actual_outcome == YES:
        return ONE
    return ZERO


def _brier_score(forecast: _ForecastItem, outcome: _OutcomeItem) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_brier_score",
            (forecast.forecast_probability - _actual_yes(outcome)) ** 2,
        )


def _bucket_index(probability: Decimal, bucket_count: int) -> int:
    if probability == ONE:
        return bucket_count - 1
    with localcontext(DECIMAL_CONTEXT):
        index = (probability * Decimal(bucket_count)).to_integral_value(
            rounding=ROUND_FLOOR,
        )
    return int(index)


def _bucket_bounds(index: int, bucket_count: int) -> tuple[Decimal, Decimal]:
    with localcontext(DECIMAL_CONTEXT):
        lower = _normalize_probability(
            "lower_probability",
            Decimal(index) / Decimal(bucket_count),
        )
        upper = (
            ONE
            if index == bucket_count - 1
            else _normalize_probability(
                "upper_probability",
                Decimal(index + 1) / Decimal(bucket_count),
            )
        )
    return lower, upper


def _bucket_label(lower_probability: Decimal, upper_probability: Decimal) -> str:
    return f"{lower_probability:.6f}-{upper_probability:.6f}"


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("mean", sum(values, ZERO) / Decimal(len(values)))


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("absolute", abs(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_buckets(
    value: object,
) -> tuple[TeamForecastCalibrationBucket, ...]:
    items = _tuple_from_iterable("buckets", value)
    previous_upper: Decimal | None = None
    normalized: list[TeamForecastCalibrationBucket] = []
    for item in items:
        if type(item) is not TeamForecastCalibrationBucket:
            raise ValueError("buckets must contain TeamForecastCalibrationBucket values")
        _require_safety_flags("TeamForecastCalibrationBucket", item)
        if previous_upper is not None and item.lower_probability < previous_upper:
            raise ValueError("buckets must not overlap")
        previous_upper = item.upper_probability
        normalized.append(item)
    return tuple(normalized)


def _normalize_groups(value: object) -> tuple[TeamForecastCalibrationGroup, ...]:
    items = _tuple_from_iterable("groups", value)
    normalized: list[TeamForecastCalibrationGroup] = []
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not TeamForecastCalibrationGroup:
            raise ValueError("groups must contain TeamForecastCalibrationGroup values")
        _require_safety_flags("TeamForecastCalibrationGroup", item)
        key = (item.group_type, item.group_key)
        if key in seen_keys:
            raise ValueError("groups must not contain duplicate keys")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(normalized)


def _tuple_from_iterable(field_name: str, value: object) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    items = _tuple_from_iterable("reason_codes", value)
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(sorted(set(items)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "TeamForecastCalibrationBucket",
    "TeamForecastCalibrationConfig",
    "TeamForecastCalibrationGroup",
    "TeamForecastCalibrationReport",
    "build_team_forecast_calibration_report",
)
