from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
    PaperStrategyCandidateRecommendationRow,
)
from polymarket_alpha_lab.strategy_recommendation_history import (
    PaperStrategyRecommendationHistoryReport,
    PaperStrategyRecommendationHistorySourceSummary,
    build_paper_strategy_recommendation_history_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


def _row(
    market_slug: str,
    *,
    action: str,
    score: Decimal = Decimal("0.500000"),
) -> PaperStrategyCandidateRecommendationRow:
    return PaperStrategyCandidateRecommendationRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        action=action,
        assessment_status="ready" if action != "reject" else "blocked",
        readiness_status="pass",
        selected_side="yes",
        scoring_side="yes",
        recommendation_score=score,
        reason_codes=("test_reason",),
    )


def _recommendation_report(
    generated_at: datetime,
    *,
    config_version: str = "strategy-recommendation-v0",
    rows: tuple[PaperStrategyCandidateRecommendationRow, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperStrategyCandidateRecommendationReport:
    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                {"recommend": 0, "watch": 1, "reject": 2}[row.action],
                -row.recommendation_score,
                row.market_slug,
            ),
        ),
    )
    return PaperStrategyCandidateRecommendationReport(
        generated_at=generated_at,
        config_version=config_version,
        readiness_overall_status="pass",
        candidate_count=len(ordered_rows),
        recommend_count=sum(1 for row in ordered_rows if row.action == "recommend"),
        watch_count=sum(1 for row in ordered_rows if row.action == "watch"),
        reject_count=sum(1 for row in ordered_rows if row.action == "reject"),
        recommendation_rows=ordered_rows,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _history_report(
    *reports: PaperStrategyCandidateRecommendationReport,
) -> PaperStrategyRecommendationHistoryReport:
    return build_paper_strategy_recommendation_history_report(
        reports,
        config_version="recommendation-history-v0",
        generated_at=GENERATED_AT,
    )


def _source_summary(
    generated_at: datetime,
    *,
    config_version: str = "strategy-recommendation-v0",
    candidate_count: int = 1,
    recommend_count: int = 1,
    watch_count: int = 0,
    reject_count: int = 0,
    top_recommendation_score: Decimal | None = Decimal("0.500000"),
    average_recommendation_score: Decimal | None = Decimal("0.500000"),
) -> PaperStrategyRecommendationHistorySourceSummary:
    return PaperStrategyRecommendationHistorySourceSummary(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        recommend_count=recommend_count,
        watch_count=watch_count,
        reject_count=reject_count,
        top_recommendation_score=top_recommendation_score,
        average_recommendation_score=average_recommendation_score,
    )


def test_strategy_recommendation_history_empty_input_is_readonly_report():
    history = _history_report()

    assert history.generated_at == GENERATED_AT
    assert history.config_version == "recommendation-history-v0"
    assert history.source_report_count == 0
    assert history.total_candidate_count == 0
    assert history.total_recommend_count == 0
    assert history.total_watch_count == 0
    assert history.total_reject_count == 0
    assert history.latest_generated_at is None
    assert history.latest_config_version is None
    assert history.latest_candidate_count == 0
    assert history.latest_recommend_count == 0
    assert history.latest_watch_count == 0
    assert history.latest_reject_count == 0
    assert history.latest_top_recommendation_score is None
    assert history.best_observed_recommendation_score is None
    assert history.average_recommendation_score is None
    assert history.latest_average_recommendation_score is None
    assert history.source_summaries == ()
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_strategy_recommendation_history_empty_iterable_is_readonly_report():
    history = build_paper_strategy_recommendation_history_report(
        (report for report in ()),
        config_version="recommendation-history-v0",
        generated_at=GENERATED_AT,
    )

    assert history.source_report_count == 0
    assert history.total_candidate_count == 0
    assert history.first_generated_at is None
    assert history.latest_generated_at is None
    assert history.latest_config_version is None
    assert history.latest_top_recommendation_score is None
    assert history.best_observed_recommendation_score is None
    assert history.average_recommendation_score is None
    assert history.latest_average_recommendation_score is None
    assert history.source_summaries == ()
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_strategy_recommendation_history_summarizes_two_ordered_reports_and_latest_counts():
    first = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v1",
        rows=(
            _row("market-a", action="recommend", score=Decimal("0.900000")),
            _row("market-b", action="watch", score=Decimal("0.200000")),
        ),
    )
    latest = _recommendation_report(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v2",
        rows=(
            _row("market-c", action="recommend", score=Decimal("0.800000")),
            _row("market-d", action="reject", score=Decimal("0.100000")),
            _row("market-e", action="watch", score=Decimal("0.300000")),
        ),
    )

    history = _history_report(first, latest)

    assert history.source_report_count == 2
    assert history.total_candidate_count == 5
    assert history.total_recommend_count == 2
    assert history.total_watch_count == 2
    assert history.total_reject_count == 1
    assert history.first_generated_at == first.generated_at
    assert history.latest_generated_at == latest.generated_at
    assert history.latest_config_version == "strategy-recommendation-v2"
    assert history.latest_candidate_count == 3
    assert history.latest_recommend_count == 1
    assert history.latest_watch_count == 1
    assert history.latest_reject_count == 1
    assert tuple(summary.generated_at for summary in history.source_summaries) == (
        first.generated_at,
        latest.generated_at,
    )
    assert history.source_summaries[-1].config_version == "strategy-recommendation-v2"
    assert history.source_summaries[-1].candidate_count == 3


