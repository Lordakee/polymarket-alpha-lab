import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


__all__ = (
    "PaperForecastEvidenceBucket",
    "PaperForecastEvidenceConfig",
    "PaperForecastEvidenceGateResult",
    "PaperForecastEvidenceLog",
    "PaperForecastEvidenceObservation",
    "PaperForecastEvidenceReport",
    "build_paper_forecast_evidence_report",
)

RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

GATE_NAMES = (
    "data_integrity",
    "sample_size",
    "probability_quality",
    "executable_edge_quality",
    "residual_exposure",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "incomplete_data",
    "insufficient_evidence",
    "blocked_by_quality",
    "paper_review_ready",
)


@dataclass(frozen=True)
class PaperForecastEvidenceConfig:
    config_version: str
    min_probability_observations: int = 30
    min_edge_observations: int = 30
    probability_bucket_width: Decimal = Decimal("0.2000")
    max_mean_probability_loss: Decimal = Decimal("0.2500")
    max_bucket_error: Decimal = Decimal("0.2000")
    max_mean_edge_gap_ratio: Decimal = Decimal("0.0500")
    min_positive_edge_hit_rate: Decimal = Decimal("0.5000")
    max_residual_exposure_ratio: Decimal = Decimal("0.1000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_probability_observations",
            self.min_probability_observations,
        )
        _require_nonnegative_int("min_edge_observations", self.min_edge_observations)
        _require_probability_bucket_width(
            "probability_bucket_width",
            self.probability_bucket_width,
        )
        _require_nonnegative_decimal(
            "max_mean_probability_loss",
            self.max_mean_probability_loss,
        )
        _require_nonnegative_decimal("max_bucket_error", self.max_bucket_error)
        _require_nonnegative_decimal(
            "max_mean_edge_gap_ratio",
            self.max_mean_edge_gap_ratio,
        )
        _require_probability_decimal(
            "min_positive_edge_hit_rate",
            self.min_positive_edge_hit_rate,
        )
        _require_probability_decimal(
            "max_residual_exposure_ratio",
            self.max_residual_exposure_ratio,
        )


@dataclass(frozen=True)
class PaperForecastEvidenceObservation:
    observed_at: datetime
    source_packet_id: str
    condition_id: str
    token_id: str
    market_slug: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    predicted_probability: Decimal | None = None
    actual_outcome_value: Decimal | None = None
    theoretical_edge_ratio: Decimal | None = None
    executable_edge_ratio: Decimal | None = None
    fill_probability: Decimal | None = None
    residual_exposure_ratio: Decimal | None = None
    paper_return_ratio: Decimal | None = None
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _as_utc(self.observed_at))
        for field_name in (
            "source_packet_id",
            "condition_id",
            "token_id",
            "market_slug",
            "strategy_type",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "risk_tags",
            _normalize_risk_tags(self.risk_tags),
        )
        _require_optional_probability_decimal(
            "predicted_probability",
            self.predicted_probability,
        )
        if self.actual_outcome_value is not None:
            _require_zero_one_decimal("actual_outcome_value", self.actual_outcome_value)
        _require_optional_finite_decimal(
            "theoretical_edge_ratio",
            self.theoretical_edge_ratio,
        )
        _require_optional_finite_decimal(
            "executable_edge_ratio",
            self.executable_edge_ratio,
        )
        _require_optional_probability_decimal("fill_probability", self.fill_probability)
        _require_optional_probability_decimal(
            "residual_exposure_ratio",
            self.residual_exposure_ratio,
        )
        _require_optional_finite_decimal("paper_return_ratio", self.paper_return_ratio)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if _some_probability_role(self) and not _complete_probability_role(self):
            raise ValueError("probability evidence role must be complete")
        if _some_edge_role(self) and not _complete_edge_role(self):
            raise ValueError("executable edge evidence role must be complete")
        if not _complete_probability_role(self) and not _complete_edge_role(self):
            raise ValueError("evidence observation must include a complete role")


