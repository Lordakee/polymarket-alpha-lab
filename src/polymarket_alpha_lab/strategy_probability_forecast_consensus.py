"""Pure report-only probability forecast consensus reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_PROBABILITY_FORECAST_CONSENSUS_CONFIG_VERSION = (
    "strategy-probability-forecast-consensus-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
CONSENSUS_STATUSES = frozenset(
    ("ready", "watch", "conflict", "insufficient_evidence"),
)


@dataclass(frozen=True)
class StrategyProbabilityForecastConsensusConfig:
    config_version: str = DEFAULT_STRATEGY_PROBABILITY_FORECAST_CONSENSUS_CONFIG_VERSION
    min_forecast_count: Decimal = Decimal("2")
    min_average_confidence: Decimal = Decimal("0.500000")
    max_ready_dispersion_score: Decimal = Decimal("0.150000")
    max_watch_dispersion_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityForecastConsensusConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_forecast_count",
            _normalize_nonnegative_decimal("min_forecast_count", self.min_forecast_count),
        )
        for field_name in (
            "min_average_confidence",
            "max_ready_dispersion_score",
            "max_watch_dispersion_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.max_watch_dispersion_score < self.max_ready_dispersion_score:
            raise ValueError(
                "max_watch_dispersion_score must be greater than or equal to "
                "max_ready_dispersion_score",
            )
        reject_unsafe_surface_fields(
            "strategy probability forecast consensus config",
            self,
        )
        require_paper_only_flags("StrategyProbabilityForecastConsensusConfig", self)


@dataclass(frozen=True)
class StrategyProbabilityForecastConsensusInput:
    team_id: str
    forecast_probability: Decimal
    weight: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityForecastConsensusInput:
            raise ValueError("forecast input must be exact")
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "weight",
            _normalize_nonnegative_decimal("weight", self.weight),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_probability("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields(
            "strategy probability forecast consensus input",
            self,
        )
        require_paper_only_flags("StrategyProbabilityForecastConsensusInput", self)


@dataclass(frozen=True)
class StrategyProbabilityForecastConsensusReport:
    generated_at: datetime
    config_version: str
    forecast_count: Decimal
    total_weight: Decimal
    total_effective_weight: Decimal
    average_confidence: Decimal
    consensus_probability: Decimal
    dispersion_score: Decimal
    consensus_status: str
    forecasts: tuple[StrategyProbabilityForecastConsensusInput, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityForecastConsensusReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_count",
            "total_weight",
            "total_effective_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence",
            "consensus_probability",
            "dispersion_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.consensus_status not in CONSENSUS_STATUSES:
            raise ValueError("consensus_status must be a known consensus status")
        object.__setattr__(self, "forecasts", _normalize_forecasts(self.forecasts))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields(
            "strategy probability forecast consensus report",
            self,
        )
        require_paper_only_flags("StrategyProbabilityForecastConsensusReport", self)
        _validate_report_consistency(self)


def build_strategy_probability_forecast_consensus(
    forecasts: (
        list[StrategyProbabilityForecastConsensusInput]
        | tuple[StrategyProbabilityForecastConsensusInput, ...]
    ),
    *,
    generated_at: datetime,
    config: StrategyProbabilityForecastConsensusConfig | None = None,
) -> StrategyProbabilityForecastConsensusReport:
    if config is None:
        config = StrategyProbabilityForecastConsensusConfig()
    if type(config) is not StrategyProbabilityForecastConsensusConfig:
        raise ValueError("config must be a StrategyProbabilityForecastConsensusConfig")
    require_paper_only_flags("StrategyProbabilityForecastConsensusConfig", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_forecasts = _normalize_forecasts(forecasts)
    _reject_duplicate_team_ids(normalized_forecasts)

    forecast_count = _decimal_count(len(normalized_forecasts))
    total_weight = _sum_decimal(row.weight for row in normalized_forecasts)
    total_effective_weight = _sum_decimal(
        _mul_decimal(row.weight, row.confidence) for row in normalized_forecasts
    )

    if not normalized_forecasts:
        return StrategyProbabilityForecastConsensusReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            forecast_count=forecast_count,
            total_weight=total_weight,
            total_effective_weight=total_effective_weight,
            average_confidence=ZERO,
            consensus_probability=ZERO,
            dispersion_score=ZERO,
            consensus_status="insufficient_evidence",
            forecasts=normalized_forecasts,
            reason_codes=("no_forecasts", "insufficient_forecast_count"),
        )

    average_confidence = _weighted_average(
        tuple((row.confidence, row.weight) for row in normalized_forecasts),
    )
    if total_effective_weight == ZERO:
        return StrategyProbabilityForecastConsensusReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            forecast_count=forecast_count,
            total_weight=total_weight,
            total_effective_weight=total_effective_weight,
            average_confidence=average_confidence,
            consensus_probability=ZERO,
            dispersion_score=ZERO,
            consensus_status="insufficient_evidence",
            forecasts=normalized_forecasts,
            reason_codes=_insufficient_reason_codes(forecast_count, config, zero_weight=True),
        )

    consensus_probability = _weighted_average(
        tuple(
            (
                row.forecast_probability,
                _mul_decimal(row.weight, row.confidence),
            )
            for row in normalized_forecasts
        ),
    )
    dispersion_score = _weighted_average(
        tuple(
            (
                abs(row.forecast_probability - consensus_probability),
                _mul_decimal(row.weight, row.confidence),
            )
            for row in normalized_forecasts
        ),
    )
    consensus_status, reason_codes = _consensus_status_and_reasons(
        forecast_count=forecast_count,
        average_confidence=average_confidence,
        dispersion_score=dispersion_score,
        config=config,
    )

    return StrategyProbabilityForecastConsensusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        forecast_count=forecast_count,
        total_weight=total_weight,
        total_effective_weight=total_effective_weight,
        average_confidence=average_confidence,
        consensus_probability=consensus_probability,
        dispersion_score=dispersion_score,
        consensus_status=consensus_status,
        forecasts=normalized_forecasts,
        reason_codes=reason_codes,
    )


def _consensus_status_and_reasons(
    *,
    forecast_count: Decimal,
    average_confidence: Decimal,
    dispersion_score: Decimal,
    config: StrategyProbabilityForecastConsensusConfig,
) -> tuple[str, tuple[str, ...]]:
    if forecast_count < config.min_forecast_count:
        return "insufficient_evidence", ("insufficient_forecast_count",)
    if dispersion_score > config.max_watch_dispersion_score:
        return "conflict", ("high_dispersion", "consensus_conflict")
    if (
        dispersion_score > config.max_ready_dispersion_score
        or average_confidence < config.min_average_confidence
    ):
        reasons: list[str] = []
        if dispersion_score > config.max_ready_dispersion_score:
            reasons.append("elevated_dispersion")
        if average_confidence < config.min_average_confidence:
            reasons.append("low_average_confidence")
        reasons.append("consensus_watch")
        return "watch", tuple(reasons)
    return "ready", ("consensus_ready",)


def _insufficient_reason_codes(
    forecast_count: Decimal,
    config: StrategyProbabilityForecastConsensusConfig,
    *,
    zero_weight: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if forecast_count < config.min_forecast_count:
        reason_codes.append("insufficient_forecast_count")
    if zero_weight:
        reason_codes.append("zero_effective_weight")
    return tuple(reason_codes)


def _validate_report_consistency(report: StrategyProbabilityForecastConsensusReport) -> None:
    if report.forecast_count != _decimal_count(len(report.forecasts)):
        raise ValueError("forecast_count must equal forecasts length")
    if report.consensus_status == "ready" and report.reason_codes != ("consensus_ready",):
        raise ValueError("ready consensus requires consensus_ready reason")
    if report.consensus_status == "conflict" and "consensus_conflict" not in report.reason_codes:
        raise ValueError("conflict consensus requires consensus_conflict reason")
    if (
        report.consensus_status == "insufficient_evidence"
        and not report.reason_codes
    ):
        raise ValueError("insufficient evidence consensus requires reason_codes")


def _normalize_forecasts(
    forecasts: (
        list[StrategyProbabilityForecastConsensusInput]
        | tuple[StrategyProbabilityForecastConsensusInput, ...]
    ),
) -> tuple[StrategyProbabilityForecastConsensusInput, ...]:
    if type(forecasts) not in (list, tuple):
        raise ValueError("forecasts must be a list or tuple")
    normalized = tuple(forecasts)
    for forecast in normalized:
        if type(forecast) is not StrategyProbabilityForecastConsensusInput:
            raise ValueError(
                "forecasts must contain StrategyProbabilityForecastConsensusInput values",
            )
        require_paper_only_flags("StrategyProbabilityForecastConsensusInput", forecast)
    return normalized


def _reject_duplicate_team_ids(
    forecasts: tuple[StrategyProbabilityForecastConsensusInput, ...],
) -> None:
    seen: set[str] = set()
    for forecast in forecasts:
        if forecast.team_id in seen:
            raise ValueError("duplicate team_id forecast")
        seen.add(forecast.team_id)


def _weighted_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    total_weight = _sum_decimal(weight for _value, weight in values)
    if total_weight == ZERO:
        return ZERO
    weighted_sum = _sum_decimal(_mul_decimal(value, weight) for value, weight in values)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("weighted_average", weighted_sum / total_weight)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total = total + _normalize_decimal("sum value", value)
    return _normalize_decimal("sum", total)


def _mul_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("product", left * right)


def _decimal_count(value: int) -> Decimal:
    return _normalize_nonnegative_decimal("count", Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
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


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    items = _normalize_string_tuple("reason_codes", value)
    return tuple(dict.fromkeys(items))


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_FORECAST_CONSENSUS_CONFIG_VERSION",
    "StrategyProbabilityForecastConsensusConfig",
    "StrategyProbabilityForecastConsensusInput",
    "StrategyProbabilityForecastConsensusReport",
    "build_strategy_probability_forecast_consensus",
)
