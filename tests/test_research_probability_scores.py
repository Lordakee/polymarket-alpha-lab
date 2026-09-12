"""Exact binary score identities and bounded, context-independent diagnostics."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext, Inexact, ROUND_UP
from fractions import Fraction
import random

import pytest

from polymarket_alpha_lab.research_probability_scores import (
    BinaryResearchObservation as Observation, ResearchProbabilityDiagnostics as Scores,
    ResearchReliabilityBin,
)


def observation(p, y):
    return Observation(Decimal(p), y)


@pytest.mark.parametrize(("p", "y", "brier", "log_status"), (
    ("0", False, "0", "finite"), ("1", True, "0", "finite"),
    ("0", True, "1", "infinite"), ("1", False, "1", "infinite"),
    ("0.5", False, "0.25", "finite"), ("0.5", True, "0.25", "finite"),
    ("0.7", True, "0.09", "finite"), ("0.7", False, "0.49", "finite"),
))
def test_binary_score_boundaries(p, y, brier, log_status):
    report = Scores((observation(p, y),))
    assert report.mean_brier_score == Decimal(brier)
    assert report.log_loss_status == log_status
    assert report.infinite_log_loss_count == int(log_status == "infinite")
    if log_status == "infinite":
        assert report.mean_log_loss is None
    elif p in ("0", "1"):
        assert report.mean_log_loss == 0


def test_hand_computed_brier_skill_and_log_loss():
    report = Scores(tuple(observation(p, y) for p, y in (("0.9", True), ("0.6", False), ("0.4", True), ("0.1", False))))
    assert report.mean_brier_score == Decimal("0.185")
    assert report.neutral_baseline_brier_score == Decimal("0.25")
    assert report.brier_skill_vs_half == Decimal("0.26")
    assert report.mean_log_loss == Decimal("0.510825623766")
    assert report.expected_calibration_error == Decimal("0.35")


def test_seventy_percent_group_seven_yes_out_of_ten():
    report = Scores(tuple(observation("0.7", i < 7) for i in range(10)))
    bucket = report.bins[7]
    assert bucket.lower == Decimal("0.7")
    assert bucket.count == 10 and bucket.yes_count == 7
    assert bucket.mean_probability_yes == bucket.observed_yes_rate == Decimal("0.7")
    assert report.mean_brier_score == Decimal("0.21")
    assert report.expected_calibration_error == 0
    assert report.sample_status == "insufficient_sample"  # Not a calibration approval.


@pytest.mark.parametrize("count", (2, 5, 10, 20))
def test_exact_lower_bin_edges_and_last_bin_includes_one(count):
    rows = tuple(Observation(Decimal(i) / count, i % 2 == 0) for i in range(count + 1))
    report = Scores(rows, bucket_count=count)
    assert [b.count for b in report.bins] == [1] * (count - 1) + [2]
    assert sum(b.count for b in report.bins) == count + 1


def test_empty_is_unknown_not_perfect_and_empty_bins_have_nulls():
    report = Scores(())
    assert report.sample_count == 0 and report.sample_status == "empty"
    assert report.mean_brier_score is report.mean_log_loss is report.expected_calibration_error is None
    assert report.brier_skill_vs_half is report.neutral_baseline_brier_score is None
    assert report.log_loss_status == "empty"
    assert all(b.count == 0 and b.mean_probability_yes is None and b.observed_yes_rate is None for b in report.bins)


def test_mixed_infinite_loss_is_not_a_finite_only_average():
    report = Scores((observation("0", True), observation("0.9", True)))
    assert report.infinite_log_loss_count == 1 and report.mean_log_loss is None
    assert report.mean_brier_score == Decimal("0.505")


def test_fixed_context_ignores_caller_precision_rounding_and_traps():
    rows = (observation("0.000000000001", True), observation("0.333333333333", False))
    expected = Scores(rows)
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.rounding = ROUND_UP
        ctx.traps[Inexact] = True
        assert Scores(rows) == expected


@pytest.mark.parametrize("p", (0.5, True, 1, "0.5", Decimal("NaN"), Decimal("Infinity"),
    Decimal("-0.01"), Decimal("1.01"), Decimal("1e-13"), Decimal("0.500000000000000000000000")))
def test_invalid_probabilities_rejected_without_clipping(p):
    with pytest.raises(ValueError):
        Observation(p, True)


@pytest.mark.parametrize("y", (0, 1, "yes", None, Decimal(1)))
def test_only_exact_bool_outcomes(y):
    with pytest.raises(ValueError):
        Observation(Decimal("0.5"), y)


@pytest.mark.parametrize("kwargs", ({"bucket_count": 0}, {"bucket_count": True}, {"bucket_count": 3},
    {"min_sample_count": 0}, {"min_sample_count": True}, {"min_bin_count": 0},
    {"paper_only": False}, {"report_only": 1}, {"readonly": False}))
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        Scores((), **kwargs)


def test_observation_types_and_mutation_are_revalidated():
    with pytest.raises(ValueError):
        Scores([])
    with pytest.raises(ValueError):
        Scores((object(),))
    row = observation("0.5", True)
    object.__setattr__(row, "probability_yes", Decimal("NaN"))
    with pytest.raises(ValueError):
        Scores((row,))
    report = Scores((observation("0.5", True),))
    with pytest.raises(FrozenInstanceError):
        report.mean_brier_score = 0
    with pytest.raises((TypeError, ValueError)):
        replace(report, mean_brier_score=Decimal(0))


def test_seeded_brier_and_ece_match_exact_rational_sufficient_statistics():
    rng = random.Random(7301)
    for _ in range(150):
        rows = tuple(Observation(Decimal(rng.randrange(1001)) / 1000, bool(rng.randrange(2))) for _ in range(rng.randrange(1, 60)))
        report = Scores(rows)
        expected_brier = sum((Fraction(row.probability_yes) - int(row.actual_yes)) ** 2 for row in rows) / len(rows)
        groups = [[] for _ in range(10)]
        for row in rows:
            groups[min(int(row.probability_yes * 10), 9)].append(row)
        expected_ece = sum(abs(sum((Fraction(r.probability_yes) - int(r.actual_yes) for r in group), Fraction())) for group in groups) / len(rows)
        assert abs(Fraction(report.mean_brier_score) - expected_brier) <= Fraction(1, 2 * 10**12)
        assert abs(Fraction(report.expected_calibration_error) - expected_ece) <= Fraction(1, 2 * 10**12)
        reversed_report = Scores(tuple(reversed(rows)))
        assert report.mean_brier_score == reversed_report.mean_brier_score
        assert report.mean_log_loss == reversed_report.mean_log_loss
        assert report.bins == reversed_report.bins


def test_sample_threshold_is_descriptive_not_validated():
    report = Scores((observation("0.5", True),) * 30)
    assert report.sample_status == "descriptive_only"
    assert report.brier_skill_vs_half == 0
    assert report.bins[5].sparse is False
