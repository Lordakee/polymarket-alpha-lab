from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_cost_stress import (
    PaperCostStressReport,
    PaperCostStressScenarioRow,
)
from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueReport,
    PaperProbabilityRecommendationQueueRow,
)


GENERATED_AT = datetime(2026, 6, 21, 15, 0, tzinfo=UTC)
QUEUE_GENERATED_AT = datetime(2026, 6, 21, 14, 0, tzinfo=UTC)
STRESS_GENERATED_AT = datetime(2026, 6, 21, 14, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.paper_probability_selection_summary",
    )


def _config(*, config_version: str = "paper-probability-selection-summary-v0"):
    module = _module()
    return module.PaperProbabilitySelectionSummaryConfig(
        config_version=config_version,
    )


def _queue_row(
    queue_rank: int,
    market_slug: str,
    *,
    side: str = "yes",
    action: str = "recommend",
    recommended_next_step: str = "research_review",
    recommendation_score: Decimal = d("0.120000"),
    net_probability_edge: Decimal = d("0.120000"),
    total_cost_per_share: Decimal = d("0.010000"),
    executable_paper_shares: Decimal = d("100.000000"),
    reason_codes: tuple[str, ...] = ("source_edge",),
) -> PaperProbabilityRecommendationQueueRow:
    if recommended_next_step == "research_review":
        review_priority = "research_review"
    elif recommended_next_step == "await_fresh_context":
        review_priority = "watch"
    else:
        review_priority = "skip"
    return PaperProbabilityRecommendationQueueRow(
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=f"Will {market_slug} resolve {side}?",
        side=side,
        action=action,
        recommendation_score=recommendation_score,
        net_probability_edge=net_probability_edge,
        total_cost_per_share=total_cost_per_share,
        depth_status="sufficient_depth",
        executable_paper_shares=executable_paper_shares,
        review_priority=review_priority,
        recommended_next_step=recommended_next_step,
        reason_codes=reason_codes,
    )


def _queue_report(
    rows: tuple[PaperProbabilityRecommendationQueueRow, ...],
) -> PaperProbabilityRecommendationQueueReport:
    return PaperProbabilityRecommendationQueueReport(
        generated_at=QUEUE_GENERATED_AT,
        source_config_version="probability-recommendation-queue-v0",
        input_count=len(rows),
        queue_count=len(rows),
        research_review_count=sum(
            1 for row in rows if row.recommended_next_step == "research_review"
        ),
        await_fresh_context_count=sum(
            1 for row in rows if row.recommended_next_step == "await_fresh_context"
        ),
        skip_count=sum(1 for row in rows if row.recommended_next_step == "skip"),
        excluded_count=0,
        queue_rows=rows,
    )


def _stress_row(
    market_slug: str,
    *,
    side: str = "yes",
    action: str = "recommend",
    scenario_name: str = "base",
    net_probability_edge: Decimal = d("0.120000"),
    cost_shock_per_share: Decimal = d("0.010000"),
    total_cost_per_share: Decimal = d("0.010000"),
    recommendation_score: Decimal = d("0.120000"),
    reason_codes: tuple[str, ...] = ("source_edge", "cost_stress_pass"),
) -> PaperCostStressScenarioRow:
    stressed_net_probability_edge = net_probability_edge - cost_shock_per_share
    if stressed_net_probability_edge <= ZERO:
        survival_status = "fail"
    elif action != "recommend":
        survival_status = "watch"
    else:
        survival_status = "pass"
    return PaperCostStressScenarioRow(
        market_slug=market_slug,
        side=side,
        action=action,
        scenario_name=scenario_name,
        net_probability_edge=net_probability_edge,
        cost_shock_per_share=cost_shock_per_share,
        total_cost_per_share=total_cost_per_share,
        recommendation_score=recommendation_score,
        stressed_net_probability_edge=stressed_net_probability_edge,
        survival_status=survival_status,
        reason_codes=reason_codes,
    )


