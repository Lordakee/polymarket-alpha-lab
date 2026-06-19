from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


__all__ = (
    "PaperForecastCalibrationBucket",
    "PaperForecastCalibrationConfig",
    "PaperForecastCalibrationReport",
    "build_paper_forecast_calibration_report",
)

RATIO_QUANTUM = Decimal("0.000001")
BUCKET_QUANTUM = Decimal("0.0001")
RATIO_MICRO_UNITS = 1_000_000
ZERO = Decimal("0")
ONE = Decimal("1")

REPORT_STATUSES = (
    "empty_calibration_history",
    "insufficient_calibration_sample",
    "calibration_evidence_observed",
    "calibration_quality_flags",
)


@dataclass(frozen=True)
class PaperForecastCalibrationConfig:
    config_version: str
    probability_bucket_width: Decimal = Decimal("0.1000")
    min_observation_count: int = 30
    max_brier_score: Decimal = Decimal("0.250000")
    max_expected_calibration_error: Decimal = Decimal("0.100000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_bucket_width(
            "probability_bucket_width",
            self.probability_bucket_width,
        )
        _require_nonnegative_int("min_observation_count", self.min_observation_count)
        _require_probability("max_brier_score", self.max_brier_score)
        _require_ratio_quantum("max_brier_score", self.max_brier_score)
        _require_probability(
            "max_expected_calibration_error",
            self.max_expected_calibration_error,
        )
        _require_ratio_quantum(
            "max_expected_calibration_error",
            self.max_expected_calibration_error,
        )


@dataclass(frozen=True)
class PaperForecastCalibrationBucket:
    bucket_label: str
    lower_probability: Decimal
    upper_probability: Decimal
    observation_count: int
    mean_predicted_probability: Decimal
    observed_frequency: Decimal
    bucket_error: Decimal
    bucket_weight: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("bucket_label", self.bucket_label)
        _require_probability("lower_probability", self.lower_probability)
        _require_bucket_quantum("lower_probability", self.lower_probability)
        _require_probability("upper_probability", self.upper_probability)
        _require_bucket_quantum("upper_probability", self.upper_probability)
        if self.upper_probability <= self.lower_probability:
            raise ValueError("upper_probability must be greater than lower_probability")
        _require_positive_int("observation_count", self.observation_count)
        _require_probability(
            "mean_predicted_probability",
            self.mean_predicted_probability,
        )
        _require_ratio_quantum(
            "mean_predicted_probability",
            self.mean_predicted_probability,
        )
        _require_probability("observed_frequency", self.observed_frequency)
        _require_ratio_quantum("observed_frequency", self.observed_frequency)
        _require_probability("bucket_error", self.bucket_error)
        _require_ratio_quantum("bucket_error", self.bucket_error)
        _require_probability("bucket_weight", self.bucket_weight)
        _require_ratio_quantum("bucket_weight", self.bucket_weight)
        if self.bucket_error != _bucket_error(
            self.mean_predicted_probability,
            self.observed_frequency,
        ):
            raise ValueError("bucket_error must match bucket means")
        if self.bucket_label != _bucket_label(
            self.lower_probability,
            self.upper_probability,
        ):
            raise ValueError("bucket_label must match bucket bounds")