@dataclass(frozen=True)
class PaperForecastEvidenceBucket:
    bucket_label: str
    lower_probability: Decimal
    upper_probability: Decimal
    observation_count: int
    mean_predicted_probability: Decimal
    observed_frequency: Decimal
    bucket_error: Decimal
    mean_probability_loss: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("bucket_label", self.bucket_label)
        _require_probability_decimal("lower_probability", self.lower_probability)
        _require_probability_decimal("upper_probability", self.upper_probability)
        if self.upper_probability <= self.lower_probability:
            raise ValueError("upper_probability must be greater than lower_probability")
        _require_positive_int("observation_count", self.observation_count)
        _require_probability_decimal(
            "mean_predicted_probability",
            self.mean_predicted_probability,
        )
        _require_probability_decimal("observed_frequency", self.observed_frequency)
        _require_nonnegative_decimal("bucket_error", self.bucket_error)
        _require_nonnegative_decimal(
            "mean_probability_loss",
            self.mean_probability_loss,
        )


@dataclass(frozen=True)
class PaperForecastEvidenceGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known forecast evidence gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known forecast evidence gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class PaperForecastEvidenceReport:
    generated_at: datetime
    config_version: str
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    observation_count: int
    probability_observation_count: int
    edge_observation_count: int
    unique_market_count: int
    unique_strategy_count: int
    unique_risk_tag_count: int
    mean_probability_loss: Decimal | None
    worst_bucket_error: Decimal | None
    mean_edge_gap_ratio: Decimal | None
    positive_edge_hit_rate: Decimal | None
    worst_residual_exposure_ratio: Decimal | None
    status: str
    gate_results: tuple[PaperForecastEvidenceGateResult, ...]
    buckets: tuple[PaperForecastEvidenceBucket, ...]
    paper_only: bool = True

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
            "observation_count",
            "probability_observation_count",
            "edge_observation_count",
            "unique_market_count",
            "unique_strategy_count",
            "unique_risk_tag_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_nonnegative_decimal(
            "mean_probability_loss",
            self.mean_probability_loss,
        )
        _require_optional_nonnegative_decimal(
            "worst_bucket_error",
            self.worst_bucket_error,
        )
        _require_optional_nonnegative_decimal(
            "mean_edge_gap_ratio",
            self.mean_edge_gap_ratio,
        )
        _require_optional_probability_decimal(
            "positive_edge_hit_rate",
            self.positive_edge_hit_rate,
        )
        _require_optional_probability_decimal(
            "worst_residual_exposure_ratio",
            self.worst_residual_exposure_ratio,
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known forecast evidence report status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                PaperForecastEvidenceGateResult,
            ),
        )
        object.__setattr__(
            self,
            "buckets",
            _normalize_typed_tuple(
                "buckets",
                self.buckets,
                PaperForecastEvidenceBucket,
            ),
        )
        if tuple(gate.gate_name for gate in self.gate_results) != GATE_NAMES:
            raise ValueError("gate_results must contain the five forecast evidence gates")
        if tuple(sorted(self.buckets, key=lambda item: item.lower_probability)) != self.buckets:
            raise ValueError("buckets must be sorted by lower_probability")
        if self.observation_count == 0:
            if self.first_observed_at is not None or self.last_observed_at is not None:
                raise ValueError("observed_at bounds must be absent without observations")
            if self.buckets != ():
                raise ValueError("buckets must be empty without observations")
            if any(gate.status != "incomplete" for gate in self.gate_results):
                raise ValueError("gate_results must be incomplete without observations")
        else:
            if self.first_observed_at is None or self.last_observed_at is None:
                raise ValueError("observed_at bounds are required with observations")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")


