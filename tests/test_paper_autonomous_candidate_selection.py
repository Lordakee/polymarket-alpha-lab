from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_candidate_selection import (
    DEFAULT_PAPER_AUTONOMOUS_CANDIDATE_SELECTION_CONFIG_VERSION,
    PaperAutonomousCandidateSelectionConfig,
    PaperAutonomousCandidateSelectionReport,
    build_paper_autonomous_candidate_selection_report,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)


GENERATED_AT = datetime(2026, 6, 30, 12, tzinfo=UTC)


def test_selection_report_passes_clean_unique_candidates_without_rescaling() -> None:
    first = _source_row(
        research_rank=1,
        queue_rank=1,
        market_slug="market-a",
        selected_side="yes",
        suggested_notional=Decimal("25.000000"),
        recommendation_score=Decimal("0.800000"),
        readiness_score=Decimal("0.600000"),
        research_priority_score=Decimal("0.700000"),
        net_edge_per_share=Decimal("0.080000"),
    )
    second = _source_row(
        research_rank=2,
        queue_rank=2,
        market_slug="market-b",
        selected_side="no",
        suggested_notional=Decimal("10.500000"),
        recommendation_score=Decimal("0.700000"),
        readiness_score=Decimal("0.500000"),
        research_priority_score=Decimal("0.600000"),
        net_edge_per_share=Decimal("0.040000"),
    )
    source_report = _source_report((first, second))

    report = build_paper_autonomous_candidate_selection_report(
        (source_report,),
        config=PaperAutonomousCandidateSelectionConfig(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperAutonomousCandidateSelectionReport)
    assert report.config_version == DEFAULT_PAPER_AUTONOMOUS_CANDIDATE_SELECTION_CONFIG_VERSION
    assert report.selection_status == "pass"
    assert report.recommended_next_step == "review_paper_candidate_selection"
    assert report.source_report_count == 1
    assert report.candidate_count == 2
    assert report.selected_candidate_count == 2
    assert report.not_selected_candidate_count == 0
    assert report.total_selected_notional == Decimal("35.500000")
    assert report.total_suggested_notional == Decimal("35.500000")
    assert report.reason_codes == ("paper_autonomous_candidate_selection_pass",)
    assert tuple(row.selected_notional for row in report.rows) == (
        Decimal("25.000000"),
        Decimal("10.500000"),
    )
    assert report.rows[0].market_slug == first.market_slug
    assert report.rows[0].question == first.question
    assert report.rows[0].source_action == first.source_action
    assert report.rows[0].source_decision == first.decision
    assert report.rows[0].recommendation_score == first.recommendation_score
    assert report.rows[0].research_priority_score == first.research_priority_score
    assert report.rows[0].reason_codes == ("candidate_selection_selected",)
    assert report.source_summaries[0].selected_candidate_count == 2
    assert report.paper_only is True and report.report_only is True and report.readonly is True


def test_selection_report_blocks_when_source_rows_are_not_selection_ready() -> None:
    stale_source_row = _source_row(
        research_rank=1,
        queue_rank=1,
        market_slug="market-a",
        net_edge_per_share=Decimal("0.080000"),
    )
    missing_edge_row = _source_row(
        research_rank=2,
        queue_rank=2,
        market_slug="market-b",
        net_edge_per_share=None,
    )
    low_priority_row = _source_row(
        research_rank=3,
        queue_rank=3,
        market_slug="market-c",
        recommendation_score=Decimal("0.400000"),
        readiness_score=Decimal("0.300000"),
        research_priority_score=Decimal("0.350000"),
        net_edge_per_share=Decimal("0.080000"),
    )
    source_report = _source_report(
        (stale_source_row, missing_edge_row, low_priority_row),
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
    )

    report = build_paper_autonomous_candidate_selection_report(
        (source_report,),
        config=PaperAutonomousCandidateSelectionConfig(
            min_research_priority_score=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.selection_status == "blocked"
    assert report.selected_candidate_count == 0
    assert report.total_selected_notional == Decimal("0.000000")
    assert tuple(row.selected_notional for row in report.rows) == (
        Decimal("0.000000"),
        Decimal("0.000000"),
        Decimal("0.000000"),
    )
    assert "source_action_status_not_research_ready" in report.rows[0].reason_codes
    assert "candidate_selection_missing_net_edge" in report.rows[1].reason_codes
    assert "candidate_selection_research_priority_below_threshold" in report.rows[2].reason_codes
    assert report.reason_codes == ("paper_autonomous_candidate_selection_no_selected_candidates",)


def test_selection_report_watches_for_duplicate_and_max_count_suppression() -> None:
    rows = (
        _source_row(
            research_rank=1,
            queue_rank=1,
            market_slug="market-a",
            selected_side="yes",
            suggested_notional=Decimal("12.000000"),
        ),
        _source_row(
            research_rank=2,
            queue_rank=2,
            market_slug="market-a",
            selected_side="yes",
            suggested_notional=Decimal("13.000000"),
        ),
        _source_row(
            research_rank=3,
            queue_rank=3,
            market_slug="market-b",
            selected_side="no",
            suggested_notional=Decimal("14.000000"),
        ),
    )

    report = build_paper_autonomous_candidate_selection_report(
        (_source_report(rows),),
        config=PaperAutonomousCandidateSelectionConfig(max_selected_candidate_count=1),
        generated_at=GENERATED_AT,
    )

    assert report.selection_status == "watch"
    assert report.selected_candidate_count == 1
    assert report.not_selected_candidate_count == 2
    assert report.total_selected_notional == Decimal("12.000000")
    assert tuple(row.selected_notional for row in report.rows) == (
        Decimal("12.000000"),
        Decimal("0.000000"),
        Decimal("0.000000"),
    )
    assert report.rows[0].selection_status == "selected"
    assert "candidate_selection_duplicate_suppressed" in report.rows[1].reason_codes
    assert "candidate_selection_max_selected_candidate_count_reached" in report.rows[2].reason_codes
    assert report.reason_codes == (
        "paper_autonomous_candidate_selection_duplicate_suppressed",
        "paper_autonomous_candidate_selection_max_selected_candidate_count_reached",
    )


def test_selection_report_watches_when_selected_candidates_have_source_warnings() -> None:
    ready_row = _source_row(
        research_rank=1,
        queue_rank=1,
        market_slug="market-a",
        suggested_notional=Decimal("9.000000"),
    )
    watch_row = _source_row(
        research_rank=2,
        queue_rank=2,
        market_slug="market-b",
        decision="skipped",
        queue_status="watch",
        research_status="watch",
        suggested_notional=Decimal("0.000000"),
        selected_position_notional=Decimal("0.000000"),
        primary_reason_code="readiness_watch",
        reason_codes=("readiness_watch",),
        evidence_gap_codes=("readiness_watch",),
    )

    report = build_paper_autonomous_candidate_selection_report(
        (_source_report((ready_row, watch_row)),),
        config=PaperAutonomousCandidateSelectionConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.selection_status == "watch"
    assert report.selected_candidate_count == 1
    assert report.source_warning_count == 1
    assert report.source_summaries[0].source_warning is True
    assert report.reason_codes == ("paper_autonomous_candidate_selection_source_warning",)


def test_builder_rejects_wrong_types_and_false_hard_flags() -> None:
    row = _source_row()
    source_report = _source_report((row,))

    with pytest.raises(ValueError, match="source_reports must be a tuple"):
        build_paper_autonomous_candidate_selection_report(
            [source_report],
            config=PaperAutonomousCandidateSelectionConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="config must be exactly"):
        build_paper_autonomous_candidate_selection_report(
            (source_report,),
            config="not-config",
            generated_at=GENERATED_AT,
        )

    broken_config = PaperAutonomousCandidateSelectionConfig()
    object.__setattr__(broken_config, "readonly", False)
    with pytest.raises(ValueError, match="config must be readonly"):
        build_paper_autonomous_candidate_selection_report(
            (source_report,),
            config=broken_config,
            generated_at=GENERATED_AT,
        )

    broken_report = replace(source_report)
    object.__setattr__(broken_report, "paper_only", False)
    with pytest.raises(ValueError, match="source_report must be paper_only"):
        build_paper_autonomous_candidate_selection_report(
            (broken_report,),
            config=PaperAutonomousCandidateSelectionConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubConfig(PaperAutonomousCandidateSelectionConfig):
            pass


def test_config_rejects_float_thresholds_and_quantizes_decimals() -> None:
    config = PaperAutonomousCandidateSelectionConfig(
        min_net_edge_per_share=Decimal("0.0100004"),
        min_research_priority_score=Decimal("0.5000004"),
    )

    assert config.min_net_edge_per_share == Decimal("0.010000")
    assert config.min_research_priority_score == Decimal("0.500000")

    with pytest.raises(ValueError, match="min_net_edge_per_share must be a Decimal"):
        PaperAutonomousCandidateSelectionConfig(min_net_edge_per_share=0.01)


def _source_report(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
    *,
    action_status: str = "research_ready",
    recommended_next_step: str = "review_candidate_research_queue",
) -> PaperStrategyCandidateResearchQueueReport:
    ready_count = sum(1 for row in rows if row.research_status == "ready")
    watch_count = sum(1 for row in rows if row.research_status == "watch")
    blocked_count = sum(1 for row in rows if row.research_status == "blocked")
    selected_count = sum(1 for row in rows if row.decision == "selected")
    skipped_count = sum(1 for row in rows if row.decision == "skipped")
    not_selected_count = sum(1 for row in rows if row.decision == "not_selected")
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=datetime(2026, 6, 30, 11, tzinfo=UTC),
        config_version="strategy-candidate-research-queue-v0",
        source_config_version="paper-action-gated-strategy-recommendation-queue-v0",
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        source_reason_code_counts=(),
        research_status="ready",
        candidate_count=len(rows),
        research_ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        selected_count=selected_count,
        skipped_count=skipped_count,
        not_selected_count=not_selected_count,
        total_ready_notional=sum(
            (row.suggested_notional for row in rows if row.research_status == "ready"),
            Decimal("0"),
        ),
        total_selected_notional=sum(
            (row.selected_position_notional for row in rows),
            Decimal("0"),
        ),
        total_suggested_notional=sum(
            (
                row.suggested_notional
                for row in rows
                if row.source_action == "recommend"
            ),
            Decimal("0"),
        ),
        top_research_priority_score=rows[0].research_priority_score if rows else Decimal("0"),
        average_research_ready_score=(
            sum(
                (
                    row.research_priority_score
                    for row in rows
                    if row.research_status == "ready"
                ),
                Decimal("0"),
            )
            / Decimal(ready_count)
            if ready_count
            else Decimal("0")
        ),
        primary_reason_code_counts=tuple(
            sorted(
                {
                    row.primary_reason_code: sum(
                        1 for item in rows if item.primary_reason_code == row.primary_reason_code
                    )
                    for row in rows
                }.items(),
                key=lambda item: (-item[1], item[0]),
            ),
        ),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def _source_row(
    *,
    research_rank: int = 1,
    queue_rank: int = 1,
    market_slug: str = "market-a",
    question: str = "Will market A resolve yes?",
    selected_side: str = "yes",
    source_action: str = "recommend",
    decision: str = "selected",
    queue_status: str = "ready",
    research_status: str = "ready",
    recommendation_score: Decimal = Decimal("0.800000"),
    readiness_score: Decimal = Decimal("0.600000"),
    research_priority_score: Decimal = Decimal("0.700000"),
    net_edge_per_share: Decimal | None = Decimal("0.050000"),
    suggested_notional: Decimal = Decimal("20.000000"),
    selected_position_notional: Decimal | None = None,
    primary_reason_code: str = "high_net_edge",
    reason_codes: tuple[str, ...] = ("high_net_edge",),
    evidence_gap_codes: tuple[str, ...] = (),
) -> PaperStrategyCandidateResearchQueueRow:
    if selected_position_notional is None:
        selected_position_notional = (
            suggested_notional if decision == "selected" else Decimal("0.000000")
        )
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=question,
        selected_side=selected_side,
        scoring_side=selected_side,
        source_action=source_action,
        decision=decision,
        queue_status=queue_status,
        research_status=research_status,
        research_bucket="core",
        assessment_status="ready",
        source_status="ready",
        readiness_status="ready",
        recommendation_score=recommendation_score,
        readiness_score=readiness_score,
        screening_score=Decimal("0.750000"),
        net_edge_per_share=net_edge_per_share,
        total_cost_per_share=Decimal("0.020000"),
        confidence=Decimal("0.700000"),
        spread=Decimal("0.020000"),
        resolution_risk=Decimal("0.050000"),
        suggested_notional=suggested_notional,
        selected_position_notional=selected_position_notional,
        primary_reason_code=primary_reason_code,
        research_priority_score=research_priority_score,
        evidence_gap_codes=evidence_gap_codes,
        reason_codes=reason_codes,
        explanation="Candidate has enough paper-only evidence.",
    )