@dataclass(frozen=True)
class PaperForecastCalibrationReport:
    generated_at: datetime
    config_version: str
    observation_count: int
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    brier_score: Decimal | None
    mean_absolute_error: Decimal | None
    expected_calibration_error: Decimal | None
    max_bucket_error: Decimal | None
    bucket_count: int
    status: str
    buckets: tuple[PaperForecastCalibrationBucket, ...]
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
        _require_nonnegative_int("observation_count", self.observation_count)
        _require_optional_probability("brier_score", self.brier_score)
        _require_optional_ratio_quantum("brier_score", self.brier_score)
        _require_optional_probability(
            "mean_absolute_error",
            self.mean_absolute_error,
        )
        _require_optional_ratio_quantum(
            "mean_absolute_error",
            self.mean_absolute_error,
        )
        _require_optional_probability(
            "expected_calibration_error",
            self.expected_calibration_error,
        )
        _require_optional_ratio_quantum(
            "expected_calibration_error",
            self.expected_calibration_error,
        )
        _require_optional_probability("max_bucket_error", self.max_bucket_error)
        _require_optional_ratio_quantum("max_bucket_error", self.max_bucket_error)
        _require_nonnegative_int("bucket_count", self.bucket_count)
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known forecast calibration report status")
        object.__setattr__(
            self,
            "buckets",
            _normalize_buckets(self.buckets),
        )
        if self.bucket_count != len(self.buckets):
            raise ValueError("bucket_count must equal buckets length")
        _require_bucket_ranges(self.buckets)
        if self.observation_count == 0:
            if self.first_observed_at is not None or self.last_observed_at is not None:
                raise ValueError("observed_at bounds must be absent without observations")
            if self.buckets != ():
                raise ValueError("buckets must be empty without observations")
            if self.status != "empty_calibration_history":
                raise ValueError("status must match empty calibration history")
            for field_name in (
                "brier_score",
                "mean_absolute_error",
                "expected_calibration_error",
                "max_bucket_error",
            ):
                if getattr(self, field_name) is not None:
                    raise ValueError(f"{field_name} must be absent without observations")
        else:
            if self.first_observed_at is None or self.last_observed_at is None:
                raise ValueError("observed_at bounds are required with observations")
            if self.first_observed_at > self.last_observed_at:
                raise ValueError("observed_at bounds must be chronological")
            if self.status == "empty_calibration_history":
                raise ValueError("status must match nonempty calibration history")
            if (
                sum((bucket.observation_count for bucket in self.buckets), 0)
                != self.observation_count
            ):
                raise ValueError("bucket observation_count values must sum to observation_count")
            if (
                sum((bucket.bucket_weight for bucket in self.buckets), ZERO)
                != ONE.quantize(RATIO_QUANTUM)
            ):
                raise ValueError("bucket weights must sum to 1.000000")
            if tuple(bucket.bucket_weight for bucket in self.buckets) != (
                _bucket_weights_from_counts(
                    tuple(bucket.observation_count for bucket in self.buckets)
                )
            ):
                raise ValueError("bucket weights must match bucket observation_count values")
            for field_name in (
                "brier_score",
                "mean_absolute_error",
                "expected_calibration_error",
                "max_bucket_error",
            ):
                if getattr(self, field_name) is None:
                    raise ValueError(f"{field_name} is required with observations")
            if self.expected_calibration_error != _expected_calibration_error(
                self.buckets,
            ):
                raise ValueError("expected_calibration_error must match buckets")
            if self.max_bucket_error != _max_or_none(
                bucket.bucket_error for bucket in self.buckets
            ):
                raise ValueError("max_bucket_error must match buckets")
            if self.brier_score > self.mean_absolute_error:
                raise ValueError(
                    "brier_score must not exceed mean_absolute_error",
                )
            if _exceeds_ratio_quantum_tolerance(
                self.expected_calibration_error,
                self.mean_absolute_error,
            ):
                raise ValueError(
                    "mean_absolute_error must be at least expected_calibration_error",
                )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_forecast_calibration_report(
    observations: Iterable[PaperForecastEvidenceObservation],
    *,
    config: PaperForecastCalibrationConfig,
    generated_at: datetime,
) -> PaperForecastCalibrationReport:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    if not isinstance(config, PaperForecastCalibrationConfig):
        raise ValueError("config must be a PaperForecastCalibrationConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    try:
        observation_items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in observation_items:
        if not isinstance(observation, PaperForecastEvidenceObservation):
            raise ValueError(
                "observations must contain PaperForecastEvidenceObservation values"
            )
        if observation.paper_only is not True:
            raise ValueError("observations must be paper-only")

    probability_items = tuple(
        item
        for item in observation_items
        if item.predicted_probability is not None and item.actual_outcome_value is not None
    )
    sorted_probability_items = tuple(
        sorted(probability_items, key=lambda item: _as_utc(item.observed_at))
    )
    buckets = _build_buckets(
        sorted_probability_items,
        config.probability_bucket_width,
    )
    brier_score = _mean(_brier_loss(item) for item in probability_items)
    mean_absolute_error = _mean(_absolute_error(item) for item in probability_items)
    expected_calibration_error = _expected_calibration_error(buckets)
    max_bucket_error = _max_or_none(bucket.bucket_error for bucket in buckets)
    status = _report_status(
        observation_count=len(probability_items),
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        config=config,
    )

    return PaperForecastCalibrationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=len(probability_items),
        first_observed_at=(
            _as_utc(sorted_probability_items[0].observed_at)
            if sorted_probability_items
            else None
        ),
        last_observed_at=(
            _as_utc(sorted_probability_items[-1].observed_at)
            if sorted_probability_items
            else None
        ),
        brier_score=brier_score,
        mean_absolute_error=mean_absolute_error,
        expected_calibration_error=expected_calibration_error,
        max_bucket_error=max_bucket_error,
        bucket_count=len(buckets),
        status=status,
        buckets=buckets,
    )