@dataclass(frozen=True)
class PaperForecastEvidenceLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperForecastEvidenceReport) -> None:
        if not isinstance(report, PaperForecastEvidenceReport):
            raise ValueError("report must be a PaperForecastEvidenceReport")
        _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_forecast_evidence_report(
    observations: Iterable[PaperForecastEvidenceObservation],
    *,
    config: PaperForecastEvidenceConfig,
    generated_at: datetime,
) -> PaperForecastEvidenceReport:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    if not isinstance(config, PaperForecastEvidenceConfig):
        raise ValueError("config must be a PaperForecastEvidenceConfig")
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

    sorted_observations = tuple(
        sorted(observation_items, key=lambda item: _as_utc(item.observed_at))
    )
    seen_keys: set[tuple[datetime, str, str]] = set()
    for observation in sorted_observations:
        evidence_key = (
            _as_utc(observation.observed_at),
            observation.token_id,
            observation.source_packet_id,
        )
        if evidence_key in seen_keys:
            raise ValueError("duplicate evidence keys are not allowed")
        seen_keys.add(evidence_key)

    probability_items = tuple(
        item for item in sorted_observations if _complete_probability_role(item)
    )
    edge_items = tuple(item for item in sorted_observations if _complete_edge_role(item))
    buckets = _build_buckets(probability_items, config.probability_bucket_width)
    probability_losses = tuple(_probability_loss(item) for item in probability_items)
    edge_gaps = tuple(_edge_gap(item) for item in edge_items)

    mean_probability_loss = _mean_decimal(probability_losses)
    worst_bucket_error = _max_optional(bucket.bucket_error for bucket in buckets)
    mean_edge_gap_ratio = _mean_decimal(edge_gaps)
    positive_edge_hit_rate = _positive_edge_hit_rate(edge_items)
    worst_residual_exposure_ratio = _max_optional(
        item.residual_exposure_ratio for item in edge_items
    )
    if worst_residual_exposure_ratio is not None:
        worst_residual_exposure_ratio = _quantize_ratio(worst_residual_exposure_ratio)

    gate_results = _build_gate_results(
        observation_count=len(sorted_observations),
        probability_observation_count=len(probability_items),
        edge_observation_count=len(edge_items),
        mean_probability_loss=mean_probability_loss,
        worst_bucket_error=worst_bucket_error,
        mean_edge_gap_ratio=mean_edge_gap_ratio,
        positive_edge_hit_rate=positive_edge_hit_rate,
        worst_residual_exposure_ratio=worst_residual_exposure_ratio,
        config=config,
    )
    status = _report_status(len(sorted_observations), gate_results)

    return PaperForecastEvidenceReport(
        generated_at=generated_at,
        config_version=config.config_version,
        first_observed_at=(
            _as_utc(sorted_observations[0].observed_at) if sorted_observations else None
        ),
        last_observed_at=(
            _as_utc(sorted_observations[-1].observed_at) if sorted_observations else None
        ),
        observation_count=len(sorted_observations),
        probability_observation_count=len(probability_items),
        edge_observation_count=len(edge_items),
        unique_market_count=len({item.market_slug for item in sorted_observations}),
        unique_strategy_count=len({item.strategy_type for item in sorted_observations}),
        unique_risk_tag_count=len(
            {risk_tag for item in sorted_observations for risk_tag in item.risk_tags}
        ),
        mean_probability_loss=mean_probability_loss,
        worst_bucket_error=worst_bucket_error,
        mean_edge_gap_ratio=mean_edge_gap_ratio,
        positive_edge_hit_rate=positive_edge_hit_rate,
        worst_residual_exposure_ratio=worst_residual_exposure_ratio,
        status=status,
        gate_results=gate_results,
        buckets=buckets,
    )


