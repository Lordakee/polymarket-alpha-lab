"""Paper-only edge cost summary over supplied forecast evidence values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

EMPTY_STATUS = "empty_edge_cost_summary"
OBSERVED_STATUS = "edge_cost_summary_observed"


@dataclass(frozen=True)
class PaperEdgeCostSummaryConfig:
    config_version: str
    low_fill_probability_threshold: Decimal = Decimal("0.500000")
    high_residual_exposure_threshold: Decimal = Decimal("0.100000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_probability_decimal(
            "low_fill_probability_threshold",
            self.low_fill_probability_threshold,
        )
        _require_probability_decimal(
            "high_residual_exposure_threshold",
            self.high_residual_exposure_threshold,
        )


@dataclass(frozen=True)
class PaperEdgeCostSummaryReport:
    generated_at: datetime
    config_version: str
    edge_observation_count: int
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    unique_market_count: int
    unique_strategy_count: int
    unique_risk_tag_count: int
    mean_theoretical_edge_ratio: Decimal | None
    mean_executable_edge_ratio: Decimal | None
    mean_edge_cost_gap: Decimal | None
    worst_edge_cost_gap: Decimal | None
    negative_executable_edge_count: int
    negative_executable_edge_ratio: Decimal | None
    mean_fill_probability: Decimal | None
    low_fill_probability_count: int
    low_fill_probability_ratio: Decimal | None
    mean_residual_exposure_ratio: Decimal | None
    worst_residual_exposure_ratio: Decimal | None
    high_residual_exposure_count: int
    high_residual_exposure_ratio: Decimal | None
    mean_paper_return_ratio: Decimal | None
    positive_paper_return_count: int
    positive_paper_return_ratio: Decimal | None
    status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
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
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "edge_observation_count",
            "unique_market_count",
            "unique_strategy_count",
            "unique_risk_tag_count",
            "negative_executable_edge_count",
            "low_fill_probability_count",
            "high_residual_exposure_count",
            "positive_paper_return_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "mean_theoretical_edge_ratio",
            "mean_executable_edge_ratio",
            "mean_paper_return_ratio",
        ):
            _require_optional_quantized_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "mean_edge_cost_gap",
            "worst_edge_cost_gap",
        ):
            _require_optional_nonnegative_quantized_decimal(
                field_name,
                getattr(self, field_name),
            )
        for field_name in (
            "negative_executable_edge_ratio",
            "mean_fill_probability",
            "low_fill_probability_ratio",
            "mean_residual_exposure_ratio",
            "worst_residual_exposure_ratio",
            "high_residual_exposure_ratio",
            "positive_paper_return_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in (EMPTY_STATUS, OBSERVED_STATUS):
            raise ValueError("status must be a known edge cost summary status")
        _require_report_shape(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_edge_cost_summary_report(
    observations: list[PaperForecastEvidenceObservation]
    | tuple[PaperForecastEvidenceObservation, ...],
    *,
    config: PaperEdgeCostSummaryConfig,
    generated_at: datetime,
) -> PaperEdgeCostSummaryReport:
    """Reduce complete paper edge evidence into a read-only report."""

    if type(config) is not PaperEdgeCostSummaryConfig:
        raise ValueError("config must be a PaperEdgeCostSummaryConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    edge_items = _normalize_observations(observations)
    edge_observation_count = len(edge_items)

    if edge_observation_count == 0:
        return PaperEdgeCostSummaryReport(
            generated_at=generated_at,
            config_version=config.config_version,
            edge_observation_count=0,
            first_observed_at=None,
            latest_observed_at=None,
            unique_market_count=0,
            unique_strategy_count=0,
            unique_risk_tag_count=0,
            mean_theoretical_edge_ratio=None,
            mean_executable_edge_ratio=None,
            mean_edge_cost_gap=None,
            worst_edge_cost_gap=None,
            negative_executable_edge_count=0,
            negative_executable_edge_ratio=None,
            mean_fill_probability=None,
            low_fill_probability_count=0,
            low_fill_probability_ratio=None,
            mean_residual_exposure_ratio=None,
            worst_residual_exposure_ratio=None,
            high_residual_exposure_count=0,
            high_residual_exposure_ratio=None,
            mean_paper_return_ratio=None,
            positive_paper_return_count=0,
            positive_paper_return_ratio=None,
            status=EMPTY_STATUS,
        )

    edge_cost_gaps = tuple(_edge_cost_gap(item) for item in edge_items)
    negative_executable_edge_count = sum(
        1 for item in edge_items if item.executable_edge_ratio < ZERO
    )
    low_fill_probability_count = sum(
        1
        for item in edge_items
        if item.fill_probability < config.low_fill_probability_threshold
    )
    high_residual_exposure_count = sum(
        1
        for item in edge_items
        if item.residual_exposure_ratio > config.high_residual_exposure_threshold
    )
    positive_paper_return_count = sum(
        1 for item in edge_items if item.paper_return_ratio > ZERO
    )

    return PaperEdgeCostSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        edge_observation_count=edge_observation_count,
        first_observed_at=edge_items[0].observed_at,
        latest_observed_at=edge_items[-1].observed_at,
        unique_market_count=len({item.market_slug for item in edge_items}),
        unique_strategy_count=len({item.strategy_type for item in edge_items}),
        unique_risk_tag_count=len(
            {risk_tag for item in edge_items for risk_tag in item.risk_tags},
        ),
        mean_theoretical_edge_ratio=_mean(
            tuple(item.theoretical_edge_ratio for item in edge_items),
        ),
        mean_executable_edge_ratio=_mean(
            tuple(item.executable_edge_ratio for item in edge_items),
        ),
        mean_edge_cost_gap=_mean(edge_cost_gaps),
        worst_edge_cost_gap=max(edge_cost_gaps),
        negative_executable_edge_count=negative_executable_edge_count,
        negative_executable_edge_ratio=_ratio(
            negative_executable_edge_count,
            edge_observation_count,
        ),
        mean_fill_probability=_mean(tuple(item.fill_probability for item in edge_items)),
        low_fill_probability_count=low_fill_probability_count,
        low_fill_probability_ratio=_ratio(
            low_fill_probability_count,
            edge_observation_count,
        ),
        mean_residual_exposure_ratio=_mean(
            tuple(item.residual_exposure_ratio for item in edge_items),
        ),
        worst_residual_exposure_ratio=max(
            item.residual_exposure_ratio for item in edge_items
        ),
        high_residual_exposure_count=high_residual_exposure_count,
        high_residual_exposure_ratio=_ratio(
            high_residual_exposure_count,
            edge_observation_count,
        ),
        mean_paper_return_ratio=_mean(
            tuple(item.paper_return_ratio for item in edge_items),
        ),
        positive_paper_return_count=positive_paper_return_count,
        positive_paper_return_ratio=_ratio(
            positive_paper_return_count,
            edge_observation_count,
        ),
        status=OBSERVED_STATUS,
    )


def _normalize_observations(
    observations: list[PaperForecastEvidenceObservation]
    | tuple[PaperForecastEvidenceObservation, ...],
) -> tuple[PaperForecastEvidenceObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observation_items = tuple(observations)
    for observation in observation_items:
        if type(observation) is not PaperForecastEvidenceObservation:
            raise ValueError(
                "observations must contain PaperForecastEvidenceObservation values",
            )
        if observation.paper_only is not True:
            raise ValueError("observations must have paper_only True")
        _require_complete_edge_observation(observation)
    return observation_items


def _require_complete_edge_observation(
    observation: PaperForecastEvidenceObservation,
) -> None:
    for field_name in (
        "theoretical_edge_ratio",
        "executable_edge_ratio",
        "fill_probability",
        "residual_exposure_ratio",
        "paper_return_ratio",
    ):
        if getattr(observation, field_name) is None:
            raise ValueError(f"observations must contain complete edge values: {field_name}")


def _edge_cost_gap(observation: PaperForecastEvidenceObservation) -> Decimal:
    gap = observation.theoretical_edge_ratio - observation.executable_edge_ratio
    if gap < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize_ratio(gap)


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _require_report_shape(report: PaperEdgeCostSummaryReport) -> None:
    if report.edge_observation_count == 0:
        _require_empty_report_shape(report)
        return
    _require_nonempty_report_shape(report)


def _require_empty_report_shape(report: PaperEdgeCostSummaryReport) -> None:
    if report.first_observed_at is not None:
        raise ValueError("first_observed_at must be absent without observations")
    if report.latest_observed_at is not None:
        raise ValueError("latest_observed_at must be absent without observations")
    for field_name in (
        "unique_market_count",
        "unique_strategy_count",
        "unique_risk_tag_count",
        "negative_executable_edge_count",
        "low_fill_probability_count",
        "high_residual_exposure_count",
        "positive_paper_return_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without observations")
    for field_name in (
        "mean_theoretical_edge_ratio",
        "mean_executable_edge_ratio",
        "mean_edge_cost_gap",
        "worst_edge_cost_gap",
        "negative_executable_edge_ratio",
        "mean_fill_probability",
        "low_fill_probability_ratio",
        "mean_residual_exposure_ratio",
        "worst_residual_exposure_ratio",
        "high_residual_exposure_ratio",
        "mean_paper_return_ratio",
        "positive_paper_return_ratio",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without observations")
    if report.status != EMPTY_STATUS:
        raise ValueError("status must match edge cost summary observations")


def _require_nonempty_report_shape(report: PaperEdgeCostSummaryReport) -> None:
    if report.first_observed_at is None:
        raise ValueError("first_observed_at is required with observations")
    if report.latest_observed_at is None:
        raise ValueError("latest_observed_at is required with observations")
    for field_name in (
        "mean_theoretical_edge_ratio",
        "mean_executable_edge_ratio",
        "mean_edge_cost_gap",
        "worst_edge_cost_gap",
        "negative_executable_edge_ratio",
        "mean_fill_probability",
        "low_fill_probability_ratio",
        "mean_residual_exposure_ratio",
        "worst_residual_exposure_ratio",
        "high_residual_exposure_ratio",
        "mean_paper_return_ratio",
        "positive_paper_return_ratio",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with observations")
    if report.unique_market_count == 0:
        raise ValueError("unique_market_count is required with observations")
    if report.unique_strategy_count == 0:
        raise ValueError("unique_strategy_count is required with observations")
    if report.unique_market_count > report.edge_observation_count:
        raise ValueError("unique_market_count cannot exceed edge_observation_count")
    if report.unique_strategy_count > report.edge_observation_count:
        raise ValueError("unique_strategy_count cannot exceed edge_observation_count")
    for field_name in (
        "negative_executable_edge_count",
        "low_fill_probability_count",
        "high_residual_exposure_count",
        "positive_paper_return_count",
    ):
        if getattr(report, field_name) > report.edge_observation_count:
            raise ValueError(f"{field_name} cannot exceed edge_observation_count")
    expected_ratios = (
        (
            "negative_executable_edge_ratio",
            report.negative_executable_edge_count,
            report.negative_executable_edge_ratio,
        ),
        (
            "low_fill_probability_ratio",
            report.low_fill_probability_count,
            report.low_fill_probability_ratio,
        ),
        (
            "high_residual_exposure_ratio",
            report.high_residual_exposure_count,
            report.high_residual_exposure_ratio,
        ),
        (
            "positive_paper_return_ratio",
            report.positive_paper_return_count,
            report.positive_paper_return_ratio,
        ),
    )
    for field_name, count, ratio in expected_ratios:
        if ratio != _ratio(count, report.edge_observation_count):
            raise ValueError(f"{field_name} must match edge_observation_count")
    if report.worst_edge_cost_gap < report.mean_edge_cost_gap:
        raise ValueError("worst_edge_cost_gap must cover mean_edge_cost_gap")
    if report.worst_residual_exposure_ratio < report.mean_residual_exposure_ratio:
        raise ValueError(
            "worst_residual_exposure_ratio must cover mean_residual_exposure_ratio",
        )
    if report.status != OBSERVED_STATUS:
        raise ValueError("status must match edge cost summary observations")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or None")
    return _as_utc(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_quantized_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_optional_quantized_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_quantized_decimal(field_name, value)


def _require_optional_nonnegative_quantized_decimal(
    field_name: str,
    value: object,
) -> None:
    if value is None:
        return
    _require_quantized_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_probability_decimal(field_name: str, value: object) -> None:
    _require_quantized_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_probability_decimal(field_name, value)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


__all__ = (
    "PaperEdgeCostSummaryConfig",
    "PaperEdgeCostSummaryReport",
    "build_paper_edge_cost_summary_report",
)
