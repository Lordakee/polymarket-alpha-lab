"""Paper-only performance summaries for specialist team forecasts.

This module is pure arithmetic over caller-supplied forecast and outcome
objects. It performs no database, network, wallet, account, order, or
Polymarket microstructure access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_category_id, require_team_id


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = frozenset(("yes", "no"))

INSUFFICIENT_TRUST_SAMPLE = "insufficient_trust_sample"
TRUST_SAMPLE_READY = "trust_sample_ready"
INSUFFICIENT_ALLOCATION_SAMPLE = "insufficient_allocation_sample"
ALLOCATION_SAMPLE_READY = "allocation_sample_ready"
NO_SETTLED_FORECASTS = "no_settled_forecasts"


@dataclass(frozen=True)
class TeamPerformanceSummaryConfig:
    config_version: str = "team-performance-summary-v0"
    min_trust_sample_count: int = 30
    min_allocation_sample_count: int = 50
    team_trust_floor: Decimal = Decimal("0.800000")
    team_trust_ceiling: Decimal = Decimal("1.200000")
    allocation_trust_floor: Decimal = Decimal("0.900000")
    allocation_trust_ceiling: Decimal = Decimal("1.100000")
    neutral_trust_score: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_trust_sample_count", self.min_trust_sample_count)
        _require_positive_int(
            "min_allocation_sample_count",
            self.min_allocation_sample_count,
        )
        for field_name in (
            "team_trust_floor",
            "team_trust_ceiling",
            "allocation_trust_floor",
            "allocation_trust_ceiling",
            "neutral_trust_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if not self.team_trust_floor <= self.neutral_trust_score <= self.team_trust_ceiling:
            raise ValueError("team trust bounds must contain neutral_trust_score")
        if not (
            self.allocation_trust_floor
            <= self.neutral_trust_score
            <= self.allocation_trust_ceiling
        ):
            raise ValueError("allocation trust bounds must contain neutral_trust_score")
        _require_safety_flags("TeamPerformanceSummaryConfig", self)


@dataclass(frozen=True)
class TeamPerformanceSummaryRow:
    team_id: str
    category_id: str
    forecast_count: int
    settled_count: int
    directionally_correct_count: int
    profitable_after_cost_count: int
    average_brier_score: Decimal
    hit_rate: Decimal
    paper_pnl: Decimal
    cost_adjusted_return: Decimal
    team_trust_score: Decimal
    allocation_trust_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        for field_name in (
            "forecast_count",
            "settled_count",
            "directionally_correct_count",
            "profitable_after_cost_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.settled_count > self.forecast_count:
            raise ValueError("settled_count must not exceed forecast_count")
        if self.directionally_correct_count > self.settled_count:
            raise ValueError(
                "directionally_correct_count must not exceed settled_count",
            )
        if self.profitable_after_cost_count > self.settled_count:
            raise ValueError(
                "profitable_after_cost_count must not exceed settled_count",
            )
        for field_name in ("average_brier_score", "hit_rate"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "paper_pnl",
            "cost_adjusted_return",
            "team_trust_score",
            "allocation_trust_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.team_trust_score < ZERO:
            raise ValueError("team_trust_score must be nonnegative")
        if self.allocation_trust_score < ZERO:
            raise ValueError("allocation_trust_score must be nonnegative")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags("TeamPerformanceSummaryRow", self)


@dataclass(frozen=True)
class TeamPerformanceSummaryReport:
    generated_at: datetime
    config_version: str
    forecast_count: int
    settled_count: int
    rows: tuple[TeamPerformanceSummaryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("forecast_count", self.forecast_count)
        _require_nonnegative_int("settled_count", self.settled_count)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.forecast_count != sum(row.forecast_count for row in self.rows):
            raise ValueError("forecast_count must match rows")
        if self.settled_count != sum(row.settled_count for row in self.rows):
            raise ValueError("settled_count must match rows")
        _require_safety_flags("TeamPerformanceSummaryReport", self)


def build_team_performance_summary_report(
    forecasts: object,
    outcomes: object,
    *,
    config: TeamPerformanceSummaryConfig,
    generated_at: datetime,
) -> TeamPerformanceSummaryReport:
    """Build a neutral paper-only summary over supplied team forecasts."""

    if type(config) is not TeamPerformanceSummaryConfig:
        raise ValueError("config must be a TeamPerformanceSummaryConfig")

    forecast_items = _normalize_forecasts(forecasts)
    outcome_items = _normalize_outcomes(outcomes)
    latest_outcomes = _latest_outcomes_by_forecast_id(outcome_items)

    grouped_forecasts: dict[tuple[str, str], list[_ForecastInput]] = {}
    for forecast in forecast_items:
        grouped_forecasts.setdefault((forecast.team_id, forecast.category_id), []).append(
            forecast,
        )

    rows = tuple(
        _build_row(
            team_id=team_id,
            category_id=category_id,
            forecasts=tuple(grouped_forecasts[(team_id, category_id)]),
            latest_outcomes=latest_outcomes,
            config=config,
        )
        for team_id, category_id in sorted(grouped_forecasts)
    )

    return TeamPerformanceSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast_count=len(forecast_items),
        settled_count=sum(row.settled_count for row in rows),
        rows=rows,
    )


@dataclass(frozen=True)
class _ForecastInput:
    forecast_id: str
    team_id: str
    market_slug: str
    category_id: str
    selected_side: str
    forecast_probability: Decimal


@dataclass(frozen=True)
class _OutcomeInput:
    outcome_id: str
    forecast_id: str
    team_id: str
    market_slug: str
    actual_outcome: str
    resolved_at: datetime
    paper_pnl: Decimal
    cost_adjusted_return: Decimal
    directionally_correct: bool | None
    profitable_after_cost: bool | None


def _normalize_forecasts(forecasts: object) -> tuple[_ForecastInput, ...]:
    items = _tuple_from_iterable("forecasts", forecasts)
    normalized: list[_ForecastInput] = []
    for item in items:
        _require_safety_flags("forecast", item)
        forecast_id = _required_canonical_attr(item, "forecast_id")
        team_id = require_team_id("team_id", _required_attr(item, "team_id"))
        market_slug = _required_canonical_attr(item, "market_slug")
        category_id = require_category_id("category_id", _required_attr(item, "category_id"))
        selected_side = _required_attr(item, "selected_side")
        if selected_side not in SIDES:
            raise ValueError("selected_side must be yes or no")
        normalized.append(
            _ForecastInput(
                forecast_id=forecast_id,
                team_id=team_id,
                market_slug=market_slug,
                category_id=category_id,
                selected_side=selected_side,
                forecast_probability=_normalize_probability_decimal(
                    "forecast_probability",
                    _required_attr(item, "forecast_probability"),
                ),
            ),
        )
    return tuple(normalized)


def _normalize_outcomes(outcomes: object) -> tuple[_OutcomeInput, ...]:
    items = _tuple_from_iterable("outcomes", outcomes)
    normalized: list[_OutcomeInput] = []
    for item in items:
        _require_safety_flags("outcome", item)
        actual_outcome = _required_attr(item, "actual_outcome")
        if actual_outcome not in SIDES:
            raise ValueError("actual_outcome must be yes or no")
        normalized.append(
            _OutcomeInput(
                outcome_id=_required_canonical_attr(item, "outcome_id"),
                forecast_id=_required_canonical_attr(item, "forecast_id"),
                team_id=require_team_id("team_id", _required_attr(item, "team_id")),
                market_slug=_required_canonical_attr(item, "market_slug"),
                actual_outcome=actual_outcome,
                resolved_at=_as_utc("resolved_at", _required_attr(item, "resolved_at")),
                paper_pnl=_normalize_decimal(
                    "paper_pnl",
                    _required_attr(item, "paper_pnl"),
                ),
                cost_adjusted_return=_normalize_decimal(
                    "cost_adjusted_return",
                    _required_attr(item, "cost_adjusted_return"),
                ),
                directionally_correct=_optional_bool_attr(
                    item,
                    "directionally_correct",
                ),
                profitable_after_cost=_optional_bool_attr(
                    item,
                    "profitable_after_cost",
                ),
            ),
        )
    return tuple(normalized)


def _latest_outcomes_by_forecast_id(
    outcomes: tuple[_OutcomeInput, ...],
) -> dict[str, _OutcomeInput]:
    latest: dict[str, _OutcomeInput] = {}
    for outcome in outcomes:
        current = latest.get(outcome.forecast_id)
        if current is None or outcome.resolved_at >= current.resolved_at:
            latest[outcome.forecast_id] = outcome
    return latest


def _build_row(
    *,
    team_id: str,
    category_id: str,
    forecasts: tuple[_ForecastInput, ...],
    latest_outcomes: dict[str, _OutcomeInput],
    config: TeamPerformanceSummaryConfig,
) -> TeamPerformanceSummaryRow:
    settled_pairs = tuple(
        (forecast, latest_outcomes[forecast.forecast_id])
        for forecast in forecasts
        if forecast.forecast_id in latest_outcomes
    )
    for forecast, outcome in settled_pairs:
        _require_outcome_matches_forecast(forecast, outcome)

    settled_count = len(settled_pairs)
    directionally_correct_count = sum(
        1
        for forecast, outcome in settled_pairs
        if _directionally_correct(forecast, outcome)
    )
    profitable_after_cost_count = sum(
        1 for _, outcome in settled_pairs if _profitable_after_cost(outcome)
    )
    brier_scores = tuple(_brier_score(forecast, outcome) for forecast, outcome in settled_pairs)

    return TeamPerformanceSummaryRow(
        team_id=team_id,
        category_id=category_id,
        forecast_count=len(forecasts),
        settled_count=settled_count,
        directionally_correct_count=directionally_correct_count,
        profitable_after_cost_count=profitable_after_cost_count,
        average_brier_score=_mean_or_zero(brier_scores),
        hit_rate=_ratio_or_zero(directionally_correct_count, settled_count),
        paper_pnl=_sum_decimals(tuple(outcome.paper_pnl for _, outcome in settled_pairs)),
        cost_adjusted_return=_sum_decimals(
            tuple(outcome.cost_adjusted_return for _, outcome in settled_pairs),
        ),
        team_trust_score=_team_trust_score(
            settled_count=settled_count,
            hit_rate=_ratio_or_zero(directionally_correct_count, settled_count),
            config=config,
        ),
        allocation_trust_score=_allocation_trust_score(
            settled_count=settled_count,
            hit_rate=_ratio_or_zero(directionally_correct_count, settled_count),
            config=config,
        ),
        reason_codes=_reason_codes(settled_count, config),
    )


def _require_outcome_matches_forecast(
    forecast: _ForecastInput,
    outcome: _OutcomeInput,
) -> None:
    if outcome.team_id != forecast.team_id:
        raise ValueError("outcome team_id must match forecast team_id")
    if outcome.market_slug != forecast.market_slug:
        raise ValueError("outcome market_slug must match forecast market_slug")


def _brier_score(forecast: _ForecastInput, outcome: _OutcomeInput) -> Decimal:
    actual_value = _actual_value_for_forecast_side(forecast, outcome)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability_decimal(
            "brier_score",
            (forecast.forecast_probability - actual_value) ** 2,
        )


def _actual_value_for_forecast_side(
    forecast: _ForecastInput,
    outcome: _OutcomeInput,
) -> Decimal:
    if outcome.actual_outcome == forecast.selected_side:
        return ONE
    return ZERO


def _directionally_correct(forecast: _ForecastInput, outcome: _OutcomeInput) -> bool:
    if outcome.directionally_correct is not None:
        return outcome.directionally_correct
    actual_value = _actual_value_for_forecast_side(forecast, outcome)
    if forecast.forecast_probability >= Decimal("0.500000"):
        return actual_value == ONE
    return actual_value == ZERO


def _profitable_after_cost(outcome: _OutcomeInput) -> bool:
    if outcome.profitable_after_cost is not None:
        return outcome.profitable_after_cost
    return outcome.cost_adjusted_return > ZERO


def _team_trust_score(
    *,
    settled_count: int,
    hit_rate: Decimal,
    config: TeamPerformanceSummaryConfig,
) -> Decimal:
    if settled_count < config.min_trust_sample_count:
        return config.neutral_trust_score
    return _interpolate_multiplier(
        floor=config.team_trust_floor,
        ceiling=config.team_trust_ceiling,
        hit_rate=hit_rate,
    )


def _allocation_trust_score(
    *,
    settled_count: int,
    hit_rate: Decimal,
    config: TeamPerformanceSummaryConfig,
) -> Decimal:
    if settled_count < config.min_allocation_sample_count:
        return config.neutral_trust_score
    return _interpolate_multiplier(
        floor=config.allocation_trust_floor,
        ceiling=config.allocation_trust_ceiling,
        hit_rate=hit_rate,
    )


def _interpolate_multiplier(
    *,
    floor: Decimal,
    ceiling: Decimal,
    hit_rate: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("trust_score", floor + ((ceiling - floor) * hit_rate))


def _reason_codes(
    settled_count: int,
    config: TeamPerformanceSummaryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if settled_count == 0:
        reason_codes.append(NO_SETTLED_FORECASTS)
    if settled_count < config.min_trust_sample_count:
        reason_codes.append(INSUFFICIENT_TRUST_SAMPLE)
    else:
        reason_codes.append(TRUST_SAMPLE_READY)
    if settled_count < config.min_allocation_sample_count:
        reason_codes.append(INSUFFICIENT_ALLOCATION_SAMPLE)
    else:
        reason_codes.append(ALLOCATION_SAMPLE_READY)
    return tuple(reason_codes)


def _mean_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability_decimal(
            "mean",
            sum(values, ZERO) / Decimal(len(values)),
        )


def _ratio_or_zero(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability_decimal(
            "ratio",
            Decimal(numerator) / Decimal(denominator),
        )


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("sum", sum(values, ZERO))


def _normalize_rows(rows: object) -> tuple[TeamPerformanceSummaryRow, ...]:
    items = _tuple_from_iterable("rows", rows)
    normalized: list[TeamPerformanceSummaryRow] = []
    previous_key: tuple[str, str] | None = None
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not TeamPerformanceSummaryRow:
            raise ValueError("rows must contain TeamPerformanceSummaryRow values")
        _require_safety_flags("TeamPerformanceSummaryRow", item)
        row_key = (item.team_id, item.category_id)
        if row_key in seen_keys:
            raise ValueError("rows must not contain duplicate team/category pairs")
        if previous_key is not None and row_key < previous_key:
            raise ValueError("rows must be sorted by team_id and category_id")
        seen_keys.add(row_key)
        previous_key = row_key
        normalized.append(item)
    return tuple(normalized)


def _tuple_from_iterable(field_name: str, value: object) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _required_canonical_attr(value: object, field_name: str) -> str:
    item = _required_attr(value, field_name)
    _require_canonical_string(field_name, item)
    return item


def _optional_bool_attr(value: object, field_name: str) -> bool | None:
    item = getattr(value, field_name, None)
    if item is None:
        return None
    if type(item) is not bool:
        raise ValueError(f"{field_name} must be a bool or None")
    return item


def _as_utc(field_name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


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


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    items = _tuple_from_iterable("reason_codes", value)
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(sorted(set(items)))


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "TeamPerformanceSummaryConfig",
    "TeamPerformanceSummaryReport",
    "TeamPerformanceSummaryRow",
    "build_team_performance_summary_report",
)