def _build_buckets(
    probability_items: tuple[PaperForecastEvidenceObservation, ...],
    bucket_width: Decimal,
) -> tuple[PaperForecastEvidenceBucket, ...]:
    bucket_values: dict[tuple[Decimal, Decimal], list[PaperForecastEvidenceObservation]] = {}
    for item in probability_items:
        lower_probability, upper_probability = _bucket_bounds(
            item.predicted_probability,
            bucket_width,
        )
        bucket_values.setdefault((lower_probability, upper_probability), []).append(item)

    bucket_rows: list[PaperForecastEvidenceBucket] = []
    for (lower_probability, upper_probability), items in sorted(bucket_values.items()):
        predicted_values = tuple(item.predicted_probability for item in items)
        actual_values = tuple(item.actual_outcome_value for item in items)
        loss_values = tuple(_probability_loss(item) for item in items)
        mean_predicted_probability = _mean_decimal(predicted_values)
        observed_frequency = _mean_decimal(actual_values)
        bucket_rows.append(
            PaperForecastEvidenceBucket(
                bucket_label=_bucket_label(lower_probability, upper_probability),
                lower_probability=lower_probability,
                upper_probability=upper_probability,
                observation_count=len(items),
                mean_predicted_probability=mean_predicted_probability,
                observed_frequency=observed_frequency,
                bucket_error=_quantize_ratio(
                    abs(mean_predicted_probability - observed_frequency)
                ),
                mean_probability_loss=_mean_decimal(loss_values),
            )
        )
    return tuple(bucket_rows)


def _bucket_bounds(
    probability: Decimal,
    bucket_width: Decimal,
) -> tuple[Decimal, Decimal]:
    if probability == ONE:
        steps = int((ONE / bucket_width).to_integral_value(rounding="ROUND_CEILING"))
        lower_probability = _quantize_ratio(bucket_width * (steps - 1))
        return lower_probability, ONE.quantize(RATIO_QUANTUM)
    steps = int((probability / bucket_width).to_integral_value(rounding="ROUND_FLOOR"))
    lower_probability = _quantize_ratio(bucket_width * steps)
    upper_probability = lower_probability + bucket_width
    if upper_probability > ONE:
        upper_probability = ONE
    return _quantize_ratio(lower_probability), _quantize_ratio(upper_probability)


def _bucket_label(lower_probability: Decimal, upper_probability: Decimal) -> str:
    return f"{lower_probability.quantize(RATIO_QUANTUM)}-{upper_probability.quantize(RATIO_QUANTUM)}"