def test_strategy_recommendation_history_summarizes_recommendation_score_trends():
    first = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v1",
        rows=(
            _row("market-a", action="recommend", score=Decimal("0.900000")),
        ),
    )
    latest = _recommendation_report(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v2",
        rows=(
            _row("market-b", action="recommend", score=Decimal("0.600000")),
            _row("market-c", action="watch", score=Decimal("0.300000")),
            _row("market-d", action="reject", score=Decimal("0.300000")),
        ),
    )

    history = _history_report(latest, first)

    assert history.latest_top_recommendation_score == Decimal("0.600000")
    assert history.best_observed_recommendation_score == Decimal("0.900000")
    assert history.average_recommendation_score == Decimal("0.525000")
    assert history.latest_average_recommendation_score == Decimal("0.400000")
    assert tuple(
        (
            summary.top_recommendation_score,
            summary.average_recommendation_score,
        )
        for summary in history.source_summaries
    ) == (
        (Decimal("0.900000"), Decimal("0.900000")),
        (Decimal("0.600000"), Decimal("0.400000")),
    )


def test_strategy_recommendation_history_handles_sources_without_candidates():
    empty_source = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v1",
        rows=(),
    )

    history = _history_report(empty_source)

    assert history.source_report_count == 1
    assert history.total_candidate_count == 0
    assert history.latest_top_recommendation_score is None
    assert history.best_observed_recommendation_score is None
    assert history.average_recommendation_score is None
    assert history.latest_average_recommendation_score is None
    assert history.source_summaries[0].top_recommendation_score is None
    assert history.source_summaries[0].average_recommendation_score is None


def test_strategy_recommendation_history_orders_input_by_generated_at():
    older = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        rows=(_row("market-a", action="watch"),),
    )
    newer = _recommendation_report(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        rows=(_row("market-b", action="recommend"),),
    )

    history = _history_report(newer, older)

    assert tuple(summary.generated_at for summary in history.source_summaries) == (
        older.generated_at,
        newer.generated_at,
    )
    assert history.latest_generated_at == newer.generated_at
    assert history.latest_recommend_count == 1
    assert history.latest_watch_count == 0
    assert history.latest_reject_count == 0


def test_strategy_recommendation_history_orders_input_by_generated_at_then_config_version():
    generated_at = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    earlier_config = _recommendation_report(
        generated_at,
        config_version="strategy-recommendation-v1",
        rows=(_row("market-a", action="recommend"),),
    )
    latest_config = _recommendation_report(
        generated_at,
        config_version="strategy-recommendation-v2",
        rows=(_row("market-b", action="watch"),),
    )

    history = _history_report(latest_config, earlier_config)

    assert tuple(summary.config_version for summary in history.source_summaries) == (
        "strategy-recommendation-v1",
        "strategy-recommendation-v2",
    )
    assert history.first_generated_at == generated_at
    assert history.latest_generated_at == generated_at
    assert history.latest_config_version == "strategy-recommendation-v2"
    assert history.latest_candidate_count == 1
    assert history.latest_recommend_count == 0
    assert history.latest_watch_count == 1
    assert history.latest_reject_count == 0


