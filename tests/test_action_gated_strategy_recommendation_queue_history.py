from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
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
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class ActionGatedQueueReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _history_module():
    module_name = "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history"
    spec = importlib.util.find_spec(module_name)
    assert spec is not None, "history module should exist"
    return importlib.import_module(module_name)


def _reason_count(
    reason_code: str,
    count: int,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


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
    generated_at: datetime,
    *,
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
) -> PaperActionGatedStrategyRecommendationQueueReport:
    queue_summary = _queue_summary(rows)
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        reason_code_counts=reason_code_counts,
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
    generated_at: datetime,
    *,
    action_status: str,
    recommended_next_step: str,
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
) -> PaperActionGatedStrategyRecommendationQueueReport:
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=reason_code_counts,
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=ZERO,
    )


def _build_history_report(queue_reports, *, generated_at=GENERATED_AT):
    module = _history_module()
    return module.build_paper_action_gated_strategy_recommendation_queue_history_report(
        queue_reports,
        generated_at=generated_at,
    )


def test_history_report_orders_sources_and_summarizes_latest_trends():
    oldest_ready = _ready_report(
        "action-gated-queue-oldest-ready",
        datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        rows=(
            _queue_row(
                1,
                "alpha-ready",
                recommendation_score=d("0.800000"),
                suggested_notional=d("10.000000"),
            ),
        ),
        reason_code_counts=(_reason_count("cycle_review_passed", 2),),
    )
    tie_watch = _non_ready_report(
        "action-gated-queue-watch",
        datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(_reason_count("cycle_review_watch", 1),),
    )
    latest_blocked = _non_ready_report(
        "action-gated-queue-z-blocked",
        datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
        reason_code_counts=(_reason_count("cycle_review_blocked", 3),),
    )

    report = _build_history_report((latest_blocked, tie_watch, oldest_ready))

    module = _history_module()
    assert isinstance(
        report,
        module.PaperActionGatedStrategyRecommendationQueueHistoryReport,
    )
    assert report.generated_at == GENERATED_AT
    assert report.source_report_count == 3
    assert report.first_source_generated_at == datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
    assert report.last_source_generated_at == datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
    assert report.research_ready_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.total_ready_notional == d("10.000000")
    assert report.latest_action_status == "blocked"
    assert report.latest_recommended_next_step == "repair_cycle_evidence"
    assert report.status_transition_count == 2
    assert report.ready_notional_delta == d("-10.000000")
    assert tuple(
        (row.reason_code, row.count) for row in report.latest_reason_code_counts
    ) == (("cycle_review_blocked", 3),)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_report_accepts_empty_input_and_normalizes_report_generated_at():
    eastern = timezone(timedelta(hours=-4))

    report = _build_history_report(
        (),
        generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.source_report_count == 0
    assert report.first_source_generated_at is None
    assert report.last_source_generated_at is None
    assert report.research_ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_ready_notional == ZERO
    assert report.latest_action_status is None
    assert report.latest_recommended_next_step is None
    assert report.status_transition_count == 0
    assert report.ready_notional_delta == ZERO
    assert report.latest_reason_code_counts == ()


def test_history_rejects_wrong_types_subclasses_flags_and_invalid_replacements():
    source = _non_ready_report(
        "action-gated-queue-watch",
        SOURCE_GENERATED_AT,
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(_reason_count("cycle_review_watch", 1),),
    )

    with pytest.raises(ValueError, match="reports"):
        _build_history_report("not reports")
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueReport",
    ):
        _build_history_report((object(),))
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueReport",
    ):
        _build_history_report((ActionGatedQueueReportSubclass(**source.__dict__),))
    with pytest.raises(ValueError, match="generated_at"):
        _build_history_report((source,), generated_at="2026-06-20")

    object.__setattr__(source, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _build_history_report((source,))

    clean_source = _non_ready_report(
        "action-gated-queue-watch",
        SOURCE_GENERATED_AT,
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(_reason_count("cycle_review_watch", 1),),
    )
    report = _build_history_report((clean_source,))

    with pytest.raises(FrozenInstanceError):
        report.source_report_count = 99
    with pytest.raises(ValueError, match="source_report_count"):
        replace(report, source_report_count=99)
    with pytest.raises(ValueError, match="ready_notional_delta"):
        replace(report, ready_notional_delta=object())
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_history_module_stays_pure_readonly_and_decimal_only_by_import_boundary():
    module = _history_module()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()
    float_literals: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)

    allowed_imports = {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue",
        "polymarket_alpha_lab.paper_recommendation_cycle_action_gate",
    }
    forbidden_calls = {
        "cancel_order",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "getenv",
        "open",
        "place_order",
        "read",
        "rollback",
        "sign_order",
        "submit_order",
        "write",
    }
    forbidden_attributes = {
        "account",
        "auth",
        "cancel",
        "client",
        "connect",
        "cursor",
        "execute",
        "getenv",
        "open",
        "request",
        "sign",
        "submit",
        "wallet",
        "write",
    }
    forbidden_fragments = (
        "account",
        "auth",
        "cancel_order",
        "cli",
        "live",
        "network",
        "order_submission",
        "private-key",
        "private_key",
        "psycopg",
        "runner",
        "signing",
        "submit_order",
        "wallet",
    )

    assert imported_modules <= allowed_imports
    assert call_names.isdisjoint(forbidden_calls)
    assert attribute_names.isdisjoint(forbidden_attributes)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)
