from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
SEGMENT_TYPES = ("risk_tag", "strategy_type")
STATUS_VALUES = (
    "insufficient_segment_probability_sample",
    "segment_evidence_observed",
    "segment_return_evidence_observed",
)


@dataclass(frozen=True)
class PaperStrategySegmentSummaryConfig:
    config_version: str
    min_segment_observations: int = 10

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_segment_observations",
            self.min_segment_observations,
        )


@dataclass(frozen=True)
class PaperStrategySegmentRow:
    segment_type: str
    segment_name: str
    observation_count: int
    probability_observation_count: int
    return_observation_count: int
    mean_predicted_probability: Decimal | None
    observed_frequency: Decimal | None
    brier_score: Decimal | None
    mean_paper_return_ratio: Decimal | None
    positive_return_rate: Decimal | None
    status: str

    def __post_init__(self) -> None:
        if self.segment_type not in SEGMENT_TYPES:
            raise ValueError("segment_type must be a known segment type")
        _require_canonical_string("segment_name", self.segment_name)
        _require_nonnegative_int("observation_count", self.observation_count)
        _require_nonnegative_int(
            "probability_observation_count",
            self.probability_observation_count,
        )
        _require_nonnegative_int(
            "return_observation_count",
            self.return_observation_count,
        )
        if self.probability_observation_count > self.observation_count:
            raise ValueError("probability_observation_count cannot exceed observation_count")
        if self.return_observation_count > self.observation_count:
            raise ValueError("return_observation_count cannot exceed observation_count")
        if (
            self.probability_observation_count + self.return_observation_count
            < self.observation_count
        ):
            raise ValueError("evidence role counts must cover observation_count")
        _require_optional_probability_decimal(
            "mean_predicted_probability",
            self.mean_predicted_probability,
        )
        _require_optional_probability_decimal(
            "observed_frequency",
            self.observed_frequency,
        )
        _require_optional_probability_decimal("brier_score", self.brier_score)
        _require_optional_decimal(
            "mean_paper_return_ratio",
            self.mean_paper_return_ratio,
        )
        _require_optional_probability_decimal(
            "positive_return_rate",
            self.positive_return_rate,
        )
        if self.status not in STATUS_VALUES:
            raise ValueError("status must be a known segment status")
        if self.probability_observation_count == 0:
            if (
                self.mean_predicted_probability is not None
                or self.observed_frequency is not None
                or self.brier_score is not None
            ):
                raise ValueError(
                    "probability evidence fields must be None without probability observations",
                )
            if self.return_observation_count == 0:
                raise ValueError("return-only rows must contain return observations")
            if self.status != "segment_return_evidence_observed":
                raise ValueError(
                    "return-only rows must use segment_return_evidence_observed",
                )
        else:
            if (
                self.mean_predicted_probability is None
                or self.observed_frequency is None
                or self.brier_score is None
            ):
                raise ValueError(
                    "probability evidence fields must be present with probability observations",
                )
            if self.status == "segment_return_evidence_observed":
                raise ValueError(
                    "segment_return_evidence_observed requires zero probability observations",
                )
        if self.return_observation_count == 0:
            if (
                self.mean_paper_return_ratio is not None
                or self.positive_return_rate is not None
            ):
                raise ValueError(
                    "return evidence fields must be None without return observations",
                )
        else:
            if (
                self.mean_paper_return_ratio is None
                or self.positive_return_rate is None
            ):
                raise ValueError(
                    "return evidence fields must be present with return observations",
                )


