from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.candidate_assessment import PaperCandidateAssessmentReport
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueConfig,
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
    build_paper_strategy_candidate_research_queue_report,
)
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
    build_paper_strategy_readiness_state_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
    build_paper_strategy_recommendation_bundle_report,
)
from polymarket_alpha_lab.strategy_recommendation_queue import (
    build_paper_strategy_recommendation_queue_summary_report,
)


SOURCE_GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
NESTED_GENERATED_AT = datetime(2026, 6, 20, 12, 15, tzinfo=UTC)
RESEARCH_GENERATED_AT = datetime(2026, 6, 20, 12, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class SourceReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def _reason_count(
    reason_code: str,
    count: int,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _research_config() -> PaperStrategyCandidateResearchQueueConfig:
    return PaperStrategyCandidateResearchQueueConfig(
        config_version="strategy-candidate-research-queue-v0",
    )


def _recommendation_bundle_config() -> PaperStrategyRecommendationBundleConfig:
    return PaperStrategyRecommendationBundleConfig(
        config_version="strategy-recommendation-bundle-v1",
        recommendation_config=PaperStrategyCandidateRecommendationConfig(
            config_version="strategy-candidate-recommendation-v1",
            min_recommendation_score=Decimal("0.100000"),
        ),
        selection_policy_config=PaperStrategySelectionPolicyConfig(
            config_version="strategy-selection-policy-v1",
            base_position_notional=Decimal("10.000000"),
            max_position_notional=Decimal("12.000000"),
            max_total_notional=Decimal("20.000000"),
        ),
    )


def _empty_candidate_assessment_report() -> PaperCandidateAssessmentReport:
    return PaperCandidateAssessmentReport(
        generated_at=NESTED_GENERATED_AT,
        config_version="candidate-assessment-v1",
        candidate_count=0,
        assessed_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        assessment_rows=(),
    )


def _empty_nested_reports():
    candidate_assessment_report = _empty_candidate_assessment_report()
    readiness_report = build_paper_strategy_readiness_state_report(
        (
            PaperStrategyReadinessSignal(
                source_name="cycle_action_gate",
                status="pass",
                reason_codes=("action_gate_research_ready",),
                severity=10,
                observed_value="research_ready",
                threshold="research_ready",
            ),
        ),
        config_version="strategy-readiness-state-v1",
        generated_at=NESTED_GENERATED_AT,
    )
    bundle_report = build_paper_strategy_recommendation_bundle_report(
        candidate_assessment_report,
        readiness_report,
        config=_recommendation_bundle_config(),
        generated_at=NESTED_GENERATED_AT,
    )
    queue_summary_report = build_paper_strategy_recommendation_queue_summary_report(
        bundle_report,
    )
    return candidate_assessment_report, bundle_report, queue_summary_report


def _source_report(
    *,
    action_status: str,
    recommended_next_step: str,
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
    nested_empty_reports: bool = False,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    nested_kwargs = {}
    if nested_empty_reports:
        (
            candidate_assessment_report,
            bundle_report,
            queue_summary_report,
        ) = _empty_nested_reports()
        nested_kwargs = {
            "candidate_assessment_report": candidate_assessment_report,
            "bundle_report": bundle_report,
            "queue_summary_report": queue_summary_report,
        }

    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=reason_code_counts,
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=ZERO,
        **nested_kwargs,
    )


def _watch_source_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    return _source_report(
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(
            _reason_count("cycle_history_stale", 1),
            _reason_count("cycle_review_watch", 1),
        ),
    )


def _blocked_source_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    return _source_report(
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
        reason_code_counts=(
            _reason_count("cycle_review_blocked", 1),
            _reason_count("pipeline_final_status_blocked", 1),
        ),
    )


def _ready_empty_source_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    return _source_report(
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        reason_code_counts=(_reason_count("cycle_review_pass", 1),),
        nested_empty_reports=True,
    )


def _build_report(
    source_report,
    *,
    config=None,
    generated_at=RESEARCH_GENERATED_AT,
):
    return build_paper_strategy_candidate_research_queue_report(
        source_report,
        config=config or _research_config(),
        generated_at=generated_at,
    )


def _assert_zero_counts_totals_and_scores(
    report: PaperStrategyCandidateResearchQueueReport,
) -> None:
    assert report.candidate_count == 0
    assert report.research_ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.selected_count == 0
    assert report.skipped_count == 0
    assert report.not_selected_count == 0
    assert report.total_ready_notional == ZERO
    assert report.total_selected_notional == ZERO
    assert report.total_suggested_notional == ZERO
    assert report.top_research_priority_score == ZERO
    assert report.average_research_ready_score == ZERO
    assert report.primary_reason_code_counts == ()
    assert type(report.total_ready_notional) is Decimal
    assert type(report.total_selected_notional) is Decimal
    assert type(report.total_suggested_notional) is Decimal
    assert type(report.top_research_priority_score) is Decimal
    assert type(report.average_research_ready_score) is Decimal
    assert report.rows == ()


def test_blocked_source_returns_empty_blocked_research_queue_without_nested_join():
    source = _blocked_source_report()
    assert source.candidate_assessment_report is None
    assert source.bundle_report is None
    assert source.queue_summary_report is None

    report = _build_report(source)

    assert isinstance(report, PaperStrategyCandidateResearchQueueReport)
    assert PaperStrategyCandidateResearchQueueRow is not None
    assert report.generated_at == RESEARCH_GENERATED_AT
    assert report.config_version == "strategy-candidate-research-queue-v0"
    assert report.source_config_version == source.config_version
    assert report.action_status == "blocked"
    assert report.recommended_next_step == "repair_cycle_evidence"
    assert report.research_status == "blocked"
    assert report.reason_codes == ("source_action_status_blocked",)
    assert report.source_reason_code_counts == source.reason_code_counts
    _assert_zero_counts_totals_and_scores(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_watch_source_returns_empty_queue_without_downstream_inputs():
    source = _watch_source_report()
    assert source.candidate_assessment_report is None
    assert source.bundle_report is None
    assert source.queue_summary_report is None

    report = _build_report(source)

    assert report.source_config_version == source.config_version
    assert report.action_status == "watch"
    assert report.recommended_next_step == "await_fresh_cycle_evidence"
    assert report.research_status == "watch"
    assert report.reason_codes == ("source_action_status_watch",)
    assert report.source_reason_code_counts == source.reason_code_counts
    _assert_zero_counts_totals_and_scores(report)


def test_research_ready_source_with_empty_nested_reports_returns_no_candidates_watch():
    source = _ready_empty_source_report()
    assert source.candidate_assessment_report is not None
    assert source.bundle_report is not None
    assert source.queue_summary_report is not None
    assert source.queue_summary_report.queue_rows == ()

    report = _build_report(source)

    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "review_candidate_research_queue"
    assert report.research_status == "watch"
    assert report.reason_codes == ("no_candidate_research_rows",)
    assert report.source_reason_code_counts == source.reason_code_counts
    _assert_zero_counts_totals_and_scores(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reducer_rejects_wrong_types_subclass_source_and_false_hard_flags():
    source = _watch_source_report()

    with pytest.raises(
        ValueError,
        match="PaperStrategyCandidateResearchQueueConfig",
    ):
        _build_report(source, config=object())
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(source, generated_at="2026-06-20")

    subclass_source = SourceReportSubclass(**source.__dict__)
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueReport",
    ):
        _build_report(subclass_source)

    source_with_false_flag = _watch_source_report()
    object.__setattr__(source_with_false_flag, "readonly", False)
    with pytest.raises(ValueError, match="source_report must be readonly"):
        _build_report(source_with_false_flag)

    config_with_false_flag = _research_config()
    object.__setattr__(config_with_false_flag, "report_only", False)
    with pytest.raises(ValueError, match="config must be report_only"):
        _build_report(source, config=config_with_false_flag)
