"""Pure binary P(YES) scoring and reliability diagnostics, never approval.

No fitting, probability rewriting, I/O or dependencies. A wrong certainty has
infinite log loss, represented by an explicit count/status rather than NaN or
clipping. All arithmetic uses a private Decimal context; confidence is not p.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_research_agent_types import hard_flags, integer

QUANTUM = Decimal("0.000000000001")
CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
BUCKET_COUNTS = (2, 5, 10, 20)
MAX_OBSERVATIONS = 10000


def probability(value: object) -> None:
    """Bound exact inputs, without clipping or rounding a supplied forecast."""
    if (type(value) is not Decimal or not value.is_finite()
            or len(value.as_tuple().digits) > 18
            or not -12 <= value.as_tuple().exponent <= 0
            or not Decimal(0) <= value <= Decimal(1)):
        raise ValueError("expected bounded Decimal probability in [0,1]")


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


@dataclass(frozen=True, slots=True)
class BinaryResearchObservation:
    probability_yes: Decimal
    actual_yes: bool

    def __post_init__(self) -> None:
        probability(self.probability_yes)
        if type(self.actual_yes) is not bool:
            raise ValueError("actual_yes must be an exact bool")


@dataclass(frozen=True, slots=True)
class ResearchReliabilityBin:
    lower: Decimal
    upper: Decimal
    count: int
    predicted_probability_sum: Decimal
    yes_count: int
    min_bin_count: int
    mean_probability_yes: Decimal | None = field(init=False)
    observed_yes_rate: Decimal | None = field(init=False)
    sparse: bool = field(init=False)

    def __post_init__(self) -> None:
        probability(self.lower)
        probability(self.upper)
        if self.lower >= self.upper:
            raise ValueError("invalid reliability bin bounds")
        integer("count", self.count, 0, MAX_OBSERVATIONS)
        integer("yes_count", self.yes_count, 0, self.count)
        integer("min_bin_count", self.min_bin_count, 1, MAX_OBSERVATIONS)
        total = self.predicted_probability_sum
        if type(total) is not Decimal or not total.is_finite():
            raise ValueError("invalid bin probability sum")
        with localcontext(CONTEXT):
            if not self.lower * self.count <= total <= self.upper * self.count:
                raise ValueError("bin sum must match bounds and count")
            if self.count and self.upper != 1 and total == self.upper * self.count:
                raise ValueError("bin upper edge is exclusive except at one")
            object.__setattr__(self, "mean_probability_yes", _rounded(total / self.count) if self.count else None)
            object.__setattr__(self, "observed_yes_rate", _rounded(Decimal(self.yes_count) / self.count) if self.count else None)
        object.__setattr__(self, "sparse", self.count < self.min_bin_count)


@dataclass(frozen=True, slots=True)
class ResearchProbabilityDiagnostics:
    observations: tuple[BinaryResearchObservation, ...] = field(repr=False)
    bucket_count: int = 10
    min_sample_count: int = 30
    min_bin_count: int = 5
    sample_count: int = field(init=False)
    sample_status: str = field(init=False)
    mean_brier_score: Decimal | None = field(init=False)
    neutral_baseline_brier_score: Decimal | None = field(init=False)
    brier_skill_vs_half: Decimal | None = field(init=False)
    mean_log_loss: Decimal | None = field(init=False)
    log_loss_status: str = field(init=False)
    infinite_log_loss_count: int = field(init=False)
    expected_calibration_error: Decimal | None = field(init=False)
    bins: tuple[ResearchReliabilityBin, ...] = field(init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        if type(self.observations) is not tuple or len(self.observations) > MAX_OBSERVATIONS:
            raise ValueError("observations must be a bounded exact tuple")
        if type(self.bucket_count) is not int or self.bucket_count not in BUCKET_COUNTS:
            raise ValueError("bucket_count must be 2, 5, 10 or 20")
        integer("min_sample_count", self.min_sample_count, 1, MAX_OBSERVATIONS)
        integer("min_bin_count", self.min_bin_count, 1, MAX_OBSERVATIONS)
        if any(type(row) is not BinaryResearchObservation for row in self.observations):
            raise ValueError("expected exact binary observations")
        observations = tuple(replace(row) for row in self.observations)
        object.__setattr__(self, "observations", observations)
        n = len(observations)
        totals = [Decimal(0) for _ in range(self.bucket_count)]
        counts = [0] * self.bucket_count
        yes_counts = [0] * self.bucket_count
        infinite_count = 0
        with localcontext(CONTEXT):
            brier_sum = log_sum = Decimal(0)
            for row in observations:
                p, y = row.probability_yes, Decimal(int(row.actual_yes))
                brier_sum += (p - y) ** 2
                true_probability = p if row.actual_yes else Decimal(1) - p
                if true_probability == 0:
                    infinite_count += 1
                else:
                    log_sum -= true_probability.ln()
                index = min(int(p * self.bucket_count), self.bucket_count - 1)
                totals[index] += p
                counts[index] += 1
                yes_counts[index] += int(row.actual_yes)
            bins = tuple(ResearchReliabilityBin(
                Decimal(i) / self.bucket_count, Decimal(i + 1) / self.bucket_count,
                counts[i], totals[i], yes_counts[i], self.min_bin_count,
            ) for i in range(self.bucket_count))
            # Aggregate exact sufficient statistics, not rounded bin means.
            error_sum = sum((abs(totals[i] - yes_counts[i]) for i in range(self.bucket_count)), Decimal(0))
            values = dict(
                sample_count=n,
                sample_status="empty" if not n else "insufficient_sample" if n < self.min_sample_count else "descriptive_only",
                mean_brier_score=_rounded(brier_sum / n) if n else None,
                neutral_baseline_brier_score=Decimal("0.250000000000") if n else None,
                brier_skill_vs_half=_rounded(1 - (brier_sum / n) / Decimal("0.25")) if n else None,
                mean_log_loss=_rounded(log_sum / n) if n and not infinite_count else None,
                log_loss_status="empty" if not n else "infinite" if infinite_count else "finite",
                infinite_log_loss_count=infinite_count,
                expected_calibration_error=_rounded(error_sum / n) if n else None,
                bins=bins,
            )
        for name, value in values.items():
            object.__setattr__(self, name, value)


__all__ = ("BinaryResearchObservation", "ResearchReliabilityBin", "ResearchProbabilityDiagnostics")
