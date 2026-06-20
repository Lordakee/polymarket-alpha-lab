from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab import (
    action_gated_strategy_recommendation_queue_priority as priority_module,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueuePriorityRow,
    build_paper_action_gated_strategy_recommendation_queue_priority_report,
)
from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
)
from polymarket_alpha_lab.strategy_recommendation_queue import (
    PaperStrategyRecommendationQueueRow,
    PaperStrategyRecommendationQueueSummaryReport,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class ActionGatedQueueReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _empty_candidate_assessment_report() -> PaperCandidateAssessmentReport:
    return PaperCandidateAssessmentReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="candidate-assessment-v1",
        candidate_count=0,
        assessed_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        assessment_rows=(),
    )


def _empty_bundle_report() -> PaperStrategyRecommendationBundleReport:
    recommendation_report = PaperStrategyCandidateRecommendationReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="strategy-candidate-recommendation-v1",
        readiness_overall_status="pass",
        candidate_count=0,
        recommend_count=0,
        watch_count=0,
        reject_count=0,
        recommendation_rows=(),
    )
    selection_policy_report = PaperStrategySelectionPolicyReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="strategy-selection-policy-v1",
        row_count=0,
        selected_count=0,
        skipped_count=0,
        not_selected_count=0,
        total_selected_notional=ZERO,
        selection_rows=(),
    )
    explanation_report = PaperStrategyRecommendationExplanationReport(
        generated_at=SOURCE_GENERATED_AT,
        source_config_version=recommendation_report.config_version,
        recommendation_count=0,
        recommend_count=0,
        watch_count=0,
        reject_count=0,
        explanation_rows=(),
    )
    return PaperStrategyRecommendationBundleReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="strategy-recommendation-bundle-v1",
        candidate_count=0,
        recommend_count=0,
        selected_count=0,
        total_selected_notional=ZERO,
        recommendation_report=recommendation_report,
        selection_policy_report=selection_policy_report,
        explanation_report=explanation_report,
    )


def _queue_row(
    rank: int,
    market_slug: str,
    *,
    recommendation_score: Decimal,
    suggested_notional: Decimal,
) -> PaperStrategyRecommendationQueueRow:
    return PaperStrategyRecommendationQueueRow(
        rank=rank,
        market_slug=market_slug,
        selected_side="yes",
        action="recommend",
        decision="selected",
        recommendation_score=recommendation_score,
        suggested_notional=suggested_notional,
        primary_reason_code="selected_by_policy",
        queue_status="ready",
    )


