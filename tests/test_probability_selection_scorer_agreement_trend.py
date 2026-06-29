from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementReport,
)


BASE_AT = datetime(2026, 6, 27, 12, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 6, 27, 12, 15, tzinfo=UTC)


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab.probability_selection_scorer_agreement_trend",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides):
    values = {
        "min_history_count": 3,
        "blocking_status_streak_threshold": 2,
    }
    values.update(overrides)
    return _api().ProbabilitySelectionScorerAgreementTrendConfig(**values)


def _agreement_report(
    *,
    generated_at: datetime,
    agreement_status: str = "aligned",
    selected_count: int = 2,
    scorer_candidate_count: int = 2,
    scorer_gate_status: str = "pass",
    reason_codes: tuple[str, ...] | None = None,
) -> ProbabilitySelectionScorerAgreementReport:
    if reason_codes is None:
        reason_codes = _agreement_reason_codes(agreement_status)
    return ProbabilitySelectionScorerAgreementReport(
        generated_at=generated_at,
        config_version="probability-selection-scorer-agreement-v0",
        selection_generated_at=generated_at - timedelta(minutes=2),
        scorer_generated_at=generated_at - timedelta(minutes=1),
        selected_count=selected_count,
        scorer_candidate_count=scorer_candidate_count,
        selected_market_overlap_count=selected_count
        if agreement_status == "aligned"
        else 0,
        selected_condition_overlap_count=selected_count
        if agreement_status == "aligned"
        else 0,
        rejected_but_scored_count=0,
        scored_but_unselected_count=0,
        scorer_gate_status=scorer_gate_status,
        agreement_status=agreement_status,
        recommended_next_step=_agreement_next_step(agreement_status),
        reason_codes=reason_codes,
        reason_code_divergence_counts=(),
    )


def _agreement_reason_codes(agreement_status: str) -> tuple[str, ...]:
    if agreement_status == "aligned":
        return ("selection_scorer_aligned",)
    if agreement_status == "low_overlap":
        return ("low_selection_scorer_overlap",)
    if agreement_status == "gate_blocked":
        return ("scorer_gate_blocked",)
    if agreement_status == "missing_inputs":
        return ("missing_inputs",)
    if agreement_status == "insufficient_identifiers":
        return ("insufficient_identifiers",)
    raise AssertionError(f"unknown agreement_status fixture: {agreement_status}")


def _agreement_next_step(agreement_status: str) -> str:
    if agreement_status in ("missing_inputs", "insufficient_identifiers"):
        return "enrich_inputs"
    if agreement_status == "gate_blocked":
        return "review_scorer_gate"
    if agreement_status == "low_overlap":
        return "review_selection_scorer_disagreement"
    return "continue_monitoring"


def _trend(
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
    *,
    config=None,
    generated_at: datetime = GENERATED_AT,
):
    return _api().build_probability_selection_scorer_agreement_trend_report(
        reports,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _valid_trend_report():
    return _trend(
        (
            _agreement_report(generated_at=BASE_AT),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=5)),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=10)),
        ),
    )


def _direct_report_from(report, **overrides):
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.update(overrides)
    return _api().ProbabilitySelectionScorerAgreementTrendReport(**values)