@dataclass(frozen=True)
class PaperStrategySegmentSummaryReport:
    generated_at: datetime
    config_version: str
    observation_count: int
    strategy_segment_count: int
    risk_tag_segment_count: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    rows: tuple[PaperStrategySegmentRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("observation_count", self.observation_count)
        _require_nonnegative_int(
            "strategy_segment_count",
            self.strategy_segment_count,
        )
        _require_nonnegative_int(
            "risk_tag_segment_count",
            self.risk_tag_segment_count,
        )
        _require_optional_datetime("first_observed_at", self.first_observed_at)
        _require_optional_datetime("last_observed_at", self.last_observed_at)
        if (self.first_observed_at is None) != (self.last_observed_at is None):
            raise ValueError("first_observed_at and last_observed_at must match presence")
        normalized_rows = _normalize_rows(self.rows)
        if self.observation_count == 0:
            if normalized_rows != ():
                raise ValueError("observation_count must match strategy rows")
            if self.first_observed_at is not None or self.last_observed_at is not None:
                raise ValueError("observed_at bounds must be absent without observations")
        else:
            if self.first_observed_at is None or self.last_observed_at is None:
                raise ValueError("observed_at bounds are required with observations")
            if self.first_observed_at > self.last_observed_at:
                raise ValueError("observed_at bounds must be chronological")
            if not normalized_rows:
                raise ValueError("observation_count must match strategy rows")
            if _strategy_observation_count(normalized_rows) != self.observation_count:
                raise ValueError("observation_count must match strategy rows")
        strategy_segment_count, risk_tag_segment_count = _count_segment_rows(
            normalized_rows,
        )
        if self.strategy_segment_count != strategy_segment_count:
            raise ValueError("strategy_segment_count must match normalized rows")
        if self.risk_tag_segment_count != risk_tag_segment_count:
            raise ValueError("risk_tag_segment_count must match normalized rows")
        object.__setattr__(self, "rows", normalized_rows)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_segment_summary_report(
    observations: Iterable[PaperForecastEvidenceObservation],
    *,
    config: PaperStrategySegmentSummaryConfig,
    generated_at: datetime,
) -> PaperStrategySegmentSummaryReport:
    if type(config) is not PaperStrategySegmentSummaryConfig:
        raise ValueError("config must be a PaperStrategySegmentSummaryConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    items = _normalize_observations(observations)
    groups = _build_groups(items)
    rows = tuple(
        _build_row(
            segment_type=segment_type,
            segment_name=segment_name,
            items=tuple(group_items),
            min_segment_observations=config.min_segment_observations,
        )
        for (segment_type, segment_name), group_items in sorted(groups.items())
    )
    strategy_segment_count, risk_tag_segment_count = _count_segment_rows(rows)

    return PaperStrategySegmentSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=len(items),
        strategy_segment_count=strategy_segment_count,
        risk_tag_segment_count=risk_tag_segment_count,
        first_observed_at=items[0].observed_at if items else None,
        last_observed_at=items[-1].observed_at if items else None,
        rows=rows,
    )


def _normalize_observations(
    observations: Iterable[PaperForecastEvidenceObservation],
) -> tuple[PaperForecastEvidenceObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of PaperForecastEvidenceObservation values",
        )
    try:
        raw_items = tuple(observations)
    except TypeError as exc:
        raise ValueError(
            "observations must be an iterable of PaperForecastEvidenceObservation values",
        ) from exc
    for item in raw_items:
        if type(item) is not PaperForecastEvidenceObservation:
            raise ValueError(
                "observations must contain only PaperForecastEvidenceObservation values",
            )
        if item.paper_only is not True:
            raise ValueError("observations must be paper-only")
    return tuple(sorted(raw_items, key=lambda item: item.observed_at))


def _build_groups(
    items: tuple[PaperForecastEvidenceObservation, ...],
) -> dict[tuple[str, str], list[PaperForecastEvidenceObservation]]:
    groups: dict[tuple[str, str], list[PaperForecastEvidenceObservation]] = {}
    for item in items:
        groups.setdefault(("strategy_type", item.strategy_type), []).append(item)
        seen_risk_tags: set[str] = set()
        for risk_tag in item.risk_tags:
            if risk_tag in seen_risk_tags:
                continue
            seen_risk_tags.add(risk_tag)
            groups.setdefault(("risk_tag", risk_tag), []).append(item)
    return groups


def _build_row(
    *,
    segment_type: str,
    segment_name: str,
    items: tuple[PaperForecastEvidenceObservation, ...],
    min_segment_observations: int,
) -> PaperStrategySegmentRow:
    probability_items = tuple(item for item in items if _has_probability_values(item))
    return_items = tuple(item for item in items if item.paper_return_ratio is not None)
    probability_observation_count = len(probability_items)
    return_observation_count = len(return_items)

    return PaperStrategySegmentRow(
        segment_type=segment_type,
        segment_name=segment_name,
        observation_count=len(items),
        probability_observation_count=probability_observation_count,
        return_observation_count=return_observation_count,
        mean_predicted_probability=_mean(
            tuple(item.predicted_probability for item in probability_items),
        ),
        observed_frequency=_mean(
            tuple(item.actual_outcome_value for item in probability_items),
        ),
        brier_score=_mean(tuple(_brier_value(item) for item in probability_items)),
        mean_paper_return_ratio=_mean(
            tuple(item.paper_return_ratio for item in return_items),
        ),
        positive_return_rate=_positive_return_rate(
            tuple(item.paper_return_ratio for item in return_items),
        ),
        status=_segment_status(
            probability_observation_count=probability_observation_count,
            min_segment_observations=min_segment_observations,
        ),
    )


def _has_probability_values(item: PaperForecastEvidenceObservation) -> bool:
    return item.predicted_probability is not None and item.actual_outcome_value is not None


def _brier_value(item: PaperForecastEvidenceObservation) -> Decimal:
    return (item.predicted_probability - item.actual_outcome_value) ** 2


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / Decimal(len(values)))