def test_strategy_recommendation_history_orders_sources_after_timezone_normalization():
    earlier = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v1",
        rows=(_row("market-a", action="recommend"),),
    )
    later = _recommendation_report(
        datetime(2026, 6, 18, 12, 30, tzinfo=UTC),
        config_version="strategy-recommendation-v2",
        rows=(_row("market-b", action="watch"),),
    )
    same_as_earlier_in_non_utc_zone = datetime(
        2026,
        6,
        18,
        6,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    object.__setattr__(earlier, "generated_at", same_as_earlier_in_non_utc_zone)

    history = _history_report(later, earlier)

    assert tuple(summary.generated_at for summary in history.source_summaries) == (
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 12, 30, tzinfo=UTC),
    )
    assert history.first_generated_at == datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    assert history.latest_generated_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    assert history.latest_config_version == "strategy-recommendation-v2"


def test_strategy_recommendation_history_normalizes_direct_source_summary_timestamps():
    earlier = _source_summary(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v1",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
    )
    later = _source_summary(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v2",
        candidate_count=1,
        recommend_count=0,
        watch_count=1,
        reject_count=0,
        top_recommendation_score=Decimal("0.300000"),
        average_recommendation_score=Decimal("0.300000"),
    )
    object.__setattr__(
        earlier,
        "generated_at",
        datetime(2026, 6, 18, 6, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    history = PaperStrategyRecommendationHistoryReport(
        generated_at=GENERATED_AT,
        config_version="recommendation-history-v0",
        source_report_count=2,
        total_candidate_count=2,
        total_recommend_count=1,
        total_watch_count=1,
        total_reject_count=0,
        first_generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        latest_generated_at=later.generated_at,
        latest_config_version="strategy-recommendation-v2",
        latest_candidate_count=1,
        latest_recommend_count=0,
        latest_watch_count=1,
        latest_reject_count=0,
        latest_top_recommendation_score=Decimal("0.300000"),
        best_observed_recommendation_score=Decimal("0.500000"),
        average_recommendation_score=Decimal("0.400000"),
        latest_average_recommendation_score=Decimal("0.300000"),
        source_summaries=(earlier, later),
    )

    assert tuple(summary.generated_at for summary in history.source_summaries) == (
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
    )
    assert history.source_summaries[0].generated_at.tzinfo is UTC


def test_strategy_recommendation_history_allows_duplicate_source_summary_keys_for_stable_ties():
    generated_at = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    first = _source_summary(
        generated_at=generated_at,
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
        top_recommendation_score=Decimal("0.600000"),
        average_recommendation_score=Decimal("0.600000"),
    )
    duplicate = _source_summary(
        generated_at=generated_at,
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=0,
        watch_count=1,
        reject_count=0,
        top_recommendation_score=Decimal("0.300000"),
        average_recommendation_score=Decimal("0.300000"),
    )

    history = PaperStrategyRecommendationHistoryReport(
        generated_at=GENERATED_AT,
        config_version="recommendation-history-v0",
        source_report_count=2,
        total_candidate_count=2,
        total_recommend_count=1,
        total_watch_count=1,
        total_reject_count=0,
        first_generated_at=generated_at,
        latest_generated_at=generated_at,
        latest_config_version="strategy-recommendation-v0",
        latest_candidate_count=1,
        latest_recommend_count=0,
        latest_watch_count=1,
        latest_reject_count=0,
        latest_top_recommendation_score=Decimal("0.300000"),
        best_observed_recommendation_score=Decimal("0.600000"),
        average_recommendation_score=Decimal("0.450000"),
        latest_average_recommendation_score=Decimal("0.300000"),
        source_summaries=(first, duplicate),
    )

    assert history.source_summaries == (first, duplicate)
    assert history.latest_watch_count == 1


def test_strategy_recommendation_history_builder_preserves_duplicate_key_stable_ties():
    generated_at = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    recommend_report = _recommendation_report(
        generated_at,
        config_version="strategy-recommendation-v0",
        rows=(_row("market-a", action="recommend"),),
    )
    watch_report = _recommendation_report(
        generated_at,
        config_version="strategy-recommendation-v0",
        rows=(_row("market-b", action="watch"),),
    )

    first_order = _history_report(recommend_report, watch_report)
    second_order = _history_report(watch_report, recommend_report)

    assert first_order.latest_recommend_count == 0
    assert first_order.latest_watch_count == 1
    assert second_order.latest_recommend_count == 1
    assert second_order.latest_watch_count == 0


def test_strategy_recommendation_history_revalidates_direct_source_summary_counts():
    summary = _source_summary(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
    )
    object.__setattr__(summary, "recommend_count", True)

    with pytest.raises(ValueError, match="recommend_count must be an int"):
        PaperStrategyRecommendationHistoryReport(
            generated_at=GENERATED_AT,
            config_version="recommendation-history-v0",
            source_report_count=1,
            total_candidate_count=1,
            total_recommend_count=1,
            total_watch_count=0,
            total_reject_count=0,
            first_generated_at=summary.generated_at,
            latest_generated_at=summary.generated_at,
            latest_config_version="strategy-recommendation-v0",
            latest_candidate_count=1,
            latest_recommend_count=1,
            latest_watch_count=0,
            latest_reject_count=0,
            latest_top_recommendation_score=Decimal("0.500000"),
            best_observed_recommendation_score=Decimal("0.500000"),
            average_recommendation_score=Decimal("0.500000"),
            latest_average_recommendation_score=Decimal("0.500000"),
            source_summaries=(summary,),
        )


@pytest.mark.parametrize(
    ("field_name", "value", "expected_message"),
    (
        (
            "top_recommendation_score",
            0.5,
            "top_recommendation_score must be a Decimal",
        ),
        (
            "average_recommendation_score",
            Decimal("-0.000001"),
            "average_recommendation_score must be nonnegative",
        ),
        (
            "average_recommendation_score",
            Decimal("NaN"),
            "average_recommendation_score must be finite",
        ),
    ),
)
def test_strategy_recommendation_history_source_summary_validates_score_metrics(
    field_name: str,
    value: object,
    expected_message: str,
):
    kwargs = {
        "generated_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "candidate_count": 1,
        "recommend_count": 1,
        "watch_count": 0,
        "reject_count": 0,
        "top_recommendation_score": Decimal("0.500000"),
        "average_recommendation_score": Decimal("0.500000"),
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=expected_message):
        _source_summary(**kwargs)  # type: ignore[arg-type]


def test_strategy_recommendation_history_rejects_invalid_source_type():
    valid_report = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="recommendation_reports must be an iterable"):
        build_paper_strategy_recommendation_history_report(
            object(),
            config_version="recommendation-history-v0",
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="recommendation_reports must contain"):
        _history_report(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("flag_name", "expected_message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_strategy_recommendation_history_rejects_source_reports_without_hard_flags(
    flag_name: str,
    expected_message: str,
):
    report = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
    )

    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=expected_message):
        _history_report(report)