def test_agreement_trend_stable_aligned_history_continues_monitoring() -> None:
    report = _trend(
        (
            _agreement_report(generated_at=BASE_AT, selected_count=1, scorer_candidate_count=3),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=5), selected_count=2, scorer_candidate_count=4),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=10), selected_count=3, scorer_candidate_count=5),
        ),
    )

    assert type(report) is _api().ProbabilitySelectionScorerAgreementTrendReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-selection-scorer-agreement-trend-v0"
    assert report.source_report_count == 3
    assert report.first_generated_at == BASE_AT
    assert report.latest_generated_at == BASE_AT + timedelta(minutes=10)
    assert report.history_span_seconds == 600
    assert report.latest_agreement_status == "aligned"
    assert report.latest_status_streak == 3
    assert report.aligned_report_count == 3
    assert report.low_overlap_report_count == 0
    assert report.gate_blocked_report_count == 0
    assert report.missing_inputs_report_count == 0
    assert report.insufficient_identifiers_report_count == 0
    assert report.average_selected_count == d("2.000000")
    assert report.average_scorer_candidate_count == d("4.000000")
    assert report.recurring_reason_code_counts == ()
    assert report.trend_status == "stable"
    assert report.recommended_next_step == "continue_monitoring"
    assert report.reason_codes == ("agreement_trend_stable",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_agreement_trend_watches_low_overlap_and_recurring_reasons() -> None:
    report = _trend(
        (
            _agreement_report(generated_at=BASE_AT),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=5),
                agreement_status="low_overlap",
                reason_codes=("low_selection_scorer_overlap", "shared_disagreement"),
            ),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                agreement_status="low_overlap",
                reason_codes=("low_selection_scorer_overlap", "shared_disagreement"),
            ),
        ),
    )

    assert report.latest_agreement_status == "low_overlap"
    assert report.latest_status_streak == 2
    assert report.aligned_report_count == 1
    assert report.low_overlap_report_count == 2
    assert report.recurring_reason_code_counts == (
        ("low_selection_scorer_overlap", 2),
        ("shared_disagreement", 2),
    )
    assert report.trend_status == "watch"
    assert report.recommended_next_step == "review_selection_scorer_disagreement"
    assert report.reason_codes == (
        "latest_agreement_low_overlap",
        "recurring_agreement_reason_codes",
    )


def test_agreement_trend_blocks_repeated_latest_gate_blockers() -> None:
    report = _trend(
        (
            _agreement_report(generated_at=BASE_AT),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=5),
                agreement_status="gate_blocked",
                scorer_gate_status="blocked",
            ),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                agreement_status="gate_blocked",
                scorer_gate_status="blocked",
            ),
        ),
    )

    assert report.latest_agreement_status == "gate_blocked"
    assert report.latest_status_streak == 2
    assert report.gate_blocked_report_count == 2
    assert report.trend_status == "blocked"
    assert report.recommended_next_step == "review_scorer_gate"
    assert report.reason_codes == (
        "latest_agreement_gate_blocked",
        "repeated_latest_agreement_blocker",
        "recurring_agreement_reason_codes",
    )


def test_agreement_trend_watches_single_missing_or_insufficient_inputs() -> None:
    missing = _trend(
        (
            _agreement_report(generated_at=BASE_AT),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=5)),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                agreement_status="missing_inputs",
                selected_count=0,
                scorer_candidate_count=0,
                scorer_gate_status="missing",
            ),
        ),
    )
    insufficient = _trend(
        (
            _agreement_report(generated_at=BASE_AT),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=5)),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                agreement_status="insufficient_identifiers",
            ),
        ),
    )

    assert missing.latest_agreement_status == "missing_inputs"
    assert missing.missing_inputs_report_count == 1
    assert missing.trend_status == "watch"
    assert missing.recommended_next_step == "enrich_inputs"
    assert missing.reason_codes == ("latest_agreement_missing_inputs",)
    assert insufficient.latest_agreement_status == "insufficient_identifiers"
    assert insufficient.insufficient_identifiers_report_count == 1
    assert insufficient.trend_status == "watch"
    assert insufficient.recommended_next_step == "enrich_inputs"
    assert insufficient.reason_codes == ("latest_agreement_insufficient_identifiers",)


def test_agreement_trend_rejects_empty_non_tuple_and_non_chronological_inputs() -> None:
    with pytest.raises(ValueError, match="tuple"):
        _trend([_agreement_report(generated_at=BASE_AT)])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="nonempty"):
        _trend(())
    with pytest.raises(ValueError, match="chronological"):
        _trend(
            (
                _agreement_report(generated_at=BASE_AT + timedelta(minutes=5)),
                _agreement_report(generated_at=BASE_AT),
            ),
        )