def _build_gate_results(
    *,
    observation_count: int,
    probability_observation_count: int,
    edge_observation_count: int,
    mean_probability_loss: Decimal | None,
    worst_bucket_error: Decimal | None,
    mean_edge_gap_ratio: Decimal | None,
    positive_edge_hit_rate: Decimal | None,
    worst_residual_exposure_ratio: Decimal | None,
    config: PaperForecastEvidenceConfig,
) -> tuple[PaperForecastEvidenceGateResult, ...]:
    if observation_count == 0:
        return tuple(
            PaperForecastEvidenceGateResult(
                gate_name=gate_name,
                status="incomplete",
                message="No paper forecast evidence observations are available.",
            )
            for gate_name in GATE_NAMES
        )

    sample_passes = (
        probability_observation_count >= config.min_probability_observations
        and edge_observation_count >= config.min_edge_observations
    )
    probability_complete = mean_probability_loss is not None and worst_bucket_error is not None
    probability_passes = (
        probability_complete
        and mean_probability_loss <= config.max_mean_probability_loss
        and worst_bucket_error <= config.max_bucket_error
    )
    edge_complete = (
        mean_edge_gap_ratio is not None
        and positive_edge_hit_rate is not None
        and worst_residual_exposure_ratio is not None
    )
    edge_passes = (
        edge_complete
        and mean_edge_gap_ratio <= config.max_mean_edge_gap_ratio
        and positive_edge_hit_rate >= config.min_positive_edge_hit_rate
    )
    residual_passes = (
        edge_complete
        and worst_residual_exposure_ratio <= config.max_residual_exposure_ratio
    )

    return (
        PaperForecastEvidenceGateResult(
            gate_name="data_integrity",
            status="pass",
            message="Paper forecast evidence observations are sorted and duplicate-free.",
            observed_value=observation_count,
            threshold=1,
        ),
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="pass" if sample_passes else "fail",
            message=(
                "Probability and executable-edge observation counts meet thresholds."
                if sample_passes
                else "Probability or executable-edge observation count is below threshold."
            ),
            observed_value=(
                f"probability_observation_count={probability_observation_count}; "
                f"edge_observation_count={edge_observation_count}"
            ),
            threshold=(
                f"min_probability_observations={config.min_probability_observations}; "
                f"min_edge_observations={config.min_edge_observations}"
            ),
        ),
        PaperForecastEvidenceGateResult(
            gate_name="probability_quality",
            status=(
                "pass"
                if probability_passes
                else ("fail" if probability_complete else "incomplete")
            ),
            message=(
                "Probability loss and bucket error are within thresholds."
                if probability_passes
                else (
                    "Probability loss or bucket error breaches threshold."
                    if probability_complete
                    else "No complete probability evidence observations are available."
                )
            ),
            observed_value=(
                f"mean_probability_loss={mean_probability_loss}; "
                f"worst_bucket_error={worst_bucket_error}"
                if probability_complete
                else None
            ),
            threshold=(
                f"max_mean_probability_loss={config.max_mean_probability_loss}; "
                f"max_bucket_error={config.max_bucket_error}"
            ),
        ),
        PaperForecastEvidenceGateResult(
            gate_name="executable_edge_quality",
            status="pass" if edge_passes else ("fail" if edge_complete else "incomplete"),
            message=(
                "Executable-edge gap and hit rate are within thresholds."
                if edge_passes
                else (
                    "Executable-edge gap or hit rate breaches threshold."
                    if edge_complete
                    else "No complete executable-edge evidence observations are available."
                )
            ),
            observed_value=(
                f"mean_edge_gap_ratio={mean_edge_gap_ratio}; "
                f"positive_edge_hit_rate={positive_edge_hit_rate}"
                if edge_complete
                else None
            ),
            threshold=(
                f"max_mean_edge_gap_ratio={config.max_mean_edge_gap_ratio}; "
                f"min_positive_edge_hit_rate={config.min_positive_edge_hit_rate}"
            ),
        ),
        PaperForecastEvidenceGateResult(
            gate_name="residual_exposure",
            status=(
                "pass"
                if residual_passes
                else ("fail" if edge_complete else "incomplete")
            ),
            message=(
                "Residual exposure is within threshold."
                if residual_passes
                else (
                    "Residual exposure breaches threshold."
                    if edge_complete
                    else "No complete executable-edge evidence observations are available."
                )
            ),
            observed_value=worst_residual_exposure_ratio if edge_complete else None,
            threshold=config.max_residual_exposure_ratio,
        ),
    )


def _report_status(
    observation_count: int,
    gate_results: tuple[PaperForecastEvidenceGateResult, ...],
) -> str:
    gates = {gate.gate_name: gate for gate in gate_results}
    if observation_count == 0 or gates["data_integrity"].status == "incomplete":
        return "incomplete_data"
    if (
        gates["probability_quality"].status == "fail"
        or gates["executable_edge_quality"].status == "fail"
        or gates["residual_exposure"].status == "fail"
    ):
        return "blocked_by_quality"
    if gates["sample_size"].status == "fail" or any(
        gate.status == "incomplete" for gate in gate_results if gate.gate_name != "data_integrity"
    ):
        return "insufficient_evidence"
    return "paper_review_ready"


def _probability_loss(item: PaperForecastEvidenceObservation) -> Decimal:
    return _quantize_ratio((item.predicted_probability - item.actual_outcome_value) ** 2)