def _build_buckets(
    probability_items: tuple[PaperForecastEvidenceObservation, ...],
    bucket_width: Decimal,
) -> tuple[PaperForecastCalibrationBucket, ...]:
    bucket_values: dict[tuple[Decimal, Decimal], list[PaperForecastEvidenceObservation]] = {}
    for item in probability_items:
        lower_probability, upper_probability = _bucket_bounds(
            item.predicted_probability,
            bucket_width,
        )
        bucket_values.setdefault((lower_probability, upper_probability), []).append(item)

    bucket_rows: list[PaperForecastCalibrationBucket] = []
    sorted_bucket_values = tuple(sorted(bucket_values.items()))
    bucket_weights = _bucket_weights_from_counts(
        tuple(len(items) for _, items in sorted_bucket_values),
    )
    for ((lower_probability, upper_probability), items), bucket_weight in zip(
        sorted_bucket_values,
        bucket_weights,
        strict=True,
    ):
        predicted_values = tuple(item.predicted_probability for item in items)
        actual_values = tuple(item.actual_outcome_value for item in items)
        mean_predicted_probability = _mean(predicted_values)
        observed_frequency = _mean(actual_values)
        bucket_rows.append(
            PaperForecastCalibrationBucket(
                bucket_label=_bucket_label(lower_probability, upper_probability),
                lower_probability=lower_probability,
                upper_probability=upper_probability,
                observation_count=len(items),
                mean_predicted_probability=mean_predicted_probability,
                observed_frequency=observed_frequency,
                bucket_error=_bucket_error(
                    mean_predicted_probability,
                    observed_frequency,
                ),
                bucket_weight=bucket_weight,
            )
        )
    return tuple(bucket_rows)


def _bucket_weights_from_counts(counts: tuple[int, ...]) -> tuple[Decimal, ...]:
    if not counts:
        return ()
    for count in counts:
        _require_positive_int("bucket observation count", count)

    total = sum(counts)
    base_units: list[int] = []
    remainders: list[tuple[int, int]] = []
    for index, count in enumerate(counts):
        numerator = count * RATIO_MICRO_UNITS
        units, remainder = divmod(numerator, total)
        base_units.append(units)
        remainders.append((remainder, index))

    units_to_allocate = RATIO_MICRO_UNITS - sum(base_units)
    for _, index in sorted(remainders, key=lambda item: (-item[0], item[1]))[
        :units_to_allocate
    ]:
        base_units[index] += 1

    return tuple(
        _quantize_ratio(Decimal(units) / Decimal(RATIO_MICRO_UNITS))
        for units in base_units
    )


def _bucket_bounds(
    probability: Decimal,
    bucket_width: Decimal,
) -> tuple[Decimal, Decimal]:
    if probability == ONE:
        steps = int((ONE / bucket_width).to_integral_value(rounding="ROUND_CEILING"))
        lower_probability = _quantize_bucket(bucket_width * (steps - 1))
        return lower_probability, ONE.quantize(BUCKET_QUANTUM)
    steps = int((probability / bucket_width).to_integral_value(rounding="ROUND_FLOOR"))
    lower_probability = _quantize_bucket(bucket_width * steps)
    upper_probability = lower_probability + bucket_width
    if upper_probability > ONE:
        upper_probability = ONE
    return _quantize_bucket(lower_probability), _quantize_bucket(upper_probability)


