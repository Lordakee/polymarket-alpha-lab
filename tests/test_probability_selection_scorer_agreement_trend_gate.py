from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement_trend import (
    ProbabilitySelectionScorerAgreementTrendReport,
)


GENERATED_AT = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 29, 11, 45, tzinfo=UTC)


def _api():
    return import_module(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides):
    values = {
        "config_version": "probability-selection-scorer-agreement-trend-gate-v0",
        "min_source_report_count": 3,
        "max_latest_status_streak_for_watch": 1,
        "max_latest_status_streak_for_block": 2,
        "max_trend_report_age_seconds": 86_400,
        "max_recurring_reason_code_count": 2,
    }
    values.update(overrides)
    return _api().ProbabilitySelectionScorerAgreementTrendGateConfig(**values)


def _trend_report(
    *,
    generated_at: datetime = SOURCE_AT,
    source_report_count: int = 4,
    first_generated_at: datetime | None = None,
    latest_generated_at: datetime | None = None,
    latest_agreement_status: str = "aligned",
    latest_status_streak: int = 1,
    aligned_report_count: int = 4,
    low_overlap_report_count: int = 0,
    gate_blocked_report_count: int = 0,
    missing_inputs_report_count: int = 0,
    insufficient_identifiers_report_count: int = 0,
    average_selected_count: Decimal = d("3.000000"),
    average_scorer_candidate_count: Decimal = d("3.000000"),
    recurring_reason_code_counts: tuple[tuple[str, int], ...] = (),
    trend_status: str = "stable",
    recommended_next_step: str = "continue_monitoring",
    reason_codes: tuple[str, ...] = ("agreement_trend_stable",),
) -> ProbabilitySelectionScorerAgreementTrendReport:
    if first_generated_at is None:
        first_generated_at = generated_at - timedelta(hours=3)
    if latest_generated_at is None:
        latest_generated_at = generated_at
    return ProbabilitySelectionScorerAgreementTrendReport(
        generated_at=generated_at,
        config_version="probability-selection-scorer-agreement-trend-v0",
        source_report_count=source_report_count,
        first_generated_at=first_generated_at,
        latest_generated_at=latest_generated_at,
        history_span_seconds=int((latest_generated_at - first_generated_at).total_seconds()),
        latest_agreement_status=latest_agreement_status,
        latest_status_streak=latest_status_streak,
        aligned_report_count=aligned_report_count,
        low_overlap_report_count=low_overlap_report_count,
        gate_blocked_report_count=gate_blocked_report_count,
        missing_inputs_report_count=missing_inputs_report_count,
        insufficient_identifiers_report_count=insufficient_identifiers_report_count,
        average_selected_count=average_selected_count,
        average_scorer_candidate_count=average_scorer_candidate_count,
        recurring_reason_code_counts=recurring_reason_code_counts,
        trend_status=trend_status,
        recommended_next_step=recommended_next_step,
        reason_codes=reason_codes,
    )


def _direct_report_from(report, **overrides):
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.update(overrides)
    return _api().ProbabilitySelectionScorerAgreementTrendGateReport(**values)


def _reason_count_rows(*reason_codes: str):
    return tuple(
        _api().ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
            reason_code,
            1,
        )
        for reason_code in reason_codes
    )


def test_agreement_trend_gate_passes_stable_aligned_trend() -> None:
    source = _trend_report()

    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is _api().ProbabilitySelectionScorerAgreementTrendGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-selection-scorer-agreement-trend-gate-v0"
    assert report.source_config_version == source.config_version
    assert report.source_generated_at == SOURCE_AT
    assert report.trend_report_age_seconds == 900
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_probability_selection_scorer_agreement_trend_review"
    assert report.source_report_count == 4
    assert report.latest_agreement_status == "aligned"
    assert report.latest_agreement_status_streak == 1
    assert report.source_trend_status == "stable"
    assert report.source_recommended_next_step == "continue_monitoring"
    assert report.aligned_report_count == 4
    assert report.low_overlap_report_count == 0
    assert report.gate_blocked_report_count == 0
    assert report.missing_inputs_report_count == 0
    assert report.insufficient_identifiers_report_count == 0
    assert report.average_selected_count == d("3.000000")
    assert report.average_scorer_candidate_count == d("3.000000")
    assert report.latest_source_reason_codes == ("agreement_trend_stable",)
    assert report.recurring_source_reason_code_counts == ()
    assert report.reason_codes == ("probability_selection_scorer_agreement_trend_gate_passed",)
    assert report.reason_code_counts == (
        _api().ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
            "probability_selection_scorer_agreement_trend_gate_passed",
            1,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_agreement_trend_gate_watches_latest_low_overlap() -> None:
    source = _trend_report(
        latest_agreement_status="low_overlap",
        latest_status_streak=1,
        aligned_report_count=2,
        low_overlap_report_count=2,
        trend_status="watch",
        recommended_next_step="review_selection_scorer_disagreement",
        reason_codes=("latest_agreement_low_overlap",),
    )

    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.recommended_next_step == "throttle_probability_selection_scorer_agreement_trend_review"
    assert report.reason_codes == ("latest_probability_selection_scorer_agreement_trend_watch",)
    assert report.reason_code_counts == (
        _api().ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
            "latest_probability_selection_scorer_agreement_trend_watch",
            1,
        ),
    )