def _edge_gap(item: PaperForecastEvidenceObservation) -> Decimal:
    return _quantize_ratio(max(item.theoretical_edge_ratio - item.executable_edge_ratio, ZERO))


def _positive_edge_hit_rate(
    edge_items: tuple[PaperForecastEvidenceObservation, ...],
) -> Decimal | None:
    if not edge_items:
        return None
    positive_count = sum(1 for item in edge_items if item.paper_return_ratio > ZERO)
    return _quantize_ratio(Decimal(positive_count) / Decimal(len(edge_items)))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_ratio(sum(items, ZERO) / Decimal(len(items)))


def _max_optional(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(item for item in values if item is not None)
    if not items:
        return None
    return _quantize_ratio(max(items))


def _complete_probability_role(item: PaperForecastEvidenceObservation) -> bool:
    return item.predicted_probability is not None and item.actual_outcome_value is not None


def _some_probability_role(item: PaperForecastEvidenceObservation) -> bool:
    return item.predicted_probability is not None or item.actual_outcome_value is not None


def _complete_edge_role(item: PaperForecastEvidenceObservation) -> bool:
    return (
        item.theoretical_edge_ratio is not None
        and item.executable_edge_ratio is not None
        and item.fill_probability is not None
        and item.residual_exposure_ratio is not None
        and item.paper_return_ratio is not None
    )


def _some_edge_role(item: PaperForecastEvidenceObservation) -> bool:
    return (
        item.theoretical_edge_ratio is not None
        or item.executable_edge_ratio is not None
        or item.fill_probability is not None
        or item.residual_exposure_ratio is not None
        or item.paper_return_ratio is not None
    )


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


def _normalize_risk_tags(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("risk_tags must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("risk_tags must be an iterable of strings") from exc
    if not items:
        raise ValueError("risk_tags must contain at least one value")
    for item in items:
        _require_canonical_string("risk_tags", item)
    return items


def _normalize_typed_tuple(
    field_name: str,
    value: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not all(isinstance(item, expected_type) for item in items):
        raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


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


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_zero_one_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")


def _require_probability_bucket_width(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO or value > ONE:
        raise ValueError(f"{field_name} must be greater than 0 and at most 1")
    if value < RATIO_QUANTUM:
        raise ValueError(f"{field_name} must be at least {RATIO_QUANTUM}")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_gate_value(field_name: str, value: Decimal | int | str | None) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, Decimal):
        _require_finite_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_finite_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


def _validate_report_tree(report: PaperForecastEvidenceReport) -> None:
    gate_results = tuple(
        PaperForecastEvidenceGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    buckets = tuple(
        PaperForecastEvidenceBucket(
            bucket_label=bucket.bucket_label,
            lower_probability=bucket.lower_probability,
            upper_probability=bucket.upper_probability,
            observation_count=bucket.observation_count,
            mean_predicted_probability=bucket.mean_predicted_probability,
            observed_frequency=bucket.observed_frequency,
            bucket_error=bucket.bucket_error,
            mean_probability_loss=bucket.mean_probability_loss,
        )
        for bucket in report.buckets
    )
    PaperForecastEvidenceReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        first_observed_at=report.first_observed_at,
        last_observed_at=report.last_observed_at,
        observation_count=report.observation_count,
        probability_observation_count=report.probability_observation_count,
        edge_observation_count=report.edge_observation_count,
        unique_market_count=report.unique_market_count,
        unique_strategy_count=report.unique_strategy_count,
        unique_risk_tag_count=report.unique_risk_tag_count,
        mean_probability_loss=report.mean_probability_loss,
        worst_bucket_error=report.worst_bucket_error,
        mean_edge_gap_ratio=report.mean_edge_gap_ratio,
        positive_edge_hit_rate=report.positive_edge_hit_rate,
        worst_residual_exposure_ratio=report.worst_residual_exposure_ratio,
        status=report.status,
        gate_results=gate_results,
        buckets=buckets,
        paper_only=report.paper_only,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
