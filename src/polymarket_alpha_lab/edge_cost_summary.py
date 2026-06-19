"""Paper-only edge cost summary over forecast evidence observations.

Pure arithmetic over caller-supplied ``PaperForecastEvidenceObservation`` values.
This module is local/report-only and only reduces already-typed evidence values.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

EDGE_COST_SUMMARY_STATUSES = (
    "empty_edge_cost_history",
    "insufficient_edge_cost_sample",
    "edge_cost_evidence_observed",
    "edge_cost_quality_flags",
)


@dataclass(frozen=True)
class PaperEdgeCostSummaryConfig:
    config_version: str
    min_edge_observation_count: int = 30
    min_fill_probability: Decimal = Decimal("0.500000")
    max_residual_exposure_ratio: Decimal = Decimal("0.250000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_edge_observation_count",
            self.min_edge_observation_count,
        )
        _require_probability_decimal("min_fill_probability", self.min_fill_probability)
        _require_probability_decimal(
            "max_residual_exposure_ratio",
            self.max_residual_exposure_ratio,
        )


@dataclass(frozen=True)
class PaperEdgeCostSummaryReport:
    generated_at: datetime
    config_version: str
    edge_observation_count: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    mean_theoretical_edge_ratio: Decimal | None
    mean_executable_edge_ratio: Decimal | None
    mean_edge_cost_drag: Decimal | None
    mean_fill_probability: Decimal | None
    mean_residual_exposure_ratio: Decimal | None
    mean_paper_return_ratio: Decimal | None
    negative_executable_edge_count: int
    negative_executable_edge_rate: Decimal | None
    low_fill_probability_count: int
    low_fill_probability_rate: Decimal | None
    high_residual_exposure_count: int
    high_residual_exposure_rate: Decimal | None
    positive_paper_return_count: int
    positive_paper_return_rate: Decimal | None
    status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.first_observed_at is not None:
            object.__setattr__(
                self,
                "first_observed_at",
                _as_utc(self.first_observed_at),
            )
        if self.last_observed_at is not None:
            object.__setattr__(
                self,
                "last_observed_at",
                _as_utc(self.last_observed_at),
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "edge_observation_count",
            "negative_executable_edge_count",
            "low_fill_probability_count",
            "high_residual_exposure_count",
            "positive_paper_return_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "mean_theoretical_edge_ratio",
            "mean_executable_edge_ratio",
            "mean_edge_cost_drag",
            "mean_paper_return_ratio",
        ):
            _require_optional_ratio_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "mean_fill_probability",
            "mean_residual_exposure_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "negative_executable_edge_rate",
            "low_fill_probability_rate",
            "high_residual_exposure_rate",
            "positive_paper_return_rate",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in EDGE_COST_SUMMARY_STATUSES:
            raise ValueError("status must be a known edge cost summary status")
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_edge_cost_summary_report(
    observations: Iterable[PaperForecastEvidenceObservation],
    *,
    config: PaperEdgeCostSummaryConfig,
    generated_at: datetime,
) -> PaperEdgeCostSummaryReport:
    """Summarize edge-cost evidence from complete paper observations."""

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
            last_observed_at=None,
            mean_theoretical_edge_ratio=None,
            mean_executable_edge_ratio=None,
            mean_edge_cost_drag=None,
            mean_fill_probability=None,
            mean_residual_exposure_ratio=None,
            mean_paper_return_ratio=None,
            negative_executable_edge_count=0,
            negative_executable_edge_rate=None,
            low_fill_probability_count=0,
            low_fill_probability_rate=None,
            high_residual_exposure_count=0,
            high_residual_exposure_rate=None,
            positive_paper_return_count=0,
            positive_paper_return_rate=None,
            status="empty_edge_cost_history",
        )

    negative_executable_edge_count = sum(
        1 for item in edge_items if item.executable_edge_ratio < ZERO
    )
    low_fill_probability_count = sum(
        1 for item in edge_items if item.fill_probability < config.min_fill_probability
    )
    high_residual_exposure_count = sum(
        1
        for item in edge_items
        if item.residual_exposure_ratio > config.max_residual_exposure_ratio
    )
    positive_paper_return_count = sum(
        1 for item in edge_items if item.paper_return_ratio > ZERO
    )

    return PaperEdgeCostSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        edge_observation_count=edge_observation_count,
        first_observed_at=edge_items[0].observed_at,
        last_observed_at=edge_items[-1].observed_at,
        mean_theoretical_edge_ratio=_mean(
            tuple(item.theoretical_edge_ratio for item in edge_items),
        ),
        mean_executable_edge_ratio=_mean(
            tuple(item.executable_edge_ratio for item in edge_items),
        ),
        mean_edge_cost_drag=_mean(tuple(_edge_cost_drag(item) for item in edge_items)),
        mean_fill_probability=_mean(tuple(item.fill_probability for item in edge_items)),
        mean_residual_exposure_ratio=_mean(
            tuple(item.residual_exposure_ratio for item in edge_items),
        ),
        mean_paper_return_ratio=_mean(
            tuple(item.paper_return_ratio for item in edge_items),
        ),
        negative_executable_edge_count=negative_executable_edge_count,
        negative_executable_edge_rate=_rate(
            negative_executable_edge_count,
            edge_observation_count,
        ),
        low_fill_probability_count=low_fill_probability_count,
        low_fill_probability_rate=_rate(
            low_fill_probability_count,
            edge_observation_count,
        ),
        high_residual_exposure_count=high_residual_exposure_count,
        high_residual_exposure_rate=_rate(
            high_residual_exposure_count,
            edge_observation_count,
        ),
        positive_paper_return_count=positive_paper_return_count,
        positive_paper_return_rate=_rate(
            positive_paper_return_count,
            edge_observation_count,
        ),
        status=_summary_status(
            edge_observation_count=edge_observation_count,
            negative_executable_edge_count=negative_executable_edge_count,
            low_fill_probability_count=low_fill_probability_count,
            high_residual_exposure_count=high_residual_exposure_count,
            config=config,
        ),
    )


def _normalize_observations(
    observations: Iterable[PaperForecastEvidenceObservation],
) -> tuple[PaperForecastEvidenceObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observation_items = tuple(observations)
    for observation in observation_items:
        if type(observation) is not PaperForecastEvidenceObservation:
            raise ValueError(
                "observations must contain PaperForecastEvidenceObservation values"
            )
        if observation.paper_only is not True:
            raise ValueError("observations must be paper-only")
        if not _complete_edge_role(observation):
            raise ValueError("observations must contain complete edge role values")
    return observation_items


def _complete_edge_role(item: PaperForecastEvidenceObservation) -> bool:
    return (
        item.theoretical_edge_ratio is not None
        and item.executable_edge_ratio is not None
        and item.fill_probability is not None
        and item.residual_exposure_ratio is not None
        and item.paper_return_ratio is not None
    )


def _edge_cost_drag(item: PaperForecastEvidenceObservation) -> Decimal:
    return max(item.theoretical_edge_ratio - item.executable_edge_ratio, ZERO)


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / Decimal(len(values)))


def _rate(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _summary_status(
    *,
    edge_observation_count: int,
    negative_executable_edge_count: int,
    low_fill_probability_count: int,
    high_residual_exposure_count: int,
    config: PaperEdgeCostSummaryConfig,
) -> str:
    if edge_observation_count == 0:
        return "empty_edge_cost_history"
    if (
        negative_executable_edge_count > 0
        or low_fill_probability_count > 0
        or high_residual_exposure_count > 0
    ):
        return "edge_cost_quality_flags"
    if edge_observation_count < config.min_edge_observation_count:
        return "insufficient_edge_cost_sample"
    return "edge_cost_evidence_observed"


def _validate_report_consistency(report: PaperEdgeCostSummaryReport) -> None:
    if report.edge_observation_count == 0:
        if report.first_observed_at is not None or report.last_observed_at is not None:
            raise ValueError("observed_at bounds must be absent without observations")
        for field_name in (
            "mean_theoretical_edge_ratio",
            "mean_executable_edge_ratio",
            "mean_edge_cost_drag",
            "mean_fill_probability",
            "mean_residual_exposure_ratio",
            "mean_paper_return_ratio",
            "negative_executable_edge_rate",
            "low_fill_probability_rate",
            "high_residual_exposure_rate",
            "positive_paper_return_rate",
        ):
            if getattr(report, field_name) is not None:
                raise ValueError(f"{field_name} must be absent without observations")
        for field_name in (
            "negative_executable_edge_count",
            "low_fill_probability_count",
            "high_residual_exposure_count",
            "positive_paper_return_count",
        ):
            if getattr(report, field_name) != 0:
                raise ValueError(f"{field_name} must be zero without edge_observation_count")
        if report.status != "empty_edge_cost_history":
            raise ValueError("status must match edge cost observations")
        return

    if report.first_observed_at is None or report.last_observed_at is None:
        raise ValueError("observed_at bounds are required with observations")
    for field_name in (
        "mean_theoretical_edge_ratio",
        "mean_executable_edge_ratio",
        "mean_edge_cost_drag",
        "mean_fill_probability",
        "mean_residual_exposure_ratio",
        "mean_paper_return_ratio",
        "negative_executable_edge_rate",
        "low_fill_probability_rate",
        "high_residual_exposure_rate",
        "positive_paper_return_rate",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with observations")
    for field_name in (
        "negative_executable_edge_count",
        "low_fill_probability_count",
        "high_residual_exposure_count",
        "positive_paper_return_count",
    ):
        if getattr(report, field_name) > report.edge_observation_count:
            raise ValueError(f"{field_name} cannot exceed edge_observation_count")
    if report.status == "empty_edge_cost_history":
        raise ValueError("status must match edge cost observations")
    expected_rates = (
        (
            "negative_executable_edge_rate",
            report.negative_executable_edge_count,
            report.negative_executable_edge_rate,
        ),
        (
            "low_fill_probability_rate",
            report.low_fill_probability_count,
            report.low_fill_probability_rate,
        ),
        (
            "high_residual_exposure_rate",
            report.high_residual_exposure_count,
            report.high_residual_exposure_rate,
        ),
        (
            "positive_paper_return_rate",
            report.positive_paper_return_count,
            report.positive_paper_return_rate,
        ),
    )
    for field_name, count, rate in expected_rates:
        if rate != _rate(count, report.edge_observation_count):
            raise ValueError(f"{field_name} must match edge observation count")
    if report.mean_edge_cost_drag is not None and report.mean_edge_cost_drag < ZERO:
        raise ValueError("mean_edge_cost_drag must be nonnegative")
    if (
        report.mean_executable_edge_ratio is not None
        and report.mean_executable_edge_ratio < ZERO
        and report.negative_executable_edge_count == 0
    ):
        raise ValueError(
            "mean_executable_edge_ratio cannot be negative without negative observations",
        )
    if (
        report.mean_theoretical_edge_ratio is not None
        and report.mean_executable_edge_ratio is not None
        and report.mean_edge_cost_drag is not None
        and report.mean_edge_cost_drag + RATIO_QUANTUM
        < _quantize_ratio(
            max(
                report.mean_theoretical_edge_ratio
                - report.mean_executable_edge_ratio,
                ZERO,
            ),
        )
    ):
        raise ValueError("mean_edge_cost_drag must cover mean executable drag")
    quality_count = (
        report.negative_executable_edge_count
        + report.low_fill_probability_count
        + report.high_residual_exposure_count
    )
    if report.status == "edge_cost_quality_flags":
        if quality_count == 0:
            raise ValueError("status must match edge cost quality flags")
    elif quality_count != 0:
        raise ValueError("status must match edge cost quality flags")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_optional_ratio_decimal(field_name: str, value: object) -> None:
    _require_optional_decimal(field_name, value)
    if value is not None and value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_probability_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_probability_decimal(field_name, value)
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


__all__ = (
    "PaperEdgeCostSummaryConfig",
    "PaperEdgeCostSummaryReport",
    "build_paper_edge_cost_summary_report",
)