def _stress_report(
    rows: tuple[PaperCostStressScenarioRow, ...],
    *,
    input_count: int | None = None,
    scenario_count: int | None = None,
) -> PaperCostStressReport:
    if input_count is None:
        input_count = len({(row.market_slug, row.side) for row in rows})
    if scenario_count is None:
        scenario_count = len({row.scenario_name for row in rows}) if rows else 0
    return PaperCostStressReport(
        generated_at=STRESS_GENERATED_AT,
        config_version="paper-cost-stress-v0",
        input_count=input_count,
        scenario_count=scenario_count,
        row_count=len(rows),
        pass_count=sum(1 for row in rows if row.survival_status == "pass"),
        watch_count=sum(1 for row in rows if row.survival_status == "watch"),
        fail_count=sum(1 for row in rows if row.survival_status == "fail"),
        rows=rows,
    )


def _build(queue_report, cost_stress_report, *, generated_at=GENERATED_AT, config=None):
    module = _module()
    return module.build_paper_probability_selection_summary_report(
        queue_report,
        cost_stress_report,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_research_review_row_with_all_stress_passes_remains_ready():
    queue_report = _queue_report(
        (
            _queue_row(
                1,
                "event-alpha",
                recommendation_score=d("0.120000"),
                net_probability_edge=d("0.120000"),
            ),
        ),
    )
    stress_report = _stress_report(
        (
            _stress_row("event-alpha", scenario_name="base", cost_shock_per_share=ZERO),
            _stress_row(
                "event-alpha",
                scenario_name="small",
                cost_shock_per_share=d("0.020000"),
            ),
        ),
        input_count=1,
        scenario_count=2,
    )

    report = _build(queue_report, stress_report)

    module = _module()
    assert isinstance(report, module.PaperProbabilitySelectionSummaryReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-probability-selection-summary-v0"
    assert report.source_queue_config_version == "probability-recommendation-queue-v0"
    assert report.source_cost_stress_config_version == "paper-cost-stress-v0"
    assert report.queue_count == 1
    assert report.ready_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.missing_stress_count == 0
    assert report.reason_codes == ("ready_selection_rows_present",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.queue_rank == 1
    assert row.market_slug == "event-alpha"
    assert row.side == "yes"
    assert row.recommended_next_step == "research_review"
    assert row.selection_status == "ready"
    assert row.stress_scenario_count == 2
    assert row.stress_pass_count == 2
    assert row.stress_watch_count == 0
    assert row.stress_fail_count == 0
    assert row.worst_stressed_net_probability_edge == d("0.100000")
    assert row.reason_codes == ("source_edge", "cost_stress_passed")


def test_cost_stress_fail_blocks_research_review_row():
    queue_report = _queue_report(
        (
            _queue_row(
                1,
                "event-alpha",
                net_probability_edge=d("0.030000"),
                recommendation_score=d("0.030000"),
            ),
        ),
    )
    stress_report = _stress_report(
        (
            _stress_row(
                "event-alpha",
                scenario_name="heavy",
                net_probability_edge=d("0.030000"),
                recommendation_score=d("0.030000"),
                cost_shock_per_share=d("0.040000"),
                reason_codes=("source_edge", "nonpositive_stressed_net_probability_edge"),
            ),
        ),
    )

    report = _build(queue_report, stress_report)

    assert report.ready_count == 0
    assert report.blocked_count == 1
    assert report.reason_codes == ("blocked_selection_rows_present",)
    assert report.rows[0].selection_status == "blocked"
    assert report.rows[0].stress_fail_count == 1
    assert report.rows[0].worst_stressed_net_probability_edge == d("-0.010000")
    assert report.rows[0].reason_codes == (
        "source_edge",
        "nonpositive_stressed_net_probability_edge",
        "cost_stress_failed",
    )


def test_missing_stress_rows_fail_closed_for_any_queue_row():
    queue_report = _queue_report(
        (
            _queue_row(1, "event-alpha"),
            _queue_row(
                2,
                "event-beta",
                action="watch",
                recommended_next_step="await_fresh_context",
                recommendation_score=d("0.020000"),
                net_probability_edge=d("0.020000"),
                reason_codes=("market_context_stale",),
            ),
        ),
    )
    stress_report = _stress_report(
        (_stress_row("event-alpha"),),
    )

    report = _build(queue_report, stress_report)

    assert report.ready_count == 1
    assert report.blocked_count == 1
    assert report.missing_stress_count == 1
    missing = report.rows[1]
    assert missing.market_slug == "event-beta"
    assert missing.selection_status == "blocked"
    assert missing.stress_scenario_count == 0
    assert missing.worst_stressed_net_probability_edge is None
    assert missing.reason_codes == ("market_context_stale", "missing_cost_stress")


def test_stress_watch_downgrades_research_review_but_source_watch_stays_watch():
    queue_report = _queue_report(
        (
            _queue_row(1, "event-alpha"),
            _queue_row(
                2,
                "event-beta",
                action="watch",
                recommended_next_step="await_fresh_context",
                recommendation_score=d("0.020000"),
                net_probability_edge=d("0.020000"),
                reason_codes=("market_context_stale",),
            ),
        ),
    )
    stress_report = _stress_report(
        (
            _stress_row(
                "event-alpha",
                action="watch",
                cost_shock_per_share=d("0.010000"),
                reason_codes=("source_edge", "source_action_not_recommend"),
            ),
            _stress_row(
                "event-beta",
                action="watch",
                net_probability_edge=d("0.020000"),
                recommendation_score=d("0.020000"),
                cost_shock_per_share=d("0.005000"),
                reason_codes=("market_context_stale", "source_action_not_recommend"),
            ),
        ),
        input_count=2,
        scenario_count=1,
    )

    report = _build(queue_report, stress_report)

    assert report.ready_count == 0
    assert report.watch_count == 2
    assert tuple(row.selection_status for row in report.rows) == ("watch", "watch")
    assert report.rows[0].reason_codes == (
        "source_edge",
        "source_action_not_recommend",
        "cost_stress_watch",
    )
    assert report.rows[1].reason_codes == (
        "market_context_stale",
        "source_next_step_await_fresh_context",
    )


def test_source_watch_stays_watch_even_when_stress_fails():
    queue_report = _queue_report(
        (
            _queue_row(
                1,
                "event-beta",
                action="watch",
                recommended_next_step="await_fresh_context",
                recommendation_score=d("0.020000"),
                net_probability_edge=d("0.020000"),
                reason_codes=("market_context_stale",),
            ),
        ),
    )
    stress_report = _stress_report(
        (
            _stress_row(
                "event-beta",
                action="watch",
                net_probability_edge=d("0.020000"),
                recommendation_score=d("0.020000"),
                cost_shock_per_share=d("0.030000"),
                reason_codes=(
                    "market_context_stale",
                    "nonpositive_stressed_net_probability_edge",
                ),
            ),
        ),
    )

    report = _build(queue_report, stress_report)

    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.rows[0].selection_status == "watch"
    assert report.rows[0].stress_fail_count == 1
    assert report.rows[0].worst_stressed_net_probability_edge == d("-0.010000")
    assert report.rows[0].reason_codes == (
        "market_context_stale",
        "source_next_step_await_fresh_context",
    )


def test_skip_queue_rows_are_blocked_even_when_stress_exists():
    queue_report = _queue_report(
        (
            _queue_row(1, "event-alpha"),
            _queue_row(
                2,
                "event-gamma",
                action="reject",
                recommended_next_step="skip",
                recommendation_score=ZERO,
                net_probability_edge=d("-0.010000"),
                executable_paper_shares=ZERO,
                reason_codes=("nonpositive_net_probability_edge",),
            ),
        ),
    )
    stress_report = _stress_report(
        (
            _stress_row("event-alpha"),
            _stress_row(
                "event-gamma",
                action="reject",
                net_probability_edge=d("-0.010000"),
                recommendation_score=ZERO,
                cost_shock_per_share=ZERO,
                reason_codes=("nonpositive_net_probability_edge",),
            ),
        ),
        input_count=2,
        scenario_count=1,
    )

    report = _build(queue_report, stress_report)

    assert tuple(row.selection_status for row in report.rows) == ("ready", "blocked")
    assert report.rows[1].reason_codes == (
        "nonpositive_net_probability_edge",
        "source_next_step_skip",
    )


def test_join_uses_market_slug_and_side_not_market_slug_only():
    queue_report = _queue_report(
        (
            _queue_row(1, "event-alpha", side="yes"),
            _queue_row(2, "event-alpha", side="no", recommendation_score=d("0.110000")),
        ),
    )
    stress_report = _stress_report(
        (
            _stress_row("event-alpha", side="yes"),
            _stress_row(
                "event-alpha",
                side="no",
                recommendation_score=d("0.110000"),
                cost_shock_per_share=d("0.200000"),
                reason_codes=("source_edge", "nonpositive_stressed_net_probability_edge"),
            ),
        ),
        input_count=2,
        scenario_count=1,
    )

    report = _build(queue_report, stress_report)

    assert tuple((row.side, row.selection_status) for row in report.rows) == (
        ("yes", "ready"),
        ("no", "blocked"),
    )


def test_builder_rejects_mismatched_stress_rows_and_non_exact_types():
    queue_report = _queue_report((_queue_row(1, "event-alpha"),))
    stress_report = _stress_report(
        (
            _stress_row(
                "event-alpha",
                net_probability_edge=d("0.020000"),
                reason_codes=("source_edge", "source_action_not_recommend"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="stress rows must match queue row"):
        _build(queue_report, stress_report)

    module = _module()
    with pytest.raises(ValueError, match="queue_report"):
        module.build_paper_probability_selection_summary_report(
            object(),
            stress_report,
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="cost_stress_report"):
        module.build_paper_probability_selection_summary_report(
            queue_report,
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_paper_probability_selection_summary_report(
            queue_report,
            stress_report,
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_validates_counts_flags_datetime_and_is_frozen():
    queue_report = _queue_report((_queue_row(1, "event-alpha"),))
    stress_report = _stress_report((_stress_row("event-alpha"),))

    module = _module()
    report = _build(
        queue_report,
        stress_report,
        generated_at=datetime(2026, 6, 21, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        report.ready_count = 0
    with pytest.raises(FrozenInstanceError):
        report.rows[0].selection_status = "blocked"
    with pytest.raises(ValueError, match="ready_count"):
        replace(report, ready_count=99)
    with pytest.raises(ValueError, match="paper_only"):
        module.PaperProbabilitySelectionSummaryConfig(
            config_version="paper-probability-selection-summary-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        _build(queue_report, stress_report, generated_at="2026-06-21T15:00:00Z")

    unsafe_queue = _queue_report((_queue_row(1, "event-alpha"),))
    object.__setattr__(unsafe_queue, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _build(unsafe_queue, stress_report)

    bypassed_row = object.__new__(module.PaperProbabilitySelectionSummaryRow)
    for field_name, value in report.rows[0].__dict__.items():
        object.__setattr__(bypassed_row, field_name, value)
    object.__setattr__(bypassed_row, "selection_status", "ready")
    object.__setattr__(bypassed_row, "stress_pass_count", 0)
    object.__setattr__(bypassed_row, "stress_fail_count", 1)
    with pytest.raises(ValueError, match="ready rows"):
        module.PaperProbabilitySelectionSummaryReport(
            generated_at=GENERATED_AT,
            config_version="paper-probability-selection-summary-v0",
            source_queue_config_version="probability-recommendation-queue-v0",
            source_cost_stress_config_version="paper-cost-stress-v0",
            queue_count=1,
            ready_count=1,
            watch_count=0,
            blocked_count=0,
            missing_stress_count=0,
            rows=(bypassed_row,),
            reason_codes=("ready_selection_rows_present",),
        )
