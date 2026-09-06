"""Pure settled-outcome evaluation for crypto research forecasts.

The evaluator joins forecast records to resolved outcomes and computes
paired metrics against the market-implied baseline. It is pure: samples
arrive fully materialized (an operator export or a future DB join), and
every exclusion carries an explicit reason code.

Sample JSON schema (CLI ``--samples`` file)::

    {
      "as_of_evaluation_cutoff": "2026-10-01T00:00:00+00:00",
      "pending_count": 3,
      "samples": [
        {
          "condition_id": "0x...",
          "team_id": "crypto_btc",
          "forecast_p_yes": "0.55",
          "market_implied_p_yes": "0.50",
          "actual_outcome": "yes",
          "generated_at": "2026-09-05T12:00:00+00:00",
          "settled_at": "2026-09-20T00:00:00+00:00"
        }
      ]
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
from typing import Any, Mapping, Sequence

from .central_data_contracts import _as_utc


DEFAULT_EPSILON = Decimal("0.001")
DEFAULT_MIN_INDICATIVE = 30
DEFAULT_MIN_COMPARATIVE = 100
CALIBRATION_BUCKET_COUNT = 10


class SettlementVerdict(str, Enum):
    INSUFFICIENT_SAMPLE = "insufficient_sample"
    NO_CONSISTENT_EDGE = "no_consistent_edge"
    INDICATIVE_EDGE = "indicative_edge"
    COMPARATIVE_EDGE = "comparative_edge"


def _canonical_probability(name: str, value: object) -> Decimal:
    if isinstance(value, Decimal):
        number = value
    elif type(value) is str:
        number = Decimal(value)
    else:
        raise ValueError(f"{name} must be a Decimal or decimal string")
    if not number.is_finite() or not Decimal(0) < number < Decimal(1):
        raise ValueError(f"{name} must be strictly between 0 and 1")
    return number


@dataclass(frozen=True)
class SettledForecastSample:
    condition_id: str
    team_id: str
    forecast_p_yes: Decimal
    market_implied_p_yes: Decimal
    actual_outcome: str
    generated_at: datetime
    settled_at: datetime
    event_id: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("condition_id", "team_id"):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        if self.event_id is not None and (
            type(self.event_id) is not str
            or not self.event_id
            or self.event_id.strip() != self.event_id
        ):
            raise ValueError("event_id must be a canonical nonblank string or None")
        object.__setattr__(
            self, "forecast_p_yes", _canonical_probability("forecast_p_yes", self.forecast_p_yes)
        )
        object.__setattr__(
            self,
            "market_implied_p_yes",
            _canonical_probability("market_implied_p_yes", self.market_implied_p_yes),
        )
        if self.actual_outcome not in ("yes", "no"):
            raise ValueError("actual_outcome must be 'yes' or 'no'")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "settled_at", _as_utc("settled_at", self.settled_at))
        if self.settled_at < self.generated_at:
            raise ValueError("settled_at must not precede generated_at")
        for name in ("paper_only", "report_only", "readonly"):
            if getattr(self, name) is not True:
                raise ValueError(f"{name} must be True")


@dataclass(frozen=True)
class SettlementEvaluationConfig:
    as_of_evaluation_cutoff: datetime
    pending_count: int = 0
    log_loss_epsilon: Decimal = DEFAULT_EPSILON
    min_samples_indicative: int = DEFAULT_MIN_INDICATIVE
    min_samples_comparative: int = DEFAULT_MIN_COMPARATIVE

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "as_of_evaluation_cutoff",
            _as_utc("as_of_evaluation_cutoff", self.as_of_evaluation_cutoff),
        )
        for name in ("pending_count", "min_samples_indicative", "min_samples_comparative"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative int")
        if self.min_samples_indicative > self.min_samples_comparative:
            raise ValueError("indicative threshold must not exceed comparative threshold")
        epsilon = self.log_loss_epsilon
        if not isinstance(epsilon, Decimal) or not Decimal(0) < epsilon < Decimal("0.5"):
            raise ValueError("log_loss_epsilon must be between 0 and 0.5")


@dataclass(frozen=True)
class CalibrationBucket:
    lower: Decimal
    upper: Decimal
    count: int
    mean_forecast: Decimal | None
    actual_yes_count: int


@dataclass(frozen=True)
class SettlementHandCheckRow:
    condition_id: str
    team_id: str
    generated_at: datetime
    event_id: str | None
    forecast_p_yes: Decimal
    market_implied_p_yes: Decimal
    actual_outcome: str
    team_squared_error: Decimal
    market_squared_error: Decimal
    team_log_loss: Decimal
    market_log_loss: Decimal


@dataclass(frozen=True)
class SettlementEvaluationReport:
    verdict: SettlementVerdict
    included_count: int
    excluded_count: int
    exclusion_reasons: tuple[tuple[str, int], ...]
    pending_count: int
    coverage: Decimal | None
    team_brier: Decimal | None
    market_brier: Decimal | None
    team_log_loss: Decimal | None
    market_log_loss: Decimal | None
    calibration_buckets: tuple[CalibrationBucket, ...]
    team_counts: tuple[tuple[str, int], ...]
    unique_condition_count: int
    verified_unique_event_count: int
    unknown_event_row_count: int
    event_counts: tuple[tuple[str, int], ...]
    max_verified_event_concentration: Decimal | None
    settlement_lag_min_seconds: Decimal | None
    settlement_lag_median_seconds: Decimal | None
    settlement_lag_max_seconds: Decimal | None
    hand_check_rows: tuple[SettlementHandCheckRow, ...]
    as_of_evaluation_cutoff: datetime
    config_min_indicative: int
    config_min_comparative: int
    limitations: tuple[str, ...] = (
        "uncertainty intervals not yet computed at small samples",
        "drawdown and capital lockup not yet measured",
        "cost-adjusted paper results (fee/slippage/fill sensitivity) arm activates at settled N >= 30",
        "memory-as-context benefit unmeasured until memory-gated handoffs settle",
        "forecast revision history not tracked; first-recorded generated_at used",
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.verdict) is not SettlementVerdict:
            raise ValueError("verdict must be a SettlementVerdict")
        for name in ("included_count", "excluded_count", "pending_count"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative int")
        for name in (
            "unique_condition_count",
            "verified_unique_event_count",
            "unknown_event_row_count",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative int")
        for name in ("paper_only", "report_only", "readonly"):
            if getattr(self, name) is not True:
                raise ValueError(f"{name} must be True")

    def render(self) -> str:
        lines = [
            "settlement evaluation",
            f"verdict: {self.verdict.value}",
            f"cutoff: {self.as_of_evaluation_cutoff.isoformat()}",
            f"included_samples: {self.included_count}",
            f"excluded_samples: {self.excluded_count}",
            f"pending_unsettled: {self.pending_count}",
        ]
        if self.exclusion_reasons:
            lines.append(
                "exclusions: " + "; ".join(f"{reason}={count}" for reason, count in self.exclusion_reasons)
            )
        for label, value in (
            ("team_brier", self.team_brier),
            ("market_brier", self.market_brier),
            ("team_log_loss", self.team_log_loss),
            ("market_log_loss", self.market_log_loss),
            ("coverage_settled_ratio", self.coverage),
        ):
            lines.append(f"{label}: {format(value, 'f') if value is not None else 'undefined'}")
        lines.extend(
            (
                f"unique_conditions: {self.unique_condition_count}",
                f"verified_unique_events: {self.verified_unique_event_count}",
                f"unknown_event_rows: {self.unknown_event_row_count}",
                "max_verified_event_concentration: "
                + (
                    format(self.max_verified_event_concentration, "f")
                    if self.max_verified_event_concentration is not None
                    else "undefined"
                ),
            )
        )
        if self.event_counts:
            lines.append(
                "verified_events: "
                + ", ".join(f"{event_id}={count}" for event_id, count in self.event_counts)
            )
        for label, value in (
            ("settlement_lag_min_seconds", self.settlement_lag_min_seconds),
            ("settlement_lag_median_seconds", self.settlement_lag_median_seconds),
            ("settlement_lag_max_seconds", self.settlement_lag_max_seconds),
        ):
            lines.append(f"{label}: {format(value, 'f') if value is not None else 'undefined'}")
        lines.append("calibration:")
        for bucket in self.calibration_buckets:
            if bucket.count == 0:
                lines.append(
                    f"  [{format(bucket.lower, 'f')}, {format(bucket.upper, 'f')}): empty"
                )
            else:
                lines.append(
                    f"  [{format(bucket.lower, 'f')}, {format(bucket.upper, 'f')}): "
                    f"n={bucket.count} mean_p={format(bucket.mean_forecast, 'f')} "
                    f"yes={bucket.actual_yes_count}"
                )
        if self.team_counts:
            lines.append("teams: " + ", ".join(f"{team}={count}" for team, count in self.team_counts))
        lines.append("limitations:")
        lines.extend(f"  - {item}" for item in self.limitations)
        return "\n".join(lines)


@dataclass(frozen=True)
class _Exclusion:
    reason: str


def _clip(value: Decimal, epsilon: Decimal) -> Decimal:
    low = epsilon
    high = Decimal(1) - epsilon
    return min(max(value, low), high)


def _log_loss_contribution(probability: Decimal, target: Decimal, epsilon: Decimal) -> Decimal:
    clipped = _clip(probability, epsilon)
    reference = clipped if target == Decimal(1) else Decimal(1) - clipped
    return Decimal(-1) * Decimal(str(_ln(reference)))


def _decimal_seconds(value: timedelta) -> Decimal:
    return (
        Decimal(value.days) * Decimal(86400)
        + Decimal(value.seconds)
        + Decimal(value.microseconds) / Decimal(1_000_000)
    )


def _median(values: Sequence[Decimal]) -> Decimal:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2)


def evaluate_settlement_samples(
    samples: Sequence[Mapping[str, Any] | SettledForecastSample],
    config: SettlementEvaluationConfig,
) -> SettlementEvaluationReport:
    if not isinstance(samples, Sequence):
        raise ValueError("samples must be a sequence")
    included: list[SettledForecastSample] = []
    exclusion_counts: dict[str, int] = {}

    def _exclude(reason: str) -> None:
        exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1

    for raw in samples:
        if isinstance(raw, Mapping):
            try:
                generated = raw["generated_at"]
                settled = raw["settled_at"]
                sample = SettledForecastSample(
                    condition_id=raw["condition_id"],
                    team_id=raw["team_id"],
                    event_id=raw.get("event_id"),
                    forecast_p_yes=Decimal(str(raw["forecast_p_yes"])),
                    market_implied_p_yes=Decimal(str(raw["market_implied_p_yes"])),
                    actual_outcome=raw["actual_outcome"],
                    generated_at=datetime.fromisoformat(generated)
                    if type(generated) is str
                    else generated,
                    settled_at=datetime.fromisoformat(settled)
                    if type(settled) is str
                    else settled,
                )
            except (KeyError, ValueError, TypeError, ArithmeticError):
                _exclude("invalid_sample_contract")
                continue
        elif isinstance(raw, SettledForecastSample):
            sample = raw
        else:
            _exclude("invalid_sample_contract")
            continue
        if sample.generated_at > config.as_of_evaluation_cutoff:
            _exclude("forecast_after_evaluation_cutoff")
            continue
        included.append(sample)

    if included:
        actual_targets = [Decimal(1) if s.actual_outcome == "yes" else Decimal(0) for s in included]
        team_errors = [(s.forecast_p_yes - target) ** 2 for s, target in zip(included, actual_targets)]
        market_errors = [
            (s.market_implied_p_yes - target) ** 2 for s, target in zip(included, actual_targets)
        ]
        count = Decimal(len(included))
        team_brier = sum(team_errors, Decimal(0)) / count
        market_brier = sum(market_errors, Decimal(0)) / count
        team_log_losses = []
        market_log_losses = []
        for s, target in zip(included, actual_targets):
            team_log_losses.append(
                _log_loss_contribution(s.forecast_p_yes, target, config.log_loss_epsilon)
            )
            market_log_losses.append(
                _log_loss_contribution(
                    s.market_implied_p_yes, target, config.log_loss_epsilon
                )
            )
        team_log_loss = sum(team_log_losses, Decimal(0)) / count
        market_log_loss = sum(market_log_losses, Decimal(0)) / count
        buckets: list[CalibrationBucket] = []
        width = Decimal(1) / Decimal(CALIBRATION_BUCKET_COUNT)
        for index in range(CALIBRATION_BUCKET_COUNT):
            lower = Decimal(index) * width
            upper = lower + width
            members = [s for s in included if lower <= s.forecast_p_yes < upper or (index == CALIBRATION_BUCKET_COUNT - 1 and s.forecast_p_yes == Decimal(1))]
            if members:
                mean = sum((s.forecast_p_yes for s in members), Decimal(0)) / Decimal(len(members))
                yes = sum(1 for s in members if s.actual_outcome == "yes")
                buckets.append(CalibrationBucket(lower, upper, len(members), mean, yes))
            else:
                buckets.append(CalibrationBucket(lower, upper, 0, None, 0))
    else:
        team_brier = None
        market_brier = None
        team_log_loss = None
        market_log_loss = None
        buckets = tuple(
            CalibrationBucket(
                Decimal(i) / Decimal(CALIBRATION_BUCKET_COUNT),
                (Decimal(i) + 1) / Decimal(CALIBRATION_BUCKET_COUNT),
                0,
                None,
                0,
            )
            for i in range(CALIBRATION_BUCKET_COUNT)
        )

    n = len(included)
    denominator = n + config.pending_count
    coverage = Decimal(n) / Decimal(denominator) if n > 0 and denominator > 0 else None
    if n < config.min_samples_indicative or team_brier is None or market_brier is None:
        verdict = SettlementVerdict.INSUFFICIENT_SAMPLE
    elif team_brier >= market_brier:
        verdict = SettlementVerdict.NO_CONSISTENT_EDGE
    elif n < config.min_samples_comparative:
        verdict = SettlementVerdict.INDICATIVE_EDGE
    else:
        verdict = SettlementVerdict.COMPARATIVE_EDGE

    team_counts: dict[str, int] = {}
    event_counts: dict[str, int] = {}
    for sample in included:
        team_counts[sample.team_id] = team_counts.get(sample.team_id, 0) + 1
        if sample.event_id is not None:
            event_counts[sample.event_id] = event_counts.get(sample.event_id, 0) + 1

    verified_event_rows = sum(event_counts.values())
    max_verified_event_concentration = (
        Decimal(max(event_counts.values())) / Decimal(verified_event_rows)
        if verified_event_rows
        else None
    )
    lags = [_decimal_seconds(sample.settled_at - sample.generated_at) for sample in included]
    hand_check_rows = []
    for sample in sorted(
        included,
        key=lambda item: (item.condition_id, item.team_id, item.generated_at),
    )[:5]:
        target = Decimal(1) if sample.actual_outcome == "yes" else Decimal(0)
        hand_check_rows.append(
            SettlementHandCheckRow(
                condition_id=sample.condition_id,
                team_id=sample.team_id,
                generated_at=sample.generated_at,
                event_id=sample.event_id,
                forecast_p_yes=sample.forecast_p_yes,
                market_implied_p_yes=sample.market_implied_p_yes,
                actual_outcome=sample.actual_outcome,
                team_squared_error=(sample.forecast_p_yes - target) ** 2,
                market_squared_error=(sample.market_implied_p_yes - target) ** 2,
                team_log_loss=_log_loss_contribution(
                    sample.forecast_p_yes, target, config.log_loss_epsilon
                ),
                market_log_loss=_log_loss_contribution(
                    sample.market_implied_p_yes, target, config.log_loss_epsilon
                ),
            )
        )

    return SettlementEvaluationReport(
        verdict=verdict,
        included_count=n,
        excluded_count=sum(exclusion_counts.values()),
        exclusion_reasons=tuple(sorted(exclusion_counts.items())),
        pending_count=config.pending_count,
        coverage=coverage,
        team_brier=team_brier,
        market_brier=market_brier,
        team_log_loss=team_log_loss,
        market_log_loss=market_log_loss,
        calibration_buckets=tuple(buckets),
        team_counts=tuple(sorted(team_counts.items())),
        unique_condition_count=len({sample.condition_id for sample in included}),
        verified_unique_event_count=len(event_counts),
        unknown_event_row_count=sum(sample.event_id is None for sample in included),
        event_counts=tuple(sorted(event_counts.items())),
        max_verified_event_concentration=max_verified_event_concentration,
        settlement_lag_min_seconds=min(lags) if lags else None,
        settlement_lag_median_seconds=_median(lags) if lags else None,
        settlement_lag_max_seconds=max(lags) if lags else None,
        hand_check_rows=tuple(hand_check_rows),
        as_of_evaluation_cutoff=config.as_of_evaluation_cutoff,
        config_min_indicative=config.min_samples_indicative,
        config_min_comparative=config.min_samples_comparative,
    )


def _ln(value: Decimal) -> float:
    import math

    return math.log(float(value))


def load_samples_document(document: str) -> tuple[list[dict[str, Any]], SettlementEvaluationConfig]:
    parsed = json.loads(document)
    if not isinstance(parsed, dict):
        raise ValueError("samples document must be a JSON object")
    config = SettlementEvaluationConfig(
        as_of_evaluation_cutoff=datetime.fromisoformat(parsed["as_of_evaluation_cutoff"]),
        pending_count=int(parsed.get("pending_count", 0)),
    )
    rows = parsed.get("samples", [])
    if not isinstance(rows, list):
        raise ValueError("samples must be a list")
    return rows, config


__all__ = (
    "CALIBRATION_BUCKET_COUNT",
    "CalibrationBucket",
    "DEFAULT_EPSILON",
    "SettlementEvaluationConfig",
    "SettlementEvaluationReport",
    "SettlementHandCheckRow",
    "SettledForecastSample",
    "SettlementVerdict",
    "evaluate_settlement_samples",
    "load_samples_document",
)
