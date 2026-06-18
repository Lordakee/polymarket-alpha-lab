from dataclasses import replace
from datetime import UTC, datetime
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


def test_strategy_recommendation_history_normalizes_unsorted_input():
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


def test_strategy_recommendation_history_rejects_invalid_source_type_and_flags():
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

    object.__setattr__(valid_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _history_report(valid_report)
    object.__setattr__(valid_report, "paper_only", True)
    object.__setattr__(valid_report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _history_report(valid_report)
    object.__setattr__(valid_report, "report_only", True)
    object.__setattr__(valid_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _history_report(valid_report)


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
        {"paper_only": False},
        {"report_only": False},
        {"readonly": False},
    )

    for changes in invalid_changes:
        with pytest.raises(ValueError):
            replace(history, **changes)


def test_strategy_recommendation_history_direct_constructor_requires_deterministic_summaries():
    older = PaperStrategyRecommendationHistorySourceSummary(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
    )
    newer = PaperStrategyRecommendationHistorySourceSummary(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        config_version="strategy-recommendation-v0",
        candidate_count=1,
        recommend_count=0,
        watch_count=1,
        reject_count=0,
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
            source_summaries=(newer, older),
        )


def test_strategy_recommendation_history_is_not_package_root_exported():
    import polymarket_alpha_lab

    assert not hasattr(polymarket_alpha_lab, "PaperStrategyRecommendationHistoryReport")
    assert not hasattr(
        polymarket_alpha_lab,
        "build_paper_strategy_recommendation_history_report",
    )