def test_agreement_trend_counts_recurrent_reasons_once_per_report() -> None:
    report = _trend(
        (
            _agreement_report(
                generated_at=BASE_AT,
                agreement_status="low_overlap",
                reason_codes=("shared_reason", "shared_reason", "once_reason"),
            ),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=5),
                agreement_status="aligned",
                reason_codes=("selection_scorer_aligned", "shared_reason"),
            ),
            _agreement_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                agreement_status="aligned",
                reason_codes=("selection_scorer_aligned",),
            ),
        ),
    )

    assert report.recurring_reason_code_counts == (("shared_reason", 2),)
    assert "recurring_agreement_reason_codes" in report.reason_codes
    assert "selection_scorer_aligned" not in dict(report.recurring_reason_code_counts)


def test_agreement_trend_uses_decimal_only_for_average_counts_and_quantization() -> None:
    report = _trend(
        (
            _agreement_report(generated_at=BASE_AT, selected_count=1, scorer_candidate_count=2),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=5), selected_count=2, scorer_candidate_count=4),
            _agreement_report(generated_at=BASE_AT + timedelta(minutes=10), selected_count=2, scorer_candidate_count=5),
        ),
    )

    assert type(report.average_selected_count) is Decimal
    assert type(report.average_scorer_candidate_count) is Decimal
    assert report.average_selected_count == d("1.666667")
    assert report.average_scorer_candidate_count == d("3.666667")

    mutated = _agreement_report(generated_at=BASE_AT)
    object.__setattr__(mutated, "selected_count", 1.0)
    with pytest.raises(ValueError, match="selected_count"):
        _trend((mutated, mutated, mutated))


def test_agreement_trend_hard_flags_frozen_and_exact_type_protections() -> None:
    config = _config()
    report = _valid_trend_report()

    with pytest.raises(FrozenInstanceError):
        config.min_history_count = 4  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.trend_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="config must be report_only"):
        replace(config, report_only=False)
    with pytest.raises(ValueError, match="config must be readonly"):
        replace(config, readonly=False)
    with pytest.raises(ValueError, match="trend report must be readonly"):
        replace(report, readonly=False)

    source = _agreement_report(generated_at=BASE_AT)
    object.__setattr__(source, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _trend((source, source, source))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        _trend(
            (
                _agreement_report(generated_at=BASE_AT),
                _agreement_report(generated_at=BASE_AT + timedelta(minutes=5)),
                _agreement_report(generated_at=BASE_AT + timedelta(minutes=10)),
            ),
            generated_at=DatetimeSubclass(2026, 6, 27, 12, 15, tzinfo=UTC),
        )

    with pytest.raises(TypeError, match="TrendConfig .*subclassing"):
        class ConfigSubclass(_api().ProbabilitySelectionScorerAgreementTrendConfig):
            pass

    with pytest.raises(TypeError, match="TrendReport .*subclassing"):
        class ReportSubclass(_api().ProbabilitySelectionScorerAgreementTrendReport):
            pass

    with pytest.raises(
        ValueError,
        match="exactly ProbabilitySelectionScorerAgreementTrendConfig",
    ):
        _api().ProbabilitySelectionScorerAgreementTrendConfig.__post_init__(
            SimpleNamespace(
                config_version="probability-selection-scorer-agreement-trend-v0",
                min_history_count=3,
                blocking_status_streak_threshold=2,
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        )
    with pytest.raises(
        ValueError,
        match="exactly ProbabilitySelectionScorerAgreementReport values",
    ):
        _trend(
            (
                _agreement_report(generated_at=BASE_AT),
                SimpleNamespace(generated_at=BASE_AT + timedelta(minutes=5)),
            ),  # type: ignore[arg-type]
        )


def test_agreement_trend_report_validates_reason_status_consistency() -> None:
    report = _valid_trend_report()

    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            trend_status="watch",
            recommended_next_step="continue_monitoring",
            reason_codes=(),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            trend_status="watch",
            recommended_next_step="continue_monitoring",
            reason_codes=("unknown_agreement_trend_reason",),
        )
    with pytest.raises(ValueError, match="recommended_next_step"):
        _direct_report_from(report, recommended_next_step="enrich_inputs")
    with pytest.raises(ValueError, match="trend_status"):
        _direct_report_from(
            report,
            trend_status="watch",
            recommended_next_step="continue_monitoring",
        )