def test_agreement_trend_gate_blocks_repeated_gate_blocked_status() -> None:
    source = _trend_report(
        latest_agreement_status="gate_blocked",
        latest_status_streak=2,
        aligned_report_count=1,
        gate_blocked_report_count=3,
        trend_status="blocked",
        recommended_next_step="review_scorer_gate",
        reason_codes=(
            "latest_agreement_gate_blocked",
            "repeated_latest_agreement_blocker",
        ),
    )

    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == "block_probability_selection_scorer_agreement_trend_review"
    assert report.reason_codes == (
        "latest_probability_selection_scorer_agreement_trend_blocked",
        "repeated_probability_selection_scorer_agreement_trend_blocker",
    )
    assert report.reason_code_counts == (
        _api().ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
            "latest_probability_selection_scorer_agreement_trend_blocked",
            1,
        ),
        _api().ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
            "repeated_probability_selection_scorer_agreement_trend_blocker",
            1,
        ),
    )


def test_agreement_trend_gate_blocks_insufficient_history() -> None:
    source = _trend_report(
        source_report_count=2,
        latest_status_streak=2,
        aligned_report_count=2,
        trend_status="insufficient_history",
        recommended_next_step="collect_more_history",
        reason_codes=("insufficient_history_count",),
    )

    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        source,
        config=_config(min_source_report_count=3),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "insufficient_probability_selection_scorer_agreement_trend_samples",
    )


def test_agreement_trend_gate_watches_stale_trend_report() -> None:
    source = _trend_report(generated_at=GENERATED_AT - timedelta(seconds=86_401))

    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        source,
        config=_config(max_trend_report_age_seconds=86_400),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.trend_report_age_seconds == 86_401
    assert report.reason_codes == (
        "stale_probability_selection_scorer_agreement_trend",
    )


def test_agreement_trend_gate_watches_repeated_reason_counts() -> None:
    source = _trend_report(
        recurring_reason_code_counts=(("low_selection_scorer_overlap", 3),),
        trend_status="watch",
        reason_codes=("recurring_agreement_reason_codes",),
    )

    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        source,
        config=_config(max_recurring_reason_code_count=2),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.reason_codes == (
        "repeated_probability_selection_scorer_agreement_trend_reason_threshold_exceeded",
    )
    assert report.recurring_source_reason_code_counts == (
        ("low_selection_scorer_overlap", 3),
    )


def test_agreement_trend_gate_rejects_wrong_source_type_and_future_generated_at() -> None:
    with pytest.raises(
        ValueError,
        match="source_report must be exactly ProbabilitySelectionScorerAgreementTrendReport",
    ):
        _api().build_probability_selection_scorer_agreement_trend_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="source_generated_at must not be after generated_at"):
        _api().build_probability_selection_scorer_agreement_trend_gate_report(
            _trend_report(generated_at=GENERATED_AT + timedelta(seconds=1)),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_agreement_trend_gate_validates_exact_config_type_and_hard_flags() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(_api().ProbabilitySelectionScorerAgreementTrendGateConfig):
            pass

    with pytest.raises(ValueError, match="config must be exactly"):
        _api().build_probability_selection_scorer_agreement_trend_gate_report(
            _trend_report(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="max_trend_report_age_seconds"):
        _config(max_trend_report_age_seconds=-1)


def test_agreement_trend_gate_report_is_frozen_and_validates_invariants() -> None:
    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="recommended_next_step"):
        _direct_report_from(report, recommended_next_step="wrong_next_step")
    with pytest.raises(ValueError, match="reason_code_counts"):
        _direct_report_from(report, reason_code_counts=())


def test_agreement_trend_gate_rejects_unsafe_direct_report_construction() -> None:
    report = _api().build_probability_selection_scorer_agreement_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    pass_reason = "probability_selection_scorer_agreement_trend_gate_passed"
    watch_reason = "latest_probability_selection_scorer_agreement_trend_watch"

    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            reason_codes=("unknown_gate_reason",),
            reason_code_counts=_reason_count_rows("unknown_gate_reason"),
        )
    with pytest.raises(ValueError, match="pass"):
        _direct_report_from(
            report,
            gate_status="watch",
            recommended_next_step=(
                "throttle_probability_selection_scorer_agreement_trend_review"
            ),
            reason_codes=(pass_reason, watch_reason),
            reason_code_counts=_reason_count_rows(pass_reason, watch_reason),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            reason_codes=(pass_reason, pass_reason),
            reason_code_counts=_reason_count_rows(pass_reason, pass_reason),
        )
    with pytest.raises(ValueError, match="source_trend_status"):
        _direct_report_from(report, source_trend_status="unexpected")
    with pytest.raises(ValueError, match="latest_agreement_status"):
        _direct_report_from(report, latest_agreement_status="unexpected")

    class GateStatus(str):
        pass

    with pytest.raises(ValueError, match="gate_status"):
        _direct_report_from(report, gate_status=GateStatus("pass"))
    with pytest.raises(ValueError, match="average_selected_count"):
        _direct_report_from(report, average_selected_count=1.0)
    with pytest.raises(ValueError, match="recurring_source_reason_code_counts"):
        _direct_report_from(
            report,
            recurring_source_reason_code_counts=(("duplicate_reason", 1),) * 2,
        )