def _bucket_label(lower_probability: Decimal, upper_probability: Decimal) -> str:
    return f"{lower_probability.quantize(BUCKET_QUANTUM)}-{upper_probability.quantize(BUCKET_QUANTUM)}"


def _brier_loss(item: PaperForecastEvidenceObservation) -> Decimal:
    return (item.predicted_probability - item.actual_outcome_value) ** 2


def _absolute_error(item: PaperForecastEvidenceObservation) -> Decimal:
    return abs(item.predicted_probability - item.actual_outcome_value)


def _bucket_error(
    mean_predicted_probability: Decimal,
    observed_frequency: Decimal,
) -> Decimal:
    return _quantize_ratio(abs(mean_predicted_probability - observed_frequency))


def _expected_calibration_error(
    buckets: tuple[PaperForecastCalibrationBucket, ...],
) -> Decimal | None:
    if not buckets:
        return None
    return _quantize_ratio(
        sum((bucket.bucket_weight * bucket.bucket_error for bucket in buckets), ZERO)
    )


def _exceeds_ratio_quantum_tolerance(value: Decimal, upper_bound: Decimal) -> bool:
    return value - upper_bound > RATIO_QUANTUM


def _report_status(
    *,
    observation_count: int,
    brier_score: Decimal | None,
    expected_calibration_error: Decimal | None,
    config: PaperForecastCalibrationConfig,
) -> str:
    if observation_count == 0:
        return "empty_calibration_history"
    if observation_count < config.min_observation_count:
        return "insufficient_calibration_sample"
    if (
        brier_score > config.max_brier_score
        or expected_calibration_error > config.max_expected_calibration_error
    ):
        return "calibration_quality_flags"
    return "calibration_evidence_observed"


def _mean(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_ratio(sum(items, ZERO) / Decimal(len(items)))


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_ratio(max(items))


def _normalize_buckets(
    value: tuple[PaperForecastCalibrationBucket, ...],
) -> tuple[PaperForecastCalibrationBucket, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("buckets must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("buckets must be an iterable") from exc
    if not all(isinstance(item, PaperForecastCalibrationBucket) for item in items):
        raise ValueError("buckets must contain PaperForecastCalibrationBucket values")
    return items


def _require_bucket_ranges(
    buckets: tuple[PaperForecastCalibrationBucket, ...],
) -> None:
    bucket_identities = tuple(
        (bucket.lower_probability, bucket.upper_probability) for bucket in buckets
    )
    if len(set(bucket_identities)) != len(bucket_identities):
        raise ValueError("bucket identity must be unique")
    if tuple(sorted(buckets, key=lambda item: item.lower_probability)) != buckets:
        raise ValueError("buckets must be sorted by lower_probability")

    previous_bucket: PaperForecastCalibrationBucket | None = None
    for bucket in buckets:
        if (
            previous_bucket is not None
            and bucket.lower_probability < previous_bucket.upper_probability
        ):
            raise ValueError("bucket ranges must not overlap")
        previous_bucket = bucket


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_ratio(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_ratio(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_nonnegative_ratio(field_name, value)


def _require_optional_probability(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_probability(field_name, value)


def _require_probability(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_ratio_quantum(field_name: str, value: Decimal) -> None:
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_optional_ratio_quantum(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_ratio_quantum(field_name, value)


def _require_bucket_quantum(field_name: str, value: Decimal) -> None:
    if value != value.quantize(BUCKET_QUANTUM):
        raise ValueError(f"{field_name} must align to {BUCKET_QUANTUM}")


def _require_bucket_width(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO or value > ONE:
        raise ValueError(f"{field_name} must be greater than 0 and at most 1")
    if value < BUCKET_QUANTUM:
        raise ValueError(f"{field_name} must be at least {BUCKET_QUANTUM}")
    if value != value.quantize(BUCKET_QUANTUM):
        raise ValueError(f"{field_name} must align to {BUCKET_QUANTUM}")


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_finite_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


def _quantize_bucket(value: Decimal) -> Decimal:
    _require_finite_decimal("bucket", value)
    return value.quantize(BUCKET_QUANTUM)
