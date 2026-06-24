from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
    PaperAutonomousAllocationProposalReasonCodeCount,
    PaperAutonomousAllocationProposalReport,
    PaperAutonomousAllocationProposalSourceQueueSummary,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION,
    PaperAutonomousAllocationProposalDbHistoryConfig,
    build_paper_autonomous_allocation_proposal_db_history_report,
)
from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationConfig,
    PaperRecommendationAllocationInput,
    build_paper_recommendation_allocation_report,
)


NOW = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 6, 24, 9, 0, tzinfo=UTC)
T2 = datetime(2026, 6, 24, 10, 0, tzinfo=UTC)
T3 = datetime(2026, 6, 24, 11, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _allocation_config(
    *,
    total_paper_budget: Decimal = d("100.000000"),
) -> PaperRecommendationAllocationConfig:
    return PaperRecommendationAllocationConfig(
        config_version="allocation-v0",
        total_paper_budget=total_paper_budget,
        max_paper_notional_per_market=d("100.000000"),
        max_paper_notional_per_event=d("100.000000"),
        max_paper_notional_per_theme=d("100.000000"),
        max_paper_notional_per_correlation_group=d("100.000000"),
    )


def _allocation_input(
    *,
    market_slug: str,
    recommendation_score: Decimal,
    executable_paper_shares: Decimal,
) -> PaperRecommendationAllocationInput:
    return PaperRecommendationAllocationInput(
        market_slug=market_slug,
        side="yes",
        action="recommend",
        recommendation_score=recommendation_score,
        net_probability_edge=None,
        executable_paper_shares=executable_paper_shares,
        side_price=d("1.000000"),
        reason_codes=("selected_by_policy",),
    )


def _allocation_report(
    *,
    generated_at: datetime,
    proposal_status: str,
) -> object:
    total_paper_budget = d("25.000000") if proposal_status == "watch" else d("100.000000")
    return build_paper_recommendation_allocation_report(
        (
            _allocation_input(
                market_slug="alpha-ready",
                recommendation_score=d("0.900000"),
                executable_paper_shares=d("20.000000"),
            ),
            _allocation_input(
                market_slug="beta-ready",
                recommendation_score=d("0.800000"),
                executable_paper_shares=d("10.000000"),
            ),
        ),
        config=_allocation_config(total_paper_budget=total_paper_budget),
        generated_at=generated_at,
    )


def _reason_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousAllocationProposalReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousAllocationProposalReasonCodeCount(
            reason_code=reason_code,
            report_count=report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _recommended_next_step(proposal_status: str) -> str:
    return {
        "pass": "review_paper_autonomous_allocation_proposal",
        "watch": "hold_paper_autonomous_allocation_proposal",
        "blocked": "block_paper_autonomous_allocation_proposal",
    }[proposal_status]


def _proposal_report(
    *,
    generated_at: datetime,
    proposal_status: str = "pass",
    reason_codes: tuple[str, ...] = (
        "paper_autonomous_allocation_proposal_passed",
    ),
) -> PaperAutonomousAllocationProposalReport:
    allocation_report = _allocation_report(
        generated_at=generated_at,
        proposal_status=proposal_status,
    )
    return PaperAutonomousAllocationProposalReport(
        generated_at=generated_at,
        config_version=DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
        proposal_status=proposal_status,
        recommended_next_step=_recommended_next_step(proposal_status),
        reason_code_counts=_reason_counts(reason_codes),
        reason_codes=reason_codes,
        screening_gate_config_version="paper-autonomous-screening-decision-support-gate-v0",
        screening_gate_generated_at=generated_at,
        screening_gate_status="pass",
        screening_gate_recommended_next_step=(
            "advance_paper_autonomous_screening_recommendations"
        ),
        queue_priority_generated_at=generated_at,
        queue_risk_generated_at=generated_at,
        queue_risk_config_version="action-gated-queue-risk-v0",
        queue_risk_status="pass",
        queue_risk_recommended_next_step="advance_action_gated_strategy_queue",
        source_queue_count=1,
        source_queue_summaries=(
            PaperAutonomousAllocationProposalSourceQueueSummary(
                source_generated_at=generated_at,
                config_version="action-gated-queue-v0",
                source_config_version="paper-recommendation-cycle-action-gate-v0",
                action_status="research_ready",
                queue_count=2,
                ready_count=2,
                watch_count=0,
                blocked_count=0,
                total_ready_notional=d("30.000000"),
                allocation_input_count=2,
            ),
        ),
        allocation_config_version=allocation_report.config_version,
        allocation_input_count=2,
        allocation_report=allocation_report,
    )


def test_config_defaults_are_safe_phase1_defaults() -> None:
    config = PaperAutonomousAllocationProposalDbHistoryConfig()

    assert (
        config.config_version
        == DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION
    )
    assert config.min_report_count == 3
    assert config.max_blocked_proposal_report_count == 0
    assert config.max_watch_proposal_report_count == 0
    assert config.max_duplicate_generated_at_count == 0
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_allocation_proposal_db_history_summarizes_chronological_reports() -> None:
    reports = (
        _proposal_report(
            generated_at=T3,
            proposal_status="watch",
            reason_codes=("allocation_capped",),
        ),
        _proposal_report(generated_at=T1),
        _proposal_report(generated_at=T2),
    )

    history = build_paper_autonomous_allocation_proposal_db_history_report(
        reports,
        config=PaperAutonomousAllocationProposalDbHistoryConfig(),
        generated_at=NOW,
    )

    assert history.history_status == "watch"
    assert history.report_count == 3
    assert history.first_report_generated_at == T1
    assert history.latest_report_generated_at == T3
    assert history.latest_proposal_status == "watch"
    assert history.latest_screening_gate_status == "pass"
    assert history.latest_queue_risk_status == "pass"
    assert history.latest_allocation_input_count == 2
    assert history.latest_allocation_row_count == 2
    assert history.latest_allocated_count == 1
    assert history.latest_total_allocated_paper_notional == d("25.000000")
    assert [
        (row.proposal_status, row.status_count)
        for row in history.proposal_status_rows
    ] == [
        ("pass", 2),
        ("watch", 1),
        ("blocked", 0),
    ]
    assert history.consecutive_latest_watch_count == 1
    assert history.latest_reason_codes == ("allocation_capped",)
    assert [
        (row.reason_code, row.report_count) for row in history.reason_code_rows
    ] == [
        ("paper_autonomous_allocation_proposal_passed", 2),
        ("allocation_capped", 1),
    ]


def test_allocation_proposal_db_history_blocks_insufficient_history() -> None:
    history = build_paper_autonomous_allocation_proposal_db_history_report(
        (),
        config=PaperAutonomousAllocationProposalDbHistoryConfig(min_report_count=2),
        generated_at=NOW,
    )

    assert history.history_status == "blocked"
    assert history.reason_codes == (
        "insufficient_paper_autonomous_allocation_proposal_history",
    )


def test_allocation_proposal_db_history_flags_duplicate_generated_at() -> None:
    reports = (
        _proposal_report(generated_at=T1),
        _proposal_report(generated_at=T1),
        _proposal_report(generated_at=T2),
    )

    history = build_paper_autonomous_allocation_proposal_db_history_report(
        reports,
        config=PaperAutonomousAllocationProposalDbHistoryConfig(),
        generated_at=NOW,
    )

    assert history.history_status == "watch"
    assert history.duplicate_generated_at_count == 1
    assert history.reason_codes == (
        "duplicate_generated_at_threshold_exceeded",
    )


def test_allocation_proposal_db_history_collects_independent_threshold_reasons() -> None:
    reports = (
        _proposal_report(
            generated_at=T1,
            proposal_status="watch",
            reason_codes=("allocation_capped",),
        ),
        _proposal_report(
            generated_at=T1,
            proposal_status="watch",
            reason_codes=("allocation_capped",),
        ),
    )

    history = build_paper_autonomous_allocation_proposal_db_history_report(
        reports,
        config=PaperAutonomousAllocationProposalDbHistoryConfig(min_report_count=3),
        generated_at=NOW,
    )

    assert history.history_status == "blocked"
    assert history.reason_codes == (
        "duplicate_generated_at_threshold_exceeded",
        "insufficient_paper_autonomous_allocation_proposal_history",
        "watch_allocation_proposal_report_threshold_exceeded",
    )


def test_allocation_proposal_db_history_rejects_unsafe_config_flags() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        PaperAutonomousAllocationProposalDbHistoryConfig(paper_only=False)
