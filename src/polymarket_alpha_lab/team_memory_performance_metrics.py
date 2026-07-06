"""Pure team-memory performance metrics over paper predictions and outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = frozenset(("yes", "no"))
SAMPLE_SIZE_CONFIDENCE_VALUES = frozenset(("thin", "developing", "confident"))
REPORT_STATUSES = frozenset(("ready", "candidate"))
REASON_CODE_ORDER = (
    "empty_predictions",
    "no_resolved_outcomes",
    "thin_team_sample",
    "sample_size_confident",
    "sample_size_developing",
    "thin_sample_size",
    "unresolved_predictions",
)


@dataclass(frozen=True)
class TeamMemoryPerformanceMetricsConfig:
    config_version: str = "team-memory-performance-metrics-v0"
    edge_bucket_bounds: tuple[Decimal, ...] = (
        Decimal("0.050000"),
        Decimal("0.150000"),
        Decimal("0.300000"),
    )
    developing_sample_size: int = 10
    confident_sample_size: int = 30
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "edge_bucket_bounds",
            _normalize_edge_bucket_bounds(self.edge_bucket_bounds),
        )
        _require_positive_int("developing_sample_size", self.developing_sample_size)
        _require_positive_int("confident_sample_size", self.confident_sample_size)
        if self.confident_sample_size < self.developing_sample_size:
            raise ValueError("confident_sample_size must be at least developing_sample_size")
        _require_hard_flags("TeamMemoryPerformanceMetricsConfig", self)


@dataclass(frozen=True)
class TeamMemoryPaperPredictionRow:
    prediction_id: str
    team_id: str
    market_slug: str
    forecast_probability: Decimal
    implied_probability: Decimal
    generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("prediction_id", self.prediction_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "implied_probability",
            _normalize_probability("implied_probability", self.implied_probability),
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_hard_flags("TeamMemoryPaperPredictionRow", self)


@dataclass(frozen=True)
class TeamMemoryPaperOutcomeRow:
    outcome_id: str
    prediction_id: str
    team_id: str
    market_slug: str
    actual_outcome: str
    resolved_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("outcome_id", self.outcome_id)
        _require_canonical_string("prediction_id", self.prediction_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("market_slug", self.market_slug)
        if self.actual_outcome not in SIDES:
            raise ValueError("actual_outcome must be yes or no")
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        _require_hard_flags("TeamMemoryPaperOutcomeRow", self)


@dataclass(frozen=True)
class TeamMemoryEdgeBucketPerformanceRow:
    bucket_key: str
    team_id: str
    prediction_count: int
    resolved_count: int
    yes_count: int
    no_count: int
    observed_rate: Decimal
    average_forecast_probability: Decimal
    calibration_error: Decimal
    brier_score: Decimal
    hit_rate: Decimal
    average_absolute_edge: Decimal
    sample_size_confidence: str
    sample_size_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("bucket_key", self.bucket_key)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in ("prediction_count", "resolved_count", "yes_count", "no_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.resolved_count != self.yes_count + self.no_count:
            raise ValueError("resolved_count must match outcome counts")
        if self.prediction_count < self.resolved_count:
            raise ValueError("prediction_count must be at least resolved_count")
        for field_name in (
            "observed_rate",
            "average_forecast_probability",
            "calibration_error",
            "brier_score",
            "hit_rate",
            "average_absolute_edge",
            "sample_size_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_sample_size_confidence(
            "sample_size_confidence",
            self.sample_size_confidence,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("TeamMemoryEdgeBucketPerformanceRow", self)


@dataclass(frozen=True)
class TeamMemoryPerformanceTeamRow:
    team_id: str
    prediction_count: int
    resolved_count: int
    unresolved_count: int
    observed_rate: Decimal
    average_forecast_probability: Decimal
    calibration_error: Decimal
    brier_score: Decimal
    hit_rate: Decimal
    average_absolute_edge: Decimal
    sample_size_confidence: str
    sample_size_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    edge_bucket_rows: tuple[TeamMemoryEdgeBucketPerformanceRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in ("prediction_count", "resolved_count", "unresolved_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.prediction_count != self.resolved_count + self.unresolved_count:
            raise ValueError("prediction_count must match resolved and unresolved counts")
        for field_name in (
            "observed_rate",
            "average_forecast_probability",
            "calibration_error",
            "brier_score",
            "hit_rate",
            "average_absolute_edge",
            "sample_size_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_sample_size_confidence(
            "sample_size_confidence",
            self.sample_size_confidence,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "edge_bucket_rows",
            _normalize_edge_bucket_rows(self.edge_bucket_rows, self.team_id),
        )
        if self.resolved_count != sum(row.resolved_count for row in self.edge_bucket_rows):
            raise ValueError("resolved_count must match edge bucket rows")
        _require_hard_flags("TeamMemoryPerformanceTeamRow", self)


@dataclass(frozen=True)
class TeamMemoryPerformanceMetricsReport:
    generated_at: datetime
    config_version: str
    prediction_count: int
    resolved_count: int
    unresolved_count: int
    team_count: int
    status: str
    reason_codes: tuple[str, ...]
    team_rows: tuple[TeamMemoryPerformanceTeamRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("prediction_count", "resolved_count", "unresolved_count", "team_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.prediction_count != self.resolved_count + self.unresolved_count:
            raise ValueError("prediction_count must match resolved and unresolved counts")
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be ready or candidate")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        if self.team_count != len(self.team_rows):
            raise ValueError("team_count must match team rows")
        if self.prediction_count != sum(row.prediction_count for row in self.team_rows):
            raise ValueError("prediction_count must match team rows")
        if self.resolved_count != sum(row.resolved_count for row in self.team_rows):
            raise ValueError("resolved_count must match team rows")
        if self.unresolved_count != sum(row.unresolved_count for row in self.team_rows):
            raise ValueError("unresolved_count must match team rows")
        _require_hard_flags("TeamMemoryPerformanceMetricsReport", self)


def build_team_memory_performance_metrics_report(
    predictions: object,
    outcomes: object,
    *,
    config: TeamMemoryPerformanceMetricsConfig,
    generated_at: datetime,
) -> TeamMemoryPerformanceMetricsReport:
    if type(config) is not TeamMemoryPerformanceMetricsConfig:
        raise ValueError("config must be a TeamMemoryPerformanceMetricsConfig")
    _require_hard_flags("TeamMemoryPerformanceMetricsConfig", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    prediction_rows = _normalize_predictions(predictions)
    outcome_rows = _normalize_outcomes(outcomes)
    latest_outcomes = _latest_outcomes_by_prediction_id(outcome_rows)

    grouped_predictions: dict[str, list[TeamMemoryPaperPredictionRow]] = {}
    for prediction in prediction_rows:
        grouped_predictions.setdefault(prediction.team_id, []).append(prediction)

    team_rows = tuple(
        _build_team_row(
            team_id=team_id,
            predictions=tuple(grouped_predictions[team_id]),
            latest_outcomes=latest_outcomes,
            config=config,
        )
        for team_id in sorted(grouped_predictions)
    )
    reason_codes = _report_reason_codes(team_rows, prediction_count=len(prediction_rows))

    return TeamMemoryPerformanceMetricsReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        prediction_count=sum(row.prediction_count for row in team_rows),
        resolved_count=sum(row.resolved_count for row in team_rows),
        unresolved_count=sum(row.unresolved_count for row in team_rows),
        team_count=len(team_rows),
        status="ready" if team_rows and not reason_codes else "candidate",
        reason_codes=reason_codes,
        team_rows=team_rows,
    )


def team_memory_performance_metrics_payload(
    report: TeamMemoryPerformanceMetricsReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryPerformanceMetricsReport:
        raise ValueError("report must be a TeamMemoryPerformanceMetricsReport")
    _require_hard_flags("TeamMemoryPerformanceMetricsReport", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_team_row(
    *,
    team_id: str,
    predictions: tuple[TeamMemoryPaperPredictionRow, ...],
    latest_outcomes: dict[str, TeamMemoryPaperOutcomeRow],
    config: TeamMemoryPerformanceMetricsConfig,
) -> TeamMemoryPerformanceTeamRow:
    resolved_pairs = tuple(
        (prediction, latest_outcomes[prediction.prediction_id])
        for prediction in predictions
        if prediction.prediction_id in latest_outcomes
    )
    for prediction, outcome in resolved_pairs:
        _require_outcome_matches_prediction(prediction, outcome)

    yes_count = sum(1 for _, outcome in resolved_pairs if outcome.actual_outcome == "yes")
    no_count = len(resolved_pairs) - yes_count
    observed_rate = _ratio_or_zero(yes_count, len(resolved_pairs))
    average_forecast_probability = _mean_or_zero(
        tuple(prediction.forecast_probability for prediction, _ in resolved_pairs),
    )
    sample_size_confidence = _sample_size_confidence(
        len(resolved_pairs),
        config=config,
    )
    edge_bucket_rows = _build_edge_bucket_rows(
        team_id=team_id,
        resolved_pairs=resolved_pairs,
        config=config,
    )

    return TeamMemoryPerformanceTeamRow(
        team_id=team_id,
        prediction_count=len(predictions),
        resolved_count=len(resolved_pairs),
        unresolved_count=len(predictions) - len(resolved_pairs),
        observed_rate=observed_rate,
        average_forecast_probability=average_forecast_probability,
        calibration_error=_absolute_difference(
            average_forecast_probability,
            observed_rate,
        ),
        brier_score=_mean_or_zero(
            tuple(_brier_score(prediction, outcome) for prediction, outcome in resolved_pairs),
        ),
        hit_rate=_ratio_or_zero(
            sum(1 for prediction, outcome in resolved_pairs if _is_hit(prediction, outcome)),
            len(resolved_pairs),
        ),
        average_absolute_edge=_mean_or_zero(
            tuple(_absolute_edge(prediction) for prediction, _ in resolved_pairs),
        ),
        sample_size_confidence=sample_size_confidence,
        sample_size_confidence_score=_sample_size_confidence_score(
            len(resolved_pairs),
            config=config,
        ),
        reason_codes=_row_reason_codes(
            resolved_count=len(resolved_pairs),
            unresolved_count=len(predictions) - len(resolved_pairs),
            sample_size_confidence=sample_size_confidence,
        ),
        edge_bucket_rows=edge_bucket_rows,
    )


def _build_edge_bucket_rows(
    *,
    team_id: str,
    resolved_pairs: tuple[
        tuple[TeamMemoryPaperPredictionRow, TeamMemoryPaperOutcomeRow],
        ...,
    ],
    config: TeamMemoryPerformanceMetricsConfig,
) -> tuple[TeamMemoryEdgeBucketPerformanceRow, ...]:
    grouped: dict[int, list[tuple[TeamMemoryPaperPredictionRow, TeamMemoryPaperOutcomeRow]]] = {}
    for prediction, outcome in resolved_pairs:
        grouped.setdefault(
            _edge_bucket_index(_absolute_edge(prediction), config.edge_bucket_bounds),
            [],
        ).append((prediction, outcome))

    bucket_rows: list[TeamMemoryEdgeBucketPerformanceRow] = []
    for index, items in sorted(grouped.items()):
        pairs = tuple(items)
        yes_count = sum(1 for _, outcome in pairs if outcome.actual_outcome == "yes")
        no_count = len(pairs) - yes_count
        observed_rate = _ratio_or_zero(yes_count, len(pairs))
        average_forecast_probability = _mean_or_zero(
            tuple(prediction.forecast_probability for prediction, _ in pairs),
        )
        sample_size_confidence = _sample_size_confidence(len(pairs), config=config)
        bucket_rows.append(
            TeamMemoryEdgeBucketPerformanceRow(
                bucket_key=_edge_bucket_key(index, config.edge_bucket_bounds),
                team_id=team_id,
                prediction_count=len(pairs),
                resolved_count=len(pairs),
                yes_count=yes_count,
                no_count=no_count,
                observed_rate=observed_rate,
                average_forecast_probability=average_forecast_probability,
                calibration_error=_absolute_difference(
                    average_forecast_probability,
                    observed_rate,
                ),
                brier_score=_mean_or_zero(
                    tuple(_brier_score(prediction, outcome) for prediction, outcome in pairs),
                ),
                hit_rate=_ratio_or_zero(
                    sum(1 for prediction, outcome in pairs if _is_hit(prediction, outcome)),
                    len(pairs),
                ),
                average_absolute_edge=_mean_or_zero(
                    tuple(_absolute_edge(prediction) for prediction, _ in pairs),
                ),
                sample_size_confidence=sample_size_confidence,
                sample_size_confidence_score=_sample_size_confidence_score(
                    len(pairs),
                    config=config,
                ),
                reason_codes=_sample_size_reason_codes(sample_size_confidence),
            ),
        )
    return tuple(bucket_rows)


def _normalize_predictions(predictions: object) -> tuple[TeamMemoryPaperPredictionRow, ...]:
    items = _tuple_from_iterable("predictions", predictions)
    seen_prediction_ids: set[str] = set()
    for item in items:
        if type(item) is not TeamMemoryPaperPredictionRow:
            raise ValueError("predictions must contain TeamMemoryPaperPredictionRow values")
        _require_hard_flags("TeamMemoryPaperPredictionRow", item)
        if item.prediction_id in seen_prediction_ids:
            raise ValueError("predictions must not contain duplicate prediction_id values")
        seen_prediction_ids.add(item.prediction_id)
    return items


def _normalize_outcomes(outcomes: object) -> tuple[TeamMemoryPaperOutcomeRow, ...]:
    items = _tuple_from_iterable("outcomes", outcomes)
    for item in items:
        if type(item) is not TeamMemoryPaperOutcomeRow:
            raise ValueError("outcomes must contain TeamMemoryPaperOutcomeRow values")
        _require_hard_flags("TeamMemoryPaperOutcomeRow", item)
    return items


def _latest_outcomes_by_prediction_id(
    outcomes: tuple[TeamMemoryPaperOutcomeRow, ...],
) -> dict[str, TeamMemoryPaperOutcomeRow]:
    latest: dict[str, TeamMemoryPaperOutcomeRow] = {}
    for outcome in outcomes:
        current = latest.get(outcome.prediction_id)
        if current is None or outcome.resolved_at >= current.resolved_at:
            latest[outcome.prediction_id] = outcome
    return latest


def _require_outcome_matches_prediction(
    prediction: TeamMemoryPaperPredictionRow,
    outcome: TeamMemoryPaperOutcomeRow,
) -> None:
    if outcome.team_id != prediction.team_id:
        raise ValueError("outcome team_id must match prediction team_id")
    if outcome.market_slug != prediction.market_slug:
        raise ValueError("outcome market_slug must match prediction market_slug")


def _brier_score(
    prediction: TeamMemoryPaperPredictionRow,
    outcome: TeamMemoryPaperOutcomeRow,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(
            (prediction.forecast_probability - _actual_value(outcome)) ** 2,
        )


def _actual_value(outcome: TeamMemoryPaperOutcomeRow) -> Decimal:
    if outcome.actual_outcome == "yes":
        return ONE
    return ZERO


def _is_hit(
    prediction: TeamMemoryPaperPredictionRow,
    outcome: TeamMemoryPaperOutcomeRow,
) -> bool:
    if prediction.forecast_probability >= Decimal("0.500000"):
        return outcome.actual_outcome == "yes"
    return outcome.actual_outcome == "no"


def _absolute_edge(prediction: TeamMemoryPaperPredictionRow) -> Decimal:
    return _absolute_difference(
        prediction.forecast_probability,
        prediction.implied_probability,
    )


def _edge_bucket_index(
    absolute_edge: Decimal,
    edge_bucket_bounds: tuple[Decimal, ...],
) -> int:
    for index, upper_bound in enumerate(edge_bucket_bounds):
        if absolute_edge < upper_bound:
            return index
    return len(edge_bucket_bounds)


def _edge_bucket_key(index: int, edge_bucket_bounds: tuple[Decimal, ...]) -> str:
    if index == 0:
        return f"{ZERO}-{edge_bucket_bounds[0]}"
    if index == len(edge_bucket_bounds):
        return f"{edge_bucket_bounds[-1]}+"
    return f"{edge_bucket_bounds[index - 1]}-{edge_bucket_bounds[index]}"


def _sample_size_confidence(
    resolved_count: int,
    *,
    config: TeamMemoryPerformanceMetricsConfig,
) -> str:
    if resolved_count >= config.confident_sample_size:
        return "confident"
    if resolved_count >= config.developing_sample_size:
        return "developing"
    return "thin"


def _sample_size_confidence_score(
    resolved_count: int,
    *,
    config: TeamMemoryPerformanceMetricsConfig,
) -> Decimal:
    return min(ONE, _ratio_or_zero(resolved_count, config.confident_sample_size))


def _row_reason_codes(
    *,
    resolved_count: int,
    unresolved_count: int,
    sample_size_confidence: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if resolved_count == 0:
        reason_codes.append("no_resolved_outcomes")
    reason_codes.extend(_sample_size_reason_codes(sample_size_confidence))
    if unresolved_count > 0:
        reason_codes.append("unresolved_predictions")
    return _normalize_reason_codes(tuple(reason_codes))


def _sample_size_reason_codes(sample_size_confidence: str) -> tuple[str, ...]:
    if sample_size_confidence == "confident":
        return ("sample_size_confident",)
    if sample_size_confidence == "developing":
        return ("sample_size_developing",)
    return ("thin_sample_size",)


def _report_reason_codes(
    team_rows: tuple[TeamMemoryPerformanceTeamRow, ...],
    *,
    prediction_count: int,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if prediction_count == 0:
        reason_codes.append("empty_predictions")
    if prediction_count > 0 and sum(row.resolved_count for row in team_rows) == 0:
        reason_codes.append("no_resolved_outcomes")
    if any(row.sample_size_confidence != "confident" for row in team_rows):
        reason_codes.append("thin_team_sample")
    if any(row.unresolved_count > 0 for row in team_rows):
        reason_codes.append("unresolved_predictions")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_team_rows(rows: object) -> tuple[TeamMemoryPerformanceTeamRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("team_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_team_ids: set[str] = set()
    for row in normalized:
        if type(row) is not TeamMemoryPerformanceTeamRow:
            raise ValueError("team_rows must contain TeamMemoryPerformanceTeamRow values")
        _require_hard_flags("TeamMemoryPerformanceTeamRow", row)
        if row.team_id in seen_team_ids:
            raise ValueError("team_rows must not contain duplicate team_id values")
        seen_team_ids.add(row.team_id)
    if tuple(row.team_id for row in normalized) != tuple(sorted(row.team_id for row in normalized)):
        raise ValueError("team_rows must be sorted by team_id")
    return normalized


def _normalize_edge_bucket_rows(
    rows: object,
    team_id: str,
) -> tuple[TeamMemoryEdgeBucketPerformanceRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("edge_bucket_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_bucket_keys: set[str] = set()
    for row in normalized:
        if type(row) is not TeamMemoryEdgeBucketPerformanceRow:
            raise ValueError(
                "edge_bucket_rows must contain TeamMemoryEdgeBucketPerformanceRow values",
            )
        _require_hard_flags("TeamMemoryEdgeBucketPerformanceRow", row)
        if row.team_id != team_id:
            raise ValueError("edge bucket row team_id must match team row team_id")
        if row.bucket_key in seen_bucket_keys:
            raise ValueError("edge_bucket_rows must not contain duplicate bucket_key values")
        seen_bucket_keys.add(row.bucket_key)
    return normalized


def _normalize_edge_bucket_bounds(values: object) -> tuple[Decimal, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("edge_bucket_bounds must be a list or tuple")
    bounds = tuple(_normalize_probability("edge_bucket_bounds", value) for value in values)
    if not bounds:
        raise ValueError("edge_bucket_bounds must not be empty")
    if len(set(bounds)) != len(bounds) or bounds != tuple(sorted(bounds)):
        raise ValueError("edge_bucket_bounds must be strictly increasing")
    if bounds[-1] == ONE:
        raise ValueError("edge_bucket_bounds must leave a final overflow bucket")
    return bounds


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODE_ORDER:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in REASON_CODE_ORDER if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic order")
    return reason_codes


def _tuple_from_iterable(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    return tuple(value)


def _mean_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(sum(values, start=ZERO) / Decimal(len(values)))


def _ratio_or_zero(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(Decimal(numerator) / Decimal(denominator))


def _absolute_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(abs(left - right))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_probability(value)


def _quantize_probability(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_sample_size_confidence(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SAMPLE_SIZE_CONFIDENCE_VALUES:
        raise ValueError(f"{field_name} must be thin, developing, or confident")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    require_paper_only_flags(label, value)


__all__ = (
    "TeamMemoryEdgeBucketPerformanceRow",
    "TeamMemoryPaperOutcomeRow",
    "TeamMemoryPaperPredictionRow",
    "TeamMemoryPerformanceMetricsConfig",
    "TeamMemoryPerformanceMetricsReport",
    "TeamMemoryPerformanceTeamRow",
    "build_team_memory_performance_metrics_report",
    "team_memory_performance_metrics_payload",
)
