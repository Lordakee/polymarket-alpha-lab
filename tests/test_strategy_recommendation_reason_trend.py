from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
)
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
    build_paper_strategy_readiness_state_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
    PaperStrategyRecommendationBundleReport,
    build_paper_strategy_recommendation_bundle_report,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    NO_REASON_CODE,
    PaperStrategyRecommendationExplanationReport,
    PaperStrategyRecommendationExplanationRow,
)
from polymarket_alpha_lab.strategy_recommendation_history import (
    PaperStrategyRecommendationHistoryReport,
)
from polymarket_alpha_lab.strategy_recommendation_reason_trend import (
    PaperStrategyRecommendationReasonTrendConfig,
    PaperStrategyRecommendationReasonTrendReport,
    build_paper_strategy_recommendation_reason_trend_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


def _config(**overrides) -> PaperStrategyRecommendationReasonTrendConfig:
    values = {
        "config_version": "strategy-recommendation-reason-trend-v0",
        "max_blocked_reason_share": Decimal("0.500000"),
        "max_no_reason_code_share": Decimal("0.500000"),
        "top_reason_code_limit": 5,
        "blocked_reason_codes": (
            "blocked_forecast_quality",
            "blocked_risk_drawdown",
            "incomplete_data",
            "missing_cost_report",
        ),
    }
    values.update(overrides)
    return PaperStrategyRecommendationReasonTrendConfig(**values)


def _explain_report(
    *,
    generated_at: datetime,
    reason_codes: tuple[str, ...],
    source_config_version: str = "strategy-candidate-recommendation-v1",
) -> PaperStrategyRecommendationExplanationReport:
    rows = tuple(
        _explain_row(index, reason_code)
        for index, reason_code in enumerate(reason_codes, start=1)
    )
    return PaperStrategyRecommendationExplanationReport(
        generated_at=generated_at,
        source_config_version=source_config_version,
        recommendation_count=len(rows),
        recommend_count=0,
        watch_count=len(rows),
        reject_count=0,
        explanation_rows=rows,
    )


def _explain_row(
    index: int,
    reason_code: str,
) -> PaperStrategyRecommendationExplanationRow:
    reason_codes = () if reason_code == NO_REASON_CODE else (reason_code,)
    score = Decimal("0.100000")
    return PaperStrategyRecommendationExplanationRow(
        market_slug=f"reason-market-{index}",
        action="watch",
        selected_side="none",
        recommendation_score=score,
        primary_reason_code=reason_code,
        reason_codes=reason_codes,
        explanation=f"watch none because {reason_code} (score {score})",
    )


def _empty_history_report(
    *,
    generated_at: datetime,
) -> PaperStrategyRecommendationHistoryReport:
    return PaperStrategyRecommendationHistoryReport(
        generated_at=generated_at,
        config_version="strategy-recommendation-history-v1",
        source_report_count=0,
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


def test_reason_trend_empty_input_is_readonly_report_only_stable():
    trend = build_paper_strategy_recommendation_reason_trend_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(trend, PaperStrategyRecommendationReasonTrendReport)
    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == "strategy-recommendation-reason-trend-v0"
    assert trend.source_report_count == 0
    assert trend.first_generated_at is None
    assert trend.latest_generated_at is None
    assert trend.latest_primary_reason_code_counts == ()
    assert trend.total_primary_reason_code_counts == ()
    assert trend.top_new_reason_codes == ()
    assert trend.persistent_reason_codes == ()
    assert trend.latest_reason_code_count == 0
    assert trend.latest_no_reason_code_count == 0
    assert trend.latest_blocked_reason_count == 0
    assert trend.latest_no_reason_code_share is None
    assert trend.latest_blocked_reason_share is None
    assert trend.status == "stable"
    assert trend.source_summaries == ()
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True


def test_reason_trend_uses_append_sequence_for_first_latest_and_aggregates_counts():
    first_append = _explain_report(
        generated_at=datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
        reason_codes=("alpha", "beta", "beta"),
    )
    earlier_timestamp = _explain_report(
        generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        reason_codes=("alpha", "gamma"),
    )
    latest_append = _explain_report(
        generated_at=datetime(2026, 6, 19, 13, 0, tzinfo=UTC),
        reason_codes=("gamma", "gamma", "alpha", NO_REASON_CODE),
    )

    trend = build_paper_strategy_recommendation_reason_trend_report(
        (first_append, earlier_timestamp, latest_append),
        config=_config(max_no_reason_code_share=Decimal("1.000000")),
        generated_at=GENERATED_AT,
    )

    assert trend.source_report_count == 3
    assert trend.first_generated_at == first_append.generated_at
    assert trend.latest_generated_at == latest_append.generated_at
    assert trend.latest_primary_reason_code_counts == (
        ("gamma", 2),
        ("alpha", 1),
        (NO_REASON_CODE, 1),
    )
    assert trend.total_primary_reason_code_counts == (
        ("alpha", 3),
        ("gamma", 3),
        ("beta", 2),
        (NO_REASON_CODE, 1),
    )
    assert trend.latest_reason_code_count == 4
    assert trend.latest_no_reason_code_count == 1
    assert trend.latest_no_reason_code_share == Decimal("0.250000")
    assert trend.latest_blocked_reason_share == Decimal("0.000000")
    assert tuple(summary.generated_at for summary in trend.source_summaries) == (
        first_append.generated_at,
        earlier_timestamp.generated_at,
        latest_append.generated_at,
    )


def test_reason_trend_reports_new_and_persistent_reason_codes_deterministically():
    trend = build_paper_strategy_recommendation_reason_trend_report(
        (
            _explain_report(
                generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
                reason_codes=("shared", "old_only"),
            ),
            _explain_report(
                generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
                reason_codes=("shared", "old_only", "seen_before"),
            ),
            _explain_report(
                generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
                reason_codes=("shared", "new_high", "new_low", "new_high"),
            ),
        ),
        config=_config(top_reason_code_limit=2),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_primary_reason_code_counts == (
        ("new_high", 2),
        ("new_low", 1),
        ("shared", 1),
    )
    assert trend.top_new_reason_codes == (
        ("new_high", 2),
        ("new_low", 1),
    )
    assert trend.persistent_reason_codes == ("shared",)
    assert trend.status == "watch"


def test_reason_trend_single_source_baseline_has_no_new_reason_drift():
    trend = build_paper_strategy_recommendation_reason_trend_report(
        (
            _explain_report(
                generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
                reason_codes=("baseline_only", "baseline_only"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.top_new_reason_codes == ()
    assert trend.persistent_reason_codes == ("baseline_only",)
    assert trend.status == "stable"


def test_reason_trend_blocks_when_latest_blocked_reason_share_is_too_high():
    trend = build_paper_strategy_recommendation_reason_trend_report(
        (
            _explain_report(
                generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
                reason_codes=("blocked_forecast_quality", "alpha"),
            ),
            _explain_report(
                generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
                reason_codes=(
                    "blocked_forecast_quality",
                    "blocked_forecast_quality",
                    "alpha",
                ),
            ),
        ),
        config=_config(max_blocked_reason_share=Decimal("0.500000")),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_blocked_reason_count == 2
    assert trend.latest_blocked_reason_share == Decimal("0.666667")
    assert trend.status == "blocked"


def test_reason_trend_blocks_when_latest_no_reason_share_is_too_high():
    trend = build_paper_strategy_recommendation_reason_trend_report(
        (
            _explain_report(
                generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
                reason_codes=(NO_REASON_CODE, "alpha"),
            ),
            _explain_report(
                generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
                reason_codes=(NO_REASON_CODE, NO_REASON_CODE, "alpha"),
            ),
        ),
        config=_config(max_no_reason_code_share=Decimal("0.500000")),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_no_reason_code_count == 2
    assert trend.latest_no_reason_code_share == Decimal("0.666667")
    assert trend.status == "blocked"


def test_reason_trend_accepts_bundle_explain_and_empty_history_reports():
    explain_report = _explain_report(
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
        reason_codes=("explain_reason",),
    )
    history_report = _empty_history_report(
        generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )
    bundle_report = _bundle_report(
        generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
    )

    trend = build_paper_strategy_recommendation_reason_trend_report(
        (explain_report, history_report, bundle_report),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(bundle_report, PaperStrategyRecommendationBundleReport)
    assert trend.source_report_count == 3
    assert trend.first_generated_at == explain_report.generated_at
    assert trend.latest_generated_at == bundle_report.generated_at
    assert trend.latest_primary_reason_code_counts == (
        ("bundle_reason", 1),
    )
    assert trend.total_primary_reason_code_counts == (
        ("bundle_reason", 1),
        ("explain_reason", 1),
    )


def test_reason_trend_normalizes_datetimes_to_utc_and_quantizes_config_shares():
    generated_at = datetime(2026, 6, 19, 14, 0, tzinfo=timezone(timedelta(hours=2)))
    source_generated_at = datetime(
        2026,
        6,
        19,
        13,
        0,
        tzinfo=timezone(timedelta(hours=2)),
    )

    trend = build_paper_strategy_recommendation_reason_trend_report(
        (
            _explain_report(
                generated_at=source_generated_at,
                reason_codes=("alpha", "beta"),
            ),
        ),
        config=_config(
            max_blocked_reason_share=Decimal("0.5000004"),
            max_no_reason_code_share=Decimal("0.2500004"),
        ),
        generated_at=generated_at,
    )

    assert trend.generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert trend.first_generated_at == datetime(2026, 6, 19, 11, 0, tzinfo=UTC)
    assert trend.latest_generated_at == datetime(2026, 6, 19, 11, 0, tzinfo=UTC)


def test_reason_trend_rejects_invalid_inputs_and_false_hard_flags():
    report = _explain_report(
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
        reason_codes=("alpha",),
    )

    for reports in (
        object(),
        "not reports",
        b"not reports",
        {"report": report},
        (item for item in (report,)),
    ):
        with pytest.raises(ValueError, match="reports must be a list or tuple"):
            build_paper_strategy_recommendation_reason_trend_report(
                reports,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="reports must contain"):
        build_paper_strategy_recommendation_reason_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        build_paper_strategy_recommendation_reason_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_strategy_recommendation_reason_trend_report(
            (),
            config=_config(),
            generated_at=object(),
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        report_with_false_flag = _explain_report(
            generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
            reason_codes=("alpha",),
        )
        object.__setattr__(report_with_false_flag, flag_name, False)
        with pytest.raises(ValueError, match=f"reports must contain {flag_name}"):
            build_paper_strategy_recommendation_reason_trend_report(
                (report_with_false_flag,),
                config=_config(),
                generated_at=GENERATED_AT,
            )


def test_reason_trend_dataclasses_are_frozen_and_revalidate_invariants():
    config = _config()
    trend = build_paper_strategy_recommendation_reason_trend_report(
        (
            _explain_report(
                generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
                reason_codes=("alpha",),
            ),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        trend.status = "stable"
    with pytest.raises(ValueError, match="paper_only"):
        replace(trend, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(trend, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(trend, readonly=False)
    with pytest.raises(ValueError, match="latest_primary_reason_code_counts"):
        replace(trend, latest_primary_reason_code_counts=(("other", 1),))
    with pytest.raises(ValueError, match="total_primary_reason_code_counts"):
        replace(trend, total_primary_reason_code_counts=(("other", 1),))
    with pytest.raises(ValueError, match="status"):
        replace(trend, status="blocked")


def test_reason_trend_config_rejects_non_decimal_and_out_of_range_shares():
    with pytest.raises(ValueError, match="max_blocked_reason_share"):
        PaperStrategyRecommendationReasonTrendConfig(
            config_version="strategy-recommendation-reason-trend-v0",
            max_blocked_reason_share=0.5,
        )
    with pytest.raises(ValueError, match="max_no_reason_code_share"):
        PaperStrategyRecommendationReasonTrendConfig(
            config_version="strategy-recommendation-reason-trend-v0",
            max_no_reason_code_share=Decimal("1.000001"),
        )
    with pytest.raises(ValueError, match="top_reason_code_limit"):
        PaperStrategyRecommendationReasonTrendConfig(
            config_version="strategy-recommendation-reason-trend-v0",
            top_reason_code_limit=0,
        )


def _bundle_report(
    *,
    generated_at: datetime,
) -> PaperStrategyRecommendationBundleReport:
    return build_paper_strategy_recommendation_bundle_report(
        _assessment_report(),
        build_paper_strategy_readiness_state_report(
            (
                PaperStrategyReadinessSignal(
                    source_name="paper_gate",
                    status="pass",
                    reason_codes=("readiness_input_passed",),
                    severity=10,
                ),
            ),
            config_version="strategy-readiness-state-v1",
            generated_at=generated_at,
        ),
        config=PaperStrategyRecommendationBundleConfig(
            config_version="strategy-recommendation-bundle-v1",
            recommendation_config=PaperStrategyCandidateRecommendationConfig(
                config_version="strategy-candidate-recommendation-v1",
                min_recommendation_score=Decimal("0.100000"),
            ),
            selection_policy_config=PaperStrategySelectionPolicyConfig(
                config_version="strategy-selection-policy-v1",
                base_position_notional=Decimal("20.000000"),
                max_position_notional=Decimal("12.000000"),
                max_total_notional=Decimal("20.000000"),
            ),
        ),
        generated_at=generated_at,
    )


def _assessment_report() -> PaperCandidateAssessmentReport:
    rows = (
        PaperCandidateAssessmentRow(
            market_slug="bundle-market",
            question="Will bundle-market resolve yes?",
            research_bucket="research_ready",
            assessment_status="ready",
            source_status="paper_review_ready",
            selected_side="yes",
            scoring_side="yes",
            screening_score=Decimal("0.600000"),
            net_edge_per_share=Decimal("0.600000"),
            total_cost_per_share=Decimal("0.000000"),
            confidence=Decimal("0.9000"),
            spread=Decimal("0.0100"),
            resolution_risk=Decimal("0.0200"),
            readiness_score=Decimal("0.600000"),
            reason_codes=("bundle_reason",),
        ),
    )
    return PaperCandidateAssessmentReport(
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=UTC),
        config_version="candidate-assessment-v1",
        candidate_count=len(rows),
        assessed_count=len(rows),
        ready_count=1,
        watch_count=0,
        blocked_count=0,
        assessment_rows=rows,
    )