def _positive_return_rate(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    positive_count = sum(1 for value in values if value > ZERO)
    return _quantize_ratio(Decimal(positive_count) / Decimal(len(values)))


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


def _normalize_rows(
    rows: tuple[PaperStrategySegmentRow, ...],
) -> tuple[PaperStrategySegmentRow, ...]:
    try:
        normalized_rows = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    previous_key: tuple[str, str] | None = None
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized_rows:
        if type(row) is not PaperStrategySegmentRow:
            raise ValueError("rows must contain PaperStrategySegmentRow values")
        row_key = (row.segment_type, row.segment_name)
        if row_key in seen_keys:
            raise ValueError(
                "rows must not contain duplicate (segment_type, segment_name) pairs",
            )
        if previous_key is not None and row_key < previous_key:
            raise ValueError("rows must be sorted by (segment_type, segment_name)")
        seen_keys.add(row_key)
        previous_key = row_key
    return normalized_rows


def _count_segment_rows(
    rows: tuple[PaperStrategySegmentRow, ...],
) -> tuple[int, int]:
    strategy_segment_count = 0
    risk_tag_segment_count = 0
    for row in rows:
        if row.segment_type == "strategy_type":
            strategy_segment_count += 1
        else:
            risk_tag_segment_count += 1
    return strategy_segment_count, risk_tag_segment_count


def _strategy_observation_count(
    rows: tuple[PaperStrategySegmentRow, ...],
) -> int:
    return sum(
        row.observation_count for row in rows if row.segment_type == "strategy_type"
    )


def _segment_status(
    *,
    probability_observation_count: int,
    min_segment_observations: int,
) -> str:
    if probability_observation_count == 0:
        return "segment_return_evidence_observed"
    if probability_observation_count < min_segment_observations:
        return "insufficient_segment_probability_sample"
    return "segment_evidence_observed"


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


def _require_optional_datetime(field_name: str, value: datetime | None) -> None:
    if value is None:
        return
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or None")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)
    _require_ratio_quantum(field_name, value)


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)
    _require_ratio_quantum(field_name, value)
    if value < ZERO or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_ratio_quantum(field_name: str, value: Decimal) -> None:
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


__all__ = (
    "PaperStrategySegmentSummaryConfig",
    "PaperStrategySegmentRow",
    "PaperStrategySegmentSummaryReport",
    "build_paper_strategy_segment_summary_report",
)