def test_strategy_recommendation_history_direct_constructor_validates_mismatches():
    report = _recommendation_report(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        rows=(_row("market-a", action="recommend"),),
    )
    history = _history_report(report)

    invalid_changes = (
        {"source_report_count": 2},
        {"total_candidate_count": 2},
        {"total_recommend_count": 2},
        {"latest_generated_at": None},
        {"latest_config_version": "different-version"},
        {"latest_candidate_count": 2},
        {"latest_recommend_count": 0},
        {"latest_top_recommendation_score": Decimal("0.000000")},
        {"best_observed_recommendation_score": Decimal("0.000000")},
        {"average_recommendation_score": Decimal("0.000000")},
        {"latest_average_recommendation_score": Decimal("0.000000")},
        {"paper_only": False},
        {"report_only": False},
        {"readonly": False},
    )

    for changes in invalid_changes:
        with pytest.raises(ValueError):
            replace(history, **changes)


def test_strategy_recommendation_history_direct_constructor_validates_empty_invariants():
    with pytest.raises(ValueError, match="source_report_count must match"):
        PaperStrategyRecommendationHistoryReport(
            generated_at=GENERATED_AT,
            config_version="recommendation-history-v0",
            source_report_count=1,
            total_candidate_count=0,
            total_recommend_count=0,
            total_watch_count=0,
            total_reject_count=0,
            first_generated_at=None,
            latest_generated_at=None,
            latest_config_version=None,
            latest_candidate_count=0,
            latest_recommend_count=0,
            latest_watch_count=0,
            latest_reject_count=0,
            latest_top_recommendation_score=None,
            best_observed_recommendation_score=None,
            average_recommendation_score=None,
            latest_average_recommendation_score=None,
            source_summaries=(),
        )

    with pytest.raises(ValueError, match="generated_at bounds must be absent"):
        PaperStrategyRecommendationHistoryReport(
            generated_at=GENERATED_AT,
            config_version="recommendation-history-v0",
            source_report_count=0,
            total_candidate_count=0,
            total_recommend_count=0,
            total_watch_count=0,
            total_reject_count=0,
            first_generated_at=GENERATED_AT,
            latest_generated_at=None,
            latest_config_version=None,
            latest_candidate_count=0,
            latest_recommend_count=0,
            latest_watch_count=0,
            latest_reject_count=0,
            latest_top_recommendation_score=None,
            best_observed_recommendation_score=None,
            average_recommendation_score=None,
            latest_average_recommendation_score=None,
            source_summaries=(),
        )

    with pytest.raises(ValueError, match="latest_config_version must be absent"):
        PaperStrategyRecommendationHistoryReport(
            generated_at=GENERATED_AT,
            config_version="recommendation-history-v0",
            source_report_count=0,
            total_candidate_count=0,
            total_recommend_count=0,
            total_watch_count=0,
            total_reject_count=0,
            first_generated_at=None,
            latest_generated_at=None,
            latest_config_version="strategy-recommendation-v0",
            latest_candidate_count=0,
            latest_recommend_count=0,
            latest_watch_count=0,
            latest_reject_count=0,
            latest_top_recommendation_score=None,
            best_observed_recommendation_score=None,
            average_recommendation_score=None,
            latest_average_recommendation_score=None,
            source_summaries=(),
        )