def _queue_summary(
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> PaperStrategyRecommendationQueueSummaryReport:
    return PaperStrategyRecommendationQueueSummaryReport(
        generated_at=SOURCE_GENERATED_AT,
        source_config_version="strategy-recommendation-bundle-v1",
        queue_count=len(rows),
        ready_count=len(rows),
        watch_count=0,
        blocked_count=0,
        total_ready_notional=sum((row.suggested_notional for row in rows), ZERO),
        top_score=rows[0].recommendation_score if rows else ZERO,
        average_ready_score=(
            sum((row.recommendation_score for row in rows), ZERO) / Decimal(len(rows))
            if rows
            else ZERO
        ),
        primary_reason_code_counts=(("selected_by_policy", len(rows)),) if rows else (),
        queue_rows=rows,
    )


def _ready_report(
    config_version: str,
    *,
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> PaperActionGatedStrategyRecommendationQueueReport:
    queue_summary = _queue_summary(rows)
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version=config_version,
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        reason_code_counts=(),
        candidate_count=queue_summary.queue_count,
        ready_count=queue_summary.ready_count,
        watch_count=queue_summary.watch_count,
        blocked_count=queue_summary.blocked_count,
        total_ready_notional=queue_summary.total_ready_notional,
        candidate_assessment_report=_empty_candidate_assessment_report(),
        bundle_report=_empty_bundle_report(),
        queue_summary_report=queue_summary,
    )


def _non_ready_report(
    config_version: str,
    *,
    action_status: str,
    recommended_next_step: str,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version=config_version,
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=(),
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=ZERO,
    )


def test_priority_report_ranks_research_ready_reports_before_watch_and_blocked():
    ready_low = _ready_report(
        "action-gated-queue-ready-low",
        rows=(
            _queue_row(
                1,
                "alpha-ready-low",
                recommendation_score=d("0.700000"),
                suggested_notional=d("12.000000"),
            ),
        ),
    )
    ready_high = _ready_report(
        "action-gated-queue-ready-high",
        rows=(
            _queue_row(
                1,
                "alpha-ready-high",
                recommendation_score=d("0.900000"),
                suggested_notional=d("10.000000"),
            ),
            _queue_row(
                2,
                "beta-ready-high",
                recommendation_score=d("0.500000"),
                suggested_notional=d("6.000000"),
            ),
        ),
    )
    watch = _non_ready_report(
        "action-gated-queue-watch",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
    )
    blocked = _non_ready_report(
        "action-gated-queue-blocked",
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
    )

    report = build_paper_action_gated_strategy_recommendation_queue_priority_report(
        (blocked, ready_low, watch, ready_high),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperActionGatedStrategyRecommendationQueuePriorityReport)
    assert report.generated_at == GENERATED_AT
    assert report.source_report_count == 4
    assert report.research_ready_count == 2
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.total_ready_notional == d("28.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.config_version for row in report.priority_rows) == (
        "action-gated-queue-ready-high",
        "action-gated-queue-ready-low",
        "action-gated-queue-watch",
        "action-gated-queue-blocked",
    )
    assert tuple(row.priority_rank for row in report.priority_rows) == (1, 2, 3, 4)
    assert tuple(row.research_priority for row in report.priority_rows) == (
        "research_review",
        "research_review",
        "await_fresh_context",
        "repair_evidence",
    )
    assert report.priority_rows[0].top_queue_score == d("0.900000")
    assert report.priority_rows[0].average_ready_score == d("0.700000")
    assert report.priority_rows[0].research_priority_score > (
        report.priority_rows[1].research_priority_score
    )
    assert type(report.priority_rows[0].research_priority_score) is Decimal
    assert report.top_research_priority_score == (
        report.priority_rows[0].research_priority_score
    )


def test_priority_report_top_score_uses_max_score_not_first_ranked_row():
    high_count_lower_score = _ready_report(
        "action-gated-queue-high-count-lower-score",
        rows=(
            _queue_row(
                1,
                "alpha-high-count",
                recommendation_score=d("0.100000"),
                suggested_notional=d("8.000000"),
            ),
            _queue_row(
                2,
                "beta-high-count",
                recommendation_score=d("0.100000"),
                suggested_notional=d("7.000000"),
            ),
        ),
    )
    lower_count_higher_score = _ready_report(
        "action-gated-queue-lower-count-higher-score",
        rows=(
            _queue_row(
                1,
                "alpha-higher-score",
                recommendation_score=d("1.000000"),
                suggested_notional=d("10.000000"),
            ),
        ),
    )

    report = build_paper_action_gated_strategy_recommendation_queue_priority_report(
        (lower_count_higher_score, high_count_lower_score),
        generated_at=GENERATED_AT,
    )

    assert tuple(row.config_version for row in report.priority_rows) == (
        "action-gated-queue-high-count-lower-score",
        "action-gated-queue-lower-count-higher-score",
    )
    assert report.priority_rows[0].research_priority_score == d("5.200000")
    assert report.priority_rows[1].research_priority_score == d("6.000000")
    assert report.top_research_priority_score == d("6.000000")


def test_priority_report_accepts_empty_input_and_normalizes_generated_at_to_utc():
    eastern = timezone(timedelta(hours=-4))

    report = build_paper_action_gated_strategy_recommendation_queue_priority_report(
        (),
        generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.source_report_count == 0
    assert report.research_ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_ready_notional == ZERO
    assert report.top_research_priority_score == ZERO
    assert report.average_research_priority_score == ZERO
    assert report.priority_rows == ()


def test_priority_dataclasses_are_frozen_and_validate_invariants():
    source = _ready_report(
        "action-gated-queue-ready",
        rows=(
            _queue_row(
                1,
                "alpha-ready",
                recommendation_score=d("0.800000"),
                suggested_notional=d("10.000000"),
            ),
        ),
    )
    report = build_paper_action_gated_strategy_recommendation_queue_priority_report(
        (source,),
        generated_at=GENERATED_AT,
    )
    row = report.priority_rows[0]

    with pytest.raises(FrozenInstanceError):
        report.source_report_count = 99
    with pytest.raises(FrozenInstanceError):
        row.priority_rank = 99
    with pytest.raises(ValueError, match="source_report_count"):
        replace(report, source_report_count=99)
    with pytest.raises(ValueError, match="priority_rank"):
        replace(row, priority_rank=0)
    with pytest.raises(ValueError, match="research_priority"):
        replace(row, research_priority="await_fresh_context")
    with pytest.raises(ValueError, match="research_priority_score"):
        replace(row, research_priority_score=d("99.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    with pytest.raises(ValueError, match="research_priority_score"):
        PaperActionGatedStrategyRecommendationQueuePriorityRow(
            priority_rank=1,
            source_generated_at=SOURCE_GENERATED_AT,
            config_version="action-gated-queue-ready",
            source_config_version="paper-recommendation-cycle-action-gate-v0",
            action_status="research_ready",
            recommended_next_step="review_candidate_research_queue",
            research_priority="research_review",
            candidate_count=1,
            ready_count=1,
            watch_count=0,
            blocked_count=0,
            total_ready_notional=d("10.000000"),
            top_queue_score=d("0.800000"),
            average_ready_score=d("0.800000"),
            research_priority_score=0.8,
        )
    with pytest.raises(ValueError, match="recommended_next_step"):
        PaperActionGatedStrategyRecommendationQueuePriorityRow(
            priority_rank=1,
            source_generated_at=SOURCE_GENERATED_AT,
            config_version="action-gated-queue-watch",
            source_config_version="paper-recommendation-cycle-action-gate-v0",
            action_status="watch",
            recommended_next_step="repair_cycle_evidence",
            research_priority="await_fresh_context",
            candidate_count=0,
            ready_count=0,
            watch_count=0,
            blocked_count=0,
            total_ready_notional=ZERO,
            top_queue_score=ZERO,
            average_ready_score=ZERO,
            research_priority_score=d("1.000000"),
        )


def test_priority_builder_rejects_wrong_types_subclasses_and_unsafe_inputs():
    source = _non_ready_report(
        "action-gated-queue-watch",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
    )

    with pytest.raises(ValueError, match="reports"):
        build_paper_action_gated_strategy_recommendation_queue_priority_report(
            (object(),),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueReport",
    ):
        build_paper_action_gated_strategy_recommendation_queue_priority_report(
            (ActionGatedQueueReportSubclass(**source.__dict__),),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_action_gated_strategy_recommendation_queue_priority_report(
            (source,),
            generated_at="2026-06-20",
        )

    object.__setattr__(source, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        build_paper_action_gated_strategy_recommendation_queue_priority_report(
            (source,),
            generated_at=GENERATED_AT,
        )


def test_priority_module_stays_pure_and_readonly_by_import_boundary():
    tree = ast.parse(inspect.getsource(priority_module))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_imports = {
        "os",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
    }

    assert imported_modules.isdisjoint(forbidden_imports)