def test_strategy_recommendation_history_direct_constructor_requires_deterministic_summaries():
    older = _source_summary(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
        top_recommendation_score=Decimal("0.600000"),
        average_recommendation_score=Decimal("0.600000"),
    )
    newer = _source_summary(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=0,
        watch_count=1,
        reject_count=0,
        top_recommendation_score=Decimal("0.300000"),
        average_recommendation_score=Decimal("0.300000"),
    )

    with pytest.raises(ValueError, match="source_summaries must be ordered"):
        PaperStrategyRecommendationHistoryReport(
            generated_at=GENERATED_AT,
            config_version="recommendation-history-v0",
            source_report_count=2,
            total_candidate_count=2,
            total_recommend_count=1,
            total_watch_count=1,
            total_reject_count=0,
            first_generated_at=older.generated_at,
            latest_generated_at=newer.generated_at,
            latest_config_version="strategy-recommendation-v0",
            latest_candidate_count=1,
            latest_recommend_count=0,
            latest_watch_count=1,
            latest_reject_count=0,
            latest_top_recommendation_score=Decimal("0.300000"),
            best_observed_recommendation_score=Decimal("0.600000"),
            average_recommendation_score=Decimal("0.450000"),
            latest_average_recommendation_score=Decimal("0.300000"),
            source_summaries=(newer, older),
        )


def test_strategy_recommendation_history_is_not_package_root_exported():
    import polymarket_alpha_lab

    assert not hasattr(polymarket_alpha_lab, "PaperStrategyRecommendationHistoryReport")
    assert not hasattr(
        polymarket_alpha_lab,
        "build_paper_strategy_recommendation_history_report",
    )
